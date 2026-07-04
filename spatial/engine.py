"""
Structure engine v0
-------------------
Two halves, one loop:

  FORWARD  (simulate): locked distances + constraint projection -> motion
  INVERSE  (perceive): observed motion -> variance ledger -> locked edges
                       -> rigid clusters -> joints -> DOF (Gruebler check)

No linear algebra beyond vector arithmetic. No solver beyond
"measure the error, split it between the endpoints, repeat."
"""

from __future__ import annotations
import math
import random
from dataclasses import dataclass, field
from itertools import combinations


# ----------------------------------------------------------------------------
# Forward half: constraint projection (position-based dynamics, distance-only)
# ----------------------------------------------------------------------------

@dataclass
class Mechanism:
    points: list[list[float]]              # [ [x, y], ... ]  scratch coordinates
    locked: dict[tuple[int, int], float] = field(default_factory=dict)  # (i,j) -> length
    pinned: dict[int, tuple[float, float]] = field(default_factory=dict)  # index -> anchor
    rails: dict[int, float] = field(default_factory=dict)  # index -> fixed y (slider on x-axis)

    def lock(self, i: int, j: int):
        """Lock the CURRENT distance between points i and j."""
        a, b = self.points[i], self.points[j]
        d = math.dist(a, b)
        self.locked[(min(i, j), max(i, j))] = d

    def pin(self, i: int):
        self.pinned[i] = tuple(self.points[i])

    def project(self, sweeps: int = 30):
        """Enforce all constraints by local projection, a few sweeps."""
        for _ in range(sweeps):
            for (i, j), rest in self.locked.items():
                ax, ay = self.points[i]
                bx, by = self.points[j]
                dx, dy = bx - ax, by - ay
                d = math.hypot(dx, dy) or 1e-12
                err = (d - rest) / d          # fraction to correct
                # split correction between endpoints (pinned points don't move)
                wi = 0.0 if i in self.pinned else 1.0
                wj = 0.0 if j in self.pinned else 1.0
                tot = wi + wj
                if tot == 0.0:
                    continue
                self.points[i][0] += wi / tot * err * dx
                self.points[i][1] += wi / tot * err * dy
                self.points[j][0] -= wj / tot * err * dx
                self.points[j][1] -= wj / tot * err * dy
            for i, (px, py) in self.pinned.items():
                self.points[i][0] = px
                self.points[i][1] = py
            for i, ry in self.rails.items():
                self.points[i][1] = ry          # slider: free in x, clamped in y

    def drive(self, i: int, x: float, y: float, sweeps: int = 40):
        """Drag point i to (x, y), let everything else settle."""
        self.points[i][0] = x
        self.points[i][1] = y
        keep = self.pinned.copy()
        self.pinned[i] = (x, y)              # temporarily pin the dragged point
        self.project(sweeps)
        self.pinned = keep


# ----------------------------------------------------------------------------
# Inverse half: watch trajectories, recover structure
# ----------------------------------------------------------------------------

@dataclass
class PairLedger:
    """Welford running mean/variance for one pairwise distance."""
    n: int = 0
    mean: float = 0.0
    m2: float = 0.0

    def add(self, x: float):
        self.n += 1
        d = x - self.mean
        self.mean += d / self.n
        self.m2 += d * (x - self.mean)

    @property
    def std(self) -> float:
        return math.sqrt(self.m2 / self.n) if self.n > 1 else 0.0


def observe(frames: list[list[list[float]]]) -> dict[tuple[int, int], PairLedger]:
    """Accumulate a distance ledger for every point pair across all frames."""
    n = len(frames[0])
    ledgers = {pair: PairLedger() for pair in combinations(range(n), 2)}
    for frame in frames:
        for (i, j), led in ledgers.items():
            led.add(math.dist(frame[i], frame[j]))
    return ledgers


def detect_locked(ledgers, scale: float, rel_tol: float = 1e-3):
    """An edge is locked if its distance never varies (relative to object scale).
    rel_tol is the sig-fig: precision relative to the object's own size."""
    return {pair: led.mean for pair, led in ledgers.items()
            if led.std < rel_tol * scale}


