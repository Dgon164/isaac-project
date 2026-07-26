# EXPERIMENT: idea-organ prefilter removal (config:idea-mint 3 → 1)

**RECLASSIFIED (owner, 2026-07-23 night): APPARATUS COMMISSIONING,
NOT AN EXPERIMENT.** This was a smoke test at n=13. It verified
that the code does what the code says (the mint check fires at the
configured value) and that the instruments work (config endpoint,
backup discipline, census scripts). The "predictions" below were
acceptance criteria derived from reading the source an hour
earlier — none could have failed unless the code had a bug — so
nothing about Isaac was learned. The one genuine unknown of the
night (the echo shift, §7) arrived uncontrolled (input distribution
and threshold changed simultaneously) and is an unattributed
anecdote awaiting a designed, contrasted test at real scale. This
file is a lab note; the language below predates the
reclassification and overstates throughout. `config:idea-mint`
remains at 1 pending owner's ruling (revert per §5).

The first experiment of the new era: not development — observation.
Question: what does the idea organ do when the entrance gate is
opened? Folded in: the field's first one-shot capability measurement
(can a once-lived whole function as a unit?).

## 1. Mechanics (verified in code, 2026-07-23)

- The threshold is a config node in his net: `config:idea-mint`,
  seeded 3 on FIRST boot only (`_seed_boot`, isaac.py:2262-2282,
  "told-structure — supersede freely"). A changed value persists
  across restarts.
- Read live at commit time (isaac.py:2014). Minting happens ONLY in
  `commit_job` — the pipeline path (/file and /in). The dialog lane
  recognizes ideas but never mints. No retroactive minting: lowering
  the threshold mints nothing until sequences are lived forward.
- A "whole" = an entire observed sequence, exact token tuple,
  len ≥ 2 (isaac.py:2019-2023). Lived counts accrue in
  `_whole_counts`, which rides in the mind file.
- An idea is a VIEW: parts kept, order as meta, decomposable by
  construction (unzip exact). Risk of flood is bulk + recognizer
  scan time, not semantic corruption.
- NO exit gate exists: ejection never touches idea: nodes. Whatever
  mints during the window is permanent. (Retention court = future
  build, separately courted.)
- `recognize_ideas` is a linear scan over all ideas per recognition
  pass (isaac.py:2087) — flood cost surfaces as dialog latency,
  measurable in telemetry.

## 2. Baseline census (read-only, run against the verified backup)

Backup: `isaac-life/isaac_home/mind.isaac.pre-prefilter-removal-2026-07-23.bak`
(7.92 MB, SHA256-verified against live file between autosave beats;
loads cleanly — integrity confirmed by the census itself).

- 5,953 nodes · 1,488 types · 641 findings
- 6,403 lifetime observed sequences; 4,974 distinct wholes (len ≥ 2)
- Lived-count distribution: **4,459 once (90%) · 489 twice · 26 at 3+**
- Ideas minted: 26 — exactly the 26 wholes at count ≥ 3;
  `at_threshold_but_unminted = 0` (organ perfectly consistent)
