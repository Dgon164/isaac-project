"""
REBUILD C — Enumerator: staged null-gated term growth vs flat polynomial L1.

OLD (broken) mechanism, faithful to equation_discovery/interaction_solver.py +
relational_all.py as documented:
  - candidate library = polynomial only (x_i, x_i^2, x_i*x_j)  <- cannot express
    cosh(d_eta) - cos(d_phi): the Stage-1/Stage-2 basis disconnect (doc 11.1)
  - flat sparse fit (sequential thresholded least squares), no null gate
  - full enumeration would be ~d^k terms: combinatorial + sample-hungry

NEW (staged enumerator):
  1. ATOMS include the transcendental pair forms physics needs:
     x_i, cos(x_i-x_j), sin(x_i-x_j), cosh(x_i-x_j)
  2. STAGED growth: candidates start at degree<=2; higher-degree products are
     built only around ADMITTED terms (beam), never full enumeration.
  3. NULL-GATED admission: a term enters the equation only if its residual
     correlation beats the 95th percentile of the MAX-over-candidates
     correlation on permuted residuals (kills selection-effect decoys).
  4. Dual-track missing-variable recovery: reconstruct in linear AND log space,
     keep the track that closes better on held-out data (doc 11.2 fix).

Tests:
  (a) planted m_jj-shaped law  y = pt1*pt2*(cosh(e1-e2) - cos(f1-f2)) + noise
      -> OLD reproduces the wall; NEW must recover the exact terms, R2 >= 0.99
  (b) planted polynomial       y = x0*x1 + x2^2 - x3
      -> NEW must recover exactly 3 terms, coefficients ~ (1, 1, -1)
  (c) pure noise               -> NEW must admit NOTHING (the "no rule" verdict)
  (d) hidden variable, additive AND multiplicative -> dual-track reconstructs
      the unrecorded variable, right space chosen, corr >= 0.95
Integrity: numpy only; the enumerator makes every decision.
"""
import numpy as np

rng = np.random.default_rng(11)


# ------------------------------------------------------------------ atoms
def build_atoms(X, names):
    cols, labels = [], []
    n, d = X.shape
    for i in range(d):
        cols.append(X[:, i]); labels.append(names[i])
    for i in range(d):
        for j in range(i + 1, d):
            diff = X[:, i] - X[:, j]
            cols.append(np.cos(diff));  labels.append(f"cos({names[i]}-{names[j]})")
            cols.append(np.sin(diff));  labels.append(f"sin({names[i]}-{names[j]})")
            cols.append(np.cosh(diff)); labels.append(f"cosh({names[i]}-{names[j]})")
    return np.column_stack(cols), labels


def term_col(A, term):
    v = A[:, term[0]].copy()
    for a in term[1:]:
        v = v * A[:, a]
    return v


def term_name(labels, term):
    return "*".join(labels[a] for a in term)


# --------------------------------------------------- NEW: staged enumerator
class StagedEnumerator:
    def __init__(self, max_degree=3, n_perm=80, pct=95, atom_fn=None):
        self.max_degree, self.n_perm, self.pct = max_degree, n_perm, pct
        self.atom_fn = atom_fn or build_atoms

    def fit(self, X, y, names):
        self.A, self.labels = self.atom_fn(X, names)
        n, n_atoms = self.A.shape
        n_vars = X.shape[1]
        # stage-0 frontier: single atoms + pairwise products of raw variables
        frontier = [(i,) for i in range(n_atoms)]
        frontier += [(i, j) for i in range(n_vars) for j in range(i, n_vars)]
        seen = set(frontier)
        self.terms, self.coefs = [], None

        while True:
            cand = [t for t in frontier if t not in self.terms]
            M = np.column_stack([term_col(self.A, t) for t in cand])
            Ms = (M - M.mean(0)) / (M.std(0) + 1e-12)
            r = y - self._predict_fit(y)
            rs = (r - r.mean()) / (r.std() + 1e-12)
            real = np.abs(Ms.T @ rs) / len(y)                       # |corr| per candidate
            # null: max-over-candidates correlation on permuted residuals
            null_max = np.empty(self.n_perm)
            for k in range(self.n_perm):
                null_max[k] = np.max(np.abs(Ms.T @ rng.permutation(rs))) / len(y)
            gate = np.percentile(null_max, self.pct)
            best = int(np.argmax(real))
            if real[best] <= gate:
                break                                               # nothing beats its null
            t = cand[best]
            self.terms.append(t)
            self._refit(y)
            if len(t) < self.max_degree:                            # beam expansion
                for a in range(n_atoms):
                    nt = tuple(sorted(t + (a,)))
                    if len(nt) <= self.max_degree and nt not in seen:
                        seen.add(nt); frontier.append(nt)
        # final prune: a term must carry weight to stay
        if self.terms:
            keep = [t for t, c in zip(self.terms, self.coefs)
                    if abs(c) * term_col(self.A, t).std() > 0.01 * y.std()]
            self.terms = keep
            self._refit(y)
        return self

    def _design(self, A=None):
        A = self.A if A is None else A
        if not self.terms:
            return np.ones((A.shape[0], 1))
        return np.column_stack([term_col(A, t) for t in self.terms] +
                               [np.ones(A.shape[0])])

    def _refit(self, y):
        beta, *_ = np.linalg.lstsq(self._design(), y, rcond=None)
        self.coefs, self.intercept = beta[:-1], beta[-1]

    def _predict_fit(self, y):
        if not self.terms:
            return np.full_like(y, y.mean())
        return self._design() @ np.concatenate([self.coefs, [self.intercept]])

    def predict(self, X, names):
        A, _ = self.atom_fn(X, names)
        if not self.terms:
            return np.full(X.shape[0], self.intercept if hasattr(self, "intercept") else 0.0)
        return self._design(A) @ np.concatenate([self.coefs, [self.intercept]])

    def equation(self):
        if not self.terms:
            return "NO RULE (nothing beat the null)"
        parts = [f"{c:+.2f}*{term_name(self.labels, t)}"
                 for t, c in zip(self.terms, self.coefs)]
        return " ".join(parts) + f" {self.intercept:+.2f}"


