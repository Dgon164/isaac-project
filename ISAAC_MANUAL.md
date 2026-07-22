# THE ISAAC MANUAL
### The complete, current capability reference — every part, every method, honestly scoped
**Engine:** `code/isaac.py` (one file, one class, numpy only, no neural nets in any decision path)
**Self-test:** `PYTHONIOENCODING=utf-8 python isaac.py` → expect **12/12**
**UI:** `python ui/isaac_workspace.py` → http://127.0.0.1:8675 (three-channel workspace; legacy console: `python ui/isaac_ui.py` → :8674)

> **MAINTENANCE RULE (same as ISAAC_BUILD_STATE.md):** when a capability is
> added, changed, or broken, update THIS manual in the same step. If a
> capability isn't documented here, assume it doesn't exist. The narrative
> introduction lives in `PAPERCLIP_MANUAL.md`; the day-by-day state ledger in
> `2_the_machine/docs/ISAAC_BUILD_STATE.md`; THIS doc is what he can DO.

---

## 0. The two primitives and the four laws

Everything below is two operations composing: **differentiation** (compare;
keep what recurs) and **memory recursion** (a discovery becomes a thing that
can enter further discoveries). Four laws govern every mechanism:

1. **The null law** — every admitted claim beats a null designed to destroy
   exactly the claimed structure, nothing else. (Five case studies: jitter
   null for co-timing; null-gated basis; conditional rate-gap for blockers;
   F-test at the noise ceiling; block-permutation needed for autocorrelated
   targets — the last is still an open item, guarded by a term cap.)
2. **Tests over thresholds** — wherever a fixed threshold caused trouble, a
   statistical test replaced it.
3. **The proposal principle** — "we offer possible solutions, not THE
   solution." Teaching adds candidates; only evidence adds conclusions.
4. **Everything enters, nothing leaves** — forgetting is demotion from the
   comparison set, never deletion.

---

## 1. The mind's substrate

| part | what it is | key methods |
|---|---|---|
| `Net` | the only data structure: nodes + directed tagged doors + metadata | `add_door(src,tgt,tag)`, `get_doors(node,tag)`, `get_predecessors`, `get_full_profile`, `set_meta/get_meta` |
| `Scratch` | working memory: named registers with history | `write/read/incr/append/latch/history/snapshot` |
| `compare(a,b)` | the differentiation atom (sets): shared / only-a / only-b | module function |
| `World` | mutable entity states + taught actions | `set_state/clear_state/has_state`, `teach_action`, `execute` |
| findings | the scientific memory (see §8) | `record_finding/recall_findings/load_ledger` |

## 2. Sensing (how experience enters)

- `observe(tokens)` — sequence → sequential doors; dirty-marking; immediate
  type-slotting (`_sense`); auto-`tick`s each token with its type doors.
- `observe_negative / observe_tagged / observe_frame / observe_matrix` —
  negation, custom tags, frames, tabular ingestion.
- `teach(subject, relation, object)` — a fact: observed AND indexed in
  `fact_index[(s,r)] → [objects]`. (Internal discoveries use `_teach_fact`,
  which skips the tokenizer — structured names would be shredded.)
- `tick(active_set)` — one instant of simultaneous activation. Any retina,
  game loop, or sensor can call it; it feeds `activation_log` and, if a
  circle is being followed (§6), advances the clock and opens statuses.
  **Caveat:** clock ticks are sensory ticks — keep one stream per episode.

## 3. Consolidation (idle mode — "sleep")

- `consolidate()` / `crystallize()` — FCA-style type discovery from door
  profiles (dirty-scoped or full). Types are nodes; membership doors both
  ways. **Known limit:** connected-component grouping cannot represent
  OVERLAPPING concepts (measured: shared doors merge groups).
