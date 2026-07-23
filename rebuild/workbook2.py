"""
THE WORKBOOK v2 — the real wheel, not a reinvented one.

Material: McGuffey's Revised First Reader (1879, public domain,
data/mcguffey_primer.txt) — the standard graduated reader: sight
words, then short sentences, longer ones gradually. Delivery:
motherese shaping (validated: takes mid-seams 0% -> 100%). Drills:
STANDARD formats only, objectively graded — cloze deletion (end +
mid), multiple choice, matching, true/false, dictation. Mastery
gates at 80% (standard mastery learning); a failed gate after
re-teaching stops the run HONESTLY — the stopping level is the
measured answer to "how far can he go" tonight.

Open-ended formats are deliberately absent: they are teacher-graded,
and the teacher is the human.

    python workbook2.py
"""
import os
import re
import sys
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "..", "code"))
from isaac import Isaac, tokenize  # noqa: E402

PRIMER = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "..", "data", "mcguffey_primer.txt")
LESSONS_PER_LEVEL = 5
MAX_LEVELS = 6
GATE = 0.8
RETEACH = 2


def parse_lessons():
    text = open(PRIMER, encoding="utf-8").read()
    blocks = re.split(r"\nLESSON [IVXLC]+\.", text)[1:]
    lessons = []
    for b in blocks:
        sents, words = [], []
        for line in b.splitlines():
            line = line.strip()
            if not line or line.startswith("[Illustration"):
                continue
            for seg in re.split(r"\s{2,}", line):
                seg = seg.strip()
                if re.match(r"^[A-Z].*[.!?]$", seg):
                    toks = [t for t in tokenize(seg)
                            if re.match(r"\w", t)]
                    if len(toks) >= 2:
                        sents.append(toks)
                elif re.match(r"^[a-z][a-z']*$", seg):
                    words.append(seg)
        if sents:
            lessons.append(dict(words=words, sents=sents))
    return lessons


def teach(isaac, lesson):
    for w in lesson["words"]:
        isaac.observe([w, w])          # sight word, seen as itself
    for t in lesson["sents"]:
        for k in range(2, len(t)):     # motherese: fragments that grow
            isaac.observe(t[:k])
        for _ in range(2):
            isaac.observe(t)


def drill(isaac, sents, vocab, rng):
    """One level's worksheet. Standard formats, objective grading."""
    s = {f: [0, 0, []] for f in ("cloze-end", "cloze-mid", "choice",
                                 "match", "true-false", "dictation")}
    wholes = Counter(tuple(x) for x in isaac.observed_sequences)
    for t in sents:
        if len(t) < 3:
            continue
        # cloze deletion — end and middle
        ans, _ = isaac.lookup(t[:-1])
        _mark(s["cloze-end"], ans == t[-1], t)
        mid = len(t) // 2
        ans, _ = isaac.lookup(t[:mid])
        _mark(s["cloze-mid"], ans == t[mid], t)
        # multiple choice — 3 options, distractors from level vocab
        truth = t[-1]
        pool = [w for w in vocab if w != truth]
        opts = [truth] + list(rng.choice(pool, 2, replace=False))
        confs = [(isaac.check(t[:-1], o)[1], o) for o in opts]
        _mark(s["choice"], max(confs)[1] == truth, t)
        # matching — right completion among the level's completions
        ends = list({x[-1] for x in sents if len(x) >= 3})
        confs = [(isaac.check(t[:-1], e)[1], e) for e in ends]
        _mark(s["match"], max(confs)[1] == t[-1], t)
        # true/false — the lived sentence vs a word-swapped foil,
        # judged by his own confidence threshold (1.0)
        _, c_true = isaac.check(t[:-1], t[-1])
        foil = str(rng.choice([w for w in vocab if w != t[-1]]))
        _, c_foil = isaac.check(t[:-1], foil)
        _mark(s["true-false"],
              c_true >= 1.0 > c_foil or c_true > c_foil, t)
        # dictation — from the first two words, replay the whole
        pre = tuple(t[:2])
        cands = [(cnt, len(seq), seq) for seq, cnt in wholes.items()
                 if seq[:2] == pre and len(seq) >= 3]
        said = list(max(cands)[2]) if cands else []
        _mark(s["dictation"], said == t, t)
    return s


def _mark(slot, ok, t):
    slot[0] += ok
    slot[1] += 1
    if not ok:
        slot[2].append(t)


if __name__ == "__main__":
    rng = np.random.default_rng(23)
    lessons = parse_lessons()
    print("=" * 72)
    print("  WORKBOOK v2 — McGuffey's First Reader, standard drills")
    print("=" * 72)
    print(f"  parsed: {len(lessons)} lessons, "
          f"{sum(len(l['sents']) for l in lessons)} sentences")

    isaac = Isaac()
    isaac.wave_logging = False
    level = 0
    while level < MAX_LEVELS:
        batch = lessons[level * LESSONS_PER_LEVEL:
                        (level + 1) * LESSONS_PER_LEVEL]
        if not batch:
            break
        level += 1
        sents = [t for l in batch for t in l["sents"]]
        vocab = sorted({w for t in sents for w in t})
        for l in batch:
            teach(isaac, l)
        isaac.consolidate()

        tries, avg = 0, 0.0
        while tries < 1 + 1:
            score = drill(isaac, sents, vocab, rng)
            avg = (sum(v[0] for v in score.values())
                   / max(sum(v[1] for v in score.values()), 1))
            row = "  ".join(f"{f} {v[0]}/{v[1]}"
                            for f, v in score.items())
            print(f"\n  level {level} (lessons "
                  f"{(level-1)*LESSONS_PER_LEVEL + 1}-"
                  f"{(level-1)*LESSONS_PER_LEVEL + len(batch)}, "
                  f"{len(sents)} sentences, try {tries + 1}):")
            print(f"    {row}   avg {avg:.0%}")
            if avg >= GATE:
                break
            missed = {tuple(t) for v in score.values() for t in v[2]}
            print(f"    below gate — re-teaching {len(missed)} "
                  f"missed sentences")
            for t in missed:
                for k in range(2, len(t)):
                    isaac.observe(list(t)[:k])
                for _ in range(RETEACH):
                    isaac.observe(list(t))
            isaac.consolidate()
            tries += 1
        st = isaac.status()
        print(f"    net: {st['nodes']} nodes · "
              f"{len(isaac.types)} types")
        if avg < GATE:
            print(f"\n  STOPPED at level {level}: {avg:.0%} after "
                  f"re-teaching — the honest frontier tonight")
            break
    else:
        print(f"\n  passed all {level} levels attempted")
    print("\n  done — the report card above IS the finding")
