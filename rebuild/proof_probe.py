"""PROOF PROBE — from extensional to proven (level-2 rules meet Z3).

The engine's level-2 machinery (meta_hunt) calls two rule chains equal
when they agree on the integers 0..24 (_op_ext_eq). That is a spot
check on 25 points, not a proof. This probe upgrades the claims: each
chain of primitive names is translated into a Z3 integer expression
(inc -> x+1, dec -> x-1, dbl -> 2*x, neg -> -x, sq -> x*x,
add_k(k) -> x+k, mul_k(k) -> k*x; induced library names expand through
the facts layer, exactly as _ind_apply resolves them) and Z3 is asked
for a counterexample to chain_a(x) == chain_b(x). No counterexample
over ALL integers = THEOREM. A counterexample = REFUTED, witness
printed and re-checked through the engine's own evaluator.

shr is the one careful case: the engine defines shr as x >> 1 for
x >= 0 only (None below zero), so a plain for-all-integers translation
would misstate the rule's domain. Stages 1-3 therefore SKIP
shr-bearing chains and say so. Stage 4 builds the exact model — Z3
integer division by 2 (floor, for a positive divisor) under an
"input >= 0" guard per shr step — and first checks it value-for-value
against the engine before trusting it.

Stages (each prints its wall-clock time):
  1  the engine's OWN discovered identities and inverses — rules
     minted via induce_op on planted pairs, then meta_hunt — each
     upgraded from 25-point spot check to proof
  2  composition laws proved: mul_k(2) then mul_k(3) == mul_k(6);
     add_k(7) then add_k(5) == add_k(12); inc then dec == identity
     (the empty chain); and more
  3  a deliberate NON-theorem (dbl then inc == inc then dbl) —
     must be REFUTED with a concrete witness value
  4  the payoff: two chains the 0..24 spot check calls EQUAL that are
     NOT equal. Construction (shr-based, real engine vocabulary):
     shr x5 (= x >> 5) vs shr x6 (= x >> 6) — both are 0 on all of
     0..24 (and up to 31), so the engine's own extensional court
     accepts the identity and meta_hunt mints it into the facts
     layer; Z3 refutes it, first divergence x = 32. The polynomial
     prims alone cannot fool a 25-point check (two different integer
     polynomials agreeing on 25 points would need degree >= 25), so
     shr — the one non-polynomial prim — is the honest material.
     Bonus: "shr undoes dbl", skipped in stage 1, gets its proof here
     under the honest x >= 0 domain guard.

Court: >= 5 theorems proven, >= 1 claim refuted with witness, the
extensional-accepts / Z3-refutes demonstration shown live.
Exit 0 = all checks pass; exit 1 = failure; exit 77 = prerequisites
missing (skip).
"""
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

from isaac import Isaac                                  # noqa: E402

FAILS = []
THEOREMS = []       # (tag, equation) for every proved claim
REFUTATIONS = []    # (tag, witness) for every refuted claim
SKIPPED = []        # shr-bearing claims deferred to stage 4
Z3_TOTAL = [0.0]    # summed solver time

X = z3.Int("x")


def check(name, ok):
    print(f"  {'v' if ok else 'x'}  {name}")
    if not ok:
        FAILS.append(name)


class SkipShr(Exception):
    """Chain uses shr and the caller did not ask for the guarded model."""


def resolve_lib(m, name):
    """Induced library name -> its chain, exactly as _ind_apply looks
    it up (op_rule facts, origin=induced, name before ' =')."""
    for f in m.facts_query(pred="op_rule", origin="induced"):
        if f["text"].split(" =")[0] == name:
            return list(f["args"])
    return None


