"""
CLOTH AUTOPSY — what did he get wrong, and WHY. Re-teaches the same
120-passage course (observation only — W is identical by construction
since compile reads only sequences), re-sits the whole-course exam
with full per-item logging, then splits the misses:

  SHRUG-GUESS: no evidence for ANY option (all confidences ~0) — the
      pick is noise. A coverage problem: he never absorbed a usable
      context. Cure = more/better exposure.
  WRONG BELIEF: he HAD evidence and chose a distractor — an
      interference problem. Cure = discrimination, negatives, syntax.
  NEAR MISS: truth was his #2 or tied — margin analysis.

Plus: accuracy by truth-word frequency (his own course statistics,
no hand lists), and a teacher's sample of actual misses to read.

    python cloth_autopsy.py
"""
import os
import sys
from collections import Counter
from glob import glob

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "..", "code"))
from isaac import Isaac, tokenize  # noqa: E402
from cloth_run import DATA, load, sentences, CTX  # noqa: E402

N_PASSAGES = 120

if __name__ == "__main__":
    import re
    files = sorted(glob(os.path.join(DATA, "*.json")))
    passages = []
    for f in files:
        p = load(f)
        if p and p["items"]:
            passages.append(p)
        if len(passages) >= N_PASSAGES:
            break

    isaac = Isaac()
    isaac.wave_logging = False
    df = Counter()
    for p in passages:
        for s in sentences(p["toks"]):
            isaac.observe(s)
            df.update(s)

    rows = []
    for p in passages:
        for b in p["items"]:
            ctx = [t for t in p["toks"][max(0, b["pos"] - CTX):b["pos"]]
                   if re.match(r"\w", t)]
            if len(ctx) < 2:
                continue
            confs = sorted(((isaac.check(ctx, tokenize(o)[0])[1], o)
                            for o in b["options"]), reverse=True)
            pick = confs[0][1]
            truth_conf = next(c for c, o in confs if o == b["truth"])
            rows.append(dict(
                ctx=" ".join(ctx[-5:]), options=[o for _, o in confs],
                confs=[c for c, _ in confs], pick=pick,
                truth=b["truth"], ok=pick == b["truth"],
                cmax=confs[0][0], truth_conf=truth_conf,
                truth_rank=[o for _, o in confs].index(b["truth"]) + 1,
                truth_df=df.get(b["truth"], 0)))

    n = len(rows)
    right = sum(r["ok"] for r in rows)
    print("=" * 72)
    print(f"  AUTOPSY — {right}/{n} = {100 * right / n:.0f}% "
          f"(replication of the 40% run)")
    print("=" * 72)

    shrug = [r for r in rows if r["cmax"] <= 0.0]
    evid = [r for r in rows if r["cmax"] > 0.0]
    for name, grp in (("SHRUG-GUESS (no evidence at all)", shrug),
                      ("EVIDENCED (he believed something)", evid)):
        if grp:
            acc = 100 * sum(r["ok"] for r in grp) / len(grp)
            print(f"\n  {name}: {len(grp)} items "
                  f"({100 * len(grp) / n:.0f}% of exam) — "
                  f"accuracy {acc:.0f}%")

    strong = [r for r in evid if r["cmax"] >= 1.0]
    if strong:
        acc = 100 * sum(r["ok"] for r in strong) / len(strong)
        print(f"  above his belief threshold (conf >= 1.0): "
              f"{len(strong)} items — accuracy {acc:.0f}%")

    near = [r for r in evid if not r["ok"] and r["truth_rank"] == 2]
    wrongbelief = [r for r in evid if not r["ok"]]
    print(f"\n  of the evidenced misses ({len(wrongbelief)}): "
          f"{len(near)} had the truth at rank 2 (near miss)")

    qs = sorted(set(np.percentile([r["truth_df"] for r in rows],
                                  [25, 50, 75]).astype(int)))
    print("\n  accuracy by truth-word course frequency:")
    lo = 0
    for q in qs + [10 ** 9]:
        grp = [r for r in rows if lo <= r["truth_df"] < q]
        if grp:
            acc = 100 * sum(r["ok"] for r in grp) / len(grp)
            print(f"    df {lo:>4}-{q if q < 10**9 else 'max'}: "
                  f"{len(grp):>4} items — {acc:.0f}%")
        lo = q

    print("\n  a teacher's sample of the misses:")
    rng = np.random.default_rng(3)
    for kind, pool in (("shrug", [r for r in shrug if not r["ok"]]),
                       ("wrong-belief", wrongbelief)):
        take = list(rng.choice(len(pool), min(5, len(pool)),
                               replace=False)) if pool else []
        for i in take:
            r = pool[int(i)]
            print(f"    [{kind}] …{r['ctx']} ___  he: {r['pick']!r} "
                  f"({r['confs'][0]:.1f})  truth: {r['truth']!r} "
                  f"(conf {r['truth_conf']:.1f}, rank "
                  f"{r['truth_rank']})")
