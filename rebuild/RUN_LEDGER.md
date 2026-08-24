# RUN LEDGER — every citable number names its commit
Standing rule (adopted 2026-08-24, record-repair): a number is citable only if produced
on a clean checkout of a named commit; review-time fixes go to a branch, never the tree
under audit. This file records gate runs, mutation demos, and investigation runs.
Machine: i9-14900KF / 48GB / Windows 11 (the only machine so far — threat 7.11).

## 2026-08-23 — teardown reproduction runs (pre-branch)
Commit state: ce5df54 + dirty tree early in the day (disclosed; this ledger and the
citation rule exist because of it). Full results in `TEARDOWN_2026-08-23.md §1`:
every §8 row reproduced green; CLOTH 120 = 942/1108 (85%); trivial baselines
100.0% / 99.6% / 90.7%; broken-rule probe 1800/1800 leg-existence vs 0/1800 join.

## 2026-08-24 — record-repair branch

**d6a0ce0** — teardown docs + measurement scripts committed.

**df94a92** — N1+N2 conversion. Mutation demos, one per harness (clean run exit 0,
one-expected-value-flipped run exit 1, reverted; per-agent details in the conversion
workflow record):
| harness | checks feeding FAILS | clean exit | mutated exit |
|---|---|---|---|
| worstcase_baseline | 26 (KNOWN-BUG: gen-truth-grinth) | 0 | 1 |
| scale_eval | 6 | 0 | 1 |
| pemdas_eval_test | 12 | 0 | 1 |
| selection_feedback_test | 17 + count guard | 0 | 1 |
| logic_bridge_probe | 6 | 0 | 1 |
| bridge_soundness_probe | 2 | 0 | 1 |
| onefile_probe | 38 | 0 | 1 |
| onefile_install_court | 3 | 0 | 1 |
| cloth_run (n=2 smoke) | 3 | 0 | 1 |
| cloth_trivial_baseline | 2 | 0 | 1 |
The XPASS mark-rot rule fired once during conversion (an over-broad known-bug mark on
florb was rejected by the mechanism itself) — the guard works.

Gate runs at df94a92:
- fast gate (`python rebuild/run_gates.py`): **10 passed, 0 failed, 1 slow-skipped,
  27.6s, exit 0**.
- fresh clone, different directory (N1 acceptance): **9 passed, 0 failed, 2 skipped
  (cloth rows — corpus is untracked data), exit 0.** No import errors from any
  location: the portability defect class is closed.
- full gate `--slow`: **FAIL — cloth_run_120 crashed** at 293s:
  `TypeError: bad operand type for unary -: 'str'` at isaac.py:4916, where the variable
  is bound by `range()` and cannot be a str by Python semantics. First catch by the new
  gate; investigation below.

## The intermittent-crash investigation (2026-08-24)

Symptom class on this machine, three distinct failures, none reproducible:
1. Historical: `TypeError: unhashable type: 'set'` ~1-in-3 in one July environment,
   0/26 reproduction attempts on 2026-08-23 (the observe() diagnostic trap from
   ce5df54 targets it; it has never fired).
2. Slow-gate run: the impossible str-from-range TypeError above (batch ~5 of CLOTH).
3. Crash hunt run #1 (random seed): **segmentation fault** at the final whole-course
   exam — a different site, a different failure class; pure Python + numpy should not
   segfault.

Discriminator matrix — five full-length CLOTH-120 workloads:
| run | seed | BLAS threads | result |
|---|---|---|---|
| 2026-08-23 evening | random | default | clean, 942/1108 |
| slow gate | random | default | TypeError (impossible value), batch ~5 |
| crash hunt #1 | random | default | segfault, final exam |
| hunt run A | 0 | default | clean |
| hunt run B | 0 | single | clean |

Reading: failures move between sites and exception classes and do not reproduce; both
fixed-seed runs (including one concurrent pair, higher load) are clean. A logic bug
that is hash-seed-dependent changes *results*, not exception *classes*, and cannot put
a str in a range-loop variable or segfault the interpreter. The profile matches
nondeterministic corruption (CPU or RAM), and this machine's CPU is an i9-14900KF —
the Intel Raptor Lake family with the documented instability/degradation defect (BIOS
here: AMI 1.80, 2024-09-26, which likely carries the mitigation microcode — but
mitigation does not heal prior damage). WHEA log: empty (common for this defect).

Pure-CPU determinism stressor (no Isaac code; all cores compress+hash an identical
buffer against a known-good digest for 8 minutes — a wrong answer on identical input
is a hardware verdict, full stop): **result recorded below.**

Result: **59,538 iterations across 30 workers, 0 mismatches, 0 crashes** — clean.
Caveat that keeps hardware on the suspect list: all-core saturation drops clocks and
voltage; the Raptor Lake defect classically manifests at high SINGLE-core boost — which
is the CLOTH run's exact profile (one hot Python thread with BLAS bursts). A clean
all-core stress is therefore consistent with the hypothesis, not against it. Named next
probe if the crash recurs: the same determinism stressor at 1-2 workers (max boost
residency), plus the owner-run diagnostics below.

Standing disposition for this crash class:
- It is on the record as ENVIRONMENT-SUSPECT, not engine-logic; no code change is
  owed against it (the observe() trap stays).
- The gate's slow row will catch recurrences; every recurrence gets a ledger entry
  (site, exception, seed, load).
- Owner recommendations: verify BIOS microcode is 0x12B or newer; run the Intel
  Processor Diagnostic Tool and MemTest86 (XMP RAM is the other corruption source);
  the 14900KF is covered by Intel's extended warranty for this defect class if it
  fails diagnosis.
