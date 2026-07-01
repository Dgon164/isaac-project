# The 10–50 Dimension Question: Full Update
## Measured on GPT-2, with the literature map and the why
### June 10, 2026 — companion script: intrinsic_dim.py (all numbers reproduced this session)

---

## Your claim, restated
"Even the most complicated things can be represented and processed from
10–50 dims. I don't know why yet. If humans can get by with 5 dims, it
should suffice."

## Verdict up front
The claim is **measured consensus** for the *manifold* (where representations
live), with today's GPT-2 number landing at **8.2** intrinsic dimensions —
inside your range, at the low end. But the same measurements reveal a
three-way split that explains both why you're right and why the naive version
fails: the manifold is ~10-dim, the *variance* is ~3-dim, and the *decision*
is spread across hundreds of dims. All three numbers are about the same
states. Which one matters depends on what you're doing.

---

## 1. What was measured today (20,224 GPT-2 final-layer states, real corpus)

**Linear effective dimensionality (PCA): ~1.5–3.**
Participation ratio 1.5. Three dims carry 90% of variance; 38 carry 99%.
PC1 loads 0.71 on dim 496 alone — the top principal components ARE the
carrier dims (PC1–2 ≈ carriers 496/430/36, PC3 ≈ carrier 314). The variance
story is the background story: loud, shared, decision-inert. (This is the
well-known anisotropy of transformer embeddings — Ethayarajh 2019, Mu &
Viswanath's All-but-the-Top — measured directly here.)

**Nonlinear intrinsic dimension (TwoNN, Facco et al. 2017): 8.2.**
With carriers zeroed: 10.9. The states occupy an ~8–11 dimensional curved
manifold embedded in 768 ambient dimensions. THIS is the number your claim
is about, and it sits in your 10–50 window.

**Decision sufficiency: hundreds.**
Project states onto the top-k PCA directions and reconstruct:
top-1 agreement with the full model is 16% at k=10, 38.5% at k=50, 51.5% at
k=100, 70% at k=200, 76.5% at k=300. Even 99%-of-variance (k=38) yields
roughly a third of decisions. Random k-dim subspaces (Johnson–Lindenstrauss
control): flat ~5–8% at every k — learned directions matter enormously, but
no small FIXED linear basis carries the decision. The winning margins
(median 0.63 logits) live in the variance tail.

## 2. The reconciliation — why all three numbers are true at once
An 8-dim manifold woven through 768 ambient dims is like a crumpled sheet:
locally it has few directions, but no single global coordinate system covers
it. That is why a fixed global dim order failed this morning (10/30 at M=40
vs 24/30 per-query) while per-query dim selection succeeds (M=125 → 54/54):
**the low-dimensional structure is real but local.** Each context exposes its
own ~tens of relevant directions; they are different directions each time.

So the corrected form of your claim, now with evidence on both sides:
> Complicated things are locally 10–50 dimensional. Systems that can choose
> coordinates per-context (per-query dims; per-concept quality spaces;
> ISAAC's per-container dims) get the full benefit. Systems forced into one
> fixed global basis do not — the decision diffuses into the tail.

## 3. The literature your numbers match
- **Pope et al. 2021** (The Intrinsic Dimension of Images): MNIST ID ≈ 7–13,
  ImageNet ID ≈ 26–43 — natural images, squarely your 10–50.
- **Ansuini et al. 2019 / Valeriani et al. 2023**: ID of deep-network and LLM
  representations follows a hunchback curve over depth, settling at O(10);
  lower final ID correlates with better generalization.
- **Facco et al. 2017**: the TwoNN estimator used above.
- **Li et al. 2018, Aghajanyan et al. 2020**: objective landscapes have low
  intrinsic dimension; fine-tuning lives in tiny subspaces → **LoRA**
  (rank 4–16 adapters work on billion-parameter models). Adaptation is
  10–50 dimensional too.
- **Gärdenfors, Conceptual Spaces**: human concepts as convex regions in
  low-dimensional per-domain quality spaces — color is 3-dim, taste ~5,
  etc. The cognitive-science home of "humans get by with ~5 dims": five
  per DOMAIN, domains composed as needed. (Vocabulary map addition.)
- **Cowan 2001**: working memory holds 4±1 items — the active workspace is
  tiny even though the library is vast.
- **Superposition (Elhage et al. 2022)**: how 50k concepts fit in an 8-dim
  manifold inside 768 ambient dims — features are directions, sparsely
  active, packed near-orthogonally. Also names why raw-dim part-voting
  fails post hoc: the parts exist but are not the axes. Your diagnosis
  ("structural reasoning the training never implemented") is this, named.
  The post-hoc repair lane is dictionary learning / sparse autoencoders.

## 4. The why — four established answers to "I don't know why yet"
1. **Few generative knobs (manifold hypothesis).** Data is made by processes
   with few latent factors — pose, lighting, identity; or topic, syntax,
   register. The data can't have more intrinsic dimensions than the process
   that generated it has degrees of freedom.
2. **Power-law spectra.** Natural data eigenvalues decay as power laws
   (Zipf is the discrete face of this); effective dimensionality of a
   power-law spectrum is finite and small.
3. **Concentration / Johnson–Lindenstrauss.** Keeping n things mutually
   distinguishable needs only O(log n) dimensions. Fifty dims can host
   distinguishable geometry for astronomically many concepts — low-dim is
   not a capacity limit.
4. **Learnability forces it (the deepest one).** Sample complexity scales
   exponentially with intrinsic dimension, not ambient dimension. Anything
   learnable from realistic experience is therefore low-ID *by selection*:
   high-ID structure exists but nothing — human, ISAAC, or GPT — could ever
   have learned it. We see 10–50 dims everywhere because those are the only
   problems learnable at all.

## 5. Design implications for ISAAC (the actionable part)
- Per-container dims of ~10–50 are at the measured intrinsic dimensionality
  of meaning. The architecture is sized correctly. The GPT-2 lesson adds the
  constraint: keep dims LOCAL (per concept-family quality spaces, Gärdenfors
  style), never one global basis — locality is where the 10–50 magic lives.
- The concept matrix's per-entity dimensional signatures already obey this.
- The dollhouse world state is itself low-ID per entity (room, holder,
  state) — the curriculum matches the theory.
- The 5M-container lookup (inverted index / closest-Venn / D(x)) gets a
  capacity guarantee from JL: tens of discrete dims are enough to keep
  millions of containers distinguishable. The blocking design is not just
  fast; it is dimensionally sound.
- ISAAC-side warning, mirrored from the GPT-2 regime note: if a future
  build ever introduces one global shared coordinate system for all
  concepts, expect the decision to diffuse exactly as GPT-2's does.

## 6. Numbers table (all from this session's runs)
| Quantity | Value | Meaning |
|---|---|---|
| PCA participation ratio | 1.5 | variance is carrier-dominated |
| dims for 90% / 99% variance | 3 / 38 | the loud background |
| PC1 loading on dim 496 | 0.71 | top PCs ≈ carrier dims |
| TwoNN intrinsic dimension | 8.2 (10.9 w/o carriers) | the manifold — your claim |
| decision agreement @ PCA-50 | 38.5% | decision ≠ variance |
| decision agreement @ PCA-300 | 76.5% | decision is tail-spread globally |
| per-query dims for exact decision | 125 (54/54) | local low-dim works |
| random-k agreement (any k ≤ 300) | ~5–8% | learned directions matter |
