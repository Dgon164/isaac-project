# Range Classifier v2: Methods

**Status: Validated and optimized. Parity with source nets on 4/4 benchmark datasets.**

---

## 1. Core Architecture

Each concept is a set of per-dimension ranges with medians:

```
dim 0 [lo_0, hi_0 : med_0]
dim 1 [lo_1, hi_1 : med_1]
...
dim F [lo_F, hi_F : med_F]
```

### 1.1 Scoring

Two-tier comparison:

1. **Count**: How many dimensions fall within the concept's range? Higher = better fit.
2. **Median distance** (tiebreaker): Sum of |observation - median| for in-range dims. Lower = closer to prototype.

Classification: score observation against every concept. Highest count wins.

### 1.2 Why This Works

No single dimension needs to be exclusive. The conjunction across all dimensions does the discrimination. Even if every dimension overlaps between classes, the probability that ALL dimensions are simultaneously in-range for the wrong concept drops with dimensionality. Shared dimensions place the category. Different dimensions identify the specific.

This is integrated information: the classification depends on the joint pattern, not any individual feature. A count of "28 of 32 dims in range" vs "25 of 32" is a measurement of how well the whole pattern matches, not a weighted sum of independent signals.

---

## 2. Learning from Data

### 2.1 Quantization

Map features to 4-bit signed integers [-7, +8] (16 levels). Linear mapping from observed data range.

**Why 4 bits**: Empirically validated that 5, 6, 7, and 8 bits provide no accuracy improvement on any tested dataset. The discriminative information in hidden representations saturates at 16 levels. More resolution captures noise. This aligns with Shannon's rate-distortion theory — there is an optimal compression point where no task-relevant information is lost.

### 2.2 Percentile-Based Range Construction

For each class in the training data:

1. Collect all quantized observations belonging to that class
2. Per dimension: lo = percentile_1 - margin, hi = percentile_95 + margin, med = median
3. Default margin: 1.5 quantization steps

**Why percentiles instead of min/max**: Min/max ranges are dominated by outliers. A single extreme observation stretches the range box until it swallows neighboring classes. Percentile bounds (1st–95th) define the concept by its typical members, not its most extreme ones. Validated improvement: +0.9% on Breast Cancer, closing a persistent gap with the source net.

**Why margin=1.5**: Cross-validated across all datasets. Margin=1 is too tight (rejects valid members at test time). Margin=3 helps on some datasets (Wine: +2.2%) but hurts on others. Margin=1.5 is the best single default. Use `find_best_margin()` for automatic per-dataset tuning.

### 2.3 Hierarchical Confusion Resolution

After building general concepts, classify the training data against them. Misclassified examples reveal confusion zones — observations that belong to class A but score higher against class B.

Group misclassified examples by (true_label, confused_with). For each group with 3+ members, build a tighter variant concept. The variant inherits the parent's label and exists to win the specific contest where the general concept loses.

Iterate up to `max_splits` rounds (default 10). Stop when no new variants are created.

**Finding from validation**: Ensembles of crystals (multi-seed, multi-layer) degraded performance vs a single well-tuned crystal. Quality over quantity. One clean extraction with the right parameters beats a committee of noisy ones.

---

## 3. Crystallization from Neural Nets

### 3.1 Pipeline

1. **Extract hidden activations**: Run training data through the net, capture a hidden layer's output
2. **Strip DC**: Subtract the global mean. The common-mode component carries no discriminative information.
3. **Quantize**: Map residual activations to [-7, +8]
4. **Build range concepts**: Per class, compute lo/hi/med on quantized activations
5. **Resolve confusions**: Build variant concepts for misclassified training examples

### 3.2 Validated Retention Rates

| Dataset   | Net Accuracy | Crystal Accuracy | Retained |
|-----------|-------------|-----------------|----------|
| Iris      | 0.953       | 0.960           | 100.7%*  |
| Wine      | 0.983       | 0.994           | 101.1%*  |
| Breast Ca | 0.977       | 0.977           | 100.0%   |
| Digits    | 0.981       | 0.977           | 99.6%    |

*Crystal exceeds source net with optimized percentile ranges and margin.

### 3.3 Source Net Recommendations

Wider nets produce better crystals. MLP(128,64) and MLP(256,128) crystals consistently outperform MLP(64,32) crystals, even when the wider net doesn't improve its own classification. The wider net creates a more separable hidden space. Use the widest available net as the crystallization source.

---

## 4. Reservoir Crystallization (Zero Training)

Replace the trained net with a random net. Frozen weights, no backpropagation. The random nonlinear projection spreads data into a higher-dimensional space where axis-aligned ranges can separate it.

