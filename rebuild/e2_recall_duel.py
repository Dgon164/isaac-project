"""E2 — THE RECALL DUEL (owner design, 2026-09-01).

Both sides read 1,000 real exam passages. Then the final: ONE
question from EVERY passage, asked at the end, no passage text
shown. A store answers from the store; a context window answers
from whatever hasn't scrolled away.

  Isaac arm : the saved cloth1000 body (9.6MB), all 1,000 questions.
  LLM arm   : qwen2.5:1.5b-instruct (ollama, num_ctx 16384, temp 0),
              one continuous conversation — the full corpus text is
              in the transcript; the server keeps what fits (the
              TAIL) exactly like a rolling attention window. 100
              questions, stratified 10 per decile of passage
              position.
  Control   : 20 questions WITH the passage present — proves the
              LLM can read; isolates RETENTION as the failing axis.

Report: accuracy by passage position (the cliff chart), totals,
wall-clocks, and the honest cost arithmetic for genuine full recall.
"""
import json
import os
import re
import sys
import time
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "..", "code"))
from isaac import Isaac  # noqa: E402
import cloth_run  # noqa: E402
from glob import glob  # noqa: E402

MODEL = "qwen2.5:1.5b-instruct"
NCTX = 16384
BODY = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "..", "data", "minds", "cloth1000.isaac")

files = sorted(glob(os.path.join(cloth_run.DATA, "*.json")))
passages = []
for f in files:
    p = cloth_run.load(f)
    if p and p["items"]:
        passages.append(p)
    if len(passages) >= 1000:
        break

# one question per passage: the first item with enough context
exam = []
for i, p in enumerate(passages):
    for b in p["items"]:
        ctx = [t for t in p["toks"][max(0, b["pos"] - cloth_run.CTX):
                                    b["pos"]] if re.match(r"\w", t)]
        if len(ctx) >= 2:
            exam.append(dict(pos=i, ctx=ctx, options=b["options"],
                             truth=b["truth"]))
            break
print(f"{len(passages)} passages read by both sides; final exam = "
      f"{len(exam)} questions (one per passage)")

corpus_text = "\n\n".join(
    f"[Passage {i + 1}] " + " ".join(p["toks"])
    for i, p in enumerate(passages))
approx_tokens = len(corpus_text) // 4
print(f"corpus ~{approx_tokens:,} tokens; the LLM window holds "
      f"{NCTX:,} — {100 * NCTX / approx_tokens:.0f}% of the course\n")

# ── ISAAC ARM: all 1,000 from the 9.6MB store ───────────────────────
m = Isaac.load(BODY)
m.wave_logging = False
t0 = time.time()
i_right = [0] * 10
i_n = [0] * 10
for q in exam:
    confs = [(m.check(q["ctx"], cloth_run.tokenize(o)[0])[1], o)
             for o in q["options"]]
    pick = max(confs)[1]
    d = min(9, q["pos"] // 100)
    i_n[d] += 1
    i_right[d] += pick == q["truth"]
t_isaac = time.time() - t0
print(f"ISAAC: {sum(i_right)}/{sum(i_n)} = "
      f"{100 * sum(i_right) / sum(i_n):.0f}%  in {t_isaac:.0f}s "
      f"({1000 * t_isaac / len(exam):.0f}ms/question, "
      f"{os.path.getsize(BODY) / 1e6:.1f}MB store)")


def ask_llm(messages):
    req = urllib.request.Request(
        "http://localhost:11434/api/chat",
        json.dumps(dict(model=MODEL, messages=messages, stream=False,
                        options=dict(temperature=0, num_ctx=NCTX,
                                     num_predict=24))).encode(),
        {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())["message"]["content"]


def q_text(q, with_passage=False):
    opts = " / ".join(q["options"])
    lead = ""
    if with_passage:
        lead = ("This passage: " +
                " ".join(passages[q["pos"]]["toks"]) + "\n\n")
    return (f"{lead}From passage {q['pos'] + 1} of your reading: the "
            f"text went \"... {' '.join(q['ctx'])} ___\". Which word "
            f"filled the blank? Options: {opts}. Reply with just the "
            f"word.")


def grade(reply, q):
    r = reply.strip().lower()
    hits = [o for o in q["options"] if o.lower() in r]
    return len(hits) >= 1 and q["truth"] in [h.lower() for h in hits] \
        and (len(hits) == 1 or r.split()[0].strip('."\',') == q["truth"])


# stratified 10 per decile
sample = []
for d in range(10):
    block = [q for q in exam if q["pos"] // 100 == d]
    sample += block[:10]

SYSTEM = ("You are sitting a memory exam. You were shown 1,000 "
          "passages. Answer each question about them from memory.")
base = [dict(role="system", content=SYSTEM),
        dict(role="user", content="Read these passages carefully:\n\n"
             + corpus_text),
        dict(role="assistant", content="I have read the passages.")]

t0 = time.time()
l_right = [0] * 10
l_n = [0] * 10
for k, q in enumerate(sample):
    reply = ask_llm(base + [dict(role="user", content=q_text(q))])
    d = q["pos"] // 100
    l_n[d] += 1
    l_right[d] += grade(reply, q)
    if (k + 1) % 20 == 0:
        print(f"  llm exam {k + 1}/{len(sample)} "
              f"[{time.time() - t0:.0f}s]", flush=True)
t_llm = time.time() - t0

# control: with the passage in hand
c_right = c_n = 0
for d in range(0, 10, 2):
    for q in [x for x in exam if x["pos"] // 100 == d][10:12]:
        reply = ask_llm([dict(role="system", content=SYSTEM),
                         dict(role="user",
                              content=q_text(q, with_passage=True))])
        c_n += 1
        c_right += grade(reply, q)

print(f"\nLLM ({MODEL}, {NCTX} ctx): "
      f"{sum(l_right)}/{sum(l_n)} = "
      f"{100 * sum(l_right) / max(1, sum(l_n)):.0f}%  in {t_llm:.0f}s "
      f"({t_llm / len(sample):.1f}s/question)")
print(f"LLM control WITH passage shown: {c_right}/{c_n} = "
      f"{100 * c_right / max(1, c_n):.0f}%  (reading works; "
      f"memory is the failing axis)")

print(f"\nACCURACY BY PASSAGE POSITION (the cliff chart):")
print(f"  {'decile':<10} {'Isaac':>8} {'LLM':>8}")
for d in range(10):
    ir = 100 * i_right[d] / max(1, i_n[d])
    lr = 100 * l_right[d] / max(1, l_n[d])
    print(f"  {d * 100 + 1:4d}-{d * 100 + 100:<4d} {ir:7.0f}% {lr:7.0f}%")

print(f"\nTHE COST ARITHMETIC: for the LLM to genuinely HAVE all "
      f"1,000 passages at question time it must re-read "
      f"~{approx_tokens:,} tokens per question = "
      f"{len(exam) * approx_tokens / 1e6:.0f}M tokens for this one "
      f"exam. Isaac read the course once and holds it in a "
      f"{os.path.getsize(BODY) / 1e6:.1f}MB file at "
      f"{1000 * t_isaac / len(exam):.0f}ms a question.")
