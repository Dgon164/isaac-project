# ISAAC — Capability Audit Standard v1.0

**Adopted:** 2026-07-01

**Purpose:** The definitive objectives document for auditing ISAAC's capabilities. Each capability gets: (a) what perfectly functional looks like, (b) the load-bearing property that makes it work, (c) the test it must pass. Verdicts are strict: WORKS / BROKEN / NEVER BUILT. No partial credit.

**Method:** For each item, demand three things — the code path that implements it, a minimal test with known ground truth, and an explicit verdict. Audit in dependency order (Section 4), not numerical order.

---

## 1. Theory Spine (context for the auditor)

Two primitives, no third:

1. **Differentiation** makes the parts.
2. **Memory recursion (holarchy)** composes the wholes.

Representational substrate: **doors** (properties/affordance declarations) and **relationships in the matrix**. Everything else is these composing.

Core theoretical commitments established in design review:

- The system is **leveled and relational, not flat**. The atom needs depth (decomposition to find comparability), doors need dimension (ranges, not bits), wholes need altitude (new capabilities at new levels).
- **Emergence = affordances.** A whole is emergent when it offers a true functional capability — an ability, opportunity, or potential — that is inoperable by any individual part and by any unstructured aggregate of the parts. (Piston ≠ engine; engine ≠ car; car ≠ vacation.) Affordances are relational: X affords F to Y. Emergence occurs when affordances **interlock** — one part's output is the enabling condition of another's uptake. Configuration = the pattern of which affordances consume which. In implementation this is doors and relationships in the matrix — no new machinery.
- **Universal null discipline:** every claim must beat its own null (permuted-output where applicable). This single principle gatekeeps: concepts, compounds, keypoints, and mini-net captures.

---

## 2. Capability Objectives

### 2.1 Differentiation Atom

**Perfect:** Every pair of inputs receives the correct verdict from a three-valued output space: SAME / DIVERGENT / ABSENT. "Absent" (noncomparable as-sits) is information, not failure. Deterministic and stable: same inputs → same output, always.

**Load-bearing properties:**

- The ABSENT verdict is honest in both directions: never forces a comparison that isn't there (no false SAME/DIVERGENT on noncomparables like worms-vs-watts), and never lazily declares ABSENT when decomposition through the matrix would find the level where the two do meet (shared dimensions: mass, energy throughput, etc.).
- Decomposition is principled: descends only as deep as needed, knows when to stop. "Everything is comparable if ground to atoms" is true and useless — comparison cost must be weighed against comparison value.

**Test:** Curated pairs with known relationships at known depths — surface-comparable, comparable-after-one-decomposition, comparable-only-at-bedrock, genuinely never-comparable. Atom must sort all correctly and report the depth it needed.

### 2.2 Doors (incl. dims / box-ranges)

**Perfect:** Doors give the crystallizer computable, graded overlap between any two entities — strongly connected / remotely connected / not connected are distinguishable. A thing is defined by what it is: its door profile is its identity. Doors carry dimension and range ("temperature ∈ [40,60]"), making overlap a geometric question (box intersection, and by how much), not binary set membership.

**Load-bearing properties:**

- **Representation invariance:** re-encoding the same data must not change the door profile. If it does, doors describe the encoding, not the world. This is the deepest untested assumption in the stack.
- Door richness bounds the resolution of everything downstream. Binary doors → coarse Venn regions, unstable crystals — regardless of crystallizer quality.
- Doors double as affordance declarations ("offers value in range R on dimension D") — this is what ties atom, doors, and holarchy into one concept.

**Test:** (a) Same data, two encodings → identical door profiles. (b) Entities with known graded similarity → overlap scores rank correctly. (c) Ranged doors: known-overlapping boxes intersect with correct magnitude.

**Status note:** dims/box-range experiments exist (new work, not yet reviewed). They likely constitute both the door enrichment AND the FCA conceptual-scaling scheme AND most of the transducer (2.12). Review these first in the audit.

### 2.3 Memory Recursion / Holarchy

