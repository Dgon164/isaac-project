# Isaac — System Architecture Document

## The Complete Structure as of Session 10

**Date:** May 18, 2026
**Version:** Post-Session 10 (redo)
**Purpose:** This document describes what Isaac IS — every component, how they connect, what they do, and what it means. It is the single reference for understanding the system in its current state.

---

## Part I: What Isaac Is

### 1.1 The Core Claim

Isaac is built on a single assertion: intelligence is one operation — comparison — recursively applied. The Comparator takes two things and produces three outputs: what they share, where they diverge, and what's absent. Every cognitive behavior — pattern recognition, abstraction, learning, generation, self-correction — emerges from applying this operation at different scales to different inputs, including its own outputs.

The system does not interpolate. It does not guess. It does not blend. It differentiates. The result of a comparison is definite: same or different, present or absent, shared or divergent. Everything built on this foundation inherits that definiteness.

### 1.2 The Two-System Architecture

Isaac has two systems corresponding to the dual-process model of cognition:

**Isaac 1 (the walker)** — Type 1 thinking. Fast, rote, pattern-based. Handles the vast majority of interactions through accumulated doors and try-chains. Translates between English and concepts, generates sentences, learns from corrections, discovers types. This is not a parser or a preprocessor — it is the primary cognitive system. The claim, supported by the existence of large language models, is that a walker-type system handling pattern matching through accumulated connections can manage most cognitive tasks.

**Isaac 2 (the crystallizer and future reasoning)** — Type 2 thinking. Slow, deliberate, structural. Comparison applied to the net's own structure. Discovers types, rules, hierarchies, and anomalies. Only invoked when Isaac 1's patterns are insufficient — when there are literally no doors and no paths. Isaac 2's results flow back to Isaac 1 as new doors and constraints, so the same problem never needs deep analysis twice.

The critical rule: Isaac 1 does not analyze. Isaac 2 does not do rote recall. When Isaac 1 has no doors, it escalates. When Isaac 2 discovers a pattern, it crystallizes it into doors that Isaac 1 can walk. The boundary is absolute.

### 1.3 The One Rule

Information only enters, never leaves. If the system already has the information, the duplicate is discarded — but nothing is lost, because the information already exists in the net. Novel information always enters regardless of apparent relevance. The total information in the system never decreases.

Everything in the architecture follows from this rule. Observation adds doors but never removes them. Error correction adds missing doors — it does not delete wrong ones. The crystallizer adds type doors and constraints — it does not remove raw observations. The net grows monotonically.

---

## Part II: The Net

### 2.1 What the Net Is

The net is the knowledge substrate. Everything the system knows lives here. It is a directed graph where nodes are words (or concepts, or structural markers) and edges are doors — observed connections between nodes.

```python
class Net:
    doors: dict[str, set[str]]           # node → set of nodes it connects to
    meta: dict[str, dict]                # node → arbitrary metadata
    door_tags: dict[tuple, set[str]]     # (src, tgt) → set of tag strings
```

That's it. Three data structures. No weights, no scores, no definitions, no pointer formats, no dimensional addresses. A door exists or it doesn't. A door has tags or it doesn't. A node has metadata or it doesn't.

### 2.2 What Happened to Weights

The Isaac 2 design used 64-bit packed pointers: 8-bit signed weight + 56-bit unsigned address. Weights ranged from -127 to +127, representing accumulated evidence (positive) or structural exclusion (negative).

Weights were removed. The walker's entire operation — observation, generation, comprehension, type discovery, error correction — works without them. A door's presence IS the evidence. A door's tag IS its type. The convergence mechanism in prediction counts how many walks reach an operation, not the weight of those walks. The crystallizer's type hierarchy provides structural grouping without weighted similarity scores.

The removal of weights is not a simplification for convenience. It is a theoretical position: the net stores connections, not strengths. The strength of a pattern is an emergent property of how many doors lead to it from how many directions — that information is computable from the graph structure at any time. Storing it on each edge destroys the ability to discover new uses for the same connection. Claim 9: don't aggregate at storage time.

### 2.3 Doors

A door is a directed edge from one node to another. `net.add_door("the", "cat", tag="seq")` means: "the" was observed directly preceding "cat" in a sentence, and this is a sequential (linguistic structure) connection.

Doors are additive. `add_door` returns True if the door is new, False if it already existed. An existing door is never modified or removed. If the same connection is observed again, nothing changes — the door already exists.

### 2.4 Tags

Tags are labels on doors that indicate what KIND of connection this is. A door can have multiple tags.

