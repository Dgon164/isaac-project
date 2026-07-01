# Isaac — Visual Spatial Curriculum

## Project Plan & Structural Analysis

---

## The Goal

Teach Isaac to see. Before he can play Snake, he needs to look at a grid
of 1s and 0s and understand what's in it — how many things, how big they
are, where they are, what shape they are, how they move, how they connect.

Every capability is taught the same way: show a grid, ask a question,
feed the correct answer. Same mechanism as math tables. Isaac memorizes
specific cases, crystallizes patterns, and generalizes to novel grids.

All training data is grids of 1s and 0s. No labels on the grids.
No preprocessing. No feature extraction. Questions and answers only.

---

## Capability Inventory

### Tier 1 — Primitives (no prerequisites)

These are the atomic visual skills. Everything else builds on them.

**1.1 Pixel Counting**
How many 1s are in this grid?

```
0 0 1 0 0
0 1 0 1 0     →  "count 4"
0 0 1 0 0
0 0 0 0 0
```

What it teaches: quantity from visual data. The most basic visual skill.
Grid sizes: start 3×3, scale to 5×5, then 8×8.
Training volume: hundreds of examples across all counts (0 through grid_size²).
Success: given a novel grid, Isaac answers the correct count.

**1.2 Position**
What row and column is this pixel in?

```
0 0 0 0
0 0 0 0     →  "row 2 col 3"
0 0 1 0
0 0 0 0
```

What it teaches: spatial coordinates. Where things are, not just that they exist.
Variation: single pixel at every possible position in the grid.
Training volume: every position in a 5×5 grid = 25 examples. Then novel positions in larger grids.
Success: given a single pixel in a grid, Isaac names the row and column.

**1.3 Edge Detection**
Is this pixel on the edge of the grid?

```
1 0 0 0 0
0 0 0 0 0     →  "edge yes"
0 0 0 0 0
```

```
0 0 0 0 0
0 0 1 0 0     →  "edge no"
0 0 0 0 0
```

What it teaches: boundary awareness. The grid has limits.
Training volume: pixels at edges vs interior, across grid sizes.
Success: correctly identifies edge vs interior for any position.

---

### Tier 2 — Spatial Relations (requires Tier 1)

These combine two or more positions to create relational understanding.

**2.1 Distance**
How far apart are these two pixels?

```
0 1 0 0 0
0 0 0 0 0     →  "distance 5"
0 0 0 0 0
0 0 0 1 0
```

What it teaches: spatial measurement. Manhattan distance (grid steps) is
the natural unit since the grid is discrete.
Prerequisite: position (need to locate both pixels first).
Training: pairs of pixels at every distance from 1 to grid diagonal.
Variation: "closer to edge" — which pixel is nearer to the border?
Success: correct distance for novel pixel pairs.

**2.2 Relative Direction**
Which direction is pixel B from pixel A?

```
0 A 0 0 0
0 0 0 0 0     →  "B is down_right from A"
0 0 0 B 0
```

(Shown as two 1s — Isaac figures out which is "from" and which is "to"
based on question format.)

What it teaches: directional relationships. The foundation of "food is to the right."
Prerequisite: position.
Training: all 8 directions (up, down, left, right, and diagonals) at various distances.
Success: correct direction for any pair of pixels.

**2.3 Adjacency**
Are these two pixels neighbors?

```
0 1 1 0     →  "adjacent yes"

0 1 0 1     →  "adjacent no"
```

What it teaches: the concept of "next to." Foundation for connectedness.
Prerequisite: position, distance.
Training: pairs at distance 1 (adjacent) vs distance 2+ (not adjacent).
Include diagonal adjacency as a variant.
Success: correctly identifies adjacent vs non-adjacent.

---

### Tier 3 — Connectedness & Grouping (requires Tier 2)

This is where individual pixels become objects.

**3.1 Connected**
Are all the 1s one connected group?

```
0 1 1 0 0
0 0 1 0 0     →  "connected yes"
0 0 1 1 0

0 1 0 0 0
0 0 0 0 0     →  "connected no"
0 0 0 1 0
```

