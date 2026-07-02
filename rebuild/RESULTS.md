# Rebuild Results — 2026-07-01

Three subsystems reported broken; each rebuilt as a minimal clean mechanism and
run head-to-head against a faithful implementation of the broken mechanism, on
planted ground truth, per `audit/AUDIT_STANDARD_v1.md`. Verdicts strict.

Integrity rule honored throughout: numpy only, the mechanism under test makes
every decision. All scripts in this folder are self-contained and rerunnable.

## The diagnosis (one line each)

| Thread | Broken load-bearing property | Evidence |
|---|---|---|
| SIS / Isaac structure | Composition stores **membership only** (no uptake edges); doors are **binary** | `code/isaac.py` `_crystallize()` stores `{"members"}`; audit 2.3 suspect confirmed |
| Net extractor | **Hard box membership** on a fixed axis basis: geometry ceiling + encoding-dependence | covtype boxes ~0.62 vs net 0.82 (no knob closes it); box→matmul finding (0.900 vs 0.922) |
| Enumerator (Stage-2 terms) | Polynomial-only basis + flat enumeration + **no null gate** | m_jj R² 0.075; §11.1 basis disconnect; d^k blowup |

Note: first two are the same disease — hard binary membership where graded,
basis-aware comparison is needed.

## Rebuild A — proximity doors (`doors_proximity.py`) — **WORKS 4/4**

Doors = observed per-class per-dim distributions (quantile histograms), scored
by summed log-likelihood in ONE matmul, formed **basis-first**: rotate to the
correlation eigenbasis, but only along correlations that beat the sampling
null (~3/√n) — *the basis itself must beat chance* (this null-gated rotation
was added after plain PCA smeared structure on correlation-free data).

| Test | Box (old) | Proximity (new) |
|---|---|---|
| T1 box-friendly blobs | 100.0% correct | 100.0% correct (parity — nothing lost) |
| T2 diagonal (box-hostile) | 88.0% | **99.0%** (the ceiling, broken) |
| T3 graded overlap strong/remote/none | 0.432 / 0.055 / **0.000** (hard zero — no gradations of "far") | 0.380 / 0.069 / 0.029 (remote ≈ true density overlap 0.08) |
| T4 re-encoding invariance (units/offset/column order) | **82.2%** of verdicts survive — 17.8% flip | **100.0%** invariant |

T4 is the headline: the box doors describe the encoding, not the world —
the audit standard's "deepest untested assumption," now measured.

## Rebuild B — uptake-edge composition (`composition_uptake.py`) — **WORKS 7/7**

Whole = parts + uptake edges (provider —affordance→ consumer). Operability =
fixed-point propagation through the edges. Emergence = interlocking affordances.

- (a) engine whole affords torque ✓ (b) torque inoperable in every part ✓
- (c) dismantled pile lacks torque ✓ — and the OLD membership representation
  gives the working engine and the dismantled pile **the same identity object**
- (d) rewired same-parts whole: different identity, torque lost ✓ — OLD: identical
- (e) 12 assembly orders → 1 identity (deterministic formation) ✓
- (f) decomposition recovers the parts ✓
- (g) first-class wholes: engine + wheels + frame → car affords locomotion ✓

This is the mechanical explanation for the system-wide symptom "structures
assemble fine but never behave differently than their parts."

## Rebuild C — staged null-gated enumerator (`enumerator_staged.py`) — **WORKS 4/4**

Fixes all three documented failures at once: transcendental atoms in the basis
(cos/sin/cosh of pairwise differences), beam growth around admitted terms (no
d^k enumeration), and permuted-null admission with a max-over-candidates null
(selection-effect decoys die). Plus dual-track (linear/log) missing-variable
recovery per §11.2.

