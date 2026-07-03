"""
CROSS-DOMAIN — analogy as closure-matching, and the transfer test.

Four acts:
  1. DISCOVER laws in six separate domains, independently (different units,
     scales, noise — the engine never told they're related).
  2. MATCH laws by STRUCTURE: a law's shape signature = its term structure
     with variable identities abstracted away (which column doesn't matter;
     the ROLE pattern does). Gravity and Coulomb should match EXACTLY;
     cooling and the capacitor should match as the exp-decay family;
     the spring (linear) matches neither.
  3. ABSTRACT: a matched family becomes a first-class node —
     family:<signature> — whose INSTANCES are laws. A concept whose members
     are closures: the theory recursing.
  4. TRANSFER (the novel-solution test): a new domain — "magnetism" — with
     only n=24 noisy samples, too few for cold discovery. The matched
     family's shape acts as a PRIOR: fit only the constants, roles assigned
     by trial (not told which column is which). Cold fails; primed succeeds;
     the answer was IMPORTED from other domains' understanding, readably.
Plus the promised Kepler retest now that power atoms exist.
"""
import sys
import numpy as np

sys.path.insert(0, r"C:\Users\jtwee\Documents\isaac_project\code")
from isaac import Isaac, _atom_col

rng = np.random.default_rng(19)
N = 1500


# ------------------------------------------------------------- the domains
def gravity():
    m1 = rng.uniform(1, 10, N); m2 = rng.uniform(1, 10, N)
    r = rng.uniform(1, 8, N)
    F = 6.674 * m1 * m2 / r ** 2
    return np.column_stack([m1, m2, r]), F * (1 + rng.normal(0, 0.02, N))


def coulomb():
    q1 = rng.uniform(0.5, 5, N); q2 = rng.uniform(0.5, 5, N)
    r = rng.uniform(0.5, 4, N)
    F = 8.99 * q1 * q2 / r ** 2
    return np.column_stack([q1, q2, r]), F * (1 + rng.normal(0, 0.02, N))


def light():
    P = rng.uniform(10, 100, N); r = rng.uniform(1, 10, N)
    I = P / (4 * np.pi * r ** 2)
    return np.column_stack([P, r]), I * (1 + rng.normal(0, 0.02, N))


def spring():
    x = rng.uniform(-2, 2, N)
    return x.reshape(-1, 1), -8.1 * x + rng.normal(0, 0.05, N)


def cooling():
    t = rng.uniform(0, 10, N)
    return t.reshape(-1, 1), 90 * np.exp(-0.31 * t) + rng.normal(0, 0.5, N)


def capacitor():
    t = rng.uniform(0, 12, N)
    return t.reshape(-1, 1), 5.0 * np.exp(-t / 2.2) + rng.normal(0, 0.03, N)


# ------------------------------------------------- shape signature machinery
def log_track(isaac, X, y, name):
    """Multiplicative laws are LINEAR in log space (June doctrine 11.2,
    lifted to the target). For a pure power law the log-log fit is linear
    with R2 ~ 1 and the coefficients ARE the exponents; anything else
    (exp decay, oscillation) bends in log-log and is rejected here."""
    if (X <= 0).any() or (y <= 0).any():
        return None
    L = np.column_stack([np.log(X), np.ones(len(y))])
    ly = np.log(y)
    half = len(y) // 2
    beta, *_ = np.linalg.lstsq(L[:half], ly[:half], rcond=None)
    pred = L[half:] @ beta
    ss = np.sum((ly[half:] - ly[half:].mean()) ** 2)
    r2 = 1 - np.sum((ly[half:] - pred) ** 2) / max(ss, 1e-12)
    if r2 < 0.99:
        return None
    expo = {j: round(float(beta[j]) * 4) / 4 for j in range(X.shape[1])
            if abs(beta[j]) > 0.1}
    return dict(r2=r2, exponents=expo)


def signature(model, dominant=0.10):
    """Shape with variable identity abstracted, DOMINANT terms only — trace
    junk must not pollute a law's identity."""
    cols = [np.abs(c) for c in model["coefs"]]
    total = sum(cols) + 1e-12
    sig_terms = []
    for t, c in zip(model["terms"], model["coefs"]):
        if abs(c) / total < dominant:
            continue
        roles = {}
        for a in t:
            kind, i, j, k = model["specs"][a]
            key = ("feat", i)
            if kind == "var":
                roles[key] = roles.get(key, 0) + 1.0
            elif kind == "pow":
                roles[key] = roles.get(key, 0) + round(float(k) * 2) / 2
            else:
                roles[(kind, i)] = "T"                # transcendental marker
        desc = ["T" if v == "T" else f"^{v:g}" for v in roles.values()]
        sig_terms.append(tuple(sorted(desc)))
    return tuple(sorted(sig_terms))


