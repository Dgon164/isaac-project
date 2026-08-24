# ISAAC — HANDOFF PROPOSAL
**Version under review:** the commit tagged **`handoff-2026-08-23`** in repo
`isaac-project` (engine version string: v0.1.2-alpha1). Run the §8 verification kit at
that tag or later — five of its eight test files postdate the older `v0.1.2-alpha1` tag.
**Date:** 2026-08-23
**Audience:** external technical reviewers. This document expects hostile review, and was
itself adversarially reviewed before circulation (four independent review passes:
overclaim hunting, kit reproduction by a fresh agent, hostile-skeptic attack, cold-read;
51 findings; all incorporated or conceded below).
**Claim discipline:** every claim is typed **[PROVEN-INTERNAL]** (mathematical proof,
authored and twice self-prosecuted by the project, NOT yet externally reviewed or
machine-checked — mechanization is scheduled), **[MEASURED]** (empirical number with a
§8 reproduction command, measured 2026-08-19..23 except where marked historical),
**[BUILT]** (code exists and is exercised by a cited test), **[DESIGNED]** (specified on
paper, not built), or **[CONJECTURED]** (believed, untested). Anything not reproducible
on request should be treated as false.

Vocabulary note: "mind" below means the engine's saved-state file. "Provenance records"
(the project calls them receipts) means per-claim audit trails. Test banners like
"ALL COURTS GREEN" are literal program output strings from an earlier naming convention;
document prose uses standard vocabulary.

---

## 0. One-page summary

Isaac is a symbolic learning system ("classic symbolic AI with the hand-coding removed")
built in one Python file plus test harnesses. He learns facts from raw token sequences,
stores them in two fully inspectable structures (a labeled graph and a compiled
prediction table), and — on the paths built this month — answers with worked derivations
or refuses honestly, naming the failing step. As of this week his learned facts compile
out to an actively maintained logic engine (clingo; Z3 is installed with integration
designed, not built), under a discipline where every external derivation is checked
step-by-step against his own store before it counts — and the checker is demonstrated to
reject planted wrong answers, not just accept right ones.

What is genuinely demonstrated [MEASURED]: zero wrong answers to questions across the
current closed-domain test suites, with honest refusal at every tested boundary;
real-exam learning (85% on 1,108 real cloze questions vs 25% chance, plain unmodified
teaching, retention ~90% across the course); a storage format with item-for-item
round-trip verification; multi-step solving with taught (not hard-coded) order of
operations; and the export/derive/verify solver bridge with working negative controls.

What is NOT demonstrated, stated before any reviewer finds it: **learned inference
rules** — the bridge demo's rule AND its translation schemas were hand-written; the demo
proves the verification discipline and the interoperation, not learning-to-logic
(§3.7, §5-R1). **Reading comprehension** — the exam protocol tests taught passages,
not unseen text (§7.1). **Answer derivations on the main path** — the prediction table's
answers carry a frequency confidence, not a certificate; worked derivations exist today
only on the expression-solver and numeric-law paths (§4.1). **Honesty on tasks he finds
hard** — honesty and difficulty have not yet been co-measured (§7.9). **Scale** beyond
~10^5 graph edges (§4.5). **External comparisons** — no comparator system has been run
(§7.4). One known bug produces false sentences in free text generation (§4.7); the
zero-wrong-answers record is about answering questions, not generating text.

Every §3 headline number is reproducible on one Windows machine via §8; the marked
exceptions (two historical/adjacent rows in §3.8) are excluded from that guarantee.
The proposal: the concept is sound, the honesty machinery is real, tested, and now
adversarially tested; the next experiment — rule induction under his validation gates
(§5-R1) — decides whether this becomes a credible modern symbolic system.

---

## 1. The concept

### 1.1 Thesis

Classic symbolic AI died of two diseases: the knowledge-acquisition bottleneck (humans
hand-coding facts and rules does not scale) and unaccountable brittleness (systems that
answer confidently outside their competence). Modern statistical AI solved acquisition
and reintroduced unaccountability at greater scale (no derivations, no refusals, no
auditable records).

Isaac's bet: attack both. **Learning without hand-coding** — facts enter only by
observation of raw material; rules must eventually be induced, not authored (they are
not yet: §5-R1). **Accountability as architecture** — wrong answers kept on record with
their corrections; "no answer" a first-class output; the goal state (not yet reached on
the main path — §4.1) is that every stored item is traceable to the observations that
created it and every answer carries a derivation.

