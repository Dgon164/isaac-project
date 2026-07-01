# The Decompositional Structure of GPT-2: A Complete Analysis

## What This Document Is

This is a complete account of what we found by treating GPT-2's weight matrices as data — not running the model, but reading its weights the way you'd read a document. The analysis spans two research sessions using a structural inference engine that applies a single comparison primitive across multiple substrates. Everything reported here is reproducible from the publicly available GPT-2 (124M parameter) model weights.

---

## Part 1: The Architecture We're Decomposing

GPT-2 is a 12-layer transformer with 12 attention heads per layer (144 total heads), an embedding dimension of 768, and an MLP hidden dimension of 3,072 neurons per layer (36,864 total). Its vocabulary is 50,257 byte-pair-encoded tokens.

The model has five learnable weight matrices that interact to produce predictions:

**Token embeddings (wte):** A 50,257 × 768 matrix. Each row is the model's representation of a token — its "meaning" in 768-dimensional space.

**Positional embeddings (wpe):** A 1,024 × 768 matrix. Each row encodes a sequence position. Position 0 has a unique 768-dimensional vector, position 1 has a different one, and so on up to position 1,023.

**Attention weights:** Each layer has three projections — Query (W_Q), Key (W_K), and Value (W_V) — plus an output projection (W_O). These create the attention routing and effect circuits.

**MLP weights:** Each layer has an up-projection (W_up: 768→3,072) and a down-projection (W_down: 3,072→768), with a GELU nonlinearity between them.

**Unembedding:** The final prediction uses wte transposed to project from the 768-dimensional space back to a 50,257-dimensional probability distribution over the vocabulary.

The critical interaction: at every position in the input sequence, the model ADDS the token embedding and the positional embedding before any attention computation occurs. The actual input to Layer 0 is:

    x[position] = wte[token_at_position] + wpe[position]

This addition is where the structural rules of the language meet the identity of the words. Everything that follows from this analysis traces back to this single operation.

---

## Part 2: The Token Embedding Space

### 2.1 What the embeddings encode

Each of the 50,257 tokens occupies a point in 768-dimensional space. Tokens that appear in similar contexts during training end up at similar locations. "Dog" is near "cat" because both appear after "the," before "runs," and in similar sentence frames. This proximity IS the encoding of category membership — no explicit label is needed.

### 2.2 SVD decomposition — the natural axes

Singular Value Decomposition of the embedding matrix reveals the natural coordinate system of the token space. 558 axes account for 90% of the variance; 50 axes capture the most structurally meaningful dimensions.

The top axes are dominated by morphological features, not semantic categories:

- Six separate axes primarily encode past tense (-ed endings)
- Three axes primarily encode progressive/gerund forms (-ing endings)
- Multiple axes encode abstract noun suffixes (-tion, -ment)
- Multiple axes encode adjective forms (-ous, -ive, -ful)

This is a significant finding: the model devotes more representational capacity to WORD FORM than to word meaning. The morphological structure of English is, from the model's perspective, more important to represent than the semantic categories.

### 2.3 Category centroids and structural separation

Computing the centroid (average embedding) for known semantic categories reveals clear categorical structure:

- Animals, foods, countries, colors, numbers, professions, body parts, and materials form distinct clusters in the embedding space
- Categories that are semantically distinct (number vs. animal) have low cosine similarity between their centroids
- Categories that share contextual overlap (food and animal, via tokens like "chicken" and "fish") show higher similarity

Tokens that belong to multiple categories (like "fish" = animal or food, "crane" = bird or machine) sit between the centroids of their categories. This intermediate position is what makes them ambiguous — the model encodes both meanings in a single vector, and context must resolve which meaning applies.

### 2.4 Anti-occurrence — features that never co-occur

The SVD decomposition reveals 164 pairs of features that never share a neuron in the MLP layers. These structural separations represent hard constraints: certain types of information are kept independent in the model's representation. The strongest separation is between syntax-related features and semantics-related features — the model maintains a wall between "how the sentence works" and "what the sentence is about."

---

## Part 3: The Dual Subsystem — MLP vs. Attention

### 3.1 The MLP frequency prior

The MLP circuit (the feedforward layers) encodes what is COMMON. When we compose the MLP weight matrices across all 12 layers into a single linear map and rank every token by its output score, the top-ranked tokens are invariably function words:

