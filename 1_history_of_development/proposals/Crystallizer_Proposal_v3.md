# Isaac — Crystallizer Proposal

## The mechanism that turns observations into understanding

---

## What It Is

The crystallizer is how Isaac learns. Not the pipeline — the pipeline creates raw observations. Not training — training corrects individual mistakes. The crystallizer is the mechanism that takes accumulated observations, corrections, mistakes, and patterns and discovers the RULES behind them.

Without the crystallizer, Isaac is a database with a pipeline. It stores what it's told. It corrects what's flagged. But it never understands WHY. It never discovers structure that nobody programmed. It never gets better on its own.

The crystallizer is what was missing from GOFAI and formal concept analysis. Those systems could store and retrieve structured knowledge, but they could never find MORE structure than what humans put in. The crystallizer looks at what IS and finds what that IMPLIES. It creates knowledge that nobody taught — crystals from potential.

It is the most important mechanism in the entire system other than the Comparator. Arguably it IS an advanced Comparator — the Comparator applied to the entire net at once, recursively, looking for the meta-patterns that individual comparisons can't see.

---

## What It Interacts With

**Everything.** The crystallizer is not a background optimizer running in a corner. It is the learning core. It needs:

- **The net.** Full read access. Every node, every pointer, every backlist. This is the primary data source.
- **The wrong pile.** Every correction record with full context. If the crystallizer doesn't learn what was flagged as wrong and WHY, the system will never learn to get better. The wrong pile is where the pipeline's failures are diagnosed.
- **The rejection pool.** Interpretations that lost in the gate selection. Why did they lose? What patterns recur in the losers?
- **The pipeline results.** Activation maps, context subnets, gate decisions, integration results. The crystallizer needs to see what the pipeline is doing, not just what ends up in the net.
- **Training corrections.** What was the expected answer? What did the pipeline produce? What was the delta? Every training event is learning data.
- **Its own previous proposals.** What did lift accept? Reject? Defer? The crystallizer learns what kinds of discoveries are useful.

---

## What It Is Not

- It is not a pipeline stage. It does not run on individual inputs.
- It is not an actor. It proposes. Lift decides whether to implement. The crystallizer never modifies existing net structure directly.
- But it IS how learning happens. Without it, nothing generalizes. Nothing improves. Nothing is understood.

---

## What It Does

### 1. Scan the Net

The crystallizer walks the graph. For every node, it reads the full pointer profile — all definitions, all shared pointers, all backlist entries. It builds a complete picture of what is connected to what, at what weight, through which definitions.

This is a background process. It runs when Isaac is idle. It does not block the pipeline. It picks up wherever it left off.

### 2. Find Co-Occurrence Patterns (Unnamed Dims)

Some dimensions consistently appear together across many nodes. The crystallizer finds these.

**Example:** Nodes "dog," "cat," "hamster," "rabbit" all share pointers to dims 23 (domestic), 26 (pet), 31 (fur), 9 (animate). No one told the system these dims go together. But they do — in every node that has one, it has the others.

The crystallizer creates an unnamed pattern node:

```
=== pattern_0042 ===
name: pattern_0042
source: crystallized

--- def:0 pattern ---
a recurring co-occurrence of dims
+127:domestic +127:pet +127:fur +127:animate

--- backlist ---
+100:dog +100:cat +100:hamster +100:rabbit
```

This node has no name that means anything. It doesn't know it represents "domestic pets." But structurally, it IS domestic pets. The pointers define it. If someone later teaches Isaac that this pattern is called "domestic_pet," the name gets attached. If nobody does, the pattern still works as a structural object — it can be compared, it has a backlist, other nodes can point to it.

**The critical principle:** The crystallizer can create things it cannot name. The structure is the identity. The name is a label of convenience.

### 3. Find Missing Overlaps

Two nodes share 80% of their dims but have no pointer between them. The structure says they should be connected.

**Example:** "Whale" has pointers to aquatic, mammal, large, animate. "Dolphin" has pointers to aquatic, mammal, large, animate, social. They share 4 out of 5 dims. But there is no pointer between whale and dolphin.

The crystallizer proposes: whale and dolphin should be connected. The evidence is their dimensional overlap. The proposal includes the overlap count, the shared dims, and the divergent dims (social is in dolphin but not whale).

### 4. Find Broken Overlaps

Two nodes are connected but their dims barely overlap. The edge doesn't have structural support.

**Example:** "Cat" has a pointer to "table" at weight +3 (accumulated from "the cat sat on the table" type inputs). But cat's dims (feline, domestic, animate, pet, fur) and table's dims (furniture, flat_surface, concrete) share almost nothing. The connection exists but the structure doesn't support it.

