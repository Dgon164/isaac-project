"""
REBUILD E — Interference: present but blocked.

The sun behind a cloud: most indicators persist (light, warmth, sky), the
central bright point is suppressed. Three capabilities, tested separately:

  PERMANENCE  the group still reads PRESENT from its unblocked majority
              (the majority vote already gives this — verify it)
  MASKING     the blocking relation is a first-class discovery:
              door d of group g is dark WHILE g is present, co-timed with
              blocker b being present  ->  edge "b blocks g.d"
              Null: large circular shift of the blocker (the claim is
              state-coincidence, not precise timing) + a rate-ratio guard:
              P(d dark | g present, b present) >> P(d dark | g present, b absent)
  RESCUE      heavy blocking exiles the door from its own group (correlation
              decays). Conditional adoption: re-test membership on the ticks
              where the candidate blocker is absent. If it joins there, it was
              always a member — plus a mask edge, discovered in one move.

The readout distinguishes three states the flat view conflates:
  PRESENT / PRESENT-BUT-BLOCKED (which doors, blocked by what) / ABSENT.
Absence-by-night is not absence-by-cloud.
"""
import numpy as np
import wave_crystallizer as wc

rng = np.random.default_rng(33)


# --------------------------------------------------------------- masking
def _shift_null(b, T):
    return np.roll(b, int(rng.integers(T // 10, 9 * T // 10)))


def masking_edges(S, groups, n_perm=40, min_events=5):
    """Detect 'b blocks g.d': suppression of d inside active g, co-present
    with b. Returns [(blocker_label, gi, door, p_dark_when_b, p_dark_no_b)]."""
    G = wc.group_series(S, groups)
    T = len(S)
    grouped = {d for g in groups for d in g}
    blockers = [(f"group{gi}", G[:, gi]) for gi in range(len(groups))]
    blockers += [(f"door{d}", S[:, d]) for d in range(S.shape[1])
                 if d not in grouped]
    edges = []
    for gi, g in enumerate(groups):
        act = G[:, gi] == 1
        if act.sum() < 4 * min_events:
            continue
        for d in g:
            if (act & (S[:, d] == 0)).sum() < min_events:
                continue

            def rate_diff(bcol):
                """P(d dark | g present, b present) − P(... | b absent).
                A raw-count gate cannot certify a high-coverage blocker
                (a shifted always-mostly-on blocker still overlaps almost
                all suppressions); the CLAIM is the conditional rate gap."""
                on = bcol == 1
                m1, m0 = act & on, act & ~on
                if m1.sum() < min_events or m0.sum() < min_events:
                    return None
                return (float((S[m1, d] == 0).mean()),
                        float((S[m0, d] == 0).mean()))

            for label, b in blockers:
                if label == f"group{gi}":
                    continue
                r = rate_diff(b)
                if r is None:
                    continue
                p1, p0 = r
                if p1 < 0.5 or p1 < 2.5 * max(p0, 0.02):
                    continue                      # not a suppression pattern
                nulls = []
                for _ in range(n_perm):
                    rn = rate_diff(_shift_null(b, T))
                    if rn is not None:
                        nulls.append(rn[0] - rn[1])
                if len(nulls) < n_perm // 2:
                    continue
                if (p1 - p0) > max(2 * np.percentile(nulls, 95), 0.2):
                    edges.append((label, gi, int(d), p1, p0))
    return edges


# ---------------------------------------------------------------- rescue
def conditional_rescue(S, groups, n_perm=40):
    """Doors exiled by heavy blocking: adopt into a group if membership holds
    on the ticks where a candidate blocker is ABSENT. Returns
    [(door, gi, blocker_label, cond_corr, uncond_corr)]."""
    G = wc.group_series(S, groups)
    grouped = {d for g in groups for d in g}
    blockers = [(f"group{gi}", G[:, gi]) for gi in range(len(groups))]
    adopted = []
    for d in range(S.shape[1]):
        if d in grouped:
            continue
        x = S[:, d]
        best = None
        for gi in range(len(groups)):
            gcol = G[:, gi]
            uncond = float(np.corrcoef(x, gcol)[0, 1])
            for label, b in blockers:
                if label == f"group{gi}":
                    continue
                off = b == 0
                if off.sum() < 200:
                    continue
                xs, gs = x[off], gcol[off]
                if xs.std() < 1e-9 or gs.std() < 1e-9:
                    continue
                c = float(np.corrcoef(xs, gs)[0, 1])
                null = [abs(float(np.corrcoef(rng.permutation(xs), gs)[0, 1]))
                        for _ in range(n_perm)]
                thr = np.percentile(null, 95)
                # conditional membership must be strong where the blocker is
                # absent AND clearly stronger than the unconditional story
                if c > max(3 * thr, 0.35) and c > uncond + 0.15:
                    if best is None or c > best[3]:
                        best = (int(d), gi, label, c, uncond)
        if best is not None:
            adopted.append(best)
    return adopted


# --------------------------------------------------------------- readout
def read_state(tick, groups, masks, blocker_series_at):
    """Per-group verdict for one instant:
    PRESENT / BLOCKED(doors, by) / ABSENT / UNCERTAIN."""
    out = {}
    for gi, g in enumerate(groups):
        frac = len(tick & set(g)) / len(g)
        missing = [d for d in g if d not in tick]
        masked_missing = [(d, b) for (b, mgi, d, *_ ) in masks
                          if mgi == gi and d in missing
                          and blocker_series_at(b)]
        if frac >= 0.5:
            out[gi] = ("BLOCKED", masked_missing) if masked_missing \
                else ("PRESENT", [])
        elif frac >= 0.3 and masked_missing and \
                len(missing) - len(masked_missing) <= len(g) // 2:
            out[gi] = ("BLOCKED", masked_missing)
        elif frac <= 0.2:
            out[gi] = ("ABSENT", [])
        else:
            out[gi] = ("UNCERTAIN", [])
    return out


# ------------------------------------------------------------- generator
def gen(T=3000, heavy=False):
    """sun = doors 0-4 (0 = bright disk), wind = 5-6, cloud = 7-8,
    noise = 9-16. Cloud blocks sun.disk while both are up."""
    D = 17
    truth = np.zeros((T, 3), dtype=int)          # sun_on, cloud_on, wind_on
    ideal = np.zeros((T, D))

    def waves(col, on_lo, on_hi, off_lo, off_hi):
        t = int(rng.integers(0, 6))
        while t < T:
            for _ in range(int(rng.integers(on_lo, on_hi))):
                if t < T:
                    col[t] = 1; t += 1
            t += int(rng.integers(off_lo, off_hi))

    sun, cloud, wind = np.zeros(T), np.zeros(T), np.zeros(T)
    waves(sun, 12, 21, 8, 15)
    if heavy:
        waves(cloud, 30, 51, 2, 5)               # coverage ~0.93: exile regime
    else:
        waves(cloud, 6, 13, 8, 16)               # coverage ~0.4
    waves(wind, 4, 9, 4, 9)
    truth[:, 0], truth[:, 1], truth[:, 2] = sun, cloud, wind
    ideal[:, 0:5] = sun[:, None]
    ideal[:, 0] *= (1 - cloud * sun)             # the disk: blocked when both
    ideal[:, 5:7] = wind[:, None]
    ideal[:, 7:9] = cloud[:, None]

    fired = np.where(ideal == 1, rng.random((T, D)) < 0.9,
                     rng.random((T, D)) < 0.05)
    fired[:, 9:] = rng.random((T, 8)) < 0.3
    return fired.astype(float), truth


def label_groups(groups):
    def name(g):
        s = set(g)
        if s & set(range(0, 5)):
            return "sun"
        if s & {5, 6}:
            return "wind"
        if s & {7, 8}:
            return "cloud"
        return "noise!"
    return {gi: name(g) for gi, g in enumerate(groups)}


# ------------------------------------------------------------------ test
def main():
    print("=" * 74)
    print("REBUILD E — interference: present but blocked")
    print("=" * 74)

    # ---- moderate coverage: disk should survive in the group
    S, truth = gen(heavy=False)
    wc.rng = np.random.default_rng(4)
    groups = wc.coactivation_groups(S)
    names = label_groups(groups)
    sun_gi = next((gi for gi, n in names.items() if n == "sun"), None)
    cloud_gi = next((gi for gi, n in names.items() if n == "cloud"), None)
    disk_in = sun_gi is not None and 0 in groups[sun_gi]
    print(f"\nT1 groups: {[(names[i], g) for i, g in enumerate(groups)]}")
    print(f"   sun group holds the disk despite 40% occlusion: {disk_in}")

    masks = masking_edges(S, groups)
    want = [(f"group{cloud_gi}", sun_gi, 0)]
    got = [(b, gi, d) for b, gi, d, *_ in masks]
    t2 = got == want
    print(f"\nT2 masking edges: {[(names.get(int(b[5:]), b) if b.startswith('group') else b, names[gi], f'door{d}', f'dark {p1:.2f} vs {p0:.2f}') for b, gi, d, p1, p0 in masks]}")
    print(f"   exactly 'cloud blocks sun.disk', nothing else: {t2}")

    # ---- permanence readout, scored per tick against truth
    G = wc.group_series(S, groups)
    ok = tot = 0
    for t in range(len(S)):
        tick = set(np.flatnonzero(S[t]))
        cloud_present = bool(G[t, cloud_gi]) if cloud_gi is not None else False
        st = read_state(tick, groups,
                        [(b, gi, d) + tuple(r) for b, gi, d, *r in masks],
                        lambda b: cloud_present)[sun_gi][0]
        want_st = ("ABSENT" if truth[t, 0] == 0 else
                   "BLOCKED" if truth[t, 1] == 1 else "PRESENT")
        ok += (st == want_st)
        tot += 1
    acc = ok / tot
    t3 = acc >= 0.85
    print(f"\nT3 per-tick readout (PRESENT / BLOCKED / ABSENT): "
          f"{acc*100:.1f}% correct  (>=85%: {t3})")

    # ---- control: masking is a SAME-INSTANT relation, so time-shuffling the
    # whole stream preserves it (rows intact). The right null: shuffle the
    # BLOCKER'S timeline (cloud columns jointly) — groups survive, the
    # suppression<->blocker link must die.
    Sbl = S.copy()
    perm = rng.permutation(len(S))
    Sbl[:, 7:9] = S[perm][:, 7:9]
    wc.rng = np.random.default_rng(5)
    gbl = wc.coactivation_groups(Sbl)
    mbl = masking_edges(Sbl, gbl) if gbl else []
    t4 = len(gbl) == len(groups) and len(mbl) == 0
    print(f"\nT4 blocker-timeline-shuffle control: groups {len(gbl)} "
          f"(intact), mask edges {len(mbl)} (want 0): {t4}")

    # ---- occlusion-robustness curve: the exile regime turns out to be
    # practically unreachable with a single blocker — a door blocked 93% of
    # the time STILL keeps its group membership (residual co-timing stays
    # above chance) and the mask edge explains its absences. Membership is
    # occlusion-robust; conditional_rescue stays as belt-and-suspenders.
    S2, _ = gen(T=5000, heavy=True)
    wc.rng = np.random.default_rng(6)
    groups2 = wc.coactivation_groups(S2)
    names2 = label_groups(groups2)
    sun2 = next((gi for gi, n in names2.items() if n == "sun"), None)
    cloud2 = next((gi for gi, n in names2.items() if n == "cloud"), None)
    retained = sun2 is not None and 0 in groups2[sun2]
    masks2 = masking_edges(S2, groups2)
    m2 = [(b, gi, d) for b, gi, d, *_ in masks2]
    mask_ok = m2 == [(f"group{cloud2}", sun2, 0)]
    rescued = conditional_rescue(S2, groups2)
    t5 = retained and mask_ok and len(rescued) == 0
    print(f"\nT5 heavy occlusion (~93% of sun-time): "
          f"groups {[(names2[i], g) for i, g in enumerate(groups2)]}")
    print(f"   disk RETAINED in its group even at 93% blocking: {retained}")
    print(f"   mask still found and exact: {mask_ok}   "
          f"({[(f'dark {p1:.2f} vs {p0:.2f}') for *_, p1, p0 in masks2]})")
    print(f"   rescue not triggered, no false adoptions: {len(rescued) == 0}")

    print("-" * 74)
    verdict = disk_in and t2 and t3 and t4 and t5
    print(f"T1 permanence-in-group: {disk_in}   T2 mask exact: {t2}   "
          f"T3 readout: {t3}   T4 control: {t4}   T5 occlusion-robust: {t5}")
    print(f"REBUILD E VERDICT: {'WORKS' if verdict else 'BROKEN'}")
    return verdict


if __name__ == "__main__":
    main()