| Test | Old (poly L1, faithful) | New (staged) |
|---|---|---|
| (a) planted pt1·pt2·(cosh(e1−e2)−cos(f1−f2)) | R² 0.609, 16 terms — the wall | **R² 1.000, exact form, coefs +1.00/−1.00** |
| (b) planted x0·x1 + x2² − x3 | — | exactly the 3 terms, no junk, R² 1.000 |
| (c) pure noise | keeps 26 junk terms (held-out R² −0.013) | **"NO RULE" — admits 0 terms** |
| (d) hidden variable, additive / multiplicative | — | right track chosen both times, corr 0.999 / 1.000 |

## Honest caveats (do not oversell)

1. All ground truth here is **planted/synthetic** — by design (audit standard),
   but the originals' failures were measured on real data. Next step is the
   real-data head-to-head: proximity doors on covtype (target: beat the 0.62
   box ceiling toward the net's 0.82) and the staged enumerator on real HIGGS
   m_jj — which may STILL fail there, because the real m_jj wall is partly
   missing jet 4-vectors (data absent, not basis wrong). The rebuild fixes
   basis + admission discipline; it cannot conjure unrecorded variables.
2. Rebuild B is a clean mechanism demonstration, not yet wired into
   `code/isaac.py`. Integration = crystallizer stores uptake edges alongside
   members, recognition consumes them.
3. OLD-mechanism numbers here are from faithful reimplementations (documented
   algorithms), not imports of the original scripts (those are dataset-bound).

## Rebuild D — wave crystallizer (`wave_crystallizer.py`) — **WORKS 5/5**

The user's spec: simultaneous activation as a first-class thing; whole-matrix
movement compared prior-frame to later-frame; higher-order patterns that
create circles. One mechanism, applied recursively:

1. SIMULTANEITY — co-activation groups, gated by an independence floor AND a
   per-pair **jitter null** (±2–5 step shifts: keeps each door's own rhythm,
   breaks precise co-timing — a full circular shift is the WRONG null for
   periodic waves, it relands in phase and makes simultaneity undiscoverable).
2. MOVEMENT — handoff edges: group g off at the same instant group h on
   (prior-matrix vs later-matrix registration), same jitter null, jittering
   the ON side only (jittering both sides sometimes preserves relative timing).
3. CIRCLES — closed paths in the surviving handoff graph.
4. RECURSION — each circle's activity becomes a door in a level-2 stream;
   the same stages rerun → patterns of patterns.

Planted: 2 concurrent processes (periods 9 and 10, independent phases) waving
across 5 door-groups among 15 noise doors, with an era rotation
A(P1)→B(P2)→C(both) on top. Results:
- T1 exactly the 5 planted groups, zero noise doors admitted
- T2 exactly the 5 planted handoffs
- T3 exactly the two planted circles (period 3, period 2)
- T4 shuffled-time control: groups survive (co-occurrence is timeless),
  **every handoff and circle dies** — this is precisely the part the static
  crystallizer cannot see, made visible
- T5 the era rotation recovered as a **circle of circles** at level 2
  ((0,1)→(1,1)→(1,0)) by the same machinery, one level up

Two development notes worth keeping (both times the "bug" was the planted
data, not the mechanism): fixed-length eras clock-locked the era boundary to
P1's phase and the crystallizer correctly reported the boundary co-timing as
a real edge; and two processes driven by one global clock ARE phase-locked
(constant relative phase), so their lcm-coincidences are real structure.
Truly independent waves need independent phases. The mechanism found every
regularity the generator actually contained, including two I didn't intend.

## Rebuild E — interference / present-but-blocked (`wave_interference.py`) — **WORKS 5/5**

The user's spec: object permanence but more — the sun behind a cloud keeps
most of its indicators; the blocked bright point should be EXPLAINED, not
just missing. Three capabilities:

- **Permanence** (free from majority vote, verified): sun group holds its
  disk-door at 40% occlusion — and, surprisingly, still at **93%** blocking.
  Exile basically does not occur with a single blocker; membership is
  occlusion-robust. (`conditional_rescue` built as belt-and-suspenders for
  exile regimes; never triggered, zero false adoptions.)
- **Masking as a first-class discovery:** exactly `cloud blocks sun.disk`
  (dark 0.86 with cloud vs 0.10 without; at 93% coverage 0.95 vs 0.22),
  nothing else — no false masks on wind, other sun doors, or noise.
- **Three-state readout:** PRESENT / PRESENT-BUT-BLOCKED(door ← blocker) /
  ABSENT at **97.1% per-tick accuracy**. Absence-by-night ≠ absence-by-cloud.

Two methodological findings worth keeping:
1. **Masking is a simultaneity-class claim** — it survives whole-stream time
   shuffling (rows intact), so the right control is shuffling the BLOCKER'S
   timeline (groups survive, masks must die — and do, 0 edges).
2. **A raw-count gate cannot certify a high-coverage blocker** (a shifted
   92%-on blocker still overlaps ~92% of suppressions; max ratio 1.09 < any
   sane margin). The claim is the CONDITIONAL RATE GAP —
   P(dark | present, blocker) − P(dark | present, no blocker) — tested
   against the shifted-blocker null of the same gap. Same lesson as the
   jitter null: the null must attack exactly the claimed structure.

## Rebuild F — entity identity + temporary statuses (`entity_status.py`) — **WORKS 5/5**

The general version of Rebuild E, per the user's correction ("that feels very
hand crafted... it knows the time of day and says the sun should be here").
No masking detector. Instead:

1. identity + rhythm from the existing machinery (groups, circles)
2. a CLOCK: a tracker walks the discovered day/night circle — evidence
   advances it, learned dwell dead-reckons when evidence is hidden.
   Phase correct 99.3% overall, **99.2% during occlusion** — it knows it's
   day even with the disk hidden.
3. EXPECTATION → REGISTRATION: the phase says which doors should be lit;
   persistent expected-but-dark opens a temporary STATUS (miss:disk),
   92.8%/tick vs truth. At night nothing is expected of the sun, so
   absence-by-night opens ~no status (0.11%, dusk-boundary lag only) —
   the night/cloud distinction FALLS OUT of the clock, no special rule.
4. **STATUSES ARE DOORS.** Fed back into the stream and crystallized by the
   ORDINARY co-activation machinery within the entity's own timeframe, the
   explanation EMERGES as a plain group: (cloud_a, cloud_b, miss:disk).
   Zero masking-specific code. Expectation errors are raw material for the
   next pass — the level rule, operating.
5. Expectation cashes out as prediction: cloud lifts in daytime 95 times,
   disk back within 3 ticks 97.9%.

Supersedes Rebuild E's bespoke detector in architecture (E's conditional
rate-gap null remains the right STATISTIC when a status needs certifying
against a high-coverage blocker).

