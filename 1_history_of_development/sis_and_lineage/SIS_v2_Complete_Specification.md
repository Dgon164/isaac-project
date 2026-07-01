# Structural Intelligence System v2.0

## Complete Design Specification

### The Intellon Method — Merge Pyramid Architecture

April 2026

---

## What This System Is

SIS is a deterministic knowledge system that learns from text through structural observation. It does not use neural networks, statistical optimization, or floating-point arithmetic. Every decision is derivable — walkable step by step through a chain of integer comparisons from evidence to conclusion.

The system reads text, builds a graph of weighted relationships between concepts, and uses that graph to answer questions, generate text, detect contradictions, and improve its own understanding over time. It does all of this through a single cognitive primitive — the Comparator — applied repeatedly at different scales.

The architecture implements the Intellon Method: every entity in the system is simultaneously a whole (with its own properties) and a part (contributing to the emergence of properties at the next level up). Meaning emerges when parts are grouped into wholes. The method for discovering that meaning is the same at every level: group, compare, observe what appears.

---

## Goals

1. **Derivability.** Every pointer, every conclusion, every correction traces to specific evidence. If the system says "whale is a mammal," you can walk the chain: which comparison fired, what the old value was, what text triggered the change, when it happened.

2. **Self-improvement.** The system gets smarter through use. Each text it processes refines weights, discovers concepts, strengthens navigation paths. The graph gets denser. Denser graphs produce richer constraint intersections. Richer intersections produce better answers.

3. **Structural honesty.** The system never pretends to know something it doesn't. Unknown is unknown — not negative, not zero, not weak. The math physically prevents confident answers on thin evidence. When the thinking loop can't satisfy all constraints, it reports exactly what was satisfied and what wasn't.

4. **Single primitive.** The Comparator is the only cognitive operation. Everything else — learning, disambiguation, thinking, generation, correction, measurement — is built by applying it. If a second comparison mechanism appears anywhere in the system, something is wrong.

5. **Integer arithmetic only.** No floating point anywhere. Every operation is deterministic. Same inputs produce same outputs on every run, every platform, every time.

---

## How It Works — The Complete Pipeline

### Text Comes In

Raw text enters the system. The tokenizer splits it into words and punctuation, preserving contractions and separating edge punctuation. "Don't stop!" becomes ["don't", "stop", "!"].

### Phrase Resolution

Before processing individual words, the phrase resolver checks windows of 5, 4, 3, 2, and 1 tokens at each position. Longest match wins. If "hot dog" exists as a known phrase node, it's consumed as a single unit. The cursor advances past the entire matched phrase. Function words count — "kick the bucket" is a 3-token phrase.

### Word Resolution

Each token resolves to a node ID. Known words resolve instantly via the master index. Unknown words get a new node created with an empty definition, flagged as "encountered." The system doesn't guess — it creates an honest blank slate that will fill in from context.

### Disambiguation

If a word has multiple definitions (bank as river edge, bank as financial institution, bank as verb meaning to tilt), the system compares each definition's pointer list against the current pyramid context at multiple resolution levels. The definition with the highest structural overlap against context wins. "River" in the recent context lights up water, geography, edge — bank def:0 matches massively, def:1 scores near zero. No grammar rules. The Comparator routes it.

### Dense Projection

Each resolved word has a sparse pointer list — weighted connections to other nodes. The dense projector maps the most relevant node addresses to fixed-width vector positions (default 64 dimensions). The projection converts the sparse pointer list into a dense int8 vector suitable for the merge pyramid. Structural seed dimensions (noun, verb, animate, concrete, boundary, etc.) are always mapped. Content dimensions rotate based on what's active in the current text.

### The Merge Pyramid

The dense vector enters the merge pyramid at Level 0. This is the context system — it replaces rolling windows and snapshots from the original architecture.

Adjacent word vectors merge upward through a binary tree (the carry ripple). When two vectors merge, the operation is simple: where both have a value for the same dimension, average them and flag that dimension. Where only one has a value, preserve it unchanged. The flag means "this was averaged — detail exists in the children below."

Within a sentence, the carry ripple is fixed — words pair into bigrams, bigrams into 4-grams, 4-grams into 8-grams. When a sentence boundary fires, the chain pads to the nearest power of two with zero vectors and completes, producing a single sentence frame. Zero padding is invisible to the merge: 0 + X = X, no flag set.

