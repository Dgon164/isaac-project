# Isaac — SIS Engine Proposal

## The Rebuild Specification

**Date:** May 6, 2026
**Version:** 2.2 — Retroactive encapsulation, encapsulation as fourth contradiction route
**Status:** Foundation document for rebuild. Derived from 43 iterations, four theory papers, and the lessons of every failure.

---

## The One Rule

Information only enters, never leaves. If the system already has the information, the duplicate is discarded — but nothing is lost, because the information already exists in the net. Novel information always enters regardless of apparent relevance. The total information in the system never decreases.

Everything else in this document follows from that rule.

---

## What Intelligence Is

Intelligence is one operation — comparison — recursively applied. The Comparator takes two things and produces three outputs: what they share, where they diverge, and what's absent. That's it. Every other behavior — pattern recognition, abstraction, planning, learning, self-correction, creativity — emerges from applying that operation at different scales to different inputs, including its own outputs.

The system does not interpolate. It does not guess. It differentiates. The result of a comparison is definite: same or different, shared or divergent, present or absent. Everything built on this foundation inherits that definiteness.

---

## What the System Does

The system takes in information, enriches it, selects the structurally densest interpretation, integrates what's novel, and learns from everything — including its own mistakes. It does this through one pipeline with five stages and a closed feedback loop.

---

## The Pipeline

### Stage 0 — Context Detection

Before enrichment begins, the system determines what kind of input this is. One Comparator call between the new input's initial profile and whatever context is currently live.

**Three outcomes:**

**Continuation.** High overlap with the current live context. This sentence chains onto what came before. "Blue is also a color" after "Red is a color." The previous activation map stays live. The enrichment step pulls from it. "Also" makes sense because the prior context is still active. The merge pyramid accumulates — this sentence merges with the previous one at the sentence-pair level.

**New context.** Low overlap with the current live context. This is unrelated — a new book, a different topic, a fresh conversation. The previous activation map is cleared or archived. The merge pyramid starts a new branch. Clean slate for enrichment.

**Query.** Question pattern markers plus reference to content already in the net or recently processed. "Is red a color?" after teaching it "red is a color." The system isn't learning new information — it's being asked to retrieve and verify. The pipeline behavior shifts: enrich and COMPARE against the net, don't integrate. The answer is already in there.

**Metastructural shortcut.** Before any of the above, the system checks one more thing: does this input match a known metastructural node? If the activation shape of the incoming input matches a cached whole-net pattern, the system can skip the full pipeline and go straight to the crystallized response. (See Metastructural Nodes below.)

**Detection is a Comparator call.** Enrich the input minimally — just enough to get a rough dimensional profile. Compare it against the current live context. The density of overlap IS the continuity signal. No hardcoded modes. No mode flag. The math tells you.

### Stage 1 — Enrich

Input arrives. Before any comparison or selection, the system makes the input RICHER. This is the sensory organ. Without it, information cannot make contact with the net and the system is deaf.

**What happens:**

Every token in the input is resolved against the net. Every definitional version is pulled. Every inherited trait from every class is attached. Every known pattern the input could match is noted. The system runs what() on every piece — one word in, full dimensional map out.

The raw input "red is a color" becomes:

- "red" → def:0 adjective (visual-property, warm-spectrum, high-salience), def:1 noun (political-alignment, left-spectrum), def:2 noun (informal, embarrassment). Each with full pointer profiles. Each carrying inherited traits from its classes.
- "is" → copula, identity-assertion, IS_A-candidate, equation-marker. Pattern trigger for X-is-a-Y.
- "a" → indefinite article, singular, category-introduction.
- "color" → def:0 noun (visual-property, perception, wavelength-spectrum), def:1 noun (appearance, character), def:2 verb (to apply pigment). Full profiles.

The enrichment also generates structural metadata:

- Sentence pattern candidates: X-is-a-Y (IS_A), X-is-a-Y (identity), X-is-a-Y (example).
- Type interactions: adjective-copula-noun, noun-copula-noun.
- Position signals: "red" at subject position, "color" at predicate position.

Nothing is selected yet. Nothing is discarded. The input went from 5 tokens to 5 tokens × N definitional versions × M inherited traits × P pattern candidates. The space got wider, not narrower.

**The principle:** You cannot learn about something you cannot sense. Enrichment creates the surface area for contact between input and net. More surface area = more potential contact = more potential learning. The enrichment step is not preprocessing. It IS the sensory system.

### Stage 2 — Interact

The enriched definitional versions are assembled into complete sentence interpretations. Every combination of definitions across all tokens produces a candidate interpretation — a full dimensional profile of what the sentence means.

**What happens:**

"Red is a color" with red having 3 definitions, is having 2 readings, and color having 3 definitions produces 3 × 2 × 3 = 18 possible complete sentence interpretations. Each is a full picture — all the pointers from the selected definitions combined.

**Pruning by impossibility:** Before assembling, the logic gates eliminate combinations that can't coexist. If red:political has a proven divergence against color:visual-category, that combination never gets assembled. This cuts the space before the expensive work.

For each surviving interpretation, lay all the words' dimensional profiles on top of each other. The interaction step counts how many words touch each dimension — co-activation, not weight. This produces the activation map that Stage 3 scores.

**The principle:** The unit of comparison is the whole interpretation, not the individual token. You're not asking "does red match color?" word by word. You're asking "which complete reading of this sentence holds together best?"

### Stage 3 — Gate

The logic gates score the surviving interpretations using activation density and select the winner.

**The Activation Map:**

For each candidate interpretation, lay all the words' dimensional profiles on top of each other. Each unique dimension is a slot. Each word that touches that slot is recorded — which word, at which position.

**Example — "red is a color" under the visual interpretation:**

```
visual-property:     red(pos:0) ✓  color(pos:3) ✓  → count: 2
warm-spectrum:       red(pos:0) ✓                   → count: 1
high-salience:       red(pos:0) ✓                   → count: 1
perception:          red(pos:0) ✓  color(pos:3) ✓  → count: 2
wavelength-spectrum:               color(pos:3) ✓  → count: 1
```

**The raw activation map travels in the bundle. Not a score. The map.**

The map contains:

- **Which dims activated.** The full list.
- **Activation count per dim.** How many words touched each one.
- **Peak.** The highest activation count on any single dim. (Here: 2)
- **Average.** Mean activations across all active dims. (Here: 7/5 = 1.4)
- **Low.** The minimum count. (Here: 1)
- **Position.** Which word at which position triggered which dim. The spatial structure of the activation.

This is three levels of meta-structure:

- **The pattern as a whole.** Total dims, peak, average, distribution shape. What IS this interpretation?
- **The pattern in its place.** Which positions activated which dims. Where does the meaning concentrate in the sentence?
- **The pattern in relation.** How does this map compare against other interpretations' maps? Where do they overlap, where do they diverge?

**Why the map, not a score:**

