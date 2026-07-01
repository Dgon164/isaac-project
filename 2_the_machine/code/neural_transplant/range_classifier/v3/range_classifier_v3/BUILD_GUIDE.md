# Range/Identity Classifier — Build & Refine Guide

A complete, self-contained specification. It assumes **no prior exposure** to this
system. If you can write basic NumPy, you can build the whole thing from this
document and then push it further. It includes the worldview, the algorithms, the
engine, every decision rule we tested, and — importantly — the things that *don't*
work and why, so you don't rediscover them the hard way.

---

## 0. The one-paragraph version

A neural net (or any transform) rearranges raw data into a space where each class
occupies a compact region. Instead of training a final layer to read that space,
we describe each class as a **box**: a per-dimension `[low, high]` range plus a
median. To classify a new point, we ask which boxes it falls inside and pick a
winner. That's it. Everything else in this document is about (a) doing that well,
(b) deciding *which dimensions* a class should care about, and (c) choosing the
*rule* for picking the winner. The deep idea underneath: an identity is just a
**unique bundle of distinctions**, and classification is **matching that bundle**,
not scoring a similarity.

---

## 1. Worldview (read this first — the rest won't make sense without it)

These are the principles the whole design serves. They are not decoration; each
one rules some implementation choices in and others out.

**1.1 Identity is relational, not positive.** A thing is defined entirely by what
it is *not*. There is no intrinsic "cat-ness" stored anywhere — there is only a set
of distinctions on which cats differ from non-cats. The label is the last and most
arbitrary thing added; permute every class name and nothing about the structure
moves.

**1.2 An identity is a bundle of distinctions, and the bundle is the unit.**
Write an id as a set of `(axis, value)` commitments: `{X1, Y1, Z1}`. Three rules
that the matcher must honor, and that ordinary "counting" violates:

- `X` is not `XY` — committing to one axis is a *different* id than committing to
  two, not a smaller amount of the same id.
- `Y` is not `XY` — neither parent is the child.
- `X and Y` *is* `XY` — the co-occurrence is its own symbol. The binding is the
  thing. You cannot read `X` back out of `XY` as a free-standing fact.

A **sum** cannot represent this (it's commutative and decomposable, so `XY`
becomes `X + Y = 2`, indistinguishable from any other two-hit pattern). **Sets**
can. This is why the final matcher is not a count.

**1.3 Significant digits.** When several ids match, report the **most resolved**
one — the one carrying the most committed distinctions that actually hold. A tabby
is `{striped, cat}`; a tiger is `{striped, big, cat}`. A tiger satisfies *both*
keys; you report tiger because it resolves further. `{striped, cat}` is the tiger
at coarser resolution — true, just fewer digits, like `5200 ft` versus `5201 ft`.
An unused axis is **unmeasured**, not zero.

**1.4 The only bias is resolution.** There is no per-feature weighting, no human
theory of what matters. The single unavoidable choice is the *grain*: how finely
you split before two values count as the same. That's it. Everything above the
grain is empirical — observed **usage**, not asserted **meaning** (the distribution
a thing actually occupies, not its dictionary definition).

**1.5 The transform need not be correct — only repeatable.** The system reads
*differences* off whatever space it's handed. A trained net, a random untrained net
(reservoir), tree-leaf indices, a hash — all are just difference-generators. The
only requirement is **determinism**: the same input must land at the same
coordinates every time. "Garbage to every other system" (a projection no head was
trained to decode) is perfectly good data here, because the differences are still
there and still stable. This is *demonstrated*, not assumed — see §9, reservoir.

---

## 2. The core algorithm (raw mode, no net)

Start here. This works on raw data with zero neural machinery and is the thing to
build first.

### 2.1 Quantize
Snap each feature to a small number of levels (default 16, i.e. "4-bit"). This sets
the grain from §1.4.

```
def quantize(X, lo=None, hi=None, levels=16):
    if lo is None: lo, hi = X.min(0), X.max(0)
    span = (hi - lo); span[span == 0] = 1
    Xq = np.round((X - lo) / span * (levels - 1))      # 0..levels-1
    Xq = Xq * (15 + 7) / (levels - 1) - 7              # map to roughly [-7, 8]
    return Xq, lo, hi      # keep lo/hi to quantize test data identically
```

> **Honest note.** A "DC stripping" step (subtract the global mean before
> quantizing) appears in some versions. It is a **provable no-op**: min/max
> quantization is shift-invariant, so subtracting a per-column constant cancels
> exactly. Don't bother with it; it does nothing.

### 2.2 Build one concept (box) per class
A concept is `{lo, hi, med}`, each a vector over features.

