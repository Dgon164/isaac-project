import { useState, useEffect, useRef, useCallback } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

// ============================================================
// CORE MATH
// ============================================================

function rootC(a, b) {
  const p = a * b;
  return p >= 0 ? Math.sqrt(p) : -Math.sqrt(-p);
}

function randomMatrix(lo = -0.5, hi = 0.5) {
  const m = new Float64Array(16);
  for (let i = 0; i < 16; i++) m[i] = lo + Math.random() * (hi - lo);
  return m;
}

function matCombine(a, b) {
  const r = new Float64Array(16);
  for (let i = 0; i < 16; i++) r[i] = rootC(a[i], b[i]);
  return r;
}

function matScore(a, b) {
  let sum = 0;
  for (let i = 0; i < 16; i++) sum += rootC(a[i], b[i]);
  return sum / 16;
}

function matLerp(a, b, t) {
  const r = new Float64Array(16);
  for (let i = 0; i < 16; i++) r[i] = a[i] + (b[i] - a[i]) * t;
  return r;
}

function matClone(m) { return new Float64Array(m); }

// ============================================================
// BITMASK ADDRESSING
// ============================================================

function popcount(n) {
  n = n | 0;
  let c = 0;
  let v = n;
  while (v) { c += v & 1; v = v >>> 1; }
  return c;
}

function overlapScore(a, b) {
  const shared = popcount(a & b);
  const total = popcount(a | b);
  return total === 0 ? 0 : shared / total;
}

// ============================================================
// POSITION ENCODING (Activation Counter)
// ============================================================

function applyPosition(matrix, position, total) {
  const r = new Float64Array(16);
  const phase = ((position + 1) / (total + 1)) * Math.PI;
  for (let row = 0; row < 4; row++) {
    for (let col = 0; col < 4; col++) {
      const idx = row * 4 + col;
      r[idx] = matrix[idx] * (0.7 + 0.3 * Math.cos(phase + (row * Math.PI / 4)));
    }
  }
  return r;
}

// ============================================================
// SYSTEM
// ============================================================

function createSystem() {
  const sys = {
    concepts: new Map(),
    nextBit: 0,
    ghosts: new Map(),     // bitmask → ghost node
    thinking: [],
    tick: 0,
    phase: "arithmetic_add",
    phaseTicks: 0,
    history: [],
    accuracyHistory: [],
    discoveries: [],
    observations: new Map(),
    surplusEnergy: 0.3,
    chainErrors: [],       // record of chain error traces
  };

  const defs = [
    ...Array.from({length: 10}, (_, i) => ({name: String(i), type: "value"})),
    {name: "ADD", type: "op"}, {name: "SUB", type: "op"}, {name: "MUL", type: "op"},
    {name: "EQ", type: "cmp"}, {name: "GT", type: "cmp"}, {name: "LT", type: "cmp"},
    {name: "TRUE", type: "bool"}, {name: "FALSE", type: "bool"},
    {name: "AND", type: "logic"}, {name: "OR", type: "logic"}, {name: "NOT", type: "logic"},
  ];

  for (const def of defs) {
    const bit = 1 << sys.nextBit;
    sys.nextBit++;
    sys.concepts.set(def.name, {
      name: def.name, type: def.type, bit,
      matrix: randomMatrix(-0.5, 0.5),
      energy: 0.5, exposures: 0, correct: 0,
    });
  }

  return sys;
}

// ============================================================
// GHOST NODE OPERATIONS
// ============================================================

function getOrCreateGhost(sys, address) {
  if (sys.ghosts.has(address)) return sys.ghosts.get(address);
  const ghost = {
    address,
    outputs: new Map(),  // conceptName → {weight, count, lastTick}
    activations: 0,
    created: sys.tick,
    energy: 0.3,
  };
  sys.ghosts.set(address, ghost);
  return ghost;
}

function ghostPredict(ghost) {
  if (ghost.outputs.size === 0) return null;
  let best = null, bestW = -Infinity;
  for (const [name, c] of ghost.outputs) {
    if (c.weight > bestW) { bestW = c.weight; best = name; }
  }
  return best !== null ? { predicted: best, confidence: bestW } : null;
}

function ghostLearn(ghost, actualId, predictedId, lr, tick) {
  if (!ghost.outputs.has(actualId)) {
    ghost.outputs.set(actualId, { weight: 0, count: 0, lastTick: tick });
  }
  const actual = ghost.outputs.get(actualId);
  actual.weight += lr;
  actual.count++;
  actual.lastTick = tick;

  if (predictedId && predictedId !== actualId && ghost.outputs.has(predictedId)) {
    const wrong = ghost.outputs.get(predictedId);
    wrong.weight = Math.max(0, wrong.weight - lr * 0.5);
  }
  ghost.activations++;
}

// ============================================================
// SINGLE-STEP EVALUATION
// ============================================================

