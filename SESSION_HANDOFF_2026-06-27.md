# ISAAC — Session Handoff · 2026-06-27
### Feature-math / equation extraction. Continues the 2026-06-24/26 neural-transplant work.

> **READ THIS FIRST — the goal, and the mistake to not repeat.**
> The objective is **NOT classification accuracy.** It is to **extract the true
> equations and relationships — the *mechanism* of a system — and validate that
> what's extracted is *real*, so that things currently requiring supercomputer
> simulation become directly computable.** Accuracy is a *trap*: gradient descent
> reaches arbitrary accuracy on pure noise, so a high score says nothing about
> truth. The win condition is **"did we recover the real math,"** not "did we
> classify well." The user wants to *find EVERYTHING* — the full set of governing
> relationships — and specific phenomena (e.g. the Higgs) appear *among* what's
> found, or as *discrepancies where the math doesn't close*, not as a thing you
> set out to confirm.
>
> **The assistant repeatedly defaulted to measuring HIGGS classification accuracy.
> That was the wrong metric every time. Do not do this.** The genuine results of
> this session are the ones that recovered *truth* (see "Real results" below).

---

## The arc

Started from the user's request to improve/monetise "neural net extraction." It
evolved, through a long chain of honest experiments and the user's own theory,
into a concrete research program: **represent concepts as fitted functional forms
and relations ("functions on doors"), recognise by fitting and reading the
residual, and extract the governing equations of a system rather than approximate
its outputs.** A full research proposal was written
(`RESEARCH_PROPOSAL_functional_concepts.md`).

---

## The theory chain (the conceptual spine, in order)

1. **Don't destroy information.** The recurring failure mode is lossy operations:
   *averaging* (the mean of a rainbow is grey — the average of a structure is its
   anti-structure), *binning* (kills proximity), *axis-aligned boxes* (a circle and
   a square have the identical bounding box). Each throws away the detail that *is*
   the signal. "The devil is in the details" — the details are the information.
2. **Presence, not average.** Recognition must *count which structure is present*
   (primary), refine by closeness (secondary), and **never average** — because a
   present-but-displaced feature is real evidence while a featureless average
   ("technically true") is fake. Validated: count-primary + held-out mask is a
   minimal-key classifier (Iris/Wine/BreastCa 1–2 dims, no loss).
3. **Generalise by fitting a form, not by averaging instances.** A function is the
   only representation that is *general, lossless, and legible* (box = lossy-general;
   lookup = lossless-specific; function = both). A circle is `‖p−c‖=r`, not a pixel
   pattern or a thousand linear pieces.