# ---------------------------------------- OLD: flat polynomial L1 (faithful)
class PolyL1:
    """Library = x_i, x_i^2, x_i*x_j; sequential thresholded least squares."""
    def _lib(self, X):
        d = X.shape[1]
        cols = [X[:, i] for i in range(d)] + [X[:, i] ** 2 for i in range(d)]
        cols += [X[:, i] * X[:, j] for i in range(d) for j in range(i + 1, d)]
        return np.column_stack(cols + [np.ones(len(X))])

    def fit(self, X, y):
        L = self._lib(X)
        self.sd = L.std(0); self.sd[self.sd == 0] = 1.0
        Ls = L / self.sd
        beta = np.linalg.lstsq(Ls, y, rcond=None)[0]
        for _ in range(10):
            small = np.abs(beta) < 0.05 * np.abs(beta).max()
            small[-1] = False
            beta[small] = 0.0
            act = ~small
            beta[act] = np.linalg.lstsq(Ls[:, act], y, rcond=None)[0]
        self.beta = beta
        return self

    def predict(self, X):
        return (self._lib(X) / self.sd) @ self.beta

    def n_terms(self):
        return int(np.sum(self.beta[:-1] != 0))


def r2(y, p):
    return float(1 - np.sum((y - p) ** 2) / np.sum((y - y.mean()) ** 2))


# ------------------------------------------- dual-track missing variable (d)
def recover_missing(Xrec, y):
    """Reconstruct an unrecorded variable from the residual, in linear AND log
    space; keep the track that closes better on held-out data."""
    n = len(y); half = n // 2
    tr, te = slice(0, half), slice(half, n)

    def lin_track():
        D = np.column_stack([Xrec, np.ones(n)])
        b = np.linalg.lstsq(D[tr], y[tr], rcond=None)[0]
        return y - D @ b, r2(y[te], (D @ b)[te])

    def log_track():
        if (y <= 0).any() or (Xrec <= 0).any():
            return None, -np.inf
        D = np.column_stack([np.log(Xrec), np.ones(n)])
        ly = np.log(y)
        b = np.linalg.lstsq(D[tr], ly[tr], rcond=None)[0]
        return np.exp(ly - D @ b), r2(ly[te], (D @ b)[te])

    (res_l, s_l), (res_g, s_g) = lin_track(), log_track()
    return ("linear", res_l) if s_l >= s_g else ("log", res_g)


