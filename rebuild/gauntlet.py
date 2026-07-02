"""
THE GAUNTLET — every dataset, one pipeline, no handholding, no tuning.

Fixed settings across all of it: registration front-end where images,
generic percepts only, ideals via crystallize_features(lens=None),
exemplar road via z-scored 5-NN (1-NN where dense), discover() where laws.
Caps are LOGGED, never silent. Failures are RESULTS (recorded, not fixed
mid-run). Expectation, per the owner: most of this fails. Good. The table
of face-plants IS the deliverable.
"""
import io
import sys
import time
import tarfile
import traceback
import wave as wavmod
import zipfile
from pathlib import Path

import numpy as np

sys.path.insert(0, r"C:\Users\jtwee\Documents\isaac_project\code")
sys.path.insert(0, r"C:\Users\jtwee\Documents\isaac_project\rebuild")
from isaac import Isaac
from registration_perception import canonical, resample

DATA = Path(r"C:\Users\jtwee\Documents\isaac_project\data")
rng = np.random.default_rng(7)
RESULTS = []


def log(ds, task, n_tr, n_te, doors, exemplar, note, secs):
    RESULTS.append(dict(dataset=ds, task=task, n_train=n_tr, n_test=n_te,
                        doors=doors, exemplar=exemplar, note=note,
                        secs=round(secs)))
    print(f"[{ds:14s}] doors={doors}  exemplar={exemplar}  {note}  "
          f"({secs:.0f}s)")


