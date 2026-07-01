# ISAAC — Theory of Operation

*How the engine actually works, mechanism by mechanism, and why each mechanism
is what it is. This is the "how it operates" doc — distinct from `ISAAC_Manual.md`
(full theory/API) and `ISAAC_BUILD_STATE.md` (live capability ledger). Accurate to
`isaac.py` as of 2026-06-24 (self-test 6/6).*

---

## 0. The one-sentence model

Isaac is a learning system built from **two primitives** — *differentiation*
(comparison: same / different / doesn't-matter) and *memory recursion* (keep what
recurs, then compare again on your own output). Knowledge is **doors** (directed,
tagged edges) between **nodes** (tokens) in a graph called the **Net**. The Net
compiles into a legible weight **Matrix** for fast inference. There are no trained
weights, no gradients, no backprop. The world differentiates itself; Isaac keeps
the stable residue.

---

## 1. The substrate — the Net (`class Net`)

The only data structure. A directed graph with three parts:
- `doors: node → {targets}` — a door `A→B` means *"I have witnessed A lead to B."*
- `door_tags: (A,B) → {tags}` — what *kind* of connection: `seq` (sequence),
  `neg` (negative example), `type` (discovered category), `lockout` (only-in-negatives),
  `lens`, `crystal`, etc.
- `meta: node → {key:value}` — arbitrary per-node data (`start`, `initiator_strength`,
  `box`, `label`, `senses`, lens `transform`, …).

Properties that matter:
- **A node has no internal content.** Its meaning *is* its connection profile —
  what precedes it, what follows it, in which tags. (`get_full_profile`.) "Meaning
  is overlap of feature-sets" made literal.
- **Add-only.** Doors are added, never removed. The Net is an append-only event
  log of witnessed structure — permanent, "infinite half-life."

## 2. The primitive — `compare()` and memory recursion

`compare(set_a, set_b)` returns `{shared, only_a, only_b, similarity}`. This is the
single cognitive operation: tell this from that. The third value (**doesn't-matter**
/ the shared) is first-class — and it turns out to be the load-bearing one (see §13).
Memory recursion = keep what recurs (consolidation), then run the same comparison
on the result one level up. Differentiation makes the parts; memory recursion
composes the wholes; each whole is a part of the next, scale-free (the **holon**).

## 3. The three memories

| memory | what it holds | form |
|---|---|---|
| **Net** (graph) | permanent witnessed structure ("what's true in general") | add-only doors |
| **Matrix** (numpy) | the Net compiled for fast inference | frame→delta weights |
| **Scratch** (`class Scratch`) | working memory / RAM ("now / this run") | overwritable registers |

The Net and Matrix are the same information in two forms (the compile step). Scratch
is the *other* kind — mutable, episodic; see §8.

## 4. Data flow — observe → consolidate → compile → route

1. **`observe(tokens)`** — the front door. Creates `seq` doors between adjacent
   tokens, stores the raw sequence (Rule 5: store raw, derive later), marks dirty,
   and immediately slots new tokens into existing types (`_sense`, Stage-1 sensing).
   `observe_negative` uses the `neg` tag; `teach` also indexes a fact; `observe_matrix`
   /`observe_frame` feed 2D data row-by-row.
2. **`consolidate` / `crystallize` (`_crystallize`)** — structure discovery. FCA
   closure over door profiles: group nodes that share predecessors/successors into
   **types**, merge overlapping types, write `type` doors, build hierarchy, discover
   co-occurrence rules, and turn neg-only patterns into **lockouts**
   (`_discover_violations`). This is "Isaac 2 — the Crystallizer": slow, deliberate.
3. **`compile` (`_compile`)** — turn the raw observed sequences into the Matrix.
   Each sequence → a **frame** (all-but-last token) → **delta** (last token), plus
   trailing partial frames at lower weight. The Matrix `W` has one row per delta,
   one column per frame; columns normalized to a distribution.
