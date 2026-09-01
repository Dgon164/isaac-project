"""
TALK — the front door. A terminal interface to the real engine.

    python code/talk.py [body_file]

Teach him, ask him, get answers with receipts or refusals with named
reasons. Every reply is stamped with the road that produced it
(recall / reduction / ranked list / generation / built-in decompose /
refusal) plus wall-clock. Autosaves to the body file on quit
(default: data/minds/talk.isaac — untracked, his life stays out of
git).

Commands (anything else is treated as TEACH if it's a statement,
ASK if it ends with '?' or '='):
    ask <words>          answer with road + confidence
    teach <words>        observe one sentence
    read <file>          teach a text file, sentence by sentence
    top <words>          ranked candidates (best to least)
    complete <words>     multi-word completions
    grade good|marginal|bad    grade the last answer
    assess <action>      consequence check (proceed/caution/unknown)
    generate <word>      build a sentence around a concept
    why                  receipt for the last answer
    status | save | quit
"""
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from isaac import Isaac, tokenize  # noqa: E402

DEFAULT_BODY = os.path.join(HERE, "..", "data", "minds", "talk.isaac")


def is_question(toks):
    """A question ends WITH '?' or '='; a statement carries its
    answer ('3 + 4 = 7' teaches, '3 + 4 =' asks)."""
    return bool(toks) and toks[-1] in ("?", "=")


def strangers(m, toks):
    return [t for t in toks
            if t not in m.net.doors and t not in m.net.preds]


def ask(m, toks):
    """Route: reducer for expressions, else recall. Returns
    (answer_text, road, receipt)."""
    toks = [t for t in toks if t != "?"]
    ops = {"+", "*", "-", "/", ">", "<", "and", "or", "xor", "implies"}
    n_ops = sum(1 for t in toks if t in ops)
    if "(" in toks or n_ops >= 1 or (toks and toks[-1] == "="):
        ctx = toks if toks[-1] == "=" else toks + ["="]
        ans, conf, steps = m.evaluate(ctx)
        receipt = [f"{a} {o} {b} -> {r}" for (a, o, b, r) in steps] \
            if steps else []
        if ans is None:
            failed = next((s for s in receipt if s.endswith("None")), None)
            return None, "reduction", receipt + [
                f"refused at: {failed or 'no answerable pair'}"]
        return str(ans), "reduction", receipt
    unk = strangers(m, toks)
    if unk:
        return None, "refusal", [f"never-observed token(s): "
                                 f"{', '.join(unk)} — no honest frame"]
    ans, conf = m.lookup(toks)
    if ans is None:
        return None, "refusal", [
            f"no frame matched with confidence (conf {conf:.2f}) — "
            f"he holds nothing certain for this context"]
    return ans, "recall", [f"confidence {conf:.1f} (frequency, "
                           f"not a certificate)"]


def main():
    body = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BODY
    m = Isaac.load(body) if os.path.exists(body) else Isaac()
    m.wave_logging = False
    st = m.status()
    print(f"ISAAC talk — {st['nodes']} nodes, {st['observations']} "
          f"observations ({'loaded ' + os.path.basename(body)
                           if os.path.exists(body) else 'fresh mind'})")
    print("type a statement to teach, a question to ask; "
          "'quit' saves and exits\n")
    last = {"ctx": None, "answer": None, "receipt": []}
    dirty = False
    while True:
        try:
            line = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            line = "quit"
        if not line:
            continue
        t0 = time.perf_counter()
        cmd, _, rest = line.partition(" ")
        cmd = cmd.lower()
        toks = tokenize(rest) if rest else []

        if cmd == "quit":
            os.makedirs(os.path.dirname(os.path.abspath(body)),
                        exist_ok=True)
            m.save(body)
            print(f"saved -> {body}")
            break
        elif cmd == "status":
            print(m.status())
        elif cmd == "save":
            path = rest or body
            os.makedirs(os.path.dirname(os.path.abspath(path)),
                        exist_ok=True)
            m.save(path)
            print(f"saved -> {path}")
        elif cmd == "read":
            if not os.path.exists(rest):
                print(f"no such file: {rest}")
                continue
            text = open(rest, encoding="utf-8", errors="replace").read()
            n = 0
            for sent in re.split(r"(?<=[.!?])\s+", text):
                ts = tokenize(sent)
                if len(ts) >= 2:
                    m.observe(ts)
                    n += 1
            m.consolidate()
            dirty = False
            print(f"read {n} sentences  [{time.perf_counter()-t0:.1f}s]")
        elif cmd == "teach":
            m.observe(toks)
            dirty = True
            print(f"taught: {' '.join(toks)}")
        elif cmd == "top":
            if dirty:
                m.consolidate()
                dirty = False
            out = m.lookup_topk(toks, k=5)
            print(f"  ranked: {out}   [road: ranked list, "
                  f"{time.perf_counter()-t0:.2f}s]")
        elif cmd == "complete":
            if dirty:
                m.consolidate()
                dirty = False
            out = m.complete_topk(toks, k=3)
            print(f"  completions: {out}   [road: ranked list]")
        elif cmd == "grade":
            g = rest.strip().lower()
            if g not in ("good", "marginal", "bad") or not last["ctx"]:
                print("grade good|marginal|bad (after an answer)")
                continue
            m.feedback(last["ctx"], last["answer"], g)
            print(f"graded {g}: {' '.join(last['ctx'])} -> "
                  f"{last['answer']}")
        elif cmd == "assess":
            a = m.assess(rest)
            print(f"  {a['recommendation']}  (checks: "
                  f"{ {k: round(v[1], 1) for k, v in a['checks'].items()} })"
                  f"   [road: persistence]")
        elif cmd == "generate":
            chain = m.generate(toks[0] if toks else rest)
            print(f"  {' '.join(chain)}   [road: generation — "
                  f"most-traveled doors]")
        elif cmd == "why":
            for ln in last["receipt"] or ["(no answer yet)"]:
                print(f"  {ln}")
        else:
            # no command word: teach statements, answer questions
            toks = tokenize(line)
            if cmd == "ask":
                pass  # toks already set from rest
            if is_question(toks) or cmd == "ask":
                qtoks = tokenize(rest) if cmd == "ask" else toks
                if dirty:
                    m.consolidate()
                    dirty = False
                ans, road, receipt = ask(m, qtoks)
                last = {"ctx": [t for t in qtoks if t != "?"],
                        "answer": ans, "receipt": receipt}
                if ans is None:
                    print(f"  (honest refusal)  [{road}]  "
                          f"{receipt[-1] if receipt else ''}")
                else:
                    print(f"  {ans}   [road: {road}, "
                          f"{time.perf_counter()-t0:.2f}s — "
                          f"'why' for the receipt]")
            else:
                m.observe(toks)
                dirty = True
                print(f"  taught. ({len(toks)} tokens; consolidates "
                      f"before the next answer)")


if __name__ == "__main__":
    main()
