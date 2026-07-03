# ISAAC — Current Build State

**The single source of truth for what Isaac can do right now.**
Last savepoint: **2026-07-01**

> **Authoritative engine (2026-07-01):** `isaac_project\code\isaac.py` (project
> root `code\`, NOT `2_the_machine\code\` — that copy is older). Self-test now
> expects **7/7** (waves added).

> **Maintenance rule:** when you add, change, or break a capability, update THIS
> file in the same step. The Manual explains the theory; this doc tracks the
> live state. If a capability isn't listed here with a status, assume it doesn't
> exist. Status tags: **SOLID** (re-run, stands) · **RAN** (executed this
> session) · **PARTIAL** (works with a stated limit) · **OPEN** (not built).

---

## How to run

- Python 3.8+ and NumPy.
- **Canonical home:** `C:\Users\jtwee\Documents\isaac_project\` (the live working
  copy; the `Downloads\New folder (3)` copy + zip history remain there as backup).
  Reorganized 2026-06-24 into four parts — **the code now lives in
  `2_the_machine\code\`** (this doc is in `2_the_machine\docs\`).
- **Windows:** prefix scripts with `PYTHONUTF8=1` (the box-drawing output errors
  on cp1252 otherwise). Not a bug in Isaac.
- Engine self-test: `cd 2_the_machine\code` then `PYTHONUTF8=1 python isaac.py` →
  expect **6/6**.

---

## The his / wired ledger (read this first)

The whole project hinges on the decision/difference running **in him**, not in
the harness around him (Rule 1). The honest split as it stands:

- **His (cognition):** typing, counting, `transduce` state-walk, working memory,
  recognition via `check`, negatives, logic combine (AND/NOT), inventory,
  honest-unknown.
- **Wired retina (allowed — cheap "looking"):** salience (GlobalBaseline),
  connected-components segmentation, bounding-box crop, locating part positions,
  computing displacement signs / neighbor contents.
- **Still harness (the unbuilt frontier):** control flow — loops over cells /
  directions, the survival-fallback structure, cross-frame data association.
  This is the genuine `if`/`while`-over-his-own-state gap.

**Representation direction (2026-06-22):** the world is a fixed alphabet of
meaning-bearing **glyphs** (parts), not pixels — e.g. snake `~~~~~<`. This plays
to his language muscle and around the pixel wall. The pixel→glyph retina is the
one piece deliberately bracketed for later.

---

## Capabilities

### Core engine (pre-session, verified this session)
| capability | status | where |
|---|---|---|
| Language: observe, crystallize, generate, type inference | SOLID | `isaac.py` |
| Math: tables + decompose-when-shrug | SOLID | `isaac.py` |
| Logic: truth tables, compound expr (`logic_eval`) | SOLID | `isaac.py` |
| Reasoning: is_a, capability inheritance w/ negative override, syllogism | SOLID | `isaac.py` |
| Problem solving: forward/backward/gap-fill/multi-step | SOLID | `isaac.py` |
| Persistence: consequence assessment, plan/think/execute | SOLID | `isaac.py` |
| `check` vs `lookup` (validate a claim vs retrieve best) | SOLID | `isaac.py` |
| Self-test | **6/6 RAN** | `python isaac.py` |

### Built / extended this session
| capability | status | where | result |
|---|---|---|---|
| **`transduce`** — universal state-walk; next state = his matmul | SOLID | `isaac.py`, `fst_transduce.py` | COUNT/PARITY/RUN 100% on novel grids |
| **`Scratch`** — working memory (registers/RAM): write/read/incr/append/latch/history | RAN | `isaac.py`, `working_memory.py` | counting in RAM: 2 doors, any N, 100% |
| episode boundaries (per-run trace reset) | RAN | `isaac.py` | trace is per-run, not lifetime |
| **Attention levels** — invisible / background / foreground, tunable floor | RAN | `attention_levels.py` | thorough scan surfaces background |
| Salience retina (per-cell EMA + field-relative) | SOLID | `global_baseline.py` | tracks normal, fades furniture |
| **Attention→Tracker** — salience opens a track, follows w/ identity+motion | PARTIAL | `attention_tracker.py` | works; **merges on contact** (occlusion) |
| **Auto-inventory + honest-unknown** (turtle loop) | RAN | `turtle_inventory.py` | dual unknown (word vs thing); mint → generalize |
| **Parts-alphabet creatures** — roles discovered from position | RAN | `ascii_creatures.py` | body/head/tongue by position; length via RAM |
| **Kindergarten curriculum** — length/facing/direction/in-line | RAN | `curriculum.py` | 100% novel (relative); absolute only 53% |
| **Multi-answer moves** via `check` (cardinal only, no diagonal) | RAN | `snake_moves.py` | check 100% exact-set; lookup 15% |
| **Negatives** — body/wall block a move, checked first | RAN | `snake_policy.py` | 100% never-suicidal, 100% optimal-when-possible |
| **Combine made his** — `(not blocked) and toward` via his gates | RAN | `snake_policy_his.py` | 100%/100%, decision end-to-end his |

### Known limits / open
| item | status | note |
|---|---|---|
| Scale / rotation invariance | OPEN | recognition is exact-bitmap; the recurring wall. Fix = relational/vector identity |
| Data association / occlusion | OPEN | two salient things touching merge into one blob |
| Control flow (`if`/`while` over his state) | OPEN | the loop/fallback structure is still harness |
| Self-directed working memory | OPEN | he's taught what to track/write, doesn't choose yet |
| Predict → surprise (change loop) | OPEN | RAM now holds "before"; loop not built |
| pixel → glyph retina | OPEN (bracketed) | deliberately deferred under the parts-alphabet choice |
| Live glyph-board Snake | OPEN | next buildable: stack runs in motion |

---

## File index (working bundle)
- `isaac.py` — the engine (Net, Isaac, Scratch, World) + self-test
- `fst_transduce.py` — transduce: 3 machines (count/parity/run)
- `working_memory.py` — registers demo (increment/track/associate/replay)
- `global_baseline.py` — salience retina
- `attention_levels.py` — invisible/background/foreground, tunable attention
- `attention_tracker.py` — salience → persistent tracker net
- `turtle_inventory.py` — auto-inventory + honest-unknown
- `ascii_creatures.py` — parts-alphabet, roles from position
- `curriculum.py` — kindergarten spatial questions
- `snake_moves.py` — multi-answer cardinal moves (check vs lookup)
- `snake_policy.py` — negatives + rule-out-then-keep policy
- `snake_policy_his.py` — the combine via his own logic gates
- `ISAAC_Manual.md` — full theory/reference · `ISAAC_BUILD_STATE.md` — this doc

---

## Changelog (savepoints)

### 2026-07-02 — the science-engine day: analogy, memory, persistence, a face

- **Power atoms** (x^k, grid ±{0.5,1,2} + {1.5,-0.5} with refine) →
  **Kepler exact: T = a^1.5, R² 1.0000** from 8 rows. **max_terms=16**
  runaway brake after the sunspot lesson: iid permutation nulls are
  INVALID on autocorrelated targets (20 CPU-hours of proof); block
  permutation = open item #1.
- **Cross-domain** (`rebuild/cross_domain.py`): laws matched by structure
  (log-track exponents = roles) — gravity ≡ coulomb; cooling ≡ capacitor;
  inverse-square role family; family abstraction nodes; **analogy-primed
  transfer**: magnetism n=24, cold 0.82 → primed 0.995 (constant 3.26/3.2).
- **Findings ledger**: record/recall/load (JSONL); negative knowledge kept;
  laws inherited across sessions — dead Isaac's Kepler predicted
  **Pluto 248.0 yr (true 247.9)**, outside training range.
- **Whole-mind save/load/fork** (9KB snapshots; forks diverge safely).
- **UI** (`ui/isaac_ui.py`, stdlib, :8674): converse / discover with
  verdict cards (equation, scope, rivals+probes) / apply laws / findings
  search / mind management. Verified end-to-end incl. Pluto via web form.
- **The Gauntlet** (10 datasets, one pipeline, `rebuild/gauntlet.py`):
  mnist 95.2, smallnorb 87.7, fsdd-audio 92 mixed, covtype arc → 94.4%
  door-weighted exemplars (row-index leakage control: 79%); honest
  refusals on kepler-without-power-atoms and noise; sunspots →
  multi-cycle solar structure (Schwabe/Gleissberg bands + modulation),
  periodogram-corroborated, honestly scoped range-valid.
- Status: **suite 10/10**; both repos pushed; handoff =
  `SESSION_HANDOFF_2026-07-02.md` (owner's four named priorities:
  scale testing, human interaction, information validation, accuracy
  validation/calibration audit).

### 2026-07-01c — DISCOVERY: the challenge loop (the thing that learns things)

- **`discover(X, y, name)`** — given examples of something he cannot do, find
  the rule: staged null-gated term enumeration (candidates grow only around
  admitted terms; admission must beat the max-over-candidates correlation on
  permuted residuals; survivors ARE the equation), validated on a held-out
  half. Four honest verdicts: **UNDERSTOOD** (equation, held-out R² ≥ 0.9) /
  **PARTIAL** (real equation, part explained, stated) / **CAPTURED**
  (nearest-exemplar prediction beats the permuted null — caught, tracked,
  not yet said; no nets) / **NO RULE** (proven nothing at this class).
- **`apply_law(name, X)`** — an UNDERSTOOD law becomes a `law:<name>` node
  (equation in meta, fact indexed); the challenge is computable from then on.
  (Named apply_law — `solve()` was already taken by the token-problem solver;
  collision found the hard way.)
- **Status: RAN — self-test `test_discovery` 5/5, suite 9/9.** Recovered
  `+1.00*x2*x2 -1.00*x3 +1.00*x0*x1` and `+1.00*x0*x1*cos(x2-x3)` EXACTLY
  (held-out R² 1.000, reusable R² 1.000); said NO RULE on noise; CAPTURED
  sin(3·x0·x1) (0.547 vs equation's 0.152) — the four epistemic verdicts,
  live in one method.
- This is the in-engine port of the equation-discovery program (rebuild C /
  equation_discovery scripts). Waves = a sensor; discover() = the learner.
- **2026-07-01d addendum — "only linear / no complex numbers" rumor killed:**
  the solver is linear in COEFFICIENTS over a nonlinear library, and the
  library was enriched with unary transcendentals (sin/cos/exp at a scale
  grid) + a REFINE pass that hill-climbs parameters INSIDE nonlinearities
  (frequency/decay/scale — where regression cannot reach). Complex-number
  structure = damped-oscillation pairs: recovered exp((-a+bi)t)'s real face
  `+1.00*cos(3*t)*exp(-0.4025*t)` with the 0.4 decay OFF-GRID. Single-input
  `0.5x² + 1.5·sin(2x)` recovered exactly (the case that used to degenerate
  to polynomials). Legibility hardening en route: trial-refit lookahead with
  reuse-aware parsimony (a scale-atom must BUY its flexibility; already-paid
  flexibility is free), structurally diverse shortlist (heavy-tailed raw
  variables lose correlation contests to bounded atoms — guarantee simple
  candidates a trial), completion bonus (a trial that finishes the equation
  outranks Taylor-expanding a surrogate term by term). test_discovery 7/7,
  every recovered equation exact and legible.
- **Open:** auto-trigger from shrug (compute/lookup failure → discover);
  symbolic/token challenges (currently numeric); law graduation for CAPTURED
  (function recovery attacking the exemplar memory — audit 2.6/2.8 loop);
  nested compositions f(g(x)) beyond degree-3 products (the deep/dense
  regime) still land in CAPTURED, by design.

### 2026-07-01b — THE GREAT REWIRING: five dormant organs connected

Audit found the engine full of built-but-never-called organs (0 call sites:
recognize_doors, transduce-pattern, predict_next, fit_lens, react...). Five
wiring jobs, zero new mechanisms, self-test now **8/8** (test_tracking added):

1. **The clock is his.** `follow(circle)` + tracked `tick()`: phase register
   and dwell counter live in Scratch; transitions are the circle's own
   `wave_next` doors; evidence comes through `recognize_doors` (partial
   recognition = permanence, the dormant organ, now load-bearing); learned
   dwell (net meta, measured at consolidation) dead-reckons when evidence is
   hidden. Phase 100% correct through occlusion in the self-test.
2. **Statuses are world state.** Registration (expected-vs-observed, each
   tick) opens `world.set_state(entity, "missing X")` after 2-tick persistence
   and clears on sight or when the entity leaves the stage (phase advance —
   absence-by-night opens no status). Isaac now owns a World instance.
   Status doors (miss:X) join the same tick — statuses are doors.
3. **Discovery reaches reasoning.** `_teach_fact` (fact_index + tagged door;
   not teach() — the tokenizer would shred structured names) records part_of,
   phase_of, and blocks facts. The status-explanation pass (ordinary
   co-activation scoped to the entity's phase rows) and the conditional
   rescue both teach `blocks` facts. Self-test: blocks(disk) <- cloud doors
   AND the cloud group node, queryable in fact_index.
4. **Conditional rescue in consolidation** (ported from rebuild E): a door
   exiled by heavy interference re-joins its group when membership is
   re-tested where a candidate blocker is absent — blocker taught as a fact
   in the same move. Needed immediately: the new 1.4x edge margin (which
   stops single-false-edge component bridging) exiles occluded members.
5. **Boxes are gone from the live path.** `fit_lens` default = null-gated
   correlation eigenbasis (the basis must beat chance); `crystallize_features`
   stores observed per-dim log-densities ("doors" meta), `classify_features`
   scores by summed log-likelihood. Legacy box meta still written for
   recognize_matrix/old scripts. Smoke test on diagonal (box-killer) data:
   **99.2% vs old boxes ~88%.**

Backup: `code\backups\isaac_pre-wiring_2026-07-01.py`. Caveat: clock ticks
are sensory ticks — mixing unrelated observe() streams into a followed
episode dead-reckons the clock; keep one stream per episode.

### 2026-07-01 — WAVES: temporal crystallization wired into the engine

- **What:** the static crystallizer is order-blind (compares door profiles).
  New idle-mode pass `wave_consolidate()` watches the whole matrix MOVE:
  co-activation **groups** (simultaneous activation as a first-class thing),
  **handoff edges** (one group dims as another lights — prior-frame vs
  later-frame registration), **circles** (waves that return to their start),
  and one level of recursion (circle activity becomes a door; same machinery
  → patterns of patterns, circles of circles).
- **Sensing:** `tick(active)` records one instant of simultaneous activation.
  `observe()` ticks each token with its type doors; the think loop ticks each
  context; `transduce`/`react` inherit via lookup. Any retina/game loop can
  call `tick()` directly. Log lives in `activation_log`.
- **Discoveries enter the net** as nodes (`wave:sun_light[2]`,
  `circle:dark>light>tools`) with tags `wave` / `wave_next` — composable
  upward like anything else.
- **Null discipline (the key method):** every admission beats a **jitter
  null** (±2–5-step shifts: keeps each door's own rhythm, breaks precise
  co-timing; jitter ONE side per pair). A full circular shift is the WRONG
  null for periodic waves — it relands in phase, making real simultaneity
  unbeatable. Handoffs must beat 1.5× the null's max.
- **Status: RAN** — self-test `test_waves` 4/4 (groups exact incl. zero noise
  doors; both planted circles; circles present as net nodes; shuffled-time
  control: groups survive, ALL movement dies). Full suite **7/7**.
- **Reference implementation + planted-truth harness:**
  `isaac_project\rebuild\wave_crystallizer.py` (5/5) and
  `rebuild\RESULTS.md` (Rebuild D) — includes the two generator lessons
  (fixed-length eras clock-lock to waves; global-clock processes are
  genuinely phase-locked — independent waves need independent phases).
- **Backup:** `code\backups\isaac_pre-wave_2026-07-01.py`.
- **Open:** feed a REAL stream (his own activation log during long tasks;
  a glyph-retina game session); wave concepts as parts for uptake-edge
  composition (rebuild B) — circles that consume each other's affordances.

### 2026-06-22 — perception/decision stack, his way
Added `transduce` (state-walk) and `Scratch` (working memory) to the engine.
Built the glyph-world line: salience attention with invisible/background/
foreground levels, salience→tracker, auto-inventory with honest-unknown, the
parts-alphabet representation (direction decision), a kindergarten spatial
curriculum that generalizes (relative » absolute), multi-answer moves via
`check`, taught **negatives** (body/wall block), and moved the final boolean
**combine into his own AND/NOT gates** — making the Snake move decision
end-to-end his. Engine still 6/6.

### 2026-06-22 — neural transplant: boxes as concepts in the net
Added `fit_lens`/`apply_lens` (the aligner = a swappable `lens:<name>` net node:
wired lift + strip-DC + Fisher dim-select now, replaceable by a learned aligner
later, same interface) and `crystallize_features`/`classify_features` (a trained
net's activations → per-class box concepts as `concept:<label>` net nodes with
`[lo,hi,med]` meta, scored by his membership+centroid). Boxes ARE Isaac's
per-container dims — they coexist with his language/math in one net. Verified
on digits (0.90, boxes + language together). Subproject lives in
`neural_transplant/` (range classifier, GPU sweep harness, decode demos).

### 2026-06-24 — contrast crystallizer (two interpretations + his comparator) — REVERTED
**ROLLED BACK 2026-06-24 (session 2, user request): `crystallize_contrast`/
`classify_contrast` were REMOVED from `isaac.py`; the engine is back to its
pre-session state (self-test 6/6). The entry below is kept as a record of what
was tried; the methods no longer exist in the code.**
~~Added `crystallize_contrast`/`classify_contrast` (RAN): user's design — keep TWO
interpretations per quantized cell, reinforced by the two label-streams; run HIS
`compare()` to null the shared and crystallize the RESIDUAL (the difference/bump),
not a per-class box. Decide by the residual. order=2 = compound cells (binding).
On HIGGS (the box-killer, hard tabular): box 0.525 (chance) → contrast 0.620
(≈ logistic), his way. FINDING: literal set-`compare()` = 0.465 (below chance);
the MAGNITUDE of the difference is the signal, so the soft log-contrast is needed
(his comparator needs "how different", not just same/different on continuous data).
Ceiling = logistic (first-order); order-2 barely moved (high-order still out of
reach via fixed pairwise). Engine 6/6 intact; contrast is a node beside language.~~

KEY FINDING: crystal quality is governed by box-geometry (axis-aligned blobs =
"box-friendly", e.g. digits ~99% retention; diagonally-interleaved =
"box-hostile", e.g. covtype caps ~0.62). The valuable lever is the ALIGNMENT
(un-superposition) front-end, now a swappable net node. Engine still 6/6.

### 2026-06-23 — binding / conditional computation (the "critical missing piece")
Diagnosed the recurring gap (polysemy muddle + box-hostility + old fraud Naive-
Bayes limit) as ONE missing primitive: condition the answer on a COMBINATION, not
independent parts. Fixed on both faces. NODE face: `crystallize_senses(node)` +
`route(node, incoming)` added to engine — clusters a node's doors into explicit
sense-sections by within-node context co-occurrence (the crystallizer turned
inward), stored on the node, and routes output by which sense the input matches.
Polysemy ("bank") now disambiguates node-locally + legibly. BOX face: compound/
interaction doors (centered pairwise products) — XOR goes 0.48 (chance, flat
boxes can't bind) → 0.89. Confirms the manual's compound-doors prediction. Both
are mechanism-proofs on toy/clean data; engine 6/6. NEXT real retest: fold
compound doors into the crystal pipeline on covtype (measured 0.62 box ceiling)
to see if binding breaks box-hostility at scale. Demos: `neural_transplant/
interaction_retest.py`; node router in `isaac.py`.

### 2026-06-23 — covtype binding retest: NULL (important finding)
Ran pairwise interaction/compound doors into the box pipeline on covtype
(`neural_transplant/binding_covtype.py`). Result: did NOT break the ceiling —
flat 0.48, +variants 0.54, +all-interactions 0.53, Fisher-selected-interactions
0.47 (WORSE), interactions+variants 0.55. RF 0.83. So pairwise binding does
nothing for covtype. WHY: XOR is a clean low-order interaction (binding nails it,
0.48→0.89); covtype is HIGH-ORDER/distributed/adaptive (RF wins via deep
recursive conditional splits, which fixed pairwise products can't reach). Sub-
finding: Fisher-selecting interactions HURT — you can't pick good interaction-
features with an independence criterion, because which interactions matter is
itself an interaction problem. CONCLUSION (corrects earlier overclaim): compound
doors fix clean, low-order, identifiable interactions (polysemy, XOR); they do
NOT substitute for representation-learning on deeply box-hostile data. Covtype's
ceiling is a REPRESENTATION problem (the registration/lens lever), not a missing-
interaction problem. Reinforces the session thesis: representation is the deep
lever; binding is a local patch.

### 2026-06-23 — covtype is SPATIAL-LEAKAGE-dominated (recontextualizes everything)
Researcher's theory, confirmed empirically: covtype's high accuracy is largely
spatial autocorrelation / lookup, not learned ecology. The 54 features act as a
location fingerprint; cover type is spatially autocorrelated; a RANDOM split
leaks (test cells' neighbors are in train). Tests: (1) kNN(k=1) random split =
0.855 ≈ RF 0.881 — a pure nearest-neighbor LOOKUP nearly matches RF, so the task
is proximity-dominated; (2) hold out a whole wilderness AREA (no neighbors to
look up) → RF collapses 0.88→~0.5-0.6 (area3 0.23, partly distribution shift).
IMPLICATION: the box→RF "gap" (0.69→0.95) is LEAKAGE RF exploits and boxes don't,
NOT deep ecology boxes can't learn — which is why the binding fix did nothing
(no real interaction to capture; just a map to memorize). The box family's ~0.69
was REFUSING to memorize the map = closer to the honest transferable signal
(~0.5-0.7) = aligned with "learn the truth not the consensus." Confirms the
researcher's own boundary-vs-occupancy finding (terrain=feasible set/transferable;
species=contingent/spatial=the leaked part). DO NOT use covtype to evaluate
honest learning — it rewards leakage; use leakage-free data or spatial CV.

### 2026-06-23 — VISION CRYSTAL + ROTATION LENS: registration thesis CONFIRMED on real data
Crystallized a frozen ResNet18's 512-d final embedding on CIFAR-10
(`neural_transplant/vision_crystal.py`, `vision_lens.py`). Encoder makes the rep
FAR more box-friendly than pixels: crystal on raw pixels 0.23 → crystal on
embedding 0.71 (linear probe 0.84, kNN 0.81). The 0.71-vs-0.84 gap = axis-aligned
boxes vs oblique linear boundaries. THEN the key result: a ROTATION LENS (LDA =
learned aligner) closes the ENTIRE gap — crystal after LDA rotation = 0.834 ≈
linear 0.839. So the cheap legible box reader MATCHES the linear head once you
ALIGN first. Registration is the lever, proven on real images. Corollary: variants
HURT after alignment (0.75 < 0.834) — good alignment makes the simplest box win
(max legibility). Validates the swappable-lens design (wired Fisher weak; learned
rotation strong → replace lens contents with a learned rotation). Honest product:
frozen encoder + cheap closed-form rotation + box crystal = legible + abstaining +
accuracy-matching head, no gradient training; but rides on the encoder (no encoder
compression) and LDA is LINEAR (deep nonlinear hostility needs nonlinear registration).
