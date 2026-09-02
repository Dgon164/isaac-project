"""THE EXPERT PROBE — MYCIN/XCON shape on the owner's THRESHOLD RACE.

Structure/filling split, straight from the facts-layer ruling:
  fillings  = ground parameter rows per material:
                threshold(material, process, temp_c)   value known
                threshold_unknown(material, process)   declared, unmeasured
                no_threshold(material, process)        told: does not exist
  structure = ONE universal rule, admitted to the facts layer as a
              rule fact: at temperature T the outcome is the process
              attached to the LOWEST critical threshold crossed;
              nothing crossed -> unchanged (solid).

The consult is data-driven: verdict(material, T) reads its premises
from the facts layer — no per-material code anywhere. Every verdict
returns a receipt naming which rows were compared, which crossed, and
which won the race (MYCIN's lesson: explanation by trace). Honest
edges: an unknown material is REFUSED and files an ask; a declared-
but-unmeasured threshold QUALIFIES the verdict with the missing
premise named and files an ask (closed-world guard: missing != false).

Two-tier gate, same shape as ask_logic: the race computes, then z3
independently replays every comparison claim as a real-number
constraint (negation unsat = proven). Proven + no missing premise ->
CERTIFIED, and the verdict enters the facts layer with sources.
QUALIFIED and REFUSED verdicts stay out. The log stays pure.

Boundary note: the engine's ask_logic road (clingo + conjunctive-join
replay) cannot carry this rule — the race needs real-number comparison
and a minimum, and the join replayer has no words for either. The
consult therefore runs beside ask_logic with the same gate shape and
z3 standing where _replay stands.
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

from isaac import Isaac  # noqa: E402

FAILS = []


def check(name, ok):
    print(f"  {'v' if ok else 'x'}  {name}")
    if not ok:
        FAILS.append(name)


def z3_prove(claims):
    """Independent replay of the comparison claims. claims are ground
    triples (lhs, op, rhs) over real numbers; z3 must find the
    negation of their conjunction unsatisfiable. Shares no comparison
    code with the race itself — that is the whole point."""
    zc = []
    for lhs, op, rhs in claims:
        a, b = z3.RealVal(str(lhs)), z3.RealVal(str(rhs))
        zc.append(a >= b if op == ">=" else
                  a < b if op == "<" else a <= b)
    s = z3.Solver()
    s.add(z3.Not(z3.And(*zc)))
    return s.check() == z3.unsat


def consult(m, rule_id, material, temp_t):
    """One expert consult: verdict(material, T) from facts + the
    threshold-race rule. Returns dict(verdict, tier, receipt,
    missing, ask, ms). The rule reads every premise from the facts
    layer; no material is named in this function."""
    t0 = time.perf_counter()
    rows = [f for f in m.facts_query(pred="threshold")
            if f["args"][0] == material]
    unknowns = [f for f in m.facts_query(pred="threshold_unknown")
                if f["args"][0] == material]
    absents = [f for f in m.facts_query(pred="no_threshold")
               if f["args"][0] == material]
    rec = [f"consult: {material} at {temp_t} C  "
           f"(threshold_race, rule fact #{rule_id})"]

    if not rows and not unknowns:
        aid = m.ask_file(["threshold", material, "?"],
                         "unknown material — no threshold rows in "
                         "the facts layer", road="consult")
        rec.append(f"  no threshold rows for '{material}' -> REFUSED"
                   f"; ask #{aid} filed")
        return dict(verdict=None, tier="REFUSED", receipt=rec,
                    missing=[], ask=aid,
                    ms=(time.perf_counter() - t0) * 1e3)

    crossed, claims = [], []
    for f in rows:
        proc, c = f["args"][1], f["args"][2]
        if temp_t >= c:
            crossed.append((c, proc, f["id"]))
            claims.append((temp_t, ">=", c))
            rec.append(f"  compared: {proc}@{c} <= {temp_t} -> "
                       f"CROSSED  (fact #{f['id']})")
        else:
            claims.append((temp_t, "<", c))
            rec.append(f"  compared: {proc}@{c} > {temp_t} -> not "
                       f"crossed  (fact #{f['id']})")
    for f in absents:
        rec.append(f"  {f['args'][1]}: no such threshold for "
                   f"{material} (told, fact #{f['id']}) — never in "
                   f"the race")

    if crossed:
        crossed.sort(key=lambda r: r[0])
        wtemp, wproc, _ = crossed[0]
        for c, _proc, _fid in crossed[1:]:
            claims.append((wtemp, "<=", c))
        order = ", ".join(f"{p}@{c}" for c, p, _ in crossed)
        rec.append(f"  race among crossed: [{order}] -> lowest is "
                   f"{wproc}@{wtemp} -> {wproc} happens first")
        verdict, bound = wproc, wtemp
    else:
        rec.append(f"  nothing crossed at {temp_t} C -> unchanged "
                   f"(solid)")
        verdict, bound = "unchanged", temp_t

    proven = z3_prove(claims) if claims else True
    rec.append(f"  checker: z3 replayed {len(claims)} comparison "
               f"claims -> "
               f"{'proven (negation unsat)' if proven else 'FAILED'}")

    missing = [f["args"][1] for f in unknowns]
    aid = None
    if not proven:
        tier = "REJECTED"
        rec.append("  REJECTED: the checker disagrees with the race")
    elif missing:
        tier = "QUALIFIED"
        for f in unknowns:
            proc = f["args"][1]
            aid = m.ask_file(["threshold", material, proc],
                             "consult leaned on a threshold the "
                             "facts do not hold (missing != false)",
                             road="consult")
            rec.append(f"  missing premise: {proc} temperature of "
                       f"{material} is declared but unmeasured "
                       f"(fact #{f['id']}) — if it lies at or below "
                       f"{bound} the outcome changes; ask #{aid} "
                       f"filed")
        rec.append(f"  QUALIFIED verdict: {verdict}, subject to the "
                   f"named missing premise — kept OUT of the facts "
                   f"layer")
    else:
        tier = "CERTIFIED"
        m.fact_add("verdict", [material, temp_t, verdict],
                   kind="ground", origin="certified",
                   sources=[rule_id] + [f["id"] for f in rows],
                   text=f"at {temp_t} C, {material} -> {verdict}")
        rec.append(f"  CERTIFIED verdict: {verdict} — entered the "
                   f"facts layer with sources")
    return dict(verdict=verdict, tier=tier, receipt=rec,
                missing=missing, ask=aid,
                ms=(time.perf_counter() - t0) * 1e3)


# ── the fillings: parameter rows per material (approximate C) ────
ROWS = [
    ("ice", "melt", 0), ("ice", "boil", 100),
    ("wax", "melt", 60), ("wax", "boil", 370),
    ("iron", "melt", 1538), ("iron", "boil", 2862),
    ("copper", "melt", 1085), ("copper", "boil", 2562),
    ("wood", "decompose", 300),
    ("sugar", "caramelize", 160), ("sugar", "melt", 186),
    ("dry_ice", "sublimate", -78),
    ("plastic", "melt", 130),
]
ABSENT = [("wood", "melt"), ("wood", "boil")]
UNKNOWN = [("plastic", "decompose")]

t_all = time.perf_counter()
t0 = time.perf_counter()
m = Isaac(fast=True)
m.wave_logging = False
for mat, proc, c in ROWS:
    m.fact_add("threshold", [mat, proc, c], kind="ground",
               origin="told", text=f"{mat}: {proc} at {c} C")
for mat, proc in ABSENT:
    m.fact_add("no_threshold", [mat, proc], kind="ground",
               origin="told",
               text=f"{mat} has no {proc} threshold")
for mat, proc in UNKNOWN:
    m.fact_add("threshold_unknown", [mat, proc], kind="ground",
               origin="told",
               text=f"{mat} {proc} temperature not measured")

# the structure: ONE rule fact over the property variables
RULE_ID = m.fact_add(
    "threshold_race", [], kind="rule", origin="admitted",
    text="verdict(M,T) = process of the LOWEST c with c <= T among "
         "threshold(M,P,c); none crossed -> unchanged; declared-"
         "unmeasured threshold -> verdict qualified by name; no rows "
         "at all -> refuse and ask")
t_load = (time.perf_counter() - t0) * 1e3
n_log0 = len(m.observed_sequences)
print(f"facts loaded: {len(m.facts)} rows ({len(ROWS)} thresholds, "
      f"{len(ABSENT)} told-absent, {len(UNKNOWN)} declared-unknown, "
      f"1 rule)  [{t_load:.1f} ms]")

# ── the court: consults with expected verdict + expected tier ────
CASES = [
    ("wood", 400, "decompose", "CERTIFIED"),    # owner's own example
    ("sugar", 200, "caramelize", "CERTIFIED"),  # 160 beats melt@186
    ("sugar", 170, "caramelize", "CERTIFIED"),
    ("ice", 50, "melt", "CERTIFIED"),
    ("ice", 150, "melt", "CERTIFIED"),          # melt first, then boil
    ("iron", 800, "unchanged", "CERTIFIED"),    # nothing crossed
    ("iron", 1600, "melt", "CERTIFIED"),
    ("dry_ice", -40, "sublimate", "CERTIFIED"),
    ("dry_ice", -100, "unchanged", "CERTIFIED"),
    ("wax", 60, "melt", "CERTIFIED"),           # exact-boundary cross
    ("copper", 2600, "melt", "CERTIFIED"),
    ("plastic", 200, "melt", "QUALIFIED"),      # missing premise
    ("granite", 500, None, "REFUSED"),          # unknown material
]

t0 = time.perf_counter()
results = {}
right = 0
for mat, temp_c, want, want_tier in CASES:
    r = consult(m, RULE_ID, mat, temp_c)
    results[(mat, temp_c)] = r
    for line in r["receipt"]:
        print(line)
    hit = (r["verdict"] == want and r["tier"] == want_tier)
    right += hit
    print(f"  verdict: {r['verdict']}  [{r['tier']}]  expected "
          f"{want} [{want_tier}]  {'v' if hit else 'x'}  "
          f"[{r['ms']:.2f} ms]\n")
t_court = (time.perf_counter() - t0) * 1e3

print(f"consults correct: {right}/{len(CASES)} "
      f"({100.0 * right / len(CASES):.0f}% — verdict AND tier)  "
      f"[court {t_court:.1f} ms]")
check("every consult matched expected verdict and tier",
      right == len(CASES))

wood = results[("wood", 400)]
check("wood at 400 C decomposes, does NOT melt — receipt says melt "
      "was never in the race (told absent)",
      wood["verdict"] == "decompose" and
      any("no such threshold" in ln and "melt" in ln
          for ln in wood["receipt"]))
sug = results[("sugar", 200)]
check("sugar at 200 C: melt@186 crossed but LOST the race to "
      "caramelize@160 — the receipt shows both in order",
      any("caramelize@160, melt@186" in ln and "lowest" in ln
          for ln in sug["receipt"]))
pla = results[("plastic", 200)]
check("qualified verdict NAMES the missing premise (decompose)",
      pla["missing"] == ["decompose"] and
      any("missing premise: decompose" in ln
          for ln in pla["receipt"]))
check("missing premise filed an ask (closed-world guard)",
      pla["ask"] is not None and any(
          a["question"] == ["threshold", "plastic", "decompose"]
          for a in m.asks_open()))
gra = results[("granite", 500)]
check("unknown material refused AND filed an ask",
      gra["tier"] == "REFUSED" and gra["ask"] is not None and any(
          a["question"] == ["threshold", "granite", "?"]
          for a in m.asks_open()))
n_open = len(m.asks_open())
again = consult(m, RULE_ID, "granite", 500)
check("second granite consult reuses the SAME open ask (dedupe)",
      again["ask"] == gra["ask"] and len(m.asks_open()) == n_open)

n_cert = len(CASES) - 2  # all but QUALIFIED plastic + REFUSED granite
check(f"the {n_cert} certified verdicts entered the facts layer "
      f"with sources",
      len(m.facts_query(pred="verdict", origin="certified"))
      == n_cert and all(
          f["sources"] and f["sources"][0] == RULE_ID
          for f in m.facts_query(pred="verdict")))
check("qualified and refused verdicts stayed OUT of the facts layer",
      not [f for f in m.facts_query(pred="verdict")
           if f["args"][0] in ("plastic", "granite")])
check("every receipt cites the rule fact (structure, not "
      "per-material code)",
      all(f"rule fact #{RULE_ID}" in r["receipt"][0]
          for r in results.values()))
check("z3 replay proved the comparison claims of every consult "
      "that compared",
      not any("FAILED" in ln for r in results.values()
              for ln in r["receipt"]))
check("the LOG stayed pure (facts layer only)",
      len(m.observed_sequences) == n_log0)

print(f"\nopen asks ({len(m.asks_open())}):")
for a in m.asks_open():
    print(f"  ask #{a['id']}: {' '.join(a['question'])}  — "
          f"{a['reason']}")

print(f"\nwall clock: load {t_load:.1f} ms | court {t_court:.1f} ms "
      f"| total {(time.perf_counter() - t_all) * 1e3:.1f} ms")
print(f"\nGATE: {'PASS' if not FAILS else 'FAIL (' + ','.join(FAILS) + ')'}")
sys.exit(1 if FAILS else 0)