What it teaches: contiguity. The difference between one object and two.
Prerequisite: adjacency.
Training: grids with single connected groups vs multiple disconnected groups.
Vary shapes, sizes, and separation distances.
Success: correctly identifies connected vs disconnected.

**3.2 Object Counting**
How many separate groups of 1s?

```
1 1 0 0 1
0 0 0 0 1     →  "objects 3"
0 1 0 0 0
0 1 0 0 0
```

What it teaches: segmentation. Distinguishing multiple objects.
Prerequisite: connected.
Training: grids with 1 through 6 objects, various sizes and positions.
Success: correct object count for novel grids.

**3.3 Which Object Is Bigger?**

```
1 1 1 0 0
0 0 0 0 0     →  "top bigger" or "first 3 second 1"
0 0 0 0 1
```

What it teaches: relative size comparison between objects.
Prerequisite: object counting, pixel counting.
Training: pairs of objects at various sizes.
Success: correctly identifies the larger object.

---

### Tier 4 — Lines & Length (requires Tier 3)

**4.1 Line Detection**
Is this a line (all pixels in a row or column)?

```
0 0 0 0 0
1 1 1 1 0     →  "line yes horizontal"
0 0 0 0 0

0 1 0
0 1 0         →  "line yes vertical"
0 1 0
0 1 0

1 0 0
0 1 0         →  "line yes diagonal"
0 0 1
```

What it teaches: linearity. Pixels arranged in a straight sequence.
Prerequisite: connected, adjacency.
Training: horizontal, vertical, and diagonal lines of varying lengths.
Also non-lines (L-shapes, clusters) as negative examples.
Success: correctly identifies lines and their orientation.

**4.2 Length**
How long is this line (or connected object)?

```
0 1 1 1 1 0     →  "length 4"

0 1 0
0 1 0            →  "length 3"
0 1 0
```

What it teaches: measuring contiguous extent.
Prerequisite: line detection, connected.
Training: lines of length 1 through grid_size in all orientations.
Also measure non-line objects (L-shapes etc.) by total pixel count.
Success: correct length for any line or object.

**4.3 Endpoint Detection**
Where does this line start and end?

```
0 0 0 0 0
0 1 1 1 0     →  "start row 1 col 1 end row 1 col 3"
0 0 0 0 0
```

What it teaches: boundaries of an object. Head and tail.
Prerequisite: line detection, position.
Training: lines in all orientations with start/end coordinates.
This directly maps to Snake: the head and tail are endpoints of a line.
Success: correct start and end positions.

---

### Tier 5 — Shapes & Patterns (requires Tier 4)

**5.1 Shape Recognition**
What shape is this group of pixels?

```
1 1 1
1 0 1     →  "square" (or "ring" or "frame")
1 1 1

1 1 1
1 1 1     →  "rectangle"

1 0 0
1 0 0     →  "L_shape"
1 1 1

1 1 1
0 1 0     →  "T_shape"
```

What it teaches: named patterns of pixels. The crystallizer should discover
that certain arrangements recur and have shared properties.
Prerequisite: connected, line detection.
Training: standard shapes in all orientations and sizes.
Success: correct shape name for novel instances.

**5.2 Symmetry**
Is this shape symmetric?

```
0 1 0
1 1 1     →  "symmetric yes"
0 1 0

1 0 0
1 1 0     →  "symmetric no"
1 0 0
```

What it teaches: visual regularity. A higher-order structural property.
Prerequisite: shape recognition.
Training: symmetric and asymmetric shapes.
Variation: horizontal symmetry vs vertical symmetry.

**5.3 Pattern Repetition**
Is there a repeating pattern?

```
1 0 1 0 1 0     →  "pattern yes period 2"

1 1 0 1 1 0     →  "pattern yes period 3"

1 0 1 1 0 0     →  "pattern no"
```

What it teaches: regularity over space. Foundation for texture recognition.
Prerequisite: counting, length.
Training: 1D patterns (single rows) first, then 2D.

**5.4 Corners and Turns**
Does this line change direction?

```
1 1 1
0 0 1     →  "turn yes right_down"
0 0 1

1 1 1 1     →  "turn no straight"
```