```
def build_concept(Xq_class, margin=1.5, plo=1, phi=95):
    lo  = np.percentile(Xq_class, plo, axis=0) - margin
    hi  = np.percentile(Xq_class, phi, axis=0) + margin
    med = np.median(Xq_class, axis=0)
    return lo, hi, med
```

Percentiles (not min/max) decide which points are "really" in the class versus
outliers; `margin` adds slack. **These are priors** — transparent ones you can see
and turn, unlike weights smeared across a matrix.

### 2.3 Score and classify (the naive rule — we replace it later)
For each concept count how many dimensions are in range; highest count wins, ties
broken by L1 distance to the median.

```
def classify_one(xq, concepts):
    best = None
    for c in concepts:
        inr   = (xq >= c.lo) & (xq <= c.hi)
        count = inr.sum()
        dist  = np.abs(xq - c.med)[inr].sum()
        key   = (count, -dist)
        if best is None or key > best[0]:
            best = (key, c.label)
    return best[1]
```

This is the **counting** matcher. It is the simplest thing that works and the wrong
thing in the end (§5). Build it anyway — it's your baseline and your sanity check.

---

## 3. Crystallization (putting a net in front)

Raw features are often tangled (no axis-aligned box separates the classes). A
trained net untangles them: each layer rotates/folds the space until, at the last
hidden layer, classes sit in compact, roughly axis-aligned clusters that boxes
*can* wrap. "Crystallizing" = building the box classifier on those hidden
activations.

```
hidden_train = extract(net, X_train)      # run net up to the LAST hidden layer
crystal = build boxes on quantize(hidden_train)
# inference:
hidden_x = extract(net, x)                # YOU STILL RUN THE NET
label = classify(quantize(hidden_x), crystal)
```

**Three honest points that contradict the marketing:**

1. **The crystal does not replace the net at inference.** You must run the net to
   get the hidden vector; the boxes only replace the final (tiny) linear layer. So
   the "10–100× cheaper inference" claim is true for **raw** and **reservoir**
   modes (no net or a cheap random net), **not** for crystallizing a trained net.
2. **It's net-agnostic.** The reader doesn't care what produced the vector —
   trained MLP, random net, RF leaves all work (§1.5).
3. **Retention is dataset-dependent.** ~99% of net accuracy on easy data (Iris,
   Wine, Digits); ~86% on a genuinely hard set (covtype). The easy datasets
   flatter the method.

> **Overstated theory to ignore.** Claims that "4 bits is a Shannon channel
> capacity" or "the count score is integrated information (Φ)" are not supported by
> the mechanism. 4 bits is just a grain that happened not to hurt on toy data; the
> count is a *sum of independent indicators*, which is the opposite of integration.
> Keep the mechanism, drop the metaphysics.

---

## 4. The scoring engine (vectorized, masked, GPU-ready)

The box test is `(x >= lo) & (x <= hi)` summed over dims — elementwise, no
cross-dim dependencies, embarrassingly parallel. Two rules:

- **Stream over concepts, vectorize over the batch.** Do *not* materialize the
  `(B, N, F)` membership tensor; it blows up memory and is slower on CPU than a
  Python loop. Loop the `N` concepts, vectorize the `B×F` comparison inside.
- **Carry a per-concept mask** `(N, F)` of `{0,1}`. The mask is the **committed
  set** — which axes this id is made of (§1.2). It multiplies into the reduction at
  zero cost. `mask = all ones` reproduces the dense behavior exactly.

```
for c in range(N):
    inr = (Xq >= LO[c]) & (Xq <= HI[c])        # (B, F)
    w   = inr * mask[c]                          # apply committed set, free
    count[:, c] = w.sum(1)
    dist[:,  c] = (abs(Xq - MED[c]) * w).sum(1)
```

**Performance reality:** for F < ~1000 this is tens of microseconds per sample on
CPU, microseconds on GPU. Selecting fewer dimensions buys **no** speed — the cost
is the net's forward pass, not the box step. Minimal dimensions matter for
*correctness of identity*, never for efficiency.

See `fastscore.py` for the reference implementation (`FastScorer`, `score_batch`).

---

## 5. The matcher (the decision rule) — this is where the worldview pays off

Three rules, in order of correctness. All operate on the *same* concepts and masks;
only the rule for picking a winner changes. Measured ranking on identical keys:
**average-difference ≥ deepest-key ≫ counting.**

### 5.1 Counting — WRONG, keep only as baseline
`score = #(committed dims in range)`, argmax. Fails all three identity rules:
`X→1`, `XY→2`, so `X` *is* `XY−1` (violates 1.2); `X and Y = 2` is indistinguishable
from any other two-hit pattern (the binding vanishes); and it **cannot compare keys
of different length** — an 18-digit id and a 9-digit id aren't rankable by total.
On variable-arity masks this collapses hard (covtype: 0.23).

