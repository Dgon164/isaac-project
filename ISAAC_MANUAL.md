# THE ISAAC MANUAL
**Version 0.1.2 alpha 1 — rewritten in plain engineering language 2026-08-20.**
The previous manual survives in git history. Maintenance rule unchanged: when a
capability is added, changed, or broken, update this file in the same commit.
If it isn't documented here, assume it doesn't exist.

- **Engine:** `code/isaac.py` — one file, one main class, Python + numpy only.
  No neural networks anywhere in a decision path. `__version__ = "0.1.2-alpha1"`.
- **Self-test:** `python code/isaac.py` → expect **15/15 capability areas**.
- **UI:** `python ui/isaac_workspace.py` → http://127.0.0.1:8675
  (⚠ on the desktop machine, do NOT launch the workspace until the migration
  work is done — on import it loads and auto-saves the live mind file from
  `../isaac-life/`). Legacy single-panel UI: `ui/isaac_ui.py` → :8674.

---

## 1. What Isaac is

A symbolic learning system. Everything he knows lives in two inspectable
stores: a **graph database** (nodes and tagged directed edges) and a
**prediction matrix** compiled from his observations. He learns by being shown
token sequences (sentences, equations, tables); he answers by matrix lookup,
graph walking, and — new this week — step-by-step expression reduction. Every
answer is traceable to stored evidence, wrong answers are kept on record with
their corrections, and "no answer" is a first-class honest output. Design
rules: no information is hard-coded into him (only machinery); anything
learned can be superseded by better evidence but never silently deleted.

## 2. Quick start

```python
import sys; sys.path.insert(0, "code")
from isaac import Isaac, tokenize

m = Isaac()
m.observe(tokenize("a florb is an animal ."))     # teach by showing
m.observe(tokenize("3 + 4 = 7"))
m.consolidate()                                   # batch index/type build
m.lookup(["a", "florb", "is", "an"])              # -> ("animal", conf)
m.lookup_topk(["3", "+", "4", "="], k=3)          # -> ["7", ...] ranked
m.teach("*", "precedes", "+")                     # order of operations, taught
m.lookup(tokenize("2 + 3 * 4 ="))                 # -> ("14", conf) via reducer
m.save("mind.isaac"); m2 = Isaac.load("mind.isaac")
```

## 3. The parts (data structures)

| structure | what it holds | key operations |
|---|---|---|
| `Net` | THE knowledge store: nodes (strings) + directed edges ("doors") with tags + per-node metadata + edge observation counts | `add_door`, `get_doors`, `get_predecessors`, `get_full_profile`, `set_meta/get_meta` |
| prediction matrix | compiled from observed sequences: rows = possible next tokens, columns = context patterns ("frames"), cells = normalized counts | built by `_compile`, used by every lookup |
| `Scratch` | working memory: named registers with history (used by state tracking, dialog window) | `write/read/incr/append/history` |
| `fact_index` | (subject, relation) → [objects] — explicit facts, incl. taught operator precedence | `teach(s, r, o)`, `teach_not` |
| types | groups discovered by shared edges (formal-concept-analysis style); types are themselves nodes | `consolidate()`, `crystallize()` |
| `World` | mutable entity states + taught actions | `set_state`, `teach_action`, `execute` |
| findings ledger | JSON-lines science log: every discovered law, verdict, confirmation, overturn | `record_finding`, `recall_findings`, `load_ledger` |
| `feedback_log` / `feedback_adjust` | every good/marginal/bad grade ever given + ranking adjustments | `feedback`, `feedback_connection` |
| `activation_log` | the event history (his diary); 2/3 of file size, compressed in storage | appended by `tick` |

## 4. How learning works

1. **`observe(tokens)`** — stores the sequence, adds sequential edges to the
   graph, marks the affected region dirty. ~49,000 facts/sec measured.
   Variants: `observe_negative` (wrong examples → lockouts),
   `observe_matrix` (each row of a 2D table as a sequence), `observe_frame`,
   `observe_tagged`.
2. **Matrix compile (`_compile`)** — turns observed sequences into the
   prediction matrix. Incremental: only sequences newer than the last compile
   are parsed. **Fixed 2026-08-19: every position in a sequence is a training
   example.** (The old code used only the final token, so punctuated
   sentences taught almost nothing — this bug invalidated all pre-fix
   language scores. A fact stated once is now retrievable; ten repetitions
   failed before.) Old save files auto-rebuild their count caches.
