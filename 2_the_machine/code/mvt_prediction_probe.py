"""
Prediction probe (addendum priority #3): can Isaac predict the next frame
of a moving pixel? And does it MEMORIZE the transition table or GENERALIZE
the motion rule?

Honest, in-mechanism representation: each frame is tokenized losslessly as
its flattened bit-string (e.g. '000010000'). A trajectory is a sequence of
such frame-tokens. Prediction = next-token prediction over frame-tokens
(Isaac's native strength). No feature extraction: the token IS the frame.

Two tests:
  (1) SEEN-transition generalization: train on many trajectories, test on
      NOVEL trajectories whose individual frame->frame steps were all seen.
      Expect HIGH -- this is the transition table being recalled.
  (2) HELD-OUT-transition generalization: remove one specific frame->frame
      step from training entirely, then require it at test. Expect FAIL --
      absolute frame-tokens carry no notion of 'shift by +1', so an unseen
      step has no door.

The boundary mirrors counting exactly: the door net recalls what it has seen
the shape of, but does not extrapolate a RELATIVE rule from ABSOLUTE tokens.
That tells us prediction needs relative/delta encoding to truly generalize.
"""

import numpy as np
from isaac import Isaac

K = 3
N = K * K


def frame_token(idx):
    """Lossless token for a single-on-pixel frame with the 1 at flat index idx."""
    bits = ["0"] * N
    bits[idx] = "1"
    return "".join(bits)


def horiz_trajectories():
    """All left-to-right single-row sweeps: pixel moves across each row."""
    trajs = []
    for r in range(K):
        trajs.append([frame_token(r * K + c) for c in range(K)])
    return trajs


def vert_trajectories():
    """All top-to-bottom single-column sweeps."""
    trajs = []
    for c in range(K):
        trajs.append([frame_token(r * K + c) for r in range(K)])
    return trajs


def teach(isaac, trajs):
    for t in trajs:
        isaac.observe(t)
    isaac.consolidate()


def predict_next_frame(isaac, context_frames):
    pn = isaac.predict_next(context_frames)
    return pn["prediction"] if pn else None


def eval_trajectories(isaac, trajs):
    """For each trajectory, give frames[:-1] context one step at a time,
    predict the next, compare to truth."""
    ok = total = 0
    for t in trajs:
        for i in range(1, len(t)):
            ctx = t[:i]
            pred = predict_next_frame(isaac, ctx)
            total += 1
            if pred == t[i]:
                ok += 1
    return ok, total


def main():
    print("=" * 70)
    print("  PREDICTION PROBE — moving pixel, next-frame")
    print("=" * 70)

    # ---- Test 1: seen-transition recall ----
    # Train on horizontal sweeps; test on the SAME transitions via the same
    # trajectories (pure transition-table recall sanity check).
    isaac = Isaac()
    train = horiz_trajectories()
    teach(isaac, train)
    ok, tot = eval_trajectories(isaac, train)
    print(f"\n  [1] recall seen transitions (horizontal sweeps)")
    print(f"      {ok}/{tot} = {ok/tot:.0%}  "
          f"(expect ~100%: every step was taught)")

    # ---- Test 2: cross-axis generalization ----
    # Train ONLY on horizontal sweeps. Test on VERTICAL sweeps -- the frames
    # overlap (same 9 tokens) but the transitions (down by +K) were never seen.
    isaac2 = Isaac()
    teach(isaac2, horiz_trajectories())
    vt = vert_trajectories()
    ok2, tot2 = eval_trajectories(isaac2, vt)
    print(f"\n  [2] generalize to UNSEEN transitions (vertical sweeps)")
    print(f"      {ok2}/{tot2} = {ok2/tot2:.0%}  "
          f"(expect ~0%: 'shift down' was never a taught door)")

    print("\n" + "=" * 70)
    print("  READING:")
    print("  High [1], low [2] => the net RECALLS taught transitions but does")
    print("  not EXTRAPOLATE a relative motion rule from absolute frame tokens.")
    print("  Same boundary as counting: memorization yes, rule-generalization")
    print("  no -- until the representation encodes RELATIVE change (delta).")
    print("=" * 70)


if __name__ == "__main__":
    main()