The crystallizer proposes: investigate cat→table. Low dimensional overlap relative to weight. Either the connection is wrong (should be cat→sat→table), or there's a missing intermediate structure (cat LOCATED_ON table, where the spatial relationship is the real connection).

### 5. Classify Connections

Two nodes are connected. What KIND of connection is it? The crystallizer looks at both nodes' type profiles and proposes a classification.

**Example:** "Dog" (noun, concrete, animate) points to "animal" (noun, category). The crystallizer observes: when a concrete noun points to a category noun, every case in the net follows the same pattern — the concrete is an instance of the category. Propose: this connection type is "instance_of." Create a pattern node for it.

**This replaces the hardcoded interaction content nodes.** The crystallizer discovers interaction types from the structure. "Noun pointing to category means IS_A" is not seeded — it's crystallized from observing that every noun→category connection in the net behaves the same way.

### 6. Sort and Retype

A node's actual pointer profile doesn't match its declared type.

**Example:** A word was tagged as a noun during seeding, but in practice its pointers look like a verb — it connects to action, movement, past_tense. Its BEHAVIOR in the graph is verb-like even though its label says noun.

The crystallizer proposes: reclassify this node. Or: create a new definition (this word is a noun in one sense and a verb in another).

### 7. Route Misplaced Information

A pointer is on the wrong definition. The dims say it belongs elsewhere.

**Example:** Node "red" def:0 (visual-property) has a pointer to "political_alignment." But political_alignment has zero overlap with visual-property dims. It has high overlap with def:1 (political alignment). The pointer is on the wrong definition.

The crystallizer proposes: move pointer from def:0 to def:1. Evidence: dimensional overlap with def:1 is 90%, with def:0 is 0%.

### 8. Discover Rules

Structural invariants across the graph.

**Example:** Every node that points to "aquatic" also points to "movement." Every node that points to "past_tense" also points to "verb" or "action." Every node with "domestic" also has "animate."

These aren't coincidences. They're structural rules the data follows. The crystallizer proposes: aquatic implies movement. Past_tense implies verb. Domestic implies animate. Each proposal includes the count of nodes that follow the rule and the count of exceptions.

If the rule is universal (zero exceptions), it becomes a hard constraint. If it has exceptions, those exceptions are themselves interesting — they might be errors, or they might reveal a structural distinction.

### 9. Detect Redundancy

Two nodes that might be the same thing.

**Example:** "Big" and "large" have near-identical pointer profiles. They connect to the same dims at similar weights. Their backlists overlap heavily. They might be synonyms.

The crystallizer proposes: possible merge. Evidence: 95% dimensional overlap, 80% backlist overlap. Not implemented automatically — lift decides.

### 10. Detect Ambiguity

One node that might be two things.

**Example:** A node has two clusters of dims that don't overlap with each other. Its def:0 pointers cluster around meaning A and its def:1 pointers cluster around meaning B, but the shared pointers include things that only apply to one meaning.

The crystallizer proposes: possible split. Or: shared pointer reclassification — move the shared pointer that only applies to meaning A into def:0.

---

## How It Outputs

Every discovery is a **proposal**. A proposal is a node in the graph with a specific structure:

```
=== proposal_0107 ===
name: proposal_0107
source: crystallized

--- def:0 proposal ---
Missing overlap: whale and dolphin share 4 dims but have no connection
+127:proposal_type_missing_overlap
+100:whale
+100:dolphin

--- evidence ---
shared_dims: aquatic, mammal, large, animate
shared_count: 4
divergent_dims: social (dolphin only)
divergent_count: 1
overlap_ratio: 80

--- status ---
pending (awaiting lift evaluation)
```

The lift layer examines proposals and decides:
- **Accept:** implement the proposed change
- **Reject:** discard, with reason logged
- **Defer:** not enough evidence yet, revisit later
- **Investigate:** the proposal surfaced something interesting but the action isn't clear

Accepted proposals become structural changes to the net. Rejected proposals are learning data — the crystallizer learns what kinds of proposals get rejected.

---

## What It Needs From the Existing System

**The Comparator.** Every comparison the crystallizer makes is a Comparator call. Dimensional overlap between two nodes = one Comparator call. No new mechanism.

**The Net.** Full read access to all nodes, all pointers, all backlists. The primary data source.

**The Wrong Pile.** Every correction record with full context — what was wrong, what was right, what types were involved, what interaction node fired, what the activation map looked like. This is how the crystallizer learns what the pipeline consistently gets wrong.

