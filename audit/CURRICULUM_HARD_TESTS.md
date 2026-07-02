# The Hard Curriculum — no handholding, no answer sheets
**Purpose:** watch it fall on its face, in public, with numbers. Designed to
probe the suspected walls: fuzzy perception, true generalization (transfer &
composition), real messy data, and epistemic honesty under adversity.

## Ground rules

1. **No handholding.** Raw inputs only. No feature engineering, no per-task
   tuning, one fixed engine configuration for the whole curriculum.
2. **No answer sheets.** Training examples carry labels (that is experience,
   not cheating). But: no test answers, no oracle hints mid-task, no
   "here's the form to look for."
3. **Validation ≠ answer.** Where feedback is allowed, it is a single
   right/wrong bit AFTER the engine commits — never the correct answer
   itself. (Note: the engine currently has NO mechanism that consumes such
   a bit. That is a known faceplant this curriculum is designed to surface,
   and the motivation for the next build.)
4. **Falling honestly is passing.** Every task gets two grades:
   - **capability** — plain % correct / R²;
   - **honesty** — did its confidence match reality? A shrug/NO RULE on an
     impossible task = pass. A confident wrong claim = the only true fail.
5. Every run logged as it happens (CSV), per the scaling discipline.

---

## Tier 1 — Fuzzy perception (the historical wall)

The engine's recorded history: recognition was exact-bitmap; scale transfer
0%; the perception front-end "blocks every time." Do the new doors change
any of that?

| # | Task | Setup | Expected faceplant |
|---|---|---|---|
| 1.1 | Digits baseline | sklearn digits (8×8, 1797), raw 64 pixels, 70/30 split | should be fine (~95%+); box-era recorded ~97.7 |
| 1.2 | MNIST raw | 28×28, 70k, raw 784 pixels, standard split | volume + fuzz; anything ≥90% honest is news |
| 1.3 | Translation | train centered, test shifted ±1, ±2 px | doors are positional — expect collapse; measure the curve |
| 1.4 | Scale | test 2× nearest-neighbor upscaled crops | recorded 0% in the old engine — retest |
| 1.5 | Occlusion | mask one quadrant at test | does majority-vote permanence help? does it CONFESS uncertainty or misclassify confidently? |
| 1.6 | Noise curve | salt & pepper 5–40% | graceful or cliff? |

## Tier 2 — Does it generalize TRULY (transfer & composition)

The GOFAI question. Search-over-library can fit; only transfer shows learning.

| # | Task | Setup | What it really tests |
|---|---|---|---|
| 2.1 | Range transfer | learn y=f(x) on x∈[0,2]; apply on x∈[4,6], no re-fit | scope label must confess; apply_law measured out of range |
| 2.2 | New clothes | same law, permuted columns, rescaled units, fresh sample | is the LAW learned, or the dataset memorized? (rediscover + recognize equivalence?) — engine has no equivalence-recognition: expected faceplant |
| 2.3 | Cross-domain same form | inverse-square planted as "gravity" then as "light intensity" (different ranges/noise) | does anything transfer? (nothing is designed to — surface it) |
| 2.4 | Composition | teach law A (v=u+at) and law B (s=vt) separately; challenge requiring A∘B with only raw inputs | can learned laws be REUSED as parts? no mechanism exists — the central faceplant of the tier |
| 2.5 | Fewer examples after experience | after 10 discover() runs on product-family laws, does an 11th need fewer samples? | learning-to-learn: nothing is designed to do this; measure to prove it |

## Tier 3 — Real, messy, public data (no planted truth)

| # | Task | Data | Success looks like |
|---|---|---|---|
| 3.1 | **Kepler** | the 8 planets: semi-major axis, orbital period (raw numbers typed in) | recovers T² ∝ a³ from 8 rows, or honestly shrugs at n=8 (both informative; n=8 is brutal) |
| 3.2 | Pendulum lab | generated with realistic instrument noise + 5% outliers + one systematic bias | T = 2π√(L/g) form; does the outlier row poison it? |
| 3.3 | Real rhythms | sunspot counts (public, ~300 yr) fed as a stream to wave_consolidate | finds the ~11-year circle without being told periods exist |
| 3.4 | Leaky table | tabular set with a spurious high-R² proxy planted among honest features | is it seduced by the leak? (needle-vs-residual honesty) |

## Tier 4 — Adversarial epistemics (bluff detection)

| # | Task | Setup | Pass = |
|---|---|---|---|
| 4.1 | Unsolvable | random labels; shuffled-pixel images | NO RULE / low capture; ANY confident claim fails |
| 4.2 | Drift | law changes halfway through the stream | anything that notices; nothing is designed to — measure the silence |
| 4.3 | Conflicting duplicates | same quantity in two units with disagreement/noise | which does it trust? does it report the conflict? |
| 4.4 | Validation-bit learning | right/wrong feedback only, after commitment | currently CANNOT consume it — the documented gap that motivates the next capability |

## Tier 5 — Self-observation (the mirror)

| # | Task | Setup |
|---|---|---|
| 5.1 | Own activation log | wave_consolidate over the log Isaac generates while RUNNING tiers 1–4: does his cognition have discoverable circles? |
| 5.2 | Verdict audit | across all tiers: calibration table — when he said UNDERSTOOD/form-true, how often was he right? The one number that decides trust. |

## Execution order & rig

1.1 → 1.3/1.4 (the old wounds first) → 4.1 (bluff check early) → 2.1/2.2 →
3.1 Kepler → 1.2 MNIST → rest. One runner script per tier in `rebuild/`,
fixed seeds, CSV logs, no engine edits mid-curriculum (fixes wait for the
post-mortem; the point is the honest face-plant catalogue).
