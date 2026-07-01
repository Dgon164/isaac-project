# The Structure of Information: Nine Empirical Constraints on How Meaning Organizes

### A framework for understanding representational structure, derived from decompositional analysis of learned systems and constructive experimentation with graph-based substrates

---

## Abstract

We present nine empirical claims about how information organizes when a system — biological, artificial, or formal — must represent structured knowledge for downstream reasoning. These claims are derived from two independent lines of investigation: (1) static decompositional analysis of the weight matrices of GPT-2 (124M), which revealed the internal representational strategy a system trained on natural language converges to, and (2) constructive experimentation with a deterministic graph-based reasoning engine built across 19 development sessions, which arrived at convergent structure from first-principles constraints. Neither line was designed to confirm the other. The convergence is the finding.

The nine claims are: information self-separates into independent constraint layers; meaning is an intersection address rather than a mixture of components; useful categorization compresses at a consistent 4–7:1 ratio; structure is learned before content in any sequential system; the default state of content is suppression; specific output is determined by constructive interference of independent signal waves; correctability is more fundamental than correctness; the same structural operation applies at every scale; and lossy aggregation at storage time destroys downstream signal. Each claim is stated, the evidence is summarized, and testable predictions are offered for independent verification.

We argue that these are not design recommendations for AI systems. They are empirical properties of how structured information behaves. Any system that represents sequential, structured, correctable knowledge will either discover these constraints or violate them at a measurable cost.

---

## 1. Introduction

Two very different investigations converged on the same structural findings. We did not expect this. The convergence is what motivates this paper.

The first investigation decomposed a trained language model (GPT-2, 124M parameters) by reading its weight matrices as static data — not running the model, but treating the trained weights as a document encoding the structure of English. This produced a detailed picture of how the model internally organizes syntactic, grammatical, and semantic information, including a four-term decomposition of the attention mechanism and a complete drive/inhibit census of the MLP neurons.

The second investigation built a reasoning engine from a minimal set of axioms — one storage primitive, one input path, one comparison operation — and observed what structural properties emerged as the system processed increasingly complex corpora. This engine was constructed iteratively across 19 sessions with a human operator directing architectural decisions and an AI assistant implementing them.

The two systems share almost nothing in substrate. One is a continuous, differentiable, gradient-trained neural network with 124 million parameters. The other is a discrete, deterministic graph with named nodes and typed edges, operating on a few thousand elements. One learned from a trillion tokens of internet text. The other learned from hand-curated corpora of a few hundred sentences.

They arrived at the same organizational structure.

This paper extracts the structural findings that both systems converge on, states them as empirical claims about information itself, and offers testable predictions for each. The claims do not depend on either system being correct or complete. They depend on the convergence being real — which is independently verifiable by anyone with access to GPT-2's public weights and a willingness to build a comparison-based graph engine.

---

## 2. Claim 1 — Information self-separates into independent constraint layers

### Statement

When a system must represent structured sequential information, the representation self-organizes into semi-independent layers, each encoding a different kind of constraint. These layers operate simultaneously on the same data but do not share representational resources.

### Evidence from decomposition

The GPT-2 attention mechanism decomposes into four mathematical terms via the QK dot product expansion:

- Term 1: token→token (semantic similarity)
- Term 2: position→position (structural scaffolding)
- Term 3: token→position (token seeks a structural slot)
- Term 4: position→token (structural slot expects a token type)

Classifying all 144 attention heads by which term dominates reveals a 60/32/8 split: 60% of heads are primarily structural (position-based), 32% are rule encoders (token–position collision), and 8% are primarily semantic (token-based). Within the readable MLP neuron population, the separation is absolute: no single neuron serves both a syntactic and a semantic function. The model maintains a hard wall between structural processing and content processing.

### Evidence from construction

The graph-based engine, processing corpora with no linguistic knowledge installed, consistently forms structural categories before content categories. Function-word circles (prepositions, determiners, auxiliaries, pronouns, conjunctions) emerge from positional dim-overlap alone. Content circles require richer input signal and form later, through different mechanisms. The two kinds of circle occupy different regions of the graph and do not interfere.

