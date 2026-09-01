# SYMBOLIC SYSTEMS — how they worked, how they failed, what to steal
**2026-08-30. For the owner. Plain language; every system gets: what it was, how it
ran, what it taught us, and the Isaac counterpart.**

---

## 1. The common skeleton

Every classic symbolic system has the same four organs, whatever it called them:

1. **A knowledge base** — facts and rules, stored as symbols (tokens, not numbers).
2. **A working memory** — the current situation: what is known *right now* about the
   problem at hand.
3. **An inference engine** — the loop that matches rules against working memory,
   picks one to fire, fires it (adding or changing facts), and repeats.
4. **A conflict-resolution policy** — when several rules match, which fires? (Most
   recent facts first, most specific rule first, priority numbers...) This little
   policy quietly decided most systems' behavior, and almost nobody tested it.

Isaac's mapping: knowledge base = the net + facts layer; working memory = scratch;
inference engine = the think loop + reducer + (now) the solver bridge; conflict
resolution = the routing order (recall → reduction → logic → refuse) — which we,
unlike them, keep explicit and gate-tested.

## 2. The systems, in the order the lessons arrived

**GPS / means-ends analysis (1957-1969).** Pick a goal, measure the difference
between here and the goal, pick an action that reduces the difference, recurse on the
new gap. *Lesson:* goal-difference-action is the universal planning shape — Isaac's
A→B seek IS this. *Failure:* on real problems the difference measure is the hard
part, and nobody could write it by hand.

**Production systems → XCON (1978-1987).** Thousands of if-then rules; the RETE
algorithm made matching fast by only rechecking what changed (Isaac's delta-compile
is the same idea applied to counting). XCON configured DEC's computers — a genuine
commercial success — until it hit ~10,000 rules and **maintenance collapse**: every
new rule interacted with old ones in untested ways; the update cost ate the profit.
*Lesson:* a rule base without regression tests rots at a rate proportional to its
size. Our answer: the gate, and rules admitted only through courts.

