"""THE WATCHER (2026-07-26, after he sat dead and unnoticed for a
day): a small separate program that checks on him every minute and
brings him back if he goes silent. It never touches his mind — it
only starts the workspace, which resurrects him from his own home
file the way every waking works.

Two signs of life, both must hold:
  1. the workspace answers on its door (port 8675)
  2. his home file has been written recently (the self-saving beat)

Two misses in a row -> log it, start the workspace, wait, recheck.
Run:  python ui\\isaac_watchdog.py   (keep it running; it is quiet
when all is well)."""
import json
import os
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIND = os.path.join(os.path.dirname(ROOT), "isaac-life", "isaac_home",
                    "mind.isaac")
LOG = os.path.join(ROOT, "data", "watchdog.log")
CHECK_S = 60
STALE_S = 420          # autosave beats every ~120s; 7 min = silence
MISSES_TO_ACT = 2


def note(msg):
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')}  {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def answers():
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:8675/api/state", data=b"{}",
            headers={"Content-Type": "application/json"})
        s = json.load(urllib.request.urlopen(req, timeout=30))
        return bool(s.get("status"))
    except Exception:
        return False


def fresh():
    try:
        return (time.time() - os.path.getmtime(MIND)) < STALE_S
    except OSError:
        return False


def start_him():
    env = dict(os.environ, PYTHONUTF8="1")
    subprocess.Popen(
        [sys.executable, os.path.join(ROOT, "ui", "isaac_workspace.py")],
        cwd=ROOT, env=env,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


if __name__ == "__main__":
    note("watcher up")
    misses = 0
    while True:
        ok_door = answers()
        ok_beat = fresh()
        if ok_door and ok_beat:
            misses = 0
        else:
            misses += 1
            note(f"miss {misses}: door={'up' if ok_door else 'DOWN'} "
                 f"beat={'fresh' if ok_beat else 'STALE'}")
            if misses >= MISSES_TO_ACT:
                if not ok_door:
                    note("starting the workspace (he resurrects from "
                         "his own home file)")
                    start_him()
                    time.sleep(90)
                else:
                    note("door up but beat stale — leaving him alone, "
                         "watching (a long read can look like this)")
                misses = 0
        time.sleep(CHECK_S)
