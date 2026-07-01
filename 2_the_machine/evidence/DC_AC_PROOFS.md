# Proofs and Tests: the DC/AC and Equivalence Claims
**Interleave World program, June 11 2026. Theorems are exact and net-independent; empirical items are properties of specific trained nets. Each theorem has a corresponding machine check in verify_theorems.py.**

## Theorem 1 — Class-space DC is null (shift invariance of the decision)
**Claim.** For any logits z ∈ ℝ^V and any constant c ∈ ℝ: argmax_i (z_i + c) = argmax_i z_i, and softmax(z + c·1) = softmax(z).

**Proof.** Adding the same c to every coordinate preserves every pairwise order: z_i + c > z_j + c ⇔ z_i > z_j, so the argmax is unchanged. For softmax: the i-th coordinate is e^{z_i+c}/Σ_j e^{z_j+c} = e^c e^{z_i} / (e^c Σ_j e^{z_j}) = e^{z_i}/Σ_j e^{z_j}. ∎

**Consequence.** Any component of any computation whose final effect is a uniform shift of all logits is answer-irrelevant by identity — not approximately, not statistically.

## Theorem 2 — Exact folding of a constant feature
**Claim.** Let FFN(x) = W₂·a(W₁x + b₁) + b₂, and suppose coordinate f of the activation a equals the constant v for every input x in a domain D. Define W₂′ as W₂ with column f zeroed and b₂′ = b₂ + v·W₂[:,f]. Then for all x ∈ D, the modified FFN with (W₂′, b₂′) equals the original exactly.

**Proof.** W₂·a = Σ_k a_k·W₂[:,k] = v·W₂[:,f] + Σ_{k≠f} a_k·W₂[:,k]. The first term is input-independent on D and moves into the bias; the second is computed identically by W₂′. ∎

**Consequence.** "Always the same value = DC offset = belongs on the bias rail" is an algebraic identity: such a feature contributes zero information and its removal (with compensation) changes nothing, bit-for-bit up to float rounding.

## Theorem 3 — LayerNorm rejects common mode exactly
**Claim.** For LN with any gain γ and bias β, and any x ∈ ℝ^D, c ∈ ℝ: LN(x + c·1) = LN(x).

**Proof.** mean(x + c·1) = mean(x) + c, so the centered vector (x + c·1) − mean(x + c·1)·1 = x − mean(x)·1 is unchanged; the variance, computed from the centered vector, is therefore also unchanged; the normalized output is identical. ∎

**Anti-theorem (stated for honesty).** LN(x + μ) ≠ LN(x) in general for a non-uniform constant vector μ: only the common-mode part mean(μ)·1 is rejected; the remainder perturbs both the centered vector and the variance, and the variance term makes the effect nonlinear in x. This is exactly why "DC becomes a fixed logit offset" is *empirical* (small) rather than provable in our architecture, and why the measured DC-removal residue (−0.018 on CYC) is nonzero.

## Theorem 4 — {0,1} and {−1,+1} binary activations define identical function classes
**Claim.** Let f(x) ∈ {0,1} be a threshold activation and g(x) = 2f(x) − 1 ∈ {−1,+1}. For any layer W₂·g(·) + b₂ there is an exactly equivalent layer using f: W₂·g + b₂ = (2W₂)·f + (b₂ − W₂·1), and conversely with the inverse transform. Hence every network using one activation has a weight-transformed twin using the other computing the same function on every input.

**Proof.** Substitute g = 2f − 1 and distribute: W₂(2f − 1) + b₂ = 2W₂f − W₂·1 + b₂. The reverse direction uses f = (g+1)/2. ∎

**Scope note.** The equivalence is representational (same function class, same answer space, shifted midpoint — the researcher's formulation). Training *trajectories* may differ: gradient scales differ by the factor 2 and interact with initialization and weight decay, so trained outcomes are expected to be similar, not identical. The ternary alphabet {−1,0,+1} is not affinely reducible to either binary: it has three output levels and two thresholds; no affine map of a two-level function produces three levels. The abstain state is genuinely new structure.

## Theorem 5 — Post-nonlinearity DC is exactly a class prior
**Claim.** If a constant vector μ is added to the representation at the affine stage (after the final LayerNorm, before the linear head W, b), logits shift by the fixed vector Wμ for every input. Combined with Theorem 1, only the non-uniform part of Wμ — its deviation from its own mean across classes — can influence any answer.

**Proof.** W(h + μ) + b = (Wh + b) + Wμ; the added term is input-independent. Decompose Wμ = m̄·1 + (Wμ − m̄·1) with m̄ the mean over classes; the first part is null by Theorem 1. ∎

## Empirical items (testable, not provable — properties of particular nets)
The DC fraction of FFN-output energy (measured 1.9% / 2.9% in the ternary net); the −0.018 CYC effect of uncompensated DC removal; the 100% feature-utilization census; the defining-set sizes (~25/256); the transfer ordering across activations; the cluster-tightness observations. Each is a measurement with stated conditions (one world, given seeds, sealed sets) and stands or falls by replication, not by proof.

## Machine verification
verify_theorems.py checks T1–T5 numerically: T1 on random logits and on real model logits; T2 by surgically freezing a feature in the trained ternary net and folding; T3/anti-T3 on random vectors through the net's own LayerNorms; T4 by constructing twin networks with transformed weights and comparing outputs on the sealed set; T5 by injecting μ after the final LN. Tolerances are float32 epsilon scale; any failure prints loudly.
