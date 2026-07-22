"""
SHAPE VIABILITY PROBE v2 — the sig-figs design, tested before built.

v1 verdict (2026-07-22, kept for the record): speed skeleton held
(12-70x op reduction) but P2 fidelity collapsed with scale and the
P3 coherence court FAILED — real shapes lost to shuffled nulls.
Root cause, the same wall a third time: frequency-weighted signatures
keep HUB doors, which discriminate nothing. v2 changes, filed before
run: (a) signatures and scores weight doors by DISCRIMINATIVENESS
(1/df across the registry — rare shared doors carry the signal);
(b) promotion joins on weighted overlap; (c) adaptive beam — widen
the zoom when the coarse signal is weak; (d) RECURSIVE levels
(shapes of shapes) so the coarse scan stays bounded at any size.

Predictions (v2): P1 ops/entry near-flat to 100k crystals;
P2 agreement >= 95%; P3 weighted coherence beats the null >= 2x.

    python shape_viability_probe.py
"""
import math
import os
import sys
import time
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "..", "code"))
from isaac import Isaac  # noqa: E402
from boot_scale_probe import corpus  # noqa: E402

SIG_FIGS = 16        # doors kept in a shape's compressed signature
SHAPE_CAP = 32       # max members per shape
BEAM = 3             # shapes zoomed per entry (doubles when weak)
JOIN = 0.20          # min weighted-overlap ratio to join a shape
TOP_LEVEL = 64       # recurse until the top level has <= this many


def idf_of(registry):
    df = defaultdict(int)
    for sig in registry.values():
        for d in sig:
            df[d] += 1
    n = max(len(registry), 1)
    return {d: math.log(1 + n / c) for d, c in df.items()}


def wov(a, b, idf):
    """Weighted overlap: the evidence rare shared doors carry."""
    return sum(idf.get(d, 0.0) for d in (a & b))


def wsum(a, idf):
    return sum(idf.get(d, 0.0) for d in a)


def build_level(registry, idf):
    """Greedy promotion with a door->shape index (no full scans):
    a crystal joins the shape it shares the most WEIGHTED signature
    with, else founds one. Signature = top-SIG_FIGS member doors by
    (in-shape frequency x idf) — shared AND rare. Residue counted."""
    shapes = []
    door_index = defaultdict(set)          # door -> shape idx
    for name, sig in registry.items():
        cands = set()
        for d in sorted(sig, key=lambda x: -idf.get(x, 0.0)):
            cands |= door_index[d]
            if len(cands) >= 24:
                break
        best, best_ov = None, 0.0
        wself = wsum(sig, idf) or 1.0
        for si in cands:
            sh = shapes[si]
            if len(sh["members"]) >= SHAPE_CAP:
                continue
            ov = wov(sig, sh["sig"], idf) / wself
            if ov > best_ov:
                best, best_ov = si, ov
        if best is not None and best_ov >= JOIN:
            sh = shapes[best]
            sh["members"].append(name)
            for d in sig:
                sh["freq"][d] = sh["freq"].get(d, 0) + 1
            top = sorted(sh["freq"],
                         key=lambda d: sh["freq"][d] * idf.get(d, 0.0),
                         reverse=True)[:SIG_FIGS]
            sh["residue"] = len(sh["freq"]) - len(top)
            sh["sig"] = set(top)
            for d in sh["sig"]:
                door_index[d].add(best)
        else:
            si = len(shapes)
            shapes.append(dict(members=[name], sig=set(sig),
                               freq={d: 1 for d in sig}, residue=0))
            for d in sig:
                door_index[d].add(si)
    return shapes


def build_tower(registry, idf):
    """Recursive promotion — do this at every level — until the top
    level fits the working set."""
    levels = [build_level(registry, idf)]
    while len(levels[-1]) > TOP_LEVEL:
        upper_reg = {i: sh["sig"] for i, sh in enumerate(levels[-1])}
        levels.append(build_level(upper_reg, idf))
    return levels


def flat_match(entry, registry, idf):
    best, score, ops = None, -1.0, 0
    for name, sig in registry.items():
        ops += 1
        sc = wov(entry, sig, idf)
        if sc > score:
            best, score = name, sc
    return best, score, ops


def tower_match(entry, levels, registry, idf):
    """Coarse-first descent with adaptive beam: score the top level,
    zoom into the best shapes, repeat downward; widen the beam when
    the coarse signal is weak relative to the entry's own weight."""
    ops = 0
    wself = wsum(entry, idf) or 1.0
    cand_idx = range(len(levels[-1]))
    for lvl in range(len(levels) - 1, -1, -1):
        shapes = levels[lvl]
        scored = []
        for i in cand_idx:
            ops += 1
            scored.append((wov(entry, shapes[i]["sig"], idf), i))
        scored.sort(reverse=True)
        beam = BEAM if scored and scored[0][0] >= 0.3 * wself \
            else BEAM * 2
        picked = [i for _, i in scored[:beam]]
        if lvl == 0:
            best, score = None, -1.0
            for i in picked:
                for name in shapes[i]["members"]:
                    ops += 1
                    sc = wov(entry, registry[name], idf)
                    if sc > score:
                        best, score = name, sc
            return best, score, ops
        nxt = []
        for i in picked:
            nxt.extend(levels[lvl][i]["members"])
        cand_idx = nxt
    return None, -1.0, ops


def coherence(members, registry, idf):
    if len(members) < 2:
        return None
    tot, n = 0.0, 0
    for i, a in enumerate(members):
        for b in members[i + 1:]:
            sa, sb = registry[a], registry[b]
            lo = min(wsum(sa, idf), wsum(sb, idf)) or 1.0
            tot += wov(sa, sb, idf) / lo
            n += 1
    return tot / n


