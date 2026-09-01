"""E2b — THE SAME-TEST GAUNTLET (owner protocol, 2026-09-01):
"give a passage, ask the questions, record the answer. every time.
then at the end, do not regive the passages, just reask the
questions."

Both sides take the identical test in the identical order:
  STUDY : passage shown -> its question asked -> answer recorded.
  FINAL : passages NOT reshown -> same questions reasked cold.

Tracked for both, every question: correct?, wall-clock ms; for the
LLM also exact token counts (ollama's own numbers). Every answer
lands in runs/e2b_answers.jsonl — open it and check any row.

Isaac: fresh mind, NO consolidation (measured better without,
2026-09-01). LLM: qwen2.5:1.5b-instruct, stateless calls, temp 0 —
the final phase measures what an API-shaped mind retains between
calls: nothing but its priors. That asymmetry IS the finding.
"""
import json
import os
import re
import sys
import time
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "..", "code"))
_argv = list(sys.argv)
sys.argv = [_argv[0]]        # cloth_run parses argv[1] at import
from isaac import Isaac  # noqa: E402
import cloth_run  # noqa: E402
from glob import glob  # noqa: E402

MODEL = "qwen2.5:1.5b-instruct"
N = 1000
ARM = ("llm" if "llm" in _argv else "isaac") \
    if "--arm" in _argv else "both"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "runs", f"e2b_answers_{ARM}.jsonl")

files = sorted(glob(os.path.join(cloth_run.DATA, "*.json")))
passages = []
for f in files:
    p = cloth_run.load(f)
    if p and p["items"]:
        passages.append(p)
    if len(passages) >= N:
        break
exam = []
for i, p in enumerate(passages):
    for b in p["items"]:
        ctx = [t for t in p["toks"][max(0, b["pos"] - cloth_run.CTX):
                                    b["pos"]] if re.match(r"\w", t)]
        if len(ctx) >= 2:
            exam.append(dict(pos=i, ctx=ctx, options=b["options"],
                             truth=b["truth"]))
            break
print(f"{len(passages)} passages, {len(exam)} questions "
      f"(one per passage); identical order both sides", flush=True)
log = open(OUT, "w", encoding="utf-8")


def record(**kw):
    log.write(json.dumps(kw) + "\n")
    log.flush()


