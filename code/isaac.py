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

# ISAAC v0.1.2 alpha 1 (owner-named, 2026-08-19) — the release that
# ships THE ONE-FILE BODY (persistence format v2).
__version__ = "0.1.2-alpha1"


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
        self.preds = defaultdict(set)             # node → {sources} (index)

    def _ensure_preds(self):
        # minds saved pre-index: rebuild once, lazily (same pattern
        # as door_counts back-compat)
        if not hasattr(self, "preds"):
            self.preds = defaultdict(set)
            for src, tgts in self.doors.items():
                for t in tgts:
                    self.preds[t].add(src)

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
        self._ensure_preds()
        self.preds[tgt].add(src)
        if tgt not in self.doors:
            self.doors[tgt] = set()
        return is_new

    def remove_door(self, src, tgt):
        """The inverse of add_door — full index cleanup (doors, tags,
        counts, preds). Added 2026-07-25: without it, superseded types
        leave stale member->type doors that keep inflating recall
        (dead types were still enumerated by type_members after the
        first lumping pass — found and fixed)."""
        self.doors.get(src, set()).discard(tgt)
        self.door_tags.pop((src, tgt), None)
        if hasattr(self, "door_counts"):
            self.door_counts.pop((src, tgt), None)
        self._ensure_preds()
        self.preds.get(tgt, set()).discard(src)

    def has_door(self, src, tgt):
        return tgt in self.doors.get(src, set())

    def get_doors(self, node, tag=None):
        all_t = self.doors.get(node, set())
        if tag is None:
            return all_t
        return {t for t in all_t if tag in self.door_tags.get((node, t), set())}

    def get_predecessors(self, node, tag=None):
        self._ensure_preds()
        srcs = self.preds.get(node, set())
        if tag is None:
            return set(srcs)
        return {s for s in srcs
                if tag in self.door_tags.get((s, node), set())}

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
        for k in (-2.0, -1.0, -0.5, 0.0, 0.5, 1.5):     # ONE DIAL: the
            specs.append(("pow", i, None, k))           # power family with
            # lambda=0 = log (the Box-Cox limit: (x^L-1)/L -> ln x as L->0;
            # x^0 collapses to a constant, so log IS the missing grid point
            # — owner, 2026-07-04: "isn't a log just a power? it's not
            # special." Correct: a family member, reachable by the same
            # grid-proposes/refine-sharpens machinery as every exponent.)
    for i in range(d):
        for j in range(i + 1, d):
            for k in (0.5, 1.0, 2.0):
                specs += [("cosd", i, j, k), ("sind", i, j, k)]
            for k in (0.5, 1.0, 1.5):
                specs.append(("coshd", i, j, k))
    # dedupe (2026-07-25): duplicate atoms inflate the max-over-
    # candidates null — every honest term then has to beat a taller
    # gate for no informational reason
    seen_s, out = set(), []
    for s in specs:
        if s not in seen_s:
            seen_s.add(s)
            out.append(s)
    return out


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
        base = np.maximum(np.abs(X[:, i]), 1e-9)
        if k == 0:                                # the lambda=0 limit: log
            return np.log(base)
        return np.power(base, k)
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
        return f"log(x{i})" if k == 0 else f"x{i}^{k:g}"
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
            if getattr(self, "trace_on", False):
                # the admission ledger: what stood at the gate, what
                # the gate demanded, and how the raw variables scored
                # (diagnosing where an honest half-answer dies)
                if not hasattr(self, "trace"):
                    self.trace = []
                order = np.argsort(-real)
                self.trace.append(dict(
                    round=len(self.terms), n_cand=len(cand),
                    gate=float(gate),
                    top=[(str(tuple(self.specs[a] for a in cand[int(ci)])),
                          float(real[int(ci)]))
                         for ci in order[:5]],
                    raw_vars={str(cand[int(ci)]): float(real[int(ci)])
                              for ci in range(len(cand))
                              if all(isinstance(a, (int, np.integer))
                                     and a < len(self.specs)
                                     and self.specs[a][0] == "var"
                                     for a in cand[int(ci)])
                              and len(cand[int(ci)]) == 1},
                    terms_so_far=[str(t) for t in self.terms]))
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
            # THE SUM-OF-PARTS TRIAL (2026-07-25, the additive cure —
            # receipts in the instrumented diagnostic): greedy single-
            # term admission prefers one flexible mimic (x0*x1 plus
            # cosh patches) over two humble terms it can only ever see
            # separately. Parts first: when several raw variables each
            # beat the gate, trial admitting them JOINTLY and let the
            # F-test and parsimony judge sum against product. At small
            # n where no variable beats the gate, NO RULE stays honest.
            raw_beat = sorted(
                (ci for ci, t0 in enumerate(cand)
                 if len(t0) == 1 and t0[0] < n_vars
                 and real[ci] > gate),
                key=lambda ci: -real[ci])
            if len(raw_beat) >= 2:
                joint = base + [cand[ci] for ci in raw_beat[:3]]
                self.terms = joint
                self._refit(y)
                r2t = self._train_r2(y)
                pred = self._fit_predict(y)
                trials.append(dict(
                    done=r2t >= 0.995, r2=r2t,
                    sse=float(np.sum((y - pred) ** 2)), comp=0,
                    tlen=sum(len(t0) for t0 in joint[len(base):]),
                    terms=list(joint)))
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
                  ("exp_growth", [("exp", -0.5)]),
                  ("log", [("pow", 0.0)]),
                  ("sqrt", [("pow", 0.5)])]
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

        # ── delta-compile accumulator (2026-07-22) ──────────────
        self._pair_counts = None          # (delta, frame) -> count
        self._pair_max_context = None     # counts valid for this context only
        self._counts_up_to = 0            # sequences already counted

        # ── the idea organ (2026-07-22) ─────────────────────────
        self._whole_counts = defaultdict(int)   # tuple(seq) -> lived count
        self._idea_index = {}                   # tuple(seq) -> idea node

    # ── observation ─────────────────────────────────────────────

    def observe(self, tokens):
        """Stage 1 (SENSE): tokens in, doors built, dirty set updated,
        immediate type-slotting for known categories."""
        if not tokens:
            return
        self.starts.add(tokens[0])
        self.net.set_meta(tokens[0], "start", True)
        # ── SURPRISE (owner, 2026-07-25: "surprise is a better
        # structural indicator than just sameness") — expectation is
        # read BEFORE experience is wired. Graded from his own door
        # counts: an arrival his evidence predicted is no news; an
        # arrival his evidence never saw is a unit of surprise.
        if not hasattr(self, "_seq_out_totals"):    # legacy pickles
            self._seq_out_totals = defaultdict(int)
        if not hasattr(self, "_surprise_recent"):
            self._surprise_recent = []
        dc = getattr(self.net, "door_counts", {})
        s_sum, novel = 0.0, 0
        n_tr = len(tokens) - 1
        for i in range(n_tr):
            a, b = tokens[i], tokens[i + 1]
            tot = self._seq_out_totals.get(a)
            if tot is None:
                # first sight of this source since the surprise sense
                # was built: seed expectation from his LIFETIME door
                # evidence, so history counts and novelty is honest
                tot = sum(dc.get((a, t), 0)
                          for t in self.net.get_doors(a, tag="seq"))
                self._seq_out_totals[a] = tot
            c = dc.get((a, b), 0)
            s = 1.0 if tot == 0 else 1.0 - min(1.0, c / tot)
            s_sum += s
            novel += (c == 0)
            self._seq_out_totals[a] += 1
            self.net.add_door(a, b, tag="seq")
        self._surprise_recent.append(
            (round(s_sum / n_tr, 4) if n_tr else 0.0, novel, n_tr))
        del self._surprise_recent[:-500]
        self.observed_sequences.append(list(tokens))
        if not hasattr(self, "_whole_counts"):    # legacy pickles
            self._whole_counts = defaultdict(int)
        self._whole_counts[tuple(tokens)] += 1
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

        THE LOCAL SLEEP (owner, 2026-07-22): with a scope, this is not a
        re-derivation of the world — new experience is already connected
        in; recrystallize ONLY what it touched (the dirty nodes and their
        door-neighbors), then RECONCILE with the standing registry:
        absorb what matches, supersede what changed, add what's new,
        leave the untouched net alone. Complete by construction: a
        circle's evidence only moves when a member's doors moved, and
        moved nodes ARE the scope. Without a scope: the canonical
        from-scratch rebuild, same output as ever (the predecessor
        index and holder-list closure are representation, not policy)."""
        local = bool(scope)
        scope_set = set(scope) if scope else None
        net = self.net

        prof = {}

        def P(n):
            if n not in prof:
                prof[n] = (net.get_predecessors(n, tag=tag),
                           net.get_doors(n, tag=tag))
            return prof[n]

        # Phase 1: raw circles via FCA — candidates from shared doors
        # (the empty ocean of never-sharing pairs is never touched),
        # closure via holder-list intersection (index math, not a
        # world scan). Output-identical to the classic pair scan.
        circles = []
        seen = set()

        def close_and_file(a, b):
            pa, sa = P(a)
            pb, sb = P(b)
            shared_p = pa & pb
            shared_s = sa & sb
            if len(shared_p) + len(shared_s) < min_shared:
                return
            members = None
            for p in shared_p:
                h = net.get_doors(p, tag=tag)
                members = set(h) if members is None else members & h
            for s_ in shared_s:
                h = net.get_predecessors(s_, tag=tag)
                members = set(h) if members is None else members & h
            members = {m for m in (members or set())
                       if not m.startswith("type:")}
            members |= {a, b}
            key = frozenset(members)
            if len(members) >= 2 and key not in seen:
                seen.add(key)
                circles.append({"members": members,
                                "preds": shared_p, "succs": shared_s})

        if local:
            # THE ENTRY INTERPRETER (owner, 2026-07-22): don't recompute
            # on every node — compare entries to CRYSTALS. Each dirty
            # node is scored against the standing type signatures
            # (dozens of ops), sorted into the pile it resembles, or
            # the new pile when it resembles nothing. Full crystal
            # matches ABSORB (one subset test, no pair work). Boundary
            # cases become "possibly this type plus some factor" —
            # their circle is closed against the pile's own members,
            # never the world. Misfits crystallize among themselves in
            # bounded chunks. Hundreds of thousands of pair ops become
            # dozens of crystal ops — with minute, accepted fidelity
            # loss: cross-pile pairs are found later at the
            # crystal-vs-crystal altitude, or not at all this sleep.
            pile_cap = int(self._config("crystal-pile", 64)) \
                if hasattr(self, "_config") else 64
            budget = int(self._config("entry-budget", 300)) \
                if hasattr(self, "_config") else 300
            # THE SIGNATURE INDEX: door -> crystals carrying it. An
            # entry only ever meets crystals it shares a RARE door
            # with — rarest doors first (most discriminative), hub
            # doors ejected (held by too many crystals, they testify
            # to nothing), candidates capped at the entry budget. No
            # entry processes more than a few hundred crystals, ever.
            sig_index = defaultdict(set)
            for tn, t in self.types.items():
                for d in (t["preds"] | t["succs"]):
                    sig_index[d].add(tn)

            def sig_candidates(doors_of):
                cand = set()
                for d in sorted(doors_of,
                                key=lambda x: len(sig_index.get(x, ()))):
                    ts_ = sig_index.get(d)
                    if not ts_ or len(ts_) > 50:
                        continue              # hub at crystal altitude
                    cand |= ts_
                    if len(cand) >= budget:
                        break
                return cand

            # FIRST PAST THE POST (owner, 2026-07-22): don't rank the
            # world — validate candidates as they arrive, rarest
            # shared door first, and KEEP THE FIRST FUNCTIONAL FIT
            # (proven in shape_fptp_probe: ~12 gate checks at 100k
            # crystals, quality 1.00, junk refused 100/100). A
            # candidate that fails the keep-gate but still shares
            # min_shared doors piles as a boundary case ("possibly
            # this type plus some factor"); nothing passing = the
            # new pile, an honest refusal.
            n_types = max(len(self.types), 1)

            def _idf(d):
                c = len(sig_index.get(d, ()))
                return float(np.log(1 + n_types / c)) if c else 1.0

            def _fptp(doors_of):
                kept = None
                weak, weak_sc = None, 0
                seen_c = set()
                for d in sorted(doors_of, key=lambda x: -_idf(x)):
                    ts_ = sig_index.get(d)
                    if not ts_ or len(ts_) > 50:
                        continue          # hub door: ejected
                    for tn in ts_:
                        if tn in seen_c:
                            continue
                        seen_c.add(tn)
                        t = self.types.get(tn)
                        if not t:
                            continue
                        sig = t["preds"] | t["succs"]
                        shared = doors_of & sig
                        sw = sum(_idf(x) for x in shared)
                        if sw >= 0.5 * sum(_idf(x) for x in sig):
                            return tn, tn, len(shared)   # past the post
                        if len(shared) > weak_sc:
                            weak, weak_sc = tn, len(shared)
                        if len(seen_c) >= 50:
                            return None, weak, weak_sc
                return kept, weak, weak_sc

            piles = defaultdict(list)
            misfits = []
            for n in sorted(scope_set):
                if n.startswith("type:"):
                    continue
                pn, sn = P(n)
                if not pn and not sn:
                    continue
                kept, weak, weak_sc = _fptp(pn | sn)
                if kept is not None:
                    piles[kept].append(n)
                elif weak is not None and weak_sc >= min_shared:
                    piles[weak].append(n)     # boundary: pile anyway
                else:
                    misfits.append(n)
            for tn, ns in piles.items():
                t = self.types[tn]
                absorbed = set()
                for n in ns:
                    pn, sn = P(n)
                    if t["preds"] <= pn and t["succs"] <= sn:
                        absorbed.add(n)         # carries the whole crystal
                        continue
                    shared_p = pn & t["preds"]  # boundary: partial carry
                    shared_s = sn & t["succs"]
                    if len(shared_p) + len(shared_s) < min_shared:
                        misfits.append(n)
                        continue
                    members = {m for m in sorted(t["members"])[:budget]
                               if shared_p <= P(m)[0]
                               and shared_s <= P(m)[1]} | {n}
                    key = frozenset(members)
                    if len(members) >= 2 and key not in seen:
                        seen.add(key)
                        circles.append({"members": members,
                                        "preds": shared_p,
                                        "succs": shared_s})
                if absorbed:
                    key = frozenset(t["members"] | absorbed)
                    if key not in seen:
                        seen.add(key)
                        circles.append({"members": t["members"] | absorbed,
                                        "preds": set(t["preds"]),
                                        "succs": set(t["succs"]),
                                        "absorbed_from": tn})
            # the new pile(s): misfits meet each other in bounded
            # chunks; closure stays inside the chunk (fidelity loss
            # accepted and bounded by the chunk)
            misfits = sorted(set(misfits))
            for c0 in range(0, len(misfits), pile_cap):
                chunk = misfits[c0:c0 + pile_cap]
                for i, a in enumerate(chunk):
                    pa, sa = P(a)
                    for b in chunk[i + 1:]:
                        pb, sb = P(b)
                        shared_p = pa & pb
                        shared_s = sa & sb
                        if len(shared_p) + len(shared_s) < min_shared:
                            continue
                        members = {m for m in chunk
                                   if shared_p <= P(m)[0]
                                   and shared_s <= P(m)[1]}
                        members |= {a, b}
                        key = frozenset(members)
                        if len(members) >= 2 and key not in seen:
                            seen.add(key)
                            circles.append({"members": members,
                                            "preds": shared_p,
                                            "succs": shared_s})
        else:
            nodes_all = sorted(n for n in net.all_nodes()
                               if not n.startswith("type:"))
            for i, a in enumerate(nodes_all):
                pa, sa = P(a)
                if not pa and not sa:
                    continue
                for b in nodes_all[i + 1:]:
                    close_and_file(a, b)
        nodes = sorted(n for n in net.all_nodes()
                       if not n.startswith("type:"))

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
        neg_added = set()
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
                # candidates carrying the rest of the intent = the
                # intersection of the rest-doors' holder lists (index
                # math). Local: hub doors ejected (a holder list past
                # the budget can't discriminate), candidates capped.
                cand_m = None
                hub_hit = False
                for r in rest:
                    h = self.net.get_predecessors(r, tag=tag)
                    if local and len(h) > 300:
                        hub_hit = True
                        break
                    cand_m = set(h) if cand_m is None else cand_m & h
                if hub_hit:
                    continue
                cand_list = sorted(cand_m or set())
                if local:
                    cand_list = cand_list[:300]
                for m in cand_list:
                    if m in c["members"] or m.startswith("type:"):
                        continue
                    if d in self.net.get_doors(m, tag=tag):
                        continue
                    n_m = min(counts.get((m, r), 0) for r in rest)
                    # repeatable evidence (>= 3 sightings) AND absence must
                    # beat the like-your-siblings null at 1%
                    if n_m >= 3 and (1 - p_hat) ** n_m < 0.01:
                        self.net.add_door(m, f"not_{d}", tag="neg")
                        neg_added.add(m)
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
                       "preds": set(c["preds"]), "succs": set(c["succs"]),
                       "absorbed_from": c.get("absorbed_from")}
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
                current["absorbed_from"] = None   # merged: new structure
                used.add(j)
            merged.append(current)

        # Phase 3: name and write to net.
        # Full: rebuild the registry from scratch (canonical view).
        # Local: RECONCILE — each fresh circle is checked against the
        # standing registry: near-identical and unvetoed -> absorbed
        # (modify locally); member set changed -> the old name is
        # superseded on the record, never erased; no match -> new.
        # Types the region never touched are left alone.
        def _install(c):
            name = (f"type:{'_'.join(sorted(c['members'])[:2])}"
                    f"[{len(c['members'])}]")
            c["name"] = name
            c["parent"] = None
            c["children"] = []
            self.types[name] = c
            for m in c["members"]:
                self.net.add_door(m, name, tag="type")
            return name

        if not local:
            self.types = {}
            for c in merged:
                _install(c)
            outgoing = merged
        else:
            outgoing = []
            for c in merged:
                best, best_ov = None, 0.0
                # crystal-vs-crystal, budget-bounded: a circle is only
                # compared against crystals sharing a non-hub door
                for tname in sig_candidates(c["preds"] | c["succs"]):
                    t = self.types.get(tname)
                    if not t:
                        continue
                    larger = max(len(c["members"]), len(t["members"]))
                    ov = (len(c["members"] & t["members"]) / larger
                          if larger else 0.0)
                    if ov > best_ov:
                        best, best_ov = tname, ov
                if best and best_ov >= 0.8:
                    t = self.types[best]
                    if (_pos_of(c) & _negs_of(t["members"])
                            or _pos_of(t) & _negs_of(c["members"])):
                        best = None       # positively negative: stays its own
                if best and best_ov >= 0.8:
                    t = self.types.pop(best)
                    c = {"members": t["members"] | c["members"],
                         "preds": t["preds"] & c["preds"],
                         "succs": t["succs"] & c["succs"],
                         "absorbed_from": c.get("absorbed_from")}
                    new_name = _install(c)
                    if c.get("absorbed_from") and t.get("verdict"):
                        # pure absorption: the standing verdict stands
                        c["verdict"] = t["verdict"]
                        c["score"] = t.get("score", 0)
                        self.net.set_meta(new_name, "verdict", t["verdict"])
                    if new_name != best:
                        self.net.set_meta(best, "superseded_by", new_name)
                else:
                    c["absorbed_from"] = None     # no match: judge it fresh
                    new_name = _install(c)
                for d in (c["preds"] | c["succs"]):
                    sig_index[d].add(c["name"])
                outgoing.append(c)

        # Phase 3.5 (owner's law, 2026-07-03): WRONG IS KEPT AND CLASSIFIED.
        # "knowing what is right is intelligence. knowing what is wrong is
        # wisdom." Every type is tested against its chance-null — the same
        # context with door targets shuffled (degrees preserved), scored by
        # the BEST structure chance produces (selection-corrected). Types
        # that fail are NOT deleted and NOT prevented: they are filed in
        # the wrong section with the WHY attached, so error itself becomes
        # learnable material. Downstream behavior is deliberately unchanged
        # (no pruning, no importance-weighting — the old trap).
        def _best_chance_score(edges, n_shuffles=8):
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

        if not hasattr(self, "wrong_types") or self.wrong_types is None:
            self.wrong_types = {}
        if local:
            # LIBERAL EJECTION (owner, 2026-07-22): a sleep that only
            # ABSORBED into standing crystals made no new structure —
            # the standing verdicts stand and the null has nothing to
            # judge. When something fresh did appear, the null runs on
            # a capped region and capped edge list with fewer shuffles
            # (a receipt-honest sample — the accepted fidelity trade).
            judge = [c for c in outgoing if not c.get("absorbed_from")]
            if judge:
                region = set(scope_set)
                for c in judge:
                    region |= c["members"]
                edge_nodes = sorted(n for n in region
                                    if not n.startswith("type:"))[:80]
                edges_in = [(a, t) for a in edge_nodes
                            for t in self.net.get_doors(a, tag=tag)][:200]
                chance_best = _best_chance_score(edges_in, n_shuffles=4)
            else:
                chance_best = None
        else:
            self.wrong_types = {}
            judge = outgoing
            edges_in = [(a, t) for a in nodes
                        for t in self.net.get_doors(a, tag=tag)]
            chance_best = _best_chance_score(edges_in)
        for c in judge:
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

        # Phase 4: hierarchy (subset = child). Local: only circles that
        # moved this sleep get (re)linked; standing links stand.
        type_list = list(self.types.values())
        link_from = ([c for c in outgoing if c.get("name") in self.types]
                     if local else type_list)
        for child in link_from:
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

        # Phase 5: discover rules (co-occurring predecessors).
        # pred_sets[p] is exactly p's targets under the tag — the index
        # identity that makes this cheap. Local: lazy profiles, hub
        # targets ejected, budget-capped pair work — never a scan of
        # the world.
        if local:
            psc = {}

            def ps(p):
                if p not in psc:
                    psc[p] = self.net.get_doors(p, tag=tag)
                return psc[p]

            affected = set()
            for n in scope_set:
                if len(ps(n)) >= 3:
                    affected.add(n)
                for p in P(n)[0]:
                    if 3 <= len(ps(p)) <= budget:
                        affected.add(p)
            self.rules = [r for r in (self.rules or [])
                          if r[0] not in affected and r[1] not in affected]
            have = {frozenset((a, b)) for a, b, _ in self.rules}
            checked = 0
            for a in sorted(affected):
                if checked >= budget * 3:
                    break                 # the sleep's rule budget
                bc = set()
                for t_ in sorted(ps(a), key=lambda x: len(
                        self.net.get_predecessors(x, tag=tag))):
                    hp = self.net.get_predecessors(t_, tag=tag)
                    if len(hp) > 50:
                        continue          # hub target: ejected
                    bc |= hp
                    if len(bc) >= budget:
                        break
                for b in sorted(bc):
                    if b == a or len(ps(b)) < 3:
                        continue
                    key = frozenset((a, b))
                    if key in have:
                        continue
                    have.add(key)
                    checked += 1
                    overlap = len(ps(a) & ps(b))
                    ratio_a = overlap / len(ps(a)) if ps(a) else 0
                    ratio_b = overlap / len(ps(b)) if ps(b) else 0
                    if ratio_a >= 0.8 or ratio_b >= 0.8:
                        self.rules.append(
                            (a, b, round(max(ratio_a, ratio_b), 2)))
                        self.net.add_door(a, b, tag="cooccurs")
        else:
            pred_sets = {p: self.net.get_doors(p, tag=tag) for p in nodes}
            preds = [p for p in nodes if len(pred_sets[p]) >= 3]
            self.rules = []
            for i, a in enumerate(preds):
                for b in preds[i + 1:]:
                    overlap = len(pred_sets[a] & pred_sets[b])
                    ratio_a = (overlap / len(pred_sets[a])
                               if pred_sets[a] else 0)
                    ratio_b = (overlap / len(pred_sets[b])
                               if pred_sets[b] else 0)
                    if ratio_a >= 0.8 or ratio_b >= 0.8:
                        self.rules.append(
                            (a, b, round(max(ratio_a, ratio_b), 2)))
                        self.net.add_door(a, b, tag="cooccurs")

        # Phase 6: violations (seq vs neg contrast). Local: only the
        # touched nodes and any node that just earned a negative are
        # contrasted — never the full edge list.
        if local:
            for src in sorted(set(scope_set) | neg_added):
                for tgt in net.get_doors(src):
                    tags_ = net.get_door_tags(src, tgt)
                    if "neg" in tags_ and "seq" not in tags_:
                        net.add_door(src, tgt, tag="lockout")
                        self.lockouts.add((src, tgt))
        else:
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
        """Internal: build the weight matrix from observed sequences.
        DELTA COMPILE (2026-07-22): pair counts accumulate in
        _pair_counts; only sequences newer than _counts_up_to are
        parsed, so the cost of absorbing new experience is the new
        experience — not a reparse of his whole life. Same matrix,
        exactly (the court is test_boot's delta-compile check).
        A different max_context invalidates the counts."""
        counts = getattr(self, "_pair_counts", None)
        if (counts is None
                or getattr(self, "_pair_max_context", None) != max_context
                or getattr(self, "_pair_counts_rule", 1) != 2
                or getattr(self, "_counts_up_to", 0)
                > len(self.observed_sequences)):
            counts = defaultdict(float)
            self._pair_counts = counts
            self._pair_max_context = max_context
            self._pair_counts_rule = 2      # rebuild final-only caches
            self._counts_up_to = 0
        # EVERY PREFIX IS A LESSON (2026-08-19). The old road compiled
        # only the LAST token of a sequence as a delta — so a
        # punctuated sentence taught nothing but "everything leads to
        # ." (the diagnosis campaign's mechanical wound, 0/20 on
        # punctuated lines; reproduced at day zero in the worst-case
        # baseline: "a grinth eats" -> None WITH the period, 'seeds'
        # WITHOUT it). Now each position in the sequence compiles as
        # a delta with the same frame+window treatment the final
        # position always had; the final prefix reproduces the old
        # counts exactly, interior positions only ADD.
        for seq in self.observed_sequences[self._counts_up_to:]:
            if len(seq) < 2:
                continue
            for end in range(1, len(seq)):
                frame = tuple(seq[:end])
                delta = seq[end]
                counts[(delta, frame)] += 1.0
                for width in range(2, min(len(frame) + 1, max_context)):
                    partial = frame[-width:]
                    if partial != frame:
                        counts[(delta, partial)] += 1.0
        self._counts_up_to = len(self.observed_sequences)

        if not counts:
            self._compiled = None
            self._compiled_up_to = len(self.observed_sequences)
            return None

        frames = sorted(set(f for d, f in counts))
        deltas = sorted(set(d for d, f in counts))
        fidx = {f: i for i, f in enumerate(frames)}
        didx = {d: i for i, d in enumerate(deltas)}

        W = np.zeros((len(deltas), len(frames)), dtype=np.float32)
        for (delta, frame), c in counts.items():
            W[didx[delta], fidx[frame]] = c
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

    # THE ONE-FILE BODY, v2 (2026-08-19, owner: "one file total,
    # smaller files as ram essentially for the workers"). One file,
    # sectioned inside: core (the mind, big stores emptied so every
    # cross-reference survives in one object graph), netgraph (every
    # node name stored ONCE + columnar edges — the old road stored
    # each name ~26x over), history (the activation log, compressed,
    # kept whole per keep-everything), then an append-only JOURNAL
    # TAIL: an autosave can append deltas instead of rewriting him.
    # preds is derived and never stored (rebuilt on load). Courted in
    # rebuild/onefile_probe.py before install: round trip item-for-
    # item EXACT on a real 49.4MB him -> 2.9MB (17x), torn tail
    # truncates cleanly. v1 pickles load forever (magic sniff).

    _V2_MAGIC = b"ISAAC2\x00\x01"

    @staticmethod
    def _v2_pack(obj, preset=3):
        import lzma
        import pickle
        return lzma.compress(
            pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL),
            preset=preset)

    @staticmethod
    def _v2_unpack(blob):
        import lzma
        import pickle
        return pickle.loads(lzma.decompress(blob))

    def save(self, path):
        """Snapshot the WHOLE mind — one file (the v2 sectioned body).
        (The ledger persists his science; this persists HIM.)
        WRITE-THEN-SWAP (2026-07-26, after the 602-second save and the
        silent day of death): the body is written to a side file first
        and the name swap is a single instant step — a death mid-write
        can never tear his real file. Luck is retired."""
        import hashlib
        import json
        import os
        import struct
        net = self.net
        log = getattr(self, "activation_log", [])
        aside = dict(doors=net.doors,
                     door_tags=net.door_tags,
                     door_counts=getattr(net, "door_counts",
                                         defaultdict(int)),
                     meta=net.meta,
                     preds=getattr(net, "preds", defaultdict(set)))
        try:
            net.doors = defaultdict(set)
            net.door_tags = defaultdict(set)
            net.door_counts = defaultdict(int)
            net.meta = defaultdict(dict)
            net.preds = defaultdict(set)
            self.activation_log = type(log)()
            core = self._v2_pack(self)
        finally:
            net.doors, net.door_tags = aside["doors"], aside["door_tags"]
            net.door_counts, net.meta = (aside["door_counts"],
                                         aside["meta"])
            net.preds = aside["preds"]
            self.activation_log = log

        names = set(aside["doors"].keys()) | set(aside["meta"].keys())
        for tgts in aside["doors"].values():
            names |= tgts
        for (s, t) in aside["door_tags"]:
            names.add(s)
            names.add(t)
        for (s, t) in aside["door_counts"]:
            names.add(s)
            names.add(t)
        vocab = sorted(names)
        nid = {n: i for i, n in enumerate(vocab)}
        tagsets, tagset_id = [], {}
        srcs, tgts_a, counts, tsids, seen = [], [], [], [], set()
        for s, ts in aside["doors"].items():
            for t in ts:
                srcs.append(nid[s])
                tgts_a.append(nid[t])
                counts.append(aside["door_counts"].get((s, t), 0))
                fs = frozenset(aside["door_tags"].get((s, t), set()))
                if fs not in tagset_id:
                    tagset_id[fs] = len(tagsets)
                    tagsets.append(sorted(fs))
                tsids.append(tagset_id[fs])
                seen.add((s, t))
        netgraph = self._v2_pack(dict(
            vocab=vocab, srcs=srcs, tgts=tgts_a, counts=counts,
            tsids=tsids, tagsets=tagsets,
            stray_tags=[(nid[s], nid[t], sorted(v))
                        for (s, t), v in aside["door_tags"].items()
                        if (s, t) not in seen],
            stray_counts=[(nid[s], nid[t], c)
                          for (s, t), c in aside["door_counts"].items()
                          if (s, t) not in seen],
            door_keys=[nid[s] for s in aside["doors"]],
            meta={nid[k]: v for k, v in aside["meta"].items()}))
        history = self._v2_pack(log)

        sections, off, table = [("core", core), ("netgraph", netgraph),
                                ("history", history)], 0, []
        for name, blob in sections:
            table.append(dict(name=name, off=off, len=len(blob),
                              sha=hashlib.sha256(blob).hexdigest()))
            off += len(blob)
        head = json.dumps(dict(version=2, sections=table)).encode()
        tmp = str(path) + ".writing"
        with open(tmp, "wb") as f:
            f.write(self._V2_MAGIC)
            f.write(struct.pack("<I", len(head)))
            f.write(head)
            for _, blob in sections:
                f.write(blob)
        os.replace(tmp, path)
        return path

    @staticmethod
    def load(path):
        """Resurrect a saved mind, exactly as it was. Reads both
        bodies: v2 (magic-sniffed, journal tail replayed) and the
        v1 whole-pickle — every protective .bak loads forever."""
        import pickle
        with open(path, "rb") as f:
            data = f.read()
        if data.startswith(Isaac._V2_MAGIC):
            return Isaac._load_v2(data)
        mind = pickle.loads(data)
        if not isinstance(mind, Isaac):
            raise ValueError("not an Isaac snapshot")
        return mind

    @staticmethod
    def _load_v2(data):
        import hashlib
        import json
        import struct
        p = len(Isaac._V2_MAGIC)
        (hlen,) = struct.unpack_from("<I", data, p)
        p += 4
        head = json.loads(data[p:p + hlen])
        p += hlen
        sec = {}
        for s in head["sections"]:
            blob = data[p + s["off"]: p + s["off"] + s["len"]]
            if hashlib.sha256(blob).hexdigest() != s["sha"]:
                raise ValueError(f"section {s['name']} corrupt")
            sec[s["name"]] = blob
        body_end = p + sum(s["len"] for s in head["sections"])

        mind = Isaac._v2_unpack(sec["core"])
        g = Isaac._v2_unpack(sec["netgraph"])
        vocab = g["vocab"]
        net = mind.net
        net.doors = defaultdict(set)
        net.door_tags = defaultdict(set)
        net.door_counts = defaultdict(int)
        net.meta = defaultdict(dict)
        for k in g["door_keys"]:
            net.doors[vocab[k]]          # empty-entry keys restored
        tagsets = [set(ts) for ts in g["tagsets"]]
        for s_i, t_i, c, ts_i in zip(g["srcs"], g["tgts"],
                                     g["counts"], g["tsids"]):
            s, t = vocab[s_i], vocab[t_i]
            net.doors[s].add(t)
            if tagsets[ts_i]:
                net.door_tags[(s, t)] = set(tagsets[ts_i])
            if c:
                net.door_counts[(s, t)] = c
        for s_i, t_i, tags in g["stray_tags"]:
            net.door_tags[(vocab[s_i], vocab[t_i])] = set(tags)
        for s_i, t_i, c in g["stray_counts"]:
            net.door_counts[(vocab[s_i], vocab[t_i])] = c
        for k_i, v in g["meta"].items():
            net.meta[vocab[k_i]] = v
        net.preds = defaultdict(set)     # derived: rebuilt, not stored
        for s, ts in net.doors.items():
            for t in ts:
                net.preds[t].add(s)
        mind.activation_log = Isaac._v2_unpack(sec["history"])
        Isaac._journal_replay(net, data, body_end)
        return mind

    @staticmethod
    def journal_append(path, ops):
        """Autosave without rewriting him: append delta records to
        the one file. op = ("add_door", src, tgt, tag) or
        ("set_meta", node, key, value). A torn record (death mid-
        append) is detected by checksum and cleanly ignored on load;
        the next full save() compacts the tail away."""
        import hashlib
        import pickle
        import struct
        payload = pickle.dumps(ops, protocol=pickle.HIGHEST_PROTOCOL)
        rec = (struct.pack("<I", len(payload))
               + hashlib.sha256(payload).digest()[:8] + payload)
        with open(path, "ab") as f:
            f.write(rec)

    @staticmethod
    def _journal_replay(net, data, pos):
        import hashlib
        import pickle
        import struct
        applied = 0
        while pos < len(data):
            if pos + 12 > len(data):
                break                    # torn: ignore, honestly
            (plen,) = struct.unpack_from("<I", data, pos)
            sha = data[pos + 4: pos + 12]
            payload = data[pos + 12: pos + 12 + plen]
            if (len(payload) < plen
                    or hashlib.sha256(payload).digest()[:8] != sha):
                break
            for op in pickle.loads(payload):
                if op[0] == "add_door":
                    net.add_door(op[1], op[2], tag=op[3])
                elif op[0] == "set_meta":
                    net.set_meta(op[1], op[2], op[3])
            applied += 1
            pos += 12 + plen
        return applied

    def fork(self):
        """A living branch: deep-copy this mind for counterfactual work —
        teach the fork something, see what follows, keep it or let it go.
        The original is untouched."""
        import copy
        return copy.deepcopy(self)

    # ── the boot line: shapes run the mind, code only walks ─────
    # The hard-drive principle (owner, 2026-07-22): the only thing
    # hard-coded is the entry point. The boot loop, the ingestion
    # pipeline, the queue — all shapes IN the net, readable from the
    # net, supersedable by him, receipted every step. Capability
    # belongs to code (the ops below); experience and POLICY belong
    # to the net (the flows). Change the shape, the next beat obeys.

    def define_flow(self, name, steps):
        """Author a flowchart AS NET CONTENT: flow:<name> holds the
        ordered step specs; each step:<flow>.<id> holds its own spec.
        The walker reads specs from the net — no code changes needed
        to change behavior."""
        node = f"flow:{name}"
        self.net.set_meta(node, "steps", [dict(s) for s in steps])
        if steps:
            self.net.add_door(node, f"step:{name}.{steps[0]['id']}",
                              tag="flow-start")
        for s in steps:
            snode = f"step:{name}.{s['id']}"
            self.net.set_meta(snode, "spec", dict(s))
            for d in s.get("doors", []):
                self.net.add_door(snode, f"step:{name}.{d['to']}",
                                  tag="flow-next")
        self.net.add_door("flows", node, tag="flow")
        # the CHAPTER: authorship order as a fact in the net, so
        # "the latest boot chapter" is readable, not guessed.
        ch = 1 + max([self.net.get_meta(f, "chapter") or 0
                      for f in self.net.get_doors("flows", tag="flow")]
                     or [0])
        self.net.set_meta(node, "chapter", ch)
        return node

    def branch_flow(self, src_name, new_name, replace_step=None):
        """Piecewise supersession: deep-copy the source flow's steps,
        swap in the replacement (matched by id), author the branch as
        its own flow. The source stays whole on the record."""
        import copy
        src = (src_name if str(src_name).startswith("flow:")
               else f"flow:{src_name}")
        steps = self.net.get_meta(src, "steps")
        if not steps:
            return None
        steps = copy.deepcopy(steps)
        if replace_step:
            for i, s in enumerate(steps):
                if s["id"] == replace_step["id"]:
                    steps[i] = dict(replace_step)
                    break
        node = self.define_flow(new_name, steps)
        self.net.set_meta(node, "branched_from", src)
        return node

    def _eval_when(self, when, result, state):
        """Declarative door predicate — small on purpose: equals /
        truthy / cmp-than. An unknown shape refuses, never guesses."""
        field = when.get("field")
        if isinstance(result, dict) and field in result:
            val = result.get(field)
        else:
            val = state.get(field)
        if "equals" in when:
            return val == when["equals"], f"{field}={val!r}"
        if "truthy" in when:
            ok = bool(val) == bool(when["truthy"])
            return ok, f"{field} truthy={bool(val)}"
        if "cmp" in when and "than" in when:
            than = when["than"]
            if isinstance(than, str):
                than = state.get(than, than)
            try:
                ok = (val > than if when["cmp"] == "larger"
                      else val < than)
                return ok, f"{field}={val} {when['cmp']}? {than}"
            except TypeError:
                return False, f"{field} not comparable — refused"
        return False, "unknown predicate — refused"

    def walk_flow(self, name, state=None, hop_cap=12):
        """Walk a flow shape from the net: run each step's op, take
        the first door whose predicate fires, and receipt EVERY door
        — the taken one AND each bypassed one with its reason (the
        consideration law). A missing spec or unknown op is REFUSED:
        an honest outcome with a receipt, never an exception."""
        state = state if state is not None else {}
        node = name if str(name).startswith("flow:") else f"flow:{name}"
        short = node[5:]
        trace = []
        starts = sorted(self.net.get_doors(node, tag="flow-start"))
        if not starts:
            return "refused", [dict(step=node,
                                    receipt="no flow-start — refused")]
        step, hops, outcome = starts[0], 0, None
        while step is not None and outcome is None:
            hops += 1
            if hops > hop_cap:
                trace.append(dict(step=step,
                                  receipt=f"HOP CAP {hop_cap} reached — "
                                          "returning (no runaway walks)"))
                outcome = "hop-cap"
                break
            spec = self.net.get_meta(step, "spec")
            if not spec:
                trace.append(dict(step=step, receipt="no spec — refused"))
                outcome = "refused"
                break
            op = spec.get("op")
            fn = getattr(self, op, None) if isinstance(op, str) else None
            if not callable(fn):
                trace.append(dict(step=step, op=op,
                                  receipt=f"REFUSED: no organ named "
                                          f"'{op}' — walk ends honestly"))
                outcome = "refused"
                break
            kwargs = {k: state.get(v)
                      for k, v in spec.get("args", {}).items()}
            result = fn(**kwargs)
            if not isinstance(result, dict):
                result = {"value": result}
            state[spec.get("out", f"_{spec['id']}")] = result
            rec = dict(step=step, op=op,
                       receipt=f"ran {op}; keys {sorted(result)[:6]}")
            taken, door_receipts = None, []
            for d in spec.get("doors", []):
                if "when" not in d:
                    if taken is None:
                        taken = d["to"]
                        door_receipts.append(f"-> {d['to']} (default door)")
                    else:
                        door_receipts.append(f"bypassed {d['to']}: an "
                                             "earlier door already fired")
                    continue
                fired, why = self._eval_when(d["when"], result, state)
                if fired and taken is None:
                    taken = d["to"]
                    door_receipts.append(f"-> {d['to']}: {why}")
                else:
                    door_receipts.append(f"bypassed {d['to']}: {why}")
            rec["doors"] = door_receipts
            trace.append(rec)
            step = None if taken is None else f"step:{short}.{taken}"
        if outcome is None:
            outcome = state.get("_outcome", "done")
        self.record_finding("flow-walk", node, outcome=outcome, hops=hops,
                            road=[t["step"].split(".")[-1]
                                  for t in trace if "step" in t])
        return outcome, trace

    # ── the spine: jobs and segments as net structure ───────────

    def _config(self, name, default):
        v = self.net.get_meta(f"config:{name}", "value")
        return default if v is None else v

    @staticmethod
    def _job_id(job):
        return job.get("job") if isinstance(job, dict) else job

    def ingest(self, content, kind="ingest"):
        """Take content in as a JOB on the spine — not straight into
        the net. Accepts raw text, one token list, or a list of token
        lists. What happens next is the pipeline's decision — and the
        pipeline is a shape, not this code."""
        if isinstance(content, str):
            seqs = [tokenize(line) for line in content.splitlines()]
            seqs = [s for s in seqs if s]
        elif content and isinstance(content[0], str):
            seqs = [list(content)]
        else:
            seqs = [list(s) for s in (content or []) if s]
        n = 1
        while self.net.get_meta(f"job:{n}", "state") is not None:
            n += 1
        job = f"job:{n}"
        self.net.add_door("queue:inbox", job, tag="job")
        self.net.set_meta(job, "payload", seqs)
        self.net.set_meta(job, "state", "open")
        self.net.set_meta(job, "kind", kind)
        return dict(job=job, sequences=len(seqs),
                    tokens=sum(len(s) for s in seqs))

    def q_next(self):
        """Oldest open job, marked working — but the FAST LANE first:
        jobs whose kind is in config:priority-kinds (the interactive
        ones) jump the queue, so a bulk read never blocks a reply.
        No job = an honest none."""
        pri = self._config("priority-kinds", ["/in"])
        jobs = [j for j in sorted(self.net.get_doors("queue:inbox",
                                                     tag="job"),
                                  key=lambda j: int(j.split(":")[1]))
                if self.net.get_meta(j, "state") == "open"]
        for j in jobs:
            if self.net.get_meta(j, "kind") in pri:
                self.net.set_meta(j, "state", "working")
                return dict(job=j)
        for j in jobs:
            self.net.set_meta(j, "state", "working")
            return dict(job=j)
        return dict(job=None)

    def segment_job(self, job):
        """Break a job's payload into pieces no larger than
        config:segment-size tokens — whole sequences, never split
        mid-sequence. Pieces become seg: nodes hung on the job."""
        job = self._job_id(job)
        if not job:
            return dict(segments=0, receipt="no job — nothing to do")
        payload = self.net.get_meta(job, "payload")
        if not payload:
            self.net.set_meta(job, "state", "refused")
            self.net.set_meta(job, "why", "no payload — refused, "
                                          "kept on the record")
            return dict(segments=0,
                        receipt=f"{job}: no payload — refused")
        size = self._config("segment-size", 128)
        pieces, cur, cur_n = [], [], 0
        for seq in payload:
            if cur and cur_n + len(seq) > size:
                pieces.append(cur)
                cur, cur_n = [], 0
            cur.append(seq)
            cur_n += len(seq)
        if cur:
            pieces.append(cur)
        for i, piece in enumerate(pieces):
            seg = f"seg:{job.split(':')[1]}.{i}"
            self.net.add_door(job, seg, tag="segment")
            self.net.set_meta(seg, "sequences", piece)
            self.net.set_meta(seg, "state", "segmented")
        self.net.set_meta(job, "state", "segmented")
        return dict(segments=len(pieces),
                    receipt=f"{job} -> {len(pieces)} pieces")

    def _job_segments(self, job, state=None):
        segs = sorted(self.net.get_doors(job or "", tag="segment"),
                      key=lambda s: int(s.split(".")[-1]))
        if state is None:
            return segs
        return [s for s in segs
                if self.net.get_meta(s, "state") == state]

    def crystallize_job(self, job, limit=None):
        """Each segment goes to a disposable worker — a FRESH scratch
        mind that observes the piece and runs its own consolidation
        pass. The crystal lands on the segment node as a receipt.
        The mind net is untouched until commit. With config:workers
        > 1, segments crystallize in PARALLEL PROCESSES — workers are
        stateless and never touch this mind, so the spine is race-free
        by construction (the main process is the single consumer).
        limit bounds the slice (the background lane's quantum)."""
        job = self._job_id(job)
        segs = self._job_segments(job, "segmented")
        if limit:
            segs = segs[:limit]
        nworkers = int(self._config("workers", 1))
        if nworkers > 1 and len(segs) > 1:
            from multiprocessing import Pool
            payloads = [self.net.get_meta(s, "sequences") for s in segs]
            with Pool(min(nworkers, len(segs))) as pool:
                crystals = pool.map(_crystallize_piece, payloads)
            for seg, cr in zip(segs, crystals):
                self.net.set_meta(seg, "crystal", cr)
                self.net.set_meta(seg, "state", "crystallized")
            return dict(crystallized=len(segs), workers=nworkers)
        for seg in segs:
            self.net.set_meta(seg, "crystal", _crystallize_piece(
                self.net.get_meta(seg, "sequences")))
            self.net.set_meta(seg, "state", "crystallized")
        return dict(crystallized=len(segs))

    def assess_job(self, job):
        """Mechanical comparison, no judgment: per segment, which
        tokens the mind net already holds vs which are new, and
        which sibling segments share material (kin)."""
        job = self._job_id(job)
        known = self.net.all_nodes()
        segs = self._job_segments(job)
        toks = {}
        for seg in segs:
            t = set()
            for seq in self.net.get_meta(seg, "sequences") or []:
                t |= set(seq)
            toks[seg] = t
        n = 0
        for seg in self._job_segments(job, "crystallized"):
            t = toks[seg]
            self.net.set_meta(seg, "assessment", dict(
                known=sorted(t & known)[:50],
                new=sorted(t - known)[:50],
                kin=[o for o in segs if o != seg and toks[o] & t]))
            self.net.set_meta(seg, "state", "assessed")
            n += 1
        return dict(assessed=n)

    def merge_job(self, job, limit=None):
        """Recrystallize assessed segments TOGETHER in bounded groups
        (config:merge-group): a scratch mind sees the group whole;
        its crystal is structure found BETWEEN segments that no
        single piece could show. limit bounds groups per slice."""
        job = self._job_id(job)
        group = self._config("merge-group", 4)
        segs = self._job_segments(job, "assessed")
        merges = len(self.net.get_doors(job or "", tag="merge"))
        done_groups = 0
        for i in range(0, len(segs), group):
            if limit and done_groups >= limit:
                break
            done_groups += 1
            batch = segs[i:i + group]
            worker = Isaac()
            worker.wave_logging = False
            for seg in batch:
                for seq in self.net.get_meta(seg, "sequences"):
                    worker.observe(seq)
            worker.consolidate(full=True)
            merge = f"merge:{job.split(':')[1]}.{merges}"
            self.net.add_door(job, merge, tag="merge")
            self.net.set_meta(merge, "segments", batch)
            self.net.set_meta(merge, "crystal", dict(
                nodes=worker.status()["nodes"],
                types={t: sorted(d["members"])
                       for t, d in worker.types.items()}))
            for seg in batch:
                self.net.set_meta(seg, "state", "merged")
            merges += 1
        return dict(merges=merges)

    def commit_job(self, job, limit=None):
        """THE SINGLE WRITER. Sequences enter the mind net through
        the same observe path as ever — the pipeline changes when
        and in what company content arrives, never what arrives.
        Delta compile absorbs it without reparsing history. limit
        bounds segments per slice; the job is marked done only when
        every segment has come through."""
        job = self._job_id(job)
        n_seq = 0
        segs = self._job_segments(job, "merged")
        if limit:
            segs = segs[:limit]
        mint_at = int(self._config("idea-mint", 3))
        s_mark = len(getattr(self, "_surprise_recent", []))
        for seg in segs:
            for seq in self.net.get_meta(seg, "sequences"):
                self.observe(seq)
                n_seq += 1
                key = tuple(seq)
                if (len(seq) >= 2
                        and self._whole_counts.get(key, 0) >= mint_at
                        and key not in self._ideas()):
                    self._mint_idea(list(seq))
            self.net.set_meta(seg, "state", "committed")
        # accumulate this slice's surprise into the job's ledger
        rows = getattr(self, "_surprise_recent", [])[s_mark:]
        if job and rows:
            acc = self.net.get_meta(job, "surprise") or [0.0, 0, 0]
            acc = [acc[0] + sum(r[0] * r[2] for r in rows),
                   acc[1] + sum(r[1] for r in rows),
                   acc[2] + sum(r[2] for r in rows)]
            self.net.set_meta(job, "surprise", acc)
        remaining = [s for s in self._job_segments(job)
                     if self.net.get_meta(s, "state") != "committed"]
        if job and not remaining:
            self.net.set_meta(job, "state", "done")
            acc = self.net.get_meta(job, "surprise") or [0.0, 0, 0]
            if acc[2]:
                self.record_finding(
                    "surprise", job,
                    mean=round(acc[0] / acc[2], 4),
                    novel=acc[1], transitions=acc[2])
            self.record_finding(
                "ingest", job, sequences=n_seq,
                segments=len(self._job_segments(job)))
        return dict(committed=n_seq)

    def sleep_pass(self):
        """The deep pass: scoped consolidation over what commit
        dirtied; the lumping organ runs on a metabolic interval, not
        in every merge-group sleep (2026-07-25: a ~20s global pass in
        EVERY sleep made a 5k-word read take 8+ minutes — the filed
        S1 contingency fired; interval throttle installed, and
        incremental dirty-scoped consolidation is the standing v2)."""
        self.consolidate()
        out = dict(receipt="slept")
        import time as _time
        interval = float(self._config("type-consolidate-interval-s",
                                      900))
        last = self.net.get_meta("types:last-pass", "value") or [0.0, 0]
        grown = (len(self.types) > float(last[1]) * 1.2) if last[1] \
            else True
        due = (_time.time() - float(last[0])) >= interval
        if due or grown:
            tstats = self.consolidate_types()
            self.net.set_meta("types:last-pass", "value",
                              [_time.time(), len(self.types)])
            out.update(types_active=tstats["after"],
                       types_ms=tstats["ms"])
        # the shape organ runs on its own clock, same lesson: deep
        # work belongs to sleep's rhythm, not to every merge-group
        sh_last = self.net.get_meta("shapes:last-pass", "value") or 0.0
        if (_time.time() - float(sh_last)) >= float(
                self._config("shape-interval-s", 900)):
            sstats = self.consolidate_shapes()
            self.net.set_meta("shapes:last-pass", "value", _time.time())
            out.update(shapes_total=sstats["shapes_total"],
                       shapes_ms=sstats["ms"])
        return out

    def consolidate_types(self):
        """THE LUMPING ORGAN (owner, 2026-07-24: "think engine instead
        of parts... wide net, then throw out anything that doesn't look
        useful before it gets reprocessed. I would rather know that
        everything is considered first and dismissed than just missed").

        Sleep-time global type consolidation. The mint-time court
        (0.8 overlap, best-candidate-only) lets 2-3 member shards pile
        up unmerged; this pass runs the same court WIDE: every
        co-membered pair is CONSIDERED and either merged or cheaply
        dismissed, with every dismissal counted by reason — considered-
        and-dismissed, never silently missed. The mint court's law
        carries over verbatim: a positive negative vetoes any merge
        (known-different never collapses). Nothing is erased: ejected
        and absorbed types stay on the record as superseded_by meta.

        Cost order matters: the junk court runs FIRST, because
        hub-shrapnel types are what feed the pair generator its
        quadratic blowup. Timed end to end — compression speed is a
        first-class measurement."""
        import time as _time
        t0 = _time.perf_counter()
        thresh = float(self._config("type-merge", 0.5))
        max_passes = int(self._config("type-merge-passes", 6))
        pair_cap = int(self._config("type-merge-pair-cap", 200))
        stats = dict(before=len(self.types), considered=0, merged=0,
                     contained=0, vetoed=0, low_overlap=0, ejected=0,
                     hub_members_skipped=0, passes=0,
                     ordered=0, dissolved=0, split_out=0)

        # ── junk court: hub-shrapnel eviction ──────────────────────
        # A type whose EVERY member is a hub token (seq-degree in the
        # top percentile of member degrees — self-derived, never a
        # word list) discriminates nothing: ejected from the active
        # registry, superseded on the record.
        degs = {}
        for t, d in self.types.items():
            for m in d.get("members", ()):
                if m not in degs:
                    degs[m] = len(self.net.get_doors(m, tag="seq"))
        if degs:
            vals = sorted(degs.values())
            cut = max(vals[max(0, int(len(vals) * 0.99) - 1)], 20)
            for t in list(self.types):
                mem = self.types[t].get("members", set())
                if mem and all(degs.get(m, 0) >= cut for m in mem):
                    self.types.pop(t)
                    self.net.set_meta(t, "superseded_by",
                                      "ejected:hub-shrapnel")
                    stats["ejected"] += 1

        # ── the consensus court + inversion splitter (owner,
        # 2026-07-25: "surprise is a better structural indicator than
        # just sameness"). A type's CONSENSUS is what at least half
        # its voting members' lived evidence predicts next. A large
        # type with NO consensus predicts nothing as a class — glue,
        # not category: dissolved on the record. A member whose
        # evidence misses too much of a real consensus INVERTS the
        # category: split out. Sameness joins; surprise splits.
        glue_min = int(self._config("glue-min-members", 6))
        # 0.85 chosen by sweep on his 42k-type state (2026-07-25):
        # the most aggressive bar with ZERO correct-losses on the
        # regression guard; 0.5 and 0.7 each cost one held sight.
        inv_bar = float(self._config("split-inversion", 0.85))
        hubcap = 500
        succ_cache = {}

        def _succs(m):
            if m not in succ_cache:
                sd = self.net.get_doors(m, tag="seq")
                succ_cache[m] = sd if len(sd) <= hubcap else None
            return succ_cache[m]

        from collections import Counter as _Counter
        for t in list(self.types):
            d = self.types.get(t)
            if d is None or d.get("parent"):
                continue
            mem = d.get("members", set())
            if len(mem) < 3:
                continue
            votes = _Counter()
            voters = {}
            for m in mem:
                sd = _succs(m)
                if not sd:
                    continue          # silent or hub: votes for nothing
                voters[m] = sd
                for tgt in sd:
                    votes[tgt] += 1
            consensus = {tgt for tgt, v in votes.items()
                         if v >= max(2, len(voters) / 2)}
            if not consensus:
                if len(mem) >= glue_min:
                    for m in mem:
                        self.net.remove_door(m, t)
                    self.types.pop(t)
                    self.net.set_meta(t, "superseded_by",
                                      "ejected:no-consensus")
                    stats["dissolved"] += 1
                continue
            for m, sd in voters.items():
                if len(mem) <= 2:
                    break
                inv = 1.0 - len(sd & consensus) / len(consensus)
                if inv >= inv_bar:
                    mem.discard(m)
                    self.net.remove_door(m, t)
                    stats["split_out"] += 1
            if len(mem) < 2:
                for m in mem:
                    self.net.remove_door(m, t)
                self.types.pop(t, None)
                self.net.set_meta(t, "superseded_by",
                                  "ejected:collapsed")
                stats["dissolved"] += 1

        neg_cache = {}

        def _negs(members):
            key = frozenset(members)
            if key not in neg_cache:
                out = set()
                for m in members:
                    out |= set(self.fact_index.get((m, "cannot"), []))
                    for tg in ("seq", "neg"):
                        out |= {d[4:] for d in self.net.get_doors(m, tag=tg)
                                if isinstance(d, str)
                                and d.startswith("not_")}
                neg_cache[key] = out
            return neg_cache[key]

        def _pos(d):
            return {s for s in d.get("succs", set()) or set()
                    if not (isinstance(s, str) and s.startswith("not_"))}

        # ── merge passes: wide net, cheap dismissal, to fixpoint ───
        for _ in range(max_passes):
            stats["passes"] += 1
            inv = {}
            for t, d in self.types.items():
                if d.get("parent"):
                    continue      # ordered children are structure,
                                  # not search space
                for m in d.get("members", ()):
                    inv.setdefault(m, []).append(t)
            gone = set()
            merges_this_pass = 0
            for m, ts in inv.items():
                if len(ts) > pair_cap:
                    # hub member: pairing through it is quadratic
                    # noise — skipped, and the skip is on the record
                    stats["hub_members_skipped"] += 1
                    continue
                for i in range(len(ts)):
                    a = ts[i]
                    for j in range(i + 1, len(ts)):
                        b = ts[j]
                        if (a in gone or b in gone
                                or a not in self.types
                                or b not in self.types):
                            continue
                        A, B = self.types[a], self.types[b]
                        am = A.get("members", set())
                        bm = B.get("members", set())
                        stats["considered"] += 1
                        inter = len(am & bm)
                        larger = max(len(am), len(bm))
                        if am == bm:
                            kind = "merged"       # true duplicates
                        elif am < bm or bm < am:
                            # ORDER, don't absorb (owner, 2026-07-25:
                            # "find the larger or smaller structures
                            # in a thing") — the sub/superconcept
                            # relation IS the information: wire the
                            # empty parent/children fields instead of
                            # erasing the child.
                            small, large = (a, b) if len(am) < len(bm) \
                                else (b, a)
                            Sm = self.types[small]
                            if Sm.get("parent") is None:
                                Sm["parent"] = large
                                Lg = self.types[large]
                                ch = Lg.get("children") or []
                                if small not in ch:
                                    ch.append(small)
                                Lg["children"] = ch
                                stats["ordered"] += 1
                            continue
                        elif larger and inter / larger >= thresh:
                            kind = "merged"
                        else:
                            stats["low_overlap"] += 1
                            continue
                        if (_pos(A) & _negs(bm)) or (_pos(B) & _negs(am)):
                            stats["vetoed"] += 1
                            continue
                        # merge into the larger seat; the shard is
                        # superseded on the record — and its stale
                        # member->type doors are REMOVED (dead types
                        # inflated recall until 2026-07-25)
                        seat, shard = (a, b) if len(am) >= len(bm) \
                            else (b, a)
                        S = self.types[seat]
                        H = self.types[shard]
                        S["members"] = (S.get("members", set())
                                        | H.get("members", set()))
                        S["preds"] = (S.get("preds", set()) or set()) \
                            & (H.get("preds", set()) or set())
                        S["succs"] = (S.get("succs", set()) or set()) \
                            & (H.get("succs", set()) or set())
                        for mm in H.get("members", set()):
                            self.net.add_door(mm, seat, tag="type")
                            self.net.remove_door(mm, shard)
                        for c in (H.get("children") or []):
                            if c in self.types:
                                self.types[c]["parent"] = seat
                                ch = S.get("children") or []
                                if c not in ch:
                                    ch.append(c)
                                S["children"] = ch
                        self.types.pop(shard, None)
                        self.net.set_meta(shard, "superseded_by", seat)
                        gone.add(shard)
                        stats[kind] += 1
                        merges_this_pass += 1
            if not merges_this_pass:
                break

        stats["after"] = len(self.types)
        stats["ms"] = round((_time.perf_counter() - t0) * 1000, 1)
        self.record_finding("type-consolidation", "types", **stats)
        return stats

    # ── THE SHAPE ORGAN (owner, 2026-07-26): "language is zero
    # numbers — only patterns and symbols... combination structures:
    # the core is always required, the modifiers are not. building,
    # modifying, and passing information. he needs to be able to
    # recreate these kinds of ideas."
    #
    # In sleep, lived wholes that share most of their words get laid
    # on top of each other by the comparator. Where they always
    # agree: the CORE, required. Where they differ by one swapped
    # word: an OPENING, and the words seen there are its fills.
    # Where a word is present in one whole and absent in the other:
    # an OPTIONAL opening — a flag. A lack of difference that makes
    # a difference is exactly where optionality comes from.
    # The shapes are HIS — minted from what he lived, never written
    # in. Grammar is never installed; the comparator earns it.

    @staticmethod
    def _shape_align(a, b):
        """Lay two wholes on top of each other. Returns
        ("sub", pos) if they agree everywhere but one swapped word,
        ("ins", pos) if the longer one has exactly one extra word,
        None if they are too different (the refusing null)."""
        if a == b:
            return None
        if len(a) == len(b):
            diffs = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
            return ("sub", diffs[0]) if len(diffs) == 1 else None
        if abs(len(a) - len(b)) == 1:
            longer, shorter = (a, b) if len(a) > len(b) else (b, a)
            i = 0
            while i < len(shorter) and longer[i] == shorter[i]:
                i += 1
            if longer[:i] + longer[i + 1:] == shorter:
                return ("ins", i)
        return None

    def _shapes(self):
        """The shape index (core-skeleton -> node), rebuilt lazily."""
        if not hasattr(self, "_shape_index"):
            self._shape_index = {}
        if not self._shape_index:
            for node in self.net.get_doors("shapes", tag="shape"):
                core = self.net.get_meta(node, "core")
                if core:
                    key = tuple("\x00" if c is None else c for c in core)
                    self._shape_index[key] = node
        return self._shape_index

    def _mint_shape(self, a, b, al, stats):
        kind, pos = al
        if kind == "ins" and len(a) < len(b):
            a, b = b, a
        core = list(a)
        fills = {a[pos]} if kind == "ins" else {a[pos], b[pos]}
        optional = (kind == "ins")
        core[pos] = None
        # the exactness court: the shape must rebuild both wholes it
        # came from, word for word, before it may exist
        filled = tuple(a[pos] if c is None else c for c in core)
        skipped = tuple(c for c in core if c is not None)
        other = b if kind == "ins" else \
            tuple(b[pos] if c is None else c for c in core)
        if filled != tuple(a) or (kind == "ins" and skipped != tuple(b)) \
                or (kind == "sub" and other != tuple(b)):
            stats["exact_refused"] += 1
            return
        key = tuple("\x00" if c is None else c for c in core)
        idx = self._shapes()
        node = idx.get(key)
        if node:
            ops = self.net.get_meta(node, "openings")
            ops[0]["fills"] = sorted(set(ops[0]["fills"]) | fills)
            ops[0]["optional"] = ops[0]["optional"] or optional
            self.net.set_meta(node, "openings", ops)
            for f in fills:
                self.net.add_door(node, f, tag="fill")
            stats["extended"] += 1
            return
        n = 0
        while self.net.get_meta(f"shape:{n}", "core") is not None:
            n += 1
        node = f"shape:{n}"
        self.net.set_meta(node, "core", core)
        self.net.set_meta(node, "openings",
                          [dict(pos=pos, optional=optional,
                                fills=sorted(fills))])
        self.net.add_door("shapes", node, tag="shape")
        for c in core:
            if c is not None:
                self.net.add_door(c, node, tag="shape")
        for f in fills:
            self.net.add_door(node, f, tag="fill")
        idx[key] = node
        self.record_finding("shape", node,
                            core=[c if c is not None else "_"
                                  for c in core])
        stats["minted"] += 1

    def consolidate_shapes(self):
        """The sleep pass that mints shapes: group short lived wholes
        by their rarest word, lay group-mates on top of each other,
        mint where the comparator finds core + one opening. Budgeted;
        every dismissal counted — considered and dismissed, never
        silently missed."""
        import time as _time
        t0 = _time.perf_counter()
        min_len = int(self._config("shape-min-len", 3))
        max_len = int(self._config("shape-max-len", 14))
        budget = int(self._config("shape-pairs", 200))
        stats = dict(groups=0, pairs=0, minted=0, extended=0,
                     too_different=0, exact_refused=0)
        totals = getattr(self, "_seq_out_totals", {})
        seen, uniq = set(), []
        for s in self.observed_sequences:
            t = tuple(str(w) for w in s)
            if min_len <= len(t) <= max_len and t not in seen:
                seen.add(t)
                uniq.append(t)
        groups = {}
        for s in uniq:
            anchor = min(s, key=lambda w: totals.get(w, 0))
            groups.setdefault(anchor, []).append(s)
        # the bookmark: each sleep resumes where the last one left
        # off, so the whole of his life gets its turn under the
        # comparator — never the same first pairs forever
        anchors = sorted(groups)
        cur = 0
        if anchors:
            cur = int(self.net.get_meta("shapes:cursor", "value")
                      or 0) % len(anchors)
        stopped_at = cur
        done = False
        for k in range(len(anchors)):
            anchor = anchors[(cur + k) % len(anchors)]
            grp = groups[anchor]
            if len(grp) < 2 or len(grp) > 12:
                continue
            stats["groups"] += 1
            for i in range(len(grp)):
                for j in range(i + 1, len(grp)):
                    if stats["pairs"] >= budget:
                        done = True
                        break
                    stats["pairs"] += 1
                    al = self._shape_align(grp[i], grp[j])
                    if al is None:
                        stats["too_different"] += 1
                        continue
                    self._mint_shape(grp[i], grp[j], al, stats)
                if done:
                    break
            if done:
                stopped_at = (cur + k) % len(anchors)
                break
        if anchors:
            self.net.set_meta("shapes:cursor", "value",
                              stopped_at if done else cur)
        stats["shapes_total"] = len(self._shapes())
        stats["ms"] = round((_time.perf_counter() - t0) * 1000, 1)
        self.record_finding("shape-consolidation", "shapes", **stats)
        return stats

    def _fill_legal(self, w, fills):
        """A word may fill an opening if he has seen it there, OR if
        one of his own types puts it in the same pile as a word he
        has seen there. His types are the generalizer — never a list
        we wrote."""
        if w in fills:
            return True
        fset = set(fills)
        for t in self.net.get_doors(w, tag="type"):
            d = self.types.get(t)
            if d and not d.get("parent") and d["members"] & fset:
                return True
        return False

    def recognize_shape(self, tokens):
        """Does this whole fit a shape he holds? Returns
        (shape_node, fill_word_or_None) — fill None means the
        optional opening was skipped. Never-lived wholes fit when
        the core matches and the fill is legal."""
        toks = [str(t) for t in tokens]
        cands = set()
        for t in set(toks):
            cands |= self.net.get_doors(t, tag="shape")
        for s in sorted(cands):
            core = self.net.get_meta(s, "core")
            ops = self.net.get_meta(s, "openings")
            if not core or not ops:
                continue
            pos, optional = ops[0]["pos"], ops[0]["optional"]
            fills = ops[0]["fills"]
            if len(toks) == len(core):
                ok = all(c is None or toks[i] == c
                         for i, c in enumerate(core))
                if ok and self._fill_legal(toks[pos], fills):
                    return s, toks[pos]
            if optional and len(toks) == len(core) - 1:
                if toks == [c for c in core if c is not None]:
                    return s, None
        return None, None

    def shape_complete(self, prefix):
        """THE BUILDING MOUTH: if the prefix walks into a shape he
        holds — core words matching, any opening filled legally —
        give back the rest of the core. He only completes what the
        shape itself determines: he never invents a fill."""
        toks = [str(t) for t in prefix]
        if len(toks) < 2:
            return []
        cands = set()
        for t in set(toks):
            cands |= self.net.get_doors(t, tag="shape")
        for s in sorted(cands):
            core = self.net.get_meta(s, "core")
            ops = self.net.get_meta(s, "openings")
            if not core or not ops or len(toks) >= len(core):
                continue
            pos, optional = ops[0]["pos"], ops[0]["optional"]
            fills = ops[0]["fills"]
            ok = True
            for i, w in enumerate(toks):
                c = core[i]
                if c is None:
                    if not self._fill_legal(w, fills):
                        ok = False
                        break
                elif w != c:
                    ok = False
                    break
            if not ok:
                continue
            rest = core[len(toks):]
            if None in rest:
                if not optional:
                    continue          # an unfilled required opening:
                rest = [c for c in rest if c is not None]  # skip flag
            if rest:
                return list(rest)
        return []

    def idle_pass(self):
        """Nothing waiting. An honest nothing."""
        return dict(receipt="idle — nothing waiting")

    # ── the idea organ: wholes lived enough become ONE thing ────
    # (owner, 2026-07-22: "treat entire ideas and concepts as unit
    # tokens... its a zip essentially of an idea... its just nodes
    # all the way down.") An idea is a NODE whose part-doors point at
    # what it is made of; the exact order rides as meta the way a
    # law carries its equation. Parts are kept; the idea is a view,
    # decomposable by construction. Which ideas exist is decided
    # entirely by what he has lived (config:idea-mint times).

    def _mint_idea(self, seq):
        if not hasattr(self, "_idea_index"):
            self._idea_index = {}
        n = 1
        while self.net.get_meta(f"idea:{n}", "order") is not None:
            n += 1
        node = f"idea:{n}"
        self.net.add_door("ideas", node, tag="idea")
        for t in dict.fromkeys(seq):
            self.net.add_door(node, t, tag="part")
        self.net.set_meta(node, "order", list(seq))
        self.net.set_meta(node, "count",
                          self._whole_counts.get(tuple(seq), 0))
        self._idea_index[tuple(seq)] = node
        self.record_finding("idea", node, units=len(seq))
        return node

    def _ideas(self):
        """The idea index, rebuilt lazily for legacy minds."""
        if not hasattr(self, "_idea_index"):
            self._idea_index = {}
        if not self._idea_index:
            for node in self.net.get_doors("ideas", tag="idea"):
                order = self.net.get_meta(node, "order")
                if order:
                    self._idea_index[tuple(order)] = node
        return self._idea_index

    def recognize_ideas(self, tokens):
        """Recognition: stretches matching a whole he holds collapse
        to that idea's node — a unit token. New material stays raw
        parts (he has not earned the compression). Greedy, longest
        whole first; his own lived ideas decide what compresses."""
        idx = {}
        for key, node in self._ideas().items():
            idx.setdefault(key[0], []).append((len(key), key, node))
        toks = [str(t) for t in tokens]
        out, i = [], 0
        while i < len(toks):
            best = None
            for ln, key, node in sorted(idx.get(toks[i], []),
                                        reverse=True):
                if tuple(toks[i:i + ln]) == key:
                    best = (ln, node)
                    break
            if best:
                out.append(best[1])
                i += best[0]
            else:
                out.append(toks[i])
                i += 1
        return out

    def unzip_idea(self, unit, depth=0):
        """Extraction: an idea rebuilds from its parts — recursively,
        since parts may themselves be ideas. Raw tokens pass through."""
        if depth > 6 or not str(unit).startswith("idea:"):
            return [str(unit)]
        order = self.net.get_meta(unit, "order")
        if not order:
            return [str(unit)]
        out = []
        for t in order:
            out.extend(self.unzip_idea(t, depth + 1))
        return out

    def dialog_turn(self, who, tokens):
        """THE ROLLING CONVERSATION MEMORY: the turn is recognized
        against his standing ideas, observed at unit altitude (so
        idea -> idea transitions accrue in the same matrix as
        everything else), and appended to the rolling window in
        scratch — his RAM — sized in UNITS, not tokens. The more he
        understands as wholes, the more conversation fits."""
        units = self.recognize_ideas(tokens)
        marked = [f"{who}:"] + [str(u) for u in units]
        self.observe(marked)
        win = self.scratch.read("dialog", []) or []
        win = (list(win) + marked)[
            -int(self._config("dialog-window", 24)):]
        self.scratch.write("dialog", win)
        return dict(units=len(units),
                    compressed=sum(1 for u in units
                                   if str(u).startswith("idea:")))

    def import_mind(self, path, kind="import", batch=200):
        """ANOTHER INSTANCE AS A WORKER (owner, 2026-07-23: he is
        never reset — he GROWS; "he can import different instances
        and just treat them as things to be integrated like coming
        from a worker"). The other mind is opened READ-ONLY; its
        lived sequences enter through his own spine as jobs —
        segmented, crystallized, assessed, and reconciled by his own
        pipeline. Integration, never overwrite: nothing about him
        changes except through his own commit path."""
        other = Isaac.load(path)
        seqs = [list(s) for s in
                getattr(other, "observed_sequences", []) if s]
        jobs = []
        for i in range(0, len(seqs), batch):
            jobs.append(self.ingest(seqs[i:i + batch], kind=kind))
        self.record_finding("import", str(path),
                            sequences=len(seqs), jobs=len(jobs))
        return dict(source=str(path), sequences=len(seqs),
                    jobs=[j["job"] for j in jobs])

    def seek(self, goal, state=None):
        """A TO X (owner, 2026-07-23): given where he is (state) and
        where to be (goal), HE figures out how to get there — never
        an a-to-b script. A standing plan for the goal is tried
        first. Otherwise: backward chaining over his action list's
        slot signatures, bounded by config:plan-depth, FIRST WORKABLE
        CHAIN WINS; the found route is AUTHORED AS A FLOW — his, on
        the record, supersedable — executed, and courted: did X
        actually obtain? Success stands as his answer to that goal;
        unreachable is an honest refusal with the reason named."""
        state = state if state is not None else {}
        goal = str(goal)
        plan = self.net.get_meta(f"goal:{goal}", "plan")
        if plan and self._flow_ok(plan):
            out, _ = self.walk_flow(plan, state=state)
            if out == "done" and goal in state:
                return dict(goal=goal, reached=True, flow=plan,
                            road="standing plan")
        acts = defaultdict(list)
        for a in self.net.get_doors("acts", tag="act"):
            m = self.net.get_meta(a, "spec")
            if m:
                acts[m["makes"]].append(m)
        chain, opened = [], set()

        def solve(atom, depth):
            if atom in state or any(m["makes"] == atom for m in chain):
                return True
            if depth <= 0 or atom in opened:
                return False
            opened.add(atom)
            for cand in sorted(acts.get(atom, []),
                               key=lambda m: m["op"]):
                if all(solve(t, depth - 1)
                       for t in cand.get("takes", [])):
                    chain.append(cand)      # deps solved first: ordered
                    return True
            return False

        if not solve(goal, int(self._config("plan-depth", 8))):
            self.record_finding("plan", goal, reached=False,
                                why="no chain within plan-depth")
            return dict(goal=goal, reached=False,
                        why="no chain within plan-depth — "
                            "an honest refusal")
        steps = [dict(id=m["op"], op=m["op"], args=dict(m["args"]),
                      out=m["makes"],
                      doors=([dict(to=chain[i + 1]["op"])]
                             if i + 1 < len(chain) else []))
                 for i, m in enumerate(chain)]
        n = 1
        while self.net.get_meta(f"flow:plan-{n}", "steps") is not None:
            n += 1
        flow = self.define_flow(f"plan-{n}", steps)
        out, _ = self.walk_flow(flow, state=state,
                                hop_cap=len(steps) + 2)
        reached = out == "done" and goal in state
        if reached:
            self.net.add_door("goals", f"goal:{goal}", tag="goal")
            self.net.set_meta(f"goal:{goal}", "plan", flow)
        self.record_finding("plan", goal, reached=reached, flow=flow,
                            road=[m["op"] for m in chain])
        return dict(goal=goal, reached=reached, flow=flow,
                    road=[m["op"] for m in chain])

    def work_quantum(self, max_segments=2):
        """ONE BOUNDED SLICE of background full-depth work (owner,
        2026-07-22: the interaction lane must stay fast; big reads
        grind behind it). Advances the oldest unfinished job by one
        stage-step — at most max_segments segments (or one merge
        group) per slice, with a scoped sleep after each commit
        slice — then returns, so interactive beats interleave
        between slices. Returns what it did, or idle."""
        jobs = sorted((j for j in self.net.get_doors("queue:inbox",
                                                     tag="job")),
                      key=lambda j: int(j.split(":")[1]))
        for job in jobs:
            st = self.net.get_meta(job, "state")
            if st in (None, "done", "refused"):
                continue
            if st == "open":
                self.net.set_meta(job, "state", "working")
                return dict(job=job, did="pulled")
            if st == "working":
                r = self.segment_job(job)
                return dict(job=job, did="segmented", **r)
            if self._job_segments(job, "segmented"):
                r = self.crystallize_job(job, limit=max_segments)
                return dict(job=job, did="crystallized", **r)
            if self._job_segments(job, "crystallized"):
                r = self.assess_job(job)
                return dict(job=job, did="assessed", **r)
            if self._job_segments(job, "assessed"):
                r = self.merge_job(job, limit=1)
                return dict(job=job, did="merged", **r)
            if self._job_segments(job, "merged"):
                r = self.commit_job(job, limit=max_segments)
                self.sleep_pass()          # bounded: only this slice's dirt
                return dict(job=job, did="committed", **r)
            self.net.set_meta(job, "state", "done")
            return dict(job=job, did="closed")
        return dict(did="idle")

    # ── the entry point (the only hard-coded thing) ─────────────

    def _seed_boot(self):
        """FIRST BOOT ONLY — the install. Authors the default boot
        loop and pipeline as net shapes, stamped told-structure, and
        writes THE RECOVERY SECTOR: a pristine copy of the original
        at boot:recovery, so a broken or missing redirect can always
        rebuild the first normal instance. From this moment the
        shapes are content: supersede freely."""
        import copy
        prov = "seeded 2026-07-22 (told-structure — supersede freely)"
        self.net.set_meta("config:segment-size", "value", 128)
        self.net.set_meta("config:merge-group", "value", 4)
        self.net.set_meta("config:workers", "value", 1)
        self.net.set_meta("config:crystal-pile", "value", 64)
        self.net.set_meta("config:entry-budget", "value", 300)
        self.net.set_meta("config:priority-kinds", "value", ["/in"])
        self.net.set_meta("config:idea-mint", "value", 3)
        self.net.set_meta("config:dialog-window", "value", 24)
        self.net.set_meta("config:plan-depth", "value", 8)
        self.net.set_meta("config:type-merge", "value", 0.5)
        self.net.set_meta("config:type-merge-passes", "value", 6)
        self.net.set_meta("config:type-merge-pair-cap", "value", 200)
        self.net.set_meta("config:think-budget", "value", 64)
        self.net.set_meta("config:type-consolidate-interval-s",
                          "value", 900)
        self.net.set_meta("config:split-inversion", "value", 0.85)
        self.net.set_meta("config:glue-min-members", "value", 6)
        self.net.set_meta("config:shape-interval-s", "value", 900)
        self.net.set_meta("config:shape-pairs", "value", 200)
        self.net.set_meta("config:shape-min-len", "value", 3)
        self.net.set_meta("config:shape-max-len", "value", 14)
        self.net.add_door("config", "config:plan-depth", tag="config")
        self.net.add_door("config", "config:priority-kinds", tag="config")
        self.net.add_door("config", "config:idea-mint", tag="config")
        self.net.add_door("config", "config:dialog-window", tag="config")
        self.net.add_door("config", "config:segment-size", tag="config")
        self.net.add_door("config", "config:merge-group", tag="config")
        self.net.add_door("config", "config:workers", tag="config")
        self.net.add_door("config", "config:crystal-pile", tag="config")
        self.net.add_door("config", "config:entry-budget", tag="config")
        steps = [
            dict(id="pull", op="q_next", args={}, out="pulled",
                 doors=[dict(to="segment",
                             when=dict(field="job", truthy=True)),
                        dict(to="idle")]),
            dict(id="segment", op="segment_job", args=dict(job="pulled"),
                 out="segmented",
                 doors=[dict(to="crystallize",
                             when=dict(field="segments", cmp="larger",
                                       than=0)),
                        dict(to="idle")]),
            dict(id="crystallize", op="crystallize_job",
                 args=dict(job="pulled"), out="crystals",
                 doors=[dict(to="assess")]),
            dict(id="assess", op="assess_job", args=dict(job="pulled"),
                 out="assessed", doors=[dict(to="merge")]),
            dict(id="merge", op="merge_job", args=dict(job="pulled"),
                 out="merged", doors=[dict(to="commit")]),
            dict(id="commit", op="commit_job", args=dict(job="pulled"),
                 out="committed", success=True,
                 doors=[dict(to="sleep")]),
            dict(id="sleep", op="sleep_pass", args={}, out="slept",
                 doors=[]),
            dict(id="idle", op="idle_pass", args={}, out="idled",
                 doors=[]),
        ]
        flow = self.define_flow("boot-loop", steps)
        # THE ACTION LIST (owner, 2026-07-23): capability only, as
        # bootup — each act declares its slot signature (takes /
        # makes; the walker wires args from state). ROUTES are never
        # seeded: A-to-X is his to find (seek), keep, and reuse.
        for op, args, takes, makes in [
                ("ingest", dict(content="content"), ["content"], "job"),
                ("segment_job", dict(job="job"), ["job"], "segments"),
                ("crystallize_job", dict(job="job"),
                 ["job", "segments"], "crystals"),
                ("assess_job", dict(job="job"),
                 ["job", "crystals"], "assessed"),
                ("merge_job", dict(job="job"),
                 ["job", "assessed"], "merged"),
                ("commit_job", dict(job="job"),
                 ["job", "merged"], "committed"),
                ("sleep_pass", dict(), ["committed"], "consolidated")]:
            a = f"act:{op}"
            self.net.add_door("acts", a, tag="act")
            self.net.set_meta(a, "spec", dict(op=op, args=args,
                                              takes=takes, makes=makes))
            self.net.set_meta(a, "provenance", prov)
        self.net.add_door("boot:entry", flow, tag="boot")
        self.net.set_meta("boot:entry", "current", flow)
        # THE RECOVERY SECTOR: the original, kept pristine. If every
        # redirect dangles and every boot flow breaks, this is what
        # the mind rebuilds from.
        self.net.add_door("boot:entry", "boot:recovery", tag="recovery")
        self.net.set_meta("boot:recovery", "flow", "boot-loop")
        self.net.set_meta("boot:recovery", "sector", copy.deepcopy(steps))
        for n in (flow, "boot:entry", "boot:recovery",
                  "config:segment-size", "config:merge-group"):
            self.net.set_meta(n, "provenance", prov)
        return flow

    def _flow_ok(self, node):
        """Structural health check on a flow shape: steps meta
        present, a flow-start door, and every step carrying its
        spec. (Behavioral refusals — unknown ops — are outcomes,
        not damage; this checks structure only.)"""
        if not node or not str(node).startswith("flow:"):
            return False
        steps = self.net.get_meta(node, "steps")
        if not steps or not self.net.get_doors(node, tag="flow-start"):
            return False
        short = str(node)[5:]
        return all(self.net.get_meta(f"step:{short}.{s.get('id')}",
                                     "spec") for s in steps)

    def _recover_boot(self):
        """THE RECOVERY SECTOR fires: every boot flow is missing or
        structurally broken. Rebuild the original from the pristine
        copy at boot:recovery; whatever broken steps existed are
        superseded onto the record, never erased. If even the sector
        is gone, factory-reseed — the last resort."""
        import copy
        sector = self.net.get_meta("boot:recovery", "sector")
        if not sector:
            flow = self._seed_boot()
            self.record_finding("boot-recovery", "boot:entry",
                                action="no recovery sector — "
                                       "factory reseed")
            return flow
        name = self.net.get_meta("boot:recovery", "flow") or "boot-loop"
        node = f"flow:{name}"
        broken = self.net.get_meta(node, "steps")
        if broken is not None:
            hist = self.net.get_meta(node, "superseded") or []
            hist.append(dict(steps=broken,
                             why="structurally broken at boot — "
                                 "rebuilt from the recovery sector"))
            self.net.set_meta(node, "superseded", hist)
        flow = self.define_flow(name, copy.deepcopy(sector))
        self.net.add_door("boot:entry", flow, tag="boot")
        self.net.set_meta("boot:entry", "current", flow)
        self.record_finding("boot-recovery", flow,
                            action="rebuilt from boot:recovery")
        return flow

    def beat(self, state=None):
        """ONE beat of the boot loop — THE ENTRY POINT. Reads
        boot:entry from the net and walks whatever flow it points at,
        re-read every beat, so supersession takes effect live. If the
        redirect is missing or names a broken shape, default to the
        FIRST normal instance; if none stands, rebuild from the
        recovery sector. This doorway is the only hard-coded thing;
        everything it runs is net content."""
        if not self.net.get_doors("boot:entry", tag="boot"):
            self._seed_boot()
        current = self.net.get_meta("boot:entry", "current")
        if not self._flow_ok(current):
            chapter = lambda f: (self.net.get_meta(f, "chapter") or 0,
                                 str(f))
            cands = [f for f in self.net.get_doors("boot:entry",
                                                   tag="boot")
                     if self._flow_ok(f)]
            if cands:
                fallback = max(cands, key=chapter)
                self.net.set_meta("boot:entry", "current", fallback)
                self.record_finding(
                    "boot-recovery", fallback,
                    action=f"redirect {current!r} missing or broken — "
                           "defaulted to the latest sound boot chapter")
                current = fallback
            else:
                # unconnected chapters: sound boot-lineage flows that
                # lost their door to boot:entry — found and reconnected
                orphans = [f for f in self.net.get_doors("flows",
                                                         tag="flow")
                           if self._flow_ok(f) and self._boot_lineage(f)]
                if orphans:
                    fallback = max(orphans, key=chapter)
                    self.net.add_door("boot:entry", fallback, tag="boot")
                    self.net.set_meta("boot:entry", "current", fallback)
                    self.record_finding(
                        "boot-recovery", fallback,
                        action="no connected chapter stood — found an "
                               "unconnected one and reconnected it")
                    current = fallback
                else:
                    current = self._recover_boot()
        return self.walk_flow(current, state=state)

    def _boot_lineage(self, node, limit=10):
        """Does this flow descend from the boot flow? Name match or a
        branched_from chain that reaches it within `limit` hops."""
        name = self.net.get_meta("boot:recovery", "flow") or "boot-loop"
        hops = 0
        while node and hops < limit:
            if str(node).startswith(f"flow:{name}"):
                return True
            node = self.net.get_meta(node, "branched_from")
            hops += 1
        return False

    def boot(self, beats=12):
        """The boot loop: beat until idle (or the beat budget runs
        out). Returns the last beat's outcome and receipts."""
        out, trace = None, []
        for _ in range(max(1, beats)):
            out, trace = self.beat()
            road = [t["step"].split(".")[-1] for t in trace
                    if "step" in t]
            if "idle" in road or out in ("refused", "hop-cap"):
                break
        return out, trace

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

    def discover(self, X, y, name=None, verbose=False, columns=None,
                 trace=False):
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
            ok_rows = np.isfinite(X).all(1)       # log/ratio domains: rows
            if not ok_rows.all():                 # outside a composite's
                X, y = X[ok_rows], y[ok_rows]     # domain drop out honestly
        half = len(y) // 2
        enum = _Enumerator()
        enum.trace_on = bool(trace)
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
            # ── SHAPE AND INSTANCE (owner, 2026-07-26): "x0 is not a
            # single thing, it is a variable... there are fixed atoms
            # and relational atoms — the shape of things and the
            # instance of things."
            #   RELATIONAL atom (shape): xN — the slot, the role in
            #     this form. Defined differentially: first-argument-of.
            #   FIXED atom (thing): the named quantity (temperature) —
            #     the abstracted thing itself, fused with the language
            #     concept of the same name.
            #   BINDING: slot —binds→ thing, per law (which thing
            #     plays which role in which form).
            #   INSTANCES (x0=6) are never net nodes: they live in
            #     Scratch at application time (net = true in general;
            #     scratch = true right now) — see apply_law. What the
            #     net keeps of instance populations is the REGIME on
            #     the fixed atom: {law, lo, hi, nominal, std, n} per
            #     context — range and normal ("water is 0-100; ocean
            #     ~10; heater ~55"), contexts being the regimes.
            cols = list(columns or [])
            used_idx = {int(mm) for mm in
                        re.findall(r"x(\d+)", enum.equation())}
            bindings = {}
            for vi in range(d_raw):
                slot = f"x{vi}"
                nm = cols[vi] if vi < len(cols) and cols[vi] else None
                fixed = ("_".join(tokenize(str(nm))) if nm else None)
                seat = fixed or slot          # regimes live on the thing
                col = X[:, vi]                # (or the slot if anonymous)
                regs = self.net.get_meta(seat, "regimes") or []
                regs.append(dict(law=name, lo=float(col.min()),
                                 hi=float(col.max()),
                                 nominal=float(col.mean()),
                                 std=float(col.std()),
                                 n=int(len(col))))
                self.net.set_meta(seat, "regimes", regs)
                if vi in used_idx:
                    self.net.add_door(node, slot, tag="slot")
                    self.net.add_door("variable", slot, tag="variable")
                    if fixed:
                        self.net.add_door(slot, fixed, tag="binds")
                        self.net.add_door(node, fixed, tag="uses")
                        self.net.add_door(fixed, node, tag="law")
                        bindings[slot] = fixed
            if bindings:
                self.net.set_meta(node, "bindings", bindings)
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
                    dossier=dossier, adequacy=adequacy, capture=capture,
                    trace=(getattr(enum, "trace", None) if trace
                           else None))

    def apply_law(self, name, X):
        """Apply a discovered law: the challenge, now computable.
        (Distinct from solve(), the token-problem solver.)
        Single-point application is an INSTANTIATION (owner,
        2026-07-26: shape vs instance — 'x0 should have the shape
        form of the atom as x0, and the instance of x0=6'): the
        shape stays in the net; the binding x0=6 is written into
        Scratch, where what-is-true-right-now lives."""
        m = self.net.get_meta(f"law:{name}", "model")
        d_raw = (m or {}).get("d_raw", (m or {}).get("d"))
        if m is None or np.asarray(X).shape[1] != d_raw:
            return None
        Xr = np.asarray(X, float)
        if len(Xr) == 1:
            binds = self.net.get_meta(f"law:{name}", "bindings") or {}
            for vi in range(d_raw):
                slot = f"x{vi}"
                self.scratch.write(f"{slot}@{name}", float(Xr[0, vi]))
                if slot in binds:
                    self.scratch.write(f"{binds[slot]}@{name}",
                                       float(Xr[0, vi]))
        X = self._augment_with(Xr, m.get("composites_used", []))
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
                "difference": (lambda a, b: a - b, lambda z0, ai: ai - z0),
                "ratio": (lambda a, b: np.where(np.abs(b) > 1e-9, a / b,
                                                np.nan),
                          lambda z0, ai: np.where(np.abs(z0) > 1e-9,
                                                  ai / z0, np.nan))}

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

        # COLLECTIVE probe (owner, 2026-07-04: "a strong significant
        # collective signal, but a weak individual signal" — and SIGNED:
        # "5-7 is -2, but 5--7 is 12. darkening vs brightening"). Shift
        # all drivers TOGETHER (coherently) vs one at a time vs the
        # matched null: same-size shifts with SCRAMBLED signs (breaks
        # coherence, keeps perturbation). Responses reported signed, both
        # directions — darkening and brightening are different facts.
        collective = None
        if len(main) >= 3:
            feats = sorted(int(j) for j in main)
            pad = 0.25 * (hi - lo)
            Xc = _wave_rng.uniform(0, 1, (600, d)) * (hi - lo - 2 * pad)                 + lo + pad
            fc = self._net_predict(net, Xc)

            def resp(signs, scale=1.0):
                Xs = Xc.copy()
                for k_, j in enumerate(feats):
                    Xs[:, j] = Xs[:, j] + signs[k_] * scale * pad[j]
                return float(np.mean(self._net_predict(net, Xs) - fc))

            ones = np.ones(len(feats))
            up, down = resp(ones), resp(-ones)
            indiv = []
            for k_, j in enumerate(feats):
                e = np.zeros(len(feats)); e[k_] = 1.0
                indiv.append(max(abs(resp(e)), abs(resp(-e))))
            max_indiv = max(indiv)
            scrambled = []
            for _ in range(12):
                sgn = _wave_rng.choice([-1.0, 1.0], len(feats))
                scrambled.append(max(abs(resp(sgn)), abs(resp(-sgn))))
            strength = max(abs(up), abs(down))
            if strength > max(scrambled) and strength > 2 * max_indiv:
                collective = dict(
                    features=feats, up=round(up, 3), down=round(down, 3),
                    ratio=round(strength / max(max_indiv, 1e-9), 1),
                    null=round(max(scrambled), 3))
                self.register_composite(
                    "mean", feats,
                    provenance=f"collective probe of x:{name}")

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
                f"{names_[i]}{ {'product': '*', 'sum': '+', 'difference': '-', 'ratio': '/'}[c['through']] }{names_[j]} "
                f"ONLY (invariance {c['invariance']:.2f}, beats its null "
                f"{c['null_best']:.2f}); along that axis the response is "
                f"{c['shape']}"
                + (f", roughly {c['freq_estimate']} rad/unit"
                   if c["freq_estimate"] else ""))
        if collective:
            k_ = len(collective["features"])
            dirword = ("rises" if collective["up"] > 0 else "falls")
            lines.append(
                f"the {k_} drivers move TOGETHER: a coherent shift up moves "
                f"the response {collective['up']:+.2f} and a coherent shift "
                f"down moves it {collective['down']:+.2f} (signed — "
                f"brightening and darkening are different facts); the "
                f"collective is {collective['ratio']}x any single feature "
                f"and beats sign-scrambled shifts ({collective['null']:.2f})"
                f" — the response {dirword} with the group's common mode")
        if not lines:
            lines.append("no gated heuristic survived — the capture is "
                         "real but structureless to these probes")
        for c in composites:
            self.register_composite(
                c["through"], c["features"],
                provenance=f"interrogation of x:{name}")
        heur = dict(drivers=drivers, collective=collective, interactions={
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
                 "difference": (lambda a, b: a - b, "-"),
                 "ratio": (lambda a, b: np.where(np.abs(b) > 1e-9,
                                                 a / np.where(b == 0, 1, b),
                                                 np.nan), "/")}

    def register_composite(self, op, features, provenance=""):
        """Mint a combination as a first-class node. Idempotent."""
        features = [int(f) for f in features]
        if op == "mean":                          # collective coordinate
            cname = "mean(" + ",".join(f"x{f}" for f in features) + ")"
        elif op == "log":                         # arity-1 transform:
            cname = f"log(x{features[0]})"        # domain-guarded (x > 0)
        else:
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
            if c["op"] == "mean":                 # a COLLECTIVE coordinate
                cols.append(X[:, c["features"]].mean(1))
            elif c["op"] == "log":                # domain-guarded transform
                v = X[:, c["features"][0]]
                with np.errstate(divide="ignore", invalid="ignore"):
                    cols.append(np.where(v > 1e-12, np.log(
                        np.where(v > 1e-12, v, 1.0)), np.nan))
            else:
                i, j = c["features"][0], c["features"][1]
                with np.errstate(divide="ignore", invalid="ignore"):
                    cols.append(
                        self._COMP_OPS[c["op"]][0](X[:, i], X[:, j]))
        return np.column_stack([X] + cols) if cols else X

    def _applicable_composites(self, d):
        # ops the CURRENT engine cannot compute are skipped, never
        # crashed on (2026-07-26: his lived history carries a
        # 'powerprod' composite from an earlier era — it stays on the
        # record but is not offered to the basis; found when the
        # first live multi-column discovery KeyError'd on it)
        return [c for c in self.composites
                if max(c["features"]) < d
                and (c["op"] in self._COMP_OPS
                     or c["op"] in ("mean", "log"))
                and (len(c["features"]) == 2
                     or c["op"] in ("mean", "log"))]

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
              "difference": (lambda a, b: a - b, "-"),
              "ratio": (lambda a, b: a / np.where(np.abs(b) > 1e-9, b,
                                                  np.nan), "/")}[
            best["through"]]
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
            # liveness: only types that still exist in the registry
            # (superseded/dissolved names must not haunt recall);
            # altitude: substitution consults ROOT engines — ordered
            # children are reachable structure, not search space.
            all_ts = [t for t in self.net.get_doors(token, tag="type")
                      if t in self.types]
            roots = [t for t in all_ts
                     if self.types[t].get("parent") is None]
            types = roots or all_ts
            successors = self.net.get_doors(token, tag="seq")
            predecessors = self.net.get_predecessors(token, tag="seq")
            # Tokens with rich profiles are well-known.
            # Tokens with empty profiles are novel/unknown.
            # a type's members ARE its type-tagged predecessors — the
            # index answers in O(members), not O(world × types). Huge
            # types are capped at the entry budget (liberal ejection:
            # substitution over hundreds of siblings isn't recall).
            type_members = set()
            for t in types:
                type_members |= self.net.get_predecessors(t, tag="type")
            type_members.discard(token)
            if len(type_members) > 300:
                type_members = set(sorted(type_members)[:300])
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
            # with type members from related known tokens.
            # BUDGETED (owner's speed doctrine, 2026-07-24): liberal
            # search, but bounded — the ladder returns its honest
            # best-so-far instead of burning the whole member union.
            if verdict.get("try_type_substitution"):
                budget = int(self._config("think-budget", 64))
                trials = 0
                found = False
                for i, token in enumerate(context):
                    if trials >= budget:
                        break
                    members = knowledge.get(token, {}).get("type_members", set())
                    for member in sorted(members):
                        if trials >= budget:
                            break
                        trial = list(context)
                        trial[i] = member
                        trial_key = tuple(trial)
                        if trial_key not in tried:
                            tried.add(trial_key)
                            trials += 1
                            answer, conf = self._route(trial, mode, target)
                            if conf > best_conf:
                                best_answer, best_conf = answer, conf
                            if conf >= CONFIDENCE_THRESHOLD:
                                return answer, conf
                            found = True
                if found and trials < budget:
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
        Routes through the think loop — recall, process, evaluate.
        THE STRANGER GUARD (2026-08-19): if a context token has NEVER
        been observed, no frame can honestly answer about it — the
        every-prefix compile's window frames would otherwise fill
        "a wug is an ___" with the population answer. A question
        about a stranger gets the shrug it deserves (courted in the
        worst-case baseline's unknown-word honesty check)."""
        for tok in context:
            if tok not in self.net.doors and tok not in self.net.preds:
                return None, 0.0
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


def _crystallize_piece(sequences):
    """The disposable worker, module-level so it can run in a separate
    PROCESS (Windows spawn imports by name): a fresh scratch mind
    observes one segment, consolidates, returns the crystal as a plain
    dict. Stateless — it never sees the real mind."""
    w = Isaac()
    w.wave_logging = False
    for seq in sequences:
        w.observe(seq)
    w.consolidate(full=True)
    st = w.status()
    return dict(nodes=st["nodes"], doors=st["doors"],
                types={t: sorted(d["members"])
                       for t, d in w.types.items()},
                rules=len(w.rules))


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


def test_boot():
    """The boot line: shapes run the mind, code only walks. Only the
    entry point is hard-coded — loop, pipeline, queue are net content."""
    _div("BOOT — the boot line: shapes run the mind, code only walks")
    correct = 0

    # 1. first boot seeds the shapes, readable from the net
    isaac = Isaac()
    isaac.wave_logging = False
    out, _ = isaac.beat()
    steps = isaac.net.get_meta("flow:boot-loop", "steps")
    ok = steps is not None and out == "done"
    correct += ok
    print(f"  {'✓' if ok else '✗'}  first boot seeds flow:boot-loop "
          f"({len(steps or [])} steps in net meta), idle beat -> {out}")

    # 2. the exactness court: pipeline vs direct observe
    lines = ["the cat sat on the mat", "the cat sat on the mat",
             "the dog ran to the gate", "3 + 4 = 7"]
    isaac.ingest("\n".join(lines), kind="battery")
    isaac.boot(beats=6)
    control = Isaac()
    control.wave_logging = False
    for ln in lines:
        control.observe(tokenize(ln))
    a1, c1 = isaac.lookup(tokenize("the cat sat on the"))
    a2, c2 = control.lookup(tokenize("the cat sat on the"))
    ok = a1 == a2 == "mat" and abs(c1 - c2) < 1e-9
    correct += ok
    print(f"  {'✓' if ok else '✗'}  pipeline lookup == direct lookup "
          f"-> {a1} (conf {c1:.1f} vs {c2:.1f})")
    ok = (isaac._compiled is not None and control._compiled is not None
          and np.array_equal(isaac._compiled["W"], control._compiled["W"])
          and isaac._compiled["frames"] == control._compiled["frames"]
          and isaac._compiled["deltas"] == control._compiled["deltas"])
    correct += ok
    print(f"  {'✓' if ok else '✗'}  W matrices machine-identical "
          f"(shape {isaac._compiled['W'].shape})")
    ok = (isaac.net.get_meta("job:1", "state") == "done"
          and isaac.net.get_meta("seg:1.0", "crystal") is not None
          and isaac.net.get_meta("seg:1.0", "assessment") is not None)
    correct += ok
    print(f"  {'✓' if ok else '✗'}  job done with crystal + assessment "
          f"receipts on the record")

    # 3. the delta-compile court: interleaved vs one-shot
    rng = np.random.default_rng(7)
    A, B = Isaac(), Isaac()
    A.wave_logging = B.wave_logging = False
    vocab = [f"w{i}" for i in range(12)]
    seqs = [[vocab[int(rng.integers(0, 12))]
             for _ in range(int(rng.integers(2, 9)))] for _ in range(40)]
    for s in seqs:
        A.observe(s)
        if rng.random() < 0.5:
            A.lookup(s[:-1])          # forces a delta compile mid-stream
    for s in seqs:
        B.observe(s)
    A._ensure_compiled()
    B._ensure_compiled()
    ok = (np.array_equal(A._compiled["W"], B._compiled["W"])
          and A._compiled["frames"] == B._compiled["frames"]
          and A._compiled["deltas"] == B._compiled["deltas"])
    correct += ok
    print(f"  {'✓' if ok else '✗'}  delta compile == one-shot compile "
          f"({len(A._compiled['frames'])} frames, machine-identical)")

    # 4. null: a scrambled flow (unknown op) must refuse, not crash
    isaac.define_flow("scrambled",
                      [dict(id="x", op="no_such_organ", args={},
                            doors=[])])
    out, tr = isaac.walk_flow("scrambled")
    ok = out == "refused" and "REFUSED" in tr[-1]["receipt"]
    correct += ok
    print(f"  {'✓' if ok else '✗'}  scrambled flow -> {out} with receipt "
          f"(no exception)")

    # 5. null: a payload-less job files refused and stays on the record
    isaac.net.add_door("queue:inbox", "job:999", tag="job")
    isaac.net.set_meta("job:999", "state", "open")
    out, _ = isaac.beat()
    ok = (isaac.net.get_meta("job:999", "state") == "refused"
          and isaac.net.get_meta("job:999", "why") is not None
          and out == "done")
    correct += ok
    print(f"  {'✓' if ok else '✗'}  empty job -> refused, reason kept, "
          f"loop unharmed")

    # 6. the supersession court: repoint boot:entry, next beat obeys
    isaac.branch_flow("boot-loop", "boot-loop-v2",
                      replace_step=dict(id="sleep", op="idle_pass",
                                        args={}, out="slept", doors=[]))
    isaac.net.add_door("boot:entry", "flow:boot-loop-v2", tag="boot")
    isaac.net.set_meta("boot:entry", "current", "flow:boot-loop-v2")
    isaac.ingest("a b c", kind="battery2")
    out, tr = isaac.beat()
    road = [t["step"] for t in tr if "step" in t]
    ok = (road and road[0].startswith("step:boot-loop-v2.")
          and isaac.net.get_meta("flow:boot-loop", "steps") is not None)
    correct += ok
    print(f"  {'✓' if ok else '✗'}  superseded mid-run: next beat walks "
          f"boot-loop-v2; the old flow stays whole")

    # 7. hop cap: a circular flow ends, never hangs
    isaac.define_flow("circle", [
        dict(id="a", op="idle_pass", args={}, doors=[dict(to="b")]),
        dict(id="b", op="idle_pass", args={}, doors=[dict(to="a")])])
    out, _ = isaac.walk_flow("circle")
    ok = out == "hop-cap"
    correct += ok
    print(f"  {'✓' if ok else '✗'}  circular flow -> {out}")

    # 8. recovery: a dangling redirect defaults to the LATEST sound
    #    boot chapter, with a receipt
    isaac.net.set_meta("boot:entry", "current", "flow:does-not-exist")
    out, _ = isaac.beat()
    cur = isaac.net.get_meta("boot:entry", "current")
    ok = (out == "done" and cur == "flow:boot-loop-v2"
          and any(f.get("kind") == "boot-recovery"
                  for f in isaac.findings))
    correct += ok
    print(f"  {'✓' if ok else '✗'}  dangling redirect -> latest sound "
          f"chapter {cur} [{out}], receipt on the record")

    # 9. recovery: connected chapters all broken, but a sound
    #    UNCONNECTED chapter exists -> found and reconnected
    isaac.branch_flow("boot-loop-v2", "boot-loop-v3")   # no boot door
    isaac.net.set_meta("flow:boot-loop", "steps",
                       [dict(id="x", op="gone")])       # broken shape
    isaac.net.set_meta("flow:boot-loop-v2", "steps", None)  # missing
    isaac.net.set_meta("boot:entry", "current", None)
    out, _ = isaac.beat()
    cur = isaac.net.get_meta("boot:entry", "current")
    ok = (out == "done" and cur == "flow:boot-loop-v3"
          and "flow:boot-loop-v3" in isaac.net.get_doors("boot:entry",
                                                         tag="boot"))
    correct += ok
    print(f"  {'✓' if ok else '✗'}  unconnected chapter found and "
          f"reconnected -> {cur} [{out}]")

    # 10. every chapter everywhere broken -> rebuilt from the
    #     recovery sector; the wreckage superseded, never erased
    isaac.net.set_meta("flow:boot-loop-v3", "steps", None)
    isaac.net.set_meta("boot:entry", "current", None)
    out, _ = isaac.beat()
    steps2 = isaac.net.get_meta("flow:boot-loop", "steps")
    hist = isaac.net.get_meta("flow:boot-loop", "superseded") or []
    ok = (out == "done" and steps2 and len(steps2) == 8
          and steps2[0]["id"] == "pull"
          and hist and hist[-1]["steps"][0]["id"] == "x")
    correct += ok
    print(f"  {'✓' if ok else '✗'}  all chapters broken -> rebuilt from "
          f"boot:recovery ({len(steps2 or [])} steps), wreckage "
          f"superseded ({len(hist)} kept)")

    # 11. the pristine sector survives its own use
    sector = isaac.net.get_meta("boot:recovery", "sector")
    ok = (sector and len(sector) == 8 and sector[0]["id"] == "pull"
          and isaac.net.get_meta("boot:recovery", "provenance")
          is not None)
    correct += ok
    print(f"  {'✓' if ok else '✗'}  recovery sector still pristine "
          f"after the rebuild")

    # 12. the fast lane: an /in job jumps a queued bulk job
    isaac2 = Isaac()
    isaac2.wave_logging = False
    isaac2.beat()
    bulk = isaac2.ingest("x y z\n" * 40, kind="/file")["job"]
    fast = isaac2.ingest(["hello", "there"], kind="/in")["job"]
    pulled = isaac2.q_next()["job"]
    ok = pulled == fast and isaac2.net.get_meta(bulk, "state") == "open"
    correct += ok
    print(f"  {'✓' if ok else '✗'}  fast lane: pulled {pulled} ahead of "
          f"bulk {bulk}")

    # 13. the background quantum: bounded slices finish the bulk job
    isaac2.net.set_meta(fast, "state", "done")   # clear the fast job
    slices = 0
    while (isaac2.net.get_meta(bulk, "state") != "done"
           and slices < 200):
        isaac2.work_quantum()
        slices += 1
    ok = (isaac2.net.get_meta(bulk, "state") == "done"
          and slices > 3
          and isaac2.lookup(["x", "y"])[0] == "z")
    correct += ok
    print(f"  {'✓' if ok else '✗'}  bulk job done in {slices} bounded "
          f"quanta; content answers -> "
          f"{isaac2.lookup(['x', 'y'])[0]}")

    # 14. the idea organ: a whole lived 3x becomes ONE thing; a
    #     once-lived whole must NOT (the null that refuses)
    isaac3 = Isaac()
    isaac3.wave_logging = False
    isaac3.beat()
    for _ in range(3):
        isaac3.ingest("the tide returns to the shore", kind="life")
    isaac3.ingest("a stranger passed only once", kind="life")
    isaac3.boot(beats=10)
    ideas = isaac3.net.get_doors("ideas", tag="idea")
    minted = [i for i in ideas if "tide" in
              (isaac3.net.get_meta(i, "order") or [])]
    once = [i for i in ideas if "stranger" in
            (isaac3.net.get_meta(i, "order") or [])]
    ok = len(minted) == 1 and not once
    correct += ok
    print(f"  {'✓' if ok else '✗'}  lived x3 -> minted {minted}; "
          f"lived once -> refused ({len(once)} minted)")

    # 15. the zip: part-doors + order; round-trip machine-exact
    idea = minted[0] if minted else None
    order = isaac3.net.get_meta(idea, "order") if idea else None
    parts = isaac3.net.get_doors(idea, tag="part") if idea else set()
    rebuilt = isaac3.unzip_idea(idea) if idea else []
    ok = (order == ["the", "tide", "returns", "to", "the", "shore"]
          and parts == set(order) and rebuilt == order)
    correct += ok
    print(f"  {'✓' if ok else '✗'}  the zip: {len(parts)} part-doors, "
          f"round-trip rebuild exact -> {' '.join(rebuilt)}")

    # 16. recognition + the rolling window: the known whole collapses
    #     to ONE unit; raw stays raw; the window holds units
    r = isaac3.dialog_turn(
        "you", "yesterday the tide returns to the shore again".split())
    win = isaac3.scratch.read("dialog")
    ok = (r["compressed"] == 1 and r["units"] == 3
          and any(str(u).startswith("idea:") for u in win))
    correct += ok
    print(f"  {'✓' if ok else '✗'}  recognition: 8 tokens -> "
          f"{r['units']} units ({r['compressed']} compressed); "
          f"window carries the idea as one slot")

    # 17. A TO X: he finds the road himself — from raw content to a
    #     committed net, no route seeded, only the action list
    isaac4 = Isaac()
    isaac4.wave_logging = False
    isaac4.beat()
    r = isaac4.seek("committed",
                    state=dict(content="x y z\nx y z\nx y z"))
    ok = (r["reached"] and r["road"] == [
        "ingest", "segment_job", "crystallize_job", "assess_job",
        "merge_job", "commit_job"]
        and isaac4.lookup(["x", "y"])[0] == "z")
    correct += ok
    print(f"  {'✓' if ok else '✗'}  A->X: found {' > '.join(r.get('road', []))} "
          f"-> reached={r['reached']}, content answers")

    # 18. the unreachable goal refuses honestly
    r2 = isaac4.seek("unobtainium", state=dict(content="a b"))
    ok = not r2["reached"] and "refusal" in r2.get("why", "")
    correct += ok
    print(f"  {'✓' if ok else '✗'}  unreachable goal -> "
          f"{r2.get('why', '')[:46]}")

    # 19. selection: a planted dead-end act (sorts first) must be
    #     bypassed for the workable road
    isaac4.net.add_door("acts", "act:aaa_teleport", tag="act")
    isaac4.net.set_meta("act:aaa_teleport", "spec",
                        dict(op="aaa_teleport", args={},
                             takes=["unobtainium"], makes="committed"))
    r3 = isaac4.seek("committed",
                     state=dict(content="p q r\np q r\np q r"))
    ok = (r3["reached"] and r3.get("road") == "standing plan"
          or (isinstance(r3.get("road"), list)
              and "aaa_teleport" not in r3["road"]))
    correct += ok
    print(f"  {'✓' if ok else '✗'}  dead-end act bypassed -> "
          f"road={r3.get('road') if not isinstance(r3.get('road'), list) else ' > '.join(r3['road'])}")

    # 20. reuse: the found road STANDS — second seek walks the
    #     standing plan, no fresh search
    ok = r3.get("road") == "standing plan" and r3["reached"]
    correct += ok
    print(f"  {'✓' if ok else '✗'}  second seek used the standing "
          f"plan (searched once, owned after)")

    # 23. import: another instance integrates as a worker — through
    #     his own pipeline, never overwritten onto him
    import os as _os
    donor = Isaac()
    donor.wave_logging = False
    for _ in range(2):
        donor.observe(["gold", "under", "the", "hill"])
    pth = "._import_test.isaac"
    donor.save(pth)
    isaac5 = Isaac()
    isaac5.wave_logging = False
    isaac5.beat()
    r = isaac5.import_mind(pth)
    isaac5.boot(beats=10)
    ok = (r["sequences"] == 2
          and isaac5.lookup(["gold", "under", "the"])[0] == "hill"
          and any(f.get("kind") == "import" for f in isaac5.findings))
    correct += ok
    print(f"  {'✓' if ok else '✗'}  imported a donor mind as a worker "
          f"({r['sequences']} sequences) -> his pipeline integrated it, "
          f"content answers")
    try:
        _os.remove(pth)
    except OSError:
        pass

    print(f"\n  {correct}/23")
    return correct == 23


# ═════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════

def test_consolidation():
    _div("15. SPLIT/GROUP — surprise splits, sameness joins, "
         "containment orders")
    z = Isaac()
    z.wave_logging = False

    def mk(name, members, succs=None):
        z.types[name] = dict(members=set(members), preds=set(),
                             succs=set(succs or ()), name=name,
                             parent=None, children=[])
        for m in members:
            z.net.add_door(m, name, tag="type")

    # surprisal: novelty is maximal once, then evidence absorbs it
    z.observe(["cat", "sat", "mat"])
    s_first = z._surprise_recent[-1]
    z.observe(["cat", "sat", "mat"])
    s_second = z._surprise_recent[-1]
    okA = s_first[0] == 1.0 and s_second[0] < 0.01
    print(f"  {'✓' if okA else '✗'}  surprisal: first pass "
          f"{s_first[0]}, repeat {s_second[0]} (novelty absorbed)")

    # containment ORDERS (parent/child wired), overlap merges
    mk("type:alpha_beta[2]", ["alpha", "beta"])
    mk("type:alpha_gamma[3]", ["alpha", "beta", "gamma"])
    # the null that must refuse: disjoint stays its own thing
    mk("type:xray_yankee[2]", ["xray", "yankee"])
    # the veto that must hold: known-different never collapses
    mk("type:robin_sparrow[2]", ["robin", "sparrow"], succs=["fly"])
    mk("type:penguin_robin[2]", ["penguin", "robin"])
    z.teach("penguin", "cannot", "fly")
    # glue: many members, no shared prediction -> dissolve
    for i, g in enumerate(["g1", "g2", "g3", "g4", "g5", "g6"]):
        z.net.add_door(g, f"x{i}", tag="seq")
    mk("type:g1_g2[6]", ["g1", "g2", "g3", "g4", "g5", "g6"])
    # inversion: three members predict {fast, far}; quack doesn't
    for v in ("run", "walk", "sit"):
        z.net.add_door(v, "fast", tag="seq")
        z.net.add_door(v, "far", tag="seq")
    z.net.add_door("quack", "pond", tag="seq")
    mk("type:run_walk[4]", ["run", "walk", "sit", "quack"])
    # true duplicates still merge (stale doors must leave recall)
    mk("type:p_q[2]", ["papa", "quebec"])
    mk("type:p_q_dup[2]", ["papa", "quebec"])

    stats = z.consolidate_types()

    child = z.types.get("type:alpha_beta[2]")
    parent = z.types.get("type:alpha_gamma[3]")
    ok1 = (child is not None and parent is not None
           and child.get("parent") == "type:alpha_gamma[3]"
           and "type:alpha_beta[2]" in (parent.get("children") or []))
    print(f"  {'✓' if ok1 else '✗'}  containment ORDERED, not "
          f"absorbed: child kept, parent/children wired "
          f"(ordered={stats['ordered']})")
    ok2 = "type:xray_yankee[2]" in z.types
    print(f"  {'✓' if ok2 else '✗'}  disjoint type refused (the null)")
    ok3 = ("type:robin_sparrow[2]" in z.types
           and "type:penguin_robin[2]" in z.types)
    print(f"  {'✓' if ok3 else '✗'}  positive negative held "
          f"(vetoed={stats['vetoed']})")
    ok4 = ("type:g1_g2[6]" not in z.types
           and z.net.get_meta("type:g1_g2[6]", "superseded_by")
           == "ejected:no-consensus"
           and "type:g1_g2[6]" not in z.net.get_doors("g1", tag="type"))
    print(f"  {'✓' if ok4 else '✗'}  glue dissolved: no consensus, "
          f"no prediction, doors removed (dissolved="
          f"{stats['dissolved']})")
    verbs = z.types.get("type:run_walk[4]")
    ok5 = (verbs is not None and "quack" not in verbs["members"]
           and "run" in verbs["members"]
           and "type:run_walk[4]" not in
           z.net.get_doors("quack", tag="type"))
    print(f"  {'✓' if ok5 else '✗'}  inversion split: quack out of "
          f"the run/walk/sit type (split_out={stats['split_out']})")
    dup_alive = [t for t in ("type:p_q[2]", "type:p_q_dup[2]")
                 if t in z.types]
    dead = [t for t in ("type:p_q[2]", "type:p_q_dup[2]")
            if t not in z.types]
    ok6 = (len(dup_alive) == 1 and len(dead) == 1
           and dead[0] not in z.net.get_doors("papa", tag="type"))
    print(f"  {'✓' if ok6 else '✗'}  duplicates merged AND stale "
          f"member->type door removed from recall")
    fnd = [f for f in z.findings
           if f.get("kind") == "type-consolidation"]
    ok7 = bool(fnd) and stats["ms"] >= 0
    print(f"  {'✓' if ok7 else '✗'}  receipts + clock filed "
          f"({stats['before']} -> {stats['after']}, "
          f"{stats['ms']}ms)")
    return all([okA, ok1, ok2, ok3, ok4, ok5, ok6, ok7])


def test_atoms():
    _div("16. VARIABLE ATOMS — quantities are nodes with range+nominal")
    z = Isaac()
    z.wave_logging = False
    X = np.linspace(1, 10, 40).reshape(-1, 1)
    z.discover(X, 3.0 * X[:, 0], name="springs",
               columns=["temperature"])
    ok1 = ("temperature" in z.net.get_doors("law:springs", tag="uses")
           and "x0" in z.net.get_doors("law:springs", tag="slot")
           and "temperature" in z.net.get_doors("x0", tag="binds")
           and (z.net.get_meta("law:springs", "bindings")
                or {}).get("x0") == "temperature")
    print(f"  {'✓' if ok1 else '✗'}  shape and instance wired: slot x0 "
          f"(relational atom) binds the thing (fixed atom)")
    regs = z.net.get_meta("temperature", "regimes") or []
    ok2 = (len(regs) == 1 and regs[0]["lo"] == 1.0
           and regs[0]["hi"] == 10.0
           and 5.0 < regs[0]["nominal"] < 6.0)
    print(f"  {'✓' if ok2 else '✗'}  regime filed: range 1-10, "
          f"nominal ~5.5 ({regs and regs[0]})")
    z.discover(X, X[:, 0] ** 2, name="areas", columns=["temperature"])
    regs2 = z.net.get_meta("temperature", "regimes") or []
    laws_on = z.net.get_doors("temperature", tag="law")
    ok3 = (len(regs2) == 2
           and {"law:springs", "law:areas"} <= set(laws_on))
    print(f"  {'✓' if ok3 else '✗'}  second context ACCUMULATES on the "
          f"same atom (regimes={len(regs2)}, laws={sorted(laws_on)})")
    z.observe(tokenize("the temperature rises in the kettle"))
    succ = z.net.get_doors("temperature", tag="seq")
    ok4 = "rises" in succ and "law:springs" in laws_on
    print(f"  {'✓' if ok4 else '✗'}  ONE node carries both lanes: "
          f"language doors + law doors on 'temperature'")
    rng = np.random.default_rng(3)
    z.discover(X, rng.normal(size=40), name="noise",
               columns=["temperature"])
    ok5 = "law:noise" not in z.net.get_doors("law", tag="law")
    print(f"  {'✓' if ok5 else '✗'}  the null refuses: noise mints no "
          f"law and no uses-doors")
    # THE OLD WOUND (y = x0 + x1, filed 2026-07-22): parts first
    z2 = Isaac()
    z2.wave_logging = False
    rng2 = np.random.default_rng(42)
    Xa = rng2.uniform(1, 10, size=(49, 2))
    ra = z2.discover(Xa, Xa[:, 0] + Xa[:, 1], name="together",
                     columns=["left", "right"])
    eq = ra["equation"]
    ok6 = (ra["verdict"] == "UNDERSTOOD" and "x0" in eq and "x1" in eq
           and "x0*x1" not in eq and "cosh" not in eq)
    print(f"  {'✓' if ok6 else '✗'}  THE ADDITIVE WOUND CLOSES: "
          f"{ra['verdict']} {eq!r}")
    pred = z2.apply_law("together", np.array([[2.0, 3.0]]))
    ok7 = (pred is not None and abs(float(pred[0]) - 5.0) < 0.1
           and z2.scratch.read("left@together") == 2.0
           and z2.scratch.read("x1@together") == 3.0)
    print(f"  {'✓' if ok7 else '✗'}  the sum-law applies elsewhere AND "
          f"instantiates in scratch: f(2,3)={pred}, "
          f"left@together={z2.scratch.read('left@together')}")
    rb = z2.discover(Xa[:12], Xa[:12, 0] + Xa[:12, 1], name="tiny",
                     columns=["left", "right"])
    ok8 = str(rb["verdict"]).startswith("NO RULE")
    print(f"  {'✓' if ok8 else '✗'}  small-n stays honest: n=12 -> "
          f"{rb['verdict']}")
    # a lived composite with an op this engine can't compute must be
    # SKIPPED, never crashed on (the 'powerprod' lesson)
    z3 = Isaac()
    z3.wave_logging = False
    z3.composites.append(dict(op="powerprod", features=[0, 1],
                              name="legacy_pp"))
    rc = z3.discover(Xa, Xa[:, 0] + Xa[:, 1], name="robust",
                     columns=["left", "right"])
    ok9 = rc["verdict"] == "UNDERSTOOD"
    print(f"  {'✓' if ok9 else '✗'}  unknown-op composite skipped, "
          f"not crashed: {rc['verdict']}")
    return all([ok1, ok2, ok3, ok4, ok5, ok6, ok7, ok8, ok9])


def test_shapes():
    _div("17. THE SHAPE ORGAN — core + optional fills, minted from "
         "lived wholes")
    z = Isaac()
    z.wave_logging = False
    z.observe(tokenize("the ball rolled down"))
    z.observe(tokenize("the red ball rolled down"))
    z.observe(tokenize("the blue ball rolled down"))
    z.observe(tokenize("we ate lunch yesterday happily"))
    z.observe(tokenize("we ate dinner yesterday happily"))
    # too different to share a shape: agree only at the end
    z.observe(tokenize("birds fly south quickly"))
    z.observe(tokenize("fish swim north quickly"))
    stats = z.consolidate_shapes()

    # one shape: core "the _ ball rolled down", opening OPTIONAL,
    # fills red and blue
    ball = None
    for node in z.net.get_doors("shapes", tag="shape"):
        core = z.net.get_meta(node, "core")
        if core and "ball" in core:
            ball = node
    ops = z.net.get_meta(ball, "openings") if ball else None
    ok1 = (ball is not None and ops and ops[0]["optional"]
           and set(ops[0]["fills"]) == {"red", "blue"})
    print(f"  {'✓' if ok1 else '✗'}  shape minted: core kept, opening "
          f"optional, fills {ops and ops[0]['fills']}")

    # exactness: the shape rebuilds its sources word for word
    core = z.net.get_meta(ball, "core") if ball else []
    with_fill = [("red" if c is None else c) for c in core]
    without = [c for c in core if c is not None]
    ok2 = (with_fill == ["the", "red", "ball", "rolled", "down"]
           and without == ["the", "ball", "rolled", "down"])
    print(f"  {'✓' if ok2 else '✗'}  rebuilds both lived wholes "
          f"exactly (filled and skipped)")

    # never-lived recognition: green was never in that opening — but
    # HIS type puts green in the same pile as red and blue
    z.types["type:col[3]"] = dict(members={"red", "blue", "green"},
                                  preds=set(), succs=set(),
                                  name="type:col[3]", parent=None,
                                  children=[])
    for w in ("red", "blue", "green"):
        z.net.add_door(w, "type:col[3]", tag="type")
    s, fill = z.recognize_shape(tokenize("the green ball rolled down"))
    ok3 = s == ball and fill == "green"
    print(f"  {'✓' if ok3 else '✗'}  NEVER-LIVED whole recognized "
          f"through his own type: fill={fill!r}")

    # THE BUILD: complete a prefix he never heard
    rest = z.shape_complete(tokenize("the green ball"))
    ok4 = rest == ["rolled", "down"]
    print(f"  {'✓' if ok4 else '✗'}  HE BUILDS: 'the green ball' -> "
          f"{rest} (not memory — construction)")

    # the refusing null: a word from the wrong family does not fit
    s2, _ = z.recognize_shape(tokenize("the green lunch rolled down"))
    ok5 = s2 is None
    print(f"  {'✓' if ok5 else '✗'}  the null refuses: wrong core "
          f"word fits no shape")

    ok6 = (stats["minted"] >= 2 and stats["too_different"] >= 1
           and bool([f for f in z.findings
                     if f.get("kind") == "shape-consolidation"]))
    print(f"  {'✓' if ok6 else '✗'}  receipts: minted={stats['minted']} "
          f"extended={stats['extended']} dismissed="
          f"{stats['too_different']} in {stats['ms']}ms, filed")
    return all([ok1, ok2, ok3, ok4, ok5, ok6])


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
    results["boot"] = test_boot()
    results["consolidation"] = test_consolidation()
    results["atoms"] = test_atoms()
    results["shapes"] = test_shapes()

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