def to_z3(m, chain, expr, allow_shr=False, guards=None):
    """Apply a chain of primitive names to a Z3 integer expression.
    Mirrors _ind_prim / _ind_apply step for step. With allow_shr, each
    shr step adds the engine's domain condition (input >= 0) to guards
    and becomes integer division by 2 (floor — matches x >> 1 there)."""
    for name in chain:
        if name == "inc":
            expr = expr + 1
        elif name == "dec":
            expr = expr - 1
        elif name == "dbl":
            expr = expr * 2
        elif name == "neg":
            expr = -expr
        elif name == "sq":
            expr = expr * expr
        elif name == "shr":
            if not allow_shr:
                raise SkipShr(name)
            guards.append(expr >= 0)
            expr = expr / z3.IntVal(2)
        elif name.startswith("add_k(") and name.endswith(")"):
            expr = expr + int(name[len("add_k("):-1])
        elif name.startswith("mul_k(") and name.endswith(")"):
            k = int(name[len("mul_k("):-1])
            if k == 0:
                raise ValueError("mul_k(0) is outside the vocabulary")
            expr = expr * k
        else:
            sub = resolve_lib(m, name)
            if sub is None:
                raise ValueError(f"unknown chain step: {name}")
            expr = to_z3(m, sub, expr, allow_shr, guards)
    return expr


def show(chain):
    return " then ".join(chain) if chain else "(empty chain = x)"


def prove(m, tag, chain_a, chain_b, allow_shr=False):
    """Ask Z3 for a counterexample to chain_a(x) == chain_b(x).
    unsat -> THEOREM. sat -> REFUTED, witness printed and re-checked
    through the engine's own _ind_apply. Returns the verdict."""
    eq = f"{show(chain_a)}  ==  {show(chain_b)}"
    guards = []
    try:
        ea = to_z3(m, chain_a, X, allow_shr, guards)
        eb = to_z3(m, chain_b, X, allow_shr, guards)
    except SkipShr:
        print(f"  -  SKIP     {tag}: {eq}")
        print("              (shr: engine defines it only for x >= 0;"
              " integer division needs the guarded model — stage 4)")
        SKIPPED.append((tag, eq))
        return "SKIP"
    s = z3.Solver()
    for g in guards:
        s.add(g)
    s.add(ea != eb)
    t0 = time.perf_counter()
    r = s.check()
    dt = time.perf_counter() - t0
    Z3_TOTAL[0] += dt
    alg = f"[{z3.simplify(ea)} == {z3.simplify(eb)}]"
    dom = "  domain: x >= 0" if guards else ""
    if r == z3.unsat:
        print(f"  v  THEOREM  {tag}: {eq}   {alg}{dom}   z3 {dt * 1000:.1f}ms")
        THEOREMS.append((tag, eq))
        return "THEOREM"
    if r == z3.sat:
        w = s.model().eval(X, model_completion=True).as_long()
        va = m._ind_apply(chain_a, w)
        vb = m._ind_apply(chain_b, w)
        if va is not None and vb is not None and va != vb:
            # a refutation counts only when the engine's own evaluator
            # reproduces the divergence at the witness
            print(f"  x  REFUTED  {tag}: {eq}   witness x={w}: "
                  f"{va} != {vb} (confirmed by the engine's own "
                  f"evaluator){dom}   z3 {dt * 1000:.1f}ms")
            REFUTATIONS.append((tag, w))
            return "REFUTED"
        print(f"  !  MISMATCH {tag}: {eq}   z3 found witness x={w} but "
              f"the engine gives {va} == {vb} — the translation does "
              f"not match the engine{dom}   z3 {dt * 1000:.1f}ms")
        return "MISMATCH"
    print(f"  ?  UNKNOWN  {tag}: {eq}   z3 {dt * 1000:.1f}ms")
    return "UNKNOWN"


def mint_rule(m, chain, source):
    """Enter a chain into the facts layer exactly as structure_hunt
    mints (op_rule, origin=induced, name before ' =' is load-bearing)."""
    name = f"op{len(m.facts_query(pred='op_rule')) + 1}"
    m.fact_add("op_rule", chain, kind="rule", origin="induced",
               text=f"{name} = {' then '.join(chain)}", sources=[source])
    return name


T_ALL = time.perf_counter()
print("=" * 64)
print("  PROOF PROBE — extensional 0..24 upgraded to Z3 proofs")
print(f"  z3 {z3.get_version_string()}")
print("=" * 64)

