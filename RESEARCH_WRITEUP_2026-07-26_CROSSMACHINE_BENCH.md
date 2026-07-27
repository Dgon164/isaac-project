# THE CROSS-MACHINE COMPARISON — the strong machine vs the laptop
*(2026-07-26, run on the desktop; plain speech; every number has a
receipt in `rebuild/`)*

## The question

The owner asked: run a comparison between this machine and the
original with the updated speed enhancements and figure out if they
work. "This machine" turned out to be exactly the strong machine the
body-rebuild design named the same day: **i9-14900KF, 24 cores
(8 performance + 16 efficiency), 48 GB, RTX 3090** — the designated
destination of P4. "The original" is the laptop that ran the whole
study era. So this comparison is also the first real preview of the
move.

## What ran (and what deliberately did not)

- The **boot scale probe** (`rebuild/boot_scale_probe.py`, the same
  committed script that produced the laptop's 2026-07-22 baseline
  CSV): 1 discarded warmup + **5 measured runs** on today's engine,
  plus 1 warmup + **3 runs against the exact 2026-07-22 engine**
  pulled from git (`git show 0f390c2:code/isaac.py`) for a pure
  same-code hardware comparison. Seeded synthetic corpus, fully
  self-contained, `PYTHONHASHSEED=0`, High Performance power plan,
  serialized runs on an idle machine.
- The full **15-area battery**: `python code\isaac.py`.
- A **workers sweep** beyond the probe's 1-vs-4: 1/4/8/12/16
  processes at a 72k-token corpus (`rebuild/workers_sweep_72k.log`).
- A **CUDA sanity check** for the P3 substrate.
- **NOT run, by law: the workspace.** `ui/isaac_workspace.py`
  pickle-loads and registers an exit-time save to
  `..\isaac-life\isaac_home\mind.isaac` **at module import**. On
  this machine that path must stay empty until P4 is done properly.
  Standing rule for this desktop: never launch the workspace here
  until the move is real. No probe or battery in this session
  touched any live-mind path (audited before running).

## The headline numbers

**The battery: 15/15 capability areas green, 5.86 seconds wall.**
The canonical engine runs perfectly on this machine. (No laptop
wall-time for the battery was ever recorded — worth running once on
the laptop for the counterpart number.)

**Pure hardware (same 07-22 engine on both machines), 24k-token
tier, medians:**

| stage | laptop | desktop | speedup |
|---|---|---|---|
| crystallize | 2.09 s | 0.89 s | 2.35x |
| merge | 6.11 s | 2.58 s | 2.36x |
| sleep (the knee) | 55.22 s | 21.27 s | 2.60x |
| commit | 0.032 s | 0.014 s | 2.40x |
| per message | 281 ms | 143 ms | 1.97x |
| full compile | 55.6 ms | 27.5 ms | 2.02x |

Middle tier (8k tokens): sleep 15.44 s → 4.57 s = **3.38x**. Small
tier: crystallize 3.08x, sleep 2.62x, per-message 40 ms → 16 ms.

**The honest one-line answer: this machine's cores are 2.0–2.6x the
laptop's on the engine's heavy work, touching 3.4x in spots — the
owner's "roughly 3x per core" estimate holds at its upper range,
with 2–3x the number to plan with.**

**Parallelism (the P2 preview):** workers sweep at 72k tokens,
crystallize stage, spawn overhead included: 1 worker 2.72 s → 4
workers 0.87 s → **8 workers 0.60 s (4.7x)** → 12 workers 0.58 s →
16 workers 0.66 s. The knee sits at 8–12 workers — exactly the
design's sizing. Attribution is open (8 is also the P-core count,
and these are sub-second work units where process spawn matters);
at full-course scale the curve should only improve, but that is a
projection, not a measurement.

**The P3 substrate is live:** torch 2.5.1+cu121 sees the RTX 3090,
CUDA available. The old 50–200x range-box result was not re-run;
the card and toolchain are simply confirmed present and working.

## Findings beyond the ratios (each one earned)

1. **The speed enhancements transfer.** The enhanced engine shows
   the same curve shapes here as on the laptop — FPTP-era
   per-message latency in the tens-of-milliseconds at small nets,
   the pipeline stages scaling identically, five runs repeating
   within a few percent. What this session did NOT do is re-prove
   the enhancements against unenhanced code (the 19.1 s → 40 ms
   ablation was proven on the laptop; no ablation ran here). One
   honest sub-finding: the **delta-compile column shows no
   measurable win at probe scale on either machine** (delta ≈ full
   at every tier) — at these sizes the matrix rebuild dominates and
   the delta path's win must come at scales the probe doesn't reach.