def rigid_clusters(n_points: int, locked_edges) -> list[set[int]]:
    """Rigid parts precipitate as connected components of the locked graph.
    (2D: any connected set of locked distances that includes a triangle is
    rigid; for this v0, linkage links are bars or braced triangles, so
    connected components suffice.)"""
    parent = list(range(n_points))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        parent[find(a)] = find(b)

    for (i, j) in locked_edges:
        union(i, j)
    groups: dict[int, set[int]] = {}
    for p in range(n_points):
        groups.setdefault(find(p), set()).add(p)
    return list(groups.values())


def find_joints(clusters: list[set[int]], frames) -> list[tuple[int, int, int]]:
    """A joint is a point shared... but in point-form linkages, links meet AT
    shared points. Two clusters sharing a point = revolute joint there.
    With disjoint clusters, a joint is a point-pair (one from each cluster)
    whose distance ledger is ~zero mean or locked across clusters.
    Here links share vertices, so: joint = vertex appearing in 2+ clusters
    OR pair of coincident vertices from different clusters."""
    joints = []
    # coincident-vertex joints: two points from different clusters that stay
    # at (near) zero distance -> same hinge pin
    for ci in range(len(clusters)):
        for cj in range(ci + 1, len(clusters)):
            for a in clusters[ci]:
                for b in clusters[cj]:
                    dmax = max(math.dist(f[a], f[b]) for f in frames)
                    if dmax < 1e-6:
                        joints.append((ci, cj, a))
    return joints


def gruebler_2d(n_links: int, n_joints: int) -> int:
    """Planar Gruebler/Kutzbach: DOF = 3*(L-1) - 2*J  (revolute joints)."""
    return 3 * (n_links - 1) - 2 * n_joints


def observed_dof(frames, clusters, ref_cluster: int = 0) -> int:
    """Estimate DOF from data: collect each non-ground cluster's orientation
    angle per frame; count how many independent parameters the motion shows.
    v0 heuristic: fit every cluster angle against cluster-1's angle; if all
    angles are functions of one parameter (max residual small), DOF = 1."""
    def cluster_angle(cluster: set[int], frame) -> float:
        pts = sorted(cluster)
        if len(pts) < 2:
            return 0.0
        a, b = frame[pts[0]], frame[pts[-1]]
        return math.atan2(b[1] - a[1], b[0] - a[0])

    moving = [c for k, c in enumerate(clusters) if k != ref_cluster]
    if not moving:
        return 0
    # parameter = angle of the first moving cluster
    params = [cluster_angle(moving[0], f) for f in frames]
    # every other cluster's angle should be a clean function of the parameter:
    # check by sorting on the parameter and testing single-valuedness
    for c in moving[1:]:
        angles = [cluster_angle(c, f) for f in frames]
        order = sorted(range(len(params)), key=lambda k: params[k])
        # single-valued = neighbors in parameter have neighboring angles
        for k in range(1, len(order)):
            p_gap = abs(params[order[k]] - params[order[k - 1]])
            a_gap = abs(angles[order[k]] - angles[order[k - 1]])
            if p_gap < 1e-4 and a_gap > 1e-2:
                return 2   # same parameter value, different pose -> extra DOF
    return 1

# ----------------------------------------------------------------------------
# Null-gated classification (added 2026-07-03, replacing bare thresholds)
# ----------------------------------------------------------------------------
# The audit-standard law: replace thresholds with statistical tests. The
# ledger's original detect_locked used a hand-tuned rel_tol. Here the gate is
# CALIBRATED FROM THE DATA: structure moves slowly between adjacent frames,
# measurement noise doesn't -- so each pair's fast component (first
# differences) estimates its own noise floor, and "locked" means "the total
# variation is explained by measurement noise alone" (a variance-ratio test),
# not "smaller than a number I liked."
#
# ASSUMPTION (document, don't hide): observation is temporally continuous --
# adjacent frames are close in time. Teleporting inputs void the noise-floor
# estimate. Perception gets this for free; shuffled data does not.

def noise_floor_of(ds: list[float]) -> float:
    """Per-sample noise std estimated from first differences: for slowly
    varying structure + iid noise, std(diff)/sqrt(2) -> noise std."""
    n = len(ds)
    if n < 3:
        return 0.0
    diffs = [ds[k + 1] - ds[k] for k in range(n - 1)]
    m = sum(diffs) / len(diffs)
    v = sum((d - m) ** 2 for d in diffs) / len(diffs)
    return math.sqrt(max(v, 0.0) / 2.0)