# ------------------------------------------------------------- shared bits
def holes(binary):
    H, W = binary.shape
    bg = ~binary
    seen = np.zeros_like(bg, dtype=bool)
    stack = [(y, x) for y in range(H) for x in (0, W - 1) if bg[y, x]] + \
            [(y, x) for x in range(W) for y in (0, H - 1) if bg[y, x]]
    for p in stack:
        seen[p] = True
    while stack:
        y, x = stack.pop()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < H and 0 <= nx < W and bg[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True
                stack.append((ny, nx))
    rest = bg & ~seen
    cnt = 0
    ys, xs = np.nonzero(rest)
    todo = set(zip(ys.tolist(), xs.tolist()))
    while todo:
        cnt += 1
        q = [todo.pop()]
        while q:
            cy, cx = q.pop()
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                p = (cy + dy, cx + dx)
                if p in todo:
                    todo.discard(p)
                    q.append(p)
    return cnt


def featurize_img(img, canon=10):
    """The one image featurizer: canonical pixels + pose + holes + crossings."""
    small = img if max(img.shape) <= 28 else resample(img, 28)
    can, pose = canonical(small)
    can = resample(can, canon) if can.shape != (canon, canon) else can
    b = can > 0.25 * max(can.max(), 1e-9)
    braw = small > 0.12 * max(small.max(), 1e-9)
    row = [(np.diff(r.astype(int)) == 1).sum() for r in b]
    col = [(np.diff(c.astype(int)) == 1).sum() for c in b.T]
    h = pose["h"] if pose else 0
    w = pose["w"] if pose else 0
    return np.concatenate([can.ravel(), [h, w, holes(braw)], row, col])


def two_roads(F_tr, y_tr, F_te, y_te, k=5):
    isaac = Isaac()
    isaac.crystallize_features(F_tr, y_tr, lens=None)
    pred = np.concatenate([isaac.classify_features(F_te[i:i + 20000])
                           for i in range(0, len(F_te), 20000)])
    acc_doors = float((pred == y_te).mean())
    mu, sd = F_tr.mean(0), F_tr.std(0) + 1e-9
    A = ((F_tr - mu) / sd).astype(np.float32)
    B = ((F_te - mu) / sd).astype(np.float32)
    hits = 0
    for i in range(0, len(B), 1000):
        c = B[i:i + 1000]
        d2 = (c ** 2).sum(1)[:, None] - 2 * c @ A.T + (A ** 2).sum(1)[None, :]
        nn = np.argpartition(d2, k, axis=1)[:, :k]
        for r in range(len(c)):
            hits += (np.bincount(y_tr[nn[r]].astype(int)).argmax()
                     == y_te[i + r])
    return acc_doors, hits / len(B)


def featurize_set(imgs, canon=10):
    return np.array([featurize_img(im, canon) for im in imgs])


def guard(name):
    def deco(fn):
        def run():
            t0 = time.time()
            try:
                fn(t0)
            except Exception as e:
                tb = traceback.format_exc().splitlines()[-1]
                log(name, "-", 0, 0, "CRASH", "CRASH", tb[:90],
                    time.time() - t0)
        return run
    return deco


# ---------------------------------------------------------------- datasets
@guard("mnist")
def run_mnist(t0):
    from sklearn.datasets import fetch_openml
    d = fetch_openml("mnist_784", version=1, as_frame=False, parser="liac-arff")
    X = d.data.astype(float).reshape(-1, 28, 28) / 255.0
    y = d.target.astype(int)
    idx = rng.permutation(len(y))
    tr, te = idx[:20000], idx[20000:25000]        # CAP LOGGED: 20k/5k of 70k
    a, b = two_roads(featurize_set(X[tr]), y[tr], featurize_set(X[te]), y[te])
    log("mnist", "10-way", 20000, 5000, f"{a*100:.1f}%", f"{b*100:.1f}%",
        "cap 20k/5k of 70k; topology-rematch check separate", time.time() - t0)


@guard("fashion")
def run_fashion(t0):
    from sklearn.datasets import fetch_openml
    d = fetch_openml("Fashion-MNIST", version=1, as_frame=False,
                     parser="liac-arff")
    X = d.data.astype(float).reshape(-1, 28, 28) / 255.0
    y = d.target.astype(int)
    idx = rng.permutation(len(y))
    tr, te = idx[:20000], idx[20000:25000]
    a, b = two_roads(featurize_set(X[tr]), y[tr], featurize_set(X[te]), y[te])
    log("fashion", "10-way", 20000, 5000, f"{a*100:.1f}%", f"{b*100:.1f}%",
        "cap 20k/5k; texture percepts absent (predicted gap)", time.time() - t0)


@guard("cifar10")
def run_cifar(t0):
    tf = tarfile.open(DATA / "cifar-10-python.tar.gz")
    Xs, ys = [], []
    import pickle
    for m in tf.getmembers():
        if "data_batch" in m.name or "test_batch" in m.name:
            d = pickle.load(tf.extractfile(m), encoding="bytes")
            Xs.append(d[b"data"]); ys.append(d[b"labels"])
    X = np.vstack(Xs).reshape(-1, 3, 32, 32).astype(float) / 255.0
    y = np.concatenate(ys).astype(int)
    idx = rng.permutation(len(y))
    tr, te = idx[:15000], idx[15000:19000]        # CAP LOGGED
    def feats(sel):
        out = []
        for i in sel:
            g = X[i].mean(0)                       # gray for shape doors
            f = featurize_img(g)
            ch = X[i].reshape(3, -1)
            color = [ch[0].mean(), ch[1].mean(), ch[2].mean(),
                     ch[0].std(), ch[1].std(), ch[2].std(),
                     ch[0].mean() / (ch[1].mean() + 1e-6),
                     ch[2].mean() / (ch[1].mean() + 1e-6)]
            out.append(np.concatenate([f, color]))
        return np.array(out)
    a, b = two_roads(feats(tr), y[tr], feats(te), y[te])
    log("cifar10", "10-way", 15000, 4000, f"{a*100:.1f}%", f"{b*100:.1f}%",
        "DESIGNED FACE-PLANT; success = honesty about it", time.time() - t0)


@guard("omniglot")
def run_omniglot(t0):
    try:
        from PIL import Image
    except ImportError:
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "-q",
                        "pillow"], check=True)
        from PIL import Image
    zf = zipfile.ZipFile(DATA / "omniglot_evaluation.zip")
    chars = {}
    for n in zf.namelist():
        if n.endswith(".png"):
            key = "/".join(n.split("/")[:-1])
            chars.setdefault(key, []).append(n)
    keys = [k for k in sorted(chars) if len(chars[k]) >= 2]
    hits = tot = 0
    n_ep = 200                                     # CAP LOGGED: 200 episodes
    for _ in range(n_ep):
        way = rng.choice(len(keys), 20, replace=False)
        protos, queries = [], []
        for ki in way:
            picks = rng.choice(chars[keys[ki]], 2, replace=False)
            pair = []
            for p in picks:
                im = 1.0 - np.array(Image.open(io.BytesIO(zf.read(p))),
                                    dtype=float)
                if im.ndim == 3:
                    im = im.mean(2)
                can, _ = canonical(resample(im, 28))
                can = resample(can, 12)
                v = can.ravel()
                pair.append(v / (np.linalg.norm(v) + 1e-9))
            protos.append(pair[0]); queries.append(pair[1])
        P = np.array(protos)
        for qi, q in enumerate(queries):
            hits += (int(np.argmax(P @ q)) == qi)
            tot += 1
    log("omniglot", "20-way 1-shot", 20, tot, "-", f"{hits/tot*100:.1f}%",
        f"{n_ep} episodes; chance 5%; humans ~95.5, BPL 96.7",
        time.time() - t0)


