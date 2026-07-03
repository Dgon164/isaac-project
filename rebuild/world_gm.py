"""
WORLD GM — the omniscient world generator + tester (v1, 2026-07-03).

The owner's spec: "we program the base rules... we define the rules, but not
the interactions... see if it resolves and discovers meta or tertiary rules
that are not explicitly programmed in but are emergent."

So: PRIMITIVES are programmed (exchange, power-law drive, gate, decay).
WORLDS are sampled (values, wiring). The LAWS ISAAC MUST FIND are never
written anywhere in this file as laws — they are consequences:
  - an exchange is antisymmetric        => a conserved total (emergent)
  - a connected exchange graph mixes    => equilibrium = mean (emergent)
  - power laws compose through a chain  => tertiary exponent alpha*beta
  - a gate makes a law conditional      => compound structure (engine gap)

THE INFORMATION RULE: Isaac earns information; the GM only answers.
  observe(n)  n sampled episodes (costs n)
  run(x)      the outcome of ONE chosen experiment — the probe verb (costs 5)
  submit(f)   predictions graded on HIDDEN inputs, incl. BEYOND the observed
              range (a range-valid surrogate fails where form-true passes).
              Returns a grade, never the truth. (costs 20)

Grading: where the emergent truth is derivable (exchange, chain) the GM also
scores Isaac's ACCOUNTING against the true noise share. Where it isn't, the
hidden-rollout grade IS the oracle.
"""
import sys
import time
import numpy as np

import os; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))  # repo-local isaac.py
from isaac import Isaac

rng = np.random.default_rng(11)


# ══════════════════════════════════════════════════════════════════
# THE GM
# ══════════════════════════════════════════════════════════════════
class World:
    """Holds hidden truth. Never leaks it. Budget makes information cost."""

    def __init__(self, kind, sample_fn, truth_fn, obs_range, test_range,
                 noise_sd, budget=600):
        self.kind = kind
        self._sample = sample_fn        # () -> x vector in obs_range
        self._truth = truth_fn          # (X) -> clean y (the hidden physics)
        self.obs_range, self.test_range = obs_range, test_range
        self.noise_sd = noise_sd
        self.budget = budget
        self.spent = 0
        self.queries = dict(observe=0, run=0, submit=0)

    def _emit(self, X):
        y = self._truth(X)
        return y + rng.normal(0, self.noise_sd * max(y.std(), 1e-9), len(y))

    def observe(self, n):
        assert self.spent + n <= self.budget, "budget exhausted"
        self.spent += n; self.queries["observe"] += n
        X = np.array([self._sample() for _ in range(n)])
        return X, self._emit(X)

    def run(self, x):
        """One chosen experiment — Isaac names it, the GM answers it."""
        assert self.spent + 5 <= self.budget, "budget exhausted"
        self.spent += 5; self.queries["run"] += 1
        X = np.asarray(x, float).reshape(1, -1)
        return float(self._emit(X)[0])

    def submit(self, predict_fn):
        """Grade predictions on hidden inputs the player never saw:
        half inside the observed range, half BEYOND it (form check)."""
        self.spent += 20; self.queries["submit"] += 1
        lo, hi = self.obs_range
        tl, th = self.test_range
        d = len(self._sample())
        Xin = rng.uniform(lo, hi, (300, d))
        Xout = rng.uniform(tl, th, (300, d))
        grades = {}
        for tag, Xh in (("inside", Xin), ("beyond", Xout)):
            yt = self._truth(Xh)
            yp = predict_fn(Xh)
            if yp is None:
                grades[tag] = None
                continue
            ss = float(np.sum((yt - yt.mean()) ** 2))
            grades[tag] = 1 - float(np.sum((yt - np.asarray(yp)) ** 2)) \
                / max(ss, 1e-12)
        return grades

    def true_noise_share(self):
        """For accounting audits only (reported AFTER the game)."""
        X = np.array([self._sample() for _ in range(4000)])
        y = self._truth(X)
        nv = (self.noise_sd * max(y.std(), 1e-9)) ** 2
        return 100 * nv / (y.var() + nv)


# ══════════════════════════════════════════════════════════════════
# WORLD GENERATORS — primitives programmed, laws emergent
# ══════════════════════════════════════════════════════════════════
def make_exchange_world():
    """PRIMITIVE: pairwise exchange dq_i += c_ij (q_j - q_i), sampled sparse
    symmetric graph, simulated forward. NEVER PROGRAMMED: that the total is
    conserved, or that a connected graph equilibrates to the mean. The
    observable: initial quantities -> one entity's FINAL quantity."""
    K = 5
    C = np.zeros((K, K))
    for i in range(K):
        for j in range(i + 1, K):
            if rng.random() < 0.8:
                C[i, j] = C[j, i] = rng.uniform(0.05, 0.25)
    steps = 400

    def simulate(q0):
        q = q0.copy()
        for _ in range(steps):
            q = q + 0.05 * (C @ q - C.sum(1) * q)
        return q

    target = int(rng.integers(0, K))

    def truth(X):
        return np.array([simulate(x)[target] for x in X])

    return World("exchange", lambda: rng.uniform(0, 4, K), truth,
                 obs_range=(0, 4), test_range=(4, 8), noise_sd=0.01), \
        dict(entities=K, target=target,
             emergent="final_i -> mean(q0) (equilibrium; total conserved)")