- `wave_consolidate()` — the temporal crystallizer, one mechanism recursed:
  - **groups** — doors that fire together (jitter-null + independence floor,
    1.4× anti-bridge margin);
  - **conditional rescue** — a door exiled by heavy interference re-joins
    when membership holds where a candidate blocker is absent; the blocker
    is taught as a `blocks` fact in the same move;
  - **handoffs** — group g off co-timed with h on (the wave moving);
  - **circles** — closed handoff paths; entered as nodes with `wave_next`
    order; dwell learned as meta (the clock's calibration);
  - **level 2** — circle activity becomes doors; same stages rerun
    (circles of circles, demonstrated);
  - **status explanations** — `miss:X` doors get explained by ordinary
    co-activation scoped to the entity's own timeframe → `blocks` facts.
  Operating envelope (battery-measured): period ≥ 9 ticks, instantaneous
  handoffs, non-overlapping groups, fire rate ≥ 0.7, ≲4 concurrent
  aperiodic waves, T ≥ ~1000. Movement claims: 0/20 false on noise.

## 4. Thinking (query paths)

- `lookup(context)` / `check(context, target)` — argmax / specific-cell read
  through the think loop (recall → process → evaluate) over the compiled
  frame→delta matrix. Auto-compiles when dirty.
- `predict_next`, `walk_chain`, `generate` — door-walking alternatives.
- `transduce(start, stream)` — the universal state walk: next state =
  `lookup([state, symbol])`; state lives in Scratch. Counting, parity,
  motion all reuse this loop; only the taught doors differ.
- `compute(a, op, b)` — arithmetic with decompose-when-shrug + memoization.
- `solve(problem)` — token problems with `?` unknowns (forward / backward /
  gap-fill). *(Distinct from `apply_law` — see §7.)*
- `logic_eval`, `reason_chain`, `is_a_check`, `can_check`,
  `containment_check`, `property_check`, `syllogism` — the symbolic layer;
  reads facts and type doors.
- `assess / plan_think_execute` + `World` actions — consequence layer.

## 5. Perception (doors, not boxes)

- `fit_lens(name, X, ...)` — registers an aligner. **Default = the
  null-gated basis**: standardize, then rotate only along correlations
  beating ~3/√n (the basis itself must beat chance). Optional random lift,
  discriminative select (Fisher option survives but is deprecated by
  audit 2.7 — do not use it for causal ranking).
- `crystallize_features(X, y, lens=)` — one concept-node per class whose
  doors are **observed quantile log-densities** (proximity doors). Legacy
  box meta still written for `recognize_matrix`/old scripts.
- `classify_features(X)` — summed log-likelihood, one matmul-shaped
  decision. **Known gap: no abstention** — it always answers (fix queued:
  shrug + genus-level answers).
- `recognize_doors(active, tag)` — partial, recursive recognition: a
  concept fires from the fraction of its `part` doors present (permanence;
  load-bearing in the clock).
- Harness-side (validated, not yet in-engine): **registration front-end**
  (`rebuild/registration_perception.py` — pose/identity factoring; digits
  under position+scale 5–15% → 84–87%; pose returned as data) and
  **ideals + differentia** (`rebuild/ideals_differentia.py` — genus/
  species recognition, key identifiers discovered by minimal inter-sibling
  door overlap, honest genus-level ties, truncation cue).

## 6. The clock, statuses, expectation

- `follow(circle)` — attend to a discovered circle: phases ordered by
  `wave_next`, members and learned dwell loaded; registers live in Scratch.
- every `tick` then: evidence advances the phase (via `recognize_doors` —
  occlusion-tolerant); learned dwell dead-reckons when evidence is hidden;
  expected-but-dark doors persist 2 ticks → **status**: `world.set_state
  (phase, "missing X")` + a `miss:X` door fed back into the same tick
  (statuses are doors — explanations emerge in §3). Statuses clear on
  sight or when the entity leaves the stage (absence-by-night ≠ occlusion).
- Self-test: phase 100% through occlusion; statuses 94.1%/tick;
  `blocks(disk) ← cloud` queryable in `fact_index`.

## 7. Discovery — the challenge loop (the thing that learns things)

- `discover(X, y, name=)` — given examples of something he cannot do:
  - **atom library**: variables; products to degree 3; sin/cos at scale
    grids; exp decay AND growth; **powers** (±0.5, ±1, −2, 1.5 grids);
    pairwise cos/sin/cosh of differences. Grids PROPOSE scale parameters
    (unreachable by regression); hill-climbing refits SHARPEN them.
  - **staged, null-gated admission**: candidates grow only around admitted
    terms; a term must beat the max-over-candidates correlation on
    permuted residuals; trial shortlist is structurally diverse (raw-var
    candidates guaranteed trials); completers judged by **F-test**
    (significance decides; genuine ties go to the simpler form);
    `max_terms=16` brake (autocorrelated targets — see law 1).
  - **half held out**: the rule must WORK, not merely fit.
  - **verdicts**: `UNDERSTOOD` (R² ≥ .9 held-out) / `PARTIAL` / `CAPTURED`
    (nearest-exemplar beats permuted null — incl. per-feature 1-D
    fallback; caught, not said; no nets) / `NO RULE` (0/40 false
    discoveries across batteries).
  - **scope**: `form-true` (edges of observed range hold) vs `range-valid`
    (usable inside; never silently swapped). Both are knowledge.
  - **rivals**: classic look-alikes (linear/quadratic/cubic/sin/cos/
    exp±) swapped in per single-feature term, F-tested; survivors stay
    LIVE on the law with a **probe** — the input where the tied forms
    diverge (usually outside the observed range).
- `confirm(name, X, y)` — new evidence retires rivals (CONFIRMED) or
  **OVERTURNS** and rewrites the law. (Pendulum demo: parabola chosen on
  ±1.2, cosine tie declared, probe "x≈3", overturned on the wide view.)
- `apply_law(name, X)` — a law is reusable computation. (Kepler, learned
  from 8 planets, predicted Pluto: 248.0 vs 247.9 — beyond training range,
  across a session boundary.)
- **Cross-domain** (harness `rebuild/cross_domain.py`, validated): laws
  matched by structure via log-track exponents (power laws are linear in
  log-log); families become abstraction nodes (`instance_of` facts);
  **analogy-primed transfer** solves data-starved domains (magnetism n=24:
  cold 0.82 → primed 0.995). Log-track inside `discover()` is a queued
  engine item.
- Known limits (battery + red team, all documented): wrong-form risk at
  n < ~400 (provisional rule); frequency reach ≈ 2× grid max; nested
  nonlinearities land in CAPTURED by design; iid permutation invalid on
  autocorrelated targets (cap + pending block-perm); rational functions
  admit usable trig surrogates (range-valid).

## 8. Memory that outlives the process

- **Findings ledger** — `record_finding` fires automatically on every
  discover (laws AND verdicts — negative knowledge included), confirm
  (confirmations/overturns), and wave consolidation. One JSON line each:
  verdict, equation, scope, rivals+probes, provenance, full model for laws.
  `recall_findings(kind=, contains=)` searches; `load_ledger(path)`
  rehydrates a previous session's laws as APPLICABLE. Set `ledger_path`
  to persist (UI uses `data/findings.jsonl`).
- **Whole-mind persistence** — `save(path)` / `Isaac.load(path)`: the
  entire mind, one small file. `fork()`: deep-copy branch for
  counterfactual experiments (teach the fork; the original is untouched).
- The distinction is deliberate: **the snapshot preserves a mind; the
  ledger preserves knowledge.** Minds are cheap to fork and discard;
  knowledge accumulates across all of them.

## 9. The UI (`ui/isaac_ui.py`)

One stdlib file. Panels: **Mind** (save/load/new/fork; laws held),
**Converse** (teach s-r-o; observe; ask — `cat is_a ?` or next-token),
**Discover** (paste CSV → verdict card: equation, R², edge, scope, rivals
with probes; apply any law to new rows), **Remember** (ledger search).
Server binds 127.0.0.1:8674; minds stored in `data/minds/`.

## 10. Test map (what proves what)

- Engine self-test (12 areas): language, math, logic, reasoning, decompose,
  persistence, waves, tracking, discovery, rivalry, spatial, boot.
- Harness (`rebuild/`): six rebuild proofs (doors, composition, enumerator,
  waves, interference, entity-status); batteries with per-run CSVs
  (`wave_battery`, `discovery_battery`); adversarial `redteam_discovery`;
  real-data (`covtype_*`, `higgs_real_test`, `gauntlet` — 10 datasets, one
  pipeline); `cross_domain`; `condensation_scaling`; `clock_world`;
  `registration_perception`; `ideals_differentia`; `digits_structural`.
- Reports: `rebuild/RESULTS.md`, `WAVE_TEST_REPORT.md`,
  `WRITEUP_2026-07-01_FOR_REVIEW.md` (§7 = verify-everything commands).

## 11. Current honest scoreboard (2026-07-02)

Competitive: covtype 94.4% (record ~97.5); exact law recovery incl.
off-grid damped oscillation; cross-domain transfer. Commodity-or-below:
MNIST 95.2 / Fashion 76.5 / CIFAR 32.6 / Omniglot 1-shot 51.6 / FSDD 92
mixed–54 transfer. Differentiated (the product): verdicts + scope +
rivals + probes + precedent-dossier explanations + cross-session
inheritance — honesty machinery wrapped around discovery, on a CPU,
readable end to end.

## 12. What does NOT exist yet (so nobody assumes it)

No abstention in classify_features; no compound doors in-engine; uptake
composition harness-only; no FCA lattice (overlap merging); no
shrug→discover reflex; no block-permutation null; no symbolic/token
challenges in discover(); no CAPTURED→law graduation loop; no
learned-invariant perception (phase 4); no curiosity — challenges arrive
from outside, and the probe queue is proposals only. The clock-reading
harness readout is broken (22.9% — harness bug, engine unimplicated).

## 13. The boot line (2026-07-22) — shapes run the mind, code only walks

The hard-drive principle: the only hard-coded thing is the entry point.
Full design: `BOOT_LINE_DESIGN.md`.

- `beat()` — THE ENTRY POINT: reads `boot:entry` from the net, walks the
  current boot flow once (re-read every beat — supersession takes effect
  live). `boot(beats=)` repeats until idle. First call on a bare net runs
  the one-time seed (`_seed_boot`): the default boot loop + pipeline are
  authored as net shapes, meta-stamped as told-structure, supersedable.
- THE RECOVERY SECTOR: the install also writes a pristine copy of the
  original at `boot:recovery` (meta `sector`). Every flow carries a
  `chapter` number (authorship order, a fact in the net). Resolution
  chain at every beat: the `current` redirect if structurally sound
  (`_flow_ok`: steps meta + flow-start + every step spec) → else the
  LATEST sound boot chapter among boot-tagged doors → else a sound
  UNCONNECTED chapter (boot lineage by name or `branched_from` chain)
  found and reconnected → else `_recover_boot()` rebuilds the original
  from the sector (broken steps superseded onto the record, never
  erased) → else factory reseed. Every recovery records a
  `boot-recovery` finding.
- Parallel workers: `config:workers` (seeded 1) — when > 1,
  `crystallize_job` runs segments in separate PROCESSES
  (`_crystallize_piece` is stateless, never touches the mind; the main
  process stays the single consumer, race-free by construction).
- Flows as net content: `define_flow(name, steps)` / `branch_flow(src,
  new, replace_step=)` — specs in `flow:`/`step:` node meta; `walk_flow`
  runs ops (`getattr` on the mind), takes the first firing door, receipts
  EVERY door taken or bypassed; unknown op / missing spec → `refused`
  (an outcome, not an exception); `hop_cap` stops runaway walks. Every
  walk records a `flow-walk` finding.
- The spine: `ingest(content)` → `job:` node on `queue:inbox` (state
  open/working/done/refused — refusals keep their why). Default pipeline:
  `segment_job` (pieces ≤ `config:segment-size` tokens, whole sequences)
  → `crystallize_job` (per-segment disposable scratch mind, crystal
  receipt on the `seg:` node) → `assess_job` (known/new/kin vs the net,
  mechanical) → `merge_job` (recrystallize in `config:merge-group`
  batches) → `commit_job` (THE SINGLE WRITER — same observe path as
  ever) → `sleep_pass` (scoped consolidation).
- Delta compile: `_compile` now parses only sequences newer than
  `_counts_up_to` (counts accumulate in `_pair_counts`); the matrix is
  machine-identical to a full reparse — proven in-battery.
- THE LOCAL SLEEP + ENTRY INTERPRETER (2026-07-22, owner's design):
  scoped `_crystallize` compares CRYSTALS TO CRYSTALS, never node to
  node. Each dirty entry is scored against the standing type
  signatures and sorted into the pile it resembles (or the new pile).
  Full crystal matches ABSORB in one subset test; boundary cases
  ("possibly this type plus some factor") close their circle against
  the pile's own members, never the world; misfits crystallize among
  themselves in chunks of `config:crystal-pile` (64). Results
  RECONCILE with the standing registry — absorb matches, supersede
  changed names on the record, add the new, leave the untouched net
  alone (this also fixed the old scoped mode's lossy registry
  rebuild). The chance-null runs on a capped region (80 nodes,
  deterministic slice). Accepted, documented fidelity trade:
  cross-pile pairs surface at the crystal-vs-crystal altitude or a
  later sleep, not this one. `Net` gained a predecessor index
  (`preds`, lazy rebuild for old pickles); closure runs by holder-list
  intersection. Full `crystallize()` keeps from-scratch semantics.
- SPEED DOCTRINE (owner, 2026-07-22): "no more than a few hundred
  nodes or crystals per entry." `config:entry-budget` (300) caps every
  per-entry scan; hub doors are ejected at every altitude (candidate
  gen, negatives, rules, the null); an absorb-only sleep skips the
  chance-null entirely (no new structure — the standing verdicts
  stand); violations contrast only touched nodes. `_recall` reads type
  members from the predecessor index (was a world-scan per token — the
  single biggest fix: lookup 24s → <10ms on a 2.5k-node net).
- FIRST PAST THE POST (owner, 2026-07-22): the interpreter does not
  rank the world — candidates arrive rarest-shared-door-first from
  the signature index and the FIRST one passing the functional gate
  (shared idf-weight ≥ half the crystal's signature weight) is KEPT;
  a gate-failing candidate sharing ≥ min_shared doors piles as a
  boundary case; nothing passing = the new pile, an honest refusal.
  Viability proven in `rebuild/shape_fptp_probe.py` before build:
  ~12 gate checks per entry at 100k crystals (cost FALLS with
  scale), kept-quality median 1.00 vs exhaustive best, pure junk
  refused 100/100. Element modification on later conflict is the
  standing repair (boundary circles + supersession + later sleeps).
  Measured in-engine (battery green throughout): per-message
  interactive 19.1s → 40ms at an 874-node net; 101ms at 2,583;
  281ms at 5,342 (was 1.2s pre-FPTP). Batch sleep for a 24k-token
  single gulp: 55s (one-time; segment-wise sleeping is the named
  next amortization). Earlier shape-tower prototypes (v1/v2,
  `rebuild/shape_viability_probe.py`) FAILED their courts — kept for
  the record; the sig-figs zoom idea remains open research on top of
  the FPTP base.
- Courts in `test_boot` (13 checks): exactness (pipeline vs direct: same
  lookup, `np.array_equal` W), delta-vs-one-shot compile, three nulls
  that must refuse (scrambled flow, payload-less job, circular flow),
  the supersession court (repoint `boot:entry` mid-run, next beat obeys,
  old flow stays whole), and four recovery checks (dangling redirect →
  latest sound chapter; connected chapters broken → unconnected chapter
  found and reconnected; everything broken → rebuilt from the sector
  with wreckage superseded; the sector pristine after its own use).
- v1 honest limits: single-process, workers inline; W dense at
  materialization (sparse is the named next step); the crystallizer's
  scoped-vs-full trade-offs unchanged (the ~800-node knee is its own
  future build).
