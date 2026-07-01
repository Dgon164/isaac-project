# Trie-Structured Concept Discovery with Convergence Routing and Defeasible Theorist

## A Recursive Architecture for Efficient Structural Inference via Formal Concept Analysis

---

### Abstract

We present an extension to iterated lift on an open dim field (SIS v34) that reframes the level hierarchy as a trie, replaces O(n²) brute-force comparison with convergence routing, and introduces a theorist operator that discovers both structural gaps and exclusion rules from the same substrate. The architecture rests on three advances: (1) a streaming discovery pipeline (route, crystallize, lift, grow) that builds the concept trie incrementally at O(context × depth) per entity; (2) a crystallizer that accumulates orphan dims from routing failures and suggests candidates to lift without comparing all pairs; and (3) a theorist that performs matrix completion within discovered domains, proposes hypothetical entities as persistent nodes, and discovers negative dims (structural exclusions) that carve circle boundaries. Proposals follow a lifecycle — open, cautioned, confirmed, dissolved — where only confirmed evidence can kill a proposal, and every discovered rule is defeasible. We validate on a controlled 20-entity synthetic dataset, demonstrating that the streaming pipeline achieves 95% of brute-force lift's recall while building incrementally, that the theorist correctly predicts structural gaps (confirmed by held-out entities), and that the complete loop — observation, crystallization, lift, theorist, recrystallization — produces and self-corrects concept structure without external supervision.

---

## 1. Introduction

The predecessor architecture (iterated lift on an open dim field) demonstrated that recursive application of a single discovery operator to its own outputs produces meta-structure that a single-level lattice cannot encode. Level-1 lift on dim co-activation achieved a 20-percentage-point improvement in held-out attribute recovery over a steel-manned single-level FCA baseline, and level-2 produced non-trivial cross-niche structure beyond level-1.

Two problems remained. First, lift's naive complexity is O(n²) in the items to be grouped. For dim fields growing to 10⁵ or 10⁶, the naive implementation does not scale. Second, the architecture could organize what it observed but could not produce hypothetical instances that the existing structure had implicitly committed to — the "theorist" capability described in the working notes but not implemented.

This paper addresses both. We reframe the level hierarchy as a trie and show that new inputs can be routed through existing structure at O(context × depth), eliminating the quadratic bottleneck. We introduce the theorist as the operator that completes a circle's dim profile by discovering negative dims and proposing structural gap entities as persistent nodes in the graph.

The central insight unifying both advances is that the four operators described in the predecessor architecture — comparator, crystallizer, lift, theorist — reduce to a single primitive: **compare**. The crystallizer compares partial groupings. Lift compares stable boundaries. Routing compares input against structure. The theorist compares what exists against what the structure predicts should exist. The different names describe different scopes for the same operation, not different mechanisms.

---

## 2. The Trie Reframe

### 2.1 Levels as selector groups

The predecessor architecture indexed concept lattices by integer level L_k and described the recursion as "stacking" — L0 produces entity circles, L1 produces dim-bundle circles, L2 groups L1 circles by substrate footprint. This framing suggests uniform layers of increasing abstraction.

The reframe treats the levels as a **trie**: a prefix tree where higher levels are selector groups that narrow the search space for levels below. L2 selects which L1 groups are relevant. L1 selects which L0 entities are worth comparing. Each level up prunes the branch space before the pairwise work happens at the bottom.

If L1 cuts the working set to 1/5 of entities, the pairwise cost at L0 drops to (n/5)² = n²/25 — 4% of the naive cost. This is the lottery ticket connection: higher levels identify the sparse substructure that carries the signal, and most of the n² pairs are noise.

### 2.2 Resolution depth, not semantic rank

The level number is not semantic rank. It is **resolution depth** — how many passes through the pipeline a concept took to stabilize. In our experiments, "birds" (feathers + bird, cohesion 1.0) resolved in one lift pass and sits at L1 as a finished concept. "Tools" fragmented across multiple L1 circles during streaming — material-groups, use-groups, weapon-subgroups — and required a second pass (what we initially called "L2") to sort redundant from complementary. Both are peer concepts semantically; their different depths reflect different discovery paths, not different importance.

This means the trie is heterogeneous. Some branches are shallow, some deep. A fully resolved L1 node is more useful than an unresolved L2 node. The question "what level is this concept at" is wrong; the right question is "is this concept resolved."

### 2.3 Dual membership and polysemy

An entity can sit in multiple circles simultaneously. A hammer belongs to a tool circle and (with the right data) to a weapon circle. This dual membership is itself the signal for a higher-order concept — the shared structure between the two circles that makes dual membership possible.

L1 selectors determine which circle activates in context. Workshop context activates tool dims and routes to the tool circle. Combat context activates weapon dims and routes to the weapon circle. Same entity, different routing. This connects directly to the polysemous definition system already present in the engine: multiple definitions on one node, each routing to different circles depending on which dims fire.

