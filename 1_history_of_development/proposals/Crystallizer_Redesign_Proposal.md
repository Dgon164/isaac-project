# Crystallizer Redesign — Draft Proposal

## Current State

The crystallizer has 10 scan phases that find patterns and propose new nodes. It's flat — finds co-occurrence pairs and wrong pile patterns, proposes exclusion rules. It creates things and asks permission.

## What It Should Be

A net refiner. The pipeline and training build the net. The crystallizer makes sense of what's there — organizes, structures, refines. It discovers the relationships that are implicit in the data.

Five core operations, all recursive:

---

## 1. Circle Discovery

**What:** Find groups of nodes whose dimensional overlap defines a new concept. The intersection IS the circle.

**How:** Take all nodes of a given type (e.g., all nodes tagged as nouns with animate tag). Collect their dim profiles. Find the dims they ALL share (or that N% share — the threshold is tunable). That shared set is a circle.

**Example:** Dog has {animate, domestic, canine, four_legged, fur, mammal, ...}. Cat has {animate, domestic, feline, four_legged, fur, mammal, ...}. Bear has {animate, wild, four_legged, fur, mammal, ...}. The intersection {animate, four_legged, fur, mammal} IS the mammal circle. Dog, cat, bear are PART OF it — they point to it. It doesn't contain them.

**What it writes:** A circle node with shared pointers to the dims that define it. Each member gets a pointer to the circle. The circle is `source="crystallized"`.

**Auto-accept vs lift:** If the overlap is based on 3+ members and 3+ shared dims, auto-accept. If it's based on only 2 members or 1-2 shared dims, it's a gap — propose to lift.

**Replaces:** Current `_find_co_occurrences`. Same raw data, but instead of finding pairs, it finds full group intersections.

---

## 2. Subtype Detection

**What:** Within an existing circle, find nodes that have everything the circle has plus specific additional dims. Those are subtypes.

**How:** For each circle, check its members. Each member has the circle's dims plus its own. The "plus its own" part defines the subtype. If multiple members share the same "plus" dims, they form a sub-circle within the circle.

**Example:** Automobile circle has {vehicle, wheeled, engine, road}. Ford has all of those plus {american, brand, truck_line}. Toyota has all of those plus {japanese, brand, reliability}. Ford and Toyota are subtypes of automobile. If Ford and Toyota share {brand}, that's a sub-circle (automobile brands).

**What it writes:** Subtype relationship pointers. The subtype node points to the circle it specializes. The additional dims that distinguish the subtype are recorded.

**Auto-accept vs lift:** Subtypes within well-established circles (5+ members) auto-accept. Subtypes within new or small circles go to lift.

---

## 3. Class Discovery

**What:** Circles of circles. Same operation as circle discovery, one level up.

**How:** Take all existing circles. Collect their dim profiles. Find which circles share dims. Their intersection is a class.

**Example:** Airplane circle has {vehicle, engine, wings, sky}. Train circle has {vehicle, engine, tracks, land}. Automobile circle has {vehicle, engine, wheeled, road}. The intersection {vehicle, engine} defines the class "powered vehicle." This is recursive — classes can have classes.

**What it writes:** Class nodes with pointers to member circles. Same structure as circles but pointing to circles instead of leaf nodes.

**Auto-accept vs lift:** Same rules as circles. 3+ member circles with 3+ shared dims = auto-accept.

---

## 4. Lockout Creation

**What:** Find definitions/circles that are mutually exclusive. When one is active, the other can't be.

**How two sources:**

**From the wrong pile:** If corrections consistently show that interpretation A is wrong when interpretation B is right, that's a lockout. "cat" as animal vs "cat" as CT-scan — the wrong pile records which context each belongs to.

**From state comparison:** Run two interpretations of the same input. Diff the activation states. Dims that appear in only one interpretation define the lockout boundary. The patterns that block each other become lockout pairs.

**What it writes:** Lockout nodes. Positive pointer to the favored pattern, negative pointer to the suppressed pattern. The gate reads these during selection. Meta-lockouts for context-dependent overrides.

