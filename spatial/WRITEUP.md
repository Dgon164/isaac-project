# The Spatial Sandbox: From Pitch to Working Perceiver

**Session write-up — July 3, 2026**

## 1. The original idea

The session opened with a proposal for Isaac: a **multi-dimensional spatial
representation engine** — a hidden coordinate sandbox, separate from the
interpreter, where concepts are built as actual 2D/3D structures that can be
translated, stretched, squashed, twisted, rotated, or reversed, then
reprojected as flat "shadows" for comparison. Three founding commitments:

- **Self-calibrating scale**: the engine establishes its own internal relative
  scale from the data's native shape; no absolute units.
- **Geometric layering**: shape (internal geometry) → surface (interface
  boundaries) → scale (real-world magnitude).
- **Informational rotation & reprojection**: rotate the high-dimensional
  structure, project 2D shadows, expose hidden dependencies, symmetries, and
  parallelisms invisible to linear analysis.

The architectural resolution that made this compatible with Isaac's
"coordinates memorize, relations generalize" rule: **coordinates are scratch
space, never storage.** The loop is relations → instantiate geometry →
transform → reproject → re-extract relations → compare. Nothing
coordinate-shaped is ever written to the net.

## 2. The conceptual build-out (pre-code)

Each exchange added a layer; each layer reused the previous ones.

**Procrustes as the core compare.** Given two point sets, closed-form optimal
alignment returns two answers at once: the recovered transform (the *framing*
difference — rotation, scale, reflection) and the residual (the *identity*
difference). Symmetry detection becomes precise: a symmetry is a non-identity
transform that maps a shape onto itself with near-zero residual. Mirror,
shift, and rotate + subtract detect bilateral symmetry, periodicity, and
radial patterns respectively — three lines each.

