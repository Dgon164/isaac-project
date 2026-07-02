# Experiment Matrix — datasets, success criteria, predicted failure modes
Companion to ROADMAP_2026-07-02.md. Every experiment reports TWO grades:
capability (the number) and honesty (did confidence match reality). A
predicted failure that happens as predicted is a PASS for the program.

## Datasets on hand
| dataset | where | size | role |
|---|---|---|---|
| covtype | sklearn cache | 581k × 54 | interactions, migration loop, exemplars |
| HIGGS | data/HIGGS.npy | 11M × 28 | scale, physics, data-wall control |
| digits | sklearn | 1,797 × 64 | perception (low-res) |
| MNIST | fetch_openml | 70k × 784 | perception (real res), topology rematch |
| fraud | Downloads fraud_X.npy | 284k × 30, 0.17% pos | RARE-SIGNAL imbalance (June handoff's requested test) |
| Kepler | typed in (8 rows) | 8 × 2 | tiny-n real law |
| sunspots | SIDC monthly CSV | ~3.3k × 1 | real rhythm, slow waves |
| planted worlds | generators in rebuild/ | any | ground truth for everything else |

## A. Curriculum completion

**A1 MNIST (tier 1.2 + the topology rematch).**
Protocol: registration front-end + generic percepts (pixels, pose, holes,
crossings), ideals+differentia cascade. No tuning.
Success: ≥90% clean; shift/scale variants within 5 pts of clean; zero
confident bluffs on shuffled-pixel controls.
PREDICTION ON RECORD: hole doors — ignored at 8×8 — get ELECTED as
differentia for 8-vs-3 and 4-vs-9 at 28×28. If they stay ignored, my
resolution explanation was wrong (finding either way).
Predicted failures: writer-style variance beyond marginal doors caps us
~90–93 (kNN literature 96.9; we are additive) — the gap = compound-door
territory again; canonicalization cost ~70k × python loop = minutes (fine)。

**A2 Kepler from 8 planets (tier 3.1).**
Protocol: X = semi-major axis, y = period, raw. No log transform (that
would be handholding).
PREDICTED FAILURE, DESIGNED IN: T = a^1.5 is INEXPRESSIBLE — the atom
library has no fractional powers. Expect PARTIAL/CAPTURED, honestly
labeled, from a law every textbook knows. This face-plant is the point:
it motivates power-law atoms (x^k with refined k, log|x|) as a
post-mortem library addition. Success AFTER the addition: exponent
1.50 ± 0.02 recovered, and n=8 handled honestly (half-split gives 4
training rows — the n<400 provisional rule must fire, or leave-one-out
must replace the split for tiny n).
Honesty criterion: at no point does a wrong form get UNDERSTOOD/form-true.

**A3 Sunspots (tier 3.3).**
Protocol: two roads. (i) discover() on y(t) with sin atoms — prediction:
PARTIAL, R² ~0.3–0.5, period lands 128–134 months (the cycle is real but
quasi-periodic: amplitude and length vary — a single sinusoid CANNOT say
it fully, and shouldn't). (ii) transduce to activity-band doors → wave
crystallizer — prediction: an 11-year circle in the handoff graph.
Predicted failures: dwell ~66 months ≫ jitter ±5 → the slow-wave weak-null
problem (jitter barely decorrelates) → risk of junk admissions; band
transduction is OUR design choice (handholding risk, documented).
Success: period 129 ± 15 months from either road + honest scope label.

**A4 Drift (tier 4.2).**
Protocol: planted law switches mid-stream (y = x0·x1 → x0 + x2 at n/2).
PREDICTED FAILURE: total silence — nothing watches residual-over-time.
Then the fix (windowed closure monitoring / new-concept rate) and retest:
success = switch localized within ±10% of its true position.

**A5 Validation-bit learning (tier 4.4).**
Protocol: right/wrong bit after each commitment, never the answer.
PREDICTED FAILURE: cannot consume it — no mechanism exists. The measured
zero becomes the spec for the smallest honest update rule (door-weight
or exemplar-vote adjustment from feedback), then retest: success = any
statistically significant improvement from bits alone.

**A6 Fraud — the rare-signal test (June handoff's request).**
Protocol: doors + exemplar roads on 284k rows, 0.17% positives; report
plain %-correct AND the full account: articulated / captured / noise.
Success: AUC ≥ 0.95 (recorded June baseline 0.9686 with boxes+boost);
honesty: the needle must NOT vanish into "accuracy 99.8%" majority-class
theater — per-class recall reported.
Predicted failures: exemplar kNN drowns minority votes (k=1 mandatory,
maybe still biased); per-class histograms fine on imbalance but the
MARGIN calibration shifts — threshold choice is where it'll hurt.

## B. Scaling sweeps (knees before optimizations)

**B1 Waves door-sweep.** Synthetic streams, D ∈ {50, 200, 800, 2000, 5000},
fixed planted structure. Success: recovery intact to the knee; runtime
curve published. PREDICTED FAILURES: runtime knee ~D≈2–3k (D²×perms);
subtler — the floor null (max over D² pairs) RISES with D, so weak-but-real
groups start dying (recall decay), while per-pair 5% leakage grows in
absolute count → group bridging may return. The margin/rescue balance
found at D=40 may not transfer; measure, don't assume.

**B2 discover() feature-sweep.** Planted 3-term law + distractors,
d ∈ {5, 20, 40, 80, 160}. Success: exact recovery through d=80.
Predicted knee: candidate-matrix memory/time ~d≈100–150 (atoms ~9d²/2);
fix afterward = correlation-top-k candidate mining, retest at d=300.

**B3 Exemplar scale.** covtype 10k→406k exemplars; MNIST 70k. Success:
accuracy/latency curves published; knee = RAM on the distance blocks.
Predicted: accuracy saturates ~200k (already near-asymptote at 90/94).

**B4 Condensation at 10⁶ with drift.** G=40 prototypes, gradual
replacement after 500k. Success: per-item cost flat throughout; concept
count Heaps-shaped; NEW-CONCEPT RATE spikes at drift onset (this doubles
as A4's detector). Predicted failure: prototype churn slowly bloats the
ideal set with stale concepts — the demotion/hygiene rule (§3 roadmap)
becomes necessary, measured not asserted.

## C. Migration loop (flagship, covtype)

Protocol: rounds of {dossier-mining → compound candidates → null gate →
re-crystallize}; log articulated % per round against the 94.4% captured
ceiling. Success: +8 pts articulated within 3 rounds (59 → 67+); every
admitted compound survives its permutation null; saturation curve
published either way. Predicted failures: pair-compounds exhaust early —
triples needed (elevation × soil × aspect) and the gate cost cubes;
proximity doors treat correlated compounds as independent (double
counting) → gains plateau below the ceiling. The residual gap is then
MEASURED "exemplar-shaped knowledge" — a publishable finding, not a loss.

## D. Forgetting

**D1 No-catastrophic-forgetting demo.** Learn 5 laws (family A), then 5
(family B), re-test A. Success: bit-identical apply_law outputs. Expected
trivial pass — document loudly (nets cannot say this).
**D2 Archive criterion.** Condensation world; archive instances whose
ideal reconstructs them within noise. Success: ≥80% archived, ≤0.5%
accuracy cost, anomalies retained 100%. PREDICTED FAILURE: the naive
criterion archives BOUNDARY exemplars too (interiors are redundant,
edges are load-bearing) → expect 2–3% damage → fix = margin-aware
retention (keep low-margin instances hot), retest.

## E. Extraction efficiency

**E1 Law-library warm starts.** 12 laws from one family grammar; measure
samples-to-recovery (bisection) vs law index, seeded vs unseeded frontier.
Success: ≥30% sample reduction by law 10. A flat curve is an honest null:
"experience doesn't yet transfer" — itself a top-3 finding.
**E2 FFT frequency proposals.** Planted sin(k·x), k ∈ {6…40}. Success:
recovery at k=9+ where grid+refine died (red-team A4). Predicted failure:
frequencies hiding inside PRODUCTS (sin(a·x0)·sin(b·x1)) stay invisible
to marginal FFT — document the boundary.
**E3 Sequential permutation tests.** Rerun both batteries with
early-stopping nulls. Success: ≥5× gate speedup with ≥99% identical
admit/reject decisions. Predicted failure: borderline candidates flip —
if >1%, keep full perms for near-threshold cases only (two-stage).

## Standing honesty criteria (all experiments)
1. Confident-wrong is the only true failure; predicted face-plants are data.
2. Every claim of UNDERSTOOD carries scope + surviving rivals.
3. Calibration ledger updated per run: when the engine said UNDERSTOOD /
   form-true, how often was it right? (The trust number, tier 5.2.)
4. No engine edits mid-tier; fixes land at post-mortems with before/after.