| Rank | Token |
|---|---|
| 1 | , (comma) |
| 2 | the |
| 3 | . (period) |
| 4 | of |
| 5 | and |
| 6 | to |
| 7 | in |
| 8 | a |

This is the frequency prior. The MLP's default prediction is always a function word — the most common tokens in English. Content words rank low. "Chicken" is at rank 12,346. "Paris" is at rank 8,921.

This is not an error. It is a structural feature. The MLP says "absent any other information, predict a function word." This is the correct prior for English, where function words account for the majority of all tokens in natural text.

### 3.2 The attention content discriminator

The attention OV (output-value) circuit does the opposite. When we compose the W_V and W_O matrices for each head and rank tokens by their output score, content words dominate:

| Token | MLP Rank | Attention Rank |
|---|---|---|
| the | 8 | 50,255 |
| chicken | 12,346 | 6 |
| Paris | 8,921 | 12 |
| , (comma) | 1 | 49,000+ |

The rankings are nearly perfectly inverted. What the MLP predicts most strongly, the attention circuit predicts least, and vice versa. This is a systematic structural opposition, not noise.

### 3.3 The selection mechanism

The model's prediction at any given position is the sum of MLP and attention contributions. The MLP says "comma." The attention says "Paris." What determines the actual prediction?

GELU (the nonlinearity in the MLP) acts as a gate. Neurons with activation below a threshold are zeroed out. Neurons above the threshold pass through. In effect, GELU selects which MLP neurons contribute to the prediction. The attention circuit, by modifying the residual stream, influences which MLP neurons clear the GELU threshold.

This creates an elimination cascade: the MLP starts with a frequency-based prior (predict function words). Attention provides content-specific evidence (this context calls for a noun, specifically a place name). The GELU gate eliminates MLP neurons that disagree with the attention signal. What survives is the intersection of "common enough to have MLP support" and "contextually appropriate according to attention."

Hallucinations occur when the MLP prior overwhelms the attention evidence — the model defaults to the statistically common answer rather than the contextually correct one.

---

## Part 4: The Winning Ticket — Readable Neurons

### 4.1 Only 2% of neurons carry readable structure

Of 36,864 MLP neurons (12 layers × 3,072 neurons per layer), only 729 (1.98%) produce output vectors that clearly align with one or more semantic categories. We call these the "winning ticket" — the neurons whose output projections, when compared against category centroids, show strong positive (driving) or strong negative (inhibiting) alignment.

### 4.2 Gradient-shaped distribution

The readable neurons are not uniformly distributed across layers. They concentrate heavily in Layer 11 (the final layer), which contains 58% of all readable neurons. This gradient shape — more readable structure in later layers — makes architectural sense: early layers build intermediate representations, and the final layer must project directly into the vocabulary space where category structure is explicit.

### 4.3 Drive/inhibit asymmetry

Each readable neuron either drives a category (strong positive projection toward the category centroid) or inhibits a category (strong negative projection away from it). The counts are asymmetric:

| Category | Drive neurons | Inhibit neurons | Ratio |
|---|---|---|---|
| Number | 141 | 86 | 1.64 (net positive) |
| Body part | 59 | 59 | 1.00 |
| Color | 58 | 61 | 0.95 |
| Material | 59 | 100 | 0.59 |
| Country | 85 | 181 | 0.47 |
| Food | 87 | 199 | 0.44 |
| Animal | 82 | 192 | 0.43 |
| Profession | 90 | 222 | 0.41 |

Number is the ONLY category where drive exceeds inhibit. Every content category has 2–2.5× more inhibition than activation. The model's default state for content categories is suppressed. Content must earn its way past the background suppression — which is the GELU gate mechanism described above.

### 4.4 Structural separation: syntax and semantics never share a neuron

Among the 729 readable neurons, no single neuron drives both a syntactic feature and a semantic feature. Neurons that respond to animal-related tokens never also respond to syntax-related tokens. This separation is absolute in the data — not a gradient, but a wall. The model maintains independent circuitry for structural and semantic processing.

---

## Part 5: The Positional Embedding — The Encoding Mask

### 5.1 What it is

The positional embedding matrix (wpe, 1024 × 768) assigns a unique 768-dimensional vector to every position in the sequence. Position 0 has one vector, position 1 has a different one, position 2 another, and so on. This vector is ADDED to the token embedding at that position before any attention processing occurs.

This means the same word has a different combined vector at every position. "Dog" at position 3 is a different signal than "dog" at position 7. The attention heads see a different input. They route differently. The positional embedding is a mask that shifts every token's representation based on where it sits in the sequence.

