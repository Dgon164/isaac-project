# NEURAL NET OPTIMIZATION HANDOFF — June 10, 2026
## For the next session (this is the active track). Continues the June 9
## handoff; today's results below. Re-establish trust by re-running
## revalidate.py (expect M=125/K=200 -> 30/30 at 6.0x) before anything else.

## Validated keep-pile (cumulative, all reproduced today)
- **M=125/K=200 exclude-10 pipeline: 54/54 exact across two independent
  held-out sets; 6.0x ops; 3.2x WALL-CLOCK single-thread CPU (15.0->4.6ms,
  first hardware measurement; M=40 config: 12.5x at 80%).**
- Coarse-to-fine ladder (researcher's posit): fatter variant 29/30 at 17.3x
  Pareto-dominates flat 2-stage at equal cost. Goes in the writeup.
- Carrier exclusion validated in a THIRD context: kNN lookup +13-15 points.
- Include-carriers costs ~2x dim budget below M=125; vanishes at M>=125.
- Intrinsic dimension of GPT-2 states: TwoNN 8.2 (8.3-8.6 under
  autocorrelation ban-windows — adversarially controlled; Austen-corpus
  stamp; registered predictions: code LOWER, mixed corpus MODESTLY HIGHER).
  Three-number reconciliation: variance ~1.5-3 (PC1-3 ARE the carriers,
  PC1 loads 0.71 on dim 496); manifold ~8-11; decision needs ~300 global
  PCA dims for 76.5% but only ~125 PER-QUERY dims for exactness. Low-dim is
  real but LOCAL. Full report: low_dimensionality_report.md.

## Closed doors (today; do not reopen without new theory)
- Branch-and-bound exact cascade with Cauchy-Schwarz bounds: exact but
  1.2-1.4x (sometimes <1x). As certificate: 0/30 at every depth M=40..500.
  Slack ~ tens of logits vs 0.63 margins. READ LEMP/FEXIPRO before any
  bound-family rebuild.
- Fixed global dim order: 10/30 at M=40 — the discriminative band is
  query-specific (same fact as local-low-dim, two instruments).
- Weights-only "slopes": shared profile = 86% of curve, 0% of decision
  (predicts ' a/the/"' for every prompt; residual carries ~490% of margin).
- Lookup-table head (kNN-LM form): 50.1% agreement at 0.8x head cost,
  logarithmic curve. The head IS the optimal 50k-entry lookup table.
- Dim nomination on RAW dims: closed (superposition — parts exist, axes
  aren't parts). OPEN LANE: part nomination on SAE-decoded features.

## Priority queue for next session
1. **Corpus-scale validation**: 500+ REAL-corpus prompts (wikitext, code,
   dialogue) for the M=125 pipeline — hand-written templates are a
   distribution risk on both existing sets.
2. **The owed baselines before any novelty claim**: adaptive softmax,
   FAISS/HNSW, exact-MIPS line (LEMP, FEXIPRO). Note kNN-LM and the
   5M-container problem both converge on HNSW — one study, two programs.
3. **Mixed-corpus intrinsic-dimension replication** (predictions registered
   June 10, pre-measurement: code lower than 8.2; mixture modestly higher).
4. Margin-based fallback characterization at corpus scale (the silent-miss
   mitigation; there is NO cheap exactness proof — certificates are dead).
5. The pattern-keyed cache architecture (13/16 at ~100x on hits, June 9):
   most original surviving idea; composes with the cascade as
   draft-and-verify. Needs: hit-rate on real corpora, staleness policy.
6. SAE lane (optional, heavier): part-voting on dictionary features —
   the constitutional successor to dim nomination.
7. Micronet/LVQ MNIST refinement (90.1% -> ~93% expected; cheapest win).

## Framing for the writeup (settled today, keep)
High-accuracy heuristic with margin fallback; empirical exactness (54/54),
honest Amdahl: ~1.2-1.3x end-to-end GPT-2-small, 3.2x head-only CPU.
Three-number dimensionality story as the conceptual contribution.
Custody mapping for every number is in the session record.

## Assets
revalidate.py, bnb_exact.py, certify.py, slopes_and_qkv.py, qkv_round2.py,
lookup_head.py, intrinsic_dim.py, low_dimensionality_report.md,
session_record_june_10_2026.md (sections 1-5, 10, custody map, vocab maps).
