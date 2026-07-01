# GPT-2 Structural Analysis: Complete Findings

This document contains every finding from the structural analysis of GPT-2 (124M parameters, 12 layers, 768 embedding dimensions, 50,257 token vocabulary). All findings were extracted from static weight matrices without running the model. This document is written as readable claims for text ingestion.

---

## 1. Model Architecture

GPT-2 has 124 million parameters. It has 12 transformer layers. Each layer has 12 attention heads, for a total of 144 attention heads. Each attention head operates in 64 dimensions. The embedding dimension is 768. Each layer has an MLP with 3,072 neurons, for a total of 36,864 MLP neurons across all layers.

The model has two embedding matrices. The token embedding matrix has 50,257 rows and 768 columns. Each row represents one token in the vocabulary. The positional embedding matrix has 1,024 rows and 768 columns. Each row represents one position in the sequence, from position 0 to position 1,023.

At every position in the input, the model adds the token embedding and the positional embedding together. The sum is the actual input to the first layer. This means the same word has a different representation at different positions in the sequence.

---

## 2. The Dual Subsystem: MLP vs Attention

### MLP encodes frequency

The MLP layers encode what is common. When the MLP weight matrices from all 12 layers are composed into a single linear map and applied to each token embedding, the highest-ranked outputs are function words.

The MLP's top-ranked tokens are: comma at rank 1, "the" at rank 2, period at rank 3, "of" at rank 4, "and" at rank 5, "to" at rank 6, "in" at rank 7, and "a" at rank 8.

Content words rank low in the MLP output. "Chicken" is at MLP rank 12,346. "Paris" is at MLP rank 8,921. The MLP's default prediction is always a function word.

### Attention encodes content

The attention OV (output-value) circuits encode the opposite. When the attention weight matrices are composed and token rankings computed, content words dominate.

"The" is at attention rank 50,255. "Chicken" is at attention rank 6. "Paris" is at attention rank 12. Comma is at attention rank 49,000 or higher.

The MLP and attention rankings are nearly perfectly inverted. What MLP ranks highest, attention ranks lowest, and vice versa.

### The selection mechanism

The prediction at any position is the sum of MLP and attention contributions. The MLP says "predict a comma." The attention says "predict Paris." The GELU nonlinearity in the MLP acts as a gate: neurons with activation below a threshold are zeroed out, neurons above the threshold pass through. The attention circuit, by modifying the residual stream, influences which MLP neurons clear the GELU threshold.

The result is an elimination cascade. The MLP starts with a frequency prior. Attention provides contextual evidence. GELU eliminates MLP neurons that disagree with the attention signal. What survives is the intersection of frequency support and contextual appropriateness.

---

## 3. The Winning Ticket: Readable Neurons

### Only 2% are readable

Of 36,864 total MLP neurons, only 729 produce output vectors that clearly align with semantic categories. This is 1.98% of all neurons. These 729 neurons are the "winning ticket" — the neurons whose structure is human-readable.

### Layer distribution

The 729 readable neurons are not evenly distributed. They concentrate in the final layers.

Layer 0 has 11 readable neurons. Layer 1 has 5. Layer 2 has 11. Layer 3 has 4. Layer 4 has 2. Layer 5 has 1. Layer 6 has 3. Layer 7 has 25. Layer 8 has 44. Layer 9 has 84. Layer 10 has 116. Layer 11 has 423.

Layer 11 alone contains 58% of all readable neurons. The readable structure is gradient-shaped, concentrating in the later layers where the model must project into vocabulary space.

### Drive and inhibit counts

Each readable neuron either drives a category (positive projection toward the category centroid) or inhibits a category (negative projection away from it).

The number category has 141 drive neurons and 86 inhibit neurons. The drive-to-inhibit ratio is 1.64. Number is the only category where drive exceeds inhibit.

The body_part category has 59 drive neurons and 59 inhibit neurons. The ratio is 1.00.

The color category has 58 drive neurons and 61 inhibit neurons. The ratio is 0.95.

The material category has 59 drive neurons and 100 inhibit neurons. The ratio is 0.59.

The country category has 85 drive neurons and 181 inhibit neurons. The ratio is 0.47.

The food category has 87 drive neurons and 199 inhibit neurons. The ratio is 0.44.

The animal category has 82 drive neurons and 192 inhibit neurons. The ratio is 0.43.