The architecture is two-layer:
- **A statistical layer** [BUILT — §3.1-3.4 tests]: a compiled prediction table
  (frequency counts over observed contexts) for fast recall and completion.
  Transparent — every cell is a count you can print.
- **A logical layer** [DESIGNED, with two subsystems BUILT]: typed evidence bookkeeping —
  facts with provenance, audits that force wholes to balance against parts, exact
  placeholders for what the evidence records show is missing. Fully implemented today
  only in the numeric-law module and the findings ledger (§4.1).

External inference engines attach as instruments [BUILT for clingo, first stage]: his
learned material compiles out, their derivations return, and each returned answer is
verified step-by-step against his own store before entering (§3.7, including the
negative controls).

### 1.2 The formal foundation

The owner's **differentiation algebra**
(`3_the_theory/differentiation_algebra_formal_2026-08-06.md`): a two-tier formal system
on a single comparison operator D(A,B) = (shared, only-A, only-B). Tier 1 (exact): a
collision loop over evidence sets terminates, is order-independent, admits no false
positives (everything witnessed via provenance), refines monotonically, and forces
exact quarantined placeholders ("posits") when accounting audits fail. Tier 2
(statistical): admissibility conditions under which false certification is bounded. The
document contains its own falsification program with declared kill conditions and two
executed self-corrections. **[PROVEN-INTERNAL — the proofs are readable finite-set
algebra, authored by the owner-with-AI pair, prosecuted twice by the same authors, and
neither externally reviewed nor machine-checked. Mechanizing Tier 1 in a proof assistant
is scheduled work the theory document itself calls for.]**

The operator D is implemented verbatim as the engine's oldest primitive (`compare()`).
The honest mapping between theory and engine is a maintained companion audit,
`THEORY_VS_ENGINE_2026-08-23.md` (§4).

### 1.3 Non-goals

- Not a large-language-model competitor on breadth of world knowledge or fluent prose.
- Non-agentic: an answer/science engine. It can answer "what sequence of actions reaches
  state B" — it never executes pursuit on its own.
- No neural networks in any decision path (standing project rule); statistical methods
  are permitted but must be inspectable.

### 1.4 Positioning against prior art (what is and is not new)

- **Formal Concept Analysis / rough sets:** the theory's atoms (evidence-
  indistinguishability classes over a set family) are textbook-adjacent mathematics —
  the claimed novelty is NOT the lattice math but the combination of typed origins
  (observed/derived/posited), mandatory provenance, forced-exact posits with quarantine,
  and the declared falsification program. A reviewer should read the theory doc's own
  "what is not claimed" section.
- **Truth maintenance systems (JTMS/ATMS, 1979-86):** the closest ancestors of the
  typed ledger; the delta is add-only history (no retraction, supersession instead) and
  audit-forced posits.
- **NELL (CMU, 2010-18):** the closest ancestor of the program — continuous fact
  learning from raw material with self-verification. NELL's documented failure was
  semantic drift at scale. Isaac's proposed defense is validation-gated admission (null
  tests, held-out checks) rather than bootstrapped self-training; whether that actually
  blocks drift is an open empirical question, and a drift test belongs in the curriculum
  plan (§5-R5) before scale is claimed.
- **Inductive logic programming (ILASP/Popper, current):** the planned rule-learning
  machinery (§5-R1) — existing systems, not project inventions; the project's
  contribution would be the validation gate around them.
- **n-gram models:** the engine's main path IS a transparent n-gram-family count model
  with guards. Whether the exam result exceeds what a plain n-gram baseline achieves on
  identical training is an open control — committed in §6 and §7.1, not claimed in
  advance.

---

## 2. The document corpus (what exists, where)

All in `isaac-project` unless noted. A second repo, `dc` (the deployment/product repo),
holds the product-side engine and several research documents; the shipped data-analysis
product itself was split into its own repos, `anna` and `anna-stopgap`, built on the
same honesty machinery (per-claim provenance records, refusals, planted-error tests).