m = Isaac(fast=True)
m.wave_logging = False
if not (hasattr(m, "meta_hunt") and hasattr(m, "induce_op")):
    print("SKIP: level-2 engine not built")
    sys.exit(77)

# ── stage 1: the engine's own finds, proved ─────────────────────────
t1 = time.perf_counter()
print("\nstage 1 — the engine's own discovered identities and inverses")
pairs_31 = [(1, 1), (4, 10), (7, 19), (9, 25), (12, 34)]      # y = 3x-2
pairs_51 = [(1, 6), (3, 16), (6, 31), (10, 51), (13, 66)]     # y = 5x+1
c1 = m.induce_op(pairs_31)
r1 = mint_rule(m, c1, "planted pairs y=3x-2 (proof probe)") if c1 else None
c2 = m.induce_op(pairs_51)
r2 = mint_rule(m, c2, "planted pairs y=5x+1 (proof probe)") if c2 else None
c3 = m.induce_op(pairs_31)      # same pairs again -> library reuse
r3 = mint_rule(m, c3, "planted pairs y=3x-2 again (proof probe)") if c3 else None
print(f"  minted: {r1} = {show(c1) if c1 else 'refused'}")
print(f"  minted: {r2} = {show(c2) if c2 else 'refused'}")
print(f"  minted: {r3} = {show(c3) if c3 else 'refused'}"
      "   (duplicate function under a new name, on purpose)")
check("induce_op produced chains for all three planted rule sets",
      None not in (c1, c2, c3))
meta = m.meta_hunt()
print(f"  meta_hunt: {len(meta['identities'])} identities, "
      f"{len(meta['inverses'])} inverses (each checked on 0..24 only)")
check("meta_hunt found the duplicate rule (the extensional identity)",
      c3 is not None and ((r1, r3) in meta["identities"]
                          or (r3, r1) in meta["identities"]))
check("meta_hunt found the inverse pair dec/inc",
      ("dec", "inc") in meta["inverses"])
check("meta_hunt found the inverse pair shr/dbl (proof deferred)",
      ("shr", "dbl") in meta["inverses"])

verdicts = []
for na, nb in meta["identities"]:
    verdicts.append(prove(m, "engine identity", [na], [nb]))
for na, nb in meta["inverses"]:
    # "na undoes nb": apply nb then na, get x back (the empty chain)
    verdicts.append(prove(m, "engine inverse", [nb, na], []))
check("every engine find proved for ALL integers (none refuted; "
      "only shr-bearing ones deferred)",
      all(v in ("THEOREM", "SKIP") for v in verdicts)
      and verdicts.count("THEOREM") >= 6)
print(f"  stage 1 wall-clock: {time.perf_counter() - t1:.2f}s")

# ── stage 2: composition laws, constructed and proved ───────────────
t2 = time.perf_counter()
print("\nstage 2 — composition laws")
laws = [
    ("composition", ["mul_k(2)", "mul_k(3)"], ["mul_k(6)"]),
    ("composition", ["add_k(7)", "add_k(5)"], ["add_k(12)"]),
    ("inverse law", ["inc", "dec"], []),
    ("inverse law", ["neg", "neg"], []),
    ("canonical",   ["dbl"], ["mul_k(2)"]),
    ("sign law",    ["neg", "sq"], ["sq"]),
    ("rearranged",  ["dec", "dbl", "inc", "inc"], ["dbl"]),
]
stage2 = [prove(m, tag, a, b) for tag, a, b in laws]
check("all 7 composition laws proved", stage2.count("THEOREM") == 7)
print(f"  stage 2 wall-clock: {time.perf_counter() - t2:.2f}s")

# ── stage 3: a claim that MUST fall ─────────────────────────────────
t3 = time.perf_counter()
print("\nstage 3 — a deliberate non-theorem")
v3 = prove(m, "non-theorem", ["dbl", "inc"], ["inc", "dbl"])
check("dbl-then-inc == inc-then-dbl REFUTED with a concrete witness",
      v3 == "REFUTED" and len(REFUTATIONS) >= 1)
print(f"  stage 3 wall-clock: {time.perf_counter() - t3:.2f}s")