The profession category has 90 drive neurons and 222 inhibit neurons. The ratio is 0.41. Profession is the most suppressed category.

Every content category except number has more inhibition neurons than drive neurons. The default state for content categories is suppressed. A category must overcome its background suppression to produce output.

### Drive-inhibit pairs: opposition between categories

Some neurons simultaneously drive one category while inhibiting another. The most common pairs are:

21 neurons drive number while inhibiting profession. 20 neurons drive number while inhibiting food. 18 neurons drive number while inhibiting animal. 17 neurons drive number while inhibiting country. 10 neurons drive food while inhibiting number. 9 neurons drive profession while inhibiting number. 8 neurons drive animal while inhibiting number. 6 neurons drive country while inhibiting number. 4 neurons drive material while inhibiting number.

Number is the strongest opposer. It has the most neurons that simultaneously suppress other categories. The opposition is asymmetric: number suppresses profession with 21 neurons, but profession only suppresses number with 9 neurons.

### Syntax and semantics never share a neuron

Among the 729 readable neurons, no single neuron drives both a syntactic feature and a semantic feature simultaneously. The model maintains completely separate circuitry for structural processing and content processing.

---

## 4. Category Structure in Embeddings

### Eight semantic categories

The analysis used 67 probe tokens across 8 semantic categories: animal, body_part, color, country, food, material, number, and profession. Each category forms a distinct cluster in the 768-dimensional embedding space.

### PREVENTS rules between categories

The crystallization process identified 67 PREVENTS rules. These are pairs of categories or word meanings that the model treats as mutually exclusive.

At the category level: number PREVENTS animal with weight 9.9. Number PREVENTS country with weight 9.7. Number PREVENTS profession with weight 9.6. Number PREVENTS food with weight 9.4. Number PREVENTS material with weight 4.9. Number PREVENTS color with weight 1.4. Number PREVENTS body_part with weight 1.0. Food PREVENTS number with weight 2.9. Profession PREVENTS number with weight 2.7. Animal PREVENTS number with weight 2.6. Country PREVENTS number with weight 2.5. Material PREVENTS number with weight 1.0.

Number has the strongest PREVENTS relationships. When the model is computing a number, it actively suppresses all other content categories.

Weaker cross-category PREVENTS: country PREVENTS animal at 0.3. Country PREVENTS profession at 0.4. Animal PREVENTS country at 0.4. Food PREVENTS profession at 0.3. Color PREVENTS number at 0.4. Color PREVENTS country at 0.4. Color PREVENTS animal at 0.3. Color PREVENTS profession at 0.5. Body_part PREVENTS country at 0.7. Body_part PREVENTS food at 0.3. Profession PREVENTS country at 0.3.

### Disambiguation: words with multiple meanings

22 words were identified as having multiple meanings that require disambiguation. Each meaning has a separate structural representation, and the meanings PREVENT each other.

"Fish" has two meanings: animal (similarity 0.660) and food (similarity 0.612). The gap between meanings is 0.048. Fish_animal PREVENTS fish_food. Fish_food PREVENTS fish_animal. The dominant meaning is animal.

"Chicken" has two meanings: food (similarity 0.756) and animal (similarity 0.585). The dominant meaning is food. Chicken_food PREVENTS chicken_animal.

"Bear" has two meanings: animal (similarity 0.595) and action (similarity near 0). The dominant meaning is animal. Bear_animal PREVENTS bear_action.

"Crane" has two meanings: animal (similarity 0.594) and machine (similarity near 0). The dominant meaning is animal. Crane_animal PREVENTS crane_machine.

"China" has two meanings: country (similarity 0.748) and material (similarity 0.365). The dominant meaning is country. The gap is 0.383, which is large. China_country PREVENTS China_material.

"Turkey" has two meanings: country (similarity 0.728) and animal (similarity 0.427). The dominant meaning is country. Turkey_country PREVENTS Turkey_animal.

"Blue" has two meanings: color (similarity 0.839) and emotion (similarity near 0). The dominant meaning is color. Blue_color PREVENTS blue_emotion.

"Green" has two meanings: color (similarity 0.793) and concept (similarity near 0). The dominant meaning is color. Green_color PREVENTS green_concept.

