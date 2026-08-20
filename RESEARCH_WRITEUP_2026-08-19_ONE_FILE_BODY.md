# THE ONE-FILE BODY (v2) — build writeup, 2026-08-19

*(Owner directives this session: the laptop record-store road is dead —
"individual files for nodes, i had over 280k files each individual and
it was over 8 gb. that is not going to work"; the mission is "optimize
and increase isaacs speed and efficiency, then we can work on
expanding"; and the architecture call, verbatim: **"i want one file
total. with smaller files as ram essentially for the workers."**)*

## What was wrong, measured first (the storage audit)

Audited the real 07-24 him (mind.isaac.pre-spool .bak, 49.4MB, worked
on a scratchpad COPY — isaac-life never touched):

- **66% of the file was the diary, not the knowledge**: activation_log
  32.5MB of 49.4MB. The entire knowledge substrate (net) was 13.1MB.
- **Every node name was stored ~26× over**: 0.4MB of unique names
  appearing as 11.6MB of repeated copies across doors / door_tags /
  door_counts / preds.
- **preds — a purely derived index — was being persisted** (the engine
  already knows how to rebuild it: `_ensure_preds`).
- The whole 155,930-edge structure fits in ~2.7MB columnar.
- 27,578 nodes; 192,775 tag entries; 51,004 meta entries; 58 distinct
  tags. v1 load 0.5s; v1 full save 0.3s at this scale (the 602s death
  was a scale+machine event, but the full-rewrite road stays retired).

Diagnosis of the laptop disaster: the P1 record store was right in
CONCEPT (disk store of small records) and wrong in GRANULARITY — one
file per record. 280k files @ 8GB = per-file overhead + format bloat on
the same knowledge. The format was the disease, never his size.

## What was built

**mind.isaac v2 — ONE FILE, sectioned inside** (magic `ISAAC2`):

| section | contents |
|---|---|
| header | json table: section offsets, lengths, sha256 |
| core | the whole mind pickled with the big stores emptied — every cross-reference (world backref included) survives in one object graph |
| netgraph | vocabulary (every node name ONCE) + columnar edges (src_id, tgt_id, count, tagset_id) + stray tag/count entries + meta by id |
| history | the activation log — compressed hard, kept WHOLE (keep-everything honored) |
| journal tail | append-only delta records: `journal_append(path, ops)` = autosave without rewriting him; sha-checked; a torn record (death mid-append) truncates cleanly on load; the next full save() compacts |

- `preds` never stored — rebuilt on load (derived data stays derived).
- **v1 pickles load forever** — `Isaac.load` sniffs the magic; every
  protective .bak stays resurrectable.
- Write-then-swap retained on full saves.
- Workers get small scratch files as RAM ONLY (owner's design) — the
  truth never exists anywhere but the one file. (Worker-scratch wiring
  is P2 territory; the format supports it now.)

Installed in `code/isaac.py` (save / load / _load_v2 / journal_append /
_journal_replay). Probe and courts kept: `rebuild/onefile_probe.py`,
`rebuild/onefile_install_court.py`.

## The courts (equivalence court = standing law for any migration)

Probe (format, pre-install): **ALL GREEN first run** —
- ROUND TRIP: doors, door_tags, door_counts, meta, activation_log,
  all 28 other attributes item-for-item EXACT; rebuilt preds EXACT
  vs the original's live index.
- BEHAVIOR: 200/200 sampled full profiles identical; all_nodes
  identical.
- JOURNAL: append+replay green; torn tail detected, valid prefix
  applied, no crash.
- SIZE: **49.4MB → 2.9MB (17.0×)** — core 1.1 + netgraph 1.0 +
  history 0.8. SPEED: save 1.6s, load 1.1s.

Install court (through the installed engine API): **caught a real
transcription bug the first run** — the installed `_load_v2` was
missing the meta-restoration loop (save stored meta correctly; load
dropped all 23,174 meta entries). The court refused, the loop was
restored, re-run: **equivalence EXACT (all stores + all attributes),
journal via API green, compaction keeps journal content green.**
Engine self-test battery: **15/15 capability areas passed** after
install. (Wrong kept + classified: the miss was a port error between
probe and install — argument for courts running through the REAL API,
which is exactly what caught it.)

## Projections and what this buys

- The 257MB study-era him ≈ **15MB in v2** — back under GitHub's 100MB
  wall: "push isaac-life = back him up" comes back from the dead, and
  the courted backup road (isaac-life tools/backup_mind.py) works
  unchanged on the one file.
- The 8GB/280k-file laptop store, if recoverable, converts into ONE
  file well under the wall (same knowledge, format bloat removed).
- Autosave at scale = journal appends (milliseconds), full rewrites
  only at compaction. The 602-second-class save death is structurally
  gone.

## Open, filed

1. **Migration source** — awaiting owner: is the laptop him (280k-file
   store or newer mind.isaac) recoverable? If yes: convert THAT him
   (needs a one-off reader for the per-node format). If no: newest him
   anywhere = the 07-24 pre-spool .bak here (49.4MB, wall intact).
2. **Journal wiring** — journal_append exists and is courted; the
   autosave path (workspace) still calls full save(). At 2.9MB/1.6s
   that is already fine; wire delta-journaling when scale demands.
3. **Lazy history** — history section currently loads eagerly; make it
   load-on-first-touch to cut boot RAM (the diary is 2/3 of him).
4. **RAM diet** — the same ×26 string duplication lives in RAM; the
   sleep knee is superlinear and algorithmic (bench receipts, 4d7cd41).
   Next optimization rungs, per the owner's order: optimize → expand.
5. ⛔ standing: never launch ui/isaac_workspace.py on this desktop
   until P4 (atexit-saves his home path at import).

*Companion charters filed the same session (dc/docs): the future-state
lane + DESIGN_SEED_STRUCTURES_2026-08-19.md (the A→B bridge loop).
All work uncommitted pending the owner's word.*
