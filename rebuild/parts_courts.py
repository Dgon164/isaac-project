# PARTS COURTS — regression tests for two new engine parts, written
# test-first against the agreed API contract, before the parts land
# in code/isaac.py.
#
# Part 1, FACTS LAYER (log / net / facts kept separate):
#   m.facts                                  list of fact records
#   m.fact_add(pred, args, kind, origin,
#              sources, text) -> id          append a fact, get its id
#   m.facts_query(pred, origin, kind)        filter the fact table
#   m.facts_export(preds)                    ground facts as clingo
#                                            lines, e.g. "sum(3,4,7)."
#   facts persist through save/load (v2 body files).
#
# Part 2, ASK QUEUE (a refusal gets filed as a question, not dropped):
#   m.asks                                   list of question records
#   m.ask_file(tokens, reason, road) -> id   file a question; an
#                                            identical open question
#                                            returns the same id
#   m.asks_open()                            open questions
#   m.ask_resolve(id, answer, road)          mark answered
#   a lookup that refuses (answer None) files a question by itself;
#   a lookup that answers files nothing.
#
# Staging: the engine parts are being built in parallel. If neither
# part exists yet, exit 77 (skip, not fail). If only one exists, test
# that one and print the other as SKIPPED.
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "..", "code"))
from isaac import Isaac, tokenize                       # noqa: E402

# failed check names collect here; summary + exit code at the bottom
FAILS = []


def check(name, ok, detail=""):
    # one printed line per check; a failure records its name
    print(f"  {'ok  ' if ok else 'FAIL'} {name}"
          + (f"  ({detail})" if detail and not ok else ""))
    if not ok:
        FAILS.append(name)


def facts_court():
    print("FACTS COURT")
    m = Isaac()

    # add ground facts: id comes back, record lands in the table
    fid = m.fact_add("sum", [3, 4, 7])
    check("fact-add-returns-id", isinstance(fid, int), f"got {fid!r}")
    fid2 = m.fact_add("edge", ["a", "b"], origin="told")
    m.fact_add("obs", [1, 2], sources=[5, 9], text="one and two")
    # a rule-kind record: stored, but never exported as a ground fact
    m.fact_add("law", ["head"], kind="rule",
               text="sum(A,B,C) :- add(A,B,C).", origin="promoted")

    # query by predicate name
    got = m.facts_query(pred="sum")
    check("query-by-pred",
          len(got) == 1 and got[0]["id"] == fid
          and got[0]["args"] == [3, 4, 7],
          f"got {got!r}")
    # query by origin tag
    got = m.facts_query(origin="told")
    check("query-by-origin",
          len(got) == 1 and got[0]["id"] == fid2, f"got {got!r}")
    # query by kind
    got = m.facts_query(kind="rule")
    check("query-by-kind",
          len(got) == 1 and got[0]["pred"] == "law", f"got {got!r}")

    # export: exactly the ground facts, "pred(a,b,c)." one per line
    exp = m.facts_export()
    lines = sorted(ln.strip() for ln in exp.splitlines() if ln.strip())
    want = sorted(["sum(3,4,7).", "edge(a,b).", "obs(1,2)."])
    check("export-ground-exact", lines == want, f"got {lines!r}")
    check("export-excludes-rule", "law" not in exp, f"got {exp!r}")
    # export filtered to named predicates
    only = m.facts_export(preds=["sum"])
    check("export-preds-filter", only.strip() == "sum(3,4,7).",
          f"got {only!r}")

    # facts survive a save/load round trip: ids, origins, sources intact
    tmpdir = tempfile.mkdtemp(prefix="parts_courts_")
    p = os.path.join(tmpdir, "facts_court.isaac2")
    m.save(p)
    m2 = Isaac.load(p)

    def proj(fs):
        return [(f["id"], f["kind"], f["pred"], list(f["args"]),
                 f["origin"], f["sources"], f["text"]) for f in fs]
    check("facts-survive-save-load",
          hasattr(m2, "facts") and proj(m2.facts) == proj(m.facts),
          f"before {proj(m.facts)!r} after "
          f"{proj(getattr(m2, 'facts', []))!r}")


