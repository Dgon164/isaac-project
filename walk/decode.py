#!/usr/bin/env python3
"""decode.py -- the comparison net: train something else on his task, then
read what it sees.

    python walk/decode.py 999999 -jobs 24            data, train, decode

Owner: "do the whole net decoding thing we did, but make it so that the
neural net being run is the comparison. see what the input is
contributing to a trained output. to see what something else explicitly
sees."

THE NET   a small alignment scorer, nothing clever: every question word
          and every candidate word gets a vector; a candidate word also
          gets a vector for its position in the sentence; the question's
          kind gets one. score(candidate) = sum over question words of
          the best match against the candidate's words. Trained on his
          half to put the right sentence first among his top twenty.
THE TEST  the other half, top-1, against his 63.5. That gap is how much
          more something else sees in the same words.
THE DECODE for every right answer on the other half: which candidate
          word each question word attended to, at what position, of what
          type. Aggregated and printed as sentences:
            - pairs where the words differ: the net's own thesaurus and
              relations, compared with his (in his / new to him)
            - where in the sentence the attended word sits, by question
              kind, and for "what is X" questions in particular
            - what type the attended word carries, by kind, against his
              kinds table
The net is scaffolding. What it saw, in words, is what we keep.
"""
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "engine"))
from core import Store
from linker import link, terms
import mind
from mind import score_all, diagnose, kind, load_tools, use, KIND_WORDS
import tools as T

DEV = torch.device("cuda" if torch.cuda.is_available() else "cpu")
TOP, QLEN, CLEN, VOCAB, DIM = 20, 12, 40, 30000, 64
KINDS = list(KIND_WORDS) + ["other"]
YEAR = re.compile(r"^(1[0-9]{3}|20[0-9]{2})$")


def init():
    load_tools()
    use("thes+kinds-second")


def pass_seq(job):
    """one article: per question its words, its kind; per candidate in his
    top twenty the sentence's words IN ORDER, and whether it is right."""
    art, side = job
    store = T.fill(art)
    out = []
    for q, key in T.questions(art):
        seeds, reached, cands = score_all(store, q)
        field = cands[:TOP]
        if not field:
            continue
        if side == "learn":
            d = diagnose(store, q, cands, reached, key)
            if not d["right"] or d["right"] not in [n for _, n in field]:
                continue
            right = [n == d["right"] for _, n in field]
        else:
            k = key.lower()
            right = [k in str(store.get(n).content).lower() for _, n in field]
        rows = []
        for (_, n), r in zip(field, right):
            it = store.get(n)
            # the sentence's tokens IN ORDER, numbers and small words included:
            # the net gets to see what his linker drops
            seq = re.findall(r"[a-z0-9]+", str(it.content).lower())
            rows.append((seq[:CLEN], r))
        # the question side: his content words plus any numbers. small words
        # stay on the candidate side (positions), but a question's "the" must
        # not get a vote, or the net learns to align "the" with "of"
        qtoks = [w for w in re.findall(r"[a-z0-9]+", q.lower()) if w.isdigit()] + terms(q)
        out.append((qtoks[:QLEN], kind(q), rows))
    return out


def run(jobs_list, jobs):
    if jobs > 1:
        from multiprocessing import Pool
        with Pool(jobs, initializer=init) as pool:
            return pool.map(pass_seq, jobs_list)
    init()
    return [pass_seq(j) for j in jobs_list]


class Half:
    def __init__(self, per_article, vocab):
        Q, QK, C, R, QID = [], [], [], [], []
        qi = 0
        for art in per_article:
            for qwords, k, rows in art:
                qids = [vocab.get(w, 1) for w in qwords] + [0] * (QLEN - len(qwords))
                for seq, r in rows:
                    cids = [vocab.get(w, 1) for w in seq] + [0] * (CLEN - len(seq))
                    Q.append(qids); QK.append(KINDS.index(k)); C.append(cids); R.append(r); QID.append(qi)
                qi += 1
        L = lambda x, dt: torch.tensor(np.asarray(x, dtype=dt), device=DEV)
        self.q, self.qk, self.c = L(Q, np.int64), L(QK, np.int64), L(C, np.int64)
        self.right, self.qid = L(R, bool), L(QID, np.int64)
        self.n, self.nq = len(R), qi


