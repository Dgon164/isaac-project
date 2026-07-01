# Sparse Output Layer Inference: Research Findings

## Executive Summary

Starting from an existing research program on sparse inference for frozen neural networks, this work focused on the output projection layer (lm_head) of GPT-2. The core finding: the full output matmul (50,257 × 768 = 38.6M ops) can be replaced by a two-stage pipeline costing 2.16M ops (5.6% of original) with 100% accuracy — mathematically identical results, not an approximation.

The key insight: trained weight matrices encode information in separable bands. A small number of hidden-state dimensions carry shared structural magnitude (the same for every input), while the remaining dimensions carry input-specific discriminative signal. By filtering on discriminative dims first and scoring on all dims second, you search the output space in two cheap passes instead of one expensive one.

The MLP sparse inference problem (the other 75% of inference compute) remains open. Gate prediction achieves 83-93% per-neuron accuracy, but 60% false negative rates on active neurons compound across 12 layers, collapsing outputs to comma/the. The GELU nonlinearity (not binary like ReLU) means even perfect gating introduces error. This is documented but unsolved.

---

## The Output Layer Pipeline

### Architecture

Given a hidden state h (768 dims), predict the output token from a vocabulary of 50,257:

**Stage 1 — Discriminative Filter (5.2% of matmul cost):**
1. Sort h's 768 dimensions by absolute magnitude
2. Exclude the top 10 (structure dims — these carry ~55% of h's magnitude but don't distinguish between tokens)
3. Use the next 40 dims (discriminative dims) to compute partial logits for all 50,257 tokens
4. Keep the top 200 tokens by partial logit score

**Stage 2 — Full Scoring (0.4% of matmul cost):**
5. Score those 200 survivors using the full 768-dim dot product
6. Pick the highest — this is the output token

**Cost:** 50,257 × 40 + 200 × 768 = 2,163,880 ops = 5.6% of full matmul. 17.8x speedup.

**Accuracy:** 20/20 on test set. The result is not approximate — it produces the identical token that the full matmul would produce. The filter never drops the correct answer.

### Why It Works

The hidden state h has extreme magnitude concentration. Three dimensions carry 50% of the total magnitude, and the top 10 carry ~67%. These dimensions are structurally dominant — they rank highest for every input regardless of context. They determine the rough scale of all logits but not which token wins.

The winning token is determined by its alignment with the remaining 758 dimensions. Among those, the top 40 by magnitude carry enough discriminative signal to reliably place the correct token in the top 200 out of 50,257 — a 250x reduction. Once narrowed to 200 candidates, the full dot product (including structure dims) picks the exact winner because all 200 candidates have genuine discriminative alignment and the structure dims add precision rather than noise.

### Robustness

The pipeline was tested across exclusion counts (3 to 30 dims excluded), filter dim counts (5 to 758), and survivor counts (50 to 1000). Key stability findings:

- Excluding 3 to 30 structure dims all work at keep=200. The method is not sensitive to the exact exclusion count.
- The correct token is ratio rank 1 in 17/20 cases and never worse than rank 3 when using the full 758 discriminative dims.
- At M=40 filter dims with keep=200: 100%. At M=30 with keep=200: 19/20 (one miss: "sun" at partial rank 439). At M=125 with keep=50: 100%.
- The ratio (actual/max_possible) and the raw partial logit produce identical filtering results — the ratio normalization is unnecessary, halving the filter computation.

### Margin-Based Fallback

The one prompt the original 3-dim hierarchy missed ("When the sun goes down the" → "sun", which ranked 15218 on 3 structure dims) is caught by the discriminative filter. A margin-based fallback was also validated: if the top-1 and top-2 logit margin is below 0.1, retry with the discriminative S1. This catches the miss with only 2/20 fallbacks triggered, keeping average S1 cost at 337K ops.

---

## Research Journey: What Worked, What Didn't, and Why

### The Starting Point

The project inherited a validated hierarchical token search: 3 structure dims → 5000 candidates → 140 semantic dims → 200 candidates → full dot on 200. This achieved 95% top-1 accuracy at 2.6% of the matmul cost. The 5% miss occurred because certain tokens (like "sun") ranked poorly on the top 3 magnitude dims and were eliminated at stage 1 before semantic filtering could rescue them.

### Dead Ends

