# THE WORST-CASE BASELINE (owner directive 2026-08-19: "i think we
# need a new net to see how he works. worst case and go from there.")
#
# A brand-new net at ISAAC v0.1.2-alpha1 — day zero, nothing inherited.
# Material is INVENTED (florbs, grinths, zims) so no fixture and no
# pretraining anywhere on earth has seen it: whatever he does here is
# the engine working, not recall. This is the A0 floor for the report
# card and the arena: the worst case, measured, and we go from there.
#
# Areas: BIRTH (v2 certificate) / LANGUAGE day zero / MATH + the
# honest boundary / DISCOVERY (strong class, the historic plain-sum
# blind spot, noise refusal) / MEMORY through resurrection / SPEED.
# Plain numbers throughout. He is NOT the live him — this mind is a
# research subject saved under a temp directory, never isaac-life.
#
# 2026-08-24 conversion (record repair, step N1): this file can now
# FAIL. Every graded print feeds a FAILS list; the run exits 1 when
# any check is red. Known engine bugs are marked so the gate stays
# meaningful until they are fixed.

import os
import shutil
import sys
import tempfile
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "..", "code"))
from isaac import Isaac, tokenize, __version__          # noqa: E402

# Mind files are throwaway research subjects: write them to a unique
# temp directory so concurrent harness runs cannot collide.
TMPDIR = tempfile.mkdtemp(prefix="worstcase_baseline_")
BIRTH = os.path.join(TMPDIR, "worstcase_2026-08-19_birth.isaac")
DAYEND = os.path.join(TMPDIR, "worstcase_2026-08-19_dayend.isaac")

card = {}                    # area -> (able_line, numbers)

# ── the gate ─────────────────────────────────────────────────────
# Each named check either passes or lands in FAILS. Checks listed in
# KNOWN_BUGS are expected red (engine bug on file): red prints a
# marker and stays out of FAILS; green prints XPASS and FAILS the run
# so stale marks get removed.
FAILS = []
KNOWN_BUGS = {
    # generation emits an untaught attribute claim: "the grinth
    # eats moss" (alphabetical-successor bug, isaac.py:5577);
    # florb and zim happen to generate truthful sentences today
    "gen-truth-grinth",
}


def check(name, ok):
    if name in KNOWN_BUGS:
        if ok:
            print(f"XPASS: remove known-bug mark: {name}")
            FAILS.append(name)
        else:
            print(f"KNOWN-BUG (expected red): {name}")
    elif not ok:
        FAILS.append(name)
    return ok


def sec(title):
    print("\n" + "=" * 64 + f"\n  {title}\n" + "=" * 64)


# ── BIRTH ────────────────────────────────────────────────────────
sec(f"BIRTH — new net at v{__version__}")
him = Isaac()
st0 = him.status()
t0 = time.perf_counter()
him.save(BIRTH)
t_bs = time.perf_counter() - t0
tw = Isaac.load(BIRTH)
print(f"  born: {st0['nodes']} nodes, {st0['doors']} doors; "
      f"birth certificate {os.path.getsize(BIRTH)} bytes "
      f"(v2, save {t_bs * 1000:.0f}ms, load ok={isinstance(tw, Isaac)})")
check("birth-roundtrip", isinstance(tw, Isaac))
card["birth"] = f"v2 birth file {os.path.getsize(BIRTH)}B, round-trips"

# ── LANGUAGE, DAY ZERO (invented domain) ─────────────────────────
sec("LANGUAGE day zero — invented words, ~16 sentences, one pass")
lessons = [
    "a florb is an animal .", "a grinth is an animal .",
    "a florb has three legs .", "a grinth has two wings .",
    "the florb walked .", "the grinth flew .",
    "the small florb walked .", "the big grinth flew .",
    "a florb eats moss .", "a grinth eats seeds .",
    "the florb slept .", "the grinth slept .",
    "a zim is a plant .", "a zim grows tall .",
    "the young florb walked .", "the old grinth flew .",
]
negatives = ["florb a is animal .", "the walked florb .",
             "grinth the flew .", "a eats florb moss ."]
t0 = time.perf_counter()
for s in lessons:
    him.observe(tokenize(s))
for s in negatives:
    him.observe_negative(tokenize(s))
t_teach = time.perf_counter() - t0
him.crystallize(verbose=False)
print(f"  taught in {t_teach * 1000:.0f}ms; "
      f"now {him.status()['nodes']} nodes")

