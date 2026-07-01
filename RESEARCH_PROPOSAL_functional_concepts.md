# Functional Concepts: Lossless, Generalizing, Legible Recognition
### A research proposal with preliminary results — draft for external review

**One-line thesis.** Represent a concept not as a stored pattern, a statistical
average, or an axis-aligned region, but as a **fitted functional form** (a
parametric function) whose **relations to other forms are themselves functions**
carried on the edges of a knowledge graph. Recognition is *fitting the form and
reading the residual*. We argue — and give preliminary evidence — that this
representation is simultaneously **general, lossless, and legible**, and that the
recurring failures of region/average-based recognition are failures of
information-destroying operations that a functional representation avoids.

> **Status and honesty note.** This document mixes (a) a principle and
> architecture we are confident in, (b) small-scale preliminary experiments on
> standard and synthetic data that we report with exact numbers including
> negatives, and (c) clearly-labelled *hypotheses* and *open problems* we are
> proposing to test. We have tried to keep these three categories visibly
> separated so the proposal can be evaluated fairly. The implementation substrate
> is an existing gradient-free, graph-based symbolic learning engine (internally
> "Isaac"); the proposal is largely substrate-independent.

---

## 1. Motivation: a common failure mode is information destruction

Across a range of recognition tasks we observe the same failure, and it has a
single shape — a *lossy* operation discards exactly the structure that carried
the signal:

- **Averaging / mean-squared error.** The average of a structure is its
  *anti-structure*: the mean colour of a rainbow is grey. An average-based matcher
  therefore scores the *least* rainbow-like object (a featureless grey patch, the
  centroid) as a strong rainbow, while a real but transformed rainbow (inverted,
  double-banded) scores *lower* because its sharp features produce zeros that drag
  the mean down. "Present but displaced" is more diagnostic than "technically
  close to the mean," yet averaging rewards the opposite.
- **Binning / quantization.** Mapping continuous values to discrete bins discards
  *proximity* — "how close" — keeping only "same bin or not." On a benchmark whose
  signal lives in continuous relationships (high-energy-physics event
  classification), an exact-match engine on binned features degenerated to chance
  because the relational/proximity information had been destroyed before it
  arrived.
- **Axis-aligned regions (boxes).** A box can only describe a circle as its
  bounding *square*. A circle and a square of equal extent have the *identical*
  bounding box, so no range/membership/count method can distinguish them. The box
  is blind to *form*.

The unifying observation: **every one of these is a compression that throws away
the details, and the details are the information.** The remedy we propose is a
representation in which the relationship, the transformation, and even the noise
are *parameterised and kept* rather than averaged away.

---

## 2. Core hypothesis

> **H1 (representation).** A concept is well represented as a parametric
> **functional form**; a relation between concepts is itself a **function on the
> graph edge** linking them. This representation is *general* (one form covers all
> instances), *lossless* (form + parameters reconstruct the instance), and
> *legible* (the form and its parameters are human-readable).

> **H2 (recognition).** Recognition is **fitting the form and reading the
> residual**, with a **presence-primary** decision rule: how many of a concept's
> committed constraints are satisfied is primary; closeness (distance to the
> prototype) is a secondary tiebreak; the two are *never blended into an average*.

> **H3 (discovery).** A system can *find* such structure autonomously via a
> **residual-driven loop**: fit known forms, treat the residual's remaining
> structure as the next form/relation to fit, keep only forms that beat chance
> (a multiple-comparisons-corrected "surprise" gate), and terminate when the
> residual is noise. *(This is the principal hypothesis we propose to test; it is
> not yet demonstrated.)*

---

## 3. The principle: generalise by fitting, not by averaging

Three ways to represent a concept trade generality against information:

| representation | general? | lossless? | example failure |
|---|---|---|---|
| region / box (averages a class to a range) | yes | **no** | square ≈ circle (same bbox) |
| instance / lookup (keeps every example) | **no** | yes | no abstraction; memorises leakage |
| **functional form (fit a parametric function)** | **yes** | **yes** | — |

A function generalises *parametrically* — ten circles of different sizes are not
averaged into a blurry ring (the grey trap) but captured as `circle(centre,
radius)` with the radius varying. This resolves the generalisation-vs-memorisation
tension that region and instance methods sit on opposite horns of, and it does so
without averaging. Recognition becomes the **null method / registration**: fit the
form (the instrument), read the residual (the difference) — the same principle as
interferometry, vernier acuity, and stereo disparity.

---

## 4. Preliminary results