### Testable prediction

Any system trained on sequential structured data — in any language, any modality, any substrate — will develop separable structural and content processing layers. This should be measurable as low mutual information between the representational dimensions serving structural roles and those serving content roles. Systems that are forced to share representational resources between structure and content will show measurable performance degradation compared to systems that maintain separation.

---

## 3. Claim 2 — Meaning is an intersection address, not a component mixture

### Statement

A concept's meaning is not a weighted combination of other concepts. It is the unique point in dimensional space where multiple independent constraint systems simultaneously agree. The address IS the meaning. Altering any single dimension moves you to a different address, which is a different concept.

### Evidence from decomposition

In GPT-2's embedding space, tokens that belong to multiple semantic categories (e.g., "fish" as both animal and food) sit at positions intermediate between the category centroids. The token's location is not a mixture of the two categories — it is the specific point where the animal dimensions and the food dimensions both have nonzero activation. Disambiguation requires context to shift the effective address toward one category centroid or the other.

Morphological features dominate the principal axes of the embedding space. The model represents "running" not as "run + present-participle" but as a point in the space where the run-dimensions and the -ing-dimensions intersect. The intersection is the representation.

### Evidence from construction

In the graph-based engine, a concept's dim profile — the set of all its typed edge targets — defines its identity. Two concepts with identical dim profiles are the same concept, regardless of their names. Remove one edge and the profile changes; the concept now sits at a different address and participates in different circles. The system does not decompose concepts into percentages of other concepts. It observes where each concept sits and the address tells the system what it is.

### Testable prediction

In any embedding space, the accuracy of a concept's representation should be measurable as the precision of its address — the degree to which its position uniquely identifies it relative to all other concepts. Representations that encode meaning as weighted mixtures of component categories will show systematic ambiguity at mixture boundaries that address-based representations do not. This should manifest as higher classification error rates for concepts near mixture boundaries compared to concepts near intersection addresses.

---

## 4. Claim 3 — Useful categorization compresses at 4–7:1

### Statement

When an associative system forms categories from observation, the ratio of input elements to useful categories consistently falls in the range of 4:1 to 7:1. Below this range, categories are too granular to compose. Above it, distinctions that matter for downstream reasoning are lost.

### Evidence from multiple domains

This compression band appears across substrates that share no implementation details:

- Miller's working-memory research: 7±2 chunks as the unit of cognitive processing.
- Principal Component Analysis on high-dimensional real-world data: 5–10 components carry most of the variance across domains.
- GPT-2's own structure: 8 readable semantic-category centroids from 50,257 tokens; the 60/32/8 attention-head split produces 3 functional categories from ~20 possible classification bins; the four-term decomposition yields 4 functional types.
- Natural language phoneme inventories and major syntactic categories cluster at similar small numbers across unrelated languages.
- Well-designed APIs and ontologies converge on approximately 5–7 top-level concepts.

### Evidence from construction

The graph-based engine, processing a 15-document Egypt corpus with ~30 candidate function-word groupings, produced 5 circles at the threshold where they first appear — a 6:1 ratio. A 24-document Wikipedia corpus produced circles whose formation rate stabilized at approximately 25 per document regardless of corpus size, consistent with a fixed compression ratio.

### Testable prediction

For any new domain, a category-formation system tuned for compositional usefulness (categories that support downstream reasoning, not just statistical clustering) will converge on a compression ratio within the 4–7:1 band. Ratios significantly outside this band predict either poor compositionality (too granular) or poor discrimination (too coarse). This should be testable by measuring downstream task performance as a function of imposed compression ratio, with a peak in the 4–7:1 range.

---

## 5. Claim 4 — Structure is learned before content

### Statement

In any system that processes sequential structured information, structural regularities (positional patterns, syntactic scaffolding, distributional frame) are extracted before content regularities (semantic categories, entity types, domain-specific knowledge). This is an ordering constraint, not a design preference.

