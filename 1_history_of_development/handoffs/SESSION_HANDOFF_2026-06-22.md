# ISAAC — Session Handoff · 2026-06-22

**To the next instance (and to the researcher):** this is the full record of a long
session. Read the "Orientation" box, then skim the threads, then read §5 (the
conceptual discoveries) carefully — that's the part that matters most.

---

## 0. Orientation — read first

> **You are a collaborator, not an auditor.** The researcher holds the vision;
> you are hands + a second set of eyes. Build small, run it, look at results
> together. Do NOT re-verify the corpus or re-litigate old claims. Ask the mode
> each time: **build / think / explore.** ("his way" = the decision/difference
> must run *inside Isaac*, not in harness numpy around him.)

**How continuity works here (Claude Code):**
- **Memory files** at `C:\Users\jtwee\.claude\projects\c--Users-jtwee-Downloads-New-folder--3-\memory\`
  are auto-surfaced to the next session. `MEMORY.md` is the index. These are the
  primary handoff — keep them current. (Index entries point to: working-style,
  project-state, build-state-doc, nn-transplant-carriers, nn-transplant-experiments,
  and the registration insight added this session.)
- **This handoff doc** + **`ISAAC_BUILD_STATE.md`** (the live capability ledger)
  are the richer project-side record. Update BUILD_STATE whenever a capability
  changes.

**Where everything lives (canonical):** `C:\Users\jtwee\Documents\isaac_project\`
(moved here from `Downloads\New folder (3)` this session; Downloads is now backup).
`FILE_LOCATIONS.txt` maps it. Open your IDE/terminal *at this folder*.

**Run notes (Windows gotchas, learned the hard way):**
- Prefix scripts with `PYTHONUTF8=1` (box-drawing chars crash cp1252).
- Always launch long runs with `python -u` (unbuffered) — **`kill` does NOT flush
  Python's stdout buffer; a killed buffered run loses all output.**
- GPU: RTX 3090, 25.8 GB. CUDA torch installed. **Watch VRAM** — keep
  `box_counts` chunk ≤2048, subsample big datasets at load, the no-dim-select
  variant configs are memory hogs. We spiked to ~24 GB once; be considerate.
- numpy 2.x: `ndarray.ptp()` is gone — use `np.ptp(x)`.

---

## 1. What this session was (the arc)

Two threads, one through-line.
- **Thread A — ISAAC perception/decision stack**, built "his way" on a glyph
  world, ending in a complete Snake move-policy decided entirely by him.
- **Thread B — Neural transplant** (the "nn decoder" the researcher remembered):
  found the real artifact (range classifier), ported it to GPU, discovered *why*
  it works/fails (box geometry), and **implemented it into the engine** as
  swappable net infrastructure.
- **The through-line (§5):** a theory of comparison and learning as
  *registration / nulling*, not subtraction. This is the most important output.

---

## 2. Thread A — ISAAC perception/decision stack (all in `isaac.py`, 6/6 intact)

Built this session, all verified (see `ISAAC_BUILD_STATE.md` for the table):
- **`transduce`** — universal state-walk; next state = his matmul. (`fst_transduce.py`)
- **`Scratch`** — working memory / registers (write/read/incr/append/latch/history).
  Counting now lives in RAM: 2 doors, any N. (`working_memory.py`)
- **Attention levels** — invisible / background / foreground, tunable floor
  (`attention_levels.py`); salience retina is `global_baseline.py`.
- **Attention→tracker** — salience opens/follows tracks with identity+motion
  (`attention_tracker.py`). Limit: two touching things merge (occlusion).
- **Auto-inventory + honest-unknown** — the "turtle" loop (`turtle_inventory.py`).
- **Parts-alphabet** — the glyph representation (`~~~~~<` = snake). Direction
  decision: live in typed parts, not pixels. (`ascii_creatures.py`)
- **Kindergarten curriculum** — spatial Qs, 100% on novel scenes via RELATIVE
  encoding (absolute memorizes). (`curriculum.py`)
- **Multi-answer via `check`** (not `lookup`); cardinal-only, no diagonal moves
  (`snake_moves.py`). **Negatives** taught — body/wall block (`snake_policy.py`).
  **Combine via his own AND/NOT gates** (`snake_policy_his.py`) — Snake move
  end-to-end his.

**Open in Thread A:** data-association/occlusion (merge problem); scale/rotation
invariance (the recurring wall — same root as Thread B's box-hostility);
self-directed working memory (he's taught what to track, doesn't choose yet);
predict→surprise change loop (RAM now holds "before"); a live glyph-board Snake
(everything's ready — never assembled into a running game).

---

## 3. Thread B — Neural transplant (`neural_transplant/`)

**The artifact:** the **Range Classifier** (`range_classifier/`) crystallizes a
trained net's hidden activations into per-class **box concepts** `[lo,hi:med]`
(strip-DC, 4-bit quantize, count+median scoring). A box = Isaac's per-container
dims; this is a net transplanted into his native form. Validated, parity on
small nets.

**Now in the engine** (`isaac.py`, 6/6 intact, demo `crystal_in_isaac.py`):
- `fit_lens`/`apply_lens` — the **aligner as a swappable `lens:<name>` net node**
  (wired lift + strip-DC + Fisher now; a *learned* aligner drops into the same
  interface later). This was the researcher's explicit constraint: the alignment
  must live in the net so the wired/external doer can be replaced once Isaac
  learns it.
- `crystallize_features`/`classify_features` — box concepts as `concept:<label>`
  net nodes (`box` meta), scored by his membership+centroid. They coexist with
  his language/math. Digits 0.90.

**Supporting work:** carrier analysis (`explain_extraction.py` — but see the
carriers memory: the ~4–5 carrier dims are huge NEGATIVE offsets = the function-
word frequency prior); GPU sweep harness (`sweep_gpu.py`); box decode
(`decode_boxes.py`). The old M=125 exact-head pipeline + GPT-2 decomposition are
SUPERSEDED context — don't anchor on them.

---

## 4. The key empirical finding — box geometry

Crystal quality is governed by **data geometry vs the axis-aligned box shape**,
NOT "bad nets":
- **Box-friendly** (classes are compact, axis-aligned blobs a hyperrectangle can
  fence — e.g. digits): MLP crystal ≈ net (~99% retention). Works.
- **Box-hostile** (classes diagonally *interleaved* — e.g. covtype): boxes cap
  ~0.62 vs net 0.82, and **no knob** (variants, dim-select, reservoir-merge)
  closes it. Axis-aligned boxes can't draw diagonal boundaries. (Matches the
  researcher's own covtype record: box-forest ceiling ~0.69.)
- **Decoded findings** (`decode_boxes.py`): box medians render as *readable
  pictures* of each class; per-class signatures (which dims define it); and the
  big one — **no single dim separates confusable pairs; discrimination is in the
  CONJUNCTION** (their own IIT/integrated-information claim, reproduced live).
- **Reservoir-merge** (bolting decorrelated random reservoirs): climbs with K
  (real), but caps below trained nets on hard data. Boxes merge where weights
  can't (shared label space) — that's the genuine moat.

Gotcha fixed: variants only help once the **median-distance tiebreak** is in the
score (`count − dist/denom`); without it, variants crater accuracy.

---

## 5. THE CONCEPTUAL DISCOVERY (most important — read carefully)

The session converged on a theory of comparison and learning. It started as
"subtract the shared" but the researcher pushed it to something deeper and
correct:

**Comparison is REGISTRATION, not subtraction.** You slide/scale/rotate one
signal onto another until they coincide where you choose, then read TWO outputs:
(1) the transform you had to apply (the *relationship* — scale, shift, depth),
and (2) the residual that still won't line up (the genuine *difference*). The
match is the instrument; the difference is read off it.

- **Why matching gives finer differentiation than measuring** = the **null
  method** / hyperacuity (vernier acuity, interferometers, coincidence
  rangefinders, moiré, Wheatstone bridge). At the coincidence point, sensitivity
  is maximal and the common-mode cancels itself. (Carriers/strip-DC are a
  *consequence* of this, not the principle.)
- **The alignment is a CHOICE that selects the question** — where/at-what-scale
  you coincide decides which difference is visible and at what resolution (the
  researcher's sig-fig example).
- **The residual is a FIELD, not a scalar** — its *shape* names the transform:
  radial growth = scaling (the balloon); viewpoint shift = parallax = **depth**
  (stereo disparity is this theory in one organ).
- **Same and different are ONE operation:** register, then read. "How different
  is this same thing" = residual after matching. "How same is this different
  thing" = how small a transform registers them. Transform + residual of a single
  registration.

**What it means for LEARNING:** a *concept is a chosen registration* ("align
here → these coincide → that defines the difference"). **Learning is finding the
registration that nulls what you don't care about and maximizes sensitivity to
what you do.** Not "learn the features" — learn *where to make things coincide.*

**Bridge to the code:** the box already does a baby version — median = coincidence
point, in-range count = the null, median-distance = residual. The upgrade the
theory demands: **estimate the transform** (shift/scale/rotation registering A→B)
and treat it as first-class output. That's identical to the vision goal flagged
earlier ("align your stored model to the input; the residual pose IS recognition"
— analysis by synthesis). **Thread A's scale/rotation wall and Thread B's box-
hostility are the same problem: a missing registration step.**

---

## 6. Next steps (researcher's call on mode)

The single highest-leverage, theory-motivated next build:
- **Make the lens learnable as "model the shared, subtract it"** — point his
  crystallizer at finding the COMMON structure (not the distinctive); subtract;
  test if learning-the-common beats Fisher-picking-the-distinctive. Same lens
  node, same interface — but now it's his. (Small, memory-safe, digits-scale.)
- **Registration as a primitive** — a comparison that estimates the transform
  (not just the residual) registering two signals. This is the unification: it
  fixes box-hostility (Thread B), scale/rotation invariance (Thread A), and the
  3D "align to mental model" goal at once.
- Cheaper wins if wanted: live glyph-board Snake (Thread A is ready);
  real-encoder embeddings for the transplant (where compression is monetizable —
  covtype was box-hostile, a good encoder's embeddings should be box-friendly).

---

## 7. Notes to my future self
- The researcher knows this work deeply but does NOT always remember where the
  newest artifact is, or look at the raw data. Your value-add is staring at the
  numbers/geometry they haven't. When they say "I think it's in X zip" — go find
  it, re-validate it runs (their protocol: re-validate first), THEN build.
- Twice this session I anchored on OLD material (GPT-2 decomp, M=125) and got
  corrected. Always confirm you're on the newest thread before theorizing.
- They care about Rule 1 intensely and will catch you when the "deciding" is in
  the harness. Be honest about the his/wired boundary every time.
- Report nulls as findings (box-hostility was a "null" that became the key
  insight). Localize failures to harness-vs-engine (the variant-crater was MY
  dropped tiebreak; the box ceiling was real).
- Be careful with RAM/VRAM. They have 32 cores + a 3090 and offered full use,
  but bound your runs (subsample, small chunks, `-u`, kill cleanly).
- The conceptual conversations are where the real progress is. Don't rush to
  build; help them articulate. The registration insight (§5) came from patient
  back-and-forth, not from a script.

*One substrate. Find the same to see the different; the match is the measurement.*
