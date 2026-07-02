"""
REBUILD D — Wave crystallizer: simultaneous activation, moving waves, circles.

What the static crystallizer cannot see (by construction): it clusters
co-occurrence, but has no representation of ORDER. A wave — activation moving
across the matrix, one group lighting as another dims — and a circle — a wave
that returns to its start — are invisible to any mechanism that only compares
door profiles. (Same disease as membership-only composition: time-order is
arrangement.)

One mechanism, applied recursively:
  Stage 1  SIMULTANEITY -> co-activation groups (doors that fire together,
           null = circular-shift each door's series: breaks cross-timing,
           keeps each door's own rhythm)
  Stage 2  MOVEMENT -> handoff edges: group g switches OFF at the same instant
           group h switches ON (prior-matrix vs later-matrix registration).
           Null-gated the same way: real handoffs are phase-locked, and
           circular shifts destroy phase-lock but preserve event rates.
  Stage 3  CIRCLES -> closed paths in the surviving handoff graph.
  Stage 4  RECURSION -> the activity of each level-1 circle becomes a door in
           a level-2 stream; the SAME stages run again -> patterns of
           patterns, circles of circles.

Planted ground truth:
  40 doors. Process P1 cycles G1(0-4) -> G2(5-9) -> G3(10-14) -> G1 (dwell 3).
  Process P2 cycles H1(15-19) -> H2(20-24) -> H1 (dwell 5).
  Doors 25-39 = pure noise. Eras rotate A(P1 only) -> B(P2 only) ->
  C(BOTH concurrently) -> A ... : the level-2 circle.
  Activation noise: active doors fire p=0.9, inactive drivers p=0.05,
  noise doors p=0.3.

Controls:
  - noise doors must join NO group
  - shuffled-time stream: groups survive (co-occurrence is timeless) but
    every handoff and circle must die -> proves stages 2-4 see exactly what
    the static crystallizer cannot.
"""
import numpy as np

rng = np.random.default_rng(21)

N_PERM = 60
PCT = 95


def jitter(col, T):
    """Small shift: keeps the door's own rhythm and rate, breaks exact
    co-timing. (A full circular shift is the WRONG null for periodic waves —
    it relands in phase 1 time in period, so real simultaneity can never beat
    it. The claim is precise co-timing; the null must break only that.)"""
    s = int(rng.choice([-5, -4, -3, -2, 2, 3, 4, 5]))
    return np.roll(col, s)


# ------------------------------------------------------------ stage 1: groups
def coactivation_groups(S):
    """Doors that fire together: must beat BOTH an independence floor
    (column permutation) and a per-pair jitter null (precise co-timing)."""
    T, D = S.shape
    Z = (S - S.mean(0)) / (S.std(0) + 1e-12)
    C = (Z.T @ Z) / T
    floor_max = np.empty(N_PERM)
    pair_null = np.empty((N_PERM, D, D))
    for k in range(N_PERM):
        Zp = np.column_stack([rng.permutation(Z[:, j]) for j in range(D)])
        Cp = (Zp.T @ Zp) / T
        np.fill_diagonal(Cp, 0)
        floor_max[k] = Cp.max()
        # jitter ONE side only: the null must break RELATIVE timing — jittering
        # both sides sometimes gives them the same shift, which preserves it
        Zj = np.column_stack([jitter(Z[:, j], T) for j in range(D)])
        pair_null[k] = (Z.T @ Zj) / T
    floor = np.percentile(floor_max, PCT)
    pair_thr = np.percentile(pair_null, PCT, axis=0)
    pair_thr = np.maximum(pair_thr, pair_thr.T)
    adj = (C > floor) & (C > pair_thr)
    np.fill_diagonal(adj, False)
    # connected components
    groups, unseen = [], set(range(D))
    while unseen:
        stack = [unseen.pop()]
        comp = set(stack)
        while stack:
            j = stack.pop()
            nxt = set(np.flatnonzero(adj[j])) & unseen
            unseen -= nxt
            comp |= nxt
            stack += list(nxt)
        if len(comp) > 1:
            groups.append(tuple(sorted(int(x) for x in comp)))
    return groups