**Surprise/z-score scoring (tested extensively, all formulations failed).** The hypothesis: score tokens by how surprising their logit is relative to a calibrated baseline. If comma always scores high, its high score isn't informative — the signal is in deviation from expectation. Seven formulations were tested: z-score, robust z, ratio, rank percentile, deviation from max, percentage of range, frequency-weighted excess. All produced 0-5% top-1 accuracy. The fundamental problem: per-token logit distributions across contexts are too noisy for calibration baselines to be meaningful with feasible sample sizes. The variance in the baseline estimate exceeds the discriminative signal.

**Blending raw logits with surprise signal.** At 95% raw / 5% surprise: drops from 100% to 90%. Any surprise contamination hurts because the surprise scores are noise, not signal.

**Surprise-weighted hierarchical search.** Applying surprise scoring at stage 1 of the hierarchy: 0% accuracy. Surprise scoring reranks the structure-dim filtering in exactly the wrong direction, systematically demoting the correct tokens.

**Output handicapping / bias adjustment (static handicap on tokens).** Subtracting each token's average logit or structural baseline from its score. Every formulation uniformly hurt accuracy (75% → 5% depending on scale). The "bias" being subtracted is larger than the discriminative signal (margins < 1.4 logit points vs. structural offsets of 10-20 points). When "the" IS the correct answer, the handicap kills it.

**Neuron-level handicapping in MLP layers.** Adjusting biases to penalize always-on neurons. Relative threshold gating (rate-aware, Bayesian). All performed equal or worse than absolute threshold, with consistent -2% to -5% accuracy drops. The activation rates from calibration don't generalize to novel inputs well enough.

**Bilateral top-K (keeping most positive + most negative neurons).** Oracle ceiling with known values: 35% at any selection up to 1000/3072 neurons, jumping to 55% at 1536 and 100% only at all 3072. The suppression signal is not concentrated in the most-negative neurons — it's spread across thousands of near-zero contributions. Skipping any of them breaks the suppression.

### Key Insight: Structure vs. Discriminative Dims

The breakthrough came from analyzing per-dimension contributions to the output logit (Part 6 of test_collapsed_full.py). Five dimensions (496, 430, 36, 314, 374) appeared in the top 5 contributors for every single prompt, carrying 78-83% of the total contribution. The winner and runner-up shared 10/10 top dims in most cases. The actual winning margin came from the remaining ~18% of contribution spread across hundreds of smaller dimensions.

This meant:
- Structure dims determine the rough neighborhood (what kind of word)
- Discriminative dims determine the specific token (which word)
- Any filter using structure dims as the primary signal will systematically favor tokens that happen to align with those dims, regardless of whether they're contextually correct

### The Ratio Discovery

Testing `score = actual / max_possible` (what percentage of maximum possible activation each token achieves) on non-structure dims produced coherent semantic neighborhoods:

- "Scientists discovered that" → bacteria, mice, neurons, genes, microbes, **the**
- "The recipe calls for cups of" → milk, rice, **water**, coffee, butter, flour  
- "When the sun goes down the" → sky, **sun**, clouds, night, temperature, moon

The correct token was always in the top 100 by ratio (mean rank 11, median 3). The ratio naturally neutralizes structural advantage because it divides each token's score by its maximum possible score on those dims, removing the effect of weight vector magnitude.

However, the ratio turned out to be unnecessary for filtering. The raw partial logit on non-structure dims produced identical survival rates at every tested configuration. The structure dims were the problem, not the lack of normalization. Removing them was sufficient.

### The Neighborhood Property

The ratio analysis revealed that correct answers always cluster with semantically related tokens. An adaptive threshold of max_ratio - 0.15 captured the correct token in 20/20 cases with an average of 223 survivors. This cluster property serves as a confidence signal: a tight cluster of related words validates the neighborhood, while a scattered result suggests the filter went down the wrong branch.

### Matmul Equivalence

Verified definitively: `lm_weight @ hidden_state` produces identical results to PyTorch's model output (max difference: 0.0001, all 20/20 tokens match). The matmul is not an approximation of the model — it IS the model's output computation. Optimizing the matmul search is optimizing the model.

---

## The MLP Problem: Why It's Hard and What We Know

### The Gate Prediction Wall

Sparse gate prediction (using K top w×x contributions per neuron) achieves 83-93% per-neuron accuracy. But the error pattern is catastrophic:

