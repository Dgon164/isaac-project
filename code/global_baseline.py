"""
GLOBAL — the baseline. The reference everything else differences against.

Spec (yours): low, fast, heuristic. It runs every frame over the whole field,
so it must be cheap and approximate. A rough "what's normal here" is enough;
the deviations carry the information.

Two cheap flavors of "normal", both O(cells), no history beyond one value/cell:

  TEMPORAL global  = per-cell running average (EMA): "what this cell usually is."
      baseline += a * (current - baseline)
      -> furniture/acclimation: a thing that appears then stays gets absorbed.

  FIELD-RELATIVE global = each cell vs the field's prevailing value right now:
      deviation = current - field_mean
      -> the inversion: rare value pops, whichever it is (object in empty field,
         hole in full field).

"Global working" = it tracks normal, fades furniture, isolates deviation, and is
cheap. We validate on controlled synthetic input so ground truth is known. It
drops onto Snake frames unchanged.
"""

import time
import numpy as np


class GlobalBaseline:
    """Per-cell EMA. One line of real work. alpha = adaptation rate."""
    def __init__(self, shape, alpha=0.1):
        self.b = np.zeros(shape, dtype=float)
        self.alpha = alpha

    def update(self, frame):
        self.b += self.alpha * (frame - self.b)        # the whole heuristic
        return self.b

    def temporal_deviation(self, frame):
        return frame - self.b                            # vs its own history

    @staticmethod
    def field_deviation(frame):
        return frame - frame.mean()                      # vs field's prevailing value


def amap(arr, thresh=0.25):
    """Render a deviation map: + strong positive, - strong negative, . quiet."""
    out = []
    for row in arr:
        s = ""
        for v in row:
            s += "+" if v > thresh else ("-" if v < -thresh else ".")
        out.append("    " + s)
    return "\n".join(out)


def scen_moving_dot():
    """Static background + one moving dot. Global should learn the background;
    deviation should isolate the dot."""
    print("=" * 60)
    print("  1) MOVING DOT on static background")
    print("=" * 60)
    H, W = 7, 7
    g = GlobalBaseline((H, W), alpha=0.2)
    # static background: a fixed bar
    bg = np.zeros((H, W)); bg[5, 1:6] = 1
    for t in range(30):                       # let baseline learn the background
        frame = bg.copy()
        frame[2, t % W] = 1                   # dot sweeps across
        g.update(frame)
    # now test one frame
    frame = bg.copy(); frame[2, 3] = 1
    dev = g.temporal_deviation(frame)
    print("  after 30 frames, baseline learned the static bar.")
    print("  current frame's deviation (should light up ONLY the moving dot):")
    print(amap(dev))


def scen_furniture():
    """A thing appears and STAYS. Deviation should spike, then fade as the
    baseline absorbs it (acclimation)."""
    print("\n" + "=" * 60)
    print("  2) FURNITURE — appears, then fades into 'normal'")
    print("=" * 60)
    H, W = 5, 5
    g = GlobalBaseline((H, W), alpha=0.3)
    blank = np.zeros((H, W))
    for _ in range(10):
        g.update(blank)                       # settle on empty
    obj = np.zeros((H, W)); obj[1:4, 1:4] = 1  # a square appears and stays
    peak = []
    for t in range(12):
        dev = g.temporal_deviation(obj)
        peak.append(round(float(dev.max()), 2))
        g.update(obj)
    print("  square appears at t=0 and never leaves.")
    print("  peak deviation per frame:", peak)
    print("  -> spikes, then decays toward 0: it became furniture.")


def scen_inversion():
    """Field fills up over time (snake growing). Show that the FIELD-RELATIVE
    deviation flips: object pops when field is empty, holes pop when field is
    full. Per-cell EMA alone does NOT do this -- it's the field term's job."""
    print("\n" + "=" * 60)
    print("  3) INVERSION — what's salient flips as the field fills")
    print("=" * 60)
    H, W = 5, 5
    for fill, label in [(0.12, "nearly EMPTY field"), (0.88, "nearly FULL field")]:
        frame = (np.random.default_rng(0).random((H, W)) < fill).astype(float)
        dev = GlobalBaseline.field_deviation(frame)
        rare_is_on = fill < 0.5
        print(f"\n  {label} (fill={fill:.0%}):")
        print(amap(frame - 0.5, thresh=0.0).replace("+", "#").replace("-", "."))
        print("  field-relative deviation (what pops):")
        print(amap(dev, thresh=0.3))
        print(f"  -> the rare cells carry the deviation "
              f"({'objects' if rare_is_on else 'holes'} pop). "
              f"figure/ground inverted by the field term.")


def cost():
    print("\n" + "=" * 60)
    print("  COST — is it cheap enough to run every frame?")
    print("=" * 60)
    for (H, W) in [(15, 15), (100, 100), (500, 500)]:
        g = GlobalBaseline((H, W), alpha=0.1)
        f = np.random.default_rng(0).random((H, W))
        t0 = time.perf_counter()
        for _ in range(100):
            g.update(f)
            g.temporal_deviation(f)
            GlobalBaseline.field_deviation(f)
        dt = (time.perf_counter() - t0) / 100 * 1000
        print(f"  {H}x{W:>3}: {dt:6.3f} ms/frame "
              f"({'fine for 60fps' if dt < 16 else 'too slow'})")


if __name__ == "__main__":
    scen_moving_dot()
    scen_furniture()
    scen_inversion()
    cost()
