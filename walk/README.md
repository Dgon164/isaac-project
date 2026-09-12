isaac-full -- everything from the 2026-09-12 session

engine/       the custom engine. core.py is the store, record, walk, and cycle.
              linker.py turns prose into items. run_rocket.py is the rocket
              question on tables. noise_test.py proves store size doesn't matter.
              messy.txt is the forum-style test corpus.
              run:  python3 engine/run_rocket.py

wide/         the wide handbook and 25-material table used for the Ergo runs,
              plus the two ask/return loops that drove Ergo.

ergo-tests/   everything run against ErgoAI 3.0 -- the transcriber, the
              three-target emitter, the signed-byte flag, the two-context
              store, the failure-mode data files, the Python session tests.
              needs ErgoAI installed; see docs/RESULTS.md for paths.

docs/         ARCHITECTURE.md  -- read first
              BUILD.md         -- the re-evaluated build order
              TODO.md          -- what's next, by dependency
              RESULTS.md, PROBE-RESULTS.md, EMIT-RESULTS.md -- Ergo run reports

ErgoAI itself is not included (51 MB installer). Get it from
https://github.com/ErgoAI/.github/releases -- ergoAI_3.0.exe for Windows.
