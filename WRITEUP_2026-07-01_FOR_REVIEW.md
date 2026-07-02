# ISAAC Discovery Stack — Technical Report for Review
**Date:** 2026-07-01 · **Code:** `code/isaac.py` (single file, numpy only) + `rebuild/` harness
**Status of every claim: re-runnable.** See §7. Nothing here requires trusting the author.

## 1. Summary

One engine (`isaac.py`, ~2,900 lines, no ML frameworks, no trained networks in
any decision path) that, given examples of a task it cannot do, returns one of
four validated verdicts and, when possible, the explicit generating equation:

- **UNDERSTOOD** — equation recovered, validated on a held-out half, reusable
  (`apply_law`), with a scope label: *form-true* (edges of observed range hold)
  or *range-valid* (usable inside observed range).
- **PARTIAL** — a real equation explaining a stated fraction.
- **CAPTURED** — no equation, but stored examples predict held-out outcomes
  beyond a permuted-outcome null (nearest-exemplar; no training).
- **NO RULE** — nothing beats chance. 0/20 false discoveries on pure noise.

The same engine additionally: crystallizes co-activation groups, movement
(handoffs) and cycles from temporal streams; tracks a discovered cycle with an
internal clock robust to occlusion; opens/clears temporary statuses on
entities ("present but blocked"); and routes every discovered relation into a
queryable fact index.

## 2. Methods (the load-bearing ideas)

**2.1 Universal null discipline.** Every admission — a correlation edge, a
handoff, a basis rotation, an equation term, a status explanation — must beat
a null designed to destroy *exactly the claimed structure and nothing else*.
Three instances arose independently and form a pattern:
- *jitter null* (±2–5-step shifts) for co-timing claims — a full circular
  shift is provably wrong for periodic signals (it relands in phase 1-in-period
  times, making real simultaneity unbeatable);
- *null-gated basis* — rotate only along correlations exceeding ~3/√n;
  near-identity eigenvectors are noise-driven rotations;
- *conditional rate-gap null* for suppression claims — raw-count nulls
  mathematically cannot certify a high-coverage blocker (overlap ratio caps at
  1/coverage); the claim is the conditional rate difference.

**2.2 Doors as observed distributions (not fitted boxes).** Per-class,
per-dim quantile histograms scored by one summed log-likelihood matmul,
formed basis-first. Replaces axis-aligned boxes, which (a) cap on diagonal
data and (b) change 17.8% of their verdicts under affine re-encoding of the
same data (measured) — i.e., they described the encoding, not the world.

**2.3 Staged, null-gated equation search.** Linear-in-coefficients over a
nonlinear atom library (products to degree 3; sin/cos/exp and pairwise
cos/sin/cosh at scale grids). Candidates grow only around admitted terms (no
d^k enumeration). Admission: residual correlation must beat the 95th
percentile of the *max-over-candidates* correlation on permuted residuals.
Scale parameters inside nonlinearities (frequency, decay) — unreachable by
regression — are proposed by the grid and sharpened by hill-climbing refits.

**2.4 Legibility defenses (against degenerate surrogates).** Rich libraries
breed impostors (a wide cosine is locally a parabola; an exponential can be
Taylor-built term by term). Four defenses, each necessary in testing:
trial-refit lookahead (score candidates by refit R², not raw correlation);
reuse-aware parsimony (a newly introduced scale-atom must buy ~2% R²;
already-admitted flexibility is free); structurally diverse shortlist
(heavy-tailed raw variables lose correlation contests to bounded atoms —
simple candidates are guaranteed trials); completion bonus (a trial reaching
R² ≥ 0.995 outranks all incremental ones).

**2.5 Temporal crystallization + expectation.** Simultaneity → groups;
off/on co-timing → handoffs; closed handoff paths → circles; recursively,
circle activity is a door one level up (a planted era rotation was recovered
as a circle-of-circles). A tracked circle gives expectation; persistent
expectation violations open statuses; statuses are doors, so the ordinary
machinery explains them (e.g., `blocks(disk) ← cloud` emerged with no
masking-specific code and entered the fact index).

## 3. Results — synthetic ground truth (all held-out)