| document | role |
|---|---|
| `ISAAC_MANUAL.md` | current plain-language manual: architecture, every query path, measured state, known bugs, test map; maintained same-commit as code changes |
| `3_the_theory/differentiation_algebra_formal_2026-08-06.md` | the formal theory (proofs, admissibility, kill conditions) |
| `THEORY_VS_ENGINE_2026-08-23.md` | the reconciliation audit: theory element × engine reality × verdict |
| `ASSESSMENT_CHARTER_2026-08-19.md` | the evaluation program: 8 capability dimensions, planted + blind tests |
| `DESIGN_VERSUS_ARENA_2026-08-19.md` | benchmarking charter vs other AI; six-axis scorecard; contamination controls |
| `DESIGN_CURRICULUM_2026-08-20.md` | teaching program: math/logic first (validated by A/B test), then categories, frontier-ordered feeding |
| `RESEARCH_WRITEUP_2026-08-19_ONE_FILE_BODY.md` | storage format v2: audit, design, equivalence tests |
| `RESEARCH_WRITEUP_2026-08-19_WORSTCASE_BASELINE.md` | fresh-mind day-zero baseline; two engine bugs found and fixed |
| `RESEARCH_WRITEUP_2026-08-20_MATHFIRST_T1.md` | math-first teaching claim A/B-tested; the inference gap isolated |
| `RESEARCH_WRITEUP_2026-08-20_SELECTION_FEEDBACK.md` | ranked-selection API + graded feedback channel |
| `dc/docs/DESIGN_SEED_STRUCTURES_2026-08-19.md` | the A→B search design (bidirectional beam over the graph) |
| `dc/docs/DESIGN_REPAIR_GRAMMAR_2026-08-02.md` | failure-classification → repair theory (designed; untested) |
| `dc/docs/DESIGN_LENS_LOOP_2026-07-30.md` | self-discovery of analysis methods (designed) |
| `ASSESSMENT_2026-07-26.md` | July capability assessment (historical; pre-bug-fix — §7.6) |

Engine: `code/isaac.py` (one file, ~7,900 lines, numpy only). Tests: `rebuild/*.py`.
Archived: `isaac_project` (June-era original engine), `isaac-paperclip` (research).

## 3. Current state — verified capabilities

Every row: the claim, the number, the test file; §8 has the commands. All numbers
measured 2026-08-19..23 on one machine (i9-14900KF, 48GB; CPU-only — the GPU is unused
by the engine), **except two rows in §3.8 explicitly marked historical/adjacent, which
are excluded from the reproduction guarantee.**

### 3.1 Learning and recall [MEASURED]
- Ingestion ~50,000 facts/sec (the §8 command prints the rate; 49-58k observed across
  runs); a fact stated once is retrievable (`worstcase_baseline.py`, `scale_eval.py`).
- Full-coverage exam over 1,198 generated facts (tables 0-19, comparisons, logic):
  **100.0% exact, 100.0% answer-in-top-3** — every fact quizzed, not a sample
  (`scale_eval.py`).
- Day-zero fresh mind (invented vocabulary — nothing can be recall from anywhere):
  language completion 3/3, generation 3/3, math 6/6, planted numeric laws recovered
  exactly (+1.00*x0*x1; +3.00*x0 −2.00*x2), memory 3/3 through save/load
  (`worstcase_baseline.py`).

### 3.2 Honesty under test [MEASURED — scope: answering questions, on tested shapes]
- 200/200 out-of-range arithmetic questions refused (known tokens only, so vocabulary
  guards cannot help), 0 wrong answers (`scale_eval.py`). Limitation, carried from the
  manual's own bug list: this battery is one question shape; fragment-matching question
  shapes that the manual predicts can produce wrong answers are not yet in the battery —
  broadening it is committed work (§6).
- Pure-noise law discovery: refused, accounting 0/0/100 (`scale_eval.py`).
- 100/100 multi-step expressions containing an unanswerable step refused, **with the
  failing step named** in the returned derivation (`pemdas_eval_test.py`).
- Unknown-word questions return no-answer rather than a plausible guess
  (`worstcase_baseline.py`). Free text GENERATION is not covered by this record and has
  a known false-output bug (§4.7).

### 3.3 Multi-step solving [MEASURED]
- Expression reduction, pair-at-a-time on the learned table; order of operations TAUGHT
  as facts, not built in: three-operand 200/200; mixed precedence 200/200 (zero
  left-to-right errors); parenthesized 200/200; exhaustive and/or chains 16/16
  (`pemdas_eval_test.py`). The pre-fix control (13/100 with 87 confident wrong answers)
  is preserved in the test header.

