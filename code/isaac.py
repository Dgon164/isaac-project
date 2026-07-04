"""
Isaac — Unified Engine
======================

Two primitives: differentiation (comparison) and memory recursion (store + repeat).
One operation at every scale. Feed it data. It figures it out.

Pipeline:  SENSE → THINK (store ↔ route ↔ evaluate) → ACT
Active:    crystallize the working set. Real-time. O(k²).
Idle:      consolidate() — full crystallization of dirty set. O(d²).

Core:    Net, observe, consolidate, lookup, check
Logic:   logic_eval, compound decomposition
Reason:  reason_chain, is_a_check, can_check, containment, properties, syllogisms
Compute: decompose_multiply, decompose_add, compute (shrug-decompose-verify-memorize)
Solve:   forward, backward, gap-fill, multi-step
World:   state management, action teaching, execution, planning
Persist: assess consequences, plan/think/execute

No parser. No interpreter. No preprocessing. No weights.
Knowledge is doors. Structure is discovered. Everything enters, nothing leaves.
"""

from collections import defaultdict
import re
import numpy as np


# ═════════════════════════════════════════════════════════════════
# NET — doors, tags, metadata. The only data structure.
# ═════════════════════════════════════════════════════════════════

class Net:
    """The knowledge substrate. Directed graph with tagged edges (doors)."""

    def __init__(self):
        self.doors = defaultdict(set)            # node → {targets}
        self.door_tags = defaultdict(set)         # (src, tgt) → {tags}
        self.meta = defaultdict(dict)             # node → {key: value}
        self.door_counts = defaultdict(int)       # (src, tgt) → observations

    def add_door(self, src, tgt, tag="seq"):
        is_new = tgt not in self.doors[src]
        self.doors[src].add(tgt)
        self.door_tags[(src, tgt)].add(tag)
        # counts are the evidence base: "seen once" and "seen a hundred
        # times" must be different facts (2026-07-03, the foundation fix —
        # without counts no statistical divergence test is possible)
        if not hasattr(self, "door_counts"):      # minds saved pre-counts
            self.door_counts = defaultdict(int)
        self.door_counts[(src, tgt)] += 1
        if tgt not in self.doors:
            self.doors[tgt] = set()
        return is_new

    def has_door(self, src, tgt):
        return tgt in self.doors.get(src, set())

    def get_doors(self, node, tag=None):
        all_t = self.doors.get(node, set())
        if tag is None:
            return all_t
        return {t for t in all_t if tag in self.door_tags.get((node, t), set())}

    def get_predecessors(self, node, tag=None):
        preds = set()
        for src, tgts in self.doors.items():
            if node in tgts:
                if tag is None or tag in self.door_tags.get((src, node), set()):
                    preds.add(src)
        return preds

    def get_door_tags(self, src, tgt):
        return self.door_tags.get((src, tgt), set())

    def get_full_profile(self, node):
        out = {}
        for tgt in self.doors.get(node, set()):
            out[tgt] = self.door_tags.get((node, tgt), set()).copy()
        inc = {}
        for src, tgts in self.doors.items():
            if node in tgts:
                inc[src] = self.door_tags.get((src, node), set()).copy()
        return {"out": out, "in": inc}

    def all_nodes(self):
        nodes = set(self.doors.keys())
        for tgts in self.doors.values():
            nodes.update(tgts)
        return nodes

    def set_meta(self, node, key, value):
        self.meta[node][key] = value

    def get_meta(self, node, key, default=None):
        return self.meta.get(node, {}).get(key, default)


# ═════════════════════════════════════════════════════════════════
# PRIMITIVES — compare and tokenize
# ═════════════════════════════════════════════════════════════════

def compare(set_a, set_b):
    """The single cognitive primitive. Same, different, not significant."""
    shared = set_a & set_b
    only_a = set_a - set_b
    only_b = set_b - set_a
    total = len(shared) + len(only_a) + len(only_b)
    return {
        "shared": shared,
        "only_a": only_a,
        "only_b": only_b,
        "similarity": round(len(shared) / total * 100, 1) if total else 0,
    }


def tokenize(text):
    """Split text into tokens. Punctuation separates. Underscores preserved.
    The ONE allowed pre-net operation (Rule 2 exception):
    defines what a NODE is, not what a DOOR means."""
    return re.findall(r"[a-zA-Z0-9_]+|[^\s]", text.lower())


# ═════════════════════════════════════════════════════════════════
# SCRATCH — working memory. Registers / RAM. The mutable half.
# ═════════════════════════════════════════════════════════════════

class Scratch:
    """His working memory: named registers he writes, reads, and updates in
    real time while processing. The OTHER kind of memory from the door-net:

        door-net   = append-only, permanent, 'what is true in general'
        scratch    = overwritable, transient, 'what is true right now / this run'

    A register holds a number (a tally), a string (a note/association), or a
    list (built by appending — chainable). Every write also logs the value to a
    step-trace, so any computation can be replayed to see where it went wrong.
    """

    def __init__(self):
        self.reg = {}                    # name -> current value
        self.log = defaultdict(list)     # name -> [every value it has held]

    # ── core: write supersedes, read returns now ────────────────
    def write(self, name, value):
        """Overwrite the register. The old value is superseded (not appended,
        unlike a door) — but it is kept in the step-trace."""
        self.reg[name] = value
        self.log[name].append(value)
        return value

    def read(self, name, default=None):
        """What is in this register right NOW."""
        return self.reg.get(name, default)

    def has(self, name):
        return name in self.reg

    # ── number ops: increment / tracking ────────────────────────
    def incr(self, name, by=1):
        """count = count + 1. Creates the register at 0 if new."""
        return self.write(name, self.reg.get(name, 0) + by)

    # ── list ops: append / chain ────────────────────────────────
    def append(self, name, value):
        """Grow a register into a list — chain values onto it."""
        cur = self.reg.get(name)
        if not isinstance(cur, list):
            cur = [] if cur is None else [cur]
        cur = cur + [value]
        self.reg[name] = cur
        self.log[name].append(tuple(cur))
        return cur

    # ── latch: 'has it ever…' (sticky bit) ───────────────────────
    def latch(self, name):
        """Flip to True once and stay — memory that something HAPPENED."""
        return self.write(name, True)

    # ── introspection: the step-trace, for replay / find-the-error
    def history(self, name):
        """Every value this register has held, in order. The audit log."""
        return list(self.log[name])

    def snapshot(self):
        """The whole current working state at this instant."""
        return dict(self.reg)

    def clear(self, name=None):
        if name is None:
            self.reg.clear(); self.log.clear()
        else:
            self.reg.pop(name, None); self.log.pop(name, None)


# ═════════════════════════════════════════════════════════════════
# Isaac — the system
# ═════════════════════════════════════════════════════════════════

CONFIDENCE_THRESHOLD = 1.0

# ── crystal/box helpers (neural transplant: boxes are Isaac concepts) ──
_QLOW, _QHIGH = -7, 8

def _quantize(X, lo=None, hi=None):
    """4-bit signed quantization [-7,8] — the resolution cliff (more = noise)."""
    if lo is None:
        lo, hi = X.min(axis=0), X.max(axis=0)
    rng = np.where((hi - lo) == 0, 1, hi - lo)
    return np.clip(np.round((X - lo) / rng * (_QHIGH - _QLOW) + _QLOW),
                   _QLOW, _QHIGH), lo, hi

def _fisher(H, y, k):
    """Top-k dims by between-class / within-class variance (discriminative)."""
    overall = H.mean(0)
    sb = np.zeros(H.shape[1]); sw = np.zeros(H.shape[1])
    for c in np.unique(y):
        Hc = H[y == c]; mu = Hc.mean(0)
        sb += len(Hc) * (mu - overall) ** 2; sw += ((Hc - mu) ** 2).sum(0)
    sw[sw == 0] = 1e-9
    return np.argsort(-(sb / sw))[:k]


# ═════════════════════════════════════════════════════════════════
# WAVES — the temporal crystallizer.
#
# The static crystallizer compares door PROFILES: it is order-blind by
# construction. This pass watches the whole matrix MOVE — compares each
# instant to the next — and crystallizes three things the profile view
# cannot see:
#   simultaneity  doors that light together        (co-activation groups)
#   movement      one group dims as another lights (handoff edges)
#   circles       waves that return to their start (closed handoff paths)
# Applied recursively: a circle's activity becomes a door one level up.
#
# Null discipline: every claim must beat a JITTER null — small ±2..5-step
# shifts that keep each door's own rhythm and rate but break precise
# co-timing. (A full circular shift is the WRONG null for periodic waves:
# it relands in phase 1-in-period times, so real simultaneity could never
# beat it.) Jitter ONE side of each pair only — jittering both sometimes
# hands them the same shift, which preserves relative timing.
# ═════════════════════════════════════════════════════════════════

_wave_rng = np.random.default_rng(0)


def _wave_jitter(col):
    return np.roll(col, int(_wave_rng.choice([-5, -4, -3, -2, 2, 3, 4, 5])))


def _wave_groups(S, n_perm=40, pct=95):
    """SIMULTANEITY: doors that fire together. Must beat an independence
    floor (column permutation) AND a per-pair jitter null."""
    T, D = S.shape
    Z = (S - S.mean(0)) / (S.std(0) + 1e-12)
    C = (Z.T @ Z) / T
    floor_max = np.empty(n_perm)
    pair_null = np.empty((n_perm, D, D))
    for k in range(n_perm):
        Zp = np.column_stack([_wave_rng.permutation(Z[:, j]) for j in range(D)])
        Cp = (Zp.T @ Zp) / T
        np.fill_diagonal(Cp, 0)
        floor_max[k] = Cp.max()
        Zj = np.column_stack([_wave_jitter(Z[:, j]) for j in range(D)])
        pair_null[k] = (Z.T @ Zj) / T
    floor = np.percentile(floor_max, pct)
    pair_thr = np.percentile(pair_null, pct, axis=0)
    pair_thr = np.maximum(pair_thr, pair_thr.T)
    # 1.4x margin: connected components merge on a SINGLE edge, so a
    # borderline false pair (the ~5% per-pair leak) can bridge two real
    # groups into one. An edge must clearly beat its null, not graze it.
    adj = (C > 1.4 * floor) & (C > 1.4 * pair_thr)
    np.fill_diagonal(adj, False)
    groups, unseen = [], set(range(D))
    while unseen:
        stack = [unseen.pop()]; comp = set(stack)
        while stack:
            j = stack.pop()
            nxt = set(np.flatnonzero(adj[j])) & unseen
            unseen -= nxt; comp |= nxt; stack += list(nxt)
        if len(comp) > 1:
            groups.append(tuple(sorted(int(x) for x in comp)))
    return groups


def _wave_handoff_counts(Goff, Gon):
    """count[a,b] = instants where a switches off and b switches on (±1 step)."""
    m = Goff.shape[1]
    cnt = np.zeros((m, m))
    for a in range(m):
        off = ((Goff[:-1, a] == 1) & (Goff[1:, a] == 0)).astype(float)
        w = off.copy(); w[1:] += off[:-1]; w[:-1] += off[1:]
        for b in range(m):
            if a != b:
                on = (Gon[:-1, b] == 0) & (Gon[1:, b] == 1)
                cnt[a, b] = float((w * on).sum())
    return cnt


def _wave_edges(G, n_perm=40):
    """MOVEMENT: handoffs that beat 1.5× the jitter null's best day."""
    real = _wave_handoff_counts(G, G)
    m = G.shape[1]
    null = np.zeros((n_perm, m, m))
    for k in range(n_perm):
        Gj = np.column_stack([_wave_jitter(G[:, j]) for j in range(m)])
        null[k] = _wave_handoff_counts(G, Gj)
    thr = null.max(axis=0)
    return [(a, b) for a in range(m) for b in range(m)
            if a != b and real[a, b] > max(1.5 * thr[a, b], 2.0)]


def _wave_circles(edges, m):
    """CIRCLES: closed paths in the handoff graph (rotation-canonical)."""
    adj = defaultdict(list)
    for a, b in edges:
        adj[a].append(b)
    found = set()

    def dfs(start, node, path):
        for nxt in adj[node]:
            if nxt == start and len(path) > 1:
                k = path.index(min(path))
                found.add(tuple(path[k:] + path[:k]))
            elif nxt not in path and len(path) < m:
                dfs(start, nxt, path + [nxt])

    for s in range(m):
        dfs(s, s, [s])
    return sorted(found)


# ═════════════════════════════════════════════════════════════════
# DISCOVERY — the challenge loop. The thing that learns things.
#
# Given examples of something he cannot do, find the rule:
#   compare -> enumerate candidate relations -> admit only what beats its
#   null -> the survivors ARE the equation -> install it as a law node ->
#   the challenge is now computable.
# Term growth is STAGED (candidates grow only around admitted terms — no
# d^k blowup) and admission is NULL-GATED against the max-over-candidates
# correlation on permuted residuals (selection-effect decoys die).
# ═════════════════════════════════════════════════════════════════

def _atom_specs(d):
    """The vocabulary of forms. Linear-in-COEFFICIENTS over a NONLINEAR
    library: unary transcendentals (sin/cos/exp at a scale grid — so a
    single-input challenge is not reduced to polynomials) and pair forms.
    Scales k live INSIDE the nonlinearity, where regression cannot reach —
    the grid proposes them, the refine pass sharpens them. Complex-number
    structure enters as damped-oscillation pairs: exp(-at)*cos(bt) is the
    real face of exp((-a+bi)t)."""
    specs = [("var", i, None, None) for i in range(d)]
    for i in range(d):
        for k in (0.5, 1.0, 2.0, 3.0, 4.5, 6.0, 8.0):
            specs += [("sin", i, None, k), ("cos", i, None, k)]
        for k in (0.25, 0.5, 1.0, -0.25, -0.5, -1.0):   # decay AND growth
            specs.append(("exp", i, None, k))
        for k in (-2.0, -1.0, -0.5, 0.5, 1.5):          # power laws (Kepler,
            specs.append(("pow", i, None, k))           # inverse-square...)
    for i in range(d):
        for j in range(i + 1, d):
            for k in (0.5, 1.0, 2.0):
                specs += [("cosd", i, j, k), ("sind", i, j, k)]
            for k in (0.5, 1.0, 1.5):
                specs.append(("coshd", i, j, k))
    return specs


def _atom_col(X, spec):
    kind, i, j, k = spec
    if kind == "var":
        return X[:, i]
    if kind == "sin":
        return np.sin(k * X[:, i])
    if kind == "cos":
        return np.cos(k * X[:, i])
    if kind == "exp":
        return np.exp(np.clip(-k * X[:, i], -30, 30))
    if kind == "pow":
        return np.power(np.maximum(np.abs(X[:, i]), 1e-9), k)
    diff = np.clip(X[:, i] - X[:, j], -20, 20)
    if kind == "cosd":
        return np.cos(k * diff)
    if kind == "sind":
        return np.sin(k * diff)
    return np.cosh(np.clip(k * diff, -15, 15))


def _atom_label(spec):
    kind, i, j, k = spec
    if kind == "var":
        return f"x{i}"
    if kind == "sin":
        return f"sin({k:g}*x{i})"
    if kind == "cos":
        return f"cos({k:g}*x{i})"
    if kind == "exp":
        return f"exp({-k:g}*x{i})"
    if kind == "pow":
        return f"x{i}^{k:g}"
    op = {"cosd": "cos", "sind": "sin", "coshd": "cosh"}[kind]
    return f"{op}({k:g}*(x{i}-x{j}))"


def _disc_col(A, term):
    v = A[:, term[0]].copy()
    for a in term[1:]:
        v = v * A[:, a]
    return v


class _Enumerator:
    def __init__(self, max_degree=3, n_perm=40, pct=95, max_terms=16):
        self.max_degree, self.n_perm, self.pct = max_degree, n_perm, pct
        # max_terms: on AUTOCORRELATED real data (e.g. a smooth time series)
        # the iid permutation null is too easy — shuffling destroys the
        # autocorrelation, so weak junk beats it forever and admission never
        # stops (found the hard way: a 20-CPU-hour runaway on sunspots).
        # The cap is the emergency brake; the proper cure is a BLOCK
        # permutation null for temporal targets (post-mortem item).
        self.max_terms = max_terms
        self.terms, self.coefs, self.intercept = [], np.array([]), 0.0

    def fit(self, X, y):
        self.X = X
        self.specs = _atom_specs(X.shape[1])
        self.A = np.column_stack([_atom_col(X, s) for s in self.specs])
        n_atoms = self.A.shape[1]
        n_vars = X.shape[1]
        frontier = [(i,) for i in range(n_atoms)]
        frontier += [(i, j) for i in range(n_vars) for j in range(i, n_vars)]
        seen = set(frontier)
        while len(self.terms) < self.max_terms:
            cand = [t for t in frontier if t not in self.terms]
            M = np.column_stack([_disc_col(self.A, t) for t in cand])
            Ms = (M - M.mean(0)) / (M.std(0) + 1e-12)
            r = y - self._fit_predict(y)
            rs = (r - r.mean()) / (r.std() + 1e-12)
            real = np.abs(Ms.T @ rs) / len(y)
            null_max = np.empty(self.n_perm)
            for k in range(self.n_perm):
                null_max[k] = np.max(np.abs(Ms.T @ _wave_rng.permutation(rs))) / len(y)
            gate = np.percentile(null_max, self.pct)
            if real.max() <= gate:
                break                               # nothing beats its null
            # raw residual correlation is myopic: a degenerate surrogate (a
            # wide cosine mimicking a parabola) can out-correlate the TRUE
            # form on a bounded range. Judge the top candidates by how far
            # they actually go — trial-admit, refit, sharpen the inside-
            # parameter, score by train R2; parsimony breaks ties.
            base = list(self.terms)
            trials = []
            # shortlist needs STRUCTURAL DIVERSITY, not just top correlation:
            # bounded transcendental atoms are better-conditioned than heavy-
            # tailed raw variables, so the true raw-variable factor can sit
            # below the correlation top-10 and never get trialed. Guarantee
            # the best simple candidates (raw vars, low flexibility) a trial.
            ranks = [int(i) for i in np.argsort(-real)]
            simple = [ci for ci in ranks
                      if any(self.specs[a][0] == "var" for a in cand[ci])
                      and sum(1 for a in cand[ci]
                              if self.specs[a][3] is not None) <= 1]
            pure = [ci for ci in ranks
                    if all(self.specs[a][3] is None for a in cand[ci])]
            shortlist = list(dict.fromkeys(ranks[:8] + simple[:4] + pure[:3]))
            for ci in shortlist:
                if real[ci] <= gate:
                    continue
                self.terms = base + [cand[ci]]
                self._refit(y)
                self._refine_term(y, len(self.terms) - 1)
                # explicit parsimony pressure: a scale-parameterized atom is
                # flexible enough to mimic simpler forms on a bounded range
                # (a wide cosine IS a parabola locally) — so it must BUY its
                # flexibility with real R2. Flexibility already paid for is
                # free: only NEWLY introduced scale-atoms are charged.
                used_atoms = {a for t0 in base for a in t0}
                comp = sum(1 for a in self.terms[-1]
                           if self.specs[a][3] is not None
                           and a not in used_atoms)
                r2t = self._train_r2(y)
                pred = self._fit_predict(y)
                trials.append(dict(
                    done=r2t >= 0.995, r2=r2t,
                    sse=float(np.sum((y - pred) ** 2)), comp=comp,
                    tlen=len(self.terms[-1]), terms=list(self.terms)))
                self.terms = base
            if not trials:
                break
            done_set = [tr for tr in trials if tr["done"]]
            if done_set:
                # completers are judged STATISTICALLY: the F-test says
                # whether the best completer's edge over a rival is real
                # (red-team A1: gap 0.00024 in R2 was F~80, decisive) or a
                # noise-ceiling tie (2%-term surrogates: F~4). Significance
                # decides; genuine ties go to the SIMPLER form.
                bestd = min(done_set, key=lambda tr: tr["sse"])
                dof = max(bestd["sse"] / len(y), 1e-30)
                tied = [tr for tr in done_set
                        if (tr["sse"] - bestd["sse"]) / dof < 10.0]
                chosen = min(tied, key=lambda tr: (tr["comp"], tr["tlen"],
                                                   tr["sse"]))
            else:
                chosen = max(trials,
                             key=lambda tr: (tr["r2"] - 0.02 * tr["comp"],
                                             -tr["tlen"]))
            self.terms = chosen["terms"]
            self._refit(y)
            t = self.terms[-1]
            if len(t) < self.max_degree:            # beam: grow around winners
                for a in range(n_atoms):
                    nt = tuple(sorted(t + (a,)))
                    if len(nt) <= self.max_degree and nt not in seen:
                        seen.add(nt); frontier.append(nt)
        self._refine(y)                             # sharpen inside-parameters
        if self.terms:                              # a term must carry weight
            keep = [t for t, c in zip(self.terms, self.coefs)
                    if abs(c) * _disc_col(self.A, t).std() > 0.02 * y.std()]
            self.terms = keep
            self._refit(y)
        return self

    def _refine(self, y, sweeps=3):
        """Regression finds coefficients; it cannot reach parameters INSIDE a
        nonlinearity (frequency, decay, scale). Hill-climb each admitted
        term's k by trial-refit — the grid proposes, this sharpens."""
        if not self.terms:
            return
        self._refit(y)
        for _ in range(sweeps):
            improved = False
            for ti in range(len(self.terms)):
                improved |= self._refine_term(y, ti)
            if not improved:
                break

    def _refine_term(self, y, ti, sweeps=2):
        improved_any = False
        for _ in range(sweeps):
            improved = False
            t = self.terms[ti]
            for pos, ai in enumerate(t):
                kind, i, j, k = self.specs[ai]
                if k is None:
                    continue
                base = self._train_r2(y)
                for mult in (0.7, 0.85, 1.15, 1.4):
                    s2 = (kind, i, j, float(k * mult))
                    self.specs.append(s2)
                    self.A = np.column_stack([self.A, _atom_col(self.X, s2)])
                    trial = list(t); trial[pos] = len(self.specs) - 1
                    old = self.terms[ti]
                    self.terms[ti] = tuple(trial)
                    self._refit(y)
                    if self._train_r2(y) > base + 1e-6:
                        improved = improved_any = True
                        t = self.terms[ti]
                        break
                    self.terms[ti] = old
                    self._refit(y)
            if not improved:
                break
        return improved_any

    def _train_r2(self, y):
        p = self._fit_predict(y)
        ss = float(np.sum((y - y.mean()) ** 2))
        return 1 - float(np.sum((y - p) ** 2)) / max(ss, 1e-12)

    def rival_check(self, y, f_thr=10.0):
        """IDENTIFIABILITY: the classic look-alikes (parabola vs wide cosine,
        exponential vs cubic, decay vs hyperbola...) agree on the dense
        center of the data and split in tails and past turning points. For
        each admitted single-feature term, swap in each rival FORM, refit,
        refine, F-test. Rivals the data cannot reject stay ALIVE on the law's
        record, each with a PROBE: where to sample to split them."""
        SHAPES = [("linear", [("var",)]),
                  ("quadratic", [("var",), ("var",)]),
                  ("cubic", [("var",), ("var",), ("var",)]),
                  ("cosine", [("cos", 1.0)]),
                  ("sine", [("sin", 1.0)]),
                  ("exp_decay", [("exp", 0.5)]),
                  ("exp_growth", [("exp", -0.5)])]
        out = []
        n = len(y)
        base_terms = [tuple(t) for t in self.terms]
        base_sse = float(np.sum((y - self._fit_predict(y)) ** 2))
        base_coefs, base_int = self.coefs.copy(), self.intercept
        for ti, t in enumerate(base_terms):
            feats = {self.specs[a][1] for a in t}
            feats |= {self.specs[a][2] for a in t
                      if self.specs[a][2] is not None}
            if len(feats) != 1:
                continue                      # unary confusions first
            i = int(list(feats)[0])
            kinds = tuple(sorted(self.specs[a][0] for a in t))
            for shape_name, atoms in SHAPES:
                s_kinds = tuple(sorted(a[0] for a in atoms))
                if s_kinds == kinds:
                    continue                  # that IS the current form
                term = []
                for a in atoms:
                    spec = (a[0], i, None, a[1] if len(a) > 1 else None)
                    self.specs.append(spec)
                    self.A = np.column_stack([self.A,
                                              _atom_col(self.X, spec)])
                    term.append(len(self.specs) - 1)
                self.terms = [list(x) for x in base_terms]
                self.terms[ti] = tuple(term)
                self.terms = [tuple(x) for x in self.terms]
                self._refit(y)
                self._refine_term(y, ti)
                sse = float(np.sum((y - self._fit_predict(y)) ** 2))
                better = min(sse, base_sse)
                F = (max(sse, base_sse) - better) / max(better / n, 1e-30)
                if F < f_thr:                 # the data cannot tell them apart
                    lo, hi = self.X[:, i].min(), self.X[:, i].max()
                    span = hi - lo
                    xs = np.linspace(lo - 0.75 * span, hi + 0.75 * span, 300)
                    Xs = np.tile(np.median(self.X, axis=0), (300, 1))
                    Xs[:, i] = xs
                    p_riv = self.predict(Xs)
                    riv = dict(terms=[list(x) for x in self.terms],
                               coefs=self.coefs.copy(),
                               intercept=self.intercept,
                               specs=list(self.specs),
                               equation=self.equation())
                    self.terms = [tuple(x) for x in base_terms]
                    self.coefs, self.intercept = base_coefs, base_int
                    p_cho = self.predict(Xs)
                    gap = np.abs(p_cho - p_riv)
                    x_star = float(xs[int(np.argmax(gap))])
                    out.append(dict(term=ti, feature=i, rival=shape_name,
                                    F=round(float(F), 1), model=riv,
                                    probe=dict(feature=i, x=round(x_star, 2),
                                               gap=round(float(gap.max()), 3),
                                               beyond=bool(x_star < lo or
                                                           x_star > hi)),
                                    rival_equation=riv["equation"]))
                self.terms = [tuple(x) for x in base_terms]
                self._refit(y)
        self.terms = [tuple(x) for x in base_terms]
        self._refit(y)
        return out

    def _design(self, A=None):
        A = self.A if A is None else A
        if not self.terms:
            return np.ones((A.shape[0], 1))
        return np.column_stack([_disc_col(A, t) for t in self.terms]
                               + [np.ones(A.shape[0])])

    def _refit(self, y):
        beta = np.linalg.lstsq(self._design(), y, rcond=None)[0]
        self.coefs, self.intercept = beta[:-1], float(beta[-1])

    def _fit_predict(self, y):
        if not self.terms:
            return np.full_like(y, y.mean())
        return self._design() @ np.concatenate([self.coefs, [self.intercept]])

    def predict(self, X):
        X = np.asarray(X, float)
        if not self.terms:
            return np.full(len(X), self.intercept)
        used = sorted({a for t in self.terms for a in t})
        cols = {a: _atom_col(X, self.specs[a]) for a in used}
        D = np.column_stack(
            [np.prod([cols[a] for a in t], axis=0) for t in self.terms]
            + [np.ones(len(X))])
        return D @ np.concatenate([self.coefs, [self.intercept]])

    def equation(self):
        if not self.terms:
            return "NO RULE (nothing beat the null)"
        parts = [f"{c:+.2f}*{'*'.join(_atom_label(self.specs[a]) for a in t)}"
                 for t, c in zip(self.terms, self.coefs)]
        return " ".join(parts) + f" {self.intercept:+.2f}"


