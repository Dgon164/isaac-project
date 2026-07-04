"""
EXPLORATION (not a pass/fail test): do scene TYPES form on their own?

Teach Isaac several mechanisms through observe_spatial (three four-bars at
different scales/poses, two rigid plates), then let the ordinary
consolidation run and report what crystallizes. The known engine limit
applies (crystals store membership, not uptake — audit 2.3), so this is a
measurement of where the static crystallizer gets to on bridged facts,
recorded honestly either way.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from isaac import Isaac

rng = np.random.default_rng(29)


def fourbar_frames(scale=1.0, rot=0.0, tx=0.0, ty=0.0, T=480, noise=0.003):
    crank, coupler, rocker, ground = (x * scale for x in (2., 7., 6., 8.))
    c, s = np.cos(rot), np.sin(rot)
    p0 = np.array([tx, ty])
    p3 = p0 + ground * np.array([c, s])
    out = []
    for k in range(T):
        th = 4 * np.pi * k / T + rot
        p1 = p0 + crank * np.array([np.cos(th), np.sin(th)])
        d = np.linalg.norm(p3 - p1)
        a = (coupler ** 2 - rocker ** 2 + d ** 2) / (2 * d)
        h = np.sqrt(max(coupler ** 2 - a ** 2, 0.0))
        u = (p3 - p1) / d
        p2 = p1 + a * u + h * np.array([-u[1], u[0]])
        out.append(np.stack([p0, p1, p2, p3])
                   + rng.normal(0, noise * scale, (4, 2)))
    return np.array(out)


def plate_frames(size=3.0, T=360, noise=0.003):
    sq = np.array([[0., 0.], [0., size], [size * 0.7, size], [size * 0.7, 0.]])
    out = []
    for k in range(T):
        th = 1.2 * np.sin(2 * np.pi * k / 180)
        c, s = np.cos(th), np.sin(th)
        out.append(sq @ np.array([[c, -s], [s, c]]).T
                   + rng.normal(0, noise, (4, 2)))
    return np.array(out)


isaac = Isaac()
scenes = {
    "fb1": fourbar_frames(1.0, 0.0),
    "fb2": fourbar_frames(2.2, 0.7, 4, -1),
    "fb3": fourbar_frames(0.6, 2.1, -3, 2),
    "plateA": plate_frames(3.0),
    "plateB": plate_frames(1.4),
}
for label, frames in scenes.items():
    rel = isaac.observe_spatial(frames, label=label)
    print(f"{label:7s} parts {sorted(len(p) for p in rel['parts'])}  "
          f"hinges {len(rel['hinges'])}  signature {rel['signature']}")

# cross-scene comparisons Isaac can already make from stored relations
print("\ncompare_scenes across everything:")
labels = list(scenes)
for i in range(len(labels)):
    for j in range(i + 1, len(labels)):
        v = isaac.compare_scenes(labels[i], labels[j])
        print(f"  {labels[i]:7s} vs {labels[j]:7s} -> {v['verdict']}"
              f"  (gap {v.get('signature_gap')})")

# now: does consolidation form any TYPE over the bridged tokens?
isaac.consolidate()
types = [n for n in isaac.net.all_nodes() if str(n).startswith("type:")]
print(f"\nafter consolidate(): {len(types)} types formed over bridged facts")
for t in types[:12]:
    members = isaac.net.get_meta(t, "members") or []
    print(f"  {t}: {list(members)[:8]}")
print("\nHONEST READING: compare_scenes (relation-profile matching) already")
print("groups the four-bars and separates the plates; whether the static")
print("crystallizer ALSO discovers that grouping is bounded by its known")
print("membership-only, null-free design (audit 2.3/2.4) — recorded above.")
