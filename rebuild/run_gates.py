"""
THE GATE RUNNER — one command, one exit code.

    python rebuild/run_gates.py [--slow] [--jobs N]

--jobs N runs rows N at a time across cores (each row is its own
process; every harness writes only to unique temp dirs, so rows are
concurrency-safe). Default 1 = serial, identical output order either
way. --jobs 0 picks a sensible width for this machine.

Runs every verification harness and aggregates exit codes. Green is
defined HERE, by exit code, not by reading stdout:

    exit 0   all rows passed (skips allowed)
    exit 1   at least one row failed

Per-row codes: 0 = pass, 77 = skip (missing input data — reported,
not a failure), anything else = fail. Rows marked slow (the 20-minute
CLOTH 120-passage exam) run only with --slow; skipping them is printed
loudly, never silently.

Each row prints its wall-clock time (standing rule: every run prints
per-stage wall-clock). On failure the last lines of the row's output
are echoed so the failing check is visible without rerunning.

Added 2026-08-24, record-repair step N2 (see TEARDOWN_2026-08-23.md:
"a test that cannot fail is not a test").
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
PY = sys.executable

# (name, command, slow)
ROWS = [
    ("battery",                [PY, os.path.join(ROOT, "code", "isaac.py")], False),
    ("worstcase_baseline",     [PY, os.path.join(HERE, "worstcase_baseline.py")], False),
    ("scale_eval",             [PY, os.path.join(HERE, "scale_eval.py")], False),
    ("pemdas_eval_test",       [PY, os.path.join(HERE, "pemdas_eval_test.py")], False),
    ("selection_feedback",     [PY, os.path.join(HERE, "selection_feedback_test.py")], False),
    ("logic_bridge_probe",     [PY, os.path.join(HERE, "logic_bridge_probe.py")], False),
    ("bridge_soundness_probe", [PY, os.path.join(HERE, "bridge_soundness_probe.py")], False),
    ("onefile_probe",          [PY, os.path.join(HERE, "onefile_probe.py")], False),
    ("onefile_install_court",  [PY, os.path.join(HERE, "onefile_install_court.py")], False),
    ("cloth_trivial_baseline", [PY, os.path.join(HERE, "cloth_trivial_baseline.py")], False),
    ("parts_courts",           [PY, os.path.join(HERE, "parts_courts.py")], False),
    ("ask_logic_court",        [PY, os.path.join(HERE, "ask_logic_court.py")], False),
    ("z3_law_scan",            [PY, os.path.join(HERE, "z3_law_scan.py")], False),
    ("s0_composition_probe",   [PY, os.path.join(HERE, "s0_composition_probe.py")], False),
    ("binder_court",           [PY, os.path.join(HERE, "binder_court.py")], False),
    ("playland_court",         [PY, os.path.join(HERE, "playland_court.py")], False),
    ("cloth_run_120",          [PY, os.path.join(HERE, "cloth_run.py"), "120"], True),
]


def run_row(name, cmd, env):
    t0 = time.perf_counter()
    r = subprocess.run(cmd, env=env, cwd=ROOT, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    return name, r, time.perf_counter() - t0


def main():
    slow = "--slow" in sys.argv
    jobs = 1
    if "--jobs" in sys.argv:
        jobs = int(sys.argv[sys.argv.index("--jobs") + 1])
        if jobs == 0:
            jobs = min(len(ROWS), max(2, (os.cpu_count() or 8) // 3))
    env = dict(os.environ, PYTHONUTF8="1")
    print("=" * 64)
    print(f"  GATES — exit code is the verdict"
          + (f"   (jobs={jobs})" if jobs > 1 else ""))
    print("=" * 64)
    outcomes = []
    t_all = time.perf_counter()
    to_run = []
    for name, cmd, is_slow in ROWS:
        if is_slow and not slow:
            print(f"  {name:<24} SLOW-SKIPPED  (rerun with --slow)")
            outcomes.append((name, "SLOW-SKIPPED"))
            continue
        if not os.path.exists(cmd[1]):
            print(f"  {name:<24} SKIP          (file not built yet)")
            outcomes.append((name, "SKIP"))
            continue
        to_run.append((name, cmd))

    results = {}
    if jobs > 1:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            futs = [pool.submit(run_row, n, c, env) for n, c in to_run]
            for f in futs:
                name, r, dt = f.result()
                results[name] = (r, dt)
    else:
        for n, c in to_run:
            name, r, dt = run_row(n, c, env)
            results[name] = (r, dt)

    for name, _ in to_run:
        r, dt = results[name]
        if r.returncode == 0:
            verdict = "PASS"
        elif r.returncode == 77:
            verdict = "SKIP"
        else:
            verdict = f"FAIL({r.returncode})"
        outcomes.append((name, verdict))
        print(f"  {name:<24} {verdict:<13} {dt:7.1f}s")
        if r.returncode not in (0, 77):
            tail = (r.stdout + "\n" + r.stderr).strip().splitlines()[-15:]
            print("    --- last lines of failing row ---")
            for line in tail:
                print("    " + line)

    fails = [n for n, v in outcomes if v.startswith("FAIL")]
    skips = [n for n, v in outcomes if v in ("SKIP", "SLOW-SKIPPED")]
    print("-" * 64)
    print(f"  total {time.perf_counter() - t_all:.1f}s   "
          f"{len(outcomes) - len(fails) - len(skips)} passed, "
          f"{len(fails)} failed, {len(skips)} skipped")
    if skips:
        print(f"  skipped: {', '.join(skips)}")
    if fails:
        print(f"  GATE: FAIL ({', '.join(fails)})")
    else:
        print("  GATE: PASS")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