def ask_llm(content, system):
    t0 = time.perf_counter()
    req = urllib.request.Request(
        "http://localhost:11434/api/chat",
        json.dumps(dict(
            model=MODEL, stream=False,
            messages=[dict(role="system", content=system),
                      dict(role="user", content=content)],
            options=dict(temperature=0, num_predict=24))).encode(),
        {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        j = json.loads(r.read())
    return (j["message"]["content"],
            j.get("prompt_eval_count", 0) + j.get("eval_count", 0),
            1000 * (time.perf_counter() - t0))


def grade(reply, q):
    r = reply.strip().lower()
    hits = {o.lower() for o in q["options"] if o.lower() in r}
    return q["truth"] in hits and (
        len(hits) == 1 or r.split()[0].strip('."\',:') == q["truth"])


def qtext(q, with_passage):
    lead = (" ".join(passages[q["pos"]]["toks"]) + "\n\n") \
        if with_passage else ""
    return (f"{lead}Passage {q['pos'] + 1}: the text went "
            f"\"... {' '.join(q['ctx'])} ___\". Which word filled the "
            f"blank? Options: {' / '.join(q['options'])}. "
            f"Reply with just the word.")


SYS = ("You are taking a reading course with a final exam. Answer "
       "each question with just the missing word.")

# ═══ ISAAC takes the course ═══════════════════════════════════════
if ARM == "llm":
    # LLM-only process: run its two phases and stop
    l_study = l_tokens = 0
    t0 = time.time()
    for k, q in enumerate(exam):
        reply, toks, ms = ask_llm(qtext(q, True), SYS)
        ok = grade(reply, q)
        l_study += ok; l_tokens += toks
        record(arm="llm", phase="study", passage=q["pos"] + 1,
               truth=q["truth"], answer=reply.strip()[:60],
               correct=ok, ms=round(ms, 1), tokens=toks)
        if (k + 1) % 100 == 0:
            print(f"  llm study {k + 1}/{len(exam)} "
                  f"[{time.time() - t0:.0f}s]", flush=True)
    print(f"LLM study: {l_study}/{len(exam)} = "
          f"{100 * l_study / len(exam):.0f}%  [{time.time() - t0:.0f}s, "
          f"{l_tokens:,} tokens]", flush=True)
    l_final = l_ftokens = 0
    l_dec = [0] * 10
    t0 = time.time()
    for k, q in enumerate(exam):
        reply, toks, ms = ask_llm(qtext(q, False), SYS)
        ok = grade(reply, q)
        l_final += ok; l_ftokens += toks
        l_dec[min(9, q["pos"] * 10 // len(passages))] += ok
        record(arm="llm", phase="final", passage=q["pos"] + 1,
               truth=q["truth"], answer=reply.strip()[:60],
               correct=ok, ms=round(ms, 1), tokens=toks)
        if (k + 1) % 100 == 0:
            print(f"  llm final {k + 1}/{len(exam)} "
                  f"[{time.time() - t0:.0f}s]", flush=True)
    print(f"LLM final: {l_final}/{len(exam)} = "
          f"{100 * l_final / len(exam):.0f}%  "
          f"[{time.time() - t0:.0f}s, {l_ftokens:,} tokens]")
    print("final by decile: " + " ".join(
        f"{100 * d / (len(exam) // 10):3.0f}" for d in l_dec))
    print(f"LLM total tokens: {l_tokens + l_ftokens:,}")
    log.close()
    sys.exit(0)

m = Isaac()
m.wave_logging = False
i_study = 0
t0 = time.time()
for q in exam:
    for s in cloth_run.sentences(passages[q["pos"]]["toks"]):
        m.observe(s)                                   # the passage
    tq = time.perf_counter()
    confs = [(m.check(q["ctx"], cloth_run.tokenize(o)[0])[1], o)
             for o in q["options"]]
    pick = max(confs)[1]
    ok = pick == q["truth"]
    i_study += ok
    record(arm="isaac", phase="study", passage=q["pos"] + 1,
           truth=q["truth"], answer=pick, correct=ok,
           ms=round(1000 * (time.perf_counter() - tq), 1))
t_i_study = time.time() - t0
print(f"ISAAC study: {i_study}/{len(exam)} = "
      f"{100 * i_study / len(exam):.0f}%  [{t_i_study:.0f}s]",
      flush=True)

i_final = 0
t0 = time.time()
i_dec = [0] * 10
for q in exam:
    tq = time.perf_counter()
    confs = [(m.check(q["ctx"], cloth_run.tokenize(o)[0])[1], o)
             for o in q["options"]]
    pick = max(confs)[1]
    ok = pick == q["truth"]
    i_final += ok
    i_dec[min(9, q["pos"] * 10 // len(passages))] += ok
    record(arm="isaac", phase="final", passage=q["pos"] + 1,
           truth=q["truth"], answer=pick, correct=ok,
           ms=round(1000 * (time.perf_counter() - tq), 1))
t_i_final = time.time() - t0
print(f"ISAAC final: {i_final}/{len(exam)} = "
      f"{100 * i_final / len(exam):.0f}%  [{t_i_final:.0f}s, "
      f"{1000 * t_i_final / len(exam):.0f}ms/q]", flush=True)

if ARM == "isaac":
    print("isaac arm complete (LLM runs in its own process)")
    print("final by decile: " + " ".join(
        f"{100 * d / (len(exam) // 10):3.0f}" for d in i_dec))
    log.close()
    sys.exit(0)

# ═══ THE LLM takes the same course ════════════════════════════════
l_study = l_tokens = 0
t0 = time.time()
for k, q in enumerate(exam):
    reply, toks, ms = ask_llm(qtext(q, True), SYS)
    ok = grade(reply, q)
    l_study += ok
    l_tokens += toks
    record(arm="llm", phase="study", passage=q["pos"] + 1,
           truth=q["truth"], answer=reply.strip()[:60], correct=ok,
           ms=round(ms, 1), tokens=toks)
    if (k + 1) % 100 == 0:
        print(f"  llm study {k + 1}/{len(exam)} "
              f"[{time.time() - t0:.0f}s]", flush=True)
t_l_study = time.time() - t0
print(f"LLM study: {l_study}/{len(exam)} = "
      f"{100 * l_study / len(exam):.0f}%  [{t_l_study:.0f}s, "
      f"{l_tokens:,} tokens]", flush=True)

l_final = l_ftokens = 0
l_dec = [0] * 10
t0 = time.time()
for k, q in enumerate(exam):
    reply, toks, ms = ask_llm(qtext(q, False), SYS)
    ok = grade(reply, q)
    l_final += ok
    l_ftokens += toks
    l_dec[min(9, q["pos"] * 10 // len(passages))] += ok
    record(arm="llm", phase="final", passage=q["pos"] + 1,
           truth=q["truth"], answer=reply.strip()[:60], correct=ok,
           ms=round(ms, 1), tokens=toks)
    if (k + 1) % 100 == 0:
        print(f"  llm final {k + 1}/{len(exam)} "
              f"[{time.time() - t0:.0f}s]", flush=True)
t_l_final = time.time() - t0
log.close()

n = len(exam)
print(f"LLM final: {l_final}/{n} = {100 * l_final / n:.0f}%  "
      f"[{t_l_final:.0f}s, {l_ftokens:,} tokens]")
print(f"\n{'':16s}{'study':>10}{'final':>10}{'study t':>10}"
      f"{'final t':>10}{'ms/q final':>12}")
print(f"{'ISAAC':16s}{100 * i_study / n:>9.0f}%{100 * i_final / n:>9.0f}%"
      f"{t_i_study:>9.0f}s{t_i_final:>9.0f}s"
      f"{1000 * t_i_final / n:>11.0f}")
print(f"{'LLM':16s}{100 * l_study / n:>9.0f}%{100 * l_final / n:>9.0f}%"
      f"{t_l_study:>9.0f}s{t_l_final:>9.0f}s"
      f"{1000 * t_l_final / n:>11.0f}")
print(f"\nfinal-phase accuracy by course position (deciles):")
per = n // 10
print("  isaac: " + " ".join(f"{100 * d / per:3.0f}" for d in i_dec))
print("  llm  : " + " ".join(f"{100 * d / per:3.0f}" for d in l_dec))
print(f"\nefficiency: LLM processed {l_tokens + l_ftokens:,} tokens "
      f"on GPU for its course; Isaac holds the course in "
      f"{len(m.observed_sequences):,} stored sentences on CPU. "
      f"Every answer: runs/e2b_answers.jsonl")