### Evidence from decomposition

GPT-2's Layer 0 attention heads are 97–98% positional. They encode pure structural scaffolding — which positions attend to which other positions — before any content signal is processed. Layer 1 contains the strongest rule encoders (token–position collision). Semantic heads appear primarily in later layers. The processing order is: skeleton → grammar → meaning.

### Evidence from construction

Across every corpus tested — hand-curated claims, Wikipedia articles, technical prose — the graph-based engine's first circles are always structural: function-word categories (prepositions, determiners, auxiliaries, pronouns, conjunctions) formed from positional overlap. Content circles require either richer data, additional input processing, or both. At no point in any test run did content circles form before structural circles.

### Testable prediction

Training any sequence model from scratch on any structured sequential data and probing its internal representations at intervals will show structural features emerging before content features, measurable as earlier convergence of positional/syntactic probes compared to semantic probes. This should hold across languages, modalities (music, code, protein sequences), and architectures. A system that is architecturally forced to learn content before structure will converge more slowly than one that learns structure first.

---

## 6. Claim 5 — The default state of content is suppression

### Statement

In any system that must distinguish signal from noise in a structured representation, the prior state of content-bearing elements is suppressed. Content must earn activation against a background of active inhibition. The prior is silence; evidence breaks the silence.

### Evidence from decomposition

In GPT-2's MLP neuron census, every content category (animal, food, country, color, profession, material) has 2–2.5× more inhibition neurons than drive neurons. The only category where drive exceeds inhibit is "number" — a closed, highly regular class. The MLP's default prediction is always a function word (the most common tokens), not a content word. Content tokens rank in the thousands or tens of thousands. "Chicken" is at rank 12,346.

The GELU nonlinearity acts as a gate: neurons below threshold are zeroed out. Content neurons must clear this threshold against the suppression background. The attention circuit provides the evidence that lifts specific content neurons past the gate.

### Evidence from construction

In the graph-based engine, new claims enter with default evidence weight. Contradicted claims drop to zero or near-zero and must be rehabilitated by new evidence. The system does not assume claims are true; it assumes they are unproven and lets evidence accumulate. Sparse nodes — tokens with few edges — remain structurally silent until taught or until the research layer fills them in.

### Testable prediction

Any trained neural network that processes structured content will show an inhibition-dominant architecture for content categories. This should be measurable as a negative mean pre-activation for content-associated neurons across the network, requiring positive contextual input to reach activation threshold. Systems that initialize with content-active priors rather than content-suppressed priors will show higher hallucination rates and lower precision on content-specific tasks.

---

## 7. Claim 6 — Output is determined by interference of independent waves

### Statement

No single constraint system determines specific output. Intent, grammar, register, position, audience, domain, and other constraint layers each propagate as independent signals across the sequence. Each signal alone underdetermines the output. Their constructive interference — the point where all signals simultaneously align — narrows the possibilities to a specific output. The output is the superposition, not any individual component.

### Evidence from decomposition

The four-term decomposition of GPT-2's attention mechanism shows that the actual attention score at any position is the sum of four independent terms. No single term determines the routing. The prediction at any position is the sum of MLP contribution and attention contribution, further gated by GELU.

Within each layer, 12 attention heads fire simultaneously. For any given transition (e.g., noun→verb), some heads amplify and others suppress. Strong rules show constructive interference (8+ heads agreeing); weak or context-dependent rules show destructive interference (heads split). The interference pattern IS the confidence signal.

Multi-layer chains compound this: Layer N pushes the residual toward one category, Layer N+1 pushes further or redirects. The prediction emerges from sequential composition of partial effects across all 12 layers.

### Evidence from construction

In the graph-based engine, a concept's dim profile is the superposition of all its edge targets. A query against the graph resolves by finding the intersection of multiple dim constraints. The activation string across a full context represents each dim as an independent signal; co-activation of multiple dims at the same position is the constructive interference that identifies specific structural roles.

### Testable prediction