---

## 3. The Streaming Pipeline

### 3.1 Architecture: route → notice → suggest → judge → grow

The pipeline processes entities one at a time rather than in batch. Each entity passes through five stages:

**Route.** Each dim in the entity's profile is looked up in a circle-dim index. Dims that find a circle contribute to convergence scoring; dims that find no circle are orphans. Multiple dims converging on the same circle produce a convergence score proportional to the number of independent probes. Cost: O(|dims| × average circles per dim).

**Notice.** The crystallizer passively records each routing event. For each orphan dim, it stores which entity carried it and what neighborhood (which circles) the entity's non-orphan dims activated. This is accumulation, not comparison.

**Suggest.** When orphan dims co-occur across multiple entities — they keep appearing together on entities that route to the same neighborhood — the crystallizer packages them as a candidate set and sends them to lift. The crystallizer's threshold for suggesting is deliberately loose; it is a suggestion engine, not a decision maker.

**Judge.** Lift runs on the candidate set using the same operator as before. It accepts or rejects based on internal cohesion (pairwise Jaccard among the supporting entities' dim profiles). In our experiments, the rejection rate was approximately 86% — the crystallizer suggests broadly, lift filters strictly.

**Grow.** Accepted groups become new circle nodes in the trie. The circle-dim index is rebuilt. Future routing for any entity improves because new dims now have homes.

### 3.2 Recrystallization

Accepted circles trigger new edges via add_edge. Those edges trigger new routing observations. Those observations may accumulate enough orphan co-occurrence to trigger another crystallizer pass in the same cascade. In our experiments, 10 initial suggestions produced circles that themselves generated 6 additional accepted circles in the recrystallization pass.

This is iterative purification within a level, not promotion to a new level. The "noisy" intermediate circles are not noise — they are unresolved structure. The recrystallization pass resolves them.

### 3.3 L2 cleanup

After the trie stabilizes, a cleanup pass runs the same compare operation on circle nodes themselves. Each circle's signature is its substrate footprint (which entities are members). Circles with >50% dim overlap are redundant and collapse into the larger circle. Circles with ≤20% dim overlap but shared substrate footprint are genuine higher-order structure — they represent different facets of the same region of the trie.

---

## 4. Empirical Results: Pipeline

### 4.1 Convergence routing

We tested convergence routing by holding out entities from the 20-entity toy ontology, using partial dim-sets as context probes routed through L1.

| Context dims provided | Recall@5 |
|---|---|
| 2 | 34.3% |
| 3 | 40.6% |
| 4 | 46.9% |

No entity-to-entity comparison was performed. Routing quality is bounded by L1 coverage; orphan dims (those not in any L1 circle) are invisible to routing. The convergence predictor is only as good as the trie, and the trie improves as more entities are processed.

### 4.2 Streaming pipeline vs. brute force

20 entities processed sequentially (3 seed, 17 streamed).

| Metric | Static (seed only) | Pipeline | Brute-force lift |
|---|---|---|---|
| L1 circles | 1 | 20 | 9 |
| Dim coverage | 31% | 95% | 85% |
| Recall@5 | 30.7% | 70.1% | 73.7% |

The pipeline achieves 95% of brute-force recall while building incrementally. It produces more circles than brute-force (20 vs 9) because it discovers structure from multiple streaming entry points; the L2 cleanup pass collapses the redundant ones.

### 4.3 L2 recursive analysis

The 20 pipeline circles were run through the same lift operator to produce L2. Two L2 groups emerged. The tools group (6 L1 circles, all touching {axe, bow, hammer, knife, spear}) contained 3 redundant pairs and 7 complementary pairs. The natural-world group (13 L1 circles) contained 10 redundant pairs and 57 complementary pairs. One L1 circle (birds) was an L2 orphan — insufficient footprint with only 3 entities.

### 4.4 Engine integration

The pipeline was integrated into the SIS engine (sis_engine.py, v35). The add_edge method was modified to route through circles and feed the crystallizer on every new edge, with the crystallizer firing on the same interval cadence as the predecessor's counter-based lift trigger.

Test results with 15 entities via direct process_claim:
- 16 circles discovered (including recrystallization cascade)
- Wolf: 6 dims, 0 orphans, convergence score 5 on fur-teeth-mammal circle, top prediction LIVES mountain (score 7 — induced from structure, not stated in data)
- Axe: 4 dims, 0 orphans after crystallizer discovered tool domain
- L2 cleanup: 3 redundant circles collapsed, 2 real L2 groups found

---

## 5. The Theorist

### 5.1 Negative dims

Lift discovers positive dims — features that co-occur within a circle. The theorist discovers negative dims — features that are consistently absent from a circle's members despite being common elsewhere in the data.

A circle's complete profile after the theorist runs includes both:

- **Positive dims** (HAS_DIM edges): what members share. The shape.
- **Negative dims** (EXCLUDES_DIM edges): what no member has despite external prevalence. The boundary.

Routing uses both: positive dims attract entities toward a circle; negative dims repel entities that carry excluded features.

### 5.2 Matrix completion

The theorist discovers structural gaps via matrix completion within domains. For each domain (a group of entities sharing a high-level IS_A category), it identifies discriminating slots — dim-relation types with multiple values, each appearing on 2+ entities. It then checks which value combinations exist and which are absent.

An absent combination where both individual values are well-attested is a structural gap. The theorist constructs the hypothetical entity's dim profile by taking the union of common dims from entities carrying each individual value.

### 5.3 Proposal lifecycle

Hypothetical entities are materialized as **proposal nodes** — persistent graph objects with predicted dims. They follow a four-state lifecycle:

**OPEN.** Proposed from structural gap analysis. The system knows this gap exists and is waiting for evidence. Circle exclusions are noted as metadata (how many circles' negative dims the proposal touches) but do not block the proposal. These are defeasible observations, not constraints.

**CAUTIONED.** A constraint has been added to the graph (e.g., a PREVENTS edge) that touches the proposal's predicted dims. The proposal persists but is flagged. Constraints reduce confidence; they do not kill.

**CONFIRMED.** A new entity arrives whose dims match the proposal at ≥70% recall. The prediction was evidence before the observation — the system says "I predicted this." The proposal is promoted and linked to the confirming entity.

**DISSOLVED.** Confirmed evidence that this specific combination is impossible — not a general constraint, but specific rejection. This is the only way to kill a proposal. Same standard for killing as for creating: evidence in, evidence out.

### 5.4 Defeasibility

Every rule the system discovers is a pattern it has not yet seen broken. The theorist's negative dims are defeasible: teeth and feathers never co-occur in the data, so the bird circle excludes teeth. When a velociraptor (a bird with teeth) arrives, the exclusion is overridden by evidence and the circle's boundary reshapes.

This is the same principle described in the predecessor's working notes: "Newton's gravity was a lift output; Einstein refined it because new observations showed lift had reached the wrong mechanism." The theorist proposes the simplest boundary consistent with current observations. New observations can revise it.

The venus fly trap principle: plant and predator never co-occur in the data, so the system would caution any proposal combining them. But venus fly traps exist. The caution persists until evidence confirms or dissolves it — it never hard-blocks.

---

## 6. Empirical Results: Theorist

### 6.1 Gap discovery

On the 20-entity toy ontology, the theorist discovered 10 structural gaps including:

- **mammal: prey + large** — deer and rabbit are prey but not large; wolf and bear are large but predators. No large prey mammal exists. A moose fills this cell.
- **tool: weapon + small** — hammer is small but not a weapon; spear is a weapon but large. A dagger fills this cell.
- **predator: bird + teeth** — every predator with teeth is a mammal or fish. No bird has teeth. Structurally interesting: the dinosaur gap.
- **plant: edible + mountain** — edible plants live in meadows; mountain plants are not edible. Mountain berries fill this cell.

### 6.2 Confirmation test

Three held-out entities were introduced after gap discovery:

**Hippo** (mammal, prey, fur, teeth, river, large) → confirmed "large prey mammal" proposal. The system had predicted this gap from structure; the hippo filled it.

**Velociraptor** (bird, predator, feathers, teeth, forest, medium) → confirmed 5 proposals including "bird with teeth." These proposals were open with defeasible cautions from circle exclusions. The velociraptor overrode the exclusions.

**Dagger** (tool, weapon, iron, small, cutting) → 67% match with "small weapon tool" proposal. Near miss: the proposal predicted MADE_OF wood and USED_FOR striking (inferred from spear and bow), but dagger uses iron and cuts. Proposal remains open.

### 6.3 Constraint test

A plant ⊥ predator constraint was added. No proposals contained both dims, so no proposals were cautioned. If a "predator plant" proposal had existed, it would have moved to CAUTIONED — flagged but not killed. A venus fly trap arriving later would have confirmed it, overriding the constraint.

---

## 7. Architectural Summary

### 7.1 One primitive

The architecture reduces to a single primitive: **compare**. The crystallizer compares partial groupings into stable boundaries. Lift compares stable boundaries into circle nodes. Routing compares input against the trie. The theorist compares what exists against what the structure predicts. The different operator names describe scope, not mechanism.

### 7.2 Three operations on one structure

- **Observation** writes edges. An entity exists; here are its dims.
- **Deduction** traverses edges. An entity is a mammal; mammals have fur; therefore fur.
- **Induction** notices convergence. Multiple entities route to the same region but carry unplaced dims with no common parent. The convergence of unrelated probes is the missing concept. Nobody stated it; the structure implied it.

### 7.3 Complete circle profiles

A circle's full profile includes positive dims (what it is), negative dims (what it isn't), and proposal nodes (what the structure predicts should exist but doesn't yet). Lift builds the shape. Theorist carves the boundary and proposes occupants for empty positions. The three together — positive, negative, hypothetical — constitute the circle's complete structural description.

### 7.4 The dual-membership signal

When an entity sits in multiple circles, the dual membership itself signals a higher-order concept: the shared structure that makes dual membership possible. L1 selectors determine which circle activates in context. The same entity routes differently depending on which dims fire. This is the polysemy mechanism applied to concept structure: one node, multiple definitions, each activating different circles.

The theorist should notice when a structural gap's predicted dims match an existing entity that is near but not in the relevant circle. In such cases, the answer may not be a new entity but a new definition on an existing entity. The gap between "hammer as tool" and "hammer as weapon" is not a missing object but a missing assignment.

---

## 8. Limitations

### 8.1 Scale

All experiments were conducted on 15-20 entities with 39 dims. Whether the crystallizer's suggestion quality holds at 200+ entities, and whether the theorist's matrix completion produces meaningful proposals in richer domains, is untested.

### 8.2 Language

The architecture was tested on structured claims (direct process_claim calls). The engine's primary purpose — discovering structure from raw text without a parser — was not addressed. The activation window machinery (sentence_map, paragraph_map, dim_channel) exists but its connection to the trie routing model is not yet established.

### 8.3 Exclusion scoping

The theorist's negative dim discovery is sensitive to the number of circles. With many overlapping circles (31 in one test), almost every dim is excluded by some circle, and scoping exclusions to relevant circles requires careful threshold tuning. The defeasible lifecycle handles this gracefully (proposals persist regardless), but the informativeness of exclusion notes degrades with circle proliferation.

### 8.4 Confirmation threshold

The 70% recall threshold for confirming proposals is arbitrary. Too low produces false confirmations; too high misses near-matches (the dagger at 67%). Whether this threshold should be fixed, domain-adaptive, or itself discoverable is an open question.

---

## 9. What This Paper Does Not Claim

- We do not claim the trie reframe changes the mathematical properties of iterated lift. The recursion is the same; the trie is a computational optimization and a conceptual reframe.
- We do not claim the theorist produces novel scientific hypotheses. It performs matrix completion on observed structure — a mechanical operation whose output quality depends entirely on the input data.
- We do not claim defeasible rules are Bayesian inference. The system does not compute posteriors. Defeasibility here means "the system does not hard-block; evidence overrides."
- We do not claim the architecture replaces neural networks, knowledge graphs, or any existing system. It is a complement for regimes where features are symbolic, named, and discrete.

---

## 10. Summary

We extended iterated lift with three advances: convergence routing replaces O(n²) comparison with O(context × depth) trie traversal; a crystallizer watches routing failures and suggests candidates to lift without exhaustive comparison; and a theorist discovers negative dims and proposes structural gap entities as persistent, defeasible nodes. The streaming pipeline achieves 95% of brute-force recall while building incrementally. The theorist correctly predicts held-out entities from structure alone (hippo confirming "large prey mammal," velociraptor confirming "bird with teeth"). Every discovered rule is defeasible — a pattern the system has not yet seen broken. The architecture reduces to one primitive (compare), three operations (observe, deduce, induce), and a complete circle profile of positive dims, negative dims, and hypothetical occupants.

---

## References

Ganter, B., & Wille, R. (1999). *Formal Concept Analysis: Mathematical Foundations*. Springer.

Koestler, A. (1967). *The Ghost in the Machine*. Hutchinson.

Stumme, G., Taouil, R., Bastide, Y., Pasquier, N., & Lakhal, L. (2002). *Computing Iceberg Concept Lattices with Titanic*. Data & Knowledge Engineering, 42(2), 189–222.

Wille, R. (1982). *Restructuring Lattice Theory: An Approach Based on Hierarchies of Concepts*. In: Ordered Sets, Springer.

---

## Appendix A: Reproducibility

The experiments described in §4 are reproducible from the following scripts (provided alongside this document):

- `convergence_test.py` — convergence routing on held-out entities (§4.1)
- `pipeline_test.py` — streaming pipeline vs. brute-force comparison (§4.2)
- `l2_recursive_test.py` — L2 cleanup on pipeline circles (§4.3)
- `theorist_lifecycle_test.py` — full theorist lifecycle with confirmation and caution (§6)

All scripts use the same 20-entity synthetic ontology encoded as Python literals. No external dependencies beyond the Python standard library. Runtime under 2 seconds each.

The engine integration (§4.4) is reproducible from `sis_engine.py` (v35) with the modifications described in `sis_v35_integration.py` and `theorist_integration.py`.
