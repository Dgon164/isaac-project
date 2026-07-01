# The Complete Picture
### The whole research line, front to back — what it is, where it came from, how it works, what's proven, and what's open.

*If you read one document, read this one. It goes through everything and points
to the deep docs for detail. Written 2026-06-29; supersedes the pre-reorg
overviews in `overviews/` (which are now historical snapshots).*

*Honest by construction: every claim below is tagged where its status matters.
Where something ran, it says so; where a number has no surviving harness, it says
that too. Nothing here is dressed up.*

---

## 0. How to read deeper

This doc is the spine. The detail lives here:

| For… | Read |
|---|---|
| the full origin story (the human one) | `4_the_story/THE_STORY_OF_ISAAC.md` |
| the origin timeline, evidence-based | `1_history_of_development/LINEAGE.md` |
| the earliest era in depth (Mar–Apr) | `1_history_of_development/intellon_era/INTELLON_HISTORY.md` |
| the master theory | `3_the_theory/Latent_Theory_of_Informational_Structure.docx` |
| how the engine actually works | `2_the_machine/docs/ISAAC_THEORY_OF_OPERATION.md` |
| what the engine can do right now | `2_the_machine/docs/ISAAC_BUILD_STATE.md` |
| the neural-net transplant work | `2_the_machine/code/neural_transplant/` + `NET_EXTRACTOR_THEORY_OF_OPERATION.md` |
| the current frontier (equations) | `equation_discovery/EQUATION_DISCOVERY_ENGINE.md` |
| where any file is | `FILE_LOCATIONS.txt` |

---

## 1. The one-paragraph version

This is a multi-year line of research into a different kind of AI: one built not on
weights and gradients, but on a **single primitive — differentiation** (comparing
two things and recording *same / different / doesn't-matter*) applied recursively,
keeping what recurs. The bet is that intelligence is **comparison sustained over
time**, not optimization of a giant parameter blob — and that a system built this
way is **explainable by construction** (every step is a readable comparison, not a
black box) and **cheap** (it runs on a Raspberry Pi, not a datacenter). The line
has gone through several named architectures; the current working engine is
**Isaac**, and the current research frontier is an **equation-discovery engine**
that reads governing equations directly out of raw data.

---

## 2. The thesis (what never changed)

Stated plainly:

> **The system differentiates. Everything else is a question of *what field* you
> point the differentiation at, and *at what scale*.**

A few principles fall out of that, and they have held from the very first
document to the current one:

- **Comparison *is* learning.** The test and the training signal are the same
  operation. (In the earliest engine this was literally one function, `rootC`,
  that computed comparison, signal, and correction at once.) Today this is stated
  as **"learning is registration"**: you don't subtract one thing from another, you
  *align* them and read what's left over.
- **Correct the model, never reality.** A wrong answer is a fault in the model, not
  the data ("you don't recalibrate your eyes when you misidentify something").
  Today: **"model everything as real structure; the answer is the residual."**
- **No workarounds — prove everything from data.** If the system can't derive it,
  it doesn't get to assert it. Today this is the hard rule that **a trained neural
  net is never the deliverable** — the deliverable is an explicit, readable law.
- **Explainable is non-negotiable.** This is what the "xAGI" phase named outright:
  *Experimental **Explainable** AGI*. A result you can't read is not a result.

These four are the through-line. The architectures changed; the thesis didn't.

---

## 3. The full lineage (how it developed)

*Condensed; full detail + caveats in `LINEAGE.md`, the Intellon era in
`INTELLON_HISTORY.md`. **On order:** the file dates in the corpus are **download**
dates, not creation dates — unreliable for absolute timing — and the early period
is fuzzy in the builder's memory. The sequence below is how the **ideas
developed**, per the builder, not a precise timeline. Where memory and dates
disagree, memory wins.*

1. **The first experiments — "answers from a net without training."** The genesis,
   before any philosophy or name: feeding data through *untrained, random* nets and
   reading answers straight off them — no gradients, no training. Surviving
   artifacts: `intellon_era/corpus/real_data_benchmark.html` +
   `two_net_independent_pipeline.html` (a *"lottery-ticket"* sweep). This came
   *before the builder knew the words* ("reservoir," "lottery ticket") — and it is
   the **direct root of the neural-net transplant thread (phase 8)**. The oldest
   thread and one of the newest are the same thread.
2. **Xenointelligence** — the philosophy that **crystallized out of** that tinkering
   (the builder places the experiments first, despite an earlier download date): AI
   as a *distinct cognitive species*, not an imitation of human thought. The *why*
   the hands-on work provoked.
3. **Intellon** — where the philosophy got *built and tested*. Its physics root is
   the **persistence theory** (the universe filters for configurations that sustain
   themselves against entropy; intelligence is a loop that accumulates depth — the
   seed of "the answer is the residual"). Two lineages ran in parallel: a
   physics/matrix engine (`rootC`, a fixed lens, ghost nodes — the untrained-net
   experiments are its experimental wing) and a symbolic node/tool-discovery engine
   (the one that actually ran: up to **457 passing tests**, a 295K-node live graph,
   autonomous "rumination"). It ended in a Python rewrite — *"differentiation is the
   only native operation"* — **Isaac before it was Isaac** (nodes + pointers = doors,
   an axiom boot, meta-knowledge as nodes, a self-judge, an idle thinker).
