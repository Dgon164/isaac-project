# INSTALL COURT for the one-file body v2 — same equivalence court as
# the probe, but through the INSTALLED engine API (Isaac.save/load),
# on the scratchpad copy of the real 07-24 him. Never touches
# isaac-life.
import os
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "code"))
sys.path.insert(0, HERE)
from isaac import Isaac                                    # noqa: E402
from onefile_probe import SCRATCH, deep_eq                 # noqa: E402

# Input: a real v1 saved mind — CLI argument or the staged scratch
# copy. No synthetic fixture here: the install court certifies the
# installed engine against a real saved state, or reports a skip.
if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
    V1 = sys.argv[1]
else:
    V1 = os.path.join(SCRATCH, "audit_copy.isaac")
if not os.path.exists(V1):
    print("SKIP: no v1 mind specimen (pass a path as argv[1] or stage "
          "audit_copy.isaac in the scratch dir)")
    sys.exit(77)

# Output file goes to a per-run temp dir with a unique name — other
# test harnesses run at the same time and must not collide.
V2 = os.path.join(tempfile.mkdtemp(prefix="install_court_"),
                  "install_court.isaac2")

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

# Exit-code gate: each printed pass/fail check above feeds the gate;
# a nonzero exit means at least one check went red.
FAILS = []
if fails:
    FAILS.append("equivalence")
if not jr:
    FAILS.append("journal_api")
if not jc:
    FAILS.append("compacted_kept")
print("GATE:", "PASS" if not FAILS else "FAIL (" + ", ".join(FAILS) + ")")
sys.exit(1 if FAILS else 0)
