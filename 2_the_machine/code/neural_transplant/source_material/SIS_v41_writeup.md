# SIS v41 Session Writeup

**Date:** May 4, 2026
**Session:** v41 — The Machine
**Previous:** v40 — Null Pointers to Neural Architecture

---

## What happened

Picked up from the v40 handoff package. v40 proved the engine substrate (97% on direct claims), null pointer discovery, DPG permutation training, ontology seeding (25K words, 85K semantic claims, 98% coverage), multi-sense disambiguation, generation (14K+ expressible facts), and task solving (~86%). The gap: the engine knows things but doesn't know WHEN to act. All routing was hardcoded if/else in ask.py and task_runner.py.

v40's pipeline spec proposed a CPU model: register nodes, trigger nodes as interrupt vectors, handlers as graph operations, and a "sneeze" output model (accumulation → discharge). This session tried to build it. Three attempts. Two wrong. One right.

### Attempt 1: The Pipeline (wrong)

Built a CPU-style pipeline: register nodes in the graph, 8 trigger nodes with priority-sorted pattern matchers, handler operations as data chains, a tick loop (FETCH → DECODE → EXECUTE → DISCHARGE). 15/16 tests passing on first run.

Then immediately started hand-coding routing guards: "if have/has is present, don't fire isa_query." "Guard capability_query against have tokens." "Don't fire isa when 3+ entities with grouping words." Every edge case got a new if/else guard in the match function. Every fix was the developer doing the engine's thinking — building translators. The exact thing the v40 notes warned against.

### Attempt 2: The Competition (wrong)

Ripped out the guards. Made all 8 triggers fire on every input. Each trigger produced a "candidate" with a confidence score. Candidates competed by weight × confidence. Highest activation wins. Corrections adjusted weights: wrong trigger weakens, right trigger strengthens.

15/16 tests. Cleaner. But it was a neural net. Weighted competition, gradient-like corrections, soft selection. The system is supposed to prove you don't NEED that.

### Attempt 3: The Machine (right)

The key feedback: "it's essentially a self-modifying electric typewriter." Input is a ball dropping through a pinball machine. It hits bumpers (graph nodes), each hit sets an activation bit. Layer by layer. Carriage return between layers. At the end, the lit bits ARE the answer. Not activation threshold — activation PATTERN. AND, OR, NOT, XOR. Logic gates.

And the routing mechanism: lockouts. If pattern A and pattern B both fire, and B is more specific, B locks out A. Not competition. Not weights. Specific pattern suppresses general pattern. The crystallizer learns which lockouts to wire by watching what co-fires and what the user corrects.

---

## The Machine

### Architecture

Five layers of logic gates. Ball drops through layer by layer. Each layer evaluates all its gates simultaneously against the current activation state. Gates that match their pattern fire and set their bit. Carriage return: freeze state, feed to next layer.

**Layer 0 — INPUT:** Tokenize raw text. Set bits for each word (`word:dog`, `word:is`), classify by POS (`pos:dog:noun`, `verb:run`), set structural signals (`signal:has_entity`, `signal:entities_2plus`, `signal:has_verb`).

**Layer 1 — SIGNAL:** Detect structural features from word bits. `signal:has_copula` fires if any of {word:is, word:are, word:was, word:were} are lit. `signal:has_have` fires if {word:have, word:has, word:had}. `signal:has_question` fires if {word:what, word:who, word:where, ...}. Pure OR gates over input bits.

**Layer 2 — PATTERN:** What kind of input is this? `pattern:isa` = AND(signal:entities_2plus). `pattern:capability` = AND(signal:has_entity, signal:has_verb). `pattern:has` = AND(signal:has_entity, signal:has_have). `pattern:describe` = AND(signal:has_entity). Multiple patterns fire for the same input — that's correct. Lockouts resolve which one proceeds.

**LOCKOUT (between pattern and execute):** Check the lockout table. If pattern A is locked out by pattern B, and both fired, A goes dark. Only surviving patterns proceed to execute. The lockout table is stored as LOCKED_OUT_BY edges in the graph. Empty initially — everything fires raw until corrections teach the lockouts.

