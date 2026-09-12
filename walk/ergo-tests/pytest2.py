import sys
ERGOROOT = "/home/claude/ergoai/ERGOAI_3.0/ErgoAI"
XSBARCHDIR = "/home/claude/ergoai/ERGOAI_3.0/XSB/config/x86_64-pc-linux-gnu"
sys.path.append(ERGOROOT + "/python")
from pyergo import pyergo_start_session, pyergo_end_session, pyergo_command, pyergo_query

def show(label, rows):
    out = []
    for r in rows:
        out.append({k: getattr(v,'value',v) for k,v in r[0]})
    print(label, out if out else "(no answers)")

pyergo_start_session(XSBARCHDIR, ERGOROOT)
pyergo_command("['/home/claude/map.ergo'].")

print("=== state persists across separate calls?")
show("query 1:", pyergo_query("open_axis(?N,?S)."))
pyergo_command("insert{steel[yield_class -> high]}.")
show("after insert:", pyergo_query("steel[yield_class -> ?V]."))

print("=== can Isaac close an open axis mid-session?")
pyergo_command("delete{open_axis(steel,catlike)}.")
pyergo_command("insert{steel[catlike -> no]}.")
show("catlike now:", pyergo_query("steel[catlike -> ?V]."))
show("open axes now:", pyergo_query("open_axis(?N,?S)."))

print("=== second session in same process?")
try:
    pyergo_start_session(XSBARCHDIR, ERGOROOT)
    print("second start_session: OK")
except Exception as e:
    print("second start_session failed:", repr(e)[:200])
pyergo_end_session()