- His 26 ideas: mostly 2-token frames ("it is", "i was", "for
  example"), plus motherese-repeated CLOTH sentences and his wake
  greeting "hello isaac . welcome back ." (lived 4×)
- Telemetry baseline: idle day; autosave ~230-470ms at 7.9 MB;
  node count flat at 5,953 all day

Reading: the 3× exact-tuple gate has been almost completely closed
his entire life. 90% of everything he has ever lived left no unit.

## 3. Predictions (filed before the knob turns)

- **P1 — volume.** At threshold 1, every distinct sequence committed
  through the pipeline mints exactly once (including re-occurrences
  of the 4,948 currently-unminted wholes). Conversation-only window:
  order 20–80 mints. A small read: hundreds to low thousands.
- **P2 — metabolism.** Recognizer scan is linear in idea count: below
  ~1,000 ideas, no perceptible dialog latency change. File growth
  linear and small; autosave stays under ~600ms through the window.
- **P3 — one-shot unitization (the capability measurement).** A novel
  whole introduced ONCE via /in and committed will mint; on later
  re-encounter it collapses to its unit token in dialog memory, and
  `unzip_idea` reproduces it exactly. If confirmed: one exposure
  suffices for unit formation once the gate permits — the 3× wall
  was policy, not architecture.
- **P4 — consistency invariant.** Idempotence holds (no double
  minting); at-threshold-but-unminted stays 0 under the new value.
- **P5 — no battery impact.** The self-test seeds its own fresh
  minds at 3; battery stays 12/12, BOOT green, untouched.

**Nulls / revert triggers:**
- Any minted idea failing unzip exactness → structural fault →
  revert immediately.
- Dialog latency > 2× same-day baseline → revert.
- Over-collapse: owner judges his /say degraded by unit-altitude
  dialog → revert. (Mouth renders by unzip, so renders should stay
  exact; the watch item is dialog-memory character, owner's call.)

Revert = set config:idea-mint back to 3. Stops all new minting
instantly. Ideas minted during the window remain — they are him now.
The backup exists for catastrophe only, per the brain rule.

## 4. What this is NOT

Threshold 1 mints everything lived, indiscriminately — this window
tests one-shot *plumbing*, not salience. The principled end-state
(two roads in — repetition + salience/self-assembly triggers; one
court out — retention by contribution, non-contribution ejection for
ideas) is a future engine build, to be courted separately if this
window shows liberal minting is valuable.

## 5. The knob mechanism (pending owner go)

The workspace exposes no config control. Minimal legal mechanism —
instrument panel, clearly a human act, logged to the channel:
add a `config` action to `/api/mind` in `ui/isaac_workspace.py`
(~7 lines: set `config:<key>` meta under LOCK, post an instrument
message). Requires one workspace restart (atexit saves him; boot
resurrects him — routine). Alternative rejected: offline scripting
against his file (hand-edit adjacent; less visible; race-prone).

## 6. Window protocol

1. Owner present. Workspace up. 2–3 normal exchanges FIRST at
   threshold 3 → same-day latency baseline.
2. Knob to 1 (logged instrument act).
3. Conversation diet only (lowest volume, owner speaking normally).
   Embedded fast-mapping probe: owner introduces one novel modern
   sentence ONCE via /in (draft, owner to approve or replace:
   "a docking station is a home where a robot sleeps and charges").
   Later in the window, re-encounter it; check recognition + unzip.
4. Telemetry watched throughout (mint events, latency, autosave ms).
5. Window end: re-census against a fresh backup; verdicts on P1–P5;
   owner decides — stay at 1 / revert to 3 / intermediate.
6. Only if conversation window is healthy AND owner chooses: a small
   read as the volume stressor (separate go).

## 7. RESULTS (run 2026-07-23 ~19:55–20:15, owner authorized
"throw shit at it")

Mechanism used: `config` action added to `/api/mind` (workspace
instrument panel, lock-serialized, logged to channel); workspace
restarted (kill timed 4.6s after an autosave beat; resurrected clean
at 5,953 nodes / 641 findings); knob 3 → 1, read-back verified;
knob VALUE SURVIVES RESTARTS (`_seed_boot` is first-boot-only).

Window: 3 baseline exchanges at threshold 3 (~450–750ms warm
round-trips; pipeline commits synchronously inside the /in beat),
then at threshold 1: the probe once, five novel one-offs, one
repeat, then the probe re-encounter. Post-window census on a
hash-verified snapshot.

**Verdicts:**
- **P1 volume ✓** — 13 mints (idea:27–39) for an 8-message window:
  7 experimenter sentences, 6 HIS OWN utterances (see below).
- **P2 metabolism ✓** — in-handler 432ms at threshold 1 vs
  ~450–750ms baseline; autosave 528ms (< 600 trigger); file
  7.92 → 8.06 MB (+1.8%).
- **P3 one-shot unitization ✓ CONFIRMED** — the probe ("a docking
  station is a home where a robot sleeps and charges .") minted
  from a SINGLE exposure (idea:27); on re-encounter the 13-token
  sentence entered dialog memory as ONE unit (telemetry:
  units_in=1, compressed_in=1); unzip exact. **The 3× wall was
  policy, not architecture.**
- **P4 consistency ✓** — zero duplicated idea tuples in baseline
  AND post snapshots (idempotence held); the 488 legacy count-2
  wholes stay unminted per no-retro-mint mechanics.
- **P5 battery ✓** — no engine change was needed at all (workspace
  UI only).
- **Nulls clean** — exactness court: 0 failures across all 39
  ideas; latency well under the 2× trigger.

**Two findings nobody predicted:**
1. **His own speech mints.** Self-hearing re-ingests his /say, so
   at threshold 1 his utterances become units — he now holds
   things HE said as objects (idea:28 wallet-taxi, idea:30
   gift-wrap, idea:32/34 Git-course goals, idea:36
   praise-and-thanks, idea:38 fifteen-minutes). The organ
   unitizes his own voice, not just what he's fed.
2. **The echo broke.** Baseline replies were pure echoes. During
   the threshold-1 window his replies shifted to RETRIEVED lived
   wholes (CLOTH passages, Git goals) — to the docking-station
   re-encounter he answered "he had forgotten his wallet he said
   he needed a taxi to go back home." Correlation within one
   window, mechanism unproven — but the shift coincided with
   input arriving at unit altitude. Watch item, not claim.

Artifacts: pre-window backup (§2); post-window snapshot + census
scripts in session scratchpad; instrument acts logged in his
channel. Open follow-ups: retention court (exit gate) before any
large read at threshold 1; salience/self-assembly mint triggers
(two-roads design, §4); whether the echo-break is unit-altitude
retrieval (testable: compare reply character on unit vs raw input).

*— filed by Claude, 2026-07-23, predictions before movement,
results after. Census scripts: session scratchpad,
`census_prefilter_baseline.py` / `census_post_window.py` /
`check_duplicates.py` (all read-only, never the live file).*