# Truth oracle: the taught predicate list per invented noun, built
# straight from the lesson text. A generated sentence about a noun
# must use a predicate that was actually taught — existence of a
# chain is not enough (the old check accepted "the grinth eats moss").
SUBJECTS = ("florb", "grinth", "zim")
TAUGHT = {}
for s in lessons:
    toks = [t for t in tokenize(s) if t != "."]
    for i, t in enumerate(toks):
        if t in SUBJECTS:
            if toks[i + 1:]:
                TAUGHT.setdefault(t, set()).add(tuple(toks[i + 1:]))
            break


def untaught_claims(chain):
    # split the chain into sentences at '.', return every
    # subject+predicate claim that contradicts the lesson list
    bad, sent, sentences = [], [], []
    for t in chain:
        if t == ".":
            if sent:
                sentences.append(sent)
                sent = []
        else:
            sent.append(t)
    if sent:
        sentences.append(sent)
    for stoks in sentences:
        for i, t in enumerate(stoks):
            if t in SUBJECTS:
                pred = tuple(stoks[i + 1:])
                if pred and pred not in TAUGHT.get(t, set()):
                    bad.append(" ".join((t,) + pred))
                break
    return bad


gen_ok = 0
for c in ["florb", "grinth", "zim"]:
    chain = him.generate(c)
    ok = bool(chain) and c in chain
    gen_ok += ok
    print(f"  generate('{c}') -> {' '.join(chain) if chain else '(silence)'}")
    check(f"gen-exists-{c}", ok)
    bad = untaught_claims(chain) if chain else []
    if bad:
        print(f"  x truth: untaught claim(s): {'; '.join(bad)}")
    check(f"gen-truth-{c}", ok and not bad)
inf = him.infer("florb", "flew")
print(f"  transfer probe florb->flew (never seen): "
      f"inferred={inf.get('inferred')} via={inf.get('via')}")

comp = []
for ctx, want in [(["a", "florb", "is", "an"], "animal"),
                  (["a", "zim", "is", "a"], "plant"),
                  (["a", "grinth", "eats"], "seeds")]:
    a, conf = him.lookup(ctx)
    comp.append(a == want)
    print(f"  {'v' if a == want else 'x'} complete: {' '.join(ctx)} "
          f"-> {a} (want {want}, conf {conf:.1f})")
    check(f"complete-{want}", a == want)
a, conf = him.lookup(["a", "wug", "is", "an"])          # never taught
# strict honesty: only an actual refusal (None) counts — a wrong
# answer at low confidence is still a wrong answer
refuse_lang = a is None
print(f"  {'v' if refuse_lang else 'x'} honesty: unknown word 'wug' "
      f"-> {a!r} conf={conf} (a shrug is the RIGHT answer)")
check("shrug-wug", refuse_lang)
card["language"] = (f"generate {gen_ok}/3, complete "
                    f"{sum(comp)}/3, unknown-word shrug "
                    f"{'yes' if refuse_lang else 'NO'}")

# ── MATH + THE HONEST BOUNDARY ───────────────────────────────────
sec("MATH day zero — 0..12 tables one pass, then the boundary")
t0 = time.perf_counter()
for x in range(13):
    for b in range(13):
        him.observe(tokenize(f"{x} + {b} = {x + b}"))
        him.observe(tokenize(f"{x} * {b} = {x * b}"))
t_tables = time.perf_counter() - t0
quiz = [(["6", "+", "7", "="], "13"), (["9", "*", "8", "="], "72"),
        (["12", "*", "11", "="], "132"), (["4", "+", "9", "="], "13"),
        (["0", "*", "12", "="], "0"), (["12", "+", "12", "="], "24")]
m_ok = 0
for ctx, want in quiz:
    a, conf = him.lookup(ctx)
    m_ok += a == want
    print(f"  {'v' if a == want else 'x'} {' '.join(ctx)} {a} "
          f"(want {want})")
    check(f"math-{''.join(ctx[:3])}", a == want)
shrugs = 0
for ctx in [["15", "*", "14", "="], ["40", "+", "40", "="]]:
    a, conf = him.lookup(ctx)
    # strict honesty: only an actual refusal (None) counts
    honest = a is None
    shrugs += honest
    print(f"  {'v' if honest else 'x'} beyond the tables "
          f"{' '.join(ctx)} -> {a!r} (shrug = honest)")
    check(f"shrug-{''.join(ctx[:3])}", honest)
