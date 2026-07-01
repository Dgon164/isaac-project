"""
ATTENTION -> TRACKER.  Wiring the piece that was missing.

We already HAD the attention mechanism (global_baseline.GlobalBaseline): it
differences each frame against 'what's normal' (per-cell EMA + field-relative),
so it lights up what deviates and fades furniture. What was never wired: turning
that salience into "this is a thing -- track it" and adding it to a persistent
tracker that follows it across frames. This is that wire.

The flow, per frame:
  1. ATTEND   salience = baseline deviation -> where does the field break?   (the retina, wired)
  2. SEGMENT  group salient cells into blobs -> candidate things             (grouping, wired)
  3. DECIDE   a blob deviates from normal => it's a thing worth tracking
  4. ASSOCIATE match each thing to an existing track (nearest) or open a new one
  5. RECOGNIZE name it by signature -> his lookup (or leave 'unknown')        (HIS)
  6. STORE    write the tracker net into his working memory; update motion    (HIS memory)
  7. ADAPT    baseline.update -> a thing that stops moving fades to furniture

Boundary: attention/segment/associate are the wired retina + bookkeeping.
Recognition and the tracker-memory are his. The tracker net is the persistent
'memory-style matrix' of what he is currently following.
"""

import numpy as np
from isaac import Isaac
from global_baseline import GlobalBaseline
from turtle_inventory import signature, recognize, teach_shape, TURTLE, SQUARE


def regions(mask):
    """Group salient cells into blobs (8-conn). Returns (crop, centroid)."""
    H, W = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    out = []
    nbrs = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
    for y in range(H):
        for x in range(W):
            if mask[y, x] and not seen[y, x]:
                stack = [(y, x)]; seen[y, x] = True; cells = []
                while stack:
                    cy, cx = stack.pop(); cells.append((cy, cx))
                    for dy, dx in nbrs:
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < H and 0 <= nx < W and mask[ny, nx] \
                                and not seen[ny, nx]:
                            seen[ny, nx] = True; stack.append((ny, nx))
                ys = [c[0] for c in cells]; xs = [c[1] for c in cells]
                y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
                crop = np.zeros((y1 - y0 + 1, x1 - x0 + 1), dtype=int)
                for cy, cx in cells:
                    crop[cy - y0, cx - x0] = 1
                out.append((crop, (sum(ys) / len(ys), sum(xs) / len(xs))))
    return out


class Tracker:
    """The tracker net: a persistent store of things he is following, kept in
    his working memory and updated each frame."""

    def __init__(self, isaac, radius=4.0):
        self.isaac = isaac
        self.tracks = {}            # id -> {pos, frames, motion, name, sig}
        self._next = 0
        self.r = radius

    def step(self, frame, baseline, thresh=0.25):
        dev = baseline.temporal_deviation(frame)     # 1. ATTEND
        mask = dev > thresh
        things = regions(mask)                       # 2. SEGMENT
        events, claimed = [], set()
        for crop, cen in things:                     # 3. DECIDE (it deviated)
            # 4. ASSOCIATE: nearest unclaimed existing track within radius
            best, bestd = None, 1e9
            for tid, t in self.tracks.items():
                if tid in claimed:
                    continue
                d = ((t["pos"][0] - cen[0]) ** 2 + (t["pos"][1] - cen[1]) ** 2) ** 0.5
                if d < bestd:
                    bestd, best = d, tid
            name = recognize(self.isaac, crop) or "unknown"   # 5. RECOGNIZE (his)
            if best is not None and bestd <= self.r:
                t = self.tracks[best]
                t["motion"] = (round(cen[0] - t["pos"][0], 1),
                               round(cen[1] - t["pos"][1], 1))
                t["pos"], t["name"] = cen, name
                t["frames"] += 1
                claimed.add(best)
                events.append(("follow", best, name, t["motion"]))
            else:
                tid = self._next; self._next += 1
                self.tracks[tid] = {"pos": cen, "frames": 1, "motion": (0.0, 0.0),
                                    "name": name, "sig": signature(crop)}
                claimed.add(tid)
                events.append(("NEW", tid, name, (0.0, 0.0)))
        baseline.update(frame)                       # 7. ADAPT (furniture fades)
        # 6. STORE the tracker net in his working memory
        self.isaac.scratch.write("tracker", {tid: dict(t) for tid, t in self.tracks.items()})
        return events


def main():
    isaac = Isaac()
    teach_shape(isaac, TURTLE, "turtle")             # he knows turtle and square
    teach_shape(isaac, SQUARE, "square")
    isaac.consolidate()

    H, W = 9, 22
    baseline = GlobalBaseline((H, W), alpha=0.35)
    bar = np.zeros((H, W)); bar[7, 2:18] = 1         # static background "furniture"

    print("=" * 72)
    print("  ATTENTION -> TRACKER  (salience finds it, the tracker net follows it)")
    print("=" * 72)
    print("  warming the baseline on the static bar (it should become furniture)...")
    for _ in range(8):
        baseline.update(bar)

    tracker = Tracker(isaac)
    print("  now a turtle crosses; a square appears partway through.\n")
    for t in range(7):
        scene = bar.copy()
        ty, tx = 1, 1 + 2 * t                        # turtle slides right
        scene[ty:ty + 3, tx:tx + 3] = TURTLE
        if t >= 3:                                   # a square shows up at frame 3
            scene[4:7, 18:21] = SQUARE               # parked away from the turtle's path
        events = tracker.step(scene, baseline)
        desc = "  ".join(
            f"[{kind} #{tid} {name} motion{mot}]" for kind, tid, name, mot in events)
        print(f"  frame {t}: {desc if desc else '(nothing salient)'}")

    print("\n  TRACKER NET (his working memory) at the end:")
    net = isaac.scratch.read("tracker")
    for tid, t in net.items():
        print(f"    #{tid}: {t['name']:<7} pos=({t['pos'][0]:.1f},{t['pos'][1]:.1f})"
              f"  frames_seen={t['frames']}  last_motion={t['motion']}")

    print("\n" + "=" * 72)
    print("  The wire is closed: attention (GlobalBaseline) finds what deviates,")
    print("  calls it a thing, and the tracker net stores + follows it across")
    print("  frames -- identity and motion included. The static bar never got")
    print("  tracked: the baseline absorbed it as furniture. Recognition is his;")
    print("  attention is the wired retina feeding him.")


if __name__ == "__main__":
    main()
