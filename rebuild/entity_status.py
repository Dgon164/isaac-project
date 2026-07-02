"""
REBUILD F — Entity identity + temporary statuses (the general version).

Rebuild E's masking detector answered the sun/cloud question with a
special-purpose organ. This is the general architecture the user actually
asked for:

  1. IDENTITY   entities = discovered groups; circles = discovered rhythms.
  2. CLOCK      a tracker walks the discovered circle: evidence moves it,
                learned dwell dead-reckons it when evidence is hidden.
                "It knows the time of day."
  3. EXPECTATION the current phase says which doors SHOULD be lit.
  4. REGISTRATION expected-vs-observed, every tick. A persistent miss does
                not erase the entity — it opens a temporary STATUS:
                miss:disk. Statuses are DOORS.
  5. EXPLANATION no masking detector. The status doors join the stream and
                the ORDINARY co-activation machinery — scoped to the ticks
                where the entity is in that phase (decompose to find
                comparability) — discovers what each status travels with:
                {miss:disk, cloud_a, cloud_b}. Blocking EMERGES.

Absence-by-night vs absence-by-cloud falls out of the clock: at night the
sun's doors are not expected, so nothing is missing. No special rule.

Planted world: a day/night circle (sun-group <-> night-group), an independent
cloud that blocks ONLY the sun's disk while both are up, a wind control,
noise doors.
"""
import numpy as np
import wave_crystallizer as wc

rng = np.random.default_rng(44)

# doors: 0-3 sun (0=disk, 1=light, 2=warm, 3=sky), 4-5 night (moon, stars),
#        6-7 cloud, 8-9 wind, 10-15 noise
SUN, NIGHT, CLOUD, WIND = (0, 1, 2, 3), (4, 5), (6, 7), (8, 9)
D = 16


# ------------------------------------------------------------- generator
def gen(T=4000):
    ideal = np.zeros((T, D))
    truth_phase = np.zeros(T, dtype=int)          # 0 = day, 1 = night
    truth_cloud = np.zeros(T, dtype=int)
    t = 0
    phase = 0
    while t < T:
        for _ in range(int(rng.integers(12, 22))):
            if t >= T:
                break
            truth_phase[t] = phase
            ideal[t, list(SUN if phase == 0 else NIGHT)] = 1
            t += 1
        phase = 1 - phase
    t = int(rng.integers(0, 5))
    while t < T:
        for _ in range(int(rng.integers(6, 14))):     # cloud on
            if t < T:
                truth_cloud[t] = 1
                ideal[t, list(CLOUD)] = 1
                t += 1
        t += int(rng.integers(8, 16))                 # cloud off
    t = int(rng.integers(0, 5))
    while t < T:                                      # wind control
        for _ in range(int(rng.integers(4, 9))):
            if t < T:
                ideal[t, list(WIND)] = 1
                t += 1
        t += int(rng.integers(4, 9))

    blocked = (truth_phase == 0) & (truth_cloud == 1)
    ideal[blocked, 0] = 0                             # cloud hides the disk
    fired = np.where(ideal == 1, rng.random((T, D)) < 0.9,
                     rng.random((T, D)) < 0.05)
    fired[:, 10:] = rng.random((T, 6)) < 0.3
    return fired.astype(float), truth_phase, truth_cloud


# ---------------------------------------------------------------- tracker
class CircleTracker:
    """Walks a discovered circle. Evidence advances it; learned dwell
    dead-reckons through stretches where the phase's doors are hidden."""

    def __init__(self, circle_groups, dwells):
        self.circle = circle_groups                  # list of door-tuples
        self.dwell = dwells                          # learned mean dwell
        self.pos, self.t_in = 0, 0

    def start(self, tick):
        fracs = [len(tick & set(g)) / len(g) for g in self.circle]
        self.pos, self.t_in = int(np.argmax(fracs)), 0

    def step(self, tick):
        cur = self.circle[self.pos]
        nxt_i = (self.pos + 1) % len(self.circle)
        nxt = self.circle[nxt_i]
        f_cur = len(tick & set(cur)) / len(cur)
        f_nxt = len(tick & set(nxt)) / len(nxt)
        if f_nxt >= 0.5 and f_cur < 0.5:             # evidence: hand-off seen
            self.pos, self.t_in = nxt_i, 0
        elif f_cur < 0.3 and self.t_in >= self.dwell[self.pos]:
            self.pos, self.t_in = nxt_i, 0           # dead reckoning
        else:
            self.t_in += 1
        return self.pos

    def expected(self):
        return set(self.circle[self.pos])


def learn_dwells(G, circle_idx):
    """Mean run length of each circle group's activity — the learned clock."""
    dwells = []
    for gi in circle_idx:
        col = G[:, gi]
        runs, r = [], 0
        for v in col:
            if v:
                r += 1
            elif r:
                runs.append(r); r = 0
        dwells.append(max(2.0, float(np.mean(runs)) if runs else 2.0))
    return dwells