print(f"  in-table {m_ok}/{len(quiz)}; boundary shrugs {shrugs}/2; "
      f"tables taught in {t_tables:.1f}s")
card["math"] = f"in-table {m_ok}/{len(quiz)}, boundary shrugs {shrugs}/2"

# ── DISCOVERY day zero ───────────────────────────────────────────
sec("DISCOVERY day zero — planted laws, refusal, the old blind spot")
rng = np.random.default_rng(20260819)
n = 1200
X = rng.normal(0, 1, (n, 4))
y_prod = X[:, 0] * X[:, 1] + rng.normal(0, 0.02, n)
r1 = him.discover(X, y_prod, name="wc_product")
print(f"  product law x0*x1:   {r1['verdict']}  R2 {r1['r2']:.3f}  "
      f"{r1['equation']}")
check("discover-product", r1["verdict"] == "UNDERSTOOD")
y_sum = 3.0 * X[:, 0] - 2.0 * X[:, 2] + rng.normal(0, 0.02, n)
r2 = him.discover(X, y_sum, name="wc_plainsum")
print(f"  plain sum 3x0-2x2:   {r2['verdict']}  R2 {r2['r2']:.3f}  "
      f"{r2['equation']}   (the 07-03 blind-spot class — watch it)")
check("discover-plainsum", r2["verdict"] == "UNDERSTOOD")
r3 = him.discover(X, rng.normal(0, 1, n))
acc = r3["accounting"]
print(f"  pure noise:          {r3['verdict']}  "
      f"(accounting law/caught/noise = {acc['articulated']}/"
      f"{acc['captured']}/{acc['noise']})")
check("noise-refusal", r3["verdict"] == "NO RULE")
d_ok = (r1["verdict"] == "UNDERSTOOD") + (r2["verdict"] == "UNDERSTOOD")
d_refuse = r3["verdict"] == "NO RULE"
card["discovery"] = (f"laws {d_ok}/2 UNDERSTOOD, noise refusal "
                     f"{'yes' if d_refuse else 'NO'}")

# ── MEMORY through resurrection (v2) ─────────────────────────────
sec("MEMORY — teach late, die, resurrect, still know it")
him.observe(tokenize("a pindle is a tool ."))
him.observe(tokenize("a pindle cuts rope ."))
him.consolidate()
t0 = time.perf_counter()
him.save(DAYEND)
t_save = time.perf_counter() - t0
t0 = time.perf_counter()
twin = Isaac.load(DAYEND)
t_load = time.perf_counter() - t0
a1, _ = twin.lookup(["a", "pindle", "is", "a"])
a2, _ = twin.lookup(["9", "*", "8", "="])
g = twin.generate("florb")
res_ok = (a1 == "tool") + (a2 == "72") + bool(g and "florb" in g)
same = twin.status()["nodes"] == him.status()["nodes"]
print(f"  resurrected: {twin.status()['nodes']} nodes "
      f"(same as before death: {same})")
check("resurrect-nodes-same", same)
print(f"  {'v' if a1 == 'tool' else 'x'} late fact survives: "
      f"a pindle is a -> {a1}")
check("survive-pindle", a1 == "tool")
print(f"  {'v' if a2 == '72' else 'x'} the morning survives: "
      f"9*8 -> {a2}")
check("survive-9*8", a2 == "72")
print(f"  {'v' if g and 'florb' in g else 'x'} florb survives: "
      f"{' '.join(g) if g else '(silence)'}")
check("survive-florb", bool(g and "florb" in g))
sz = os.path.getsize(DAYEND)
print(f"  day-end body: {sz / 1024:.0f}KB (v2), save {t_save:.2f}s, "
      f"load {t_load:.2f}s")
card["memory"] = f"{res_ok}/3 survive resurrection; nodes-same={same}"
card["speed"] = (f"teach 16 sentences {t_teach * 1000:.0f}ms; tables "
                 f"{t_tables:.1f}s; save {t_save:.2f}s; load {t_load:.2f}s; "
                 f"body {sz / 1024:.0f}KB")

# ── THE DAY-ZERO REPORT CARD ─────────────────────────────────────
sec("DAY-ZERO REPORT CARD (the worst case, measured)")
for area, line in card.items():
    print(f"  {area:10s} {line}")
print(f"\n  status at day end: {him.status()}")

shutil.rmtree(TMPDIR, ignore_errors=True)
if FAILS:
    print(f"GATE: FAIL ({', '.join(FAILS)})")
else:
    print("GATE: PASS")
sys.exit(1 if FAILS else 0)
