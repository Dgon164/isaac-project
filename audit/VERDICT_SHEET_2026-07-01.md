# Verdict Sheet — filled 2026-07-01 (evening)

Against `AUDIT_STANDARD_v1.md`. Strict: WORKS / BROKEN / NEVER BUILT, with the
evidence number. "In engine" = wired into `code/isaac.py` and covered by its
self-test (9/9); "harness" = validated in `rebuild/` scripts only.

| # | Capability | Code path | Test | Verdict | Evidence |
|---|------------|-----------|------|---------|----------|
| 2.2 | Doors / dims / ranges | `isaac.py` fit_lens + crystallize_features (proximity doors); `rebuild/doors_proximity.py` | rebuild A 4/4 + engine smoke | **WORKS** (in engine) | diagonal 99.0% vs box 88.0%; re-encoding invariance 100% vs 82.2%; engine smoke 99.2% |
| 2.1 | Atom (3-verdict SAME/DIVERGENT/ABSENT) | `compare()` gives shared/only-a/only-b; no principled ABSENT-vs-decompose | none | **NEVER BUILT** (as specified) | depth-aware comparability test does not exist |
| 2.10 | Permuted-null infra | pervasive: `_wave_groups` (jitter+floor), `_wave_edges`, `_Enumerator` admission, `_capture` | every battery | **WORKS** | noise: 0 false circles/20, 0 false masks, discover false-discovery see E9; "null must attack exactly the claimed structure" ×3 (jitter / basis gate / rate-gap) |
| 2.4 | Crystallizer / FCA lattice | `_crystallize` (types, FCA-ish closure); wave groups = connected components, NOT a lattice | test_language etc. | **BROKEN** (partial) | overlap cannot be represented: shared doors merge groups (wave battery E7: circles 0% at 2 shared doors); no concept lattice |
| 2.5 | Null detection (level-indexed) | discover() NO RULE verdict; wave nulls | discovery (c), E9 | **WORKS** (flat), level-indexing NEVER BUILT | NO RULE on noise; no "null at surface, lawful at whole level" machinery |
| 2.3 | Holarchy / composition (uptake) | `rebuild/composition_uptake.py` ONLY | rebuild B 7/7 | **WORKS (harness)** — NOT in engine | dismantled-engine control passes; engine still membership-only in `_crystallize` |
| 2.11 | Classification flat+compound | flat: proximity doors; compound doors | covtype/HIGGS | flat **WORKS**, compound **NEVER BUILT** | covtype 56.2%, HIGGS 64.6%/AUC 0.700; both gaps point at compounds; ceiling→trigger not wired |
| 2.7 | Keypoints (drop-one causal) | `_fisher` still exists (lens select param) — the FORBIDDEN statistic | none | **NEVER BUILT** (and Fisher still present in a selection path) | audit says Fisher MUST NOT rank; it's optional but available |
| 2.8 | Completeness (3-valued accounting) | discover() verdicts approximate it | test_discovery 7/7 | **PARTIAL** | UNDERSTOOD/PARTIAL/CAPTURED/NO RULE exist per-challenge; % accounting (law+captured+noise=100) not implemented |
| 2.6 | Function recovery | `discover()`/`_Enumerator` in engine | test_discovery 7/7 + battery | **WORKS** (see battery limits) | exact forms incl. off-grid damped oscillation; identifiability clause (name tied candidates, request discriminating sample) NEVER BUILT — observed cos/cosh commit on real m_jj |
| 2.9 | Shadow census | equation_discovery scripts only | HIGGS m_jj diagnostic | **PARTIAL (harness)** | m_jj wall proven a data wall (true form R² 0.065 across all pairings) — verdict #4 demonstrated once, not a general engine capability |
| 2.13 | Scaling curves | batteries log CSV per run | wave + discovery batteries | **PARTIAL** | onset/saturation measured for waves + doors bins; not yet for every capability |

## Carried suspects — status
- Membership-only composition: CONFIRMED as designed-in flaw; fixed in harness (B), engine migration pending.
- Representation-variance of doors: CONFIRMED and measured (box 17.8% verdict flips); fixed by proximity doors.
- Fisher-ratio in ranking paths: still present as `fit_lens(select=...)` option — should be replaced with drop-one relevance (2.7).
- Compound doors: still NEVER BUILT — the single highest-leverage missing piece (covtype 56→82 gap, HIGGS 0.700→0.881 gap).
- O(n²) crystallizer: unaddressed.