**2D→3D via structure-from-motion.** Rotation is the condition under which
depth becomes recoverable (representable ≠ recoverable). Correspondence
across adjacent frames is nearly free with continuous motion (optical flow —
already on Isaac's wired-retina list). On deformable objects, the *failure*
of rigid reconstruction discovers the skeleton: regions of coherent flow are
rigid parts; boundaries where flow disagrees are joints.

**Topology as identity, geometry as framing.** What crystallizes into the
net is the part graph (connectivity + proportion ranges), which survives
stretching, scaling, and pose. Geometric parameters layer on top.

**Engineering drawings as a solved inverse problem.** Orthographic multiview
is projection engineered (since Monge, 1790s) to be invertible: known 90°
view rotations, no perspective, correspondence given by convention. A
drawing's content is already relational — dimensions are relations,
tolerances are relations with allowed ranges, GD&T symbols are typed edges.
The reconstruction target is a constraint graph, Isaac's native format.
Reprojection gives a built-in correctness test. The hard part is the learned
conventions layer (hidden lines, sections, symbols), teachable by synthetic
curriculum with the reprojection residual as the teacher.

**Sig figs / precision as represented knowledge.** No quantity is a bare
number: every value is magnitude + precision. Title blocks supply precision
for drawings; instruments supply it for perception. Comparison thresholds
arrive with the data, not as magic constants in code.

**Fine-structure variance.** Categories store mean + per-dimension variance
(Mahalanobis matching): snout length varies a lot, ear proportion little.
Two ledgers per dimension — within-individual and between-individual — split
category membership from individual identity. Temporal continuity supplies
free within-individual labels (a tracked video of one cat is guaranteed
same-individual data). The caricature effect and cartoon legibility are
behavioral evidence for norm-plus-scaled-deviation representation.

**Fuzzy points (position + covariance + count).** Uncertainty lives in the
geometry itself — each sandbox point is a Gaussian blob (independently
reinvented Gaussian splatting). Triangulation produces directional
uncertainty naturally; fusion is inverse-variance weighting; fat ellipsoids
point at what to look at next; on articulated bodies, elongated ellipsoids
near joints trace the degrees of freedom. Full covariance (not per-axis)
so transforms carry the fuzz correctly (RΣRᵀ).

**Bones and rigging.** A rig is a part graph with tolerances on its edges.
Shape parameters (bone lengths/girths — between-individual) vs pose
parameters (joint angles — within-individual). Joint limits are learned
variance ledgers over angles, giving a plausibility prior, an anomaly
detector (the limp alarm), and motion prediction.

**Nonlinear, non-uniform scaling.** Variance is distributed by function, not
size: a car's length varies by feet, a valve clearance by thousandths,
regardless of vehicle size. Proportional dimensions ride global scale;
absolute dimensions are pinned by function — and pinned dimensions are almost
always **interfaces** (where parts mate). Population covariance + PCA learns
the "knobs" (size, boxiness…) with per-dimension coefficients; interface
dimensions announce themselves as variance that stays constant while
everything around it grows.

**Two-layer deformation architecture.** Layer 1: deformation graph — sparse
control nodes with local affine transforms, points blend their neighbors'
transforms (embedded deformation; bends are chains of small rotations,
lattices handle free-form squash). Layer 2: driver graph — parameter B =
f(parameter A) as monotone learned curves on typed directed edges (driven
keys / parametric relations), learnable from population data. Known costs:
linear-blend pinch at joints (fixable by corrective nodes learned from
reprojection residual); driver cycles need topological-order propagation.

**Linkages resolved.** Locked lengths are *undirected simultaneous*
constraints, not directed drivers — no circularity. Constraint projection
(position-based dynamics): measure each pair's distance error, split the
correction between endpoints, sweep a few times. Ten lines, loops free.
Rigid parts precipitate as fully-locked clusters. Materials vocabulary:
locked = rigid, sprung = elastic (variance ledgers already express ranges),
free = separate. Volume conservation added as one aggregate constraint gives
squash-and-stretch (the 2024 water-balloon conversation, closed).

## 3. The engine

`engine.py` — a few hundred lines total:

- **Mechanism**: points, locked distances, pins, rails (sliders). `project()`
  = the sweep loop. `drive()` = drag a point, let everything settle.
- **PairLedger**: Welford running mean/variance per pairwise distance.
- **observe / detect_locked**: ledger over all pairs; locked = std below a
  sig-figs threshold relative to self-calibrated scale.
- **rigid_clusters** (2D shortcut; superseded by pairwise-locked cliques in
  3D), **find_joints**, **gruebler_2d**, **observed_dof**.

## 4. The tests (11 files, all passing)

**test_structure.py — four-bar + door.** Forward sim at machine precision
(8.9e-16 drift) once geometry satisfied Grashof — the solver refused to run
a physically impossible mechanism, catching a real design bug. Perceiver,
given only trajectories: recovered all locked edges *including the ground
link nobody declared* (both ends pinned → distance never varies → it IS a
link), rigid parts, Grübler DOF = 1 matching observed DOF = 1. The door
reduced to: one rigid part + one anchored point + one angle.

**test_occlusion.py — the invisible crank.** Crank tip hidden; connections
never given (the perceiver never sees connections — it infers all edges).
From three visible trajectories: bounded variation with repeatable limits on
d(pivot, rocker-tip) betrayed hidden constraint; fold/extend geometry
(max = coupler + crank, min = coupler − crank) recovered the invisible link
lengths to 0.0000 error; synthesis rebuilt the whole mechanism and matched
the observed rocker sweep to 0.001°. New edge tier: bounded = hidden
constraint. New principle: verification by synthesis is the hypothesis
filter.

**test_engine_cycle.py — slider-crank under hostile conditions.** Erratic
(reversing, stalling) drive, ±0.003 bearing slop, measurement noise. All
structure recovered because the questions are asked in configuration space,
not the time domain — no cycle period needs to exist. The slop itself was
measured (wrist pin: implied clearance ±0.0030 vs truth ±0.003) — wear
diagnosis for free. The TDC/BDC acceleration asymmetry (the secondary
harmonic; measured ratio 1.87 vs analytic (l+r)/(l−r) = 2.0) was *predicted*
from the two lengths the perceiver inferred: structure predicted dynamics.
Configuration binning (average over configuration, not time) turns erratic
speed into free coverage.

**test_snake.py — serial chains and follow-the-path.** Adjacent distances
locked (segment length); next-adjacent bounded → hidden turn limit recovered
at 29.99° vs truth 30° by the same fold/extend trick (joint limits ARE
fold bounds). Lag detection: every link's present = the head's past at lag =
chain position, residual zero → one generator, causality direction found.
The path itself — never an object in the simulation — was reconstructed as a
mapped 1D curve constraint. New reference class: difference against
*another's history*. New constraint species: the curve/manifold constraint
(rails, grooves, cams).

**test_materials.py — states of matter as invariance signatures.** Three
blobs (rigid / soft / liquid), one drop test, one classifier using two
ledgers: neighbor permanence + distance character, plus local density as an
aggregate invariant. All three classified correctly; the liquid found its own
level (emergent, unprogrammed). The two failures en route were the real
findings: (1) **material identity only exists under load** — a settled soft
body is measurement-identical to rigid; material perception is inherently
interactive or opportunistic; (2) **elastic vs plastic is undecidable while
loaded** — the discriminating observation is the release, requiring stored
memory of the pristine pre-load state. Also: yield is real — hit soft matter
hard enough and it rearranges permanently; material labels are properties of
object + load regime.

**test_assembly.py — design as perception reversed.** Given only 48 points
of a coupler curve: random exploration (345/400 proposals rejected free by
Grashof screening) + coordinate refinement rediscovered the hidden mechanism
(1.995, 6.992, 5.938, 7.895 vs truth 2, 7, 6, 8), curve mismatch 0.31%.
Design cognates (different mechanisms, same behavior) are equally valid
because function, not blueprint, is the spec. Arbitrary rules: any scorable
condition is an enforceable constraint (solver side) and any measurable
quantity is a discoverable invariant (ledger side).

**test_pressure.py — volume, containment, hidden state.** Water balloon:
every pair distance varying, area locked to rel-std 0.0001, transverse bulge
under pinch (Poisson as arithmetic) → incompressible. Air balloon: area
compresses 20% and recovers → sprung aggregate (Boyle's law = the invariant
is a product). Pressurized rigid vessel: Procrustes residual 0.0015 under
the same pinch (200x stiffer than the balloons), externally identical to an
empty box — then breach released kinetic energy five orders of magnitude
above baseline with zero external work → hidden internal state proven.
Lessons: the invariant hierarchy has levels (pairs → aggregates), each with
the locked/sprung split; probes must be compliant (an infinitely strong
gripper destroys the evidence — the probe's own deformation is half the
measurement); and the epistemic ladder: shape needs a glance, structure
needs motion, material needs load, internal state needs breach (or an
installed side channel — that's what gauges are).

**test_3d.py — the third dimension.** The identical projection loop dropped
a rigid tetrahedron at 2.5e-10 drift (dimension-blind). The earned upgrade:
rigidity = **pairwise-locked cliques** (connectivity is insufficient in 3D
— two plates sharing an edge are connected but hinged). The gift: joint
taxonomy from clique overlap cardinality — 3+ shared points = weld, 2 =
hinge (the shared pair IS the axis), 1 = ball (the shared point IS the
socket). All three classified and located correctly. Remaining 3D specifics
are contained upgrades: volume via signed tetrahedra, Kabsch Procrustes,
spatial Grübler coefficients; richer joints (slider/cylinder/screw) are
motion signatures between cliques — the driver-curve detector pointed at
inter-clique motion.

**test_maps.py — maps, archetypes, the hidden center.** (1) Ego-motion: from
140 egocentric frames (every observation in a different rotated/translated
frame), 66/66 landmark pairs locked → the scene is one rigid clique; one
rigid transform explains each frame to 1.4e-15 → parsimonious verdict: the
scene is still, the OBSERVER moved; self-localization to 1.8e-15. "I" is the
hypothesis that best compresses the coherent motion of everything else.
(2) The cube: distance spectrum quantized into exactly 3 tiers (12/12/4
pairs at ratios 1 : √2 : √3 — the cube's archetype fingerprint, invariant to
size/pose); tier-1 adjacency yielded the role vocabulary — 8 corners (degree
3), 12 edges, 6 faces — and passed Euler's V − E + F = 2 as a checksum on
the observation. Corner/edge/face are theorems of the spectrum, not lessons.
(3) The globe: hidden center fitted to (1.000, 0.500, −0.300) exactly,
radius 3.0000 ± 4.8e-16. Discriminator from the cube (whose corners also lie
on a sphere): spectrum character — discrete tiers = polyhedron (crystalline),
continuum = smooth surface (gap statistic 0.566 vs 0.059).

**test_keyframes.py — state A, state B, and the road between.** (1) Naive
point-lerp of a rotated square violated shape by 71% of an edge length;
diffing the keyframes in transform space (Procrustes: "rotate 120°,
translate (2.63, 0.87)") and interpolating the *change* held rigidity to
8.9e-16. Interpolate the change, not the coordinates. (2) Four-bar crank
20°→160°: lerp-then-project walked the constraint manifold — 60 inbetweens,
every one a legal state, smooth steps, exact arrival. The solver is also the
planner. (3) Same crank angle, mirrored assembly branch: every frame
individually legal but the path contained an 8.06-unit teleport (40x any
legal step) → verdict: no continuous path exists; the target is in a
different component of the configuration manifold; reaching it requires
disassembly. Three grades of possibility: legal, reachable,
unreachable-without-breaking. Bonus: a keyframe path is itself a curve on
the manifold — actions ("opening", "folding", "walking") are storable,
recognizable named paths.

**test_circuits.py — diagrams, circuits, time.** (1) Two schematics sharing
no coordinates produced identical netlists; a dotless crossover (2.5D
convention) correctly contributed nothing. Diagrams are topology-faithful
(layout is nuisance) — the mirror of metric-faithful engineering drawings.
Nets are electrical rigid bodies; KVL is loop closure; KCL is a conservation
ledger. (2) A resistor network solved by the same local-relaxation style
(each node settles to its neighbors' demand), KCL conserved to 8.9e-16.
(3) The showstopper: from five raw waveforms of an unknown logic circuit,
the lag question (whose present is whose past?) over a Boolean function
vocabulary recovered the full circuit — A, B unexplained → primary inputs
(generators, like the snake's head); C = NOT(A) delay 1; D = NAND(A,B)
delay 2; E = AND(C,D) delay 1. Topology, gate functions, propagation delays,
and flow direction from watching wires talk. Delays are sig-figs in time and
diagnostic (growing delay = degrading component). Diagrams are humanity's
serialization format for constraint graphs — the one external medium already
in Isaac's native format; generation (Isaac drawing schematics of what he
understands) is the same pipe reversed.

## 5. The principles (the durable output)

1. **Pick the right space, ask what refuses to vary, and structure names
   itself.** The single move behind every result.
2. **One operation, many references** (from the June framing) gained new
   reference classes: transformed self (symmetry), another's history
   (causality/leadership), a prediction (absence — designed, not yet built).
3. **Coordinates are scratch, relations are storage.** The sandbox computes
   in coordinates; only relations cross back.
4. **Configuration space beats the time domain** for structure: invariance
   questions ignore speed profiles entirely; erratic motion is free coverage.
5. **The edge/invariant vocabulary** (all empirically demonstrated):
   tight-locked → locked-within-measured-tolerance → sprung (mean-reverting)
   → bounded (hidden constraint) → free; plus curve/manifold constraints;
   plus aggregate-level invariants (area/volume/density/momentum) with the
   same locked/sprung split; plus discrete-vs-continuous spectrum character
   (crystalline archetype vs smooth manifold).
6. **Hidden things are inferable**: hidden links (from bounded variation),
   hidden paths (from trajectory union), hidden centers (from equidistance),
   hidden state (from breach energy), hidden causes (from lag structure),
   the hidden self (from scene coherence).
7. **Verification by synthesis**: propose → simulate → reproject → compare.
   The residual filters hypotheses, teaches conventions, and spawns
   corrective structure.
8. **The epistemic ladder**: shape (glance) → structure (motion) → material
   (load) → internal state (breach/side-channel). Each rung costs more
   interaction and irreversibility; knowing which rung a question lives on
   is itself understanding. Probes must be compliant; memory of the pristine
   state is a prerequisite for elastic/plastic distinctions.
9. **Precision is a first-class citizen** at every level: sig figs on values,
   covariance on points, variance ledgers on relations, tolerance on
   dimensions, delay on signals. Thresholds arrive with the data.
10. **Design is perception reversed**: propose over typed interfaces, screen
    by counting rules (free rejection), simulate, judge by the perceiver
    against behavior. Cognates are valid; function is the spec.
11. **Solver = simulator = planner**: one projection loop, driven three ways.
12. **Structure predicts dynamics**: lengths inferred from statics predicted
    the TDC slam ratio measured independently from motion.

## 6. Honest remaining work

- **The pixel bridge** (keystone): render → dumb tracker → unchanged
  perceiver. Identity minting is the tracker's only job; then 3D-lift
  (image-plane distances aren't invariant under out-of-plane rotation —
  ledger must run on reconstructed points for general scenes).
- **Systematic sig-figs substrate** (currently philosophy + hand-tuned
  thresholds per test).
- **Integration into Isaac**: emitted relations → typed edges → crystallizer,
  so verdicts become owned concepts.
- **Scale**: all-pairs ledgers need neighborhood sparsification past a few
  hundred points.
- **Unbuilt-but-specced**: deformation graph + driver curves; active
  perception (choosing to poke); abductive missing-part (Grübler vs observed
  DOF disagreement → posit unseen part); volume/Kabsch/spatial-Grübler 3D
  upgrades; slider/cylinder/screw joint signatures; UV unwrapping (curvature
  from distortion); diagram *generation* (Isaac showing his work).
- **Beyond spatial** (from the capabilities inventory): dynamics
  (mass/force/energy as new ledger quantities — ledger-native), time-domain
  machinery (duration, rhythm, sequence; the lag detector is the seed),
  animacy/intention (violations of learned passive physics; goal-convergent
  paths), absence/negation (needs prediction as reference), conventional
  symbols (arbitrary grounding — a different kind of edge), and valence
  (what matters — a design decision, not a discovery).

## 7. File manifest

- `engine.py` — mechanism solver + ledger perceiver core
- `test_structure.py` — four-bar & door: forward sim + structure recovery
- `test_occlusion.py` — invisible link inference + synthesis verification
- `test_engine_cycle.py` — slider-crank: hostile conditions, slop diagnosis,
  TDC asymmetry
- `test_snake.py` — serial chain, joint limits, lag causality, hidden path
- `test_materials.py` — rigid/soft/fluid classification, load & release
- `test_assembly.py` — mechanism design from a target curve
- `test_pressure.py` — water/air/pressurized vessels, hidden state
- `test_3d.py` — dimension-blind solver, clique rigidity, joint taxonomy
- `test_maps.py` — ego-motion & mapping, cube roles & Euler, hidden center
- `test_keyframes.py` — transform-space diffs, manifold inbetweening,
  unreachability detection
- `test_circuits.py` — netlist invariance, relaxation solving, logic
  reverse-engineering from waveforms

Every test runs standalone: `python3 test_<name>.py`. All pass.
