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
- Technical next target is in **`SESSION_HANDOFF_2026-06-24.md`**: test the
  **unsupervised / "his" aligner** — can the crystallizer find the alignment LDA
  found *with* labels, *without* them? (Don't re-diagnose the problem; run the candidate.)