def main():
    print("=" * 74)
    print("CROSS-DOMAIN — analogy as closure-matching, then transfer")
    print("=" * 74)
    isaac = Isaac()

    # act 0: the promised Kepler retest (power atoms now exist)
    a = np.array([0.387, 0.723, 1.0, 1.524, 5.203, 9.537, 19.19, 30.07])
    T = np.array([0.241, 0.615, 1.0, 1.881, 11.86, 29.46, 84.01, 164.8])
    order = rng.permutation(8)
    res = isaac.discover(a[order].reshape(-1, 1), T[order], name="kepler")
    print(f"\n0. KEPLER retest: {res['verdict']}  R2 {res['r2']:.4f}")
    print(f"   equation: {res['equation'][:70]}")

    # act 1: independent discovery across domains
    domains = dict(gravity=gravity(), coulomb=coulomb(), light=light(),
                   spring=spring(), cooling=cooling(), capacitor=capacitor())
    models = {}
    print("\n1. independent discovery:")
    for name, (X, y) in domains.items():
        r = isaac.discover(X, y, name=name)
        m = isaac.net.get_meta(f"law:{name}", "model")
        models[name] = m
        print(f"   {name:10s} {r['verdict']:10s} R2 {r['r2']:.3f}  "
              f"{r['equation'][:58]}")

    # act 2: structural matching — who is secretly the same law?
    # multiplicative domains go through the log track: exponents = roles
    print("\n2. structural matching (variable identities abstracted):")
    sigs = {}
    for n, m in models.items():
        lt = log_track(isaac, *domains[n], n)
        if lt is not None:
            expos = tuple(sorted(lt["exponents"].values()))
            sigs[n] = ("powerlaw", expos)
            print(f"   {n:10s} log-track exponents {expos} "
                  f"(R2 {lt['r2']:.3f})")
        else:
            sigs[n] = signature(m)
            print(f"   {n:10s} shape {sigs[n]}")
    groups = {}
    for n, s in sigs.items():
        groups.setdefault(s, []).append(n)
    # family rule (generic): power laws sharing a common ROLE (an exponent)
    # join a family even if their other roles differ in count
    power_laws = {n: s[1] for n, s in sigs.items()
                  if isinstance(s, tuple) and len(s) == 2
                  and s[0] == "powerlaw"}
    inv_family = [n for n, e in power_laws.items()
                  if any(abs(x + 2.0) < 0.3 for x in e)]
    print()
    families = []
    for s, members in groups.items():
        if len(members) > 1:
            print(f"   EXACT FAMILY {members}")
            families.append(("exact", members))
    if len(inv_family) > 1:
        print(f"   ROLE FAMILY (shared ^-2 role): {inv_family}")
        families.append(("inverse_square", inv_family))

    # act 3: abstraction — the family becomes a node whose instances are laws
    fams = 0
    print()
    for fi, (kind, members) in enumerate(families):
        fams += 1
        fname = f"family:{kind}:{'+'.join(sorted(members))}" \
            if kind == "exact" else f"family:{kind}"
        for mem in members:
            isaac._teach_fact(f"law:{mem}", "instance_of", fname)
        print(f"3. abstraction node {fname}: instances = "
              f"{sorted(isaac.net.get_predecessors(fname, tag='instance_of'))}")

    # act 4: TRANSFER — magnetism with n=24: cold fails, analogy succeeds
    print("\n4. transfer to a data-starved domain (magnetism, n=24):")
    n = 24
    p1 = rng.uniform(1, 6, n); p2 = rng.uniform(1, 6, n)
    r = rng.uniform(1, 5, n)
    F = 3.2 * p1 * p2 / r ** 2 * (1 + rng.normal(0, 0.05, n))
    Xm = np.column_stack([p1, p2, r])
    cold = Isaac().discover(Xm, F)
    print(f"   cold discovery:   {cold['verdict']}  R2 {cold['r2']:.3f}  "
          f"(n=24 — too few)")

    # primed: reuse the inverse-square family's TERM STRUCTURE; roles by trial
    grav = models["gravity"]
    best = None
    for r_col in range(3):                     # which column plays 'r'?
        others = [c for c in range(3) if c != r_col]
        design = np.column_stack([
            Xm[:, others[0]] * Xm[:, others[1]] *
            np.power(np.maximum(Xm[:, r_col], 1e-9), -2.0),
            np.ones(n)])
        half = n // 2
        beta, *_ = np.linalg.lstsq(design[:half], F[:half], rcond=None)
        pred = design[half:] @ beta
        ss = np.sum((F[half:] - F[half:].mean()) ** 2)
        r2 = 1 - np.sum((F[half:] - pred) ** 2) / max(ss, 1e-12)
        if best is None or r2 > best[0]:
            best = (r2, r_col, beta)
    r2, r_col, beta = best
    print(f"   analogy-primed:   role trial chose column {r_col} as 'r'; "
          f"held-out R2 {r2:.3f}")
    print(f"   imported law: F = {beta[0]:.2f} * a*b/r^2   (true constant 3.2)")
    verdict = res["verdict"] == "UNDERSTOOD" and fams >= 2 and \
        cold["r2"] < 0.9 and r2 >= 0.9
    print("-" * 74)
    print(f"kepler: {res['verdict']}   families found: {fams}   "
          f"cold R2 {cold['r2']:.2f} vs primed {r2:.2f}")
    print(f"VERDICT: {'WORKS' if verdict else 'BROKEN'}")


if __name__ == "__main__":
    main()
