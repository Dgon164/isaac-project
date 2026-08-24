# Teardown probe: is the bridge's leg-verification a soundness
# guarantee or a provenance stamp?  Recreates the exact mind of
# rebuild/logic_bridge_probe.py (read-only on the repo; in-memory
# mind only), then runs the RIGHT rule and two deliberately WRONG
# rules through (a) a generic "every leg exists in his store" check
# and (b) the probe's actual verify() (which adds the zc==z join).
# Also autopsies the native 0/100 control.
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "..", "code"))
from isaac import Isaac, tokenize  # noqa: E402

try:
    import clingo  # noqa: E402
except ImportError:
    print("SKIP: clingo module not installed (pip install clingo)")
    sys.exit(77)

# Failed check names collect here; the gate at the bottom exits
# nonzero if any check failed.
FAILS = []


def check(name, ok):
    if not ok:
        FAILS.append(name)

W = ["zero", "one", "two", "three", "four", "five", "six", "seven",
     "eight", "nine", "ten", "eleven", "twelve", "thirteen",
     "fourteen", "fifteen", "sixteen", "seventeen", "eighteen"]

m = Isaac()
for a in range(10):
    for b in range(10):
        m.observe(tokenize(f"{a} + {b} = {a + b}"))
for d in range(19):
    m.observe(tokenize(f"{W[d]} = {d}"))
m.consolidate()

print("== A. native-control autopsy ==")
print("A1 'plus' ever observed:",
      "plus" in m.net.doors or "plus" in m.net.preds)
print("A2 lookup [three plus four =] :", m.lookup(["three", "plus", "four", "="]))
print("A3 lookup [three + four =]    :", m.lookup(["three", "+", "four", "="]))
xa = m.lookup(["three", "="])[0]
xb = m.lookup(["four", "="])[0]
z = m.lookup([xa, "+", xb, "="])[0]
back = [w for w in W if m.lookup([w, "="])[0] == z]
print(f"A4 3-lookup native chain: three->{xa}, four->{xb}, "
      f"{xa}+{xb}->{z}, word->{back}")

facts = []
for seq in m.observed_sequences:
    if (len(seq) == 5 and seq[1] == "+" and seq[3] == "="
            and all(t.isdigit() for t in (seq[0], seq[2], seq[4]))):
        facts.append(f"sum({seq[0]},{seq[2]},{seq[4]}).")
    elif (len(seq) == 3 and seq[1] == "=" and seq[0].isalpha()
            and seq[2].isdigit()):
        facts.append(f"word({seq[0]},{seq[2]}).")
facts = sorted(set(facts))
base = "\n".join(facts)
print(f"\n== B. export == {len(facts)} facts (probe reported 119)")


def run_rule(rule):
    ctl = clingo.Control(["--warn=none"])
    ctl.add("base", [], base + "\n" + rule)
    ctl.ground([("base", [])])
    out = []

    def g(model):
        for s in model.symbols(atoms=True):
            if s.name == "word_sum":
                out.append(tuple(str(x) for x in s.arguments))
    ctl.solve(on_model=g)
    return out


def legs_exist(a_w, b_w, c_w):
    """Generic provenance check: every leg EXISTS in his store
    (what 'verified leg by leg against his own store' literally
    says) -- WITHOUT the final equality join."""
    xa, _ = m.lookup([a_w, "="])
    xb, _ = m.lookup([b_w, "="])
    if xa is None or xb is None:
        return False
    z, _ = m.lookup([xa, "+", xb, "="])
    zc, _ = m.lookup([c_w, "="])
    return z is not None and zc is not None


def probe_verify(a_w, b_w, c_w):
    """The bridge probe's actual verify(): same legs PLUS zc == z."""
    xa, _ = m.lookup([a_w, "="])
    xb, _ = m.lookup([b_w, "="])
    if xa is None or xb is None:
        return False
    z, _ = m.lookup([xa, "+", xb, "="])
    zc, _ = m.lookup([c_w, "="])
    return z is not None and zc == z


RIGHT = ("word_sum(A,B,C) :- word(A,X), word(B,Y), "
         "sum(X,Y,Z), word(C,Z).")
WRONG_JOIN = ("word_sum(A,B,C) :- word(A,X), word(B,Y), "
              "sum(X,Y,Z), word(C,W).")   # dropped the Z=W join
WRONG_OFF1 = ("word_sum(A,B,C) :- word(A,X), word(B,Y), "
              "sum(X,Y,Z), word(C,Z+1).")  # off-by-one

print("\n== C. wrong rules vs the two verification notions ==")
for name, rule in [("RIGHT           ", RIGHT),
                   ("WRONG dropped-join", WRONG_JOIN),
                   ("WRONG off-by-one ", WRONG_OFF1)]:
    atoms = run_rule(rule)
    wrong = [(a, b, c) for a, b, c in atoms
             if c != W[W.index(a) + W.index(b)]]
    le_wrong = sum(1 for a, b, c in wrong if legs_exist(a, b, c))
    pv_wrong = sum(1 for a, b, c in wrong if probe_verify(a, b, c))
    print(f"{name}: derived={len(atoms):5d}  false-conclusions="
          f"{len(wrong):5d}  pass-legs-exist={le_wrong:5d}  "
          f"pass-probe-verify={pv_wrong}")
    # Stated expectations: the broken dropped-join rule's false
    # conclusions all pass the bare leg-existence check (1800), and
    # NO false conclusion from any broken rule survives the
    # re-derivation join (0).
    if name.startswith("WRONG dropped-join"):
        check("dropped-join-legs-exist-1800", le_wrong == 1800)
    if name.startswith("WRONG"):
        check("broken-rule-probe-verify-0", pv_wrong == 0)
print("\nreading: pass-legs-exist on false conclusions = provenance "
      "stamp fails as soundness; pass-probe-verify=0 means the "
      "equality join (a native RE-DERIVATION) is the load-bearing "
      "check.")

# GATE — the summary line and the exit code agree with the receipts
if FAILS:
    print(f"\nGATE: FAIL ({', '.join(sorted(set(FAILS)))})")
else:
    print("\nGATE: PASS")
sys.exit(1 if FAILS else 0)