class Isaac:
    def __init__(self):
        self.net = Net()
        self.starts = set()
        self.types = {}
        self.rules = []
        self.lockouts = set()
        self.observed_sequences = []      # raw record (Rule 5: store raw)
        self.fact_index = defaultdict(list)  # (subject, relation) → [objects]
        self.scratch = Scratch()          # working memory: his registers / RAM
        self.composites = []              # learned combinations — first-class,
                                          # reused by every future discover()
        self._compiled = None

        # ── pipeline state ──────────────────────────────────────
        self._compiled_up_to = 0          # how many sequences are in the matrix
        self._dirty_nodes = set()         # nodes with new doors since last consolidation
        self._consolidated_up_to = 0     # how many sequences consolidated
        self._type_profiles = {}          # cached type profiles

        # ── wave state ──────────────────────────────────────────
        self.activation_log = []          # one frozenset of active nodes per instant
        self.wave_logging = True          # observe/think record ticks automatically
        self.waves = {}                   # wave_consolidate() results
        self.followed = {}                # circles being tracked (his clock)
        self.phase_log = {}               # circle -> [(log_index, phase)]
        self.world = World(self)          # entity states: temporary statuses live here

        # ── findings ledger: durable, searchable scientific memory ──
        self.findings = []                # structured records of what he knows
        self.ledger_path = None           # set to a .jsonl path to persist

    # ── observation ─────────────────────────────────────────────

    def observe(self, tokens):
        """Stage 1 (SENSE): tokens in, doors built, dirty set updated,
        immediate type-slotting for known categories."""
        if not tokens:
            return
        self.starts.add(tokens[0])
        self.net.set_meta(tokens[0], "start", True)
        for i in range(len(tokens) - 1):
            self.net.add_door(tokens[i], tokens[i + 1], tag="seq")
        self.observed_sequences.append(list(tokens))
        # Mark dirty — new data not yet consolidated
        for t in tokens:
            self._dirty_nodes.add(t)
        # Stage 1: immediately slot new tokens into existing types
        self._sense(tokens)
        # wave sensing: each token is one instant; it lights together with
        # the types it opens — simultaneity the wave pass can see
        if self.wave_logging:
            for t in tokens:
                self.tick({t} | self.net.get_doors(t, tag="type"))

    def _sense(self, tokens):
        """Stage 1 (SENSE): check if new tokens fit existing types.
        Immediate slotting — O(k × T), runs on every observe.
        Full type discovery waits for consolidate()."""
        if not self.types:
            return
        for token in set(tokens):
            # Skip if already typed
            if self.net.get_doors(token, tag="type"):
                continue
            preds = self.net.get_predecessors(token, tag="seq")
            succs = self.net.get_doors(token, tag="seq")
            if not preds and not succs:
                continue
            for tname, tdata in self.types.items():
                tp = tdata.get("preds", set())
                ts = tdata.get("succs", set())
                shared_p = preds & tp if tp else set()
                shared_s = succs & ts if ts else set()
                if len(shared_p) + len(shared_s) >= 2:
                    tdata["members"].add(token)
                    self.net.add_door(token, tname, tag="type")
                    break

    def observe_negative(self, tokens):
        """Same mechanism, different tag. Negation is contrast, not storage."""
        if not tokens:
            return
        for i in range(len(tokens) - 1):
            self.net.add_door(tokens[i], tokens[i + 1], tag="neg")

    def observe_matrix(self, matrix, row_prefix=None):
        """Observe a 2D data matrix. Each row becomes a sequence of tokens.
        No preprocessing. No feature extraction. Just the numbers.

        matrix: 2D numpy array or list of lists
        row_prefix: optional prefix per row (e.g., 'r0', 'r1', ...) for position
        """
        for i, row in enumerate(matrix):
            tokens = [str(int(v)) for v in row]
            if row_prefix:
                tokens.insert(0, f"{row_prefix}{i}")
            self.observe(tokens)

    def observe_frame(self, frame, label=None):
        """Observe a full video/game frame as a matrix.
        Handles 2D (grayscale) or 3D (color) arrays.
        Flattens color channels per pixel. Each row is one observation.

        frame: numpy array (H, W) or (H, W, C)
        label: optional frame label (e.g., 'f0', 'f1', ...) prepended to first row
        """
        if frame.ndim == 3:
            # Color frame: flatten channels per pixel
            h, w, c = frame.shape
            flat = frame.reshape(h, w * c)
        else:
            flat = frame

        for i, row in enumerate(flat):
            tokens = [str(int(v)) for v in row]
            if label and i == 0:
                tokens.insert(0, label)
            self.observe(tokens)

    def observe_tagged(self, tokens, tag):
        """Observe with a custom tag. Properties, relations, anything."""
        if not tokens:
            return
        for i in range(len(tokens) - 1):
            self.net.add_door(tokens[i], tokens[i + 1], tag=tag)

    def teach(self, subject, relation, obj):
        """Teach a fact. Observes as a sequence AND indexes for relation lookup."""
        self.observe(tokenize(f"{subject} {relation} {obj}"))
        self.fact_index[(subject, relation)].append(obj)

    def teach_not(self, subject, prop):
        """A POSITIVE NEGATIVE (owner's law, 2026-07-03): 'penguin does not
        fly' is evidence, not absence. Indexed as a cannot-fact (the
        reasoning layer already honors those) AND written as a first-class
        not_<prop> door, so negative knowledge is present in door profiles
        — where crystallization can both SEE it (penguins and ostriches
        share not_fly) and be VETOED by it (known-different never merges;
        only unknown may)."""
        if prop not in self.fact_index[(subject, "cannot")]:
            self.fact_index[(subject, "cannot")].append(prop)
        self.net.add_door(subject, f"not_{prop}", tag="neg")

    # ── crystallization ─────────────────────────────────────────

    def _crystallize(self, tag="seq", min_shared=2, verbose=False, scope=None):
        """Internal: discover types by comparing door profiles. FCA closure.
        If scope is provided, only pairs involving at least one scope node
        are compared — O(d×n) instead of O(n²)."""
        nodes = sorted([n for n in self.net.all_nodes()
                        if not n.startswith("type:")])
        scope_set = set(scope) if scope else None

        # Phase 1: raw circles via FCA
        circles = []
        seen = set()
        seen_pairs = set()
        for i, a in enumerate(nodes):
            preds_a = self.net.get_predecessors(a, tag=tag)
            succs_a = self.net.get_doors(a, tag=tag)
            if not preds_a and not succs_a:
                continue
            for b in nodes[i + 1:]:
                # Scoped: skip pairs where neither node is dirty
                if scope_set and a not in scope_set and b not in scope_set:
                    continue
                preds_b = self.net.get_predecessors(b, tag=tag)
                succs_b = self.net.get_doors(b, tag=tag)
                shared_p = preds_a & preds_b
                shared_s = succs_a & succs_b
                if len(shared_p) + len(shared_s) < min_shared:
                    continue
                members = {a, b}
                for n in nodes:
                    if n in members:
                        continue
                    np_ = self.net.get_predecessors(n, tag=tag)
                    ns_ = self.net.get_doors(n, tag=tag)
                    if shared_p <= np_ and shared_s <= ns_:
                        members.add(n)
                key = frozenset(members)
                if key not in seen and len(members) >= 2:
                    seen.add(key)
                    circles.append({"members": members,
                                    "preds": shared_p, "succs": shared_s})

        # Phase 1.5 (the owner's foundation law, 2026-07-03): DIVERGENT
        # doors SELF-ASSEMBLE. The atom's three verdicts finally all write:
        #   SAME      -> membership (always did)
        #   DIVERGENT -> a not_<door> minted from experience
        #   ABSENT    -> nothing (insufficient evidence stays silent)
        # A node that carries the REST of a circle's intent, observed
        # repeatedly WITHOUT the one door its siblings show essentially
        # always, has positively diverged — penguin earns not_fly by being
        # WATCHED, not taught. The null is "this node is like its
        # siblings"; the gate is a smoothed binomial on observation
        # counts, not a constant. Runs BEFORE the merge so a fresh
        # negative can veto a collapse in the same sleep.
        counts = getattr(self.net, "door_counts", {})
        for c in circles:
            intent = {d for d in c["succs"]
                      if not (isinstance(d, str) and d.startswith("not_"))}
            if len(intent) < 2:
                continue
            for d in intent:
                rest = intent - {d}
                obs_sib = sum(max((counts.get((s, r), 0) for r in rest),
                                  default=0) for s in c["members"])
                with_d = sum(counts.get((s, d), 0) for s in c["members"])
                p_hat = (with_d + 1) / (obs_sib + 2)     # Laplace-smoothed
                for m in nodes:
                    if m in c["members"]:
                        continue
                    ms = self.net.get_doors(m, tag=tag)
                    if d in ms or not (rest <= ms):
                        continue
                    n_m = min(counts.get((m, r), 0) for r in rest)
                    # repeatable evidence (>= 3 sightings) AND absence must
                    # beat the like-your-siblings null at 1%
                    if n_m >= 3 and (1 - p_hat) ** n_m < 0.01:
                        self.net.add_door(m, f"not_{d}", tag="neg")
                        if d not in self.fact_index[(m, "cannot")]:
                            self.fact_index[(m, "cannot")].append(d)

        # Phase 2: merge overlapping circles (Rule 13; AMENDED 2026-07-03
        # to the owner's two laws). (1) Merge ONLY near-identical member
        # sets (overlap vs the LARGER set): a proper subgroup is a real
        # thing of its own — abc and abd are not the same thing; both may
        # belong to ab via the hierarchy, never by dissolving into it.
        # (2) A POSITIVE NEGATIVE VETOES any merge: penguin not_fly is
        # evidence, not absence — a merge that would erase a distinction
        # some member has positively disclaimed is forbidden. Unknown may
        # collapse; known-different never does.
        def _negs_of(members):
            out = set()
            for m in members:
                out |= set(self.fact_index.get((m, "cannot"), []))
                for t in (tag, "neg"):
                    out |= {d[4:] for d in self.net.get_doors(m, tag=t)
                            if isinstance(d, str) and d.startswith("not_")}
            return out

        def _pos_of(c):
            return {d for d in c["succs"]
                    if not (isinstance(d, str) and d.startswith("not_"))}

        merged = []
        used = set()
        circles.sort(key=lambda c: len(c["members"]), reverse=True)
        for i, c in enumerate(circles):
            if i in used:
                continue
            current = {"members": set(c["members"]),
                       "preds": set(c["preds"]), "succs": set(c["succs"])}
            for j in range(i + 1, len(circles)):
                if j in used:
                    continue
                other = circles[j]
                larger = max(len(current["members"]), len(other["members"]))
                overlap = len(current["members"] & other["members"])
                if larger == 0 or overlap / larger < 0.8:
                    continue          # subgroup/sibling: keep it its own thing
                if (_pos_of(current) & _negs_of(other["members"])
                        or _pos_of(other) & _negs_of(current["members"])):
                    continue          # positively negative: never collapse
                current["members"] |= other["members"]
                current["preds"] &= other["preds"]
                current["succs"] &= other["succs"]
                used.add(j)
            merged.append(current)

        # Phase 3: name and write to net
        self.types = {}
        for c in merged:
            name = f"type:{'_'.join(sorted(c['members'])[:2])}[{len(c['members'])}]"
            c["name"] = name
            c["parent"] = None
            c["children"] = []
            self.types[name] = c
            for m in c["members"]:
                self.net.add_door(m, name, tag="type")

        # Phase 3.5 (owner's law, 2026-07-03): WRONG IS KEPT AND CLASSIFIED.
        # "knowing what is right is intelligence. knowing what is wrong is
        # wisdom." Every type is tested against its chance-null — the same
        # context with door targets shuffled (degrees preserved), scored by
        # the BEST structure chance produces (selection-corrected). Types
        # that fail are NOT deleted and NOT prevented: they are filed in
        # the wrong section with the WHY attached, so error itself becomes
        # learnable material. Downstream behavior is deliberately unchanged
        # (no pruning, no importance-weighting — the old trap).
        def _best_chance_score(n_shuffles=8):
            edges = []
            for a in nodes:
                for t in self.net.get_doors(a, tag=tag):
                    edges.append((a, t))
            if len(edges) < 4:
                return 0.0
            srcs = [e[0] for e in edges]
            tgts = [e[1] for e in edges]
            best = 0.0
            srng = np.random.default_rng(len(edges))
            for _ in range(n_shuffles):
                perm = srng.permutation(len(tgts))
                succs_s = defaultdict(set)
                preds_s = defaultdict(set)
                for k, s in enumerate(srcs):
                    t = tgts[perm[k]]
                    succs_s[s].add(t)
                    preds_s[t].add(s)
                ns = sorted(set(succs_s) | set(preds_s))
                for i, a in enumerate(ns):
                    for b in ns[i + 1:]:
                        sh_s = succs_s[a] & succs_s[b]
                        sh_p = preds_s[a] & preds_s[b]
                        if len(sh_s) + len(sh_p) < min_shared:
                            continue
                        mem = sum(1 for m in ns
                                  if sh_s <= succs_s[m] and sh_p <= preds_s[m])
                        best = max(best,
                                   (mem - 1) * (len(sh_s) + len(sh_p)))
            return best

        chance_best = _best_chance_score()
        self.wrong_types = {}
        for c in merged:
            score = (len(c["members"]) - 1) * (len(c["preds"])
                                               + len(c["succs"]))
            c["score"] = score
            if score <= chance_best:
                why = (f"coherence {score} within chance for this context "
                       f"(best shuffled structure scores {chance_best}) — "
                       f"co-occurrence alone explains it")
                c["verdict"] = "wrong"
                c["why_wrong"] = why
                self.wrong_types[c["name"]] = c
                self.net.set_meta(c["name"], "verdict", "wrong")
                self.net.set_meta(c["name"], "why_wrong", why)
            else:
                c["verdict"] = "sound"
                self.net.set_meta(c["name"], "verdict", "sound")

        # Phase 4: hierarchy (subset = child)
        type_list = list(self.types.values())
        for child in type_list:
            for parent in type_list:
                if child is parent:
                    continue
                if len(child["members"]) >= len(parent["members"]):
                    continue
                overlap = len(child["members"] & parent["members"])
                if overlap / len(child["members"]) >= 0.8:
                    child["parent"] = parent["name"]
                    parent["children"].append(child["name"])
                    self.net.add_door(child["name"], parent["name"],
                                     tag="subtype_of")
                    break

        # Phase 5: discover rules (co-occurring predecessors)
        self.rules = []
        pred_sets = defaultdict(set)
        for n in nodes:
            for p in self.net.get_predecessors(n, tag=tag):
                pred_sets[p].add(n)
        preds = [p for p, ns in pred_sets.items() if len(ns) >= 3]
        for i, a in enumerate(preds):
            for b in preds[i + 1:]:
                overlap = len(pred_sets[a] & pred_sets[b])
                ratio_a = overlap / len(pred_sets[a]) if pred_sets[a] else 0
                ratio_b = overlap / len(pred_sets[b]) if pred_sets[b] else 0
                if ratio_a >= 0.8 or ratio_b >= 0.8:
                    self.rules.append((a, b, round(max(ratio_a, ratio_b), 2)))
                    self.net.add_door(a, b, tag="cooccurs")

        # Phase 6: violations (seq vs neg contrast)
        self._discover_violations()

        # Phase 7: initiator ranking
        for s in self.starts:
            strength = len(self.net.get_doors(s, tag="seq"))
            self.net.set_meta(s, "initiator_strength", strength)

        if verbose:
            print(f"  crystallized: {len(self.types)} types, "
                  f"{len(self.rules)} rules, {len(self.lockouts)} lockouts")
        return self.types

    def _discover_violations(self):
        """Compare seq doors vs neg doors. The difference IS negation."""
        seq_pairs = set()
        neg_pairs = set()
        for (src, tgt), tags in self.net.door_tags.items():
            if "seq" in tags:
                seq_pairs.add((src, tgt))
            if "neg" in tags:
                neg_pairs.add((src, tgt))
        for src, tgt in (neg_pairs - seq_pairs):
            self.net.add_door(src, tgt, tag="lockout")
            self.lockouts.add((src, tgt))

    # ── compilation ─────────────────────────────────────────────
    # Doors → matrix. Same information, different representation.
    # W[delta, frame] = door count. y = W @ x. Answer from y.

    def _ensure_compiled(self):
        """Stage 3 (ROUTE): lazy compilation. Only recompile if dirty.
        Called automatically before any inference. Never call compile() manually."""
        if self._compiled_up_to < len(self.observed_sequences):
            self._compile()
        return self._compiled is not None

    def _compile(self, max_context=7):
        """Internal: build the weight matrix from observed sequences."""
        pairs = []
        for seq in self.observed_sequences:
            if len(seq) < 2:
                continue
            frame = tuple(seq[:-1])
            delta = seq[-1]
            pairs.append((frame, delta))
            for width in range(2, min(len(frame) + 1, max_context)):
                partial = frame[-width:]
                if partial != frame:
                    pairs.append((partial, delta))

        if not pairs:
            self._compiled = None
            self._compiled_up_to = len(self.observed_sequences)
            return None

        frames = sorted(set(f for f, d in pairs))
        deltas = sorted(set(d for f, d in pairs))
        fidx = {f: i for i, f in enumerate(frames)}
        didx = {d: i for i, d in enumerate(deltas)}

        W = np.zeros((len(deltas), len(frames)), dtype=np.float32)
        for frame, delta in pairs:
            W[didx[delta], fidx[frame]] += 1.0
        col_sums = W.sum(axis=0, keepdims=True)
        col_sums[col_sums == 0] = 1
        W_norm = W / col_sums

        self._compiled = {
            "W": W, "W_norm": W_norm,
            "frames": frames, "deltas": deltas,
            "fidx": fidx, "didx": didx,
        }
        self._compiled_up_to = len(self.observed_sequences)
        return {
            "frames": len(frames), "deltas": len(deltas),
            "nonzero": int((W != 0).sum()),
            "matrix_shape": W.shape,
        }

    def compile(self, max_context=7):
        """Convenience wrapper. Prefer automatic compilation via lookup/check."""
        return self._compile(max_context)

    def consolidate(self, tag="seq", min_shared=2, verbose=False, full=False):
        """IDLE MODE: Crystallization of dirty regions.
        Run when nothing is waiting. This is sleep.

        By default, scopes to dirty nodes — O(d×n) instead of O(n²).
        Pass full=True to force a complete re-crystallization."""
        scope = None if full or not self._dirty_nodes else list(self._dirty_nodes)
        result = self._crystallize(tag=tag, min_shared=min_shared,
                                   verbose=verbose, scope=scope)
        self._consolidated_up_to = len(self.observed_sequences)
        self._dirty_nodes.clear()
        return result

    def crystallize(self, tag="seq", min_shared=2, verbose=False):
        """Convenience alias. Runs full (unscoped) consolidation."""
        return self.consolidate(tag=tag, min_shared=min_shared,
                                verbose=verbose, full=True)

    # ── waves: temporal crystallization ─────────────────────────

    def tick(self, active):
        """Record one instant of simultaneous activation. Any sensing path
        may call this directly (a retina, a game loop, a sensor frame);
        observe() and the think loop call it automatically.

        If a circle is being followed (see follow()), every tick also advances
        his phase register, registers expectation against observation, and
        opens/clears temporary statuses — whose miss-doors join THIS tick, so
        the ordinary machinery can crystallize them later. (Clock ticks are
        sensory ticks: mixing unrelated observe() streams into a followed
        sensor stream will dead-reckon the clock forward — keep one stream
        per episode, or pause with wave_logging=False.)"""
        if not active:
            return
        active = set(active)
        for circle in list(self.followed):
            active |= self._track(circle, active)
        self.activation_log.append(frozenset(active))

    def follow(self, circle):
        """Attend to a discovered circle: initialize his clock over its phases.
        State lives in scratch; transitions are the circle's own wave_next
        doors; dwell (for dead reckoning) was learned at consolidation."""
        phases = [p for p in self.net.get_predecessors(circle, tag="wave")
                  if str(p).startswith("wave:")]
        if not phases:
            return False
        order, pset = [phases[0]], set(phases)
        while len(order) < len(phases):
            nxt = [d for d in self.net.get_doors(order[-1], tag="wave_next")
                   if d in pset and d not in order]
            if not nxt:
                order += [p for p in phases if p not in order]
                break
            order.append(nxt[0])
        self.followed[circle] = {
            "order": order,
            "members": {p: set(self.net.get_predecessors(p, tag="wave"))
                        for p in order},
            "dwell": {p: float(self.net.get_meta(p, "dwell", 3.0))
                      for p in order}}
        self.scratch.write(f"phase@{circle}", None)
        self.scratch.write(f"dwell@{circle}", 0)
        self.phase_log.setdefault(circle, [])
        return True

    def _track(self, circle, active):
        """One clock step: evidence advances the phase (via recognize_doors —
        partial recognition, so an occluded entity still fires); learned dwell
        dead-reckons when evidence is hidden. Expected-but-dark doors that
        persist open temporary statuses: a status is a world-state fact AND a
        door fed back into the stream."""
        f = self.followed[circle]
        reg, dw = f"phase@{circle}", f"dwell@{circle}"
        fired = self.recognize_doors(active, tag="part", threshold=0.5)
        cur = self.scratch.read(reg)
        order = f["order"]
        if cur is None:                                # first evidence seats the clock
            cands = [p for p in order if p in fired]
            if not cands:
                return set()
            cur = max(cands, key=lambda p: fired[p])
            self.scratch.write(reg, cur)
            self.scratch.write(dw, 0)
        nxt = order[(order.index(cur) + 1) % len(order)]
        advanced = False
        if fired.get(nxt, 0) >= 0.5 and fired.get(cur, 0) < 0.5:
            advanced = True
        elif cur not in fired and (self.scratch.read(dw) or 0) >= f["dwell"][cur]:
            advanced = True
        if advanced:
            # the entity leaves the stage: nothing is expected of it now, so
            # its open statuses close (absence-by-night is not a status)
            for d in f["members"][cur]:
                self.scratch.write(f"miss#{circle}#{d}", 0)
                self.world.clear_state(cur, f"missing {d}")
            self.scratch.write(reg, nxt); self.scratch.write(dw, 0); cur = nxt
        else:
            self.scratch.incr(dw)
        # registration: what the phase EXPECTS vs what is seen
        extras = set()
        for d in f["members"][cur]:
            key = f"miss#{circle}#{d}"
            if d in active:
                self.scratch.write(key, 0)
                self.world.clear_state(cur, f"missing {d}")
            else:
                self.scratch.incr(key)
                if (self.scratch.read(key) or 0) >= 2:   # persistent, not flicker
                    extras.add(f"miss:{d}")
                    self.world.set_state(cur, f"missing {d}")
        self.phase_log[circle].append((len(self.activation_log), cur))
        return extras

    def _teach_fact(self, subject, relation, obj):
        """Index a discovered relation for the reasoning layer (fact_index +
        a tagged door). Not teach(): the tokenizer would shred structured
        node names like 'wave:a_b[2]'."""
        if obj not in self.fact_index[(subject, relation)]:
            self.fact_index[(subject, relation)].append(obj)
        self.net.add_door(str(subject), str(obj), tag=relation)

    # ── whole-mind persistence ──────────────────────────────────

    def save(self, path):
        """Snapshot the WHOLE mind — net, doors, types, facts, laws,
        compiled matrix, activation log, world state, findings — one file.
        (The ledger persists his science; this persists HIM.)"""
        import pickle
        with open(path, "wb") as f:
            pickle.dump(self, f, protocol=pickle.HIGHEST_PROTOCOL)
        return path

    @staticmethod
    def load(path):
        """Resurrect a saved mind, exactly as it was."""
        import pickle
        with open(path, "rb") as f:
            mind = pickle.load(f)
        if not isinstance(mind, Isaac):
            raise ValueError("not an Isaac snapshot")
        return mind

    def fork(self):
        """A living branch: deep-copy this mind for counterfactual work —
        teach the fork something, see what follows, keep it or let it go.
        The original is untouched."""
        import copy
        return copy.deepcopy(self)

    # ── the findings ledger ─────────────────────────────────────

    @staticmethod
    def _jsonable(v):
        if isinstance(v, np.ndarray):
            return v.tolist()
        if isinstance(v, (np.integer,)):
            return int(v)
        if isinstance(v, (np.floating,)):
            return float(v)
        if isinstance(v, dict):
            return {str(k): Isaac._jsonable(x) for k, x in v.items()}
        if isinstance(v, (list, tuple)):
            return [Isaac._jsonable(x) for x in v]
        return v

    def record_finding(self, kind, name, **payload):
        """Every outcome — a law, a family, a NO RULE, an overturn — becomes
        a structured, searchable record. Negative knowledge is knowledge:
        a recorded 'proven nothing' saves the next session from re-proving it."""
        entry = dict(id=len(self.findings) + 1, kind=kind, name=str(name))
        entry.update({k: self._jsonable(v) for k, v in payload.items()})
        self.findings.append(entry)
        node = f"finding:{entry['id']}"
        self.net.add_door("findings", node, tag="finding")
        self.net.set_meta(node, "entry", entry)
        if self.ledger_path:
            import json
            with open(self.ledger_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, default=str) + "\n")
        return entry["id"]

    def recall_findings(self, kind=None, contains=None, limit=50):
        """Search his own scientific memory."""
        import json
        out = []
        for e in reversed(self.findings):
            if kind and e.get("kind") != kind:
                continue
            if contains and contains.lower() not in \
                    json.dumps(e, default=str).lower():
                continue
            out.append(e)
            if len(out) >= limit:
                break
        return out

    def load_ledger(self, path):
        """Rehydrate a previous session's findings: laws become APPLICABLE
        again (apply_law works on them), records become searchable."""
        import json
        n_laws = 0
        for line in open(path, encoding="utf-8"):
            e = json.loads(line)
            e["id"] = len(self.findings) + 1
            self.findings.append(e)
            if e.get("kind") == "composite":
                if not any(c["name"] == e["name"] for c in self.composites):
                    self.composites.append(dict(
                        op=e["op"], features=[int(f) for f in e["features"]],
                        name=e["name"], provenance=e.get("provenance", "")))
            if e.get("kind") == "law" and e.get("model"):
                m = e["model"]
                node = f"law:{e['name']}"
                self.net.add_door("law", node, tag="law")
                self.net.set_meta(node, "model", dict(
                    terms=[tuple(t) for t in m["terms"]],
                    coefs=np.array(m["coefs"]),
                    intercept=float(m["intercept"]), d=int(m["d"]),
                    r2=float(m.get("r2", 0)),
                    specs=[tuple(s) for s in m["specs"]],
                    rivals=m.get("rivals", []),
                    d_raw=int(m.get("d_raw", m["d"])),
                    composites_used=m.get("composites_used", [])))
                self.net.set_meta(node, "equation", e.get("equation", ""))
                self._teach_fact(node, "explains", e["name"])
                n_laws += 1
        return dict(records=len(self.findings), laws_restored=n_laws)

    # ── discovery: the challenge loop ───────────────────────────

    def discover(self, X, y, name=None, verbose=False):
        """THE CHALLENGE LOOP. Given examples of something he cannot yet do
        (inputs X -> outcome y), find the rule. Half the examples are held
        out — the rule must WORK, not merely fit. Four honest verdicts:

          UNDERSTOOD  explicit equation, validated held-out (R2 >= 0.9)
          PARTIAL     a real equation that explains part; the rest is dark
          CAPTURED    no equation yet, but stored examples predict held-out
                      outcomes past the permuted null — caught, not said
          NO RULE     nothing beats chance: proven nothing, at this class

        An UNDERSTOOD/PARTIAL law becomes a node (law:<name>) with its
        equation in meta; apply_law() applies it from then on — the
        challenge has become computable. Facts are indexed for reasoning."""
        X = np.asarray(X, float); y = np.asarray(y, float)
        good = np.isfinite(X).all(1) & np.isfinite(y)     # red-team A8
        if not good.all():
            X, y = X[good], y[good]
        # learned combinations join the basis: every registered composite
        # that fits this data becomes a first-class column, so atoms
        # (sin/cos/exp/pow) can act ON combinations — the vocabulary Isaac
        # earned on past problems is offered to every new one
        d_raw = X.shape[1]
        comps = self._applicable_composites(d_raw)
        if comps:
            X = self._augment_with(X, comps)
        half = len(y) // 2
        enum = _Enumerator()
        enum.fit(X[:half], y[:half])
        p = enum.predict(X[half:])
        ss = float(np.sum((y[half:] - y[half:].mean()) ** 2))
        r2 = 1 - float(np.sum((y[half:] - p) ** 2)) / max(ss, 1e-12)
        # right-enough-to-use vs form-true: a surrogate can match the law on
        # the dense CENTER of the observed range yet diverge at its EDGES.
        # Score the outer quarter of the held-out set separately and LABEL
        # the law's scope — both grades are usable, neither is silently the
        # other.
        dist = np.linalg.norm(X[half:] - X[:half].mean(0), axis=1)
        edge = dist >= np.percentile(dist, 75)
        if edge.sum() >= 20:
            ss_e = float(np.sum((y[half:][edge] - y[half:][edge].mean()) ** 2))
            r2_edge = 1 - float(np.sum((y[half:][edge] - p[edge]) ** 2)) \
                / max(ss_e, 1e-12)
        else:
            r2_edge = r2
        scope = "form-true (edges hold)" if r2_edge >= 0.85 else \
            "range-valid (usable inside observed range)"
        cap_r2, cap_null = self._capture(X[:, :d_raw], y, half)
        # a real partial equation is knowledge whatever the headline verdict
        # says — it must never be discarded because capture scored higher
        # (the CAPTURED-erases-law bug, 2026-07-03 audit)
        has_law = bool(enum.terms) and r2 >= 0.2
        if enum.terms and r2 >= 0.9:
            verdict = "UNDERSTOOD"
        elif cap_r2 > max(cap_null + 0.1, 0.2) and cap_r2 > r2 + 0.1:
            verdict = "CAPTURED"
        elif has_law:
            verdict = "PARTIAL"
        else:
            verdict = "NO RULE"

        # ═══ THE ACCOUNTING (audit 2.8): articulated% + captured% + noise%
        # = 100. Articulated = what the kept equation explains (held-out).
        # Captured = what exemplars additionally predict ON THE RESIDUAL,
        # past a permuted null. Noise = the remainder that beat nothing in
        # this expressive class — proven noise AT THIS CLASS, not absolutely.
        art = max(0.0, min(r2, 1.0)) if has_law else 0.0
        if has_law:
            resid = y - np.concatenate([enum.predict(X[:half]), p])
            if resid[half:].std() > 1e-9 * max(y.std(), 1e-12):
                capres, capres_null = self._capture(X, resid, half)
            else:
                capres, capres_null = 0.0, 0.0
        else:
            resid, capres, capres_null = y - y.mean(), cap_r2, cap_null
        cap_frac = (max(0.0, min(capres, 1.0)) * (1.0 - art)
                    if capres > max(capres_null + 0.1, 0.1) else 0.0)
        accounting = dict(
            articulated=round(100 * art, 1),
            captured=round(100 * cap_frac, 1),
            noise=round(100 * (1.0 - art - cap_frac), 1),
            noise_meaning="proven at THIS expressive class only: neither the "
                          "equation library nor exemplar capture beat the "
                          "permuted null on this remainder")
        # the unexplained share is a FIRST-CLASS object with a dossier:
        # can't say what it is; can characterize how it behaves; track it
        dossier = None
        if (1.0 - art) > 0.05:
            rs = resid[half:]
            cr = np.zeros(X.shape[1])
            if rs.std() > 1e-12:
                Z = (X[half:] - X[half:].mean(0)) / (X[half:].std(0) + 1e-12)
                cr = np.abs((Z * ((rs - rs.mean()) / rs.std())[:, None]
                             ).mean(0))
            top = np.argsort(-cr)[:3]
            dossier = dict(
                unknown=f"x:{name or 'challenge'}",
                share_pct=round(100 * (1.0 - art), 1),
                captured_pct_of_it=round(
                    100 * cap_frac / max(1e-9, 1.0 - art), 1),
                responsive_channels=[[int(j), round(float(cr[j]), 3)]
                                     for j in top],
                rms=round(float(np.sqrt(np.mean(rs ** 2))), 4),
                edge_rms=round(float(np.sqrt(np.mean(rs[edge] ** 2)))
                               if edge.sum() else 0.0, 4))

        # DATA ADEQUACY (owner, 2026-07-03: "able to detect or define the
        # data that is too weak to interpret?"). When little or nothing was
        # interpretable, name the cause WITH evidence and what would fix
        # it — weak data is a diagnosis, not a shrug.
        adequacy = dict(verdict="interpretable", reasons=[])
        if verdict in ("NO RULE", "CAPTURED") or r2 < 0.5:
            reasons = []
            if len(y) < 100:
                reasons.append(
                    f"sample too small: n={len(y)} is below the measured "
                    f"recovery onset (~100 rows) — collect more")
            if dossier and max((c for _, c in
                                dossier["responsive_channels"]),
                               default=0.0) < 2.0 / np.sqrt(max(len(y), 4)):
                reasons.append(
                    "no measured channel responds to the unexplained part "
                    "— the driver may not be among these columns (a "
                    "missing-variable shadow)")
            if cap_r2 > max(cap_null + 0.1, 0.2) and r2 < 0.5:
                reasons.append(
                    "structure IS present (stored examples predict it "
                    f"at {cap_r2:.2f}) but no equation in the library says "
                    "it — an expressive-class limit, not weak data")
            if accounting["noise"] >= 90 and \
                    cap_r2 <= max(cap_null + 0.1, 0.2):
                reasons.append(
                    "nothing beats chance at this class: either noise, or "
                    "the drivers were not measured")
            if reasons or verdict == "NO RULE":
                adequacy = dict(
                    verdict=("too weak to interpret"
                             if verdict == "NO RULE" else
                             "partially interpretable"),
                    reasons=reasons or
                    ["weak fit without a single identified cause"])
        if adequacy["verdict"] == "interpretable" and len(y) < 100:
            # found something anyway — but small samples carry wrong-form
            # risk (battery: provisional below n~400, onset ~100), so the
            # caution attaches even to a success
            adequacy = dict(
                verdict="interpretable (provisional: small sample)",
                reasons=[f"sample too small for a confident form: "
                         f"n={len(y)} — the equation may be a look-alike; "
                         f"collect more or confirm() at the probes"])

        rivals = []
        if has_law:
            rivals = enum.rival_check(y[:half])
        eq_str = self._rename_composites(enum.equation(), d_raw, comps)
        if rivals and adequacy["verdict"] != "interpretable":
            adequacy["reasons"].append(
                f"observed range too narrow to pin the form: "
                f"{len(rivals)} rival form(s) still tied — extend sampling "
                f"toward the named probe(s)")
        if name and has_law:
            node = f"law:{name}"
            self.net.add_door("law", node, tag="law")
            self.net.set_meta(node, "model", dict(
                terms=list(enum.terms), coefs=enum.coefs,
                intercept=enum.intercept, d=X.shape[1], r2=r2,
                specs=list(enum.specs), rivals=rivals,
                ranges=[[float(X[:, k].min()), float(X[:, k].max())]
                        for k in range(X.shape[1])],
                r2_edge=r2_edge, d_raw=d_raw,
                composites_used=[dict(c) for c in comps]))
            self.net.set_meta(node, "equation", eq_str)
            self.net.set_meta(node, "accounting", accounting)
            if dossier:
                self.net.set_meta(node, "residual_dossier", dossier)
            self._teach_fact(node, "explains", name or "challenge")
        if verbose:
            print(f"    discover[{name}]: {verdict} [{scope}]  R2 {r2:.3f}  "
                  f"edge {r2_edge:.3f}  captured {cap_r2:.3f}  "
                  f"eq: {eq_str}")
            print(f"      accounting: articulated {accounting['articulated']}"
                  f"% + captured {accounting['captured']}% + noise "
                  f"{accounting['noise']}% = 100")
        riv_summary = [dict(rival=r["rival"], F=r["F"], probe=r["probe"])
                       for r in rivals]
        self.record_finding(
            "law" if has_law else "verdict",
            name or "challenge", verdict=verdict, equation=eq_str,
            r2=r2, r2_edge=r2_edge, scope=scope, captured_r2=cap_r2,
            n=len(y), d=X.shape[1], rivals=riv_summary,
            accounting=accounting, dossier=dossier,
            model=(dict(terms=list(enum.terms), coefs=enum.coefs,
                        intercept=enum.intercept, d=X.shape[1], r2=r2,
                        specs=list(enum.specs), d_raw=d_raw,
                        composites_used=[dict(c) for c in comps])
                   if has_law else None))
        capture = None
        if verdict == "CAPTURED" and name:
            capture = self.capture_net(name, X[:, :d_raw], y)
        return dict(verdict=verdict, equation=eq_str,
                    r2=r2, r2_edge=r2_edge, scope=scope, captured_r2=cap_r2,
                    rivals=riv_summary, accounting=accounting,
                    dossier=dossier, adequacy=adequacy, capture=capture)

    def apply_law(self, name, X):
        """Apply a discovered law: the challenge, now computable.
        (Distinct from solve(), the token-problem solver.)"""
        m = self.net.get_meta(f"law:{name}", "model")
        d_raw = (m or {}).get("d_raw", (m or {}).get("d"))
        if m is None or np.asarray(X).shape[1] != d_raw:
            return None
        X = self._augment_with(np.asarray(X, float),
                               m.get("composites_used", []))
        used = sorted({a for t in m["terms"] for a in t})
        cols = {a: _atom_col(X, m["specs"][a]) for a in used}
        D = np.column_stack(
            [np.prod([cols[a] for a in t], axis=0) for t in m["terms"]]
            + [np.ones(len(X))])
        return D @ np.concatenate([m["coefs"], [m["intercept"]]])

    # Extrapolation survival of form-true claims, MEASURED (2026-07-03,
    # experiments/confidence_curve.py — 100-world externally graded audit;
    # re-measure whenever the enumerator changes). Keys are hull-exceedance
    # distances in units of the observed span; values are observed hold
    # rates. This is a calibrated prior, not an opinion.
    DECAY_MEASURED = {0.0: 0.765, 0.1: 0.588, 0.3: 0.451,
                      0.6: 0.431, 1.0: 0.373}
    # (measured 2026-07-03 on 51 externally-graded laws; validated on 52
    # FRESH laws: ECE 0.070, Brier 0.249 vs flat-baseline 0.288)

    def law_confidence(self, name, X, decay=None):
        """GRADED BELIEF instead of a binary scope stamp (owner's design,
        2026-07-03: 'maybe just a boundary confidence? what about
        extrapolated confidence?'). Per query point:
          - inside the observed hull -> the law's boundary confidence
            (held-out edge R2, clamped to [0,1])
          - beyond the hull -> boundary confidence x the MEASURED survival
            curve of claims like this one, interpolated at the point's
            hull-exceedance distance (in units of the observed span).
        Returns an array of per-point confidences. Honest by construction:
        the decay is what actually happened to extrapolating laws in the
        externally-graded audit, not an assertion."""
        m = self.net.get_meta(f"law:{name}", "model")
        if m is None or "ranges" not in m:
            return None
        X = self._augment_with(np.asarray(X, float),
                               m.get("composites_used", []))
        lo = np.array([r[0] for r in m["ranges"]])
        hi = np.array([r[1] for r in m["ranges"]])
        span = np.maximum(hi - lo, 1e-12)
        exceed = np.maximum(np.maximum(lo - X, X - hi), 0.0) / span
        delta = exceed.max(axis=1)                    # hull distance / span
        curve = decay if decay is not None else {
            k: v for k, v in self.DECAY_MEASURED.items() if v is not None}
        boundary = float(np.clip(m.get("r2_edge", m.get("r2", 0.0)), 0, 1))
        if not curve:
            return np.where(delta <= 0, boundary, np.nan)
        ks = np.array(sorted(curve))
        vs = np.array([curve[k] for k in ks])
        surv = np.interp(delta, ks, vs, left=vs[0], right=vs[-1])
        conf = np.where(delta <= 0, boundary, boundary * surv)
        return conf

    def _fit_terms(self, specs, terms, X, y):
        """Least-squares refit of a term set; returns (coefs, intercept,
        predictions_fn ingredients). Shared by pruning and refinement."""
        used = sorted({a for t in terms for a in t})
        cols = {a: _atom_col(X, specs[a]) for a in used}
        D = np.column_stack([np.prod([cols[a] for a in t], axis=0)
                             for t in terms] + [np.ones(len(X))])
        beta, *_ = np.linalg.lstsq(D, y, rcond=None)
        pred = D @ beta
        sse = float(np.sum((y - pred) ** 2))
        return list(beta[:-1]), float(beta[-1]), sse

    def _prune_terms(self, m, X, y, f_thr=10.0):
        """OCCAM'S RAZOR as an operation (owner's law, 2026-07-03: 'simpler
        with the same accuracy or better is better'). Greedily drop any
        term whose removal survives an F-test tie on held-out data — a
        genuine tie goes to the simpler form. Returns (terms, coefs,
        intercept, n_dropped)."""
        half = len(y) // 2
        terms = list(m["terms"])
        specs = list(m["specs"])
        coefs, intercept, _ = self._fit_terms(specs, terms, X[:half],
                                              y[:half])

        def held_sse(ts):
            c, b, _ = self._fit_terms(specs, ts, X[:half], y[:half])
            used = sorted({a for t in ts for a in t})
            cols = {a: _atom_col(X[half:], specs[a]) for a in used}
            D = np.column_stack([np.prod([cols[a] for a in t], axis=0)
                                 for t in ts] + [np.ones(len(y) - half)])
            p = D @ np.concatenate([c, [b]])
            return float(np.sum((y[half:] - p) ** 2)), c, b

        sse_full, coefs, intercept = held_sse(terms)
        dropped = 0
        changed = True
        while changed and len(terms) > 1:
            changed = False
            for k in range(len(terms)):
                trial = terms[:k] + terms[k + 1:]
                sse_t, c_t, b_t = held_sse(trial)
                F = (max(sse_t - sse_full, 0.0)) \
                    / max(sse_full / max(len(y) - half, 1), 1e-30)
                if F < f_thr:                     # tie -> simpler wins
                    terms, coefs, intercept = trial, c_t, b_t
                    sse_full = sse_t
                    dropped += 1
                    changed = True
                    break
        return terms, coefs, intercept, dropped

    def refine(self, name, X, y, ask=None, budget=60, rounds=3,
               verbose=False):
        """THE CORRECTION LOOP (owner's design, 2026-07-03: 'it has an
        indicator it can use as a correction signal... recalculate and
        experiment with different information to refine'). The confidence
        curve stops being a dashboard and becomes a steering signal:

          1. find the law's WEAKEST region (lowest extrapolated confidence)
          2. EXPERIMENT exactly there (ask(X)->y — the oracle/instrument),
             spending a budget
          3. re-derive on everything now known
          4. PREFER what is better — or equally good and simpler (Occam
             as a preference, not a gate; same F-test that judges rivals)
          5. the displaced law is SUPERSEDED with the why; a candidate
             that is not preferred is RETAINED as an alternative —
             nothing is rejected into nothing

        Ends with an Occam prune either way. Returns a report dict."""
        node = f"law:{name}"
        m = self.net.get_meta(node, "model")
        if m is None:
            return None
        X = np.asarray(X, float); y = np.asarray(y, float)
        comps_m = m.get("composites_used", [])
        d_raw_m = int(m.get("d_raw", X.shape[1]))
        pool_X, pool_y = X.copy(), y.copy()      # pool stays RAW; the
        spent = 0                                 # instrument speaks raw
        report = dict(rounds=[], accepted=0, spent=0)

        def complexity(mm):
            return (len(mm["terms"]),
                    sum(len(t) for t in mm["terms"]))

        def held_sse_of(mm, Xh, yh):
            used = sorted({a for t in mm["terms"] for a in t})
            cols = {a: _atom_col(Xh, mm["specs"][a]) for a in used}
            D = np.column_stack([np.prod([cols[a] for a in t], axis=0)
                                 for t in mm["terms"]]
                                + [np.ones(len(Xh))])
            p = D @ np.concatenate([mm["coefs"], [mm["intercept"]]])
            return float(np.sum((yh - p) ** 2))

        for rd in range(rounds):
            if ask is None or spent >= budget:
                break
            m = self.net.get_meta(node, "model")
            lo = np.array([r[0] for r in m["ranges"]])[:d_raw_m]
            hi = np.array([r[1] for r in m["ranges"]])[:d_raw_m]
            span = np.maximum(hi - lo, 1e-12)
            # 1. weakest region: candidate probes fan out past the hull;
            #    the confidence signal picks where belief is thinnest
            cand = np.vstack([
                lo + _wave_rng.uniform(-1.0, 1.4, (300, len(lo))) * span])
            conf = self.law_confidence(name, cand)
            b = max(min(budget - spent, budget // rounds), 8)
            weakest = cand[np.argsort(conf)[:b]]
            # 2. experiment there (an instrument can fail — a probe outside
            # a law's physical support returns nothing; keep only finite
            # answers, red-team A8 discipline)
            y_new = np.asarray(ask(weakest), float)
            spent += b
            fin = np.isfinite(y_new) & np.isfinite(weakest).all(1)
            weakest, y_new = weakest[fin], y_new[fin]
            if not len(y_new):
                report["rounds"].append("all probes returned non-finite")
                continue
            pool_X = np.vstack([pool_X, weakest])
            pool_y = np.concatenate([pool_y, y_new])
            sh = _wave_rng.permutation(len(pool_y))
            pool_X, pool_y = pool_X[sh], pool_y[sh]
            # 3. re-derive on everything known (fits see the augmented
            # basis: learned combinations are columns here too)
            poolA = self._augment_with(pool_X, comps_m)
            enum = _Enumerator()
            half = len(pool_y) // 2
            enum.fit(poolA[:half], pool_y[:half])
            cand_m = dict(terms=list(enum.terms), coefs=enum.coefs,
                          intercept=enum.intercept, specs=list(enum.specs))
            if not cand_m["terms"]:
                report["rounds"].append("no candidate")
                continue
            # 4. the Occam gate: judged on the held half of the pool
            sse_old = held_sse_of(m, poolA[half:], pool_y[half:])
            sse_new = held_sse_of(cand_m, poolA[half:], pool_y[half:])
            n_h = len(pool_y) - half
            F = (sse_old - sse_new) / max(min(sse_old, sse_new) / n_h, 1e-30)
            better = F > 10.0 and sse_new < sse_old
            tie_simpler = abs(F) <= 10.0 and \
                complexity(cand_m) < complexity(m)
            # OCCAM IS A PREFERENCE, NOT A GATE (owner, 2026-07-03: "its
            # not only. its just preferred."). Accuracy decides; at ties
            # the simpler form is PREFERRED for use — and the
            # non-preferred candidate is RETAINED as an alternative, not
            # discarded. Nothing is rejected into nothing.
            if better or tie_simpler:
                old_eq = self.net.get_meta(node, "equation")
                why = (f"refined with {b} experiments in the weakest "
                       f"region (round {rd+1}): "
                       + (f"held-out SSE {sse_new:.4g} vs {sse_old:.4g} "
                          f"(F {F:.1f})" if better else
                          f"tie (F {F:.1f}) and simpler "
                          f"({complexity(cand_m)[0]} vs "
                          f"{complexity(m)[0]} terms)"))
                m.setdefault("superseded", []).append(dict(
                    equation=old_eq,
                    model=dict(terms=m["terms"], coefs=m["coefs"],
                               intercept=m["intercept"], specs=m["specs"]),
                    why=why))
                m.update(terms=cand_m["terms"], coefs=cand_m["coefs"],
                         intercept=cand_m["intercept"],
                         specs=cand_m["specs"],
                         ranges=[[float(poolA[:, k].min()),
                                  float(poolA[:, k].max())]
                                 for k in range(poolA.shape[1])])
                self.net.set_meta(node, "equation", self._rename_composites(
                    enum.equation(), d_raw_m, comps_m))
                self.net.set_meta(node, "model", m)
                report["accepted"] += 1
                report["rounds"].append(why)
                if verbose:
                    print(f"    refine[{name}] r{rd+1}: ACCEPTED — {why}")
            else:
                e = _Enumerator()
                e.terms, e.coefs, e.intercept, e.specs = \
                    (cand_m["terms"], cand_m["coefs"],
                     cand_m["intercept"], cand_m["specs"])
                m.setdefault("alternatives", []).append(dict(
                    equation=e.equation(), model=cand_m,
                    why=(f"round {rd+1}: not preferred — "
                         f"F {F:.1f} vs incumbent"
                         + ("" if abs(F) > 10.0 else
                            f", tied but not simpler "
                            f"({complexity(cand_m)[0]} vs "
                            f"{complexity(m)[0]} terms)"))))
                self.net.set_meta(node, "model", m)
                report["rounds"].append(
                    f"incumbent preferred (F {F:.1f}); candidate retained "
                    f"as alternative")

        # 5. Occam prune the final law on everything known
        m = self.net.get_meta(node, "model")
        poolA = self._augment_with(pool_X, comps_m)
        terms, coefs, intercept, dropped = self._prune_terms(
            m, poolA, pool_y)
        if dropped:
            old_eq = self.net.get_meta(node, "equation")
            m.setdefault("superseded", []).append(dict(
                equation=old_eq, model=dict(
                    terms=m["terms"], coefs=m["coefs"],
                    intercept=m["intercept"], specs=m["specs"]),
                why=f"Occam prune: {dropped} term(s) removed at F-tie — "
                    f"simpler with the same accuracy"))
            m.update(terms=terms, coefs=coefs, intercept=intercept)
            self.net.set_meta(node, "model", m)
            e = _Enumerator()
            e.terms, e.coefs, e.intercept, e.specs = \
                terms, coefs, intercept, m["specs"]
            self.net.set_meta(node, "equation", self._rename_composites(
                e.equation(), d_raw_m, comps_m))
        report["spent"] = spent
        report["pruned"] = dropped
        report["equation"] = self.net.get_meta(node, "equation")
        return report

    def validate_law(self, name, X, y):
        """Re-validate a (possibly inherited) law on NEW evidence before
        trusting it. load_ledger() restores laws as APPLICABLE; this is the
        check that keeps 'applicable' from silently meaning 'still true'.
        Returns HOLDS (R2 >= 0.9) / DEGRADED (>= 0.2) / FAILS, recorded in
        the ledger either way. (2026-07-03: apply_law was applied blind.)"""
        p = self.apply_law(name, X)
        if p is None:
            return None
        y = np.asarray(y, float)
        ss = float(np.sum((y - y.mean()) ** 2))
        r2 = 1 - float(np.sum((y - p) ** 2)) / max(ss, 1e-12)
        status = ("HOLDS" if r2 >= 0.9 else
                  "DEGRADED" if r2 >= 0.2 else "FAILS")
        self.record_finding("validation", name, r2=round(r2, 4),
                            status=status, n=len(y))
        return dict(status=status, r2=r2)

    def confirm(self, name, X, y):
        """Resolve a tied law with NEW evidence — ideally sampled at the
        probe the tie names. F-tests every live rival against the chosen
        form on the new data: decisively beaten rivals retire; a rival that
        decisively wins OVERTURNS the law, which is rewritten. 'Check both
        and keep whichever fits, until confirmed.'"""
        node = f"law:{name}"
        m = self.net.get_meta(node, "model")
        if m is None:
            return None
        X = self._augment_with(np.asarray(X, float),
                               m.get("composites_used", []))
        y = np.asarray(y, float)

        def sse_of(model):
            used = sorted({a for t in model["terms"] for a in t})
            cols = {a: _atom_col(X, model["specs"][a]) for a in used}
            D = np.column_stack([np.prod([cols[a] for a in t], axis=0)
                                 for t in model["terms"]]
                                + [np.ones(len(X))])
            p = D @ np.concatenate([model["coefs"], [model["intercept"]]])
            return float(np.sum((y - p) ** 2))

        chosen = dict(terms=m["terms"], coefs=m["coefs"],
                      intercept=m["intercept"], specs=m["specs"])
        s0, n = sse_of(chosen), len(y)
        kept, winner = [], None
        for r in m.get("rivals", []):
            s1 = sse_of(r["model"])
            better = min(s0, s1)
            F = (max(s0, s1) - better) / max(better / n, 1e-30)
            if F < 10.0:
                kept.append(r)                       # still genuinely tied
            elif s1 < s0 and (winner is None or s1 < winner[0]):
                winner = (s1, r)
        if winner is not None:
            r = winner[1]
            # SUPERSESSION, not overwrite (owner's law, 2026-07-03): "if
            # there is a and b, and b works better, use b" — and A is KEPT,
            # wearing its defeat. The overturned form stays on the record
            # with the WHY: what was believed, what beat it, by how much.
            # Knowing what was wrong — and why — is the wisdom half.
            old_eq = self.net.get_meta(node, "equation")
            m.setdefault("superseded", []).append(dict(
                equation=old_eq,
                model=dict(terms=m["terms"], coefs=m["coefs"],
                           intercept=m["intercept"], specs=m["specs"]),
                why=(f"overturned by rival '{r['rival']}' on new evidence "
                     f"(n={n}): rival SSE {winner[0]:.4g} vs {s0:.4g}")))
            m.update(terms=r["model"]["terms"], coefs=r["model"]["coefs"],
                     intercept=r["model"]["intercept"],
                     specs=r["model"]["specs"], rivals=[])
            self.net.set_meta(node, "equation", r["model"]["equation"])
            self.net.set_meta(node, "model", m)
            self.record_finding("confirmation", name,
                                status=f"OVERTURNED -> {r['rival']}",
                                equation=r["model"]["equation"],
                                superseded=old_eq)
            return dict(status=f"OVERTURNED -> {r['rival']}", rivals_left=[])
        m["rivals"] = kept
        self.net.set_meta(node, "model", m)
        # absolute-fit guard (2026-07-03): beating your rivals is not the
        # same as fitting the data — a law with no live rivals must still
        # actually hold on the new evidence to be CONFIRMED
        ss_tot = float(np.sum((y - y.mean()) ** 2))
        r2_abs = 1 - s0 / max(ss_tot, 1e-12)
        if r2_abs < 0.2:
            status = f"REFUTED (fit collapsed on new data: R2 {r2_abs:.2f})"
        else:
            status = "CONFIRMED" if not kept else f"STILL TIED ({len(kept)})"
        self.record_finding("confirmation", name, status=status,
                            r2_new=round(r2_abs, 4),
                            rivals_left=[r["rival"] for r in kept])
        return dict(status=status, r2_new=r2_abs,
                    rivals_left=[r["rival"] for r in kept])

    def _capture(self, X, y, half):
        """Nearest-exemplar prediction (presence, not average): do stored
        examples predict held-out outcomes past a permuted-outcome null?
        If yes, the relationship is CAUGHT even while unarticulated —
        tracked until discovery can articulate it. No net, no training."""
        mu, sd = X[:half].mean(0), X[:half].std(0) + 1e-12
        A, B = (X[:half] - mu) / sd, (X[half:] - mu) / sd
        d2 = ((B[:, None, :] - A[None, :, :]) ** 2).sum(-1)
        nn = np.argsort(d2, 1)[:, :5]
        yh = y[half:]
        ss = float(np.sum((yh - yh.mean()) ** 2))

        def r2_of(vals, nn_idx):
            pred = vals[nn_idx].mean(1)
            return 1 - float(np.sum((yh - pred) ** 2)) / max(ss, 1e-12)

        # per-feature 1-D neighbors too: a rule living in ONE feature must
        # not be drowned by 30 irrelevant distance dimensions (red-team A4)
        nns = [nn]
        for j in range(A.shape[1]):
            d1 = np.abs(B[:, j:j + 1] - A[None, :, j])
            nns.append(np.argsort(d1, 1)[:, :5])
        real, best_nn = max(((r2_of(y[:half], m), m) for m in nns),
                            key=lambda t: t[0])
        # the null must attack EXACTLY the claimed structure: the real score
        # won a max-over-candidate-neighbor-sets contest, so each permutation
        # replays the same contest (permuting only under the winner is
        # anti-conservative — found in the 2026-07-03 audit)
        null = max(max(r2_of(yp, m) for m in nns)
                   for yp in (_wave_rng.permutation(y[:half])
                              for _ in range(20)))
        return real, null

    # ── spatial perception: relations from motion (the bridge) ─────────
    # Migrated from spatial/ (2026-07-03) after harness validation
    # (spatial/test_isaac_bridge.py 4/4, test_null_battery.py clean).
    # Coordinates are scratch, relations are storage: what enters the net
    # is locked/bounded edges, parts, hinges, anchors, and a scale-free
    # ratio signature. Every verdict is null-gated (variance-ratio vs the
    # pair's own noise floor; increment-shuffle surrogate for bounded) —
    # no hand-tuned thresholds. Assumes temporally continuous frames.

    @staticmethod
    def _extreme_visits(ds, nf):
        """min(visits to own min, to own max), hysteresis-counted."""
        lo, hi = float(ds.min()), float(ds.max())
        rng_ = hi - lo
        if rng_ <= 0:
            return 0
        band = max(0.02 * rng_, 3 * nf)
        if band >= 0.2 * rng_:
            return 0
        away = 0.25 * rng_
        counts = []
        for target in (lo, hi):
            v, armed = 0, True
            for d in ds:
                if armed and abs(d - target) < band:
                    v += 1
                    armed = False
                elif not armed and abs(d - target) > away:
                    armed = True
            counts.append(v)
        return min(counts)

    def observe_spatial(self, frames, label="scene", machine_eps=1e-9):
        """THE BRIDGE: watch trajectories, store only what refuses to vary.
        Teaches facts (locked_to / bounded_with / contains / hinge_at /
        anchored_at) via teach() — indexed AND observed, so doors form —
        and a scale-free signature on a scene node. If nothing survives
        the nulls, NOTHING is taught (perception that can refuse).
        Returns the relation bundle."""
        F = np.asarray(frames, float)               # (T, n_points, dims)
        T, n, _ = F.shape
        rng = np.random.default_rng(1234)
        verdicts, scale = {}, 0.0
        series = {}
        for i in range(n):
            for j in range(i + 1, n):
                ds = np.linalg.norm(F[:, i] - F[:, j], axis=1)
                series[(i, j)] = ds
                scale = max(scale, float(ds.mean()))
        for pair, ds in series.items():
            std = float(ds.std())
            diffs = np.diff(ds)
            nf = float(np.sqrt(max(float(diffs.var()), 0.0) / 2.0))
            gate = max(nf * (1 + 4 / np.sqrt(T)), machine_eps * scale)
            if std <= gate:
                kind = "locked"
            else:
                real_v = self._extreme_visits(ds, nf)
                d0 = diffs.copy()
                surr = []
                for _ in range(20):
                    rng.shuffle(d0)
                    walk = np.concatenate([[ds[0]], ds[0] + np.cumsum(d0)])
                    surr.append(self._extreme_visits(walk, nf))
                rng_ = float(ds.max() - ds.min())
                kind = ("bounded" if real_v >= 2 and real_v > max(surr)
                        and rng_ > 10 * max(nf, machine_eps * scale)
                        else "free")
            verdicts[pair] = dict(kind=kind, mean=float(ds.mean()), std=std,
                                  noise=nf)
        locked = {p: v["mean"] for p, v in verdicts.items()
                  if v["kind"] == "locked"}
        bounded = sorted(p for p, v in verdicts.items()
                         if v["kind"] == "bounded")
        # parts = maximal pairwise-locked cliques, grown from EDGES
        cliques = []
        for (a, b) in locked:
            c = {a, b}
            for cand in range(n):
                if cand not in c and all(
                        (min(cand, m), max(cand, m)) in locked for m in c):
                    c.add(cand)
            if not any(c <= q for q in cliques):
                cliques = [q for q in cliques if not q <= c] + [c]
        hinges = sorted({min(a & b) for ai, a in enumerate(cliques)
                         for b in cliques[ai + 1:] if len(a & b) == 1})
        # anchors: coordinate variation explained by noise alone
        anchors = []
        for i in range(n):
            still = True
            for d in range(F.shape[2]):
                cs = F[:, i, d]
                nf = float(np.sqrt(max(float(np.diff(cs).var()), 0.0) / 2.0))
                if float(cs.std()) > max(nf * (1 + 4 / np.sqrt(T)),
                                         machine_eps * max(scale, 1e-12)):
                    still = False
                    break
            if still:
                anchors.append(i)
        lens = sorted(locked.values())
        sig = [round(x / lens[-1], 3) for x in lens] if lens else []
        # ---- emit: relations cross, coordinates never do
        for (i, j) in sorted(locked):
            self.teach(f"{label}.p{i}", "locked_to", f"{label}.p{j}")
        for (i, j) in bounded:
            self.teach(f"{label}.p{i}", "bounded_with", f"{label}.p{j}")
        for k, part in enumerate(sorted(map(sorted, cliques))):
            for i in part:
                self.teach(f"{label}.part{k}", "contains", f"{label}.p{i}")
        for h in hinges:
            self.teach(label, "hinge_at", f"{label}.p{h}")
        for a in anchors:
            self.teach(label, "anchored_at", f"{label}.p{a}")
        if sig:
            self.net.add_door("scene", f"scene:{label}", tag="scene")
            self.net.set_meta(f"scene:{label}", "spatial_signature", sig)
            self.net.set_meta(f"scene:{label}", "structure", dict(
                n_parts=len(cliques),
                part_sizes=sorted(len(p) for p in cliques),
                n_hinges=len(hinges)))
        return dict(locked=sorted(locked), bounded=bounded,
                    parts=[sorted(c) for c in cliques], hinges=hinges,
                    anchors=anchors, signature=sig)

    def compare_scenes(self, label_a, label_b, tol=0.02):
        """Are two perceived scenes the same STRUCTURE? Judged entirely from
        stored relations: the scale-free signature (sorted locked-length
        ratios) plus part-size multiset and hinge count. Pose, scale and
        position cannot matter — they were never stored."""
        sa = self.net.get_meta(f"scene:{label_a}", "spatial_signature")
        sb = self.net.get_meta(f"scene:{label_b}", "spatial_signature")
        ta = self.net.get_meta(f"scene:{label_a}", "structure")
        tb = self.net.get_meta(f"scene:{label_b}", "structure")
        if None in (sa, sb, ta, tb):
            return dict(verdict="UNKNOWN", reason="scene(s) not perceived")
        if len(sa) != len(sb):
            return dict(verdict="DIFFERENT", reason="different bar counts")
        gap = max(abs(x - y) for x, y in zip(sa, sb))
        same = (gap < tol and ta["part_sizes"] == tb["part_sizes"]
                and ta["n_hinges"] == tb["n_hinges"])
        return dict(verdict="SAME" if same else "DIFFERENT",
                    signature_gap=round(gap, 4))

    # ── the capture net: a stopgap that exists to be destroyed ─────────
    # Audit 2.8, built 2026-07-03 at the owner's prompt. THE NO-NETS LAW
    # HOLDS: the net is never the deliverable — it is quarantined inside
    # the residual dossier as the tracked unknown x:<name>, it counts ONLY
    # if it beats its own permuted-output null, and its purpose is to be
    # ATTACKED by graduate() (distillation) until caught becomes said.

    @staticmethod
    def _net_fit(X, y, hidden=16, steps=400, lr=0.05, seed=7):
        """Tiny numpy MLP (1 tanh layer), full-batch momentum GD."""
        r = np.random.default_rng(seed)
        mu, sd = X.mean(0), X.std(0) + 1e-9
        ym, ys = y.mean(), y.std() + 1e-9
        Xs, yn = (X - mu) / sd, (y - ym) / ys
        d = X.shape[1]
        W1 = r.normal(0, 1 / np.sqrt(d), (d, hidden))
        b1 = np.zeros(hidden)
        W2 = r.normal(0, 1 / np.sqrt(hidden), hidden)
        b2 = 0.0
        vW1 = np.zeros_like(W1); vb1 = np.zeros_like(b1)
        vW2 = np.zeros_like(W2); vb2 = 0.0
        n = len(yn)
        for _ in range(steps):
            H = np.tanh(Xs @ W1 + b1)
            p = H @ W2 + b2
            g = 2 * (p - yn) / n
            gW2 = H.T @ g; gb2 = g.sum()
            gH = np.outer(g, W2) * (1 - H ** 2)
            gW1 = Xs.T @ gH; gb1 = gH.sum(0)
            vW1 = 0.9 * vW1 - lr * gW1; W1 += vW1
            vb1 = 0.9 * vb1 - lr * gb1; b1 += vb1
            vW2 = 0.9 * vW2 - lr * gW2; W2 += vW2
            vb2 = 0.9 * vb2 - lr * gb2; b2 += vb2
        return dict(W1=W1.tolist(), b1=b1.tolist(), W2=W2.tolist(),
                    b2=float(b2), mu=mu.tolist(), sd=sd.tolist(),
                    ym=float(ym), ys=float(ys))

    @staticmethod
    def _net_predict(net, X):
        X = np.asarray(X, float)
        Xs = (X - np.array(net["mu"])) / np.array(net["sd"])
        H = np.tanh(Xs @ np.array(net["W1"]) + np.array(net["b1"]))
        return (H @ np.array(net["W2"]) + net["b2"]) * net["ys"] + net["ym"]

    def capture_net(self, name, X, y, n_perm=8):
        """Train the stopgap on (X, y) with train/held halves. COUNTS ONLY
        if held-out R2 beats the max over permuted-output re-trainings
        (the null replays the whole training contest). On success the net
        is stored on the unknown's dossier node x:<name>; on failure
        NOTHING is stored — a big-enough net memorizing noise is exactly
        the lie the null exists to kill (audit 2.8)."""
        X = np.asarray(X, float); y = np.asarray(y, float)
        half = len(y) // 2

        def held_r2(yy):
            net = self._net_fit(X[:half], yy[:half])
            p = self._net_predict(net, X[half:])
            ss = float(np.sum((y[half:] - y[half:].mean()) ** 2))
            return 1 - float(np.sum((yy[half:] - p) ** 2)) / max(
                float(np.sum((yy[half:] - yy[half:].mean()) ** 2)), 1e-12), net

        real, net = held_r2(y)
        null = max(held_r2(_wave_rng.permutation(y))[0]
                   for _ in range(n_perm))
        if real <= max(null + 0.1, 0.2):
            return dict(status="FAILED NULL", r2=real, null=null)
        node = f"x:{name}"
        self.net.add_door("unknown", node, tag="unknown")
        self.net.set_meta(node, "capture_net", net)
        resid = y[half:] - self._net_predict(net, X[half:])
        self.net.set_meta(node, "capture_resid_sd", float(resid.std()))
        self.net.set_meta(node, "capture_r2", round(real, 4))
        self.net.set_meta(node, "ranges",
                          [[float(X[:, k].min()), float(X[:, k].max())]
                           for k in range(X.shape[1])])
        self.record_finding("capture", name, r2=round(real, 4),
                            null=round(null, 4))
        return dict(status="CAPTURED (net)", r2=real, null=null, node=node)

    def graduate(self, name, X=None, y=None, n_queries=3000, verbose=False):
        """THE DISTILLATION ATTACK (audit 2.8's closing loop): query the
        captured net as a free oracle across the unknown's observed
        ranges, run discover() on its answers, and accept the resulting
        equation ONLY if it also explains the net's held behavior — then
        the law supersedes the capture and x:<name> is retired (kept,
        marked graduated — supersession, never deletion). If no equation
        survives, the capture stands, honestly still unarticulated."""
        node = f"x:{name}"
        net = self.net.get_meta(node, "capture_net")
        ranges = self.net.get_meta(node, "ranges")
        if net is None or ranges is None:
            return None
        lo = np.array([r[0] for r in ranges])
        hi = np.array([r[1] for r in ranges])
        Xq = _wave_rng.uniform(0, 1, (n_queries, len(lo))) * (hi - lo) + lo
        yq = self._net_predict(net, Xq)
        # the net's held-out residual IS its uncertainty: answer queries
        # with that noise attached, so the net's own wiggle-artifacts die
        # at F-ties instead of graduating as tiny fake terms
        resid_sd = self.net.get_meta(node, "capture_resid_sd", 0.0)
        if resid_sd:
            yq = yq + _wave_rng.normal(0, resid_sd, len(yq))
        res = self.discover(Xq, yq, name=f"{name}_distilled")
        ok = res["verdict"] == "UNDERSTOOD" and res["r2"] >= 0.95
        if ok:
            # the razor runs at graduation too: a distilled law should be
            # the SIMPLE form, not a term-cloud imitating the net — and
            # when the ORIGINAL data is available, prune against REALITY:
            # terms that only serve the net's private warp F-tie on real
            # data and die; terms that serve the truth survive
            dnode = f"law:{name}_distilled"
            dm = self.net.get_meta(dnode, "model")
            if X is not None and y is not None:
                Xp, yp_ = np.asarray(X, float), np.asarray(y, float)
            else:
                Xp, yp_ = Xq, yq
            terms, coefs, intercept, dropped = self._prune_terms(dm, Xp, yp_)
            if dropped:
                dm.update(terms=terms, coefs=coefs, intercept=intercept)
                self.net.set_meta(dnode, "model", dm)
                e2 = _Enumerator()
                e2.terms, e2.coefs, e2.intercept, e2.specs = \
                    terms, coefs, intercept, dm["specs"]
                self.net.set_meta(dnode, "equation", e2.equation())
                res = dict(res, equation=e2.equation())
            self.net.set_meta(node, "status",
                              f"graduated -> law:{name}_distilled")
            self.record_finding("graduation", name,
                                equation=res["equation"], r2=res["r2"])
            if verbose:
                print(f"    graduate[{name}]: CAUGHT became SAID — "
                      f"{res['equation'][:60]}")
            return dict(status="GRADUATED", equation=res["equation"],
                        r2=res["r2"])
        self.net.set_meta(node, "status", "still captured (distillation "
                                          "found no equation)")
        return dict(status="STILL CAPTURED", r2=res["r2"],
                    verdict=res["verdict"])

    # ── interrogation: make the CAPTURED explicit (owner, 2026-07-04:
    # "there is structure and meaning, there is something being found but
    # we don't know what... enumerate that and make it explicit. define
    # the heuristic connections... even if they aren't specifically
    # correct, they can at least point in the direction — 'this is a
    # pattern' as a deliverable.")

    def interrogate(self, name, n=2500, grid=24):
        """Enumerate what a captured net is responding to, as explicit,
        gated heuristic claims stored on x:<name> and returned in English:
          drivers      — share of the response each input carries
                         (permutation importance on net queries)
          interactions — joint vs additive, per driver pair (ANOVA share
                         on a 2-D query grid)
          composites   — does the dependence flow ONLY THROUGH xi*xj,
                         xi+xj or xi−xj? (level-set invariance, judged
                         against random-direction level sets — the claim
                         must beat its matched null)
          shape        — along the main axis: monotone / peaked /
                         periodic, with a frequency estimate
        None of this claims the LAW — it points at it."""
        node = f"x:{name}"
        net = self.net.get_meta(node, "capture_net")
        ranges = self.net.get_meta(node, "ranges")
        if net is None or ranges is None:
            return None
        lo = np.array([r[0] for r in ranges])
        hi = np.array([r[1] for r in ranges])
        d = len(lo)
        X = _wave_rng.uniform(0, 1, (n, d)) * (hi - lo) + lo
        f0 = self._net_predict(net, X)
        var0 = max(float(f0.var()), 1e-12)

        # drivers: permutation importance
        drivers = []
        for j in range(d):
            Xp = X.copy()
            Xp[:, j] = _wave_rng.permutation(Xp[:, j])
            damage = float(np.mean((self._net_predict(net, Xp) - f0) ** 2))
            drivers.append(damage)
        tot = sum(drivers) + 1e-12
        drivers = [round(v / tot, 3) for v in drivers]
        main = [j for j in np.argsort(drivers)[::-1]
                if drivers[j] >= 0.05]

        # interactions on the top driver pairs (2-D ANOVA share)
        mid = (lo + hi) / 2
        interactions = {}
        for a_i in range(len(main)):
            for b_i in range(a_i + 1, len(main)):
                i, j = main[a_i], main[b_i]
                gi = np.linspace(lo[i], hi[i], grid)
                gj = np.linspace(lo[j], hi[j], grid)
                Q = np.tile(mid, (grid * grid, 1))
                Q[:, i] = np.repeat(gi, grid)
                Q[:, j] = np.tile(gj, grid)
                F = self._net_predict(net, Q).reshape(grid, grid)
                row = F.mean(1, keepdims=True)
                col = F.mean(0, keepdims=True)
                resid = F - row - col + F.mean()
                share = float(resid.var() / max(F.var(), 1e-12))
                interactions[(int(i), int(j))] = round(share, 3)

        # composites: level-set invariance vs random-direction null
        composites = []
        for (i, j), share in interactions.items():
            if share < 0.1:
                continue
            # each candidate composite = (z-function, level-set solver:
            # given z0 and a sweep of xi values, the xj that keeps z=z0)
            cands = {
                "product": (lambda a, b: a * b,
                            lambda z0, ai: np.where(np.abs(ai) > 1e-6,
                                                    z0 / ai, np.nan)),
                "sum": (lambda a, b: a + b, lambda z0, ai: z0 - ai),
                "difference": (lambda a, b: a - b, lambda z0, ai: ai - z0)}

            def invariance(zfun, solve_b):
                keep = []
                for _ in range(40):
                    base = _wave_rng.uniform(0, 1, d) * (hi - lo) + lo
                    z0 = zfun(base[i], base[j])
                    ai = np.linspace(lo[i], hi[i], 24)
                    with np.errstate(divide="ignore", invalid="ignore"):
                        bj = solve_b(z0, ai)
                    okm = np.isfinite(bj) & (bj >= lo[j]) & (bj <= hi[j])
                    if okm.sum() < 8:
                        continue
                    Q = np.tile(base, (int(okm.sum()), 1))
                    Q[:, i] = ai[okm]
                    Q[:, j] = bj[okm]
                    keep.append(float(self._net_predict(net, Q).var()))
                if not keep:
                    return 0.0
                return 1.0 - float(np.mean(keep)) / var0

            scores = {k: invariance(z, s) for k, (z, s) in cands.items()}
            # matched null: the SAME level-set walk along random oblique
            # directions w0*xi + w1*xj — the claim must beat directions
            # nobody proposed
            nulls = []
            for _ in range(6):
                w = _wave_rng.normal(0, 1, 2)
                if abs(w[1]) < 0.1:
                    w[1] = 0.1 * np.sign(w[1] or 1)
                nulls.append(invariance(
                    lambda a, b, w=w: w[0] * a + w[1] * b,
                    lambda z0, ai, w=w: (z0 - w[0] * ai) / w[1]))
            best = max(scores, key=scores.get)
            if scores[best] > 0.8 and scores[best] > max(nulls):
                # shape along the composite axis
                z = cands[best][0](X[:, i], X[:, j])
                order = np.argsort(z)
                zs, fs = z[order], f0[order]
                bins = np.array_split(np.arange(len(zs)), 60)
                prof = np.array([fs[b].mean() for b in bins])
                zc = np.array([zs[b].mean() for b in bins])
                dsign = np.sign(np.diff(prof))
                turns = int(np.sum(np.diff(dsign[dsign != 0]) != 0))
                s_ = np.sign(prof - prof.mean())
                crossings = int(np.sum(s_[:-1] * s_[1:] < 0))
                span = float(zc[-1] - zc[0]) or 1.0
                freq = round(np.pi * crossings / span, 2)
                shape = ("periodic" if turns >= 3 else
                         "single-peaked" if turns in (1, 2) else "monotone")
                composites.append(dict(
                    features=[int(i), int(j)], through=best,
                    invariance=round(scores[best], 3),
                    null_best=round(max(nulls), 3),
                    shape=shape, turns=turns,
                    freq_estimate=(freq if shape == "periodic" else None)))

        # English: the deliverable, even when the law is out of reach
        names_ = [f"x{k}" for k in range(d)]
        lines = []
        if main:
            lines.append("the pattern lives in "
                         + ", ".join(f"{names_[j]} ({drivers[j]*100:.0f}%)"
                                     for j in main)
                         + (" — the rest of the columns are bystanders"
                            if len(main) < d else ""))
        for (i, j), share in sorted(interactions.items(),
                                    key=lambda kv: -kv[1]):
            if share >= 0.1:
                lines.append(f"{names_[i]} and {names_[j]} act JOINTLY "
                             f"(interaction carries {share*100:.0f}% of "
                             f"their effect) — not a sum of separate "
                             f"influences")
        for c in composites:
            i, j = c["features"]
            lines.append(
                f"the dependence flows through the {c['through']} "
                f"{names_[i]}{'*' if c['through']=='product' else ('+' if c['through']=='sum' else '-')}{names_[j]} "
                f"ONLY (invariance {c['invariance']:.2f}, beats its null "
                f"{c['null_best']:.2f}); along that axis the response is "
                f"{c['shape']}"
                + (f", roughly {c['freq_estimate']} rad/unit"
                   if c["freq_estimate"] else ""))
        if not lines:
            lines.append("no gated heuristic survived — the capture is "
                         "real but structureless to these probes")
        for c in composites:
            self.register_composite(
                c["through"], c["features"],
                provenance=f"interrogation of x:{name}")
        heur = dict(drivers=drivers, interactions={
            f"{i},{j}": v for (i, j), v in interactions.items()},
            composites=composites, english=lines)
        self.net.set_meta(node, "heuristics", heur)
        self.record_finding("heuristics", name, english=lines)
        return heur

    # ── combinations are THINGS (owner, 2026-07-04: "x0,x1 in this
    # relationship... shouldn't be two separate things. it should have a
    # node... enumerate and then use that... it's combinatorial. it should
    # be able to memorize and reuse those combinations. a topological venn
    # diagram... a dimensionless structure.") A certified combination is
    # minted as a node comb:<name>, distinct from its parts and from every
    # other combination (ab ≠ a,b ≠ abc ≠ abd), persisted through the
    # ledger, and OFFERED TO EVERY FUTURE discover() as a first-class
    # feature — the atom library grows with experience.

    _COMP_OPS = {"product": (lambda a, b: a * b, "*"),
                 "sum": (lambda a, b: a + b, "+"),
                 "difference": (lambda a, b: a - b, "-")}

    def register_composite(self, op, features, provenance=""):
        """Mint a combination as a first-class node. Idempotent."""
        features = [int(f) for f in features]
        sym = self._COMP_OPS[op][1]
        cname = "(" + sym.join(f"x{f}" for f in features) + ")"
        if any(c["name"] == cname for c in self.composites):
            return cname
        comp = dict(op=op, features=features, name=cname,
                    provenance=provenance)
        self.composites.append(comp)
        node = f"comb:{cname}"
        self.net.add_door("combination", node, tag="comb")
        for f in features:
            self.net.add_door(node, f"feat:x{f}", tag="comb")
        self.net.set_meta(node, "composite", comp)
        self.record_finding("composite", cname, op=op, features=features,
                            provenance=provenance)
        return cname

    def _augment_with(self, X, comps):
        """Append the given combinations as columns. Order = comps order."""
        X = np.asarray(X, float)
        cols = []
        for c in comps:
            i, j = c["features"][0], c["features"][1]
            cols.append(self._COMP_OPS[c["op"]][0](X[:, i], X[:, j]))
        return np.column_stack([X] + cols) if cols else X

    def _applicable_composites(self, d):
        return [c for c in self.composites
                if max(c["features"]) < d and len(c["features"]) == 2]

    @staticmethod
    def _rename_composites(eq, d_raw, comps):
        """Equation legibility: augmented columns print by their names."""
        for k in range(len(comps) - 1, -1, -1):
            eq = re.sub(rf"\bx{d_raw + k}\b", comps[k]["name"], eq)
        return eq

    def graduate_composite(self, name, X, y, verbose=False):
        """The closing move: if interrogation found the dependence flows
        through a composite, RE-DISCOVER IN THAT COORDINATE — a pattern
        that was out of class in raw coordinates may be plainly sayable
        in the right ones. Returns the law (with the composite named) or
        an honest miss."""
        node = f"x:{name}"
        heur = self.net.get_meta(node, "heuristics")
        if not heur or not heur["composites"]:
            return None
        X = np.asarray(X, float); y = np.asarray(y, float)
        best = max(heur["composites"], key=lambda c: c["invariance"])
        i, j = best["features"]
        op = {"product": (lambda a, b: a * b, "*"),
              "sum": (lambda a, b: a + b, "+"),
              "difference": (lambda a, b: a - b, "-")}[best["through"]]
        z = op[0](X[:, i], X[:, j]).reshape(-1, 1)
        res = self.discover(z, y, name=f"{name}_via_composite")
        if res["verdict"] == "UNDERSTOOD":
            eq = res["equation"].replace("x0", f"(x{i}{op[1]}x{j})")
            self.net.set_meta(f"law:{name}_via_composite", "equation", eq)
            self.net.set_meta(node, "status",
                              f"graduated via composite -> {eq[:60]}")
            self.record_finding("graduation", name, equation=eq,
                                r2=res["r2"], via=best["through"])
            if verbose:
                print(f"    graduate_composite[{name}]: {eq[:70]}")
            return dict(status="GRADUATED (via composite)", equation=eq,
                        r2=res["r2"])
        return dict(status="STILL CAPTURED", verdict=res["verdict"],
                    r2=res["r2"])

    def wave_consolidate(self, min_count=5, n_perm=40, verbose=False):
        """IDLE MODE, temporal: crystallize the activation STREAM.

        Where consolidate() compares door profiles (order-blind),
        this compares each instant of the whole matrix to the next:
          groups   — doors that light together (simultaneity, a real thing)
          edges    — one group dims as another lights (the wave moving)
          circles  — waves that return to their start
          level 2  — the same three over circle-activity: patterns of patterns
        Discoveries enter the net as first-class nodes (tag 'wave', order in
        tag 'wave_next') so they can compose upward like anything else.
        Every admission beats a jitter null. Shuffle the log in time and
        the groups survive but every edge and circle dies — that is exactly
        the slice of structure the static crystallizer cannot see."""
        log = self.activation_log
        empty = {"groups": [], "edges": [], "circles": [], "level2": {}}
        if len(log) < 30:
            return empty
        counts = defaultdict(int)
        for fs in log:
            for n in fs:
                counts[n] += 1
        doors = sorted(str(n) for n, c in counts.items() if c >= min_count)
        if len(doors) < 2:
            return empty
        idx = {n: j for j, n in enumerate(doors)}
        S = np.zeros((len(log), len(doors)))
        for t, fs in enumerate(log):
            for n in fs:
                j = idx.get(str(n))
                if j is not None:
                    S[t, j] = 1.0
        groups_ix = _wave_groups(S, n_perm)
        if not groups_ix:
            return empty
        G = np.column_stack([(S[:, list(g)].mean(1) >= 0.5).astype(float)
                             for g in groups_ix])

        # conditional rescue: a door exiled from its group by heavy
        # interference re-joins when membership is re-tested WHERE a candidate
        # blocker is absent — and the blocker is a 'blocks' fact, discovered
        # in the same move. (Occlusion weakens correlation; conditioning on
        # the blocker's absence restores it. Decompose to find comparability.)
        grouped_ix = {j for g in groups_ix for j in g}
        pending_blocks = []
        for j in range(len(doors)):
            if j in grouped_ix or doors[j].startswith("miss:"):
                continue
            x = S[:, j]
            if x.std() < 1e-9:
                continue
            best = None
            for gi in range(len(groups_ix)):
                uncond = float(np.corrcoef(x, G[:, gi])[0, 1])
                for bi in range(len(groups_ix)):
                    if bi == gi:
                        continue
                    off = G[:, bi] == 0
                    if off.sum() < 150:
                        continue
                    xs, gs = x[off], G[off, gi]
                    if xs.std() < 1e-9 or gs.std() < 1e-9:
                        continue
                    c = float(np.corrcoef(xs, gs)[0, 1])
                    null = [abs(float(np.corrcoef(
                        _wave_rng.permutation(xs), gs)[0, 1]))
                        for _ in range(30)]
                    if c > max(2 * np.percentile(null, 95), 0.35) \
                            and c - uncond > 0.1:
                        if best is None or c > best[0]:
                            best = (c, gi, bi)
            if best is not None:
                _, gi, bi = best
                groups_ix[gi] = tuple(sorted(groups_ix[gi] + (j,)))
                pending_blocks.append((bi, doors[j]))
        if pending_blocks:                       # membership changed: re-derive
            G = np.column_stack([(S[:, list(g)].mean(1) >= 0.5).astype(float)
                                 for g in groups_ix])

        groups = [tuple(doors[j] for j in g) for g in groups_ix]
        edges_ix = _wave_edges(G, n_perm)
        circles_ix = _wave_circles(edges_ix, len(groups))

        # discoveries become nodes — same naming shape as type crystals.
        # 'wave' doors: member -> group (identity); 'part' doors: group ->
        # member (so recognize_doors can fire the group from partial members
        # — permanence through the existing organ). Dwell meta = his clock.
        gname = []
        for gi, g in enumerate(groups):
            name = f"wave:{'_'.join(g[:2])}[{len(g)}]"
            gname.append(name)
            col = G[:, gi]
            runs, r = [], 0
            for v in col:
                r = r + 1 if v else (runs.append(r) or 0 if r else 0)
            if r:
                runs.append(r)
            self.net.set_meta(name, "dwell", float(np.mean(runs)) if runs else 3.0)
            for m in g:
                self.net.add_door(m, name, tag="wave")
                self.net.add_door(name, m, tag="part")
                self._teach_fact(m, "part_of", name)
        edges = [(gname[a], gname[b]) for a, b in edges_ix]
        for a, b in edges:
            self.net.add_door(a, b, tag="wave_next")
        circles = []
        for c in circles_ix:
            cname = "circle:" + ">".join(groups[i][0] for i in c)
            circles.append(cname)
            for i in c:
                self.net.add_door(gname[i], cname, tag="wave")
                self.net.add_door(cname, gname[i], tag="part")
                self._teach_fact(gname[i], "phase_of", cname)
        for bi, dname in pending_blocks:         # rescue's discovered blockers
            self._teach_fact(gname[bi], "blocks", dname)

        # one level up: each circle's activity is a door; same machinery
        level2 = {}
        if len(circles_ix) >= 2:
            A = np.column_stack([G[:, list(c)].max(1) for c in circles_ix])
            K = np.ones(3) / 3.0                     # smooth handoff flicker
            A = np.column_stack([(np.convolve(A[:, j], K, mode="same") >= 0.5)
                                 .astype(float) for j in range(A.shape[1])])
            keys = [tuple(int(v) for v in r) for r in A]
            uniq = sorted(set(keys))
            if len(uniq) >= 2:
                S2 = np.zeros((len(keys), len(uniq)))
                for t, k in enumerate(keys):
                    S2[t, uniq.index(k)] = 1.0
                e2 = _wave_edges(S2, n_perm)
                level2 = {"states": uniq, "edges": e2,
                          "circles": _wave_circles(e2, len(uniq))}

        # statuses are doors: explain each one WITHIN its entity's own
        # timeframe (the ticks where the tracker had that phase) using the
        # SAME co-activation machinery — explanations EMERGE, then enter the
        # reasoning layer as 'blocks' facts.
        explanations = []
        for sd in [d for d in doors if d.startswith("miss:")]:
            target = sd[5:]
            for gname_t in self.net.get_doors(target, tag="wave"):
                ent_members = set(self.net.get_predecessors(gname_t, tag="wave"))
                for circle, plog in self.phase_log.items():
                    rows = [ti for ti, ph in plog if ph == gname_t and ti < len(log)]
                    if len(rows) < 60:
                        continue
                    cols = [d for d in doors
                            if d not in ent_members
                            and (not d.startswith("miss:") or d == sd)]
                    sub = S[np.array(rows)][:, [idx[d] for d in cols]]
                    for eg in _wave_groups(sub, n_perm):
                        names_e = [cols[j] for j in eg]
                        if sd in names_e:
                            co = [n for n in names_e if n != sd]
                            for c in co:
                                self._teach_fact(c, "blocks", target)
                            for W in set(self.net.get_doors(co[0], tag="wave")) if co else set():
                                if set(self.net.get_predecessors(W, tag="wave")) <= set(co) | {sd}:
                                    self._teach_fact(W, "blocks", target)
                            explanations.append((sd, sorted(co)))

        self.waves = {"groups": groups, "edges": edges, "circles": circles,
                      "circle_orders": [[gname[i] for i in c] for c in circles_ix],
                      "level2": level2, "explanations": explanations}
        if groups:
            self.record_finding(
                "waves", "consolidation", n_groups=len(groups),
                circles=circles, explanations=explanations,
                level2_circles=len(level2.get("circles", [])))
        if verbose:
            print(f"    waves: {len(groups)} groups, {len(edges)} handoffs, "
                  f"{len(circles)} circles, "
                  f"{len(level2.get('circles', []))} level-2 circles, "
                  f"{len(explanations)} explained statuses")
        return self.waves

    def _encode(self, context):
        """Encode context tokens into the input vector.
        Full frame gets highest weight. Partial trailing frames get lower.
        Phase 6: when direct frames miss, try type-member substitution."""
        if not self._compiled:
            return None
        c = self._compiled
        x = np.zeros(len(c["frames"]), dtype=np.float32)

        # Direct frame matching
        frame = tuple(context)
        if frame in c["fidx"]:
            x[c["fidx"][frame]] = 16.0
        for width in range(2, min(len(context) + 1, 8)):
            partial = tuple(context[-width:])
            if partial in c["fidx"] and partial != frame:
                x[c["fidx"][partial]] = float(width)

        # Phase 6: type-level attention
        # If no direct frames matched, try substituting tokens with
        # their type members. Activate ALL matches — let the matmul
        # resolve which type member is most relevant. Weight lower
        # than direct (8.0 vs 16.0) so direct always wins.
        if x.sum() == 0 and self.types:
            for i, token in enumerate(context):
                type_doors = self.net.get_doors(token, tag="type")
                for tname in type_doors:
                    tdata = self.types.get(tname)
                    if not tdata:
                        continue
                    for member in sorted(tdata["members"]):
                        if member == token:
                            continue
                        # Try full frame with this substitution
                        trial = list(context)
                        trial[i] = member
                        trial_frame = tuple(trial)
                        if trial_frame in c["fidx"]:
                            x[c["fidx"][trial_frame]] += 8.0
                        # Try partial frames with substitution
                        for w in range(2, min(len(trial) + 1, 8)):
                            partial = tuple(trial[-w:])
                            if partial in c["fidx"] and partial != trial_frame:
                                x[c["fidx"][partial]] += float(w) * 0.5

        return x if x.sum() > 0 else None

    # ── inference (matrix) ──────────────────────────────────────
    # The THINK loop: recall → process → evaluate → repeat until stable.
    # Memory sends forward. Evaluation sends back. Loop until settled.

    def _route(self, context, mode="lookup", target=None):
        """Stage 3 (ROUTE): single matmul pass. Returns (answer, confidence)."""
        x = self._encode(context)
        if x is None:
            if mode == "check":
                return False, 0.0
            return None, 0.0
        y = self._compiled["W_norm"] @ x
        if mode == "check":
            if target not in self._compiled["didx"]:
                return False, 0.0
            score = float(y[self._compiled["didx"][target]])
            return score >= CONFIDENCE_THRESHOLD, score
        else:
            idx = y.argsort()[-1]
            answer = self._compiled["deltas"][idx]
            conf = float(y[idx])
            if conf < CONFIDENCE_THRESHOLD:
                return None, conf
            return answer, conf

    def _recall(self, context):
        """Stage 2 (STORE/RECALL): What do I know about these tokens?
        Pull types, related tokens, known facts, door profiles.
        This is memory sending information forward to processing."""
        knowledge = {}
        for token in context:
            types = list(self.net.get_doors(token, tag="type"))
            successors = self.net.get_doors(token, tag="seq")
            predecessors = self.net.get_predecessors(token, tag="seq")
            # Tokens with rich profiles are well-known.
            # Tokens with empty profiles are novel/unknown.
            type_members = set()
            for t in types:
                for n in self.net.all_nodes():
                    if t in self.net.get_doors(n, tag="type"):
                        type_members.add(n)
                type_members.discard(token)
            knowledge[token] = {
                "types": types,
                "successors": successors,
                "predecessors": predecessors,
                "type_members": type_members,
                "known": len(successors) > 0 or len(predecessors) > 0,
            }
        return knowledge

    def _evaluate(self, answer, conf, context, knowledge, mode):
        """Stage 4 (EVALUATE): Is this answer good? What should we do next?
        Returns a verdict dict — stable, or what to try next.
        This is evaluation sending feedback back to memory/processing.

        Critical distinction:
          - conf > 0 but < threshold: system has SOME info, just weak → don't substitute
          - conf == 0 and no frames match: genuine unknown → try substitution
          - answer found but wrong target: definite no, not unknown"""
        verdict = {"stable": False, "answer": answer, "conf": conf}

        # Confident answer → stable
        if conf >= CONFIDENCE_THRESHOLD:
            verdict["stable"] = True
            return verdict

        # Check: did the encoding produce ANY activation?
        # If yes, the system has info — just not for this target.
        # That's a real 'no', not an 'I don't know'.
        has_some_info = False
        if self._compiled:
            x = self._encode(context)
            if x is not None:
                y = self._compiled["W_norm"] @ x
                if y.max() >= CONFIDENCE_THRESHOLD:
                    has_some_info = True

        # Which tokens are unknown?
        unknown_tokens = [t for t in context
                          if not knowledge.get(t, {}).get("known", False)]
        known_tokens = [t for t in context
                        if knowledge.get(t, {}).get("known", False)]

        verdict["unknown_tokens"] = unknown_tokens
        verdict["known_tokens"] = known_tokens

        # If we have unknown tokens, suggest dropping them
        if unknown_tokens and len(known_tokens) >= 2:
            verdict["try_known_only"] = known_tokens

        # Only try type substitution when the system has NO info at all.
        # If it has info but the target doesn't match, that's a real 'no'.
        elif not unknown_tokens and not has_some_info:
            verdict["try_type_substitution"] = True

        return verdict

    def _think(self, context, mode="lookup", target=None, max_cycles=5):
        """Stages 2/3/4 loop. Recall → Process → Evaluate → repeat.

        Memory sends knowledge forward to processing.
        Processing sends results forward to evaluation.
        Evaluation sends feedback back to memory/processing.
        Loop until the answer stabilizes or we've exhausted what we know.

        Exit conditions (governor):
          1. Confidence >= threshold → stable
          2. Evaluation says stable (exhausted all strategies)
          3. Max cycles reached
        """
        self._ensure_compiled()
        if not self._compiled:
            return (None, 0.0) if mode == "lookup" else (False, 0.0)

        # wave sensing: thinking about a context IS simultaneous activation
        if self.wave_logging and context:
            self.tick(set(context))

        # ── Stage 2: RECALL — what do I know about this? ────────
        knowledge = self._recall(context)

        best_answer = None
        best_conf = 0.0
        tried = set()  # track what we've already attempted

        for cycle in range(max_cycles):
            # ── Stage 3: PROCESS — compute against what I know ──
            context_key = tuple(context)
            if context_key not in tried:
                tried.add(context_key)
                answer, conf = self._route(context, mode, target)

                if conf > best_conf:
                    best_answer, best_conf = answer, conf

                # ── Stage 4: EVALUATE — is this good enough? ────
                verdict = self._evaluate(answer, conf, context, knowledge, mode)

                if verdict["stable"]:
                    return answer, conf

            # ── Evaluation feedback → back to memory/processing ─
            # The verdict tells us what to try next

            # Strategy A: drop unknown tokens, keep what we know
            known_only = verdict.get("try_known_only")
            if known_only and tuple(known_only) not in tried:
                context = known_only
                # Recall again with the simplified context
                knowledge = self._recall(context)
                continue

            # Strategy B: type substitution — replace unknown tokens
            # with type members from related known tokens
            if verdict.get("try_type_substitution"):
                found = False
                for i, token in enumerate(context):
                    members = knowledge.get(token, {}).get("type_members", set())
                    for member in sorted(members):
                        trial = list(context)
                        trial[i] = member
                        trial_key = tuple(trial)
                        if trial_key not in tried:
                            tried.add(trial_key)
                            answer, conf = self._route(trial, mode, target)
                            if conf > best_conf:
                                best_answer, best_conf = answer, conf
                            if conf >= CONFIDENCE_THRESHOLD:
                                return answer, conf
                            found = True
                if found:
                    continue

            # Strategy C: try each known token paired with the tail
            # (verb-level: "smash" + "result")
            if len(context) > 2:
                tail = context[-1]
                for token in context[:-1]:
                    pair_key = (token, tail)
                    if pair_key not in tried:
                        tried.add(pair_key)
                        answer, conf = self._route(list(pair_key), mode, target)
                        if conf > best_conf:
                            best_answer, best_conf = answer, conf
                        if conf >= CONFIDENCE_THRESHOLD:
                            return answer, conf

            # Nothing more to try — return best we found
            break

        return best_answer, best_conf

    def lookup(self, context, top_k=5):
        """Argmax over the output vector. 'What comes next?'
        Routes through the think loop — recall, process, evaluate."""
        return self._think(context, mode="lookup")

    def check(self, context, target):
        """Read a SPECIFIC cell in y. 'Is THIS claim true?'
        Routes through the think loop — recall, process, evaluate."""
        return self._think(context, mode="check", target=target)

    # ── walking (net) ───────────────────────────────────────────

    def predict_next(self, context, tag="seq"):
        """Convergence voting from context words. For language, not math."""
        if not context:
            return None
        votes = defaultdict(int)
        voters = defaultdict(list)
        for word in context:
            for tgt in self.net.get_doors(word, tag=tag):
                if (word, tgt) not in self.lockouts:
                    votes[tgt] += 1
                    voters[tgt].append(word)
        if not votes:
            return None
        max_votes = max(votes.values())
        candidates = [c for c, v in votes.items() if v == max_votes]

        def recency(c):
            positions = [context.index(w) for w in voters[c] if w in context]
            return max(positions) if positions else -1
        winner = max(candidates, key=recency)
        return {"prediction": winner, "votes": votes[winner],
                "total_voters": len(context),
                "all_candidates": dict(votes)}

    def walk_chain(self, start, tag="seq", max_steps=20):
        """Walk forward from start, following doors."""
        chain = [start]
        current = start
        visited = {start}
        for _ in range(max_steps):
            nexts = self.net.get_doors(current, tag=tag) - visited
            nexts = {n for n in nexts if (current, n) not in self.lockouts}
            if not nexts:
                break
            best = max(nexts, key=lambda n: (
                self.net.get_meta(n, "initiator_strength") or 0, n))
            chain.append(best)
            visited.add(best)
            current = best
        return chain

    def transduce(self, start, stream, into="state", halt=None,
                  max_steps=None, verbose=False):
        """Universal state walk over an input stream — the missing primitive.

        Thread a state through a sequence of input symbols. At each step the
        NEXT state is chosen by HIS matrix: lookup([state, symbol]) -> state'.
        The transition function delta(state, symbol)=state' lives entirely in
        learned doors (a real frame->delta), so no task logic sits in Python.

        This is the finite-state-transducer / Turing-head shape: the loop here
        is the universal tape-reader (general, the same for every machine); the
        PROGRAM is whatever transitions were taught. Counting, parity, motion,
        and the game loop all reuse this — they differ only in their doors.

        The state is held in a working-memory register (`into`), so it lives in
        HIM across steps — read from scratch and written back each step. The
        harness loop holds nothing but the next symbol.

        Returns (final_state, trace). final_state is None on an honest shrug
        (no transition learned for some [state, symbol]); trace is the register's
        full step-history (scratch.history(into)).
        """
        self.scratch.clear(into)                       # fresh episode
        self.scratch.write(into, start)                # state lives in HIM
        steps = 0
        for symbol in stream:
            state = self.scratch.read(into)            # he reads his own state
            nxt, conf = self.lookup([state, symbol])   # his matmul decides
            if nxt is None or conf < CONFIDENCE_THRESHOLD:
                if verbose:
                    print(f"    shrug at step {steps}: no door for "
                          f"[{state}, {symbol}]")
                return None, self.scratch.history(into)  # honest: rule unlearned
            self.scratch.write(into, nxt)              # he writes it back into himself
            steps += 1
            if verbose:
                print(f"    {symbol:>4} -> {nxt}  (conf {conf:.1f})")
            if halt is not None and nxt == halt:
                break
            if max_steps is not None and steps >= max_steps:
                break
        return self.scratch.read(into), self.scratch.history(into)

    def _apply_op(self, op, target):
        """The tiny ALU: execute one named op against a working register.
        Fixed instruction set (like a CPU's decoder); the PROGRAM — which op to
        run when — is in his net, not here."""
        if op == "incr":
            self.scratch.incr(target)
        elif op == "hold":
            pass
        elif op == "reset":
            self.scratch.write(target, 0)
        elif op == "mark":
            self.scratch.latch(target + "_seen")
        else:
            return False                               # unknown op -> shrug
        return True

    def react(self, stream, target="acc", verbose=False):
        """Run an input stream against his ACTION doors, updating working memory
        in real time. For each symbol his matrix says what to DO
        (lookup([symbol]) -> an op token); the ALU applies it to `target`.

        The program (which op fires for which symbol) is HIS — learned doors.
        The register is HIS. Only 'apply a named op' is engine plumbing. This is
        counting-without-a-state-ladder: 'on'->incr, 'off'->hold lets him count
        to ANY N with two doors, because the magnitude lives in RAM, not in the
        graph as N separate nodes.
        """
        self.scratch.clear(target)                     # fresh episode
        self.scratch.write(target, 0)
        for symbol in stream:
            op, conf = self.lookup([symbol])           # his matmul: what to do
            if op is None or conf < CONFIDENCE_THRESHOLD:
                if verbose:
                    print(f"    {symbol:>4}: (no instruction — skip)")
                continue
            self._apply_op(op, target)
            if verbose:
                print(f"    {symbol:>4} -> {op:<6} {target}={self.scratch.read(target)}")
        return self.scratch.read(target), self.scratch.history(target)

    def generate(self, concept, tag="seq"):
        """Generate a sequence containing the concept.
        Trace backward to find an initiator, then forward to completion."""
        backward = []
        current = concept
        visited = {concept}
        for _ in range(10):
            preds = self.net.get_predecessors(current, tag=tag)
            preds = {p for p in preds if p not in visited
                     and (p, current) not in self.lockouts}
            if not preds:
                break
            starts = {p for p in preds if self.net.get_meta(p, "start")}
            if starts:
                best = max(starts, key=lambda p: (
                    self.net.get_meta(p, "initiator_strength") or 0))
                backward.append(best)
                break
            best = max(preds, key=lambda p: len(self.net.get_doors(p, tag=tag)))
            backward.append(best)
            visited.add(best)
            current = best
        backward.reverse()
        chain = backward + [concept]
        current = concept
        for _ in range(10):
            nexts = self.net.get_doors(current, tag=tag) - visited
            nexts = {n for n in nexts if (current, n) not in self.lockouts}
            if not nexts:
                break
            best = sorted(nexts)[0]
            chain.append(best)
            visited.add(best)
            current = best
            if best in (".", "!", "?", "="):
                break
        return chain

    def check_connection(self, src, tgt):
        """Is src→tgt valid? Walk the full net to check. Returns (valid, manifest)."""
        manifest = {"direct_seq": False, "direct_neg": False,
                    "lockout": False, "types_checked": [],
                    "type_support": 0, "type_contradict": 0}
        tags = self.net.get_door_tags(src, tgt)
        if "seq" in tags:
            manifest["direct_seq"] = True
        if "neg" in tags:
            manifest["direct_neg"] = True
        if (src, tgt) in self.lockouts:
            manifest["lockout"] = True
            return False, manifest
        src_types = self.net.get_doors(src, tag="type")
        for t in src_types:
            members = {n for n in self.net.all_nodes()
                       if t in self.net.get_doors(n, tag="type")}
            members.discard(src)
            support = any(self.net.has_door(m, tgt) for m in members)
            manifest["types_checked"].append({"type": t, "support": support})
            if support:
                manifest["type_support"] += 1
            else:
                manifest["type_contradict"] += 1
        valid = manifest["direct_seq"] or manifest["type_support"] > 0
        if manifest["lockout"]:
            valid = False
        return valid, manifest

    def compare_nodes(self, a, b, tag=None):
        """Structural comparison of two nodes."""
        return {
            "outgoing": compare(set(self.net.get_doors(a, tag=tag)),
                                set(self.net.get_doors(b, tag=tag))),
            "incoming": compare(self.net.get_predecessors(a, tag=tag),
                                self.net.get_predecessors(b, tag=tag)),
        }

    def infer(self, src, tgt, tag="seq"):
        """Can src connect to tgt? Walk types to find out."""
        src_types = self.net.get_doors(src, tag="type")
        for t in src_types:
            members = {n for n in self.net.all_nodes()
                       if t in self.net.get_doors(n, tag="type")}
            for m in members:
                if m != src and self.net.has_door(m, tgt):
                    self.net.add_door(src, tgt, tag=tag)
                    return {"inferred": True, "via": m, "type": t}
        return {"inferred": False}

    # ── crystal: transplant a net/features into box-concepts IN THE NET ──

    def fit_lens(self, name, X, y=None, lift=0, select=None, seed=0,
                 rotate=True):
        """Register an ALIGNER as net infrastructure: optional random lift
        (spread the data so classes pull apart) + basis-first alignment +
        discriminative dim-select. Lives in the net as a 'lens:<name>' node.

        The default alignment is now the NULL-GATED BASIS (the learned aligner
        this slot was reserved for): standardize, then rotate only along
        correlations that beat the sampling null (~3/sqrt(n)) — the basis
        itself must beat chance, otherwise near-identity eigenvectors are
        noise-driven arbitrary rotations. rotate=False restores plain
        strip-DC."""
        g = np.random.default_rng(seed); R = b = None; H = np.asarray(X, float)
        if lift:
            R = g.standard_normal((H.shape[1], lift)) / np.sqrt(H.shape[1])
            b = g.standard_normal(lift) * 0.1
            H = np.maximum(H @ R + b, 0.0)
        mu = sd = rot = None
        dc = H.mean(0)
        if rotate and len(H) >= 30:
            mu, sd = H.mean(0), H.std(0) + 1e-12
            Z = (H - mu) / sd
            C = np.nan_to_num(np.corrcoef(Z, rowvar=False))
            gate = np.abs(C) >= 3.0 / np.sqrt(len(Z))
            np.fill_diagonal(gate, True)
            w, V = np.linalg.eigh(np.where(gate, C, 0.0))
            rot = V[:, np.argsort(-w, kind="stable")]
            Hc = Z @ rot
        else:
            Hc = H - dc
        dims = (_fisher(Hc, y, select)
                if (select and y is not None and select < Hc.shape[1]) else None)
        node = f"lens:{name}"
        self.net.add_door("lens", node, tag="lens")
        self.net.set_meta(node, "transform",
                          dict(R=R, b=b, dc=dc, mu=mu, sd=sd, rot=rot, dims=dims))
        return name

    def apply_lens(self, name, X):
        """Run an input through a registered lens. None = identity."""
        if name is None:
            return np.asarray(X, float)
        t = self.net.get_meta(f"lens:{name}", "transform") or {}
        H = np.asarray(X, float)
        if t.get("R") is not None:
            H = np.maximum(H @ t["R"] + t["b"], 0.0)
        if t.get("rot") is not None:
            H = ((H - t["mu"]) / t["sd"]) @ t["rot"]
        elif t.get("dc") is not None:
            H = H - t["dc"]
        if t.get("dims") is not None:
            H = H[:, t["dims"]]
        return H

    def crystallize_features(self, X, y, lens=None, margin=1.5, bins=12):
        """Transplant: one concept per class as a NODE in the net, tagged
        'crystal'. The concept's doors are now OBSERVED DISTRIBUTIONS
        (quantile-binned per-dim log-densities) — observe + matmul, not a
        fitted box. Boxes were a ceiling: they cap on diagonal data and flip
        verdicts under re-encoding (rebuild A head-to-head). The legacy box
        meta is still written so recognize_matrix and old scripts keep
        running; classification no longer uses it."""
        H = self.apply_lens(lens, X)
        d = H.shape[1]
        qs = np.linspace(0, 100, bins + 1)[1:-1]
        edges = np.stack([np.percentile(H[:, j], qs) for j in range(d)])
        Hq, qlo, qhi = _quantize(H)
        for c in np.unique(y):
            obs = H[y == c]
            ld = np.empty((d, bins))
            for j in range(d):
                cnt = np.bincount(np.searchsorted(edges[j], obs[:, j]),
                                  minlength=bins).astype(float)
                ld[j] = np.log((cnt + 1.0) / (cnt.sum() + bins))
            node = f"concept:{c}"
            self.net.add_door("crystal", node, tag="crystal")
            self.net.set_meta(node, "doors", ld)          # observed densities
            self.net.set_meta(node, "label", c)
            obs_q = Hq[y == c]                            # legacy box, kept
            self.net.set_meta(node, "box", dict(
                lo=np.percentile(obs_q, 1, axis=0) - margin,
                hi=np.percentile(obs_q, 95, axis=0) + margin,
                med=np.median(obs_q, axis=0)))
        self.net.set_meta("crystal", "calib",
                          dict(qlo=qlo, qhi=qhi, lens=lens, edges=edges))
        return sorted(self.net.get_doors("crystal", tag="crystal"))

    def classify_features(self, X):
        """Classify by summed log-likelihood over each concept's observed
        density doors — graded membership, one matmul-shaped decision.
        Lens + doors both live in the net."""
        calib = self.net.get_meta("crystal", "calib")
        H = self.apply_lens(calib["lens"], np.atleast_2d(np.asarray(X, float)))
        edges = calib["edges"]
        concepts = [(self.net.get_meta(n, "label"), self.net.get_meta(n, "doors"))
                    for n in sorted(self.net.get_doors("crystal", tag="crystal"))]
        n, d = H.shape
        scores = np.zeros((n, len(concepts)))
        for j in range(d):
            idx = np.searchsorted(edges[j], H[:, j])
            for k, (_, ld) in enumerate(concepts):
                scores[:, k] += ld[j][idx]
        labels = np.array([lab for lab, _ in concepts], dtype=object)
        return labels[np.argmax(scores, axis=1)]

    # ── recognition by PARTIAL DOOR OVERLAP (recursive) ──

    def recognize_doors(self, active, tag="part", threshold=0.5, max_loops=12):
        """Recognize concepts by how many of their defining doors are present —
        partial, not all-or-nothing. A concept is a node with out-doors (tagged
        `tag`) to its parts; its score is the fraction of those doors present in
        `active`, weighted by each part's confidence (his compare 'similarity',
        carried). A concept that clears `threshold` joins `active` with its score,
        which lets HIGHER concepts (whose doors point to it) fire in turn. Loop
        until nothing new fires — on a finite net that always halts. So '10 of a
        concept's 12 doors present' -> 0.83 -> it fires, and its 0.83 flows up.

        active: an iterable of present nodes, or {node: confidence}.
        Returns {concept: score} for every concept that fired, all levels."""
        active = dict(active) if isinstance(active, dict) else {n: 1.0 for n in active}
        fired = {}
        for _ in range(max_loops):
            changed = False
            for node in self.net.all_nodes():
                doors = self.net.get_doors(node, tag)
                if not doors:
                    continue
                score = sum(active.get(d, 0.0) for d in doors) / len(doors)
                if score >= threshold and score > active.get(node, 0.0):
                    active[node] = fired[node] = score
                    changed = True
            if not changed:                       # stabilized: finite net is exhausted
                break
        return fired

    # ── recognition by the PADDED CONCEPT-MATRIX (box-friendly + padding) ──

    def recognize_matrix(self, X, rule="count", mask=None):
        """The working matrix: every box-concept is a ROW (its [lo,hi,med] across
        F dims, padded to F); a per-concept 0/1 MASK marks its committed slots
        (its real list vs padding). Score by PARTIAL OVERLAP over committed dims —
        ported from range_classifier/v3 fastscore, fed by crystallize_features.
          rule='count'   : # committed dims in range (membership), median-dist tiebreak
                           — all-ones mask reproduces classify_features (the box reader)
          rule='deepest' : fires if ALL committed satisfied; deepest fired wins;
                           else most-satisfied partial ('10 of 12'). Length-aware.
        Returns predicted labels (B,)."""
        calib = self.net.get_meta("crystal", "calib")
        H = self.apply_lens(calib["lens"], np.atleast_2d(np.asarray(X, float)))
        Xq, _, _ = _quantize(H, calib["qlo"], calib["qhi"])
        nodes = sorted(self.net.get_doors("crystal", tag="crystal"))
        LO = np.array([self.net.get_meta(n, "box")["lo"] for n in nodes])
        HI = np.array([self.net.get_meta(n, "box")["hi"] for n in nodes])
        MED = np.array([self.net.get_meta(n, "box")["med"] for n in nodes])
        labels = np.array([self.net.get_meta(n, "label") for n in nodes])
        N, F = LO.shape
        if mask is None:
            mask = np.ones((N, F))
        Xq = np.asarray(Xq, float); B = Xq.shape[0]
        BIG = 16.0 * F + 1.0
        if rule == "count":
            cnt = np.empty((B, N)); dist = np.empty((B, N))
            for c in range(N):
                inr = (Xq >= LO[c]) & (Xq <= HI[c]); w = inr * mask[c]
                cnt[:, c] = w.sum(1); dist[:, c] = (np.abs(Xq - MED[c]) * w).sum(1)
            key = cnt * BIG - dist
        elif rule == "deepest":                          # bundle-match + significant-digit
            depth = mask.sum(1); W1 = BIG; W2 = (F + 1.0) * W1
            fires = np.empty((B, N)); satisf = np.empty((B, N)); dist = np.empty((B, N))
            for c in range(N):
                inr = (Xq >= LO[c]) & (Xq <= HI[c]); comm = mask[c].astype(bool)
                m = int(comm.sum())
                s = inr[:, comm].sum(1) if m else np.zeros(B)
                satisf[:, c] = s; fires[:, c] = (s == m) if m else 1.0
                dist[:, c] = (np.abs(Xq - MED[c]) * (inr * mask[c])).sum(1)
            fb = fires.astype(bool)
            key = fb * W2 + np.where(fb, depth[None], satisf) * W1 - dist
        elif rule == "avgdiff":                          # arity-normalized (length-fair)
            depth = mask.sum(1); BIGA = 1e9; BIGB = 1e3
            avgdiff = np.empty((B, N)); avgmed = np.empty((B, N))
            for c in range(N):
                comm = mask[c].astype(bool); m = max(int(comm.sum()), 1)
                gap = np.maximum.reduce([LO[c] - Xq, Xq - HI[c], np.zeros_like(Xq)])
                avgdiff[:, c] = gap[:, comm].sum(1) / m
                avgmed[:, c] = (np.abs(Xq - MED[c])[:, comm]).sum(1) / m
            key = -avgdiff * BIGA + depth[None] * BIGB - avgmed
        else:
            raise ValueError(f"unknown rule {rule!r}")
        return labels[key.argmax(1)]

    # ── sense routing: internal node routers (conditional / binding) ──

    def crystallize_senses(self, node, min_shared=2):
        """Split a node's flat doors into SENSE-SECTIONS, stored ON the node.
        Each occurrence of the node carries the context it appeared in; cluster
        occurrences by shared context (the crystallizer, turned inward on one
        node); each cluster is a sense with its own in-doors and out-doors.
        This is what gives the node internal structure instead of a flat pile."""
        occ = []  # (context_set, pred, succ) per occurrence
        for seq in self.observed_sequences:
            for k, t in enumerate(seq):
                if t == node:
                    occ.append((set(seq) - {node},
                                seq[k - 1] if k > 0 else None,
                                seq[k + 1] if k + 1 < len(seq) else None))
        n = len(occ)
        parent = list(range(n))
        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]; x = parent[x]
            return x
        for a in range(n):              # link occurrences sharing >= min_shared context words
            for b in range(a + 1, n):
                if len(occ[a][0] & occ[b][0]) >= min_shared:
                    parent[find(a)] = find(b)
        comps = defaultdict(lambda: {"in": set(), "out": set(), "context": set()})
        for i, (ctx, p, s) in enumerate(occ):
            r = find(i)
            if p: comps[r]["in"].add(p)
            if s: comps[r]["out"].add(s)
            comps[r]["context"] |= ctx
        senses = list(comps.values())
        self.net.set_meta(node, "senses", senses)
        return senses

    def route(self, node, incoming):
        """Route through the node by which sense the incoming context matches.
        incoming = a token or a set of context tokens. Returns that sense's
        out-doors; falls back to the flat door-set if no sense matches."""
        senses = self.net.get_meta(node, "senses") or []
        inc = {incoming} if isinstance(incoming, str) else set(incoming)
        best, best_ov = None, 0
        for sense in senses:
            ov = len(inc & (sense["in"] | sense["context"]))
            if ov > best_ov:
                best_ov, best = ov, sense
        return best["out"] if best else set(self.net.get_doors(node, tag="seq"))

    # ── logic ───────────────────────────────────────────────────

    def logic_eval(self, expression, verbose=False):
        """Evaluate a logic expression via chained matmul lookups.
        Decompose-when-shrug: compound → single-gate lookups."""
        tokens = expression.lower().split()
        result, trace = self._logic_reduce(tokens, verbose)
        return result, trace

    def _logic_reduce(self, tokens, verbose=False):
        trace = []
        while len(tokens) >= 2 and tokens[0] == "(" and tokens[-1] == ")":
            tokens = tokens[1:-1]
        if len(tokens) == 1:
            return tokens[0], trace
        if tokens[0] == "not":
            inner, inner_trace = self._logic_reduce(tokens[1:], verbose)
            trace.extend(inner_trace)
            context = ["not", inner, "="]
            answer, conf = self.lookup(context)
            trace.append({"op": f"not {inner}", "answer": answer, "conf": conf})
            if verbose:
                print(f"    not {inner} → {answer} (conf={conf:.1f})")
            return answer, trace
        main_op_idx = self._find_main_op(tokens)
        if main_op_idx is not None:
            left_tokens = tokens[:main_op_idx]
            op = tokens[main_op_idx]
            right_tokens = tokens[main_op_idx + 1:]
            left_val, lt = self._logic_reduce(left_tokens, verbose)
            trace.extend(lt)
            right_val, rt = self._logic_reduce(right_tokens, verbose)
            trace.extend(rt)
            context = [left_val, op, right_val, "="]
            answer, conf = self.lookup(context)
            trace.append({"op": f"{left_val} {op} {right_val}",
                          "answer": answer, "conf": conf})
            if verbose:
                print(f"    {left_val} {op} {right_val} → {answer} (conf={conf:.1f})")
            return answer, trace
        return " ".join(tokens), trace

    def _find_main_op(self, tokens):
        ops_by_precedence = [{"implies"}, {"or", "nor"}, {"xor"},
                             {"and", "nand"}, {"equals"}]
        depth = 0
        for prec_level in ops_by_precedence:
            for i, t in enumerate(tokens):
                if t == "(":
                    depth += 1
                elif t == ")":
                    depth -= 1
                elif depth == 0 and t in prec_level and i > 0:
                    return i
        return None

    # ── reasoning ───────────────────────────────────────────────

    def reason_chain(self, subject, relation, verbose=False):
        """Follow a relation chain via matmul hops. Each hop is one matmul."""
        chain = [subject]
        current = subject
        visited = {subject}
        for step in range(20):
            answer, conf = self.lookup([current, relation])
            if answer is None or conf < CONFIDENCE_THRESHOLD or answer in visited:
                break
            chain.append(answer)
            visited.add(answer)
            current = answer
            if verbose:
                print(f"    hop {step}: {chain[-2]} {relation} → {answer}"
                      f" (conf={conf:.1f})")
        return chain

    def is_a_check(self, subject, target, verbose=False):
        """Is subject a target? Walk the is_a chain."""
        chain = self.reason_chain(subject, "is_a", verbose=verbose)
        return target in chain, chain

    def can_check(self, subject, ability, verbose=False):
        """Can subject do ability? Negative first, then direct, then inherited.
        Each check is one matmul reading a specific cell."""
        # Step 1: negative blocks everything
        neg_match, neg_conf = self.check([subject, "cannot"], ability)
        if neg_match:
            if verbose:
                print(f"    {subject} cannot {ability} → BLOCKED (conf={neg_conf:.1f})")
            return False, [subject]
        # Step 2: direct capability
        direct_match, direct_conf = self.check([subject, "can"], ability)
        if direct_match:
            if verbose:
                print(f"    {subject} can {ability} → YES (direct, conf={direct_conf:.1f})")
            return True, [subject]
        # Step 3: walk is_a chain, check each ancestor
        chain = self.reason_chain(subject, "is_a")
        for ancestor in chain[1:]:
            aneg, aneg_conf = self.check([ancestor, "cannot"], ability)
            if aneg:
                if verbose:
                    print(f"    {ancestor} cannot {ability} → BLOCKED")
                return False, chain[:chain.index(ancestor) + 1]
            amatch, aconf = self.check([ancestor, "can"], ability)
            if amatch:
                if verbose:
                    print(f"    {subject} can {ability} → YES"
                          f" (inherited from {ancestor}, conf={aconf:.1f})")
                return True, chain[:chain.index(ancestor) + 1]
        # Step 4: fact index fallback (for multi-valued relations)
        direct_facts = self.fact_index.get((subject, "can"), [])
        if ability in direct_facts:
            if verbose:
                print(f"    {subject} can {ability} → YES (fact index)")
            return True, [subject]
        for ancestor in chain[1:]:
            ancestor_facts = self.fact_index.get((ancestor, "can"), [])
            if ability in ancestor_facts:
                if verbose:
                    print(f"    {subject} can {ability} → YES"
                          f" (inherited from {ancestor} via fact index)")
                return True, chain[:chain.index(ancestor) + 1]
        if verbose:
            print(f"    {subject} can {ability} → UNKNOWN")
        return None, chain

    def containment_check(self, item, container, verbose=False):
        """Is item in container? Walk the 'in' chain."""
        chain = self.reason_chain(item, "in", verbose=verbose)
        return container in chain, chain

    def property_check(self, subject, verbose=False):
        """What properties does subject have? Direct + inherited."""
        properties = []
        direct = self.fact_index.get((subject, "has"), [])
        for p in direct:
            properties.append((p, "direct"))
        chain = self.reason_chain(subject, "is_a")
        for ancestor in chain[1:]:
            inherited = self.fact_index.get((ancestor, "has"), [])
            for p in inherited:
                if not any(pp == p for pp, _ in properties):
                    properties.append((p, f"from {ancestor}"))
        if verbose:
            for prop, source in properties:
                print(f"    {subject} has {prop} ({source})")
        return properties

    def syllogism(self, premises, conclusion, verbose=False):
        """Evaluate a syllogism by asserting premises and checking conclusion."""
        if verbose:
            for p in premises:
                print(f"    premise: {p[0]} {p[1]} {p[2]}")
            print(f"    ∴ {conclusion[0]} {conclusion[1]} {conclusion[2]}?")
        subj, rel, obj = conclusion
        if rel == "is_a":
            found, chain = self.is_a_check(subj, obj, verbose=verbose)
            return found, chain
        elif rel == "can":
            found, chain = self.can_check(subj, obj, verbose=verbose)
            return found, chain
        elif rel == "in":
            found, chain = self.containment_check(subj, obj, verbose=verbose)
            return found, chain
        return None, []

    # ── computation ─────────────────────────────────────────────

    def compute(self, a, op, b, memorize=True, verbose=True):
        """The full loop: try → shrug → decompose → verify → memorize."""
        context = [str(a), op, str(b), "="]
        answer, conf = self.lookup(context)
        if answer is not None and conf >= CONFIDENCE_THRESHOLD:
            if verbose:
                print(f"  {a} {op} {b} = {answer}  [direct recall, conf={conf:.1f}]")
            return answer, "recall"

        if verbose:
            print(f"  {a} {op} {b} = ?  [shrug, conf={conf:.2f}] → decomposing...")

        if op == "*":
            result = _decompose_multiply(a, b, self, verbose)
        elif op == "+":
            result = _decompose_add(a, b, self, verbose)
        elif op == "-":
            result = _decompose_add(a, -b, self, verbose)  # placeholder
            if result is None:
                result = a - b
        else:
            result = None

        if result is None:
            if verbose:
                print(f"  FAILED TO DECOMPOSE")
            return None, "failed"

        # Cross-check (commutative verify for multiplication)
        if op == "*":
            rev, rev_conf = self.lookup([str(b), op, str(a), "="])
            if rev is not None and rev_conf >= CONFIDENCE_THRESHOLD:
                if int(rev) == result and verbose:
                    print(f"  cross-check: {b}*{a} = {rev} ✓")
            else:
                rev_result = _decompose_multiply(b, a, self, False)
                if rev_result == result and verbose:
                    print(f"  cross-check: {b}*{a} decomposed = {rev_result} ✓")

        # Memorize
        if memorize and result is not None:
            self.observe(tokenize(f"{a} {op} {b} = {result}"))
            if verbose:
                print(f"  memorized: {a} {op} {b} = {result}")

        return result, "decomposed"

    # ── problem solving ─────────────────────────────────────────

    def solve(self, problem, verbose=True):
        """Solve a problem with unknowns. Forward, backward, gap-fill."""
        tokens = tokenize(problem)
        unknowns = [i for i, t in enumerate(tokens) if t == "?"]

        if not unknowns:
            # Forward: just lookup
            answer, conf = self.lookup(tokens)
            if verbose:
                print(f"  {problem} → {answer} (conf={conf:.1f})")
            return answer

        if len(unknowns) == 1:
            pos = unknowns[0]
            if pos == len(tokens) - 1:
                # Forward: ? is the answer
                context = tokens[:-1]
                answer, conf = self.lookup(context)
                if verbose:
                    print(f"  {problem} → {answer} (conf={conf:.1f})")
                return answer
            else:
                # Backward: try candidates, validate
                target = tokens[-1] if "=" in tokens else None
                eq_pos = tokens.index("=") if "=" in tokens else None
                if eq_pos and eq_pos + 1 < len(tokens):
                    target = tokens[eq_pos + 1]
                candidates = self._get_candidates(tokens, pos)
                for c in candidates:
                    trial = list(tokens)
                    trial[pos] = c
                    context = trial[:-1] if trial[-1] != "=" else trial
                    if target:
                        match, conf = self.check(
                            trial[:eq_pos + 1] if eq_pos else trial[:-1],
                            target)
                        if match:
                            if verbose:
                                print(f"  {problem} → {c} (conf={conf:.1f})")
                            return c
        # Multi-unknown gap-fill
        if len(unknowns) >= 2 and "=" in tokens:
            eq_pos = tokens.index("=")
            target = tokens[eq_pos + 1] if eq_pos + 1 < len(tokens) else None
            if target:
                solutions = []
                candidates = self._get_candidates(tokens, unknowns[0])
                for c1 in candidates:
                    for c2 in candidates:
                        trial = list(tokens)
                        trial[unknowns[0]] = c1
                        trial[unknowns[1]] = c2
                        match, conf = self.check(trial[:eq_pos + 1], target)
                        if match:
                            solutions.append((c1, c2))
                if verbose:
                    print(f"  {problem} → {len(solutions)} solutions")
                    for s in solutions[:5]:
                        print(f"    {s}")
                return solutions
        return None

    def _get_candidates(self, tokens, pos):
        """Generate candidate values for an unknown position."""
        candidates = set()
        for t in tokens:
            if t != "?":
                candidates.update(self.net.get_doors(t, tag="seq"))
                candidates.update(self.net.get_predecessors(t, tag="seq"))
        candidates.discard("?")
        candidates.discard("=")
        for op in ["+", "-", "*", "/", "and", "or", "not"]:
            candidates.discard(op)
        return sorted(candidates)

    def solve_steps(self, steps, verbose=True):
        """Multi-step problem solving with scratch references ($0, $1, ...)."""
        results = []
        for i, step in enumerate(steps):
            # Replace scratch references
            resolved = step
            for j, prev in enumerate(results):
                resolved = resolved.replace(f"${j}", str(prev))
            result = self.solve(resolved, verbose=verbose)
            results.append(result)
            if verbose:
                print(f"  step {i}: {step} → {result}")
        return results

    # ── persistence ─────────────────────────────────────────────

    def assess(self, action_text):
        """Ask the matrix what it learned about this action's consequences.
        The think loop handles fallback automatically — if the full context
        shrugs, it tries progressively simpler contexts."""
        tokens = tokenize(action_text)
        context = tokens + ["result"]
        assessment = {"action": action_text, "checks": {}}

        pos, pos_c = self.check(context, "net_positive")
        neg, neg_c = self.check(context, "net_negative")
        zero, zero_c = self.check(context, "net_zero")

        assessment["checks"]["net_positive"] = (pos, pos_c)
        assessment["checks"]["net_negative"] = (neg, neg_c)
        assessment["checks"]["net_zero"] = (zero, zero_c)

        if neg and neg_c > pos_c and neg_c > zero_c:
            assessment["recommendation"] = "caution"
        elif pos and pos_c > neg_c:
            assessment["recommendation"] = "proceed"
        elif zero and zero_c > neg_c:
            assessment["recommendation"] = "proceed"
        else:
            assessment["recommendation"] = "unknown"

        return assessment

    def plan_think_execute(self, action_text, verbose=True):
        """The universal output loop. Plan, assess persistence, execute or block."""
        if verbose:
            print(f"\n  ┌─ PLAN: {action_text}")
        a = self.assess(action_text)
        if verbose:
            print(f"  ├─ THINK:")
            for name, (val, conf) in a["checks"].items():
                if val:
                    print(f"  │  ✓ {name} (conf={conf:.1f})")
            print(f"  │  → {a['recommendation'].upper()}")
        if a["recommendation"] == "caution":
            if verbose:
                print(f"  └─ ⚠ CAUTION — net negative outcome learned")
            return False, a
        else:
            if verbose:
                print(f"  └─ ✓ PROCEED")
            return True, a

    # ── status ──────────────────────────────────────────────────

    def status(self):
        nodes = self.net.all_nodes()
        tags = set()
        for t in self.net.door_tags.values():
            tags.update(t)
        doors = sum(len(t) for t in self.net.doors.values())
        compiled = bool(self._compiled)
        matrix_shape = self._compiled["W"].shape if compiled else None
        dirty_seqs = len(self.observed_sequences) - self._compiled_up_to
        dirty_consolidation = len(self.observed_sequences) - self._consolidated_up_to
        return {
            "nodes": len(nodes), "doors": doors,
            "tags": sorted(tags), "types": len(self.types),
            "rules": len(self.rules), "lockouts": len(self.lockouts),
            "starts": len(self.starts),
            "observations": len(self.observed_sequences),
            "facts_indexed": sum(len(v) for v in self.fact_index.values()),
            "compiled": compiled, "matrix_shape": matrix_shape,
            "dirty_sequences": dirty_seqs,
            "dirty_nodes": len(self._dirty_nodes),
            "needs_consolidation": dirty_consolidation > 0,
        }


# ═════════════════════════════════════════════════════════════════
# COMPUTATION HELPERS — decompose when shrug
# ═════════════════════════════════════════════════════════════════

def digits_of(n):
    """Extract digits of a number. Tokenization-level (Rule 2 exception)."""
    n = abs(int(n))
    if n == 0:
        return [0]
    ds = []
    while n > 0:
        ds.append(n % 10)
        n //= 10
    ds.reverse()
    return ds


def _decompose_multiply(a, b, isaac, verbose=True):
    """Decompose a * b into digit-pair lookups from memorized tables."""
    da = digits_of(a)
    db = digits_of(b)
    total = 0
    for i, digit_a in enumerate(da):
        place_a = len(da) - 1 - i
        for j, digit_b in enumerate(db):
            place_b = len(db) - 1 - j
            place_value = 10 ** (place_a + place_b)
            product_str, conf = isaac.lookup(
                [str(digit_a), "*", str(digit_b), "="])
            if product_str is None or conf < CONFIDENCE_THRESHOLD:
                return None
            product = int(product_str)
            contribution = product * place_value
            total += contribution
            if verbose:
                print(f"    {digit_a}×{digit_b}={product:>4d}"
                      f" × {place_value:>6d} = {contribution:>8d}")
    if verbose:
        print(f"    {'─' * 40}")
        print(f"    TOTAL = {total}")
    return total


def _decompose_add(a, b, isaac, verbose=True):
    """Decompose a + b into digit-pair additions with carry."""
    da = digits_of(a)
    db = digits_of(b)
    max_len = max(len(da), len(db))
    da = [0] * (max_len - len(da)) + da
    db = [0] * (max_len - len(db)) + db
    result_digits = []
    carry = 0
    for i in range(max_len - 1, -1, -1):
        digit_sum = da[i] + db[i] + carry
        sum_str, conf = isaac.lookup([str(da[i]), "+", str(db[i]), "="])
        if sum_str is not None and conf >= CONFIDENCE_THRESHOLD:
            partial = int(sum_str)
            if carry > 0:
                carry_str, cc = isaac.lookup([str(partial), "+", str(carry), "="])
                if carry_str is not None and cc >= CONFIDENCE_THRESHOLD:
                    digit_sum = int(carry_str)
                else:
                    digit_sum = da[i] + db[i] + carry
            else:
                digit_sum = partial
        carry = digit_sum // 10
        result_digits.append(digit_sum % 10)
    if carry > 0:
        result_digits.append(carry)
    result_digits.reverse()
    result = int("".join(str(d) for d in result_digits))
    if verbose:
        print(f"    {a} + {b} = {result}")
    return result


# ═════════════════════════════════════════════════════════════════
# WORLD — state management and planning
# ═════════════════════════════════════════════════════════════════

class World:
    """Manages mutable world state. Actions have preconditions and effects.
    Uses Isaac for persistence assessment."""

    def __init__(self, isaac=None):
        self.state = defaultdict(set)   # entity → {facts}
        self.actions = {}               # (source_pattern, action, target_pattern) → {...}
        self.isaac = isaac

    def set_state(self, entity, fact):
        self.state[entity].add(fact)

    def clear_state(self, entity, fact):
        self.state[entity].discard(fact)

    def has_state(self, entity, fact):
        return fact in self.state.get(entity, set())

    def show_state(self):
        for entity in sorted(self.state):
            facts = sorted(self.state[entity])
            if facts:
                print(f"  {entity}: {', '.join(facts)}")

    def teach_action(self, source, action, target,
                     preconditions=None, effects=None):
        self.actions[(source, action, target)] = {
            "preconditions": preconditions or [],
            "effects": effects or [],
        }

    def execute(self, source, action, target, verbose=True):
        """Execute an action. Check preconditions. Apply effects."""
        key = (source, action, target)
        wildcard = ("*", action, "*")
        specific_src = (source, action, "*")
        specific_tgt = ("*", action, target)

        spec = None
        for k in [key, specific_src, specific_tgt, wildcard]:
            if k in self.actions:
                spec = self.actions[k]
                break
        if spec is None:
            if verbose:
                print(f"  Unknown action: {source} {action} {target}")
            return False, ["unknown action"]

        # Check preconditions
        failed = []
        for cond in spec["preconditions"]:
            resolved = cond.replace("SOURCE", source).replace("TARGET", target)
            parts = resolved.split()
            if len(parts) >= 3 and parts[1] == "near":
                # Proximity check
                loc_src = self._get_location(parts[0])
                loc_tgt = self._get_location(parts[2])
                if loc_src != loc_tgt:
                    failed.append(resolved)
            elif len(parts) >= 3 and parts[1] == "is":
                if not self.has_state(parts[0], " ".join(parts[1:])):
                    failed.append(resolved)
            elif len(parts) >= 2 and parts[1] == "has":
                if not self.has_state(parts[0], " ".join(parts[1:])):
                    failed.append(resolved)

        if failed:
            if verbose:
                print(f"  Preconditions failed: {failed}")
            return False, failed

        # Apply effects
        for effect in spec["effects"]:
            resolved = effect.replace("SOURCE", source).replace("TARGET", target)
            parts = resolved.split()
            if len(parts) >= 3 and parts[1] == "is":
                self.set_state(parts[0], " ".join(parts[1:]))
            elif len(parts) >= 2 and parts[0].startswith("not_"):
                entity = parts[0].replace("not_", "")
                # Remove the matching positive state
                # This is a simplification — should match more carefully
                pass
            elif len(parts) >= 2 and parts[1] == "has":
                self.set_state(parts[0], " ".join(parts[1:]))
            if verbose:
                print(f"  effect: {resolved}")
        return True, []

    def _get_location(self, entity):
        for fact in self.state.get(entity, set()):
            if fact.startswith("in_") or fact.startswith("at_"):
                return fact
        return None


# ═════════════════════════════════════════════════════════════════
# TEST SUITE
# ═════════════════════════════════════════════════════════════════

def _div(title):
    print(f"\n{'═' * 65}")
    print(f"  {title}")
    print(f"{'═' * 65}")


def test_language():
    """Language: observe, crystallize, generate, type inference."""
    _div("LANGUAGE")
    isaac = Isaac()
    sentences = [
        "the cat sat .", "the dog ran .", "the cat ran .",
        "the big cat sat .", "the small dog ran .",
        "a cat is soft .", "a dog is loyal .",
        "the bird flew .", "a fish swam .",
        "the big dog barked .", "the small cat purred .",
        "she ran fast .", "he walked slowly .",
        "a red ball bounced .", "the blue car stopped .",
    ]
    bad = ["cat the sat .", "dog the ran .", "the sat cat .", "the ran dog ."]
    for s in sentences:
        isaac.observe(tokenize(s))
    for s in bad:
        isaac.observe_negative(tokenize(s))
    isaac.crystallize(verbose=True)

    print(f"\n  Generation:")
    for concept in ["cat", "dog", "ball"]:
        chain = isaac.generate(concept)
        print(f"    '{concept}' → {' '.join(chain)}")

    # Type inference
    result = isaac.infer("dog", "sat")
    print(f"\n  dog→sat inferred: {result['inferred']} via {result.get('via')}")
    return True


def test_math():
    """Math: memorize tables, recall via matrix, shrug boundary."""
    _div("MATH — matrix recall")
    isaac = Isaac()
    for a in range(20):
        for b in range(20):
            isaac.observe(tokenize(f"{a} + {b} = {a + b}"))
            isaac.observe(tokenize(f"{a} * {b} = {a * b}"))
    # No manual compile() — lookup auto-compiles (Stage 3: ROUTE)

    tests = [
        (["7", "*", "8", "="], "56"),
        (["3", "+", "5", "="], "8"),
        (["12", "*", "12", "="], "144"),
        (["19", "+", "19", "="], "38"),
        (["0", "*", "15", "="], "0"),
        (["1", "*", "7", "="], "7"),
    ]
    correct = 0
    for context, expected in tests:
        answer, conf = isaac.lookup(context)
        ok = answer == expected
        correct += ok
        print(f"  {'✓' if ok else '✗'}  {' '.join(context)} → {answer}"
              f"  (expected {expected}, conf={conf:.1f})")
    print(f"\n  {correct}/{len(tests)}")
    return correct == len(tests)


def test_logic():
    """Logic: truth tables via matmul, compound decomposition."""
    _div("LOGIC")
    isaac = Isaac()
    for a in ["true", "false"]:
        for b in ["true", "false"]:
            av, bv = a == "true", b == "true"
            isaac.observe(tokenize(f"{a} and {b} = {'true' if av and bv else 'false'}"))
            isaac.observe(tokenize(f"{a} or {b} = {'true' if av or bv else 'false'}"))
            isaac.observe(tokenize(f"{a} xor {b} = {'true' if av ^ bv else 'false'}"))
            isaac.observe(tokenize(f"{a} implies {b} = {'true' if (not av) or bv else 'false'}"))
        isaac.observe(tokenize(f"not {a} = {'false' if a == 'true' else 'true'}"))
    # Auto-compiles on first query

    tests = [
        ("true and true", "true"), ("true and false", "false"),
        ("false or true", "true"), ("false or false", "false"),
        ("not true", "false"), ("not false", "true"),
        ("true xor false", "true"),
    ]
    correct = 0
    for expr, expected in tests:
        result, _ = isaac.logic_eval(expr)
        ok = result == expected
        correct += ok
        print(f"  {'✓' if ok else '✗'}  {expr:30s} → {result}")
    print(f"\n  {correct}/{len(tests)}")

    # Compound
    compound = [
        ("true and false or true", "true"),
        ("not true or false", "false"),
        ("not false and true", "true"),
    ]
    cc = 0
    for expr, expected in compound:
        result, _ = isaac.logic_eval(expr)
        ok = result == expected
        cc += ok
        print(f"  {'✓' if ok else '✗'}  {expr:30s} → {result}")
    print(f"  compound: {cc}/{len(compound)}")
    return correct == len(tests) and cc == len(compound)


def test_reasoning():
    """Reasoning: is_a chains, capability inheritance, containment."""
    _div("REASONING")
    isaac = Isaac()
    # Taxonomy
    for subj, obj in [("cat", "mammal"), ("dog", "mammal"),
                      ("mammal", "animal"), ("animal", "living_thing"),
                      ("robin", "bird"), ("penguin", "bird"),
                      ("bird", "animal"), ("salmon", "fish"),
                      ("fish", "animal"), ("oak", "tree"),
                      ("tree", "plant"), ("plant", "living_thing")]:
        isaac.teach(subj, "is_a", obj)
    # Capabilities
    for subj, obj in [("bird", "fly"), ("bird", "sing"),
                      ("fish", "swim"), ("cat", "purr"), ("cat", "climb"),
                      ("dog", "bark"), ("penguin", "swim"),
                      ("living_thing", "grow"), ("animal", "move")]:
        isaac.teach(subj, "can", obj)
    # Negatives
    for subj, obj in [("penguin", "fly"), ("fish", "walk")]:
        isaac.observe(tokenize(f"{subj} cannot {obj}"))
        isaac.fact_index[(subj, "cannot")].append(obj)
    # Containment
    for inner, outer in [("ball", "box"), ("box", "closet"),
                         ("closet", "room"), ("room", "house")]:
        isaac.teach(inner, "in", outer)
    # Auto-compiles on first query

    # Is-a
    correct = 0
    for subj, tgt, expected in [("cat", "animal", True),
                                 ("cat", "living_thing", True),
                                 ("robin", "animal", True),
                                 ("cat", "plant", False)]:
        found, chain = isaac.is_a_check(subj, tgt)
        ok = found == expected
        correct += ok
        print(f"  {'✓' if ok else '✗'}  {subj} is_a {tgt}? {found}"
              f"  chain: {' → '.join(chain)}")

    # Can
    for subj, ability, expected in [("robin", "fly", True),
                                     ("robin", "sing", True),
                                     ("cat", "climb", True),
                                     ("cat", "grow", True),
                                     ("penguin", "fly", False),
                                     ("penguin", "swim", True)]:
        result, chain = isaac.can_check(subj, ability, verbose=True)
        if result is None:
            result = False
        ok = result == expected
        correct += ok
        print(f"  {'✓' if ok else '✗'}  can {subj} {ability}? {result}")

    # Containment
    found, chain = isaac.containment_check("ball", "house")
    ok = found == True
    correct += ok
    print(f"  {'✓' if ok else '✗'}  ball in house? {found}  chain: {' → '.join(chain)}")

    print(f"\n  {correct}/11")
    return correct == 11


def test_decompose():
    """Decompose: shrug → digit-pair lookups → assemble → verify."""
    _div("DECOMPOSE WHEN SHRUG")
    isaac = Isaac()
    for a in range(100):
        for b in range(100):
            isaac.observe(tokenize(f"{a} * {b} = {a * b}"))
            isaac.observe(tokenize(f"{a} + {b} = {a + b}"))
    for a in range(100):
        isaac.observe(tokenize(f"{a} * 100 = {a * 100}"))
        isaac.observe(tokenize(f"{a} * 1000 = {a * 1000}"))
    # Auto-compiles on first compute() call

    tests = [(137, "*", 48, 6576), (256, "*", 31, 7936), (999, "*", 999, 998001)]
    correct = 0
    for a, op, b, expected in tests:
        result, method = isaac.compute(a, op, b, memorize=False)
        ok = (result == expected)
        correct += ok
        print(f"  {'✓' if ok else '✗'}  {a} {op} {b} = {result}"
              f"  (expected {expected}) [{method}]")
    print(f"\n  {correct}/{len(tests)}")
    return correct == len(tests)


def test_persistence():
    """Persistence: learn from consequences, assess novel actions."""
    _div("PERSISTENCE — learn from consequences")
    isaac = Isaac()

    scenarios = [
        ("me build birdhouse", 3, 6),
        ("me assemble watch", 6, 8),
        ("me smash watch", 8, 3),
        ("me knock tower", 7, 5),
        ("me burn painting", 6, 2),
        ("me snap stick", 1, 1),
        ("me crack rock", 1, 1),
        ("me oil watch", 7, 8),
        ("me repair roof", 5, 5),
    ]
    for action, before, after in scenarios:
        delta = after - before
        if delta > 0:
            isaac.observe(tokenize(f"{action} result net_positive"))
        elif delta < 0:
            isaac.observe(tokenize(f"{action} result net_negative"))
        else:
            isaac.observe(tokenize(f"{action} result net_zero"))
        # Verb-level observation for generalization
        verb = tokenize(action)[1]  # "me VERB object" → VERB at index 1
        if delta > 0:
            isaac.observe(tokenize(f"{verb} result net_positive"))
        elif delta < 0:
            isaac.observe(tokenize(f"{verb} result net_negative"))
        else:
            isaac.observe(tokenize(f"{verb} result net_zero"))

    # Auto-compiles on first assess() call

    # Known actions
    correct = 0
    for action, expected in [("me build birdhouse", "proceed"),
                              ("me smash watch", "caution"),
                              ("me snap stick", "proceed"),
                              ("me oil watch", "proceed")]:
        a = isaac.assess(action)
        ok = a["recommendation"] == expected
        correct += ok
        print(f"  {'✓' if ok else '✗'}  {action:25s} → {a['recommendation']}")

    # Novel actions (verb-level generalization)
    for action, expected in [("me smash computer", "caution"),
                              ("me build castle", "proceed"),
                              ("me snap pencil", "proceed")]:
        a = isaac.assess(action)
        ok = a["recommendation"] == expected
        correct += ok
        print(f"  {'✓' if ok else '✗'}  {action:25s} → {a['recommendation']}"
              f"  [think loop fallback]")

    print(f"\n  {correct}/7")
    return correct == 7


def test_waves():
    _div("WAVES — simultaneity, movement, circles")
    isaac = Isaac()
    rng = np.random.default_rng(5)
    # two independent routines wave through his doors, noise flickers around:
    # day cycle (dwell 3):   sun+light -> work+tools -> moon+dark -> ...
    # tide cycle (dwell 5):  tide_in+wet <-> tide_out+dry
    P1 = [("sun", "light"), ("work", "tools"), ("moon", "dark")]
    P2 = [("tide_in", "wet"), ("tide_out", "dry")]
    noise = ["gull", "cloud", "truck", "radio"]
    for _ in range(8):                       # fresh phases: independent waves
        o1, o2 = int(rng.integers(0, 9)), int(rng.integers(0, 10))
        for s in range(75):
            active = set(P1[((s + o1) // 3) % 3]) | set(P2[((s + o2) // 5) % 2])
            active = {a for a in active if rng.random() < 0.9}   # sensor flicker
            active |= {n for n in noise if rng.random() < 0.3}
            isaac.tick(active)
    waves = isaac.wave_consolidate()

    correct = 0
    got = {frozenset(g) for g in waves["groups"]}
    want = {frozenset(p) for p in P1 + P2}
    ok = got == want
    correct += ok
    print(f"  {'✓' if ok else '✗'}  simultaneity: the 5 planted pairs, "
          f"no noise doors ({len(waves['groups'])} groups)")

    ok = sorted(len(c) for c in waves["circle_orders"]) == [2, 3]
    correct += ok
    print(f"  {'✓' if ok else '✗'}  circles: day-cycle (3) and tide-cycle (2) "
          f"→ {waves['circles']}")

    ok = all(isaac.net.get_predecessors(c, tag="wave") for c in waves["circles"])
    correct += ok
    print(f"  {'✓' if ok else '✗'}  circles entered the net as nodes "
          f"(composable upward)")

    # shuffled time: co-occurrence survives, ALL movement must die
    shuffled = Isaac()
    order = rng.permutation(len(isaac.activation_log))
    shuffled.activation_log = [isaac.activation_log[i] for i in order]
    w2 = shuffled.wave_consolidate()
    ok = ({frozenset(g) for g in w2["groups"]} == want
          and not w2["edges"] and not w2["circles"])
    correct += ok
    print(f"  {'✓' if ok else '✗'}  shuffled-time control: groups survive, "
          f"movement dies ({len(w2['edges'])} edges, {len(w2['circles'])} circles)")

    print(f"\n  {correct}/4")
    return correct == 4


def test_tracking():
    _div("TRACKING — his clock, temporary statuses, emergent explanation")
    isaac = Isaac()
    rng = np.random.default_rng(9)
    SUNd = ["disk", "light", "warm", "sky"]
    NIGHTd = ["moon", "stars"]
    CLOUDd = ["cloud_a", "cloud_b"]
    NOISEd = ["gull", "truck"]

    def build(T):
        day = np.zeros(T, dtype=int); cl = np.zeros(T, dtype=int)
        t, ph = 0, 1
        while t < T:
            for _ in range(int(rng.integers(8, 15))):
                if t < T:
                    day[t] = ph; t += 1
            ph = 1 - ph
        t = int(rng.integers(0, 5))
        while t < T:
            for _ in range(int(rng.integers(6, 14))):
                if t < T:
                    cl[t] = 1; t += 1
            t += int(rng.integers(8, 16))
        ticks = []
        for t in range(T):
            a = set()
            base = (SUNd if day[t] else NIGHTd)
            for dname in base:
                if dname == "disk" and day[t] and cl[t]:
                    if rng.random() < 0.05:
                        a.add(dname)
                elif rng.random() < 0.9:
                    a.add(dname)
            for dname in CLOUDd:
                if (cl[t] and rng.random() < 0.9) or rng.random() < 0.05:
                    a.add(dname)
            a |= {dname for dname in NOISEd if rng.random() < 0.3}
            ticks.append(a)
        return ticks, day, cl

    # phase A: plain sensing -> consolidation discovers identity + rhythm
    ticksA, _, _ = build(1400)
    for a in ticksA:
        isaac.tick(a)
    waves = isaac.wave_consolidate()
    sun_g = next((g for g in waves["groups"] if "light" in g), None)
    sun_name = f"wave:{'_'.join(sun_g[:2])}[{len(sun_g)}]" if sun_g else None
    circle = next((c for c in waves["circles"]
                   if sun_name in isaac.net.get_predecessors(c, tag="wave")), None)
    ok = circle is not None and isaac.follow(circle)
    correct = int(ok)
    print(f"  {'✓' if ok else '✗'}  day/night circle discovered and followed "
          f"({circle})")
    if not ok:
        print(f"\n  {correct}/5")
        return False

    # phase B: tracked sensing — clock, statuses, world state
    ticksB, dayB, clB = build(900)
    state_hits = phase_hits = 0
    for t, a in enumerate(ticksB):
        isaac.tick(a)
        _, ph = isaac.phase_log[circle][-1] if isaac.phase_log[circle] else (0, None)
        phase_hits += ((ph == sun_name) == bool(dayB[t]))
        want = bool(dayB[t] and clB[t])
        state_hits += (isaac.world.has_state(sun_name, "missing disk") == want)
    ok = phase_hits / len(ticksB) >= 0.9
    correct += ok
    print(f"  {'✓' if ok else '✗'}  clock in scratch: phase correct "
          f"{phase_hits/len(ticksB)*100:.1f}% (incl. occlusion)")
    ok = state_hits / len(ticksB) >= 0.85
    correct += ok
    print(f"  {'✓' if ok else '✗'}  temporary status via world state: "
          f"'sun missing disk' tracks (day AND cloud) "
          f"{state_hits/len(ticksB)*100:.1f}%/tick")

    # consolidate again: statuses are doors -> explanation emerges -> fact
    isaac.wave_consolidate()
    blockers = set()
    for (s, r), objs in isaac.fact_index.items():
        if r == "blocks" and "disk" in objs:
            blockers.add(s)
    ok = any("cloud" in str(b) for b in blockers) and \
        not any(n in str(b) for b in blockers for n in NOISEd)
    correct += ok
    print(f"  {'✓' if ok else '✗'}  explanation emerged and was taught as a "
          f"fact: blocks(disk) <- {sorted(str(b) for b in blockers)}")

    # permanence through the existing organ
    fired = isaac.recognize_doors({"light", "warm", "sky"}, tag="part")
    ok = fired.get(sun_name, 0) >= 0.5
    correct += ok
    print(f"  {'✓' if ok else '✗'}  recognize_doors: sun fires from partial "
          f"doors, disk hidden (score {fired.get(sun_name, 0):.2f})")

    print(f"\n  {correct}/5")
    return correct == 5


def test_discovery():
    _div("DISCOVERY — the challenge loop: the thing that learns things")
    isaac = Isaac()
    rng = np.random.default_rng(12)
    n = 1600

    # (a) a hidden law -> UNDERSTOOD, and the law is REUSABLE
    X = rng.normal(0, 1, (n, 5))
    y = X[:, 0] * X[:, 1] + X[:, 2] ** 2 - X[:, 3] + rng.normal(0, 0.02, n)
    res = isaac.discover(X, y, name="challenge_a")
    ok = res["verdict"] == "UNDERSTOOD"
    correct = int(ok)
    print(f"  {'✓' if ok else '✗'}  hidden law found: {res['verdict']} "
          f"(held-out R2 {res['r2']:.3f})")
    print(f"       equation: {res['equation']}")

    Xn = rng.normal(0, 1, (400, 5))
    yn = Xn[:, 0] * Xn[:, 1] + Xn[:, 2] ** 2 - Xn[:, 3]
    p = isaac.apply_law("challenge_a", Xn)
    r2n = 1 - np.sum((yn - p) ** 2) / np.sum((yn - yn.mean()) ** 2)
    ok = r2n >= 0.99
    correct += ok
    print(f"  {'✓' if ok else '✗'}  the law is now COMPUTABLE: apply_law() on "
          f"new instances R2 {r2n:.3f}")

    # (b) a transcendental law (the physics shape)
    Xb = np.column_stack([rng.lognormal(0, .4, n), rng.lognormal(0, .4, n),
                          rng.normal(0, 1, n), rng.normal(0, 1, n)])
    yb = Xb[:, 0] * Xb[:, 1] * np.cos(Xb[:, 2] - Xb[:, 3])
    yb = yb + rng.normal(0, 0.01 * yb.std(), n)
    resb = isaac.discover(Xb, yb, name="challenge_b")
    ok = resb["verdict"] == "UNDERSTOOD"
    correct += ok
    print(f"  {'✓' if ok else '✗'}  transcendental law: {resb['verdict']} "
          f"(R2 {resb['r2']:.3f})  {resb['equation']}")

    # (c) pure noise -> he must SAY there is nothing, and the accounting
    # must put essentially everything in the noise column
    resc = isaac.discover(X, rng.normal(0, 1, n))
    acc_c = resc["accounting"]
    ok = (resc["verdict"] == "NO RULE" and acc_c["noise"] >= 90.0
          and abs(acc_c["articulated"] + acc_c["captured"]
                  + acc_c["noise"] - 100.0) < 0.2)
    correct += ok
    print(f"  {'✓' if ok else '✗'}  pure noise: {resc['verdict']} "
          f"(no invented equation; accounting {acc_c['articulated']}/"
          f"{acc_c['captured']}/{acc_c['noise']} = law/caught/noise)")

    # (d) a rule his equation class cannot say (yet): caught, not said
    Xd = np.column_stack([rng.normal(0, 1, (n, 2)), rng.normal(0, 1, (n, 1))])
    yd = np.sin(3.0 * Xd[:, 0] * Xd[:, 1])
    resd = isaac.discover(Xd, yd)
    ok = resd["verdict"] in ("CAPTURED", "PARTIAL") and resd["r2"] < 0.9
    correct += ok
    print(f"  {'✓' if ok else '✗'}  hard rule sin(3*x0*x1): {resd['verdict']} "
          f"(equation R2 {resd['r2']:.3f}, captured {resd['captured_r2']:.3f})"
          f" — partially said / caught, honestly not UNDERSTOOD")

    # (e) single input, mixed forms — 'it only does linear' is dead here
    Xe = rng.uniform(-3, 3, (n, 1))
    ye = 0.5 * Xe[:, 0] ** 2 + 1.5 * np.sin(2 * Xe[:, 0]) \
        + rng.normal(0, 0.02, n)
    rese = isaac.discover(Xe, ye, name="challenge_e")
    ok = rese["verdict"] == "UNDERSTOOD"
    correct += ok
    print(f"  {'✓' if ok else '✗'}  one input, transcendental+poly: "
          f"{rese['verdict']} (R2 {rese['r2']:.3f})")
    print(f"       equation: {rese['equation']}")

    # (f) damped oscillation — the real face of exp((-a+bi)t): complex
    # structure arrives as an exp*cos PAIR, and the decay 0.4 is NOT on the
    # atom grid — the refine pass must find it
    t = rng.uniform(0, 5, n).reshape(-1, 1)
    yf = np.exp(-0.4 * t[:, 0]) * np.cos(3.0 * t[:, 0]) \
        + rng.normal(0, 0.01, n)
    resf = isaac.discover(t, yf, name="challenge_f")
    ok = resf["verdict"] == "UNDERSTOOD"
    correct += ok
    print(f"  {'✓' if ok else '✗'}  damped oscillation (complex pair, "
          f"off-grid decay): {resf['verdict']} (R2 {resf['r2']:.3f})")
    print(f"       equation: {resf['equation']}")

    # (g) THE ACCOUNTING (audit 2.8): plant a law + a KNOWN noise fraction;
    # articulated% + captured% + noise% must equal 100 and match the truth.
    # y = x0*x1 (var ~1) + noise sd 0.6 (var 0.36) -> true law share ~73.5%
    Xg = rng.normal(0, 1, (n, 4))
    yg = Xg[:, 0] * Xg[:, 1] + rng.normal(0, 0.6, n)
    resg = isaac.discover(Xg, yg, name="challenge_g")
    acc = resg["accounting"]
    true_share = 100.0 / 1.36
    ok = (abs(acc["articulated"] + acc["captured"] + acc["noise"] - 100.0)
          < 0.2 and abs(acc["articulated"] - true_share) < 10.0
          and resg["dossier"] is not None)
    correct += ok
    print(f"  {'✓' if ok else '✗'}  accounting vs planted truth: articulated "
          f"{acc['articulated']}% (true ~{true_share:.1f}%) + captured "
          f"{acc['captured']}% + noise {acc['noise']}% = 100; residual "
          f"dossier attached ({resg['dossier']['unknown']}, "
          f"{resg['dossier']['share_pct']}% share)")

    # (h) graded belief: confidence must be high inside the data, decay
    # with extrapolation distance, and never be a binary stamp
    Xin = rng.normal(0, 1, (200, 4))
    Xnear = Xg.max(0) * 1.1 + rng.uniform(0, 0.1, (200, 4))
    Xfar = Xg.max(0) * 2.0 + rng.uniform(0, 0.1, (200, 4))
    ci = isaac.law_confidence("challenge_g", Xin).mean()
    cn = isaac.law_confidence("challenge_g", Xnear).mean()
    cf = isaac.law_confidence("challenge_g", Xfar).mean()
    ok = ci > 0.85 and ci > cn > cf and cf < 0.5
    correct += ok
    print(f"  {'✓' if ok else '✗'}  extrapolated confidence: inside "
          f"{ci:.2f} > near-beyond {cn:.2f} > far-beyond {cf:.2f} "
          f"(measured decay, not a stamp)")

    print(f"\n  {correct}/9")
    return correct == 9


def test_rivalry():
    _div("RIVALRY — the classic look-alikes, held open until confirmed")
    isaac = Isaac()
    rng = np.random.default_rng(15)
    n = 1200

    # a pendulum observed only near its center: cos(0.5x) on |x|<1.2 —
    # parabola territory. The tie must be DECLARED, with a probe.
    X = rng.uniform(-1.2, 1.2, (n, 2))
    y = 5.0 * np.cos(0.5 * X[:, 0]) + rng.normal(0, 0.02, n)
    res = isaac.discover(X, y, name="pendulum")
    ties = res["rivals"]
    ok = len(ties) > 0
    correct = int(ok)
    print(f"  {'✓' if ok else '✗'}  narrow-range cosine: tie declared with "
          f"{[t['rival'] for t in ties]} (F {[t['F'] for t in ties]})")

    probes_out = [t for t in ties if t["probe"]["beyond"]]
    ok = len(probes_out) > 0
    correct += ok
    p0 = (probes_out or ties or [dict(probe=dict(x=0))])[0]["probe"]
    print(f"  {'✓' if ok else '✗'}  probe points OUTSIDE the observed range: "
          f"sample x0 near {p0.get('x')} (observed was ±1.2)")

    # the discriminating data arrives — the tie must resolve to the cosine
    X2 = rng.uniform(-4.5, 4.5, (600, 2))
    y2 = 5.0 * np.cos(0.5 * X2[:, 0]) + rng.normal(0, 0.02, 600)
    c = isaac.confirm("pendulum", X2, y2)
    eq = isaac.net.get_meta("law:pendulum", "equation")
    ok = c is not None and not c["rivals_left"] and "cos" in eq
    correct += ok
    print(f"  {'✓' if ok else '✗'}  confirm(): {c['status'] if c else None} "
          f"-> {eq[:60]}")

    # control: a TRUE parabola, same narrow range — must resolve the other way
    yb = 5.0 - 0.6 * X[:, 0] ** 2 + rng.normal(0, 0.02, n)
    isaac.discover(X, yb, name="bowl")
    y2b = 5.0 - 0.6 * X2[:, 0] ** 2 + rng.normal(0, 0.02, 600)
    cb = isaac.confirm("bowl", X2, y2b)
    eqb = isaac.net.get_meta("law:bowl", "equation")
    ok = cb is not None and not cb["rivals_left"] and "x0*x0" in eqb \
        and "cos" not in eqb.split("x0*x0")[0]
    correct += ok
    print(f"  {'✓' if ok else '✗'}  control (true parabola): "
          f"{cb['status'] if cb else None} -> {eqb[:60]}")

    print(f"\n  {correct}/4")
    return correct == 4


def test_spatial():
    _div("SPATIAL — the bridge: relations from motion, coordinates stay out")
    isaac = Isaac()
    rng = np.random.default_rng(23)

    def fourbar_frames(scale=1.0, rot=0.0, tx=0.0, ty=0.0, T=480,
                       noise=0.003):
        """Closed-form four-bar (crank 2, coupler 7, rocker 6, ground 8)
        under 2 crank cycles, arbitrary pose, gaussian measurement noise."""
        crank, coupler, rocker, ground = (x * scale for x in (2., 7., 6., 8.))
        c, s = np.cos(rot), np.sin(rot)
        p0 = np.array([tx, ty])
        p3 = p0 + ground * np.array([c, s])
        out = []
        for k in range(T):
            th = 4 * np.pi * k / T + rot
            p1 = p0 + crank * np.array([np.cos(th), np.sin(th)])
            d = np.linalg.norm(p3 - p1)
            a = (coupler ** 2 - rocker ** 2 + d ** 2) / (2 * d)
            h = np.sqrt(max(coupler ** 2 - a ** 2, 0.0))
            u = (p3 - p1) / d
            p2 = p1 + a * u + h * np.array([-u[1], u[0]])
            out.append(np.stack([p0, p1, p2, p3])
                       + rng.normal(0, noise * scale, (4, 2)))
        return np.array(out)

    # (a) perceive a four-bar; the facts must be queryable
    rel = isaac.observe_spatial(fourbar_frames(), label="fbA")
    q_locked = isaac.fact_index[("fbA.p0", "locked_to")]
    q_anchor = isaac.fact_index[("fbA", "anchored_at")]
    ok = (len(rel["parts"]) == 4 and len(rel["hinges"]) == 4
          and "fbA.p1" in q_locked and "fbA.p3" in q_locked
          and set(q_anchor) == {"fbA.p0", "fbA.p3"})
    correct = int(ok)
    print(f"  {'✓' if ok else '✗'}  four-bar perceived: 4 bars (incl. the "
          f"undeclared ground), 4 hinges; facts answer: p0 locked_to "
          f"{q_locked}, anchored {q_anchor}")

    # (b) recognition across pose and scale — relations are invariant
    isaac.observe_spatial(fourbar_frames(scale=2.4, rot=0.9, tx=6, ty=-2),
                          label="fbB")
    v = isaac.compare_scenes("fbA", "fbB")
    ok = v["verdict"] == "SAME"
    correct += ok
    print(f"  {'✓' if ok else '✗'}  same mechanism, 2.4x bigger, rotated, "
          f"moved: {v['verdict']} (signature gap {v.get('signature_gap')})")

    # (c) discrimination: a rigid plate swinging on a pin is NOT a four-bar
    sq = np.array([[0., 0.], [0., 3.], [2., 3.], [2., 0.]])
    plate = []
    for k in range(360):
        th = 1.2 * np.sin(2 * np.pi * k / 180)
        c, s = np.cos(th), np.sin(th)
        R = np.array([[c, -s], [s, c]])
        plate.append(sq @ R.T + rng.normal(0, 0.003, (4, 2)))
    isaac.observe_spatial(np.array(plate), label="plate")
    v = isaac.compare_scenes("fbA", "plate")
    ok = v["verdict"] == "DIFFERENT"
    correct += ok
    print(f"  {'✓' if ok else '✗'}  rigid plate on a pin vs four-bar: "
          f"{v['verdict']}")

    # (d) the null gate at the bridge: walkers must teach NOTHING
    walk = np.cumsum(rng.normal(0, 0.08, (500, 5, 2)), axis=0) \
        + rng.normal(0, 0.003, (500, 5, 2))
    before = sum(len(v_) for v_ in isaac.fact_index.values())
    reln = isaac.observe_spatial(walk, label="nothing")
    after = sum(len(v_) for v_ in isaac.fact_index.values())
    ok = before == after and not reln["locked"] and not reln["parts"]
    correct += ok
    print(f"  {'✓' if ok else '✗'}  random walkers: 0 relations survive the "
          f"nulls, 0 facts taught (index {before} -> {after})")

    print(f"\n  {correct}/4")
    return correct == 4


# ═════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Isaac — Unified Engine")
    print("One operation. All the way up.\n")

    results = {}
    results["language"] = test_language()
    results["math"] = test_math()
    results["logic"] = test_logic()
    results["reasoning"] = test_reasoning()
    results["decompose"] = test_decompose()
    results["persistence"] = test_persistence()
    results["waves"] = test_waves()
    results["tracking"] = test_tracking()
    results["discovery"] = test_discovery()
    results["rivalry"] = test_rivalry()
    results["spatial"] = test_spatial()

    _div("SUMMARY")
    for name, passed in results.items():
        print(f"  {'✓' if passed else '✗'}  {name}")
    total = sum(1 for v in results.values() if v)
    print(f"\n  {total}/{len(results)} capability areas passed")

    # Final status
    isaac = Isaac()
    for expr in ["the cat sat .", "3 + 5 = 8", "true and false = false",
                 "cat is_a mammal"]:
        isaac.observe(tokenize(expr))
    isaac.consolidate()
    st = isaac.status()
    print(f"\n  Quick status: {st['nodes']} nodes, {st['doors']} doors, "
          f"compiled={st['compiled']}, dirty_seqs={st['dirty_sequences']}")
    print(f"\n  One file. One class. One operation.")