## Real-data head-to-heads (2026-07-01, same day — full datasets)

### Covtype, all 581,012 rows (`covtype_real_test.py`)

| Mechanism | % correct |
|---|---|
| BoxDoors (old, faithful) | 49.31% |
| ProximityDoors (rebuild, 32 bins) | **56.15%** |
| recorded box-forest ceiling / net | ~62% / 82% |

Proximity doors beat the box mechanism they replace, but covtype's remaining
signal is interaction-heavy — marginal doors hit their DECLARED expressiveness
ceiling. Per audit 2.11 the ceiling is the trigger for compound-door search
(the designed next rung, not built today). A class-conditional-basis variant
was attempted and is **BROKEN** (cross-class density calibration; two bugs
fixed — point-mass density spikes, missing out-of-support penalty — still
miscalibrated at ~20%; kept in the script as a marked failure).

### Covtype revisited — NET PARITY (`covtype_compounds.py`, 2026-07-02)

| road | % correct |
|---|---|
| marginal doors (articulated) | 56.2% |
| + 25 compound doors, one round (audit 2.11: ceiling→trigger→null-gated admission; mined only on confusion pairs) | 59.0% |
| exemplar recognition (captured; presence-not-average, 5-NN over 200k experiences, 26 s, no training) | **90.0%** |
| recorded net | 82% |