# --------------------------------------------------------------------- tests
def main():
    print("=" * 72)
    print("REBUILD C — staged null-gated enumerator vs flat polynomial L1")
    print("=" * 72)

    # (a) the m_jj-shaped wall
    n = 6000
    names = ["pt1", "pt2", "e1", "e2", "f1", "f2", "n1", "n2"]
    X = np.column_stack([rng.lognormal(0, 0.5, n), rng.lognormal(0, 0.5, n),
                         rng.normal(0, 1, n), rng.normal(0, 1, n),
                         rng.normal(0, 1.2, n), rng.normal(0, 1.2, n),
                         rng.normal(0, 1, n), rng.normal(0, 1, n)])
    y = X[:, 0] * X[:, 1] * (np.cosh(X[:, 2] - X[:, 3]) - np.cos(X[:, 4] - X[:, 5]))
    y = y + rng.normal(0, 0.01 * y.std(), n)
    half = n // 2
    Xtr, ytr, Xte, yte = X[:half], y[:half], X[half:], y[half:]

    old = PolyL1().fit(Xtr, ytr)
    old_r2 = r2(yte, old.predict(Xte))
    new = StagedEnumerator().fit(Xtr, ytr, names)
    new_r2 = r2(yte, new.predict(Xte, names))
    want = {("pt1", "pt2", "cosh(e1-e2)"), ("pt1", "pt2", "cos(f1-f2)")}
    got = {tuple(sorted(term_name(new.labels, t).split("*"))) for t in new.terms}
    want = {tuple(sorted(w)) for w in want}
    exact = got == want
    print(f"\n(a) planted pt1*pt2*(cosh(e1-e2)-cos(f1-f2)):")
    print(f"    OLD poly-L1: held-out R2 {old_r2:.3f} with {old.n_terms()} terms  <- the wall")
    print(f"    NEW staged:  held-out R2 {new_r2:.3f}")
    print(f"    NEW equation: {new.equation()}")
    print(f"    exact form recovered: {exact}")
    ta = exact and new_r2 >= 0.99

    # (b) planted polynomial
    Xb = rng.normal(0, 1, (n, 6))
    nb = [f"x{i}" for i in range(6)]
    yb = Xb[:, 0] * Xb[:, 1] + Xb[:, 2] ** 2 - Xb[:, 3]
    yb = yb + rng.normal(0, 0.01 * yb.std(), n)
    newb = StagedEnumerator().fit(Xb[:half], yb[:half], nb)
    r2b = r2(yb[half:], newb.predict(Xb[half:], nb))
    gotb = {term_name(newb.labels, t) for t in newb.terms}
    tb = gotb == {"x0*x1", "x2*x2", "x3"} and r2b >= 0.99
    print(f"\n(b) planted x0*x1 + x2^2 - x3:")
    print(f"    NEW equation: {newb.equation()}   held-out R2 {r2b:.3f}")
    print(f"    exactly the 3 planted terms, no junk: {tb}")

    # (c) pure noise -> must say NO RULE
    yn = rng.normal(0, 1, n)
    newc = StagedEnumerator().fit(Xb[:half], yn[:half], nb)
    oldc = PolyL1().fit(Xb[:half], yn[:half])
    tc = len(newc.terms) == 0
    print(f"\n(c) pure noise:")
    print(f"    NEW admits {len(newc.terms)} terms -> '{newc.equation()}'")
    print(f"    OLD keeps {oldc.n_terms()} junk terms "
          f"(train R2 {r2(yn[:half], oldc.predict(Xb[:half])):.3f}, "
          f"held-out R2 {r2(yn[half:], oldc.predict(Xb[half:])):.3f})")

    # (d) dual-track missing variable
    A = rng.normal(0, 1, (n, 3)); d_add = rng.normal(0, 1, n)
    y_add = A.sum(1) + d_add
    trk1, rec1 = recover_missing(A, y_add)
    c1 = float(np.corrcoef(rec1, d_add)[0, 1])
    B = rng.lognormal(0, 0.5, (n, 3)); d_mul = rng.lognormal(0, 0.5, n)
    y_mul = B.prod(1) * d_mul
    trk2, rec2 = recover_missing(B, y_mul)
    c2 = float(np.corrcoef(rec2, d_mul)[0, 1])
    td = trk1 == "linear" and trk2 == "log" and c1 >= 0.95 and c2 >= 0.95
    print(f"\n(d) hidden-variable recovery, dual-track:")
    print(f"    additive law  -> chose {trk1}, corr(d_hat, d_true) {c1:.3f}")
    print(f"    multiplicative-> chose {trk2}, corr(d_hat, d_true) {c2:.3f}")

    print("-" * 72)
    verdict = ta and tb and tc and td
    print(f"(a) wall broken: {ta}   (b) exact poly: {tb}   "
          f"(c) no-rule on noise: {tc}   (d) dual-track: {td}")
    print(f"REBUILD C VERDICT: {'WORKS' if verdict else 'BROKEN'}")
    return verdict


if __name__ == "__main__":
    main()