Sentence frames then merge with sentence frames through a separate carry chain. Whole thoughts merge with whole thoughts. When a paragraph boundary fires, the sentence-level chain completes and produces a paragraph frame. The process continues upward — sections, documents.

No information is ever destroyed. The averaged value lives at the current level. The pre-averaged values live in the children. The original word values live at Level 0. The overlap flag bitmask is the navigation map. The pyramid is a resolution-navigable trie of meaning.

### MetaFrame Engine

The pyramid's own operating rules are not hardcoded. They are metaframes — patterns about how frames interact at each level.

Five metaframes are seeded as scaffolding: sentence boundary (period fires carry chain completion), negation (the "not" dimension flips signs on the next word), paragraph boundary (high flag density between consecutive sentence frames), definition branching (high divergence indicates a new sense of a word), and document boundary (total dimensional reset).

The system discovers new metaframes from observing its own transitions. Every frame transition is recorded as a signature (which dims were strong) paired with an outcome (what happened — flag density spike, sign flip, divergence). When the same pairing recurs across enough transitions, it becomes a learned metaframe. The system discovers its own layer rules from the dimensional physics, the same way it discovers everything else.

### Boundary Detection

Boundary detection is metaframe-driven. When a word enters the pyramid, the metaframe engine checks all active metaframes for the current transition. A period node has the boundary dimension at +127. The sentence_boundary metaframe triggers, completing the carry chain and producing a sentence frame.

The paragraph_boundary metaframe watches for high flag density between consecutive sentence frames — sentences that don't blend cleanly indicate a topic shift. The document_boundary metaframe watches for near-total dimensional reset at the paragraph level.

A missed boundary creates one extra frame that merges into the correct level one step later. A false boundary splits a sentence into two frames. Neither is catastrophic — the pyramid self-heals because everything converges upward. But the metaframe engine refines its triggers over time, getting better at detecting boundaries as it observes more transitions.

### Negation

Negation is a metaframe. When the system encounters a word with the "not" dimension, the negation_flip metaframe fires, setting a flag. The next word's dense vector has its signs inverted before entering the pyramid. "Not small" → the dimensions from "small" enter with flipped signs. +120:size_small becomes -120:size_small. No grammar rules. Composable. Fully traceable.

### Comparator-Gated Learning

The system does not create pointers from raw co-occurrence. Co-occurrence is noise. "The cat sat on the mat" tells the system almost nothing because every word is generic.

When two words appear in the same clause, the system runs the Comparator between them. The result determines whether learning happens:

- **High shared + high absent = informative.** The words are structurally related (shared foundation) and the absent dimensions are novel information for the subject. Create or strengthen pointers. Example: "cat" encounters "purred" — they share feline, and purred has vocalization, contentment that cat lacks. Real knowledge.

- **High shared + low absent = confirmation.** The information is already known. No new pointers needed.

- **Low shared + anything = unrelated.** There's no structural foundation making the absent dimensions meaningful. Skip entirely. This is why function words don't create noise — "the" next to "cat" produces near-zero shared set.

The initial weight of a new pointer is derived from the Comparator output — the strength of the shared foundation times the specificity of the novel information. The weight IS the structural assessment. Not a hardcoded number.

### Self-Correction

When the Comparator finds a direct contradiction — an existing pointer says +100 but new evidence says the opposite — the update is the integer average of old weight and new evidence. Progressive refinement, not abrupt flips.

The merge pyramid enhances correction: when a word's comparison against the pyramid frame shows divergent dimensions that are ALSO flagged (averaged) in the frame, that's a double signal. The dimension is structurally uncertain AND contradicted by new evidence. High-priority correction target.

Every correction is logged with timestamp, node, target, old weight, new weight, source, and triggering evidence. The log is append-only, human-readable, fully traceable.

### Correction Ripple

When a pointer changes significantly, dimensions that overlap heavily with the corrected dimension are queued for re-evaluation. The dimensional overlap module computes this by running the Comparator on two concepts' back-lists — the shared set size divided by total unique entries gives the overlap percentage. High overlap means high priority.

When whale's fish pointer changes, the system checks: what dimensions travel with fish? Gills overlaps fish at 90%. Scales at 85%. Cold-blooded at 80%. Each goes onto the re-evaluation queue, ordered by overlap percentage. The queue is processed when the idle processor gets to it.

### Pattern Abstraction

