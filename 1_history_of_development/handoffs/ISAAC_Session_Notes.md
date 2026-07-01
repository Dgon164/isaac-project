# Isaac — Session Notes

*Working session. Perception/representation track. Read alongside
ISAAC_Project_Overview.md (status) and ISAAC_Theory_and_Headspace.md (framing).*

---

## Standing caution (the recurring mistake — address this)

**I keep solving things in the harness instead of in Isaac.** The counting
"100%" was an external Python loop. The locate/extract/corner-reads use numpy
scans. The hash+overlay test "matched" templates in code. Every time the seeing
or the deciding happens in my code, it's programming, not Isaac — Rule 1
violation wearing a results badge. This is the single most important thing to fix
going forward: **the difference/decision has to run in him, not around him.**

Standing TODO, explicitly:
- [ ] **hash + overlay → make it Isaac's.** The overlay score IS his operation
  (difference between two fields, least-difference wins). The hash is a cheap
  classical shortlister. Wire the verify step so the difference is computed/typed
  by Isaac, not by numpy. Currently it's a classical proof-of-concept only.
- [ ] **the walk** (traversal-with-memory) keeps being the missing primitive but
  was explicitly SHELVED — a hand-written walk is programming and unsatisfying.
  Do not build it as a Python loop. If it returns, it must be his.
- [ ] **representation bridge** — there is still no pixel→concept path that lives
  in Isaac. Crystallization is the converter (proven in the holon test) but only
  fires on directional/vector differences and collapses on flat or mixed input.

---

## What this session was about

Pushing Isaac from symbols toward perception. Repeated pattern: pick a visual
capability, build the smallest test, run it, report honestly (including failures),
let the result point at the next thing. The throughline that emerged: **it's all
one operation — differentiation against a reference — and the only variables are
which field and what scale.**

---

## Experiments run (chronological-ish), with honest results

1. **Counting MVT** — single-shot lookup fails to generalize (23% ≈ chance,
   100% train = memorization). Sequential tally-walk hit 100% on novel grids BUT
   the walk was an external loop (not clean — flagged).
2. **Recognition** — recall 5/5, robust to 1–2px noise. Real, but small distinct
   set, pixel-noise only.
3. **Translation/localization** — center fails across translation (0% novel),
   size partial (67%). Coordinates memorize. The core wall.
4. **Relative vs absolute target** — relative generalizes (100% novel), absolute
   0%. Proves the principle: translation-invariance lives in how the answer is
   encoded. (Fixed size made relative answer constant — principle, not full
   solution.)
5. **Extraction / normalization** — one object → byte-identical crop from 50
   positions/scales. Translation deleted by extraction. (Single object; size kept;
   on-bit collection still numpy.)
