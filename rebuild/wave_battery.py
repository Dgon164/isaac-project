"""
WAVE CRYSTALLIZER — full-pass test battery.

Parameterized generator + scorer. Every run: planted processes wave through
door-groups among noise doors; the mechanism must recover groups (simultaneity),
handoff edges (movement), circles. Metrics are plain percentages; every run is
logged to wave_battery_results.csv as it happens (scaling discipline, audit 2.13).

Experiments (failure hypotheses stated up front):
  E1 stream length      — onset curve: how much stream before detection turns on
  E2 sensor flicker     — active doors fire with p<1
  E3 background noise   — noise-door count and rate
  E4 dwell/period       — H1: waves whose PERIOD fits inside the jitter range
                          (2-5 steps) are killed by their own null, by construction
  E5 handoff lag        — H2: a gap >=2 steps between off and on falls outside
                          the +-1 co-timing window; the wave becomes invisible
  E6 concurrency        — many independent waves at once
  E7 shared doors       — H3: groups sharing doors merge (connected components)
  E8 pure noise         — false-positive rates (should be ~0)
  E9 irregular dwell    — aperiodic waves (no clock): should still work,
                          co-timing is the claim, not periodicity
"""
import csv
import time
import numpy as np
import wave_crystallizer as wc

CSV = "wave_battery_results.csv"