def courts(shapes, registry, idf, rng):
    cohs = [c for c in (coherence(s["members"], registry, idf)
                        for s in shapes) if c is not None]
    names = list(registry)
    nulls = []
    for s in shapes:
        if len(s["members"]) < 2 or len(names) < len(s["members"]):
            continue
        fake = list(rng.choice(names, size=len(s["members"]),
                               replace=False))
        c = coherence(fake, registry, idf)
        if c is not None:
            nulls.append(c)
    return (float(np.mean(cohs)) if cohs else 0.0,
            float(np.mean(nulls)) if nulls else 0.0)


def real_tier(n_tokens):
    seqs, _ = corpus(n_tokens)
    isaac = Isaac()
    isaac.wave_logging = False
    isaac.beat()
    isaac.ingest(seqs, kind="shape-probe")
    isaac.boot(beats=8)
    registry = {}
    for name, t in isaac.types.items():
        sig = set(t["preds"]) | set(t["succs"])
        if sig:
            registry[name] = sig
    idf = idf_of(registry)
    levels = build_tower(registry, idf)
    entries = []
    skip = ("type:", "job:", "seg:", "merge:", "flow:", "step:",
            "config", "boot:", "queue:", "finding:", "not_")
    for tok in sorted(isaac.net.all_nodes()):
        if tok.startswith(skip):
            continue
        e = (isaac.net.get_predecessors(tok, tag="seq")
             | isaac.net.get_doors(tok, tag="seq"))
        if len(e) >= 2:
            entries.append(e)
        if len(entries) >= 120:
            break
    agree = flat_ops = hier_ops = 0
    for e in entries:
        fb, fs, fo = flat_match(e, registry, idf)
        sb, ss, so = tower_match(e, levels, registry, idf)
        flat_ops += fo
        hier_ops += so
        if fb == sb or abs(ss - fs) < 1e-9:
            agree += 1
    n = max(len(entries), 1)
    coh, null = courts(levels[0], registry, idf,
                       np.random.default_rng(3))
    return dict(tokens=n_tokens, crystals=len(registry),
                levels=[len(lv) for lv in levels],
                flat_ops=flat_ops / n, hier_ops=hier_ops / n,
                agree=100.0 * agree / n, coh=coh, null=null,
                entries=len(entries))


def synth_tier(n_crystals, seed=5):
    rng = np.random.default_rng(seed)
    n_doors = max(200, n_crystals // 4)
    p = 1.0 / np.arange(1, n_doors + 1)
    p /= p.sum()
    registry = {}
    for i in range(n_crystals):
        k = int(rng.integers(6, 24))
        registry[f"c{i}"] = {f"d{int(x)}"
                             for x in rng.choice(n_doors, k, p=p)}
    idf = idf_of(registry)
    levels = build_tower(registry, idf)
    names = list(registry)
    entries = []
    for _ in range(60):
        base = registry[names[int(rng.integers(0, n_crystals))]]
        keep = {d for d in base if rng.random() < 0.6}
        noise = {f"d{int(x)}" for x in rng.choice(n_doors, 4, p=p)}
        entries.append(keep | noise)
    agree = flat_ops = hier_ops = 0
    t_flat = t_hier = 0.0
    for e in entries:
        t0 = time.perf_counter()
        fb, fs, fo = flat_match(e, registry, idf)
        t_flat += time.perf_counter() - t0
        t0 = time.perf_counter()
        sb, ss, so = tower_match(e, levels, registry, idf)
        t_hier += time.perf_counter() - t0
        flat_ops += fo
        hier_ops += so
        if fb == sb or abs(ss - fs) < 1e-9:
            agree += 1
    n = len(entries)
    return dict(crystals=n_crystals,
                levels=[len(lv) for lv in levels],
                flat_ops=flat_ops / n, hier_ops=hier_ops / n,
                flat_ms=1000 * t_flat / n, hier_ms=1000 * t_hier / n,
                agree=100.0 * agree / n)


if __name__ == "__main__":
    print("=" * 72)
    print("  SHAPE VIABILITY PROBE v2 — idf signatures, adaptive beam,"
          " recursion")
    print("=" * 72)

    print("\n  PART 1 — real minds")
    print("  tokens  crystals tower         ops flat->hier  agree"
          "   coherence vs null")
    for tier in (2000, 8000, 24000):
        r = real_tier(tier)
        holds = r["coh"] > 2 * r["null"]
        print(f"  {r['tokens']:>6}  {r['crystals']:>8}"
              f" {str(r['levels']):>12}"
              f"  {r['flat_ops']:>7.0f} -> {r['hier_ops']:>5.0f}"
              f"  {r['agree']:>5.1f}%"
              f"  {r['coh']:.3f} vs {r['null']:.3f}"
              f"  {'(court holds)' if holds else '(COURT FAILS)'}",
              flush=True)

    print("\n  PART 2 — synthetic registries (million-node proxy)")
    print("  crystals  tower            ops flat->hier"
          "      ms flat->hier   agree")
    for m in (200, 2000, 20000, 100000):
        r = synth_tier(m)
        print(f"  {r['crystals']:>8} {str(r['levels']):>16}"
              f"  {r['flat_ops']:>8.0f} -> {r['hier_ops']:>6.0f}"
              f"   {r['flat_ms']:>8.2f} -> {r['hier_ms']:>6.2f}"
              f"   {r['agree']:>5.1f}%", flush=True)

    print("\n  verdicts: P1 = hier ops near-flat while flat grows;"
          "\n            P2 = agree >= 95%; P3 = coherence >= 2x null.")