def asks_court():
    print("ASKS COURT")
    m = Isaac()
    # tiny taught corpus: enough for one answerable question
    for s in ["3 + 4 = 7", "2 + 2 = 4", "5 + 1 = 6", "the sky is blue"]:
        m.observe(tokenize(s))
    m.consolidate()

    # snapshot the raw record: questions are bookkeeping, not
    # observations, so this count must not move below
    n_obs = len(m.observed_sequences)

    # direct filing: id back, duplicate open question -> same id
    q = ["what", "is", "a", "quark"]
    a1 = m.ask_file(q, "test: never taught", road="court")
    a2 = m.ask_file(list(q), "test: never taught", road="court")
    check("ask-file-returns-id", isinstance(a1, int), f"got {a1!r}")
    check("ask-file-dedupe-same-id", a1 == a2, f"{a1!r} vs {a2!r}")
    opens = m.asks_open()
    check("ask-open-listed",
          any(a["id"] == a1 and a["question"] == q
              and a["status"] == "open"
              and a["reason"] == "test: never taught" for a in opens),
          f"got {opens!r}")

    # a refused lookup files a question on its own
    toks = tokenize("zebra + 4 =")
    ans, _ = m.lookup(toks)
    check("unknown-lookup-refuses", ans is None, f"got {ans!r}")
    match = [a for a in m.asks_open() if a["question"] == toks]
    check("refusal-auto-files-ask", len(match) == 1,
          f"{len(match)} matching open asks")
    # the same refused lookup again: still exactly one open question
    m.lookup(toks)
    match = [a for a in m.asks_open() if a["question"] == toks]
    check("refusal-dedupe", len(match) == 1,
          f"{len(match)} matching open asks")

    # a lookup that answers files nothing
    before = len(m.asks)
    ans, _ = m.lookup(tokenize("3 + 4 ="))
    check("known-lookup-answers", ans == "7", f"got {ans!r}")
    check("success-files-nothing", len(m.asks) == before,
          f"{before} -> {len(m.asks)}")

    # resolving flips status and stores the answer
    m.ask_resolve(a1, "a quark is a particle", "told")
    rec = [a for a in m.asks if a["id"] == a1]
    check("resolve-flips-status",
          len(rec) == 1 and rec[0]["status"] == "resolved",
          f"got {rec!r}")
    check("resolve-stores-answer",
          len(rec) == 1 and rec[0]["answer"] == "a quark is a particle",
          f"got {rec!r}")
    check("resolved-leaves-open-list",
          all(a["id"] != a1 for a in m.asks_open()))

    # the raw record did not grow from any of the question traffic
    check("asks-dont-grow-observed", len(m.observed_sequences) == n_obs,
          f"{n_obs} -> {len(m.observed_sequences)}")

    # asks survive a save/load round trip, resolved status included
    tmpdir = tempfile.mkdtemp(prefix="parts_courts_")
    p = os.path.join(tmpdir, "asks_court.isaac2")
    m.save(p)
    m2 = Isaac.load(p)

    def proj(asks):
        return [(a["id"], list(a["question"]), a["status"], a["answer"])
                for a in asks]
    check("asks-survive-save-load",
          hasattr(m2, "asks") and proj(m2.asks) == proj(m.asks),
          f"before {proj(m.asks)!r} after "
          f"{proj(getattr(m2, 'asks', []))!r}")


HAS_FACTS = hasattr(Isaac(), "fact_add")
HAS_ASKS = hasattr(Isaac(), "ask_file")
if not HAS_FACTS and not HAS_ASKS:
    print("SKIP: parts not built yet")
    sys.exit(77)

if HAS_FACTS:
    try:
        facts_court()
    except Exception as e:                              # noqa: BLE001
        # a crash mid-court is a failure, not a silent stop
        print(f"  FAIL facts-court-crash  ({e!r})")
        FAILS.append("facts-court-crash")
else:
    print("FACTS COURT SKIPPED: fact_add not built yet")

if HAS_ASKS:
    try:
        asks_court()
    except Exception as e:                              # noqa: BLE001
        print(f"  FAIL asks-court-crash  ({e!r})")
        FAILS.append("asks-court-crash")
else:
    print("ASKS COURT SKIPPED: ask_file not built yet")

if FAILS:
    print(f"GATE: FAIL ({', '.join(FAILS)})")
else:
    print("GATE: PASS")
sys.exit(1 if FAILS else 0)