### 5.2 The four-term decomposition

Because the input to attention is the sum wte + wpe, the attention QK (query-key) dot product — which determines what attends to what — decomposes into four independent terms:

    score(i,j) = [wte(i) + wpe(i)]^T × W_QK × [wte(j) + wpe(j)]

    Expanding:

    Term 1:  wte(i) × W_QK × wte(j)    — token→token    (semantic)
    Term 2:  wpe(i) × W_QK × wpe(j)    — position→position (structural)
    Term 3:  wte(i) × W_QK × wpe(j)    — token→position   (collision)
    Term 4:  wpe(i) × W_QK × wte(j)    — position→token   (collision)

Previous interpretability work has focused almost exclusively on Term 1 — what tokens attend to what other tokens. Terms 2, 3, and 4 have been largely ignored.

### 5.3 What each term encodes

**Term 1 (token→token):** This is the semantic routing. "Dog" attends to "cat" because they're semantically similar. This term operates independently of position — it would produce the same score regardless of where in the sequence the tokens appear.

**Term 2 (position→position):** This is the structural scaffold. Position 5 attends to position 4 regardless of what tokens fill those positions. This creates the skeleton of the sequence — the bare structural frame before any content fills it.

**Term 3 (token→position):** The token seeks a position. "The" (a determiner) produces high QK scores toward position N+1 regardless of what token is at N+1. The token knows where its dependent should be.

**Term 4 (position→token):** The position expects a token type. Position N+1 (after a determiner position) produces high QK scores toward noun tokens regardless of where those nouns sit. The position has a typed slot.

Terms 3 and 4 together are the COLLISION — where the identity of the token interacts with the structure of the position. This is where grammatical rules live.

### 5.4 Head classification: 60/32/8

We classified all 144 attention heads by which term dominates their QK computation:

| Head type | Count | Percentage | What dominates |
|---|---|---|---|
| STRUCTURAL | 87 | 60.4% | Position→position (Term 2) |
| RULE ENCODER | 46 | 31.9% | Token×position collision (Terms 3+4) |
| SEMANTIC | 11 | 7.6% | Token→token (Term 1) |

This is the most consequential finding of the analysis. The common understanding of transformers — that they learn relationships between tokens — describes less than 8% of the attention mechanism. The overwhelming majority of attention heads care about POSITION, either directly (structural heads) or through the collision with token identity (rule encoders).

### 5.5 Layer distribution

Layer 0 heads are almost exclusively structural: 97–98% of their QK computation is the position→position term. These heads establish the structural scaffold before any content processing occurs.

Layer 1 contains the strongest rule encoders. L1H9 is 95% collision — virtually all of its attention routing depends on the interaction between what the token is and where it sits. L1H8 is at 92%, L1H10 at 86%.

Later layers show a mix of all three types, with semantic heads appearing more frequently as the model nears its output.

The architectural implication: the model builds a structural skeleton (Layer 0), installs grammatical rules (Layer 1), and then fills in semantic content (later layers). Structure first, grammar second, meaning third.

---

## Part 6: Grammar Extraction from Collision Terms

### 6.1 Method

For each rule-encoder head, we compute only the collision terms (Terms 3+4) for all pairs of syntactic categories at relative offsets of -1, +1, +2, and +3 positions. We aggregate across all 46 rule-encoder heads, then apply two noise-reduction steps:

**Baseline subtraction:** For each offset, we compute the mean collision score across all category pairs and subtract it. This removes the positional bias — the fact that offset +1 has a higher baseline than offset +3 regardless of what categories are involved. What remains is the category-SPECIFIC signal: how much more or less this particular category pair co-occurs at this offset than the average pair.

**Thresholding:** We compute the standard deviation of the baseline-subtracted scores and zero out any score within one standard deviation of zero. These are the noisy dimensions — scores that could be measurement noise rather than real structure.

### 6.2 Results

120 candidate rules (6 categories × 5 other categories × 4 offsets) reduce to 45 discrete rules after noise elimination. 62% of the raw signal was noise.

The surviving rules, ranked by magnitude:

