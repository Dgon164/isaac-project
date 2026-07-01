# Isaac — Project Overview

*A complete structural picture: what Isaac is, how he works, what's proven,
what's open, and where we're going. Written to be handed to collaborators.*

*Status date: June 2026. Engine verified green at time of writing (6/6 core
capabilities, 7/7 pipeline phases).*

---

## 1. What Isaac is, in one paragraph

Isaac is a symbolic learning engine — closer to classical (GOFAI) AI than to a
neural network — built on a single operation: **forming connections between
elements based on the differences between them.** Elements ("nodes") are linked
by "doors" (directed edges). The system observes sequences, discovers which
elements play the same relational role (crystallizes them into *types*), and
routes/predicts by following doors. The one idea borrowed from neural nets is
that the connections are **grown from data rather than hand-authored**, with
information-theoretic difference deciding what's worth keeping. Everything else —
language, math, logic, reasoning, and now perception — grows from that one
mechanism applied to different kinds of elements.

The guiding slogan: **feed it data, it figures it out.**

---

## 2. The core thesis

Stated plainly, after extensive work this session:

> **Isaac differentiates. Everything else is a question of *what field* you point
> the differentiation at, and *at what scale*.**

A door is a difference between two elements. The engine does nothing but find,
store, type, and follow differences. Crucially this is substrate-agnostic — the
same machinery that found word-types from text finds shape-roles from pixels,
because "difference between elements in a structure" doesn't care whether the
elements are words, numbers, concepts, pixels, objects, or whole video frames.

This is a **holonic** view: a frame is a whole made of parts (pixels); each part
can be a whole made of parts; "difference between parts" is one operation that
runs at every level — pixel-to-pixel, object-to-object, frame-to-frame. The
engine composes upward for free: pixels crystallize into shapes, shapes relate to
shapes, the same way tokens crystallize into types and concepts relate to
concepts.

---

## 3. How he works (architecture)

### 3.1 The substrate
- **Nodes**: elements (tokens, numbers, pixels, whatever is observed).
- **Doors**: directed connections between nodes, tagged by relation type.
- **Types**: groups of nodes that share a relational profile (same
  predecessors/successors), discovered automatically via Formal Concept Analysis
  (FCA) closure. This is how "cat" and "dog" become "animal," and how an edge-cell
  and another edge-cell become "edge."

### 3.2 The operations (the "Sections" / pipeline)
The engine runs a five-stage pipeline modeled loosely on brain anatomy:

1. **Sense** (sensory cortex) — new elements slotted into existing types on
   observe.
2. **Store** (hippocampus) — observe lays down doors; dirty-tracking marks what
   changed.
3. **Route** (thalamus) — queries follow doors; lazy auto-compile on first query.
4. **Evaluate** (prefrontal) — a think-loop: recall → process → evaluate, looping
   until stable. Diagnoses *why* a query failed and retries informed, rather than
   brute-forcing.
5. **Act** (motor cortex) — commit gate for output.

Two operating modes: **active** (real-time, small working set, cheap) and **idle**
(consolidation / crystallization of everything that changed — effectively
"sleep," where types are formed and the graph reorganizes).

### 3.3 What this buys
The same engine demonstrably does language (observe/generate/type-infer), math
(tables + decomposition, scales to large numbers via decomposition), logic (truth
tables, compound expressions), reasoning (is-a chains, inheritance with override,
syllogisms), and problem-solving (forward/backward/gap-fill). All verified.

---

## 4. The constraint that defines the project ("Rule 1")

This is non-negotiable and shapes every design decision:

> **We give Isaac data and answers. We never give him the method. He makes an
> attempt, compares it to the answer, and learns from the difference.**

Concretely: no feature extractors, no hand-written `see()`/`centroid()`/`decide()`
functions that compute the answer and hand it over, no pre-digested tokens, no
preprocessing beyond presenting the raw field. Feature extraction is something
Isaac *learns*, never something we install. We are allowed to *generate correct
answers to teach with* (a teacher knows the answer); we are not allowed to compute
the answer at inference and pass it off as his.

The corollary that emerged this session: **if he can't perceive it, he cannot
learn it.** Perception is upstream of everything. The allowed kind of "adding" is
giving the input a form the existing engine can perceive (a perception transform).
The disallowed kind is bolting on new behavior logic or rules. Rule of thumb: *if
a fix needs you to modify a lot or add rules, you're doing it wrong.*

---

## 5. What we give him vs. what is his

A clean architectural split crystallized this session:

**Wired — free, given (his "retina"):**
- Difference operators over a field. These are cheap and, on a GPU, essentially
  free (map ops, convolution, optical-flow hardware). Biology doesn't count the
  retina's edge-detection as cognition; it's wiring. Same here.
- Two sensory primitives specifically: **differentiation** (difference between
  elements) and **baseline** (the reference to difference against).