### 3.4 Real-exam learning [MEASURED — scope: taught passages; see §7.1]
CMU CLOTH middle-school cloze exams (real exams, 4 options, chance = 25%), 120
passages, taught as plain unmodified passages, one pass each (`cloth_run.py 120`):
- Item population, disclosed: the harness keeps only blanks where all four options are
  single tokens — for these 120 passages that is **1,108 of 1,132 blanks (98%; 24
  excluded)**. Passages are the first 120 usable files in sorted filename order from
  the train/middle split (a choice, stated as one).
- Per-batch after-class: 92, 91, 80, 86, 88, 88% vs pre-teaching baseline controls of
  30, 35, 31, 31, 26, 23%. The baseline picker is deterministic (confidence ties break
  alphabetically); it lands near chance because answer keys are balanced.
- Batch 1 scored 92% after class; re-tested after each of the five later batches:
  91, 92, 91, 89, 90%.
- **Whole-course final: 944/1,108 = 85%** — every question re-tested after the full
  course (single recorded run; the engine is deterministic given identical input order,
  and any run-to-run variance source would be Python hash-order in set iteration —
  variance unmeasured, N=1 stated plainly).
- July context: the same class-then-quiz protocol scored 40% before the training-code
  fix of 08-19 (the compiler used only each sentence's final token as a training
  target). A DIFFERENT July experiment — free-answer exam scoring, no options — scored
  9.3/100; the two July numbers are different protocols, both measured through the
  since-fixed bug (§7.6).

### 3.5 Storage [MEASURED, equivalence-tested]
- Single-file format v2: a real 49.4MB v1 mind → **2.9MB (17×)**, save 1.6s, load 1.0s;
  round trip verified **item-for-item** across every data structure. The install-level
  test caught a real bug (dropped metadata) before it shipped; both test levels are
  retained. Append-only journal: autosaves append rather than rewrite; deliberately
  torn tails truncate cleanly. v1 files still load (format detected by magic bytes);
  backward compatibility is a standing commitment. For reviewers without a real v1
  mind, the test synthesizes a fixture automatically (10.6× on the small fixture —
  ratio varies with history size, property identical). (`onefile_probe.py`,
  `onefile_install_court.py`.)

### 3.6 Selection and feedback [MEASURED]
- Ranked candidate lists (order only, per spec), fill-in-the-blank at
  beginning/middle/end, multi-word beam completions, and a good/marginal/bad grading
  channel that moves future rankings and persists through save/load: 17/17 checks
  (`selection_feedback_test.py`).

### 3.7 The solver bridge [MEASURED — what it does and does not show]
- Mechanics: his observed sequences translate to 119 logic facts; clingo derives all
  100 word-arithmetic consequences he cannot reach natively (native control 0/100);
  every derived answer is verified step-by-step against his own store (100/100); reverse
  queries ("three plus WHAT is ten") work. **Negative controls added after review: a
  planted wrong derivation is REJECTED, and the same derivation checked against a store
  missing one supporting fact is REJECTED** (`logic_bridge_probe.py`).
- **What this demonstrates: the interoperation and the verification discipline. What it
  does NOT demonstrate: learning-to-logic.** The export reads his raw observation log
  (the verbatim training transcript), not learned structure — his graph and prediction
  table contribute nothing to the export. The inference rule AND the two translation
  schemas (that `[A,+,B,=,C]` means sum(A,B,C); that `[W,=,D]` means word(W,D)) were
  hand-written. Verification certifies consistency with his store, not truth — the
  store's own correctness is the job of the audit machinery that does not exist yet
  (§4.3). Removing every hand-authored element is §5-R1's success criterion.

### 3.8 Infrastructure
- Engine regression battery: 15/15 capability areas [MEASURED]; run after every change
  in this record. Known reliability issue, disclosed: an intermittent crash (TypeError,
  unhashable set) was observed by an independent review agent in 3 of 6 runs under
  concurrent load, and in July records on another machine; 26 single-process attempts
  here could not reproduce it. A diagnostic trap now fails at the insertion boundary
  with full context if it recurs (§8 documents the retry instruction).
- Interactive reply latency [HISTORICAL — excluded from the reproduction guarantee]:
  current manual figures are 40ms at 874 graph nodes and 281ms at 5,342; latency at
  exam scale (2,554×82,169 prediction table) is unmeasured. An 8ms figure from July
  predates the training-bug fix and should not be cited.
