# Intellon — Development History & Discovery Timeline

**Scope:** The "Intellon" era of the AI research, roughly **March 22 → April 11, 2026**, ending when the project was renamed/redesigned into **SIS (Structural Intelligence System)** on April 12, 2026. SIS and the later **Isaac** project are out of scope here.

**How this was reconstructed:** Chat logs were not available. This timeline was rebuilt from the on-disk artifacts themselves — file contents plus modification timestamps — across the `intellon/` folder and `june_17_isaac_research/` archive (which holds the dated handoff documents that narrate each session). Every date below is a file modification date. Test counts, findings (F#), and decisions (D#) are quoted from the handoff docs. Where a result is only *asserted* in a document and is **not** backed by runnable code in the corpus, it is flagged as such.

> **Caveat:** This is a faithful recounting of what the files contain — not an independent verification that each claimed result is correct. A few numbers (notably MNIST 99.8%) are claims with no surviving harness; these are marked.

---

## At a glance — the version arc

| Date | Phase / Version | Tests | Headline |
|------|-----------------|-------|----------|
| Mar 22 | Persistence theory paper | — | Theoretical root: intelligence = persistence, not optimization |
| Mar 25–27 | Matrix/lens benchmarks | — | Iris/Wine/synthetic-digit classifiers; MNIST dataset acquired |
| Mar 30 | `unified_spec_v2` + `v3.jsx` | — | rootC operation, fixed lens, ghost nodes, ensembles; MNIST 99.8% **claimed** |
| Apr 1 | **Pivot → node architecture** (a/b/c series) | 57 (a.5) | Symbolic node/tool-discovery engine; holonic rebuild |
| Apr 1–3 | d-series | 171 total | Trust gradient; 100% coverage; 58/60 tools; 1M/1M predict/explain |
| Apr 2–3 | e-series | 39 (e.9) | Language: reading comprehension over 51K sentences, WordNet |
| Apr 4 | xb.4 | 210 | JS engine: Layer-0 substrate, questions, learning loop, self-exploration |
| Apr 5 | xb.5 | 343 | Gather/relate, macros, operational cycle, self-test, comprehension |
| Apr 5 | xb.6 | 385 | Ruminate (self-directed discovery), compose, WordNet, Node.js |
| Apr 5–6 | xb.7 → xb.8 | 457 | Unified pipeline; SQLite storage; sessions; hypotheses; provenance |
| Apr 7 | xb.8 (1) | 457 | Six thinking modes; 295K-node live DB; "synthesize" gap identified |
| Apr 8–11 | **v4 Python rewrite** (sessions 1–5) | 11 | Node/Register/Librarian; LMDB; "differentiation is the only operation" |
| Apr 12 | → **SIS** (`concept_proposal.md`) | — | Renamed/redesigned; Intellon era ends |

---

## Two lineages, one fork

The Intellon corpus is not a single straight line. Two architectural lineages run close together and the fork between them is the single most important structural fact of this era:

- **Lineage A — persistence / matrix / sub-symbolic** (Mar 22–30). Grounded in the persistence-theory paper. Built on `rootC`, a fixed "lens," 4×4 matrices, ghost nodes, ensembles. Validated (on paper) by an MNIST number. Mostly **spec**, one claimed result.
- **Lineage B — symbolic node / tool-discovery** (the a/b/c/d/e and xb series, plus the v4 Python rewrite). Nodes, a main loop, ~100 primitives, trie addressing, a trust lifecycle. This is the line that **actually got built and tested** — from 57 tests up to 457.

Both lineages produced a document declaring itself the project's *"single source of truth"* within days of each other: `unified_spec_v2.md` (Mar 30, Lineage A) and `project_spec.md` (Apr 4–5, Lineage B, the "18 rules"). The Apr 4 spec drops rootC, the lens, and ghost nodes entirely. **The half that was most believed in (A, physics-grounded) and the half that was engineered (B, symbolic) were not the same half.** The hardest problem — building a system that constructs its *own* way of perceiving above a fixed lens — was correctly named the crux and deferred.

There is also a **pre-history** to Lineage B referenced in the Apr 1 docs but not separately archived here: a **"v6" methodology** (a tool-discovery *simulation*: 60 tools, 190 seed observations, an 8-phase / 6-phase discovery algorithm) and a **"v0.3"** that suffered a **30,753-node explosion**. The node pivot (below) was a direct response to those.

---

## Phase 1 — Theoretical root & the matrix/lens engine (Mar 22 – Mar 30)

**Mar 22 — `The_Transformational_Basis_of_Persistence_v2.pdf`.** The theory root. The core claim (as carried into `unified_spec_v2` Part 0): the universe is a filter for configurations that sustain their own operation against entropy; **persistence is the only objective reference frame**; chemistry, biology, cognition, and computation are the same kind of thing — persistent structures using internal rearrangement to keep existing — at different scales. Intelligence is information flow (detection, prediction, transformation) sustained because the loop that survives is the one that accumulates depth. The "subactive depth" argument: today's AI achieves vast surface association but lacks a substrate whose *own continued operation* depends on the quality of its computation, so there is no selection pressure forging depth.

**Mar 25 — `real_data_benchmark.html`.** A runnable benchmark on **Iris, Wine, and *synthetic* 8×8 digits** (digits are generated procedurally in-file, not real MNIST). Method: a random untrained hierarchy + Gaussian nearest-centroid ("lottery ticket" style — generate many random nets, report the distribution). **Does not use `rootC`; is not real MNIST; does not produce the 99.8% number.**

**Mar 26 — `two_net_independent_pipeline.html`.** A synthetic digit generator + two-net independent-pipeline experiment. Synthetic, not real MNIST.

**Mar 27 — `mnist-master.zip`.** The well-known cazala/mnist **dataset** (digits as JSON) acquired and placed in the folder. Data only — no classifier wired to it in the corpus.

**Mar 30 — `intellon_unified_spec_v2.md`** (the Lineage-A "single source of truth") and **`intellon_v3.jsx`**. The spec consolidates the matrix engine:
- **`rootC(a,b) = sign(a×b)·√|a×b|`** — one operation doing three jobs at once: comparison (sign of output = agreement/disagreement), signal propagation (a chain holds ~0.9 where raw multiplication decays to ~0.53), and training signal (the same value is the correction gradient). Zero self-eliminates.
- **The fixed lens** — encodes reality and never changes; corrections go to hypotheses, never to the lens ("you don't recalibrate your eyes when you misidentify something"). Three channels: hex-tile vocabulary, structural compression, raw nested matrix.
- **4×4 matrices** (16 values/node) as the unit of representation; element-wise rootC.
- **Ghost nodes** — concepts that exist only as combinatorial bitmask addresses over base nodes; zero storage until co-activation fires (15 base nodes → 32,753 possible combinations).
- **Ensembles ARE concepts**; **energy bands** (a node's accuracy funds its persistence; consistently-wrong nodes drop below band and die); **antifacts** (wrong answers are terminal intellons leaving boundary information — never retry a rejected hypothesis); **relative correction** (sharpen 5-vs-8 only where they disagree, not a global pull toward the mean).

`intellon_v3.jsx` (Mar 30) implements `rootC` and 4×4 matrices with relative correction and an accuracy display — but it runs on **arithmetic/logic triples**, not images (this is the source of the "logic 100%" result, not a vision result).

> **The 99.8% MNIST claim.** It appears in `unified_spec_v2.md` only — once in prose ("Validated empirically at 99.8% MNIST accuracy on 728 samples") and once in the Part-14 validation table. A full search of the corpus (`.jsx/.html/.js/.md`) finds **no runnable code** that loads real MNIST, applies the rootC/4×4 architecture, and produces that number, and the spec gives **no replication procedure** (no split, no preprocessing, no seed). "728" is an unusual sample count (one digit off from 784 = 28×28). Treat 99.8% as an **undocumented, non-reproducible claim** within this corpus.

---

## Phase 2 — The node pivot & the a/b/c series (Apr 1)

On **Apr 1** the project pivots from the matrix engine to a **symbolic "node" architecture** (`intellon_node_design_proposal.md`, `intellon_handoff.md`, both Apr 1). The stated motivation: prior symbolic attempts produced **dead knowledge** ("procedures sit in arrays, properties in separate lists, inverses in a lookup table — nothing is connected") and a **v0.3 node explosion (30,753 nodes)**. The pivot is framed as **supersession, not abandonment** — the same discovery goals on a new foundation.

Core ideas introduced:
- **Holonic principle (D1):** a single pool of nodes, no type-based filtering — a node is a whole and a part at once.
- **Self-describing nodes:** each carries an internal definition using AND/OR/NOT and can answer queries about itself.
- **Live references:** nodes compose by reference, not copy; changes propagate automatically. **Partial-reference behavior model (D2):** an overlapping node references shared cases and stores only its divergences (e.g. AND agrees with EQ on 3/4 boolean cases, owns only the (F,F) divergence).
- **AddressBook (D5):** one flat global structure — `byName`, `byId`, `byDomain`, `allNodes` (O(1) lookups + domain indexing).
- **Work → Ruminate → Play** ordering (D7), strict priority; **tiered rumination** (D6).

**The lettered build (test counts from the handoffs):**
- **a-series (dev / batch):** proved the node architecture works. **a.5: 57/57 tests**, 12,675 ops, 97% coverage (154/158 observations), 8/8 algebra, 40 procedures, 6 inverses, 7 synonyms, 58 overlaps.
- **b-series (training):** first incremental learning; discovered the conflict-driven approach. **b.1: 17/17**, ADD confirmed at observation #3, ADD↔SUB inverse found during rumination.
- **c-series (foundation rebuild on the holonic principle):** **c.1: 27/27** (Node + AddressBook); **c.2: 28/28**, full 60-tool discovery — matched a.5's results (40 procedures, 97% coverage) on the new foundation with only 67 nodes (vs the old 30,753).

**"v6 methodology"** (`intellon_v6_methodology.docx`, Apr 1) is the *reference baseline* the node engine had to match or exceed: 60 tools, 190 seed observations, a 6-phase discovery algorithm. **The teaching plan** (`intellon_teaching_sequence.md`, Apr 1) restructures 158 observations into 13 developmental stages (perception → logic → single-digit arithmetic → place value → number construction → multi-digit → comparison → types → strings → sequences → bitwise → algebra), on the rule **"known inputs / novel outputs = ok; novel inputs = wait."**

---

## Phase 3 — The d-series: trust gradient & full discovery (Apr 1 – Apr 3)

The d-series replaced fixed confirmation thresholds with a **trust gradient** and drove the discovery pipeline to completeness. Test counts and metrics from the handoffs:

- **d.1 (Apr 1, 36/36):** five-tier trust gradient (D13) — base/starred/standard/trial/working; one-way rule (persistent nodes can't reference working nodes); eviction respects gradient order.
- **d.2 (Apr 2, 28/28):** **100% coverage — 158/158 observations** (the 5 previously-uncovered tools now discovered); 45 procedures. Confirmed **F8: removing the confirmation threshold is beneficial** (no false positives).
- **d.3 (Apr 2, 25/25):** explainable promotion logic (`shouldPromote`, `shouldAdvance`, `sessionEnd`) — every decision carries a reason string.
- **d.4 (Apr 2, 22/22):** incremental LearningSession ported onto the tier foundation; **ADD/SUB/MUL confirmed at observation #1** (vs b.1's #3); supersedes b.1.
- **d.5 (Apr 3, 17/17):** three-tier `ruminate(budget)` — correction queue drains fully before budgeted broad maintenance; resumable cursor.
- **d.6 (Apr 3, 20/20):** full pipeline, flat order, 158/158 coverage, 77% recognition. **F9: EQ/NEQ perfectly partition boolean outputs — GT/LT/GTE/LTE are never independently discoverable from observation alone**, only via rumination overlap.
- **d.7 (Apr 3, 6/6):** standalone verification benchmark — 100% predict / 75% explain on novel random inputs (proved learned, not memorized).
- **d.8 (Apr 3, 18/18) — the main artifact:** developmental 12-stage teaching sequence; **58/60 tools discovered** (19 recovered via overlap rumination); L2 chain discovery (`FLOOR(DIV(x,10))` from 5 observations); inverse solver 8/8 algebra; configurable benchmark to **1M/1M predict/explain at 100%**. **F11: generalization is automatic for deterministic tools** (learned ADD on single digits → recognizes 47+35=82 with no new discovery).

By Apr 3 the architecture decisions are documented as **D1–D19** and findings as **F1–F12** (`intellon_handoff_v6.md`).

---

## Phase 4 — The e-series: language (Apr 2 – Apr 3)

The e-series turned the same engine toward **language structure** (`intellon_e_series_design.md` and the `e9/e10/e11` code):
- **e.1–e.2:** letters and sight words.
- **e.3 — "the gate test":** the system derives **3 positional categories from 30 *unlabeled* sentences** — categories emerging from observation patterns without labels.
- **e.4–e.8:** syntax, grammar, WordNet integration (`intellon_wordnet_reasoning.js`, Apr 2 — sense selection; corpus reaching hundreds of thousands of nodes).
- **e.9 (39/39):** self-directed reading comprehension over **51,394 labeled sentences**, with event extraction and queries (`intellon_e9_reading.js`, `intellon_e9_selfdirected.js`).
- **e.10 / e.11:** raw ingestion and deep reading (`intellon_e10_raw_ingestion.js`, `intellon_e11_deep_reading.js`).

This is also where the project's signature discipline was proven from data: the later spec records that **"e.12" replaced three hardcoded workarounds with 75 observation pairs** — the system learning from data what the architect had been prescribing with if-statements (the seed of the standing "no workarounds" rule).

---

## Phase 5 — The xb-series: the JS engine (Apr 4 – Apr 7)

The xb-series is the mature JavaScript engine. Test-count progression: **xb.4 = 210 → xb.5 = 343 → xb.6 = 385 → xb.7 = 457 → xb.8 = 457.**

- **xb.4 (Apr 4, 210 tests):** Layer-0 substrate (two tries, five-component nodes [macro/address/context/buffer/pointers], prefix-notation evaluator, ~85 primitives, 128 base nodes); questions; the learning loop (attempt → feedback → retry×3 → diagnose → re-verify); logarithmic trust (working-trial → standard → proven → node-trial → node-proven); self-exploration of primitives via a tool curriculum (10 correct novel predictions = TRUSTED). **43 primitives trusted, 10 verified.** The foundation docs `project_spec.md` (the **18 rules**) and `project_plan.md` (10-phase roadmap) are written here.
- **xb.5 (Apr 5, 343 tests):** six roadmap phases in one session — `gather`/`relate` (attention + overlap), macro composition with template args, the operational cycle (observe/question/deduce/verify) as composable macros, `selftest`, adjacency tracking, and scaffolded sentence comprehension with entity/state tracking. Hardcoded English grammar ("the bodge") flagged for later removal via learned patterns.
- **xb.6 (Apr 5, 385 tests):** **ruminate** — idle-time self-directed discovery (gather → propose → interrogate, recursive) across a 77K-node WordNet graph, storing cross-type discoveries; `compose` (multi-inheritance working concepts); extracted to a Node.js module; O(n²) bottlenecks removed (5K facts 30s → 1s; 77K WordNet in 7.4s).
- **xb.7 (Apr 5, 457 tests):** unified input pipeline (`_processInput`: recognize → context → integrate → observe) — every input is also training data; role/pattern observation nodes; learned-pattern recognition. Storage-migration (Track 5) and provenance (Track 4) specced.
- **xb.8 (Apr 6, 457 tests):** the in-memory trie replaced by **SQLite-backed StorageEngine** (write-through cache); **session manager** (new/save/load/switch/end with trust-filtered "curated commit"); the **hypothesis system** (predict a relationship, then let incoming data confirm it — timestamps prove prediction preceded confirmation); **provenance** (per-pointer source arrays; trust grows with source diversity; cross-context contradictions don't fire).
- **xb.8 (1) (Apr 7, 457 tests):** live DB at **295K nodes / 67K relationships / 35K hypotheses**; a core **`compare` operation** and **six thinking modes** (compare, classify, extrapolate, counterfactual, hypothesize, ruminate-deep); hypothesis materialization; parallel ruminate workers. **Self-identified blocker: the "thinking engine" `synthesize(topic)`** — the system can compare A↔B but cannot yet fold many comparisons into a new concept ("legs appeared 47 times" never becomes a "locomotion" category). Track 6 (response generation as the reverse of comprehension, self-checked by feeding output back through comprehend) was specced (Apr 6) to depend on it.

---

## Phase 6 — The v4 Python rewrite (Apr 8 – Apr 11)

After the JS engine, the project was **rewritten from scratch in Python** under a new architecture whose slogan was **"differentiation is the only native operation."** Three components: **Node** (dictionary entry), **Register** (the three-slot A/B/Center comparator that produces a "notepad"), **Librarian** (knowledge authority / bundler). Sessions:

- **Session 1 (Apr 8):** architecture frozen; design only.
- **Session 2 (Apr 9):** full working prototype — **18 Python modules**, 119 foundation nodes (95 ASCII + 14 operators + 10 digits), curriculum of ~153 observations, WordNet loader (84K lemmas in ~16s), autonomous "thinker," Tkinter GUI, CLI, SQLite persistence, **11 tests passing**. Worked: boot, pattern extraction, autonomous thinking, 88% recognition. Didn't: knowledge retrieval (0% on auto-generated challenges), shallow synthesis, scoring not feeding back to generation.
- **Session 3 (Apr 10):** code rolled back; design insights only — negentropic scoring formula, a grading loop (two answers + score delta = signal, no instruction needed), rule emergence from clustered corrections, register-produces / generator-grades.
- **Session 4 (Apr 10 PM):** storage rebuilt on **LMDB** (graph store: nodes as "emails" with readable header + opaque payload; edges with polarity in forward/reverse DBs) + a tagged-text payload codec. ~10K nodes+edges in 0.10s.
- **Session 5 (Apr 11):** full pipeline rebuilt on LMDB + tagged text — 9 source files + a Flask web UI (`localhost:7433`); one-note-per-pair comparison (linear, not exponential); grading loop measurably improving scores across iterations (0.04 → 0.32 → 1.42 → 3.29); save/resume working.

---

## Endpoint — Intellon → SIS (Apr 12)

**`concept_proposal.md` (Apr 12)** proposes a fundamentally different system — **SIS (Structural Intelligence System)** — replacing Node/Register/Librarian with a **concept spreadsheet (sparse matrix)**, **five simultaneous rolling context windows (3/10/50/100/500 words)**, **holonic pattern layers (chars → words → phrases → sentences → paragraphs)**, definition fingerprinting via concept-mask averaging, and **integer-only computation (−255…+255, no floating point, no gradients)**. A later doc (`HANDOFF_TO_NEW_CHAT.md`, Apr 27) records that **"SIS … is also called the Intellon Method"** — conceptual continuity, new architecture.

**The Intellon era ends here (Apr 11 build / Apr 12 redesign).** What followed — SIS, then Isaac — is documented elsewhere.

---

## Findings & decisions ledger (as recorded in the handoffs)

**Decisions (symbolic lineage):** D1 holonic principle (no type boundaries) · D2 partial-reference behavior model · D3 one-hop depth per node · D4 rumination discovers shortcuts · D5 single global AddressBook · D6 tiered rumination · D7 Work→Ruminate→Play ordering · D8 conflicts drive discovery · D9 base-10 is perceived not constructed · D10 composite numbers via right-peel · D11 logic as architect-scaffolded infrastructure · D12 EQ/NEQ as valid structural primitives · D13 trust gradient replaces confirmation thresholds · D14–D19 ghost nodes, learning/working modes, session lifecycle, deferred wiring, self-authored `_meta` extensions. (The later xb-era `project_spec` carries decisions forward through ~D30 and findings through ~F37.)

**Findings:** F1 boolean-domain tool overlap (EQ/NEQ universal matchers) · F2 discovery dominates cost, reasoning nearly free · F4 right-peel decomposition works (left-peel infinite-recursed) · F5 confirmation threshold caused the uncovered observations · F8 threshold elimination → 100% coverage · F9 EQ/NEQ partition boolean outputs (GT/LT/GTE/LTE only via overlap) · F10 overlap-driven discovery recovers 19 tools · F11 generalization automatic for deterministic tools · F12 chain discovery needs observations beyond single-tool reach. (xb-era adds F28 "case is data," F29 single-exposure vocabulary, F37 "workarounds unnecessary when data is sufficient," etc.)

---

## Throughline (why this era still matters)

Three instincts forged in Intellon carried forward intact:
1. **Comparison = learning** (rootC: the test and the training signal are one operation) → later "learning is registration / nulling."
2. **Correct the model, never reality** (the fixed lens) → later "model everything; the answer is the residual."
3. **No workarounds — prove everything from data** (e.12: three hardcodes → 75 observation pairs; "if it can't prove it, it proves nothing") → the standing rule against shipping a trained net as "the answer."

Intellon is where the philosophy was built and tested on small, hard problems. What came after pointed it at larger ones.

---

## Source files (in this folder and `../june_17_isaac_research/`)

- **Theory:** `The_Transformational_Basis_of_Persistence_v2.pdf` (Mar 22)
- **Matrix lineage:** `intellon_unified_spec_v2.md`, `intellon_v3.jsx` (Mar 30); `real_data_benchmark.html` (Mar 25); `two_net_independent_pipeline.html` (Mar 26); `mnist-master.zip` (Mar 27, dataset only)
- **Node pivot / a–c series:** `intellon_node_design_proposal.md`, `intellon_handoff.md`, `intellon_training_test_plan.md`, `intellon_v6_methodology.docx`, `intellon_teaching_sequence.md` (Apr 1)
- **d-series:** `intellon_handoff (1)…(6).md`, `intellon_d_series_step_design*.md`, `intellon_d8_tests.jsx`, `intellon_handoff_v6.md` (Apr 1–3)
- **e-series:** `intellon_e_series_design*.md`, `intellon_e3_tests.jsx`, `intellon_e9_reading*.js`, `intellon_e10_raw_ingestion*.js`, `intellon_e11_deep_reading*.js`, `intellon_wordnet_reasoning.js` (Apr 2–3)
- **xb-series:** `intellon_handoff_xb4/xb5/xb6/xb7/xb8.md`, `intellon_project_spec.md`, `intellon_project_plan.md`, `intellon_terminal.jsx`, `intellon.js`, `storage_engine.js`, `intellon_track5_proposal_v2.md`, `intellon_track6_response_generation.md` (Apr 4–7)
- **v4 Python rewrite:** `HANDOFF.md`, `HANDOFF_SESSION2…5.md`, `IMPLEMENTATION_SPEC.md`, `intellon_v4_session3_plan.docx`, and the `intellon/` Python package (`cli.py`, `gui.py`, `core/*.py`, `tests/*.py`) (Apr 8–11)
- **Endpoint:** `concept_proposal.md` (Apr 12)

---

*Reconstructed from on-disk artifacts and file timestamps. Test counts, findings, and decisions are quoted from the handoff documents; the MNIST 99.8% figure is a documented claim with no surviving reproduction harness in this corpus.*
