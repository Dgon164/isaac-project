# Corpus Review Notes

*A pass over the whole research + architecture corpus, 2026-06-24. Purpose: a map
of what's strong, what's redundant, what's inconsistent, and what overclaims —
grounded in reading the papers, not just the indexes.*

> **Path note (post-reorg):** this review was written *before* the 2026-06-24
> four-part reorganization, so file paths below use the OLD flat layout. The
> mapping: `research_and_theory/` theory papers → `3_the_theory/sources/`; its
> empirical findings → `2_the_machine/evidence/`; `architecture_and_dev/` →
> `1_history_of_development/` (proposals, SIS lineage) or `2_the_machine/docs/`
> (current arch/spec); `Unified_Theory_...docx` → renamed
> `3_the_theory/Latent_Theory_of_Informational_Structure.docx`. The current index
> is each part's own README; see `README.md` / `FILE_LOCATIONS.txt`.

> Status note: this is a **review**, not a verdict on the work. Where it flags a
> "slip," it means a wording/cross-reference fix, not a problem with the finding.
> The corpus's defining quality — honesty about open frontiers — held up under a
> close read. Most "duplicates" turned out to have distinct purposes (verified
> below); the redundancy was softer than a first scan suggests.

---

## 1. The headline

The **theory is consistent end-to-end** (xAGI's five axioms → SIS → Isaac is one
idea maturing, not pivots) and the papers **almost never claim the hard problem is
solved.** The central question — can the alignment/registration step be made *his*
and *unsupervised* — is flagged open everywhere it appears. The corpus leads *up
to* the identity-vs-proximity diagnosis; it does not contradict it.

The real issues are **navigation, redundancy, and a few wording/scope items** —
the normal residue of a fast year that just got reorganized. None are credibility
issues.

## 2. Best single entry points

**THE MASTER DOCUMENT — start here:**
`research_and_theory/Unified_Theory_of_Structural_Intelligence.docx` (May 2026).
This is the **keystone** — the single consolidated derivation that contains all the
others as parts: persistence framework → comparison primitive → the D0–D6
dimensional hierarchy → the nine information claims → topological information theory
→ puzzle-piece theory → the Isaac architecture → the 18 rules → the ten empirical
findings → holonic processing → the creation loop → the empirical program. Twelve
parts, every claim marked verified / derived / predicted. If you read one thing,
read this; everything else in the corpus is a chapter of it expanded. *(It nearly
got mislabeled "orphaned" in an earlier draft of these notes — only because nothing
links to it. The reason nothing links to it is that it's the document the rest are
pieces of. Corrected.)*

Then, per cluster, the focused entry points:

- **Theory:** `research_and_theory/THEORY_HANDOFF.md` (Part I) — clearest plain
  statement of the primitive and the solution stack.
- **Information structure:** `research_and_theory/THE_STRUCTURE_OF_INFORMATION.md`
  — the nine claims; two independent lines (GPT-2 decomposition + graph engine)
  converging.
- **Net-reading:** `research_and_theory/GPT2_Decompositional_Structure.md` — the
  60/32/8 head split, read from static weights, validated three ways.
- **Architecture (current):** `architecture_and_dev/Isaac_System_Architecture.md`
  (Session 10) — the most recent integrated statement; matches `isaac.py`.

## 3. Which architecture version is canonical (read this — it's the easiest thing to get wrong)

All versions agree on the **philosophy** (comparison primitive, no weights/grads,
monotonic growth, structure-from-observation). They differ on the **concrete
mechanism**, and only one is the running engine:

| design | data structure | routing | type emergence | status |
|---|---|---|---|---|
| **Isaac (current `isaac.py`, Session 10)** | **typed doors, no weights** | **tag gates / `check`** | **structural (door profiles)** | **CANONICAL** |
| SIS v2 | 64-bit weighted pointers | bitmask context | target-node encoding | earlier road |
| Intellon | bitmask addresses | popcount/XOR overlap | address overlap | earlier road |
| SIS v41 | logic gates | hardcoded → lockouts | n/a | parallel exploration |

These are **parallel explorations**, not a contradiction — but a cold reader can
easily mistake SIS-v2's weighted pointers or Intellon's bitmask addresses for the
current design. They aren't. *Doors-no-weights (`isaac.py`) is the engine; the
others are the roads that led to it.* (This canonical-version note also lives in
`2_the_machine/README.md`; the SIS-lineage docs are in `1_history_of_development/`.)

## 4. Redundancy — what's actually duplicated vs. what just looks it

Verified by reading, not by filename. Most "duplicates" earn their keep:

