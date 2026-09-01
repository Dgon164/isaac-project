# THE ARCHITECTURE DECISION MEMO
**2026-08-30. The one-page ruling the record-repair plan (N10) owed, argued from
measurements — every premise has a command and a number. Owner ratifies or vetoes.**

## The premises (all measured)

1. **The prediction table is a text memory.** Same-passage recall 85% sits below the
   100%/99.6% trivial ceilings (W2 EXECUTED); unseen-passage transfer is **26% — at
   the 27% tie-policy floor** against a 91% taught-passage control
   (`cloth_unseen.py`, this commit). It is fast, inspectable, honest about being a
   frequency instrument — and it does not read.
2. **Structure search composes; frequency doesn't.** The S0 road: 0/100 native →
   **100/100 forward + reverse through plain lookup()**, schema cost one encoding
   rule + three operators, now an engine road with the wildcard soundness law
   (`s0_composition_probe.py`, parts court, `a6e8e7f`).
3. **The solver lane works as instrument, not oracle.** Two-tier acceptance +
   independent replay: certified facts enter the facts layer with legs; the
   rule-relativity boundary is red-lettered (trust rides on rule admission);
   unprovable files an ask (`ask_logic_court.py`). Z3 catches disagreeing laws and
   records them as findings (`z3_law_scan.py`).
4. **Honesty is mechanism-narrow and now instrumented.** Refusal was frame-luck at
   the boundary (measured); every refusal now files an ask; falsehood-manufacturing
   paths are closed (`8481cfd`); no test can silently pass (17-row gate, exit-coded,
   mutation-verified).
5. **Scale is no longer the wall.** Column-sparse table: memory wall dead, full gate
   in ~90s; the 1,000-passage run (first past the old coded halt) is in flight and
   its result lands in the ledger either way.

## The ruling

**The spine of capability is the STRUCTURE lane** — the log → facts layer →
composition search → admitted rules → solver instruments — because that is the lane
every positive result came from. **The prediction table is formally retyped as what
it measured itself to be:** a fast text-memory instrument (completion, familiarity,
retention), consulted by the spine, never the spine. **The bridge stays an
instrument** for derivation depth the native search lacks, behind the two-tier gate.
**The W-phase ledger build proceeds next** — not as theory homage but because the
last 24 hours built its exact contents ad hoc (origins, certified facts, asks,
quarantine): the differentiation algebra is the spec that makes that bookkeeping
sound, pending the owner's Def 1.5/1.8 amendment sign-off.

**What this rules OUT, on the evidence:** betting comprehension on the table
(premise 1 kills it); freezing native inference in favor of solvers-only (premise 2
kills it — the native arm won); and treating rule admission as a formality
(premise 3's boundary).

**The open bets it leaves honest:** schema induction under the cost curve (three
domains, pre-committed kill condition), and reading — real transfer will need
structure-lane machinery over text (composition + binder + facts), and no current
number promises it.

*Standing next actions: 1,000-passage ledger entry; W-phase on sign-off; the
manifest row for part 3 re-graded "text-memory instrument (measured)".*
