"""
Isaac — Visual Retina Pipeline Test
====================================

Tests the frame-delta pipeline:
  Frame → subtract reference → bit shift → threshold → observe sparse → matmul

No real video — generates synthetic game frames with moving objects.
Measures every stage independently, then the full pipeline.
"""

import numpy as np
import time


def _div(title):
    print(f"\n{'═' * 65}")
    print(f"  {title}")
    print(f"{'═' * 65}")


# ═══════════════════════════════════════════════════════════════
# Synthetic frame generation
# ═══════════════════════════════════════════════════════════════

def make_background(h, w):
    """Static game background — sky gradient + ground."""
    frame = np.zeros((h, w, 3), dtype=np.uint8)
    # Sky gradient
    for y in range(h // 2):
        blue = int(100 + 100 * (1 - y / (h // 2)))
        frame[y, :] = [blue, blue // 2, 20]
    # Ground
    frame[h // 2:, :] = [30, 80, 30]
    return frame


def add_object(frame, x, y, w, h, color):
    """Add a colored rectangle (enemy, player, item)."""
    f = frame.copy()
    y1, y2 = max(0, y), min(frame.shape[0], y + h)
    x1, x2 = max(0, x), min(frame.shape[1], x + w)
    f[y1:y2, x1:x2] = color
    return f


def make_game_frames(h, w, n_frames=60):
    """Generate a sequence of frames with moving objects."""
    bg = make_background(h, w)
    frames = []

    # Enemy moves left to right
    enemy_x = 0
    enemy_speed = max(1, w // 60)

    # Player stays mostly still, slight movement
    player_x = w // 2
    player_y = h * 3 // 4

    for i in range(n_frames):
        frame = bg.copy()
        # Moving enemy (red)
        ex = (enemy_x + i * enemy_speed) % (w - 30)
        frame = add_object(frame, ex, h // 3, 30, 30, [200, 30, 30])
        # Player (green, slight movement)
        px = player_x + int(3 * np.sin(i * 0.1))
        frame = add_object(frame, px, player_y, 20, 40, [30, 200, 30])
        # HUD: health bar (top-left, changes at frame 30)
        health = 100 if i < 30 else 60
        bar_w = int(w * 0.15 * health / 100)
        frame = add_object(frame, 10, 10, bar_w, 8, [200, 50, 50])
        # Ammo counter (top-right, static)
        frame = add_object(frame, w - 50, 10, 40, 8, [200, 200, 50])
        frames.append(frame)

    return frames


# ═══════════════════════════════════════════════════════════════
# Delta pipeline stages
# ═══════════════════════════════════════════════════════════════

def compute_delta(current, reference):
    """Subtract reference from current. Returns absolute difference."""
    return np.abs(current.astype(np.int16) - reference.astype(np.int16)).astype(np.uint8)


def bit_shift_threshold(delta, shift=2):
    """Shift right to suppress noise. Nonzero after shift = significant change."""
    return delta >> shift


def extract_sparse(shifted_delta):
    """Extract only the nonzero pixels. Returns (positions, values, count)."""
    mask = shifted_delta.sum(axis=2) > 0  # any channel changed
    positions = np.where(mask)
    values = shifted_delta[mask]
    return positions, values, int(mask.sum())


def region_delta_summary(delta, grid_h, grid_w):
    """Summarize delta activity per region. Returns grid of activity levels."""
    h, w = delta.shape[:2]
    rh, rw = h // grid_h, w // grid_w
    activity = np.zeros((grid_h, grid_w), dtype=np.float32)
    for gy in range(grid_h):
        for gx in range(grid_w):
            region = delta[gy * rh:(gy + 1) * rh, gx * rw:(gx + 1) * rw]
            activity[gy, gx] = region.sum() / (rh * rw * 3 * 255)
    return activity


# ═══════════════════════════════════════════════════════════════
# Tests
# ═══════════════════════════════════════════════════════════════

def test_delta_detection():
    """Test frame differencing catches movement."""
    _div("DELTA DETECTION")
    correct = 0

    frames = make_game_frames(240, 320, n_frames=10)

    # Consecutive frame delta
    delta = compute_delta(frames[1], frames[0])
    total_pixels = 240 * 320
    changed = (delta.sum(axis=2) > 0).sum()
    pct = changed / total_pixels * 100

    ok = 0 < pct < 20  # enemy moved, most is static
    correct += ok
    print(f"  {'✓' if ok else '✗'}  frame 0→1: {changed:,} changed pixels "
          f"({pct:.1f}% of {total_pixels:,})")

    # Static frame (same frame twice)
    delta_static = compute_delta(frames[0], frames[0])
    changed_static = (delta_static.sum(axis=2) > 0).sum()
    ok = changed_static == 0
    correct += ok
    print(f"  {'✓' if ok else '✗'}  same frame: {changed_static} changed (should be 0)")

    # Big change (frame 0 vs frame 30 — health bar changed)
    delta_big = compute_delta(frames[5], frames[0])
    changed_big = (delta_big.sum(axis=2) > 0).sum()
    ok = changed_big > changed  # more changed than single step
    correct += ok
    print(f"  {'✓' if ok else '✗'}  frame 0→5: {changed_big:,} changed "
          f"(more than single step)")

    print(f"\n  {correct}/3")
    return correct == 3


def test_bit_shift():
    """Test bit shifting as sensitivity control."""
    _div("BIT SHIFT THRESHOLD")
    correct = 0

    frames = make_game_frames(240, 320, n_frames=5)
    delta = compute_delta(frames[1], frames[0])

    prev_nonzero = None
    for shift in [0, 2, 4, 6]:
        shifted = bit_shift_threshold(delta, shift)
        nonzero = (shifted.sum(axis=2) > 0).sum()
        if prev_nonzero is not None:
            ok = nonzero <= prev_nonzero  # more shift = fewer detections
            correct += ok
            print(f"  {'✓' if ok else '✗'}  shift {shift}: {nonzero:>6,} pixels survive "
                  f"(≤ {prev_nonzero:,})")
        else:
            print(f"       shift {shift}: {nonzero:>6,} pixels survive (baseline)")
            correct += 1
        prev_nonzero = nonzero

    print(f"\n  {correct}/4")
    return correct == 4


def test_sparse_extraction():
    """Test sparse pixel extraction from delta."""
    _div("SPARSE EXTRACTION")
    correct = 0

    frames = make_game_frames(240, 320, n_frames=5)
    delta = compute_delta(frames[1], frames[0])
    shifted = bit_shift_threshold(delta, shift=2)

    positions, values, count = extract_sparse(shifted)
    total = 240 * 320
    compression = (1 - count / total) * 100

    ok = count < total * 0.2  # sparse — less than 20% nonzero
    correct += ok
    print(f"  {'✓' if ok else '✗'}  sparse pixels: {count:,} / {total:,} "
          f"({compression:.1f}% compression)")

    ok = values.shape[0] == count
    correct += ok
    print(f"  {'✓' if ok else '✗'}  values shape: {values.shape} (matches count)")

    ok = len(positions) == 2 and len(positions[0]) == count
    correct += ok
    print(f"  {'✓' if ok else '✗'}  positions: {len(positions[0])} y-coords, "
          f"{len(positions[1])} x-coords")

    print(f"\n  {correct}/3")
    return correct == 3


def test_region_attention():
    """Test region-based attention from deltas."""
    _div("REGION ATTENTION (emergent, not prescribed)")
    correct = 0

    frames = make_game_frames(240, 320, n_frames=10)
    delta = compute_delta(frames[1], frames[0])

    # 4x6 grid of regions
    activity = region_delta_summary(delta, 4, 6)

    # Enemy is in the upper portion, moving — those regions should be active
    active_regions = (activity > 0.001).sum()
    total_regions = 4 * 6
    ok = 0 < active_regions < total_regions
    correct += ok
    print(f"  {'✓' if ok else '✗'}  active regions: {active_regions}/{total_regions} "
          f"(not all, not none)")

    # Quiet regions should have near-zero activity
    quiet = (activity < 0.001).sum()
    ok = quiet > total_regions // 2
    correct += ok
    print(f"  {'✓' if ok else '✗'}  quiet regions: {quiet}/{total_regions} (most are quiet)")

    # Top 3 regions by activity — these are where the action is
    flat = activity.flatten()
    top_3 = flat.argsort()[-3:][::-1]
    top_3_coords = [(idx // 6, idx % 6) for idx in top_3]
    print(f"       top 3 regions: {top_3_coords} (activity: "
          f"{[f'{flat[i]:.4f}' for i in top_3]})")

    # Accumulate attention over multiple frames
    attention_map = np.zeros((4, 6), dtype=np.float32)
    for i in range(1, min(10, len(frames))):
        d = compute_delta(frames[i], frames[i - 1])
        attention_map += region_delta_summary(d, 4, 6)

    hotspots = (attention_map > attention_map.mean()).sum()
    ok = hotspots > 0
    correct += ok
    print(f"  {'✓' if ok else '✗'}  accumulated hotspots over 9 frames: {hotspots} regions")
    print(f"       attention map (higher = more activity):")
    for row in range(4):
        vals = " ".join(f"{attention_map[row, c]:>6.3f}" for c in range(6))
        print(f"         [{vals}]")

    print(f"\n  {correct}/3")
    return correct == 3


def test_matmul_on_sparse():
    """Test matmul inference on sparse delta — the full pipeline endpoint."""
    _div("MATMUL ON SPARSE DELTA")
    correct = 0

    frames = make_game_frames(240, 320, n_frames=5)
    delta = compute_delta(frames[1], frames[0])
    shifted = bit_shift_threshold(delta, shift=2)
    _, values, count = extract_sparse(shifted)

    # Flatten sparse values as input vector
    if count > 0:
        x = values.flatten().astype(np.float32)
        # Simulated weight matrix: 10 possible "events" detected from visual delta
        W = np.random.randn(10, len(x)).astype(np.float32) * 0.01
        W[0, :100] = 0.1  # event 0 responds to first region of changes

        t0 = time.perf_counter()
        runs = 1000
        for _ in range(runs):
            y = W @ x
        t = (time.perf_counter() - t0) / runs * 1000

        ok = t < 16.67
        correct += ok
        print(f"  {'✓' if ok else '✗'}  sparse matmul: {len(x):,} inputs → 10 outputs "
              f"in {t:.3f}ms")
    else:
        correct += 1
        print(f"  ✓  no changes (static frame)")

    # Compare: full frame matmul vs sparse
    x_full = frames[1].flatten().astype(np.float32)
    W_full = np.random.randn(10, len(x_full)).astype(np.float32) * 0.01

    t0 = time.perf_counter()
    runs = 100
    for _ in range(runs):
        y = W_full @ x_full
    t_full = (time.perf_counter() - t0) / runs * 1000

    x_sparse = values.flatten().astype(np.float32) if count > 0 else np.zeros(1)
    W_sparse = np.random.randn(10, len(x_sparse)).astype(np.float32) * 0.01

    t0 = time.perf_counter()
    runs = 1000
    for _ in range(runs):
        y = W_sparse @ x_sparse
    t_sparse = (time.perf_counter() - t0) / runs * 1000

    speedup = t_full / max(t_sparse, 0.001)
    ok = t_sparse < t_full
    correct += ok
    print(f"  {'✓' if ok else '✗'}  full frame: {t_full:.3f}ms vs sparse: "
          f"{t_sparse:.3f}ms ({speedup:.0f}x faster)")

    print(f"\n  {correct}/2")
    return correct == 2


def test_full_pipeline():
    """Full pipeline timing: capture → delta → shift → sparse → matmul → decide."""
    _div("FULL PIPELINE — per frame budget")

    resolutions = [(240, 320, "320×240"), (480, 640, "480p"), (720, 1280, "720p")]
    all_pass = True

    for h, w, label in resolutions:
        frames = make_game_frames(h, w, n_frames=5)
        reference = frames[0].copy()

        times = {"delta": [], "shift": [], "sparse": [], "regions": [],
                 "matmul": [], "total": []}

        for i in range(1, len(frames)):
            t_total_start = time.perf_counter()

            # Stage: delta
            t0 = time.perf_counter()
            delta = compute_delta(frames[i], reference)
            times["delta"].append(time.perf_counter() - t0)

            # Stage: bit shift
            t0 = time.perf_counter()
            shifted = bit_shift_threshold(delta, shift=2)
            times["shift"].append(time.perf_counter() - t0)

            # Stage: sparse extraction
            t0 = time.perf_counter()
            positions, values, count = extract_sparse(shifted)
            times["sparse"].append(time.perf_counter() - t0)

            # Stage: region attention
            t0 = time.perf_counter()
            activity = region_delta_summary(shifted, 4, 6)
            times["regions"].append(time.perf_counter() - t0)

            # Stage: matmul on sparse (if any changes)
            t0 = time.perf_counter()
            if count > 0:
                x = values.flatten().astype(np.float32)
                W = np.random.randn(10, len(x)).astype(np.float32) * 0.01
                y = W @ x
            times["matmul"].append(time.perf_counter() - t0)

            # Update reference (slow decay blend)
            reference = ((reference.astype(np.float32) * 0.9 +
                          frames[i].astype(np.float32) * 0.1)).astype(np.uint8)

            times["total"].append(time.perf_counter() - t_total_start)

        avg = {k: np.mean(v) * 1000 for k, v in times.items()}
        total = avg["total"]
        fits = total < 16.67

        if not fits:
            all_pass = False

        print(f"\n  {label} ({'✓' if fits else '✗'} {total:.2f}ms / 16.67ms budget):")
        print(f"    delta:   {avg['delta']:.3f}ms")
        print(f"    shift:   {avg['shift']:.3f}ms")
        print(f"    sparse:  {avg['sparse']:.3f}ms")
        print(f"    regions: {avg['regions']:.3f}ms")
        print(f"    matmul:  {avg['matmul']:.3f}ms")
        print(f"    TOTAL:   {avg['total']:.3f}ms "
              f"({avg['total']/16.67*100:.0f}% of budget)")

    return all_pass


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Isaac — Visual Retina Pipeline Test")
    print("Frame → delta → shift → sparse → observe → decide\n")

    results = {}
    results["delta_detection"] = test_delta_detection()
    results["bit_shift"] = test_bit_shift()
    results["sparse_extraction"] = test_sparse_extraction()
    results["region_attention"] = test_region_attention()
    results["matmul_sparse"] = test_matmul_on_sparse()
    results["full_pipeline"] = test_full_pipeline()

    _div("VISUAL PIPELINE SUMMARY")
    for name, passed in results.items():
        print(f"  {'✓' if passed else '✗'}  {name}")
    total = sum(1 for v in results.values() if v)
    print(f"\n  {total}/{len(results)} visual pipeline tests passed")
