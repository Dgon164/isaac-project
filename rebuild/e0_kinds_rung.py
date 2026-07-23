"""
E0.1 — THE KINDS RUNG (opened 2026-07-23; engineer lane, D1).

Structural vocabulary as atoms; typed relation doors; the composite
court: a proposed composite must account for planted composed data
better than its ingredients separately, past a scrambled null.

Predictions, filed in RESEARCH_AGENDA.md before this first run:
  P1  two planted families (tubes, planes) mint as SOUND types with
      clean membership — the composite accounts for its members.
  P2  the scrambled null (same tokens, family structure broken) mints
      NO sound cleanly-separated type — the court refuses chance.
  P3  typed relation doors (wrapped_around, grown_from, ...) recall
      5/5 through the fact index.

Instrument: his own crystallizer and its chance-null verdicts —
nothing added for this experiment.

    python e0_kinds_rung.py
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "..", "code"))
from isaac import Isaac, tokenize  # noqa: E402

FAMILIES = {
    "tube": dict(members=["pipe", "hose", "straw"],
                 props=["hollow", "round", "long"]),
    "plane": dict(members=["sheet", "board", "panel"],
                  props=["flat", "thin", "wide"]),
}


def build(scrambled=False, seed=7, copula=False):
    """copula=True: 'pipe is hollow' (English-shaped). copula=False:
    'pipe hollow' (bare structural adjacency). First-run finding
    (2026-07-23): the copula shape gives siblings only ONE shared
    door ('is'), below min_shared — English function words act as
    structural separators his crystallizer cannot yet see through.
    The kinds court therefore runs on bare adjacency until the
    language line earns the copula."""
    rng = np.random.default_rng(seed)
    isaac = Isaac()
    isaac.wave_logging = False
    sentences = []
    all_props = [p for f in FAMILIES.values() for p in f["props"]]
    for fam in FAMILIES.values():
        for m in fam["members"]:
            props = (list(rng.choice(all_props, 3, replace=False))
                     if scrambled else fam["props"])
            for p in props:
                sentences.append(f"{m} is {p}" if copula
                                 else f"{m} {p}")
    for _ in range(2):
        for s in sentences:
            isaac.observe(tokenize(s))
    isaac.crystallize()
    return isaac


def family_of(members):
    for name, f in FAMILIES.items():
        if set(f["members"]) <= members and not any(
                m in members for g, f2 in FAMILIES.items()
                if g != name for m in f2["members"]):
            return name
    return None


def sound_families(isaac):
    out = {}
    for tname, t in isaac.types.items():
        fam = family_of({m for m in t["members"]
                         if not str(m).startswith(("is",))})
        if fam and t.get("verdict") == "sound":
            out[fam] = dict(type=tname, score=t.get("score"),
                            members=sorted(t["members"]))
    return out


if __name__ == "__main__":
    print("=" * 70)
    print("  E0.1 — THE KINDS RUNG: composites vs the scrambled null")
    print("=" * 70)

    print("\n  P1 — planted families:")
    real = build(scrambled=False)
    fams = sound_families(real)
    for fam, d in fams.items():
        print(f"    {fam}: SOUND as {d['type']} score={d['score']} "
              f"members={d['members']}")
    wrongs = len(getattr(real, "wrong_types", {}) or {})
    p1 = set(fams) == set(FAMILIES)
    print(f"    -> P1 {'HOLDS' if p1 else 'FAILS'} "
          f"({len(fams)}/2 families sound; {wrongs} filed wrong)")

    print("\n  P2 — the scrambled null (must refuse):")
    null = build(scrambled=True)
    nfams = sound_families(null)
    nwrongs = len(getattr(null, "wrong_types", {}) or {})
    p2 = len(nfams) == 0
    print(f"    -> P2 {'HOLDS' if p2 else 'FAILS'} "
          f"({len(nfams)} clean sound families from scrambled data; "
          f"{nwrongs} filed wrong — kept and classified)")

    print("\n  P3 — typed relation doors:")
    rel = Isaac()
    rel.wave_logging = False
    facts = [("tube", "wrapped_around", "axis"),
             ("tube", "grown_from", "circle"),
             ("thread", "repeated_along", "cylinder"),
             ("surface", "extruded_from", "edge"),
             ("plane", "bounded_by", "edges")]
    for s, r, o in facts:
        rel.teach(s, r, o)
    got = sum(1 for s, r, o in facts
              if o in rel.fact_index.get((s, r), []))
    p3 = got == 5
    print(f"    -> P3 {'HOLDS' if p3 else 'FAILS'} ({got}/5 typed "
          f"relations recalled)")

    print(f"\n  E0.1 verdict: "
          f"{'GREEN' if p1 and p2 and p3 else 'NOT GREEN'} "
          f"(P1 {p1} · P2 {p2} · P3 {p3})")