**Perfect:** Composition encodes **configuration, not membership**. A whole is validated as emergent by an operable function (affordance) that fails in every individual part and in the unstructured aggregate of the same parts. Wholes are first-class: they enter the atom, hold doors, compose upward. Supports both structural composition (piston→engine) and participatory composition (car→vacation) — unified as affordance-matching via doors + matrix relationships.

**Load-bearing properties:**

- Two different arrangements of the same parts must be distinguishable in the representation. A bag-of-part-IDs holarchy cannot produce emergence, by construction.
- Formation is deterministic: same parts + same arrangement → same whole, every run. Emergent ≠ arbitrary.
- Decomposition recovers the parts (identity of parts survives; behavior of whole need not equal sum of parts — that's the point).
- A part's latent affordances (offered, currently unconsumed — piston in a drawer) are representable; this latent inventory is what feeds crystallizer connectivity.

**Test:** Compose a whole with a known emergent function. Verify: (a) function operable at whole level; (b) inoperable in every part; (c) inoperable in shuffled/dismantled aggregate of the same parts (the dismantled-engine control); (d) same structure assembled in different orders yields the same whole.

**AUDIT PRIORITY QUESTION:** Does current composition code store uptake/arrangement (who consumes what from whom) or membership only? Membership-only is the leading suspect for "structures assemble fine but never behave differently than their parts, across every experiment."

### 2.4 Crystallizer (FCA target)

**Perfect:** Produces the **concept lattice** of the door context (Formal Concept Analysis or near equivalent): every concept = (all entities sharing a door set, all doors shared by that entity set); concepts order into a hierarchy by containment. This IS the Venn/object-oriented structure, made rigorous. Entities legitimately live in every concept whose intent they satisfy — no forced single-bucket assignment. The crystallizer is what makes the system able to do anything at all.

**Free by construction (FCA theorems, verify anyway):**

- Order-invariance: lattice fully determined by the context; shuffle test passes automatically.
- Multi-resolution: dense cores (many doors, few entities) and loose super-groups (few doors, many entities) are different depths of one structure.
- No duplicate-label collisions (concepts defined by intents).

**Known costs / required components:**

- Conceptual scaling for ranged/dims doors (native FCA is binary). The dims/box-range design IS the scaling scheme; its design determines lattice resolution.
- Combinatorial explosion on dense contexts (the existing O(n²) concern, formalized). Mitigations: stability/support pruning (= permuted-null discipline applied to concepts) and iceberg lattices (compute only well-supported top).

**Test:** (a) Known small context → hand-verifiable lattice. (b) Shuffle input order → identical lattice. (c) Planted overlap structure → recovered as concepts. (d) Stability pruning kills concepts that die under perturbation.

**Dependency:** CANNOT be audited before doors (2.2). A crystallizer fed binary doors produces coarse unstable circles no matter how correct its own logic.

### 2.5 Null Detection

**Perfect:** When there is no rule, says "no rule" with confidence; never says "no rule" when one exists at detectable strength. **Level-indexed:** distinguishes "null at surface, untested at depth" from "null everywhere." Some groups are null at part level and lawful at whole level — the rule lives in configuration. Conflating these throws away exactly the signal emergence lives in.

**Load-bearing property:** Calibrated null model — knows what chance looks like for this data size and structure; not a fixed R² cutoff.

**Test:** (a) Pure noise → NULL. (b) Weak-but-real signal → NOT null. (c) Part-level-null / whole-level-lawful construction → verdict states the level.

### 2.6 Function / Equation Recovery

**Perfect:** Given samples, recovers the **generating equation** — not a fit agreeing at sample points. States when samples are insufficient to disambiguate and asks for the discriminating sample.

**Load-bearing property:** Identifiability awareness — knows which candidate functions are still tied (the pos-3 trap: linear vs. quadratic agreeing at one point) and what input unties them.

**Test:** Underdetermined sample set → system names the tied candidates and requests the specific discriminating input, rather than committing.

**Extended role:** distillation attack on mini-nets (see 2.8) — recovering the equation a trained capture-net learned, graduating captures to articulated law.

### 2.7 Keypoint Detection

**Perfect:** Channels ranked by **causal upstream contribution** to the output. Every decoy ranks at chance. Every downstream consequence / passive correlate (fuel-rides-with-racer: exhaust, not driver) is demoted below every true driver.

**Load-bearing property:** Conditional relevance — drop-one-channel damage ("does removing this hurt prediction"), not group separation. Fisher-ratio separation is structurally incapable of distinguishing drivers from bystanders and MUST NOT be the ranking statistic.

**Test:** Planted decoys and planted passive correlates. Decoys rank at chance; correlates rank below all true drivers. (The timing and fuel failures are the regression test.)

### 2.8 Completeness Scoring (three-valued, level-indexed)

**Perfect:** For each level of decomposition/composition:

    articulated law % + captured-but-unarticulated % + proven noise % = 100

- **Articulated:** lattice + explicit law.
- **Captured:** a mini-net trained to specialize in the relationship holds it as a stopgap. The unexplained portion becomes hints + a named x-variable unknown — a first-class tracked object with a dossier (responsive channels, strength/weakness regions, net-sensitivity shape). The dark-matter move: can't say what it is; can characterize how it behaves; track until resolved.
- **Proven noise:** demonstrated irreducibility — no model in the system's expressive class reduces it. Never leftover residual relabeled.

**Non-negotiable discipline:** a mini-net's capture counts ONLY if the net beats its own permuted-output null. Otherwise a big-enough net memorizes noise and the middle category becomes a lie.

**Closing loop:** function recovery (2.6) later attacks the trained mini-net; on success, capture graduates to articulated law and x is retired. (This is the project's original neural-net-extraction method, redeployed internally.)

**Level rule:** residual at level N is handed upward as raw material for level N+1 — part-level noise may be whole-level law.

**Test:** (a) Synthetic data with known law + known noise fractions → score matches ground truth. (b) Plant a learnable-but-hard relationship → lands in "captured" with a mini-net that beats its null. (c) Pure-noise residual → mini-net fails its null → correctly lands in "proven noise."

### 2.9 Shadow Census

**Perfect:** Outputs "what these inputs cannot tell you, and the data you'd need" — and is **right**: when the named missing data is supplied, performance improves as predicted. Two kinds of shadow, operationalized: unmeasured variables = missing doors; structural invisibilities (e.g., time in covtype) = missing levels/relationships in the matrix.

**Test:** Predictive — withhold a known variable, run census, verify the census names it (or its shadow-shape), restore it, verify the predicted improvement materializes.

### 2.10 Permuted-Null Stability (infrastructure)

**Perfect:** Any claim whose real-data stability doesn't beat its shuffled-output stability is dropped. Kills the "89%-consistent decoy" that sneaks past resampling — small consistent biases collapse to chance under the right null (permuted output, same channel, same data).

**Role:** BUILT ONCE, AS INFRASTRUCTURE. Gatekeeps: concepts (2.4 pruning), compounds (2.11), keypoints (2.7), mini-net captures (2.8), null detection calibration (2.5).

**Test:** The timing decoy (89% sign-consistent) must die under permuted-output null while a true weak driver survives.

### 2.11 Classification — flat and compound (merged; one capability, two levels)

**Perfect:**

- **Flat:** on single-feature-separable problems, matches standard baselines with zero feature engineering (fraud AUC 0.9686 class of results).
- **Compound:** expresses "V4 high AND V12 low" as a first-class **compound door** — a small whole whose parts are doors — discovered from data, composable (compounds of compounds).
- **Declares its own ceiling:** hitting the flat expressiveness limit (e.g., boosting finding the same split 9×) automatically triggers compound search. The ceiling is the signal to attempt composition — the theory operating, not a patch.

**Load-bearing property:** Compound admission discipline — a compound is formed only when its predictive power exceeds its best part by a margin that survives the permuted null (2.10 as gatekeeper). Without this, compound search drowns in spurious conjunctions (combinatorial space).

**Test:** (a) Flat problem → baseline parity. (b) XOR-style / interaction-only problem → flat path declares ceiling → compound search fires → correct compound found → beats parts → passes null. (c) No-interaction data → compound search forms nothing.

### 2.12 Transducer (continuous → discrete)

**Perfect:** Continuous input becomes ranged doors such that meaningfully-different values get different doors, meaningfully-same values share doors. Boundaries placed **where the output changes**, learned from the data's structure — never hand-set equal-interval bins. Hysteresis or soft membership near edges (nearly-identical values straddling a boundary is THE failure mode).

**Status:** likely not a separate layer — probably IS the dims/box-range door design done right. Confirm during doors audit.

**Test:** (a) Values just inside/outside a learned boundary with identical outputs → same door (soft membership works). (b) Output-change points → boundaries land there, not at interval marks.

### 2.13 Scaling Behavior (project capability, not system capability)

**Perfect:** For every capability above, a measured curve — quality vs. data volume — with known shape: onset, saturation, degradation. Logging built into every run, recorded as it happens, never recalled afterward.

**Why non-negotiable:** without curves, "poor progress" is unmeasurable — a dead end and an underfed structure are indistinguishable. Crystallization has NO published scaling literature; nobody knows this architecture's behavior at 10 min vs 10 hr vs 10 days. The curve must be measured because it cannot be looked up.

---

## 3. The Four Epistemic Verdicts (system-level goal)

A finished ISAAC can say four different things about any pattern, each backed by a demonstration:

1. **"I understand it"** — lattice + articulated law (2.4, 2.6)
2. **"I've caught it but can't say it yet"** — mini-net + x + hints dossier (2.8)
3. **"I've proven it's nothing"** — null / proven noise, beat-the-null discipline (2.5, 2.10)
4. **"I can't see it from here — here's what's missing"** — shadow census (2.9)

---

## 4. Audit Order (dependency order — mandatory)

1. **Doors + dims/box-ranges** (2.2, absorbing 2.12) — everything downstream is bounded by their resolution. First question: representation invariance. Second: graded overlap correctness. Third: is the box-range design a valid FCA conceptual scaling?
2. **Atom** (2.1) — three-verdict behavior tested against the real doors.
3. **Permuted-null infrastructure** (2.10) — built once before anything that needs gatekeeping.
4. **Crystallizer / FCA lattice** (2.4) — on top of audited doors.
5. **Null detection** (2.5) — calibrated against the infrastructure.
6. **Holarchy / composition** (2.3) — PRIORITY QUESTION: uptake edges vs. membership-only storage.
7. **Classification flat → compound** (2.11) — ceiling-detection trigger wired to compound search.
8. **Keypoints** (2.7) — drop-one relevance, decoy/correlate regression tests.
9. **Completeness + mini-net captures** (2.8) — three-valued accounting.
10. **Function recovery** (2.6) — including distillation attack on captures.
11. **Shadow census** (2.9).
12. **Scaling curves** (2.13) — instrumented into every step above from the start, reviewed last.

---

## 5. Known Open Suspects (carry into the audit)

- **Membership-only composition** — leading suspect for system-wide "assembles but never behaves differently" symptom (2.3).
- **Representation-variance of doors** — deepest untested assumption; could alone explain diffuse mediocre results everywhere (2.2).
- **Fisher-style separation still in any ranking path** — structurally wrong statistic (2.7).
- **Duplicate-label bug in cluster→label join** (dies automatically under FCA, verify).
- **Compound doors specified but never built** (2.11).
- **O(n²) crystallizer scaling** — mitigate via stability pruning / iceberg lattice (2.4).
- **89%-consistent decoy passing resampling** — permuted-output null required (2.10).

---

## 6. Verdict Sheet (fill during audit)

| # | Capability | Code path | Test written | Verdict | Evidence (the number) |
|---|------------|-----------|--------------|---------|----------------------|
| 2.2 | Doors / dims / ranges | | | | |
| 2.1 | Atom (3-verdict) | | | | |
| 2.10 | Permuted-null infra | | | | |
| 2.4 | Crystallizer / FCA | | | | |
| 2.5 | Null detection | | | | |
| 2.3 | Holarchy / composition | | | | |
| 2.11 | Classification flat+compound | | | | |
| 2.7 | Keypoints | | | | |
| 2.8 | Completeness / captures | | | | |
| 2.6 | Function recovery | | | | |
| 2.9 | Shadow census | | | | |
| 2.13 | Scaling curves | | | | |

Verdicts: **WORKS / BROKEN / NEVER BUILT.** No partial credit. No "seems fine."