**Auto-accept vs lift:** Lockouts from wrong pile corrections (human said it's wrong) auto-accept. Lockouts from state comparison (system inferred) go to lift.

---

## 5. Inference (Reverse Crystallization)

**What:** Estimate an unknown from its context. When the real answer arrives, the delta is the learning signal.

**Five sub-operations:**

**Gather surround:** Unknown word appears. Collect the dims of every known word around it. This is the context profile.

**Class profile:** For each existing circle/class, what are its typical dims? (Threshold: dims that appear in 60%+ of members.)

**Best cover:** Greedy set cover — find the fewest existing circles that explain the most of the context profile. "This unknown word is probably a [mammal] that is [domestic] based on surrounding dims."

**Estimate hole:** The best-cover estimate is the hypothesis. Store it. When the real answer arrives (through training, teaching, or future context), compare estimate vs reality.

**Learning delta:** The difference between estimate and reality. If the estimate was close, the covering circles are good. If the estimate was way off, either the circles are incomplete or a new circle needs to exist. When NO existing class covers the union of context dims, that's a new circle being discovered — the inference failed to find a match, which means the system encountered something genuinely new.

**What it writes:** Estimate records on unknown nodes. When resolved, learning delta records. New circle proposals when coverage fails.

**Auto-accept vs lift:** Estimates are always tentative — they don't modify the net until verified. When the real answer arrives and the delta is small (estimate was right), the inference is confirmed → auto-accept the covering circles as verified. When the delta is large, the gap goes to lift.

---

## Existing Capabilities — What Stays, What Changes

| Current | New Role |
|---------|----------|
| Co-occurrence detection | → Raw input for circle discovery. Pairs become full group intersections. |
| Missing overlap | → Feeds circle/subtype gap detection. |
| Broken overlap | → Feeds lockout creation (why did the overlap break?). |
| Wrong pile analysis | → Feeds lockout creation (auto-accept, human confirmed). Also confidence is per-pattern (2/2 = 100%), not per-pile (2/5 = 40%). |
| Connection classification | → Feeds subtype detection. |
| Anomaly detection | → Feeds class restructuring. Redundant nodes = merge into circle. Ambiguous nodes = need lockouts. |
| Rule discovery | → Stays. Structural invariants constrain the net. |
| Sandbox eval analysis | → Feeds lift decisions. |
| Rejection pool analysis | → Feeds lockout creation (patterns that keep losing). |
| History analysis | → Feeds inference (what contexts produce unknowns). |

---

## Recursion

The whole thing is recursive. Circle discovery runs. Subtype detection runs on the circles. Class discovery runs on the circles. Then circle discovery runs AGAIN because the new circles/classes may reveal new overlaps. Each pass may unlock discoveries the previous pass couldn't see. Run until stable (no new discoveries) or max passes.

---

## Auto-Accept vs Lift Routing

| Discovery | Definite (auto-accept) | Gap (propose to lift) |
|-----------|----------------------|----------------------|
| Circle | 3+ members, 3+ shared dims | 2 members or 1-2 shared dims |
| Subtype | Within established circle (5+ members) | Within new/small circle |
| Class | 3+ member circles, 3+ shared dims | Same as circle |
| Lockout | From wrong pile (human confirmed) | From state comparison (inferred) |
| Inference | Small delta (estimate was right) | Large delta or no coverage |
| Wrong pile rules | Per-pattern 100% wrong rate | Mixed wrong rate |

---

## Build Order

1. **Fix confidence calculation** — per-pattern, not per-pile. Wrong pile auto-accepts definite patterns.
2. **Circle discovery** — replace co-occurrence pairs with full group intersection. This is the core operation everything else builds on.
3. **Lockout creation from wrong pile** — the copula problem gets fixed immediately through auto-accept.
4. **Subtype detection** — once circles exist, find structure within them.
5. **Class discovery** — once circles exist, find structure across them.
6. **Inference** — once circles and classes exist, estimate unknowns from context.
7. **State comparison** — once lockouts exist and the gate is routing, compare interpretation states to find inferred lockouts.

---

## What This Means for Lift

Lift gets simpler. It only receives gap proposals — uncertain discoveries the crystallizer isn't confident about. The T-junction tests them. The wrong-pile scoring we built still applies for evaluating gaps. But the bulk of the crystallizer's work (definite patterns) bypasses lift entirely.

---

## Net Impact

The net gets richer without getting bigger in a catastrophic way. Circles reuse existing dims — they're just pointers to intersections, not new dimensional data. Subtypes are refinements of existing structure. Classes are groupings of existing circles. Lockouts are routing constraints, not new content. The net grows in structure, not in noise.