function evalStep(sys, inputNames, candidateNames) {
  const thinking = [];

  // 1. Build address
  let address = 0;
  for (const name of inputNames) {
    const c = sys.concepts.get(name);
    if (c) address |= c.bit;
  }

  // 2. Build landscape
  let landscape = null;
  for (let i = 0; i < inputNames.length; i++) {
    const c = sys.concepts.get(inputNames[i]);
    if (!c) continue;
    const enc = applyPosition(c.matrix, i, inputNames.length);
    landscape = landscape ? matCombine(landscape, enc) : matClone(enc);
  }

  // 3. Ghost lookup
  const ghost = getOrCreateGhost(sys, address);
  const exactPred = ghostPredict(ghost);

  thinking.push({
    type: "activate",
    msg: `[${inputNames.join(" ")}] addr=${address.toString(2).padStart(Math.min(21, sys.nextBit), '0')}`
  });

  // 4. Score candidates from multiple sources
  const scores = new Map();
  for (const name of candidateNames) scores.set(name, 0);

  // Source A: Exact ghost (strongest)
  for (const [name, conn] of ghost.outputs) {
    if (scores.has(name)) scores.set(name, scores.get(name) + conn.weight * 3.0);
  }

  // Source B: Overlapping ghosts (generalization)
  let neighborCount = 0;
  for (const [addr, g] of sys.ghosts) {
    if (addr === address || g.outputs.size === 0) continue;
    const ov = overlapScore(address, addr);
    if (ov >= 0.5) {
      neighborCount++;
      for (const [name, conn] of g.outputs) {
        if (scores.has(name)) scores.set(name, scores.get(name) + conn.weight * ov * 0.6);
      }
    }
  }

  // Source C: Matrix similarity (raw perception, weakest)
  if (landscape) {
    for (const name of candidateNames) {
      const c = sys.concepts.get(name);
      if (!c) continue;
      scores.set(name, scores.get(name) + matScore(landscape, c.matrix) * 0.3);
    }
  }

  const sorted = [...scores.entries()].sort((a, b) => b[1] - a[1]);
  const predicted = sorted[0][0];
  const confidence = sorted.length > 1 ? sorted[0][1] - sorted[1][1] : sorted[0][1];

  if (exactPred) {
    thinking.push({ type: "ghost", msg: `ghost→${exactPred.predicted} (w=${exactPred.confidence.toFixed(2)})` });
  }
  if (neighborCount > 0) {
    thinking.push({ type: "spread", msg: `${neighborCount} neighbors contributed` });
  }
  thinking.push({ type: "predict", msg: `→ ${predicted} (gap=${confidence.toFixed(3)})` });

  return { address, ghost, landscape, predicted, confidence, thinking, sorted };
}

function learnStep(sys, address, ghost, landscape, predicted, actual) {
  const lr = 0.25;
  const correct = predicted === actual;
  const thinking = [];

  ghostLearn(ghost, actual, predicted, lr, sys.tick);

  const ac = sys.concepts.get(actual);
  const pc = sys.concepts.get(predicted);

  if (ac && landscape) {
    if (correct) {
      ac.matrix = matLerp(ac.matrix, landscape, 0.008);
      ac.energy = Math.min(0.9, ac.energy + 0.004);
    } else if (pc) {
      // Relative correction
      for (let i = 0; i < 16; i++) {
        const diff = Math.abs(ac.matrix[i] - pc.matrix[i]);
        if (diff > 0.1) {
          ac.matrix[i] += (landscape[i] - ac.matrix[i]) * 0.025;
          pc.matrix[i] -= (landscape[i] - pc.matrix[i]) * 0.008;
        }
      }
      ac.energy = Math.max(0.05, ac.energy - 0.01);
      thinking.push({ type: "correct", msg: `relative correction: ${actual} vs ${predicted}` });
    }
  }

  if (ac) {
    ac.exposures++;
    if (correct) ac.correct++;
  }

  return { correct, thinking };
}

// ============================================================
// CHAIN DECOMPOSITION & ERROR TRACING
// ============================================================

// A chain is: { steps: [{inputs, op, expected}], finalExpected }
// e.g. MUL(5, ADD(2, 7)) = 45
//   step 0: ADD(2, 7) → 9
//   step 1: MUL(5, [result of step 0]) → 45

function generateChain(sys) {
  const r = Math.random();

  if (r < 0.5) {
    // ADD then MUL: MUL(b, ADD(a, c))
    const a = Math.floor(Math.random() * 5);
    const c = Math.floor(Math.random() * (5 - a));
    const sum = a + c;
    const b = Math.floor(Math.random() * 4);
    const product = b * sum;
    if (product > 9 || sum > 9) return generateChain(sys);

    return {
      display: `${b} × (${a} + ${c})`,
      steps: [
        { inputs: [String(a), "ADD", String(c)], expected: String(sum), candidates: Array.from({length: 10}, (_, i) => String(i)) },
        { inputs: [String(b), "MUL", null], expected: String(product), candidates: Array.from({length: 10}, (_, i) => String(i)), usePrevResult: true },
      ],
      finalExpected: String(product),
    };
  } else {
    // SUB from ADD: ADD(a, b) then SUB(result, b) should give a
    const a = Math.floor(Math.random() * 5);
    const b = Math.floor(Math.random() * (5 - a));
    const sum = a + b;
    if (sum > 9) return generateChain(sys);

    return {
      display: `(${a} + ${b}) − ${b} = ?`,
      steps: [
        { inputs: [String(a), "ADD", String(b)], expected: String(sum), candidates: Array.from({length: 10}, (_, i) => String(i)) },
        { inputs: [null, "SUB", String(b)], expected: String(a), candidates: Array.from({length: 10}, (_, i) => String(i)), usePrevResult: true },
      ],
      finalExpected: String(a),
    };
  }
}