def _visits(ds: list[float], target: float, band: float,
            away: float) -> int:
    """Count SEPARATE visits to an extreme, with hysteresis: after a visit,
    the series must move at least `away` from the target before a new visit
    can count. Without this, measurement noise flickering at a random walk's
    one-time extreme counts as many 'visits' and free pairs read as bounded
    (caught by the null battery, 2026-07-03)."""
    v, armed = 0, True
    for d in ds:
        if armed and abs(d - target) < band:
            v += 1
            armed = False
        elif not armed and abs(d - target) > away:
            armed = True
    return v


def _min_extreme_visits(ds: list[float], nf: float) -> int:
    """min(visits to own min, visits to own max), hysteresis-counted,
    with band/away derived from the series' own range and noise."""
    lo, hi = min(ds), max(ds)
    rng = hi - lo
    if rng <= 0:
        return 0
    band = max(0.02 * rng, 3 * nf)
    if band >= 0.2 * rng:            # extremes noise-dominated: no verdict
        return 0
    away = 0.25 * rng
    return min(_visits(ds, lo, band, away), _visits(ds, hi, band, away))


def classify_edges(frames, machine_eps: float = 1e-9):
    """Null-gated edge vocabulary. For every point pair, verdicts:

      LOCKED  -- total std <= its own noise floor * (1 + 4/sqrt(N))
                 (variance-ratio test: nothing but measurement noise varies)
      BOUNDED -- varies beyond noise, but hits REPEATABLE limits (>= 2
                 separate visits to each extreme, range >> noise)
      SPRUNG  -- varies beyond noise around a STABLE mean (first-third vs
                 last-third means agree within their standard error)
      FREE    -- none of the above (drifts)

    Returns {pair: dict(kind, mean, std, noise)}. No hand-tuned rel_tol:
    every gate is derived from the pair's own measured noise or from
    sampling error, plus a machine-precision floor for noiseless sims."""
    n = len(frames[0])
    N = len(frames)
    out = {}
    scale = 0.0
    series = {}
    for (i, j) in combinations(range(n), 2):
        ds = [math.dist(frames[t][i], frames[t][j]) for t in range(N)]
        series[(i, j)] = ds
        scale = max(scale, sum(ds) / N)
    for pair, ds in series.items():
        mean = sum(ds) / N
        std = math.sqrt(sum((d - mean) ** 2 for d in ds) / N)
        nf = noise_floor_of(ds)
        gate = max(nf * (1.0 + 4.0 / math.sqrt(N)), machine_eps * scale)
        if std <= gate:
            kind = "locked"
        else:
            # BOUNDED must beat ITS null: a matched random walk. Shuffling
            # the series' own increments preserves the step statistics but
            # destroys any boundedness -- if surrogates revisit their
            # extremes as often as the real series does, "repeatable
            # limits" is what walks do, not what constraints do. (A walk
            # CAN revisit extremes twice by luck -- caught by the null
            # battery, 2026-07-03; the constant '>= 2 visits' was not a
            # test, this is.)
            rng_ = max(ds) - min(ds)
            real_v = _min_extreme_visits(ds, nf)
            surr = []
            diffs = [ds[k + 1] - ds[k] for k in range(len(ds) - 1)]
            srng = random.Random(1234)
            for _ in range(20):
                srng.shuffle(diffs)
                s, walk_ = ds[0], [ds[0]]
                for d in diffs:
                    s += d
                    walk_.append(s)
                surr.append(_min_extreme_visits(walk_, nf))
            repeatable = (real_v >= 2 and real_v > max(surr)
                          and rng_ > 10 * max(nf, machine_eps * scale))
            if repeatable:
                kind = "bounded"
            else:
                third = N // 3
                m1 = sum(ds[:third]) / third
                m3 = sum(ds[-third:]) / third
                se = 3.0 * std / math.sqrt(third)
                kind = "sprung" if abs(m1 - m3) <= se else "free"
        out[pair] = dict(kind=kind, mean=mean, std=std, noise=nf)
    return out