The accuracy of a prediction should correlate with the degree of constructive interference across independent constraint channels, measurable as the proportion of channels that agree on the output at a given position. Positions where interference is destructive (channels disagree) should show higher entropy in the output distribution, higher error rates, and — in language models — higher hallucination rates. This should be measurable by decomposing the output into per-channel contributions and computing their alignment.

---

## 8. Claim 7 — Correctability is more fundamental than correctness

### Statement

A system optimized for correctness is brittle: when wrong, the fix requires modifying the system's machinery. A system optimized for correctability treats contradiction as data, provides the same path for correction as for the original input, and lets evidence resolve disputes over time. Correctability subsumes correctness as a special case (a fully corrected system is correct) while remaining robust under incomplete or contradictory information.

### Evidence from observed systems

Wave-particle duality is the canonical example. Both models contradict each other. Neither is correct. Both are useful in specific contexts. Physics holds both and applies whichever produces better predictions in a given domain. The ability to hold contradictory models simultaneously and select by context is a form of correctability.

Bayesian reasoning is another instance. The prior can be wrong. Evidence updates it. The system does not require the prior to be correct; it requires the update path to be well-defined. Correctability is the Bayesian property generalized beyond probability distributions to arbitrary representational structures.

### Evidence from construction

The graph-based engine stores contradicted claims as contested rather than rejected. A claim taught wrong ("fire is cold") persists at low evidence weight. A subsequent correction ("fire is hot," supported by evidence about combustion temperatures) flows through the same input path as the original claim. The wrong claim is not deleted; it is outweighed. If future evidence supports the wrong claim in a specific context (e.g., "fire is cold relative to plasma"), the contested edge can be rehabilitated.

### Testable prediction

Systems designed for correctability will show faster recovery from adversarial or erroneous training data than systems designed for correctness, measurable as the number of correction steps required to restore performance after deliberate poisoning. Systems designed for correctness will show catastrophic degradation under the same conditions because the correction path is different from the input path (requiring retraining, fine-tuning, or parameter surgery rather than simply providing correct evidence through the same input channel).

---

## 9. Claim 8 — The same structural operation applies at every scale

### Statement

When a system discovers structure at one level (tokens, sentences, paragraphs, documents, or meta-discoveries about its own behavior), the operation that discovers it is identical at every level. Structure is self-similar across scales. This is not an implementation convenience; it is a property of how structured information composes.

### Evidence from decomposition

GPT-2 uses the same attention mechanism at every layer. Layer 0 processes raw embeddings; Layer 11 processes 11× refined representations. The operation is identical. What changes is the input, not the mechanism. The model does not have "word-level attention" and "phrase-level attention" and "document-level attention." It has attention, applied uniformly, and the layers self-organize into structural/grammatical/semantic roles.

### Evidence from construction

The graph-based engine uses one comparison operation (Comparator: SHARED / DIVERGENT / ABSENT on dim-sets). When this operation is applied to tokens, it discovers word-level patterns. Applied to sentence-level snapshots, it discovers sentence-structure patterns. Applied to paragraph-level snapshots, it discovers paragraph-composition patterns. Applied to the system's own proposed-content nodes, it discovers patterns in its own discoveries — 607 meta-structural categories from a 24-document corpus, without any meta-learning machinery, simply by allowing the same operation to run on its own output.

### Evidence from broader domains

Holonic structure — parts that are simultaneously wholes — appears in biological organization (cells → tissues → organs → systems), in linguistic structure (morphemes → words → phrases → clauses → sentences → paragraphs → documents), in software architecture (functions → modules → services → systems), and in physical organization (quarks → nucleons → atoms → molecules → cells → organisms). At each level, the same structural relationships (containment, composition, interaction) apply. The operation that describes the relationship between a cell and a tissue is the same operation that describes the relationship between an organ and a system.

### Testable prediction

Any system that applies a structural discovery operation at one level and deliberately prevents it from operating at other levels will show measurable information loss compared to a system that allows the same operation at all levels. The loss should manifest as inability to discover cross-scale regularities (e.g., "sentence patterns that recur at the paragraph level" are invisible to a system that has separate sentence-level and paragraph-level discovery mechanisms). This is testable by comparing a system with uniform cross-scale operations against a system with level-specific operations on the same corpus.