def group_series(S, groups):
    """Binary activity of each group: majority of its doors on."""
    return np.column_stack([(S[:, list(g)].mean(1) >= 0.5).astype(float)
                            for g in groups])


# --------------------------------------------------- stage 2: handoff edges
def events(series):
    off = (series[:-1] == 1) & (series[1:] == 0)
    on = (series[:-1] == 0) & (series[1:] == 1)
    return off, on


def handoff_counts(Goff, Gon):
    """count[g, h] = # instants where g (in Goff) switches off and h (in Gon)
    switches on within +-1 step — the wave moving from g to h."""
    m = Goff.shape[1]
    cnt = np.zeros((m, m))
    offs = [events(Goff[:, j])[0] for j in range(m)]
    ons = [events(Gon[:, j])[1] for j in range(m)]
    for a in range(m):
        oa = offs[a].astype(float)
        window = oa.copy()
        window[1:] += oa[:-1]
        window[:-1] += oa[1:]
        for b in range(m):
            if a != b:
                cnt[a, b] = float((window * ons[b]).sum())
    return cnt


def handoff_edges(G):
    """Handoffs that beat the jitter null (precise off/on co-timing is the
    claim; jitter the ON side only so relative timing is always broken)."""
    T, m = G.shape
    real = handoff_counts(G, G)
    null = np.zeros((N_PERM, m, m))
    for k in range(N_PERM):
        Gj = np.column_stack([jitter(G[:, j], T) for j in range(m)])
        null[k] = handoff_counts(G, Gj)
    thr = null.max(axis=0)                    # beat the null's best day, with margin
    return [(a, b) for a in range(m) for b in range(m)
            if a != b and real[a, b] > max(1.5 * thr[a, b], 2.0)]


# ------------------------------------------------------- stage 3: circles
def find_circles(edges, m):
    adj = {a: [] for a in range(m)}
    for a, b in edges:
        adj[a].append(b)
    circles = set()

    def dfs(start, node, path):
        for nxt in adj[node]:
            if nxt == start and len(path) > 1:
                k = path.index(min(path))
                circles.add(tuple(path[k:] + path[:k]))
            elif nxt not in path and nxt > start - 1 and len(path) < m:
                dfs(start, nxt, path + [nxt])

    for s in range(m):
        dfs(s, s, [s])
    # deduplicate rotations
    out = []
    for c in circles:
        k = c.index(min(c))
        canon = c[k:] + c[:k]
        if canon not in out:
            out.append(canon)
    return out


# ------------------------------------------------ stage 4: one level up
def circle_activity(G, circles):
    """A circle is 'running' while any of its groups is active — its activity
    is a door in the level-2 stream. Smoothed (3-step majority) so phase
    handoff flicker does not mint fake level-2 states."""
    A = np.column_stack([(G[:, list(c)].max(1)).astype(float) for c in circles])
    K = np.ones(3) / 3.0
    return np.column_stack([(np.convolve(A[:, j], K, mode="same") >= 0.5)
                            .astype(float) for j in range(A.shape[1])])


def state_onehot(A):
    """Distinct simultaneous-activity states as one-hot series (a state is a
    simultaneity-concept at this level)."""
    keys = [tuple(r) for r in A.astype(int)]
    uniq = sorted(set(keys))
    S = np.zeros((len(keys), len(uniq)))
    for t, k in enumerate(keys):
        S[t, uniq.index(k)] = 1.0
    return S, uniq