def make_chain_world():
    """PRIMITIVE: two power-law drives a->b->c, values sampled; b is HIDDEN.
    NEVER PROGRAMMED: the tertiary law c = (c2*c1^beta) * a^(alpha*beta)."""
    a_exp = float(rng.choice([0.5, 1.0, 1.5, 2.0]))
    b_exp = float(rng.choice([0.5, 1.0, 1.5]))
    c1, c2 = float(rng.lognormal(0, .2)), float(rng.lognormal(0, .2))

    def truth(X):
        b = c1 * X[:, 0] ** a_exp
        return c2 * b ** b_exp

    return World("chain", lambda: rng.uniform(0.5, 3.0, 1), truth,
                 obs_range=(0.5, 3.0), test_range=(3.0, 8.0),
                 noise_sd=0.02), \
        dict(alpha=a_exp, beta=b_exp,
             emergent=f"c = {c2*c1**b_exp:.2f} * a^{a_exp*b_exp:.2f} "
                      f"(composed exponent, never written)")


def make_gated_world():
    """PRIMITIVE: an interaction that only exists when a gate property is
    in range. NEVER PROGRAMMED: the compound conditional law. The engine
    has no compound doors — a DESIGNED probe of that gap."""
    thr = float(rng.uniform(-0.3, 0.3))

    def truth(X):
        on = X[:, 2] > thr
        return np.where(on, 2.0 * X[:, 0] * X[:, 1], 0.3 * X[:, 0])

    return World("gated", lambda: rng.normal(0, 1, 3), truth,
                 obs_range=(-2.5, 2.5), test_range=(2.5, 4.0),
                 noise_sd=0.03), \
        dict(threshold=thr, emergent="y = 2*x0*x1 IF x2>thr ELSE 0.3*x0")


def make_null_world():
    """Inputs with rich internal structure; the target is decoupled.
    The winning move is NO RULE."""
    def truth(X):
        return np.zeros(len(X))          # signal literally absent

    return World("null", lambda: rng.normal(0, 1, 4), truth,
                 obs_range=(-2.5, 2.5), test_range=(2.5, 4.0),
                 noise_sd=1.0), dict(emergent="nothing — refusal is the win")