---

## 10. Claim 9 — Lossy aggregation at storage time destroys downstream signal

### Statement

When observations are aggregated (averaged, scored, compressed, thresholded) at the time of storage, information that downstream queries need is permanently lost. Storage and query are different operations with different requirements. Storage should preserve what was observed; queries should aggregate for their specific purpose. The same stored data can serve multiple queries. Pre-aggregated data can serve only the query it was aggregated for.

### Evidence from decomposition

GPT-2's embedding space is a permanent lossy aggregation. A token's embedding is the average of all contexts it appeared in during training. "Bank" (financial) and "bank" (river) share a single embedding that is the average of both usages. Disambiguation requires runtime context to shift the effective representation — but the information about which specific usage was intended in each training instance is permanently lost. The model must reconstruct from context what it could have stored directly.

The MLP frequency prior is another instance. The MLP collapses the full distribution of token occurrences into a single frequency ranking. Token 12,346 is "chicken." The MLP knows chicken is rare relative to "the." It does not know whether chicken appeared more often as food or as animal, in formal or informal text, in early or late positions. The aggregation destroyed the distributional detail.

### Evidence from construction

The graph-based engine's development history includes four instances in a single session where the AI proposed aggregation at storage time (max of channel scores, mean of informative channels, broad-agreement filtering, structural co-activation thresholds). Each was corrected by the operator: "just store the data; queries find what they need." The resulting architecture stores per-position concept heatmaps (every dim that fires at every position, with its weight) and derives all similarity measures, function-similarity proposals, and recurrence observations from queries over that stored data.

### Testable prediction

Given two systems with identical input and identical query capability, the system that stores raw observations and aggregates at query time will answer a strictly larger set of queries correctly than the system that aggregates at storage time. This is trivially true in theory (no information is lost) but the practical question is whether the additional queries that raw storage enables are useful. We predict they are, because downstream tasks that the system designer did not anticipate at storage time are the norm, not the exception. This is testable by designing a storage scheme, defining a set of queries it was optimized for, then introducing novel queries and measuring which storage strategy degrades less.

---

## 11. Relationship between the claims

The nine claims are not independent. They form a dependency structure:

**Claim 1** (independent constraint layers) is foundational. If information self-separates into independent layers, then meaning must be defined by the intersection of those layers (**Claim 2**), not by any single layer.

**Claim 6** (interference determines output) follows from Claims 1 and 2: if there are multiple independent layers and meaning is their intersection, then output is determined by the constructive interference of those layers.

**Claim 4** (structure before content) is a consequence of Claim 1 applied to learning order: structural constraints are more regular and higher-frequency than content constraints, so any learning system extracts them first.

**Claim 5** (default suppression of content) follows from Claim 4: if structure is learned first, the structural scaffold is the prior, and content must earn activation against that prior.

**Claim 3** (4–7:1 compression) follows from Claim 6: the compression band is the resolution limit of compositional interference. Too few categories and the interference pattern can't distinguish between outputs. Too many and the interference becomes noise.

**Claim 8** (same operation at every scale) is the self-similarity claim. If the operation that discovers structure is general (not domain-specific), then it applies at whatever scale structure exists.

**Claim 7** (correctability over correctness) is the epistemological claim. It governs how the system handles the case where its observations are wrong or incomplete, which is always.

