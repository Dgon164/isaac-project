#!/usr/bin/env python3
"""wordtypes.py -- does he know what a noun is? told, and discovered.

    python walk/wordtypes.py                 build his word types, measure both

TOLD        WordNet on disk carries a part of speech for every entry.
            He reads it once into walk/wordtypes.json: word -> its kinds
            (noun, verb, adjective, adverb). Measured: how much of what he
            reads (squad sentences, squad questions, the word problems) he
            can now type, and how many words carry more than one type.
DISCOVERED  from his own store, no reference: a word's company is the
            function words around it (the, a, of, is, was, to ...). Words
            with the same company are grouped. Then the groups are checked
            against WordNet: does the group of words that follow "the" and
            precede "of" turn out to be nouns? That is whether he can find
            the noun on his own.
"""
import json
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "engine"))
from linker import STOP

WORDNET = os.environ.get(
    "ISAAC_DICT",
    r"C:\Users\jtwee\Downloads\New folder (3)\intellon\wordnet_full.json")
SQUAD = os.environ.get(
    "ISAAC_SQUAD",
    r"C:\Users\jtwee\Downloads\New folder (3)\intellon\train-v2.0.json")
TYPESFILE = os.path.join(HERE, "wordtypes.json")
SHORT = {"noun": "n", "verb": "v", "adjective": "a", "adverb": "r"}


def build():
    if os.path.exists(TYPESFILE):
        return json.load(open(TYPESFILE, encoding="utf-8"))
    types = defaultdict(set)
    for e in json.load(open(WORDNET, encoding="utf-8")):
        w = e["word"].lower().replace("-", "_")
        types[w].add(SHORT.get(e["pos"], e["pos"][:1]))
    out = {w: "".join(sorted(t)) for w, t in types.items()}
    json.dump(out, open(TYPESFILE, "w", encoding="utf-8"))
    return out


def words(text):
    import re
    return re.findall(r"[a-z][a-z0-9_\-]*", text.lower().replace("-", "_"))


def main():
    types = build()
    print("TOLD: %d words with a type from wordnet (walk/wordtypes.json)" % len(types))
    dist = Counter(types.values())
    print("  one type: %d   more than one: %d   e.g. %s" % (
        sum(v for k, v in dist.items() if len(k) == 1),
        sum(v for k, v in dist.items() if len(k) > 1),
        ", ".join("%s=%s" % kv for kv in dist.most_common(6))))

    data = json.load(open(SQUAD, encoding="utf-8"))["data"]
    sents = [p["context"] for art in data[:60] for p in art["paragraphs"]]
    qs = [qa["question"] for art in data[:60] for p in art["paragraphs"] for qa in p["qas"]]
    for label, texts in (("squad sentences", sents), ("squad questions", qs)):
        toks = [w for t in texts for w in words(t) if w not in STOP and len(w) >= 3]
        known = sum(1 for w in toks if w in types)
        print("  %-16s %6d content words, %5.1f%% typed; of those %4.1f%% ambiguous"
              % (label, len(toks), 100.0 * known / len(toks),
                 100.0 * sum(1 for w in toks if w in types and len(types[w]) > 1) / max(known, 1)))
    from problems import FORMS
    ptoks = [w for forms, _ in FORMS.values() for f in forms for w in words(f)
             if w not in STOP and len(w) >= 3 and not w.startswith("{")]
    print("  %-16s %6d content words, %5.1f%% typed" % (
        "word problems", len(ptoks), 100.0 * sum(1 for w in ptoks if w in types) / len(ptoks)))

    # ---------------------------------------------------------- discovered
    print("\nDISCOVERED: words grouped by the function words around them, in "
          "%d squad paragraphs, then checked against wordnet" % len(sents))
    company = defaultdict(Counter)
    for t in sents:
        ws = words(t)
        for i, w in enumerate(ws):
            if w in STOP or len(w) < 3:
                continue
            left = ws[i - 1] if i > 0 and ws[i - 1] in STOP else "_"
            right = ws[i + 1] if i + 1 < len(ws) and ws[i + 1] in STOP else "_"
            company[w][(left, right)] += 1
    # a word's main company: its most frequent (left, right) frame
    groups = defaultdict(list)
    for w, frames in company.items():
        if sum(frames.values()) < 3:
            continue
        groups[frames.most_common(1)[0][0]].append(w)
    print("  %d frames with words; the biggest, and what wordnet says the words in each are:" % len(groups))
    rows = []
    for frame, ws in groups.items():
        if len(ws) < 25:
            continue
        typed = [types[w] for w in ws if w in types]
        if not typed:
            continue
        c = Counter(t[0] if len(t) == 1 else "multi" for t in typed)
        top, cnt = c.most_common(1)[0]
        rows.append((len(ws), frame, top, 100.0 * cnt / len(typed), 100.0 * len(typed) / len(ws),
                     ", ".join(ws[:6])))
    for n, frame, top, pur, cov, ex in sorted(rows, reverse=True)[:14]:
        print("  %5d words  %-16s -> mostly %-9s %3.0f%% of the typed (%.0f%% typed)   %s"
              % (n, "%s _ %s" % frame, top, pur, cov, ex))
    # the noun, discovered: pool the frames whose majority is noun; how pure?
    noun_frames = [f for n, f, top, pur, cov, ex in rows if top == "n" and pur >= 60]
    pooled = [w for f in noun_frames for w in groups[f]]
    typed = [types[w] for w in pooled if w in types]
    pure = sum(1 for t in typed if t == "n")
    print("\n  HIS NOUN: %d words from %d frames; wordnet agrees on %d of the %d it knows (%.0f%%); "
          "%d it does not know at all (names, mostly)"
          % (len(pooled), len(noun_frames), pure, len(typed), 100.0 * pure / max(len(typed), 1),
             len(pooled) - len(typed)))
    verb_frames = [f for n, f, top, pur, cov, ex in rows if top == "v" and pur >= 50]
    pooled = [w for f in verb_frames for w in groups[f]]
    typed = [types[w] for w in pooled if w in types]
    pure = sum(1 for t in typed if t == "v")
    print("  HIS VERB: %d words from %d frames; wordnet agrees on %d of the %d it knows (%.0f%%)"
          % (len(pooled), len(verb_frames), pure, len(typed), 100.0 * pure / max(len(typed), 1)))


if __name__ == "__main__":
    main()
