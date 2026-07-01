# Concept Harvesting with Basis Recalibration: Relocating Distributed Representations into Dedicated Neurons While Preserving Function

**Working paper — June 13 2026**
**Companion code: `concept_harvest.py` (self-contained, ~30s on CPU)**

---

## Abstract

We test whether an output-predicting "concept" learned by a trained transformer
can be **extracted** from its distributed representation and **relocated** into a
single dedicated neuron in a second, growing network — without changing the
network's overall function. We find that this is possible, but only if a specific
and easily-overlooked step is performed: after the representation is moved into a
new basis, the **output readout must be recalibrated to that new basis**. Because
everything downstream of the final hidden layer is linear, the recalibration is an
exact least-squares solve. With recalibration, the modified network reproduces the
original's logits to within float-rounding error (reconstruction error 2.3×10⁻³,
accuracy unchanged at 0.978). Without recalibration, the same extraction destroys
the network (error 4.67, accuracy collapses). Ablation confirms that each harvested
neuron cleanly owns its concept: removing it damages only that concept's predictions
and leaves all others intact, with the cleanliness of ownership scaling with how
concentrated (vs. distributed) the concept is. We interpret this as evidence that
(a) the "concepts" a network predicts are real and separable, (b) they are stored in
a shared, entangled basis (superposition), and (c) moving meaning between bases is
a translation that requires recalibrating any consumer of that meaning.

---

## 1. Motivation and hypothesis

A trained neural network represents many "concepts" (here: the disposition to
predict a particular next token) in a distributed, overlapping way: each hidden
dimension participates in many concepts, and each concept is spread over many
dimensions ("superposition"). This makes the representation compact but unreadable.

