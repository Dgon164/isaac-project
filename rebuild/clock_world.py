"""
CLOCK WORLD — the anti-invariance benchmark, with perfect ground truth.

Everywhere else rotation is nuisance to factor OUT; here rotation IS the
signal: hand angle = the answer. Fine-grained (hour hand moves 0.5deg/min;
720 classes), self-occluding (overlapping hands), and containing a
DISCOVERABLE LAW: theta_hour = 30*H + theta_minute/12 — the consistency
equation of clockness, findable by discover() from extracted angles.

Generator variations: center jitter, radius (scale), hand style (lengths/
widths), stroke noise, optional face tilt. Ground truth: (hour, minute) and
both true angles. Saved to data/clocks_48.npz (gitignored).
"""
import numpy as np

rng = np.random.default_rng(42)
SIZE = 48


def draw_line(img, cy, cx, angle_deg, length, width, val=1.0):
    th = np.deg2rad(angle_deg)
    n = int(length * 3)
    ts = np.linspace(0, length, max(n, 2))
    ys = cy - ts * np.cos(th)
    xs = cx + ts * np.sin(th)
    for off in np.linspace(-(width - 1) / 2, (width - 1) / 2, max(width, 1)):
        oy = ys + off * np.sin(th)
        ox = xs + off * np.cos(th)
        yi = np.clip(np.round(oy).astype(int), 0, SIZE - 1)
        xi = np.clip(np.round(ox).astype(int), 0, SIZE - 1)
        img[yi, xi] = val


def clock(h, m, tilt=0.0):
    img = np.zeros((SIZE, SIZE))
    cy = SIZE / 2 + rng.uniform(-3, 3)
    cx = SIZE / 2 + rng.uniform(-3, 3)
    R = rng.uniform(0.30, 0.44) * SIZE
    # face ring + ticks (double tick marks 12: the orientation anchor)
    ang = np.linspace(0, 2 * np.pi, 220)
    yi = np.clip(np.round(cy - R * np.cos(ang)).astype(int), 0, SIZE - 1)
    xi = np.clip(np.round(cx + R * np.sin(ang)).astype(int), 0, SIZE - 1)
    img[yi, xi] = 0.5
    for k in range(12):
        a = k * 30 + tilt
        inner = 0.88 if k else 0.78          # longer tick at 12
        th = np.deg2rad(a)
        for r in np.linspace(inner * R, R, 4):
            y = int(round(cy - r * np.cos(th)))
            x = int(round(cx + r * np.sin(th)))
            if 0 <= y < SIZE and 0 <= x < SIZE:
                img[y, x] = 0.6
    th_m = m * 6.0 + tilt
    th_h = (h % 12) * 30.0 + m * 0.5 + tilt
    draw_line(img, cy, cx, th_m, 0.85 * R, 1, 0.95)      # minute: long, thin
    draw_line(img, cy, cx, th_h, 0.55 * R, 2, 0.95)      # hour: short, thick
    img += rng.normal(0, 0.02, img.shape)
    return np.clip(img, 0, 1), th_m % 360, th_h % 360


def make(n, tilt_range=0.0):
    X = np.empty((n, SIZE, SIZE), dtype=np.float32)
    Y = np.empty((n, 4), dtype=np.float32)               # h, m, th_m, th_h
    for i in range(n):
        h, m = int(rng.integers(0, 12)), int(rng.integers(0, 60))
        tilt = rng.uniform(-tilt_range, tilt_range) if tilt_range else 0.0
        img, tm, th = clock(h, m, tilt)
        X[i] = img
        Y[i] = (h, m, tm, th)
    return X, Y


if __name__ == "__main__":
    X, Y = make(12_000)
    Xt, Yt = make(2_000, tilt_range=15.0)                # advanced: tilted faces
    np.savez_compressed(
        r"C:\Users\jtwee\Documents\isaac_project\data\clocks_48.npz",
        X=X, Y=Y, X_tilt=Xt, Y_tilt=Yt)
    print(f"saved 12,000 upright + 2,000 tilted clocks (48x48)")
    img, tm, th = clock(3, 47)
    print(f"sample 3:47 -> minute angle {tm:.0f} (true 282), "
          f"hour angle {th:.1f} (true 113.5)")
    chars = " .:-=+*#%@"
    for row in img[::2]:
        print("".join(chars[int(v * 9.99)] for v in row[::1]))