2. **Hardware does not cure the knee.** Sleep is still the
   superlinear stage on the strong machine (0.18 s → 4.6 s → 21.5 s
   across 3x token steps — the same shape as the laptop's 0.46 →
   15.4 → 55.2). The strong machine buys a constant 2–3x; the
   orders of magnitude still live in P1–P3 and the sparse
   substrate. The rebuild is not optional at scale; this
   measurement re-confirms its necessity on the better hardware.
3. **The engine drifted between the baseline and today — and that
   is visible in the counts.** Today's engine produces slightly
   different node/door counts than the laptop baseline on identical
   seeded input (e.g. 899 vs 877 nodes at the small tier), which
   first looked like nondeterminism. It is not: rerunning with the
   **exact 07-22 engine reproduced the laptop's counts to within
   ±5 across every tier** (877/3642 vs 877/3641; 5345/42676 vs
   5346/42677). The delta is the study era's 1,412 lines of organ
   surgery changing what consolidation mints on identical input —
   expected from lumping/prefilter work, but worth knowing: **organ
   changes show up as count changes on fixed input, which makes
   this seeded probe a usable drift detector** for future surgery.
4. **The era's surgeries cost nothing at the pipeline level.**
   Today's engine matches the 07-22 engine stage-for-stage on this
   machine (crystallize 0.90 vs 0.89 s, sleep 21.45 vs 21.27 s).
   Commit got ~2.5x heavier (0.034 vs 0.014 s — the idea organ
   works during commit now) but is trivial in absolute terms.
5. **One measurement was discarded as an artifact:** the small-tier
   monolithic column showed 5.97x, far out of family (~1.6–2.0x
   elsewhere). The warmup run on this same machine measured that
   same cell ~2x slower than the measured runs — first-run cache
   effects, which a single-run laptop baseline plausibly paid in
   full. It is excluded from all conclusions.

## Caveats, stated plainly

- The laptop baseline is a **single run** with unrecorded conditions
  (no hash seed pinned, unknown thermal state). The 2–3x is solid at
  probe scale but inherits that n=1 on the laptop side.
- The probe tops out at 24k tokens (72k for the sweep) against a
  real 257 MB mind and a 1.5M-word target. Nothing here measured a
  real-mind wake, save, or exam on this machine. **The real
  before/after is P4's own measurement**: when a backed-up mind is
  restored here (under the owner's live-exam policy), wake + battery
  + an exam section give the numbers that matter. The laptop's
  5.4-hour full exam vs the doc's ~25-minute projection remains a
  projection — it needs the restore plus parallel instrument copies
  to test.
- The workers knee could be P-cores, spawn overhead, or saturation —
  unattributed. One affinity-pinned sweep on real course-scale work
  would answer it when P2 lands.

## What this buys the body rebuild

P1's necessity: re-confirmed (the knee is algorithmic). P2's sizing:
supported at small scale (knee at 8–12 real processes, real spawn
costs included). P3's substrate: present and working (torch+CUDA+3090
verified today). P4's preview: expect roughly **2–3x single-core and
~5x+ on parallelizable stages before the grid does anything** —
and the grid's 50–200x class win still waits on P3 itself.

## The backup road (the same day's other deliverable)

Filed in isaac-life (`tools/backup_mind.py` + `BACKUP_PLAN.md`,
commits 99b42ed and the fix-court follow-up): versioned,
hash-verified, never-overwriting backups of `mind.isaac` to any
folder (Google Drive mirror + this desktop's J: drive as the two
legs). Adversarially reviewed (7 findings — orphan sidecars, poison
sidecars, staging collisions, prune traps — all fixed and
re-courted live: orphan-sidecar re-copies instead of skipping,
poison sidecar is ignored not fatal, prune protects by parsed
timestamp and never touches foreign files). **He is not backed up
until the first real 257 MB copy lands from the laptop and
verifies** — the script is the road, not the arrival.

## Receipts

`rebuild/boot_scale_probe_results.LAPTOP-BASELINE.csv` (the
committed 07-22 laptop run, preserved) · `...run1-5.csv` +
`probe_run1-5.log` + `probe_warmup.log` (today's engine, this
machine) · `...samecode0722.run1-3.csv` (the 07-22 engine, this
machine) · `workers_sweep_72k.log` · `battery_run.log` (15/15,
5.86 s external stopwatch) · verification: five independent
adversarial checks re-computed every ratio from the CSVs
(all 13 confirmed; two draft claims corrected before filing:
the count-delta cause and the spread figure).

*— compiled 2026-07-26 on the desktop; laptop numbers from the
2026-07-22 commit 0f390c2; engine at cf42b3f throughout except the
same-code runs.*