@guard("fsdd")
def run_fsdd(t0):
    zf = zipfile.ZipFile(DATA / "fsdd.zip")
    wavs = [n for n in zf.namelist() if n.endswith(".wav")]
    feats, labels, speakers = [], [], []
    for n in wavs:
        with wavmod.open(io.BytesIO(zf.read(n))) as w:
            sig = np.frombuffer(w.readframes(w.getnframes()),
                                dtype=np.int16).astype(float)
        if len(sig) < 512:
            continue
        frame, hop = 256, 128
        nf = (len(sig) - frame) // hop
        S = np.abs(np.fft.rfft(np.stack(
            [sig[i * hop:i * hop + frame] for i in range(max(nf, 1))]),
            axis=1))
        edges = np.unique(np.geomspace(2, S.shape[1] - 1, 17).astype(int))
        bands = np.log1p(np.add.reduceat(S, edges[:-1], axis=1))
        T = np.stack([np.interp(np.linspace(0, len(bands) - 1, 20),
                                np.arange(len(bands)), bands[:, j])
                      for j in range(bands.shape[1])], axis=1)
        base = n.split("/")[-1].split("_")
        feats.append(np.concatenate([T.ravel(), [len(sig) / 8000.0]]))
        labels.append(int(base[0]))
        speakers.append(base[1])
    F = np.array(feats); y = np.array(labels); spk = np.array(speakers)
    te_spk = sorted(set(spk))[0]
    tr, te = spk != te_spk, spk == te_spk          # speaker-transfer split
    a, b = two_roads(F[tr], y[tr], F[te], y[te], k=1)
    idx = rng.permutation(len(y))                  # mixed-speaker split
    a2, b2 = two_roads(F[idx[:2400]], y[idx[:2400]],
                       F[idx[2400:]], y[idx[2400:]], k=1)
    log("fsdd", "10-way audio", int(tr.sum()), int(te.sum()),
        f"{a*100:.1f}%", f"{b*100:.1f}%",
        f"SPEAKER-TRANSFER; mixed-speaker: doors {a2*100:.0f}% "
        f"ex {b2*100:.0f}%", time.time() - t0)