4. **`_route` / `_encode`** — inference. `_encode(context)` builds an input vector
   (full frame at weight 16, partial frames at width-weight, **type-level
   activation** spreads to type members). `_route` does the matmul `y = W_norm @ x`.

## 5. The two query modes — `lookup` vs `check` (the reasoning unlock)

Both route through `_think`, but read the output vector `y` differently:
- **`lookup(context)`** — argmax of `y`. *"What comes next?"* Retrieval. (Confidence
  > 1.0 = known; < 1.0 = a **shrug**, honest "I don't know.")
- **`check(context, target)`** — read the *specific cell* for `target`. *"Is THIS
  claim true?"* Validation.

This distinction is the single most consequential thing in the engine. Recognition
is `lookup`; **reasoning is `check`** — because multi-valued relations ("can a bird
sing?" when "fly" scores higher) are invisible to argmax but readable by `check`.
Negative-first reasoning (`can_check`) checks `[subject,"cannot"]` before the
positive — the override mechanism.

## 6. The think loop (`_think`)

Not a single matmul — a small governed loop: **recall → process → evaluate →
retry**. `_recall` flags known vs unknown context tokens; `_route` produces an
answer + confidence; `_evaluate` diagnoses *why* a shrug happened (which tokens
were unknown, whether real information exists for this context); feedback drives an
*informed* retry (e.g. type-substitution only when there's genuinely zero info, not
when a real answer exists). The governor exits on confidence or `max_cycles`.

## 7. Frames & contextual meaning (how disambiguation works)

The Matrix keys on the **frame** (the context window), not single tokens. So the
same node means different things in different frames: `(money,bank)→lends` vs
`(river,bank)→overflowed` are distinct columns; `lookup([bank])` alone correctly
**shrugs** (genuinely ambiguous). Meaning lives in the relation, not the symbol —
which is why disambiguation falls out for free *and* honest-unknown comes with it.
(`crystallize_senses`/`route`, §10, make these senses explicit *on the node*.)

## 8. Working memory — `Scratch` (the mutable half)

Registers Isaac writes/reads/updates in real time: `write` (overwrite, supersede),
`read`, `incr` (count=count+1), `append` (build a list / chain), `latch` (sticky
"has it ever"), `history` (the step-trace, replayable to find where a computation
went wrong), `snapshot`, `clear` (episode boundary). The door-net is permanent
knowledge; Scratch is *now*. State a process needs (a tally, a note, a tracked
thing) lives here.

## 9. The sequential layer — transduce / react / walk

- **`transduce(start, stream)`** — the universal state-walk (finite-state
  transducer / Turing head). At each step the next state = his matmul
  `lookup([state, symbol])`; state lives in Scratch (`into`). The control loop is
  the tape-reader; the *program* is learned doors. Counting, parity, run-detection
  are all one machine differing only in doors.
- **`react(stream, target)`** — net-driven ops on RAM: his matrix says what to DO
  (`lookup([symbol]) → op`), a tiny ALU (`_apply_op`) applies it to a register.
  Counting to any N with two doors (the magnitude lives in RAM, not as N nodes).
- **`walk_chain` / `generate`** — follow doors forward / trace an initiator then
  walk; `predict_next` is convergence-voting (for language, not math).

## 10. Structure discovery, turned inward — sense routing

`crystallize_senses(node)` runs the *crystallizer's own clustering on a single
node's doors*: cluster the node's occurrences by shared context → **sense-sections**
(each with its own in-doors/out-doors), stored in the node's meta. `route(node,
incoming)` then conditions output on which sense the input matches — an **internal
node router** (binding / conditional computation at the node level). This is the
holon one rung down: the same comparison operation aimed at one node's connections.

## 11. The reasoning / compute / persistence layers (built on §1–7)

- **Reasoning:** `reason_chain` (matmul hops along a relation), `is_a_check`,
  `can_check` (negative→direct→inherited), `containment_check`, `property_check`,
  `syllogism`. Each hop is one `check`/`lookup`.
- **Compute:** `compute` = the growth cycle — try `lookup`; on shrug, **decompose**
  (place-value, `digits_of`, `_decompose_multiply/add`); cross-check; **memorize**
  the result (new door → next time it's recall). Re-derives Common-Core
  "memorize + decompose-when-shrug."
- **Problem solving:** `solve` (forward / backward / gap-fill), `solve_steps`.
- **Persistence / action:** `assess` (consequence patterns: net_positive/negative/
  zero), `plan_think_execute`, and the `World` (mutable external state, taught
  actions with preconditions/effects, `execute`).

## 12. The transplant layer — boxes & lens (net extractor, in-engine)

A trained net's representation can be crystallized into Isaac concepts *in the same
net*. `fit_lens` registers an **aligner** as a `lens:<name>` node (the
swappable Stage-2 transform); `crystallize_features` writes per-class **box
concepts** (`concept:<label>` nodes with `[lo,hi,med]` meta); `classify_features`
scores by his membership (count in-range) + centroid (median distance). A box *is*
Isaac's per-container-dims concept. Full theory: `NET_EXTRACTOR_THEORY_OF_OPERATION.md`.

## 13. Why it works (the theory under the mechanism)

- **Intellon (completeness):** distinguish + store + repeat is the definition of a
  Turing machine. Differentiation, iterated and composed (NAND-complete), is a
  universal substrate. The only non-trivial part is *identification/integration*,
  not the computation.
- **Information self-organizes (the entropic filter):** structure is an objective
  property of relationships, imprinted by whatever process generated the data. The
  crystallizer doesn't sculpt structure — it lets the entropic churn of comparison
  run and **keeps what survived** (memory recursion). Learning is negentropy
  accumulation: keep what's stable / expensive-to-erase. This is why it's holonic —
  one filter applied at every scale, each level's stable residue becoming the next
  level's parts.
- **Comparison is registration:** you align two things at a chosen reference, then
  read (a) the transform you applied and (b) the residual that won't line up. The
  match is the instrument; the difference is read off it. "Find the same to see the
  different." Finding the right alignment/format is the whole game (see the net
  extractor doc — proven on vision: align first, the cheap reader matches the
  expensive head).
- **The "doesn't-matter" value is load-bearing.** Good comparison = correctly
  identifying what's *shared* (the carriers, the common-mode, the background) and
  removing it, so the residual *is* the meaning. The system that knows what to
  ignore compares well.

## 14. The his / wired ledger and the operating constraints

**Rule 1 ("his way"):** the difference/decision/aggregation must run *inside Isaac*
(his matmul / learned doors / `compare`), not in a numpy/Python harness loop around
him. Feeding raw input is fine; *deciding* in Python is the violation.

- **His (cognition):** typing, counting, `transduce`, working memory, recognition
  via `check`, negatives, logic combine (AND/NOT), inventory, honest-unknown, sense
  routing, box scoring.
- **Wired retina (allowed — cheap "looking"):** salience baseline, segmentation,
  bbox-crop, locating parts, computing displacement signs. The *lens* alignment is
  currently a wired/external transform (LDA/Fisher) — making it *his* is the open
  frontier.
- **Still harness (unbuilt):** control flow — `if`/`while` over his own state, the
  loop/fallback structure. This is the genuine gap.

**INTEGRITY (load-bearing):** *testing Isaac means testing Isaac.* Never substitute
an external learner (sklearn RandomForest/MI/etc.) for the cognition and report it
as an Isaac result — cheating, even labeled "ground truth/validation." sklearn is
for **data I/O only**; all finding/predicting/deciding must be his engine. Don't
tune the harness until he passes (same sin, different shirt). Report nulls as-is;
localize failures to harness-vs-engine; check baselines for bugs before trusting a
flattering number.

---

*Differentiation makes the parts. Memory recursion composes the wholes. There is no
third primitive. The hard part is never the comparison — it's getting the world into
a form where the comparison reveals the truth.*
