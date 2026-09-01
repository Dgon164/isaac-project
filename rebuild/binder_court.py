"""BINDER court — output-input pairs bind by correlation, never by
raw time adjacency (owner ruling 2026-08-30).

Plants: (a) switch->light recurring with noise between = must BIND,
fused episode in the log + a binds-fact; (b) one-off pairings = must
NOT bind; (c) an input that appears constantly WITHOUT the act (the
background null) = must NOT bind despite co-occurrences; (d) binder
state survives save/load."""
import os
import sys
import tempfile

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
if not hasattr(m, "act_log"):
    print("SKIP: binder not built yet")
    sys.exit(77)

noise = [tokenize(f"filler sentence number {i} drifts by .")
         for i in range(30)]

# (a) the plant: press switch ... light on, four recurrences
for i in range(4):
    m.act_log(tokenize("press the switch"))
    m.observe(noise[i])                      # jitter inside the window
    m.observe(tokenize("the light is on"))
    m.observe(noise[10 + i])                 # spacing between episodes
    m.observe(noise[20 + i])

bound = [(a, b) for a, b in m.bound_episodes
         if "switch" in a and "light" in b]
check("switch->light BOUND after recurrence", bool(bound))
fused_in_log = any("then" in s and "switch" in s and "light" in s
                   for s in m.observed_sequences)
check("fused episode entered the log as ONE sequence", fused_in_log)
check("binds-fact minted with origin=bound",
      bool(m.facts_query(pred="binds", origin="bound")))

# (b) one-off pairing: never recurs -> never binds
m.act_log(tokenize("kick the stone"))
m.observe(tokenize("a bird flies past"))
check("one-off pairing did NOT bind",
      not any("stone" in a for a, b in m.bound_episodes))

# (c) the background null: hum happens all the time on its own;
# co-occurring with an act a few times must not bind it
m2 = Isaac()
m2.wave_logging = False
hum = tokenize("the fan hums")
for i in range(20):                          # hum is just background
    m2.observe(hum)
    m2.observe(noise[i % 30])
for i in range(4):
    m2.act_log(tokenize("wave the hand"))
    m2.observe(hum)
    m2.observe(noise[i])
check("everywhere-input rejected by the background null",
      not any("hand" in a for a, b in m2.bound_episodes))

# (d) persistence
p = os.path.join(tempfile.mkdtemp(prefix="binder_"), "b.isaac")
m.save(p)
m3 = Isaac.load(p)
check("bound episodes survive save/load",
      any("switch" in a for a, b in m3.bound_episodes))

print(f"\nGATE: {'PASS' if not FAILS else 'FAIL (' + ','.join(FAILS) + ')'}")
sys.exit(1 if FAILS else 0)
