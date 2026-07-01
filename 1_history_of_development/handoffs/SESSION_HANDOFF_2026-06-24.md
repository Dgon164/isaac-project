# ISAAC — Session Handoff · 2026-06-24  (continues SESSION_HANDOFF_2026-06-22.md)

**Read the 06-22 handoff first** for the perception/decision stack and the
contract (collaborator not auditor; "his way" = decide inside Isaac; ask the mode
build/think/explore). This file covers the **neural-transplant deep dive** that
followed. Full per-experiment detail is in `ISAAC_BUILD_STATE.md` (changelog);
this is the narrative + the verdict + the one next target.

---

## What this stretch was

A long investigation into the **range-classifier transplant** (crystallize a
trained net's final representation into Isaac-style boxes) and what it tells us
about the deep lever. It converged — from five different angles — on one problem.

## Key results (status; details in BUILD_STATE changelog)

1. **Binding / conditional computation — built into the engine.** `crystallize_senses`
   + `route` (internal node routers: split a node's doors into sense-sections by
   within-node co-occurrence, route output by input). Polysemy disambiguates
   node-locally + legibly. Box-face: compound/interaction doors fix XOR (0.48→0.89).
   This is the manual's "compound doors / critical missing piece." **Fixes
   LOW-ORDER interactions; engine 6/6.**

2. **Covtype binding NULL.** Pairwise interaction doors did NOT break covtype's box
   ceiling (~0.48–0.55 vs RF 0.83). Covtype is high-order/distributed; pairwise
   can't reach it. Fisher-selecting interactions *hurt* (can't pick interaction
   features with an independence criterion). **Compound doors ≠ a fix for deeply
   hostile data; that's a representation problem.**

