"""
ATTENTION LEVELS — invisible vs background vs foreground, with a movable cutoff.

The old tracker had ONE threshold: salient or not. That collapses two different
things into 'not salient':
    - INVISIBLE : nothing is there (no presence)
    - BACKGROUND: something IS there, but it's stable / normal (furniture)
These must be kept apart. Background is *recorded* (we know it's there); invisible
is nothing. Only foreground is *attended* by default.

  level 2  FOREGROUND : present AND deviates from normal   -> attended, tracked
  level 1  BACKGROUND : present but not deviating           -> recorded, under radar
  level 0  INVISIBLE  : no presence                         -> nothing

ATTENTION is a movable floor on this ladder:
    attend(floor=2)  -> foreground only          (focused; the default)
    attend(floor=1)  -> background + foreground  (thorough: pull background in)
    attend(floor=0)  -> everything, even empty   (paranoid scan)

'Attention higher than background' = floor 2. 'Attention set below background for
a more thorough assessment' = floor 1. The knob is one number.

Presence = what's in the frame now. Novelty = how far it broke from the baseline
('what's normal here', the GlobalBaseline retina). Two signals, three levels.
"""

import numpy as np
from global_baseline import GlobalBaseline

INVISIBLE, BACKGROUND, FOREGROUND = 0, 1, 2
_GLYPH = {INVISIBLE: ".", BACKGROUND: ":", FOREGROUND: "#"}


class Attention:
    def __init__(self, shape, alpha=0.35, novelty=0.25, presence=0.05):
        self.base = GlobalBaseline(shape, alpha=alpha)
        self.novelty = novelty       # deviation above which a thing is foreground
        self.presence = presence     # value above which a cell counts as 'there'

    def settle(self, frame, n=1):
        for _ in range(n):
            self.base.update(frame)

    def levels(self, frame):
        """Classify every cell into INVISIBLE / BACKGROUND / FOREGROUND."""
        dev = self.base.temporal_deviation(frame)            # novelty vs normal
        present = frame > self.presence
        novel = dev > self.novelty
        out = np.where(present, BACKGROUND, INVISIBLE)
        out = np.where(present & novel, FOREGROUND, out)
        return out

    def attend(self, frame, floor=FOREGROUND):
        """Boolean mask of cells at or above the attention floor.
        Lower floor = more thorough (background, then even invisible)."""
        return self.levels(frame) >= floor

    def update(self, frame):
        """Let normal absorb the frame — a thing that stops moving fades to
        background (acclimation). Attention does NOT update during a thorough
        probe; only during normal living."""
        self.base.update(frame)

    @staticmethod
    def render(level_map):
        return "\n".join("    " + "".join(_GLYPH[int(v)] for v in row)
                         for row in level_map)


# ── demo ───────────────────────────────────────────────────────────
def main():
    from turtle_inventory import TURTLE, signature, recognize, teach_shape
    from isaac import Isaac

    isaac = Isaac()
    teach_shape(isaac, TURTLE, "turtle")
    isaac.consolidate()

    H, W = 9, 22
    att = Attention((H, W))
    bar = np.zeros((H, W)); bar[7, 2:18] = 1            # static furniture
    att.settle(bar, n=10)                               # baseline learns the bar

    # a frame: the learned bar + a turtle that just moved in (novel)
    frame = bar.copy()
    frame[1:4, 8:11] = TURTLE

    print("=" * 72)
    print("  ATTENTION LEVELS  ( . invisible   : background   # foreground )")
    print("=" * 72)
    print("  scene: a settled bar (furniture) + a turtle that just moved in\n")
    print(Attention.render(att.levels(frame)))
    print("\n  -> the turtle is FOREGROUND (#): present AND novel.")
    print("     the bar is BACKGROUND (:): present but absorbed as normal.")
    print("     everything else is INVISIBLE (.): no presence.")

    def assess(floor, label):
        mask = att.attend(frame, floor=floor)
        # segment what's attended and name it
        from attention_tracker import regions
        found = []
        for crop, cen in regions(mask):
            name = recognize(isaac, crop) or "unknown"
            found.append(f"{name}@({cen[0]:.0f},{cen[1]:.0f})")
        print(f"\n  attend(floor={floor}) — {label}")
        print(f"    attended things: {found if found else '(none)'}")

    print("\n" + "-" * 72)
    assess(FOREGROUND, "DEFAULT: attention above background -> only the turtle")
    assess(BACKGROUND, "THOROUGH: attention below background -> the bar surfaces too")

    print("\n  Note: the bar was BACKGROUND the whole time — recorded, known to be")
    print("  there, just under the attention floor. Lowering the floor assessed it")
    print("  without it ever having been invisible. (It reads 'unknown' only")
    print("  because a 16-wide bar isn't a taught shape — the scale wall again.)")

    print("\n" + "=" * 72)
    print("  Attention is now a dial, not a switch. Default: spend it on what")
    print("  changed. On demand: drop it below background for a full sweep. The")
    print("  invisible/background line is kept — absence and furniture are not")
    print("  the same thing.")


if __name__ == "__main__":
    main()