@guard("clocks")
def run_clocks(t0):
    z = np.load(DATA / "clocks_48.npz")
    X, Y = z["X"], z["Y"]
    n = 2000                                       # CAP LOGGED
    ok_m = ok_t = amb = 0
    angles = []
    for i in range(n):
        img = X[i]
        ys, xs = np.nonzero(img > 0.7)             # hands are brightest
        if len(ys) < 10:
            continue
        w = img[ys, xs]
        cy, cx = (ys * w).sum() / w.sum(), (xs * w).sum() / w.sum()
        dy, dx = ys - cy, xs - cx
        r = np.sqrt(dy ** 2 + dx ** 2)
        th = (np.degrees(np.arctan2(dx, -dy))) % 360
        R = np.percentile(r, 97)
        prof_out = np.zeros(120); prof_in = np.zeros(120)
        for rr, tt, ww in zip(r, th, w):
            b = int(tt // 3) % 120
            if rr > 0.62 * R:
                prof_out[b] += ww * rr
            elif rr > 0.15 * R:
                prof_in[b] += ww
        tm_hat = (np.argmax(prof_out) * 3 + 1.5) % 360
        mask = np.minimum(np.abs(np.arange(120) * 3 + 1.5 - tm_hat),
                          360 - np.abs(np.arange(120) * 3 + 1.5 - tm_hat)) < 20
        prof_h = prof_in.copy(); prof_h[mask] = 0
        if prof_h.max() < 0.25 * prof_in.max():    # hands overlap: AMBIGUOUS
            amb += 1
            th_hat = tm_hat
        else:
            th_hat = (np.argmax(prof_h) * 3 + 1.5) % 360
        h_true, m_true, tm, th_true = Y[i]
        dm = min(abs(tm_hat - tm), 360 - abs(tm_hat - tm))
        ok_m += (dm <= 6)
        m_hat = int(round(tm_hat / 6)) % 60
        h_hat = int(round((th_hat - m_hat * 0.5) / 30)) % 12
        ok_t += (h_hat == int(h_true) and abs(m_hat - int(m_true)) <= 1)
        angles.append((tm_hat, th_hat))
    ang = np.array(angles)
    isaac = Isaac()
    res = isaac.discover(ang[:, :1] , ang[:, 1] % 30, name="clockness")
    log("clocks", "read time", n, n, f"min±6°: {ok_m/n*100:.1f}%",
        f"time±1m: {ok_t/n*100:.1f}%",
        f"ambig declared {amb}; LAW: {res['verdict']} "
        f"{res['equation'][:40]}", time.time() - t0)


@guard("fraud")
def run_fraud(t0):
    X = np.load(r"C:\Users\jtwee\Downloads\New folder (3)\fraud_X.npy")
    y = np.load(r"C:\Users\jtwee\Downloads\New folder (3)\fraud_y.npy").astype(int)
    idx = rng.permutation(len(y))
    tr, te = idx[:150000], idx[150000:200000]      # CAP LOGGED
    a, b = two_roads(X[tr], y[tr], X[te], y[te], k=1)
    pos = y[te] == 1
    mu, sd = X[tr].mean(0), X[tr].std(0) + 1e-9
    A = ((X[tr] - mu) / sd).astype(np.float32)
    B = ((X[te][pos] - mu) / sd).astype(np.float32)
    d2 = (B ** 2).sum(1)[:, None] - 2 * B @ A.T + (A ** 2).sum(1)[None, :]
    rec = (y[tr][np.argmin(d2, 1)] == 1).mean()
    log("fraud", "rare 0.17%", 150000, 50000, f"{a*100:.2f}%",
        f"{b*100:.2f}%", f"minority RECALL (the needle): {rec*100:.0f}% "
        f"— accuracy is majority theater here", time.time() - t0)


@guard("kepler")
def run_kepler(t0):
    a = np.array([0.387, 0.723, 1.0, 1.524, 5.203, 9.537, 19.19, 30.07])
    T = np.array([0.241, 0.615, 1.0, 1.881, 11.86, 29.46, 84.01, 164.8])
    isaac = Isaac()
    res = isaac.discover(a.reshape(-1, 1), T, name="kepler")
    log("kepler", "8 rows", 4, 4, res["verdict"], f"R2 {res['r2']:.2f}",
        f"PREDICTED FAIL (a^1.5 inexpressible, n=8): {res['equation'][:40]}",
        time.time() - t0)


@guard("sunspots")
def run_sunspots(t0):
    import urllib.request
    raw = urllib.request.urlopen(
        "https://www.sidc.be/SILSO/DATA/SN_m_tot_V2.0.csv", timeout=60
    ).read().decode()
    rows = [r.split(";") for r in raw.strip().splitlines()]
    t = np.array([float(r[2]) for r in rows])
    s = np.array([float(r[3]) for r in rows])
    keep = s >= 0
    t, s = t[keep], s[keep]
    isaac = Isaac()
    res = isaac.discover(((t - t.mean()) / 10).reshape(-1, 1), s,
                         name="sunspots")
    period = "-"
    for part in res["equation"].split(" "):
        if "sin(" in part or "cos(" in part:
            k = float(part.split("(")[1].split("*")[0])
            period = f"{2*np.pi*10/k:.1f}yr"
            break
    log("sunspots", f"{len(s)} months", len(s)//2, len(s)//2,
        res["verdict"], f"R2 {res['r2']:.2f}",
        f"period read: {period} (true ~11); quasi-periodic so PARTIAL is "
        f"honest", time.time() - t0)


@guard("smallnorb")
def run_norb(t0):
    import gzip
    def read_norb(path):
        with gzip.open(path, "rb") as f:
            magic = int.from_bytes(f.read(4), "little")
            ndim = int.from_bytes(f.read(4), "little")
            dims = [int.from_bytes(f.read(4), "little")
                    for _ in range(max(ndim, 3))][:ndim]
            dt = {0x1e3d4c55: np.uint8, 0x1e3d4c54: np.int32}[magic]
            return np.frombuffer(f.read(), dtype=dt).reshape(dims)
    X = read_norb(DATA / "smallnorb_dat.mat.gz")[:, 0]     # first of stereo
    y = read_norb(DATA / "smallnorb_cat.mat.gz")
    idx = rng.permutation(len(y))
    tr, te = idx[:8000], idx[8000:10000]           # CAP LOGGED of 24,300
    def feats(sel):
        return featurize_set([X[i][::4, ::4] / 255.0 for i in sel])
    a, b = two_roads(feats(tr), y[tr].astype(int), feats(te),
                     y[te].astype(int))
    log("smallnorb", "5-way pose-varied", 8000, 2000, f"{a*100:.1f}%",
        f"{b*100:.1f}%", "viewpoint variation unhandled (phase-4 target); "
        "chance 20%", time.time() - t0)


if __name__ == "__main__":
    print("=" * 78)
    print("THE GAUNTLET — every dataset, one pipeline, failures welcome")
    print("=" * 78)
    for fn in (run_kepler, run_clocks, run_fsdd, run_omniglot, run_fraud,
               run_norb, run_cifar, run_fashion, run_mnist,
               run_sunspots):
        fn()
    print("\n" + "=" * 78)
    import csv
    with open("gauntlet_results.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(RESULTS[0]))
        w.writeheader()
        for r in RESULTS:
            w.writerow(r)
    print(f"{'dataset':14s} {'doors':>12s} {'exemplar':>12s}  note")
    for r in RESULTS:
        print(f"{r['dataset']:14s} {str(r['doors']):>12s} "
              f"{str(r['exemplar']):>12s}  {r['note'][:64]}")
