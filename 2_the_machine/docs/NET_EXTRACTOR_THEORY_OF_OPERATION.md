# Net Extractor — Theory of Operation

*How the transplant / crystallization works, mechanism by mechanism, what it's for,
and the honest verdict on what's actually pulling weight. Pairs with
`ISAAC_THEORY_OF_OPERATION.md`. Reflects findings through 2026-06-24. Code:
`isaac.py` (`fit_lens`/`crystallize_features`/`classify_features`) and
`neural_transplant/` (`range_classifier.py`, `vision_lens.py`, `lens_bench.py`,
`grid_reservoir.py`, …).*

---

## 0. What it is (and isn't)

The net extractor **crystallizes a trained net's *final, fully-formed*
representation into Isaac-style boxes.** It is **not feature extraction** — it does
not learn edges/textures or low-level features. The net (or encoder, or reservoir)
already did the representation work; the extractor reads off the *finished*
class-discriminative representation and turns it into legible, axis-aligned
**box concepts**. A box *is* an Isaac per-container-dims concept, so a transplanted
net's knowledge lives in the **same Net** as his language and math.

The deep claim it tests: *a trained network is "an expensive, opaque way of finding
the symbols"* — and when you read what it learned, the result is symbolic
(axis-aligned boxes, discrete boundaries, countable membership).

---

## 1. The pipeline — four stages

```
   net activations  ──►  ALIGN (lens)  ──►  QUANTIZE  ──►  BUILD boxes  ──►  SCORE
   (the finished rep)     strip-DC +         4-bit          per-class        count +
                          rotate/select       [-7..8]        [lo,hi,med]      distance
```

**Stage 1 — Extract.** Run data through the net; grab one hidden layer's
activations (typically the penultimate / final representation). No magic — just
read the representation the net already computed.

**Stage 2 — Align (the load-bearing stage; `fit_lens`/`apply_lens`).** Three
sub-steps, any of which may be identity:
- **strip-DC** — subtract the mean activation. Removes the part that's the *same
  for every input* (the carrier / common-mode), which carries zero discriminative
  info. This is "difference, not similarity; identity is the residual."
- **rotate / select** — orient the representation into a *box-friendly* basis
  (Fisher dim-select, reservoir lift, or — the one that actually works — an **LDA
  rotation**). **This is where the difficulty and the value live.**
- The lens is stored as a **net node** (`lens:<name>` with a `transform` meta), so
  it is swappable: wired/external now, a learned/his aligner later, same interface.

**Stage 3 — Quantize (`_quantize`).** Map to 4-bit signed `[-7, +8]` (16 levels).
Empirically optimal — more bits add noise, not signal (the resolution cliff; signed
4-bit ≈ continuous, per the compile-equivalence result). A compression step, not a
learning step.

**Stage 4 — Build & score.** For each class, per dimension, record a **range**
`[lo, hi]` (1st–95th percentile + margin) and a **median** (prototype). Score a new
point against each box with the **two-tier** rule below.

## 2. The box, and the two-tier scoring ("secondary pointers")

A **box** is a hyper-rectangle: a `[lo,hi]` interval per dimension + a median center.
A class can have several (variants, below). Scoring is two-tier:
- **Primary pointer — count (membership):** how many dims fall *inside* the range.
  Coarse — places the point in a neighborhood. *"The walls do membership."*
- **Secondary pointer — median distance (discrimination):** sum of `|point −
  median|` over in-range dims. The **tiebreak** that does the fine cut. *"The
  center does discrimination."* (Without this tiebreak, variants crater accuracy —
  a real bug we hit and fixed.)
- **Variants** (confusion resolution): after building one box per class, classify
  the training data; where it confuses A for B, build a *tighter* box for A to win
  *that* contest. The score takes the best box per class (`per_label` max).

Why count works at all: no single dimension needs to be exclusive — the
**conjunction** across dims does the discrimination (integrated information). On
digits, *no single pixel* separates any class pair, yet the joint box classifies at
0.90. Meaning is in the relationship, not the element.

## 3. The theory — box-friendly vs box-hostile, and the lever

A box's decision boundary is always made of **axis-perpendicular walls.** So:
- **box-friendly** = each class is a compact, roughly axis-aligned **blob** a
  hyper-rectangle can fence (even if individual dims overlap). Boxes nail it.
- **box-hostile** = classes separated by **diagonal / oblique / interleaved**
  boundaries. No axis-aligned box follows a diagonal — it can only staircase, badly.

**The lever is Stage 2's alignment (registration), not the boxes.** The box reader
is finished, cheap, and solid; its success is *entirely gated by the alignment you
feed it.* Aligned rep → boxes match the expensive head. Unaligned → the same boxes
flail. This is the whole game.

## 4. Quantified findings (what the experiments actually showed)

- **Geometry governs quality, not "bad nets."** Box-friendly data (digits):
  MLP-crystal 0.96 vs net 0.97 (~99% retention). Box-hostile (covtype): caps ~0.62
  vs net 0.82, and **no knob** (variants / dim-select / merge / binding) closes it.
- **The vision win — registration confirmed on real data** (`vision_lens.py`).
  Frozen ResNet18 on CIFAR-10: boxes on raw pixels **0.23** → boxes on the encoder's
  final embedding **0.71** (linear probe 0.84). The 0.71→0.84 gap = axis vs oblique.
  An **LDA rotation lens closes the entire gap → 0.834 ≈ linear 0.839**, with no
  gradient training (LDA is closed-form). *The cheap legible box reader matches the
  expensive head once you align first.* Corollary: **variants HURT after good
  alignment** (0.75 < 0.83) — good alignment makes the simplest box win.