Small-scale, on standard and synthetic data. Exact numbers, negatives included.
Scripts are available (`feature_math.py`, `relational.py`, and the matcher/mask
benchmarks).

**4.1 The presence-primary matcher is a minimal-key classifier.** With a held-out
axis-selection mask and the count-primary / distance-secondary rule (no
averaging), accuracy is preserved at a small fraction of the dimensions:

| dataset | dense acc (dims) | held-out acc (dims) |
|---|---|---|
| Iris | 0.978 (64) | 0.978 (**1**) |
| Wine | 1.000 (64) | 1.000 (**2**) |
| Breast-cancer | 0.947 (128) | 0.947 (**2**) |
| Digits | 0.963 (64) | 0.920 (**7**) |

*Honest negative:* on forest-cover-type (high-order, spatially-autocorrelated),
the dense box reads 0.638 and the held-out mask *collapses* to 0.529 at 5 dims —
because the signal is *distributed*, so cutting dimensions destroys information.
This is the principle confirmed from the failure side: dimension-selection helps
only when the discarded dimensions are genuinely redundant.

**4.2 Forms generalise across scale and position, and see what boxes cannot.**
A form recogniser (circle = "equidistant from a fitted centre"; line = "minimal
perpendicular spread") with **no training and no stored coordinates** reached
0.97 overall (circles 1.00 after a proper least-squares centre fit; lines 0.99),
recognising shapes at arbitrary scale and position because the form is invariant
and only its parameters move. The sharp control: a circle and a square at the same
centre and extent have the **identical bounding box** (any region method sees them
as one object), yet the form residual is 0.000 vs 0.121.

**4.3 Relations distinguish same-component concepts.** "8 = two circles, aligned
and touching" vs "∞ = two circles, touching but side-by-side": identical
components, identical "touching," differing *only* in the alignment axis. Given
the component forms, relational recognition (equations between the circles'
parameters: `dist = r₁+r₂`, `Δx=0` vs `Δy=0`) reached **1.000** across
{8, ∞, separated, overlapping, single-circle}.

**4.4 The honest bottleneck is perception, not the relation.** Recovering the
component forms from a *raw merged point cloud* (segmentation / direct form
detection) is hard: naive 2-means scored 0.49 and a RANSAC attempt 0.21 on
touching/overlapping circles. The relational logic is trivial *given* the
components; *finding* the components is the work. This matches every other
front-end in our experience (region→requires a good linear lens; pixels→require
clustering into visual words; vision→requires a trained encoder).

---

## 5. Proposed architecture

### 5.1 Functions on doors
A graph edge ("door") stops meaning "A relates to B" and becomes
`A —f(θ)→ B`, carrying three readings at once:
- **the function's *type* is the relationship** — positive slope = correlation,
  negative = inverse, threshold = inequality, step = step-dynamics, etc.; the
  qualitative families (absolute / signed / relational) are just function classes;
- **the function's *parameters* are the specifics and the transforms** — offset,
  scale, alignment; scale-invariance is automatic because the form is fixed and
  only the parameter moves;
- **the residual becomes a *variance function*** (§5.3).

### 5.2 The matcher (validated, §4.1)
Presence-primary: count of satisfied committed constraints first, distance to
prototype as a secondary tiebreak, never averaged. Concepts of different arity are
compared on *which/how-many* constraints fire, with a "fires only if all committed
constraints are satisfied, else most-satisfied" (significant-digit) rule for the
length-fair case. This is the only combination rule consistent with a
padded/partial/scaled/composed representation (a missing part lowers the count by
one; padding contributes nothing; matches accumulate up a hierarchy) — averaging
breaks under each of these.

### 5.3 Variance as a function (model the noise, do not average it)
The residual after a fit is not discarded; it is represented as a parametric
**variance field**: variance ≈ 0 at the form, growing with distance, with a
*direction vector*. A blurry circle is not "a worse circle" but "a circle with
radial variance σ"; a smeared one carries directional variance. This applies the
no-information-destruction principle to the one place that always forced averaging
(noise), and it recovers the registration claim that *the residual is a field
whose shape names the transform* (radial variance = scaling; directional = motion).

### 5.4 Transforms as parameters unify perception modules
If a door between two *views* of a scene carries a registration function, its
**shift parameter is binocular disparity (hence depth)** and its **scale parameter
is zoom**. Stereo depth, parallax, and zoom are not separate modules but
parameters read off one door-function — a concrete, testable consequence.

### 5.5 The form-fitter front-end ("the math retina")
Converts continuous input into form-glyphs-with-parameters: detect centres and
edges; fit a small library of functional primitives (linear, radial, quadratic,
periodic, sigmoidal…); accept a fit via the residual. Spatial relations
(spaced/touching/overlap) are *derived* from centre + edge geometry rather than
hand-coded. Robust direct fitting (Hough-style voting, RANSAC, sequential
fit-and-remove) is the key engineering problem (§4.4, §9).

### 5.6 The discovery loop (H3)
`fit known forms → read residual → residual's structure proposes the next form/
relation → keep forms that beat chance (surprise-gated, multiple-comparison
corrected) → repeat until the residual is noise.` The data is finite, so the loop
terminates; "no form fits" is not failure but the trigger to compose or search.

### 5.7 Integration with a symbolic graph substrate
Forms are concepts (nodes); relations are doors carrying functions; recognition
reuses the existing presence-primary matcher; a recurring fit is *crystallised*
into a node exactly as recurring symbolic patterns already are. The substrate's
co-occurrence structure *guides* the search (fit relations between features that
already co-occur), keeping the otherwise-combinatorial search tractable. Net
effect: feature-math is a new *vocabulary* (a mathematical language) for machinery
the substrate already has for language.

### 5.8 Gradient descent over a symbolic basis (fit the mechanism, not the surface)
The objection is not to gradient descent but to the *space* it is pointed at. A
standard network parametrises a space of piecewise-linear **result surfaces**; the
same optimiser, pointed at a space of **equations**, refines the mechanism. Two
changes suffice, and they are exactly the two that separate a mechanism from a
table: (i) **replace the primitive** — swap the universal `linear + fixed
nonlinearity` unit for a *menu of mathematical primitives* (the form library of
§5.5 as the activation set), so the network is itself a parametric equation;
(ii) **add sparsity** — an L1 penalty forces the optimiser to commit to a *few*
terms (a mechanism) rather than smear across *many* (a table) — the differentiable
form of the presence-not-average rule (§5.2). Gradient descent then refines *which
terms are present and their coefficients*. Fitting a fixed form's parameters is
ordinary nonlinear least squares; selecting structure over the basis is sparse
regression. This is an established line — **SINDy** (sparse identification of
nonlinear dynamics) and **Equation-Learner networks (EQL)** — whose hallmark is
**extrapolation**: a recovered equation generalises *beyond* the training range
where a result surface flatlines. Honest limits: parameter fitting is robust, but
structure selection is non-convex and **bounded by the primitive library**, and
deeply *nested* mechanisms remain the frontier. The corrected position is not
"avoid gradient descent" but **"point gradient descent at equations, not surfaces,
and make it commit"** — so the form fitter (§5.5) and discovery loop (§5.6) may
*use* gradient descent as their engine, over a symbolic basis with sparsity.

---

## 6. Falsifiable predictions

1. On tasks whose signal is a continuous functional relationship (e.g.
   invariant-mass-style constructed features), a form/relation recogniser will
   *substantially* beat a binned exact-match or axis-aligned region method at
   equal interpretability, and approach a trained net at far higher legibility.
2. Form recognition will be **scale- and position-invariant with zero retraining**
   and far more **sample-efficient** than a CNN on shape/relational tasks
   (predicted: order-of-magnitude fewer examples).
3. The **disparity-as-door-parameter** claim predicts metric depth can be read off
   the registration parameter between two views without a trained stereo network.
4. The discovery loop will **recover known generative forms** (e.g. the functional
   relations physicists hand-engineer) from raw features *unsupervised*, and will
   *fail gracefully* (abstain) where no low-order functional structure exists —
   not hallucinate one (surprise-gating is the test).
5. **Mechanism recovery + extrapolation (§5.8).** Gradient descent over a sparse
   symbolic basis, fit to datapoints sampled in a bounded range, will recover the
   generating equation and **extrapolate beyond that range**, whereas a
   same-capacity MLP fit to the identical points tracks the data inside the range
   and **diverges outside it** — it learned the surface, not the rule.

A clear *negative* prediction: on genuinely high-order, distributed-signal data
with no exploitable low-order functional/parametric structure (the cover-type
regime in §4.1), this approach will *not* beat ensemble trees, and aggressive
form/dimension selection will hurt. We state this to make the proposal falsifiable
and to bound the claim.

---

## 7. Evaluation plan

- **Tasks.** (a) Shape/form recognition across scale/position/noise; (b)
  relational concepts with shared components (8 vs ∞ vs …); (c) tabular sets with
  planted functional relations (linear, quadratic, threshold, interaction) and
  controls with none; (d) a leakage-free split of a hard tabular benchmark; (e)
  two-view depth from disparity-as-parameter.
- **Baselines.** Random forest, gradient-boosted trees, MLP, linear probe, kNN,
  CNN (vision), and our own region/box and instance/lookup variants.
- **Metrics.** Accuracy; **dimensions/parameters used** (legibility proxy);
  **sample efficiency** (accuracy vs training size); **generalisation gap** across
  held-out scales/positions; **abstention calibration** (does it correctly say "no
  form" when there is none); **human-readability** of the recovered forms.
- **Controls (learned the hard way).** Use leakage-free / spatial-CV splits for
  any "honest learning" claim; never substitute an external learner (e.g. a random
  forest) for the system under test and report it as the system's result; report
  all negatives.

---

## 8. Related work (positioning)

- **Conceptual spaces** (Gärdenfors): concepts as convex regions in low-dimensional
  quality spaces. We extend "region" to "fitted functional form," and make the
  inter-domain relations explicit functions.
- **Symbolic regression / equation discovery** (Eureqa; SINDy; PySR) and **program
  synthesis** (DreamCoder): our discovery loop is a graph-resident, residual-driven
  variant; the novelty we claim is the *integration with a recognition substrate*
  and the presence-primary, variance-as-function reading, not symbolic regression
  per se.
- **Capsule networks / part-whole + pose** (Hinton et al.): "pose" is our
  parameter vector and "agreement" our relational equation; we propose an
  explicit, fittable, gradient-free version.
- **RANSAC / Hough transforms**: the direct form-detection front-end (§5.5).
- **Sparse coding / dictionary learning / single-layer unsupervised features**
  (Coates & Ng): a precedent for "fit a small learned vocabulary, read it cheaply";
  we replace patch atoms with parametric forms.
- **Instance- vs parametric-based learning**, and **range/box classifiers**: the
  generality/losslessness trade in §3.
- **Predictive coding / analysis-by-synthesis**: recognition as residual after
  registering a model.
- **The null method / hyperacuity** (interferometry, vernier acuity, stereo): the
  recognition-as-registration claim.

The contribution is not any single one of these but the **synthesis**: relationship
*type*, transformation *parameters*, and *variance* unified as one fittable
function on a graph edge, read by a presence-primary (non-averaging) matcher,
discovered by a residual loop.

---

## 9. Open problems and risks (stated up front)

1. **The perception front-end is the bottleneck (§4.4).** Robust, autonomous form
   detection from raw input is unsolved in our prototypes and is the same wall that
   has blocked every front-end we have built. This is the highest-risk component.
2. **Search combinatorics.** Which forms, over which feature subsets, in which
   relations — guided search (via the substrate's co-occurrence) is proposed but
   unproven at scale.
3. **Primitive coverage.** A fixed primitive library + composition covers much,
   but *inventing* new primitives is symbolic-regression-hard; we may be bounded by
   the library.
4. **Scope.** The approach targets data with exploitable low-order
   functional/parametric structure; we predict (and have one data point that) it
   will *not* dominate on high-order distributed-signal data.
5. **Overfitting forms.** Without a correct surprise/multiple-comparison gate, a
   rich form library will "find" structure by luck; the gate is load-bearing and
   must be validated.

---

## 10. Implementation milestones

1. **Form library + robust fitter** (the math retina): primitives, RANSAC/Hough/
   sequential fitting, residual-as-variance. *Deliverable:* form recognition that
   survives §4.4's perception bottleneck on cluttered scenes.
2. **Forms and functions on doors in the substrate:** node = form, door meta =
   `{function, parameters}`; recognition via the existing presence-primary matcher.
3. **Relations from centre+edge detection:** derive spaced/touching/overlap and
   alignment automatically; reproduce §4.3 from raw input rather than given
   components.
4. **The discovery loop (H3):** residual-driven, surprise-gated, finite-terminating;
   evaluate falsifiable prediction 4 (recover planted forms unsupervised; abstain
   where none exist).
5. **Two-view depth** from disparity-as-parameter (falsifiable prediction 3).
6. **Full evaluation** (§7) against all baselines, reporting negatives.

---

*Prepared as a draft for external validation and review. We invite scrutiny
especially of §4 (do the preliminary numbers hold up and are the baselines fair?),
§6 (are the predictions genuinely falsifiable?), and §9 (is the perception
bottleneck fatal or merely hard?).*