"Orange" has two meanings: color (similarity 0.787) and food (similarity 0.486). The dominant meaning is color. Orange_color PREVENTS orange_food.

"Apple" has two meanings: food (similarity 0.637) and company (similarity near 0). The dominant meaning is food. Apple_food PREVENTS apple_company.

"Salmon" has two meanings: food (similarity 0.687) and animal (similarity 0.587). The dominant meaning is food. Salmon_food PREVENTS salmon_animal.

"Gold" has two meanings: material (similarity 0.702) and color (similarity 0.496). The dominant meaning is material. Gold_material PREVENTS gold_color.

"Silver" has two meanings: material (similarity 0.722) and color (similarity 0.557). The dominant meaning is material. Silver_material PREVENTS silver_color.

"Iron" has two meanings: material (similarity 0.709) and action (similarity near 0). The dominant meaning is material. Iron_material PREVENTS iron_action.

"Stone" has two meanings: material (similarity 0.705) and name (similarity near 0). The dominant meaning is material. Stone_material PREVENTS stone_name.

"Head" has two meanings: body_part (similarity 0.632) and position (similarity near 0). The dominant meaning is body_part. Head_body_part PREVENTS head_position.

"Hand" has two meanings: body_part (similarity 0.725) and action (similarity near 0). The dominant meaning is body_part. Hand_body_part PREVENTS hand_action.

"Foot" has two meanings: body_part (similarity 0.717) and measurement (similarity near 0). The dominant meaning is body_part. Foot_body_part PREVENTS foot_measurement.

"Heart" has two meanings: body_part (similarity 0.647) and emotion (similarity near 0). The dominant meaning is body_part. Heart_body_part PREVENTS heart_emotion.

"Palm" has two meanings: body_part (similarity 0.638) and plant (similarity near 0). The dominant meaning is body_part. Palm_body_part PREVENTS palm_plant.

"Bat" has two meanings: animal (similarity 0.552) and object (similarity near 0). The dominant meaning is animal. Bat_animal PREVENTS bat_object.

"Violet" has two meanings: color (similarity 0.692) and name (similarity near 0). The dominant meaning is color. Violet_color PREVENTS violet_name.

---

## 5. SVD Decomposition: Natural Feature Axes

The embedding matrix decomposed via SVD reveals 50 structurally meaningful axes. 558 axes are needed for 90% of total variance.

### Top 30 axes

Axis 0 accounts for 1.81% of variance. Its positive direction contains function words: "and," "the," comma, hyphen, "in." Its negative direction contains rare tokens. This axis encodes commonness versus rarity.

Axis 1 accounts for 0.82% of variance. Its positive direction contains Greco-Latin roots: "dystop," "Neander," "narciss," "chimpan," "Freud." Its negative direction contains suffixes: "-ional," "-ance," "-ered." This axis separates classical word roots from common English suffixes.

Axis 2 accounts for 0.72% of variance. Its positive direction contains informal short tokens: "zzy," "ko," "ka," "Rabbit." Its negative direction contains formal institutional words: "interventions," "assessments," "prescribing," "implementations." This axis separates informal from formal register.

Axis 3 accounts for 0.69% of variance. Its positive direction contains institutional terms: "Catholic," "Government," "Economic," "Islamic." Its negative direction contains small physical events: "bounces," "blink," "fade." This axis separates institutional from physical-event language.

Axis 4 accounts for 0.65% of variance. Its positive direction contains negative evaluations: "intolerable," "wretched," "unpleasant," "indifferent." Its negative direction contains commercial/product terms: "iPads," "Libraries," "Packs," "Cards." This axis separates subjective judgment from categorical labels.

Axis 5 accounts for 0.61% of variance. Its positive direction contains concrete plural nouns: "houses," "stones," "wives," "birds," "boys." Its negative direction contains technical codes. This axis encodes concrete countable plurals.

Axis 6 accounts for 0.56% of variance. Its positive direction contains technical infrastructure terms: "phosphate," "valves," "kilometers," "reservoirs." Its negative direction contains abstract values: "Fear," "Shame," "Truth," "Love," "Evil." This axis separates concrete-technical from abstract-emotional.

Axis 7 accounts for 0.55% of variance. Its positive direction contains compound verb-direction nouns: "lockout," "foreclosure," "blackout," "bailout," "driveway." This is a morphological class with the suffix "-out" pattern. This axis encodes system-failure or shutdown concepts.