- Product line [ADJACENT EVIDENCE — different repo, out of this kit]: `anna-stopgap`
  ships the same honesty machinery against client data (13/13 planted-error checks in
  its own demo suite; reproducible from that repo, not this one).

## 4. Current state — honest gaps
*(sources: `THEORY_VS_ENGINE_2026-08-23.md` for items 1-4; `ISAAC_MANUAL.md`
known-bug list and the 08-19/20 writeups for items 5-8)*

1. **The main answer path is the statistical layer, not the formal theory — and it
   carries no derivations.** The prediction table earned the exam results; its answers
   carry a frequency confidence, not a certificate, and graph edges have no provenance
   chains ("why does this edge exist" is unanswerable today). A reviewer who asks "show
   me the derivation for one exam answer" gets none — worked derivations exist on the
   expression-solver and numeric-law paths only. The theory's exact machine is
   implemented faithfully today only in the numeric-law module (null-gated admission,
   held-out validation, kept rival forms) and the findings ledger (real provenance).
2. **No learned inference rules** (§3.7). Measured gap: he holds `three=3` and
   `3+4=7` and cannot natively answer "three plus four" (0/12, 0/100 controls).
3. **Missing entirely:** accounting audits over his own content; posits; conservation
   checks; the epistemic work scheduler.
4. **Type groups cannot overlap** (measured) — coarser than the theory's atoms.
5. **Scale ceilings measured, unfixed:** consolidation — the post-batch step that
   groups nodes by shared context and recompiles indexes — grew 5→26→68→127→199→299s
   per batch across the exam run (superlinear); the dense prediction table reached
   2,554×82,169 (~210M cells) at 120 passages. A July two-machine comparison found
   more hardware does not fix the growth curve; that comparison predates the
   training-bug fix, but the superlinear shape was re-confirmed post-fix on this
   machine (the numbers above). Sparse storage and consolidation rework are named,
   unstarted (§5-R4).
6. **Feedback grades do not generalize** past the exact question graded; constants
   hand-tuned.
7. **Free text generation can emit false sentences** (measured: attributed one item's
   property to a similar item — fluent, false, on the known-bug list). The
   zero-wrong-answers record (§3.2) is about answering, not generating.
8. **All pre-2026-08-19 numbers are historically contaminated** by the training bug
   (§7.6); comparisons to July carry that caveat in both directions.

## 5. Anticipated direction (the roadmap, in order)

**R1 — Rule induction under his validation gates. The decisive experiment.** [NEXT]
Induce the bridge demo's rule AND its translation schemas from his experience — via
inductive logic programming (ILASP/Popper class) over examples drawn from his store,
and/or template induction from his own type groups — with held-out validation and the
step-verification loop as the acceptance gate. Success: the §3.7 demo reproduced with
**zero hand-authored elements**. Failure: an honest record of exactly where induction
breaks. This decides §0's open question.

**R2 — The exact-tier working space.** Build the typed ledger + collision loop + audit +
posit machinery to the formal spec, with a property suite (order-shuffle tests,
conservation checks per operation, deflation tests on known-independent input) as a
permanent regression gate. [CONJECTURED recoverability note: a prototype was written in
a separate working environment on 08-06 and never committed to this repo; if recovered
it seeds R2 — otherwise the formal spec suffices to rebuild.]

**R3 — Bridge expansion.** An engine-level query path (compile out → solve → verify →
memorize the certified result); Z3 consistency scanning across his discovered numeric
laws (a measured need: two live laws disagreeing on shared domain went undetected in a
July experiment); Prolog with proof traces; planner export for the state-A-to-state-B
planning path.

**R4 — Scale.** Sparse table representation; consolidation rework. Acceptance: per-batch
time flat-to-linear; a 1,000-passage run completes on this machine.

**R5 — Curriculum.** Re-measure teaching economics post-bug-fix (an earlier finding
that lessons needed ~8 repeated framings per fact was measured before the fix and may
be obsolete); then staged corpora: math/logic first (already A/B-validated: one-pass
8/8 with honest refusals), then taxonomy (WordNet, Simple English Wikipedia
first-sentences, general-to-specific), relations, simple narratives — with
unknown-word-rate ordering (never feed a lesson made mostly of unknown tokens). Include
a semantic-drift test before any scale claim (the NELL lesson, §1.4).

