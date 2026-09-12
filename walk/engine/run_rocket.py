#!/usr/bin/env python3
"""run_rocket.py -- the same question, on the custom engine, no Ergo."""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import Item, Store, Cycle

S = Store()
CTX = "nozzle_apcp_5s"

# ---- handbook: derived quantities point at what they depend on
HAND = {
 "thrust": ["chamber_pressure","throat_area","thrust_coefficient"],
 "chamber_pressure": ["gas_generation_rate","throat_area","characteristic_velocity"],
 "characteristic_velocity": ["flame_temperature","mean_molecular_weight"],
 "throat_area": ["throat_diameter"],
 "heat_transfer_coefficient": ["chamber_pressure","throat_diameter"],
 "wall_temperature": ["heat_transfer_coefficient","flame_temperature",
                      "thermal_conductivity","density","specific_heat","burn_duration"],
 "wall_load": ["chamber_pressure","wall_thickness"],
 "wall_capacity": ["yield_strength","wall_temperature","melting_point"],
 "current": ["voltage","resistance"],            # noise
 "orbital_period": ["semi_major_axis"],          # noise
}
for q, deps in HAND.items():
    S.put(Item(q, "derived", content=deps, refs=deps))

# ---- run conditions point at the material table (that is where ceilings live)
for c in ("flame_temperature","wall_temperature","wall_load","wall_capacity"):
    if c not in S.items:
        S.put(Item(c, "condition", refs=["material_table"]))
    else:
        S.items[c].kind = "condition"
        S.items[c].refs = tuple(S.items[c].refs) + ("material_table",)

# ---- the material table is one item: reading it is free
MAT = {
 "lead":(600,700,12,11340,128,35,2.2,5,"pb"),
 "aluminum":(933,400,276,2700,896,167,2.4,107,"al"),
 "steel_1018":(1783,800,370,7870,486,50,0.9,126,"fe"),
 "copper":(1358,500,210,8960,385,400,9.0,50,"cu"),
 "titanium":(1941,600,880,4500,523,22,35.0,349,"ti"),
 "nickel":(1728,900,148,8900,440,91,20.0,140,"ni"),
 "tungsten":(3695,800,550,19300,134,170,35.0,350,"w"),
 "tantalum":(3290,600,200,16690,140,57,300.0,120,"ta"),
 "graphite":(3900,700,70,1800,710,100,15.0,60,"c"),
 "silicon_carbide":(3003,1100,550,3200,690,120,25.0,2800,"si"),
 "zirconia":(2988,2000,200,6000,450,2,60.0,1300,"zr"),
 "alumina_ceramic":(2345,2000,300,3950,880,30,20.0,1800,"al"),
 "ptfe":(600,570,23,2200,1000,0.25,20.0,5,"c"),
 "nylon":(533,520,80,1150,1700,0.25,4.0,10,"c"),
 "ice":(273,9999,5,917,2100,2.2,0.01,1,"h"),
 "concrete":(1500,1200,3,2400,880,1.7,0.1,100,"ca"),
}
COLS=("melting_point","oxidation_onset","yield_strength","density",
      "specific_heat","thermal_conductivity","cost_per_kg","hardness","made_of")
S.put(Item("material_table","table",content=COLS,refs=list(MAT)))
for n, row in MAT.items():
    S.put(Item(n,"material",content=dict(zip(COLS,row)),tag="chart",refs=["reaction_table"]))

# ---- chemistry, one item
PROD={"co":82,"al2o3":3250,"fe2o3":1838,"cuo":2270,"pbo":1750,"wo3":1000,"tio2":3245,
      "nio":2228,"ta2o5":2145,"sio2":3220,"zro2":4573,"cao":3120,"h2o":373,
      "fecl3":588,"alcl3":451,"cucl2":1266}
RX={("c","ox"):"co",("al","ox"):"al2o3",("fe","ox"):"fe2o3",("cu","ox"):"cuo",
    ("pb","ox"):"pbo",("w","ox"):"wo3",("ti","ox"):"tio2",("ni","ox"):"nio",
    ("ta","ox"):"ta2o5",("si","ox"):"sio2",("zr","ox"):"zro2",("ca","ox"):"cao",
    ("h","ox"):"h2o",("fe","cl"):"fecl3",("al","cl"):"alcl3",("cu","cl"):"cucl2"}
S.put(Item("reaction_table","table",content=(RX,PROD)))

# ---- Isaac-only records: true, and never leave
S.put(Item("pass_count","record",content=3,native=True))
S.put(Item("lead_supplier_code","record",content="sc_4417",truth=0,native=True))

# ---- relevance for this context
for n in HAND: S.set_rel(CTX,n,3)
S.set_rel(CTX,"current",0); S.set_rel(CTX,"orbital_period",0)
S.set_rel(CTX,"material_table",4); S.set_rel(CTX,"reaction_table",4)
for n in MAT: S.set_rel(CTX,n,2)
S.set_rel(CTX,"cost_per_kg",1); S.set_rel(CTX,"hardness",1)

# ---- the run being assessed
Tg=2900.; h=4814.; BURN=5.0; T0=293.; rho_g=.8; cp_g=1900.; km=h/(rho_g*cp_g)
SPEC={"ox":0.02,"cl":0.15}; Pc=300*6895.; r_in=0.002; WALL=0.002

def surf(m,t):
    a=m["thermal_conductivity"]/(m["density"]*m["specific_heat"])
    b=h*h*a*t/m["thermal_conductivity"]**2
    return Tg if b>500 else T0+(Tg-T0)*(1-math.exp(b)*math.erfc(math.sqrt(b)))

# ---- ONE gate: load against capacity. mode names fall out.
def load_vs_capacity(cand, desk):
    m=cand.content; wall=WALL; t=0.; dt=0.02
    while t<=BURN:
        T=surf(m,t)
        if T>=m["oxidation_onset"]:
            for sp,Y in SPEC.items():
                pr=RX.get((m["made_of"],sp))
                if pr and PROD.get(pr,9e9)<T:
                    wall-=km*rho_g*Y*0.75/m["density"]*dt
        cap = 0. if T>=m["melting_point"] else m["yield_strength"]*1e6*(
              1. if T<m["melting_point"]*.55 else
              max(0.,1-(T-m["melting_point"]*.55)/(m["melting_point"]*.45)))
        lo = 1e30 if wall<=0 else Pc*r_in/wall
        if lo>=cap:
            why=("capacity gone at %.1fs"%t if cap==0 else
                 "wall eaten to %.2fmm at %.1fs"%(wall*1000,t) if wall<WALL*.95 else
                 "softened at %.1fs"%t)
            return False, why
        t+=dt
    return True, ""

def rank(c):
    m=c.content; NOZ=math.pi*((0.011)**2-(0.002)**2)*0.015
    return (round(m["density"]*NOZ*m["cost_per_kg"],2), round(m["density"]*NOZ*1000,1), m["hardness"])

cyc=Cycle(S, CTX, "thrust", gates=[("load>capacity",load_vs_capacity)], rank_by=rank)
ranked=cyc.run()

print("\n---- rejected, with reason")
for n,(g,why) in cyc.rejected.items(): print("  %-18s %s"%(n,why))
print("\n---- set aside on the desk (pulled, not in play)")
for n,(it,why) in cyc.desk.set_aside.items(): print("  %-22s %s"%(n,why))
print("\n---- trace for graphite")
path,verdict=cyc.why("graphite")
for t in path: print("  reached via", t[0], "->", t[1])
print("  verdict:", verdict)