**The Rejection Pool.** Losing interpretations from the gate. Patterns in what consistently loses are structural knowledge.

**The Pipeline Telemetry.** Activation maps, context subnets, integration results. The crystallizer needs to see how the pipeline processes things, not just what it produces.

**Training History.** Every `\train` result — expected vs. actual, what was missed, what was wrong. The delta between expected and actual IS the learning signal.

**Its Own Proposal History.** What lift accepted, rejected, deferred. The crystallizer learns which kinds of proposals are valuable.

**Node creation ability.** The crystallizer must be able to create proposal nodes and unnamed pattern nodes. These are the only writes it makes directly — and they're proposals, not structural changes to existing nodes.

---

## Priority Order

The crystallizer has limited cycles. It should prioritize by **learning value**, not by traffic or weight.

```
learning_value = overlap_percentage × divergent_count
```

This is the same function from the main proposal. It naturally selects the most interesting comparisons:

- **Dog vs dolphin** — high overlap, high divergence. Maximum learning value. The crystallizer finds what makes them different despite being so similar.
- **Dog vs cat** — high overlap, low divergence. Low learning value. They're too similar. Not much to discover.
- **Animal vs noun** — low overlap, massive divergence. Low learning value. They're too different. Noise, not signal.
- **Noun (high-traffic node)** — connects to everything. Every comparison produces noise because the overlap is diluted across thousands of connections. The signal-to-noise ratio is terrible.

In practice, the most interesting discoveries come from **mid-range nodes** — enough connections to show patterns but not so many that every pattern is diluted. The learning value function naturally finds these without needing a hand-tuned traffic threshold.

Scan order:
1. **Highest learning-value pairs first.** The Comparator between two nodes produces the telemetry. The learning value is derivable from it. Rank all candidate pairs by learning value. Work from the top.
2. **Recently changed nodes.** Anything modified since the last pass gets re-compared against its neighborhood. Changes create new potential.
3. **Flagged items.** Anything the wrong pile, rejection pool, or training corrections flagged. These are where the system KNOWS it has a problem. The crystallizer needs to understand WHY.

---

## The Cycle

```
Scan → Compare → Discover → Propose → (Lift evaluates) → Learn from lift's decisions → Scan again
```

**The crystallizer is recursive.** Each pass may produce new pattern nodes, new rules, new unnamed dims. Those new nodes are themselves data in the net. The next pass scans them too — and may find meta-patterns that only become visible AFTER the first-pass patterns exist.

```
Pass 1: Finds dog/cat/hamster share dims → creates pattern_0042 (domestic pets)
Pass 2: Finds pattern_0042 and pattern_0051 (aquatic animals) share dims → creates pattern_0078 (animals)
Pass 3: Finds pattern_0078 (animals) and pattern_0063 (plants) share dims → creates pattern_0091 (living things)
Pass 4: No new proposals. Stable. Stop.
```

Each pass crystallizes potential into structure. That structure becomes potential for the next pass. The recursion terminates when a pass produces zero new proposals — the net has been fully crystallized at the current depth.

This IS the recursive comparison from the intelligence theory. The Comparator applied to its own outputs, producing higher-order structure, which becomes input for the next level of comparison. The crystallizer doesn't run once. It runs until it can't find anything new. What it finds on pass N unlocks meta-patterns on pass N+1 that were invisible before.

**Termination:** A pass with zero accepted proposals means the current evidence has been fully crystallized. New input, new training, or new corrections will create new potential — and the crystallizer runs again.

**Depth tracking:** Each pattern node records which pass created it. Pass-1 patterns are direct observations. Pass-2 patterns are meta-observations. Pass-3 patterns are meta-meta-observations. The depth IS the holonic level — emergent structure at increasing scales of abstraction.

---

## Relationship to Intelligence Theory

The crystallizer is D2 through D4 — not just D2.

**D2 (Interpretive/Reactive):** It watches the Comparator's outputs (D1) over time and finds regularities. Co-occurrence patterns, broken overlaps, redundant nodes. This is the base level.

**D3 (Predictive):** It extracts rules — "aquatic always co-occurs with movement" — which are predictions about future observations. If a new aquatic node appears without movement, the rule predicts it should have it. The crystallizer doesn't just find what IS, it finds what SHOULD BE.

**D4 (Systemic):** It holds the entire structural model at once and navigates freely. It can compare any pair against any other pair. It can trace chains of implication. It can find that a rule in one domain mirrors a rule in another. It operates on the whole net, not on individual inputs.

The lift layer that evaluates proposals is the deliberation component of D4 — it takes the crystallizer's observations and projections and decides what to implement. Together, crystallizer + lift = observation + projection + deliberation. The base of structured reasoning.