**Learned — his, grown from data:**
- What the differences *mean*.
- Shape, identity, object tracking (same-thing-over-time), counting, segmentation,
  and ultimately reasoning about what's seen.

The job is narrow: **deliver difference + baseline into the net in a form he can
grow on, and get out of the way.** He does the rest.

---

## 6. The perception layer (current design)

Perception decomposes into four channels — one operator pointed at four different
references:

| Channel | Differences against | Gives | Cost |
|---|---|---|---|
| **Global** | the baseline (what's normal here) | figure/ground, steady-state, the salience inversion | trivial (pixel-parallel) |
| **Local** | your neighbors | edges, shape, corners, tips | cheap (convolution) |
| **Shifting** | your own previous state | motion, change, onset/offset | cheap (optical flow; HW on GPU) |
| **Attention** | — (readout) | where the deviation is biggest | reduction over the field |

**Attention is not a fourth measurement** — it's the normalized magnitude of the
other three pooled together. Where the model is weak, attention pools; where the
baseline has absorbed something, attention drains off it. This matches biology
(center-surround = local, adaptation = global, motion-selectivity = shifting,
salience = the pooled readout) and maps onto GPU primitives almost one-to-one.

**Global is settled and cheap** (validated this session): a dual overlay — a
per-cell rolling average (temporal baseline) plus a field-relative term (spatial
baseline). One multiply-add and one comparison per pixel; ran 500×500 in ~3ms on
CPU, trivial on GPU. It tracks "normal," fades furniture (acclimation), isolates
deviation, and inverts figure/ground as field statistics flip. The only knob is
the adaptation rate (how fast "new" becomes "normal").

**Key empirical finding on getting differences into the net (holon test):** the
existing crystallizer *does* form shape-roles from pixels with **no encoder and no
new code** — but only if the difference is a **vector (direction), not a scalar
(magnitude).** "How many neighbors" (a count) is too flat: everything merges into
one type. "*Which* neighbors" (a direction) is rich enough: distinct roles
(edges, corners, tips) crystallize apart. The difference must keep its direction.

---

## 7. The dimensional space (what perception must cover)

Being fastidious about completeness, the things representable in a visual space
factor into four spatial families, and **time differentiates every one of them**
(each spatial dimension gets a rate-of-change twin once frames exist):

- **Location** — x, y (and depth z in 3D).
- **Framing** — rotation, scale, reflection/chirality, shear. (This is the affine
  group; it is closed — those four are the complete set of rigid re-framings.)
- **Identity** — topology (open/closed, holes, # pieces — the invariant core),
  fill (outline vs solid), contrast/polarity (figure/ground, "inverted"), and
  local part-roles (corner/edge/tip/junction/curve).
- **Inter-object relations** (require >1 object) — relative position
  (above/below, inside/outside), relative size (bigger/smaller), containment,
  adjacency, alignment, count.

Two honest complications that are load-bearing for the curriculum:
1. **Representable ≠ recoverable.** Some dimensions are ambiguous from a single
   flat frame (bigger-vs-closer = scale vs depth; sheared-square vs
   rotated-in-3D). These need motion or stereo to disentangle. We must decide per
   dimension whether he can *perceive* it or merely *represent* it.
2. **Signal vs. nuisance is a per-dimension choice.** "Rotated" can mean "detect
   the rotation" (signal) or "recognize the shape despite rotation" (invariant).
   The right handling differs by task (rotation matters for letters, not for
   balls). Tagging each dimension signal-vs-nuisance is half the curriculum.

*(A full enumerated table with these tags is the proposed next spec document.)*

---

## 8. Session work log — what was tested, and the honest result

Every item below was run; results are reported with seams marked.

| Experiment | Result | Honest caveat |
|---|---|---|
| Counting (single-shot lookup) | **Fails to generalize** (23% on novel grids ≈ chance) | Memorizes (100% train); global sum has no aggregation operator |
| Counting (sequential tally walk) | 100% on novel grids | The walk was driven by an external loop — *not* clean; behavior was the harness's, not Isaac's |
| Recognition (recall + noise) | Works; 5/5 recall, robust to 1–2px flips | Small distinct set; only pixel-noise tested, not movement |
| Localization across translation | **Center fails** (0% novel), size partial (67%) | Coordinates memorize; the core wall |
| Relative vs absolute target | Relative **generalizes 100%**, absolute 0% | Fixed size made the relative answer constant — proves the principle, not full localization |
| Extraction / normalization | Works; one object → identical crop from 50 positions/scales | Single object only (multi needs flood fill); keeps size (scale not normalized); on-bit collection still a numpy seam |
| Occlusion / partial match | Works; occluded X gracefully ties `\` | Voting favors bigger shapes; needs normalized input |
| Locate-by-difference at scale | **100% at 10×10, 100×100, 500×500** | Comparison + Isaac's arithmetic scale; corner-read still a numpy seam; surfaced an arithmetic memoization bug |
| Global baseline | Validated: tracks normal, fades furniture, inverts, ~3ms @ 500×500 | Adaptation-rate knob is live |
| Holon test (pixels → crystallize) | Types crystallize **with no encoder**, IF difference is directional | Messy at tiny scale; not proven clean at scale |

**Bugs found:** arithmetic memoization keys on trailing context, so repeated
operands (`x + 1`) return the first cached answer — corrupts arithmetic until
isolated/disabled. Capabilities sharing one net cross-talk through shared tokens.
Both worth fixing in `isaac.py`.

---

## 9. Goals

1. **Near-term:** give Isaac a working perception layer — difference + baseline
   delivered into the net relationally — so he can perceive the dimensions in §7.
2. **Mid-term:** he learns to *do* things with that perception — shape, motion,
   tracking, counting, segmentation — via the attempt/compare/learn loop, taught
   by classical algorithms acting as answer keys (not as installed code).
3. **Long-term / bootstrap:** Isaac is designed to **self-update once he can build
   code** — modify and extend his own structure. The real success criterion is
   therefore not "passes any single benchmark" but **"has enough composable
   primitives that *he* can assemble the next capability himself."** This argues
   for a small, orthogonal, composable primitive set over maximizing any one
   behavior.

---

## 10. Recurring open problems (the honest frontier)

These are not "the architecture can't" — they're "not yet built." They recur
across nearly every task:

1. **Traversal-with-memory** (flood fill / walk-and-remember). Needed for
   segmentation, counting touching things, line-length, curve-radius, object
   tracking. The one primitive lookup doesn't natively do. **Open decision:** is
   the walk learned, or scaffolded around judgments he *does* learn?
2. **Object tracking / identity-over-time.** Correctly on the *learned* side —
   it's the first genuinely semantic act (deciding two appearances are one thing).
   To be built as a predictive curriculum, not a kernel.
3. **Scale normalization** — so recognition is size-invariant, not just
   position-invariant.
4. **The arithmetic/contamination bugs** (§8).
5. **The predictive baseline** — the richest version of global, where prediction
   (not just a running average) makes expected change boring and unexpected change
   loud. The "head loud, tail quiet" asymmetry needs this.

---

## 11. Decisions needed before the next build phase

1. **Connectivity: 4- or 8-connected?** (bakes into every local patch and into
   flood fill)
2. **The walk: learned or scaffolded?**
3. **Per-dimension tags** (§7): which dimensions are signal vs nuisance, and which
   are recoverable from a single binary frame vs need time/stereo.
4. **First perception brick:** local directional difference (the holon result
   points here) vs. the shifting/motion channel.

---

## 12. File inventory (current)

**Engine & infrastructure**
| File | Lines | Purpose |
|---|---|---|
| isaac.py | 1,672 | Unified engine (nodes, doors, types, pipeline). Verified 6/6, 7/7. |
| test_pipeline.py | 501 | Pipeline phase tests (7/7) |
| test_visual.py | 412 | Visual delta-pipeline benchmarks (frame delta, region attention) |
| app.py / launcher.py / build.py | ~450 | Flask GUI, launcher, packaging |
| snake.py | 170 | Snake testbed (1s and 0s, four buttons) |

**This session's perception experiments**
| File | Lines | Purpose |
|---|---|---|
| global_baseline.py | 143 | Global channel — validated, cheap |
| holon_test.py | 155 | Pixels → crystallize; directional-difference finding |
| shapegen.py | 112 | Labeled-shape generator (the data engine) |
| extract_object.py | 90 | Object extraction / normalization |
| predict_compare_locate.py | 126 | Locate-by-difference, 100% to 500×500 |
| learn_loop_relative.py | 123 | Relative-vs-absolute target (attempt/compare/learn) |
| translate_localize.py | 136 | Translation generalization test |
| recognize_shapes.py | 151 | Recognition (recall + noise) |
| occlusion_match.py | 97 | Partial/voting match under occlusion |
| mvt_counting.py / _walk / _prediction_probe | 450 | Counting MVT and prediction probes |

**Documentation**
| File | Purpose |
|---|---|
| ISAAC_Perception_Curriculum.md | Perception-first relational curriculum & training guide |
| ISAAC_Session_Handoff(.md / _Addendum) | Prior session handoffs |
| (existing) ISAAC_Manual / Pipeline_Spec / Visual_Curriculum / Audit_Report | Engine docs |

---

## 13. The shape of it, for a newcomer

Isaac is one operation — difference — applied recursively to a structure of
elements, growing connections from data. It already reasons over symbols. We are
now pointing that same operation at pixels, holonically, so it can perceive space
the way it perceives language. We give it two wired primitives (difference and
baseline); it learns the rest by attempting, comparing to a known answer, and
keeping what reduces the difference. The destination is a system with enough
composable perceptual primitives to extend itself.

*One file. One class. One operation.*
