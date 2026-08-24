# ISAAC — HANDOFF PROPOSAL v2 (the rebuilt document)
**Date:** 2026-08-23. **Supersedes:** `HANDOFF_PROPOSAL_2026-08-23.md` (tag
`handoff-2026-08-23`, commit `ce5df54`) — kept on the record, per standing law.
**Why a v2 exists:** the v1 document invited hostile review and got it
(`TEARDOWN_2026-08-23.md`: 41 agents, 18 skeptic-verified findings, full §8 re-run).
Reproduction held; several headline scopes did not. This version executes the owed
demotions, corrects every claim the teardown confirmed against, and replaces the roadmap
with the judged rebuild plan. **Wrongs are kept in place with their corrections marked
`[DEMOTED]` — a withdrawal condition that fires and is honored is the record working.**

**Claim legend:** [PROVEN-INTERNAL] (mathematics checked by internal adversarial reading;
NOT externally reviewed or machine-checked), [MEASURED] (empirical number with a
reproduction command AND a stated sampled region AND a stated oracle), [SMOKE] (test
asserts existence, not truth — never a headline), [DESIGNED] (specified on paper),
[CONJECTURED] (believed, untested), [OPEN] (named unsolved problem), [DEMOTED] (former
claim, withdrawn by its own condition — kept with the correction).

**Citation rule (standing, adopted after the teardown):** no number is citable unless
produced on a clean checkout of a named commit. Review-time fixes go to a branch, never
the tree under audit.

**Access (owner action required before external circulation):** repo
`github.com/Dgon164/isaac-project` is currently PRIVATE with no license — an external
reviewer cannot take step zero. Required: access-grant procedure or public flip; a
license; the five hardcoded-path harnesses made portable (N1 below); CLOTH fetch URL.

---

## 0. One-page summary (rescoped)

Isaac is a symbolic learning system in one Python file: facts enter by observation of
raw token sequences, live in inspectable structures (a labeled graph and a compiled
count table), and are answered from with confidence gates and refusals. A shipped
product line (anna, separate codebase) applies the same refusal-first design philosophy
to client data.

**What is genuinely demonstrated, with honest scopes:**
- Ingestion and recall: ~50k facts/sec; a fact stated once is retrievable; 1198/1198 on
  the full taught fact list (an ingestion/index check — the test set IS the taught set).
  [MEASURED]
- Retention: ~90% on first-batch material across a 6-batch course. [MEASURED]
- Storage: 49.4MB → 2.9MB (17x, one specimen), item-for-item round-trip verified,
  torn-tail recovery tested. [MEASURED]
- Multi-step reduction with taught pairwise precedence (discriminating control:
  untaught → left-to-right errors, taught → correct) — with a now-declared native
  arithmetic fallback that must be fixed or typed (§4). [MEASURED, mechanism partially
  hand-coded — declared]
- Interoperation: his facts compile out to clingo; an external derivation plan closes a
  measured composition gap (0/100 → 100/100), every accepted answer natively re-derived
  against his store; negative controls committed. [MEASURED — see §3.7 for what this
  does and does not prove]
- The formal theory's exact tier: five core guarantees proven for the Boolean-set model
  and independently re-derived during hostile review. [PROVEN-INTERNAL — Boolean sets;
  count/weight applicability OPEN; two definition amendments required, §5 N9]

**What was withdrawn by the record's own rules:**
- **[DEMOTED] "85% real-exam performance vs 25% chance."** Withdrawal condition W2
  fired: the trivial exact-position baseline scores 100.0% by construction (the taught
  stream contains the answer key), and a 30-line same-inputs text matcher scores 99.6%
  vs the engine's 85.2%. The honest title is: **lossy verbatim recall of taught passages
  under 4-option forced choice, 85% against a ~100% trivial ceiling.** What survives:
  pre-teaching 23-35% → after-teaching 80-92% (ingestion is real), retention ~90%, and
  the July-40%→85% training-bug-fix delta. Comprehension of unseen text: unmeasured —
  the N6 exam decides it.