function evalChain(sys, chain) {
  const thinking = [];
  thinking.push({ type: "chain", msg: `Chain: ${chain.display}` });

  let prevResult = null;
  const stepResults = [];

  for (let s = 0; s < chain.steps.length; s++) {
    const step = chain.steps[s];

    // Build input names, substituting previous result where needed
    const inputs = step.inputs.map(x => {
      if (x === null && step.usePrevResult && prevResult !== null) return prevResult;
      return x;
    });

    thinking.push({ type: "chain_step", msg: `Step ${s + 1}: ${inputs.join(" ")} → expect ${step.expected}` });

    const evalResult = evalStep(sys, inputs, step.candidates);
    const predicted = evalResult.predicted;
    const correct = predicted === step.expected;

    stepResults.push({
      stepIdx: s,
      inputs,
      predicted,
      expected: step.expected,
      correct,
      ghost: evalResult.ghost,
      address: evalResult.address,
      landscape: evalResult.landscape,
    });

    thinking.push({
      type: correct ? "chain_ok" : "chain_fail",
      msg: `Step ${s + 1}: predicted ${predicted}, expected ${step.expected} ${correct ? "✓" : "✗ BREAK"}`,
    });

    prevResult = predicted;  // Feed forward (even if wrong — system follows its own predictions)
  }

  // Final result
  const finalPredicted = prevResult;
  const finalCorrect = finalPredicted === chain.finalExpected;

  // ERROR TRACING: if final is wrong, trace back through chain
  if (!finalCorrect) {
    thinking.push({ type: "trace", msg: `Final wrong (${finalPredicted} vs ${chain.finalExpected}). Tracing error...` });

    // Re-evaluate each step with CORRECT inputs to find the break
    let traceResult = null;
    for (let s = 0; s < chain.steps.length; s++) {
      const step = chain.steps[s];
      const correctInputs = step.inputs.map(x => {
        if (x === null && step.usePrevResult) {
          // Use the EXPECTED result of previous step, not the predicted one
          return s > 0 ? chain.steps[s - 1].expected : x;
        }
        return x;
      });

      const verifyResult = evalStep(sys, correctInputs, step.candidates);
      const stepCorrect = verifyResult.predicted === step.expected;

      if (!stepCorrect) {
        thinking.push({
          type: "trace_found",
          msg: `Error in step ${s + 1}: ${correctInputs.join(" ")} → ${verifyResult.predicted} (should be ${step.expected})`,
        });
        traceResult = {
          brokenStep: s,
          inputs: correctInputs,
          predicted: verifyResult.predicted,
          expected: step.expected,
          ghost: verifyResult.ghost,
          address: verifyResult.address,
          landscape: verifyResult.landscape,
        };
        break;
      } else {
        thinking.push({
          type: "trace_ok",
          msg: `Step ${s + 1} verified OK with correct inputs`,
        });
      }
    }

    // Learn: correct ONLY the broken step
    if (traceResult) {
      const lr = learnStep(
        sys, traceResult.address, traceResult.ghost, traceResult.landscape,
        traceResult.predicted, traceResult.expected
      );
      thinking.push(...lr.thinking);
      thinking.push({
        type: "trace_fix",
        msg: `Corrected step ${traceResult.brokenStep + 1} only. Other steps intact.`,
      });
    } else {
      // Error was caused by feeding wrong intermediate result forward
      // The individual steps are correct but the chain propagated an error
      thinking.push({
        type: "trace_cascade",
        msg: `Cascade error: individual steps OK but wrong intermediate was fed forward`,
      });
      // Learn at each step that got a wrong intermediate input
      for (const sr of stepResults) {
        if (!sr.correct) {
          learnStep(sys, sr.address, sr.ghost, sr.landscape, sr.predicted, sr.expected);
        }
      }
    }
  } else {
    // Correct — reinforce all steps
    for (const sr of stepResults) {
      learnStep(sys, sr.address, sr.ghost, sr.landscape, sr.predicted, sr.expected);
    }
    thinking.push({ type: "chain_ok", msg: `Chain correct! All steps reinforced.` });
  }

  return { finalPredicted, finalCorrect, thinking, stepResults };
}

// ============================================================
// TRAINING DATA: Single triples
// ============================================================

