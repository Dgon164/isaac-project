# Positional Structure in Transformer Attention: Grammar as Token-Position Collision

**Date:** April 24, 2026  
**Status:** Draft — all claims backed by reproducible code on GPT-2 (124M)

---

## Abstract

We decompose the attention mechanism of GPT-2 into four independent terms arising from the additive combination of token and positional embeddings. The query-key dot product expands as: token-token (semantic routing), position-position (structural scaffolding), and two token-position cross-terms (grammatical rule encoding). Classifying all 144 attention heads by which term dominates reveals that 60% are primarily structural (position-based), 32% are rule encoders (dominated by the token-position collision), and only 8% are primarily semantic (token content). The collision terms — where token identity interacts with sequential position — encode grammatical constraints: "determiner at position N amplifies noun at position N+1." These continuous collision scores can be discretized into explicit grammatical rules by subtracting the positional baseline and thresholding at one standard deviation, reducing 120 raw dimensions to 45 discrete rules while discarding 62% as noise. The surviving rules correspond to recognizable English phrase structure. The finding that transformers are predominantly structural rather than semantic challenges the common framing of these models as primarily learning semantic relationships.

---

## 1. Introduction

Transformer language models combine two embedding matrices at their input: a token embedding (wte) mapping each vocabulary item to a vector, and a positional embedding (wpe) mapping each sequence position to a vector. The input to the first attention layer is their sum: x = wte[token] + wpe[position]. Interpretability research has focused heavily on the token embedding — analyzing what semantic relationships the model encodes — while the positional embedding and its interaction with token identity have received less attention.

We show that this interaction is where grammatical structure lives. By decomposing the attention score into four additive terms and measuring which term dominates each head, we find that the majority of GPT-2's attention heads are structural rather than semantic, and that the token-position cross-terms encode extractable grammatical rules.

---

## 2. Method

### 2.1 Four-Term Decomposition

The attention score between a query at position i and a key at position j, for a single head with learned projections W_Q and W_K, is:

    score(i,j) = (wte[i] + wpe[i])^T W_QK (wte[j] + wpe[j])

where W_QK = W_Q W_K^T. Expanding:

    score = wte[i]^T W_QK wte[j]        ... (T1: token→token)
          + wpe[i]^T W_QK wpe[j]        ... (T2: position→position)
          + wte[i]^T W_QK wpe[j]        ... (T3: token→position)
          + wpe[i]^T W_QK wte[j]        ... (T4: position→token)

T1 is purely semantic: which token types attend to which, regardless of position. T2 is purely structural: which positions attend to which, regardless of content. T3 and T4 are the collision terms: attention that depends on BOTH what the token is AND where it sits. We refer to T3+T4 collectively as the "collision signal."

### 2.2 Head Classification

For each of GPT-2's 144 attention heads (12 layers × 12 heads), we compute the squared magnitude of each term over a sample of category centroids (6 syntactic categories: determiner, noun, adjective, verb, preposition, pronoun) and positions 3-8. We classify each head by its dominant term:

- **SEMANTIC:** T1 > T2 and T1 > (T3+T4)
- **STRUCTURAL:** T2 > T1 and T2 > (T3+T4)
- **RULE ENCODER:** (T3+T4) > T1 and (T3+T4) > T2

### 2.3 Collision Rule Extraction

For each rule-encoder head, we compute only the collision terms (T3+T4) for all pairs of syntactic categories at relative offsets of -1, +1, +2, +3 positions. We aggregate across all rule-encoder heads, subtract the per-offset mean (removing positional bias), and threshold at one standard deviation to produce discrete rules.

---

## 3. Results

### 3.1 Head Classification

Of 144 attention heads:

| Type | Count | Percentage | Dominant signal |
|---|---|---|---|
| STRUCTURAL | 87 | 60.4% | Position→position |
| RULE ENCODER | 46 | 31.9% | Token×position collision |
| SEMANTIC | 11 | 7.6% | Token→token |

**Layer distribution:** Layer 0 heads are almost exclusively structural (97-98% position-dominated). Layer 1 contains the strongest rule encoders (L1H9: 95% collision, L1H8: 92%, L1H10: 86%). Later layers show a mix.

### 3.2 Structural Scaffolding

The 87 structural heads create a positional scaffold independent of token content. Layer 0 heads at 97-98% positional signal establish position-relative attention patterns before any semantic processing occurs. This scaffold determines which positions can attend to which other positions, creating the structural frame that content fills.

### 3.3 Collision Rules

After subtracting the positional baseline and thresholding at 1σ (noise floor = 22.3), 120 candidate rules reduce to 45 discrete rules (62% noise eliminated).

**Strongest extracted rules (by collision magnitude):**

