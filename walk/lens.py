#!/usr/bin/env python3
"""lens.py -- comparison lenses, entirely his: right vs wrong from the key.

    python walk/lens.py 999999 -jobs 24

Owner: "do comparison reservoirs to see what was right vs wrong... what
contributing factors were right vs wrong. we need it to be entirely him,
not us. he has the answer key and should be able to resolve it without
you making decisions. adversarial learning against himself and the
answer."

ATOMS     nothing named by us. what he can see about a question and a
          candidate: the words the question has, the words the candidate
          has, the words both have, his own shared count and his own
          rarity. that is all.
LENS      random conjunctions of atoms DRAWN FROM WHAT OCCURS in his
          pairs. how many, how long, and how many sightings a conjunction
          needs before it counts are his to set: each alternative is
          looked at once on the other half; the more right one is kept.
READOUT   on his half: the right sentence (he has the key) against every
          other candidate in his field. what a conjunction earned is how
          much more often it sits on the right one.
USE       the lens decides the ties he now decides by nothing.
RECURSIVE the next lens reads only the questions the chain still gets
          wrong; the chain stops when a level gains nothing.
CRITIC    against himself: a lens over (question, HIS top answer) taught
          by the key when he was wrong. when it objects he takes his
          runner-up. measured: how often the objection is right, and what
          switching gains.
SPEED     the atoms are computed once, in parallel, and kept as arrays;
          every lens, readout and exam after that is matrix work on the
          gpu (torch), so a test costs milliseconds, not minutes.
"""
import json
import math
import os
import random
import sys
import time
from collections import Counter

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "engine"))
from core import Store
from linker import link, terms
import mind
from mind import score_all, diagnose, load_tools, use

SQUAD = os.environ.get(
    "ISAAC_SQUAD",
    r"C:\Users\jtwee\Downloads\New folder (3)\intellon\train-v2.0.json")
TOP = 20
DEV = torch.device("cuda" if torch.cuda.is_available() else "cpu")
SETTINGS = {"size": 300, "length": 2, "min_seen": 20}
OPTIONS = {"size": [300, 1000, 3000], "length": [2, 3], "min_seen": [5, 20, 100]}


def split(data, want):
    arts, n = [], 0
    for art in data:
        if n >= want:
            break
        n += sum(1 for p in art["paragraphs"] for qa in p["qas"]
                 if not qa.get("is_impossible"))
        arts.append(art)
    half = len(arts) // 2
    return arts[:half], arts[half:]


def fill(art):
    store = Store()
    for p in art["paragraphs"]:
        link(p["context"], store, tag=art["title"])
    return store


def questions(art):
    return [(qa["question"], qa["answers"][0]["text"])
            for p in art["paragraphs"] for qa in p["qas"]
            if not qa.get("is_impossible")]


# ------------------------------------------------------------------ atoms
def atoms(store, own, name):
    it = store.get(name)
    r = {w for w in it.refs if store.get(w) is not None
         and store.get(w).kind == "term"}
    a = {"q:" + w for w in own} | {"c:" + w for w in r} | \
        {"both:" + w for w in own & r}
    shared = own & r
    a.add("share:%s" % (len(shared) if len(shared) < 3 else "3+"))
    if shared:
        rare = max(1.0 / len(store.get(t).refs) for t in shared
                   if store.get(t) and store.get(t).refs)
        a.add("rare:" + ("hi" if rare >= 0.5 else "mid" if rare >= 0.1 else "lo"))
    return a


# ------------------------------------------------- the two parallel passes
INDEX = {}


def init(index):
    load_tools()
    use("thes+kinds-second")
    INDEX.clear()
    INDEX.update(index)


def pass_atoms(art):
    """which atoms occur, on his half."""
    store = fill(art)
    seen = Counter()
    for q, key in questions(art):
        _, _, cands = score_all(store, q)
        own = set(terms(q))
        for _, name in cands[:TOP]:
            seen.update(atoms(store, own, name))
    return seen


