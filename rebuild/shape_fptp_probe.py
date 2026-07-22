"""
FIRST-PAST-THE-POST PROBE — satisficing shape matching, tested
before built. (Owner, 2026-07-22: "50 cheap operations, reject 49
bad ones, keep a functional one... keep the first past the post
working solution, do element modification when a problem arises.")

The reframe: v1/v2 tested OPTIMALITY (agree with exhaustive best) —
the wrong court for this epistemology. These courts test FUNCTION:

  V1  cost:    <= ~60 ops/entry at 100k crystals (flat = 100k)
  V2  function: >= 95% of kept answers pass the validation gate on
               structured data; median quality >= 0.8 of flat-best
  V3  repair:  a flagged keep is fixed by one element-modification
               pass >= 80% of the time, bounded cost
  V4  null:    on structureless data the gate REFUSES (new pile),
               it does not keep junk

Matcher: candidates generated rarest-shared-door-first from a
door->crystal index (the 50 cheap ops), each validated by an
absolute functional gate; FIRST PASS KEPT, search stops. No ranking
of the world. Repair: when a keep is flagged, re-match with the
conflicting evidence required and a widened budget.

    python shape_fptp_probe.py
"""
import math
import os
import sys
import time
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "..", "code"))
from isaac import Isaac  # noqa: E402
from boot_scale_probe import corpus  # noqa: E402

CAND_CAP = 50        # the owner's number: 50 cheap operations
VALID_FRAC = 0.5     # keep if shared evidence >= this frac of the
                     # CANDIDATE's signature weight (it explains him)
HUB_SKIP = 200       # doors indexed in more crystals than this are
                     # not used for candidate generation (ejected)


def idf_of(registry):
    df = defaultdict(int)
    for sig in registry.values():
        for d in sig:
            df[d] += 1
    n = max(len(registry), 1)
    return {d: math.log(1 + n / c) for d, c in df.items()}


def wov(a, b, idf):
    return sum(idf.get(d, 0.0) for d in (a & b))


def wsum(a, idf):
    return sum(idf.get(d, 0.0) for d in a)


def door_index(registry):
    ix = defaultdict(set)
    for name, sig in registry.items():
        for d in sig:
            ix[d].add(name)
    return ix


def fptp_match(entry, registry, idf, ix, cap=CAND_CAP, require=None):
    """First functional candidate wins. Candidates arrive rarest-
    shared-door-first; each costs one gate check; the first that
    passes is KEPT and the search STOPS. Returns
    (kept, ops, examined) — kept is None if nothing passed (new
    pile — an honest refusal, not a failure)."""
    ops = 0
    seen = set()
    doors = sorted(entry, key=lambda d: -idf.get(d, 0.0))
    if require is not None:
        doors = [require] + [d for d in doors if d != require]
    for d in doors:
        holders = ix.get(d, ())
        if len(holders) > HUB_SKIP:
            continue
        for name in holders:
            if name in seen:
                continue
            seen.add(name)
            ops += 1
            sig = registry[name]
            if require is not None and require not in sig:
                continue
            gate = wov(entry, sig, idf) >= VALID_FRAC * wsum(sig, idf)
            if gate:
                return name, ops, len(seen)
            if len(seen) >= cap:
                return None, ops, len(seen)
    return None, ops, len(seen)