function generateTriple(sys) {
  switch (sys.phase) {
    case "arithmetic_add": {
      const a = Math.floor(Math.random() * 10);
      const b = Math.floor(Math.random() * (10 - a));
      return { inputs: [String(a), "ADD", String(b)], actual: String(a + b),
        candidates: Array.from({length: 10}, (_, i) => String(i)), display: `${a} + ${b} = ?` };
    }
    case "arithmetic_sub": {
      const a = Math.floor(Math.random() * 10);
      const b = Math.floor(Math.random() * (a + 1));
      return { inputs: [String(a), "SUB", String(b)], actual: String(a - b),
        candidates: Array.from({length: 10}, (_, i) => String(i)), display: `${a} − ${b} = ?` };
    }
    case "arithmetic_mul": {
      const a = Math.floor(Math.random() * 4);
      const b = Math.floor(Math.random() * 4);
      const r = a * b;
      if (r > 9) return generateTriple({...sys, phase: "arithmetic_mul"});
      return { inputs: [String(a), "MUL", String(b)], actual: String(r),
        candidates: Array.from({length: 10}, (_, i) => String(i)), display: `${a} × ${b} = ?` };
    }
    case "comparison": {
      const a = Math.floor(Math.random() * 10);
      const b = Math.floor(Math.random() * 10);
      const ops = ["EQ", "GT", "LT"];
      const op = ops[Math.floor(Math.random() * 3)];
      const sym = {EQ: "==", GT: ">", LT: "<"}[op];
      let result = op === "EQ" ? (a === b) : op === "GT" ? (a > b) : (a < b);
      return { inputs: [String(a), op, String(b)], actual: result ? "TRUE" : "FALSE",
        candidates: ["TRUE", "FALSE"], display: `${a} ${sym} ${b} → ?` };
    }
    case "logic": {
      const r = Math.random();
      if (r < 0.4) {
        const a = Math.random() < 0.5 ? "TRUE" : "FALSE";
        const b = Math.random() < 0.5 ? "TRUE" : "FALSE";
        return { inputs: [a, "AND", b], actual: (a === "TRUE" && b === "TRUE") ? "TRUE" : "FALSE",
          candidates: ["TRUE", "FALSE"], display: `${a} ∧ ${b} → ?` };
      } else if (r < 0.8) {
        const a = Math.random() < 0.5 ? "TRUE" : "FALSE";
        const b = Math.random() < 0.5 ? "TRUE" : "FALSE";
        return { inputs: [a, "OR", b], actual: (a === "TRUE" || b === "TRUE") ? "TRUE" : "FALSE",
          candidates: ["TRUE", "FALSE"], display: `${a} ∨ ${b} → ?` };
      } else {
        const a = Math.random() < 0.5 ? "TRUE" : "FALSE";
        return { inputs: ["NOT", a], actual: a === "TRUE" ? "FALSE" : "TRUE",
          candidates: ["TRUE", "FALSE"], display: `¬${a} → ?` };
      }
    }
    default: return generateTriple({...sys, phase: "arithmetic_add"});
  }
}

// ============================================================
// PHASE MANAGEMENT
// ============================================================

const PHASES = ["arithmetic_add", "arithmetic_sub", "arithmetic_mul", "chains", "comparison", "logic"];
const PHASE_NAMES = {
  arithmetic_add: "Addition",
  arithmetic_sub: "Subtraction",
  arithmetic_mul: "Multiplication",
  chains: "Chained Operations",
  comparison: "Comparison → T/F",
  logic: "Boolean Logic",
};

function checkPhaseTransition(sys) {
  const idx = PHASES.indexOf(sys.phase);
  if (idx >= PHASES.length - 1) return false;
  if (sys.phaseTicks < 50) return false;

  const recent = sys.history.filter(h => h.phase === sys.phase).slice(-80);
  if (recent.length < 40) return false;

  const accuracy = recent.filter(h => h.correct).length / recent.length;
  if (accuracy >= 0.85) {
    const next = PHASES[idx + 1];
    sys.discoveries.push({
      tick: sys.tick, type: "phase",
      msg: `Mastered ${PHASE_NAMES[sys.phase]} (${(accuracy * 100).toFixed(0)}%) → ${PHASE_NAMES[next]}`,
    });
    sys.phase = next;
    sys.phaseTicks = 0;
    return true;
  }
  return false;
}

// ============================================================
// PROPERTY DISCOVERY
// ============================================================

