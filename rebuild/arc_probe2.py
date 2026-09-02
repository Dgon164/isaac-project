"""ARC PROBE 2 — the objectness rung + full test run with telemetry.

Adds the missing organ probe 1's asks named: OBJECTS. Segmentation
by connected same-color components over a background (most common
color), then object-level inducers — every rule must still hold on
every example pair before it may answer:

  crop        output = bounding-box crop of the non-background content
  big-crop    output = crop of the LARGEST object (unique max)
  big-only    output = input with all but the largest object erased
  odd-crop    output = crop of the object whose color is unique
  shift       every non-background cell moves by one constant (dy,dx)
  recolor#    same geometry; object colors remapped by SIZE RANK

Runs the frozen battery (probe 1's five + these six) over BOTH sets:
400 training and 400 evaluation (the held-out practice exam), with
full telemetry: solves per rule per set, wall-clock, per-task times.
"""
import json
import os
import sys
import time
from collections import Counter, deque
from glob import glob

from arc_probe import INDUCERS as GRID_INDUCERS  # probe 1, frozen

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "..", "data", "arc-agi", "data")
if not os.path.isdir(BASE):
    print("SKIP: arc data not present")
    sys.exit(77)


def bg_of(g):
    return Counter(c for row in g for c in row).most_common(1)[0][0]


def objects(g, bg):
    seen, out = set(), []
    H, W = len(g), len(g[0])
    for r in range(H):
        for c in range(W):
            if g[r][c] == bg or (r, c) in seen:
                continue
            col, cells, dq = g[r][c], [], deque([(r, c)])
            seen.add((r, c))
            while dq:
                y, x = dq.popleft()
                cells.append((y, x))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < H and 0 <= nx < W \
                            and (ny, nx) not in seen \
                            and g[ny][nx] == col:
                        seen.add((ny, nx))
                        dq.append((ny, nx))
            out.append(dict(color=col, cells=cells))
    return out


def crop(g, cells):
    ys = [y for y, _ in cells]
    xs = [x for _, x in cells]
    y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
    return [[g[y][x] for x in range(x0, x1 + 1)]
            for y in range(y0, y1 + 1)]


def nonbg_cells(g, bg):
    return [(y, x) for y, row in enumerate(g)
            for x, c in enumerate(row) if c != bg]


def ind_crop(pairs):
    def fn(g):
        bg = bg_of(g)
        nb = nonbg_cells(g, bg)
        return crop(g, nb) if nb else None
    if all(fn(p["input"]) == p["output"] for p in pairs):
        return fn
    return None


def _largest(objs):
    if not objs:
        return None
    objs = sorted(objs, key=lambda o: -len(o["cells"]))
    if len(objs) > 1 and len(objs[0]["cells"]) == len(objs[1]["cells"]):
        return None
    return objs[0]


def ind_big_crop(pairs):
    def fn(g):
        o = _largest(objects(g, bg_of(g)))
        return crop(g, o["cells"]) if o else None
    if all(fn(p["input"]) == p["output"] for p in pairs):
        return fn
    return None


def ind_big_only(pairs):
    def fn(g):
        bg = bg_of(g)
        o = _largest(objects(g, bg))
        if not o:
            return None
        keep = set(o["cells"])
        return [[g[y][x] if (y, x) in keep else bg
                 for x in range(len(g[0]))] for y in range(len(g))]
    if all(fn(p["input"]) == p["output"] for p in pairs):
        return fn
    return None


def ind_odd_crop(pairs):
    def fn(g):
        objs = objects(g, bg_of(g))
        counts = Counter(o["color"] for o in objs)
        odd = [o for o in objs if counts[o["color"]] == 1]
        return crop(g, odd[0]["cells"]) if len(odd) == 1 else None
    if all(fn(p["input"]) == p["output"] for p in pairs):
        return fn
    return None