# ------------------------------------------------------------- generator
def gen(cfg, rng):
    """Build a stream from planted processes.

    cfg: n_proc, groups_per_proc, group_size, dwell (int or 'irregular'),
         lag, share (doors shared between adjacent groups of proc 0),
         T, noise_doors, noise_p, flicker, rephase_every
    Returns S, truth = {groups, edges, circles} (global group ids).
    """
    n_proc = cfg.get("n_proc", 1)
    gpp = cfg.get("groups_per_proc", 3)
    gsize = cfg.get("group_size", 4)
    dwell = cfg.get("dwell", 3)
    lag = cfg.get("lag", 0)
    share = cfg.get("share", 0)
    T = cfg.get("T", 1500)
    nd = cfg.get("noise_doors", 12)
    noise_p = cfg.get("noise_p", 0.3)
    flicker = cfg.get("flicker", 0.9)
    rephase = cfg.get("rephase_every", 150)

    groups, gid = [], 0
    door = 0
    for p in range(n_proc):
        for g in range(gpp):
            members = list(range(door, door + gsize))
            if p == 0 and share > 0 and g > 0:
                members[:share] = groups[gid - 1][-share:]   # overlap with prev
            groups.append(members)
            door = max(door, members[-1] + 1)
            gid += 1
    D = door + nd
    S = np.zeros((T, D))

    truth_edges, truth_circles = set(), []
    for p in range(n_proc):
        base = p * gpp
        truth_circles.append(tuple(base + g for g in range(gpp)))
        for g in range(gpp):
            truth_edges.add((base + g, base + (g + 1) % gpp))

    for p in range(n_proc):
        base = p * gpp
        t = int(rng.integers(0, 7))
        while t < T:
            if cfg.get("start_phase_random", True):
                pass
            phase_order = range(gpp)
            for g in phase_order:
                d = int(rng.integers(2, 9)) if dwell == "irregular" else dwell
                for _ in range(d):
                    if t >= T:
                        break
                    S[t, groups[base + g]] = 1
                    t += 1
                t += lag                                    # gap before next phase
            if rephase and rng.random() < (1.0 / max(1, rephase // (gpp * (dwell if dwell != "irregular" else 5)))):
                t += int(rng.integers(2, 9))                # decohere processes

    drivers = S[:, :door]
    fired = np.where(drivers == 1, rng.random(drivers.shape) < flicker,
                     rng.random(drivers.shape) < 0.05)
    noise = rng.random((T, nd)) < noise_p
    S = np.column_stack([fired, noise]).astype(float)
    return S, {"groups": [tuple(g) for g in groups],
               "edges": truth_edges, "circles": truth_circles, "n_drivers": door}


# --------------------------------------------------------------- scoring
def pair_set(groups):
    out = set()
    for g in groups:
        for i, a in enumerate(g):
            for b in g[i + 1:]:
                out.add((min(a, b), max(a, b)))
    return out


def score(S, truth, seed):
    wc.rng = np.random.default_rng(seed + 10_000)   # mechanism's own nulls
    t0 = time.time()
    found = wc.coactivation_groups(S)
    tp_pairs = pair_set(found) & pair_set(truth["groups"])
    prec = len(tp_pairs) / max(1, len(pair_set(found)))
    rec = len(tp_pairs) / max(1, len(pair_set(truth["groups"])))
    noise_admitted = sum(1 for g in found for d in g if d >= truth["n_drivers"])

    # map found groups -> planted groups by majority overlap
    gmap = {}
    for fi, f in enumerate(found):
        best, bo = None, 0
        for ti, tg in enumerate(truth["groups"]):
            o = len(set(f) & set(tg))
            if o > bo:
                best, bo = ti, o
        if best is not None and bo >= max(1, len(truth["groups"][best]) // 2):
            gmap[fi] = best

    edges_f, circles_f = [], []
    if found:
        G = wc.group_series(S, found)
        edges_f = wc.handoff_edges(G)
        circles_f = wc.find_circles(edges_f, len(found))
    edges_m = {(gmap[a], gmap[b]) for a, b in edges_f
               if a in gmap and b in gmap and gmap[a] != gmap[b]}
    e_prec = len(edges_m & truth["edges"]) / max(1, len(edges_m))
    e_rec = len(edges_m & truth["edges"]) / max(1, len(truth["edges"]))

    def canon(c):
        k = c.index(min(c))
        return tuple(c[k:]) + tuple(c[:k])
    want = {canon(list(c)) for c in truth["circles"] if len(c) > 1}
    got = set()
    for c in circles_f:
        mapped = [gmap.get(i) for i in c]
        if None not in mapped and len(set(mapped)) == len(mapped):
            got.add(canon(mapped))
    c_rec = len(got & want) / max(1, len(want))
    false_circles = len(got - want) + sum(1 for c in circles_f
                                          if None in [gmap.get(i) for i in c])
    return {"pair_prec": prec, "pair_rec": rec, "noise_doors": noise_admitted,
            "edge_prec": e_prec, "edge_rec": e_rec, "circle_rec": c_rec,
            "false_circles": false_circles, "n_groups": len(found),
            "secs": time.time() - t0}


# --------------------------------------------------------------- battery
def run(exp, param, cfg, seeds=5):
    rows = []
    for s in range(seeds):
        rng = np.random.default_rng(1000 * seeds + s + hash((exp, str(param))) % 1000)
        S, truth = gen(cfg, rng)
        m = score(S, truth, s)
        m.update({"exp": exp, "param": param, "seed": s, "T": S.shape[0]})
        rows.append(m)
        with open(CSV, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=sorted(m))
            if f.tell() == 0:
                w.writeheader()
            w.writerow(m)
    agg = {k: float(np.mean([r[k] for r in rows]))
           for k in ("pair_prec", "pair_rec", "edge_prec", "edge_rec",
                     "circle_rec", "false_circles", "noise_doors", "secs")}
    print(f"{exp:22s} {str(param):>10s}   "
          f"groups P/R {agg['pair_prec']*100:5.1f}/{agg['pair_rec']*100:5.1f}%   "
          f"edges P/R {agg['edge_prec']*100:5.1f}/{agg['edge_rec']*100:5.1f}%   "
          f"circles {agg['circle_rec']*100:5.1f}%   "
          f"false_circ {agg['false_circles']:.1f}   "
          f"noise {agg['noise_doors']:.1f}   [{agg['secs']:.1f}s]")
    return agg


def main():
    open(CSV, "w").close()
    base = dict(n_proc=2, groups_per_proc=3, group_size=4, dwell=3,
                noise_doors=12, noise_p=0.3, flicker=0.9, T=1500)
    print("=" * 118)

    print("\nE1 stream length (onset curve)")
    for T in (120, 240, 480, 960, 1920):
        run("E1_length", T, {**base, "T": T})

    print("\nE2 sensor flicker (active doors fire with p)")
    for p in (0.95, 0.9, 0.8, 0.7, 0.6, 0.5):
        run("E2_flicker", p, {**base, "flicker": p})

    print("\nE3 background noise (doors, rate)")
    for nd, np_ in ((12, 0.1), (12, 0.5), (40, 0.3), (80, 0.3)):
        run("E3_noise", f"{nd}@{np_}", {**base, "noise_doors": nd, "noise_p": np_})

    print("\nE4 dwell (H1: period inside jitter range 2-5 dies by construction)")
    for d in (1, 2, 3, 5, 8, 12):
        run("E4_dwell", d, {**base, "n_proc": 1, "dwell": d})

    print("\nE5 handoff lag (H2: gap >= 2 falls outside the +-1 window)")
    for lag in (0, 1, 2, 3):
        run("E5_lag", lag, {**base, "n_proc": 1, "lag": lag})

    print("\nE6 concurrency (independent waves at once)")
    for n in (1, 2, 4, 6):
        run("E6_concurrency", n, {**base, "n_proc": n})

    print("\nE7 shared doors (H3: overlapping groups merge)")
    for s in (0, 1, 2):
        run("E7_share", s, {**base, "n_proc": 1, "share": s})

    print("\nE8 pure noise (false positives; want all zeros)")
    fp_groups = fp_edges = fp_circ = 0
    for s in range(20):
        rng = np.random.default_rng(777 + s)
        S = (rng.random((1500, 30)) < 0.3).astype(float)
        wc.rng = np.random.default_rng(s)
        g = wc.coactivation_groups(S)
        e = wc.handoff_edges(wc.group_series(S, g)) if g else []
        c = wc.find_circles(e, len(g)) if g else []
        fp_groups += len(g) > 0
        fp_edges += len(e) > 0
        fp_circ += len(c) > 0
    print(f"E8_null: streams with any groups {fp_groups}/20, "
          f"edges {fp_edges}/20, circles {fp_circ}/20")

    print("\nE9 irregular dwell (aperiodic waves — co-timing, not clocks)")
    run("E9_irregular", "2-8", {**base, "n_proc": 2, "dwell": "irregular"})

    print("\ndone — per-run log in", CSV)


if __name__ == "__main__":
    main()