As each word enters the pyramid, it produces a delta — the change to the context. The pattern abstractor strips the dimension IDs from these deltas and keeps only the sorted magnitudes and signs. What remains is the structural shape of the sentence.

"The dog ran quickly" and "A storm approached silently" produce the same shape: function word (low count, positive), heavy content word (high count, all positive), action shift (medium count, mixed signs), modifier (low count, positive). Same grammar, different content. Grammar discovered from dimensional physics, not rules.

The system tracks these shapes across sentences. When the same shape recurs with different content, it becomes a pattern — a grammatical template. Pattern matching tells the system "this sentence has the same structure as 200 others I've seen" without parsing.

### Trie Navigation

The pyramid is a trie. Navigation follows the numbers.

When matching a query against the trie, the navigator checks the current frame. If the dimension you care about reads +3, go to the children. One reads 0, the other reads 6. Go to the 6. Its children read 8 and 4. Go to the 8. Keep following the bigger number until you find the concentration. Gradient descent through integers.

Going UP works in reverse — if the current frame doesn't have enough dimensions to match the query (large absent set), the parent frame covers a wider span and may have the missing context.

The match quality at each level — shared count, flag count, absent count — tells the navigator whether to go up, down, or stop. Strong match with few flags = right resolution. Flagged shared dims = go down for detail. Large absent set = go up for breadth.

### The Thinking Loop

Every act of reasoning begins with a resolver — a constraint map specifying required dimensions. "Find me something that is animate AND noun AND domestic." The thinking loop gathers candidates from back-list intersections, scores each against the resolver using the Comparator, refines by expanding the search into top candidates' neighborhoods, and iterates until the divergent set hits zero or the search space is exhausted.

The thinking loop never silently fails. It always produces the best candidate found, with an honest report: which constraints were satisfied (shared set), which conflicted (divergent set), and which couldn't be resolved (absent from all candidates). The consumer decides what to do with gaps.

Resolution-adaptive: the thinking loop scores candidates against pyramid frames at the level that best matches the query. Broad questions navigate up for thematic answers. Specific questions navigate down for precise answers.

### Generation

Generation descends the pyramid trie. Each level constrains the next. Section frames set voice and register. Paragraph frames set topic. Sentence frames set mood and intent. Clause frames set grammatical slot. Word-pair frames constrain selection. Level 0 selects the specific word.

Every proposed word must survive scoring against ALL levels simultaneously. A word that fits the grammar but violates the voice is eliminated. A word that fits the voice but breaks the grammar is eliminated. Only words that satisfy every level of constraint at once make it through.

The quality equation scores each output:

```
quality = (match_score × constraints²) / (log(words) × log(time_μs))
```

Match score is averaged, not summed — stays bounded. Constraints squared rewards simultaneous satisfaction of many constraints. Log penalties for verbosity and compute. All integer-safe.

### Self-Assessment

The system assesses its own output at every pyramid level. The self-assessor takes text (produced or ingested), projects each word into the pyramid, and runs the quality equation at each level independently.

When a level scores low, the Comparator output tells you exactly which dimensions failed. The trie navigator traces each failure down through the pyramid to find which specific word introduced the violation. Failures are classified as either output errors (fixable by swapping a word) or understanding gaps (the graph needs correction).

For output errors, the assessor searches the failing dimension's back-list for replacement words that have the right sign. For understanding gaps, the failing dimension is queued for the idle processor.

The assess-and-refine loop iterates: assess, apply the best suggestion, re-assess, repeat until quality converges or max iterations reached.

### Conversation

Every input gets processed through the pyramid normally. Then the system looks at what lit up — the most extreme dimensions in the resulting frame. It separates structural signals (declarative, interrogative — what kind of sentence) from content signals (animate, positive, verb — what the sentence is about). It searches its existing knowledge for nodes whose pointer structure matches those extreme content dimensions. The response comes from what the system already knows that relates most strongly to what was just said.

