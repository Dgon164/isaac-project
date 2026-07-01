# Track 6: Response Generation — Self-Evaluating Assembly

**Date:** April 5, 2026
**Depends on:** xb.8 (457 tests, SQLite storage, hypotheses, provenance)
**Goal:** The system produces coherent English responses from its knowledge, validated by its own comprehend and verify systems.

---

## The Problem

The system can reason but cannot speak. It walks chains, discovers connections, predicts relationships, verifies facts — but every output is a debug readout. "cat —is_a→ animal" is not English. "Yes (via is_a, depth 1)" is not a sentence.

The system has everything it needs to produce English. It has vocabulary (WordNet), grammar rules (textbook), structural knowledge (ConceptNet, loaded facts), and a pipeline that can parse and verify English input (comprehend + verify). It just never points those capabilities at its own output.

---

## The Principle

Generation is the reverse of comprehension. Comprehend takes English and extracts structure. Generation takes structure and produces English. The same grammar rules apply in both directions. The same verification applies to generated statements as to input statements.

The system is its own evaluator. If it can't comprehend what it just said, it didn't say it right. If what it said doesn't match what it knows, it said the wrong thing. Two failure modes, both already handled, both informative.

---

## Architecture: The Assembly Loop

```
Query arrives
  │
  ├── 1. RETRIEVE — gather relevant knowledge
  │     Pull nodes, chains, relationships into working space
  │
  ├── 2. PLAN — decide what to say
  │     What facts answer the query?
  │     What order? What's most relevant?
  │
  ├── 3. ASSEMBLE — build candidate response
  │     Apply grammar rules to arrange knowledge into English
  │     Start simple: subject + relationship + object
  │     Grow: add modifiers, conjunctions, clauses as grammar improves
  │
  ├── 4. SELF-CHECK — comprehend the candidate
  │     Feed candidate through _processInput / comprehend
  │     Does the pipeline parse it?
  │     Does it extract the same structure that was assembled?
  │     If parse fails → grammar error → adjust assembly, try again
  │
  ├── 5. VERIFY — fact-check the candidate
  │     Does the statement match the knowledge graph?
  │     Walk chains to confirm each claim
  │     If verify fails → content error → adjust content, try again
  │
  ├── 6. EMIT — return the validated response
  │     Response has passed both structural and factual checks
  │     Log the generation for observation (training data for improvement)
  │
  └── On failure: log what went wrong, return best attempt with confidence
```

---

## Implementation

### Phase 1: Dumb Assembly (Get it working)

The simplest possible generation. No grammar rules, no intelligence. Just concatenation.

```
Chain: cat —is_a→ animal
Output: "cat is_a animal"

Chain: cat —is_a→ animal, animal —has→ fur  
Output: "cat is_a animal. animal has fur."

Question: "is cat an animal?"
Answer chain found, depth 1
Output: "yes. cat is_a animal."
```

This is barely English. The relationship names aren't proper English ("is_a" not "is a"). Sentences are choppy. But it's a starting point that can be fed through comprehend and verified.

**What this tests:** The loop works. Assembly → self-check → verify → emit. The output is terrible but the pipeline is functional.

### Phase 2: Relationship Templates

Map relationship types to English patterns. These are nodes in the graph, not hardcoded.

```
_template_is_a:     "{subject} is a {object}"
_template_has:      "{subject} has {object}"
_template_not:      "{subject} is not {object}"
_template_part_of:  "{subject} is part of {object}"
_template_causes:   "{subject} causes {object}"
_template_produces: "{subject} produces {object}"
_template_requires: "{subject} requires {object}"
_template_opposite_of: "{subject} is the opposite of {object}"
```

Now the output becomes:

```
Chain: cat —is_a→ animal
Output: "cat is a animal"  → self-check catches "a animal" → 
        "cat is an animal" (if article rules are loaded)
```

Templates are loadable facts. The system learns new templates the same way it learns anything else. When it encounters a new relationship type with no template, it falls back to "{subject} {rel} {object}" and logs the gap.

**What this tests:** Template-based generation, self-correction on article usage, gap detection for missing templates.

### Phase 3: Multi-Fact Composition

Combine multiple facts into compound sentences using grammar rules.

```
Facts: cat is_a animal, cat has whiskers, cat has fur
Candidate: "cat is an animal. cat has whiskers. cat has fur."
Self-check: valid but repetitive
Grammar rule: compound predicate — same subject, multiple predicates join with "and"
Revised: "cat is an animal with whiskers and fur."
Self-check: parses → verify: all three facts confirmed → emit
```

This is where the grammar textbook pays off. The system has rules about conjunctions, compound sentences, subordinate clauses. It applies them to combine simple statements into complex ones.

### Phase 4: Query-Driven Response Shaping

Different query types need different response shapes:

**Yes/No questions:** "is cat an animal?" → verify chain → "Yes, cat is an animal."

**What questions:** "what is cat?" → gather all → "Cat is an animal. It has whiskers and fur."

**How questions:** "how does sun relate to dark?" → walk chain → "Sun produces light, and light is the opposite of dark."

**Open queries:** "tell me about cat" → gather, prioritize by trust and source diversity → compose multi-sentence response.

