# TODO — Isaac project (durable; not session-scoped)

*Persistent task list so nothing important gets lost. Check things off as they
happen; add freely. The *technical* next-step lives in the latest handoff (see
bottom); this file is mostly the keep-it-safe / hand-it-off / tell-the-story work.*

## Preservation — "don't let it be lost to history"
- [ ] **Make the project a git repository.** Version control = a self-documenting
      history of every future change + the basis for offsite backup. Then push to a
      **private GitHub/GitLab** so a dead drive can't erase it. (Claude can set this
      up in a few minutes: init, ignore rules, first commit capturing tonight's state.)
- [ ] **One offsite copy.** Zip `Documents/isaac_project/` + the `Downloads`
      archive → put it somewhere that is NOT this PC (cloud drive and/or external disk).
- [ ] **Export the Claude chats** (claude.ai → Settings → export your data). Drop
      the export in a folder; a future session can read through and **condense the
      hundreds of chats into a navigable history.** No rush — when there's energy for it.

## Handoff
- [ ] **Give the project to [brother]** to go over the code + details. Start him
      with the one doc that goes through everything:
      1. **`THE_COMPLETE_PICTURE.md`** (the whole arc, front to back — read first)
      2. `FILE_LOCATIONS.txt` (the map, if he wants to navigate)
      3. `1_history_of_development/LINEAGE.md` + `intellon_era/INTELLON_HISTORY.md` (origins)
      4. `2_the_machine/docs/ISAAC_THEORY_OF_OPERATION.md` (how the engine works)
      5. `2_the_machine/code/isaac.py` — run it: `python isaac.py` → expect 6/6
      6. `equation_discovery/EQUATION_DISCOVERY_ENGINE.md` (the current frontier)

## The bigger story (when/if ready)
- [ ] `THE_STORY_OF_ISAAC.md` captures a *small slice* of a much larger story. The
      builder can expand/revise it, or write a public-facing version that keeps the
      work and softens the personal — his call, his pace.

## The work itself
- **Technical next targets are in `SESSION_HANDOFF_2026-07-02.md`** — the
  owner's four named priorities: thorough scale testing (sweeps → vectorize
  → 3090), human interaction improvement (UI v2 + probe queue), information
  validation (block-permutation null #1, log-track in discover, power
  merging), accuracy validation (calibration audit = the one trust number;
  finish the curriculum; repair the clock readout). Then: shrug→discover,
  covtype migration rounds, uptake-into-engine, warm starts, forgetting.
- ~~unsupervised aligner (2026-06-24 target)~~ → superseded: the null-gated
  basis is in `fit_lens` (default) and validated; registration perception
  carries the alignment thesis further (digits under transform 5%→85%).
- Note: engine self-test expectation is now **10/10** (item 5 above says
  6/6 — that was true at reorg time; authoritative engine = root `code/`).

## Done since 2026-06-27 (for the record)
- ✓ Git repos, private GitHub, both pushed and current (preservation item).
- ✓ Audit standard + verdict sheet; six rebuilds; engine rewiring (10/10).
- ✓ discover()/rivals/confirm/apply_law; waves/clock/statuses; ledger;
  save/load/fork; UI. Kepler exact; Pluto predicted; cross-domain transfer.
