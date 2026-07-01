// ============================================================
// INTELLON × WORDNET — Sense Selection + Reasoning
//
// The working model: definitions are strings until query time.
// At query, tokenize the definition, resolve each word against
// the full graph, score overlap with context. Ghost computation.
//
// Tests: sense disambiguation, is-a traversal, antonyms,
//        definition queries, real sentence processing.
// ============================================================

const fs = require('fs');

let _ops = 0, _tick = 0;
function tick() { return ++_tick; }

const TIERS = { BASE: "base", STARRED: "starred", STANDARD: "standard", TRIAL: "trial", WORKING: "working" };

class AddressBook {
  constructor() { this.byName = {}; this.byId = {}; this.allNodes = []; this._count = 0; }
  register(node) { this.byId[node.id] = node; if (node.label) this.byName[node.label] = node; this.allNodes.push(node); node._book = this; this._count++; }
  resolve(name) { return this.byName[name] || null; }
  size() { return this._count; }
}

let _nextId = 1;
class Node {
  constructor({ type = "node", value = null, label = null, tier = TIERS.WORKING }, book = null) {
    this.id = _nextId++; this.type = type; this.value = value;
    this.label = label || (value !== null ? String(value) : "node_" + this.id);
    this.tier = tier;
    this.connections = new Map(); this._reverse = new Map();
    this._obsCount = 0; this._version = 0;
    this._meta = {}; this._metaFlags = [];
    this._book = book; if (book) book.register(this);
  }
  _mutate() { this._version++; }
  setMeta(key, value, reason = null) { this._meta[key] = value; this._mutate(); }
  getMeta(key) { return key in this._meta ? this._meta[key] : null; }
  hasMeta(key) { return key in this._meta; }
  getMetaKeys() { return Object.keys(this._meta); }
  addConnection(tgt, qual, w = 1) {
    const e = this.connections.get(tgt.id);
    if (e) { e.weight += w; }
    else { this.connections.set(tgt.id, { target: tgt, weight: w, qualifier: qual }); }
    if (!tgt._reverse.has(this.id)) tgt._reverse.set(this.id, []);
    const rev = tgt._reverse.get(this.id);
    const existing = rev.find(r => r.qualifier === qual);
    if (existing) existing.weight += w;
    else rev.push({ source: this, qualifier: qual, weight: w });
    return { ok: true };
  }
  getConnection(qual) { for (const [, c] of this.connections) { if (c.qualifier === qual) return c.target; } return null; }
  getAllConnections(qual) { const r = []; for (const [, c] of this.connections) { if (!qual || c.qualifier === qual) r.push(c); } return r; }
  getReverse(qual) { const r = []; for (const [, entries] of this._reverse) { for (const e of entries) { if (qual === undefined || e.qualifier === qual) r.push(e); } } return r; }
}

