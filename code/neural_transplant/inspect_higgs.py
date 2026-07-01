"""
MICROSCOPE on the HIGGS feed — what does the data look like going in, and what
does his matrix actually have to attend to? NOT a test of Isaac's cognition;
this is inspecting the REPRESENTATION (counts/correlations = looking, not deciding).
Goal: find what hides the structure from him.

Sections:
  A. one event raw -> glyphs (what the feed literally is)
  B. combinatorial sparsity: do multi-feature glyph windows RECUR? (his matrix
     can only use windows that repeat; if they're all unique, he memorizes)
  C. his matrix at test: how many frames does _encode even activate per event?
     (what his 'attention' has to work with)
  D. where the info lives: continuous correlation vs after binning (does the
     glyphing destroy a known relationship?)

Run:  PYTHONUTF8=1 python -u inspect_higgs.py
"""
import sys
sys.path.insert(0, "..")
import numpy as np
from sklearn.datasets import fetch_openml          # load ONLY
from isaac import Isaac

BINS = 6


def main():
    d = fetch_openml(data_id=23512, as_frame=False)
    X = np.asarray(d.data, np.float32); X = X[~np.isnan(X).any(1)]
    names = list(d.feature_names); n = X.shape[1]
    Xtr, Xte = X[:5000], X[5000:5400]
    edges = [np.quantile(Xtr[:, j], np.linspace(0, 1, BINS + 1)[1:-1]) for j in range(n)]
    gly = lambda row: [f"{j}_{int(np.digitize(v, edges[j]))}" for j, v in enumerate(row)]

    # ---- A. one event: raw -> glyph ----
    print("=" * 70); print("  A. ONE EVENT — raw value -> glyph"); print("=" * 70)
    e = Xtr[0]
    for j in range(n):
        print(f"    {names[j]:<26} {e[j]:>8.3f}   ->  {gly(e)[j]}")

    # ---- B. do multi-feature windows recur? ----
    print("\n" + "=" * 70)
    print("  B. COMBINATORIAL SPARSITY — fraction of w-feature glyph-windows")
    print("     that occur only ONCE (his matrix can't generalize over unique ones)")
    print("=" * 70)
    G = np.array([[int(np.digitize(v, edges[j])) for j, v in enumerate(r)] for r in Xtr])
    rng = np.random.default_rng(0)
    for w in (1, 2, 3, 4, 5):
        cols = rng.choice(n, w, replace=False)
        keys = [tuple(r) for r in G[:, cols]]
        _, counts = np.unique(keys, axis=0, return_counts=True)
        once = (counts == 1).mean()
        print(f"    w={w}: {len(counts):>5} distinct windows, {once*100:>5.1f}% occur only once")

    # ---- C. his matrix at test: what does his 'attention' have to attend to? ----
    print("\n" + "=" * 70)
    print("  C. HIS MATRIX AT TEST — frames activated per held-out event")
    print("     (W_norm @ x is his attention; x is what _encode lights up)")
    print("=" * 70)
    isaac = Isaac()
    for r in Xtr:
        for _ in range(3):
            isaac.observe([gly(r)[k] for k in rng.permutation(n)])
    isaac.compile(max_context=4)
    c = isaac._compiled
    occ = c["W"].sum(0)
    print(f"    his matrix: {len(c['frames'])} frames; "
          f"{(occ==1).mean()*100:.1f}% of frames seen only ONCE (memorized, not learned)")
    acts = []
    for r in Xte:
        x = isaac._encode([gly(r)[k] for k in range(n)])
        acts.append(int((x > 0).sum()) if x is not None else 0)
    acts = np.array(acts)
    print(f"    per test event, _encode activates {acts.mean():.1f} frames on average "
          f"(of {len(c['frames'])}); {(acts==0).mean()*100:.0f}% activate ZERO")

    # ---- D. where the info lives: continuous vs glyph ----
    print("\n" + "=" * 70)
    print("  D. DATA MICROSCOPE (looking, not Isaac): is the relationship in the")
    print("     numbers preserved after glyphing? m_wbb vs its best partner")
    print("=" * 70)
    j = names.index("m_wbb")
    corr = np.array([abs(np.corrcoef(Xtr[:, j], Xtr[:, k])[0, 1]) if k != j else 0 for k in range(n)])
    k = int(corr.argmax())
    # glyph-space: how peaked is P(m_wbb glyph | partner glyph)?
    gj, gk = G[:, j], G[:, k]
    cond = []
    for b in np.unique(gk):
        sub = gj[gk == b]
        if len(sub): cond.append(np.bincount(sub, minlength=BINS+1).max() / len(sub))
    print(f"    best continuous partner of m_wbb = {names[k]}  (|corr|={corr[k]:.2f})")
    print(f"    continuous: |corr|={corr[k]:.2f} (strong linear relationship in the NUMBERS)")
    print(f"    glyph-space: knowing {names[k]}'s bin pins m_wbb's bin only "
          f"{np.mean(cond)*100:.0f}% of the time (1/{BINS}={100//BINS}% = no info)")
    print("\n  READ: if windows are all unique (B) and _encode lights up almost")
    print("  nothing at test (C), his exact-match attention has NOTHING to match.")
    print("  The info is in the NUMBERS' proximity, not in glyph IDENTITY.")


if __name__ == "__main__":
    main()