def pass_fields(job):
    """one article, either half: per question the field, per candidate its
    atom ids, whether it is right, and whether it ties his top score."""
    art, side = job
    store = fill(art)
    out = []
    for qi, (q, key) in enumerate(questions(art)):
        seeds, reached, cands = score_all(store, q)
        field = cands[:TOP]
        if side == "learn":
            d = diagnose(store, q, cands, reached, key)
            names = [n for _, n in field]
            if not d["right"] or d["right"] not in names:
                continue
            right = [n == d["right"] for n in names]
        else:
            if not cands:
                out.append([])          # asked, nothing to say
                continue
            k = key.lower()
            right = [k in str(store.get(n).content).lower() for _, n in field]
        own = set(terms(q))
        topkey = field[0][0]
        rows = []
        for j, ((k_, n), r) in enumerate(zip(field, right)):
            ids = [INDEX[a] for a in atoms(store, own, n) if a in INDEX]
            rows.append((ids, r, k_ == topkey))
        out.append(rows)
    return out


def run(fn, jobs_list, jobs, index):
    if jobs > 1:
        from multiprocessing import Pool
        with Pool(jobs, initializer=init, initargs=(index,)) as pool:
            return pool.map(fn, jobs_list)
    init(index)
    return [fn(j) for j in jobs_list]


class Side:
    """one half as arrays on the device."""
    def __init__(self, per_article):
        ids, rows, right, top, qid, j = [], [], [], [], [], []
        c = q = 0
        self.asked = 0
        for art in per_article:
            for field in art:
                self.asked += 1
                if not field:
                    continue
                for jj, (a, r, t) in enumerate(field):
                    ids.extend(a); rows.extend([c] * len(a))
                    right.append(r); top.append(t); qid.append(q); j.append(jj)
                    c += 1
                q += 1
        self.n, self.nq = c, q
        L = lambda x, dt: torch.tensor(np.asarray(x, dtype=dt), device=DEV)
        self.ids, self.rows = L(ids, np.int64), L(rows, np.int64)
        self.right, self.top = L(right, bool), L(top, bool)
        self.qid, self.j = L(qid, np.int64), L(j, np.int64)

    def columns(self, atom_ids, n_atoms):
        pos = torch.full((n_atoms,), -1, dtype=torch.long, device=DEV)
        pos[torch.tensor(atom_ids, device=DEV)] = torch.arange(len(atom_ids), device=DEV)
        cols = pos[self.ids]
        m = cols >= 0
        M = torch.zeros((self.n, len(atom_ids)), dtype=torch.bool, device=DEV)
        M[self.rows[m], cols[m]] = True
        return M

    def conj(self, lens, n_atoms):
        """the conjunction matrix: candidates x conjunctions, true where
        every atom of the conjunction is on the candidate."""
        A = sorted({a for c in lens for a in c})
        M = self.columns(A, n_atoms)
        pos = {a: i for i, a in enumerate(A)}
        C = torch.ones((self.n, len(lens)), dtype=torch.bool, device=DEV)
        for k in range(len(lens[0])):
            C &= M[:, torch.tensor([pos[c[k]] for c in lens], device=DEV)]
        return C


def draw_lens(seen_ids, weights, rng):
    conj, tries = set(), 0
    while len(conj) < SETTINGS["size"] and tries < SETTINGS["size"] * 50:
        tries += 1
        c = tuple(sorted(set(rng.choices(seen_ids, weights, k=SETTINGS["length"]))))
        if len(c) == SETTINGS["length"]:
            conj.add(c)
    return sorted(conj)


def readout(C, right, inplay):
    """right vs every other, over the candidates in play."""
    pos = (right & inplay).float()
    neg = (~right & inplay).float()
    rc, wc = pos @ C.float(), neg @ C.float()
    npos, nneg = max(pos.sum().item(), 1.0), max(neg.sum().item(), 1.0)
    earned = torch.log((rc + 0.5) / npos / ((wc + 0.5) / nneg))
    earned[(rc + wc) < SETTINGS["min_seen"]] = 0.0
    return earned, rc, wc


