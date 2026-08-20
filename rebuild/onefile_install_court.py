# INSTALL COURT for the one-file body v2 — same equivalence court as
# the probe, but through the INSTALLED engine API (Isaac.save/load),
# on the scratchpad copy of the real 07-24 him. Never touches
# isaac-life.
import os
import sys
import time

SCRATCH = (r"C:\Users\jtwee\AppData\Local\Temp\claude"
           r"\c--Users-jtwee-Downloads-New-folder--3-"
           r"\d93c0d2c-8d04-45aa-9f80-804c774fbc7e\scratchpad")
sys.path.insert(0, r"C:\Users\jtwee\Documents\isaac-project\code")
sys.path.insert(0, r"C:\Users\jtwee\Documents\isaac-project\rebuild")
from isaac import Isaac                                    # noqa: E402
from onefile_probe import deep_eq                          # noqa: E402

V1 = os.path.join(SCRATCH, "audit_copy.isaac")
V2 = os.path.join(SCRATCH, "install_court.isaac2")

orig = Isaac.load(V1)                       # v1 pickle road (forever)
t0 = time.perf_counter()
orig.save(V2)                               # the INSTALLED v2 save
t_save = time.perf_counter() - t0
t0 = time.perf_counter()
twin = Isaac.load(V2)                       # magic-sniffed v2 load
t_load = time.perf_counter() - t0
print(f"API save {t_save:.1f}s  load {t_load:.1f}s  "
      f"{os.path.getsize(V1)/1048576:.1f}MB -> "
      f"{os.path.getsize(V2)/1048576:.1f}MB")

fails = []
for name, a, b in [
        ("doors", dict(orig.net.doors), dict(twin.net.doors)),
        ("door_tags", dict(orig.net.door_tags), dict(twin.net.door_tags)),
        ("door_counts", dict(orig.net.door_counts),
         dict(twin.net.door_counts)),
        ("meta", dict(orig.net.meta), dict(twin.net.meta)),
        ("preds", dict(orig.net.preds), dict(twin.net.preds)),
        ("activation_log", orig.activation_log, twin.activation_log)]:
    ok, why = deep_eq(a, b)
    if not ok:
        fails.append(f"{name}: {why}")
for name in sorted(vars(orig)):
    if name in ("net", "activation_log"):
        continue
    ok, why = deep_eq(getattr(orig, name), getattr(twin, name, None))
    if not ok:
        fails.append(f"attr {name}: {why}")

# journal through the API + resave compacts the tail
Isaac.journal_append(V2, [("add_door", "court:x", "court:y", "seq")])
j = Isaac.load(V2)
jr = j.net.has_door("court:x", "court:y")
j.save(V2)                                  # compaction: full save
j2 = Isaac.load(V2)
jc = j2.net.has_door("court:x", "court:y")

print("equivalence:", "EXACT (all stores + all attributes)"
      if not fails else "FAIL " + "; ".join(fails[:5]))
print("journal via API:", "GREEN" if jr else "FAIL",
      "  compacted-and-kept:", "GREEN" if jc else "FAIL")
print("VERDICT:", "ALL GREEN" if not fails and jr and jc else "FAILS")