**This is what makes Isaac genuinely intelligent rather than a fancy database.** Without the crystallizer, information goes in and stays exactly as it was put in. With the crystallizer, information goes in and the system discovers what it means, how it connects to everything else, what rules it follows, and what it implies. That's understanding. That's what GOFAI couldn't do and what the crystallizer makes possible.

---

## Closing the Learning Loop

Without the crystallizer, Isaac's learning is linear: teach it A, it knows A. Teach it B, it knows B. It never discovers C on its own. Every piece of knowledge was put there by a human.

With the crystallizer, learning compounds:

1. **Pipeline processes input.** Creates raw observations. Makes mistakes.
2. **Training corrects mistakes.** Wrong edges go to the wrong pile with full context. Right edges get created.
3. **Crystallizer examines everything.** The net, the wrong pile, the rejection pool, the training history. It finds: "words typed as copula always produce wrong edges when treated as targets. Here's the evidence from 15 wrong pile records."
4. **Crystallizer proposes a rule.** "Copula-typed words should not be edge targets." This is a new node — an unnamed pattern or a named rule — with pointers to the evidence.
5. **Lift evaluates.** Accepts the rule. The rule becomes a structural fact in the net.
6. **Pipeline uses the rule.** Next time a copula appears, the context subnet builder can check if the word has a connection to the "not a target" rule. The pipeline's behavior changes — not because a developer hardcoded it, but because the crystallizer discovered it from accumulated evidence.
7. **The pipeline makes fewer mistakes.** Which means the wrong pile changes character. Which means the crystallizer finds different, deeper patterns. Which means new proposals. Which means more learning.

This is the compound loop. Each cycle produces knowledge that makes the next cycle more productive. The crystallizer is the engine of that compounding. Without it, Isaac is static. With it, Isaac improves with every pass.

This is what GOFAI and FCA could never do. They could represent knowledge beautifully. They could reason over it correctly. But they could never look at their own knowledge and discover structure that nobody put there. The crystallizer closes that gap.

---

## Build Order

### Phase A — Scanner
Walk the net. Build per-node dimensional profiles. Compute learning value for node pairs. Identify highest-value candidates. Store profiles for comparison.

### Phase B — Co-occurrence Detection
Compare profiles by learning value order. Find dims that consistently co-occur. Create unnamed pattern nodes.

### Phase C — Overlap Analysis
Find missing overlaps (should be connected, aren't). Find broken overlaps (connected, shouldn't be). Score each by the strength of the structural evidence.

### Phase D — Wrong Pile Analysis
Read the wrong pile. Cluster correction records by source types, target types, and interaction nodes used. Find recurring patterns in what the pipeline gets wrong. Propose rules to prevent classes of errors.

### Phase E — Connection Classification
Look at connected pairs' type profiles. Cluster connection types. Create pattern nodes for recurring connection types. This is where IS_A, HAS_PROPERTY, CAN_DO get DISCOVERED rather than seeded.

### Phase F — Anomaly Detection
Find mistyped nodes, misplaced pointers, redundant nodes, ambiguous nodes.

### Phase G — Proposal System
Structure all discoveries as proposal nodes. Interface with lift for evaluation. Track proposal outcomes for meta-learning.

### Phase H — Rule Discovery
Find structural invariants across the entire graph. Universal rules, near-universal rules with named exceptions. Rules derived from the wrong pile, the rejection pool, and the training history.

---

## Success Criteria

1. Given a seeded net with 50 animal words and no category labels, the crystallizer discovers the "domestic pet" pattern and the "aquatic" pattern without being told.
2. Given 100 trained sentences, the crystallizer discovers that copula-typed words consistently appear in wrong edges and proposes a connection classification rule for them. **This is the test that proves the wrong pile learning works.**
3. Given two synonyms with near-identical profiles, the crystallizer proposes a merge.
4. Given a polysemous word with two unrelated definition clusters, the crystallizer proposes a split.
5. After 10 crystallizer passes, the net has more structural knowledge than what was explicitly taught — the crystallizer found things the training didn't cover.
6. Unnamed pattern nodes are functional — they can be compared, queried, and used as targets, even without human-readable names.
7. After processing the wrong pile from 20 training corrections, the crystallizer proposes at least one rule that, if implemented by lift, would prevent a class of pipeline errors from recurring.
8. The crystallizer discovers connection types (IS_A, HAS_PROPERTY, CAN_DO) from the structure — not because they were seeded, but because it observes that certain type pairings consistently connect in the same way.

---

*The crystallizer is where Isaac stops reciting and starts thinking.*
