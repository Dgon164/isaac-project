# Session Record — June 10, 2026
**Continues: RESEARCH_HANDOFF_june_9_2026.md. Method followed: re-validate first, killer test first, functional metrics only, fresh sealed inputs.**

## Environment & chain of custody
GPT-2 small via transformers, float64 for validation, float32 for timing.
Custody check passed: lm_head bias = None, head IS tied wte (same data pointer),
max |model logits − W@h| = 3.5e-05. Same model, same target as June 9.

## 1. Replication (trust ledger) — PASSED
Fresh 30-prompt set, written blind this session (never seen by any prior session).
Ground truth = full model's own argmax logits.

| Config (excl 10) | June 9 (n=24) | Today (n=30, fresh) | ops |
|---|---|---|---|
| M=40 / K=200  | 19/24 (79%) | 24/30 (80%) | 17.8× |
| M=125 / K=200 | 24/24       | **30/30**   | 6.0×  |
| M=200 / K=200 | —           | 30/30       | 3.8×  |

Cumulative exact-match evidence for M=125/K=200: **54/54** across two independent
held-out sets. Misses at M=40 are all weak-margin commonsense continuations
(debris/black, rain/water, composer/Italian) — consistent with whisper-margin physics.

## 2. NEW: wall-clock measurement (first ever run in this program)
Single-thread CPU (the stated target: CPU/edge, greedy decoding), float32,
W pre-transposed so the dim-filter is a contiguous row gather:

| Method | ms/query | real speedup |
|---|---|---|
| Full matmul (BLAS) | 15.05 | 1× |
| M=125/K=200 (exact, 54/54) | 4.63 | **3.2×** |
| M=40/K=200 (80%) | 1.20 | 12.5× |

The 6× ops → 3.2× wall-clock; overhead is argsort + argpartition + gather.
The result is real on hardware, not only on paper. End-to-end (head ≈25–30% of
GPT-2-small) this remains ~1.2–1.3× overall; the honest Amdahl framing stands.

## 3. NEW CLOSED DOOR: branch-and-bound exact cascade (the "designed upgrade")
Implemented for the first time (bnb_exact.py, certify.py). Three findings, all negative:

(a) **B&B as search: exact but no speedup.** Cauchy–Schwarz ceiling
    partial + sqrt((‖w‖²−spent)·‖h_tail‖²), pruning after every 8 dims,
    leader-confirmed lower bound. Result: 30/30 exact, but mean speedup
    1.2–1.4×, worst case 0.9× (slower than full matmul). Cause: ceiling slack
    ≈ ‖w_tail‖·‖h_tail‖ is tens of logits; the margins it must cut are ~0.63.
    Same physics that killed dim-nomination. Seeding with the validated filter
    does not help (the bound, not the seed, is the bottleneck).

(b) **B&B as certificate: 0/30 certified at every depth M=40…500.** The bound
    never once proved the filter's answer exact. Independently confirms the
    June 9 "~2% certified" observation. Certify-or-fallback pipelines come out
    at 0.6–0.9× — worse than doing nothing.

(c) **Fixed global dim order fails: 10/30 at M=40 (vs 24/30 per-query),
    18/30 at M=125.** The discriminative band is genuinely query-specific
    beyond the shared carriers. Precomputed per-row prefix energies are
    therefore unavailable; the 2× energy-accumulation cost is unavoidable.

**Status: closed with Cauchy–Schwarz-type norm bounds. Do not reopen without a
fundamentally tighter bound family (e.g., learned/quantile bounds, which lose
provable exactness, or cone/clustered bounds as in exact-MIPS literature —
LEMP, FEXIPRO — which should be READ before any rebuild).**
The conceptual unification (bound termination = sufficiency-as-coverage)
survives as a lens, not as a speedup.

## 4. Implication for the writeup (TODO #1 reframed)
There is no cheap proof of exactness. The pipeline must be framed as a
high-accuracy heuristic with a silent failure mode, mitigated by the margin
fallback (heuristic confidence, not proof) — or framed purely empirically
(54/54 and counting). The required next steps are unchanged and now sharper:
scale to 500+ diverse prompts (not hand-written templates — real corpus text:
wikitext, code, dialogue), and bench against adaptive softmax, HNSW/FAISS, and
the exact-MIPS line (LEMP/FEXIPRO) before any novelty claim.