### 5.2 Deepest satisfied key — bundle match + significant digits
A concept **fires** iff *all* its committed constraints hold (AND over the bundle).
Among firing concepts, the **most resolved** (most committed digits) wins. If none
fire, fall back to the one closest to firing (most committed constraints satisfied).
Honors §1.2 and §1.3. Brittle: one noisy axis vetoes the whole key.

```
fires_c   = (committed dims all in range)
resolved  = depth_c if fires_c else (#committed satisfied)
key       = fires_c * W2 + resolved * W1 - dist      # W2 >> W1 >> dist
```

### 5.3 Average difference — BEST tested rule
Per committed axis, the "difference" is how far the value lies *outside* the
accepted range (0 if inside). **Average** it over the committed set (do not sum).
Smallest average difference wins; ties (e.g. several keys fully contain the point,
avg 0) go to the most resolved; final ties to nearest prototype.

```
gap_c    = max(LO[c] - Xq, Xq - HI[c], 0)            # 0 inside, else outside distance
avgdiff  = gap_c[committed].mean()
key      = -avgdiff * BIGA + depth_c * BIGB - avgmed # avgdiff primary, then depth
```

Why it wins: averaging is **per-digit**, so keys of different length are comparable
(fixes counting's fatal flaw); and it's **graceful** where deepest-key is brittle —
a digit barely out of range nudges the average instead of vetoing the id. It still
keeps significant-digits behavior via the depth tiebreak. **Use this matcher.**

See `fastscore.py`: `score_batch` (counting), `score_batch_deepest`,
`score_batch_avgdiff`.

---

## 6. Co-activation (redundancy collapse + joint axes)

Hidden dimensions are not independent. Two mechanisms read the second-order
structure — which axes move together — from the same sampled reality.

### 6.1 Collapse redundant axes
If two axes co-vary the same way across all classes, they're **one factor counted
many times**. Measured: a 64-dim hidden layer had **effective dimensionality ~6**.
Fold correlated columns (|corr| ≥ threshold, connected components) into a single
mean-column so the score tallies *independent* differences. (Effect on accuracy is
small-to-neutral; its real job is honest counting.)

### 6.2 Joint axes (interaction features)
When a pair co-activates **class-conditionally** (fires together for some classes,
not others), the pattern itself is discriminative — and a sum of marginals *cannot*
encode "both-or-neither." Append a derived **interaction feature** (centered
product `(a-ā)(b-b̄)`, or `min(a,b)` for a soft-AND) as a new axis. This makes `XY`
a first-class symbol (§1.2) and is the principled way axis-aligned boxes get at
diagonal/interaction structure.

**When joints help:** entangled/raw data where single axes don't separate. On a
constructed XOR problem in raw mode, dense boxes sit at chance (0.50); adding the
one detected joint axis lifts it to 0.76, and selection then keeps only that axis.
**When they don't:** after a trained net has already disentangled the data (covtype:
+0.003). A good net does the binding for you; joints are held in reserve for when it
hasn't.

See `concept_pipeline.py`: `collapse_redundant`, `joint_axes`.

---

## 7. Selection (which distinctions an id commits) — the current frontier

The mask **is** the identity: it names the axes a concept is made of. Choosing it
well is the open problem. The hard-won lessons:

**7.1 Select for held-out generalization, NOT training separation.** A rule that
greedily picks axes to exclude every other-class *training* point (set-cover on the
training set) overfits catastrophically — covtype **0.72 → 0.17**. The *same*
minimal-dims idea aimed at **held-out accuracy** preserves it: covtype held accuracy
while cutting 64 axes to 21. The objective must be *minimal, unique, and stable*
(recurs out of sample). Stability is the word that matters.

**7.2 Per-concept arity.** Different ids need different numbers of digits (tabby: 2,
tiger: 3). A shared global mask abandons this; per-concept selection restores it.
The current per-concept rule (`per_concept_resolution_mask`, recall − leakage)
works but commits *too many* sprawling digits (mean ~14), which drags every matcher
below the dense baseline. **It is the current bottleneck, not the matcher.**

**7.3 The next experiment (unfinished — do this).** Co-design selection *with* the
average-difference matcher: greedy forward selection on a validation split, scored
by `predict_q_avgdiff`, adding a digit to an id only when it raises held-out
resolution accuracy, stopping early. This is the one change standing between
"validated on equal keys" and "beats the dense baseline end to end."

See `concept_pipeline.py`: `greedy_holdout_mask` (global, accuracy-preserving),
`per_concept_resolution_mask` (per-id, current bottleneck),
`sample_separation_mask` (kept only to reproduce the overfitting failure — do not
use).

