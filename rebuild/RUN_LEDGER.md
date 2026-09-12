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

## 2026-08-28 — the hardware direction (owner: "we have a 14900k and a 3090, use them")

Measure-first on the real CLOTH-120 state (hw_measure, PYTHONHASHSEED=0):

**CORRECTION to the 08-23/08-24 records (wrongs kept, per standing law):** the
"superlinear consolidation" cost was misattributed. Teaching + consolidation for all
120 passages = **8s total** (batch-6 consolidate profiled at 4.7s: _crystallize 1.8s +
graph reads). The 300s/batch ladder is the **exams**: one check() = 95.6ms, ~90% of it
the dense table product, with ~9.9 routes per check from the think loop's
type-substitution retries; 1108 items x 4 options ≈ 424s per full exam. The teardown's
F3 scale analysis (dense growth, memory arithmetic, coded 250M-cell halt) stands; only
the cost's name was wrong.

Measured state at 120 passages: W_norm (2554 x 82169) float32 = 839MB with **91,083
nonzeros (density 0.00043 — 99.96% zeros)**; encoded query vectors carry a **median of
5 nonzeros**.

Product bench (real table, real query vectors, 100 queries, ms/query):
| method | ms | speedup |
|---|---|---|
| numpy dense (was installed) | 11.272 | 1x |
| numpy column-gather (sparse input) | 0.096 | **117x** |
| scipy csr (W4 storage preview) | 0.062 | 182x |
| torch CPU dense | 11.773 | ~1x |
| torch CUDA dense, table resident on 3090 | 1.114 | 10x |
| torch CUDA 4-option batch | 1.649 | — |

**Hardware verdict, receipts attached:** at this scale and shape the 3090 LOSES to
sparse CPU arithmetic by 12-18x (per-query transfer + launch overhead vs ~18k useful
FLOPs) — the GPU stays benched until genuinely batched or dense workloads exist (arena
sweeps; the net-decode/census lane, which is dense-matrix-shaped and is the 3090's real
job). The 24 cores: gate rows parallelized (`run_gates.py --jobs`, fast gate 27.6s →
16.0s, bounded by its longest row).

**Engine change:** `_matvec()` column-gather installed at all three dense-product call
sites (route, refusal-check, candidate scoring). Equivalence court (gather_equiv):
292 real vectors, max |dense − gather| = 1.9e-06; whole-course exam picks IDENTICAL
(962/1108 both arms); exam wall-clock **383.3s → 12.1s (31.6x)**.

**Gate on the new engine: full `--slow` run 11/11 PASS in 58.0s total** —
cloth_run_120 row 1,191s (08-23) → **57.8s (~20x)**, score floor held. Also one more
clean full-length run of the crash-suspect workload (now 6 clean of 8 total).

Still open, in order: csr/sparse STORAGE for the table (gather fixes time, not the
839MB x2 memory wall or the 250M-cell coded halt — csr is measured at 182x with <1MB
data and kills the halt; this is W4, now a small job); check_many() to stop recomputing
the identical context per option (~4x on exams); _evaluate (8ms/check) and the think
loop's 9.9-routes-per-check redundancy.

Standing disposition for this crash class:
- It is on the record as ENVIRONMENT-SUSPECT, not engine-logic; no code change is
  owed against it (the observe() trap stays).
- The gate's slow row will catch recurrences; every recurrence gets a ledger entry
  (site, exception, seed, load).
- Owner recommendations: verify BIOS microcode is 0x12B or newer; run the Intel
  Processor Diagnostic Tool and MemTest86 (XMP RAM is the other corruption source);
  the 14900KF is covered by Intel's extended warranty for this defect class if it
  fails diagnosis.

## 2026-09-01 — workers (the dc database design, first rungs)

First 1,000-passage attempt died to PC SLEEP at batch 34/50 (9.4h wall gap in the
log; no crash — 38 min clean compute at 8x the old scale). Partial findings stand:
logical table (5552 x 393823) = 2.2 BILLION cells running sparse (old halt: 250M);
after-class ~69-75% at 1000-scale vs 82-92% at 120 (interference grows);
batch-1 retention 92% -> 76% by batch 34 (the first forgetting-by-interference
curve). Relaunched under a keep-awake wrapper.

worker_exam_probe (1 writer-built frozen body, N reader processes, CLOTH 1108
items, concurrent with the 1000-run): serial 33.7s; 4 workers 3.9x; 8 workers
6.5x; 12 workers 7.0x — the July knee (8-12) reproduces; answers BIT-IDENTICAL
at every width (the admissibility line: parallel reads may never change an
answer; consolidation stays serial until the confluence machinery lands).

ops_queue_probe (the dc vision run for real): mixed teach/ask queue, single
writer + 8 readers over versioned frozen bodies, 2 refreezes. Ordering court:
the ask after the teach sees the taught fact across a version bump; all
answers equal the serial twin. Economics, honestly: at trivial per-ask cost
the pool overhead LOSES (0.011s/op vs 0.001s serial) — workers pay off when
per-ask work is real (see 7x above); restart cost amortizes over burst size.

## 2026-09-12 — the walk prototype comes home (walk/, walk_court)

The 2026-09-12 claude.ai session built the reference-walk engine the owner's
ARCHITECTURE.md describes — store of items (name/kind/content/truth/native/
tag/refs) + depth-one walk + ask/return/reject/persist/rank cycle, ~200 lines
(walk/engine/core.py), prose linker ~30 lines (linker.py), plus ErgoAI 3.0
runs (walk/ergo-tests, walk/wide, receipts in walk/docs). Zip landed in
walk/, three hardcoded sandbox paths made script-relative, nothing else
touched.

walk_court (new gate row, 0.1s): every documented number re-derived on this
machine — rocket walk settles at 23 pulls, 9 persist / 7 rejected each with
a stated reason; +50 noise items -> pulls 23 -> 23, persist identical, no
noise reached; desk law (native set aside, negative relevance refuses,
truth-0 present-not-for-this, truth never touched by relevance); forum post
-> 114 items, copper touched by 4 sentences, walk from copper settles at 92
pulls. Sabotage arm: wiring one noise item into the path trips the
indifference check (court can fail). Mutation-verified: breaking the
refusal law in core.py -> exact row red, exit 1; restored -> green.

Full gate after adding the row: 27 passed, 0 failed, 2 skipped
(cloth_run_120 slow-skipped, onefile_install_court), 26.6s at jobs=10.

Ergo rows NOT courted here: ErgoAI not installed on this machine (51MB
installer, bandwidth rule — owner's call). walk/docs/RESULTS.md,
PROBE-RESULTS.md, EMIT-RESULTS.md carry those session receipts; the emitter
loss table (ergo 0 lost / prolog 6 / rdf 7) is session-attested, not yet a
gate row.