Axis 8 accounts for 0.52% of variance. Its positive direction contains past-tense legal/punitive actions: "withheld," "fined," "refused," "revoked," "bailed." Its negative direction contains process/transformation words: "evolution," "transformation," "visualization." This axis separates punitive past events from ongoing processes.

Axis 9 accounts for 0.49% of variance. Its positive direction contains terrain and fortification: "Armored," "Underground," "mountainous," "destroyed," "ravaged." Its negative direction contains communication/response: "interviewer," "listener," "commenting." This axis separates physical landscape from discourse.

Axis 10 accounts for 0.49% of variance. Its positive direction contains authority enforcement: "Sever," "Warden," "Vigil," "Vest," "Removal." This axis encodes enforcement and authority actions.

Axis 11 accounts for 0.48% of variance. Its positive direction contains antagonist and outlaw terms: "mafia," "pirate," "ninja," "traitor," "assassinate." This axis encodes antagonist roles.

Axis 12 accounts for 0.47% of variance. Its positive direction contains ceremony and celebration: "banquet," "adorned," "celebrated," "crowned," "commemorate." Its negative direction contains toxicity and harm: "toxicity," "toxic," "toxins," "lethal," "viruses." This axis separates celebration from harm.

Axis 13 accounts for 0.46% of variance. Its positive direction contains specific numbers: 373, 666, 383, 343, 344. Its negative direction contains business terms: "buy," "econom," "business." This axis separates numeric identifiers from commercial language.

Axis 14 accounts for 0.44% of variance. Its positive direction contains military deployment: "fielded," "deployed," "aligned," "spearheaded," "tasked." Its negative direction contains suffering and personal crisis: "sickness," "miscarriage," "abstinence," "divorce." This axis separates organized action from personal suffering.

Axis 15 accounts for 0.43% of variance. Its positive direction contains surveillance and control: "photographed," "abducted," "scanned," "interrogated," "filmed." Its negative direction contains abstract quality: "greatness," "profitability," "affordability." This axis separates surveillance actions from abstract qualities.

Axis 16 accounts for 0.43% of variance. Its positive direction contains geopolitical terms: "Moscow," "Syria," "London," "Brexit," "France." This axis encodes geopolitical entities and events.

Axis 17 accounts for 0.42% of variance. Its positive direction contains Germanic name roots: "burg," "Smith," "smith," "cart." Its negative direction contains Asian/tropical place names: "Ramadan," "Thailand," "Okinawa." This axis separates Germanic from Asian/tropical cultural references.

Axis 18 accounts for 0.41% of variance. Its positive direction contains growth and care terms: "rejuven," "nurture," "wellness," "cultivating," "enhancing." Its negative direction contains ambiguity and opacity: "arbitrary," "unmarked," "opaque," "notations." This axis separates nurturing from obscurity.

Axis 19 accounts for 0.40% of variance. Its positive direction contains nocturnal and mysterious: "nighttime," "sightings," "haunted." Its negative direction contains measurement and principles: "Ruler," "blade," "coefficient." This axis separates mystery from precision.

### Feature anti-occurrence

164 pairs of features never co-occur in the same neuron. The strongest anti-occurrence pattern: Feature 0 (function words: "and," "the," comma) never co-occurs with Features 6 through 19 (all content features). This means the function-word axis is structurally isolated from every content axis. The model keeps function word processing completely separate from content processing.

Feature 1 (Greco-Latin roots) never co-occurs with Feature 2 (informal short tokens), Feature 6 (technical infrastructure), Feature 7 (system failure), Feature 8 (punitive actions), Feature 9 (terrain), Feature 10 (authority enforcement), Feature 11 (antagonist), or Feature 12 (ceremony). Classical roots are isolated from all specific content domains.

### Feature co-occurrence

Feature 4 (negative evaluation: "intolerable," "wretched") co-occurs with Feature 5 (concrete plurals: "houses," "stones") in 5 neurons. This is the only significant co-occurrence found, suggesting that negative evaluation and concrete nouns share some neural circuitry.

---

## 6. The Positional Embedding: The Encoding Mask

### Four-term attention decomposition

The attention score between position i and position j decomposes into four terms.

Term 1 is token-to-token. It measures how much the token at position i attends to the token at position j, regardless of position. This is the semantic signal.