| Challenge | Result |
|---|---|
| x0·x1 + x2² − x3 | exact, R² 1.000; reusable law R² 1.000 |
| pt1·pt2·(cosh(Δη)−cos(Δφ)) (m_jj form) | exact (harness); old poly-L1 walls at 0.609 |
| x0·x1·cos(x2−x3) | exact, R² 1.000 |
| 0.5x² + 1.5·sin(2x), single input | exact |
| e^(−0.4t)·cos(3t), decay off-grid | `+1.00*cos(3t)*exp(−0.4025t)`, R² 0.999 |
| sin(3·x0·x1) (nested) | honest PARTIAL/CAPTURED, never UNDERSTOOD |
| pure noise | NO RULE, 0 terms |

## 4. Results — failure modes and limits (battery, ~60 runs + nulls)

`rebuild/discovery_battery.py`, per-run log in CSV. Headlines:

- **Noise:** exact form survives to noise = 1.5× signal std (coefs within
  10%); verdict downgrades honestly UNDERSTOOD→PARTIAL from 0.4×. Never fake.
- **Sample onset:** exact at n=100. **One WRONG-form event at n=200** (cosine
  surrogate at R² 0.998) — small samples weaken the parsimony contest; treat
  n < ~400 recoveries as provisional.
- **Distractors:** exact with 40 irrelevant features (2 s runtime).
- **Law size:** 6 simultaneous product terms recovered exactly (6/6).
- **Small terms:** a 2%-of-signal term detected exactly (floor ≤ 0.02).
- **Collinearity:** correct variable chosen even at 97% collinearity.
- **Off-grid scale reach:** exact to ~1.5× grid max; *functionally* perfect
  but form-approximate (sum-of-sines surrogates) to ~2× (k≈4.5–6); lost at
  k=9 — refine cannot climb where correlation carries no gradient.
  **Practical limit: frequencies ≲ 2× the atom grid.**
- **Beyond the class (must not fake):** nested sin(3·x0·x1) → PARTIAL with
  the **edge score exposing the surrogate (center 0.599 vs edge 0.180)**;
  degree-4 product → CAPTURED (exemplars) with honest "no equation";
  rational 1/(1+x0²) → a *usable* trig surrogate at R² 0.996 labeled
  UNDERSTOOD — correct by the range-valid standard, wrong beyond the
  observed range (documented limitation of the scope label: it can only
  test edges that were observed).
- **False discoveries: 0/20 on pure noise.**
- **Heavy tails:** exact under lognormal and Student-t(3) inputs.

## 4b. Adversarial self-review (red team, `rebuild/redteam_discovery.py`)

Eight attacks designed WITH knowledge of the internals, each targeting a
specific design decision. First round: 3 kills + 1 crash. All fixed with
principled (not patched) changes; second round: 0 kills, 0 crashes, and the
full regression (battery + suite) holds.