def choose(side, signals, exclude=None):
    """per question: his top group, then each signal in turn breaks the
    ties the one before left, then his own order. returns the chosen
    candidate index per question (-1 if none)."""
    mask = side.top.clone()
    if exclude is not None:
        mask[exclude[exclude >= 0]] = False
        empty = torch.zeros(side.nq, dtype=torch.bool, device=DEV)
        empty.scatter_(0, side.qid, torch.zeros_like(side.qid, dtype=torch.bool))
        has = torch.zeros(side.nq, dtype=torch.bool, device=DEV)
        has.scatter_(0, side.qid[mask], torch.ones(int(mask.sum()), dtype=torch.bool, device=DEV))
        fallback = (~has)[side.qid] & (side.j == 1)
        mask |= fallback
    for s in signals:
        best = torch.full((side.nq,), -1e30, device=DEV)
        best.scatter_reduce_(0, side.qid[mask], s[mask], reduce="amax")
        mask &= s >= best[side.qid] - 1e-6
    minj = torch.full((side.nq,), 10 ** 6, dtype=torch.long, device=DEV)
    minj.scatter_reduce_(0, side.qid[mask], side.j[mask], reduce="amin")
    pick = mask & (side.j == minj[side.qid])
    chosen = torch.full((side.nq,), -1, dtype=torch.long, device=DEV)
    idx = torch.nonzero(pick).squeeze(1)
    chosen[side.qid[idx]] = idx
    return chosen


def n_right(side, chosen):
    ok = chosen >= 0
    return int(side.right[chosen[ok]].sum().item())


def say(names, c):
    out = []
    for x in c:
        k, _, v = names[x].partition(":")
        out.append({"q": "question has '%s'", "c": "candidate has '%s'",
                    "both": "both have '%s'", "share": "they share %s words",
                    "rare": "the shared word is %s rarity"}[k] % v)
    return " AND ".join(out)


def show_top(names, lens, earned, rc, wc, n=16):
    e = earned.cpu().numpy(); r = rc.cpu().numpy(); w = wc.cpu().numpy()
    for i in np.argsort(-np.abs(e))[:n]:
        if e[i] == 0:
            break
        print("    %+.2f  %6d / %-7d %s" % (e[i], r[i], w[i], say(names, lens[i])))


