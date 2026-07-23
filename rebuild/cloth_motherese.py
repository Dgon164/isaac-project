"""
THE DECISIVE EXPERIMENT — same real exams, two deliveries.
Autopsy said: 83% of items = zero evidence (the mid-seam wall), 94%
accuracy where evidence existed. Prediction, filed: motherese
delivery (fragments that grow — interior seams registered) explodes
coverage and lifts the total toward the 94% ceiling. Dense-W cost of
the extra frames is the measured price that gates sparse W.

    python cloth_motherese.py [n_passages]
"""
import os
import re
import sys
import time
from glob import glob

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "..", "code"))
from isaac import Isaac, tokenize  # noqa: E402
from cloth_run import DATA, load, sentences, CTX  # noqa: E402

N = int(sys.argv[1]) if len(sys.argv) > 1 else 80


def exam(isaac, passages):
    right = total = evid = evid_right = 0
    for p in passages:
        for b in p["items"]:
            ctx = [t for t in p["toks"][max(0, b["pos"] - CTX):b["pos"]]
                   if re.match(r"\w", t)]
            if len(ctx) < 2:
                continue
            confs = [(isaac.check(ctx, tokenize(o)[0])[1], o)
                     for o in b["options"]]
            cmax, pick = max(confs)
            ok = pick == b["truth"]
            right += ok
            total += 1
            if cmax > 0:
                evid += 1
                evid_right += ok
    return right, total, evid, evid_right


if __name__ == "__main__":
    files = sorted(glob(os.path.join(DATA, "*.json")))
    passages = []
    for f in files:
        p = load(f)
        if p and p["items"]:
            passages.append(p)
        if len(passages) >= N:
            break
    print("=" * 72)
    print(f"  SAME EXAM, TWO DELIVERIES — {N} passages")
    print("=" * 72)

    for name, motherese in (("plain (sentence-final seams only)",
                             False),
                            ("motherese (fragments that grow)", True)):
        isaac = Isaac()
        isaac.wave_logging = False
        t0 = time.time()
        for p in passages:
            for s in sentences(p["toks"]):
                if motherese:
                    for k in range(2, len(s) + 1):
                        isaac.observe(s[:k])
                else:
                    isaac.observe(s)
        r, t, e, er = exam(isaac, passages)
        st = isaac.status()
        print(f"\n  {name}:")
        print(f"    score {r}/{t} = {100 * r / t:.0f}%  ·  coverage "
              f"{e}/{t} = {100 * e / t:.0f}%  ·  accuracy-when-seen "
              f"{100 * er / max(e, 1):.0f}%")
        print(f"    W {st['matrix_shape']} · {st['nodes']} nodes · "
              f"{time.time() - t0:.0f}s")