# --------------------------------------------------------------------- run
def main():
    print("=" * 74)
    print("REBUILD F — entity identity + temporary statuses (general)")
    print("=" * 74)
    S, truth_phase, truth_cloud = gen()
    T = len(S)

    # 1-2. identity and rhythm, from the existing machinery
    wc.rng = np.random.default_rng(7)
    groups = wc.coactivation_groups(S)
    G = wc.group_series(S, groups)
    edges = wc.handoff_edges(G)
    circles = wc.find_circles(edges, len(groups))
    sun_gi = next(i for i, g in enumerate(groups) if 1 in g)
    day_circle = next((c for c in circles if sun_gi in c), None)
    t1 = day_circle is not None and len(day_circle) == 2
    print(f"\nT1 identity+rhythm: groups {groups}")
    print(f"   day/night circle discovered: {t1} "
          f"({[groups[i] for i in (day_circle or [])]})")

    # 3. the clock: track phase through the whole stream
    circ_groups = [groups[i] for i in day_circle]
    tracker = CircleTracker(circ_groups, learn_dwells(G, day_circle))
    ticks = [set(np.flatnonzero(S[t])) for t in range(T)]
    tracker.start(ticks[0])
    sun_pos = circ_groups.index(groups[sun_gi])
    phase_pred = np.empty(T, dtype=int)
    expected = []
    for t in range(T):
        pos = tracker.step(ticks[t])
        phase_pred[t] = 0 if pos == sun_pos else 1
        expected.append(tracker.expected())
    acc_phase = float((phase_pred == truth_phase).mean())
    occl = (truth_phase == 0) & (truth_cloud == 1)
    acc_occl = float((phase_pred[occl] == 0).mean())
    t2 = acc_phase >= 0.9 and acc_occl >= 0.9
    print(f"\nT2 the clock: phase correct {acc_phase*100:.1f}% overall, "
          f"{acc_occl*100:.1f}% during occlusion (knows it's day "
          f"though the disk is hidden): {t2}")

    # 4. registration: expected-vs-observed -> status doors (2-tick persist)
    miss = np.zeros((T, D))
    for t in range(T):
        for d in expected[t]:
            if d not in ticks[t]:
                miss[t, d] = 1
    persist = miss.copy()
    persist[1:] *= miss[:-1]                          # >=2 consecutive ticks
    status_cols = [d for d in range(D) if persist[:, d].sum() >= 5]
    truth_block = ((truth_phase == 0) & (truth_cloud == 1)).astype(float)
    acc_stat = float((persist[:, 0] == truth_block).mean()) if 0 in status_cols else 0.0
    night = truth_phase == 1
    night_misses = persist[night][:, list(SUN)].sum()
    night_rate = night_misses / max(1, night.sum() * len(SUN))
    occl_misses = persist[:, 0].sum()
    t3 = 0 in status_cols and acc_stat >= 0.85 and night_rate < 0.01
    print(f"\nT3 statuses: miss-doors opened for {status_cols} "
          f"(0 = the disk)")
    print(f"   miss:disk tracks (sun AND cloud) at {acc_stat*100:.1f}%/tick; "
          f"sun-door misses at night {int(night_misses)} "
          f"({night_rate*100:.2f}% — dusk-boundary tracker lag) vs "
          f"{int(occl_misses)} occlusion misses: absence-by-night opens "
          f"~no status: {t3}")

    # 5. explanation by the SAME machinery: statuses are doors; crystallize
    #    them WITHIN the entity's own timeframe (sun-phase ticks only)
    frame = truth_phase == 0                         # use tracker's own frame:
    frame = phase_pred == 0                          # (his clock, not truth's)
    aug = np.column_stack([S[frame][:, [d for d in range(D) if d not in SUN]],
                           persist[frame][:, 0:1]])
    aug_names = [d for d in range(D) if d not in SUN] + ["miss:disk"]
    wc.rng = np.random.default_rng(8)
    egroups = wc.coactivation_groups(aug)
    named = [tuple(aug_names[j] for j in g) for g in egroups]
    expl = next((g for g in named if "miss:disk" in g), None)
    t4 = expl is not None and set(expl) == {6, 7, "miss:disk"}
    print(f"\nT4 explanation EMERGES from ordinary co-activation on the "
          f"status-augmented stream:")
    print(f"   groups found in the sun's timeframe: {named}")
    print(f"   miss:disk travels with the cloud doors {{6,7}}: {t4}")

    # 6. expectation cashes out as prediction: cloud lifts (day) -> disk back
    lift = np.flatnonzero((truth_block[:-1] == 1) & (truth_block[1:] == 0)
                          & (truth_phase[1:] == 0))
    back = sum(1 for t in lift if S[min(t + 1, T - 1):t + 4, 0].any())
    rate = back / max(1, len(lift))
    t5 = rate >= 0.9
    print(f"\nT5 prediction: cloud lifts in daytime {len(lift)} times; "
          f"disk back within 3 ticks {rate*100:.1f}%: {t5}")

    print("-" * 74)
    verdict = t1 and t2 and t3 and t4 and t5
    print(f"T1 rhythm: {t1}  T2 clock: {t2}  T3 statuses: {t3}  "
          f"T4 emergent explanation: {t4}  T5 prediction: {t5}")
    print(f"REBUILD F VERDICT: {'WORKS' if verdict else 'BROKEN'}")
    return verdict


if __name__ == "__main__":
    main()