Statements produce: shape identification (declarative), content dimensions (what it's about), matching nodes (what existing knowledge fits), what was learned (new connections, refinements), and unknown words.

Questions route through the query interface, which uses the thinking loop and trie navigation to find answers at the appropriate resolution level.

### Idle Processing

When no input is arriving, the system thinks about what it already knows. Two modes, 80/20 split:

80% dimension scanning: examines flagged dimensions across recent pyramid frames. Which dimensions are most frequently averaged? Those are structurally uncertain regions. Traces them down through the trie to Level 0 source nodes. When leaf values disagree in sign, that's a contradiction to investigate.

20% node following: picks a node (prioritized by learning value — sparse or uncertain nodes first), follows its strongest pointer, compares what it finds, notices something interesting in the divergent or absent set, follows that trail. Refines as it goes. Stops when the trail goes cold.

Both modes use the learning priority function: overlap_percentage × divergent_count. High overlap + high divergence = maximum learning value. The idle processor seeks out the comparisons most likely to produce new knowledge.

### Concept Emergence

Concepts emerge from recurring structural patterns in pyramid frames. Two Level 3 frames with near-zero delta on overlapping dimensions are structurally similar regardless of vocabulary — they have the same clause structure. The shared dimensional pattern across multiple matching frames IS an emergent concept.

Level metadata is automatic. Concepts from Level 2 comparisons capture word-pair patterns. From Level 3, grammatical structure. From Level 5, rhetoric. The level of the frames being compared determines the kind of concept that emerges.

### Emergent Dimensionality

Each level of the pyramid observes a different holonic level. Properties that don't exist at the word level — grammar, mood, rhetoric, voice — emerge naturally as words group into sentences, sentences into paragraphs, paragraphs into sections.

You cannot find "grammatical role" by looking at individual words. "Dog" alone has no grammatical role. It acquires one when grouped with other words into a sentence. The dimension emerges from the grouping. The merge pyramid directly implements this: within-sentence levels discover grammatical structure, sentence levels discover mood, paragraph levels discover rhetoric, section levels discover register.

### Metacontextual Measurement

Every style, register, genre, and voice is a node. Measuring any of them against any text is one Comparator call. Project the style node's pointers to a dense vector, compare against the current pyramid frame. Shared count over total pointer count gives the percentage.

Drift detection compares sentence frames across positions. First sentence frame vs last sentence frame gives voice consistency. High match score = consistent voice. Low score = the text drifted.

---

## What Gets Stored

### Nodes

Human-readable text files. Each node has an ID (positional index), name, creation date, source, one or more definitions with pointer lists, shared pointers, and a back-list. Back-lists stay in sync bidirectionally on every pointer update.

```
=== 201 ===
name: dog
created: 2026-04-12
source: wordnet

--- def:0 noun ---
a domesticated canine kept as a pet
+127:2 +120:88 +115:17 +100:44 -100:3

--- shared ---
+127:5 +127:9 +127:13

--- backlist ---
+127:88 +100:17 +80:301
```

### Pointers

64-bit packed integers. 8-bit signed weight (-127 to +127) in the top byte, 56-bit unsigned address in the bottom 7 bytes. Weight 0 is forbidden — absence means unknown. Weight -127 is reserved for proven contradictions.

### Master Index

Plain text file. Maps node IDs to names. Always in RAM. ~8 MB for 310K nodes.

### Pyramid Frames

Each frame stores a dense int8 vector, an overlap flag bitmask, coherence count, level, boundary type, position, width, and child pointers. Sentence and paragraph frames are saved as numpy binary files for persistence. Frame metadata is JSON.

### Correction Log

Append-only plain text. Every pointer change recorded with timestamp, node, target, old weight, new weight, source, and triggering evidence.

---

## The Data Flow

```
Text → Tokenize → Phrase Resolution → Word Resolution → Disambiguation
  → Dense Projection → Merge Pyramid Push → MetaFrame Check
  → [Boundary: Complete Sentence/Paragraph]
  → [Negation: Flip Next Word Signs]
  → Comparator-Gated Learning → Correction Ripple
  → Pattern Abstraction → Concept Emergence
  → N-gram Promotion
```

```
Query → Tokenize → Resolve Concepts → Build Resolver
  → Gather Candidates (back-list intersection)
  → Score Against Resolver (Comparator)
  → Score Against Pyramid Context (trie navigation)
  → Iterate → Report (satisfied / conflicted / unresolved)
```

```
Generate → Resolver Constraints → Gather Candidates
  → Score Across All Pyramid Levels (cross-level coherence)
  → Select Best Word → Push Into Pyramid → Repeat
  → Quality Equation → Output
```

```
Self-Assess → Project Text → Score Per Level
  → Find Failing Dimensions → Trace Through Trie
  → Classify: Output Error vs Understanding Gap
  → Suggest Replacements / Queue Corrections
  → Iterate Until Convergence
```

---

## Memory Model

### Hot Cache

Fixed-capacity LRU cache. All reads and writes happen to RAM copies. Disk is only touched on page-in and write-back. Dirty nodes are written on eviction or periodic safe-save. Clean nodes are dropped with zero I/O. Capacity calculated from RAM budget (default 512 MB → ~119K nodes).

On GPU, the entire graph fits in VRAM (~310 MB). No eviction needed. Every node hot, all the time.

### Paging

Node requested by ID → check master index cache pointer → if NULL, read from disk, parse, load into hot cache, update index. O(1) lookup, O(node_size) page-in.

### Crash Safety

Safe-save writes all dirty nodes periodically. Atomic writes via temp file + rename. If the system crashes between saves, only changes since the last save are lost. On-disk files are always consistent.

---

## Bootstrapping

Seeded with WordNet and ConceptNet in bulk mode. All synsets sharing a lemma collapse into a single node with multiple definitions. All direct relationships get maximum weight (is_a → +127, antonym → -127). Starting approximations, not final scores. Evidence from text processing adjusts them.

Before WordNet, three seed stages build the structural scaffolding: ASCII characters as nodes, equality/inequality vocabulary (equal, different, true, false), and logical/mathematical scaffolding (and, or, not, is_a, has_a, noun, verb, animate, concrete).

---

## Learning Progression

| Stage | Nodes | Avg Pointers | What Happens |
|-------|-------|-------------|--------------|
| Seed | ~165 | ~5 | Structural scaffolding |
| + WordNet | ~150K | ~50 | Full vocabulary with taxonomy |
| + ConceptNet | ~200K | ~65 | Cross-concept relationships |
| + 1 book | ~210K | ~70 | Context-refined weights, new phrases |
| + 10 books | ~230K | ~80 | Dense connections, emergent concepts |
| + 100 books | ~280K | ~100 | Rich constraint intersections |

Each book is easier than the last. Denser graphs produce more precise Comparator results, which produce more selective learning, which produces denser graphs.

---

## Component Inventory

### Pyramid Engine (4 files)
- `merge_pyramid.py` — Frame structure, merge operation, carry chain, boundary completion with padding, frame store.
- `overlap_tracker.py` — Drill-down retrieval, flag density analysis, boundary spike detection, dimension tracing from high-level frames to Level 0 sources.
- `trie_navigator.py` — Dense vector comparison, navigation decisions (down on flagged, up on absent, stop on good match), gradient descent search, dimension source finding.
- `dense_projector.py` — Maps sparse pointer lists to fixed-width dense vectors, dimension map management, seed from index.

### Processing Pipeline (2 files)
- `text_processor.py` — Full ingestion pipeline: tokenize, resolve, disambiguate, project, pyramid push, metaframe check, Comparator-gated learning, pattern abstraction, concept emergence, N-gram promotion.
- `metaframe_engine.py` — Layer patterns: seeded rules (boundaries, negation, definition branching), transition recording, signature→outcome pairing, automatic metaframe discovery.

### Cognition (5 files)
- `disambiguator.py` — Multi-level pyramid comparison across definitions.
- `thinking_loop.py` — Resolver-based constraint satisfaction with back-list intersection, resolution-adaptive scoring, honest reporting.
- `generator.py` — Top-down constraint cascade through pyramid trie descent, cross-level coherence scoring, quality equation.
- `self_assessor.py` — Per-level quality scoring, per-dimension failure tracing, output error vs understanding gap classification, suggestion generation, iterative refinement.
- `idle_processor.py` — 80/20 dimension scanning + node following, learning priority function.

### Learning (4 files)
- `concept_emergence.py` — Same-level frame comparison, recurring pattern detection, concept node creation with level metadata.
- `pattern_abstractor.py` — Delta value profiles, dimension ID stripping, grammatical shape tracking, pattern discovery.
- `self_correction.py` — Contradiction detection, gradual refinement (integer average), append-only correction logging.
- `dimensional_overlap.py` — Back-list Comparator for dimension co-occurrence, correction ripple priority queue.

### Foundation (11 files, unchanged)
- `pointer.py` — 64-bit pack/unpack, sort, binary search, derived weight.
- `node.py` — Identity, definitions, shared pointers, back-list, dirty flag.
- `node_io.py` — Human-readable file format, atomic writes, tiered directories.
- `master_index.py` — Positional array, name lookup, save/load plain text.
- `hot_cache.py` — LRU eviction, dirty write-back, safe-save, RAM-budget capacity.
- `backlist_manager.py` — Bidirectional sync on every pointer update.
- `comparator.py` — Three-part output (shared/divergent/absent), confidence equation, three-slate verification.
- `resolver.py` — Constraint map with hard/soft/exclude, pointer list conversion.
- `word_resolver.py` — Exact/lowercase/unknown resolution, tokenizer.
- `phrase_resolver.py` — Longest-match-first, windows 1-5.
- `graph_traversal.py` — Two-hop hard limit, negative wall, derived weight.

### Knowledge (3 files)
- `seed.py` — ASCII characters, eq/neq, logic/math scaffolding.
- `wordnet_loader.py` — Bulk import with synset collapse.
- `conceptnet_loader.py` — Bulk import with relation weight mapping.

### Interface (6 files)
- `conversation.py` — Frame-based response: process input, extract extreme dims, separate structural from content, search matching knowledge, build response.
- `query.py` — Resolution-aware answering: definitions, comparisons, similarity, generation.
- `metacontextual.py` — Style/voice/genre measurement against pyramid frames, drift detection, voice consistency.
- `state_persistence.py` — Save/load pyramid frames, projector dim map, promoter state.
- `web.py` — HTTP server: chat, node inspector, pyramid viewer, self-assessor, idle control.
- `gui.html` — Dashboard: chat tab, pyramid tab, assess tab, status sidebar, node inspector.

### Support (2 files)
- `structural_promotion.py` — N-gram frequency + context stability tracking, automatic phrase node creation.
- `run.py` — CLI entry point with full command set.

---

## Absolute Constraints

1. All arithmetic is integer. No floating point anywhere.
2. The Comparator is the only cognitive primitive.
3. The 64-bit pointer format is fixed. 8-bit weight, 56-bit address.
4. Absent is not negative. Missing pointer = unknown, not false.
5. Every value traces to evidence.
6. Determinism. Same inputs, same outputs, every time.
7. Human-readable storage. Open any file in a text editor.
8. The system never pretends. Inconclusive evidence produces inconclusive scores.

---

## What Remains

### GPU Port (Phase 6)

The merge operation is three lines of numpy that become three lines of CuPy. The carry chains are independent — run all offsets in parallel. Batch comparison scores all candidates in one dispatch. The architecture is identical. The backend changes.

The GPU adds: Offset 1 support (second carry chain per within-sentence level for phrase alignment coverage), batch merge kernel, batch comparison kernel, dense graph projection into VRAM, dimension partition bitmasks for bitwise pair queries, and the 10-pass comprehensive analysis pipeline.

Target hardware: NVIDIA RTX 3090 — 10,496 CUDA cores, 24 GB GDDR6X. Total working set ~560 MB (2.3% of VRAM). The entire graph, every frame, every comparison runs in VRAM. No paging. No eviction. Every node hot, all the time.

---

## How to Run

```bash
# CLI
python sis_v2/run.py --storage ./brain
sis> seed
sis> wordnet
sis> Dogs are loyal animals.
sis> What is a dog?

# Web GUI
python sis_v2/web.py --storage ./brain
# → http://localhost:8080
```

---

## The Intellon Method

A representational paradigm for machine intelligence.

1. Reality has structure. Discovered, not created.
2. The structure is a trie. Shared paths = shared meaning.
3. The intellon is the waypoint. Every node is simultaneously whole and part.
4. Meaning emerges at each depth level. Dimensions that do not exist at the level below appear when parts become wholes.
5. Discovery is comparison. The Comparator applied to wholes at any level reveals the emergent dimensions of that level.
6. Learning is in the divergence. Shared paths confirm. Divergent paths reveal.
7. Thinking is constraint satisfaction. The resolver specifies required paths. The thinking loop navigates until a coherent path survives.
8. Generation is exiting the trie. Output is produced by descending through constraints at each level.
9. The system's own rules are discoverable. Metaframes — patterns about how frames interact — are learned from observing transitions, the same way everything else is learned.
10. Everything is derivable. Every waypoint, every edge, every path, every conclusion traces to a specific comparison between specific wholes at a specific level.

*39 files. 10,456 lines. 119 tests passing. One cognitive primitive.*