| Attack | First round | Fix | Now |
|---|---|---|---|
| A1 true wide cosine (parsimony toll suppresses the true form) | KILL — reported a parabola | completers judged by **F-test** (A1's 0.00024 R² gap = F≈80, decisive; genuine ties → simpler form) | SURVIVED, cosine found |
| A4 deterministic sin(9x) + 30 noise dims | KILL — false NO RULE (the cardinal sin) | wider frequency grid (reach ~16) + per-feature 1-D neighbor capture (noise dims can't swamp a 1-feature rule) | honest CAPTURED at 0.997 |
| A5 exponential growth (library was decay-only) | KILL — cubic passed as form-true | growth atoms (negative k) | exact `exp(0.5*x0)` |
| A8 NaN cell | CRASH | non-finite row guard | clean, exact recovery |
| A2 completion vs 0.5% crumb / A3 interior hole / A6 sorted input / A7 9-orders-of-magnitude scales | survived round 1 | — | still survive |

Residual known weakness after both rounds: ONE wrong-form event at n=200
(small samples weaken the F-test's power — the n<400 provisional rule stands),
and sin(9x)-class rules are caught but not said (expressive-class limit,
honestly labeled).

## 4c. Identifiability: rivals held open until confirmed

Classic look-alike families (parabola↔wide cosine↔cosh; exponential growth↔
cubic↔power law; exponential decay↔hyperbola; the sigmoid family;
Gaussian↔Lorentzian tails; everything↔linear on a narrow range) agree on the
dense center of any bounded sample and split in tails and past turning
points. The engine now implements the audit's identifiability clause:

- after a law is admitted, each single-feature term is challenged by every
  rival form (swap, refit, refine, F-test);
- rivals with F < 10 are genuinely indistinguishable on this data and stay
  ALIVE on the law's record, each with a **probe** — the input where the
  tied forms diverge most, usually outside the observed range;
- `confirm(name, X, y)` takes new evidence: decisively beaten rivals retire
  (CONFIRMED); a decisively winning rival OVERTURNS and rewrites the law.

Demonstration (self-test, 4/4): cos(0.5x) observed only on |x| ≤ 1.2 → the
engine chooses the parabola, declares the cosine tie (F=1.4), and names the
probe "x ≈ 2.99"; given wide-range data it OVERTURNS to `+5.19*cos(0.49*x0)`
(truth 5·cos(0.5x)). The true-parabola control on the same range is CONFIRMED
unchanged. Suite: 10/10.

## 5. Results — real data (full datasets)

- Covtype (581k): proximity doors 56.2% vs faithful box baseline 49.3%
  (recorded box-forest ~62%, net 82% — remaining gap = interactions =
  compound doors, not yet built).
- HIGGS (11M): doors 64.6% / AUC 0.700 in 22 s on 10.5M rows (logistic 64.2%,
  MLP 69.1%, additive ceiling AUC 0.765, full ceiling 0.881). Saturated in
  bins → limit is the additive structure.
- HIGGS m_jj: recovery fails (R² ~0.03–0.05) — and fitting the TRUE form
  with scanned scales across all six jet pairings caps at **R² 0.065**,
  proving a *data* wall (missing jet masses, per-event pairing), not a
  method wall. The engine's fourth verdict, demonstrated on real physics.

## 6. What is still missing (gap analysis)

Full sheet: `audit/VERDICT_SHEET_2026-07-01.md`. The short list, ranked:

1. **Compound doors (audit 2.11)** — both real-data gaps point here; ceiling
   detection → compound search is specified, not built.
2. **Uptake-edge composition in the engine** — validated in harness (7/7
   incl. dismantled-engine control); `_crystallize` still stores members only.
3. **Identifiability clause (2.6)** — when two forms tie on observed data
   (cos vs cosh in the bulk; trig surrogates of rationals), the engine should
   NAME the tie and request the discriminating sample; today it commits.
4. **Shrug → discover auto-trigger** — discovery is a method call, not yet a
   reflex on failure.
5. **CAPTURED → law graduation** — attack the exemplar memory with function
   recovery until caught becomes said (completeness loop, 2.8).
6. **Symbolic/token challenges** — discover() is numeric-only.
7. **FCA lattice** — groups are connected components; shared doors merge
   (measured: circles lost at 2 shared doors). Concepts-with-overlap need
   the lattice.
8. **Atom 3-verdict comparability (2.1)** and level-indexed nulls (2.5) —
   never built.
9. Fisher-ratio still available in a selection path — replace with drop-one
   relevance (2.7).

## 7. How to verify (no trust required)

```
cd Documents\isaac_project\code
set PYTHONIOENCODING=utf-8
python isaac.py                          # engine self-test: expect 9/9

cd ..\rebuild
python doors_proximity.py                # rebuild A: expect WORKS 4/4
python composition_uptake.py             # rebuild B: expect WORKS 7/7
python enumerator_staged.py              # rebuild C: expect WORKS 4/4
python wave_crystallizer.py              # rebuild D: expect WORKS 5/5
python wave_interference.py              # rebuild E: expect WORKS 5/5
python entity_status.py                  # rebuild F: expect WORKS 5/5
python wave_battery.py                   # ~5 min, CSV + failure modes
python discovery_battery.py              # ~3 min, CSV + failure modes
python covtype_real_test.py              # full covtype head-to-head
python higgs_real_test.py                # full HIGGS (needs data/HIGGS.npy)
```
All randomness is seeded. The engine backup chain is in `code/backups/`.

## 8. Relation to prior art (positioning for review)

Sparse symbolic regression over term libraries is established (SINDy, EQL).
Claimed contributions here are the *synthesis and discipline*, not the
regression: (a) the max-over-candidates permutation gate at every admission
(0/20 false discoveries); (b) claim-specific nulls as a design principle,
with two provably-wrong-null case studies (circular shift for periodic
co-timing; raw counts for high-coverage suppression); (c) the four-verdict
epistemic interface with held-out validation and scope labeling; (d) the
legibility defenses against degenerate surrogates (§2.4), which standard
R²-driven selection does not provide; (e) integration: discovered laws,
groups, cycles, and blocking relations enter one substrate (doors + facts)
queryable by the same reasoning layer.