**Update (door-weighted metric):** weighting the exemplar distance by each
door's class-overlap (the differentia statistic — learned, readable:
elevation 0.76 dominates, then wilderness/road/fire) + all 406k exemplars +
k=1: **94.42%**. Literature context: original 1999 net 70.6%; the June "net
0.82" was our own baseline MLP, not the record; tree-ensemble record ~96–98.
Also measured: the ROW INDEX alone (hidden spatial coordinate) scores
**79.1%** with zero terrain — the June "spatial-leakage-dominated" diagnosis,
quantified; every covtype benchmark partly reads the map, not the terrain.

**The net is beaten — by the CAPTURED tier.** The completeness frame:
the net's 82% sits between our articulated floor (59%) and captured ceiling
(90%). The 31-point gap between our own tiers is the measured inventory of
caught-but-not-yet-said structure (local terrain geometry). The research
program is the migration: every compound-door round moves points from
captured to articulated. Notably pair 3-6 admitted ZERO compounds — the
null gate declining junk. One round, 4 pairs, top-8 features only; the
compound road is not exhausted, just begun.

### HIGGS, full 11,000,000 rows (`higgs_real_test.py`)

**Doors as classifier** (28 features, train 10.5M, test = last 500k, 22 s):

| Mechanism | % correct | AUC |
|---|---|---|
| box (recorded) | 52.5% | — |
| logistic (recorded) | 64.2% | — |
| his-matmul best (recorded) | 65.0% | — |
| **ProximityDoors (rebuild)** | **64.6%** | **0.700** |
| MLP (recorded) | 69.1% | — |
| additive-model ceiling (recorded) | — | 0.765 |
| full detector / Baldi ceiling (recorded) | 79.6% | 0.881 |

Beats logistic, matches the best previous "his-way" number, fully explainable,
22 seconds for 10.5M rows. Saturated in bins (32/64/128 → 64.6/64.7/64.7%):
the limit is the additive structure, not resolution — the remaining gap to
0.765/0.881 is interactions + joint structure, again compound-door territory.

**The real m_jj wall** (fit 100k, held-out 500k):

- OLD poly-L1: R² 0.050 (reproduces the recorded 0.075 wall)
- NEW staged enumerator: R² 0.033 — also fails, AND exhibits the pos-3 trap:
  admitted `-0.70*cos(1.00*Δη)` where truth wants `+cosh` — indistinguishable
  in the bulk (same quadratic), separable only in the tails. Audit 2.6's
  identifiability warning, observed in the wild.
- **Decisive diagnostic:** fitting the TRUE form
  `A·pt_a·pt_b·cosh(k_e·Δη) + B·pt_a·pt_b·cos(k_f·Δφ) + C` with scanned
  scale constants, for ALL SIX jet pairings, caps at **R² 0.065** (best:
  jets 1,2). The relation is not present in the recorded columns.
  **Verdict upgraded from "enumerator broken" to epistemic verdict #4:
  "can't see it from here — missing: jet masses / full 4-vectors and
  per-event pair assignment."** The wall is a data wall, proven, not a
  method wall. (The method's form-recovery stands on the planted test.)

## Verdict sheet

| Rebuild | Old mechanism | New mechanism | Verdict |
|---|---|---|---|
| A doors | boxes: ceiling + encoding-dependent | observe + null-gated basis + matmul | **WORKS** |
| B composition | membership-only: arrangement-blind by construction | uptake edges + fixed-point operability | **WORKS** |
| C enumerator | poly L1: wrong basis, no gate, junk on noise | staged + transcendental atoms + null gate | **WORKS** |
| D wave crystallizer | static crystallizer: order-blind by construction | simultaneity + handoffs + circles, recursive, jitter-null gated | **WORKS** |
| E interference | absence unexplained; blocked ≡ gone | masking edges + rate-gap null + 3-state readout (present/blocked/absent) | **WORKS** |
| F entity statuses | bespoke masking detector (E) | clock + expectation + statuses-as-doors; explanation emerges from ordinary co-activation | **WORKS** |
