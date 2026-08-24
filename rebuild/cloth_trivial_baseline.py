"""
TRIVIAL BASELINE for the CLOTH 85% claim (handoff W2 / section 7.1).
READ-ONLY on the repo: reads data/cloth JSONs only, writes nothing.

Replicates cloth_run.py's passage selection EXACTLY (sorted glob, load(),
keep passages with >=1 single-token item, stop at 120), then scores:

  (a) EXACT-POSITION match: pick the option whose token equals the token
      at the blank position in the taught (completed) passage.
  (b) ANYWHERE-IN-PASSAGE match: pick an option whose token appears
      anywhere in the taught word stream of the SAME passage.
      Tie policy: first-listed option among matches (deterministic);
      expected value under random tie-break also reported.
  (c) SAME-INPUTS suffix lookup ("grep baseline"): given ONLY what the
      exam gives Isaac (the <=8-token left context + 4 options) and the
      taught material (all 120 passages as word streams), find the
      longest suffix of the context (width 8..2) occurring in ANY taught
      stream, count next-tokens, pick the option with the highest count.
      Ties/no-evidence -> first-listed option (counted separately).
  (c') same as (c) but windows restricted to within taught sentences
      (Isaac's own preprocessing scope: one observe() per sentence).

Also reports: item counts, blank-filter losses, whether the full context
window appears verbatim in the taught stream, and the score of "always
pick the alphabetically-last option" (the harness's tie-break behavior
when all confidences are 0.0, i.e. the pre-teaching control's actual
deterministic policy — cloth_run.py:78-81 max() over (conf, text)).

tokenize() copied verbatim from code/isaac.py:146-150.
load()/sentences() copied verbatim from rebuild/cloth_run.py:34-67
(load additionally returns n_blanks; selection logic unchanged).
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict
from glob import glob

# data path relative to this file (same layout as cloth_run.py:25-26)
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "..", "data", "cloth", "CLOTH", "train", "middle")
N_PASSAGES = 120

# collected check failures; gate at the bottom exits nonzero if any
FAILS = []
CTX = 8
LETTERS = "ABCD"


def tokenize(text):
    # verbatim: code/isaac.py:146-150
    return re.findall(r"[a-zA-Z0-9_]+|[^\s]", text.lower())


def load(path):
    # verbatim: rebuild/cloth_run.py:34-55 (+ n_blanks instrumentation)
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
    items = [b for b in blanks
             if all(len(tokenize(o)) == 1 for o in b["options"])
             and len(tokenize(b["truth"])) == 1]
    return dict(toks=toks, items=items, n_blanks=len(blanks))


def sentences(toks):
    # verbatim: rebuild/cloth_run.py:58-67
    out, cur = [], []
    for t in toks:
        cur.append(t)
        if t in ".?!" and len(cur) > 1:
            out.append([x for x in cur if re.match(r"\w", x)])
            cur = []
    if len(cur) > 1:
        out.append([x for x in cur if re.match(r"\w", x)])
    return [s for s in out if len(s) >= 2]


# ── selection: verbatim logic of cloth_run.py:87-94 ─────────────────
files = sorted(glob(os.path.join(DATA, "*.json")))
if not files:
    print("SKIP: no CLOTH data at %s" % DATA)
    sys.exit(77)
passages = []
for f in files:
    p = load(f)
    if p and p["items"]:
        passages.append(p)
    if len(passages) >= N_PASSAGES:
        break

n_items = sum(len(p["items"]) for p in passages)
n_blanks = sum(p["n_blanks"] for p in passages)
print("passages: %d   blanks in them: %d   single-token items kept: %d"
      % (len(passages), n_blanks, n_items))

# taught material per passage, exactly what observe() received
streams = [[t for s in sentences(p["toks"]) for t in s] for p in passages]
sent_lists = [sentences(p["toks"]) for p in passages]

# suffix -> next-token counters over ALL taught streams (widths 2..8)
nxt_flat = defaultdict(Counter)
for words in streams:
    for i in range(len(words) - 1):
        for w in range(2, 9):
            if i - w + 1 >= 0:
                nxt_flat[tuple(words[i - w + 1:i + 1])][words[i + 1]] += 1

# same, but within taught sentences only (Isaac's observation scope)
nxt_sent = defaultdict(Counter)
for slists in sent_lists:
    for s in slists:
        for i in range(len(s) - 1):
            for w in range(2, 9):
                if i - w + 1 >= 0:
                    nxt_sent[tuple(s[i - w + 1:i + 1])][s[i + 1]] += 1

included = 0
skipped_short_ctx = 0
a_right = a_multi = a_zero = 0
b_right_first = 0
b_expect = 0.0
b_truth_absent = 0
b_nmatch_sum = 0
c_right = c_noev = 0
cs_right = cs_noev = 0
full_ctx_verbatim = 0
alpha_last_right = 0
sanity_pos_mismatch = 0

for pi, p in enumerate(passages):
    words = streams[pi]
    wordset = set(words)
    for b in p["items"]:
        ctx = [t for t in p["toks"][max(0, b["pos"] - CTX):b["pos"]]
               if re.match(r"\w", t)]
        if len(ctx) < 2:                     # exam() skip rule, cloth_run.py:76-77
            skipped_short_ctx += 1
            continue
        included += 1
        truth = b["truth"]
        opts_tok = [tokenize(o)[0] for o in b["options"]]

        # sanity: the completed passage holds the truth at the blank position
        if p["toks"][b["pos"]] != tokenize(truth)[0]:
            sanity_pos_mismatch += 1

        # (a) exact-position
        postok = p["toks"][b["pos"]]
        matches = [o for o, ot in zip(b["options"], opts_tok) if ot == postok]
        if not matches:
            a_zero += 1
            pick = b["options"][0]
        else:
            if len(matches) > 1:
                a_multi += 1
            pick = matches[0]
        a_right += pick == truth

        # (b) anywhere in own taught stream
        present = [o for o, ot in zip(b["options"], opts_tok) if ot in wordset]
        b_nmatch_sum += len(present)
        if truth not in present:
            b_truth_absent += 1
        pick = present[0] if present else b["options"][0]
        b_right_first += pick == truth
        if present and truth in present:
            b_expect += 1.0 / len(present)

        # (c)/(c') longest-suffix next-token lookup
        for table, is_flat in ((nxt_flat, True), (nxt_sent, False)):
            picked = None
            for w in range(min(8, len(ctx)), 1, -1):
                cnts = table.get(tuple(ctx[-w:]))
                if not cnts:
                    continue
                scored = [(cnts.get(ot, 0), -k)          # ties -> first-listed
                          for k, ot in enumerate(opts_tok)]
                best = max(scored)
                if best[0] > 0:
                    picked = b["options"][-best[1]]
                    break
            if picked is None:
                picked = b["options"][0]
                if is_flat:
                    c_noev += 1
                else:
                    cs_noev += 1
            if is_flat:
                c_right += picked == truth
            else:
                cs_right += picked == truth

        # does the full quiz context window occur verbatim in taught text?
        w = len(ctx)
        if w <= 8 and tuple(ctx) in nxt_flat or \
           any(tuple(ctx) == tuple(words[i:i + w])
               for i in range(len(words) - w + 1)):
            full_ctx_verbatim += 1

        # harness tie-break policy when every confidence is 0.0
        alpha_last_right += max(b["options"]) == truth

N = included
print("items in exam (ctx>=2): %d   skipped for short ctx: %d"
      % (N, skipped_short_ctx))
print("sanity pos-token != truth-token: %d" % sanity_pos_mismatch)
print()
print("(a) exact-position match:      %4d/%d = %.1f%%   "
      "(multi-option matches: %d, zero-match items: %d)"
      % (a_right, N, 100.0 * a_right / N, a_multi, a_zero))
print("(b) anywhere-in-passage, ties->first: %4d/%d = %.1f%%"
      % (b_right_first, N, 100.0 * b_right_first / N))
print("(b) anywhere-in-passage, random-tie expected: %.1f%%   "
      "(avg options present: %.2f, truth absent from stream: %d)"
      % (100.0 * b_expect / N, b_nmatch_sum / float(N), b_truth_absent))
print("(c) suffix-lookup, cross-sentence windows:    %4d/%d = %.1f%%   "
      "(no-evidence fallbacks: %d)"
      % (c_right, N, 100.0 * c_right / N, c_noev))
print("(c') suffix-lookup, within-sentence windows:  %4d/%d = %.1f%%   "
      "(no-evidence fallbacks: %d)"
      % (cs_right, N, 100.0 * cs_right / N, cs_noev))
print()
print("full quiz context verbatim in taught stream:  %4d/%d = %.1f%%"
      % (full_ctx_verbatim, N, 100.0 * full_ctx_verbatim / N))
print("always-pick-alphabetically-last option:       %4d/%d = %.1f%%  "
      "(the harness tie-break when all confs are 0)"
      % (alpha_last_right, N, 100.0 * alpha_last_right / N))

# ── gate ─────────────────────────────────────────────────────────────
# (a) is 100% by construction: the completed passage holds the truth
# token at the blank position. Anything else means the harness or the
# corpus changed, so it must go red.
if a_right != N:
    FAILS.append("exact_position_100pct")
# with the standard 120-passage selection the corpus yields 1108
# single-token items; a different count means the corpus changed
if len(passages) == 120 and n_items != 1108:
    FAILS.append("item_count_1108")

print()
if FAILS:
    print("GATE: FAIL (%s)" % ", ".join(FAILS))
else:
    print("GATE: PASS")
sys.exit(1 if FAILS else 0)