**Hypothesis.** For a given concept, the *strongest, cleanest* contributing
dimensions (the "peaks" of the concept's contribution profile) can be lifted out of
the shared representation and wired into a single dedicated neuron in a second
network. The original dimensions are then stripped, and the network's function is
preserved. Over many concepts, the second network grows into a set of clean,
single-concept neurons while the original is progressively stripped of its
identifiable structure.

**Prediction (registered before the recalibration step was added).** Naive
extraction will fail to preserve function, because the extracted peaks carry only
part of each concept and because peaks are *shared* across concepts. The fix is to
expand (give shared peaks per-concept copies) and to recalibrate the output to the
new basis.

---

## 2. Definitions

Let the network's final hidden state at a token position be **h** ∈ ℝ^d
(d = 64 here), produced after the last LayerNorm. The output logits are

    logits = W h        (W ∈ ℝ^{V×d}, the readout / unembedding matrix)

This last stage is **purely linear** in h — a fact we exploit throughout.

**Concept.** We operationalize a concept as "predicting next-character c". Its
readout row is W[c] ∈ ℝ^d.

**Fan (contribution profile).** For contexts that are actually followed by c, let
**h̄_c** be the mean final hidden state. The concept's *fan* is the per-dimension
contribution to its own logit:

    fan_c[i] = h̄_c[i] · W[c, i]        (i = 1..d)

This is the same per-dimension "vote" decomposition used elsewhere in the program:
logit_c = Σ_i fan_c[i]. The fan tells us how much each dimension contributes to
predicting c.

**Peaks.** The top-K dimensions of |fan_c| (K = 8 here). These are the
strongest, most identifiable contributors to the concept.

**Harvested neuron.** A new unit whose *read vector* r_c ∈ ℝ^d is the peak
activation pattern (h̄_c on the peak dimensions, zero elsewhere). Its activation on
any hidden state h is r_c · h. We then need to decide how this activation maps to
the output (its *write vector*); this is what recalibration determines.

---

## 3. Method

### 3.1 Base model

A standard 3-layer pre-norm transformer (d = 64, 4 heads, FFN width 256,
character-level, vocab 24) trained for 400 steps of AdamW on a small fixed corpus.
Reaches test loss 0.065, accuracy 0.978. (All hyperparameters in `concept_harvest.py`.)

### 3.2 Harvesting

For each character c (excluding newline):
1. Collect ≤40 input windows whose next character is c.
2. Compute the mean final hidden state h̄_c.
3. Compute fan_c = h̄_c ⊙ W[c].
4. Select the top-8 peak dimensions.
5. Build the read vector r_c (h̄_c on peaks, else 0).

This yields H = 23 harvested neurons (one per character with enough contexts).

### 3.3 The naive (failing) version

Strip the peak dimensions from the main readout (set W[c, peaks] = 0), and add a
harvested neuron that reads r_c (normalized) and writes to logit c with weight 1.0.

**Result:** reconstruction error 4.67; accuracy collapses 0.978 → 0.845. The
extraction preserves *direction* (ablation is clean — see §4.3) but destroys
*magnitude*, because the write weight (1.0) is an arbitrary guess in the new,
translated coordinate system, not the value that reproduces the peaks' original
contribution.

### 3.4 The recalibration (working) version — THE KEY STEP

The insight: moving the peaks into a harvested neuron changes the *basis* in which
the concept is represented. The output readout was calibrated to the **old** basis.
It must be re-fit to the **new** basis. Because the map from
[hidden state | harvest activations] to logits is linear, the re-fit is an exact
least-squares problem.

Two variants:

**V1 — full recalibration.** Use features [h | harvest_acts] ∈ ℝ^{d+H} and solve

    minimize ‖ [h | harvest_acts] · X − logits_original ‖²    over X ∈ ℝ^{(d+H)×V}

via `torch.linalg.lstsq`. This reproduces the original logits using both the
hidden state and the harvest activations.

**V2 — stripped main + fitted harvest.** Strip the peaks from the main readout,
then fit *only* the harvest write-weights B ∈ ℝ^{H×V} to supply the missing
contribution:

    residual = logits_original − (h · W_stripped^T)
    minimize ‖ harvest_acts · B − residual ‖²    over B

This is the stronger test: it forces the concepts to flow *through the harvested
neurons*, with the stripped main network unable to contribute the peak dimensions.

---

## 4. Results

All numbers from `concept_harvest.py`, seed 0, on a 300-window held-out set.

### 4.1 Reconstruction (the headline)

| Version | test loss | test acc | reconstruction err (mean |Δlogit|) |
|---|---|---|---|
| Base model | 0.0651 | 0.9778 | — |
| Naive extraction (no recal) | 1.051 | 0.845 | **4.67** |
| **V1 full recalibration** | 0.0651 | 0.9778 | **0.0023** |
| **V2 stripped + fitted harvest** | 0.0655 | 0.9780 | 0.075 |

With recalibration the network is reproduced **essentially exactly** (V1 error
2.3×10⁻³, i.e. float-rounding scale). Even when the peak dimensions are *removed*
from the main network and the concepts forced through the harvested neurons (V2),
the function is recovered (error 0.075, accuracy identical within noise).

### 4.2 Interpretation of the failure→success flip

The only difference between the 4.67-error failure and the 0.002-error success is
**whether the output was re-fit to the new basis.** This isolates the mechanism:
extraction was correct all along; the naive version simply read the relocated
representation through a readout calibrated for the *old* representation. The
"translation" (moving peaks into a harvested neuron) was not matched by a
re-calibration of the "reader" (the output layer). Once matched, the function is
preserved.

This is the general principle the experiment demonstrates:

> **Moving meaning into a new basis requires recalibrating every consumer of that
> meaning. The encoder transplant is only half the operation; the decoder must be
> re-fit to the new code.**

### 4.3 Ablation: do harvested neurons cleanly own their concepts?

Killing harvested neuron c (setting its activation to 0) and measuring accuracy on
c-targets vs. all other targets (V2):

| char | own_acc (full) | own_acc (ablated) | other_acc (ablated) |
|---|---|---|---|
| ' ' | 0.993 | 0.978 | 0.976 |
| 'a' | 0.993 | 0.924 | 0.978 |
| 'b' | 0.949 | **0.270** | 0.978 |
| 'c' | 0.958 | **0.701** | 0.979 |
| 'd' | 0.963 | 0.794 | 0.979 |
| 'e' | 0.990 | 0.980 | 0.977 |
| 'f' | 0.933 | 0.725 | 0.979 |
| 'l' | 0.960 | **0.634** | 0.979 |

**Two findings:**
1. **Other-concept accuracy is untouched** (always ≈0.978) regardless of which
   neuron is ablated. Each harvested neuron's influence is confined to its own
   concept — clean ownership.
2. **Own-concept damage scales with concentration.** Rare, distinctive characters
   (b, c, l) lose most of their accuracy when their neuron is killed — their
   concept genuinely lives in the harvested peaks. Common, highly-distributed
   characters (space, e) barely move — 8 peaks do not capture them, and the
   stripped main network still predicts them from the residual. This matches a
   "nested shell" view in which broad/common concepts are spread over far more than
   K dimensions while specific concepts concentrate.

---

## 5. What this does and does not show

**Shows.**
- Output-predicting concepts are *separable*: they can be relocated into dedicated
  units and ablated independently (clean per-concept ablation).
- The representation is *entangled in a shared basis*: peaks are reused across
  concepts, and naive relocation interferes.
- Function preservation under relocation *reduces to a linear recalibration* in
  this setting, and that recalibration is exact.

**Does not show (limitations / open questions).**
- **Linearity was essential.** We harvested from the *final* hidden layer, with
  only the linear readout downstream. The exact least-squares recalibration works
  *because* there are no nonlinearities between the harvest point and the output.
  Harvesting from a *middle* layer (nonlinearities downstream) will make
  recalibration approximate and may require a short retrain instead of a closed-form
  solve. This is the most important untested case.
- **Scale.** Demonstrated on a 24-token character model, d = 64, 3 layers. Behavior
  at GPT-2 scale and with real word-level concepts is untested.
- **"Concept = next character" is a deliberately simple operationalization.** Richer
  concepts (semantic categories, relations) are not tested here.
- **Common concepts were not fully captured by K = 8 peaks.** A complete extraction
  of distributed concepts would require larger or adaptive K, or multiple neurons
  per concept (expansion).

---

## 6. How to reproduce

```bash
python3 concept_harvest.py
```

Expected output (seed 0): base acc 0.978; V1 reconstruction error ≈ 2×10⁻³ with
unchanged accuracy; V2 accuracy ≈ 0.978; ablation table showing clean per-concept
ownership with concentration-dependent damage.

The script is fully self-contained (only `torch` and `numpy`). Every result in this
paper is printed by it. To explore:
- Change `TOP_K` to see how peak count affects capture (more peaks → more complete
  concepts, less clean separation).
- Change `SEED` to confirm the qualitative result is seed-independent (the exact
  numbers will vary; the failure→success flip and clean ablation will not).
- Replace the corpus or move to a larger model to probe scaling.

---

## 7. Suggested next experiments

1. **Middle-layer harvest.** Harvest from an intermediate layer and test whether a
   short retrain of downstream weights recovers function (linearity no longer
   guarantees an exact fit). This is the decisive test for whether the method
   generalizes beyond the final layer.
2. **Iterative harvesting.** Harvest concept after concept, each time stripping and
   recalibrating, and measure how the main network degrades and the second network
   grows. Does the second network converge to a clean, mostly-monosemantic set?
3. **Adaptive K via the fan slope.** Instead of fixed K = 8, cut each concept's fan
   at the point where its sorted contribution flattens (the "irreducible width"),
   giving each concept exactly as many peaks as it needs.
4. **Expansion for shared peaks.** Give each shared peak dimension a per-concept
   copy in the second network, removing cross-concept interference, and test
   whether V2 reconstruction error drops toward the V1 level.

---

## Appendix: the linear-recalibration argument

Let the final hidden state be h and the original logits be ℓ = W h. Introduce
harvest activations a = R h (R the matrix of read vectors). The augmented feature
vector is φ = [h ; a] = [I ; R] h, a linear function of h. Any target that was a
linear function of h — in particular the original logits ℓ = W h — is therefore a
linear function of φ, so there exists an exact X with φᵀ X = ℓ for every h in the
span. Least squares recovers it. This is why V1 reconstruction error is at
float-rounding scale and not merely small: the solution is exact up to the
conditioning of the lstsq solve. The argument fails the moment a nonlinearity sits
between the harvest point and the output, which is precisely why middle-layer
harvesting is the key open case.
