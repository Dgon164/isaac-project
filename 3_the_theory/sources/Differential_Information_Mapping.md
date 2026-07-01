# Differential Information Mapping
## The Double Black Box Theory

---

## The Problem

You have a black box. You cannot open it. You have no reference frame — no labels, no legend, no prior knowledge of what it contains. You have only the box itself.

Now you have two black boxes. You still cannot open either one. But you can hold them next to each other and observe what happens.

This is the only operation available: comparison. From comparison alone, you must derive everything — identity, structure, relationships, rules, and meaning.

The question is: what is the maximum amount of information you can extract, and what are the operations that extract it?

---

## The Primitives

Every black box is composed of four primitives. You cannot see them directly, but comparison reveals their effects.

**Dim** — an address. A position in a space. Which slot is occupied. By itself, dimensionless and meaningless — it is only a coordinate.

**Weight** — a magnitude and a direction. How much, and which way. Positive or negative. Strong or weak. By itself, a number attached to nothing.

**Node** — a collection of dim+weight pairs. A bag of assertions. Each assertion says "at this address, this much, in this direction." The bag is the identity.

**Frame** — an aggregation of nodes at a given scale. Multiple nodes merged together, with magnitude reflecting how much evidence supports each dimension. A word is a frame of width 1. A sentence is a frame of width N. Same data type, different resolution.

None of these say anything alone. Meaning begins at combinations of two.

---

## Combinatorial Information — What Exists

The first class of information comes from reading what is present and comparing it across boxes. No modification, no experimentation — just observation.

### Two-primitive combinations

**Node + dims (weights ignored) → Type.** Which positions are occupied at all? This defines the category. Two nodes with the same dims lit up are the same type, regardless of how strongly. A mammal-type thing occupies positions 12, 47, 203. Anything else occupying those same positions is categorically similar.

**Node + weights (dims ignored) → Intensity profile.** How strongly does this node assert anything? A node with all weights near maximum is densely evidenced. A node with all weights near minimum is barely established. You know how confident the node is, but not what it's confident about.

**Dim + weight → A single assertion.** One fact. One pointer. "Position 47, strength 90, positive." The atom of information.

**Frame + dims → Consensus type.** Which dimensions survived aggregation? At the sentence scale, only the dims that multiple words reinforced (or that one word carried strongly enough to survive dilution) are still nonzero. This is what the sentence is *about*, categorically.

**Frame + weights → Consensus strength.** How well-supported is each surviving dimension at this scale? Under arithmetic mean merging, the weight directly encodes evidence count: a weight of 50 at a frame of width 8 means roughly 3 of 8 leaves carried this dimension at full strength.

### Three-primitive combinations

**Node + dim + weight → Identity.** The complete pointer list. This is what the node *is*. The full answer to "what are you?"

**Frame + dim + weight → Contextual identity.** The same as identity, but at a given scale. A word frame is one word's identity. A sentence frame is the sentence's identity. A paragraph frame is the paragraph's. Same structure, different resolution.

**Node + node + dims → Type overlap.** Which types do two nodes share? Which categories do they both belong to? Weights stripped — just the categorical intersection and difference.

**Node + node + weights → Strength comparison.** For the dimensions they share, how similarly weighted are they? Both strongly mammalian, or one strongly and one weakly?

### Four-primitive combinations