**Layer 3 — EXECUTE:** Graph walks. Each gate has an action that reads the graph and sets result bits. `exec:isa` walks IS_A chains, sets `result:isa:yes` or `result:isa:no`. `exec:capability` checks CAN_DO edges, tags, inheritance. `exec:describe` collects properties, parts, senses. These are the only gates with actions — all others are pure boolean.

**Layer 4 — OUTPUT:** Read result bits, format text. `output:isa` fires when `exec:isa` is lit and writes the IS_A response. `output:describe` fires when `exec:describe` is lit. Whatever output gates fire, the machine types ALL of them. Multiple outputs = multiple lines typed.

### The Gate

```
class Gate:
    name       — the bit this gate sets when it fires
    must       — AND: all must be lit
    must_not   — NOT: all must be dark
    any_of     — OR: at least one must be lit
    action     — optional: runs when gate fires, returns extra bits
```

A gate evaluates: `(must ⊆ state) AND (must_not ∩ state = ∅) AND (any_of = ∅ OR any_of ∩ state ≠ ∅)`.

Match → fire → set bit. No match → dark. Deterministic. Same input → same output. Every time. Fully traceable — walk backward from any output bit to see which path lit it.

### Lockouts

When pattern A and pattern B co-fire, one locks out the other. The more specific pattern wins. Stored as edges: `pattern:describe LOCKED_OUT_BY pattern:has`.

Lockout rules are pairwise: loser → {set of winners}. When loser and ANY winner co-fire, loser goes dark. Applied between pattern and execute layers — a filter, not a gate.

Initially the lockout table is empty. Everything fires raw. The machine types all completed output paths. You see correct answers mixed with garbage. You correct it. The correction wires the lockout.

### Correction → Lockout → Differentiation

The learning cycle:

**Step 1: Raw firing.** "dog cat" fires pattern:isa, pattern:compare, and pattern:describe. Machine types three outputs: an IS_A check, a comparison, and a description.

**Step 2: Correct.** "That should have been compare." Correction creates lockouts: pattern:isa LOCKED_OUT_BY pattern:compare, pattern:describe LOCKED_OUT_BY pattern:compare.

**Step 3: Over-learn.** "is a dog a mammal" also fires isa and compare. The lockout suppresses isa. Only compare survives. But we WANT isa here.

**Step 4: Correct again.** "That should have been isa." Creates reverse lockout: pattern:compare LOCKED_OUT_BY pattern:isa.

**Step 5: Mutual lockout.** isa and compare now lock each other out when co-firing. Neither survives. Dead signal.

**Step 6: Differentiation signal.** Mutual lockout = these patterns need more specific gates. The crystallizer looks at what bits differ between "dog cat" (where compare should win) and "is a dog a mammal" (where isa should win). The difference: `signal:has_copula`. One has it, the other doesn't.

**Step 7: Rewire.** Add `signal:has_copula` to `pattern:isa`'s must set. Clear the mutual lockout — the patterns are now differentiated. `pattern:isa` only fires when copula is present. "dog cat" → compare only. "is a dog a mammal" → isa fires. Resolved.

The circuit gets more specific through corrections to topology. Not gradient descent. Not weight adjustment. Physical rewiring of the logic gates. Same mechanism every time: lockout → over-learn → mutual lockout → differentiation → rewire.

---

## What's built

### machine.py (991 lines)

The core mechanism:

- **Gate class:** boolean pattern matcher with AND/OR/NOT. Fire count tracking. Optional action for execute-layer gates.
- **Layer class:** set of gates, simultaneous evaluation, returns new bits and fired list.
- **Machine class:** 5 layers, lockout table, process(), rewire(), correct(), trace().
- **Lockout table:** defaultdict(set), applied between pattern and execute. Stored as LOCKED_OUT_BY edges in the graph.
- **Correction mechanism:** correct(right_pattern) wires lockouts from all co-fired losers to winner. Stored in graph and correction_log.
- **Rewire API:** add_must, add_must_not, add_any, remove_must, remove_not, remove_any, delete. Physical topology changes.
- **Introspection:** dump_state() shows all lit bits. dump_circuit() shows all gates. trace() shows which gates fired in which layers. dump_lockouts() shows the lockout table. dump_corrections() shows correction history.