| Tag | Meaning | Source |
|---|---|---|
| `seq` | Sequential — linguistic structure. A precedes B in observed sentences. | Observation |
| `neg` | Negative — observed in a BAD sentence. A precedes B in a known-wrong example. | Negative observation |
| `prop` | Property — semantic meaning. A has property B. | Teaching |
| `class` | Class membership — A belongs to modifier class B. | Seeding or crystallizer |
| `circle` | Type group — A is a member of crystallized type B. | Crystallizer |
| `type` | Condensed type — A belongs to condensed type hierarchy node B. | Crystallizer |
| `subtype_of` | Hierarchy — type A is a specialization of type B. | Crystallizer |
| `cooccurs` | Co-occurrence rule — A and B appear as predecessors of the same nodes. | Crystallizer |
| `sibling` | Sibling — A and B have similar structural profiles. | Crystallizer |
| `lockout` | Violation — A→B was found ONLY in negative examples. Generation avoids this transition. | Crystallizer (violation discovery) |

Tags enable gated walks. The walker's behavior changes depending on which tags it follows. Generation follows `seq` doors and avoids `lockout` doors. Property lookup follows `prop` doors. Violation discovery compares `seq` doors against `neg` doors. Type discovery can operate on any tag independently. The same net, the same walk mechanism, different behavior depending on the gate.

### 2.5 Metadata

Metadata is arbitrary key-value data attached to nodes. Used for:

- `"start": True` — this word has been observed starting a sentence
- `"initiator_strength": 93` — crystallizer-computed ranking of how good this word is as a sentence initiator
- `"merged_into": "cat"` — this word was identified as a duplicate and merged
- `"lockout_count": 3` — this word appeared in wrong generation attempts 3 times

Metadata is not walked. It is consulted during specific operations (initiator selection, conflict resolution) but does not participate in the door-walking mechanism.

### 2.6 Operations on the Net

| Operation | Method | What it does |
|---|---|---|
| Add a door | `add_door(src, tgt, tag)` | Creates the connection if new |
| Get outgoing doors | `get_doors(node, tag)` | Returns all targets, optionally filtered by tag |
| Get incoming doors | `get_predecessors(node, tag)` | Returns all sources that have a door TO this node |
| Check door existence | `has_door(src, tgt)` | Boolean |
| Get door tags | `get_door_tags(src, tgt)` | All tags on a specific door |
| Set/get metadata | `set_meta(node, key, val)` / `get_meta(node, key)` | Arbitrary metadata |
| All nodes | `all_nodes()` | Every node that appears anywhere in the net |
| Door count | `door_count()` | Total number of directed edges |

No delete. No modify. No weight update. Add-only.

---

## Part III: Isaac 1 — The Walker

### 3.1 Observation

The walker's primary learning mechanism. Given a sentence as a list of tokens, build sequential doors between every adjacent pair and mark the first token as a sentence start.

```python
def observe(self, sentence: list[str]):
    self.starts.add(sentence[0])
    for i in range(len(sentence) - 1):
        self.net.add_door(sentence[i], sentence[i + 1], tag="seq")
```

"The cat sat" produces: the→cat (seq), cat→sat (seq). "The" is marked as a start. That's all observation does. No parsing. No extraction. No analysis. The sentence enters as raw sequential structure.

The tokenizer separates punctuation: "The cat sat." becomes ["the", "cat", "sat", "."]. Punctuation nodes participate in the door structure. A period is a node with many predecessors (every sentence-final word) and is itself a structural signal.

### 3.2 Negative Observation

The walker can observe bad sentences — examples of how language should NOT work:

```python
def observe_negative(self, sentence: list[str]):
    for i in range(len(sentence) - 1):
        self.net.add_door(sentence[i], sentence[i + 1], tag="neg")
```

"The cat big sat" produces: the→cat (neg), cat→big (neg), big→sat (neg). These doors coexist with positive seq doors in the same net, on the same nodes. The sentence is not rejected or discarded — it is observed through a different tag. The negative meaning is not stored on any individual door. It emerges later, when the crystallizer COMPARES the neg-tagged door set against the seq-tagged door set. Doors in neg but not seq are violations. Doors in seq but not neg are rules. The comparison IS the negative meaning.

### 3.3 Comprehension (Try-Chain Learning)

Given English sentences with known numeric answers, the walker discovers which arithmetic operation produces the answer. It extracts numbers and context words, tries each operation (add, subtract, multiply, divide) with each number ordering, and when one works, builds doors from context words to that operation.

After training on "she had 5 apples and ate 2" (answer: 3), the word "ate" gets a door to "subtract." After varied training, nouns like "apples" accumulate doors to all four operations — they appear in every context. Verbs like "ate" accumulate a door to only one operation.

Prediction walks from each context word through its doors. The operation reached by the most words wins. Nouns contribute equally to all operations (noise). Verbs tip the balance (signal). The distinction between content words and function words emerges from the door structure.

No scores. No counters. No specificity formulas. Doors and walks.

### 3.4 Generation (Grouped Concept Chains)

