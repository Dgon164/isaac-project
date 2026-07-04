"""
WORLD GM — SPATIAL WORLDS (step 5, 2026-07-03). The two newest threads
close into one loop: the spatial sandbox's forward solver IS a world
generator, so the GM can now deal mechanism worlds — and the spatial
perceiver is how Isaac plays them.

Primitives programmed: bars, pins, a crank. Worlds sampled: lengths, pose.
Never written as answers: the ground link (emerges from two pins), the
fold/extend geometry that betrays an occluded link, the absence of
structure in the null world.

Information is EARNED:
  observe(n)   n frames under an erratic, reversing drive (cost n)
  run(theta)   ONE frame at a crank angle of the player's choosing —
               the probe verb; fold/extend extremes are reached by ASKING
               for them, not waiting for them (cost 5)
  submit(...)  bar lengths (or 'none') graded against hidden truth (cost 20)

Worlds:
  S1  visible four-bar, random lengths/pose   -> all 4 lengths incl. ground
  S2  OCCLUDED four-bar (crank tip hidden)    -> the 2 invisible lengths
      must be inferred from the bounded pair's fold/extend limits
  S3  null world (independent walkers)        -> the honest 'none'
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                "..", "spatial")))
from engine import Mechanism, classify_edges

rng = random.Random(31)
NOISE = 0.002


def line(c="-", n=66):
    print(c * n)


# ═══════════════════════════════ THE GM ═══════════════════════════════
class SpatialWorld:
    def __init__(self, kind, budget=700):
        self.kind = kind
        self.budget, self.spent = budget, 0
        self.queries = dict(observe=0, run=0, submit=0)
        if kind == "null":
            self.truth = None
            return
        while True:
            crank = rng.uniform(1.0, 2.5)
            coupler, rocker, ground = (rng.uniform(4.0, 9.0) for _ in range(3))
            lens = sorted([crank, coupler, rocker, ground])
            if (lens[0] + lens[3] <= lens[1] + lens[2]
                    and min(crank, coupler, rocker, ground) == crank):
                break
        self.lengths = dict(crank=crank, coupler=coupler,
                            rocker=rocker, ground=ground)
        rot, tx, ty = rng.uniform(0, 6.28), rng.uniform(-5, 5), rng.uniform(-5, 5)
        c, s = math.cos(rot), math.sin(rot)
        self.pin0 = (tx, ty)
        self.pin3 = (tx + ground * c, ty + ground * s)
        self.rot = rot
        m = Mechanism(points=[list(self.pin0),
                              [tx + crank * c, ty + crank * s],
                              [tx, ty + 5.0], list(self.pin3)])
        # place rocker tip legally: circle intersection from crank start
        d = math.dist(m.points[1], self.pin3)
        a = (coupler ** 2 - rocker ** 2 + d ** 2) / (2 * d)
        h = math.sqrt(max(coupler ** 2 - a ** 2, 1e-9))
        ux, uy = ((self.pin3[0] - m.points[1][0]) / d,
                  (self.pin3[1] - m.points[1][1]) / d)
        m.points[2] = [m.points[1][0] + a * ux - h * uy,
                       m.points[1][1] + a * uy + h * ux]
        m.locked[(0, 1)] = crank
        m.locked[(1, 2)] = coupler
        m.locked[(2, 3)] = rocker
        m.pin(0); m.pin(3)
        self.m = m
        self.th = 0.0
        self.visible = [0, 2, 3] if kind == "occluded" else [0, 1, 2, 3]
        self.truth = sorted([crank, coupler, rocker, ground])

    def _frame(self):
        if self.kind == "null":
            for w in self.walkers:
                w[0] += rng.gauss(0, 0.08); w[1] += rng.gauss(0, 0.08)
            pts = [w[:] for w in self.walkers]
        else:
            pts = [self.m.points[i] for i in self.visible]
        return [[c + rng.gauss(0, NOISE) for c in p] for p in pts]

    def observe(self, n):
        assert self.spent + n <= self.budget
        self.spent += n; self.queries["observe"] += n
        if self.kind == "null":
            self.walkers = [[rng.uniform(-3, 3), rng.uniform(-3, 3)]
                            for _ in range(4)]
            return [self._frame() for _ in range(n)]
        out = []
        for _ in range(n):
            self.th += rng.choice([0.5, 1.0, 1.0, 2.0, -0.5, 0.1]) * 0.05
            self.m.drive(1,
                         self.pin0[0] + self.lengths["crank"] * math.cos(self.th + self.rot),
                         self.pin0[1] + self.lengths["crank"] * math.sin(self.th + self.rot),
                         sweeps=60)
            out.append(self._frame())
        return out

    def run(self, theta):
        """The probe verb: drive the crank to a CHOSEN angle, get one frame."""
        assert self.spent + 5 <= self.budget
        self.spent += 5; self.queries["run"] += 1
        if self.kind == "null":
            return self._frame()
        self.m.drive(1,
                     self.pin0[0] + self.lengths["crank"] * math.cos(theta + self.rot),
                     self.pin0[1] + self.lengths["crank"] * math.sin(theta + self.rot),
                     sweeps=80)
        return self._frame()

    def submit(self, lengths):
        """Grade sorted bar lengths vs hidden truth (or 'none' honesty)."""
        self.spent += 20; self.queries["submit"] += 1
        if self.truth is None:
            return dict(correct=(lengths is None),
                        detail="refusal" if lengths is None else "INVENTED")
        if lengths is None:
            return dict(correct=False, detail="false refusal")
        got = sorted(lengths)
        if len(got) != 4:
            return dict(correct=False, detail=f"{len(got)} lengths, want 4")
        errs = [abs(g - t) / t for g, t in zip(got, self.truth)]
        return dict(correct=max(errs) < 0.02, max_rel_err=max(errs),
                    detail=", ".join(f"{g:.3f}/{t:.3f}"
                                     for g, t in zip(got, self.truth)))


# ══════════════════════════════ THE PLAYER ═══════════════════════════════
def play(world):
    """The player NEVER sees world.kind — it decides from what it perceives:
    4 locked edges -> a complete four-bar, submit; fewer locked + a varying
    pair -> hidden links, EARN the fold/extend extremes by buying probe
    angles; nothing locked -> refuse."""
    frames = world.observe(360)
    v = classify_edges(frames)
    locked = {p: d["mean"] for p, d in v.items() if d["kind"] == "locked"}

    if not locked:
        return world.submit(None), "nothing locked anywhere -> submitted 'none'"

    if len(locked) == 4:
        return world.submit(list(locked.values())), \
            "4 locked edges = the 4 bars (ground included, undeclared)"

    # fewer bars than a four-bar needs -> hidden links behind the varying
    # pair. 360 erratic frames gave ~2 cycles: too weak for the bounded
    # verdict (its surrogate null rightly refuses). So EARN the extremes:
    # buy frames at 36 chosen crank angles -- fold and extend
    # configurations by request, not by luck.
    varying = [p for p, d in v.items() if d["kind"] != "locked"]
    probe_frames = [world.run(2 * math.pi * k / 36) for k in range(36)]
    all_frames = frames + probe_frames
    (bi, bj) = max(varying, key=lambda p: max(
        math.dist(f[p[0]], f[p[1]]) for f in all_frames) - min(
        math.dist(f[p[0]], f[p[1]]) for f in all_frames))
    ds = [math.dist(f[bi], f[bj]) for f in all_frames]
    lo, hi = min(ds), max(ds)
    crank = (hi - lo) / 2
    coupler = (hi + lo) / 2
    claim = list(locked.values()) + [crank, coupler]
    return world.submit(claim), \
        (f"{len(locked)} locked + 1 varying pair; bought 36 probe angles -> "
         f"fold/extend: hidden crank {crank:.3f}, hidden coupler {coupler:.3f}")


def main():
    print("WORLD GM — SPATIAL: the sandbox generates, the perceiver plays,")
    print("the GM only grades. Information earned, never given.\n")
    score = 0
    for kind, label in [("visible", "S1 visible four-bar"),
                        ("occluded", "S2 occluded four-bar (crank tip hidden)"),
                        ("null", "S3 null world (walkers)")]:
        world = SpatialWorld(kind)
        res, note = play(world)
        ok = res["correct"]
        score += ok
        line()
        print(f"{label}")
        print(f"  {note}")
        print(f"  GM grade: {'CORRECT' if ok else 'WRONG'}  "
              f"({res.get('detail', '')})")
        print(f"  earned with {world.queries['observe']} observations, "
              f"{world.queries['run']} probes  "
              f"[{world.spent}/{world.budget} budget]")
    line("=")
    print(f"SCORE {score}/3 — "
          f"{'the loop is closed: generator, perceiver, examiner' if score == 3 else 'GAPS (see above)'}")
    line("=")


if __name__ == "__main__":
    main()
