#!/usr/bin/env python3
"""create.py -- he makes the thing, says what he made, python checks him.

    python walk/create.py                the challenges
    python walk/create.py -show          every attempt in full

The other side of parts.py. A challenge is a spec in the parts
vocabulary: {kind: tuple, count: 1, made_by: parentheses, name: one},
or {kind: function, params: "p, q", returns: yes}, or {tool: len,
output: 3}. He has no model; he has templates -- his lesson examples
and the book examples he verified in school -- and his own locators
tell him where the name, the values, the parameters sit in a template.
So he picks the template closest to the spec and substitutes.

Then he CLAIMS the parts of what he made, and python reads the parts
back (run it / parse it). Two kinds of wrong, marked separately:
    MADE WRONG    truth != spec   (asked for a tuple, made an int)
    MISJUDGED     claim != truth  (made an int, called it a tuple)
A template that fails a spec is set aside and he tries again; the
retry shows whether he can correct himself within the run.
"""
import ast
import io
import json
import os
import random
import re
import sys
import tokenize

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import parts as P

STORE = os.path.join(HERE, "python_store.json")


# ----------------------------------------------------------- his templates
def parts_of(statement):
    """what python says a statement made: a def by ast, anything else by
    running it and looking at the object."""
    s = statement.lstrip()
    if s.startswith(("def ", "async def ")) or re.match(r"\w+ = lambda\b", s):
        t = P.truth_function(statement, "-")
        t["thing"] = "function"
        return t
    t = P.run_tuple(statement)
    t["thing"] = "value"
    t["made_by"] = TUPLE_RULES["made_by"](P.toks(statement), {}) \
        if t["kind"] == "tuple" else "-"
    return t


def templates():
    """his lessons plus every verified single-line assignment from the
    book he read in school (walk/python_store.json)."""
    out = []
    for s, m in P.LESSON:
        out.append(s)
    for s, m in P.FUNC_LESSON:
        out.append(s)
    if os.path.exists(STORE):
        d = json.load(open(STORE, encoding="utf-8"))
        for name, kind, content, truth, native, tag, refs in d["items"]:
            if kind != "sentence" or truth != 1 or not tag.endswith(" example"):
                continue
            src = str(content).split(" -> ")[0]
            if "\n" in src or ">>>" in src or not re.match(r"^\w+ = ", src):
                continue
            try:                       # plain data only: no files, no calls
                ast.literal_eval(src.split("=", 1)[1].strip())
            except Exception:
                continue
            out.append(src)
    seen, uniq = set(), []
    for s in out:
        if s not in seen:
            seen.add(s)
            uniq.append(s)
    return [(s, parts_of(s)) for s in uniq]


# ------------------------------------------------------------- making
def span(tk):
    return tk.start[1], tk.end[1]


def substitute(template, tparts, spec, rng):
    """fill the template with the spec's parts, using his locators for
    where each part sits. returns the statement and his claim."""
    tk = P.toks(template)
    s = template
    claim = dict(tparts)
    edits = []                                   # (start, end, new text)
    if tparts["thing"] == "function":
        new_name = spec.get("name", tparts["name"])
        edits.append((span(tk[1])[0], span(tk[1])[1], new_name))
        claim["name"] = new_name
        if "params" in spec:
            old = [p for p in tparts["params"].split(", ") if p]
            new = [p for p in spec["params"].split(", ") if p]
            if len(old) == len(new):
                for o, n in zip(old, new):
                    s = re.sub(r"\b%s\b" % re.escape(o), n, s)
                claim.update(params=spec["params"], count=str(len(new)),
                             first=new[0] if new else "", last=new[-1] if new else "")
                tk = P.toks(s)
                edits = [(span(tk[1])[0], span(tk[1])[1], new_name)]
        claim["returns"] = tparts["returns"]
    else:
        new_name = spec.get("name", "x")
        edits.append((span(tk[0])[0], span(tk[0])[1], new_name))
        claim["name"] = new_name
        count = int(spec.get("count", tparts["length"] if tparts["length"] != "-" else 0))
        if "values" in spec:
            new = spec["values"].split(", ") if spec["values"] else []
        elif spec.get("of") == "str":
            new = ["'%s'" % w for w in rng.sample(P.WORDS, count)]
        else:
            new = [str(rng.randint(1, 9)) for _ in range(count)]
        lits = []
        seen_eq = False
        for t in tk:
            if seen_eq and t.type in P.LIT:
                lits.append(t)
            if t.string == "=":
                seen_eq = True
        if lits:
            if len(lits) == len(new):
                for t, n in zip(lits, new):
                    edits.append((span(t)[0], span(t)[1], n))
            else:
                edits.append((span(lits[0])[0], span(lits[-1])[1], ", ".join(new)))
        elif new:
            return None, None                   # nothing to put them in
        claim.update(values=", ".join(new), length=str(len(new)),
                     first=new[0] if new else "", last=new[-1] if new else "")
        claim["kind"] = spec.get("kind", tparts["kind"])
        claim["made_by"] = spec.get("made_by", tparts["made_by"])
    for a, b, n in sorted(edits, reverse=True):
        s = s[:a] + n + s[b:]
    return s, claim