# ── stage 4: what the 25-point spot check cannot see ────────────────
t4 = time.perf_counter()
print("\nstage 4 — the payoff: extensionally accepted, Z3-refuted")
m2 = Isaac(fast=True)   # fresh instance: its rule ledger starts empty,
m2.wave_logging = False  # so its op1/op2 are NOT stage 1's op1/op2
ca = ["shr"] * 5        # x >> 5   (0 on all of 0..31)
cb = ["shr"] * 6        # x >> 6   (0 on all of 0..63)
ext_says_equal = m2._op_ext_eq(ca, cb)
check("engine's extensional court (0..24) calls shr x5 == shr x6 EQUAL",
      ext_says_equal)
p1 = mint_rule(m2, ca, "constructed (proof probe, stage 4)")
p2 = mint_rule(m2, cb, "constructed (proof probe, stage 4)")
print(f"  fresh instance; planted: {p1} = {show(ca)}, {p2} = {show(cb)}")
meta2 = m2.meta_hunt()
minted_false = ((p1, p2) in meta2["identities"]
                or (p2, p1) in meta2["identities"])
check("meta_hunt MINTED the false identity into the facts layer "
      f"({p1} == {p2})",
      minted_false and len(m2.facts_query(pred="op_identity")) >= 1)

# the guarded shr model, checked against the engine before use:
# engine shr = x >> 1 for x >= 0; z3 model = integer div by 2 under
# an input >= 0 guard (for a positive divisor, z3 div is floor div).
sample = list(range(0, 81)) + [127, 128, 1000, 4095, 4096]
model_ok = True
for chain in (ca, cb):
    g = []
    e = to_z3(m2, chain, X, allow_shr=True, guards=g)
    for v in sample:
        zv = z3.simplify(z3.substitute(e, (X, z3.IntVal(v)))).as_long()
        if zv != m2._ind_apply(chain, v):
            model_ok = False
check(f"shr model court: z3 value == engine value at all "
      f"{len(sample)} sample points, both chains", model_ok)
check("engine refuses shr below zero (so proofs carry the x >= 0 "
      "domain guard)", m2._ind_apply(["shr"], -1) is None)

v4 = prove(m2, "payoff", [p1], [p2], allow_shr=True)
first_div = next(v for v in range(0, 200)
                 if m2._ind_apply(ca, v) != m2._ind_apply(cb, v))
print(f"  first divergence by direct scan: x = {first_div} "
      f"({m2._ind_apply(ca, first_div)} != {m2._ind_apply(cb, first_div)}) "
      "— the 0..24 spot check stops 8 short of it")
check("Z3 REFUTED the identity the extensional court accepted",
      v4 == "REFUTED")
check("first divergence sits just past the extensional range (x=32)",
      first_div == 32)
# the one engine find stage 1 had to skip, now proved under its guard
v4b = prove(m2, "engine inverse (deferred)", ["dbl", "shr"], [],
            allow_shr=True)
check("shr undoes dbl proved for all x >= 0 (the honest domain)",
      v4b == "THEOREM")
print(f"  stage 4 wall-clock: {time.perf_counter() - t4:.2f}s")

# ── the court ───────────────────────────────────────────────────────
print("\ncourt")
check(f"at least 5 theorems proven (got {len(THEOREMS)})",
      len(THEOREMS) >= 5)
check(f"at least 1 claim refuted with a printed witness "
      f"(got {len(REFUTATIONS)})", len(REFUTATIONS) >= 1)
check("the extensional-accepts / Z3-refutes case was demonstrated",
      ext_says_equal and minted_false and v4 == "REFUTED")
print(f"\n  totals: {len(THEOREMS)} theorems, {len(REFUTATIONS)} refuted, "
      f"{len(SKIPPED)} deferred (shr)   z3 solver time "
      f"{Z3_TOTAL[0] * 1000:.1f}ms   wall-clock "
      f"{time.perf_counter() - T_ALL:.2f}s")

print(f"\nGATE: {'PASS' if not FAILS else 'FAIL (' + ', '.join(FAILS) + ')'}")
sys.exit(1 if FAILS else 0)