**R6 — The arena.** Six-axis scorecard (correct / honest / sample-efficient / retentive
/ inspectable / correctable) against local comparators (mistral 7B, qwen 14B via
ollama; SOAR as the symbolic comparator) on generated material neither side has seen —
**plus the two null baselines this document owes: a same-training n-gram model on the
exam protocol, and the position-overlap trivial baseline (§7.1).**

## 6. Goals and objectives

**Near term (weeks):**
1. R1 executed and written up, success or failure.
2. The exam-protocol controls: unseen-passage generalization test; the trivial
   position-overlap baseline; the same-training n-gram baseline. [closes §7.1]
3. The honesty-difficulty co-measurement (§7.9): an abstention-enabled exam run
   reporting the accuracy/refusal/wrong-when-confident tradeoff; a confidence
   calibration table (P(correct | confidence bin)); the existing miss-analysis harness
   run and published for the 164 wrong exam answers.
4. Broadened honesty battery across question shapes (§3.2 limitation).
5. Engine query path for the solver bridge; Z3 law-consistency scan.
6. A test manifest: every file in `rebuild/` marked current-gate / stale / archived
   (the folder holds ~50 files from three eras; 8 are current gates; at least one older
   harness no longer runs against the current layout).

**Mid term (months):** R2 working space passing its property suite; R4 scale targets;
R5 curriculum through taxonomy with retention measured; first full arena scorecard
including the null baselines.

**Long term:** the two-layer architecture inverted into its intended form (exact ledger
as the spine, statistics as its typed instrument); every mechanism labeled with its
architectural role — theory component vs statistical instrument vs scheduled-for-
removal (the project rule adopted 2026-08-23, recorded in `THEORY_VS_ENGINE`); the
layerwise audit of a trained neural network (the theory doc's designed experiment
bridging to interpretability work).

**Standing objective:** zero unexplained numbers — every result reproducible by
command, every claim typed, wrong results kept on the record with their corrections.

## 7. Threats to validity (what we would attack, stated first)

**7.1 The 85% exam result measures learning-and-retention, not comprehension.** The
protocol is class-then-quiz on the SAME passages; items are 4-option cloze; and a
trivial baseline — pick the option that appeared in the taught passage at that
position — would plausibly score high, since teaching includes the completed passage.
The pre-teaching control (~chance) proves learning occurred; it does not prove the
learning exceeds high-fidelity text memory. Conceded; the unseen-passage exam and both
null baselines are committed (§6.2). What the number honestly supports: plain-delivery
teaching works post-fix (vs 40% before), retention holds ~90%, at 100% inspectability.

**7.2 The 100% closed-domain results are infrastructure, not intelligence.** Exact
recall plus reduction over generated tables is trivial as capability; the real claim is
narrower: zero wrong answers with honest refusal at the boundary — a property both
classic expert systems and current language models routinely lack.

**7.3 The bridge demo's inferential content was hand-written** — the rule and the
translation schemas (§3.7). R1 exists to remove exactly this.

**7.4 No external comparators have been run.** All numbers are absolute. No superiority
claim over any system is made anywhere in this document.