class Aligner(nn.Module):
    """one vocabulary for both sides, so a word matching itself is the base
    signal; candidate words weighted by rarity, so "the" cannot be a sink;
    position and kind as small additions the net may learn to use."""
    def __init__(self, idf):
        super().__init__()
        self.emb = nn.Embedding(VOCAB + 2, DIM, padding_idx=0)
        self.pos = nn.Embedding(CLEN, DIM)
        self.kind = nn.Embedding(len(KINDS), DIM)
        self.exact = nn.Parameter(torch.tensor(1.0))
        self.register_buffer("idf", idf)                                # VOCAB+2

    def align(self, q, qk, c):
        """[b, QLEN, CLEN] similarities, masked; plus the score."""
        qe = self.emb(q) + 0.1 * self.kind(qk)[:, None, :]              # b x QLEN x D
        ce = self.emb(c) + 0.1 * self.pos(torch.arange(CLEN, device=c.device))[None]
        sim = torch.einsum("bqd,bcd->bqc", qe, ce) / DIM ** 0.5
        sim = sim + self.exact * (q[:, :, None] == c[:, None, :]).float()
        sim = sim * self.idf[c][:, None, :]                             # rare words count
        sim = sim.masked_fill((c == 0)[:, None, :], -1e4)
        best, where = sim.max(dim=2)                                    # b x QLEN
        best = best.masked_fill(q == 0, 0.0)
        return best.sum(dim=1), where, best

    def forward(self, q, qk, c):
        return self.align(q, qk, c)[0]


def listwise(model, half, idx):
    s = model(half.q[idx], half.qk[idx], half.c[idx])
    qid = half.qid[idx]
    # softmax within each question: log-sum-exp per qid via scatter
    m = torch.full((half.nq,), -1e30, device=DEV).scatter_reduce(0, qid, s, reduce="amax")
    e = torch.exp(s - m[qid])
    z = torch.zeros(half.nq, device=DEV).scatter_add(0, qid, e)
    logp = s - m[qid] - torch.log(z[qid] + 1e-9)
    return -(logp[half.right[idx]]).mean()


def top1(model, half):
    with torch.no_grad():
        s = torch.cat([model(half.q[i:i + 65536], half.qk[i:i + 65536], half.c[i:i + 65536])
                       for i in range(0, half.n, 65536)])
    best = torch.full((half.nq,), -1e30, device=DEV).scatter_reduce(0, half.qid, s, reduce="amax")
    ismax = s >= best[half.qid] - 1e-6
    # first max per question, in his order
    idx = torch.arange(half.n, device=DEV)
    first = torch.full((half.nq,), half.n, dtype=torch.long, device=DEV).scatter_reduce(
        0, half.qid[ismax], idx[ismax], reduce="amin")
    chosen = first[first < half.n]
    return int(half.right[chosen].sum().item()), s