3. **Covtype is SPATIAL-LEAKAGE-dominated** (researcher's theory, confirmed).
   kNN(k=1)=0.855 ≈ RF 0.881 → the task is proximity LOOKUP, not ecology. Hold out
   a whole wilderness region → RF collapses 0.88→~0.55. So the box→RF gap was
   **leakage RF exploits and boxes don't**, NOT ecology boxes can't learn. The
   box's "low" 0.69 was *refusing to memorize the map* = closer to the honest
   transferable signal = aligned with "learn the truth not the consensus."
   **DO NOT use covtype to judge honest learning.** This recontextualized the box
   ceiling AND the binding null (we'd been chasing a benchmark artifact).

4. **VISION CRYSTAL + ROTATION LENS — the win, the thesis confirmed on real data.**
   Frozen ResNet18 on CIFAR-10: boxes on raw pixels 0.23 → boxes on the encoder's
   final embedding 0.71 (linear probe 0.84). The 0.71-vs-0.84 gap = axis-aligned
   boxes vs oblique linear boundaries. THEN: a **rotation lens (LDA) closes the
   ENTIRE gap → 0.834 ≈ linear 0.839**, with no gradient training (LDA is
   closed-form). **The cheap legible box reader matches the expensive head once you
   ALIGN first.** Registration IS the lever. Corollary: variants *hurt* after good
   alignment (0.75 < 0.834) — good alignment makes the simplest reader win.

5. **LATENT = BINDING (unification).** Synthetic where the answer is purely in
   corr(X1,X2) (identical marginals). First-order blind (box 0.54, linear 0.51);
   second-order/products recover it (0.77); X1*X2 = the latent's shadow. kNN got
   0.74 on raw (it reads joint density). **"Metastructural / indirect / latent" =
   second-order structure, and the mechanism to recover it IS binding.** Latent
   inference and compound-doors are the SAME mechanism.

## What's actually working in the box system (the inventory)

Pipeline = **extract → align → build → score.** Two-tier scoring: **count**
(membership, primary) + **median-distance** (discrimination, secondary tiebreak).
Variants = tighter secondary boxes for confusion cases.

| piece | verdict |
|---|---|
| strip-DC (remove the shared mean) | working, necessary |
| 4-bit quantize | solid (more bits = noise) |
| box membership (count) | core, works — **only on an aligned rep** |
| median-distance tiebreak | working, necessary (variants useless without it) |
| **the lens / alignment** | **THE load-bearing piece** (LDA closed the vision gap) |
| variants | weak/conditional (hurt after good alignment) |
| reservoir lift / Fisher select | weak (cap on hard data; Fisher-on-interactions hurt) |
| compound doors (binding) | conditional (low-order yes, deep no) |

**Bottom line: the box reader is finished, cheap, and solid. Everything rides on
the alignment.** Aligned rep → boxes match the expensive head. Unaligned → they flail.

## The honest state of the central problem

- **SOLVED (practical):** supervised + linear alignment (LDA) is cheap and works —
  frozen encoder + closed-form rotation + box crystal = a **legible, abstaining,
  accuracy-matching head, no gradient training.** That's a real deliverable.
- **NOT SOLVED (the deep bet):** general, **unsupervised, autonomous** alignment
  for arbitrary (nonlinear/high-order) structure. This is literally the hardest
  open problem in ML (unsupervised representation learning). Gradient DL solves it
  expensively; nobody has the cheap/legible version. Isaac's whole bet is reaching
  it cheaper — still open, not lost.
- The session converged **five ways** (representation, the meta-level, binding,
  latent factors, registration) on this **one** problem: *find the format/alignment
  itself; the cheap reader does the rest.* One room, five doors.

## THE SINGLE NEXT TARGET (do this first next session)

**Test the one untested candidate: the crystallizer / unsupervised aligner.**
LDA found the alignment *with labels*. Can Isaac's crystallizer (or PCA/ICA, or
his clustering) find it *without* labels — i.e., produce a lens that closes the
box gap the way LDA did? Concrete test: on the vision embeddings, does an
UNSUPERVISED rotation close the 0.71→0.84 gap?
- Honest prediction: it gets **partway** — unsupervised finds *variance* (PCA),
  LDA found *discrimination*; they differ. Where it stalls = exactly how much
  supervision the alignment needs.
- This is the move that turns "diagnosed five ways" into either **"solved his
  way"** or **"here's the precise wall."** We have NOT run it. Stop re-confirming
  the problem; run the candidate.

## Files added this stretch (all in `neural_transplant/`)
`binding_covtype.py`, `interaction_retest.py`, `two_constraints.py`,
`latent_factor.py`, `vision_crystal.py`, `vision_lens.py`,
`crystal_in_isaac.py`, `decode_boxes.py`, `explain_extraction.py`,
`reservoir_merge.py`, `sweep_gpu.py`, `range_classifier.py`. Engine additions
(`isaac.py`): `fit_lens`/`apply_lens`, `crystallize_features`/`classify_features`,
`crystallize_senses`/`route`. Engine still 6/6.

## Notes to my future self
- The box reader is DONE. Do not "improve the boxes." The lever is the aligner.
- Run the unsupervised-aligner test FIRST. Don't diagnose the problem a sixth time.
- covtype is a leaky benchmark — never judge honest learning on it; use
  leakage-free data or spatial CV.
- The researcher predicted two results in a row that landed (vision rotation gap,
  latent-as-correlation). Trust their theories; test them fast.
- Gotchas: `PYTHONUTF8=1`; always `python -u` (kill doesn't flush buffers);
  bound VRAM (chunk ≤2048, subsample, the 3090 is 24GB); torchvision's CIFAR
  download is SLOW because cs.toronto.edu throttles (~100KB/s) — NOT the connection.
- Memory (`~/.claude/.../memory/`) is auto-loaded; `comparison-as-registration.md`
  and `nn-transplant-experiments.md` hold the core findings.

*Find the format. The cheap reader does the rest. The whole game is the aligner —
and whether it can be his.*