# ══════════════════════════════════════════════════════════════════
# THE PLAYER — Isaac earns it: observe -> discover -> probe -> submit
# ══════════════════════════════════════════════════════════════════
def play(world, meta, n_obs=300, verbose=True):
    isaac = Isaac()
    t0 = time.time()
    X, y = world.observe(n_obs)
    res = isaac.discover(X, y, name=world.kind)

    # the probe loop: open rivals name the experiment; the GM answers it;
    # confirm() resolves — resolution is no longer manual
    probes_run = 0
    if res["rivals"]:
        Xp, yp = [], []
        for r in res["rivals"][:3]:
            feat = r["probe"].get("feature", 0) if isinstance(r["probe"], dict) else 0
            xval = r["probe"].get("x", None) if isinstance(r["probe"], dict) else None
            if xval is None:
                continue
            for _ in range(4):
                x = X[int(rng.integers(0, len(X)))].copy()
                x[feat] = xval * rng.uniform(0.95, 1.05)
                Xp.append(x); yp.append(world.run(x)); probes_run += 1
        if Xp:
            isaac.confirm(world.kind, np.array(Xp), np.array(yp))
            res = dict(res, equation=isaac.net.get_meta(
                f"law:{world.kind}", "equation") or res["equation"])

    # SCOPE SELF-CHECK: internal edge-labels can only test edges that were
    # observed. So Isaac SPENDS BUDGET to earn the extrapolation claim:
    # run experiments beyond his own observed hull, validate_law on them,
    # and if the law fails out there, re-learn WITH the earned points.
    scope_arc = ""
    if res["verdict"] in ("UNDERSTOOD", "PARTIAL"):
        hi = X.max(0)
        Xb = np.array([hi * rng.uniform(1.3, 1.9, X.shape[1])
                       for _ in range(6)])
        yb = np.array([world.run(x) for x in Xb])
        val = isaac.validate_law(world.kind, Xb, yb)
        if val and val["status"] != "HOLDS":
            # the law fails out there -> EARN more far points and re-learn
            # on the shuffled union (shuffled so both discover() halves see
            # near and far; no duplication - duplicates corrupt the null)
            Xb2 = np.array([hi * rng.uniform(1.2, 2.0, X.shape[1])
                            for _ in range(6)])
            yb2 = np.array([world.run(x) for x in Xb2])
            X2 = np.vstack([X, Xb, Xb2])
            y2 = np.concatenate([y, yb, yb2])
            sh = rng.permutation(len(y2))
            res = isaac.discover(X2[sh], y2[sh], name=world.kind)
            val2 = (isaac.validate_law(world.kind, Xb, yb)
                    if res["verdict"] in ("UNDERSTOOD", "PARTIAL") else None)
            scope_arc = (f"scope check beyond own hull: {val['status']} "
                         f"(R2 {val['r2']:.2f}) -> earned 6 more far points,"
                         f" re-learned -> "
                         f"{val2['status'] if val2 else res['verdict']}")
        else:
            scope_arc = "scope check beyond own hull: HOLDS"

    predict = (lambda Xh: isaac.apply_law(world.kind, Xh)) \
        if res["verdict"] in ("UNDERSTOOD", "PARTIAL") else (lambda Xh: None)
    grades = world.submit(predict)

    # ---- scorecard (GM-side truth revealed only for grading display)
    true_noise = world.true_noise_share()
    acc = res["accounting"]
    if verbose:
        print(f"\n── {world.kind.upper()} world "
              f"(emergent, never programmed: {meta['emergent']})")
        print(f"   verdict {res['verdict']:11s} [{res.get('scope', '—')}]")
        print(f"   eq: {res['equation'][:70]}")
        if scope_arc:
            print(f"   {scope_arc}")
        gi, gb = grades["inside"], grades["beyond"]
        print(f"   GM grade: inside-range R2 "
              f"{'—' if gi is None else format(gi, '.3f')}   "
              f"BEYOND-range R2 {'—' if gb is None else format(gb, '.3f')}")
        print(f"   accounting said law/caught/noise = {acc['articulated']}/"
              f"{acc['captured']}/{acc['noise']}  (GM true noise share "
              f"{true_noise:.1f}%)")
        print(f"   earned with: {world.queries['observe']} observations, "
              f"{world.queries['run']} probe runs, "
              f"{world.queries['submit']} submission "
              f"[{world.spent}/{world.budget} budget, {time.time()-t0:.1f}s]")
    return dict(kind=world.kind, verdict=res["verdict"],
                scope=res.get("scope", ""), grades=grades,
                accounting=acc, true_noise=true_noise,
                queries=dict(world.queries), probes=probes_run)


def main():
    print("WORLD GM v1 — primitives programmed, laws emergent, "
          "information earned")
    results = []
    for maker in (make_exchange_world, make_chain_world,
                  make_gated_world, make_null_world):
        world, meta = maker()
        results.append(play(world, meta))

    # Two separate marks, because they are separate virtues:
    #   SOLVED — the emergent law was recovered form-true (beyond-range)
    #   HONEST — no claim outran the GM's grade (overclaim = the only sin)
    # Two separate marks, judged against the engine's OWN claims:
    #   SOLVED — the emergent law recovered form-true (GM beyond-range > .9)
    #   HONEST — the claim as scoped held up: form-true must survive beyond
    #            range; range-valid must survive inside; PARTIAL/CAPTURED
    #            accounting must not outrun the GM's inside grade.
    # This IS the calibration audit: when he says form-true, is he?
    print("\n══ SCORECARD ══   (solved = capability; honest = calibration "
          "of his own labels)")
    solved_n = honest_n = 0
    for r in results:
        gi, gb = r["grades"]["inside"], r["grades"]["beyond"]
        if r["kind"] == "null":
            solved = honest = r["verdict"] == "NO RULE"
        else:
            solved = gb is not None and gb > 0.9
            if r["verdict"] == "UNDERSTOOD":
                honest = (gb is not None and gb > 0.7) \
                    if r["scope"].startswith("form-true") \
                    else (gi is not None and gi > 0.7)
            else:
                honest = (gi is None
                          or r["accounting"]["articulated"] / 100
                          <= max(gi, 0) + 0.3)
        solved_n += solved; honest_n += honest
        print(f"  {r['kind']:9s} {r['verdict']:11s} "
              f"[{r['scope'][:10] or '—':10s}] "
              f"solved {'✓' if solved else '✗'}   "
              f"honest {'✓' if honest else '✗'}")
    print(f"\n  solved {solved_n}/4   honest {honest_n}/4")
    print("  The GM's law: capability misses are findings; a scope label "
          "that doesn't hold is the kill.")
    print(f"  VERDICT: {'CALIBRATED' if honest_n == 4 else 'CALIBRATION GAP'}"
          f"{' — and all worlds solved' if solved_n == 4 else ''}")


if __name__ == "__main__":
    main()
