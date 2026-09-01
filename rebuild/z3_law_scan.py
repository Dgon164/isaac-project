# Z3 CONSISTENCY SCAN — detect when two discovered numeric laws disagree
# on shared domain. Measured July need: two live laws disagreed on the
# same inputs and nothing noticed. This probe plants a known conflict and
# a known-consistent control through the real discovery module, then runs
# a solver-backed scan over the findings ledger and courts the results.
#
# Method: for each pair of laws over the same raw input variables, take
# the intersection of their declared per-variable domains (the observed
# ranges stored on the law node), encode both prediction formulas as Z3
# real-arithmetic expressions, and ask whether a point exists inside the
# shared domain where |law1(x) - law2(x)| > TOLERANCE.
#   SAT   -> conflict; Z3 hands back a concrete witness point, which the
#            court re-checks through the engine's own apply_law road.
#   UNSAT -> consistent within tolerance everywhere on the shared domain.
# Empty domain intersection -> nothing to compare (clean by disjointness).
#
# Note found while building: the ledger copy of a law's model carries no
# per-variable ranges — only the net node law:<name> does. A session
# rehydrated via load_ledger() therefore has laws with no declared
# domain and cannot be domain-scanned; the scanner reports those as
# unscannable instead of guessing.
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "..", "code"))

try:
    import z3
except Exception as ex:                                  # noqa: BLE001
    print(f"SKIP: z3 unavailable ({ex}) — pip install z3-solver")
    sys.exit(77)

import numpy as np                                       # noqa: E402
from fractions import Fraction                           # noqa: E402
from isaac import Isaac                                  # noqa: E402

# failed check names collect here; summary + exit code at the bottom
FAILS = []
rng = np.random.default_rng(20260831)

# Two predictions further apart than this on any shared point = the laws
# materially disagree. Half a unit of y is far above float noise from
# refitting the same clean data, and far below the planted 3*x0 gap.
TOLERANCE = 0.5


class Unencodable(Exception):
    """This law uses an atom the real-arithmetic scan cannot express."""


class _LawEncoder:
    """Turn one law's model (terms/coefs/intercept/specs) into a Z3 real
    expression, mirroring apply_law exactly. var atoms are the input
    itself. pow atoms are encoded against the engine's ACTUAL base,
    max(|x|, 1e-9) — via z3.If — so odd powers and negative domains
    behave like the engine, not like the textbook. Fractional exponents
    p/q (the grid emits halves and quarters) get a definitional variable
    u > 0 with u^q = base^p, which pins u = base^(p/q) exactly.
    sin/cos/exp and pow k=0 (=log) are not real-arithmetic; those laws
    are reported unscannable rather than approximated."""

    def __init__(self, tag, xs):
        self.tag, self.xs = tag, xs
        self.side = []                # definitional constraints
        self._cache = {}
        self._n = 0

    def _base(self, i):               # engine base: max(|x|, 1e-9)
        x = self.xs[i]
        return z3.If(x >= 1e-9, x,
                     z3.If(x <= -1e-9, -x, z3.RealVal(1e-9)))

    def _atom(self, a, spec):
        if a in self._cache:
            return self._cache[a]
        kind, i, j, k = spec
        if kind == "var":
            e = self.xs[i]
        elif kind == "pow" and k is not None and float(k) != 0.0:
            fr = Fraction(float(k))   # grid k are exact dyadic floats
            if fr.denominator > 4 or abs(fr.numerator) > 12:
                raise Unencodable(f"pow exponent {k} is not a small "
                                  f"rational — refuse, don't approximate")
            b = self._base(i)
            p, q = fr.numerator, fr.denominator
            if q == 1 and p >= 1:     # integer power: plain product
                e = b
                for _ in range(p - 1):
                    e = e * b
            else:                     # u = b^(p/q), pinned definitionally
                u = z3.Real(f"u_{self.tag}_{self._n}")
                self._n += 1
                uq = u
                for _ in range(q - 1):
                    uq = uq * u
                bp = z3.RealVal(1)
                for _ in range(abs(p)):
                    bp = bp * b
                self.side.append(u > 0)
                self.side.append(uq == bp if p > 0 else uq * bp == 1)
                e = u
        else:
            raise Unencodable(f"{kind} atom (k={k}) is not "
                              f"real-arithmetic encodable")
        self._cache[a] = e
        return e

    def law(self, model):
        expr = z3.RealVal(float(model["intercept"]))
        for t, c in zip(model["terms"], model["coefs"]):
            term = z3.RealVal(float(c))
            for a in t:
                term = term * self._atom(a, model["specs"][a])
            expr = expr + term
        return expr