---

## 8. Build order (from zero to refining)

1. **Raw box classifier** (§2): quantize → build_concept per class → counting
   matcher. Test on Iris/Wine. Target ~0.9+. This proves the core.
2. **Vectorized engine** (§4): `FastScorer` with an all-ones mask. Verify it
   reproduces step 1 *exactly* (parity check). Now you can score any mask fast.
3. **Crystallization** (§3): train an MLP, extract the last hidden layer, build the
   crystal on it. Confirm ~99% retention on easy data.
4. **Better matchers** (§5): add deepest-key and average-difference. Confirm
   avg-diff ≥ deepest ≫ counting on variable-arity masks.
5. **Co-activation** (§6): redundancy collapse + joint axes. Confirm joints rescue
   a synthetic XOR in raw mode.
6. **Selection** (§7): held-out global mask first (preserves accuracy at far fewer
   axes), then the per-concept co-design (the open frontier).
7. **Refine** (§10): always against a *harder* dataset than the toy four, always
   reporting both accuracy and mean digits-per-id.

---

## 9. Empirical results to reproduce (your regression suite)

| Finding | Number | Meaning |
|---|---|---|
| Crystal retention, easy data | ~99–100% | boxes read a well-arranged space |
| Crystal retention, covtype | ~86% (0.72 vs net 0.84) | hard data gives up more |
| Hidden effective dimensionality | 6.3 of 64 | counting double-counts ~10× |
| Digit class pairs separable by 1 axis | 45/45 at AUC≥0.99 | minimal keys are feasible |
| Held-out selection, covtype | 64 → 21 axes, no loss | minimal-dims works (held-out) |
| Training-separation selection | 0.72 → 0.17 | the overfitting trap (avoid) |
| Joints on XOR (raw) | 0.50 → 0.76 | interaction features work |
| Joints on covtype (post-net) | +0.003 | net already disentangled |
| Matcher ranking (equal keys) | avgdiff ≥ deepest ≫ counting | the worldview, on the board |

Reservoir (random untrained net as the transform) classifying above chance is the
key qualitative result behind §1.5 — reproduce it to convince yourself the
transform need only be repeatable, not correct.

---

## 10. Known limitations & open problems

- **Axis-aligned only.** A single box can't trace a diagonal boundary. Joints and
  extra variant-boxes patch it, at a cost to minimality/interpretability.
- **High dimensionality (≈768+) degrades** the raw method; boxes overlap. Crystallize
  through a net first, or collapse aggressively.
- **Selection/matcher co-design is unfinished** (§7.3). This is the live frontier.
- **Variant explosion.** A naive confusion-resolution loop can emit duplicate
  concepts forever; dedupe and require each variant to actually reduce held-out
  confusion.
- **Brittleness vs grain.** Strict bundle-matching needs the grain (quantization,
  margin) to absorb noise, or single-axis violations veto correct ids. Average
  difference mitigates this; per-axis grain would help more.
- **Don't trust the toy four.** Iris/Wine/BreastCancer/Digits hide every hard
  problem. Validate on covtype, Fashion-MNIST, or a controlled interaction set.

---

## 11. Module map

| File | Contains |
|---|---|
| `range_classifier.py` | core boxes: `quantize`, `build_concept`, `RangeClassifier`, `CrystalClassifier`, extractors (`extract_sklearn_mlp`, RF leaves) |
| `fastscore.py` | vectorized engine + all three matchers: `FastScorer`, `score_batch` (counting), `score_batch_deepest`, `score_batch_avgdiff` |
| `concept_pipeline.py` | `collapse_redundant`, `joint_axes`, selection rules (`greedy_holdout_mask`, `per_concept_resolution_mask`, `sample_separation_mask`), `build_general_concepts` |
| `verify_fastscore.py` | parity check (all-ones == shipped) + sparse-mask measurement |
| `experiment_harder.py` | XOR (raw) + covtype (crystal) ablation: collapse / joints / selection |
| `experiment_matcher.py` | counting vs deepest-key vs average-difference, head to head |

---

## 12. The shortest correct summary

Build a transform that maps the same input to the same vector every time (anything
deterministic — trained, random, borrowed). Describe each class as a box on the
axes that actually distinguish it — a **bundle of distinctions**, of whatever arity
it needs. Match a new point to the id whose bundle it best satisfies, scored by
**average difference** so that keys of different length compete fairly and a single
noisy axis doesn't veto a true id, breaking ties toward the **most resolved** id.
Select the bundles for **held-out stability**, not training fit. Everything else —
quantization, collapse, joints, the engine — is in service of those sentences.