- **[DEMOTED] "Zero wrong answers; honest refusal at the boundary."** The 200/200
  refusal exam samples only where refusal is structurally guaranteed (both operands
  outside every taught frame); at the actual boundary, confident wrong answers are
  MEASURED (x+0 → "0" 121/121; "zero plus zero → two", T1 writeup: "frame-luck, not
  principle"). Honest form: zero wrong answers ON THE SAMPLED DISTRIBUTIONS; measured
  confident-wrong classes adjacent to them, counted and on the known-bug list.
- **[DEMOTED] "Generation 3/3."** The check was existence-only; a known-false sentence
  ("the grinth eats moss") passed green. Root cause found (alphabetical successor pick,
  `isaac.py:5577`). Generation is [SMOKE] until the truth-oracle check exists and
  passes.

**The proposal:** two weeks of record repair (N1-N10) producing four new decisive
measurements → an architecture decision memo → the typed-ledger build (W-phase) with the
prediction table retyped as its instrument, and the bridge rebuilt on a two-tier
acceptance gate. The bet the program actually stakes its future on is named honestly in
§6: schema induction under a measured cost curve — not toy rule induction.

---

## 1. The concept (unchanged thesis, corrected posture)

The thesis stands: attack the knowledge-acquisition bottleneck (facts by observation,
never hand-entry) and unaccountable brittleness (derivations or refusals, provenance,
wrongs kept) together. The teardown's field review confirms the architecture matches
the pattern that actually produced post-2020 results (formalize → external solver →
verify-before-count; small-trusted-checker discipline). Two honest postures it adds:

1. **Acquisition is currently curriculum-shaped.** Facts enter by observation, but the
   observations are owner-authored generators and curated corpora. Cheaper per fact than
   writing assertions by hand — that is the genuine difference from Cyc — but human
   schema-shaped input, and declared as such.
2. **The hand-coding question moves to the translation layer.** The solver bridge's
   fact export is mechanical; its SCHEMA (predicates, arities, argument order, typing)
   is hand-written. The field's record (Cyc's ontology engineering, NELL's drift,
   OpenIE's canonicalization) says this is where the real problem lives, and post-2020
   systems solved it with large neural translators — forbidden here by standing rule.
   Whether inspectable statistics can induce schemas is this program's actual central
   experiment (§6), and it runs under a cost ledger with a kill condition, not on faith.

**The theory** (differentiation algebra, `3_the_theory/`): Tier 1 [PROVEN-INTERNAL for
Boolean sets] — termination, order-independence, no false positives via provenance,
monotone refinement, forced-exact placeholders; independently re-derived under hostile
review. Tier 2 [DESIGNED — admissibility properties stated; central bounds are
self-declared sketches with undefined constants]. Applicability to the engine's
count/weight data [OPEN — the theory's own named open problem]. Two definition
amendments are REQUIRED before any implementation (§5 N9): the audit/quarantine letter
is circular as written (a minted placeholder balances the audit that minted it —
confirmed by hand; the doc's own P-10 names this failure fatal). The theory's cited
empirical exhibits are off-machine and unrecovered: [CONJECTURED] until the property
suite is rebuilt in-repo (W1). `compare()` implements the D operator but is currently
dead code — the claim "the theory is implemented" is true today only of the numeric-law
module and the findings ledger, which run the full discipline and are the exemplar the
rest generalizes from.

Non-goals unchanged: not an LLM competitor; non-agentic; no neural networks in decision
paths (the dormant in-engine MLP gets deleted or archived, N3).

---

## 2. The document corpus

As v1 §2, plus: `TEARDOWN_2026-08-23.md` (the hostile review this document answers),
`rebuild/cloth_trivial_baseline.py` (the W2-deciding measurement),
`rebuild/bridge_soundness_probe.py` (the verification-boundary measurement), this
document. The v1 handoff stays on the record. Note from the teardown: engine line count
is 7,138; the 85% result gains its missing writeup via N6's exam writeup.

---

## 3. Verified capabilities (every row: number / oracle / sampled region / command)

| # | claim | number | what the test asserts | sampled region | command |
|---|---|---|---|---|---|
| 3.1 | ingestion rate | ~46-58k facts/sec | wall-clock over generated facts | generated tables | `scale_eval.py` |
| 3.1 | recall of taught list | 1198/1198 exact | answer == taught answer | **the taught list itself** (ingestion/index check) | `scale_eval.py` |
| 3.1 | day-zero card | language 3/3 complete, math 6/6, laws 2/2, memory 3/3 | exact match | invented vocab, one pass | `worstcase_baseline.py` |
| 3.1 | generation | [SMOKE — DEMOTED] | output exists & contains subject (truth NOT checked; known-false output measured) | — | `worstcase_baseline.py` |
| 3.2 | refusals | 200/200 refused, 0 wrong | refusal occurred | **both operands >25 only** — outside every taught frame; adjacent regions measured WRONG (x+0: 121/121) | `scale_eval.py` |
| 3.2 | noise refusal | NO RULE on pure noise; 0/40 false discoveries | verdict-checked | discovery module | `worstcase_baseline.py` (v1 miscited scale_eval) |
| 3.3 | multi-step | 200/200 ×3 exams, 16/16 logic, 100/100 refusals | answer == truth; refusal occurred (failing-step naming asserted 0 times — demonstrated once) | operands constructed to keep every pair in-table | `pemdas_eval_test.py` |
| 3.3 | taught precedence | untaught→20 L-to-R errors; taught→correct | discriminating control | pairwise precedence only (parens & routing hard-coded; native fallback declared §4) | `pemdas_eval_test.py` |
| 3.4 | CLOTH | **[DEMOTED]** 85.2% (942-944/1108) | pick == answer key | **taught passages, same-passage 8-token contexts**; trivial ceilings 100.0%/99.6% measured | `cloth_run.py 120` + `cloth_trivial_baseline.py` |
| 3.4 | CLOTH survivors | pre 23-35% → post 80-92%; retention ~90%; July 40%→85% post-fix | before/after deltas | same protocol | same |
| 3.5 | storage v2 | 17.0x (49.4→2.9MB, N=1 specimen), round-trip exact, torn tail survives | item-for-item equivalence + sha256 | one v1 saved state | `onefile_probe.py`, `onefile_install_court.py` |
| 3.5 | journal | [DESIGNED] format passes tests; **zero production call sites** — autosave still full-saves w/ exceptions swallowed | — | — | — |
| 3.6 | selection/feedback | 17/17 | ranked lists, grade effects, persistence | taught micro-corpus; boost constants hard-coded | `selection_feedback_test.py` |
| 3.7 | logic bridge | native 0/100 → derived 100/100, accepted answers natively re-derived 100/100; reverse query works; negative controls REJECT | see §3.7 below | one hand-written rule + hand-written schema, 119 exported facts | `logic_bridge_probe.py` |
| 3.8 | battery | 15/15 areas | mixed oracles; **exit code carries nothing yet** (N2 fixes) | — | `python code/isaac.py` |

**§3.7, stated exactly (the bridge).** What the demo proves: his observed facts
translate to a solver's language through a hand-written schema; clingo, given one
hand-written rule, produces a derivation PLAN whose every step his own store re-derives
natively — external inference as a query planner over his facts, with acceptance gated
on native re-derivation. What it does not prove: soundness of leg-checking in general
(measured: a deliberately broken rule grounds 1800 false conclusions and **1800/1800
pass bare leg-existence; 0/1800 pass the re-derivation join** —
`bridge_soundness_probe.py`); inference beyond what the store could already re-derive
(the reverse query, the one thing his table cannot do, ships unverified); and the 0/100
native control measures the never-taught token "plus" (vocabulary absence), not
inference difficulty. The rebuilt acceptance gate (N9/W3) is two-tier: **CERTIFIED**
(head natively re-derived via a check auto-generated from the solver's grounded proof
trace — the only tier that may enter memory) and **SOLVER-DERIVED** (proof-trace legs
check, head not re-derivable — reported with the rule named, never memorized; trusted
only once the RULE passes held-out validation, the numeric-law module's discipline).
The dropped-join rule is a permanent planted must-reject control.

---

## 4. Measured defects (the full list — expanded by the teardown)

1. **Instruments:** zero assert/nonzero-exit paths in every harness and the battery —
   green is stdout prose. (N2)
2. **Generation:** alphabetical successor pick (`isaac.py:5577`) produces fluent false
   statements; the day-zero check couldn't see it. (N3)
3. **Boundary honesty:** refusal is frame-miss + confidence gate; no range concept;
   confident wrong answers measured at x+0 (121/121) and in-vocabulary untaught
   combinations (T1: "frame-luck, not principle" — MEASURED, not predicted). (N4)
4. **Reducer fallback:** on exact-fact-gate miss, digit arithmetic computes natively and
   cannot refuse; the subtraction placeholder returns a+|b| for untaught pairs **and
   memorizes it as a learned fact** (`isaac.py:6060/6262/6083-6084`); `logic_eval`
   carries a second live hard-coded precedence table. (N3)
5. **Store hygiene:** feedback "good" writes the graded pair into the raw observation
   log unlabeled (`isaac.py:5310-5312`); `remove_door()` deletes edges against the
   add-only law; no origin typing anywhere outside the findings ledger. (W2)
6. **Guard gaps:** the unknown-token confabulation guard exists on `lookup()` only;
   `check()` (the CLOTH path) and `predict_next()` lack it. (N3)
7. **Scale wall, quantified:** dense W + W_norm, every sentence prefix a column; 120
   passages = 210M cells = 84% of the harness's own coded halt (250M,
   `cloth_run.py:30,126`); 1,000 passages ≈ 33-49GB on a 48GB machine. The sparse
   pair-count store (`isaac.py:808`) is the natural canonical form. All curriculum
   scale-up is **blocked on this**. (W4)
8. **Selection/indication (the sharpest known defect):** July measured retrieval 90% vs
   selection 15% — knowledge held but unreachable from the question's shape. Numbers
   are compile-bug-contaminated both directions; must be re-measured post-fix. No prior
   roadmap item owned it. (N7)
9. **Type groups cannot overlap** (unchanged from v1). Feedback grades don't generalize
   (unchanged). Consolidation superlinear (measured again this session: per-batch 6→27→
   74→132→209→311s). (W4)
10. **Theory letter:** the audit/quarantine circularity and the mint-presence ambiguity
    (amendments required before R2-class code). The off-machine exhibits unrecovered.
    (N9, W1)
11. **Kit portability:** 5 of 8 harnesses hardcode `C:\Users\jtwee` paths; repo private,
    no license; CLOTH untracked with no direct URL. (N1)
12. **Dead/foreign code:** `compare()` dead; in-engine MLP violates the no-neural-net
    rule for the decision-path file; line count 7,138 not ~7,800. (N3)

---

## 5. The plan — phase N: two weeks of record repair (judged winner, 2 judges of 2)

*Every step ends in a writeup with reproduction commands. Steps N1-N5 alone already make
the record citable; a pre-committed cut line after N6 still yields a shippable document.*

- **N1. Freeze, portability, access.** Clean-checkout citation rule adopted; five
  harnesses converted to relative imports (pattern `cloth_run.py` already uses);
  portable temp dirs; access block drafted (owner: repo visibility + license decision);
  CLOTH fetch documented + small in-repo sample. *Accept: all 8 rows green from a fresh
  clone in a different directory; new tag.*
- **N2. Assert conversion.** All harnesses + battery assert-and-exit; runner aggregates;
  green = exit 0. *Accept (mutation-tested): one planted wrong expectation per harness →
  8/8 exit nonzero; unmodified suite exits 0; both runs recorded with commit hashes.*
- **N3. Oracle & falsehood-path repair.** Generation asserts truth (grinth goes RED
  until the alphabetical-pick bug is fixed); wrong-at-low-confidence stops counting as
  honest; per-item assertion of named failing steps; reducer fallback refuses or becomes
  a declared typed built-in; subtraction placeholder fixed; duplicate precedence table
  reconciled or retired; `check()`/`predict_next()` get the stranger guard; MLP and
  `compare_nodes` dead code removed or archived. *Accept: no green line can coexist with
  a known-false output (mutation-verified); battery 15/15 still green, now exit-coded.*
- **N4. Boundary honesty battery.** Sampling AT the edge: x+0/x+1, mixed-range (3+30),
  the 20-25 band, in-vocabulary untaught combinations. Wrong answers published as
  wrong, per-region. *Accept: §0's honesty claim carries exact adjacent-wrong counts;
  frame-luck row cites T1 as MEASURED.*
- **N5. W2 execution (done in this document; harness-ize it).** The two baselines run as
  first-class exit-coded harnesses beside `cloth_run.py`; "vs 25% chance" deleted
  everywhere including the harness banner. *Accept: baselines in the same table as the
  engine number; W2 marked EXECUTED.*
- **N6. Unseen-passage exam + variance.** ≥30 never-taught CLOTH passages, same
  protocol, interpretation pre-declared BEFORE the run (≈trivial-baseline → the
  statistical layer is a text memory; above it → transfer, quantified). Every headline
  suite re-run ≥5x across hash seeds; medians and spreads published; the intermittent
  unhashable-set crash reproduced-or-documented. *Accept: the number publishes whichever
  way it lands; "N=1, variance unmeasured" disappears.*
- **N7. Selection re-measure + the native probe.** The retrieval-vs-selection pair
  re-measured on the fixed engine; the S0 bidirectional graph search run as a
  `rebuild/` probe (Arm A of the composition experiment) on T1's held-out word-math
  set. *Accept: both numbers published; pre-declared kill condition: selection stuck
  near old level while retrieval ~90% → the answering road is the bottleneck; R5
  curriculum marked blocked on it.*
- **N8. First comparator.** Same-training n-gram + one local LLM (mistral 7B via
  ollama) on the CLOTH protocol and the boundary battery; six-axis scorecard
  (correct/honest/sample-efficient/retentive/inspectable/correctable); no superiority
  claims; the SOAR mention corrected to what the arena charter actually says. *Accept:
  comparator column beside engine numbers for ≥2 task families; §7.4 retired by
  measurement.*
- **N9. Paper repairs to both architecture bets (no code).** Theory amendments (Def 1.8
  subtracts observed/derived atomics only; Def 1.5 pool-wide presence with
  auto-discharge) + the two new property tests, hand-worked counterexample in a
  committed appendix, owner sign-off (his mathematics); bridge two-tier acceptance spec
  committed with the planted broken-rule control; R1 recast as the two-arm composition
  experiment (teach-k-positives design; machine-generated ILP search bias measured by
  diff; schema induction a NAMED item with the cost ledger); roadmap resequenced (sparse
  rework precedes all curriculum scale). *Accept: all four documents committed; zero
  implementation code in this window.*
- **N10. The architecture decision memo.** One page: theory-spine vs bridge-lean,
  argued from N4/N6/N7/N8 as premises. *Accept: each premise names its measurement; memo
  + this document + run ledger in one tagged commit.*

## Phase W (after the memo; the judged runner-up, informed by it)

- **W1. The Tier-1 property suite, in-repo, as the permanent gate** — rebuilt from the
  amended spec (the lost 08-06 exhibits stay [CONJECTURED]); ≥500 random families x3
  shuffled strategies; termination/confluence/soundness/atoms=cells/conservation/audit
  closure/forced-exact placeholders + the two new posit-audit properties; mutation-tested.
- **W2. Origin typing on the live stores** — observed/derived/approved tags on sequences
  and edges (feedback fix lands here); `remove_door` becomes named supersession; lineage
  query API; storage tests round-trip the tags. Architecture-neutral; first engine
  change after the memo regardless of direction.
- **W3. The typed-ledger working space** beside the engine (strangler pattern, battery
  green at every cutover): entries with origin + provenance; collision loop; audits;
  placeholder mint/discharge/quarantine per amended spec; Boolean + count valuations;
  count-atom canonicity stays [OPEN]. The bridge's CERTIFIED tier starts consuming
  ledger certificates.
- **W4. The prediction table retyped as instrument** — sparse pair-counts canonical;
  dense W/W_norm a budget-declared compiled view excluded from save(); every answer
  carries a typed source record; every refusal mints a queryable deficit record instead
  of evaporating; the 250M-cell budget stated in code. Answer-equivalence across the
  full suite pre/post. This closes the scale wall and unblocks curriculum.
- **W5. The composition experiment, both arms** (from N9's protocol), judged by ledger
  certificates; then bridge expansion (`ask_logic`, Z3 law-consistency scan) behind the
  two-tier gate; the schema-cost curve begins its ledger with domain #2. "Budget
  exhausted" becomes a typed refusal class distinct from no-derivation, with per-stage
  wall-clock printed (standing rule).

**Kill conditions on the program's real bets:** schema induction — if the marginal
hand-written-schema cost per new domain does not fall across three domains, the
translation lane is Cyc-shaped and gets demoted to instrumentation [pre-committed];
selection — N7's condition as stated; theory-at-scale — W1 suite failure on any amended
theorem is a stop-the-line event (the theory's own K-conditions apply).

---

## 6. What this program now honestly claims to be

An acquisition-and-bookkeeping engine with receipts, whose statistical recall layer is
fast, inspectable, and lossy; whose honesty today is mechanism-narrow (guards + gates,
strong exactly where tested); whose formal theory is real mathematics not yet governing
the main path; and whose solver bridge is a working query-planner pattern with the two
genuinely hard experiments — schema induction under a cost curve, and composition-gap
closure by any owner-free mechanism — named, scheduled, and equipped with kill
conditions. The product identity (refusals, provenance, wrongs-kept) survived hostile
review; the capability headlines did not, and this document says so plainly.

## 7. Threats to validity (carried forward + new)

7.1-7.8 of v1 remain (with 7.1 now RESOLVED by measurement against it — the strongest
possible form of the concession). New: **7.9** the review instruments themselves were
AI-built like the code (mitigated: mutation-tested asserts, planted controls, the
clean-checkout rule); **7.10** survivorship — red runs before this record's green ones
were not systematically kept; the run ledger (N2+) fixes this going forward; **7.11**
single-machine, still (unchanged).

## 8. Verification kit contract (post-N2)

`python rebuild/run_gates.py` from a fresh clone: exit 0 = the record's claims hold on
your machine; any nonzero exit names its row. Until N2 lands, the v1 table + eyeball
protocol applies, with today's re-run results in `TEARDOWN_2026-08-23.md §1`. New
measurement commands: `cloth_trivial_baseline.py`, `bridge_soundness_probe.py`.

## 9. Withdrawal conditions

- **W2 — EXECUTED 2026-08-23.** Trivial baseline 100.0%/99.6% ≥ engine 85.2%: "teaching
  works" demoted to "context matching works" throughout this document. Retention and
  ingestion claims stand independently, as the condition specified.
- **W1** (§8 reproduction) — unchanged; now targets the N1 tag.
- **W3 — REPLACED** by the symmetric two-arm rule: Arm-B (induction) success on the toy
  alone decides nothing; both arms failing on the held-out composition set under fair
  budgets withdraws the "evolvable into a modern symbolic system" claim; either arm
  succeeding names the winning mechanism and the roadmap follows it.
- **W4** (order-dependence in the ledger) — unchanged, now with the two new posit-audit
  properties included.
- **W5 — REWRITTEN rule-relative:** an answer enters memory only via a CERTIFIED
  native re-derivation from a solver proof trace; any SOLVER-DERIVED conclusion found
  memorized voids the bridge's honesty claim.
- **W6 (new):** N7's selection kill condition, verbatim.
- **W7 (new):** any green line coexisting with a known-false output voids that line's
  entire suite until the oracle is repaired (mutation-test required to re-admit).

## Appendix — run ledger, 2026-08-23 (this session, commit ce5df54, dirty→clean noted)

battery 15/15 · worstcase green (generation SMOKE; grinth false-blend reproduced) ·
scale_eval 1198/1198 + 200/200 + 100/100 · pemdas 200/200×3 + 16/16 + 100/100 ·
selection 17/17 · bridge 0/100→100/100, re-derived 100/100 · storage 17.0x ALL GREEN ·
CLOTH 942/1108 = 85% (committed run: 944/1108) · trivial baselines 100.0% / 99.6% /
90.7% · broken-rule probe: leg-existence passes 1800/1800 false conclusions, join passes
0 · x+0 boundary probe: 121/121 confident wrong · morning fast-suite runs predate
ce5df54 (dirty-tree caveat, disclosed; the citation rule exists because of it).

*Prepared 2026-08-23 from the teardown record. Companion: `TEARDOWN_2026-08-23.md`
(findings, verdicts, and evidence, all file:line-cited). The v1 document remains in the
repo unedited — supersession, never overwrite.*
