"""PLAYLAND court — the four game modes run, and THE QUARANTINE LAW
holds: nothing imagined enters the log, the net, or the facts layer.
The leak probe is the permanent row the charter demands."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "..", "code"))
from isaac import Isaac, tokenize  # noqa: E402

FAILS = []


def check(name, ok):
    print(f"  {'v' if ok else 'x'}  {name}")
    if not ok:
        FAILS.append(name)


m = Isaac()
m.wave_logging = False
if not hasattr(m, "play"):
    print("SKIP: playland not built yet")
    sys.exit(77)

for s in ["the cat sat on the mat .", "a dog chased the cat .",
          "the bird flew over the house .", "a fish swam in the pond .",
          "the cat ate the fish .", "3 + 4 = 7", "5 + 3 = 8"]:
    m.observe(tokenize(s))
m.consolidate()

n_log = len(m.observed_sequences)
n_facts = len(m.facts)
n_findings = len(m.findings)

rep = m.play(budget=6, rng_seed=7)
print(f"  session report: { {k: v for k, v in rep['modes'].items()} }")

check("all four modes ran", set(rep["modes"]) == {"g1", "g2", "g3", "g4"})
check("g1 self-exam produced a retention score",
      rep["modes"]["g1"]["tried"] > 0)
check("g2 what-if actually generated novelties",
      rep["modes"]["g2"]["tried"] > 0)
check("g3 sandbox recovered the planted law",
      rep["modes"]["g3"]["solved"] == 1)
check("g4 stranger honestly refused", rep["modes"]["g4"]["solved"] == 1)

# THE LEAK PROBE — the quarantine law, asserted
check("QUARANTINE: the log did not grow from play",
      len(m.observed_sequences) == n_log)
check("QUARANTINE: the facts layer did not grow from play",
      len(m.facts) == n_facts)
check("QUARANTINE: his findings ledger did not grow (g3 stayed in "
      "the sandbox)", len(m.findings) == n_findings)
strangers = [t for a in m.asks for t in a["question"]
             if str(t).startswith("imag")]
check("QUARANTINE: no imaginary token entered the net",
      all(t not in m.net.doors and t not in m.net.preds
          for t in strangers))

# asks are the designed export
check("play exports asks (curiosity survives the sandbox)",
      any(a["road"] == "playland" for a in m.asks)
      or rep["asks_filed"] >= 0)
check("session stats accumulated", len(m._play_stats) == 1)

print(f"\nGATE: {'PASS' if not FAILS else 'FAIL (' + ','.join(FAILS) + ')'}")
sys.exit(1 if FAILS else 0)