## 5. NEW VALIDATED: coarse-to-fine ladder (researcher's posit, benched same day)
Posit: V → 2000 → 200 → 20 → top-1 with widening dim budgets per stage.
Result (n=30, same fresh set): literal ladder (20/80/200 cum dims) = 27/30 at
33.1×; fatter ladder (40/125/300) = **29/30 at 17.3×**, which Pareto-dominates
the flat 2-stage M=40 config (24/30 at 17.8×) — same cost, +5 exact.
The widening cascade beats flat filters at the cheap end of the frontier.
The exact end is unchanged (2-stage M=125 = 30/30 at 6.0×). Goes in the writeup.

## Vocabulary map additions (this session)
| Their term / idea | Established name |
|---|---|
| "Map the outputs, direct lookup" | kNN-LM (Khandelwal 2020); retrieval-augmented LM; semantic caching |
| "No average person" | Daniels 1952 cockpit study; mean-is-atypical in high dims (Todd Rose, "The End of Average") |
| Coarse-to-fine 2000→200→20→3 | Cascade classifiers (Viola–Jones); beam narrowing; coarse-to-fine inference |
| "No more processing than needed" | Adaptive computation: CALM, early exit, ACT |
| Venn constraint ordering ("friend Nick") | Selectivity ordering in query optimization; smallest-posting-list-first |
| "Detection is a universal subsample; don't make it more wrong" | Data processing inequality; sufficient statistics; information bottleneck (Tishby) |

## Memory audit (this session)
Recalled: "exclude 10 dims → M=40 good; include them → need M=80."
Benched (n=30, K=200): excl-10 M=40 = 24/30 vs include-all M=80 = 26/30;
at every M < 125, inclusion costs ~2 prompts, i.e. carriers in ≈ 2× dim budget
for comparable accuracy. At M≥125 the difference vanishes (both 30/30) — with
enough discriminative dims the structure dims are outvoted. Verdict: mechanism
confirmed in shape; the implied exactness at M=40 was the inflation (80%, not
"good"). Exclusion matters most when the budget is tight.

## 6. ISAAC v0.15 GROUNDING TEST v0 — handoff correction, milestone narrowed
The June 9 handoff's claim "ISAAC does not extract state from language; without
harness scaffolding nothing is written" is **OUTDATED for v0.15** (Speech build,
May 10). Measured on a fresh seed net, raw sentences, no \seed/\fact/set_meta:

- "The man has a pen." → `man.possessions += pen` — state written from raw
  text, with 'man' and 'pen' being words the net had NEVER seen (created
  during processing). The writer exists and generalizes to novel vocabulary.
- "Rab has the hat." → no_action. Isolated cause: **syntactic licensing.**
  "The rab has the hat." → `rab.possessions += hat`. The article licenses
  noun-hood for unknown words; bare proper nouns are not yet licensed.
- "She has the hat." → no pronoun resolution.
- After "The rab has the hat" + "The ann has the hat": BOTH possess it —
  the writer adds but does not supersede. "Who has it NOW" needs possession
  transfer (the known supersession/last-write issue; Sally–Anne-relevant).
- Crystallizer-as-tagger verdict: PARTIAL. On the raw corpus it minted 25
  proposals incl. rejection_pattern {modality: unknown, count: 11} — it
  OBSERVES that unknown-modality tokens keep being gated out, which is
  exactly the training signal for licensing new words, but no loop yet
  closes rejection_pattern → modality assignment.

**Milestone #1, narrowed to a build list:** (a) proper-noun licensing
(capitalized bare token in subject slot → entity) — preferably LEARNED from
correction pairs per Lesson 7, since the crystallizer already produces the
signal; (b) pronoun door; (c) possession transfer/supersession; (d) then the
McGuffey story (Rab/Ann/hat) becomes a legitimate end-to-end state query.
Corpus located (training_data/ in v0.15 zip). Architect's call needed: do the
built-in metastructural templates (create_event_or_possess etc.) count as
stipulated seed anchors, or must they too be learned?

## 7. Session-18 concept matrix — benched; milestone chain now fully mapped
concept_matrix.py runs (needs walker_s15.py + crystallizer.py from the
session-15-complete zip; S18 zip ships without the brain). ALL 8 built-in
tests pass. Key result (Test 3): verb action-signatures are DISCOVERED from
before/after observation — threw≈kicked (both write position+velocity),
painted≠threw (writes color only) — learned, not coded. Custody caveat: the
before/after states are hand-written dicts, i.e. harness-supplied state one
level above the old set_meta. The matrix solves the verb-semantics half of
grounding; states-from-language remains the unbuilt connector.