**7.5 Single developer, single machine, AI-assisted throughout — including the
mathematics.** The AI assistant that wrote the code also wrote the tests and drafted
the theory document's proofs with the owner; "[PROVEN-INTERNAL]" is typed accordingly,
and external proof review or mechanization is required before the tag strengthens.
Mitigations: planted ground truth in every test; the process has caught its own bugs
repeatedly — a metadata-dropping port bug (§3.5), a confabulation regression (the
unknown-word guard, §3.2), and a refusal failure on junk expressions (50 of 100
answered instead of refused; fixed the same day by requiring exact-fact matches for
solver steps; the fixed battery is §3.3's 100/100) — all preserved in the record.
This handoff's request IS independent re-verification.

**7.6 All pre-08-19 numbers are contaminated** by the training bug (only sentence-final
tokens compiled as targets). Both July exam numbers (40% cloze protocol; 9.3/100
free-answer protocol) predate the fix.

**7.7 The theory-engine gap is real and mapped** (`THEORY_VS_ENGINE_2026-08-23.md`).
The main path is not the theory; §4.1 states what that costs (no derivations on the
flagship result). R2 is the closure plan.

**7.8 Scale is unproven** beyond ~10^5 edges / ~10^2 documents, with measured
superlinear costs at the frontier (§4.5).

**7.9 Honesty and difficulty have not been co-measured.** Every honesty number comes
from domains where competence is 100%; the exam harness is forced-choice (refusal is
structurally impossible there), and the exam-answering path lacks the unknown-word
guard the direct-answer path has. The 164 exam misses are, in the engine's own terms,
confident wrong picks. An abstention-enabled exam run, a calibration table, and the
miss-type analysis are committed near-term work (§6.3) — until they exist, "honest"
means "honest on the tested closed domains", nothing broader.

## 8. Verification kit

Environment: Windows 11, Python 3.12, numpy; `pip install clingo` for the bridge row
(z3-solver is used by no current test — install only if exploring R3). Run from the
repo root at tag `handoff-2026-08-23` or later, with `$env:PYTHONUTF8='1'`.

| claim | command | expected pass criteria |
|---|---|---|
| engine battery | `python code/isaac.py` | `15/15 capability areas passed`. Known intermittent crash (unhashable set, §3.8): if hit, rerun and report the trap message it now prints |
| day-zero baseline | `python rebuild/worstcase_baseline.py` | language 3/3+3/3, unknown-word refusal "yes"; math 6/6 + 2/2 refusals; laws 2/2 exact + noise refusal; memory 3/3 |
| full coverage + honesty + multi-step | `python rebuild/scale_eval.py` | exact 1198/1198; refused 200/200 with 0 wrong; multi-step 100/100 |
| expression solver | `python rebuild/pemdas_eval_test.py` | 200/200, 200/200 (0 order errors), 200/200, 16/16, refusals 100/100 |
| selection + feedback | `python rebuild/selection_feedback_test.py` | `FINAL: 17/17 checks` |
| storage round trip + journal | `python rebuild/onefile_probe.py [path-to-v1-mind]` then `python rebuild/onefile_install_court.py` | `ALL COURTS GREEN` / `ALL GREEN` (literal test banners). With no path given, a fixture mind is synthesized automatically; the 49.4MB→2.9MB/17× figures require the original mind file, available to reviewers on request |
| real exams | `python rebuild/cloth_run.py 120` | final line `944/1108 (85%)`; ~20 min. Data: CLOTH.zip from the CMU CLOTH page, extracted to `data/cloth/CLOTH/` so that `data/cloth/CLOTH/train/middle/*.json` exists |
| solver bridge + negative controls | `python rebuild/logic_bridge_probe.py` | NATIVE 0/100; BRIDGED 100/100; VERIFIED 100/100; both negative controls print REJECTED; reverse query returns ['seven'] |

Note on `rebuild/`: the folder contains ~50 test files from three project eras; the
8 above are the current regression gates. A full current/stale manifest is committed
work (§6.6). All data except CLOTH and the optional real v1 mind is generated in-test.

## 9. Withdrawal conditions (what would make us retract which claim)

- **W1.** Any §8 command producing materially different numbers on this machine → the
  corresponding §3 claim is withdrawn until explained.
- **W2.** The position-overlap baseline (or the n-gram baseline) matching his
  after-class exam scores → the "teaching works" claim demotes to "context matching
  works"; retention and honesty claims stand independently.
- **W3.** Rule induction (R1) failing under fair conditions → the §0 claim that this
  can become "a credible modern symbolic system" loses its central support, and §0 must
  be rewritten to say so.
- **W4.** The R2 property suite finding order-dependent content in the ledger
  implementation → that implementation is inadmissible by the theory's own standard and
  does not ship.
- **W5.** Any answer entering his store from an external engine without step-
  verification passing → the bridge's honesty claim is void. (The verifier's ability to
  reject is itself now under test — §3.7 negative controls.)

---

*Prepared 2026-08-23. Process note, stated plainly: this document was drafted by the
project's AI assistant, fact-checked by a separate verification pass that re-ran all
eight §8 test rows from scratch, then attacked by four adversarial review passes
(overclaim hunting, kit reproduction, hostile skeptic, cold read; 51 findings), and
revised. "Independent" third-party verification has NOT yet occurred — soliciting it
is this document's purpose. It is committed in the same commit as the code and test
changes it describes, at the tag named in the header.*
