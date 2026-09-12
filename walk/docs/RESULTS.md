# Isaac to Ergo — first build and test

Ergo 3.0 was downloaded, compiled and run. A small Isaac-shaped map was written
by hand, put through a transcriber, and loaded into Ergo. Every test below was
actually run, not reasoned about.

## What was built

| File | What it is |
|---|---|
| `isaac_map.json` | A stand-in for Isaac's output net. 7 class links, 15 slot entries, 2 competing claims, 1 supersession, 1 structure comparison. Uses all four values. |
| `transcribe.py` | Reads the map, writes an Ergo knowledge base plus two side records. |
| `map.ergo` | The generated knowledge base. |
| `withheld.tsv` | Addresses that carried value 0 and were not sent. |
| `open_axes.tsv` | Slots that carried null — the axis exists, nobody has assessed it. |
| `queries.txt` | The test queries. |

## How each value came out

| Isaac value | Written as | Result in Ergo |
|---|---|---|
| 1 | `node[slot -> value].` | asserted, answers Yes |
| −1 | `\neg node[slot -> value].` | asserted as a negative, answers Yes to the negative query and No to the positive one |
| 0 | not written at all, address logged | invisible to Ergo, present in `withheld.tsv` |
| null | not written as a value; an `open_axis(node,slot)` marker is written | no answer either way, but the open question is listed |

## Test results

**Supersession.** Two tagged claims, both saying something about nylon in a hot
section — an early positive from pass 1, a later negative from pass 3. One line
of `\overrides(later_read, early_read)`.

    \neg nylon[suitable_for -> hot_section].   ->  Yes
         nylon[suitable_for -> hot_section].   ->  No

Both rules stayed in the file. The loser was not deleted, it was outranked. The
tags and the reason for each are still queryable:

    basis(?Tag,?Why).
      early_read = pass_1 shallow match on availability
      later_read = pass_3 creep under sustained load disqualifies

That is your competitive supersession with retained keys, working, in about
five lines of generated text.

**−1 and null stayed apart.** This was the one I most wanted to check.

    \neg nylon[conducts_heat -> high].   ->  Yes    (known negative)
    \naf nylon[conducts_heat -> high].   ->  Yes    (also not positively provable)
         steel[catlike -> ?X].           ->  No     (never assessed)
    \neg steel[catlike -> ?X].           ->  No     (also no negative)

A known negative answers Yes to the negative query. An unassessed axis answers
No to both. They do not collapse into each other.

**0 stayed invisible, as intended.**

    steel[supplier_code -> ?X].   ->  No

Nothing leaked. And the difference from null is visible from outside: null left
an `open_axis` marker, 0 left nothing in Ergo and a line in `withheld.tsv`.

    open_axis(?N,?S).
      bonded_joint / cure_time
      nylon / fatigue_limit
      steel / catlike

**Structure comparison.** Bolted joint against bonded joint, on two slots:

    agree(bolted_joint, bonded_joint, ?S).   ->  transfers_force
    differ(bolted_joint, bonded_joint, ?S).  ->  reversible

Overlap and non-overlap fell out of two three-line rules. The 0 and null cases
never entered the comparison, which is the behaviour you wanted.

**Class structure.** Subclass links are transitive without being told:
`steel :: material` answers Yes although only `steel :: metal` and
`metal :: material` were written.

## What went wrong, and what I'd suggest

One test failed. I wrote every Isaac node as a subclass (`::`), so the
instance-of query `steel : material` answered No. Ergo separates "is a kind of"
from "is one of these" and I collapsed them.

This is a modelling decision the transcriber has to make and I made it without
asking. Isaac nodes are not all the same kind of thing — some are categories
(metal), some are particular items (this bolt, lot 88). Suggestion: carry a flag
per node in the map saying category or instance, and let the transcriber pick
`::` or `:` from it. If Isaac doesn't currently mark that distinction, then the
honest first move is to emit everything as `::` and see how far it gets before
it hurts — which is roughly what just happened.

Timing note: loading the argumentation theory took about 16 seconds. That is a
one-time cost when the knowledge base is loaded, not per query. Queries came
back in under 5 milliseconds.

## To run it again

    sh ergoAI_3.0.run              # from the ErgoAI releases page
    python3 transcribe.py isaac_map.json map.ergo withheld.tsv open_axes.tsv
    <install>/ErgoAI/runergo < queries.txt

## Open questions this raised

1. Category vs instance, above.
2. Slot values here are single. Isaac holds several representations of the same
   concept at once. F-logic has multi-valued slots (`->>`) — untested.
3. Nothing here tested the return path. Ergo's answers have not been fed back
   into Isaac yet.
4. Confidence and tolerance were left out entirely. They would ride as extra
   slots, not as truth values, but that is still an assumption.