def choose(temps, spec, avoid):
    """the template that matches the most of the spec's shape (kind,
    made_by, count / returns), simplest first; not one set aside."""
    best = None
    for s, t in temps:
        if (spec_key(spec), s) in avoid:
            continue
        if spec.get("kind", "tuple" if "made_by" in spec else None) == "function":
            if t["thing"] != "function":
                continue
        elif t["thing"] != "value":
            continue
        score = 0
        for k in ("kind", "made_by", "returns"):
            if k in spec and t.get(k) == spec[k]:
                score += 2
        if "count" in spec:
            have = t.get("length" if t["thing"] == "value" else "count")
            score += 3 if str(have) == str(spec["count"]) else 0
        if "params" in spec and t.get("count") == str(len(spec["params"].split(", "))):
            score += 3
        key = (score, -len(s))
        if best is None or key > best[0]:
            best = (key, s, t)
    return (best[1], best[2]) if best else (None, None)


def spec_key(spec):
    return tuple(sorted((k, str(v)) for k, v in spec.items() if k != "name"))


# ------------------------------------------------------------- checking
def check(statement, claim, spec):
    """python reads the parts back. per part: made right (truth == spec)
    and knew it (claim == truth)."""
    truth = parts_of(statement)
    made_wrong, misjudged = [], []
    for k, v in spec.items():
        if k in ("name", "of", "tool", "output"):
            continue
        tk = {"count": "length" if truth["thing"] == "value" else "count"}.get(k, k)
        if str(truth.get(tk)) != str(v):
            made_wrong.append("%s: asked %s, made %s" % (k, v, truth.get(tk)))
    for k, v in claim.items():
        if k == "thing" or k not in truth or v in ("-", None) or truth[k] == "-":
            continue
        if str(truth[k]) != str(v):
            misjudged.append("%s: said %s, it is %s" % (k, v, truth[k]))
    return truth, made_wrong, misjudged


def his_read(statement):
    """what HE says he made: his own locators on his own statement. this
    is the claim python checks, not the spec he was given."""
    s = statement.lstrip()
    if s.startswith(("def ", "async def ")):
        P.THING.update(P.THINGS["function"]); P.PARTS[:] = P.FUNC_PARTS
        claim = P.read(P.toks(statement), FUNC_RULES)
    else:
        P.THING.update(P.THINGS["tuple"]); P.PARTS[:] = P.TUPLE_PARTS
        claim = P.read(P.toks(statement), TUPLE_RULES)
    return claim


EXTRA = []          # what he misread, added to his lesson as he goes


def relearn(statement, truth):
    """a misjudgment corrects his reading: the statement he misread joins
    his lesson with python's labels, and the rules are learned again."""
    global TUPLE_RULES, FUNC_RULES
    if truth["thing"] == "function":
        EXTRA.append((statement, "-"))
        P.THING.update(P.THINGS["function"]); P.PARTS[:] = P.FUNC_PARTS
        FUNC_RULES, report = P.learn_rules(P.FUNC_LESSON + EXTRA)
    else:
        EXTRA.append((statement, truth["made_by"]))
        P.THING.update(P.THINGS["tuple"]); P.PARTS[:] = P.TUPLE_PARTS
        TUPLE_RULES, report = P.learn_rules(P.LESSON + EXTRA)
    print("       relearned his reading with this example; rules now: " +
          "; ".join("%s = %s (%d/%d)" % (p, n[:50], r, t)
                    for p, n, r, t in report if p == "kind"))


def run_expr(statement, expr):
    g = {}
    try:
        exec(statement, g)
        return repr(eval(expr, g))
    except Exception as e:
        return "error: " + type(e).__name__