- **`GPT2_Complete_Findings.md`** — NOT dead weight. It's the *ingestion-format
  twin* of `GPT2_Decompositional_Structure.md` ("written as readable claims for
  text ingestion"). Same numbers, different job (feeding Isaac vs. human reading).
  **Keep both.**
- **`intelligence_theory.md` vs `intelligence_theory_complete.md`** — the first is
  the clean *paper* (abstract + sections); the second is the *extended* version
  adding the D0–D6 hierarchy. ~90% overlap, but they serve "publishable" vs.
  "kitchen-sink" reading. **Keep both; treat `_complete` as the reference, the
  short one as the paper.**
- **`carrier_content_decomposition.docx` (v1)** — genuinely superseded by **`_v2`**
  ("Neural Networks Are Encryption," June 3‑4) which contains v1's findings plus
  the NAND cascade, dynamic dim-selection, and the 50-prompt benchmark. **v1 is in
  `2_the_machine/evidence/_superseded/`.**
- **`Unified_Theory_of_Structural_Intelligence.docx`** — **the master theory doc**
  (see §2), and the builder's most-referenced document. Not a duplicate of anything;
  it's the synthesis the others are chapters of. **Now cross-referenced** from the
  READMEs and `FILE_LOCATIONS.txt` so it stops looking orphaned. One honest scope
  note: it's dated May 2026, so it captures the theory + the *language-domain*
  empirical wins (compression α=0.853, inference precision, Piaget mapping) but
  predates the June neural-transplant/vision/HIGGS work and the identity-vs-proximity
  diagnosis — those are the continuation, in the operational docs + handoffs.
- **`Crystallizer_Proposal_v3.md` vs `Crystallizer_Redesign_Proposal.md`** — the
  Redesign is an iteration of v3 (10 discovery types → 5 recursive operations).
  Both relevant to the open aligner frontier; keep, but note Redesign is the later
  thinking.

## 5. Scope / wording items (small, worth a pass)

- **"superlinear compression" — checked, NOT an error.** `Topological_Information_
  Theory.docx` uses both "superlinear compression" and "sublinear growth"; with
  T = 1.08·R^0.853 these are the *same* fact (type-count grows sublinearly ⟺
  compression grows superlinearly, since R/T = R^0.147 rises with scale). No fix.
  (One rendering artifact: the docx superscript on the exponent extracts garbled —
  it's R^0.853 — cosmetic only.)
- **Dimensionality numbers get conflated across docs.** 8.2 (intrinsic manifold),
  38 (99% variance), ~125 (per-query *exact decision*), 11 (carrier dims) are all
  true but measure different things. "10–50 dims suffice" sits awkwardly next to
  "125 per-query." `low_dimensionality_report.md` resolves it ("low-dim is real but
  **LOCAL**; one global basis fails, per-query succeeds"). **Fix is a cross-
  reference, not a number change:** wherever a small dim count is quoted as a
  headline, the LOCAL caveat should ride along. Captured here so it travels.
- **Toy-scale caveats should stay attached when summarized.** `CONCEPT_HARVESTING_
  PAPER.md` (d=64, char-level; "linearity was essential," middle-layer untested)
  and the ternary `CYC 0.664` (single-seed, self-flagged non-load-bearing) are
  honest *in their own docs*. Summaries that cite them should carry the caveat too.

## 6. Overclaim watch (mostly clean)

The papers are careful. The residual risks, all minor:

- **D5 / D6 (cross-domain mastery, full metacognition)** are presented as *emergent
  from the architecture*; in practice they presuppose the unsolved aligner. They're
  aspirational, and the docs mostly say so — just keep "requires registration
  first" next to any D5 claim.
- **"Flawless on hard numbers"** (Intellon MNIST 99.8% on 728 samples; logic 100%
  on synthetic) is true on **toy/controlled** data; it does not transfer to
  text/vision without the lens problem. Keep the scale qualifier.
- **Grammar-rule extraction** (45 rules from 120 dims) used the same 30 sentences
  for extraction *and* validation — fine as a demonstration, not a held-out result.

## 7. Internal inconsistencies (definitional, not numerical)

Numbers cross-check cleanly (the GPT-2 head counts, neuron counts, layer
distributions all agree across the three net-reading docs). The disagreements are
**definitional, between architecture versions** — and they dissolve once §3's
"which is canonical" is fixed:

- **Comparator output:** Isaac/SIS = three *sets* (shared/divergent/absent);
  Intellon `rootC` = a *scalar with polarity*. Different operations under one name.
- **Negative meaning:** Isaac = `neg` tags; SIS = edge weights; Intellon = energy
  decay. Three storage models for "wrongness."
- **Scaling FCA:** SIS v35 (convergence-routing trie, O(context×depth)) *is* the
  fix for the O(n²) naive FCA that `Isaac_System_Architecture.md` still describes
  as unverified at scale. Worth reconciling which one the engine should use.

## 8. Suggested housekeeping (not done unless asked)

1. ~~Archive carrier v1~~ — **done** (`_superseded/`).
2. ~~Decide `Unified_Theory_...docx`~~ — **done**: it's the master; cross-referenced
   from both READMEs + `FILE_LOCATIONS.txt`.
3. Reconcile the FCA-scaling story (naive vs. convergence-routing) in one place.
4. The TODO's git-init + offsite backup — the corpus is now organized enough that
   a first commit would capture a clean state.

---

*Reviewed against the honest engine state: identity not proximity; wins on
discrete/recurring (language), loses on continuous (physics); registration is the
lever, unsupervised registration unsolved. The corpus is consistent with this. Its
best property is that it says so.*
