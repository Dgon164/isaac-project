#!/usr/bin/env python3
"""
emit2.py -- capability flags instead of per-target special cases.

Every item carries two bits saying what a target must support to hold it:

    bit 0  NEG    needs real negation
    bit 1  RULE   needs conditional rules with priority

The bits are DERIVED from the item, not written by hand, so they cannot
drift out of step with what the item actually is.

Value 0 is separate and prior to all of this: it never leaves Isaac at
all, so it is never offered to an emitter.

A target declares which bits it supports. Anything needing a bit the
target lacks is dropped and reported. Adding a target means declaring
two bits and writing the text formatting -- no loss logic per target.
"""

import json
import sys

NEG = 0b01
RULE = 0b10
BITNAME = {NEG: "negation", RULE: "rules"}


def needs(item, kind):
    """Derive the requirement bits. Nothing hand-set."""
    b = 0
    if kind == "slot":
        if item["v"] == -1:
            b |= NEG
    elif kind == "claim":
        b |= RULE
        if item["v"] == -1:
            b |= NEG
    elif kind == "supersession":
        b |= RULE
    elif kind == "comparison_rule":
        b |= RULE
        if item.get("uses_negation"):
            b |= NEG
    return b


def missing_bits(required, supported):
    return [BITNAME[b] for b in (NEG, RULE) if (required & b) and not (supported & b)]


class Target:
    def __init__(self, name, supports):
        self.name = name
        self.supports = supports
        self.lines = []
        self.lost = []

    def offer(self, item, kind, render):
        req = needs(item, kind)
        gap = missing_bits(req, self.supports)
        if gap:
            self.lost.append("%s %s: target has no %s"
                             % (kind, label(item, kind), " or ".join(gap)))
            return False
        self.lines.append(render())
        return True


def label(item, kind):
    if kind == "slot":
        return "%s/%s" % (item["node"], item["slot"])
    if kind == "claim":
        return item["tag"]
    if kind == "supersession":
        return "%s over %s" % tuple(item)
    return item.get("name", "?")


def run(mapfile, targetname):
    m = json.load(open(mapfile))
    t = {
        "ergo":   Target("ergo",   NEG | RULE),
        "prolog": Target("prolog", RULE),          # rules, but no real negation
        "turtle": Target("turtle", 0),             # facts only
    }[targetname]

    def a(s):
        s = str(s)
        return s if s and s[0].islower() and all(c.isalnum() or c == '_' for c in s) \
            else "'%s'" % s

    for sub, sup in m["classes"]:
        t.lines.append({"ergo": "%s :: %s." % (a(sub), a(sup)),
                        "prolog": "sub(%s, %s)." % (a(sub), a(sup)),
                        "turtle": "i:%s rdfs:subClassOf i:%s ." % (sub, sup)}[t.name])

    withheld = 0
    for s in m["slots"]:
        if s["v"] == 0:                 # never offered. Isaac-only, by rule.
            withheld += 1
            continue
        n, sl, v = a(s["node"]), a(s["slot"]), a(s["value"])
        if s["v"] is None:
            t.lines.append({"ergo": "open_axis(%s,%s)." % (n, sl),
                            "prolog": "open_axis(%s, %s)." % (n, sl),
                            "turtle": "i:%s i:openAxis i:%s ." % (s["node"], s["slot"])}[t.name])
            continue
        if s["v"] == 1:
            t.lines.append({"ergo": "%s[%s -> %s]." % (n, sl, v),
                            "prolog": "slot(%s, %s, %s)." % (n, sl, v),
                            "turtle": "i:%s i:%s i:%s ." % (s["node"], s["slot"], s["value"])}[t.name])
        else:
            t.offer(s, "slot", lambda: "\\neg %s[%s -> %s]." % (n, sl, v))

    for c in m["claims"]:
        def render(c=c):
            n, sl, vl = [a(x) for x in c["head"]]
            body = " \\and ".join("%s[%s -> %s]" % tuple(a(x) for x in w) for w in c["when"])
            head = "%s[%s -> %s]" % (n, sl, vl)
            if c["v"] == -1:
                head = "\\neg " + head
            return "@{%s}\n%s :- %s." % (a(c["tag"]), head, body)
        t.offer(c, "claim", render)

    for sup in m["supersessions"]:
        t.offer(sup, "supersession",
                lambda sup=sup: "\\overrides(%s,%s)." % (a(sup[0]), a(sup[1])))

    t.offer({"name": "agree"}, "comparison_rule",
            lambda: "agree(?A,?B,?S) :- ?A[?S -> ?V], ?B[?S -> ?V], ?A \\= ?B.")
    t.offer({"name": "differ", "uses_negation": True}, "comparison_rule",
            lambda: "differ(?A,?B,?S) :- ?A[?S -> ?V], \\neg ?B[?S -> ?V].")

    print("\n".join(t.lines))
    sys.stderr.write("[%s] supports %s | %d lines, %d withheld as 0, %d dropped\n"
                     % (t.name,
                        "+".join(BITNAME[b] for b in (NEG, RULE) if t.supports & b) or "facts only",
                        len(t.lines), withheld, len(t.lost)))
    for l in t.lost:
        sys.stderr.write("    dropped: %s\n" % l)


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2])