| Source | Relation | Target | Score | Interpretation |
|---|---|---|---|---|
| verb | AVOIDS | preposition | -52.6 | Verbs and prepositions occupy different structural frames |
| determiner | EXPECTS | verb | +44.5 | After a determiner, verb is amplified |
| adjective | AVOIDS | preposition | -43.5 | Adjectives don't precede prepositions |
| determiner | EXPECTS | pronoun | +38.5 | Determiner position also accepts pronouns |
| noun | EXPECTS | verb | +33.1 | Subject-predicate: noun primes verb |
| noun | AVOIDS | preposition | -28.8 | Nouns don't directly precede prepositions |
| verb | AVOIDS | determiner | -26.8 | Verb phrase boundary |
| determiner | EXPECTS | noun | +25.2 | Determiner primes noun (the NP rule) |
| pronoun | EXPECTS | verb | +23.6 | Subject-predicate (pronoun variant) |
| preposition | EXPECTS | verb | +22.9 | Infinitival complement: "to run" |

### 6.3 Per-category grammar

Aggregating by source category produces recognizable grammatical expectations:

**After determiner:** EXPECTS noun (+25.2), verb (+44.5), pronoun (+38.5). The determiner opens a phrase that can continue with a noun (noun phrase), a verb (reduced relative), or a pronoun (demonstrative use).

**After noun:** EXPECTS verb (+33.1), pronoun (+27.0). The noun primes the predicate. AVOIDS preposition (-28.8).

**After pronoun:** EXPECTS verb (+23.6). Pronouns prime predicates, same as nouns. AVOIDS preposition (-36.0).

**After verb:** AVOIDS preposition (-52.6), AVOIDS determiner (-26.8). The verb creates a boundary — it resists being followed by the structural elements that introduce new phrases.

**After preposition:** EXPECTS verb (+22.9). This captures infinitival "to" constructions.

**After adjective:** AVOIDS preposition (-43.5). Adjectives don't transition into prepositional phrases.

### 6.4 Validation against observed text

30 English sentences parsed into category sequences confirm the extracted rules:

| Phrase pattern | Occurrences | Weight support |
|---|---|---|
| DET + ADJ + NOUN (noun phrase) | 23 | determiner→noun: +25.2 |
| NOUN + VERB (clause core) | 19 | noun→verb: +33.1 |
| DET + NOUN | 18 | determiner→noun: +25.2 |
| PRONOUN + VERB | 9 | pronoun→verb: +23.6 |
| PREP + DET + NOUN (PP) | 6 | determiner→noun: +25.2 |
| DET + ADJ + NOUN + VERB | 10 | noun→verb: +33.1 |
| VERB + DET + ADJ + NOUN (VP with object) | 8 | determiner→noun: +25.2 |

The phrase patterns observed in text correspond exactly to the rules extracted from the weights. The two sources — statistical observation of sentences and structural analysis of weight matrices — converge on the same grammar.

---

## Part 7: Layer-by-Layer Chaining and Interference

### 7.1 The cascade

Each layer's output modifies the residual stream, which becomes the next layer's input. Layer 0 processes the raw embeddings and produces a modified representation. Layer 1 processes that modified representation and produces a further modification. The final prediction is shaped by the entire 12-layer cascade.

For sequential rules, this means the effect builds across layers. "Noun primes verb" is not encoded in a single layer. It is the accumulated effect of multiple layers each pushing the residual stream incrementally toward verb-space after processing a noun.

### 7.2 Constructive vs. destructive interference

Within each layer, 12 attention heads fire simultaneously. For any given category transition (e.g., noun→verb), some heads amplify it and others suppress it. When most heads agree (8+ amplifying, 2-3 suppressing), the interference is constructive and the rule is strong. When heads are split (5 amplifying, 5 suppressing), the interference is destructive and the rule is weak or context-dependent.

The interference pattern tells us how confident the model is about each rule. Strong rules have constructive interference across most heads. Weak rules have destructive interference — the model is "unsure" because its own circuits disagree.

### 7.3 Two-layer chains

When Layer N pushes the residual from category A toward category B, and Layer N+1 pushes from B toward C, the combined effect is a two-layer chain: A → B → C. These chains encode multi-step derivations. For example, if Layer 8 pushes noun→action-space and Layer 9 pushes action-space→verb-space, the chain encodes: "after a noun, through an intermediate action representation, the model arrives at verb predictions."

These chains are the mechanism by which the model implements context-dependent processing. No single layer makes the full prediction. The prediction emerges from the sequential composition of partial effects.

---

## Part 8: The Residual — What We Can't See Yet

### 8.1 The dark matter

