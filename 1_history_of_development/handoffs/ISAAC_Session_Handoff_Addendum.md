# Isaac — Session Handoff Addendum

## Five Things Worth Flagging Before Next Session

This addendum supplements ISAAC_Session_Handoff.md with points that
emerged at the end of the session. Read the main handoff first.

---

## 1. The Minimum Viable Test Is the Most Important Thing

Everything in the visual curriculum depends on one question:
**Can Isaac learn to count pixels on a 3×3 grid and generalize to novel grids?**

Do this FIRST. Before building any curriculum tier. Before more game work.
Before anything else.

```python
from isaac import Isaac
import numpy as np

isaac = Isaac()

# Generate 50 training grids with known counts
for _ in range(50):
    grid = np.random.randint(0, 2, (3, 3))
    count = int(grid.sum())
    isaac.observe_matrix(grid)
    isaac.observe([f"count_{count}"])  # the answer

isaac.consolidate()

# Test on 20 novel grids
correct = 0
for _ in range(20):
    grid = np.random.randint(0, 2, (3, 3))
    true_count = int(grid.sum())
    isaac.observe_matrix(grid)
    # Ask: what's the count?
    answer, conf = isaac.lookup(["count"])  # or however the query forms
    # Check if Isaac predicts count_{true_count}
    ...
```

**If it works:** the whole curriculum approach is validated. Every other
tier follows the same grid → question → answer pattern. Build with confidence.

**If it doesn't work:** you've found the real problem in minutes instead of
after building 3,500 examples. The failure mode tells you exactly what's
missing in the grid-to-answer binding.

This single test de-risks the entire visual program. Don't skip it.

---

## 2. observe_matrix Is Unverified Plumbing

I added observe_matrix() and observe_frame() and confirmed they RUN.
I did NOT verify they produce learnable structure.

What they do: feed each grid row as a sequence of "0" and "1" tokens,
creating doors (0→1, 1→0, 1→1, 0→0).

What's unknown: whether 4 nodes and 4 doors carry enough information for
the crystallizer to find spatial patterns. The predecessor/successor
profiles of "0" and "1" might be too uniform — "1" follows "0" everywhere,
"0" follows "1" everywhere — for meaningful types to emerge.

The MVT (point 1) tests exactly this. If counting fails, the likely cause
is that raw 0/1 sequences don't preserve enough spatial information, and
you'll need one of:
- Positional tags per row ("r0", "r1", ...) so rows are distinguishable
- Positional tags per cell (row+col encoding)
- A flattened whole-grid observation instead of row-by-row
- A 2D compile path (neighborhood patches instead of trailing substrings)

Treat observe_matrix as a hypothesis, not a solution.

---

## 3. Predictive Coding May Matter More Than the Curriculum

We opened this thread and didn't fully develop it. It deserves attention.

The insight: Isaac is currently reactive. He sees a grid, presses a button,
sees the result. He never PREDICTS. Without prediction there's no surprise,
and surprise is the only real learning signal.

The brain doesn't process what it sees — it processes the ERROR between
what it expected and what it got. Predictive coding. Pixels that match
prediction carry zero information. Pixels that violate prediction carry
all of it.

The reframe: the visual curriculum teaches Isaac to see static grids.
Prediction teaches him to anticipate dynamic ones. **Anticipation is what
actually drives gameplay.** You might find prediction is the primary
mechanism and the static curriculum is secondary scaffolding.

The loop should be:
```
see grid → press button → PREDICT next grid → see ACTUAL next grid
        → COMPARE prediction to actual → learn from the difference
```

The difference (prediction error) is the visual shrug. "I expected the
pixel here but it's there." That error is what gets observed and learned.

And it self-expands: at first he can barely predict one frame, so everything
surprises him. As one-frame predictions get accurate, surprise moves to two
frames out, then three. Multi-frame prediction IS planning.

Consider testing prediction EARLY — maybe even before the full static
curriculum. Teach Isaac: here are frames 1, 2, 3 — predict frame 4.
Simple motions first (one pixel moving in a line). If he can learn to
predict a moving pixel, the surprise-driven learning loop works, and
that may bootstrap faster than static-grid training.

---

## 4. Iteration Speed Changes the Strategy

You mentioned your CPU runs ~10x faster than this container.

That changes everything about how to approach the curriculum. On this
container, a 50-game Snake run takes minutes. On your machine, it's
seconds. A counting test with 50 examples runs near-instantly.

**The strategy this enables: build one tier, test it, move on. Don't batch.**

Don't write all 3,500 curriculum examples and then run them. Write Tier 1
counting (~200 examples), run it, verify generalization, THEN write Tier 2.
Each tier should take minutes of wall-clock time. If a tier fails, you find
out before investing in the next one.

This tight loop is only possible because of your hardware speed. Use it.
The slow-container habit of "build a lot, run once, hope it works" is
exactly backwards for your setup.

---

## 5. Add Save/Load Before Iterating on Games

Right now every run starts Isaac from scratch. Once you train the visual
curriculum, you'll want to freeze it and reload instead of retraining
every session.

It's a small addition — pickle the relevant state:

```python
import pickle

def save(self, path):
    """Save trained state to disk."""
    state = {
        "doors": dict(self.net.doors),
        "door_tags": dict(self.net.door_tags),
        "meta": dict(self.net.meta),
        "starts": self.starts,
        "types": self.types,
        "rules": self.rules,
        "lockouts": self.lockouts,
        "observed_sequences": self.observed_sequences,
        "fact_index": dict(self.fact_index),
    }
    with open(path, "wb") as f:
        pickle.dump(state, f)

def load(self, path):
    """Load trained state from disk."""
    with open(path, "rb") as f:
        state = pickle.load(f)
    self.net.doors = defaultdict(set, state["doors"])
    self.net.door_tags = defaultdict(set, state["door_tags"])
    self.net.meta = defaultdict(dict, state["meta"])
    self.starts = state["starts"]
    self.types = state["types"]
    self.rules = state["rules"]
    self.lockouts = state["lockouts"]
    self.observed_sequences = state["observed_sequences"]
    self.fact_index = defaultdict(list, state["fact_index"])
    self._compiled = None  # force recompile on next query
    self._compiled_up_to = 0
    self._consolidated_up_to = len(self.observed_sequences)
    self._dirty_nodes = set()
```

(Sets and defaultdicts need careful handling in pickle — the above is a
sketch, not tested. The door_tags keys are tuples, which pickle handles,
but verify roundtrip equality after implementing.)

Why it matters: train the spatial foundation ONCE. Save it. Then every
game session loads the pre-trained Isaac and builds on top. You're not
re-teaching him to see every time you want to test a game change.

This becomes essential the moment the curriculum works. Train once,
load many.

---

## Priority Order for Next Session

1. Run the three verification commands (isaac.py, test_pipeline.py, snake.py)
2. **Run the minimum viable counting test** (point 1) — this gates everything
3. If counting works: consider testing prediction early (point 3)
4. Add save/load (point 5) once you have something worth saving
5. Build the curriculum tier by tier, testing each (point 4)
6. Keep prediction in view as possibly the primary mechanism (point 3)

---

*Test the foundation before building on it.*