Term 2 is position-to-position. It measures how much position i attends to position j, regardless of what tokens fill those positions. This is the structural signal.

Term 3 is token-to-position. It measures how much the token at position i attends to position j itself. This is a collision term where the token seeks a specific position.

Term 4 is position-to-token. It measures how much position i attends to the token at position j. This is a collision term where the position expects a specific token type.

Terms 3 and 4 together are the collision signal. They encode grammatical rules because they depend on BOTH what the token is AND where it sits.

### Head classification

Of 144 total attention heads, 87 are primarily structural, meaning position-to-position dominates their computation. This is 60.4% of all heads.

46 heads are rule encoders, meaning the collision terms (token times position) dominate. This is 31.9% of all heads.

11 heads are primarily semantic, meaning token-to-token dominates. This is 7.6% of all heads.

The model is overwhelmingly structural. Only 8% of attention heads are primarily concerned with token content.

### Layer structure

Layer 0 heads are 97 to 98% positional. They establish a structural scaffold before any content processing. Layer 1 contains the strongest rule encoder heads. Head L1H9 is 95% collision. Head L1H8 is 92% collision. Head L1H10 is 86% collision.

The processing order is: Layer 0 builds the positional skeleton, Layer 1 installs grammatical rules through the token-position collision, and later layers fill in semantic content.

### Extracted grammar rules

After isolating the collision terms from the 46 rule-encoder heads, subtracting the positional baseline, and thresholding at one standard deviation, 120 raw dimensions reduce to 45 discrete grammatical rules.

The strongest rules: verb avoids preposition at offset plus one with score negative 52.6. Determiner expects verb at plus one with score positive 44.5. Adjective avoids preposition at plus one with score negative 43.5. Determiner expects pronoun at plus one with score positive 38.5. Noun expects verb at plus one with score positive 33.1. Noun avoids preposition at plus one with score negative 28.8. Verb avoids determiner at plus one with score negative 26.8. Determiner expects noun at plus one with score positive 25.2. Pronoun expects verb at plus one with score positive 23.6. Preposition expects verb at plus one with score positive 22.9.

---

## 7. Generation Tests

The model was tested on 8 prompts to verify the crystallized structure against actual output.

Given "The fish swam through the," the model generated "water, and the fish sw" with confidence 0.134. It selected the animal context correctly.

Given "I ordered the fish with," the model generated "the same ingredients as the other" with confidence 0.173. It selected the food context but generated a generic continuation.

Given "The crane lifted the heavy," the model generated "duty crane and the crane" with confidence 0.144. It selected the machine context correctly.

Given "The crane flew over the," the model generated "building and the crane was able" with confidence 0.107. It mixed animal (flew) and machine (building) contexts. Low confidence reflects the ambiguity.

Given "Gold is a precious," the model generated "metal that is used in many" with confidence 0.281. It selected the material context correctly with relatively high confidence.

Given "The gold colored paint," the model generated "is a bit of a mess" with confidence 0.199. It selected the color context and generated an evaluative continuation.

Given "The capital of France is," the model generated "the capital of the French Republic" with confidence 0.317. It recognized the country context with high confidence but generated a tautological answer.

Given "The chicken crossed the," the model generated "line" with confidence 0.353. The highest confidence of all tests. The model recognized a set phrase pattern.

---

## 8. Summary of Key Numbers

The model has 124 million parameters. It has 144 attention heads across 12 layers. It has 36,864 MLP neurons. Its vocabulary is 50,257 tokens.

729 neurons (1.98%) are structurally readable. 423 of those are in Layer 11 (58%).

87 attention heads (60.4%) are structural. 46 (31.9%) are rule encoders. 11 (7.6%) are semantic.

Number is the only category with a positive drive-to-inhibit ratio (1.64). Profession has the lowest ratio (0.41) and is the most suppressed category.

22 words have multiple meanings with PREVENTS relationships between definitions. The smallest gap between competing meanings is 0.048 (fish: animal 0.660 vs food 0.612). The largest gap is 0.383 (China: country 0.748 vs material 0.365).

67 PREVENTS rules were identified. 45 discrete grammatical rules were extracted from the positional collision analysis. 164 feature anti-occurrence pairs were found. The strongest grammatical signal is verb-avoids-preposition at negative 52.6.