The known categories (14 categories including semantic and syntactic types) plus the frequency axis span a subspace of the 768-dimensional embedding space. When we project all token embeddings onto this known subspace and measure the variance explained, a substantial fraction of the total variance lies OUTSIDE the subspace.

This residual variance is structure that the model uses but that we cannot name. It is not category membership, not frequency, not syntactic type. It is "dark matter" — it functions, but we don't know what it represents.

### 8.2 Hidden feature axes

SVD on the residual embeddings (after subtracting the known category subspace) reveals axes that are orthogonal to all known categories. These hidden axes group tokens in ways that have no standard linguistic label:

- One axis groups "lockout, foreclosure, blackout, bailout" — compound verb-direction nouns (the -out morphological class)
- Another groups "intolerable, wretched, unpleasant" against "iPads, Libraries, Packs" — negative evaluation vs. commercial categories
- Another groups "phosphate, valves, kilometers" against "Fear, Shame, Truth" — technical-concrete vs. abstract-emotional

These are real features that the model uses for prediction. They don't have names in English grammar. The model discovered them from data.

### 8.3 Hidden neurons

MLP neurons can also be decomposed into known and residual components. Neurons where more than 80% of their weight vector lies outside the known category subspace are serving the hidden structure. These neurons are not responding to animals or colors or syntax. They are processing the unnamed features.

---

## Part 9: The Mechanism of Hallucination

### 9.1 Hallucination as boundary crossing

The model's predictions exist in a continuous probability space. For most predictions, the correct answer has a large probability margin over alternatives — the decision is clearly on one side of the boundary. Hallucinations occur at the boundary, where two or more options have nearly equal probability.

"The fish is a ___" might have P(animal) = 0.660 and P(food) = 0.612. The gap is 0.048. Temperature (the randomness injected during sampling) can easily flip this decision. Sometimes the model outputs "animal." Sometimes "food." Sometimes something entirely wrong that happened to have probability 0.55 due to the MLP frequency prior boosting it.

### 9.2 Three factors that amplify hallucination

**The boundary moves with context.** "Fish" after "I caught a" → animal. "Fish" after "I ordered the" → food. The model's boundary shifts based on what preceded the token. If the context window doesn't capture enough disambiguating signal, the model operates with the wrong boundary position.

**Temperature amplifies boundary errors.** At temperature 0 (greedy decoding), the model always picks the highest-probability option. Hallucinations still occur when the wrong option is genuinely ranked highest, but they are deterministic. At temperature > 0, random sampling can flip any near-boundary decision. Higher temperature = more boundary crossings = more hallucinations.

**The model cannot distinguish near-boundary from far-from-boundary predictions.** A prediction with P=0.52 vs. P=0.48 produces a token with the same confidence as a prediction with P=0.95 vs. P=0.05. The model has no mechanism to flag uncertainty. Every output looks equally confident.

### 9.3 The structural explanation

The 60/32/8 head classification provides a structural explanation for why hallucinations are often grammatically correct. The 87 structural heads and 46 rule-encoder heads ensure the output follows English grammar. The 11 semantic heads provide content. When the semantic signal is weak (ambiguous context, rare entity, knowledge boundary), the structural scaffold still functions perfectly — producing grammatically impeccable nonsense.

This is consistent with the MLP prior analysis: the default prediction is always a common function word, which is always grammatically appropriate. Hallucination is not the model failing to produce language. It is the model producing structurally perfect language with the wrong content, because the structural and grammatical circuits (92% of attention) function correctly even when the semantic circuits (8% of attention) are uncertain.

---

## Part 10: Sequential Pattern Discovery

### 10.1 Self-squash — the refractory period

When the system processes a sequence of claims and observes that the same category appears repeatedly within a short window, it creates a self-suppression rule. "Noun" appeared 43 times within 5 ticks of itself → noun SQUASHES noun (weight 2.0). This is the refractory period: after a category fires, it suppresses itself temporarily, making repetition less likely.

This behavior mirrors the MLP drive/inhibit data: every content category has more inhibition neurons than drive neurons. The default state is suppressed. A category fires only when sufficient evidence overcomes the suppression, and after firing, the suppression returns.

### 10.2 Cross-category priming

From the same observation process, the system discovers that certain categories follow each other more often than chance would predict. Noun → verb at 4.9× the expected frequency → noun AMPLIFIES verb. These cross-category rules correspond to the grammatical expectations extracted from the collision terms, providing independent confirmation from two different methods.

### 10.3 Emergent categories