function discoverProperties(sys) {
  if (sys.tick % 50 !== 0 || sys.observations.size < 15) return;

  for (const op of ["ADD", "SUB", "MUL"]) {
    const pk = `comm_${op}`;
    if (sys.discoveries.find(d => d.propKey === pk)) continue;
    let comm = 0, non = 0, checks = 0;
    for (const [key, val] of sys.observations) {
      const p = key.split("|");
      if (p[1] !== op) continue;
      const rev = `${p[2]}|${op}|${p[0]}`;
      if (sys.observations.has(rev)) {
        checks++;
        if (sys.observations.get(rev) === val) comm++; else non++;
      }
    }
    if (checks >= 5) {
      if (comm >= checks * 0.85)
        sys.discoveries.push({ tick: sys.tick, type: "property", propKey: pk, msg: `${op} is commutative` });
      else if (non >= checks * 0.4)
        sys.discoveries.push({ tick: sys.tick, type: "property", propKey: pk, msg: `${op} is NOT commutative` });
    }
  }

  const ik = "inv_sub_add";
  if (!sys.discoveries.find(d => d.propKey === ik)) {
    let ev = 0, ch = 0;
    for (const [key, val] of sys.observations) {
      const p = key.split("|");
      if (p[1] !== "ADD") continue;
      const rk = `${val}|SUB|${p[2]}`;
      if (sys.observations.has(rk)) { ch++; if (sys.observations.get(rk) === p[0]) ev++; }
    }
    if (ch >= 4 && ev >= ch * 0.8)
      sys.discoveries.push({ tick: sys.tick, type: "property", propKey: ik, msg: "SUB inverts ADD" });
  }

  for (const op of ["ADD", "MUL"]) {
    const idK = `identity_${op}`;
    if (sys.discoveries.find(d => d.propKey === idK)) continue;
    const cands = new Map();
    for (const [key, val] of sys.observations) {
      const p = key.split("|");
      if (p[1] !== op || val !== p[0]) continue;
      cands.set(p[2], (cands.get(p[2]) || 0) + 1);
    }
    for (const [b, count] of cands) {
      if (count >= 4) {
        sys.discoveries.push({ tick: sys.tick, type: "property", propKey: idK, msg: `${b} is identity for ${op}` });
        break;
      }
    }
  }
}

// ============================================================
// MAIN TICK
// ============================================================

function systemTick(sys) {
  let result;
  const isChain = sys.phase === "chains";

  if (isChain) {
    // 30% chains, 70% simple (to keep reinforcing basics)
    if (Math.random() < 0.35) {
      const chain = generateChain(sys);
      const chainResult = evalChain(sys, chain);

      sys.tick++;
      sys.phaseTicks++;

      sys.history.push({
        tick: sys.tick, correct: chainResult.finalCorrect,
        predicted: chainResult.finalPredicted, actual: chain.finalExpected,
        display: chain.display, confidence: 0, phase: sys.phase,
        isChain: true,
      });

      if (sys.history.length > 600) sys.history = sys.history.slice(-600);

      // Record chain error traces
      if (!chainResult.finalCorrect) {
        sys.chainErrors.push({ tick: sys.tick, display: chain.display, thinking: chainResult.thinking });
        if (sys.chainErrors.length > 20) sys.chainErrors = sys.chainErrors.slice(-20);
      }

      const w = sys.history.slice(-30);
      const acc = w.filter(h => h.correct).length / w.length;
      if (sys.tick % 3 === 0) {
        sys.accuracyHistory.push({ tick: sys.tick, accuracy: Math.round(acc * 100) });
        if (sys.accuracyHistory.length > 400) sys.accuracyHistory = sys.accuracyHistory.slice(-400);
      }

      if (chainResult.finalCorrect) sys.surplusEnergy = Math.min(1, sys.surplusEnergy + 0.003);
      else sys.surplusEnergy = Math.max(0, sys.surplusEnergy - 0.005);

      checkPhaseTransition(sys);
      discoverProperties(sys);

      return {
        display: chain.display,
        predicted: chainResult.finalPredicted,
        actual: chain.finalExpected,
        correct: chainResult.finalCorrect,
        thinking: chainResult.thinking,
        isChain: true,
        acc,
      };
    }
    // else fall through to simple triple (using add/sub/mul randomly)
    const phases = ["arithmetic_add", "arithmetic_sub", "arithmetic_mul"];
    const triple = generateTriple({...sys, phase: phases[Math.floor(Math.random() * phases.length)]});
    return doSimpleTick(sys, triple);
  }

  const triple = generateTriple(sys);
  return doSimpleTick(sys, triple);
}

function doSimpleTick(sys, triple) {
  const ev = evalStep(sys, triple.inputs, triple.candidates);
  const lr = learnStep(sys, ev.address, ev.ghost, ev.landscape, ev.predicted, triple.actual);

  sys.tick++;
  sys.phaseTicks++;

  const correct = ev.predicted === triple.actual;
  sys.history.push({
    tick: sys.tick, correct, predicted: ev.predicted, actual: triple.actual,
    display: triple.display, confidence: ev.confidence, phase: sys.phase,
  });
  if (sys.history.length > 600) sys.history = sys.history.slice(-600);

  const obsKey = triple.inputs.join("|");
  sys.observations.set(obsKey, triple.actual);

  const w = sys.history.slice(-30);
  const acc = w.filter(h => h.correct).length / w.length;
  if (sys.tick % 3 === 0) {
    sys.accuracyHistory.push({ tick: sys.tick, accuracy: Math.round(acc * 100) });
    if (sys.accuracyHistory.length > 400) sys.accuracyHistory = sys.accuracyHistory.slice(-400);
  }

  if (correct) sys.surplusEnergy = Math.min(1, sys.surplusEnergy + 0.003);
  else sys.surplusEnergy = Math.max(0, sys.surplusEnergy - 0.006);

  checkPhaseTransition(sys);
  discoverProperties(sys);

  return {
    display: triple.display,
    predicted: ev.predicted,
    actual: triple.actual,
    correct,
    thinking: [...ev.thinking, ...lr.thinking],
    isChain: false,
    acc,
  };
}

