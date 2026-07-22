# THE BOOT LINE — design
*2026-07-22. The hard-drive principle: the only thing hard-coded is the entry point. Everything that runs Isaac is a shape in his net — flowcharts he (or teaching) can modify or supersede, with receipts. Prior art: the flow walker from the paperclip lineage (flows as net content, refusal as an honest outcome, every door bypassed with a reason); re-derived here, not copied.*

---

## 1. The layers

**Hard-coded (the hardware — nothing else):**

- `Isaac.boot()` / `Isaac.beat()` — the entry point. `beat()` reads `boot:entry` in the net, follows its door to the current boot-loop flow, walks it once, returns `(outcome, trace)`. `boot(beats=N)` repeats. On a bare net, the first call runs the one-time seed (§3) — the OS install — after which the shapes are net content like everything else. `boot()` contains **no policy**: not the pipeline order, not the sizes, not the ops to run. Change the shapes, and the next beat behaves differently. No Python edits.
- **The instruction set** — the walker dispatches a step's `op` to a method on the mind (`getattr`), same convention as the prior art: capability belongs to code, experience belongs to the net. The new mechanical ops (§4) each do ONE thing and return receipts. An unknown op is refused with a receipt, never an exception.

**In the net (his, supersedable):**

- `boot:entry` —door(tag=`boot`)→ `flow:boot-loop`. Meta `current` names the live flow; superseding = author a new flow, point `current` at it, keep the old (meta `superseded` chain, same convention as laws).
- `flow:<name>` — meta `steps` = ordered step dicts; `step:<flow>.<id>` — meta `spec`. Step spec: `id, op, args (kwarg→state key), out, doors: [{to, when}], success`. `when` predicates are declarative (`equals` / `cmp`/`than` / `truthy`); every door gets a receipt — the taken one AND each bypassed one with the reason (the consideration law).
- `queue:inbox` — the spine. Doors (tag=`job`) to `job:<n>` nodes; meta: `payload` (list of token sequences), `state` (`open → working → done`, or `refused` with the reason kept), `kind`, `received`. Segments hang off jobs: `seg:<job>.<i>` (tag=`segment`), meta `tokens`, `state`, `crystal`, `assessment`. Nothing is erased; a finished job is its own receipt trail.
- `config:segment-size` (default 128), `config:merge-group` (default 4) — meta `value`. Numbers in the net, adjustable live, read fresh each beat.

## 2. The default boot sequence (seeded as told-structure, then his)

```
pull ── q_next ──(job?)──► segment ► crystallize ► assess ► merge ► commit ► sleep
   └──(no job)──► idle
```

- **segment**: split the job's payload into pieces ≤ `config:segment-size` tokens (whole sequences, never split mid-sequence). 800 tokens in → manageable pieces, per the spec.
- **crystallize**: each segment goes to a disposable worker — a fresh scratch mind that observes the piece and runs its own consolidation pass. The crystal (types found, door counts) is stored on the segment node as a receipt. The mind net is untouched.
- **assess**: each crystal compared against the mind net (known vs new tokens, similarity) and against sibling segments (kin) — stored, mechanical, no judgment.
- **merge**: crystallized segments recrystallized together in bounded groups (`config:merge-group`) — the "crystallized segments get recrystallized with other crystallized segments" stage.
- **commit**: the single writer. Sequences enter the mind net through the same `observe` path as ever — the court below proves the pipeline changes *when and in what company* content arrives, never *what* arrives. Then delta-compile (§5) absorbs it cheaply.
- **sleep**: the deep pass — scoped consolidation over what the commit dirtied.

## 3. First boot = the install

`_seed_boot()` runs once (guarded by `boot:entry` existing): authors the flow above via `define_flow`, hangs config nodes, stamps every seeded node with meta `provenance="seeded 2026-07-22 (told-structure — supersede freely)"`. From that moment the boot sequence is content, not code.

## 3b. The recovery sector (owner, 2026-07-22)

The install also writes `boot:recovery`: meta `sector` = a pristine deep-copy of the original steps, meta `flow` = the flow it rebuilds. Every flow carries a `chapter` number — authorship order as a fact in the net, so "the latest boot chapter" is readable, not guessed. Beat-time resolution, in order:

1. **The redirect** — `boot:entry` meta `current`, if `_flow_ok` (structural health: steps meta present, a flow-start door, every step carrying its spec).
2. **The latest sound chapter** — among boot-tagged doors, the structurally-sound flow with the highest chapter. The redirect is repaired to it, receipted.
3. **An unconnected chapter** — if no connected chapter stands, scan the flows hub for sound flows of boot lineage (name match or a `branched_from` chain reaching the boot flow) that lost their door to `boot:entry`; reconnect the latest, receipted.
4. **Rebuild from the sector** — `_recover_boot()`: the original re-authored from the pristine copy; whatever broken steps existed are pushed onto the flow's `superseded` list (kept, never erased — same convention as law supersession).
5. **Factory reseed** — only if the sector itself is gone: `_seed_boot()` runs again, receipted.

Behavioral refusals (an unknown op in a walking flow) are NOT damage and do not trigger recovery — they are honest outcomes. The sector guards *structure*, not policy.

## 4. New instruction-set ops (all mechanical, all receipted)

`ingest(text_or_sequences, kind)` → job node · `q_next()` → oldest open job or none · `segment_job(job)` · `crystallize_job(job)` · `assess_job(job)` · `merge_job(job)` · `commit_job(job)` · `sleep_pass()` · `idle_pass()`. Plus the walker itself: `define_flow`, `branch_flow` (piecewise supersession), `walk_flow`, `beat`, `boot`.

## 5. The compile becomes incremental (the other half of scaling)

`_compile` currently reparses **all** history every time anything new is observed. It becomes delta: pair counts accumulate in `_pair_counts` keyed `(delta, frame)`, only `observed_sequences[_counts_up_to:]` are parsed, and W/frames/deltas re-materialize in sorted order. Behavior-bearing invariants preserved exactly (suffix widths 2..6, `partial != frame`, sorted index identity and the argsort tie-break, float32 accumulation, empty→None, `max_context` pinning with full-rebuild fallback, lazy-init on legacy pickles per the `door_counts` pattern). The court: same sequences fed incrementally vs monolithically must produce `np.array_equal` W and identical frames/deltas.

## 6. The battery (a 12th capability area: BOOT)

1. First boot seeds the shapes; they are readable from the net.
2. **Exactness court**: ingest through the full pipeline vs direct `observe` on a control mind — identical lookup answers, confidences, node/door counts.
3. **Delta-compile court**: interleaved observe/lookup vs one-shot compile — `np.array_equal(W)`.
4. **Null — scrambled flow**: a step with an unknown op walks to `refused` with a receipt, no exception.
5. **Null — empty job**: a payload-less job files `refused` and stays on the record; it does not vanish or crash the loop.
6. **Supersession court**: point `boot:entry` at a branched flow mid-run; the next beat follows the new road; the old flow remains in the net.
7. **Hop cap**: a circular flow ends with `hop-cap`, not a hang.

## 7. Honest limits (v1)

Single-process; workers are scratch minds run inline (disposable fork-workers can drop onto the same queue later without changing the spine — the same promise the orchestrator prototype recorded). The deep pass inherits the crystallizer's existing scoped-vs-full trade-offs (the ~800-node knee is not addressed here; the tiered crystallizer remains its own build). W is still dense at materialization — sparse is the named next step; the delta compile removes the reparse wall, not the memory wall.