What it teaches: angle detection. Where a line bends.
Prerequisite: line detection, direction.
Training: lines with 0, 1, 2+ turns. All directions.
This directly maps to Snake: the body has turns where the player changed direction.

---

### Tier 6 — Temporal / Multi-Frame (requires all above)

Everything above is single-frame. This tier adds time.

**6.1 Change Detection**
What changed between these two grids?

```
Frame 1:          Frame 2:
0 0 0 0 0         0 0 0 0 0
0 1 0 0 0    →    0 0 1 0 0     →  "pixel moved right"
0 0 0 0 0         0 0 0 0 0
```

What it teaches: temporal differencing. The foundation of motion perception.
Prerequisite: position, pixel counting.
Training: single pixel moves (all directions), pixel appears, pixel disappears.
Success: correctly describes what changed.

**6.2 Movement / Velocity**
Which direction and how fast is this object moving?

```
Frame 1:     Frame 2:     Frame 3:
0 0 0 0      0 0 0 0      0 0 0 0
1 0 0 0  →   0 1 0 0  →   0 0 1 0    →  "moving right speed 1"
0 0 0 0      0 0 0 0      0 0 0 0
```

What it teaches: motion tracking. Velocity = direction + speed.
Prerequisite: change detection, direction.
Training: objects moving in all directions at speeds 1-3.
Multi-frame sequences (3-5 frames).
Success: predict next position given motion history.

**6.3 Prediction**
Given these frames, what does the next frame look like?

```
Frame 1:     Frame 2:     Frame 3:
0 1 0 0      0 0 1 0      0 0 0 1     →  predict Frame 4:  0 0 0 0
0 0 0 0      0 0 0 0      0 0 0 0                          1 0 0 0
                                                            (wraps? or hits wall?)
```

What it teaches: extrapolation. The core of planning.
Prerequisite: movement.
Training: simple motions with predictable continuations.
Include wall bounces, wrapping, and stopping as variations.
The surprise signal: compare Isaac's prediction to reality. The error IS the learning.
Success: accurate frame prediction for simple motions.

**6.4 Growth / Shrinkage**

```
Frame 1:        Frame 2:
0 1 1 0    →    0 1 1 1      →  "grew right by 1"
0 0 0 0         0 0 0 0
```

What it teaches: objects can change size. Directly maps to Snake eating food.
Prerequisite: length, change detection.
Training: lines that grow (add pixel at one end) and shrink (remove pixel at one end).
This IS the snake body growing after eating.
Success: correctly identifies growth direction and amount.

**6.5 Object Persistence**

```
Frame 1:        Frame 2:
1 1 0 0 0       0 1 1 0 0      →  "same object moved right"
0 0 0 0 1       0 0 0 0 1      →  "second object unchanged"
```

What it teaches: objects persist across frames. The moving pixels are the same
thing, not a new thing. The stationary pixels are also the same thing.
Prerequisite: object counting, movement.
This is the key Snake insight: the snake is ONE persistent object that moves.
The food is another persistent object that stays still until touched.

**6.6 Cause and Effect**

```
Frame 1:         →  press "right"  →  Frame 2:
0 0 1 0 0                             0 0 0 1 0
0 0 0 0 0                             0 0 0 0 0
```

What it teaches: MY ACTION caused THIS CHANGE. The button press → pixel movement
connection. This is agency.
Prerequisite: movement, prediction.
Training: simple objects that move when a button is pressed.
One object, one direction per button. Then more complex.
This is the direct precursor to Snake: pressing right moves the head right.

---

## Dependency Graph