- **The lens is a scalability lever, not just accuracy** (`lens_bench.py`). LDA does
  alignment **and** compression in one closed-form step: raw 512-d box 0.708 @
  21.4 ms/1k → LDA-9 box 0.834 @ **0.88 ms/1k** (24× smaller/faster) ≈ linear, fit
  ~0 ms. Caveat: LDA gives `C−1` dims, so the lens *is* the compressor for few
  classes; for thousands of classes you still need blocking/inverted-index.
- **Unsupervised lenses PRESERVE but don't REGISTER.** PCA-50: linear 0.834 but box
  **0.659** — the signal survives, but the axes stay oblique, so the box can't read
  it. *Registration is the part that needs labels.* Auto-lens (pseudo-label
  k-means→LDA) lands **partway**, exactly as predicted: best 0.723 (k-means purity
  only 0.64 — the encoder doesn't cluster by class), recovering ~15% of the gap;
  semi-supervised needs ~10–25% of labels to lock registration (25% → 0.802).
- **No-encoder route (grid + reservoir, `grid_reservoir.py`).** Average-pool image
  → grid → random reservoir → box. WORKS on digits (0.92) FAILS on CIFAR (0.28 box
  vs encoder 0.71). Two findings: (1) **the reservoir adds ~nothing** over the raw
  grid (a dense random projection preserves linear structure, manufactures no
  discrimination — performance is set by the grid). (2) Grid works *iff class is a
  coarse spatial layout* (digit ink-position) and fails when identity is in fine
  texture/parts (cat vs dog average to the same brown smear). **The encoder's whole
  job is turning not-grid-friendly data into grid-friendly** — the 0.43→0.83 gap is
  the measured value of the learned folds.
- **Contrast crystallizer (tried, REVERTED).** Keep two interpretations per cell,
  null the shared with his `compare()`, crystallize the *residual*. On hard tabular
  (HIGGS): box 0.525 (chance) → contrast 0.620 (≈ logistic). But literal set-compare
  = 0.465 (below chance): on continuous data the **magnitude** of the difference is
  the signal, so a soft log-contrast is needed — his comparator needs "how
  different," not just same/different. Ceiling = logistic (first-order); order-2
  barely moved. Removed from the engine; kept as a record.

## 5. What's actually working — the verdict

| piece | verdict |
|---|---|
| strip-DC (remove the shared mean) | **working, necessary** |
| 4-bit quantize | **solid** (more bits = noise) |
| box membership (count) | **core, works — only on an aligned rep** |
| median-distance tiebreak | **working, necessary** (variants useless without it) |
| **the lens / alignment** | **THE load-bearing piece** (LDA closed the vision gap; also the compressor) |
| variants | weak/conditional (hurt *after* good alignment) |
| reservoir lift / Fisher select | weak (cap on hard data; Fisher-on-interactions hurt) |
| compound doors (binding) | conditional (low-order interactions/latents yes, deep no) |

## 6. Binding & latent factors (the second-order layer)

"Metastructural / indirect / latent" structure = **second-order** structure
(correlations among observables), and the mechanism to expose it **is binding** —
compound doors / pairwise products (the product *is* the latent recovered). Fixes
clean, low-order, *identifiable* interactions (XOR 0.48→0.89; a latent-in-correlation
0.51→0.77) and node-level polysemy (`crystallize_senses`/`route`). It does **NOT**
substitute for representation-learning on deeply hostile data (covtype null), and
you **cannot select which interactions matter with an independence criterion** —
because that's itself an interaction problem.

## 7. Honest limits & the frontier

- **Rides on the encoder.** The crystal replaces a tiny *head*, not the encoder —
  no encoder compression in that mode. (Crystal *does* compress when it replaces a
  small whole net, e.g. digits/tabular.)
- **The working lens (LDA) is linear and supervised.** Deep *nonlinear* hostility
  needs nonlinear registration; full alignment needs labels (or ~10–25% of them).
- **The frontier (the whole open bet):** make the lens **his** and **unsupervised** —
  let the crystallizer find the alignment LDA finds *with* labels, *without* them.
  Current evidence: unsupervised gets *partway* (preserves, doesn't register).
  Untried levers: iterative self-training lens (box preds → new pseudo-labels);
  **bolted ensemble** of cheap lenses (decorrelated, merged); a **random
  convolutional** reservoir (keeps spatial locality the dense grid throws away).

## 8. The product read & the integrity boundary

**Ship-as-is (real, today):** frozen encoder + cheap closed-form **LDA lens** + box
crystal = a **legible, abstaining, accuracy-matching** classifier head, fit with no
gradient training, label-efficient, 24× smaller/faster scan. Narrow zero-training
niche: digit/form/icon/gauge/symbol tasks where layout = identity (grid route).

**Integrity boundary:** the **lens** step currently uses external methods (LDA,
PCA, k-means — sklearn). That is the honest seam between "his" and "wired." sklearn
is allowed here as a *transform/IO*, but a result is only an **Isaac** result when
the **deciding** (the box build + membership/centroid scoring + `compare`) is his —
which it is. Making the *alignment* his (not LDA) is the goal, not a cosmetic. Never
report an external learner's decision as Isaac's.

---

*The box reader is finished. The whole game is the aligner — and whether it can be
his.*
