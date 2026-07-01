# Isaac — Perception-First Relational Curriculum & Training Guide

*How to teach Isaac to see, by translating classical (GOFAI) vision into a
training curriculum he learns — instead of installing the algorithms as code
that runs for him.*

---

## 0. The one sentence this whole guide hangs on

**If he can't perceive it, he cannot learn it.** Perception is upstream of every
behavior. We do not teach "count" or "segment" to a system that cannot yet
perceive the relation those behaviors stand on. We make the relation perceivable
first; the behavior then becomes learnable on top of it.

---

## 1. The constitution (read before writing any curriculum)

These are the rules every tier must obey. They come from what worked and what
failed this session. Violating one is the smell that you're doing it wrong.

1. **Feed the thing and the answer, never the method.** Isaac makes an attempt,
   compares it to the truth, and learns from the difference (predictive coding).
   We are allowed to *generate correct answers to teach with*. We are never
   allowed to compute the answer at query time and hand it back as his — that is
   us seeing for him. (The counting-loop mistake: an external Python loop "solved"
   counting; it was the harness counting, not Isaac.)

2. **Relational, not spatial.** Feed what *connects*, not what's *where*.
   Coordinates are unique per instance → memorized. Relations recur across
   instances → generalized. This is the root cause of every spatial failure this
   session: we fed a relational engine absolute coordinates, so it had nothing to
   share across examples. Adjacency ("this cell touches that cell") is a door —
   his native unit.

3. **Teach the atomic step, not the result.** Teaching scene→answer memorizes
   (counting MVT: 100% on trained grids, 23% on novel — chance). Teach the local
   step that *composes* into the answer (the tally walk taught "+1", not sums,
   and hit 100% on novel grids). Every tier names its atomic learnable unit.

4. **The classical algorithm is the answer key, not the deliverable.** The oracle
   (flood fill, skeletonize, connected components, structure tensor, etc.) is as
   brittle and classical as we like, because it never ships. It only *grades*.
   Isaac learns the mapping; what generalizes is his.

5. **Local and bounded beats global and metric.** A 3×3/5×5 patch has a tiny,
   recurring vocabulary and means the same thing everywhere it appears. A corner
   is a corner at any position and scale. Slide a small window and ask one local
   relational question; never build the whole global graph if a patch will do.
   This is also the tractability win — the expensive global structure never has
   to exist.

6. **Normalize before you match.** extract → normalize → compare. Skeletonize
   (thin to 1-px) before asking about endpoints/junctions, or "end" and "stub"
   blur together.

7. **The coordinate enters only at the readout.** Perception finds *which* cells
   are the endpoints/center/corners (relational, scale-free). *Then* you read off
   the (x,y) they sit at. The seeing is relational; the report is a number. Never
   the reverse.

8. **Add perception, not rules.** Rule of thumb: if a fix needs you to modify a
   lot or add rules, you're doing it wrong. The allowed kind of "add" is giving
   the input a form the *existing* engine can perceive (extraction was this — no
   new rule, just the difference presented so he could see it). The disallowed
   kind is bolting on new behavior logic.

9. **Isolate capabilities.** Distinct skills sharing one net cross-talk through
   shared tokens (the arithmetic bug: teaching halving hijacked addition;
   memorized "x + 1 = 4" hijacked every later "+ 1"). Each perceiver should be
   trainable and testable on its own, and you should watch for contamination when
   they share vocabulary.

