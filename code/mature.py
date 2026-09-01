"""MATURE — the full operation conversion (owner, 2026-09-01:
"just build a version of it and see what happens").

Loads a mind (or builds a demo one), converts its stores onto the
mature symbolic stack, and hunts for EMERGENT capability — things
the mature machinery concludes or provides that nobody designed in:

  fact_index   -> a logic program (clingo): generic transitive
                  closure, frame-style DEFAULT INHERITANCE of every
                  relation down the is_a tree (nearest-wins for
                  can/cannot), and a GLOBAL CONTRADICTION SCAN of
                  the whole belief store — none of which Isaac has.
  math frames  -> operator facts + ONE generic word-math rule that
                  covers EVERY taught operator (the hand-built
                  bridge only ever did addition).
  found laws   -> computer algebra (sympy): simplified forms and
                  algebraic-identity classes across the ledger.

    python code/mature.py [body.isaac]     (no body = demo mind)

Output is the delta: what does the converted mind know that the
native one was never told?
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from isaac import Isaac, tokenize  # noqa: E402

try:
    import clingo
except ImportError:
    print("clingo missing — the conversion needs it")
    sys.exit(77)


def q(tok):
    return '"' + str(tok).replace('"', "") + '"'


TRANSITIVE = ("is_a", "in", "part_of")
NO_INHERIT = TRANSITIVE + ("cannot", "can", "explains", "blocks")

RULES = """
% -- mature rule set: nothing here is per-domain ------------------
tc(R,X,Y) :- trans(R), rel(R,X,Y).
tc(R,X,Z) :- trans(R), rel(R,X,Y), tc(R,Y,Z).
% frame-style default inheritance: every plain relation flows down
% the is_a tree (penguin eats what birds eat, unless said otherwise)
inh(R,X,O) :- rel(R,X,O), not noinherit(R).
inh(R,X,O) :- tc("is_a",X,Y), rel(R,Y,O), not noinherit(R).
% nearest-ancestor-wins capability verdicts (E1's rule)
verdict(X,A,yes) :- rel("can",X,A).
verdict(X,A,no)  :- rel("cannot",X,A).
verdict(X,A,V)   :- rel("is_a",X,Y), verdict(Y,A,V),
                    not rel("can",X,A), not rel("cannot",X,A).
% the global consistency scan Isaac never runs on himself
conflict(cap,X,A)   :- verdict(X,A,yes), verdict(X,A,no).
conflict(cycle,X,X) :- tc("is_a",X,X).
conflict(direct,X,A):- rel("can",X,A), rel("cannot",X,A).
% ONE word-math rule for EVERY taught operator
wordop(OP,A,B,C) :- word(A,X), word(B,Y), opfact(OP,X,Y,Z), word(C,Z).
"""


def convert(m):
    lines, taught = [], set()
    for (s, r), objs in m.fact_index.items():
        for o in objs:
            lines.append(f"rel({q(r)},{q(s)},{q(o)}).")
            taught.add((r, str(s), str(o)))
    for r in TRANSITIVE:
        lines.append(f"trans({q(r)}).")
    for r in NO_INHERIT:
        lines.append(f"noinherit({q(r)}).")
    n_math = 0
    for seq in m.observed_sequences:
        if (len(seq) == 5 and str(seq[0]).isdigit()
                and str(seq[2]).isdigit() and str(seq[4]).isdigit()
                and seq[3] == "="):
            lines.append(f"opfact({q(seq[1])},{q(seq[0])},"
                         f"{q(seq[2])},{q(seq[4])}).")
            n_math += 1
        elif (len(seq) == 3 and seq[1] == "="
              and str(seq[0]).isalpha() and str(seq[2]).isdigit()):
            lines.append(f"word({q(seq[0])},{q(seq[2])}).")
    return "\n".join(sorted(set(lines))) + RULES, taught, n_math


def solve(program):
    ctl = clingo.Control(["--warn=none"])
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    out = {"tc": [], "inh": [], "verdict": [], "conflict": [],
           "wordop": []}
    ctl.solve(on_model=lambda mo: [
        out[a.name].append(tuple(str(x).strip('"')
                                 for x in a.arguments))
        for a in mo.symbols(atoms=True) if a.name in out])
    return out


def law_algebra(m):
    """Computer algebra over the findings ledger."""
    import sympy
    exprs = []
    for f in m.findings:
        if f.get("kind") != "law":
            continue
        mod = f.get("model") or {}
        try:
            # spec format (read from a live finding): [kind, i, j, k]
            xs = sympy.symbols("x0:8", positive=True)
            e = sympy.Float(round(mod.get("intercept", 0), 6))
            for coef, term in zip(mod["coefs"], mod["terms"]):
                t = sympy.Float(round(coef, 6))
                for ai in term:
                    kind, vi, _vj, k = mod["specs"][ai]
                    if kind == "var":
                        t *= xs[vi]
                    elif kind == "pow":
                        t *= xs[vi] ** sympy.nsimplify(round(k, 4))
                    else:
                        raise ValueError("transcendental")
                e += t
            exprs.append((f.get("name", "?"),
                          sympy.simplify(sympy.expand(e))))
        except Exception:
            exprs.append((f.get("name", "?"), None))
    same = []
    for i in range(len(exprs)):
        for j in range(i + 1, len(exprs)):
            a, b = exprs[i], exprs[j]
            if a[1] is not None and b[1] is not None:
                try:
                    if sympy.simplify(a[1] - b[1]) == 0:
                        same.append((a[0], b[0]))
                except Exception:
                    pass
    return exprs, same


def report(m, label):
    print(f"\n{'=' * 66}\n  FULL CONVERSION — {label}\n{'=' * 66}")
    t0 = time.perf_counter()
    program, taught, n_math = convert(m)
    out = solve(program)
    dt = time.perf_counter() - t0
    n_taught = len(taught)
    new_tc = [t for t in out["tc"] if (t[0], t[1], t[2]) not in taught]
    new_inh = [t for t in out["inh"]
               if (t[0], t[1], t[2]) not in taught]
    print(f"converted+derived in {1000 * dt:.0f}ms — "
          f"{n_taught} taught relations, {n_math} math frames")
    print(f"\nTHE DELTA (known now, never taught):")
    print(f"  {len(new_tc):4d} transitive conclusions      "
          f"e.g. {new_tc[:3]}")
    print(f"  {len(new_inh):4d} inherited properties        "
          f"e.g. {new_inh[:3]}")
    ops = {}
    for op, a, b, c in out["wordop"]:
        ops.setdefault(op, []).append((a, b, c))
    for op, rows in sorted(ops.items()):
        print(f"  {len(rows):4d} word-math results for '{op}'   "
              f"e.g. {rows[0]}")
    if out["conflict"]:
        print(f"  {len(out['conflict']):4d} CONTRADICTIONS FOUND:      "
              f"{out['conflict'][:5]}")
    else:
        print(f"     0 contradictions (belief store is consistent)")
    exprs, same = law_algebra(m)
    if exprs:
        print(f"\nLAW ALGEBRA ({len(exprs)} laws through sympy):")
        for name, e in exprs[:6]:
            print(f"  {name}: {e if e is not None else '(not algebraic)'}")
        for a, b in same:
            print(f"  ALGEBRAICALLY IDENTICAL: {a} == {b}  "
                  f"(the ledger holds one law twice)")
    return out


if __name__ == "__main__":
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        m = Isaac.load(sys.argv[1])
        m.wave_logging = False
        report(m, os.path.basename(sys.argv[1]))
    else:
        m = Isaac()
        m.wave_logging = False
        for s, o in [("cat", "mammal"), ("dog", "mammal"),
                     ("mammal", "animal"), ("animal", "living_thing"),
                     ("robin", "bird"), ("penguin", "bird"),
                     ("bird", "animal"), ("salmon", "fish"),
                     ("fish", "animal"), ("oak", "tree"),
                     ("tree", "plant"), ("plant", "living_thing")]:
            m.teach(s, "is_a", o)
        for s, o in [("bird", "fly"), ("bird", "sing"),
                     ("fish", "swim"), ("cat", "purr"),
                     ("cat", "climb"), ("dog", "bark"),
                     ("penguin", "swim"), ("living_thing", "grow"),
                     ("animal", "move")]:
            m.teach(s, "can", o)
        for s, o in [("penguin", "fly"), ("fish", "walk")]:
            m.observe(tokenize(f"{s} cannot {o}"))
            m.fact_index[(s, "cannot")].append(o)
        for s, o in [("bird", "worms"), ("cat", "mice"),
                     ("salmon", "plankton")]:
            m.teach(s, "eats", o)
        for s, o in [("bird", "feathers"), ("mammal", "fur"),
                     ("cat", "whiskers")]:
            m.teach(s, "has", o)
        for i, o in [("ball", "box"), ("box", "closet"),
                     ("closet", "room"), ("room", "house")]:
            m.teach(i, "in", o)
        W = ["zero", "one", "two", "three", "four", "five", "six",
             "seven", "eight", "nine", "ten", "eleven", "twelve",
             "thirteen", "fourteen", "fifteen", "sixteen",
             "seventeen", "eighteen"]
        for a in range(10):
            for b in range(10):
                m.observe(tokenize(f"{a} + {b} = {a + b}"))
                if a * b <= 18:
                    m.observe(tokenize(f"{a} * {b} = {a * b}"))
        for d in range(19):
            m.observe(tokenize(f"{W[d]} = {d}"))
        import numpy as np
        rng = np.random.default_rng(7)
        X = rng.uniform(0, 10, (40, 2))
        m.discover(X, 2 * X[:, 0], name="doubling")
        m.discover(X, X[:, 0] + X[:, 0], name="twice_by_addition")
        m.discover(X, 3 * X[:, 0] + 4 * X[:, 1], name="mixed")
        report(m, "demo mind (taxonomy + math + words + laws)")