3. **`consolidate()` / `crystallize()`** — batch step ("sleep"): groups nodes
   with shared edge profiles into types, reconciles with existing types
   (absorb / supersede / add). Known limits: groups cannot overlap (shared
   attributes merge groups); batch time grows superlinearly with size — see
   §10.
4. **`teach(subject, relation, object)`** — an explicit fact: observed as a
   sentence AND indexed for direct query. Used for is-a facts and for
   operator precedence (`teach("*", "precedes", "+")`).
5. **Time-series learning** — `tick(active_set)` feeds simultaneous
   activation; `wave_consolidate()` discovers co-firing groups, handoffs,
   repeating cycles, and expectation-failure statuses. (Details unchanged
   from July; see git history of this manual for the full envelope numbers.)

## 5. How answering works

`lookup(context)` runs this pipeline, in order:

1. **Multi-step routing (2026-08-20):** if the question ends with `=` and
   contains two or more operators, or parentheses → the **expression
   reducer** (§6). Prevents the measured failure where multi-step questions
   got wrong answers from partial pattern matches (was 87/100 wrong).
2. **Never-seen-word guard (2026-08-19):** if any context token was never
   observed, return no answer. (Without this, generalized patterns would
   answer questions about words he's never seen.)
3. **The think loop:** recall (what do I know about these tokens) → route
   (one matrix multiply over the compiled matrix; best-scoring next token)
   → evaluate (confidence check; retry strategies: drop unknown tokens,
   substitute type members). Returns `(answer, confidence)`; below the
   confidence threshold returns `(None, conf)`.

**The selection API (owner spec 2026-08-20 — ranked lists, order only):**
- `lookup_topk(context, k)` → list of candidates, best to least. No numbers
  attached (pass `scores=True` in a test harness to see them).
- `complete_topk(context, k, max_len)` → ranked multi-word completions
  (beam search; a completion ends at "." or the length cap).
- `cloze_topk(left, right, k)` → fill-in-the-blank at ANY position:
  end = ranked lookup; middle = candidates re-ranked by whether the
  right-hand context actually follows them; beginning = ranked sentence
  starters.
- `feedback(context, candidate, "good"|"marginal"|"bad")` — good boosts that
  answer's future rank AND stores question+answer as a real observation;
  bad suppresses ×0.1 (penalty, not a ban); marginal is logged only.
- `feedback_connection(src, tgt, grade)` — same grading for suggested graph
  edges: good adds the edge, bad adds a lockout.
- All grades append to `feedback_log`; everything persists through save/load.
- Current limitation: a grade applies only to the exact question it was
  given on (no generalization to similar questions yet).

**Other query paths:**
- `check(context, target)` — "is THIS the answer?" — reads one matrix cell.
- `evaluate(tokens)` — the reducer directly; returns `(answer, confidence,
  steps)` where steps is the worked derivation.
- `solve("3 + ? = 7")` — single unknown, forward/backward/gap-fill.
- `solve_steps([...])` — a list of steps resolved in order with `$0, $1`
  references to earlier results (caller supplies the steps).
- `compute(a, op, b)` — arithmetic with fallback: direct recall, else
  decompose into known sub-facts, verify, memorize the result.
- `transduce(start, stream)` — state-machine walk: next state =
  `lookup([state, symbol])`. Counting, parity, tracking reuse this.
- `generate(concept)` — produce a sentence by walking learned transitions.
  Known bug: can mix attributes of similar items (see §10).
- `infer(a, b)` — type-based transfer ("florb can fly? — via grinth").
- Reasoning layer: `reason_chain`, `is_a_check`, `can_check`,
  `containment_check`, `property_check`, `syllogism` — reads facts + type
  edges.
- `discover(X, y)` — the numeric law engine: given a data table, searches
  readable equation forms, validates on a held-out half, reports verdict
  UNDERSTOOD / PARTIAL / CAPTURED / NO RULE with the equation, its valid
  range, and surviving rival forms with the experiment that would decide
  them. `confirm()` retires or overturns on new evidence; `apply_law()`
  reuses a law as computation. (0/40 false discoveries across batteries;
  Kepler-from-8-planets predicted Pluto at 248.0 vs true 247.9.)

## 6. The expression reducer (owner design 2026-08-20)

Multi-step math and logic are evaluated the way you'd hand-trace them:
organize into pairs, resolve one pair at a time, carry interim results.

- **One pair at a time:** the highest-precedence operator's pair is answered
  through the learned matrix (`lookup([a, op, b, "="])`); the result replaces
  the pair; repeat until one value remains.
- **Order of operations is TAUGHT, not built in:** the reducer consults
  `fact_index` for `X precedes Y` facts. Untaught pairs resolve left to
  right.
- **Parentheses = subsections,** innermost first.
- **A pair only counts if the exact fact is in the matrix** (or derivable by
  `compute`'s decompose road for + * −). Partial pattern matches are
  rejected — that rule took the junk-expression wrong-answer rate from
  50/100 to 0/100.
- **Interim state is tracked:** `evaluate()` returns the step list — a
  worked derivation, including the failing step when it refuses.
- Derived pair results are memorized as observations, so worked problems
  become matrix entries.
- Limitation: binary operators only ("not" is unary — not yet routed).

Measured (rebuild/pemdas_eval_test.py): 200/200 three-operand additions,
200/200 mixed precedence (zero left-to-right errors), 200/200 parenthesized,
16/16 exhaustive and/or chains, 100/100 honest refusals on expressions with
an unanswerable step.

## 7. Files on disk

- **Save format v2 (2026-08-19), one file:** header + sections — core (the
  object graph), netgraph (every node name stored once; edges as integer
  arrays), history (the event log, compressed) — plus an append-only journal
  tail (`Isaac.journal_append`) so autosaves append instead of rewriting;
  a torn tail is detected by checksum and skipped. Measured on a real
  49.4MB v1 mind: **2.9MB (17× smaller), save 1.6s, load 1.0s**, every data
  structure verified equal after round trip. v1 pickle files load forever
  (format detected by magic bytes). `fork()` deep-copies a mind for
  what-if experiments.
- **Findings ledger** (`data/findings.jsonl` in the UI): one JSON line per
  discovery/confirmation/overturn. The snapshot preserves a mind; the
  ledger preserves knowledge.
- **Telemetry** (`data/telemetry.jsonl`): one line per event (timestamp,
  event, ms, node count).

## 8. The background processing system

- **Job pipeline:** `ingest(content)` → job node → split into segments →
  each segment processed in a disposable scratch mind (parallel worker
  processes if `config:workers` > 1) → assessed against the net → merged →
  committed by a single writer → scoped consolidation. All queue/config
  state lives in the graph itself.
- **Two lanes:** interactive replies take priority (8ms median message
  latency measured while a 9.6k-token document processed in the
  background); bulk work advances in bounded slices (`work_quantum`).
- **Boot flows:** the processing steps themselves are stored in the graph
  as flow nodes — inspectable, supersedable, with a pristine recovery copy
  and a 4-stage fallback chain if flows are damaged. Only the entry point
  is hard-coded.
- **The workspace** (`ui/isaac_workspace.py`): three channels — /file
  (inputs, read-only to him), /in + /say (conversation, append-only), and
  /findings (his output). Auto-saves the standing mind every 2 minutes.
  Nothing generates words on his behalf; silence is an honest answer.

## 9. Current measured state (2026-08-19/20, this machine: 14900K/48GB/3090)

**Fresh-mind baseline** (`rebuild/worstcase_baseline.py` — invented words,
so nothing is recall from anywhere):
language generate 3/3, completion 3/3, unknown-word refusal ✓; math 6/6
with 2/2 honest refusals beyond the tables; discovery 2/2 planted laws
exact + noise correctly refused; memory 3/3 through save/load death.

**Full-coverage scale test** (`rebuild/scale_eval.py`): 1,198 generated
facts (tables 0-19, comparisons, logic), one pass — **100.0% on all 1,198**;
honesty: 200/200 out-of-range questions refused, 0 wrong; multi-step:
**100/100** three-operand problems (13/100 before the reducer, with 87
wrong answers).

**Real exams** (`rebuild/cloth_run.py` — CMU CLOTH, real middle-school
cloze exams, 4 options, chance = 25%): 120 passages, 1,108 questions,
taught as plain unmodified passages, one pass each:

| batch | baseline (control) | after class | batch-1 retention |
|---|---|---|---|
| 1 | 30% | **92%** | 92% |
| 2 | 35% | **91%** | 91% |
| 3 | 31% | 80% | 92% |
| 4 | 31% | 86% | 91% |
| 5 | 26% | 88% | 89% |
| 6 | 23% | 88% | 90% |

**Whole-course final exam: 944/1,108 = 85%** — every question from all six
batches re-tested after the full course, so this includes retention across
the entire run (1,148s total, 7,346 nodes, 4,518 types).

July comparison: plain teaching scored 40% then (the compile bug discarded
sentence content); reaching 89% required reformatting all material into
fragments at 8× the data volume. Plain teaching now scores 85-92%.

**Speeds:** 49,000 facts/sec ingest; ~5,000-9,000 questions/sec at small
scale; interactive replies 40ms at 874 nodes / 281ms at 5,342 nodes.
**The measured scale problem:** per-batch processing time in the exam run
grew 5s → 26 → 68 → 127 → 199 → 299s (superlinear consolidation), and the
dense matrix reached 2,554 × 82,169 (~210M cells) at just 120 passages.
Sparse matrix storage + consolidation algorithm work are the named fixes.

## 10. Known bugs and missing features (honest list)

1. **No general working space.** The design Isaac was meant to have — take
   incoming information, organize it into a structured working table
   (formal-concept-analysis style), then resolve row by row toward a final
   answer — does not exist in this engine. Fragments exist: `observe_matrix`
   (table intake), `solve_steps` (row-by-row resolution, but caller supplies
   the rows), `Scratch` (registers), and the expression reducer (a working
   special case for math/logic only). Top architecture gap. The June-era
   engine (`Documents/isaac_project`) may hold the original design.
2. **No general inference/chaining** outside expressions: he cannot combine
   two known facts to answer a novel question (knows three=3 and 3+4=7;
   cannot answer "three plus four" unless taught in words — measured 0/12).
   The planned fix is bidirectional search through the graph (design doc:
   dc/docs/DESIGN_SEED_STRUCTURES_2026-08-19.md).
3. **Partial-match wrong answers** remain possible on the general
   single-answer path (a fragment of the question can match a common
   pattern). Fixed inside the reducer via the exact-pair rule; the general
   confidence rule (score tied to how much of the question matched) is not
   built. `check()` and `predict_next()` also lack the never-seen-word
   guard.
4. **The generator can mix up similar items' attributes** (said "the grinth
   eats moss" — grinths eat seeds; florbs eat moss). It follows
   category-level statistics, not per-item facts.
5. **Scale:** superlinear consolidation time and dense-matrix memory growth
   (numbers in §9). More hardware does not fix it (measured on both
   machines); it's algorithmic work.
6. **Feedback doesn't generalize** past the exact question graded, and the
   boost/penalty constants (×2.5 / ×0.1) are first-pass hard-codes.
7. **Language dose economics unmeasured post-fix** — how much repetition and
   what delivery format real prose needs is being re-established (July
   numbers were measured through the compile bug).
8. Older known limits still true: `classify_features` never abstains;
   type groups cannot overlap; no curiosity loop (challenges arrive from
   outside).

## 11. Test suites (all under `rebuild/`, run with `python <file>`)

| file | what it proves |
|---|---|
| `code/isaac.py` itself | 15-area engine self-test (regression gate for every change) |
| `worstcase_baseline.py` | fresh-mind floor: what day zero can do; rerun after every engine change |
| `scale_eval.py` | full-coverage recall, honesty, and multi-step at scale + throughput numbers |
| `pemdas_eval_test.py` | expression reducer: precedence, parentheses, logic chains, refusals |
| `selection_feedback_test.py` | ranked selection API + feedback channel (17 checks) |
| `cloth_run.py [n]` | real exams: baseline control → teach → exam → retention |
| `onefile_probe.py` / `onefile_install_court.py` | v2 file format: round-trip equality, crash recovery, journal |
| `discovery_battery.py`, `redteam_discovery.py`, `wave_battery.py`, `gauntlet.py` | law-discovery correctness, adversarial cases, time-series, 10 real datasets |

## 12. Version history (short)

- **June 2026** — original engine (`Documents/isaac_project`): equation
  discovery, closure theory, the working-space design era.
- **July 2026** — canonical rebuild (this repo): boot flows, job pipeline,
  two lanes, idea nodes, workspace; the study era (real-exam attempts);
  measured wounds: retrieval strong / selection weak.
- **2026-08-19 — v0.1.2 alpha 1:** one-file save format v2 (17× smaller,
  journal appends, v1 loads forever); compile bug fixed (every position
  trains — invalidated all prior language scores in his favor);
  never-seen-word guard.
- **2026-08-20:** ranked selection API (order only) + good/marginal/bad
  feedback channel; expression reducer with taught precedence; multi-step
  routing; exact-pair honesty rule; CLOTH re-run at 88-92% vs 25% chance.