| Source category | Relation | Target category | Score |
|---|---|---|---|
| verb | AVOIDS | preposition | -52.6 |
| determiner | EXPECTS | verb | +44.5 |
| adjective | AVOIDS | preposition | -43.5 |
| determiner | EXPECTS | pronoun | +38.5 |
| noun | EXPECTS | verb | +33.1 |
| noun | AVOIDS | preposition | -28.8 |
| verb | AVOIDS | determiner | -26.8 |
| determiner | EXPECTS | noun | +25.2 |
| pronoun | EXPECTS | verb | +23.6 |
| preposition | EXPECTS | verb | +22.9 |

These rules are consistent across offsets +1, +2, and +3, indicating they encode category-level preferences rather than fixed-distance constraints.

### 3.4 Per-Category Grammar

Aggregating the extracted rules by source category produces recognizable grammatical expectations:

**After determiner:** EXPECTS noun, verb, pronoun (noun phrase head or clause continuation)

**After noun:** EXPECTS verb, pronoun (predicate). AVOIDS preposition.

**After pronoun:** EXPECTS verb (predicate). AVOIDS preposition.

**After verb:** AVOIDS preposition, determiner (verb phrase boundary).

**After preposition:** EXPECTS verb (infinitival complement: "to run").

### 3.5 Validation Against Observed Text

We validated the extracted rules against 30 English sentences parsed into category sequences. The most frequent phrase patterns in the text align with the strongest collision rules:

| Pattern | Occurrences | Weight support |
|---|---|---|
| DET + ADJ + NOUN (noun phrase) | 23 | determiner→noun: +25.2 |
| NOUN + VERB (clause) | 19 | noun→verb: +33.1 |
| DET + NOUN | 18 | determiner→noun: +25.2 |
| PRONOUN + VERB | 9 | pronoun→verb: +23.6 |
| PREP + DET + NOUN (prepositional phrase) | 6 | determiner→noun: +25.2 |

---

## 4. Discussion

### 4.1 Transformers Are Predominantly Structural

The finding that 60% of attention heads are structural and only 8% are primarily semantic inverts the common understanding of these models. The prevalent framing — that transformers learn semantic relationships between words — describes less than one-tenth of the attention mechanism. The majority of computation establishes positional scaffolding and grammatical rules.

This is consistent with the observation that early layers (especially Layer 0) process position before content. The structural scaffold must be established before semantic routing can operate on it.

### 4.2 Grammar as Collision

The token-position collision terms (T3+T4) provide a natural formalization of grammatical rules. A rule like "determiners expect nouns" is not stored in any single weight — it emerges from the interaction between the determiner's token embedding and the noun's positional context through the QK projection. This distributed encoding explains why grammatical knowledge is difficult to localize in individual neurons or heads: it requires both the token identity and the positional context to manifest.

### 4.3 Discretization Preserves Structure

The reduction from 120 continuous dimensions to 45 discrete rules (62% compression) demonstrates that the grammatical signal is concentrated in a subset of the collision space. The majority of token-position interactions are noise — small, inconsistent variations that do not encode stable rules. Thresholding at one standard deviation cleanly separates the grammatical signal from this noise.

### 4.4 Implications for Hallucination

These findings connect to the hallucination problem. When the model generates text, it relies on the collision between the current token's embedding and the current position's embedding to determine what should come next. If the structural signal (from the 87 positional heads) and the grammatical signal (from the 46 rule-encoder heads) disagree with the semantic signal (from the 11 semantic heads), the prediction is structurally plausible but semantically wrong — a grammatically correct hallucination. The three-way decomposition (structural, grammatical, semantic) may provide a diagnostic for identifying predictions where these signals conflict.

### 4.5 Limitations

The analysis uses 6 syntactic categories with 5-7 probe tokens each. A broader category set and larger probe vocabulary would refine the rules and may reveal additional structure. The positional analysis samples positions 3-15; edge effects at sequence boundaries are not characterized. The head classification uses squared magnitude as the dominance metric; other metrics may produce different classifications. All results are from GPT-2 (124M parameters); scaling behavior to larger models is unknown.

---

## 5. Conclusion

The attention mechanism in GPT-2 decomposes into four terms. The dominant terms are structural (position-based) and grammatical (token-position collision), not semantic (token-based). Grammatical rules can be extracted from the collision terms by subtracting the positional baseline and discretizing, producing explicit phrase-structure rules that correspond to observed English syntax. The transformer is primarily a structural engine that routes information based on position and grammatical type, with semantic processing as a smaller component operating within the structural scaffold.

---

## Reproducibility

All analysis was performed on GPT-2 (124M parameters, publicly available via Hugging Face). Category centroids were computed from 5-7 tokens per category. Head classification used positions 3-8 with 3 sample categories. Collision rule extraction used all 144 heads, positions 3-15, 6 categories, and offsets [-1, +1, +2, +3]. Thresholding was at 1σ of the relative collision score distribution. Code is available upon request.

---

*Positional Structure in Transformer Attention — April 24, 2026*