4. **Relations are functions too.** "8 = two circles, aligned + touching" — a
   relation is an *equation between the forms' parameters*, carried on a graph edge
   (door). Transforms (shift/scale) are the *parameters*; stereo disparity = depth,
   zoom = scale, all read off one door-function. Variance is *also* a function
   (model the noise, don't average it).
5. **Results vs mechanism.** A trained net stores **results** (a ~100k-parameter
   tabulation of a function's outputs), never the **mechanism** (the rule). It
   reinforces outputs, not generators. Your own intrinsic-dim measurement is the
   fingerprint: GPT-2's manifold is ~8-D (the mechanism) but its decision is smeared
   across hundreds of dims (the result-table).
6. **Gradient descent is not the enemy — the *space* is.** Point GD at a *space of
   equations* (a menu of math primitives + sparsity) instead of a space of
   result-surfaces, and it refines the *mechanism*. This is established (SINDy, EQL,
   symbolic distillation — see §8 of the proposal). Its hallmark is **extrapolation**.
7. **Matmul exceeds explicit interactions because it's the complete distributed
   sum** — every input touches every output, interactions emerge from composition,
   no enumeration. Explicit interaction extraction must enumerate (~dᵏ terms),
   which is combinatorial and sample-hungry — "more variables → more samples →
   harder." The way out: the structure is low-D but *dense in the raw basis*; find
   the **basis (lens/rotation) where it goes sparse**, *then* extract the form. The
   lens was never a side-quest — it's what makes mathematical decoding tractable.
8. **Model everything; the needle is the residual.** Don't hunt the Higgs — model
   all the other structure so completely that the signal is what won't fit (the
   null method at system scale; how real physics finds an excess over a modelled
   background). Confirmed: structure-completeness drives discrimination, and the
   model recovered *real* physics (R²=0.865 reconstructing the invariant masses).

---

## Real results (the ones that recovered TRUTH — the right metric)

- **`equation_fit.py`** — GD with L1 over a symbolic basis fit to points from
  `0.5x² + 1.5·sin(2x)`: recovered `+0.49·x² + 1.46·sin(2x)` (every other term
  zeroed) and **extrapolated** — MSE 0.07 vs an MLP's 5.5 outside the range. The
  MLP learned the surface; the equation learned the rule.
- **`interaction_extract.py`** — sparse interaction regression. On a synthetic with
  planted `x0·x1 + 0.8·x2² − 1.2·x3`, **recovered exactly those three terms** (top
  3, right signs). On HIGGS, **named the correct physics** (m_wwbb, m_bb², m_jlv·m_bb,
  …) — but with 280 flat terms, *which is itself the finding*: term-concentration
  is a built-in detector. Few dominant terms ⇒ a compact mechanism exists; a flat
  smear ⇒ no short form at that order (deep/dense).
- **`higgs_residual.py`** — modelling each class's full structure and reading the
  residual: completeness ladder climbed (box→linear→nonlinear), and the structure
  model **reconstructed the real invariant masses at R²=0.865** — i.e. the extracted
  associations are *real*, recovered without being told.
- **`feature_math.py` / `relational.py`** — forms (circle by fit, 1.00, scale/pos
  invariant; box-blind proof: circle vs square = identical bbox, residual 0.00 vs
  0.12) and relations (8 vs ∞ etc., 1.00 given components). **The bottleneck is
  perception** — recovering the forms from raw input (segmentation), not the logic.

## Results that were the WRONG metric (recorded so they aren't over-weighted)

HIGGS *classification accuracy* across many methods (box ~0.52, contrast 0.62,
his-matrix 0.65, functional 0.61, interaction 0.65, residual 0.64; refs logistic
0.63, RF 0.71, deep ~0.88). These were the assistant chasing accuracy. The *only*
useful readings inside them are the **truth-recovery** signals above (R²=0.865,
named physics, term-concentration), and the structural fact that HIGGS is
**deep/dense** (no compact form at low order) — which is *why* accuracy plateaus
and *why accuracy was the wrong question.*

---

## Engine state (`code/isaac.py`) — self-test 6/6

- **Added this session (RAN, kept):**
  - `recognize_doors` — partial **door-overlap** recognition, recursive,
    confidence-carrying ("10 of 12 → 0.83"). Works *with* the box, not instead
    (scene test: composition absorbed the box's per-item errors).
  - `recognize_matrix` — the **padded concept-matrix** (box-friendly + per-concept
    mask) ported from `range_classifier/v3/fastscore.py`; `rule="count"` reproduces
    the box reader exactly; `deepest`/`avgdiff` available. **The box is the
    constant-function special case**; the upgrade is `f(context)` in place of the
    stored median (validated: HIGGS 0.49→0.61 from that single change).
- **Backup:** `code/backups/isaac_pre-partial-doors_2026-06-26.py` (pre-additions).
- **Earlier this session, REVERTED:** `crystallize_contrast`/`classify_contrast`
  were added then rolled back at user request; not present.
- **Integrity rule (still load-bearing):** testing Isaac means *only* Isaac does
  the cognition; never substitute sklearn/RF for the decision and call it his.
  sklearn is allowed only as a *function fitter* (least-squares/L1 fitting form
  parameters) or for data I/O — the *decision* must be the his-way matcher.

---

## The proposal

`Documents/isaac_project/RESEARCH_PROPOSAL_functional_concepts.md` (~6pp, draft for
external review). Honest categories separated (principle / preliminary results /
hypotheses). §5.8 added (GD over a symbolic basis). **Literature check done: SINDy,
EQL (+variants), symbolic distillation (SymTorch, Cranmer), KAN-SR are established
— so the equation-learning *component* is prior art; the project's novelty must be
the SYNTHESIS** (functions-on-doors recognition graph + presence-primary matcher +
variance-as-function + residual-driven discovery loop), and §8 must say so to
survive review. **One pending revision** the user approved in spirit: fold the "GD
over a symbolic basis is established; we adopt it as a component" framing into §8
explicitly, and re-centre the contribution on the synthesis + the *equation-
extraction goal* (not accuracy).

---

## Open problems / the honest crux (unchanged, now sharper)

1. **The perception front-end is the wall, every single time** — raw input → clean
   forms/variables (segmentation, form-detection). It blocked rung 2 (0.49/0.21),
   it's why symbolic methods stayed niche, and it's the make-or-break for this
   program. *This is where to point effort.*
2. **Basis-first decode** — find the rotation/lens where dense structure goes
   sparse, *then* extract. Tie the early-session lens work to the extraction.
3. **Deep/dense regime** — where no basis makes it sparse (HIGGS-style nested
   structure), only the matmul-sum works and extraction is intractable; the
   term-concentration diagnostic tells you which regime you're in.
4. **Rare-signal vindication (proposed, not yet run):** rerun `higgs_residual.py`
   on a heavily *imbalanced* split (~1% signal). Prediction: discriminative methods
   collapse (can't train on the rare class) while the model-everything residual
   holds — the honest test of "model everything else, the needle is the residual,"
   on the regime the balanced benchmark hides.

---

## File index (all under `code/`, proposal+handoffs under `isaac_project/`)

**Feature-math / equation extraction (this session's core):**
`feature_math.py` (forms), `relational.py` (relations / 8), `equation_fit.py`
(GD-over-basis, extrapolation), `interaction_extract.py` (named-term extraction),
`higgs_functional.py` (box→function), `higgs_residual.py` (model-everything ladder).

**Matching / recognition prototypes:** `match_proto.py` (partial+scaled),
`match_proto2.py` (relational ratios), `recursive_match.py` (partial door overlap,
recursive), `door_digits.py`, `scene_recognition.py` (box+door together).

**Engine:** `isaac.py` (+`recognize_doors`,`recognize_matrix`; 6/6),
`backups/isaac_pre-partial-doors_2026-06-26.py`.

**Earlier-session (vision/HIGGS, in `code/` and `code/neural_transplant/`):**
`lens_bench.py`, `auto_lens.py`, `grid_reservoir.py`, `codebook_{net,sweep,full}.py`,
`higgs_{bench,isaac,contrast,matrix,fuzzy,discover_isaac}.py`, `inspect_higgs.py`,
and the `range_classifier/v3/` package (the padded-matrix + masks + matchers
`fastscore.py` is the source of `recognize_matrix`).

**Docs:** `RESEARCH_PROPOSAL_functional_concepts.md`, this handoff. Note: a *second*
code tree exists at `2_the_machine/code/` (reference snapshot); `code/` is the live
working copy — pick one as authoritative before editing further.

*Next session: lead with the GOAL box at the top. Measure truth-recovery, not
accuracy. The front-end is the crux. The rare-signal imbalanced test is the
cleanest next experiment.*