The response planner selects which facts to include based on:
- Relevance to the query
- Trust level (higher trust = more confident)
- Source diversity (multi-sourced = more authoritative)
- Novelty (things the user probably doesn't know yet)

### Phase 5: Self-Improvement Loop

Every generated response is training data.

```
Generate candidate
  │
  ├── Comprehend it → did it parse?
  │     NO → log failure pattern → "adjective after noun failed"
  │          → update pattern confidence → try alternative arrangement
  │     YES → continue
  │
  ├── Verify it → is it factually correct?
  │     NO → log content error → "assembled wrong chain"
  │          → adjust retrieval/planning
  │     YES → continue
  │
  ├── Compare to input patterns → does it look like natural English?
  │     The system has observed thousands of sentences through comprehend
  │     Does the generated sentence match observed patterns?
  │     Track pattern match rate
  │
  └── Emit response
        Store generation event as observation
        Track which templates/rules produced successful outputs
        Templates that consistently pass → trust increases
        Templates that consistently fail → trust decreases, eventually replaced
```

The same trust lifecycle that governs knowledge governs generation strategies. Templates that produce good English get promoted. Templates that produce garbage get demoted. The system learns to speak better over time, from its own feedback.

---

## Self-Check Implementation

### Grammar Check (Comprehend Pass)

```javascript
assemble(facts) → candidate string
_processInput(candidate) → recognition result

If recognition = 'structured':
  // Pipeline parsed it as a valid fact statement
  // Compare extracted (source, rel, target) to intended (source, rel, target)
  // If they match → grammar is correct
  // If they don't match → grammar distorted the meaning

If recognition = 'sentence':  
  // Pipeline recognized it as a natural sentence
  // _parseSentence extracted SVO
  // Compare extracted SVO to intended content
  // Match → good, mismatch → assembly error

If recognition = 'token':
  // Pipeline couldn't parse it at all
  // Total grammar failure → log and retry
```

### Fact Check (Verify Pass)

```javascript
// For each claim in the candidate response:
extractClaims(candidate) → [{subject, rel, object}, ...]

for each claim:
  result = verify(subject, rel, object)
  if result.found → confirmed
  if !result.found → check if it's a reasonable inference
    gather(subject) → does any chain lead to object?
    if yes → inferential (lower confidence)
    if no → unsupported → remove from response
```

### Coherence Check (Pattern Match)

```javascript
// Does the sentence structure match observed patterns?
tokens = tokenize(candidate)
roles = tokens.map(t => _getDominantRole(t))
pattern = roles.join(':')
knownPattern = _matchPattern(tokens)

if knownPattern → structural confidence high
if !knownPattern → novel structure, lower confidence, but not necessarily wrong
```

---

## Working Space Role

Working space becomes the assembly workspace:

1. Query arrives → pull relevant nodes into working space
2. Plan response → arrange working nodes by relevance and order  
3. Assemble → walk working nodes, apply templates/grammar, produce candidate
4. Self-check → feed candidate through pipeline (reads from node space, not working)
5. If pass → emit and flush working space
6. If fail → adjust working space arrangement, try again

The working space is the "thinking about what to say" stage. The node space is "what I know." Generation lives in the gap between them.

---

## What This Does NOT Do

- Does not produce creative or novel language. It assembles from known patterns and facts.
- Does not handle ambiguity in queries (yet). It takes the most literal interpretation.
- Does not produce paragraph-length text initially. Start with single sentences, grow.
- Does not replace comprehend. Comprehend handles input, generation handles output. Same rules, opposite directions.
- Does not require a language model. Assembly is rule-following, not prediction. Grammar rules are nodes, templates are nodes, vocabulary is nodes.

---

## Open Questions

**Q1: How many retry attempts before giving up?** If assembly keeps failing self-check, when does it stop and say "I know the answer but can't express it"? Recommendation: 3 attempts with different strategies, then fall back to structured display (current behavior) with a note that generation failed.

**Q2: Should generated responses be stored as nodes?** If the system produces "cat is an animal with whiskers and fur" and it passes all checks, should that sentence become a node? It would be available for future reference — "I've said this before and it was valid." Recommendation: yes, as working nodes that promote if reused.

**Q3: Should the system explain its reasoning?** "Cat is an animal (because cat is_a animal, via direct pointer, trust node-proven, sources: wordnet, biology)." Provenance on generated responses. Recommendation: optional flag, like `--source` on gather. Default is clean English, flag adds the evidence chain.

**Q4: How to handle uncertainty?** If a fact is at working-trial trust, should the system say "cat might have fur" vs "cat has fur"? Trust level mapping to confidence language. Recommendation: yes. working-trial = "might", working-standard = probable, working-proven+ = definitive. This falls out naturally from the grammar rules if modality is in the textbook.

---

## Dependencies

| What | Why |
|------|-----|
| English grammar textbook loaded | Assembly rules come from the graph |
| Relationship templates as nodes | Maps rel types to English patterns |
| Comprehend pipeline working | Self-check grammar validation |
| Verify/gather working | Self-check fact validation |
| Working space | Assembly workspace |
| Role/pattern observations | Coherence checking |

---

## Success Criteria

1. System produces a valid English sentence from a knowledge chain
2. Sentence passes comprehend self-check (pipeline can parse its own output)
3. Sentence passes verify self-check (facts match the knowledge graph)
4. Multi-fact responses combine sentences using grammar rules
5. Failure modes are informative (grammar error vs content error vs coherence error)
6. Templates are nodes, learnable and replaceable, not hardcoded
7. Generation quality improves over time via trust lifecycle on templates/patterns
8. System can fall back to structured display when generation fails

---

## Estimated Progression

| Phase | What | Effort |
|-------|------|--------|
| Phase 1: Dumb assembly | Concatenate chain nodes | Low — proof of loop |
| Phase 2: Templates | Relationship → English patterns | Low — loadable facts |
| Phase 3: Composition | Multi-fact compound sentences | Medium — grammar rule application |
| Phase 4: Query shaping | Response varies by question type | Medium — planner logic |
| Phase 5: Self-improvement | Trust lifecycle on generation strategies | Low — uses existing machinery |