When the system processes raw claims with no prescribed categories, it discovers its own groupings. Entities that appear as both SOURCE of DID and SOURCE of HAS_PROPERTY form one group (animate nouns). Entities that appear only as SOURCE of HAS_PROPERTY form another (inanimate nouns). Entities that appear only as TARGET of HAS_PROPERTY form a third (adjectives). Entities that appear only as TARGET of DID form a fourth (verbs).

The system discovered the animate/inanimate distinction — a real linguistic category — without being told it exists. The structural signature was sufficient.

---

## Part 11: What We Still Don't Know

### 11.1 Combinatorial patterns

The current analysis finds pairwise relationships: A→B, A SQUASHES B. The deeper structure of language involves combinatorial patterns: when A AND B are both present, C emerges. "Subject + auxiliary → inverted question" requires both elements to be present simultaneously. Pairwise analysis cannot capture this.

### 11.2 The full residual

We identified that a substantial fraction of embedding variance lies outside the known category subspace, but we only examined this residual through its SVD axes. The full characterization — what the residual encodes, how neurons serve it, and how it interacts with the positional mask — requires projecting all 50,257 tokens onto each residual axis and analyzing the resulting clusters.

### 11.3 Scaling behavior

All analysis was performed on GPT-2 (124M parameters, 12 layers, 768 dimensions). Whether the 60/32/8 head classification, the dual subsystem architecture, and the collision-based grammar extraction scale to larger models (GPT-2 Medium, Large, XL, or architectures like Llama, Qwen, etc.) is unknown.

### 11.4 Dynamic behavior

The entire analysis operates on static weights. The model's dynamic behavior — how computations unfold during actual inference with GELU gating, LayerNorm rescaling, and softmax attention — is not captured. The static analysis reveals what the weights encode, not what the model does on any particular input. The gap between these may be small (if the static structure is a good approximation) or large (if dynamic interactions dominate).

### 11.5 Phrase-level sub-definitions

The phrase rules discovered (NP, VP, PP, CLAUSE) are structural frames. The same frame has different behavior depending on what fills it. "The big dog runs" (physical entity → action verb) uses the same NP+VP structure as "the big idea spreads" (abstract concept → state verb). The system needs to discover sub-definitions of phrases parameterized by the semantic type of their head word. This requires more data — a full book rather than 30 sentences.

---

## Part 12: Summary of Findings

1. **GPT-2's attention is 60% structural, 32% grammatical, 8% semantic.** The common framing of transformers as semantic relationship learners describes less than one-tenth of the attention mechanism.

2. **The positional embedding is a grammatical mask.** It collides with token embeddings to create position-dependent representations that the attention QK circuits read as grammatical signals. The grammar is not in the tokens or the positions alone — it is in the collision between them.

3. **The MLP and attention circuits are structurally opposed.** MLP encodes frequency (predict common tokens). Attention encodes content (predict contextually appropriate tokens). GELU selects the winner by elimination. The default is the common token; context must override it.

4. **Only 2% of MLP neurons carry readable semantic structure.** These are concentrated in Layer 11 (58%). Every content category has more inhibition than activation — the default state is suppressed.

5. **Syntax and semantics never share a neuron.** The model maintains a structural wall between "how the sentence works" and "what it's about." This separation is absolute in the readable neuron population.

6. **Grammatical rules can be extracted from collision terms.** 120 raw dimensions reduce to 45 discrete rules after baseline subtraction and 1σ thresholding (62% noise elimination). The surviving rules correspond to English phrase structure: determiner→noun, noun→verb, prepositional phrases, clause boundaries.

7. **The model builds structure first.** Layer 0 is 97-98% positional — pure structural scaffolding. Layer 1 installs grammatical rules via collision. Later layers fill in semantic content. The processing order is: skeleton → grammar → meaning.

8. **Hallucinations are structurally perfect semantic failures.** The 92% of attention that is structural/grammatical functions correctly even when the 8% that is semantic is uncertain. The result is grammatically impeccable text with the wrong content.

9. **A substantial fraction of the embedding space encodes unnamed structure.** After stripping the 14 known categories and the frequency axis, residual structure remains that has no linguistic label. The model discovered features of language that we haven't named yet.

10. **All of the above was extracted from static weights without running the model.** The weight matrices, read as data, contain the encoded grammar, semantics, and structural architecture of the language the model was trained on.

---

*The Decompositional Structure of GPT-2 — Sessions 9 & 10, April 2026*