# ------------------------------------------------------------- challenges
CHALLENGES = [
    {"kind": "tuple", "count": 3, "name": "t"},
    {"kind": "tuple", "count": 1, "name": "one"},
    {"kind": "tuple", "count": 1, "made_by": "trailing comma", "name": "solo"},
    {"kind": "tuple", "count": 0, "name": "empty"},
    {"kind": "tuple", "count": 2, "made_by": "tuple()", "name": "pair"},
    {"kind": "tuple", "count": 3, "of": "str", "made_by": "commas", "name": "rgb"},
    {"kind": "list", "count": 2, "of": "str", "name": "names"},
    {"kind": "tuple", "values": "4, 5, 6", "name": "abc"},
    {"kind": "function", "params": "p, q", "returns": "yes", "name": "join2"},
    {"kind": "function", "count": 0, "returns": "no", "name": "quiet"},
    {"kind": "function", "params": "word", "returns": "yes", "name": "echo"},
    {"kind": "function", "count": 1, "returns": "no", "name": "say"},
]

OUTPUT_CHALLENGES = [("len", "3"), ("sum", "6"), ("max", "9"), ("len", "0"),
                     ("sorted", "[1, 2, 3]"), ("tuple", "('a', 'b')")]


def attempt_output(tool, want, rng, tries=300):
    """use this tool, get this output: brute force with a check, over
    things he can make."""
    for _ in range(tries):
        count = rng.choice([0, 1, 2, 3, 3])
        if rng.random() < 0.3:
            vals = ["'%s'" % w for w in rng.sample(["a", "b", "c", "d"], count)]
        else:
            vals = [str(rng.randint(0, 9)) for _ in range(count)]
        if rng.random() < 0.3:
            stmt = "t = [%s]" % ", ".join(vals)
        else:
            stmt = "t = (%s%s)" % (", ".join(vals), "," if count == 1 else "")
        expr = "%s(t)" % tool
        got = run_expr(stmt, expr)
        if got == want:
            return stmt, expr, got
    return None, None, None


def main():
    show = "-show" in sys.argv
    rng = random.Random(3)
    global TUPLE_RULES, FUNC_RULES
    P.THING.update(P.THINGS["function"]); P.PARTS[:] = P.FUNC_PARTS
    FUNC_RULES, _ = P.learn_rules(P.FUNC_LESSON)
    P.THING.update(P.THINGS["tuple"]); P.PARTS[:] = P.TUPLE_PARTS
    TUPLE_RULES, _ = P.learn_rules(P.LESSON)
    temps = templates()
    print("his templates: %d (%d from the lessons, the rest verified book "
          "examples)" % (len(temps), len(P.LESSON) + len(P.FUNC_LESSON)))

    avoid = set()
    made_ok = knew_ok = 0
    print("\nTHE CHALLENGES: make it, say what you made, python checks")
    for spec in CHALLENGES:
        want = ", ".join("%s=%s" % kv for kv in spec.items())
        made_wrong = misjudged = ["no attempt"]
        for attempt in (1, 2, 3):
            tpl, tparts = choose(temps, spec, avoid)
            if tpl is None:
                print("  x  %s\n       no template fits" % want)
                break
            stmt, _ = substitute(tpl, tparts, spec, rng)
            if stmt is None:
                avoid.add((spec_key(spec), tpl))
                continue
            claim = his_read(stmt)              # his own reading of it
            truth, made_wrong, misjudged = check(stmt, claim, spec)
            ok = not made_wrong and not misjudged
            mark = "v" if ok else ("~" if not made_wrong else "x")
            print("  %s  %s%s" % (mark, want,
                                 "   (try %d)" % attempt if attempt > 1 else ""))
            print("       made:   %s" % P.one_line(stmt))
            if show or not ok:
                print("       from:   %s" % P.one_line(tpl))
            print("       claims: %s" % ", ".join(
                "%s=%s" % (k, claim[k]) for k in
                (P.TUPLE_PARTS if truth["thing"] == "value" else P.FUNC_PARTS)
                if claim.get(k) not in (None, "-")))
            for m in made_wrong:
                print("       MADE WRONG  %s" % m)
            for m in misjudged:
                print("       MISJUDGED   %s" % m)
            if ok:
                break
            if not made_wrong:                     # made right, read wrong:
                relearn(stmt, truth)               # a lesson for his reading
                break
            avoid.add((spec_key(spec), tpl))       # made wrong: set aside
        made_ok += not made_wrong
        knew_ok += not misjudged
    print("\n  made the right thing on %d / %d, knew what he made on %d / %d"
          % (made_ok, len(CHALLENGES), knew_ok, len(CHALLENGES)))

    print("\nUSE THIS TOOL, GET THIS OUTPUT (brute force over things he can "
          "make, checked by running):")
    for tool, want in OUTPUT_CHALLENGES:
        stmt, expr, got = attempt_output(tool, want, rng)
        if stmt is None:
            print("  x  %s -> %s   no way found" % (tool, want))
        else:
            print("  v  %s -> %s   %s ; %s -> %s" % (tool, want, stmt, expr, got))


if __name__ == "__main__":
    main()
