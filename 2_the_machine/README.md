# The Machine — Isaac

**Part 2 of 4.** The thing itself: the running engine that bets on the theory
(`../3_the_theory/`). Three sub-parts — the code, the docs that describe it, and
the evidence that tests it.

## code/ — the engine and everything runnable

- **`isaac.py`** — the whole engine (Net, Isaac, Scratch, World) + self-test.
  ```
  cd code
  python isaac.py        # expect 6/6   (Windows: PYTHONUTF8=1 python isaac.py)
  ```
- The **demo scripts** live beside it and `import isaac` directly — the
  perception/decision stack (`fst_transduce`, `working_memory`, `global_baseline`,
  `attention_*`, `turtle_inventory`, `ascii_creatures`, `curriculum`, `snake_*`),
  plus the earlier probes. `app.py`/`launcher.py`/`build.py`/`templates/` are the
  GUI + packaging.
- **`neural_transplant/`** — the transplant/boxes/lens subproject. Its scripts do
  `sys.path.insert(0,"..")` then `from isaac import …`, so run them from inside that
  folder. Cache: `neural_transplant/emb_cache.npz`.

## docs/ — what it is and how it works

- **`ISAAC_BUILD_STATE.md`** — the live capability ledger (read first).
- **`ISAAC_THEORY_OF_OPERATION.md`** — how the engine works, mechanism by mechanism.
- **`NET_EXTRACTOR_THEORY_OF_OPERATION.md`** — the transplant / boxes / lens.
- **`ISAAC_Manual.md`** — full theory + API reference.
- `Isaac_System_Architecture.md`, `Isaac_Implementation_Rules.md` (the 18 rules),
  `intellon_unified_spec_v2.md`, `Isaac_Complete_Walkthrough.docx` — the spec/arch.
- `ISAAC_Pipeline_Spec.md`, `ISAAC_Perception_Curriculum.md`,
  `ISAAC_Visual_Curriculum.md`, `ISAAC_Theory_and_Headspace.md` — pipeline,
  curricula, mindset.

## evidence/ — the empirical claims (the lab record, NOT the theory)

These are the *findings* that test the bet — kept here, with the machine, on
purpose. The theory stays in `../3_the_theory/`; the claims live here.

- **Reading trained nets:** `GPT2_Decompositional_Structure.md` (the 60/32/8 head
  split) + its ingestion twin `GPT2_Complete_Findings.md`,
  `Positional_Structure_in_Transformers.md`, `NET_EXTRACTION_METHODS.md`,
  `CONCEPT_HARVESTING_PAPER.md`, `word_meaning_packages_complete.md`.
- **Compression / dimensionality:** `compression_research_report.docx`,
  `low_dimensionality_report.md`, `sparse_output_research_findings.md`,
  `carrier_content_decomposition_v2.docx` (v1 in `_superseded/`),
  `pattern_hash_table_paper_v2.docx`, `spectral_type_encoding_addendum_v2.docx`.
- **Proofs / experiments:** `DC_AC_PROOFS.md`, `TERNARY_EXPERIMENT_METHODS.md`,
  `structured_comparison_loss_proposal.docx`.

> Integrity rule (load-bearing): testing Isaac means testing Isaac. Findings here
> are the engine's, reported as-is — nulls included. See `../REVIEW_NOTES.md`.
