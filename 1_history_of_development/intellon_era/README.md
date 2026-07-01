# The Intellon era (Mar 22 → Apr 12, 2026)

The early, pre-Isaac work — where the philosophy was built and tested on small,
hard problems. Recovered and consolidated here on 2026-06-29.

## Start here
- **`INTELLON_HISTORY.md`** — the authoritative timeline. Read this first.
  Evidence-based (file contents + timestamps), honest about which claims have
  surviving code and which don't (e.g. MNIST 99.8% = unreproduced claim).

## What's in the folder
- **`INTELLON_HISTORY.md`** — the reconstruction.
- **`corpus/`** — the surviving Intellon source artifacts:
  - **THE GENESIS — `real_data_benchmark.html` + `two_net_independent_pipeline.html`.**
    The *earliest* experiments: reading answers off **untrained, random nets with no
    training** (a "lottery-ticket" sweep on Iris/Wine/synthetic-digits). Per the
    builder these predate the vocabulary ("reservoir," "lottery ticket") and the
    philosophy itself — and they are the **direct root of the June neural-net
    transplant work.** See `../LINEAGE.md` items 1 & 8.
  - `The_Transformational_Basis_of_Persistence_v2.pdf` — the persistence theory root.
  - matrix lineage: `intellon_unified_spec_v2.md`, `intellon_v3*.jsx`.
  - xb-series JS engine + handoffs: `intellon_terminal*.jsx`, `files/`,
    `files (1)/`, `files (2)/` (handoffs xb6/xb7/xb8, `intellon.js`,
    `storage_engine.js`, fact corpora, tag/extract scripts).
  - curricula & proposals: `intellon_tool_curriculum*.md`,
    `intellon_training_test_plan.md`, `intellon_track6_response_generation.md`,
    `intellon_v6_methodology.docx`, `intellon_wordnet_reasoning.js`.
- **`python_v4_package/`** — the **runnable v4 Python rewrite** (Apr 8–11):
  `core/` (Node/Register/Librarian/Engine, boot, thinker, selfjudge, meta,
  curriculum, storage…), `cli.py`, `gui.py`, `tests/`. This is Isaac's direct
  ancestor in code form — see LINEAGE.md §3.

## Deliberately NOT copied (lived on the source drive)
The big datasets (`wordnet_full.json`, `train-v2.0.json`, `mnist-master.zip`),
a 6.8 GB partial download, and unrelated files (a games folder) were left in
`Downloads/New folder (3)/intellon/`. Only the text corpus + runnable package
were brought in. If a dataset is ever needed to re-run something, it's still there.

See `../LINEAGE.md` for how this era connects forward to SIS → Isaac.