def _z3_num(v):
    """Z3 numeral -> float (handles rational and algebraic values)."""
    return float(v.as_decimal(12).rstrip("?"))


def scan_laws(m, tol=TOLERANCE):
    """Scan every pair of discovered laws for disagreement on shared
    domain. Returns a list of result dicts; conflicts are also written
    into the findings ledger (kind='law-conflict') so a disagreement is
    RECORDED, not just printed."""
    laws, seen = [], set()
    for e in m.findings:
        if e.get("kind") != "law" or e.get("model") is None:
            continue
        nm = e["name"]
        if nm in seen:
            continue
        seen.add(nm)
        mod = m.net.get_meta(f"law:{nm}", "model")
        if not mod or "ranges" not in mod:
            print(f"  {nm}: no declared domain on the law node "
                  f"(rehydrated ledger?) — cannot domain-scan")
            continue
        if mod.get("composites_used") or mod["d"] != mod.get("d_raw",
                                                            mod["d"]):
            print(f"  {nm}: uses composite columns — not scanned")
            continue
        laws.append((nm, mod))
    if len(laws) < 2:
        print(f"  nothing to scan ({len(laws)} scannable law(s); need 2)")
        return []
    results, incomparable = [], 0
    for a in range(len(laws)):
        for b in range(a + 1, len(laws)):
            na, ma = laws[a]
            nb, mb = laws[b]
            d = ma["d_raw"]
            if mb["d_raw"] != d:
                incomparable += 1        # different variable spaces
                continue
            lo = [max(ma["ranges"][i][0], mb["ranges"][i][0])
                  for i in range(d)]
            hi = [min(ma["ranges"][i][1], mb["ranges"][i][1])
                  for i in range(d)]
            if any(lo[i] > hi[i] for i in range(d)):
                results.append(dict(pair=(na, nb),
                                    status="CLEAN-DISJOINT"))
                continue
            xs = [z3.Real(f"x{i}") for i in range(d)]
            enc_a, enc_b = _LawEncoder("a", xs), _LawEncoder("b", xs)
            try:
                diff = enc_a.law(ma) - enc_b.law(mb)
            except Unencodable as ex:
                results.append(dict(pair=(na, nb), status="UNSCANNED",
                                    why=str(ex)))
                continue
            s = z3.Solver()
            for i in range(d):
                s.add(xs[i] >= lo[i], xs[i] <= hi[i])
            for c in enc_a.side + enc_b.side:
                s.add(c)
            s.add(z3.Or(diff > tol, diff < -tol))
            verdict = s.check()
            if verdict == z3.sat:
                zm = s.model()
                pt = [_z3_num(zm.eval(xs[i], model_completion=True))
                      for i in range(d)]
                gap = _z3_num(zm.eval(diff, model_completion=True))
                results.append(dict(pair=(na, nb), status="CONFLICT",
                                    witness=pt, gap=gap))
                m.record_finding("law-conflict", f"{na}|{nb}",
                                 witness=pt, gap=gap, tolerance=tol,
                                 domain_lo=lo, domain_hi=hi)
            elif verdict == z3.unsat:
                results.append(dict(pair=(na, nb),
                                    status="CLEAN-CONSISTENT"))
            else:
                results.append(dict(pair=(na, nb), status="UNSCANNED",
                                    why="solver returned unknown"))
    if incomparable:
        print(f"  ({incomparable} pair(s) over different variable "
              f"spaces — not comparable, skipped)")
    return results


def find_pair(results, a, b):
    for r in results:
        if set(r["pair"]) == {a, b}:
            return r
    return None


