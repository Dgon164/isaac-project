"""linker.py -- prose in, items with references out. no parser, no model.
a sentence is an item. every term it names is a reference. done."""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import Item, Store

STOP=set("the a an of to in and or is are was were be been it its this that these those for with as at by on from but if so than then too very can will would should could may might not no yes you i we they he she them their our your my me us him her do does did have has had which who what when where why how about into over under out up down off just also only more most some any all each every both either neither such same other another much many few less least".split())

def terms(sentence):
    toks=re.findall(r"[a-z][a-z0-9_\-]*",sentence.lower())
    out=[]
    for t in toks:
        t=t.replace("-","_")
        if t in STOP or len(t)<3: continue
        out.append(t)
    return out

def link(text, store, tag="prose"):
    sents=[s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+",text) if s.strip()]
    made=0
    for i,s in enumerate(sents):
        ts=terms(s)
        if not ts: continue
        name="s%03d_%s"%(i,"_".join(ts[:3]))
        store.put(Item(name,"sentence",content=s,tag=tag,refs=ts))
        for t in ts:
            if store.get(t) is None:
                store.put(Item(t,"term",tag=tag,refs=[name]))
            else:
                it=store.get(t)
                if name not in it.refs: it.refs=tuple(it.refs)+(name,)
        made+=1
    return made