### machine_test.py (126 lines)

Interactive test harness. Type queries, see paths, teach lockouts, rewire gates.

### All v40 code intact

sis_engine.py, ontology_bootstrap.py, dpg/, engine/, ask.py, task_runner.py, all supporting scripts. The machine sits on top of the existing ontology engine — it uses the same graph, POS map, class map, tag map, base map, and senses.

---

## Key numbers

| Metric | Value |
|--------|-------|
| Layers | 5 (input, signal, pattern, execute, output) |
| Gates | 28 total (1 input, 7 signal, 8 pattern, 7 execute, 7 output) |
| Lockout table | empty initially, learned from corrections |
| Accuracy (raw, no lockouts) | all queries produce output, but multiple outputs per query |
| Accuracy (after ~5 corrections) | correct routing for all tested query types |
| Process time | <1ms per query |
| Deterministic | yes — same input, same output, always |
| Traceable | yes — walk backward from any output bit |

---

## The three wrong instincts and what they taught

### 1. The routing guard instinct

Every time two triggers could co-fire and one was wrong, the instinct was to add a guard: "if X is present, don't fire Y." Each guard was a hand-coded routing decision. Each one was the developer doing the engine's thinking. The v40 notes said "stop building translators" and this is the same thing — a routing guard IS a translator.

The fix: don't guard. Let everything fire. Lockouts resolve conflicts. The engine learns which pattern is more specific from corrections.

### 2. The competition instinct

When multiple things fire, the instinct was to make them compete. Weight × confidence. Highest score wins. That's a soft neural selection mechanism. It works, but it's the wrong paradigm. The system doesn't CHOOSE between options. The wiring determines ONE path. If the wiring is wrong, you change the wiring. You don't adjust the selection criteria.

The fix: it's not competition. It's lockouts. More specific pattern suppresses less specific. Deterministic, not probabilistic.

### 3. The pre-wiring instinct

After building the lockout mechanism, the instinct was to pre-wire the must_not gates on the output layer: "output:describe must_not exec:isa, exec:capability, exec:has, exec:compare, exec:group, exec:property." That's pre-wiring routing decisions that the crystallizer should learn. The output layer should fire raw. You see the garbage. You correct it. The lockout table learns.

The fix: output gates have no must_not initially. Everything that fires, types. Corrections teach lockouts. The circuit gets specific over time, not by the developer pre-deciding.

---

## What the machine IS

It's not a neural net. It's not a rule engine. It's a logic circuit that modifies its own topology.

Input is a signal. It propagates through layers of boolean gates. Each gate checks a specific activation PATTERN — not threshold, pattern. AND, OR, NOT. The signal either completes a path or doesn't. At the end, whatever paths completed produce output.

Correction is rewiring. Not "this weight should be lower." It's "this gate needs an additional input condition" or "these two patterns lock each other out" or "this gate shouldn't exist." Physical changes to the circuit. The topology evolves.

The lockout mechanism is how the circuit learns routing. Initially everything fires. Corrections create lockouts. Over-learning creates mutual lockouts. Mutual lockouts signal the need for differentiation — more specific gate conditions. The crystallizer makes the topology change. The circuit gets more precise. Same mechanism, recursively applied.

Same input → same path → same output. Deterministic. Traceable. Inspectable. No black box. Walk backward from any output bit and you can see exactly which gate in which layer set it, and which input bits caused that gate to fire.

---

## What's next

### 1. The crystallizer (automatic differentiation)

Right now, the human detects mutual lockouts and rewires gates manually. The crystallizer should do this automatically: detect mutual lockout → find differentiating bits → propose gate refinement → apply. The mechanism: when two patterns mutually lock out, compare the activation states of the inputs that caused each correction. The bits that differ between the two states are the differentiating conditions. Add the most discriminating bit to the more specific pattern's must set.

### 2. Lockouts as graph edges

