import subprocess, re, math
ERGO="/home/claude/ergoai/ERGOAI_3.0/ErgoAI/runergo"
LOAD="['materials.ergo', +'handbook_wide.ergo']."
def q(query,var):
    p=subprocess.run([ERGO],input=LOAD+"\n"+query+"\n\\end\n",
                     capture_output=True,text=True,timeout=400)
    return [m.group(1).strip() for m in re.finditer(r"^\?%s\s*=\s*(.+)$"%var,p.stdout,re.M)]

# ---- the run being assessed
Tg=2900.; h=4814.; BURN=5.0; T0=293.; rho_g=.8; cp_g=1900.; km=h/(rho_g*cp_g)
SPECIES={"oxidiser":0.02,"chloride":0.15}; ALLOW=0.2

MAT={}
for line in open('materials.ergo'):
    line=line.strip().rstrip('.')
    if not line: continue
    n,rest=line.split('[',1); p,v=rest.rstrip(']').split(' -> ')
    MAT.setdefault(n,{})[p]= v if p=='made_of' else float(v)
PROD={"co":82,"al2o3":3250,"fe2o3":1838,"cuo":2270,"pbo":1750,"wo3":1000,"tio2":3245,
"mgo":3873,"nio":2228,"moo3":1428,"nb2o5":1785,"ta2o5":2145,"sio2":3220,"zro2":4573,
"beo":4123,"zno":2633,"cao":3120,"h2o":373,"fecl3":588,"alcl3":451,"cucl2":1266}
RX={("c","oxidiser"):"co",("al","oxidiser"):"al2o3",("fe","oxidiser"):"fe2o3",
("cu","oxidiser"):"cuo",("pb","oxidiser"):"pbo",("w","oxidiser"):"wo3",
("ti","oxidiser"):"tio2",("mg","oxidiser"):"mgo",("ni","oxidiser"):"nio",
("mo","oxidiser"):"moo3",("nb","oxidiser"):"nb2o5",("ta","oxidiser"):"ta2o5",
("si","oxidiser"):"sio2",("zr","oxidiser"):"zro2",("be","oxidiser"):"beo",
("zn","oxidiser"):"zno",("ca","oxidiser"):"cao",
("fe","chloride"):"fecl3",("al","chloride"):"alcl3",("cu","chloride"):"cucl2"}
def Ts(m):
    a=m['thermal_conductivity']/(m['density']*m['specific_heat'])
    b=h*h*a*BURN/m['thermal_conductivity']**2
    return Tg if b>500 else T0+(Tg-T0)*(1-math.exp(b)*math.erfc(math.sqrt(b)))

# the gates the loop DISCOVERED earlier, in the order it found them
GATES=[("melting_point","surface reaches melting point"),
       ("boiling_point","surface reaches boiling point"),
       ("oxidation_onset","reacts and the product leaves")]

alive=set(MAT); print("starting candidates: %d\n"%len(alive))
for prop,desc in GATES:
    holders=set(q("?M[%s -> ?V]."%prop,"M"))
    rejected=[]
    for name in sorted(alive):
        m=MAT[name]; T=Ts(m)
        if prop=="melting_point" and T>=m['melting_point']: rejected.append((name,"Ts %.0f >= melt %.0f"%(T,m['melting_point'])))
        elif prop=="boiling_point" and T>=m['boiling_point']: rejected.append((name,"boils"))
        elif prop=="oxidation_onset" and T>=m['oxidation_onset']:
            rec=0
            for sp,Y in SPECIES.items():
                pr=RX.get((m['made_of'],sp))
                if pr and PROD.get(pr,9e9)<T: rec+=km*rho_g*Y*.75/m['density']*BURN*1000
            if rec>ALLOW: rejected.append((name,"loses %.2f mm as %s"%(rec,RX.get((m['made_of'],'chloride')) or RX.get((m['made_of'],'oxidiser')))))
    print("GATE: %s  (%s)"%(prop,desc))
    print("  rejected %d:"%len(rejected))
    for n,why in rejected: print("     %-18s %s"%(n,why))
    alive-={n for n,_ in rejected}
    print("  %d persist\n"%len(alive))

print("="*58)
print("PERSIST (all are valid solutions): %s\n"%", ".join(sorted(alive)))
NOZ=math.pi*((0.011)**2-(0.002)**2)*0.015
print("secondary ranking -- choose by what you care about")
print("%-18s %8s %8s %7s %s"%("material","mass g","cost $","HV","best when you want"))
for n in sorted(alive,key=lambda x:MAT[x]['cost_per_kg']*MAT[x]['density']):
    m=MAT[n]; mass=m['density']*NOZ
    want=[]
    if m['hardness']<150: want.append("easy to machine")
    if mass*1000<25: want.append("light")
    if m['cost_per_kg']*mass<0.5: want.append("cheap")
    if m['hardness']>1000: want.append("grind only")
    print("%-18s %8.1f %8.2f %7.0f %s"%(n,mass*1000,mass*m['cost_per_kg'],m['hardness'],", ".join(want) or "-"))