def main():
    want = int(sys.argv[1]) if len(sys.argv) > 1 else 999999
    jobs = int(sys.argv[sys.argv.index("-jobs") + 1]) if "-jobs" in sys.argv else 1
    epochs = int(sys.argv[sys.argv.index("-epochs") + 1]) if "-epochs" in sys.argv else 12
    t0 = time.perf_counter()
    print("device: %s" % DEV)
    print("prediction, stated first: the net lands at 70-75%% top-1 on the other "
          "half (his 63.5); its decoded pairs hold his morphology and synonyms "
          "plus paraphrases he lacks; for 'what is X' questions its attention "
          "sits at the start of the sentence.\n")
    data = json.load(open(T.SQUAD, encoding="utf-8"))["data"]
    learn, other = T.split(data, want)
    seqs = run([(a, "learn") for a in learn] + [(a, "other") for a in other], jobs)
    cnt = Counter(w for art in seqs[:len(learn)] for qw, k, rows in art for w in qw)
    cnt.update(w for art in seqs[:len(learn)] for qw, k, rows in art for seq, r in rows for w in seq)
    vocab = {w: i + 2 for i, (w, _) in enumerate(cnt.most_common(VOCAB))}
    inv = {i: w for w, i in vocab.items()}
    inv[1] = "<unknown>"
    his, oth = Half(seqs[:len(learn)], vocab), Half(seqs[len(learn):], vocab)
    print("his half: %d questions, %d candidates; other half: %d questions, %d candidates; "
          "vocabulary %d  (%.0fs)" % (his.nq, his.n, oth.nq, oth.n, len(vocab), time.perf_counter() - t0))
    base_o = int(oth.right[torch.nonzero(torch.cat([torch.tensor([True], device=DEV),
                 oth.qid[1:] != oth.qid[:-1]])).squeeze(1)].sum().item())
    print("as he is (his first candidate) on the other half: %d / %d (%.1f%%)\n"
          % (base_o, oth.nq, 100.0 * base_o / oth.nq))

    # rarity of each candidate word over his half: log(candidates / candidates carrying it)
    df = torch.zeros(VOCAB + 2, device=DEV)
    ids, counts = torch.unique(his.c, return_counts=True)       # occurrences, near enough
    df[ids] = counts.float()
    idf = torch.log((his.n + 1.0) / (df + 1.0)).clamp(min=0.0)
    idf[0] = 0.0
    torch.manual_seed(1)
    model = Aligner(idf).to(DEV)
    opt = torch.optim.AdamW(model.parameters(), lr=2e-3, weight_decay=1e-2)
    qids = torch.arange(his.nq, device=DEV)
    for ep in range(1, epochs + 1):
        t1 = time.perf_counter()
        perm = qids[torch.randperm(his.nq, device=DEV)]
        losses = []
        for i in range(0, his.nq, 512):
            batch_q = perm[i:i + 512]
            mask = torch.isin(his.qid, batch_q)
            idx = torch.nonzero(mask).squeeze(1)
            opt.zero_grad()
            loss = listwise(model, his, idx)
            loss.backward()
            opt.step()
            losses.append(loss.item())
        r_h, _ = top1(model, his)
        r_o, _ = top1(model, oth)
        print("  epoch %d: loss %.3f | his half %.1f%% | other half %d (%.1f%%)  %.0fs"
              % (ep, float(np.mean(losses)), 100.0 * r_h / his.nq, r_o, 100.0 * r_o / oth.nq,
                 time.perf_counter() - t1))
    r_o, scores = top1(model, oth)
    print("\nTHE COMPARISON: something else, on the same words: %d / %d (%.1f%%) vs his %.1f%%: %+.1f points\n"
          % (r_o, oth.nq, 100.0 * r_o / oth.nq, 100.0 * base_o / oth.nq, 100.0 * (r_o - base_o) / oth.nq))

    # ------------------------------------------------------------- decode
    tools = json.load(open(os.path.join(HERE, "tools.json"), encoding="utf-8"))
    his_pairs = {(q, s) for q, ss in tools["thesaurus"].items() for s in ss}
    his_rel = {(q, s) for q, ss in tools.get("relations", {}).items() for s in ss}
    right_idx = torch.nonzero(oth.right).squeeze(1)
    pairs, posby, typeby, defpos = Counter(), defaultdict(list), defaultdict(Counter), []
    with torch.no_grad():
        for i in range(0, len(right_idx), 65536):
            idx = right_idx[i:i + 65536]
            _, where, best = model.align(oth.q[idx], oth.qk[idx], oth.c[idx])
            q = oth.q[idx].cpu().numpy(); c = oth.c[idx].cpu().numpy()
            wh = where.cpu().numpy(); bs = best.cpu().numpy(); qk = oth.qk[idx].cpu().numpy()
            for b in range(len(idx)):
                k = KINDS[qk[b]]
                qws = [inv.get(t, "?") for t in q[b] if t]
                for j, t in enumerate(q[b]):
                    if not t or bs[b, j] <= 0:
                        continue
                    qw, pos = inv.get(int(t), "?"), int(wh[b, j])
                    cw = inv.get(int(c[b, pos]), "?")
                    if "<unknown>" in (qw, cw) or "?" in (qw, cw):
                        continue
                    if qw != cw:
                        pairs[(qw, cw)] += 1
                    posby[k].append(pos)
                    typ = "year" if YEAR.match(cw) else "number" if cw.isdigit() else "word"
                    typeby[k][typ] += 1
                if qws[:2] in (["what", "is"], ["what", "are"], ["what", "was"]) and len(qws) <= 5:
                    defpos.extend(int(wh[b, j]) for j, t in enumerate(q[b]) if t)
    print("WHAT THE NET ATTENDED TO, decoded on the other half's right answers")
    print("  pairs of different words the net aligned most (its thesaurus and relations):")
    new = 0
    for (qw, cw), n in pairs.most_common(30):
        tag = "in his thesaurus" if (qw, cw) in his_pairs else "in his relations" if (qw, cw) in his_rel \
            else "NEW to him"
        new += tag.startswith("NEW")
        print("    %5d  %-14s -> %-14s %s" % (n, qw, cw, tag))
    print("  of the top 30, new to him: %d" % new)
    print("\n  where in the sentence the attended word sits (mean position, 0 = first word):")
    for k in KINDS:
        if posby[k]:
            a = np.array(posby[k])
            print("    %-9s mean %4.1f   first-two-words %3.0f%%   (n=%d)"
                  % (k, a.mean(), 100.0 * (a <= 1).mean(), len(a)))
    if defpos:
        a = np.array(defpos)
        print("    'what is X' questions: mean position %.1f, in the first two words %.0f%% (n=%d)"
              % (a.mean(), 100.0 * (a <= 1).mean(), len(a)))
    print("\n  what type the attended word carries, by kind (his kinds table said when->year, "
          "how many->number):")
    for k in KINDS:
        tot = sum(typeby[k].values())
        if tot:
            print("    %-9s year %3.0f%%  number %3.0f%%  word %3.0f%%"
                  % (k, 100.0 * typeby[k]["year"] / tot, 100.0 * typeby[k]["number"] / tot,
                     100.0 * typeby[k]["word"] / tot))
    torch.save(model.state_dict(), os.path.join(HERE, "decode.pt"))
    json.dump({"pairs": [[q, c, n] for (q, c), n in pairs.most_common(2000)]},
              open(os.path.join(HERE, "decode.json"), "w", encoding="utf-8"))
    print("\nsaved walk/decode.json (the net's pairs) and walk/decode.pt  (%.0fs in all)"
          % (time.perf_counter() - t0))


if __name__ == "__main__":
    main()