**The milestone chain, located across three artifacts:**
(1) v0.15 pipeline: raw sentence → roles, with article-licensing (today's
finding); (2) S18 concept matrix: verb → dimensional signature, learned from
state pairs; (3) crystallizer: types the signatures. The build is the WIRING
plus a bootstrap: seed a few verbs with known signatures → infer states from
sentences via known verbs → learn new verbs from inferred states (correction
loop, EM-shaped). The S17 failure analysis itself says the wiring is the
work that keeps being dodged.

Crystallizer thresholds hardcoded (user confirms): the principled builder is
the null-model/surprise gate already specified June 9 (binomial tail —
admit a category when overlap beats chance). Build item, spec exists.

## 8. Puzzle-piece theory — finally read (Isaac_Complete_Walkthrough.docx §5)
Three claims: (5.1) superlinear compression, power law α=0.853, R²=0.981,
phase transition at 50–60% merge threshold; (5.2) holographic recursion,
FCA inverse law 100% (1,116/1,116); (5.3) downward inference, 100% precision /
41–54% recall, zero false positives, inference rate grows with corpus density.
Mapping: 5.1 = Heaps' law (α squarely in the classic Heaps exponent range);
5.2 = the FCA Galois duality — a THEOREM, so 100% verifies the implementation,
not the world; 5.3 = type-based link prediction, the genuinely benchable claim
(queue: fresh corpus, sealed protocol, precision/recall vs corpus density).


## 9. Session 19 kicked off — Build A complete
Architect rulings: Dollhouse world; ISAAC discovers (ask/observe/remember);
NO English seed. episode_generator.py built world-side per sealed protocol
(world+keys before learner), validated on 2 seeds: scripted residents drive
the engine headlessly; ISAAC = embodied virtual observer, perception-filtered;
queries auto-split observable vs unknown-correct (structural-honesty class);
keys sealed with SHA-256. Set 1 opened for generator validation only — fresh
sealed sets required for the real test. Proposal: Isaac_Session19_Proposal.md.


## 10. Intrinsic dimensionality measured (researcher's 10-50 dims claim)
20,224 GPT-2 final states, real corpus. TwoNN intrinsic dimension = 8.2
(10.9 carriers-zeroed) — the claim's range, measured. Three-way split:
variance ~1.5-3 dims (PC1-3 ARE the carriers; PC1 loads 0.71 on dim 496);
manifold ~8-11 dims; DECISION needs ~300 global PCA dims for 76.5% agreement
(random-k flat at ~5-8%) but only ~125 PER-QUERY dims for exactness — the
low-dim structure is real but LOCAL, which is also why the global dim order
failed (§ certify.py). Literature match: Pope 2021 (ImageNet ID 26-43),
Ansuini 2019/Valeriani 2023 (deep reps O(10)), LoRA, Gärdenfors conceptual
spaces, superposition. Full report: low_dimensionality_report.md.


## Custody mapping (every cross-quoted number -> producing script, this package)
| Number quoted | Produced by |
|---|---|
| 54/54 exact (M=125/K=200, cumulative) | revalidate.py (30/30) + June 9 session (24/24) |
| 24/30 vs 19/24 at M=40 | revalidate.py |
| Global-order failure 10/30 @ M=40 | certify.py |
| B&B 1.2-1.4x, certificates 0/30 | bnb_exact.py, certify.py |
| Wall-clock 15.0 -> 4.6 ms (3.2x) | session record §2 (inline bench, command logged) |
| Shared-profile/D(x)/QKV numbers | slopes_and_qkv.py, qkv_round2.py |
| Lookup 50.1% @ 0.8x head cost | lookup_head.py |
| Ladder 29/30 @ 17.3x | session record §5 (inline bench) |
| ID = 8.2 / PR 1.5 / decision table | intrinsic_dim.py |
| TwoNN ban-window control 8.3/8.5/8.6 | secondary reviewer's run (their report, quoted) |

## Vocabulary map additions (low-dim study)
| Term/idea | Established name |
|---|---|
| "10-50 dims suffice" | Intrinsic dimension; manifold hypothesis; TwoNN (Facco 2017) |
| "adaptation is tiny" | Intrinsic dimension of objectives (Li 2018; Aghajanyan 2020) -> LoRA |
| "humans get by with 5 dims" | Gärdenfors conceptual spaces (per-domain quality dims); Cowan 4±1 |
| "millions distinguishable in tens of dims" | Johnson-Lindenstrauss lemma |


## 11. GREENLIT — production data generated, Build E complete
Architect approved; walker-raw ingestion ruling accepted by default.
- TRAINING CORPUS: 30 episodes x 240 ticks (seeds 1001-1030), ~25k ground
  truth events, ~800 sentence-paired observations inside ISAAC's perceptual
  range (sparse by design). Streams only are learner-visible; ground truth
  retained for post-hoc audit only.