```
Tier 1 (primitives):
  1.1 Pixel Counting
  1.2 Position
  1.3 Edge Detection

Tier 2 (relations):       requires Tier 1
  2.1 Distance            ← 1.2
  2.2 Direction            ← 1.2
  2.3 Adjacency            ← 1.2, 2.1

Tier 3 (grouping):        requires Tier 2
  3.1 Connected            ← 2.3
  3.2 Object Counting      ← 3.1, 1.1
  3.3 Size Comparison      ← 3.2, 1.1

Tier 4 (lines):           requires Tier 3
  4.1 Line Detection       ← 3.1, 2.3
  4.2 Length                ← 4.1, 1.1
  4.3 Endpoints             ← 4.1, 1.2

Tier 5 (shapes):          requires Tier 4
  5.1 Shape Recognition    ← 3.1, 4.1
  5.2 Symmetry             ← 5.1
  5.3 Pattern Repetition   ← 1.1, 4.2
  5.4 Corners / Turns      ← 4.1, 2.2

Tier 6 (temporal):        requires Tier 5
  6.1 Change Detection     ← 1.2, 1.1
  6.2 Movement             ← 6.1, 2.2
  6.3 Prediction           ← 6.2
  6.4 Growth               ← 4.2, 6.1
  6.5 Object Persistence   ← 3.2, 6.2
  6.6 Cause and Effect     ← 6.2, 6.3

Snake readiness:          requires 6.4, 6.5, 6.6
```

---

## Teaching Method

Every capability uses the same loop:

```
1. Generate a grid (training data)
2. Feed the grid to Isaac (observe_matrix)
3. Feed the question (observe tokens)
4. Feed the correct answer (observe tokens)
5. Repeat with variations
6. Test: feed grid + question, check Isaac's answer
7. If wrong: feed correct answer (correction)
8. If right: move to harder examples
```

This is identical to how math tables work:
- "3 + 5 = 8" → observe, memorize
- "3 + 5 = ?" → lookup → "8" (correct, confident)
- "47 + 83 = ?" → shrug → decompose → compute → memorize

For spatial skills:
- grid + "count = 4" → observe, memorize
- similar grid + "count = ?" → lookup → "4" (correct)
- harder grid + "count = ?" → shrug → needs more examples or decomposition

---

## Scaling Plan

**Phase 1: 3×3 grids**
Tiny. Every possible configuration is tractable (2⁹ = 512 possible grids).
Teach Tiers 1-3 exhaustively on 3×3.
Goal: Isaac handles all counting, position, distance, adjacency, and
connectedness queries on 3×3 grids.

**Phase 2: 5×5 grids**
Medium. Too many configurations to exhaustively cover (2²⁵ = 33 million).
Isaac must generalize from training examples to novel grids.
Teach Tiers 1-5.
Goal: Isaac handles lines, shapes, lengths, and patterns on 5×5.

**Phase 3: 8×8 grids**
Larger. This is where the crystallizer needs to have discovered
spatial types (lines, clusters, edges) that transfer from smaller grids.
Teach Tier 6 (temporal) here — multi-frame sequences.
Goal: Isaac predicts next frames and tracks objects on 8×8.

**Phase 4: 15×15 grids (Snake-size)**
Full game scale. Isaac should need minimal additional training at this
size if the spatial concepts transfer from smaller grids.
Teach cause-and-effect with buttons.
Goal: Isaac plays Snake.

---

## Training Volume Estimates

| Capability | Examples needed | Grid sizes |
|---|---|---|
| 1.1 Pixel Counting | ~200 | 3×3, 5×5 |
| 1.2 Position | ~50 | 3×3, 5×5 |
| 1.3 Edge Detection | ~50 | 3×3, 5×5 |
| 2.1 Distance | ~200 | 5×5 |
| 2.2 Direction | ~100 | 5×5 |
| 2.3 Adjacency | ~100 | 3×3, 5×5 |
| 3.1 Connected | ~200 | 3×3, 5×5 |
| 3.2 Object Counting | ~200 | 5×5 |
| 3.3 Size Comparison | ~100 | 5×5 |
| 4.1 Line Detection | ~200 | 5×5, 8×8 |
| 4.2 Length | ~200 | 5×5, 8×8 |
| 4.3 Endpoints | ~100 | 5×5 |
| 5.1 Shapes | ~200 | 5×5, 8×8 |
| 5.2 Symmetry | ~100 | 5×5 |
| 5.3 Patterns | ~100 | 5×5, 8×8 |
| 5.4 Corners | ~100 | 5×5, 8×8 |
| 6.1 Change Detection | ~200 | 5×5, 8×8 |
| 6.2 Movement | ~200 | 5×5, 8×8 |
| 6.3 Prediction | ~300 | 5×5, 8×8 |
| 6.4 Growth | ~200 | 5×5, 8×8 |
| 6.5 Object Persistence | ~200 | 8×8 |
| 6.6 Cause and Effect | ~300 | 8×8, 15×15 |
| **Total** | **~3,500** | |