**Node + node + dim + weight → Full structural comparison.** The complete output of holding two boxes next to each other. For every dimension in either node: is it shared (both have it, same sign), divergent (both have it, opposite signs), or absent (one has it, the other doesn't)? With the actual weights on both sides. This is the maximum information extractable from a single comparison between two boxes.

**Frame + frame + dim + weight → Cross-scale comparison.** Compare a word frame to its sentence frame. Which of the word's dimensions survived to the sentence level, and at what dilution? This tells you what the word contributed to the larger meaning, and what was lost.

---

## The Six Questions

The combinatorial information answers six questions about any node. These form three axes.

### Self axis — what is this box?

**1. What is it?** Its nonzero dimensions define what it is. The set of occupied positions is its type. The weights at those positions are its identity.

**2. What is it not?** Its zero dimensions define what it is not. The set of unoccupied positions is everything it has no evidence for. Absence is not negation — it is unknown, not opposite.

### Match axis — how does this box sit against another?

**3. What does it compare to?** Shared dimensions with another node. Same address, same sign. The overlap defines the relationship. More shared dims with higher weights means stronger structural similarity.

**4. What doesn't it compare to?** Divergent dimensions (same address, opposite signs) and absent dimensions (present in one, missing from the other). Divergence is active disagreement. Absence is non-overlap.

### Lineage axis — where does this box come from, and what does it build?

**5. What is it made of?** The pointer list: which other nodes compose this one, at what weight. Its parents. Follow the pointers and you decompose the node into its constituents. This is looking down.

**6. What can it make?** The backlist: which nodes point to this one. What it participates in building. Its children. This is looking up.

Comparison answers questions 1–4. The pointer list answers question 5. The backlist answers question 6. Every cognitive operation — learning, thinking, querying — is asking one or more of these six questions across many nodes simultaneously.

---

## Perturbation Information — What Matters

The second class of information comes from *modifying* a box and observing what changes. This is experimentation, not observation. You are no longer reading the graph — you are testing it.

Combinatorial analysis tells you what a cat *is*. Perturbation analysis tells you what makes a cat *a cat*.

### Three perturbation operations

**Ablative — remove something.** Zero out a dimension. "Cat minus fur." Compare the result against the original, or against a target. The delta in comparison output tells you how much that dimension contributed to the original match. If removing fur barely changes the mammal-match, fur is incidental to mammalness. If removing fur tanks the Persian-match, fur is definitional to Persianness.

Same dim, same node, different importance depending on the comparison target. Contribution is always relative to a question being asked.

**Additive — inject something foreign.** Add a dimension the node doesn't have. "Cat plus wings." Compare the result against various targets. The delta tells you how much that foreign dimension moves the node toward or away from other concepts. If adding wings increases the bird-match by 5 but the mammal-match only drops by 1, the boundary between mammal and bird is asymmetric — it's easier to approach bird than to leave mammal.

How many foreign dims do you need to add before the node starts matching the foreign concept better than its original cluster? That count *is* the distance between the two concepts, measured in dimensions.

**Substitution — swap one thing for another.** Remove a dimension and replace it with a different one. "Cat with tentacles instead of whiskers." This probes two boundaries simultaneously: how much does removing whiskers degrade catness, AND how much does adding tentacles push toward something else? The compound delta tells you whether the concept is defined more by what it has or by what it doesn't have.

If swapping whiskers for tentacles barely changes the mammal match, whiskers were not structurally load-bearing for mammalness. If it tanks the match, whiskers were definitional. Substitution is the sharpest instrument because it tests addition and removal in one operation.

### What perturbation reveals that combination cannot

Combinatorial analysis tells you that cat has 20 nonzero dimensions. Perturbation analysis tells you that 5 of those are definitional (removing any one of them significantly changes what the node matches), 12 are supporting (removing them slightly weakens matches but doesn't change which targets are best), and 3 are incidental (removing them changes nothing).

This is the difference between the *structure* of a node and the *function* of a node. Structure is what it is. Function is what it does in context. Two nodes can have identical structure but different function if they sit in different neighborhoods of the graph.

---

## Crosswise Interaction — The Coupling Matrix

Individual perturbation runs in sequence can tell you each dimension's contribution independently. But dimensions are not independent. They interact. Two dimensions that are individually unimportant might be jointly critical.

This is where crosswise comparison changes everything.

### The method

Take a node with D nonzero dimensions. Generate D+1 vectors: the original, plus D copies each with one dimension zeroed out. Stack them into a matrix. Run all-vs-all comparison in a single dispatch: (D+1)² pairwise comparisons.

For dim=256, that's 66,049 comparisons. For dim=64, it's 4,225. Both are trivial for a GPU that handles 100 million comparisons per chunk.

### What falls out

**The diagonal** — each perturbed copy compared against the original. This is the ablative contribution vector: how much each dimension individually matters.

**The off-diagonals** — each perturbed copy compared against every other perturbed copy. This is the interaction structure. If the copy missing dim X and the copy missing dim Y are nearly identical to each other, then X and Y are independent — they don't affect each other's contribution. If those two copies are very *different* from each other, X and Y are coupled — they interact, they form a functional unit, damaging one changes the meaning of the other.

### The coupling matrix

The off-diagonal entries form a D×D coupling matrix. Each cell represents the interaction strength between two dimensions within this node.

**Near-zero coupling** — independent dims. Can be removed or added without affecting each other. They contribute to different aspects of the node's identity.

**Strong positive coupling** — cooperative dims. They form a functional sub-unit. Together they mean something that neither means alone. The "whisker-face complex" — whiskers and a face-shape and forward-facing eyes and pointed ears form a coupled cluster that together define "cat face." Remove any one and the others lose contextual meaning.

**Strong negative coupling** — competitive dims. Each one dilutes the other's contribution. They represent alternative aspects of the node that partially cancel.

### What the coupling matrix reveals

From one GPU dispatch per node:

**Functional sub-units.** Clusters of tightly coupled dims within the node. These are the node's internal parts — the structural decomposition. A cat is not 20 independent features; it's 4-5 functional units (face-cluster, body-plan-cluster, behavior-cluster, domestication-cluster) each made of coupled dims.

**Load-bearing dims.** Dims with high diagonal values (important individually) AND high off-diagonal coupling to other important dims. These are the keystones — remove them and the functional unit collapses.

**Incidental dims.** Low diagonal, low off-diagonal. Removing them changes nothing, and nothing depends on them. Noise, or context-specific coloring that doesn't affect identity.

**Bridge dims.** Low individual contribution but high coupling to dims in different functional units. They don't matter much alone, but they connect two sub-structures. Remove a bridge dim and two previously related aspects of the node become independent.

---

## Crosswise Perturbation — Additive and Substitutive

The same crosswise method applies to all three perturbation types.

### Additive crosswise

Take a node. Select D_candidate foreign dims from another concept. Generate D_candidate copies, each with one foreign dim injected. Run all-vs-all.

The diagonal tells you each foreign dim's individual effect. The off-diagonals tell you which foreign dims *cooperate* — "adding wings and adding feathers together push harder toward bird than either alone." This reveals the internal structure of the *target* concept as seen from the perspective of the *source* concept.

### Substitutive crosswise

Generate copies with each swap applied. Crosswise reveals which swaps are compatible. "Swapping whiskers for tentacles AND swapping fur for scales together push harder toward alien than either swap alone, so whiskers and fur are coupled in defining mammalness, and tentacles and scales are coupled in defining alienness."

Substitution crosswise is the most information-dense operation: one dispatch reveals the coupling structure of both the source concept (which removals interact) and the target concept (which additions interact), plus the cross-coupling (which swap-pairs have synergistic effects).

### Combined sweep

For a complete analysis of one node against one target concept, you can combine all three perturbation types in a single dispatch:

- D ablative copies (one dim removed each)
- D_target additive copies (one foreign dim added each)
- D × D_target substitution copies (one dim swapped each)
- The original unperturbed vector

Total vectors: 1 + D + D_target + (D × D_target). At D=256, D_target=20 (top 20 dims of the target node), that's 1 + 256 + 20 + 5,120 = 5,397 vectors. All-vs-all on 5,397 vectors is ~29 million comparisons. One chunk's worth. One GPU dispatch.

The result is a complete differential map of how one concept relates to another: which of its parts matter, which foreign parts would change it, and which swaps move it across boundaries.

---

## Emergent Node Types

The combination of combinatorial analysis and perturbation experimentation produces information that is too structured to live only in intermediate computations. It crystallizes into persistent nodes.

### Word nodes — identity
What dims exist, at what weights. The raw assertion. "This is what I am." Created by the ingestion pipeline when text is processed.

### Backreference nodes — co-occurrence clusters
Which dims travel together across many nodes. "These dimensions usually appear as a group." Created when concept emergence detects consistent co-occurrence. You can compare a new unknown node against a backreference node to test cluster membership in one comparison instead of N.

### Constraint nodes — dim-to-dim rules
Discovered from cross-node coupling analysis. Not "which dims travel together" (that's backreference) but "which dims *must* or *cannot* coexist, and in what polarity."

Types of constraints:
- **Mutual exclusion** — these dims are never both positive in the same node.
- **Implication** — this dim predicts that dim, directionally. Not symmetric.
- **Polarity lock** — if dim X is positive, dim Y must be negative. Not absent — actively opposite.
- **Weight correlation** — these dims scale together proportionally.
- **Scale restriction** — this dim only appears at certain frame levels. Some dimensions are word-level only. Some only emerge at sentence level.

### Contribution nodes — essentiality profiles
Discovered from perturbation analysis. For a given backreference cluster, which dims are definitional, which are incidental, and which are gateway dims (adding them to a non-member creates membership).

### Coupling nodes — internal structure maps
Discovered from crosswise perturbation analysis. The functional sub-units within a concept — which dims form cooperative clusters, which are bridges between clusters, which are keystones.

### Meta nodes — structural rules
Positional and relational patterns. Not about content but about how content interacts based on role. Discovered from comparing sentence frames across many sentences and finding positional regularities.

---

## The Operation Taxonomy

All information extraction reduces to applications of one operation (comparison) with varying modes of input preparation.

### Read
Input: one node, unmodified.
Output: its dims, weights, type, intensity profile.
Questions answered: 1, 2 (self axis).
What you learn: what it is.

### Compare
Input: two nodes, unmodified.
Output: shared, divergent, absent classifications with weights per dimension.
Questions answered: 3, 4 (match axis).
What you learn: how two things relate.

### Mask (ablative)
Input: one node with one or more dims zeroed, compared against a target.
Output: delta in comparison output.
Questions answered: how much does this part contribute to this relationship?
What you learn: which parts matter for which matches.

### Inject (additive)
Input: one node with one or more foreign dims added, compared against a target.
Output: delta in comparison output.
Questions answered: how close is this thing to becoming that thing?
What you learn: concept distance measured in dimensions, boundary shape.

### Swap (substitutive)
Input: one node with one or more dims replaced by foreign dims, compared against a target.
Output: compound delta in comparison output.
Questions answered: what defines the boundary between these two concepts?
What you learn: which features are load-bearing on both sides simultaneously.

### Crosswise
Any of the above three (mask, inject, swap) run as all-vs-all across the full set of perturbations in a single dispatch.
Output: coupling matrix — the interaction structure between all perturbed dimensions.
Questions answered: which parts form functional units? Which parts are independent? Which are bridges?
What you learn: the internal architecture of a concept.

---

## Relationship to the Six Questions

The six questions are answered by different combinations of operations:

| Question | Operation(s) | What you get |
|---|---|---|
| 1. What is it? | Read | Nonzero dims and weights |
| 2. What is it not? | Read | Zero dims |
| 3. What does it match? | Compare | Shared dims |
| 4. What doesn't it match? | Compare | Divergent + absent dims |
| 5. What is it made of? | Read (pointer list) + Mask (which parts are load-bearing) | Lineage down, with importance weights |
| 6. What can it make? | Read (backlist) + Inject (what happens when others gain its features) | Lineage up, with influence weights |

Questions 1–4 are fully answered by combinatorial operations. Questions 5 and 6 gain depth from perturbation: the pointer list tells you the *structure* of the lineage, but masking and injection tell you the *function* of the lineage — which inherited parts actually matter, and how much influence this node exerts on the things it participates in building.

---

## The Double Black Box

The title of this framework comes from the fundamental constraint: you have two boxes you cannot open. You can only hold them together and observe the comparison output. Everything else — identity, structure, coupling, boundaries, rules — is derived from that single operation applied repeatedly with systematic perturbations.

One box gives you nothing. You need two to begin. But two is enough.

From two black boxes and one comparison operation, applied combinatorially and with systematic perturbations, you can derive:

- What each box is (identity)
- What each box is not (absence)
- How they relate (similarity and difference)
- What parts of each box matter for the relationship (contribution)
- Which parts of each box form internal units (coupling)
- Where the boundary is between the concepts they represent (perturbation sweeps)
- What rules govern which parts can coexist (constraint discovery)
- What larger structures each box participates in (lineage)

You never open the boxes. You never need to. The comparison *is* the instrument. Perturbation *is* the experiment. The graph that accumulates from millions of such experiments *is* the knowledge.

---

## Computational Characteristics

All operations reduce to the Comparator applied to arrays of vectors. Every mode of input preparation (read, compare, mask, inject, swap, crosswise) produces vectors that feed into the same comparison kernel. The GPU sees the same operation regardless of what question is being asked.

**Ablative sweep of one node (D=256):** 257 vectors → ~66K comparisons → one dispatch.

**Additive sweep against one target (D_target=20):** 21 vectors → ~441 comparisons → one dispatch.

**Full substitutive crosswise (D=256, D_target=20):** ~5,400 vectors → ~29M comparisons → one dispatch.

**Batch profiling of 1,000 nodes (ablative only):** 1,000 × ~66K = ~66M comparisons → one chunk's worth of GPU work.

The perturbation operations do not require new GPU kernels, new data formats, or new pipeline stages. They require only the ability to generate modified vectors and feed them into the existing all-vs-all comparison dispatch. The entire framework runs on the single primitive that already exists.
