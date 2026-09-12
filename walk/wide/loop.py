import subprocess, re
ERGO="/home/claude/ergoai/ERGOAI_3.0/ErgoAI/runergo"
LOAD="['materials.ergo', +'handbook_wide.ergo']."
def q(query, var):
    p=subprocess.run([ERGO],input=LOAD+"\n"+query+"\n\\end\n",
                     capture_output=True,text=True,timeout=400)
    return [m.group(1).strip() for m in
            re.finditer(r"^\?%s\s*=\s*(.+)$"%var,p.stdout,re.M)]
QUESTION={
 "derived_quantity": lambda t:("what does %s depend on?"%t,"relates(%s,?L)."%t,"L"),
 "run_condition":    lambda t:("what material property caps %s?"%t,
                               "candidate_failure(%s,?P,?_)."%t,"P"),
 "material_property":lambda t:("which materials list a %s?"%t,"?M[%s -> ?V]."%t,"M"),
 "material":         lambda t:("what is %s made of?"%t,"%s[made_of -> ?E]."%t,"E"),
}
GOAL="thrust"; resolved=set(); openq=[GOAL]; asked=0
while openq and asked<12:
    t=openq.pop(0)
    if t in resolved: continue
    resolved.add(t)
    kinds=q("term_kind(%s,?K)."%t,"K")
    k=next((x for x in ["derived_quantity","run_condition","material_property","material"]
            if x in kinds),None)
    if not k:
        continue
    text,query,var=QUESTION[k](t)
    ans=q(query,var); asked+=1
    new=[]
    for a in ans:
        for tok in re.findall(r"[a-z_][a-z0-9_]+",a):
            if tok not in resolved and tok not in openq:
                openq.append(tok); new.append(tok)
    print("ASK %d [%s] %s"%(asked,k,text))
    print("RET %s"%(", ".join(ans[:7])+(" ..." if len(ans)>7 else "") if ans else "(nothing)"))
    if new: print("    opens: %s"%", ".join(new[:9]))
    print()
print("="*58)
print("asked %d questions, resolved %d terms, %d still open"%(asked,len(resolved),len(openq)))
print("open:", ", ".join(openq[:12]))