4. **xAGI = Experimental Explainable AGI** — its own named style. The name *is* the
   thesis (**explainable** is non-negotiable). Five axioms: differentiation-only;
   intelligence is iteration; selection before computation; elimination-not-discovery
   (the answer is what's left in the constraint box); reasoning ≠ retrieval.
5. **SIS = Structural Intelligence System** — a redesign: a sparse-matrix "concept
   spreadsheet," five rolling context windows, holonic pattern layers, integer-only
   computation (no floats, no gradients).
6. **The exploratory stretch** — "a bunch of screwing around" (the builder's honest
   words): trying things, the necessary mess between a clean idea and a working
   system. Part of what innovation actually looks like, not a gap.
7. **Isaac** (~June 2026) — the line consolidates into **one running engine.** Two
   primitives (differentiate + remember what recurs), now with a perception/
   decision stack, working memory, and the registration lever. Passes its 6/6
   self-test.
8. **The neural-net transplant** — *phase 1's thread, grown up.* The same instinct —
   get answers out of a net without training it — applied to *frozen, pretrained*
   nets (the untrained random nets survive here as the "reservoir" baseline). See §5.1.
9. **The Equation-Interaction Discovery engine** (now) — the current frontier. See §5.2.

**The shape of it:** not a series of pivots — *one continuous idea getting sharper.*
untrained-net tinkering → Xenointelligence → Intellon → xAGI → SIS → Isaac → the
transplant → the equation engine. The names changed; the program didn't.

---

## 4. How Isaac works (the engine)

*Full mechanism-by-mechanism account in `ISAAC_THEORY_OF_OPERATION.md`. The
short version:*

**The substrate.**
- **Nodes** — the elements (tokens, numbers, pixels, concepts — whatever is observed).
- **Doors** — directed, relation-tagged connections between nodes (`is_a`,
  `part_of`, `contradicts`, …). A door *is* a stored difference.
- **Types** — groups of nodes that share a relational profile, discovered
  automatically. This is how "cat" and "dog" become "animal," and how one edge-cell
  and another become "edge." Same machinery, any field.
- The net **compiles to a legible weight matrix** — you can read it.

**The two primitives.**
1. **Differentiation** — compare two things: `same / different / doesn't-matter`.
   The third value, **"doesn't-matter," is load-bearing** and is Isaac's key
   advance over the origin (Intellon had only same/different). The don't-care is
   what lets a comparison *generalize* instead of memorize.
2. **Memory recursion** — keep what recurs; the structure that survives repeated
   comparison is the knowledge.

**The reasoning unlock.** Two ways to read the matrix:
- **`lookup`** — argmax retrieval ("what's the most likely answer?").
- **`check`** — validate a *specific* cell ("is *this* claim true?").
`check` is what lets multi-valued relations and honest "I don't know" work — and
it's what turns retrieval into reasoning.

**The pipeline** (loosely brain-shaped): sense → store → route → evaluate → act,
with an **active** mode (cheap, real-time) and an **idle** mode (consolidation /
crystallization — effectively "sleep," where types form and the graph reorganizes).

**The rule that defines the project ("his way" / Rule 1).** *We give Isaac data and
answers — never the method.* He attempts, compares to the answer, and learns from
the difference. The decision/aggregation must happen **inside the engine** (his
matmul, his learned doors), never in a Python harness loop around him. Feeding raw
input is fine; *deciding in Python is the violation.* This is enforced as an
**integrity rule** (see §7).

---

## 5. The two research threads

### 5.1 The neural-net transplant — *the lever is registration*

*Detail: `NET_EXTRACTOR_THEORY_OF_OPERATION.md` + `neural_transplant/`.*

**This is the oldest thread in the project** (lineage phase 1): it began with the
very first experiments — reading answers off *untrained* random nets with no
training (the "lottery-ticket" benchmarks). Here that instinct grows up and is
pointed at *frozen, pretrained* nets; the untrained random nets survive as the
"reservoir" baseline (what was linearly free before any learning).

Can you take a frozen neural net and read its knowledge out into Isaac's cheap,
explicit form? The pipeline: extract a net's activations → **align them (a "lens")**
→ quantize → build per-class "boxes" → classify by box membership.

The finding that matters: **the box reader is cheap and finished; success is gated
entirely by the alignment.** Get the representation into the right frame
(registration) and a trivial reader matches a linear classifier (vision: 0.71 →
0.834 with the right rotation lens, ≈ the linear ceiling 0.839). This *proved
"comparison = registration" on real networks.* The open hard part — the field's
hard part — is finding that alignment **without labels** ("his" aligner).

And the rule this thread hardened: **a trained net is never the deliverable.** The
extraction is a means; the goal is always the explicit, readable structure.

### 5.2 The Equation-Interaction Discovery engine — *the current frontier*

*Detail: `equation_discovery/EQUATION_DISCOVERY_ENGINE.md`. Test bed: the HIGGS
dataset. Every number there was produced by the scripts in its `code/`.*

The reframe that ties the whole line together: **stop chasing classification
accuracy.** Gradient descent reaches arbitrary accuracy on noise; accuracy says
nothing about truth. Instead, take a **raw dataset with no labels** and recover the
**governing equations** that produce it. Four reusable moves:

| Move | Question | Mechanism |
|---|---|---|
| **Detect** | which sources are related? | all-pairs covariance of a feature lift; eigen-decompose; shuffle null floor |
| **Derive** | what's the exact equation? | sparse fit over a library of *allowed* forms; read the constants |
| **Recover** | what's missing? | a never-recorded variable *is* the residual of the equation that won't close |
| **Score** | how complete are we? | every bit of structure is either a stated law or *proven* noise |

The central finding on real data: **two kinds of structure are separable.**
- **Relationship shadows** (redundancy — derived quantities like invariant masses)
  reduce to **readable equations.**
- The **differentiation shadow** (the *signal* itself — e.g. the Higgs) is
  high-order and distributed: it can be **detected** with a single deterministic
  equation but **not reduced** to a short formula, because the information genuinely
  isn't low-order.

Honest bottom line: *where the data is sufficient, the engine closes equations
exactly and accounts for 100% (law + proven noise); where information was never
recorded, it detects the shadow, reconstructs what it can up to an anchor, and
measures exactly how far the recoverable reaches.* This is the persistence paper's
"the answer is the residual," finally built — and it is **explainable AGI's** point
made concrete: it tells you not just the answer, but precisely which part *cannot*
be turned into a clean law, and why.

---

## 6. The theory spine

*The master statement is `3_the_theory/Latent_Theory_of_Informational_Structure.docx`;
its source papers (Intellon, the Puzzle-Piece theory, persistence, topology) are in
`3_the_theory/sources/`.*

The recurring theoretical commitments, in one place:

- **Don't destroy information.** Averaging, binning, and axis-aligned boxes throw
  away the detail that *is* the signal (the mean of a rainbow is grey; a circle and
  a square share a bounding box). Recognition must *count which structure is
  present* and refine by closeness — never average.
- **Presence, not average.** What matters is *what is there*, registered exactly,
  not a summary statistic.
- **Generalize by fitting forms, not memorizing points.** A concept is a fitted
  functional form ("a function on doors"); you recognize by fitting and reading the
  residual.
- **Holonic / scale-free.** "Difference between parts of a structure" is one
  operation that runs at every level — pixel↔pixel, object↔object, frame↔frame. The
  system composes upward for free.
- **The needle is the residual.** Model everything real first; the thing you're
  hunting (the Higgs, the anomaly, the signal) is what's left once the rest is
  explained as real, readable math.

---

## 7. What's proven vs. what's open (honest)

**Solid / ran:**
- The symbolic engine passes its own **6/6 self-test**; language, math, logic,
  reasoning, and problem-solving all demonstrated.
- Working memory, the finite-state "walk" (`transduce`), and his-way decision
  (perceive=`check`, negate=NOT, combine=AND through his own logic gates) — built
  and run on novel inputs.
- Registration proven on real nets (the vision lens result).
- The equation engine recovers planted equations exactly, reconstructs real
  invariant masses, and separates the two shadow kinds on HIGGS.

**Open (the honest frontier):**
- **The unsupervised "his" aligner** — can the system find the alignment *without*
  labels that it currently finds *with* them? This is the single most important
  open problem; it's roughly the field's hardest problem.
- **Perception from raw signal** — a "retina" that turns a raw field into the typed
  parts the engine reasons over is deliberately bracketed for later.
- **Capabilities the origin had that Isaac hasn't rebuilt** — the autonomous
  *thinker* (idle self-directed discovery), in-engine *trust tiers*, and a
  *self-judge*. The stated next frontier ("learn to fill working memory actively")
  is essentially rebuilding the thinker.

**The integrity rule (load-bearing, non-negotiable):** *Testing the engine means
testing the engine.* You never substitute an external learner (a scikit-learn
model, etc.) for the cognition and report it as a result — even labeled "ground
truth." External tools are allowed for **data I/O only**; all finding, predicting,
and deciding must be the engine's. Nulls are reported as nulls. Flattering numbers
are checked for baseline bugs before they're trusted. This rule is *why* the
results above can be believed.

---

## 8. Run it

```
cd 2_the_machine/code
python isaac.py            # expect: 6/6 passed
```
On Windows, if box-drawing characters error out: `set PYTHONUTF8=1` first.

The demo scripts live beside `isaac.py`; the transplant work is in
`neural_transplant/`; the equation engine is in `../../equation_discovery/`.

---

## 9. Why this is kept

The builder's own framing: *"I don't think I'm special, but I think this may
matter."* The record is preserved not as a finished product but as an honest
example of **what independent innovation actually looks like** — including the
dead ends, the "screwing around," the nulls reported as nulls, and the one open
wall that's still a wall. If it amounts to something, the trail is here. If it
doesn't, the trail is *still* here — which was the point.

*One operation — difference — applied recursively to a structure, growing
knowledge from data, explainable at every step. From a grief-period distraction in
January to an equation engine in June. The names changed; the idea didn't.*