// ============================================================
// UI
// ============================================================

const C = {
  bg: "#0a0c10", panel: "#11141b", border: "#1c2030",
  text: "#c8cdd8", dim: "#5a6070", faint: "#262b38",
  accent: "#5b8cee", green: "#4ade80", red: "#ef5555",
  yellow: "#e2b340", cyan: "#40c8c0", purple: "#a080e0",
  orange: "#e8944a",
};

function Panel({ title, children, style: s }) {
  return (
    <div style={{ background: C.panel, border: `1px solid ${C.border}`, borderRadius: 6, padding: "10px 12px", ...s }}>
      {title && <div style={{ fontSize: 9, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: C.dim, marginBottom: 6 }}>{title}</div>}
      {children}
    </div>
  );
}

function MatrixViz({ matrix, size = 36, label }) {
  if (!matrix) return null;
  const cs = size / 4;
  return (
    <div style={{ display: "inline-block", marginRight: 4, textAlign: "center" }}>
      {label && <div style={{ fontSize: 7, color: C.dim, marginBottom: 1 }}>{label}</div>}
      <svg width={size} height={size}>
        {Array.from({length: 16}, (_, idx) => {
          const v = matrix[idx]; const a = Math.min(1, Math.abs(v));
          return <rect key={idx} x={(idx%4)*cs} y={Math.floor(idx/4)*cs}
            width={cs-0.5} height={cs-0.5} rx={1}
            fill={v >= 0 ? `rgba(90,140,238,${a})` : `rgba(239,85,85,${a})`} />;
        })}
      </svg>
    </div>
  );
}

function GhostViz({ sys }) {
  const ghosts = [...sys.ghosts.entries()]
    .filter(([_, g]) => g.outputs.size > 0)
    .sort((a, b) => b[1].activations - a[1].activations)
    .slice(0, 25);

  if (ghosts.length === 0) return <div style={{ fontSize: 10, color: C.dim, padding: 8 }}>Awaiting first observations…</div>;

  function addrNames(addr) {
    const n = [];
    for (const [name, c] of sys.concepts) { if (addr & c.bit) n.push(name); }
    return n;
  }

  return (
    <div style={{ maxHeight: 170, overflowY: "auto", fontSize: 9 }}>
      {ghosts.map(([addr, ghost]) => {
        const names = addrNames(addr);
        const top = ghostPredict(ghost);
        const outCount = ghost.outputs.size;
        return (
          <div key={addr} style={{ padding: "2px 0", borderBottom: `1px solid ${C.faint}`, display: "flex", gap: 4, alignItems: "center" }}>
            <span style={{ color: C.purple, fontWeight: 600, minWidth: 80 }}>{names.join("+")}</span>
            <span style={{ color: C.faint }}>→</span>
            <span style={{ color: C.cyan, fontWeight: 600 }}>{top ? top.predicted : "?"}</span>
            {outCount > 1 && <span style={{ color: C.dim, fontSize: 7 }}>({outCount})</span>}
            <span style={{ color: C.faint, fontSize: 7, marginLeft: "auto" }}>×{ghost.activations}</span>
          </div>
        );
      })}
    </div>
  );
}

function ThinkingViz({ thinking }) {
  if (!thinking || thinking.length === 0) return null;
  const colors = {
    activate: C.accent, ghost: C.cyan, spread: C.yellow, predict: C.text,
    correct: C.orange, chain: C.purple, chain_step: C.dim, chain_ok: C.green,
    chain_fail: C.red, trace: C.orange, trace_found: C.red, trace_ok: C.green,
    trace_fix: C.yellow, trace_cascade: C.orange, learn: C.green,
  };
  return (
    <div style={{ maxHeight: 160, overflowY: "auto" }}>
      {thinking.map((t, i) => (
        <div key={i} style={{ fontSize: 9, padding: "1px 0", color: colors[t.type] || C.dim, lineHeight: 1.4 }}>
          {t.msg}
        </div>
      ))}
    </div>
  );
}