The density score (sum_activations × 100 // total_dims) and the confidence score (Comparator output) are both derivable from the map at any time. But the map cannot be recovered from the scores. Scores destroy information. The map preserves it.

Isaac can discover that peak matters more than average for short sentences. Or that position clustering predicts correctness better than raw count. Or that the gap between peak and low signals ambiguity. Or something nobody has thought of. The raw data supports all of those discoveries. Pre-computed scores support none of them.

**Scores are derivable conveniences, not the data.** Isaac can compute them whenever needed. The map is what travels.

**Selection from the map:**

The gates read the activation maps of all candidate interpretations. The starting heuristic for selection: highest average activation across dims (the density score, derivable as sum_activations × 100 // total_dims). Floor of 100 means no word shared any dim with any other word — structurally empty. Above 100 means words interact.

But this is just the starting heuristic. The selection criterion is itself a learnable node structure. Isaac experiments with what works through the sandbox loop. Maybe peak matters more than average. Maybe the position distribution matters. Isaac finds out from the raw data.

**The output:** One selected interpretation (with its full activation map) AND all non-selected interpretations (each with their full activation maps and metadata about why they lost).

### Stage 4 — Integrate

The selected interpretation — with its full activation map — makes contact with the net.

**What happens:**

The Comparator runs between the selected interpretation and the existing net:

**If novel:** The information does not already exist in the net. It is integrated. New edges created. New structural connections established. The net grows. IS_A(red, color) did not exist → it now exists. The node for "red" gains a pointer to "color." The node for "color" gains a back-list entry from "red." Bidirectional sync immediate.

**If redundant:** The information already exists in the net. IS_A(red, color) was already known. Confidence may be updated. The duplicate is discarded — but nothing is lost because the net already has it. The information is being used, not stored twice.

**The Comparator is the gate between novel and redundant.** One call. Does this already exist or doesn't it? Match = confirm and discard the packaging. No match = novel, integrate it.

**The principle:** The net grows with novelty, not with volume. Feed it the same book twice and it barely grows. Feed it a new domain and it grows fast. Storage scales with information content, not with input volume.

### Stage 5 — Redirect and Learn

Everything that was not selected in Stage 3 goes to a rejection pool. This pool is not trash. It is a structured learning resource.

**What happens:**

The non-selected interpretations are stored with metadata about why they lost:

- What was the activation state when they were rejected?
- Which gate conditions did they fail?
- What structural density score did they have?
- What did the winning interpretation have that they didn't?

This rejection pool serves three functions:

**Negative crystallization.** The crystallizer examines the rejection pool for patterns. "Political-alignment interpretations of color words consistently lose to visual-property interpretations in descriptive contexts." That pattern IS structural knowledge about how language works. It becomes a gate condition that makes future selections faster and more accurate.

**Error detection.** If the selected interpretation later turns out to be wrong — the system generates an incorrect output, or new evidence contradicts the selection — the rejection pool is checked. Was the correct answer already there? If so, the gates made a bad selection. The specific gate conditions that chose wrong are identified and corrected through contradiction-driven rewiring.

**Confidence calibration.** Interpretations that consistently lose across many inputs, in many contexts, with the same structural profile, gradually become marked as low-confidence definitional versions. They don't get deleted — they get deprioritized. The system learns which interpretations are generally weak without destroying them for the rare case where they're right.

**After learning, the rejection pool for that input is cleared.** The system has extracted everything useful from it. The information — the patterns, the gate improvements, the confidence adjustments — now lives in the net and the gates. The packaging can go.

**The principle:** Every decision the system makes, right or wrong, generates structural knowledge. Correct selections confirm gate conditions. Incorrect selections trigger rewiring. Rejected interpretations teach the system about what doesn't work and why. The feedback loop is closed. Nothing is wasted.

---

## The Net

The net is the knowledge substrate. Everything the system knows lives here.

### Structure

Every piece of knowledge is a **node**. Words, concepts, phrases, patterns, styles, categories, relationships, tense markers, temporal locations, grammatical roles — all nodes, all the same structure. There is one data structure. Everything lives in it.

**A node contains:**

- **Identity.** ID (positional — node 201 is at index 201), name, creation timestamp, last accessed timestamp, source (seed, emerged, learned, corrected).
- **Definitions.** One or more. Each definition has a modality (noun, verb, visual, auditory, etc.), human-readable text, and its own weighted pointer list. Definitions are structurally isolated — pointers on def:0 do not blend with def:1.
- **Shared pointers.** Apply to all definitions. "Dog" is animate regardless of which sense.
- **Back-list.** Every node that points TO this node, with weights. Bidirectional sync on every update. Not optional.

**Example — a word node:**

```
=== 201 ===
name: dog
created: 2026-05-06
source: wordnet

--- def:0 noun ---
a domesticated canine kept as a pet
+127:animal +120:canine +115:pet +100:domestic -100:wild

--- def:1 noun ---
a close friend, slang
+110:informal +80:positive_mood -80:animal

--- shared ---
+127:noun +127:concrete +127:animate

--- backlist ---
+127:canine +100:pet +80:loyal +50:fetch
```

**Example — a tense node:**

```
=== 80001 ===
name: past_tense
created: 2026-05-06
source: seed

--- def:0 temporal ---
an event that has already occurred
+127:temporal +127:completed +120:before_now -127:future

--- shared ---
+127:tense +127:grammatical

--- backlist ---
+100:ran +100:walked +100:said +90:built +80:discovered ...
```

The past_tense node's back-list is every past-tense word in the system. "Ran" has +100:past_tense in its pointer list. When the system encounters a new word in past-tense form, it adds a pointer to past_tense and past_tense's back-list grows. The Comparator can compare past_tense against present_tense and get shared/divergent/absent — they share "tense" and "temporal," diverge on "completed/ongoing" and "before_now/at_now." The system reasons about tense the same way it reasons about anything else.

**Example — a temporal location node:**

```
=== 90501 ===
name: 1066
created: 2026-05-06
source: learned

--- def:0 date ---
a year in the medieval period
+127:past_tense +120:medieval +110:11th_century +100:historical

--- shared ---
+127:temporal_location +127:year +127:number

--- backlist ---
+120:battle_of_hastings +100:norman_conquest +80:william_the_conqueror
```

"1066" is a node. "Tuesday" is a node. "During the war" is a phrase node. All temporal structure lives in the graph where the Comparator can touch it and the crystallizer can find patterns in it. A query like "what happened in 1066?" is a Comparator call between the 1066 node and the event nodes in its back-list neighborhood.

### Pointers

The 64-bit pointer format:

```
[ 8-bit signed weight | 56-bit unsigned address ]
```

- Weight range: -127 to +127. Signed integer.
- Address space: 56-bit unsigned. 72 quadrillion possible nodes.
- Positive weight = accumulated evidence. Incremented by activation count each encounter. "I have seen this much evidence for this connection."
- Weight 0 = no pointer exists. Unknown. Never evaluated. NOT negative. NOT zero-confidence. Unknown.
- Negative weight = structural exclusion. A declaration that these two things are mutually exclusive on specific dimensions. Sits in the graph quietly. Default is pass-through. Only fires when the current context's bitmask overlaps with the contradiction's dimensional footprint.
- Weight -127 = strongest possible exclusion. Proven, heavily evidenced contradiction.

**The pointer stores ONLY weight and address. Nothing else.**

No relationship type on the edge. No tense. No timestamp. No metadata. The pointer says "this node connects to that node at this strength." Period.

### Weight Semantics

**Positive weights are accumulated evidence.** Each time the system observes a connection, the weight increments by the activation count from that observation. A weight of +2 means "I saw this once and it was weak." A weight of +50 means "I've seen this many times across many contexts." A weight of +127 means "I've hit the ceiling — maximum observed evidence." The weight IS the evidence count, capped at 127.

**Negative weights are structural declarations.** A weight of -100 between whale and fish does not mean "weak connection." It means "these are mutually exclusive on this dimension." Negative weights are not accumulated — they are set when the system encounters or is taught a structural exclusion. -127 is a proven, absolute contradiction.

**The default behavior of a negative weight is pass-through.** The -100 between whale and fish sits in the graph quietly. Most of the time, nobody cares. "I caught a whale while fishing" doesn't trigger a contradiction alarm — nothing in that context requires whale and fish to be structurally compatible.

**Contradictions activate only in context.** When the system IS trying to classify whale — "what kind of thing is a whale?" — and walks the graph to fish, the -100 fires. The gate checks: does the current context require this dimension? Bitmask AND between active context dims and the contradiction's dims. Zero overlap = ignore, pass through. Nonzero = this contradiction is relevant right now, act on it.

**What acting on a contradiction means:**

- **New definition needed.** The word is being used in a way none of its current definitions cover. The contradiction is the signal to create one.
- **Wrong interpretation selected.** The gates picked wrong. Route back to the rejected interpretations — one of them might not have the contradiction.
- **Pointer was wrong.** The evidence that created it was incomplete. Flag for investigation.

**The system LEARNS which contexts make which contradictions relevant.** That's gate learning. Early on, maybe it fires on every negative it encounters. After experience, it knows: whale-fish matters during classification, doesn't matter during scene description. Learned gate condition, not hardcoded rule.

**Coexistence.** A node can have positive connections and negative connections to the same target simultaneously, on different dimensions or different definitions. Whale has positive connections to fish-like properties (aquatic, swims, fin-like structures) AND -100 on the IS_A dimension. Good enough approximation for most purposes. Precise distinction when precision matters. Both live in the graph. Context determines which one activates.

Everything that used to be edge metadata is graph structure instead:

**Relationship type is encoded by the target node.** A pointer from "dog" to "animal" means IS_A because "animal" is a category node. A pointer from "dog" to "fur" means HAS_PROPERTY because "fur" is a property node. The system knows what "animal" IS — it's in the graph. That knowledge doesn't need to be duplicated on every edge pointing to it. This means relationship types are emergent. If the system discovers a new kind of node — "location" nodes — then pointers to location nodes automatically carry spatial meaning without anyone adding a new edge type. The type vocabulary grows with the net.

**Tense is a node.** "Ran" has a pointer to the "past_tense" node. "Runs" has a pointer to "present_tense." Tense is a trait of the word, not metadata about how it connects to something else. The past_tense node has its own back-list (every past-tense word), its own pointers (to "completed," "before," "historical"), and participates in Comparator calls like any other node. "Give me all past-tense words" = one back-list read.

**Temporal markers are nodes.** "1066" is a node with pointers to "past_tense," "medieval," "11th_century." "Tuesday" is a node with pointers to "present_tense" or "near_future" depending on context. "During the war" is a phrase node with pointers to temporal and conflict dimensions. All temporal structure lives in the graph where the Comparator can touch it, the crystallizer can find patterns in it, and the system can reason about it.

**This eliminates ALL special-case data from the edge format.** Everything that was edge metadata — rel_type, tense, timestamp, is_current — becomes nodes and pointers. One data structure (the node), one relationship format (the weighted pointer), one operation (comparison). The richness lives in the graph, not hidden in edge fields that nothing can reason about.

### Memory Model

- **Cold (disk).** Human-readable .node text files. Tiered directories. A developer can read any file.
- **Hot (RAM).** Parsed pointer arrays. Active for processing.
- **Paging.** Request by ID → check master index → if not cached, load from disk, parse, cache.
- **LRU Eviction.** Fixed cache capacity. Oldest-accessed evicted first. Dirty nodes written back on eviction.
- **Crash safety.** Periodic safe-save. Atomic writes via temp file + rename.

### The Back-List

When node A adds a pointer to node B, B's back-list gets an entry for A. When removed, B's back-list updates. Sync is immediate and mandatory.

Intersection queries use sorted-array merges on back-lists. "What is animal AND domestic?" = merge-intersect two back-lists. O(k) where k is the smaller back-list.

---

## The Comparator

The only cognitive primitive.

**Input:** Two pointer lists, sorted by address.

**Output:** Three sets:

- **Shared.** Both lists have a pointer to this address, same sign.
- **Divergent.** Both lists have a pointer to this address, opposite signs.
- **Absent.** Present in one list, missing from the other.

### The Confidence Equation

```
match_score = ((sum_shared_weights + sum_divergent_weights) * 100) // total_unique_dimensions
```

- `sum_shared_weights`: sum of min(|weight_a|, |weight_b|) for each shared pair.
- `sum_divergent_weights`: sum of -min(|weight_a|, |weight_b|) for each divergent pair (negative).
- `total_unique_dimensions`: count of ALL dimensions in either list (shared + divergent + absent).
- Result: integer percentage, 0-100. Floor division. No floats.

This is Jaccard similarity adapted to integer arithmetic. Multiply by 100 before dividing so the result is a percentage. Absent dimensions dilute without asserting. Sparse comparisons score near zero. High scores require dense structural overlap.

The three sets (shared, divergent, absent) are the Comparator's real output. The confidence score is a convenience derivable from them:

```
confidence_score = ((sum_shared_weights + sum_divergent_weights) * 100) // total_unique_dimensions
```

Integer percentage. Absent dimensions dilute without asserting. But the sets themselves carry more information than the score and should be preserved in the bundle whenever possible. Don't aggregate when you can keep the raw data.

### Discovery vs. Evaluation

- **Hops are for discovery.** Back-lists gather candidates. O(k). Proximity ≠ similarity.
- **The Comparator is for evaluation.** Applied to candidates after discovery. The divergent set overrides graph proximity.

Never confuse the two.

---

## The Gate Circuit

The proven architecture from v43. Five layers of boolean logic gates.

### Structure

```
Input Layer → Signal Layer → Pattern Layer → Execute Layer → Output Layer
```

Each layer contains gates. Each gate is boolean: AND, OR, NOT. A gate fires when its pattern matches the current activation state, or it does not. No weights. No thresholds. No probability. Deterministic.

### Lockouts

Between pattern and execute layers, lockouts prevent specific patterns from reaching execution when certain other patterns are also active. These are the system's learned exclusion rules — structural knowledge about what doesn't go together.

### Mutual Lockouts

When correction creates a lockout that overgeneralizes, a reverse lockout is created. Two patterns now suppress each other. This is a dead signal — the system's current structure can't distinguish these cases. The system then compares the activation states of the conflicting cases, identifies the differentiating features, and rewires the gate conditions. The contradiction is resolved through topology change, not weight adjustment.

### What the Gates Do in the Pipeline

**Stage 3 (Selection):** The gates determine which enriched interpretation is most structurally consistent.

**Stage 5 (Action):** A second gate pass determines what to DO with the integrated information. Generate output? Update a connection? Trigger a new comparison cycle? Queue for further enrichment?

**Self-improvement:** The gates learn from their own mistakes through the contradiction → suppression → mutual suppression → differentiation → rewiring cycle. This is comparison applied to the system's own routing structure.

---

## The Crystallizer

The crystallizer watches what touches what and finds meaning in the patterns of contact.

### What It Does

When input goes through the enrichment and interaction stages, specific regions of the net light up. The crystallizer observes which regions consistently co-activate across different inputs and identifies structural patterns:

- **Convergence.** Multiple different inputs activate the same cluster of nodes. That cluster is a natural category — a concept the data is telling the system exists.
- **Divergence.** Two clusters that mostly overlap but split on specific dimensions. That split is a structural distinction — the data is telling the system where to draw a line.
- **Orphan features.** Dimensions that activate but don't cluster with anything. These are either noise or undiscovered structure. The crystallizer flags them for the idle processor.

### Creating Meaning vs. Creating Statistics

Statistical co-occurrence says: "dog" and "cat" appeared near each other 47 times.

The crystallizer says: "dog" and "cat" both activated animate, domestic, pet, four-legged, fur, mammal — and diverged on canine/feline, pack/solitary, trained/independent. The shared activation pattern IS the category "domestic pet." The divergent pattern IS the distinction between them. The category wasn't programmed. It was discovered from the structure of what the net already knew, revealed by what the input touched.

This only works because the enrichment step made the input rich enough to touch the net. Without enrichment, "dog" and "cat" are just tokens that appeared near each other. With enrichment, they're full dimensional profiles whose contact patterns reveal real structure.

### Negative Crystallization

The rejected interpretations from Stage 5 also produce contact patterns. The crystallizer watches these too. Patterns in what consistently gets rejected are structural knowledge about what DOESN'T work — which is just as valuable as knowledge about what does.

---

## Metastructural Nodes

The system doesn't just learn what words mean. It learns what kinds of interactions it keeps having.

### What They Are

A metastructural node captures the activation pattern of the ENTIRE net for a recognized type of interaction. It's a cached whole-pipeline state — which dims fired, how they connected, what the winning interpretation looked like, what the output was.

When the system has processed fifty different color classification questions, the crystallizer notices: these all produce the same activation shape across the net. The enrichment hits the same regions. The interaction produces the same density pattern. The gates select the same way. The integration does the same thing. That whole-net shape becomes a metastructural node — a single node whose pointers describe the entire activation pattern for "color classification query."

### How They Work

Metastructural nodes are still nodes. Same format. Same pointers. Same Comparator access. But their pointers don't point to individual concepts — they point to patterns of how many lower-level nodes interact. They're holonic: the pattern across the net IS the node.

When new input arrives at Stage 0, the system does a fast match against known metastructural nodes:

```
input_profile AND metastructural_pattern → overlap
```

High overlap means "I've seen this exact kind of interaction before." The system can skip the full pipeline — skip generating 18 interpretation combinations, skip scoring them all, skip the gate selection — and go straight to the cached activation pattern that it knows works for this shape of input.

### When They Form

Metastructural nodes emerge from the crystallizer the same way concept nodes emerge — from recurring patterns. The difference is scale:

- **Concept node:** recurring pattern across word-level activations. "Dog and cat keep lighting up the same dims → domestic_pet exists."
- **Metastructural node:** recurring pattern across whole-pipeline activations. "Color questions keep producing the same net-wide shape → color_classification_query exists."

Same mechanism. Different holonic level. The crystallizer doesn't need a separate system to create them. It just needs to observe at the pipeline level, not just the word level.

### What They Save

The full pipeline for a 4-word sentence with 2-3 definitions each: ~18 interpretations, each needing activation maps built, compared, scored, selected. Milliseconds on a CPU, but it adds up.

A metastructural shortcut: one comparison between the input profile and the cached pattern. If it matches, skip straight to the answer. Microseconds.

More importantly, metastructural nodes represent understanding that goes beyond individual facts. Knowing IS_A(red, color) is a fact. Knowing "when someone says X is a Y, they're asserting a category relationship" is a metastructural pattern. The system goes from answering individual questions to understanding kinds of questions.

### They're Still Learnable

Metastructural nodes can be wrong. If the system cached a bad pattern — maybe it saw a run of weird inputs that don't generalize — the cached shortcut will produce wrong answers. The self-improvement loop catches this through telemetry (accuracy drops when the shortcut fires), and the sandbox can investigate and revise or discard the metastructural node.

They are nodes. They are in the graph. They are subject to the same correction, contradiction, and refinement as everything else.

---

## Episodic Memory

### What an Episode Is

An episode is a node that captures the full concept state of a continuous interaction. Its pointers ARE the dimensional landscape of the conversation — which topics were active, how they connected, what the register was, what was learned, what was unresolved, what metastructural patterns fired.

Loading an episode is loading the result of the entire interaction, not replaying it. The system spent hundreds of processing cycles building up context during the conversation. The episode node captures that context in one loadable structure. Instant state restoration.

### How Episodes Work

**Creation.** When Stage 0 detects a new context (not a continuation), a new episode node is created. Everything processed during this interaction is tagged with the episode ID — activation maps, gate decisions, winning interpretations, rejection pool contents, live context state.

**During processing.** The episode node's pointers update as the conversation progresses. New topics activate — the episode gets pointers to them. The register settles — the episode gets pointers to register nodes. Something gets learned — the episode gets a pointer to the new knowledge. The episode is a live accumulator of the interaction's dimensional state.

**Resumption.** Later, new input arrives. Stage 0 enriches it, compares against the net, finds high overlap with nodes tagged to episode #4072. The system pulls the episode node. Its pointers provide the full context: here's the concept state when I stopped, here's what was active, here's what was unresolved. The merge pyramid doesn't start from zero — it loads the episode's accumulated context as its starting frame. Pick up and continue.

**Closure.** When an interaction ends, the crystallizer examines the episode's full state. Everything useful gets integrated into the net. The bulky raw data — full activation maps, rejection pools, gate traces — can be cleared. The episode node keeps the structural summary: what was the episode ABOUT, what was learned, what connects to what. The information already lives in the net. The episode node is the index entry.

### Episodes as Containers — Scoped Knowledge

Episodes aren't just bookmarks. They're containers. Scoped worlds.

When the system reads a novel, the rules of that world apply WITHIN that episode. "Harry can fly on a broomstick" is true inside episode #8001 (Harry Potter Chapter 1). It's not true globally. The knowledge has scope — and the scope is structural. The pointer from "magic is real" to episode #8001 IS the scoping.

**This solves containerization — something current AI cannot do.** LLMs treat everything as one flat context. Information from a novel bleeds into factual reasoning. The model can't distinguish "true in this story" from "true in general." There are no container boundaries.

In Isaac, the episode node defines the scope:

- Knowledge learned within an episode is tagged to that episode's ID.
- The bitmask context checking already handles this. When processing within episode #8001, the active context includes that episode's dimensional footprint. "Magic is real" passes through — the container makes it relevant.
- When processing in a different context (a science textbook), the bitmask doesn't overlap. "Magic is real" is invisible. Not deleted. Not contradicted. Out of scope.

**Contradictory knowledge in different containers coexists without conflict.** "Magic is real" in the Harry Potter container. "Magic is not real" in the physics container. Both correct within their scope. The contradiction only fires if you try to apply one inside the other's scope — which the bitmask catches and routes to action.

**Cross-container reasoning is deliberate, not accidental.** You can compare two episode containers — the Comparator shows shared structure (both have cause-and-effect, both have internal rules) and divergent structure (magic vs. conservation of energy). You cross the boundary explicitly by comparing the containers. You don't cross it accidentally by mixing scoped knowledge into global reasoning.

This is no different than understanding the limitations within a field. A book's world is entire unto itself, but the deductions you make within it do not automatically apply everywhere. The episode boundary is an artificial but useful heuristic for internal understanding. Containers can be crossed, but crossing is a conscious structural operation, not a leak.

### Retroactive Encapsulation

The system doesn't always know information is fictional when it first encounters it. It might read about a land where animals talk and process it as potentially factual — maybe it's a real place it hasn't heard of. Then it hits a signal: "the Chronicles of Narnia" or "this is a fictional world" or simply "talking animals" contradicts known physics. The bitmask fires.

The action isn't "delete what I learned." The action is "scope what I learned."

**Step 1 — Contradiction fires.** Something recently integrated conflicts with the established net. The bitmask detects relevant overlap.

**Step 2 — Create a container retroactively.** Instead of routing to "fix the pointer" or "create a new definition," the system takes a third route: encapsulate. A new episode node is created and tagged as fiction-scoped.

**Step 3 — Walk recent connections.** Everything integrated during this processing sequence — the talking animals, the magic, the fictional geography — is directly connected in the graph. The episode accumulator has the full list. Walk those connections. Add a pointer from each affected node to the new container's scope.

**Step 4 — Nothing changes structurally.** The pointers stay. The weights stay. The information stays. A new boundary node was added and the recent knowledge now points to it. The bitmask system handles the rest — these facts only activate when the Narnia container is in scope.

This is cheap. No reprocessing. No deletion. One new node (the container), a walk of the recent connections (already tracked by the episode accumulator), and one pointer per affected node. The graph structure is untouched. A circle was drawn around it.

**The trigger is the existing contradiction system.** The bitmask fires. The gates decide which route to take — new definition, reselection, or encapsulation. "Encapsulation needed" is a third route. The gates learn when to take it through the same contradiction-driven rewiring as everything else.

This also works for retroactive reclassification beyond fiction. The system reads a paper, integrates the claims, then discovers the paper was retracted. Encapsulate. The claims don't get deleted — they get scoped to "retracted_paper_X." They're still accessible if you deliberately query that container. They just don't leak into general knowledge.

### Cross-Episode Structure

Because episodes are nodes with pointers, comparing them is one Comparator call.

Episode #4072 (color conversation) and episode #5891 (wavelength conversation) both have strong pointers to visual_property and perception. Shared dims = these conversations were about related things. Divergent dims = where they went different directions. The system discovers cross-episode structure without replaying either conversation.

The crystallizer watches episode nodes the same way it watches everything else. Recurring patterns across episodes become their own metastructural nodes. "Every conversation with this person involves visual properties and classification" — that's a theme, discoverable from the episode pointer patterns.

### Genre and Medium as Emergent Structure

Compare 50 fantasy novel episodes. The shared dims across all of them ARE the genre. Magic systems, chosen ones, quests, dark lords, mentor figures — those recurring structural patterns crystallize into a metastructural node for "fantasy." The divergent dims across the 50 episodes are what makes each book unique.

Compare 50 thriller episodes. Tension arcs, unreliable information, time pressure, stakes escalation. Different shared pattern. Different metastructural node. "Thriller."

**The system KNOWS these are conventions of a medium, not facts about reality.** Every shared dim traces back to episode nodes scoped as fiction. The genre node inherits the scope. "Dark lords are common in fantasy" is a structural observation about a container type. It never leaks into "dark lords exist."

This means Isaac can:

- **Follow genre conventions.** The genre metastructural node is a constraint for generation. Write a fantasy scene = apply the fantasy pattern as a frame.
- **Subvert genre conventions.** It knows exactly what the expectation is because it discovered the pattern. Breaking the pattern is a deliberate structural choice, not random noise.
- **Mix genres.** Overlay two genre metastructural nodes. The Comparator shows where they're compatible and where they conflict. The conflicts are where genre blending gets interesting.
- **Understand medium without confusing it for reality.** All of this stays containerized. Genre knowledge is structural knowledge about fiction containers. It informs generation and analysis. It doesn't contaminate factual reasoning.

This is the metacontextual measurement from the original design spec, but emergent instead of hand-seeded. Nobody told the system what "grimdark" is. It discovered the pattern from comparing dark fantasy episodes — the same way it discovers everything else. The crystallizer at the episode level produces genre. No new mechanism needed.

### The Full Holonic Stack

Episodes add levels to the hierarchy:

| Level | Units | What Emerges |
|-------|-------|-------------|
| 2 | Words | Semantic dimensions |
| 3 | Sentences | Grammar, mood, intent |
| 4 | Paragraphs | Rhetoric, argument, topic |
| 5 | Sections | Register, voice, genre |
| 6 | Documents | Purpose, audience, worldview |
| 7 | Episodes | Interaction state, conversation identity |
| 8 | Episode clusters | Recurring themes, relationship patterns |

Each level has emergent dimensions invisible at the level below. The concept state of a conversation is invisible from any individual sentence within it. The recurring theme across conversations is invisible from any single conversation. The merge pyramid, the episode nodes, and the metastructural nodes together implement the full holonic stack.

---

## The Merge Pyramid

The context system. Replaces rolling windows and snapshots.

### Why It Exists

Words mean different things at different scales. "Bank" means something at the word level. "River bank" means something at the phrase level. "The bank of the river was eroding" means something at the sentence level. "The environmental chapter discussed how river banks were eroding across the region" means something at the paragraph level.

The merge pyramid captures all of these scales simultaneously by merging frames upward through a binary tree structure.

### Core Merge Operation

For two frames A and B, each a dense int8 vector:

```
For each dimension d:
    if A[d] != 0 AND B[d] != 0:
        result[d] = (A[d] + B[d]) // 2
        overlap_flag[d] = 1
    else:
        result[d] = A[d] + B[d]
        overlap_flag[d] = 0
```

The overlap flag means "averaged — detail exists below." Not error. Not contested. Just: this dimension was present in both children and got averaged. If you need the detail, go down to the children.

### Two Modes

**Mode 1 — Within-Sentence.** Fixed binary carry ripple. Words merge strictly by arrival order through a binary tree. Word arrives → Level 0 frame. If pending frame at Level 0, merge → Level 1. If pending at Level 1, merge → Level 2. Cascade continues.

**Mode 2 — Across-Sentence.** Boundary-driven. When the boundary detector fires sentence end: pad remaining words to nearest power of 2 with zero vectors, complete carry ripple → single sentence frame. Reset within-sentence chain. Sentence frames merge into paragraph frames. Same mechanism, different boundary trigger.

### Trie Navigation

The pyramid IS a trie. Each frame is a node. Navigation follows the numbers:

- **Down** (flagged dims dragging match quality): The frame averaged over something the query cares about. Check children. Follow the stronger signal.
- **Up** (large absent set): Not enough context. Check parent for broader context.
- **Stop** (strong match, few flags, small absent): This is the right resolution level.

### Boundary Detection

The boundary detector CONTROLS the pyramid structure. Punctuation nodes with boundary pointers trigger sentence-level completion. Overlap flag density spikes detect topic changes and trigger paragraph-level completion.

---

## Learning

### How Weights Work

**Positive weight = accumulated evidence.** Each encounter that shows a connection increments the weight by the activation count — how many shared dims were observed. The weight grows toward +127. It literally means "this is how much evidence I have seen for this connection." Weight of 3 = saw it once, weak signal. Weight of 95 = seen many times across many contexts. Weight of 127 = ceiling, massive evidence.

**Negative weight = structural exclusion.** A declaration that two things are mutually exclusive on specific dimensions. Whale has -100 to fish. That means "on the IS_A dimension, these are incompatible." The negative weight is a structural annotation, not a trigger. It sits in the graph quietly.

**Zero weight = no pointer exists.** Unknown. Never evaluated. Not false. Not weak. The relationship has never been observed or assessed.

### Positive Learning — Evidence Accumulation

The system does not create pointers from raw co-occurrence. Co-occurrence is noise. The Comparator is the gate.

When a word appears in context with a subject, run the Comparator between their existing pointers:

- **High shared + high absent = informative.** Structurally related AND carries novel dimensions. Create/strengthen pointer. Weight incremented by the activation count.
- **High shared + low absent = confirmation.** Already known. Increment existing weight by 1. The system saw it again — that's evidence.
- **Low shared + high absent = unrelated.** No structural foundation. No pointer.
- **Low shared + low absent = nothing.** Function words. Zero learning value.

### Negative Learning — Contradiction as Stored Knowledge

Contradiction is NEVER noise. It is the most important signal in the system. But the default is **pass through**.

When the Comparator finds a structural exclusion — two things that cannot both be true on the same dimension — a negative pointer is set. Not averaged. Set. The value reflects the structural strength of the exclusion.

**The negative pointer then sits there.** It does nothing unless the current context makes it relevant. Most of the time, nobody cares. "I caught a whale while fishing" — the whale/fish -100 pointer exists but nothing in that sentence requires whale and fish to be structurally compatible. Pass through.

### Bitmask Context Checking — When Contradictions Matter

Every negative pointer has a dimensional footprint — the dims it declares mutual exclusion on. Every active context has a dimensional footprint — the dims currently relevant to processing.

```
relevance = context_dims AND contradiction_dims
```

If relevance is zero, the contradiction doesn't matter right now. **Pass through.** Whale and fish are both in the sentence but the context isn't asking them to be the same kind of thing. Ignore it.

If relevance is nonzero, the contradiction is active in the current context. **Now it matters.** The system is trying to classify whale and the fish pointer comes up with -100 on the IS_A dimension. The context IS asking about classification. The bitmask fires. Route to action:

- **New definition needed.** The word is being used in a way that contradicts its current definition. The contradiction is the evidence that a new definition is needed.
- **Reselection needed.** The gates picked the wrong interpretation. Go check the rejected interpretations.
- **Investigation needed.** The pointer itself may be wrong. Flag it for the idle processor.
- **Encapsulation needed.** The recently integrated knowledge contradicts established facts but isn't wrong — it's scoped. A fictional world, a retracted paper, a hypothetical scenario. Create a container retroactively and scope the recent knowledge to it. Nothing gets deleted or changed — just bounded.

**Which route? The gates decide.** And the gates LEARN which contexts make which contradictions relevant, through the same contradiction-driven rewiring mechanism as everything else.

### Coexistence of Positive and Negative

The system can hold "whale is kind of like a fish" and "whale is definitely not a fish" simultaneously. Both are in the graph:

- Whale has positive pointers to aquatic, swims, fins-like-structures, large-body — many of the same dims as fish.
- Whale has -100 to fish on the IS_A dimension.

The positive connections are the "good enough approximation" for most contexts. When someone says "whales are like big fish," the positive overlap is real and useful. When someone asks "is a whale a fish?" the -100 fires because the IS_A dimension is now relevant. Both coexist. Context determines which matters. The system doesn't have to choose between them globally. It uses whichever is appropriate right now.

This is not ambiguity. This is precision. The graph captures the full structural truth — whale shares many traits with fish AND whale is not a fish. Both are correct. The bitmask determines which fact is relevant to the current operation.

### Learning Priority

```
learning_value = overlap_percentage × divergent_count
```

The idle processor prioritizes comparisons where there's enough overlap to be meaningful but enough divergence to learn something. Dog vs. dolphin (high overlap, high divergence) beats dog vs. cat (too similar) and dog vs. table (too different).

### Concept Emergence

Compare frames at the same level of the merge pyramid. Two frames with near-zero delta on overlapping dimensions = structurally similar regardless of vocabulary. The shared dimensional pattern across matching frames IS an emergent concept. New concept becomes a node. Level metadata tracks which pyramid level produced it.

---

## Self-Improvement

Ported from the proven v43 methodology.

### Telemetry

Every processing cycle auto-records: timing, winning interpretation, gate fires, structural density scores, novel vs. redundant classification, integration result. Per-category accuracy accumulates. Trend detection compares recent vs. historical.

### Self-Inference

The system reads its own telemetry. Finds its weakest areas. Generates probes from its own knowledge to test itself. Runs the probes. Scores itself. Same pipeline — enrich, gate, integrate — pointed at the system's own performance data.

### A/B Testing

Before any structural change is committed: checkpoint the current state. Apply the change to a fork. Run tests through both. Compare results. Commit the winner. Revert the loser.

**Rule: every experiment starts from a fresh fork. No exceptions.**
**Rule: not-breaking > gaining. A change that fixes 3 things but breaks 16 is reverted.**

### The Sandbox Loop

```
Observe → Analyze → Theorize → Experiment → Promote
```

1. **Observe.** Rich traces of what happened during processing.
2. **Analyze.** Structural differentials. Root cause detection.
3. **Theorize.** What mechanism caused the failure? What fix would address the root cause?
4. **Experiment.** Apply the proposed fix to a fresh fork. Test.
5. **Promote.** Only if: root cause addressed + zero regressions + system can explain why.

### Honest Tests

Feed real text. Check what was actually learned. Not unit tests asking "did the Comparator produce the right three sets?" but integration tests asking "after reading this paragraph, does the system know something it didn't know before?"

If the answer is no, the pipeline is broken. The information went through but didn't make contact.

---

## Absolute Constraints

These are walls. Nothing in the system violates them.

1. **All arithmetic is integer.** No floating point anywhere. No floats in storage, computation, comparison, scoring, or output.

2. **The Comparator is the only cognitive primitive.** One comparison operation. Everything else is built by applying it.

3. **The 64-bit pointer format is fixed.** 8-bit signed weight, 56-bit address. One machine word. No metadata on the edge — no rel_type, no tense, no timestamp. Weight and address only.

4. **Everything is a node.** Relationship types, tense markers, temporal locations, grammatical roles, interaction patterns — all nodes in the graph. If information would have been edge metadata, it becomes a node with pointers instead. The richness lives in the graph where the Comparator can reason about it, not hidden in edge fields.

5. **Absent is not negative.** Missing pointer = unknown. Not false. Not zero. Unknown.

6. **Negative is not noise.** Negative pointers are structural exclusions, not errors to be averaged away. Default is pass-through. Bitmask context checking determines when a contradiction is relevant. The system learns which contexts activate which contradictions.

7. **Every value traces to evidence.** If a pointer exists, the system can explain why. If the chain can't be walked, the pointer shouldn't exist.

8. **Determinism.** Same inputs, same outputs, every time.

9. **Human-readable storage.** Plain text node files. A developer can read any file.

10. **The system never pretends.** If it doesn't know, it says so — because the math produces an inconclusive score.

11. **Information only enters, never leaves.** Novel information always integrates. Redundant information confirms and the duplicate is discarded. Nothing new is ever destroyed.

12. **No filters.** The system does not pre-decide what's relevant. Enrichment widens. Gates select but preserve. The net decides what matters through comparison, not because a designer threw something away.

13. **Rejected interpretations are learned from.** They go to the rejection pool, get crystallized for patterns, get checked when selected interpretations fail. Then cleared.

---

## Type System

Everything interacts with everything, but there are structural categories that determine HOW things interact.

### The Unified Data Principle

There is one data structure: the node. There is one relationship format: the weighted pointer. There is one operation: comparison. Everything else is emergent.

Relationship types are not hardcoded. They are encoded by what the target node IS. Pointers to category nodes are IS_A relationships. Pointers to property nodes are HAS_PROPERTY relationships. Pointers to tense nodes are grammatical-tense relationships. Pointers to location nodes are spatial relationships. The system does not have a fixed vocabulary of relationship types. It has nodes. When it discovers a new kind of node, pointers to that kind of node automatically carry the right meaning.

This means the system's understanding of how things relate grows with the net. Early in training, it might only distinguish "category" from "property" from "action." After processing enough text, it distinguishes "temporal-location" from "spatial-location" from "institutional-location" — because those are structurally different kinds of nodes with different pointer profiles, and the Comparator can tell them apart.

### Holonic Levels

Each level of organization produces dimensions invisible at the level below:

| Level | Units | What Emerges |
|-------|-------|-------------|
| 0 | Bits | Nothing |
| 1 | Characters | Visual/phonetic patterns |
| 2 | Words | Semantic dimensions |
| 3 | Sentences | Grammar, mood, intent |
| 4 | Paragraphs | Rhetoric, argument, topic |
| 5 | Sections | Register, voice, genre |
| 6 | Documents | Purpose, audience, worldview |

The merge pyramid implements this. Within-sentence levels discover grammar. Sentence frames discover mood. Paragraph frames discover rhetoric. Each level of the pyramid observes a different holonic level.

### Type Interactions

Nodes have types (noun, verb, adjective, pattern, concept, style, tense, location, etc.). Types have interaction rules — not as hard walls, but as structural expectations:

- Noun-verb interaction produces predicate structure.
- Adjective-noun interaction produces modified reference.
- Pattern-instance interaction produces classification.
- Concept-concept interaction produces abstraction.
- Word-tense interaction produces temporal grounding.
- Event-location interaction produces spatial grounding.

These interaction rules are themselves nodes. They are learned, not hardcoded. The system discovers "adjectives modify nouns" from the dimensional physics of how adjective profiles interact with noun profiles, not from a grammar rule. The system discovers "past_tense words describe completed events" from the pointer overlap between past_tense-tagged words and completion-tagged concepts.

Everything CAN interact with everything. The type system describes what TENDS to happen when things interact, learned from observation. It's structural expectation, not permission.

---

## Build Order

### Phase 0 — Validate Unknowns

Before committing to the full build:

1. Build the enrichment step. Feed "red is a color" through it. Does the enrichment create enough surface area for the interaction step to find structural density between red:visual-property and color:visual-category?
2. Test the interaction step. Do definitional version combinations actually condense and cancel as predicted? Does the richest intersection correspond to the correct interpretation?
3. Test Comparator-gated learning. Process "the cat sat on the mat" — verify minimal pointer creation (low shared, low absent novelty). Process "the cat purred while kneading" — verify real pointer creation (high shared via feline, high absent novelty).
4. Build the merge pyramid. Feed real text. Validate carry ripple and boundary detection.
5. Run the honest test. After the full pipeline processes a paragraph, does the net contain new structural knowledge? If not, diagnose where contact failed.

### Phase 1 — Foundation

Reuse the proven data layer with one structural change: the current edge objects (source, target, rel_type, weight, truth_weight, timestamp, tense, is_current) are replaced by the 64-bit pointer format (weight + address only). Everything that was edge metadata becomes graph structure:

- rel_type → encoded by target node type (emergent, not hardcoded)
- tense → tense nodes (past_tense, present_tense, future_tense) with back-lists
- timestamp → temporal location nodes in the graph
- truth_weight → the pointer weight IS the truth weight
- is_current → temporal context resolved during enrichment, not stored per-edge

**Components:**

- Pointer format (pack/unpack, sort, binary search, derive_weight)
- Node structure (identity, multi-definition, shared, back-list, dirty flag)
- Node I/O (text files, atomic writes, tiered directories)
- Master index (by_id, by_name)
- Hot cache (LRU, paging, write-back)
- Back-list manager (bidirectional sync)
- Comparator (three-part output, confidence equation with integer scaling)
- Seed tense/temporal/grammatical nodes (past_tense, present_tense, future_tense, noun, verb, adjective, category, property, action, etc.)

### Phase 2 — The Intake Organ

This is the new core build:

- **Enricher.** Resolves every input token against the net. Pulls all definitional versions. Attaches inherited traits. Generates pattern candidates and structural metadata.
- **Interactor.** Runs the Comparator on all definitional version combinations of neighboring tokens. Produces the structural density map.
- **Gate circuit.** Five-layer boolean logic. Takes the density map. Selects the structurally consistent interpretation. Preserves everything else.
- **Integrator.** Comparator call against the net. Novel → create edges. Redundant → confirm and discard.
- **Rejection pool.** Stores non-selected interpretations with metadata. Interface for crystallizer and error detection.

### Phase 3 — The Crystallizer

- Contact pattern observation
- Convergence detection (natural categories)
- Divergence detection (structural distinctions)
- Negative crystallization (patterns in rejections)
- Concept emergence (from same-level pyramid frame comparison)

### Phase 4 — The Merge Pyramid

- Core merge operation (int8 vectors, overlap flags)
- Within-sentence carry ripple
- Boundary-driven across-sentence completion
- Trie navigation (up/down/stop)
- Frame metadata

### Phase 5 — Learning Pipeline

- Comparator-gated learning
- Contradiction-driven correction (integer average, three-slate, logging)
- Correction ripple (dimensional overlap priority)
- Learning priority function (overlap × divergent_count)
- Idle processor (80% dim scanning, 20% node following)

### Phase 6 — Self-Improvement

- Telemetry
- Self-inference
- A/B testing with fresh forks
- Sandbox loop (observe → analyze → theorize → experiment → promote)
- Honest tests

### Phase 7 — Cognition

- Thinking loop (resolver, trie-navigated constraint satisfaction)
- Generator (pyramid trie descent, quality equation, cross-level scoring)
- Metacontextual engine (style/genre nodes, one Comparator call)
- Query system (resolution-aware answering)

### Phase 8 — GPU

- Full graph in VRAM
- Batch merge kernel
- Parallel Comparator
- Dimension-wise processing (boolean bitmasks, bitwise queries)
- Oracle testing against CPU path

---

## Validation Tests

Must pass before each phase is considered complete.

### Foundation (Phase 1)

1. Node round-trip: 10,000 nodes written and read back exactly.
2. Back-list sync: add/remove across 1,000 operations, bidirectional sync holds.
3. Comparator determinism: same inputs, 1,000 runs, identical output.
4. Cache paging: cold → hot → cache pointer set → second request from cache.
5. LRU eviction: full cache, new request, LRU evicted.
6. Dirty write-back: modify → dirty → evict → disk updated. Clean evict = zero I/O.
7. Crash safety: modify 100, safe-save, verify consistency.

### Unified Data Model (Phase 1b)

8. Target-encodes-type: pointer from "dog" to "animal" is interpretable as IS_A because "animal" is resolvable as a category node. No rel_type field needed.
9. Tense as node: "ran" has a pointer to past_tense node. past_tense back-list contains "ran." Query "all past-tense words" returns correct set from one back-list read.
10. Temporal location: "1066" node has pointers to past_tense, medieval, 11th_century. Comparator between 1066 and battle_of_hastings produces meaningful shared set.
11. Confidence equation percentage: 3 shared dims out of 47 total produces a small but nonzero integer percentage (not truncated to 0). Two near-zero candidates are distinguishable.

### Intake Organ (Phase 2)

12. Enrichment completeness: "red" produces all definitional versions with full inherited traits.
13. Gate pruning: known divergences between definitions prevent impossible combinations from being assembled.
14. Activation map quality: for "red is a color," visual interpretation's map shows dims with count > 1 (words sharing dims). Political interpretation's map shows all dims at count 1 (no shared dims). The maps travel with the interpretations.
15. Gate selection: correct interpretation selected from enriched candidates for 20 test sentences. All selected interpretations score above 100.
16. Integration novelty: new information creates new edges. Existing information confirms without duplication.
17. Rejection pool: non-selected interpretations preserved with density scores and metadata.
18. **The honest test.** Feed "red is a color" through the full pipeline. Verify IS_A(red, color) exists in the net afterward.
19. **The noise test.** Feed "the cat sat on the mat" through the full pipeline. Verify minimal structural change. No junk pointers from function word co-occurrence.

### Crystallizer (Phase 3)

20. Convergence detection: feed 10 color words in descriptive contexts. Verify crystallizer discovers the color category.
21. Divergence detection: feed "dog" and "cat" in similar contexts. Verify crystallizer finds the shared domestic-pet category AND the canine/feline distinction.
22. Negative crystallization: verify patterns emerge from the rejection pool.

### Merge Pyramid (Phase 4)

23. Merge math: zero overlap, full overlap identical, full overlap opposite, partial overlap. Flags correct.
24. Carry ripple: 1/2/4/8 words produce correct frame counts per level.
25. Boundary detection: punctuation triggers sentence completion. Topic change triggers paragraph completion.
26. Trie navigation: down on flagged dims, up on large absent set, stop on strong match.

### Learning (Phase 5)

27. Comparator-gated: "the cat purred while kneading" creates real pointers. "The cat sat on the mat" doesn't.
28. Correction: contradictory evidence produces integer-average update. Log walkable.
29. Correction ripple: changing whale:fish propagates to gills/scales via dimensional overlap.
30. Concept emergence: same-level pyramid frames with near-zero delta produce new concept node.

### Self-Improvement (Phase 6)

31. Telemetry: per-cycle records, per-category accuracy, trend detection.
32. Self-inference: system finds its weakest area, generates probes, scores itself.
33. A/B testing: change applied to fork, regression detected, correctly reverted.
34. Sandbox: full observe → analyze → theorize → experiment → promote cycle.
35. **The big honest test.** Feed a full paragraph of novel text. The system reads it. Then ask the system what it learned. If it can articulate new knowledge that wasn't in the net before reading, the pipeline works. If it can't, it doesn't.

### Context Detection (Stage 0)

36. Continuation detection: feed "red is a color" then "blue is also a color." Verify the second input is detected as continuation (high overlap with live context).
37. New context detection: feed "red is a color" then "the dog ran quickly." Verify detected as new context (low overlap).
38. Query detection: feed "red is a color" then "is red a color?" Verify detected as query about existing knowledge, not new information to integrate.

### Metastructural Nodes

39. Pattern formation: feed 10 different "X is a Y" sentences. Verify the crystallizer creates a metastructural node for the IS_A query pattern.
40. Shortcut firing: after the metastructural node exists, feed a new "X is a Y" sentence. Verify Stage 0 matches the metastructural pattern and shortcuts the pipeline.
41. Shortcut correctness: verify the shortcut produces the same result as the full pipeline would have.
42. Bad shortcut detection: feed an input that superficially matches the metastructural pattern but is structurally different. Verify the system catches the error through telemetry and revises the metastructural node.

### Episodic Memory

43. Episode creation: start a new conversation. Verify an episode node is created with pointers to the active topics.
44. Episode accumulation: process 5 sentences in the same conversation. Verify the episode node's pointer profile grows to reflect the conversation's concept state.
45. Episode resumption: close the conversation. Start a new input related to the same topics. Verify Stage 0 finds the episode node and loads it as starting context.
46. Cross-episode comparison: create two episodes about related topics. Comparator between them produces meaningful shared and divergent sets.
47. Container scoping: learn "magic is real" within a fiction episode. Verify it does NOT activate when processing in a science context (bitmask non-overlap).
48. Cross-container reasoning: explicitly compare the fiction episode against the science episode. Verify the Comparator produces meaningful shared structure (both have rules, cause-effect) and meaningful divergence (magic vs. physics).
49. Retroactive encapsulation: feed factual-seeming claims, then feed a signal that they're fiction. Verify the system creates a new container, scopes the recent knowledge to it, and the scoped knowledge no longer activates in non-fiction contexts. Verify no pointers or weights were changed — only scope was added.

---

## Open Questions

Empirical — test, don't design.

1. **Enrichment depth.** How many definitional versions and inherited traits make optimal contact? Too few = deaf. Too many = slow. Find the sweet spot.
2. **Gate learning rate.** How many contradictions before rewiring? Too fast = unstable. Too slow = stuck.
3. **DIM_WIDTH.** Start at 64. Profile memory vs. accuracy.
4. **Boundary detector sensitivity.** Flag density threshold for sentence/paragraph detection.
5. **Concept emergence threshold (K).** Start at K=3.
6. **Phrase promotion threshold.** How many occurrences with stable context?
7. **Rejection pool lifespan.** How long before unexamined rejections are cleared? Or: clear after every crystallizer pass?
8. **Confidence equation edge cases.** Very small or very large pointer lists.
9. **Pattern abstraction clustering.** Do delta profiles cluster by grammar? Test with 100 sentences.
10. **Activation map features.** Which features of the map predict correctness? Peak? Average? Position clustering? Distribution shape? The gap between peak and low? Isaac experiments through the sandbox.
11. **Combinatorial scaling.** Long sentences with polysemous words produce many interpretation candidates. Monitor whether gate pruning keeps this manageable or whether additional limits are needed.

---

## What Success Looks Like

The same pipeline that learns IS_A(red, color) from "red is a color" learns IS_A(whale, mammal) from "whales are mammals." The same pipeline that discovers the domestic-pet category from dog/cat examples discovers the color category from red/blue/green examples. The same pipeline that handles simple declarative sentences handles questions, commands, and complex multi-clause constructions — not because those were programmed, but because the enrichment step generates the right interpretive candidates and the gates learn to select correctly from feedback.

Isaac reads and Isaac learns through the same system. The translation gap is closed because the intake organ makes information touch the brain. The information goes in, makes contact, and meaning emerges from what got touched.

One pipeline. One primitive. Raw data in, meaning out. Everything else is emergence.

---

*End of Proposal*