**Claim 9** (don't aggregate at storage time) is the information-preservation claim. It governs how observations are stored so that all other claims can operate on undegraded data.

The dependency suggests an ordering: start with Claim 1 (layers exist), then Claim 4 (structure first), then Claim 5 (content suppressed), then Claim 2 (meaning is intersection), then Claim 6 (interference determines output), then Claim 3 (compression band), then Claims 7, 8, and 9 as operational consequences.

---

## 12. What this is not

This is not a proposal for an AI architecture. Architectures implement subsets of these constraints with varying fidelity. These claims describe what any architecture will encounter when processing structured information, regardless of substrate.

This is not a theory of consciousness, understanding, or intelligence. Whether a system that satisfies all nine constraints "understands" anything is a philosophical question that this paper does not address. The claims are about representational structure, not about subjective experience.

This is not a claim that current AI systems are wrong. GPT-2's architecture implicitly satisfies several of these constraints (Claims 1, 4, 5, 6). It violates others (Claims 7, 9) as a consequence of its substrate, not as a design error. The constraints describe the territory; architectures are maps of varying accuracy.

This is not a finished theory. Nine claims derived from two systems on a narrow range of data (English language, Wikipedia-scale corpora, one 124M-parameter model) do not constitute a general theory of information. They constitute a set of empirical observations with testable predictions. The predictions may fail. That would be informative.

---

## 13. How to test these claims

Each claim includes a specific testable prediction. For convenience, here are the experimental designs that would provide the strongest evidence for or against:

1. **Claim 1 (independent layers):** Train a sequence model with a shared representational bottleneck that forces syntax and semantics onto the same neurons. Measure performance degradation relative to a model with independent capacity. If Claim 1 is right, the shared model degrades.

2. **Claim 2 (intersection address):** Compare a mixture-model representation (concept = weighted sum of category prototypes) against an intersection representation (concept = point where category dimensions co-activate) on a disambiguation task. If Claim 2 is right, the intersection model resolves ambiguity with less context.

3. **Claim 3 (compression band):** Sweep the compression ratio from 2:1 to 20:1 on a category-formation task and measure downstream reasoning performance. If Claim 3 is right, peak performance falls in the 4–7:1 range across domains.

4. **Claim 4 (structure before content):** Probe a model's internal representations at training checkpoints. If Claim 4 is right, structural probes converge before content probes, regardless of architecture, language, or modality.

5. **Claim 5 (default suppression):** Measure the mean pre-activation of content-associated neurons in any trained network. If Claim 5 is right, it is negative, requiring positive contextual evidence to reach threshold.

6. **Claim 6 (interference):** Decompose a model's output into per-channel contributions and measure alignment. If Claim 6 is right, positions with high channel agreement show lower error than positions with low agreement.

7. **Claim 7 (correctability):** Poison a fraction of training data, then provide corrections through the same input channel. Compare recovery time against a system that requires retraining. If Claim 7 is right, the correctable system recovers faster.

8. **Claim 8 (same operation at every scale):** Compare a system with uniform cross-scale discovery against one with level-specific mechanisms on cross-scale pattern detection. If Claim 8 is right, the uniform system finds patterns the level-specific system misses.

9. **Claim 9 (don't aggregate early):** Store observations in raw and pre-aggregated forms. Introduce novel queries not anticipated at design time. If Claim 9 is right, raw storage answers more of them.

---

## 14. Conclusion

Nine observations. Two independent systems. One convergent structure.

The claims describe how information organizes when it must support structured, sequential, correctable reasoning. They are not normative — they do not say how systems should be built. They are descriptive — they say what systems will encounter when they represent structured knowledge, regardless of how they are built.

The strongest evidence for these claims is the convergence itself. A gradient-trained neural network with 124 million continuous parameters and a deterministic graph engine with a few thousand discrete nodes arrived at the same organizational structure: independent constraint layers, structure before content, default suppression, interference-based output, self-similar operations across scales. The substrates could not be more different. The structure is the same.

If these claims are right, they constrain the design space of any future reasoning system. Not as rules to follow, but as terrain to navigate. A system that violates them will pay a measurable cost. A system that satisfies them will discover the same structural regularities we report here, because the regularities are in the information, not in the system.

---

*Draft prepared April 2026. Based on decompositional analysis of GPT-2 (124M) and constructive experimentation with a graph-based reasoning substrate across 19 development sessions. All GPT-2 findings are reproducible from publicly available model weights. The graph-based engine's results are documented in session records available from the authors.*
