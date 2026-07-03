# THE ISAAC MANUAL
### The complete, current capability reference — every part, every method, honestly scoped
**Engine:** `code/isaac.py` (one file, one class, numpy only, no neural nets in any decision path)
**Self-test:** `PYTHONIOENCODING=utf-8 python isaac.py` → expect **10/10**
**UI:** `python ui/isaac_ui.py` → http://127.0.0.1:8674

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

- Engine self-test (10 areas): language, math, logic, reasoning, decompose,
  persistence, waves, tracking, discovery, rivalry.
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