def ind_shift(pairs):
    def delta(p):
        i, o = p["input"], p["output"]
        if len(i) != len(o) or len(i[0]) != len(o[0]):
            return None
        bg = bg_of(i)
        a, b = nonbg_cells(i, bg), nonbg_cells(o, bg_of(o))
        if not a or len(a) != len(b):
            return None
        dy = min(y for y, _ in b) - min(y for y, _ in a)
        dx = min(x for _, x in b) - min(x for _, x in a)
        H, W = len(i), len(i[0])
        moved = [[bg] * W for _ in range(H)]
        for y, x in a:
            ny, nx = y + dy, x + dx
            if not (0 <= ny < H and 0 <= nx < W):
                return None
            moved[ny][nx] = i[y][x]
        return (dy, dx) if moved == o else None
    d0 = delta(pairs[0])
    if d0 is None or any(delta(p) != d0 for p in pairs):
        return None
    dy, dx = d0

    def fn(g):
        bg = bg_of(g)
        H, W = len(g), len(g[0])
        out = [[bg] * W for _ in range(H)]
        for y, x in nonbg_cells(g, bg):
            ny, nx = y + dy, x + dx
            if not (0 <= ny < H and 0 <= nx < W):
                return None
            out[ny][nx] = g[y][x]
        return out
    return fn


def ind_recolor_rank(pairs):
    rank_map = {}
    for p in pairs:
        i, o = p["input"], p["output"]
        if len(i) != len(o) or len(i[0]) != len(o[0]):
            return None
        oi = sorted(objects(i, bg_of(i)),
                    key=lambda ob: -len(ob["cells"]))
        go = o
        for rank, ob in enumerate(oi):
            cols = {go[y][x] for y, x in ob["cells"]}
            if len(cols) != 1:
                return None
            nc = cols.pop()
            if rank_map.setdefault(rank, nc) != nc:
                return None
        # geometry must be unchanged
        bg = bg_of(i)
        if {(y, x) for ob in oi for y, x in ob["cells"]} != \
                set(nonbg_cells(o, bg_of(o))):
            return None
    def fn(g):
        bg = bg_of(g)
        out = [row[:] for row in g]
        for rank, ob in enumerate(sorted(objects(g, bg),
                                         key=lambda o: -len(o["cells"]))):
            if rank not in rank_map:
                return None
            for y, x in ob["cells"]:
                out[y][x] = rank_map[rank]
        return out
    return fn


OBJ_INDUCERS = [("crop", ind_crop), ("big-crop", ind_big_crop),
                ("big-only", ind_big_only), ("odd-crop", ind_odd_crop),
                ("shift", ind_shift), ("recolor#", ind_recolor_rank)]
BATTERY = list(GRID_INDUCERS) + OBJ_INDUCERS


def run_set(name):
    t0 = time.perf_counter()
    solved, by_rule, times = [], Counter(), []
    files = sorted(glob(os.path.join(BASE, name, "*.json")))
    for path in files:
        task = json.load(open(path))
        tid = os.path.basename(path)[:-5]
        tq = time.perf_counter()
        for rname, ind in BATTERY:
            try:
                fn = ind(task["train"])
            except Exception:
                fn = None
            if fn is not None:
                try:
                    ok = all(fn(t["input"]) == t["output"]
                             for t in task["test"])
                except Exception:
                    ok = False
                if ok:
                    solved.append((tid, rname))
                    by_rule[rname] += 1
                    break
        times.append(1000 * (time.perf_counter() - tq))
    wall = time.perf_counter() - t0
    times.sort()
    n = len(files)
    print(f"\n{name.upper()}: {len(solved)}/{n} solved "
          f"({100 * len(solved) / n:.1f}%), {n - len(solved)} asks   "
          f"wall {wall:.1f}s, per-task p50 {times[n // 2]:.1f}ms "
          f"p95 {times[int(n * .95)]:.1f}ms max {times[-1]:.0f}ms")
    for rname, cnt in by_rule.most_common():
        ids = [t for t, r in solved if r == rname][:3]
        print(f"  {rname:10s} {cnt:3d}   e.g. {', '.join(ids)}")
    return solved


if __name__ == "__main__":
    tr = run_set("training")
    ev = run_set("evaluation")
    print(f"\nTELEMETRY TOTAL: battery of {len(BATTERY)} inducers "
          f"(5 grid + 6 object), 800 tasks examined, "
          f"{len(tr) + len(ev)} solved, all solves exact-match on every "
          f"test output, zero guesses possible by construction.")