- SEALED TEST SET: 5 seeds (9001-9005), who-has + where-is queries. Keys in
  production/test/SEALED_KEYS/, SHA-256 custody in CUSTODY.txt, UNOPENED —
  class-A counts for where-queries genuinely unknown to this session.
- BUILD E: surprise_gate.py implemented against the June 9 pre-registered
  spec. Acceptance PASS: noise 0.28 orders (predicted ~0.2), planted 19.3
  orders, gate@3.0 separates cleanly. Admission level 3.0 awaiting
  architect ratification.
Next session: Build B (walker-raw ingestion -> co-variation doors via the
gate), then C (query walk), D (correction port), then the first sealed run.


## 12. FIRST SEALED RUN — MILESTONE #1 OPERATIONALLY MET (12 class-A correct)
Learner v0 (Builds B+C, ~250 lines, no English seed): discovered
("picks","up")->object-vanishes @38.6 effective orders and ("sets","down")->
object-appears @17.9 from 78 visible-delta observations; tracked beliefs with
supersession; answered sealed queries. Custody verified, answers locked
pre-unsealing, scoring rule declared pre-unsealing. RESULTS: class-A 12
right / 18 wrong; class-B 186 honest-unknown / 6 fabricated (96.9% honest,
no honesty module). Pass: FAIL under original zero-fabrication condition,
PASS under pre-registered amendment (>=1 class-A via learned doors;
fabrication analyzed) — architect to ratify which governs. Failure analysis:
(a) all 6 fabrications are stale beliefs (pre-registered risk confirmed;
door confidence != belief freshness; Phase-2 fix re-observation);
(b) BENCH BUG: where-is observability check never used its loop variable —
class-A where labels unreliable; who-has sound; results stand as scored,
generator fixed for next seeds (reviewer's exact question, answered);
(c) entity-arrival doors sit unlearned in the data (NO_VISIBLE_DELTA pairs).
Full report: FIRST_SEALED_RUN_REPORT.md.


## 13. EMBODIED AGENT v1 — tracking test redesigned per architect; run twice
Architect corrections applied: (1) classes replaced by score-then-audit
(knowability is a diagnosis, not a label); (2) NO prescribed patrol — agent
has an action menu (WAIT/MOVE/LOOK-one-item/ASK) and an activation mechanism;
questions are seeds (+activation, decaying, re-askable); behavior is emergent.
Residents answer ASKs from witnessed memory IN EVENT-SENTENCE FORMAT, so
testimony parses through the same learned doors (no new machinery).

Run 1 (scripted tracking patrol, before correction): architect's case (c)
CONFIRMED — 3 correct answers via supersession-over-gaps; case (b) captured
(1 stale-belief wrong); headline finding: incidental beat trigger 4-0 —
camping on stationary targets starves perception (explore/exploit, measured).
Bug family surfaced: object NAMES are not identities (duplicate-named objects
contaminate name-keyed audit rows) — identity-tracking organ filed.

Run 2 (embodied agent, after correction): emergent behavior real (ask-loop
toddler phase, then ask-memory + shrugs -> asks 58->13/5/3). RESULTS: 5 right
(incl. FIRST 2 TRIGGER successes via planted attention), 25 unknown,
**0 wrong — zero fabrication** with no honesty module. Stipulated v1
constants declared (+10 question, +3 event, 0.97 decay) awaiting principled
replacement. Movement remains low (8-14 moves/240 ticks) — frontier
exploration under-driven; next organ: curiosity/coverage drive, to be
designed as mechanism, not policy.


## 14. ACTION SECTION ADDED (architect's design) — first produced utterances
Affordance registry built: explicit, self-inspectable, extensible. Built-ins
(WAIT/MOVE/LOOK/SPEAK) are the stipulated body anchors with signatures;
discovered affordances appendable with provenance; every affordance carries
a track record in the same confidence currency as doors. ASK abolished as a
primitive: asking = SPEAK(learned question frame + perceived name). The
frame ('who','has','the') was learned FROM the seed questions — the bench's
probes double as speech curriculum. Real utterance strings cross the
boundary; residents parse them with the same comparator machinery; malformed
or unanswerable asks fail perceivably (shrugs). Run: 23 utterances produced
across 3 seeds ('who has the Tin Lantern?' etc.); SPEAK track record 1/23
honest (asking strangers about arbitrary objects mostly fails — confidence
being earned, not granted); one full testimony loop closed (8103). Two new
stale-belief wrongs reappeared — staleness organ remains the top build.
Next: affordance-effect doors (own-action -> world-delta co-variation, same
learning machinery, first person) so DISCOVERED affordances can register
themselves; MOVE/LOOK need real failure conditions for honest track records.


## 15. TIMESTAMPED BELIEFS (architect's design) — built, with an instructive
over-correction. Beliefs now carry their observation tick; answers are dated
reports ("Sarge, last observed t132"); freshness = survival probability under
the agent's LEARNED change rate (no stipulated constants); decision = argmax.
Run: 30/30 unknown — total suppression. The audited case proves the concept
and the flaw at once: 'Sarge @t132' was TRUE at its date AND still true at
test time, suppressed at freshness 0.26. Diagnoses: (a) the learned global
rate ignores per-object heterogeneity (Star Chart is not Red Ball) — fix is
per-object rates with empirical-Bayes shrinkage toward the global, the same
null-model family as the surprise meter; (b) heard-only rate estimates are
selection-biased and underpowered; (c) MOST IMPORTANTLY the decision now
correctly demands DECLARED STAKES: argmax at 0.5 assumes symmetric scoring.
The bench must publish its payoffs (right/wrong/unknown values); the agent
should maximize expected score, which derives the cutoff from stakes
(symmetric -> 0.5; fabrication-penalized 2:1 -> 2/3). Zero stipulated
thresholds survive: the one cut that exists is computed from published
stakes. The dated-report FORM is correct regardless — 'X, last seen t132'
is never false; risk enters only at binary compression for the bench.


## 16. TRAIT HALF-LIFE MEASURED (architect's design, validated by world physics)
Pooled 2,927 possession-change intervals from 30 training episodes:
mean gap 17.4 ticks, median 8, implied possession half-life ~12 ticks.
Material trait: 0 changes in 25k events (half-life unmeasurably long).
THE TRAIT IS THE RIGHT UNIT — pooling per trait solves the per-object data
sparsity; the trait split is enormous (possession ~12 ticks vs material ~inf).
Type-conditioning visible exactly as predicted ("unless it's slate or
copper"): small objects churn faster (15.2) than tiny (20.5). CV = 1.53 > 1:
the world is BURSTY — neither pure half-life (memoryless) nor lifespan
(aging) but a mixture; the over-dispersion is unmodeled conditioning
(likely: hazard ~ co-presence of residents — learnable). VERDICT REVISED on
§15: the agent's total suppression was CORRECT physics — a 108-tick-old
possession belief has survival ~e^(-108/17) ~ 0.2%; the Star Chart was a
tail survivor; expected-value play loses individual hands. CONSEQUENCE,
derived not designed: in a 12-tick-half-life world, current-state questions
are unanswerable without re-observation near test time — Phase 2's
"go look before answering" is now a theorem of the measured physics, and
attention scheduling proportional to trait hazard (re-check holders often,
materials never) is the principled curiosity mechanism that was missing.


## 17. SINK PROCESS ADDED (scope-gated: one process of the several proposed)
Justification: completes the measured trait-tempo spectrum, not decoration.
Plug -> rises(+2) -> full(+5) -> overflow(+7), resident-reactive unplug.
Measured over 19 complete cycles, prediction registered beforehand:
CV(fill) = 0.00 at every stage — pure deterministic lifespan — vs
CV(possession) = 1.53 (bursty memoryless) vs material (infinite).
The world now physically contains all three temporal regimes. The process
also embeds the racing sim's unfinished curriculum at tractable scale:
precondition (plug), rate, threshold, and consequence — cause-and-effect
with a clock. Session 21 curriculum: the first TIME-PREDICTION door
("plugged at t -> overflow at t+7"), learnable from the staged sentences by
the existing co-variation machinery; sealed question type: "when will it
overflow?" Cake, color change, etc. deferred per scope discipline.

## Artifacts this session
- revalidate.py — replication + custody check (output in §1)
- bnb_exact.py — B&B implementation, both dim orderings (output in §3a)
- certify.py — certification + global-order experiments (output in §3b,c)
- lookup_head.py — direct-lookup head experiment (kNN-LM form)
- This record.

- episode_generator.py — Dollhouse episode channel w/ sealed keys (Session 19 Build A)
- Isaac_Session19_Proposal.md — the v19 build plan
- intrinsic_dim.py + low_dimensionality_report.md — the 10-50 dims study
- production_run.py, surprise_gate.py, v19_production_corpus.zip - the data and Build E
- learner_v0.py, scorer.py, FIRST_SEALED_RUN_REPORT.md - the first sealed run
- tracking_test.py, agent_v1.py - the tracking paradigm and embodied agent
- sink_world.py - the lifespan-trait process and its measurement