# ------------------------------------------------------------- planted data
def make_stream(n_rot=10):
    G = [list(range(i, i + 5)) for i in (0, 5, 10)]          # P1 phases
    H = [list(range(i, i + 5)) for i in (15, 20)]            # P2 phases
    rows = []
    for _ in range(n_rot):
        for era in "ABC":
            # era lengths vary AND each process draws a fresh phase each era:
            # truly independent waves are not phase-locked to each other or to
            # the era clock — otherwise cross-process co-timings are REAL
            # structure and the crystallizer (correctly) reports them
            o1, o2 = int(rng.integers(0, 9)), int(rng.integers(0, 10))
            for t in range(int(rng.integers(70, 91))):
                row = np.zeros(40)
                if era in "AC":
                    row[G[((t + o1) // 3) % 3]] = 1          # P1 wave, dwell 3
                if era in "BC":
                    row[H[((t + o2) // 5) % 2]] = 1          # P2 wave, dwell 5
                rows.append(row)
    S = np.array(rows)
    drivers = S[:, :25]
    fire = np.where(drivers == 1, rng.random(drivers.shape) < 0.9,
                    rng.random(drivers.shape) < 0.05)
    noise = rng.random((len(S), 15)) < 0.3
    return np.column_stack([fire, noise]).astype(float)


# --------------------------------------------------------------------- test
def main():
    print("=" * 72)
    print("REBUILD D — wave crystallizer: simultaneity, movement, circles")
    print("=" * 72)
    S = make_stream()
    print(f"stream: {S.shape[0]} steps x {S.shape[1]} doors "
          f"(25 drivers in 5 planted groups, 15 noise)")

    # T1 simultaneity
    groups = coactivation_groups(S)
    planted = [tuple(range(i, i + 5)) for i in (0, 5, 10, 15, 20)]
    t1 = sorted(groups) == planted
    noise_in = any(d >= 25 for g in groups for d in g)
    print(f"\nT1 co-activation groups: found {len(groups)} "
          f"{[g for g in groups]}")
    print(f"   exactly the 5 planted groups: {t1}   noise doors admitted: {noise_in}")

    # T2 movement
    G = group_series(S, groups)
    edges = handoff_edges(G)
    name = {i: f"G{i+1}" if i < 3 else f"H{i-2}" for i in range(5)}
    planted_edges = {(0, 1), (1, 2), (2, 0), (3, 4), (4, 3)}
    t2 = set(edges) == planted_edges
    print(f"\nT2 handoff edges (the wave moving): "
          f"{sorted((name[a], name[b]) for a, b in edges)}")
    print(f"   exactly the planted transitions: {t2}")

    # T3 circles
    circles = find_circles(edges, len(groups))
    t3 = sorted(tuple(sorted(c)) for c in circles) == [(0, 1, 2), (3, 4)]
    print(f"\nT3 circles: {[[name[i] for i in c] for c in circles]}")
    print(f"   the two planted cycles (period 3 and period 2): {t3}")

    # T4 static-blindness control: shuffle time
    Ssh = S[rng.permutation(len(S))]
    gsh = coactivation_groups(Ssh)
    esh = handoff_edges(group_series(Ssh, gsh)) if gsh else []
    csh = find_circles(esh, len(gsh)) if gsh else []
    t4 = (sorted(gsh) == planted) and len(esh) == 0 and len(csh) == 0
    print(f"\nT4 shuffled-time control: groups {len(gsh)} (same: "
          f"{sorted(gsh) == planted}), handoffs {len(esh)}, circles {len(csh)}")
    print(f"   co-occurrence survives, ALL movement dies: {t4}")
    print(f"   (this is exactly the part the static crystallizer cannot see)")

    # T5 recursion: circles of circles
    if not circles:
        print("\nT5 skipped: no level-1 circles")
        return False
    A = circle_activity(G, circles)
    S2, states = state_onehot(A)
    e2 = handoff_edges(S2)
    c2 = find_circles(e2, S2.shape[1])
    lab = [str(tuple(int(v) for v in s)) for s in states]
    t5 = any(len(c) == 3 for c in c2)
    print(f"\nT5 level-2 (same machinery on circle-activity):")
    print(f"   level-2 states: {lab}")
    print(f"   level-2 circles: {[[lab[i] for i in c] for c in c2]}")
    print(f"   the planted era rotation A->B->C found as a circle of circles: {t5}")

    print("-" * 72)
    verdict = t1 and (not noise_in) and t2 and t3 and t4 and t5
    print(f"T1 groups: {t1}   T2 movement: {t2}   T3 circles: {t3}   "
          f"T4 static-blind: {t4}   T5 recursion: {t5}")
    print(f"REBUILD D VERDICT: {'WORKS' if verdict else 'BROKEN'}")
    return verdict


if __name__ == "__main__":
    main()
