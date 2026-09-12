import sys
ERGOROOT = "/home/claude/ergoai/ERGOAI_3.0/ErgoAI"
XSBARCHDIR = "/home/claude/ergoai/ERGOAI_3.0/XSB/config/x86_64-pc-linux-gnu"
sys.path.append(ERGOROOT + "/python")
from pyergo import pyergo_start_session, pyergo_end_session, pyergo_command, pyergo_query

pyergo_start_session(XSBARCHDIR, ERGOROOT)
pyergo_command("['/home/claude/map.ergo'].")

print("neg suitable_for:", pyergo_query("\\neg nylon[suitable_for -> hot_section]."))
print("pos suitable_for:", pyergo_query("nylon[suitable_for -> hot_section]."))
print("open axes:", pyergo_query("open_axis(?N,?S)."))
print("differ:", pyergo_query("differ(bolted_joint,bonded_joint,?S)."))
pyergo_end_session()
