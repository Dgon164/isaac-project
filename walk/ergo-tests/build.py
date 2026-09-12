#!/usr/bin/env python3
"""
build.py -- one store, two readings per item, run through Ergo.

Every item carries:
    truth      -1 / 0 / +1        what Isaac holds about it
    relevance  a graded number, PER CONTEXT

Relevance is not a property of the item on its own. The same fact is
worth a lot in one context and nothing in another, so relevance is
looked up by (item, context).

Nothing combines the two numbers. Relevance sorts and gates. Truth is
carried through untouched.
"""

import sys, subprocess, os

ERGOROOT = "/home/claude/ergoai/ERGOAI_3.0/ErgoAI"
XSBARCH  = "/home/claude/ergoai/ERGOAI_3.0/XSB/config/x86_64-pc-linux-gnu"

# ---------------------------------------------------------------- store
# (node, slot, value, truth)
STORE = [
    ("candidate_a", "years_experience", "eight",     +1),
    ("candidate_a", "certification",    "current",   +1),
    ("candidate_a", "commute",          "far",       +1),
    ("candidate_a", "race",             "stated",    +1),
    ("candidate_a", "religion",         "stated",    +1),
    ("candidate_a", "age",              "fortyone",  +1),
    ("candidate_a", "favorite_colour",  "green",     +1),
    ("candidate_a", "criminal_record",  "none",      +1),
    ("candidate_a", "heart_surgery",    "qualified", -1),
]

# ---------------------------------------------- relevance, per context
RELEVANCE = {
    "hiring_for_technician": {
        "years_experience":  4,
        "certification":     4,
        "criminal_record":   2,
        "commute":           1,
        "favorite_colour":   0,
        "heart_surgery":     0,
        "age":              -2,
        "race":             -4,
        "religion":         -4,
    },
    "staffing_a_surgery": {
        "heart_surgery":     4,
        "certification":     3,
        "years_experience":  2,
        "commute":           1,
        "favorite_colour":   0,
        "criminal_record":   0,
        "age":              -2,
        "race":             -4,
        "religion":         -4,
    },
}

BAND = {4: "required", 3: "relevant", 2: "may matter", 1: "background",
        0: "irrelevant", -2: "harmful", -4: "forbidden"}


def gate(context):
    """Sort by relevance, cut at zero, refuse the negatives."""
    rel = RELEVANCE[context]
    ranked = sorted(STORE, key=lambda it: -rel.get(it[1], 0))
    passed, resting, refused = [], [], []
    for item in ranked:
        r = rel.get(item[1], 0)
        if r > 0:
            passed.append((item, r))
        elif r == 0:
            resting.append((item, r))
        else:
            refused.append((item, r))
    return passed, resting, refused


def atom(s):
    return s if s[0].islower() and all(c.isalnum() or c == "_" for c in s) else "'%s'" % s


def write_ergo(passed, path):
    lines = []
    for (node, slot, value, truth), r in passed:
        head = "%s[%s -> %s]." % (atom(node), atom(slot), atom(value))
        lines.append(head if truth == +1 else "\\neg " + head)
        lines.append("priority(%s, %d)." % (atom(slot), r))
    lines.append("considered(?S) :- priority(?S, ?_).")
    lines.append("top_factor(?S) :- priority(?S, 4).")
    open(path, "w").write("\n".join(lines) + "\n")
    return len(lines)


def run_ergo(path, queries):
    script = "['%s'].\n" % path + "".join(q + "\n" for q in queries) + "\\end\n"
    p = subprocess.run([ERGOROOT + "/runergo"], input=script,
                       capture_output=True, text=True, timeout=400)
    return p.stdout


for context in ("hiring_for_technician", "staffing_a_surgery"):
    print("=" * 62)
    print("CONTEXT:", context)
    passed, resting, refused = gate(context)

    print("\n  sent, in priority order:")
    for (n, s, v, t), r in passed:
        print("     %-2d %-12s %-18s truth %+d" % (r, BAND[r], s, t))
    print("  resting in the store (relevance 0), not sent:")
    for (n, s, v, t), r in resting:
        print("        %-18s truth %+d" % (s, t))
    print("  refused:")
    for (n, s, v, t), r in refused:
        print("     %-2d %-12s %-18s truth %+d" % (r, BAND[r], s, t))

    path = "/home/claude/ctx_%s.ergo" % context
    n = write_ergo(passed, path)
    out = run_ergo(path, ["considered(?S).", "top_factor(?S).",
                          "candidate_a[race -> ?V].",
                          "candidate_a[heart_surgery -> ?V].",
                          "\\neg candidate_a[heart_surgery -> ?V]."])
    print("\n  --- what Ergo answered ---")
    keep = False
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("ergo>") or not line:
            continue
        if line.startswith("Times") or line.startswith("Ciao"):
            continue
        print("     " + line)
    print()