6. **Occlusion / partial match** — occluded X gracefully ties `\`; voting, not
   exact match. Ambiguity reported honestly. (Voting favors bigger shapes; needs
   normalized input.)
7. **Locate-by-difference at scale** — 100% at 10×10, 100×100, 500×500. The
   comparison + Isaac's arithmetic scale. Surfaced an arithmetic memoization bug
   (trailing-context recall corrupts repeated operands) and capability cross-talk
   (shared tokens hijack lookups). (Corner-read still numpy.)
8. **Global baseline** — validated: tracks normal, fades furniture, inverts
   figure/ground, ~3ms @ 500×500. Two cheap terms: per-cell EMA (temporal) +
   field-relative (spatial). Adaptation-rate knob is live.
9. **Holon test (pixels → crystallize)** — types crystallize with NO encoder, IF
   the difference is a VECTOR (direction), not a SCALAR (magnitude). "How many
   neighbors" collapses to 1 type; "which neighbors" gives 7. Key finding.
10. **Line-scan (run-widths)** — a pixel in two runs at once; (row-width,
    col-width) gives correct directional roles (interior/h-stroke/v-stroke/
    diagonal). Representation is right. But crystallizer still collapsed — the
    wall moved to the TYPING CRITERION, not the representation.
11. **Structure enumeration (width-profile derivative)** — oracle perfectly
    enumerates line/rect/square/triangle/curve from how run-widths change
    (constant/linear/unimodal). Isaac collapsed again; a single mixed example (the
    curve, containing all transitions) glues the classes. Diagnosis: structure is
    a WHOLE-PROFILE property; token-level FCA can't see it. Three collapses now,
    representation cleaner each time — conclusively the typing LEVEL, not the
    representation.
12. **Continuation (predict next turn)** — CLEAN WIN. Lines continue straight,
    arcs keep curving, generalizes across orientation (relative-turn encoding).
    The prediction loop works.
13. **Edge count** — recognizes trained counts robustly across SIZE, but caps at
    the max trained count (heptagon→6, octagon→6). Recognition, not counting.
    Same wall as #1. Reframe (user): he's not counting, he's representing/
    predicting the answer; off-by-one is what an estimator does, not a bug.
14. **Grey edges** — feeding the raw flattened field collapsed to a constant
    output (~grey_3 for everything; 14% exact). Mechanism: flatten binds the
    answer to the all-background trailing cells, so nothing discriminates.
    Representation issue (the question landed on the empty corner), not a verdict
    on Isaac.
15. **Hash + overlay** — classical proof-of-concept (NOT Isaac). Invariant hash
    shortlisted the true shape 100% (top-3) across novel size+rotation; overlay
    verify 78%. Failures = roundish polygons (hexagon/square) because the overlay
    scored FILLED area where they all overlap; distinctive silhouettes
    (star/circle) nailed it. Knobs: score edges not fill; finer rotation step.
    TODO: make the overlay-difference Isaac's, not numpy's.

---

## Conceptual ground gained (the framing that now holds)

- **One operation, many references.** Difference against neighbors (space), own
  past (time), previous position (motion), a prediction (surprise), the field
  norm (salience), another concept (meaning). Don't build parallel modules.
- **Holons.** Same operation pixel↔pixel, object↔object, frame↔frame. Composes
  upward: pixels → roles → shapes, each rung the same crystallizer.
- **Relational, not absolute.** Coordinates memorize; relations generalize; keep
  the DIRECTION (vector difference, not scalar).
- **Wired vs learned.** Difference + baseline are the wired "retina" (cheap, GPU-
  native: map ops, convolution, optical flow). Meaning, identity, tracking are
  learned (his).
- **Perceive first.** If he can't perceive it, he can't learn it. Fixes live in
  the input/representation, not in added rules.
- **He represents and predicts; he doesn't compute.** Recognition/approximation
  is the native faculty. "Counting to an exact novel N" is a different, deliberate
  mode — and must not be faked with a harness loop.
- **No pixel→concept bridge exists yet**, but the converter does: crystallization
  over relations (same thing that made "animal"). The job is feeding it pixels AS
  relations.
- **Vector/font representation** (paths, Béziers, glyph outlines + hinting) is the
  representation Isaac wants — typed, measured, related parts, position/scale-free.
  Raster→vector (tracing) is the hard direction; authoring in vector and rendering
  to raster sidesteps it. Open design fork: does Isaac live in vector and only
  touch raster at the edges?

---

## Dimensional space to cover (from the fastidious pass)

Four spatial families, and TIME differentiates every one:
- **Location** (x, y, z)
- **Framing** (rotation, scale, reflection, shear — the affine group, closed)
- **Identity** (topology open/closed/holes/#pieces; fill; polarity/inverted;
  part-roles corner/edge/tip/junction/curve)
- **Inter-object relations** (relative position, relative size, containment,
  adjacency, alignment, count)

Two load-bearing caveats: *representable ≠ recoverable* (some need motion/stereo),
and *signal vs nuisance is a per-dimension choice* (detect rotation vs be
invariant to it). Tagging each dimension is half the curriculum. (Full enumerated
table = a proposed next spec.)

---

## Bugs / engine notes

- Arithmetic memoization keys on trailing context → repeated operands (`x+1`)
  return the first cached answer. Disable memoize or fix the keying.
- Capabilities in one net cross-talk through shared tokens. Isolate, or namespace.
- Crystallizer types tokens by neighbor-context only → collapses distinct roles
  that sit adjacent, and a single mixed example glues classes. Structure-level
  typing needs to consider a node's own signature and/or operate on whole profiles
  (the holon step up), not just token neighbor-context.

---

## Where it stands / candidate next moves (user's call)

- Make hash+overlay Isaac's (overlay-difference computed by him).
- Push crystallization the rung up: roles → shape concepts (the holon step we
  keep circling but haven't taken).
- Decide the raster-vs-vector fork for how Isaac represents shapes.
- Better representation for the grey-edge / edge-detection task (crop/center
  first, or boundary-as-sequence, or two-channel edge×grey join).
- Build the full dimensional table with signal/nuisance + recoverable tags.

*Run the test. Report what it did. Don't forecast his limits, and don't do the
seeing for him.*