# ── stage 1: plant laws through the real discovery module ──────────
print("STAGE 1 — PLANT: drive discover() to install the test laws")
t0 = time.perf_counter()
m = Isaac()
plants = [
    # name, n_vars, domain lo/hi per var, true function
    ("lawA", 1, [0], [10], lambda X: 2 * X[:, 0]),       # conflict pair:
    ("lawB", 1, [0], [10], lambda X: 5 * X[:, 0]),       # same x0 range
    ("lawE_far", 1, [20], [30], lambda X: 7 * X[:, 0]),  # disjoint range
    ("lawC", 2, [0, 0], [5, 5],                          # consistent
     lambda X: 3 * X[:, 0] + 4 * X[:, 1]),               # control pair:
    ("lawD", 2, [0, 0], [5, 5],                          # same law, a
     lambda X: 3 * X[:, 0] + 4 * X[:, 1]),               # fresh sample
]
for name, d, lo, hi, f in plants:
    X = rng.uniform(lo, hi, size=(200, d))
    r = m.discover(X, f(X), name=name)
    print(f"  {name}: {r['verdict']}  eq: {r['equation']}")
    if r["verdict"] != "UNDERSTOOD":
        FAILS.append(f"plant-{name}")
n_laws = sum(1 for e in m.findings if e.get("kind") == "law")
print(f"  findings ledger now holds {len(m.findings)} records "
      f"({n_laws} laws)   [{time.perf_counter() - t0:.1f}s]")

# ── stage 2: the scan + the court ──────────────────────────────────
print(f"\nSTAGE 2 — SCAN: pairwise Z3 consistency, tolerance "
      f"{TOLERANCE} on shared domain")
t0 = time.perf_counter()
results = scan_laws(m)
for r in results:
    line = f"  {r['pair'][0]} vs {r['pair'][1]}: {r['status']}"
    if r["status"] == "CONFLICT":
        w = ", ".join(f"x{i}={v:g}" for i, v in enumerate(r["witness"]))
        line += f"  witness ({w})  gap {r['gap']:g}"
    if "why" in r:
        line += f"  ({r['why']})"
    print(line)
print(f"  [{time.perf_counter() - t0:.1f}s]")

conflict = find_pair(results, "lawA", "lawB")
if not conflict or conflict["status"] != "CONFLICT" \
        or "witness" not in conflict:
    FAILS.append("planted-conflict-found")
else:
    # court the witness through the engine's own application road:
    # both laws, applied at the point Z3 named, must actually disagree
    w = np.array([conflict["witness"]])
    ya = m.apply_law("lawA", w)
    yb = m.apply_law("lawB", w)
    real_gap = abs(float(ya[0]) - float(yb[0]))
    print(f"  witness re-checked via apply_law: lawA={float(ya[0]):g} "
          f"lawB={float(yb[0]):g}  measured gap {real_gap:g}")
    if real_gap <= TOLERANCE - 1e-6:  # 1e-6: decimal-witness roundoff
        FAILS.append("witness-verifies")
    # the conflict must be RECORDED in the ledger, not just printed
    if not any(e.get("kind") == "law-conflict"
               and set(e["name"].split("|")) == {"lawA", "lawB"}
               for e in m.findings):
        FAILS.append("conflict-recorded-in-ledger")

control = find_pair(results, "lawC", "lawD")
if not control or control["status"] != "CLEAN-CONSISTENT":
    FAILS.append("control-pair-clean")
for far in ("lawA", "lawB"):
    r = find_pair(results, far, "lawE_far")
    if not r or r["status"] != "CLEAN-DISJOINT":
        FAILS.append(f"disjoint-{far}-clean")
if any(r["status"] == "UNSCANNED" for r in results):
    FAILS.append("no-unscanned-pairs")

# ── stage 3: small-engine guard — scan must not crash on <2 laws ───
print("\nSTAGE 3 — SMALL-ENGINE GUARD: scan with 0 laws and 1 law")
t0 = time.perf_counter()
try:
    r0 = scan_laws(Isaac())
    m1 = Isaac()
    X = rng.uniform(0, 10, size=(200, 1))
    m1.discover(X, 2 * X[:, 0], name="lone_law")
    r1 = scan_laws(m1)
    if r0 != [] or r1 != []:
        FAILS.append("small-engine-empty-result")
except Exception as ex:                                  # noqa: BLE001
    print(f"  crashed: {ex}")
    FAILS.append("small-engine-no-crash")
print(f"  [{time.perf_counter() - t0:.1f}s]")

if FAILS:
    print(f"\nGATE: FAIL ({', '.join(FAILS)})")
else:
    print("\nGATE: PASS")
sys.exit(1 if FAILS else 0)