export default function IntellonV3() {
  const sysRef = useRef(null);
  const [snap, setSnap] = useState(null);
  const [lastResult, setLastResult] = useState(null);
  const [running, setRunning] = useState(false);
  const [speed, setSpeed] = useState(40);
  const intervalRef = useRef(null);

  function takeSnap(sys, result) {
    const w = sys.history.slice(-30);
    const acc = w.length > 0 ? w.filter(h => h.correct).length / w.length : 0;
    const matrices = {};
    for (const id of ["0","1","5","9","ADD","SUB","MUL","TRUE","FALSE"]) {
      const c = sys.concepts.get(id); if (c) matrices[id] = c.matrix;
    }
    return {
      tick: sys.tick, phase: sys.phase, accuracy: acc,
      surplusEnergy: sys.surplusEnergy,
      ghostCount: sys.ghosts.size,
      activeGhosts: [...sys.ghosts.values()].filter(g => g.outputs.size > 0).length,
      totalEdges: [...sys.ghosts.values()].reduce((s, g) => s + g.outputs.size, 0),
      discoveries: sys.discoveries.slice(-20),
      totalDiscoveries: sys.discoveries.length,
      accuracyHistory: sys.accuracyHistory,
      recentHistory: sys.history.slice(-15),
      matrices,
      thinking: result ? result.thinking : [],
      observationCount: sys.observations.size,
      chainErrors: sys.chainErrors.slice(-5),
    };
  }

  useEffect(() => {
    sysRef.current = createSystem();
    setSnap(takeSnap(sysRef.current, null));
  }, []);

  const doStep = useCallback(() => {
    const r = systemTick(sysRef.current);
    setLastResult(r); setSnap(takeSnap(sysRef.current, r));
  }, []);

  const doBatch = useCallback((n) => {
    let r;
    for (let i = 0; i < n; i++) r = systemTick(sysRef.current);
    setLastResult(r); setSnap(takeSnap(sysRef.current, r));
  }, []);

  useEffect(() => {
    if (running) {
      intervalRef.current = setInterval(() => {
        const tpf = speed < 10 ? 10 : speed < 30 ? 5 : 2;
        let r;
        for (let i = 0; i < tpf; i++) r = systemTick(sysRef.current);
        setLastResult(r); setSnap(takeSnap(sysRef.current, r));
      }, speed);
    }
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [running, speed]);

  function handleReset() {
    setRunning(false);
    sysRef.current = createSystem();
    setLastResult(null); setSnap(takeSnap(sysRef.current, null));
  }

  if (!snap) return null;

  const phaseIdx = PHASES.indexOf(snap.phase);
  const btn = (dis) => ({
    padding: "4px 10px", fontSize: 10, fontFamily: "inherit",
    background: dis ? C.faint : C.border, color: dis ? C.dim : C.text,
    border: `1px solid ${dis ? C.faint : C.dim}`, borderRadius: 4,
    cursor: dis ? "not-allowed" : "pointer",
  });

  return (
    <div style={{
      minHeight: "100vh", background: C.bg, color: C.text,
      fontFamily: "'JetBrains Mono','Fira Code','SF Mono',Consolas,monospace",
      fontSize: 11, padding: 14, boxSizing: "border-box",
    }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
        <div>
          <div style={{ fontSize: 15, fontWeight: 700, color: C.accent }}>INTELLON v3</div>
          <div style={{ fontSize: 8, color: C.dim }}>ghost nodes · chains · error tracing · co-activation</div>
        </div>
        <div style={{ display: "flex", gap: 12, fontSize: 10 }}>
          <span><span style={{color:C.dim}}>tick </span><b>{snap.tick}</b></span>
          <span><span style={{color:C.dim}}>ghosts </span><b style={{color:C.purple}}>{snap.activeGhosts}</b><span style={{color:C.faint}}>/{snap.ghostCount}</span></span>
          <span><span style={{color:C.dim}}>edges </span><b style={{color:C.cyan}}>{snap.totalEdges}</b></span>
          <span><span style={{color:C.dim}}>obs </span><b>{snap.observationCount}</b></span>
          <span><span style={{color:C.dim}}>acc </span><b style={{color: snap.accuracy > 0.8 ? C.green : snap.accuracy > 0.5 ? C.yellow : C.red}}>{(snap.accuracy*100).toFixed(0)}%</b></span>
        </div>
      </div>

      {/* Phase bar */}
      <div style={{ display: "flex", gap: 2, marginBottom: 8 }}>
        {PHASES.map((p, i) => (
          <div key={p} style={{ flex: 1, textAlign: "center" }}>
            <div style={{ height: 3, borderRadius: 2, background: i < phaseIdx ? C.green : i === phaseIdx ? C.accent : C.faint }} />
            {i === phaseIdx && <div style={{ fontSize: 7, color: C.accent, marginTop: 3 }}>{PHASE_NAMES[p]}</div>}
          </div>
        ))}
      </div>

      {/* Controls */}
      <div style={{ display: "flex", gap: 5, marginBottom: 8, alignItems: "center" }}>
        <button onClick={doStep} disabled={running} style={btn(running)}>Step</button>
        <button onClick={() => doBatch(50)} disabled={running} style={btn(running)}>+50</button>
        <button onClick={() => doBatch(500)} disabled={running} style={btn(running)}>+500</button>
        <button onClick={() => doBatch(2000)} disabled={running} style={btn(running)}>+2k</button>
        {running
          ? <button onClick={() => setRunning(false)} style={{...btn(false), background:"#3a1515", borderColor:"#5a2020"}}>■ Pause</button>
          : <button onClick={() => setRunning(true)} style={{...btn(false), background:"#153a15", borderColor:"#205a20"}}>▶ Run</button>}
        <button onClick={handleReset} style={btn(false)}>Reset</button>
        <div style={{ marginLeft: 8, display: "flex", alignItems: "center", gap: 4 }}>
          <span style={{ fontSize: 8, color: C.dim }}>speed</span>
          <input type="range" min="1" max="100" value={101-speed} onChange={e => setSpeed(101-+e.target.value)} style={{ width: 60, accentColor: C.accent }} />
        </div>
      </div>

      {/* Main grid */}
      <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1.5fr 0.8fr", gap: 8, marginBottom: 8 }}>
        <Panel title="Thinking Trace">
          {lastResult ? (
            <>
              <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 3 }}>
                {lastResult.isChain && <span style={{color:C.purple,fontSize:9,marginRight:4}}>CHAIN</span>}
                {lastResult.display}
              </div>
              <div style={{ marginBottom: 3 }}>
                <span style={{color:C.dim}}>predicted </span>
                <span style={{color: lastResult.correct ? C.green : C.red, fontWeight: 700}}>{lastResult.predicted}</span>
                {!lastResult.correct && <span style={{color:C.dim}}> (actual: <b style={{color:C.accent}}>{lastResult.actual}</b>)</span>}
              </div>
              <ThinkingViz thinking={snap.thinking} />
            </>
          ) : <div style={{color:C.dim}}>Press Step or Run</div>}
        </Panel>

        <Panel title="Accuracy (rolling 30)">
          {snap.accuracyHistory.length > 3 ? (
            <ResponsiveContainer width="100%" height={145}>
              <LineChart data={snap.accuracyHistory}>
                <CartesianGrid strokeDasharray="3 3" stroke={C.faint} />
                <XAxis dataKey="tick" tick={{fontSize:7,fill:C.dim}} stroke={C.faint} />
                <YAxis domain={[0,100]} tick={{fontSize:7,fill:C.dim}} stroke={C.faint} width={24} />
                <Tooltip contentStyle={{background:C.panel,border:`1px solid ${C.border}`,borderRadius:4,fontSize:9,color:C.text}} />
                <Line type="monotone" dataKey="accuracy" stroke={C.accent} strokeWidth={1.5} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : <div style={{height:145,display:"flex",alignItems:"center",justifyContent:"center",color:C.dim}}>Collecting data…</div>}
        </Panel>

        <Panel title="System">
          <div style={{ marginBottom: 6 }}>
            <div style={{fontSize:8,color:C.dim,marginBottom:2}}>surplus energy</div>
            <div style={{width:"100%",height:5,background:C.faint,borderRadius:3}}>
              <div style={{width:`${snap.surplusEnergy*100}%`,height:5,borderRadius:3,background:snap.surplusEnergy>0.6?C.green:snap.surplusEnergy>0.3?C.yellow:C.red}} />
            </div>
          </div>
          <div style={{fontSize:8,color:C.dim,marginBottom:3}}>matrices</div>
          <div style={{display:"flex",flexWrap:"wrap",gap:2}}>
            {Object.entries(snap.matrices).map(([id,m]) => <MatrixViz key={id} matrix={m} size={30} label={id} />)}
          </div>
        </Panel>
      </div>

      {/* Bottom row */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
        <Panel title="Recent Trials">
          <div style={{ maxHeight: 170, overflowY: "auto" }}>
            {snap.recentHistory.slice().reverse().map((h, i) => (
              <div key={i} style={{ display:"flex", gap:4, fontSize:9, padding:"2px 0", borderBottom:`1px solid ${C.faint}`, opacity:1-i*0.05 }}>
                <span style={{color:C.faint,width:28}}>#{h.tick}</span>
                <span style={{color:h.correct?C.green:C.red,width:10}}>{h.correct?"✓":"✗"}</span>
                {h.isChain && <span style={{color:C.purple,fontSize:7,marginRight:2}}>⛓</span>}
                <span style={{color:C.text}}>{h.display}</span>
                {!h.correct && <span style={{color:C.dim,marginLeft:"auto"}}>said {h.predicted}</span>}
              </div>
            ))}
          </div>
        </Panel>

        <Panel title={`Ghost Nodes (${snap.activeGhosts}/${snap.ghostCount})`}>
          <GhostViz sys={sysRef.current || {ghosts:new Map(),concepts:new Map()}} />
        </Panel>

        <Panel title={`Discoveries (${snap.totalDiscoveries})`}>
          <div style={{ maxHeight: 170, overflowY: "auto" }}>
            {snap.discoveries.slice().reverse().map((d, i) => (
              <div key={i} style={{ fontSize: 9, padding: "2px 0", borderBottom: `1px solid ${C.faint}` }}>
                <span style={{color:C.faint}}>t{d.tick} </span>
                <span style={{color: d.type === "phase" ? C.yellow : C.cyan}}>{d.msg}</span>
              </div>
            ))}
            {snap.discoveries.length === 0 && <div style={{color:C.dim,fontSize:9}}>Patterns emerge from observations…</div>}
          </div>
        </Panel>
      </div>
    </div>
  );
}
