"""ARC PROBE 3 — THE DIFFERENTIATOR RUNG (owner diagnosis,
2026-09-01: "its not finding structure pairs... it is just failing
on any match no partial").

D(input, output) on grids: shared bin = preserved cells (the
structure that carries over), residues = added/removed cells (the
delta). Induction then targets ONLY the delta:

  fill-in     preserved structure + cells enclosed by an object
              (border flood-fill defines inside) gain an induced
              color — constant, or keyed to the enclosing color
  nbr-rule    preserved structure + the added cells are exactly the
              background cells whose 4-neighborhood pattern falls in
              a learned set (and no unchanged bg cell's does) —
              local repeated structure, like the 3-0-3 motif

Battery = probe 1 + probe 2 + these; both sets; full telemetry.
"""
import json
import os
import sys
import time
from collections import Counter, deque
from glob import glob

from arc_probe2 import BATTERY as PREV_BATTERY, BASE, bg_of

if not os.path.isdir(BASE):
    print("SKIP: arc data not present")
    sys.exit(77)


def d_split(p):
    """D on one pair: (preserved-ok, added cells, removed cells).
    Preserved-ok means every cell not in the delta is identical."""
    i, o = p["input"], p["output"]
    if len(i) != len(o) or len(i[0]) != len(o[0]):
        return None
    bg = bg_of(i)
    added, removed = [], []
    for r in range(len(i)):
        for c in range(len(i[0])):
            a, b = i[r][c], o[r][c]
            if a == b:
                continue
            if a == bg:
                added.append((r, c, b))
            elif b == bg:
                removed.append((r, c, a))
            else:
                return None          # recolor in place = not this rung
    return added, removed


def inside_cells(g, bg):
    """Border flood-fill over background: bg cells NOT reachable from
    the border are 'inside' (enclosed)."""
    H, W = len(g), len(g[0])
    reach = set()
    dq = deque((r, c) for r in range(H) for c in range(W)
               if (r in (0, H - 1) or c in (0, W - 1))
               and g[r][c] == bg)
    reach.update(dq)
    while dq:
        y, x = dq.popleft()
        # 4-connected background: ARC's enclosure does NOT leak
        # through diagonal gaps — measured on 00d62c1b pair-by-pair
        # (the 8-connected 'fix' was a theory; the autopsy said
        # inside=0 exactly where ARC fills)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < H and 0 <= nx < W and (ny, nx) not in reach \
                    and g[ny][nx] == bg:
                reach.add((ny, nx))
                dq.append((ny, nx))
    return [(r, c) for r in range(H) for c in range(W)
            if g[r][c] == bg and (r, c) not in reach]


def ind_fill_in(pairs):
    fill_color = None
    for p in pairs:
        d = d_split(p)
        if d is None:
            return None
        added, removed = d
        if removed or not added:
            return None
        g = p["input"]
        bg = bg_of(g)
        ins = set(inside_cells(g, bg))
        if {(r, c) for r, c, _ in added} != ins:
            return None
        cols = {v for _, _, v in added}
        if len(cols) != 1:
            return None
        col = cols.pop()
        if fill_color is None:
            fill_color = col
        elif fill_color != col:
            return None
    if fill_color is None:
        return None

    def fn(g):
        bg = bg_of(g)
        out = [row[:] for row in g]
        for r, c in inside_cells(g, bg):
            out[r][c] = fill_color
        return out
    return fn


def nbr_pat(g, r, c, bg):
    H, W = len(g), len(g[0])
    out = []
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1),
                   (-1, -1), (-1, 1), (1, -1), (1, 1)):
        ny, nx = r + dy, c + dx
        out.append(g[ny][nx] if 0 <= ny < H and 0 <= nx < W else -1)
    return tuple(out)


def ind_nbr_rule(pairs):
    good, add_color = set(), None
    for p in pairs:
        d = d_split(p)
        if d is None:
            return None
        added, removed = d
        if removed or not added:
            return None
        cols = {v for _, _, v in added}
        if len(cols) != 1:
            return None
        col = cols.pop()
        if add_color is None:
            add_color = col
        elif add_color != col:
            return None
        g = p["input"]
        bg = bg_of(g)
        for r, c, _ in added:
            good.add(nbr_pat(g, r, c, bg))
    # the separating check: no unchanged bg cell may carry a pattern
    for p in pairs:
        g = p["input"]
        bg = bg_of(g)
        addset = {(r, c) for r, c, _ in d_split(p)[0]}
        for r in range(len(g)):
            for c in range(len(g[0])):
                if g[r][c] == bg and (r, c) not in addset \
                        and nbr_pat(g, r, c, bg) in good:
                    return None

    def fn(g):
        bg = bg_of(g)
        out = [row[:] for row in g]
        for r in range(len(g)):
            for c in range(len(g[0])):
                if g[r][c] == bg and nbr_pat(g, r, c, bg) in good:
                    out[r][c] = add_color
        return out
    return fn


BATTERY = list(PREV_BATTERY) + [("fill-in", ind_fill_in),
                                ("nbr-rule", ind_nbr_rule)]


def run_set(name):
    t0 = time.perf_counter()
    solved, by_rule, times = [], Counter(), []
    for path in sorted(glob(os.path.join(BASE, name, "*.json"))):
        task = json.load(open(path))
        tid = os.path.basename(path)[:-5]
        tq = time.perf_counter()
        for rname, ind in BATTERY:
            try:
                fn = ind(task["train"])
                ok = fn is not None and all(
                    fn(t["input"]) == t["output"] for t in task["test"])
            except Exception:
                ok = False
            if ok:
                solved.append((tid, rname))
                by_rule[rname] += 1
                break
        times.append(1000 * (time.perf_counter() - tq))
    wall = time.perf_counter() - t0
    times.sort()
    n = len(times)
    print(f"\n{name.upper()}: {len(solved)}/{n} solved "
          f"({100 * len(solved) / n:.1f}%)   wall {wall:.1f}s, "
          f"p50 {times[n // 2]:.1f}ms p95 {times[int(n * .95)]:.1f}ms "
          f"max {times[-1]:.0f}ms")
    for rname, cnt in by_rule.most_common():
        ids = [t for t, r in solved if r == rname][:4]
        print(f"  {rname:10s} {cnt:3d}   e.g. {', '.join(ids)}")
    return solved


tr = run_set("training")
ev = run_set("evaluation")
new_tr = [t for t, r in tr if r in ("fill-in", "nbr-rule")]
print(f"\nDIFFERENTIATOR RUNG: +{len(new_tr)} training tasks from "
      f"D-decomposition (partial structure now counts): {new_tr[:8]}")