- **60% false negative rate on active neurons.** At K=5, layer 6 misses 65% of the neurons that should fire. Out of ~500 active neurons per layer, ~325 are silenced.
- **Errors compound across 12 layers.** Each layer's gate errors produce a slightly corrupted hidden state, which feeds the next layer with wrong inputs, producing more gate errors.
- **Errors are asymmetric.** Common tokens (comma, the, and) have more support paths through the network. Gate errors disproportionately kill the paths that suppress common tokens, causing them to break through.

### The GELU Problem

Even with 100% perfect gate prediction, hard gating introduces error of 4.8 to 50.6 per layer (measured). GPT-2 uses GELU, not ReLU. GELU of a negative input is a small negative value, not zero. Thousands of "off" neurons each contributing a small negative add up to significant error. The binary on/off model that works for ReLU networks doesn't apply.

### The Corruption Is Everywhere

Analysis of sparse vs. full hidden states showed:
- Structure dims cosine: 0.97-0.98 (preserved, because they're dominated by attention which runs full)
- Discriminative dims cosine: 0.27-0.40 (destroyed)
- The discriminative signal that the output search relies on is exactly what the sparse MLP corrupts

This means the output layer optimization (which requires correct discriminative dims) cannot compensate for MLP sparsity errors. The output search faithfully finds the best answer for whatever hidden state it receives — but the hidden state is garbage.

### What Hasn't Been Tried

From the original research handoff, two unexplored paths remain viable:

1. **Semantic-dim MLP filtering.** The MLP filter failures used structure dims for neuron selection (keeping broadly-activated noise neurons, dropping context-specific signal neurons). Using semantic/discriminative dims for neuron selection was identified but never tested.

2. **Larger models.** GPT-2's 768 dimensions may be pathologically narrow. Dynamic concentration data suggests wider models (LLaMA-7B at 4096 dims, LLaMA-70B at 8192 dims) should have better separation between structure and discriminative dimensions, more redundancy in suppression paths, and more room for sparse methods to work.

---

## Lessons Learned

**1. Separate filtering from scoring.** The structure that makes tokens easy to score (high-magnitude dims) is exactly what makes them hard to filter (structural advantage creates false positives). Use different dims for each job.

**2. The matmul IS the model.** There is no approximation gap between `lm_weight @ h` and the model's output. Any search method that finds the argmax of this dot product is finding the model's exact answer. The only question is how cheaply you can search.

**3. Ratio normalization is unnecessary when you remove the right dims.** The ratio (actual/max_possible) was the conceptual breakthrough that led to understanding the structure/discriminative split. But once you exclude structure dims, raw partial logit works identically. The ratio's value was diagnostic, not operational.

**4. Calibration-based approaches fail on this problem.** Every method that required learning per-token or per-neuron baselines from calibration data failed. The distributions are too context-dependent for small calibration sets to capture, and the discriminative signal lives in deviations smaller than the calibration noise.

**5. GELU networks are not sparse networks.** The entire gating framework assumes binary on/off neurons. GELU is analog — every neuron contributes, and the aggregate of thousands of small contributions is not small. Any sparse MLP approach for GELU networks must account for the continuous activation function, not just the sign.

**6. Test end-to-end before optimizing components.** The output layer optimization was validated on correct hidden states and works perfectly. But it doesn't help if the hidden states are wrong. Verifying the full pipeline early would have redirected effort toward the actual bottleneck (hidden state quality) sooner.

**7. The neighborhood property is real and useful.** Correct answers cluster with semantically related tokens in the discriminative subspace. This provides both a search target (find a coherent cluster) and a confidence signal (cluster coherence validates the result). This property likely generalizes to other transformer architectures.

---

## Proven Results Summary

| Component | Method | Accuracy | Cost | Speedup |
|---|---|---|---|---|
| Output layer | Discriminative filter (M=40, keep=200) + full logit | 100% (exact) | 5.6% of matmul | 17.8x |
| Output layer | With margin fallback | 100% (exact) | ~3% avg of matmul | ~33x avg |
| Output layer | Original hierarchy (baseline) | 95% | 2.6% of matmul | 38x |
| MLP layers | Sparse gating K=5 | 30% | ~4% of MLP cost | N/A (broken) |
| MLP layers | Oracle bilateral K=500/200 | 35% | 23% of MLP cost | N/A (broken) |
| Full pipeline (output only) | Best output search on full hidden state | 100% | 25% total inference reduction | 1.3x overall |

The output layer speedup is validated and ready for implementation. The MLP layer problem requires a fundamentally different approach than gate prediction.