The generation algorithm takes grouped concepts and produces a sentence. Each group is independently traced as a short backward chain, then all chains are concatenated.

**Input format:**
```python
[["cat", "big"], "slept", ["fireplace"], ["evening", "cold", "winter"]]
```

**Processing per group:**

Standalone groups (single word): Check if the word has a start-word predecessor. Nouns do ("the" → "cat"), verbs don't ("cat" → "ran"). Nouns get their initiator; verbs stand alone. The distinction is structural, not tagged.

Modified groups (anchor + modifiers): Walk backward from the anchor. At each step, prefer predecessors in the modifier set. Once all modifiers are placed, accept only a start word. Never walk through content words — that would cross sentence boundaries.

**Modifier conflict resolution:** If two modifiers share a class door (e.g., both have doors to "size_class"), they conflict. One is dropped unless "and" is in the modifier set. Classes are net structure — seeded or crystallized, not Python code.

**Deduplication:** After chains are built, scan boundaries. If chain B starts with a determiner + noun that already ended chain A, trim the redundant prefix.

**Lockout filtering:** At every step of chain building, predecessors are filtered through a lockout check. If the transition pred→current has a "lockout" tag (applied by the crystallizer's violation discovery), that predecessor is excluded. This is how negative examples feed back into generation: bad word orderings discovered from contrast become lockouts, and lockouts prevent those orderings from being generated.

```python
def _filter_lockouts(self, predecessors, target):
    return {p for p in predecessors
            if "lockout" not in self.net.get_door_tags(p, target)}
```

One line of filtering. No architectural change. The lockout tag is just another door property that the walker's gated walk respects.

**Output:** A flat list of words forming the sentence. "The big cat slept the fireplace a cold winter evening." Group ordering is free — the same concepts can be strung in any order and produce valid English.

### 3.5 Error Correction

The system tries to generate from concepts, receives the correct sentence, compares, diagnoses missing doors, adds exactly those doors, and retries.

```python
def correct(self, concept_groups, correct_words):
    attempt = self.generate(concept_groups)
    missing = [(correct_words[i], correct_words[i+1])
               for i in range(len(correct_words)-1)
               if not self.net.has_door(correct_words[i], correct_words[i+1])]
    self.observe(correct_words)  # adds the missing doors
    after = self.generate(concept_groups)  # retry
```

Each correction is targeted — typically 1-2 missing doors. The system doesn't memorize the correct sentence as a whole. It identifies specific structural gaps and fills exactly those. Corrections compound: doors learned from round 1 enable generation in round 3.

### 3.6 Type Discovery

Words that share predecessors AND successors function the same way. The walker discovers this from the door structure.

"Big" and "small" both follow "the" and precede "cat"/"dog" → same type. "Cat" and "dog" both follow adjectives and precede "ran"/"sat" → same type.

If two words are the same type, and one has a door the other doesn't, the missing door is inferred and added. This is the walker's basic inference mechanism — same-type words borrow each other's doors. The inference is tagged with the same tag as the original, maintaining gate separation.

### 3.7 Gated Doors

Different kinds of doors enable different kinds of reasoning. Sequential doors (seq tag) encode linguistic structure — word order, grammar patterns. Property doors (prop tag) encode semantic meaning — cat is furry, dog is loyal.

Type discovery operates per tag. The same words may group differently depending on which doors are examined. Cat and dog are the same LINGUISTIC type (same seq doors — both work the same way in sentences) but may be different SEMANTIC types (different prop doors — cats meow, dogs bark).

The walker's current function determines which doors it follows. This is the gate mechanism. No separate gate module — the tag parameter on `get_doors()` IS the gate.

---

## Part IV: Isaac 2 — The Crystallizer

### 4.1 The Comparator

The only cognitive primitive. Adapted from the Isaac 2 pointer-list version to work on door sets.

Given two nodes, the comparator examines their full door profiles (outgoing doors + incoming predecessors) and produces:

- **Shared:** Present in both profiles
- **Absent A:** In A's profile but not B's
- **Absent B:** In B's profile but not A's
- **Jaccard similarity:** |shared| / |shared ∪ absent_a ∪ absent_b| × 100

No weights. No divergent category (there are no opposite-sign connections without weights). A door is present or absent. The comparison is definite.

The same comparison operation is applied to nodes (circle discovery), to circles (class discovery / condensation), to types (hierarchy building), to predecessors (rule discovery). Different inputs, same operation.

### 4.2 The Crystallization Process

The crystallizer operates in five sequential steps, running after observation, not during.

**Step 1 — Raw Circle Discovery.** FCA-style (Formal Concept Analysis) closure on door profiles. For every pair of nodes sharing at least one predecessor AND one successor:

1. Compute shared predecessors and shared successors
2. Find ALL nodes in the net that have ALL of those shared preds and succs (the extent)
3. Re-intersect: compute the preds and succs shared by ALL members of the extent
4. Repeat steps 2-3 until stable
5. The stable (extent, intent) pair IS the concept — the natural grouping

From 379 sentences of training text, this produces 459 raw circles. Each circle has a unique member set and a unique pred/succ signature because FCA closure is maximally specific.

**Step 2 — Condensation.** The crystallizer's own output is crystallized. Three sub-phases:

*Phase 1 (Merge):* Sort circles by size (largest first). For each circle, scan all smaller circles. If the overlap between two circles' member sets, relative to the smaller set, exceeds 80%, they are seeing the same structural pattern from different seed pairs. Merge: take the union of members (the fuller picture) and the intersection of preds/succs (what they agree on). 459 raw → 235 merged.

The theoretical basis for merging: two random samples of the same population each miss a different subset. Neither captures the full group. Their union approximates it better than either alone. The members present in A but not B, and in B but not A, are both probably valid members. The intersection of structural requirements (preds/succs) is what both samples confirm.

*Phase 2 (Hierarchy):* After merging, build parent/child relationships. A circle is a child of a larger circle if 80%+ of its members appear in the larger circle. Skip trivial refinements where the overlap exceeds 95% and no new structural information (preds/succs) is contributed.

*Phase 3 (Recursive Stabilization):* The crystallizer crystallizes its own hierarchy. If a type's predecessor word is itself a member of another type, the first type is a sub-behavior of the second. `man→?[8]` describes what follows "man." "Man" is a member of `the→?[64]` (nouns). Therefore `man→?[8]` is a child of `the→?[64]` — it describes noun-verb behavior.

The parent must be larger than the child (preventing inverted hierarchies). Cycle detection prevents circular parent chains. The loop continues until no new parent assignments are made (stabilization).

Result: 235 types → 59 roots, max depth 5. The largest tree (`the→?[64]`, the noun type) has 294 nodes in its subtree.

**Step 3 — Rule Discovery.** Co-occurrence patterns among predecessors. For each pair of predecessors that each precede at least 3 different nodes: if 80%+ of the nodes preceded by A are also preceded by B, that's a structural rule (A implies B). 41 rules discovered from the training corpus.

**Step 4 — Initiator Ranking.** Start words (words that have begun observed sentences) are ranked by their outgoing door count. Higher count means the word precedes more different words, indicating it's a function word (determiner, auxiliary) rather than a content word. "The" (93 outgoing doors) ranks highest. "Is" (36) is high but context-dependent. "Later" (2) is low — it's a content word that happened to start a sentence.

Initiator strength is stored as node metadata and consulted by the generation algorithm when selecting which start word to use as a chain initiator.

**Step 5 — Application.** The condensed type hierarchy is written into the net as tagged doors. Each member of a type gets a door to the type name with tag "type." Type-to-parent relationships get doors with tag "subtype_of." 824 type doors applied from the training corpus.

### 4.3 What the Crystallizer Discovered

From 379 sentences of children's text, with zero linguistic knowledge:

**Noun type** (`the→?[64]`): 64 words preceded by "the" and followed by ".": cat, dog, boy, girl, horse, house, fire, water, sun, ball, bird, book, cow, farm, fish, hen, milk, nest, school, and 45 others.

**Adjective/predicate type** (`?→?[27]`): 27 words preceded by "is" and followed by ".": big, bright, clear, cold, dangerous, friendly, green, happy, hard, hot, kind, old, quiet, round, small, smart, still, warm, wet, white, young, and 6 others.

**Indefinite noun type** (`a→?[31]`): 31 words preceded by "a" and followed by ".": barn, bee, big, book, boy, car, cart, cat, cow, dog, door, farm, fat, horse, house, lion, nest, pen, story, tortoise, tree, and 10 others.

**Conjunct type** (`and→.[21]`): 21 words preceded by "and" and followed by ".": things that appear as the second element in conjunctions.

**Noun-before-conjunction type** (`the→and[15]`): Nouns that precede "and" — indicating compound structures.

**Infinitive type** (`to→.[15]`): 15 words preceded by "to" and followed by ".": drink, eat, fly, grow, jump, learn, live, play, read, skate, sleep, try.

**Modal complement type** (`can→.[8]`): 8 words preceded by "can": bounce, fly, go, jump, sing, swim, talk.

**Verb sub-behaviors:** Within the noun tree, subtypes describe what specific nouns do. `man→?[8]` contains the verbs/prepositions that follow "man." `bird→the[6]` contains what follows "bird." These are verb groups organized by their typical subjects.

**Initiator quality ranking:** "The" (93) >> "a" (41) >> "is" (36) >> "can" (21) >> "she" (17) >> "it" (14). This ranking directly addresses the generation quality problem: "the" is the best initiator for noun phrases, "is" should not initiate noun phrases despite being a start word.

**Structural hierarchy at five levels:** Nouns → nouns with properties → what those nouns do → what those verbs connect to → what those prepositions lead to. Grammar as a door hierarchy.

### 4.4 Violation Discovery (Negative Meaning)

The crystallizer can compare two tagged door sets to discover what makes bad sentences bad. When the walker has observed both positive examples (seq-tagged) and negative examples (neg-tagged), the crystallizer runs `discover_violations()`:

1. **Collect** all seq doors and all neg doors from the net.
2. **Compare:** neg_doors - seq_doors = violations (patterns ONLY in bad sentences). seq_doors - neg_doors = rules (patterns ONLY in good sentences). Intersection = ambiguous (the transition appears in both — the violation is elsewhere in the sentence).
3. **Order rules:** For each violation A→B, check if B→A is a rule. If so, the word pair has a correct direction. "Cat→big" is neg-only (violation), "big→cat" is seq-only (rule) → order rule: big before cat, not cat before big.
4. **Type-level analysis:** For each violation, check the types of the source and target nodes. If both have types, the violation can be described structurally: "adjective-type word followed by verb-type word" rather than just "big followed by sat."
5. **Apply lockouts:** Violations are written back to the net as "lockout" tagged doors. The generation algorithm filters these during chain building, preventing the walker from producing patterns only observed in bad sentences.

From 14 positive and 8 negative sentences about adjective-noun order, the crystallizer discovered all 8 correct word orderings and applied lockouts that made generation produce correct order in every test case.

The mechanism is general. Any structural contrast between positive and negative observation sets produces rules. Word order, agreement patterns, semantic constraints — all discoverable through the same comparison.

---

## Part V: How the Pieces Connect

### 5.1 The Data Flow

```
Text input (good examples)
    ↓
Tokenize → Observe (build seq doors)
    ↓
[Net grows with positive structure]

Text input (bad examples)
    ↓
Tokenize → Observe Negative (build neg doors)
    ↓
[Net grows with negative structure]

    ↓
Crystallize (periodic, not per-input)
    ↓
[Types, rules, initiator rankings added to net]
    ↓
Discover Violations (compare seq vs neg)
    ↓
[Lockouts added to net]
    ↓
Generate (grouped concepts → chains → sentence)
  ├─ uses initiator rankings
  ├─ uses type membership
  └─ avoids lockouts
    ↓
Error correct (if wrong: diagnose → add doors → retry)
    ↓
[Net grows more precisely]
```

The crystallizer runs after batches of observation, not after every sentence. It operates on the net's accumulated structure, not on individual inputs. Its discoveries (types, rules, rankings, lockouts) are written back into the net as tagged doors and metadata, which subsequent generation and comprehension walks can use.

### 5.2 Generation Uses Crystallizer Output

When building a chain for a concept group, the generation algorithm consults:

- **Initiator ranking** (from crystallizer): When selecting a start word from multiple candidates, pick the one with highest `initiator_strength` metadata. "The" (93) beats "is" (36) beats "later" (2).
- **Type membership** (from crystallizer): A modifier's type can be checked against the anchor's type to validate that the combination makes structural sense. An adjective-type word preceding a noun-type word is valid. A verb-type word preceding a noun-type word is suspicious.
- **Class doors** (seeded or crystallized): Same-class modifiers within a group conflict. The walker checks class doors to detect and resolve conflicts.

### 5.3 Comprehension Uses Crystallizer Output

The try-chain comprehension system benefits from type awareness:

- **Signal/noise separation:** Words in verb-like types (few operation doors) are signal. Words in noun-like types (many operation doors) are noise. Type membership makes this explicit before the convergence count is even computed.
- **Error analysis:** When comprehension makes a wrong prediction, the crystallizer can identify the structural role of the words that misled it. If a word's type indicates it should be noise but it incorrectly tipped the balance, the type hierarchy explains why.

### 5.4 Morphology Uses Type Membership

The crystallizer enables morphological discovery:

- "Cat" and "cats" both land in the noun type (same predecessors, same successors in sentence structure).
- The crystallizer compares same-type word pairs: they differ by suffix "s."
- That suffix pattern IS the plural rule, discovered from structure, not taught.
- Similarly: "run"/"ran"/"running" share verb-type membership. The morphological relationship emerges from type comparison.

This has not been implemented yet but the mechanism is clear: the StringPatternLearner from Session 8e can be driven by type membership rather than explicit teaching. Same-type words that differ by consistent affixes are morphological variants.

### 5.5 The Feedback Loop

```
Observe good → Net grows → Crystallize → Types refine →
Observe bad → Discover violations → Lockouts applied →
Generate better → Error correct less → Net grows more precisely →
Crystallize again → Types refine further → ...
```

Each loop makes the system better at all three tasks simultaneously. Better types mean better generation. Lockouts prevent known-bad patterns. Better generation means fewer corrections. Fewer corrections mean cleaner door patterns. Cleaner patterns mean better crystallization. The loop is closed and self-improving.

Negative examples accelerate the loop. Without them, the system must wait to make a mistake, be corrected, and learn from the correction. With them, the system can be taught entire categories of mistakes preemptively. "These sentences are wrong" provides constraint information that positive examples alone cannot supply — it establishes boundaries, not just examples.

---

## Part VI: What Was Removed

### 6.1 The Pipeline (5,234 lines → 0)

The Isaac 2 pipeline implemented five-stage processing: Context Detection → Enrich → Interact → Gate → Integrate. Each stage is replaced by the walker's simpler mechanism:

- Context Detection → not needed (net is cumulative, mode is caller-determined)
- Enrich → `observe()` (doors are the enrichment)
- Interact → convergence counting via walks (not cartesian products of definitions)
- Gate → try-chain (not scored activation maps)
- Integrate → `observe()` / `error_correct()` (doors, not weighted edges)

### 6.2 The Weighted-Pointer Infrastructure (1,636 lines → 0)

- `net.py` (250 lines): Weighted-pointer net with definitions, backlists, scopes, dirty tracking → replaced by the walker's three-field Net class
- `node.py` (239 lines): Multi-definition nodes with shared pointers, scope visibility, combined sorted pointer lists → not needed (words are nodes, doors are connections)
- `pointer.py` (91 lines): 64-bit packed weight+address format → not needed (no weights)
- `seed.py` (1,056 lines): Initial knowledge seeding with weighted pointers → replaced by observation and optional class seeding

### 6.3 Supporting Infrastructure (2,890 lines → 0)

- `persistence.py` (674 lines): Save/load with snapshots and deltas → deferred (future feature)
- `state_log.py` (412 lines): Telemetry, ingestion records, performance tracking → not needed
- `world_state.py` (471 lines): Entity tracking, state snapshots, projections → not needed for language processing
- `goal_manager.py` (806 lines): Goal decomposition, monitoring, execution → deferred (future reasoning)
- `lift.py` (527 lines): Sandbox evaluation, promotion/reversion → not needed (crystallizer applies directly)

### 6.4 Tests and GUI (7,709 lines → 0)

Separate test files (4,210 lines) and Flask GUI (3,499 lines) are not part of the core architecture.

### 6.5 What Remains

- `crystallizer.py` (1,548 lines original → ~350 lines adapted): Stripped of pipeline dependencies, rebuilt for door sets. The core operations (circles, rules, anomalies, hierarchy, stabilization) translated cleanly.
- `comparator.py` (242 lines original → ~30 lines adapted): The compare function on door sets instead of pointer lists.
- `reasoning.py` (753 lines): Untouched, for future escalation. Goal decomposition, causal chains, solution generation.
- `aoa.py` (510 lines) and `rules.py` (440 lines): Seed knowledge. Noun/verb/adjective categories, POS rules, modifier patterns. Available for net seeding but not required — the crystallizer discovers equivalent structure from observation.

### 6.6 Net Reduction

The full Isaac 2 codebase: approximately 13,274 lines of Python across 16 files.
After removal: approximately 1,150 lines of active code (walker + crystallizer).
Reduction: 91%.

The walker (800 lines) does everything the pipeline (5,234 lines) did, plus generation and learning. The crystallizer (350 lines) does everything the original crystallizer (1,548 lines) did, without the pipeline dependency overhead.

---

## Part VII: What Remains to Be Built

### 7.1 Immediate (Next Session)

**Wire crystallizer into generation.** The crystallizer produces initiator rankings and type hierarchies. The generation algorithm needs to consult them during chain building: use `best_initiator()` for start-word selection, check type membership for modifier validation, use the hierarchy to constrain which words can precede which.

**Morphology integration.** The StringPatternLearner from Session 8e and the teach_irregular mechanism from Session 8f need to be connected. Two approaches were discussed: (a) keep them as separate classes that the walker consults, or (b) drive them from the crystallizer's type membership comparison. Either works — the designer said to try one then the other.

**Pred/succ loss during merging.** When circles are merged, preds and succs are intersected (only keeping what ALL merged circles agree on). This is too aggressive — it loses determiners when noun circles from "the" contexts and "a" contexts are merged. Fix: majority vote (keep preds appearing in 70%+ of merged circles).

### 7.2 Near-Term

**Modifier ordering.** The crystallizer discovers that adjectives precede nouns and determiners precede adjectives, but not the ordering within adjective classes. The mechanism: compare observed positions of adjective-type words across many sentences to discover that size precedes color precedes origin. Discoverable from data but the positional comparison is not yet built.

**Merge threshold tuning.** The anomaly detector merged "tree" and "cart" because they have identical door profiles in the training corpus. This is a false positive — they need more observations to diverge. The merge threshold needs a minimum observation count or a deferral mechanism.

**Rejection pool equivalent — partially addressed.** The walker now has `observe_negative()` for external negative examples, and the crystallizer's `discover_violations()` compares neg-tagged doors against seq-tagged doors to find and enforce structural violations as lockouts. What remains is SELF-DETECTION: the walker generating output, checking it against the type hierarchy, and flagging type-constraint violations as internal negative examples without being told. This would close the loop: generate → self-assess → self-correct.

### 7.3 Future

**The escalation interface.** When Isaac 1's try-chain bottoms out, what gets handed to Isaac 2's reasoning module? The concept packet — grouped concepts that failed, the walk state, the type memberships of stuck nodes — needs to be defined. The reasoning module (753 lines, untouched) handles goal decomposition, causal chains, and solution generation.

**Complex sentence handling.** All testing uses simple sentences (3-8 words). Embedded clauses, relative structures, passive voice, and compound-complex sentences are untested. The kenku principle predicts the mechanism extends (more complex observations create more complex door chains), but this is unverified.

**Scale to real language.** 379 sentences produced 577 nodes and 1,739 doors. Real language use involves millions of sentences. Whether the crystallizer's FCA closure, which is O(n²) on the number of nodes, remains tractable at large scale is an open question. The condensation reduces the working set but the raw discovery pass is the bottleneck.

**Persistence.** The net exists only in memory during a session. Save/load (snapshots, deltas) was part of the Isaac 2 infrastructure and needs to be rebuilt for the walker's simpler net structure.

**Vision integration.** The Isaac Vision System Design describes a recognition pipeline (attention → shape → surface → color → identity) that maps directly to the language pipeline (tokenize → enrich → interpret → gate → integrate). The walker's architecture should handle visual input through the same door mechanism — visual features as nodes, spatial relationships as doors. This is designed but entirely unimplemented.

---

## Part VIII: Theoretical Implications

### 8.1 Claim 8 Confirmed: Same Operation at Every Scale

The Comparator (shared/divergent/absent) is applied to:

- **Nodes:** Circle discovery. Two nodes' door profiles compared → shared doors found → type group.
- **Circles:** Class discovery. Two circles' member sets compared → shared members found → superclass.
- **Types:** Hierarchy. A type's predecessor checked against another type's members → parent relationship.
- **Rules:** Predecessor co-occurrence. Two predecessors' following-node sets compared → implication rule.
- **Self:** The crystallizer's output compared against itself → condensation, merge, stabilization.
- **Tag sets:** Violation discovery. Seq-tagged doors compared against neg-tagged doors → violations, rules, order constraints.

One operation. Six scales. All producing the same kind of result (what's shared, what's not) with different actions dispatched on the result.

### 8.2 Claim 9 Confirmed: Store Raw, Derive on Demand

The net stores sequential doors. Nothing is aggregated at storage time.

From those raw doors, the system derives:

- **Type membership:** Which words share structural roles
- **Grammar:** Which positions words can occupy
- **Initiator quality:** Which starts are function words vs content words
- **Modifier classes:** Which adjectives conflict
- **Morphological relationships:** Which words are variants of each other
- **Hierarchical structure:** Five levels of structural role nesting
- **Violations and rules:** Which transitions are bad (from neg/seq contrast)
- **Order constraints:** Which word pairs have a correct direction

All of these are derived on demand by the crystallizer. None are stored as pre-computed aggregates. The raw doors support all current uses and all future uses that haven't been discovered yet.

### 8.3 Claim 7 Confirmed: Correctability Over Correctness

The system makes mistakes. "Is old woman walked" is wrong. But:

- The error is DETECTABLE: "is" in initiator position violates the type hierarchy
- The error is DIAGNOSABLE: "is" is a predicate-type word, not an initiator-type word
- The error is CORRECTABLE: error correction adds the right doors, the type hierarchy prevents recurrence
- The correction COMPOUNDS: the same structural insight (predicates aren't initiators) applies to all similar cases

The system doesn't need to be right the first time. It needs every mistake to teach something, and every correction to prevent a class of future mistakes. This is architecturally guaranteed by the feedback loop: generate → compare against correct → add missing doors → crystallize → prevent same error type.

### 8.4 The Kenku Principle at Scale

Generation is recombination of observed fragments. Each chain is a fragment the net has seen. The grouped generation mechanism ensures fragments stay coherent (short chains, no hub contamination). The type hierarchy enables recombination: if two words share a type, fragments containing one can be recombined to contain the other.

With 379 sentences, the system produces novel sentences that nobody wrote — "the big cat barked," "the small dog jumped" — by recombining "the big [dog]" with "[cat] barked." The type system confirms cat and dog are the same type, so the recombination is licensed. Without the type system, the walker would need to have directly observed "big cat" to use it. With types, observing "big dog" and knowing cat≈dog is sufficient.

This is how language works. Nobody invents grammar from scratch. They recombine observed fragments, licensed by structural similarity. The net's door structure IS grammar. The crystallizer's type hierarchy IS the licensing.

### 8.5 Negative Meaning Without Negation

The system has no concept of "not." No negative weights, no anti-doors, no boolean flags marking things as false. Yet it learns what NOT to do.

The mechanism: tag separation plus comparison. Good observations get one tag. Bad observations get another. The same nodes, the same doors, the same net. The Comparator runs on the two tag sets and the DIFFERENCE is the negative meaning. Doors in neg but not seq are violations — patterns that define wrongness. Doors in seq but not neg are rules — patterns that define correctness.

This has a profound implication: negative knowledge is always relative. "Wrong" is defined by contrast with "right." As the positive observation set grows, what counts as a violation may change. A door that was neg-only (violation) becomes ambiguous when it's also observed in a good sentence. The system's understanding of wrongness evolves with its understanding of correctness. There is no absolute wrong — only contrast.

This maps to how humans learn constraints. We don't store "adjective-after-noun is forbidden" as an abstract rule. We store "I've never heard adjective-after-noun work" alongside "I've always heard adjective-before-noun work." The constraint is the gap between two observation sets, not a stored prohibition.

### 8.6 What This Architecture Is Not

It is not a neural network. There are no continuous weights, no gradient descent, no interpolation, no attention mechanism, no transformer layers. The net is a discrete graph with binary edges.

It is not a rule-based system. There are no handcoded grammar rules, no production systems, no if-then chains. Structure emerges from observation and is discovered by the crystallizer.

It is not a statistical model. There are no probability distributions, no likelihood estimates, no Bayesian updates. The convergence mechanism counts walks, not probabilities.

It is not a hybrid. It does not combine symbolic and subsymbolic processing. Everything is symbolic (nodes and doors) but the symbols emerge from observation rather than being assigned by a designer.

It is a comparison engine. One operation. Applied to the system's own structure. Recursively. Until stable.

---

## Part IX: File Reference

### Active Code

| File | Lines | What it does |
|---|---|---|
| `walker_s10.py` | ~830 | Isaac 1: Net, observation (positive and negative), comprehension, grouped generation (with lockout filtering), error correction, type discovery, gated doors, modifier classes, deduplication. 19 tests. |
| `crystallizer.py` | ~400 | Isaac 2 (adapted): Comparator, raw circle discovery, merge condensation, hierarchy building, recursive stabilization, rule discovery, initiator ranking, violation discovery, lockout application. |

### Test & Diagnostic Code

| File | Lines | What it does |
|---|---|---|
| `stress_test_s10.py` | ~250 | Scale test: 379 sentences, hub analysis, generation quality, chain length audit. |
| `test_crystallizer.py` | ~200 | Crystallizer integration test: initiator ranking, generation with feedback, comparator examples. |
| `meta_crystallize.py` | ~150 | Meta-analysis: patterns within the crystallizer's patterns. |

### Reference (not actively used)

| File | What it is |
|---|---|
| `walker_s9_english.py` | Clean Session 9 walker (original, untouched) |
| `walker_s10_grow.py` | Failed Session 10 attempt (preserved as reference of what not to do) |
| `isaac/` directory | Full Isaac 2 codebase (13,274 lines, largely superseded) |
| `walker_sessions/` | Sessions 7-8f code and documentation |
| `Isaac_Engine_Proposal_v2.2.md` | Original engine specification |
| `Theory_Reference.md` | Four theoretical papers consolidated |

---

## Part X: The State of Isaac

Isaac is a working prototype that demonstrates the core theoretical claims. One operation (comparison) applied recursively produces: type discovery from raw observation, hierarchical grammar from sequential doors, generation from recombined fragments, self-correction from structural analysis, a five-level type hierarchy from 379 sentences of children's text, and negative meaning from contrasting good and bad examples.

The walker (Isaac 1) handles Type 1 processing: observation (positive and negative), generation (with lockout avoidance), comprehension, error correction, type discovery, gated walks. The crystallizer (Isaac 2) handles Type 2 processing: structural analysis, condensation, hierarchy building, rule discovery, recursive stabilization, and violation discovery from tag-set contrast.

The pipeline is gone. The weights are gone. Negation is not a stored flag — it is a derived property of comparing two observation sets. What remains is a directed graph of doors, a walk mechanism, and a comparison operation that runs on the graph's own structure to discover what the graph contains — including what it should not produce.

That's Isaac.