This is comparable to the math tables (20×20 = 400 addition + 400 multiplication)
but across more capability dimensions.

---

## Connection to Snake

Each Snake skill maps directly to a curriculum capability:

| Snake need | Curriculum source |
|---|---|
| See the board | 1.1 counting, 1.2 position |
| Know where the walls are | 1.3 edge detection |
| Know where food is | 2.1 distance, 2.2 direction |
| Know the snake is one thing | 3.1 connected |
| Know food is a separate thing | 3.2 object counting |
| Know how long the snake is | 4.2 length |
| Know where head and tail are | 4.3 endpoints |
| Know the snake has turns | 5.4 corners |
| See that the head moved | 6.1 change detection |
| Know which way it's going | 6.2 movement |
| Predict where it will be | 6.3 prediction |
| See that it grew after eating | 6.4 growth |
| Track snake vs food across frames | 6.5 persistence |
| Know that buttons cause movement | 6.6 cause and effect |

When all of these are solid, Snake is just applying them together.

---

## What We Don't Teach

- Color (everything is 1s and 0s)
- Names for objects (no "this is a snake" — Isaac discovers identity from behavior)
- Strategy (no "go toward food" — Isaac discovers this from consequences)
- Game rules (no "hitting walls kills you" — Isaac learns this from experience)

The curriculum teaches perception. The game teaches behavior.

---

## Additional Capabilities Worth Including

**Density / Fill**
What fraction of the grid is filled? Sparse vs dense.
Useful for: recognizing when the Snake board is getting crowded.

**Enclosure**
Is this group of pixels enclosed? Is there empty space surrounded by 1s?
Useful for: recognizing traps — the snake forming a loop around empty space.

**Path Existence**
Is there a clear path from A to B?
Useful for: the fundamental Snake planning question — can I reach the food
without hitting myself?

**Orientation / Heading**
Which way does this L-shape point? Which end of a line is the "front"?
Useful for: knowing which way the snake is facing.

**Proximity Warning**
Is this object close to the edge? Close to another object?
Useful for: danger awareness — am I about to hit the wall?

---

## Open Questions

**Q1: How does Isaac represent a grid internally?**
observe_matrix feeds rows as sequences of "0" and "1" tokens.
This creates doors: "0"→"1", "1"→"0", "1"→"1", "0"→"0".
Are 4 nodes and 4 doors enough to learn spatial structure?
Or does Isaac need positional encoding (row/column tags) to
distinguish row 0 from row 5?

**Q2: How does the grid connect to the question/answer?**
The grid is observed row by row. Then the question is observed.
Then the answer. But the compile step creates frames from trailing
subsequences — so the frame for the answer only includes the last
few tokens of the last row + the question. It doesn't include the
full grid. Is partial-grid context enough, or does Isaac need the
full grid to answer?

**Q3: Does the crystallizer discover spatial types from grid data?**
In language, it discovers noun/verb types from shared contexts.
In grids, will it discover "line" and "dot" and "L-shape" as types?
The predecessor/successor profiles of grid tokens might be too
uniform ("1" follows "0" and "0" follows "1" everywhere) for the
crystallizer to find meaningful structure.

**Q4: Should we add a spatial compile path?**
The current compile creates 1D frame tuples from sequences.
Spatial data might need 2D frame tuples — neighborhoods or patches
instead of trailing substrings. This would be an architectural
addition, not a change.

**Q5: What's the minimum viable test?**
Before building the full curriculum: teach Isaac to count pixels
on a 3×3 grid. If he can learn "this grid has 3 lit pixels"
from 50 examples and generalize to novel grids, the approach works.
If not, we know where the gap is before investing in 3,500 examples.

---

*Teach him to see before asking him to play.*
