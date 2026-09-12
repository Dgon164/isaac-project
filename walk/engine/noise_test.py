import sys, io, os, contextlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
buf=io.StringIO()
with contextlib.redirect_stdout(buf):
    exec(open(os.path.join(HERE, "run_rocket.py")).read())
before=S_pulls=cyc.step_no; n_before=len(S.items)
from core import Item
noise=[("cat","animal",["fur","whiskers","tuna"]),("bread","food",["flour","yeast","oven"]),
       ("sourdough","food",["bread","starter"]),("tuna","food",["cat","ocean"]),
       ("guitar","instrument",["strings","fret"]),("estes_c6","product",["black_powder"]),
       ("phoenix","city",["arizona","heat"]),("arizona","state",["phoenix"]),
       ("heat","concept",["fire","summer"]),("fire","concept",["heat","oxygen"])]
for i in range(40): noise.append(("junk_%d"%i,"misc",["junk_%d"%((i+1)%40)]))
for n,k,r in noise: S.put(Item(n,k,refs=r))
S.set_rel(CTX,"heat",3)   # even relevance can't make it get pulled if nothing points at it
from core import Cycle
c2=Cycle(S,CTX,"thrust",gates=[("load>capacity",load_vs_capacity)],rank_by=rank,verbose=False)
c2.run()
print("store size: %d -> %d items"%(n_before,len(S.items)))
print("pulls:      %d -> %d"%(before,c2.step_no))
print("persist:    %s"%", ".join(c2.candidates))
print("noise items reached:", [n for n,_,_ in noise if n in c2.resolved] or "none")