10. **Report ambiguity; don't force an answer.** Partial/occluded evidence
    genuinely supports several readings (occluded X ties with `\`). The honest
    output is a ranked set with confidence, resolved by context, not a forced
    single guess. Confidence is already a usable signal (nonsense scored ~4 vs
    real matches ~30).

---

## 2. The checklist (build order)

Each item is gated by the ones above it. Do not start a row until the rows above
it pass their generalization test.

### Tier 0 — Perception prerequisites (the spark plug)
- [ ] **0.1 Adjacency intake.** A way to present a cell *with its neighborhood*
      (the patch) so "next to" is expressible. This is the single perception that
      converts spatial → relational. Everything else depends on it.
- [ ] **0.2 Connectivity decision.** 4-connected or 8-connected. Baked into the
      patch, not a flag on top. (4 keeps diagonal-only touches separate; 8 merges
      them. For thin diagonal strokes like X/`<`/`v`, this is "one object" vs
      "five".)
- [ ] **0.3 Degree.** The local count of on-neighbors (0–4 or 0–8). Bounded, tiny,
      trivially perceivable — the foundation under line/corner/end/junction.
- [ ] **0.4 Skeletonize (oracle-side normalize).** Thin strokes to 1-px so degree
      is unambiguous: degree-1 = end, degree-2 = through, degree-3+ = junction.

### Tier 1 — Local relational primitives (3×3 patches)
- [ ] **1.1 straight / line** (passes through, no turn)
- [ ] **1.2 corner** (turns ~90° inside the window)
- [ ] **1.3 endpoint** (enters, doesn't leave; degree-1) — *also the point detector*
- [ ] **1.4 junction** (3+ strokes meet; degree-3+)
- [ ] **1.5 interior / blank** (the negative classes, so it can say "nothing here")

### Tier 2 — Orientation (3×3, then 5×5)
- [ ] **2.1 slope / angle of a straight patch** (which direction it runs)

### Tier 3 — Curvature (5×5)
- [ ] **3.1 bent vs straight**
- [ ] **3.2 sharpness of bend** (curvature magnitude, patch-local)

### Tier 4 — Composition via traversal (the walk)
- [ ] **4.1 stroke walk** — follow adjacency cell to cell, with a visited set
      ("have I been here") — the traversal-with-memory primitive
- [ ] **4.2 endpoints A & B** — the two degree-1 cells of a stroke; read out their
      coords ("give me the end coordinates of this line")
- [ ] **4.3 open vs closed** — endpoints present → line; none, all degree-2 → ring.
      This is line-vs-circle with no measurement at all.
- [ ] **4.4 length** — count steps along the walk (tally walk; his scale-free add)
- [ ] **4.5 radius** — integrate local curvature along the walk (composed, not
      patch-local)

### Tier 5 — Shape identity as relational signature
- [ ] **5.1 primitive histogram** — how many corners / how much straight / curve /
      junctions a shape contains
- [ ] **5.2 shape type from signature** — line, square-outline, circle, cross, etc.,
      scale- and position-free

### Tier 6 — Segmentation (connected components / flood fill)
- [ ] **6.1 region membership** — atomic step: "this on-cell's on-neighbor is the
      same object"
- [ ] **6.2 separate objects** — the walk applied until on-neighbors run out = one
      object
- [ ] **6.3 count objects** — tally walk, +1 per new region
- [ ] **6.4 per-object extract & locate** — reuse extract + center per region

### Tier 7 — Robustness
- [ ] **7.1 occlusion** — partial/voting match, ambiguity reported (done in proto)
- [ ] **7.2 noise tolerance** — graceful degradation under pixel flips
- [ ] **7.3 scale-normalize** — resample crop to canonical box so *type*
      recognition is size-invariant, not just position-invariant

---

## 3. The shared training pattern (every tier is the same shape)

```
generator   → makes raw scenes/patches (unlimited, by construction)
oracle      → the classical algorithm labels them   (ANSWER KEY ONLY)
encode      → present input to Isaac as RELATIONS, in his vocabulary
train       → attempt → compare to oracle label → learn from the difference
test        → held-out scenes at NEW positions/scales/orientations
gate        → generalization (TEST) clearly beats the memorization baseline
```

Key disciplines, learned the hard way:

- **Generate, don't extract, to label.** We place the shape, so we know its
  answer by construction. We never run a reduction over pixels to *find* the
  label — that direction is the wall, and we simply never go there.
- **Disjoint train/test, deduplicated.** Test items must be genuinely novel
  (split by position parity / held-out scale / held-out orientation).
- **Two numbers always: TRAIN and TEST.** TRAIN = memorization, TEST =
  generalization. The *gap* is the diagnostic. 100/23 means "memorized, learned
  nothing." High on both means it learned the relation.
- **Report exact and within-tolerance.** "within ±1" tells you if it's "sort of"
  perceiving vs random.
- **One perceiver per net (or per clean namespace).** Avoid cross-talk. Test each
  primitive in isolation before composing.

### Encoding rule of thumb
Describe a cell by **what it touches**, not where it is. A patch becomes a small
relational token (e.g., the degree + the neighbor pattern), which recurs across
the whole image and across images — so it generalizes. The same square's patches
are the same patches whether it's 3×3 in a corner or 50×50 in the middle.

---

## 4. Per-tier spec (the first three, fully; the rest follow the template)

### Tier 1.3 — Endpoint (the highest-value first brick)
- **Why first:** it's a shape primitive *and* the point-extractor. Answers
  "where are A and B" for free, and gates open-vs-closed (line vs ring).
- **Generator:** draw 1-px strokes (lines, bent lines, rings) at random
  positions, lengths, angles, scales. Skeletonize.
- **Oracle:** degree map. degree-1 = endpoint. (Classical, trivial.)
- **Encode:** each cell → its local neighbor pattern (relational). No coordinate
  in the input.
- **Atomic unit:** "this neighbor pattern = end / through / junction." Local,
  position-free.
- **Train:** patches → label, attempt/compare/learn.
- **Test:** held-out strokes at new angles/scales. Does "end" fire on exactly the
  two tips?
- **Readout:** the two cells whose patch says "end" → read their (x,y). That's A
  and B.
- **Gate:** ≥95% of strokes return exactly two correct endpoints, generalizing to
  unseen angles/scales.
- **Watch:** thick strokes (skeletonize first); near-endpoints at fat corners.

### Tier 1.1 / 1.2 — Straight vs Corner
- **Generator:** strokes that go straight through a window vs turn ~90°.
- **Oracle:** local direction before/after center; unchanged = straight, ~90°
  change = corner.
- **Atomic unit:** "this 3×3 neighbor pattern = straight / corner."
- **Test:** rotate and rescale; does "corner" survive orientation? (Rotation
  invariance is the real test — teach few orientations, test the rest.)
- **Gate:** corner/straight classification ≥90% on unseen orientations.

### Tier 4.3 — Open vs Closed (line vs ring, no measurement)
- **Depends on:** 4.1 walk, 1.3 endpoint.
- **Atomic unit:** none new — it's a *composition*. Walk the stroke; if you find
  degree-1 cells it's open (a line, with those as A/B); if you return to start
  with all degree-2 it's closed (a ring).
- **Gate:** lines vs rings separated 100% across sizes, because it's topological,
  not metric.

*(Tiers 2, 3, 5, 6, 7 follow the same six-part template: generator, oracle,
encode-as-relation, atomic unit, train, held-out generalization test + gate.)*

---

## 5. What I would add (my contributions to your design)

These weren't in the original handoff; I'm flagging them as additions for you to
accept or reject.

1. **Degree as the explicit foundation (0.3).** Line / corner / endpoint /
   junction are all just *degree patterns*. Making "count my on-neighbors" the
   first perceivable primitive means the rest are read off one cheap local count
   (0–4), not separately engineered. This is the bounded version of the "count"
   that kept breaking globally — locally it's trivial.

2. **Skeletonization as a normalize prereq (0.4).** Endpoints/junctions are only
   crisp on 1-px strokes. It's classical, oracle-side, and it makes the whole
   degree vocabulary unambiguous. Without it, Tier 1 is noisy.

3. **The traversal-with-memory primitive, named and decided early (4.1).** This
   is the one thing that genuinely recurs and that lookup doesn't natively do:
   flood fill, line-walk, length, radius all need "follow neighbors, remember
   where I've been." **Decision needed:** is the visited-set learned by Isaac, or
   is the walk harness scaffolding around primitives he *does* learn? I lean
   scaffold-the-walk, learn-the-judgments — but it's your call and it shapes
   everything in Tiers 4 and 6.

4. **Ambiguity/confidence as first-class output (Rule 10, Tier 7.1).** Don't make
   the curriculum force single answers under occlusion. Teach it to return ranked
   candidates; let context/prediction break ties. The confidence number already
   discriminates signal from nonsense — use it as the abstention threshold.

5. **Rotation invariance as an explicit test axis.** We've been testing position
   and scale. Corners/curves also need *orientation* generalization (teach few
   angles, test the rest). Add it to every local-primitive gate.

6. **Contamination checks in the test harness.** After the arithmetic cross-talk
   bug, every "it works" should be re-run on a clean net and after co-training
   with a neighbor skill, to catch hijacking. Cheap insurance.

7. **A bootstrap target.** The end goal you stated is Isaac self-updating once he
   can build code. So the curriculum's real success criterion isn't "passes Tier
   7" — it's "has enough composable primitives that *he* can assemble the next
   capability." Worth keeping the primitive set small, orthogonal, and
   composable with that in mind, rather than maximizing any single behavior.

---

## 6. Decisions I need from you before generating curriculum code

1. **Connectivity: 4 or 8?** (bakes into every patch)
2. **The walk (4.1): learned or scaffolded?** (shapes Tiers 4 & 6)
3. **Start window: 3×3 or 5×5?** (3×3 for the sharp primitives; 5×5 if you want
   curvature in the first pass)
4. **First brick: endpoint (1.3)** — agreed? It's the highest-leverage (point
   detector + open/closed gate) and the cleanest generalization test.

---

## 7. Anti-patterns (the mistakes, so they're not repeated)

- Building a feature extractor / scan loop and calling the result Isaac's.
- Teaching scene→answer and being happy with high TRAIN (it's memorization).
- Feeding coordinates and expecting generalization.
- Adding a primitive/rule to force a result instead of making the input
  perceivable.
- Letting two skills share a net and trusting the lookup.
- Forcing a single answer where the evidence is honestly ambiguous.
- Declaring "the architecture can't" when it's "I haven't framed the input so it
  can perceive this yet."

---

*Translate the classical algorithm into a curriculum. Let him learn the relation.
What generalizes is his.*
