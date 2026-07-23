"""
CLOTH — the first REAL exam corpus through the class-then-quiz loop.
Real English-exam cloze passages (CMU CLOTH, modern English, human
answer keys). The loop per batch: BASELINE exam (before any class —
should sit at chance, the control) -> THE CLASS (the completed
passage, taught) -> THE EXAM (same blanks, his check() over the four
real options) -> retention retest of earlier batches. Substrate
guard: stop honestly when the dense-W wall approaches.

    python cloth_run.py [n_passages]
"""
import json
import os
import re
import sys
import time
from glob import glob

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "..", "code"))
from isaac import Isaac, tokenize  # noqa: E402

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "..", "data", "cloth", "CLOTH", "train", "middle")
N_PASSAGES = int(sys.argv[1]) if len(sys.argv) > 1 else 120
BATCH = 20
CTX = 8                       # left-context tokens per blank
CELL_CAP = 250_000_000        # dense-W guard (~1GB float32)
LETTERS = "ABCD"


def load(path):
    j = json.load(open(path, encoding="utf-8"))
    art, opts, ans = j["article"], j["options"], j["answers"]
    toks, blanks = [], []
    for piece in re.split(r"(_)", art):
        if piece == "_":
            k = len(blanks)
            if k >= len(ans):
                return None
            truth = opts[k][LETTERS.index(ans[k])].strip().lower()
            blanks.append(dict(pos=len(toks),
                               options=[o.strip().lower()
                                        for o in opts[k]],
                               truth=truth))
            toks.extend(tokenize(truth))
        else:
            toks.extend(tokenize(piece))
    # single-token options only (his check() judges one door)
    items = [b for b in blanks
             if all(len(tokenize(o)) == 1 for o in b["options"])
             and len(tokenize(b["truth"])) == 1]
    return dict(toks=toks, items=items)


def sentences(toks):
    out, cur = [], []
    for t in toks:
        cur.append(t)
        if t in ".?!" and len(cur) > 1:
            out.append([x for x in cur if re.match(r"\w", x)])
            cur = []
    if len(cur) > 1:
        out.append([x for x in cur if re.match(r"\w", x)])
    return [s for s in out if len(s) >= 2]


def exam(isaac, passages):
    right = total = 0
    for p in passages:
        for b in p["items"]:
            ctx = [t for t in p["toks"][max(0, b["pos"] - CTX):b["pos"]]
                   if re.match(r"\w", t)]
            if len(ctx) < 2:
                continue
            confs = [(isaac.check(ctx, tokenize(o)[0])[1], o)
                     for o in b["options"]]
            pick = max(confs)[1]
            right += pick == b["truth"]
            total += 1
    return right, total


if __name__ == "__main__":
    files = sorted(glob(os.path.join(DATA, "*.json")))
    passages = []
    for f in files:
        p = load(f)
        if p and p["items"]:
            passages.append(p)
        if len(passages) >= N_PASSAGES:
            break
    n_items = sum(len(p["items"]) for p in passages)
    print("=" * 72)
    print("  CLOTH — real exams, class-then-quiz")
    print("=" * 72)
    print(f"  {len(passages)} passages, {n_items} single-token cloze "
          f"items (4 options each, chance = 25%)")

    isaac = Isaac()
    isaac.wave_logging = False
    taught = []
    t0 = time.time()
    for i in range(0, len(passages), BATCH):
        batch = passages[i:i + BATCH]
        pre_r, pre_t = exam(isaac, batch)          # the control
        for p in batch:                            # THE CLASS
            for s in sentences(p["toks"]):
                isaac.observe(s)
        isaac.consolidate()
        post_r, post_t = exam(isaac, batch)        # THE EXAM
        taught.extend(batch)
        ret_r, ret_t = exam(isaac, taught[:BATCH])  # retention of batch 1
        st = isaac.status()
        shape = st["matrix_shape"]
        cells = (shape[0] * shape[1]) if shape else 0
        print(f"  batch {i // BATCH + 1:2d}: baseline "
              f"{pre_r}/{pre_t} ({100 * pre_r / max(pre_t, 1):.0f}%)  "
              f"after class {post_r}/{post_t} "
              f"({100 * post_r / max(post_t, 1):.0f}%)  "
              f"retention(b1) {100 * ret_r / max(ret_t, 1):.0f}%  "
              f"| {st['nodes']} nodes, W {shape} "
              f"[{time.time() - t0:.0f}s]", flush=True)
        if cells > CELL_CAP:
            print(f"  STOPPED: dense-W wall ({cells / 1e6:.0f}M cells) "
                  f"— the honest frontier; sparse substrate is the gate")
            break

    fr, ft = exam(isaac, taught)
    print(f"\n  final: whole-course exam {fr}/{ft} "
          f"({100 * fr / max(ft, 1):.0f}%) vs 25% chance · "
          f"{isaac.status()['nodes']} nodes · "
          f"{len(isaac.types)} types · {time.time() - t0:.0f}s")