### 4.1 Results

| Dataset   | Random Crystal | Trained Crystal | Gap  |
|-----------|---------------|----------------|------|
| Iris      | 0.940         | 0.960          | 2.0% |
| Wine      | 0.944         | 0.994          | 5.0% |
| Breast Ca | 0.946         | 0.977          | 3.1% |
| Digits    | 0.880         | 0.977          | 9.7% |

Width matters more than depth. One wide layer (512 dims) outperforms multiple narrow layers.

### 4.2 Interpretation

The gap between random and trained grows with task complexity. For simple problems (Iris), a random projection is nearly as good as trained features — the data is already separable after mixing. For harder problems (Digits), training adds substantial value by finding the specific rotation that makes classes axis-aligned.

Training is not "just a mixer." But the mixer gets you surprisingly far, and what training adds is a specific coordinate system, not a fundamentally different kind of knowledge.

---

## 5. Efficiency

### 5.1 Inference Cost

| Net Size      | Net FLOPs  | Crystal FLOPs | Ratio |
|---------------|-----------|---------------|-------|
| Small(64,32)  | 12,928    | 1,440         | 9×    |
| Med(128,64)   | 34,048    | 2,880         | 12×   |
| Large(256,128)| 100,864   | 5,760         | 18×   |
| XL(512,256)   | 332,800   | 11,520        | 29×   |
| XXL(1024,512) | 1,189,888 | 23,040        | 52×   |

Net cost grows quadratically with width. Crystal cost grows linearly (concepts × hidden_dim × 3). The ratio increases monotonically.

### 5.2 Memory

A crystal model is: `n_concepts × n_dims × 3 vectors × 4 bits`. For Iris from MLP(128,64): 3 concepts × 64 dims × 3 × 4 bits = 2,304 bits = 288 bytes. The source MLP: ~33,000 float32 parameters = 132 KB. Compression ratio: ~460×.

---

## 6. Theoretical Connections

### 6.1 Shannon Information Theory

The 4-bit quantization finding is a measurement of channel capacity. The discriminative information in a neural net's hidden layer for classification tasks saturates at ~4 bits per dimension. This holds across datasets and architectures, suggesting it's a property of how neural nets encode categories, not a dataset-specific artifact.

A 124M parameter model crystallizing to a few KB of concepts means the actual information content for a classification task is orders of magnitude smaller than the model. Shannon would call this a wildly inefficient code.

### 6.2 Integrated Information (IIT)

The count score is a proxy for integrated information (phi). It measures how much of the whole pattern matches, not whether any individual dimension matches. The Wine dataset demonstrates this cleanly: no single feature separates any class pair, but the crystal classifies at 99.4% through conjunction across all 13 dimensions.

The confusion resolution system finds subsets of observations where a tighter integration pattern exists — analogous to IIT's complexes where phi is maximized.

### 6.3 GOFAI / Neurosymbolic

Range concepts are frame representations from classical AI. Bounded feature descriptions with prototype-based matching. The deep learning revolution rejected hand-crafted symbolic representations because they couldn't scale. What crystallization shows is that when you let a neural net learn freely and then examine what it learned, the result is symbolic: axis-aligned boxes, discrete boundaries, countable membership.

The connectionist-vs-symbolic debate may be a false dichotomy. The neural net is not an alternative to symbolic reasoning — it's an expensive, opaque way of finding the symbols.

---

## 7. Known Limitations

- **Axis-aligned boundaries**: Range concepts are hyperrectangles. Diagonal decision boundaries require more concepts or dimensionality reduction.
- **High-dimensional overlap**: With 768+ dims (transformer scale), most dims overlap between all classes. Compress to 32-64 discriminative dims before crystallizing.
- **Single distribution per dim**: Bimodal distributions within one class are captured as one wide range, not two tight ones.
- **Tree ensembles**: RF and GB leaf embeddings are sparse/discrete and crystallize poorly (36-81% retention). The method requires continuous hidden activations.

---

## 8. Optimal Defaults

| Parameter      | Default | Rationale |
|---------------|---------|-----------|
| Quantization  | 4-bit [-7,+8] | Empirically optimal; more bits add noise |
| Percentile    | [1, 95] | Resists outliers while preserving coverage |
| Margin        | 1.5     | Best single-value default across datasets |
| Max splits    | 10      | Sufficient for convergence; more doesn't help |
| Min group     | 3       | Prevents overfitting to individual outliers |

For production use: run `find_best_margin()` on training data to auto-tune margin per dataset.