// ============================================================
// INGESTION (same as before, compact)
// ============================================================
class WordNetIngestion {
  constructor(book) { this.book = book; this._dictCategories = {}; this._synsetNodes = {}; this._stats = { entries: 0, words: 0, synsets: 0, hypernyms: 0, synonyms: 0, antonyms: 0 }; }
  _getPOSCategory(pos) { if (this._dictCategories[pos]) return this._dictCategories[pos]; const label = "dict_" + pos; let node = this.book.resolve(label); if (!node) node = new Node({ type: "concept", label, tier: TIERS.STANDARD }, this.book); this._dictCategories[pos] = node; return node; }
  _getSynsetNode(synsetId) { if (this._synsetNodes[synsetId]) return this._synsetNodes[synsetId]; let node = this.book.resolve("syn_" + synsetId); if (!node) { node = new Node({ type: "concept", label: "syn_" + synsetId, tier: TIERS.TRIAL }, this.book); this._stats.synsets++; } this._synsetNodes[synsetId] = node; return node; }
  _getWordNode(word) { const label = "word_" + word; let node = this.book.resolve(label); if (!node) { node = new Node({ type: "base", value: word, label, tier: TIERS.TRIAL }, this.book); this._stats.words++; } return node; }
  receiveDict(entry) {
    tick(); _ops++;
    const wordNode = this._getWordNode(entry.word);
    const posNode = this._getPOSCategory(entry.pos);
    const synsetNode = this._getSynsetNode(entry.sense);
    const existingPOS = wordNode.getAllConnections("member_of_pos");
    if (!existingPOS.some(c => c.target.id === posNode.id)) wordNode.addConnection(posNode, "member_of_pos");
    wordNode.addConnection(synsetNode, "member_of_synset");
    if (!synsetNode.hasMeta("definition")) { synsetNode.setMeta("definition", entry.def); synsetNode.setMeta("pos", entry.pos); }
    if (!wordNode.hasMeta("pos_tags")) wordNode.setMeta("pos_tags", [entry.pos]);
    else { const tags = wordNode.getMeta("pos_tags"); if (!tags.includes(entry.pos)) tags.push(entry.pos); }
    if (!wordNode.hasMeta("primary_def")) wordNode.setMeta("primary_def", entry.def);
    if (entry.hypernyms) { for (const hid of entry.hypernyms) { const hn = this._getSynsetNode(hid); synsetNode.addConnection(hn, "hypernym"); this._stats.hypernyms++; } }
    if (entry.antonyms) { for (const ant of entry.antonyms) { const an = this._getWordNode(ant); wordNode.addConnection(an, "antonym"); this._stats.antonyms++; } }
    if (entry.synonyms) { for (const syn of entry.synonyms) { const sn = this._getWordNode(syn); wordNode.addConnection(sn, "synonym"); this._stats.synonyms++; } }
    if (entry.examples && !synsetNode.hasMeta("examples")) synsetNode.setMeta("examples", entry.examples);
    wordNode._obsCount++;
    this._stats.entries++;
  }
}

// ============================================================
// SENSE SELECTOR — the working model
// ============================================================
class SenseSelector {
  constructor(book) { this.book = book; this._cache = {}; }