**MYCIN (1972-1980).** Medical diagnosis by backward chaining: start from possible
conclusions, chain back to what evidence would support them, ask for what's missing.
Two immortal contributions: (1) **explanation by trace** — it could answer "WHY?"
by printing the rule chain (this outlived everything else; it is Isaac's receipts);
(2) **certainty factors** — ad-hoc confidence numbers bolted on because probability
felt too hard. The CFs were incoherent: they composed wrong, and nobody could say
what 0.7 MEANT. *Lesson:* uncertainty machinery that isn't grounded in anything
(counts, frequencies, held-out tests) poisons every number downstream. Isaac's
confidences are frequencies and say so on the label. *Also:* MYCIN outperformed
Stanford's own faculty on test cases and was still never deployed — liability,
integration, trust. The deployment gap is a failure mode of its own.

**Semantic networks and frames (1968-1985).** Concepts as nodes, relations as
links, inheritance down the hierarchy ("a robin is a bird, birds fly, so robins
fly") with exceptions ("penguins don't"). Frames added slots with defaults. This is
Isaac's graph, types, and shape organ, almost exactly — the battery's
robin/penguin reasoning section is a frames demo. *Failure:* the links were never
typed rigorously ("is-a" meant six different things in one network), so inference
over long chains silently changed meaning. Our answer: tagged doors, and the ledger
build's origin typing.

**Blackboard systems / HEARSAY-II (1971-1976).** Independent specialists (one knows
phonetics, one knows grammar, one knows the vocabulary) all read and write one
shared workspace — the blackboard — each firing when it recognizes something,
building the answer in layers. *Lesson:* specialists + shared workspace beats one
giant reasoner; that is Isaac's organs + scratch, and it's worth keeping deliberate.
*Failure:* scheduling (whose turn?) became its own unsolvable tuning problem.

**SOAR (1983-today).** Everything is problem-space search; when the system can't
decide what to do next it declares an **impasse**, recursively opens a subproblem
about the impasse, and when the subproblem resolves it **chunks** the solution into
a new rule so the same impasse never recurs. *Lesson — the big one for us:*
**impasse-driven learning.** The system's own stuck-points are its curriculum.
Isaac's ask queue is exactly this: a refusal files an ask; a resolved ask should
leave a reusable road behind (SOAR's chunk = our certified fact/route).

**Cyc (1984-today).** The bet that enough hand-entered common sense (millions of
assertions, ~2,000 person-years) would reach general reasoning. It never did:
ontology engineering cost grew instead of shrinking, the assertions embedded their
authors' framing, and no killer application ever arrived. *Lesson:* hand-coding
does not amortize. This is why Isaac's facts must come from observation and why the
schema-per-domain cost curve has a pre-committed kill condition.

**Prolog and resolution theorem proving (1965-1990s).** Facts and Horn-clause
rules; one inference mechanism (unification + resolution) does everything;
negation-as-failure ("not provable" treated as "false"). Elegant, and the direct
ancestor of our clingo lane. *Failures:* search blows up without hand-placed
guidance (cut operators — hand-coding sneaking back in); negation-as-failure
quietly converts "I don't know" into "no," which is an honesty bug from Isaac's
point of view — our refusal machinery must never let the solver's closed-world
assumption speak in Isaac's open-world voice. **This is a live translation-layer
rule: unprovable ≠ false; unprovable = ask.**

## 3. Watson / DeepQA (2007-2011) — the case study you asked for

Watson is the best-documented hybrid, and its shape is instructive because it WON
while "understanding" almost nothing:

**The pipeline:** (1) *Question analysis* — parse the clue, detect the LAT (lexical
answer type: the word telling you what KIND of thing the answer is — "this city",
"this poet"). (2) *Hypothesis generation* — generate hundreds of candidate answers
from many sources (text search, tables, knowledge bases) with recall prioritized
over precision: wrong candidates are cheap, a missing right one is fatal.
(3) *Evidence scoring* — for each candidate, dozens-to-hundreds of INDEPENDENT
scorers each measure one narrow thing (does the candidate's type match the LAT?
does supporting text align with the clue? geographic plausibility? temporal
plausibility?). No scorer is smart. (4) *Merging and ranking* — a TRAINED model
(logistic regression over all scorer outputs, trained on thousands of past
question-answer pairs) combines the weak evidence into one ranked list with a
calibrated confidence. (5) *The bet* — Watson buzzed only when confidence cleared
a threshold. The confidence machinery, not the reasoning, was the product.

**How it learned with feedback:** not by changing rules — by re-weighting scorers
against a growing answer-key corpus. The symbolic parts (parsers, type systems,
scorers) were hand-built and frozen; the COMBINATION was learned. That division —
hand-built inspectable parts, learned transparent weighting — is a legitimate
pattern for us: Isaac's grade-feedback adjusting rankings over honest scorers is
Watson's shape in miniature.

**Where it failed, famously:** Final Jeopardy, category "U.S. Cities," Watson
answered "Toronto" — the category constraint never made it into the evidence as a
hard filter, only as one soft scorer among hundreds, and the soft vote lost.
*Lesson:* **known hard constraints must be hard gates, not votes.** In Isaac terms:
a taught constraint belongs in the exact-fact gate / solver program, never diluted
into a confidence blend.

**What Watson teaches Isaac, condensed:** many honest weak scorers + transparent
trained combination beats one clever reasoner; calibrated confidence with a
bet/pass threshold IS the product (Isaac's refusal gate is this); recall-first
candidate generation with late verification matches our two-tier bridge; and hard
constraints go in gates.

## 4. The failure-mode checklist (watch for these in Isaac, forever)

1. **Brittleness at the edge** — right inside the tested region, confidently wrong
   one step outside, no graceful degradation. (We measured exactly this: the
   frame-luck boundary. Standing cure: boundary batteries, per-region claims.)
2. **Knowledge-acquisition bottleneck** — hand-coding doesn't amortize (Cyc). Cure:
   observation-only entry; schema cost curve with kill condition.
3. **Maintenance collapse** — untested rule interactions rot the base (XCON). Cure:
   the gate; rules admitted only through courts; supersession not overwrite.
4. **Ungrounded uncertainty** — confidence numbers that mean nothing compose into
   garbage (MYCIN's CFs). Cure: frequencies labeled as frequencies; certificates
   separate from confidences.
5. **Closed-world leakage** — solver says "not provable," system hears "false."
   Cure: unprovable → ask, never → no.
6. **Soft-voting away hard constraints** — Toronto. Cure: constraints are gates.
7. **Combinatorial explosion** — search without guidance dies; guidance by hand
   (Prolog cuts) is the bottleneck returning. Cure: budgeted search, deficit-aimed
   scheduling, honest budget-exhausted refusals.
8. **Symbol grounding gap** — symbols that touch nothing (the barcode seed is our
   answer's first rung).
9. **Demo overclaim** — blocks-world success narrated as general capability
   (SHRDLU's shadow). Cure: the claim discipline; per-region scopes; W-conditions.
10. **The deployment gap** — MYCIN beat the faculty and shipped nowhere. A system
    nobody can run, audit, or trust doesn't exist. Cure: the runnable kit, receipts,
    the front door.
11. **No learning loop** — most systems could only be improved by editing rules by
    hand; feedback never entered the machine. Cure: graded feedback, ask queue,
    impasse→chunk (below).

## 5. How they were tested — and the one habit to keep

Mostly: golden demo cases, hand-checked, no regression culture — which is WHY
maintenance collapse kept surprising everyone. The rule-base verification work that
did exist (consistency/completeness checkers: unreachable rules, contradictory
pairs, missing cases) is worth stealing as a facts-layer court: when the facts
layer grows, run the contradiction scan (our Z3 lane) and the dead-rule scan as
standing gates. Their missing test culture is our strongest inheritance — we
already run it.

## 6. How they learned from feedback — the short honest list

- **SOAR's chunking:** impasse → subproblem → solution cached as a rule. (Ask queue
  → resolved ask → certified reusable road. Build this.)
- **Explanation-based learning:** one worked example + the trace of WHY it worked →
  a general rule from the trace. Isaac's reducer receipts are traces; generalizing
  a receipt into a rule under courts is a future experiment worth naming.
- **Watson's ranker:** frozen honest parts, learned transparent combination.
  (Grade-feedback over roads/scorers — partially built.)
- Everything else: a human edited rules by hand. That absence is what killed the
  era, and the feedback loop (grades, binder, playland) is Isaac's structural
  answer to it.

*Written for the record 2026-08-30; companion to HANDOFF_PROPOSAL_v2 and
DESIGN_PLAYLAND_2026-08-30.md.*