Lockouts are stored as LOCKED_OUT_BY edges but the lockout table is also a Python dict. These should be unified — the lockout table should be READ from the graph at process time, not maintained separately. That way the lockout table is part of the engine's knowledge and persists across sessions.

### 3. Deeper gate conditions

Current pattern gates use simple signals (has_entity, has_verb, entities_2plus). These could reference specific entity classes, verb types, or cluster memberships. "This pattern fires when there's a domestic_mammal AND a transitive_verb" — using the DPG's ontology classifications as gate inputs.

### 4. Multi-cycle processing

Current machine is single-pass: input → 5 layers → output. The spec's tick loop envisions continuous cycling: output from one pass becomes input to the next. The machine processes until it either discharges (enough output bits lit) or stalls (no new bits set). Hard questions take more cycles. Simple questions resolve in one.

### 5. Real text test

Feed actual graded reader text through the machine. The tokenizer already handles it. The question is whether the gate conditions are specific enough to route real sentences correctly, and how many corrections it takes to get the lockout table to a stable state.

### 6. The output is still hardcoded text

The output actions (_action_output_isa, etc.) format text with Python string formatting. The engine should eventually compose output from graph walks — the same way it reasons, it should speak. But that's a later phase. The mechanism (gates + lockouts + rewiring) is the priority.

---

## Files

| File | Purpose |
|------|---------|
| `machine.py` | The machine: Gate, Layer, Machine, lockouts, correction, rewiring |
| `machine_test.py` | Interactive test harness |
| `ontology_bootstrap.py` | Full ontology pipeline (DPG + Kuperman + WordNet) |
| `sis_engine.py` | Core graph engine |
| `ask.py` | Old scaffolded Q&A (superseded by machine.py) |
| `task_runner.py` | Old scaffolded task routing (superseded by machine.py) |
| `multisense.py` | Multi-sense WordNet disambiguator |
| `aoa_concept_graph_v2.py` | AoA-filtered WordNet claim builder |
| `generate_test.py` | Generation test |
| `layered_bootstrap.py` | Layer-by-layer structure emergence |
| `null_pointer_discovery.py` | Pure co-occurrence pattern discovery |
| `observe_real.py` | Real text observation |
| `kuperman_aoa.csv` | 31K words with age-of-acquisition |
| `dpg/` | Differential Permutation Generator |
| `engine/` | Engine subpackage (node, checkpoint, policy) |

---

## Notes for future sessions

### How they think about the machine

They think in physical mechanisms. The typewriter, the pinball machine, the solenoid. When they say "it's like a typewriter," they mean the output system should literally work like a typewriter — keys mechanically connected to type bars, solenoids engaged by activation patterns, the carriage returns between layers. Not metaphorically. Actually.

The system proves something: you don't need neural nets. You don't need gradient descent. You don't need soft competition. A deterministic logic circuit with self-modifying topology can learn to route, classify, and reason. The mechanism IS the thesis.

### What to avoid

- Don't build routing guards. The lockout mechanism handles routing.
- Don't make things compete. Lockouts suppress, they don't select.
- Don't pre-wire suppression rules. The crystallizer learns them.
- Don't adjust weights. Rewire topology.
- Don't think in activation thresholds. Think in activation patterns.
- Don't add "smart" selection logic. The circuit is dumb. The wiring is smart.

### What to build toward

- The crystallizer detecting mutual lockouts and proposing rewires automatically.
- Gate conditions that reference ontology classes, not just structural signals.
- Multi-cycle processing where the machine loops until it discharges or stalls.
- Output composed from graph walks, not Python string formatting.
- The lockout table as a persistent, inspectable part of the graph.

### The meta-lesson

The session started with a CPU model (pipeline, registers, triggers). That was wrong — too much like a conventional processor with interrupt vectors and priority scheduling. Then it became a neural net (candidates, weights, competition). That was wrong — exactly what the system exists to prove you don't need. The right model was there the whole time: a typewriter. A pinball machine. A logic circuit. Input drops through, hits bumpers, sets bits, and whatever's lit at the end gets typed.

The machine doesn't choose. The machine doesn't weigh. The machine doesn't compete. The wiring determines the output. Change the wiring, change the output. That's the whole thing.