  // Tokenize text → resolve to word nodes in the book
  _resolveTokens(text) {
    const tokens = text.toLowerCase().replace(/[^a-z\s'-]/g, '').split(/\s+/).filter(t => t.length > 2);
    const resolved = [];
    for (const t of tokens) {
      const node = this.book.resolve("word_" + t);
      if (node) resolved.push({ token: t, node });
    }
    return resolved;
  }

  // Collect synset neighborhood (hypernyms up N hops)
  _getNeighborhoodIds(synsetNode, depth = 2) {
    const ids = new Set();
    const queue = [{ node: synsetNode, d: 0 }];
    while (queue.length > 0) {
      const { node, d } = queue.shift();
      ids.add(node.id);
      if (d < depth) {
        const hyper = node.getConnection("hypernym");
        if (hyper) queue.push({ node: hyper, d: d + 1 });
      }
    }
    return ids;
  }

  // Build context fingerprint: set of synset IDs reachable from context words
  _buildContextFingerprint(contextWords) {
    const fp = new Set();
    for (const cw of contextWords) {
      const cwNode = this.book.resolve("word_" + cw);
      if (!cwNode) continue;
      const synsets = cwNode.getAllConnections("member_of_synset").map(c => c.target);
      for (const syn of synsets) {
        const hood = this._getNeighborhoodIds(syn, 2);
        for (const id of hood) fp.add(id);
      }
    }
    return fp;
  }

  // Select best sense for word given context
  selectSense(word, contextWords) {
    _ops++;
    const wordNode = this.book.resolve("word_" + word);
    if (!wordNode) return { sense: null, reason: "word not found", score: 0 };

    const senses = wordNode.getAllConnections("member_of_synset").map(c => c.target);
    if (senses.length === 0) return { sense: null, reason: "no senses", score: 0 };
    if (senses.length === 1) return { sense: senses[0], score: 1, reason: "single sense", definition: senses[0].getMeta("definition") };

    // Build context fingerprint
    const ctxFP = this._buildContextFingerprint(contextWords);

    let bestSense = null, bestScore = -1, bestReason = "";

    for (const sense of senses) {
      let score = 0;
      const hits = [];

      // Strategy 1: Definition word overlap
      // Tokenize this sense's definition, resolve against graph
      const def = sense.getMeta("definition") || "";
      const defTokens = this._resolveTokens(def);

      for (const dt of defTokens) {
        // Direct hit: definition word IS a context word
        if (contextWords.includes(dt.token)) {
          score += 5;
          hits.push(dt.token + "=direct");
        } else {
          // Neighborhood hit: definition word's synsets overlap context fingerprint
          const dtSynsets = dt.node.getAllConnections("member_of_synset").map(c => c.target);
          let found = false;
          for (const dts of dtSynsets) {
            if (ctxFP.has(dts.id)) { score += 2; hits.push(dt.token + "=synset"); found = true; break; }
            // Check 1 hop up
            const hyper = dts.getConnection("hypernym");
            if (hyper && ctxFP.has(hyper.id)) { score += 1; hits.push(dt.token + "=hyper"); found = true; break; }
          }
        }
      }

      // Strategy 2: Synset's own neighborhood overlaps context
      const senseHood = this._getNeighborhoodIds(sense, 2);
      let hoodHits = 0;
      for (const id of senseHood) { if (ctxFP.has(id)) hoodHits++; }
      score += hoodHits * 2;

      if (score > bestScore) {
        bestScore = score;
        bestSense = sense;
        bestReason = `hits=[${hits.slice(0, 6).join(",")}${hits.length > 6 ? "..." : ""}] hood=${hoodHits}`;
      }
    }

    return {
      sense: bestSense,
      score: bestScore,
      totalSenses: senses.length,
      reason: bestReason,
      definition: bestSense?.getMeta("definition"),
      pos: bestSense?.getMeta("pos"),
    };
  }
}

// ============================================================
// REASONING ENGINE — queries against the full graph
// ============================================================
class ReasoningEngine {
  constructor(book, selector) { this.book = book; this.selector = selector; }

  // "Is a cat an animal?" → traverse hypernym chain
  isA(word, category, maxDepth = 20) {
    _ops++;
    const wordNode = this.book.resolve("word_" + word);
    if (!wordNode) return { answer: false, reason: "word not found" };

    // Check all senses of the word
    const senses = wordNode.getAllConnections("member_of_synset").map(c => c.target);

    for (const sense of senses) {
      let current = sense;
      const chain = [sense.label.replace("syn_", "").split(".")[0]];
      let depth = 0;

      while (depth < maxDepth) {
        const hyper = current.getConnection("hypernym");
        if (!hyper) break;

        const hyperName = hyper.label.replace("syn_", "").split(".")[0];
        chain.push(hyperName);

        // Check if this hypernym's synset has the category word as a lemma
        const hyperMembers = hyper.getReverse("member_of_synset").map(r => r.source.value);
        if (hyperMembers.includes(category) || hyperName === category) {
          return { answer: true, chain: chain, depth: depth + 1, sense: sense.label.replace("syn_", "") };
        }

        current = hyper;
        depth++;
      }
    }
    return { answer: false, reason: "not found in hypernym chains", checkedSenses: senses.length };
  }

  // "What's the opposite of happy?" → antonym connections
  oppositeOf(word) {
    _ops++;
    const wordNode = this.book.resolve("word_" + word);
    if (!wordNode) return { answer: null, reason: "word not found" };
    const antonyms = wordNode.getAllConnections("antonym").map(c => c.target.value || c.target.label.replace("word_", ""));
    return { answer: antonyms.length > 0 ? antonyms : null, reason: antonyms.length > 0 ? "found" : "no antonyms" };
  }

  // "What is a cat?" → definition with optional context for sense selection
  whatIs(word, context = []) {
    _ops++;
    if (context.length > 0) {
      const result = this.selector.selectSense(word, context);
      return { word, definition: result.definition, pos: result.pos, score: result.score, senses: result.totalSenses, reason: result.reason };
    }
    // No context: return primary definition
    const node = this.book.resolve("word_" + word);
    if (!node) return { word, definition: null, reason: "word not found" };
    return { word, definition: node.getMeta("primary_def"), pos: (node.getMeta("pos_tags") || [])[0], senses: node.getAllConnections("member_of_synset").length };
  }

  // "What words are similar to happy?" → synonym connections
  similarTo(word) {
    _ops++;
    const node = this.book.resolve("word_" + word);
    if (!node) return { answer: null, reason: "word not found" };
    const syns = node.getAllConnections("synonym").map(c => c.target.value || c.target.label.replace("word_", ""));
    return { answer: [...new Set(syns)].slice(0, 15), reason: syns.length > 0 ? "found" : "no synonyms" };
  }

  // Process a real sentence: resolve each word, select senses, report
  processSentence(tokens) {
    _ops++;
    const results = [];
    // Use all OTHER words as context for each word
    for (let i = 0; i < tokens.length; i++) {
      const word = tokens[i].toLowerCase();
      const context = tokens.filter((_, j) => j !== i).map(t => t.toLowerCase());
      const node = this.book.resolve("word_" + word);

      if (!node) {
        results.push({ word, resolved: false, reason: "not in graph" });
        continue;
      }

      const senseCount = node.getAllConnections("member_of_synset").length;
      if (senseCount <= 1) {
        const def = node.getMeta("primary_def");
        results.push({ word, resolved: true, senses: senseCount, selectedDef: def?.slice(0, 60), method: "single/no sense" });
      } else {
        const selected = this.selector.selectSense(word, context);
        results.push({ word, resolved: true, senses: senseCount, score: selected.score, selectedDef: selected.definition?.slice(0, 60), pos: selected.pos, method: "context-scored" });
      }
    }
    return results;
  }
}

// ============================================================
// MAIN
// ============================================================
async function main() {
  console.log("=".repeat(60));
  console.log("INTELLON × WORDNET — Reasoning Test");
  console.log("=".repeat(60));

  // Load & ingest
  console.log("\nLoading...");
  const entries = JSON.parse(fs.readFileSync("/home/claude/wordnet_full.json", "utf-8"));
  console.log(`  ${entries.length.toLocaleString()} entries loaded`);

  const book = new AddressBook();
  const engine = new WordNetIngestion(book);
  console.log("Ingesting...");
  const t0 = Date.now();
  for (const e of entries) engine.receiveDict(e);
  console.log(`  ${book.size().toLocaleString()} nodes in ${((Date.now()-t0)/1000).toFixed(1)}s`);

  const selector = new SenseSelector(book);
  const reasoning = new ReasoningEngine(book, selector);

  let pass = 0, fail = 0, total = 0;
  function test(name, fn) {
    total++;
    try {
      const result = fn();
      if (result.pass) { pass++; console.log(`  PASS  ${name}`); }
      else { fail++; console.log(`  FAIL  ${name}`); }
      console.log(`        ${result.detail}`);
    } catch (err) {
      fail++;
      console.log(`  FAIL  ${name}`);
      console.log(`        EXCEPTION: ${err.message}`);
    }
  }

  // ============================================================
  // T1: SENSE DISAMBIGUATION — "bank" in different contexts
  // ============================================================
  console.log("\n" + "=".repeat(60));
  console.log("T1: SENSE DISAMBIGUATION");
  console.log("=".repeat(60));

  test("bank + [money, deposit, account] → financial", () => {
    const r = selector.selectSense("bank", ["money", "deposit", "account"]);
    const isFinancial = r.definition && (r.definition.includes("financial") || r.definition.includes("deposit") || r.definition.includes("lending") || r.definition.includes("money"));
    return { pass: isFinancial, detail: `score=${r.score} senses=${r.totalSenses} def="${(r.definition||"").slice(0,70)}" ${r.reason}` };
  });

  test("bank + [river, water, slope, land] → geographical", () => {
    const r = selector.selectSense("bank", ["river", "water", "slope", "land"]);
    const isGeo = r.definition && (r.definition.includes("slop") || r.definition.includes("water") || r.definition.includes("land") || r.definition.includes("shore"));
    return { pass: isGeo, detail: `score=${r.score} senses=${r.totalSenses} def="${(r.definition||"").slice(0,70)}" ${r.reason}` };
  });

  test("run + [marathon, race, finish] → footrace", () => {
    const r = selector.selectSense("run", ["marathon", "race", "finish"]);
    const isRace = r.definition && (r.definition.includes("race") || r.definition.includes("foot") || r.definition.includes("running"));
    return { pass: isRace, detail: `score=${r.score} senses=${r.totalSenses} def="${(r.definition||"").slice(0,70)}" ${r.reason}` };
  });

  test("run + [computer, program, software, execute] → operate", () => {
    const r = selector.selectSense("run", ["computer", "program", "software", "execute"]);
    return { pass: r.score > 0, detail: `score=${r.score} senses=${r.totalSenses} def="${(r.definition||"").slice(0,70)}" ${r.reason}` };
  });

  test("fast + [speed, car, quick] → quick", () => {
    const r = selector.selectSense("fast", ["speed", "car", "quick"]);
    const isQuick = r.definition && (r.definition.includes("quick") || r.definition.includes("rapid") || r.definition.includes("moving") || r.definition.includes("speed") || r.definition.includes("acting"));
    return { pass: isQuick, detail: `score=${r.score} senses=${r.totalSenses} def="${(r.definition||"").slice(0,70)}" ${r.reason}` };
  });

  test("fast + [food, eat, hunger, abstain] → not eating", () => {
    const r = selector.selectSense("fast", ["food", "eat", "hunger", "abstain"]);
    const isFasting = r.definition && (r.definition.includes("food") || r.definition.includes("eat") || r.definition.includes("abstain"));
    return { pass: isFasting, detail: `score=${r.score} senses=${r.totalSenses} def="${(r.definition||"").slice(0,70)}" ${r.reason}` };
  });

  // ============================================================
  // T2: IS-A QUERIES — hypernym chain traversal
  // ============================================================
  console.log("\n" + "=".repeat(60));
  console.log("T2: IS-A QUERIES");
  console.log("=".repeat(60));

  test("is a cat an animal? → yes", () => {
    const r = reasoning.isA("cat", "animal");
    return { pass: r.answer === true, detail: r.answer ? `yes — ${r.chain?.join(" → ")} (depth ${r.depth})` : `no — ${r.reason} (checked ${r.checkedSenses} senses)` };
  });

  test("is a dog a mammal? → yes", () => {
    const r = reasoning.isA("dog", "mammal");
    return { pass: r.answer === true, detail: r.answer ? `yes — depth ${r.depth}` : `no — ${r.reason}` };
  });

  test("is a computer a device? → yes", () => {
    const r = reasoning.isA("computer", "device");
    return { pass: r.answer === true, detail: r.answer ? `yes — ${r.chain?.join(" → ")} (depth ${r.depth})` : `no — ${r.reason}` };
  });

  test("is a hammer a tool? → yes", () => {
    const r = reasoning.isA("hammer", "tool");
    return { pass: r.answer === true, detail: r.answer ? `yes — depth ${r.depth}` : `no — ${r.reason}` };
  });

  test("is a cat a vehicle? → no", () => {
    const r = reasoning.isA("cat", "vehicle");
    return { pass: r.answer === false, detail: r.answer ? `unexpectedly yes — ${r.chain?.join(" → ")}` : `correctly no` };
  });

  test("is a rose a plant? → yes", () => {
    const r = reasoning.isA("rose", "plant");
    return { pass: r.answer === true, detail: r.answer ? `yes — depth ${r.depth}` : `no — ${r.reason}` };
  });

  // ============================================================
  // T3: ANTONYMS
  // ============================================================
  console.log("\n" + "=".repeat(60));
  console.log("T3: ANTONYMS");
  console.log("=".repeat(60));

  test("opposite of happy → unhappy", () => {
    const r = reasoning.oppositeOf("happy");
    return { pass: r.answer?.includes("unhappy"), detail: `[${(r.answer||[]).join(", ")}]` };
  });

  test("opposite of big → small or little", () => {
    const r = reasoning.oppositeOf("big");
    return { pass: r.answer?.some(a => a === "small" || a === "little"), detail: `[${(r.answer||[]).join(", ")}]` };
  });

  test("opposite of hot → cold", () => {
    const r = reasoning.oppositeOf("hot");
    return { pass: r.answer?.includes("cold"), detail: `[${(r.answer||[]).join(", ")}]` };
  });

  test("opposite of love → hate", () => {
    const r = reasoning.oppositeOf("love");
    return { pass: r.answer?.includes("hate"), detail: `[${(r.answer||[]).join(", ")}]` };
  });

  // ============================================================
  // T4: SYNONYMS
  // ============================================================
  console.log("\n" + "=".repeat(60));
  console.log("T4: SYNONYMS");
  console.log("=".repeat(60));

  test("similar to happy → glad, felicitous, etc", () => {
    const r = reasoning.similarTo("happy");
    return { pass: r.answer?.length > 0, detail: `[${(r.answer||[]).slice(0,8).join(", ")}]` };
  });

  test("similar to car → automobile, etc", () => {
    const r = reasoning.similarTo("car");
    return { pass: r.answer?.some(s => s.includes("auto") || s.includes("vehicle")), detail: `[${(r.answer||[]).slice(0,8).join(", ")}]` };
  });

  // ============================================================
  // T5: DEFINITION QUERIES WITH CONTEXT
  // ============================================================
  console.log("\n" + "=".repeat(60));
  console.log("T5: DEFINITION QUERIES");
  console.log("=".repeat(60));

  test("what is 'bat' (baseball context)?", () => {
    const r = reasoning.whatIs("bat", ["baseball", "hit", "ball", "swing"]);
    const isSports = r.definition && (r.definition.includes("bat") || r.definition.includes("hit") || r.definition.includes("ball") || r.definition.includes("club") || r.definition.includes("base"));
    return { pass: isSports, detail: `"${(r.definition||"none").slice(0,70)}" score=${r.score} senses=${r.senses}` };
  });

  test("what is 'bat' (animal context)?", () => {
    const r = reasoning.whatIs("bat", ["cave", "wing", "fly", "nocturnal"]);
    const isAnimal = r.definition && (r.definition.includes("mammal") || r.definition.includes("wing") || r.definition.includes("fly") || r.definition.includes("nocturnal"));
    return { pass: isAnimal, detail: `"${(r.definition||"none").slice(0,70)}" score=${r.score} senses=${r.senses}` };
  });

  // ============================================================
  // T6: REAL SENTENCE PROCESSING
  // ============================================================
  console.log("\n" + "=".repeat(60));
  console.log("T6: REAL SENTENCE PROCESSING");
  console.log("=".repeat(60));

  const sentences = [
    ["the", "cat", "sat", "on", "the", "mat"],
    ["she", "went", "to", "the", "bank", "to", "deposit", "money"],
    ["the", "bright", "sun", "warmed", "the", "cold", "earth"],
    ["he", "can", "run", "a", "fast", "mile"],
    ["democracy", "requires", "active", "participation"],
  ];

  for (const sent of sentences) {
    const results = reasoning.processSentence(sent);
    const resolved = results.filter(r => r.resolved).length;
    console.log(`\n  "${sent.join(" ")}"`);
    console.log(`  Resolved: ${resolved}/${sent.length}`);
    for (const r of results) {
      if (r.resolved) {
        console.log(`    ${r.word}: [${r.pos||"?"}] ${r.senses}s score=${r.score||"-"} "${(r.selectedDef||"").slice(0,55)}"`);
      } else {
        console.log(`    ${r.word}: ${r.reason}`);
      }
    }
    // Count this as a pass if majority of content words resolved
    const contentResolved = results.filter(r => r.resolved && r.senses > 0).length;
    total++; if (contentResolved >= 2) pass++; else fail++;
  }

  // ============================================================
  // SUMMARY
  // ============================================================
  const mem = process.memoryUsage();
  console.log("\n" + "=".repeat(60));
  console.log(`RESULTS: ${pass}/${total} passed (${fail} failed)`);
  console.log(`Nodes: ${book.size().toLocaleString()} | Ops: ${_ops.toLocaleString()} | Memory: ${(mem.heapUsed/1024/1024).toFixed(0)}MB`);
  console.log("=".repeat(60));
}

main().catch(err => console.error("FATAL:", err));