def main():
    want = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    jobs = int(sys.argv[sys.argv.index("-jobs") + 1]) if "-jobs" in sys.argv else 1
    data = json.load(open(SQUAD, encoding="utf-8"))["data"]
    learn, other = split(data, want)
    load_tools()
    t0 = time.perf_counter()
    print("device: %s" % DEV)
    print("prediction, stated first: words-only atoms land near the last lens "
          "(+0.2); the chain adds little; the critic gains 0.5 to 1.5 points.\n")

    seen = Counter()
    for s in run(pass_atoms, learn, jobs, {}):
        seen.update(s)
    names = [a for a, c in seen.items() if c >= 2]
    index = {a: i for i, a in enumerate(names)}
    weights = [seen[a] for a in names]
    t1 = time.perf_counter()
    print("atoms that occur on his half: %d  (%.0fs)" % (len(names), t1 - t0))
    fields = run(pass_fields, [(a, "learn") for a in learn] + [(a, "other") for a in other],
                 jobs, index)
    his, oth = Side(fields[:len(learn)]), Side(fields[len(learn):])
    t2 = time.perf_counter()
    print("his half: %d questions with the key in his field, %d candidates; "
          "other half: %d questions, %d candidates  (%.0fs)"
          % (his.nq, his.n, oth.asked, oth.n, t2 - t1))
    base = n_right(oth, choose(oth, []))
    print("other half as he is: %d / %d right (%.1f%%)\n" % (base, oth.asked, 100.0 * base / oth.asked))

    seen_ids = list(range(len(names)))

    def test(lens, chain_prev=()):
        C = his.conj(lens, len(names))
        earned, rc, wc = readout(C, his.right, torch.ones(his.n, dtype=torch.bool, device=DEV))
        sig_o = [oth.conj(l, len(names)).float() @ e for l, e in chain_prev]
        sig_o.append(oth.conj(lens, len(names)).float() @ earned)
        return n_right(oth, choose(oth, sig_o)), earned, rc, wc

    print("HIS SETTINGS FOR A LENS (one look each on the other half):")
    best = None
    for setting, options in OPTIONS.items():
        for value in options:
            was = SETTINGS[setting]
            SETTINGS[setting] = value
            lens = draw_lens(seen_ids, weights, random.Random(7))
            r, earned, rc, wc = test(lens)
            print("  %s = %s%s: %d right (%+d)  %.1fs" % (
                setting, value, " (now)" if value == was else "", r, r - base,
                time.perf_counter() - t2))
            if best is None or r > best[0]:
                best = (r, dict(SETTINGS), lens, earned, rc, wc)
            SETTINGS[setting] = was
        SETTINGS[setting] = best[1][setting]
    after1, chosen_s, lens, earned, rc, wc = best
    SETTINGS.update(chosen_s)
    print("  he keeps: %s -> %d right (%+d)\n" % (chosen_s, after1, after1 - base))
    print("  what carried meaning, right vs wrong:")
    show_top(names, lens, earned, rc, wc)

    print("\nRECURSIVE: each lens reads only the questions the chain still misses")
    chain = [(lens, earned)]
    last = after1
    for level in range(2, 6):
        sig_h = [his.conj(l, len(names)).float() @ e for l, e in chain]
        ch = choose(his, sig_h)
        wrong_q = ~his.right[ch]
        inplay = wrong_q[his.qid]
        lens2 = draw_lens(seen_ids, weights, random.Random(100 + level))
        C2 = his.conj(lens2, len(names))
        earned2, rc2, wc2 = readout(C2, his.right, inplay)
        sig_o = [oth.conj(l, len(names)).float() @ e for l, e in chain]
        sig_o.append(oth.conj(lens2, len(names)).float() @ earned2)
        r = n_right(oth, choose(oth, sig_o))
        print("  level %d: read from %d still-wrong questions -> %d right (%+d vs level %d)"
              % (level, int(wrong_q.sum().item()), r, r - last, level - 1))
        if r <= last:
            print("  gains nothing; the chain stops at level %d" % (level - 1))
            break
        chain.append((lens2, earned2))
        last = r

    print("\nTHE CRITIC: a lens over (question, HIS top answer), taught by the key "
          "when he was wrong")
    sig_h = [his.conj(l, len(names)).float() @ e for l, e in chain]
    ch_h = choose(his, sig_h)
    onlytop = torch.zeros(his.n, dtype=torch.bool, device=DEV)
    onlytop[ch_h[ch_h >= 0]] = True
    clens = draw_lens(seen_ids, weights, random.Random(9))
    Cc = his.conj(clens, len(names))
    cearned, crc, cwc = readout(Cc, ~his.right, onlytop)     # "right" = he was wrong
    print("  what marks a wrong top answer:")
    show_top(names, clens, cearned, crc, cwc, 10)
    sig_o = [oth.conj(l, len(names)).float() @ e for l, e in chain]
    ch_o = choose(oth, sig_o)
    after = n_right(oth, ch_o)
    csc = oth.conj(clens, len(names)).float() @ cearned
    runner = choose(oth, sig_o, exclude=ch_o)
    for cut in (0.0, 1.0, 2.0, 3.0):
        ok = ch_o >= 0
        obj = ok & (csc[ch_o.clamp(min=0)] > cut)
        objected = int(obj.sum().item())
        obj_right = int((obj & ~oth.right[ch_o.clamp(min=0)]).sum().item())
        final = torch.where(obj & (runner >= 0), runner, ch_o)
        sw = n_right(oth, final)
        print("  objects when its score > %.0f: objected on %d (%.1f%%), right to "
              "object %d (%.0f%%); taking the runner-up then -> %d right (%+d)"
              % (cut, objected, 100.0 * objected / oth.asked, obj_right,
                 100.0 * obj_right / max(objected, 1), sw, sw - after))
    print("\nRESULT: other half %d / %d as he is (%.1f%%); with his lens chain %d (%+d)"
          % (base, oth.asked, 100.0 * base / oth.asked, after, after - base))
    json.dump({"settings": SETTINGS, "atoms": names,
               "chain": [[list(c) for c in l] for l, _ in chain],
               "earned": [e.cpu().tolist() for _, e in chain],
               "critic": [list(c) for c in clens], "critic_earned": cearned.cpu().tolist()},
              open(os.path.join(HERE, "lens.json"), "w", encoding="utf-8"))
    print("saved walk/lens.json  (%.0fs in all)" % (time.perf_counter() - t0))


if __name__ == "__main__":
    main()