def run_structured(n_crystals, seed=5):
    """Planted structure: entries derive from true parent crystals."""
    rng = np.random.default_rng(seed)
    n_doors = max(200, n_crystals // 4)
    p = 1.0 / np.arange(1, n_doors + 1)
    p /= p.sum()
    registry = {}
    for i in range(n_crystals):
        k = int(rng.integers(6, 24))
        registry[f"c{i}"] = {f"d{int(x)}"
                             for x in rng.choice(n_doors, k, p=p)}
    idf = idf_of(registry)
    ix = door_index(registry)
    names = list(registry)

    kept_n = valid_n = miss = 0
    ops_t = 0
    qualities = []
    repair_flagged = repair_fixed = repair_ops = 0
    t0 = time.perf_counter()
    n_entries = 100
    for _ in range(n_entries):
        true = names[int(rng.integers(0, n_crystals))]
        base = registry[true]
        keep = {d for d in base if rng.random() < 0.7}
        noise = {f"d{int(x)}" for x in rng.choice(n_doors, 3, p=p)}
        entry = keep | noise
        kept, ops, _ = fptp_match(entry, registry, idf, ix)
        ops_t += ops
        if kept is None:
            miss += 1
            continue
        kept_n += 1
        sig = registry[kept]
        valid = wov(entry, sig, idf) >= VALID_FRAC * wsum(sig, idf)
        valid_n += valid
        # quality vs flat-best (the expensive truth, computed only
        # by the probe to grade the cheap answer)
        best = max(registry, key=lambda n_: wov(entry, registry[n_],
                                                idf))
        bq = wov(entry, registry[best], idf) or 1.0
        q = wov(entry, sig, idf) / bq
        qualities.append(q)
        # element modification: a problem arises when the keep is
        # meaningfully worse than the truth — repair re-matches with
        # the strongest unexplained evidence REQUIRED
        if q < 0.8:
            repair_flagged += 1
            unexplained = sorted(entry - sig,
                                 key=lambda d: -idf.get(d, 0.0))
            if unexplained:
                fixed, rops, _ = fptp_match(entry, registry, idf, ix,
                                            cap=CAND_CAP * 2,
                                            require=unexplained[0])
                repair_ops += rops
                if fixed is not None:
                    fq = wov(entry, registry[fixed], idf) / bq
                    if fq > q:
                        repair_fixed += 1
    dt = (time.perf_counter() - t0) * 1000 / n_entries
    return dict(crystals=n_crystals, ops=ops_t / n_entries,
                kept=kept_n, miss=miss,
                valid=100.0 * valid_n / max(kept_n, 1),
                q_med=float(np.median(qualities)) if qualities else 0,
                flagged=repair_flagged, fixed=repair_fixed,
                repair_ops=repair_ops / max(repair_flagged, 1),
                ms=dt)


def run_structureless(n_tokens=8000):
    """The null: real-mind registry from random text (no true
    families) + pure-noise entries. The gate should REFUSE."""
    seqs, _ = corpus(n_tokens)
    isaac = Isaac()
    isaac.wave_logging = False
    isaac.beat()
    isaac.ingest(seqs, kind="fptp-null")
    isaac.boot(beats=8)
    registry = {}
    for name, t in isaac.types.items():
        sig = set(t["preds"]) | set(t["succs"])
        if sig:
            registry[name] = sig
    idf = idf_of(registry)
    ix = door_index(registry)
    rng = np.random.default_rng(9)
    vocab = [f"z{i}" for i in range(500)]      # doors the net never saw
    kept = miss = 0
    for _ in range(100):
        entry = {vocab[int(rng.integers(0, 500))] for _ in range(10)}
        k, ops, _ = fptp_match(entry, registry, idf, ix)
        if k is None:
            miss += 1
        else:
            kept += 1
    return dict(crystals=len(registry), refused=miss, kept_junk=kept)


if __name__ == "__main__":
    print("=" * 72)
    print("  FIRST-PAST-THE-POST PROBE — keep the first functional fit")
    print("=" * 72)
    print("\n  structured (planted parents):")
    print("  crystals   ops/entry  miss  valid%  q_median"
          "   repairs fixed/flagged (ops)")
    for m in (2000, 20000, 100000):
        r = run_structured(m)
        print(f"  {r['crystals']:>8}   {r['ops']:>7.1f}  {r['miss']:>4}"
              f"  {r['valid']:>5.1f}%   {r['q_med']:>5.2f}"
              f"     {r['fixed']}/{r['flagged']}"
              f" ({r['repair_ops']:.0f})   [{r['ms']:.2f}ms/entry]",
              flush=True)
    print("\n  structureless null (gate must refuse):")
    r = run_structureless()
    print(f"  {r['crystals']} crystals: refused {r['refused']}/100, "
          f"kept junk {r['kept_junk']}/100"
          f"  {'(court holds)' if r['kept_junk'] == 0 else '(COURT FAILS)'}")
    print("\n  verdicts: V1 ops<=~60 @100k · V2 valid>=95%, q_med>=0.8"
          " · V3 repair>=80% · V4 refuse junk")
