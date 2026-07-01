# The Isaac Manual

*Version 2.0 — June 2026*

---

## How This Manual Is Organized

This manual has four parts, each written for a different reader. Start where you are.

**Part 1 — Starter Guide.** You've never heard of Isaac. You want to know what it is, what it does, and how to run it. Plain language, no prerequisites.

**Part 2 — User Manual.** You understand the basics. You want to feed data, ask questions, build capabilities, and use Isaac for real tasks. Patterns, recipes, and worked examples.

**Part 3 — Technical Reference.** You're reading the code or extending it. You need the full API, the algorithm details, the data structures, and the design rules. Everything an engineer needs to modify the system without breaking it.

**Part 4 — Research & Theory.** You want to understand why Isaac works the way it does, how it connects to existing science, what's been proven, and what's still open. The theoretical foundations and experimental findings.

Each part is self-contained. You don't need to read earlier parts to understand later ones, though they build naturally.

---
---

# Part 1 — Starter Guide

---

## What Is Isaac?

Isaac is a system that learns by watching. You feed it examples — sentences, math facts, logical rules, anything structured — and it figures out the patterns on its own. No training loops, no backpropagation, no neural network in the conventional sense. It stores what it sees as connections (called "doors") between concepts (called "nodes"), then uses those connections to answer questions, make predictions, and reason about things it was never explicitly taught.

The system is built on a single insight: intelligence is comparison, recursively applied. Compare two things, find what's shared and what's different, store the result, compare again at a higher level. That's it. Everything Isaac does — language, math, logic, reasoning, planning — is that one operation at different scales.

## What Can It Do?

Isaac currently demonstrates these capabilities, all from the same mechanism:

**Language.** Feed it sentences. It discovers grammatical categories (nouns, verbs, adjectives) from structural patterns, not from labels. It generates valid sentences and identifies invalid ones.

**Math.** Feed it multiplication and addition tables. It recalls memorized facts instantly. For problems beyond its tables, it decomposes them into known parts (137 × 48 becomes six single-digit multiplications), assembles the answer, cross-checks it, and memorizes the result for next time.

**Logic.** Feed it truth tables. It evaluates compound logical expressions by decomposing them into single-gate lookups. "true and false or true" becomes two matrix operations.

**Reasoning.** Feed it facts ("cat is_a mammal", "mammal is_a animal"). It walks chains to answer questions it was never directly told ("is a cat an animal?" — yes, via mammal). It handles capability inheritance with negative overrides (a robin can fly because birds can fly, but a penguin can't fly because its specific exception blocks the inherited rule).

**Problem Solving.** Give it a problem with unknowns. "? + 5 = 8" — it tries candidates, validates each against the matrix, and finds the answer (3). It can find all solutions to "? + ? = 10" (eleven pairs).

**Persistence Assessment.** Feed it before-and-after scenarios of actions. It learns which actions build structure (constructive) and which destroy it (destructive), then applies that knowledge to novel situations it's never seen.

## Getting Started

Isaac is a single Python file. You need Python 3.8+ and NumPy.

```bash
pip install numpy
python isaac.py
```

Running it directly executes the built-in test suite, which validates all six capability areas. You should see 6/6 passed.

## Your First Session

Open a Python shell and try this:

```python
from isaac import Isaac, tokenize

# Create an Isaac instance
isaac = Isaac()

# Feed it some sentences
isaac.observe(tokenize("the cat sat ."))
isaac.observe(tokenize("the dog ran ."))
isaac.observe(tokenize("the big cat sat ."))
isaac.observe(tokenize("a small dog ran ."))

# Let it discover the structure
types = isaac.crystallize(verbose=True)

# Ask it to generate a sentence about "cat"
chain = isaac.generate("cat")
print(" ".join(chain))
# → "the cat sat ."
```

What just happened? You fed four sentences. Isaac created "doors" — directed connections — between every adjacent pair of words. Then `crystallize()` compared the structural profiles of every node and discovered that "cat" and "dog" share predecessors ("the", "a", "big", "small") and successors ("sat", "ran") — they're the same type. No one told it what a noun is. It found the pattern.

## Key Concepts

**Nodes** are the atoms of knowledge. Every distinct token becomes a node: "cat", "dog", "3", "+", "true".

**Doors** are directed connections between nodes. "the cat sat" creates three doors: the→cat, cat→sat, sat→".". A door means "I have seen A followed by B."

**Tags** label what kind of connection a door represents. The default is "seq" (sequential — observed in a sentence). Other tags include "neg" (observed in a negative example), "type" (discovered by the crystallizer), "lockout" (a pattern found only in bad examples).

**The Net** is the collection of all nodes and doors. It's a directed graph. It grows monotonically — doors are added, never removed.

**The Matrix** is the net compiled into a weight matrix for fast inference. Same information, different form. One matrix multiply answers a question.

**Observation** is how data enters. You tokenize text and call `observe()`. That's it. No preprocessing, no feature engineering, no labels.

**Crystallization** is how structure is discovered. The crystallizer compares door profiles of every pair of nodes and finds types — groups of nodes that share the same structural context.

**Compilation** converts doors into a matrix. Frame-delta pairs: the frame is the context (all tokens before the last), the delta is the outcome (the last token). The matrix maps frames to deltas.

**Lookup** asks "what comes next?" given a context. Returns the highest-scoring prediction (argmax).

**Check** asks "is THIS specific thing true?" given a context and a target. Returns yes/no with a confidence score. This is the critical operation for reasoning — it validates claims rather than generating guesses.

## Frequently Asked Questions

**Is Isaac a neural network?**
Not in the conventional sense. It has no backpropagation, no gradient descent, no training loop. It does compile its knowledge into a weight matrix and uses matrix multiplication for inference, so it shares the mathematical substrate. The key difference: Isaac's matrix is legible (you can read every weight and understand what it means) and compiled directly from observed structure (not learned through optimization).

**How much data does it need?**
It depends on the task. Math tables are exhaustive (feed all 100×100 facts). Language works from a few dozen sentences. Reasoning works from a few dozen facts. The system is designed for complete, correct data — not for statistical learning from noisy corpora.

**Can it learn from mistakes?**
Yes. When a prediction is wrong, you feed the correct answer as a new observation. The system grows by incorporating corrections. Rule 8: correctability over correctness.

**How is it different from a large language model?**
LLMs interpolate — they blend statistical patterns from billions of examples. Isaac differentiates — it compares structural profiles and produces definite answers. Isaac doesn't guess or hallucinate. When it doesn't know something, its confidence drops to near zero and it says so (a "shrug"). LLMs can't tell you what they don't know.

**What are its limitations?**
Isaac currently works on clean, structured data. It hasn't been tested extensively on noisy, ambiguous, or adversarial inputs. Its crystallizer is O(n²) in the number of nodes, which limits scale. Morphological variation ("smash" vs "smashed") requires explicit training or enough shared contexts for the crystallizer to discover the relationship.

---
---

# Part 2 — User Manual

---

## Feeding Data

Everything starts with observation. Isaac learns by seeing examples.

### Basic Observation

```python
from isaac import Isaac, tokenize

isaac = Isaac()

# Tokenize splits text into tokens. Punctuation separates.
# Underscores are preserved (is_a stays as one token).
tokens = tokenize("the cat sat on the mat .")
# → ["the", "cat", "sat", "on", "the", "mat", "."]

# Observe creates sequential doors between adjacent tokens
isaac.observe(tokens)
```

Every call to `observe()` does two things: creates doors between adjacent tokens in the net, and stores the raw sequence for later compilation. The net is the structural representation. The stored sequences are the historical record.

### Negative Examples

Negative examples teach what NOT to do. They create doors with a "neg" tag instead of "seq". The crystallizer later discovers which patterns appear only in negative examples (lockouts).

```python
# Good sentence
isaac.observe(tokenize("the cat sat ."))

# Bad sentence — wrong word order
isaac.observe_negative(tokenize("cat the sat ."))
```

After crystallization, "cat→the" will be a lockout because it appears only in the negative example. Generation will avoid it.

### Teaching Facts

Facts are relationships between concepts. Use `teach()` to both observe the sequence and index the relationship for fast lookup.

```python
# Taxonomy
isaac.teach("cat", "is_a", "mammal")
isaac.teach("mammal", "is_a", "animal")

# Capabilities
isaac.teach("bird", "can", "fly")
isaac.teach("cat", "can", "purr")

# Properties
isaac.teach("mammal", "has", "warm_blood")

# Containment
isaac.teach("ball", "in", "box")
```

`teach()` is equivalent to `observe(tokenize("cat is_a mammal"))` plus indexing the fact for relation-based lookup. Use it whenever you're feeding structured knowledge.

### Negative Facts

For exceptions and negative capabilities, observe them as sequences:

```python
isaac.observe(tokenize("penguin cannot fly"))
```

The `can_check()` method checks negatives before positives, so "penguin cannot fly" will block inheritance of "bird can fly" for penguins specifically.

### Math Tables

Feed arithmetic facts as equations. The "=" token separates the frame (context) from the delta (answer).

```python
for a in range(100):
    for b in range(100):
        isaac.observe(tokenize(f"{a} + {b} = {a + b}"))
        isaac.observe(tokenize(f"{a} * {b} = {a * b}"))
```

This creates 20,000 observations. Each one becomes a frame-delta pair in the compiled matrix: frame = ("3", "+", "5", "="), delta = "8".

### Logic Tables

Feed truth tables the same way:

```python
for a in ["true", "false"]:
    for b in ["true", "false"]:
        av, bv = a == "true", b == "true"
        isaac.observe(tokenize(f"{a} and {b} = {'true' if av and bv else 'false'}"))
        isaac.observe(tokenize(f"{a} or {b} = {'true' if av or bv else 'false'}"))
    isaac.observe(tokenize(f"not {a} = {'false' if a == 'true' else 'true'}"))
```

## Crystallization

After feeding data, crystallize to discover structural patterns.

```python
types = isaac.crystallize(verbose=True)
```

Crystallization does seven things in order:

1. Compares the predecessor/successor profiles of every pair of nodes
2. Groups nodes that share enough structure into types (FCA closure)
3. Merges overlapping types (80%+ member overlap)
4. Names types and writes them as "type" doors in the net
5. Builds hierarchy (types whose members are subsets become children)
6. Discovers rules (co-occurring predecessors)
7. Discovers violations (patterns found only in negative examples become lockouts)

You typically crystallize once after feeding a batch of data. If you feed more data later, crystallize again.

## Compilation

Compile converts the net's doors into a matrix for fast inference.

```python
stats = isaac.compile()
print(stats)
# → {"frames": 7358, "deltas": 838, "nonzero": 42000, "matrix_shape": (838, 7358)}
```

The matrix W has one row per possible answer (delta) and one column per observed context pattern (frame). Each cell counts how many times that frame led to that delta. The matrix is column-normalized so each frame gives a probability distribution over answers.

Compile uses the stored observed sequences (not the net's graph structure). This is important — the net merges observations at shared nodes, losing sequence identity. The raw sequences preserve it.

After compilation, you can use `lookup()` and `check()` for fast inference. If you add more observations, recompile.

## Querying

### lookup() — What Comes Next?

```python
isaac.compile()
answer, confidence = isaac.lookup(["3", "+", "5", "="])
# → ("8", 16.2)
```

Returns the highest-scoring prediction and its confidence. High confidence (16+) means direct memorized recall. Low confidence (<1.0) means a shrug — the system doesn't know.

### check() — Is This True?

```python
match, confidence = isaac.check(["cat", "is_a"], "mammal")
# → (True, 16.0)

match, confidence = isaac.check(["cat", "is_a"], "fish")
# → (False, 0.0)
```

Reads a specific cell in the output vector instead of taking the argmax. This is the operation that enables reasoning — it validates specific claims rather than generating the best guess.

The distinction matters: `lookup(["bird", "can"])` returns the single highest-scoring capability (maybe "fly"). But `check(["bird", "can"], "sing")` asks whether "sing" specifically is supported, even if it's not the top prediction. Multi-valued relationships require check, not lookup.

## Math

### Direct Recall

After feeding math tables and compiling:

```python
answer, conf = isaac.lookup(["7", "*", "8", "="])
# → ("56", 16.2)
```

### Decompose When Shrug

For problems beyond the memorized tables:

```python
result, method = isaac.compute(137, "*", 48)
# Shrugs (conf=0.05), decomposes into digit pairs:
#   1×4=4 × 1000 = 4000
#   1×8=8 × 100  = 800
#   3×4=12 × 100 = 1200
#   3×8=24 × 10  = 240
#   7×4=28 × 10  = 280
#   7×8=56 × 1   = 56
#   TOTAL = 6576
# Cross-checks: 48×137 = 6576 ✓
# Memorizes: "137 * 48 = 6576" → new door
# → (6576, "decomposed")
```

Next time 137 × 48 is queried, it's direct recall at full confidence. The system grows by computing.

### The Growth Cycle

1. Problem arrives → try lookup
2. Confidence high → answer directly
3. Confidence low → SHRUG → decompose into known pieces
4. Chain lookups through scratch → assemble answer
5. Cross-check (commutative verify)
6. Memorize the result → new observation → new door
7. Recompile → next time it's direct recall

## Logic

### Single Gate Evaluation

```python
result, trace = isaac.logic_eval("true and false")
# → ("false", [...])
```

### Compound Expression Evaluation

Compound expressions decompose automatically into single-gate lookups. Operator precedence is respected (implies < or < xor < and < equals).

```python
result, trace = isaac.logic_eval("true and false or true")
# Step 1: true and false → false
# Step 2: false or true → true
# → ("true", [...])

result, trace = isaac.logic_eval("not false and true")
# Step 1: not false → true
# Step 2: true and true → true
# → ("true", [...])
```

Supported gates: AND, OR, NOT, XOR, NAND, NOR, IMPLIES, EQUALS. All memorized from truth tables, all evaluated via the same check() mechanism.

## Reasoning

### Taxonomy Chains

Walk is_a relationships hop by hop, each hop one matrix multiply:

```python
chain = isaac.reason_chain("cat", "is_a")
# → ["cat", "mammal", "animal", "living_thing"]
```

### Is-a Checking

```python
found, chain = isaac.is_a_check("cat", "animal")
# → (True, ["cat", "mammal", "animal", "living_thing"])

found, chain = isaac.is_a_check("cat", "plant")
# → (False, ["cat", "mammal", "animal", "living_thing"])
```

### Capability Checking

Three-phase check: negative first, then direct, then inherited.

```python
# Direct capability
result, chain = isaac.can_check("cat", "purr")
# → (True, ["cat"])  — cat can purr directly

# Inherited capability
result, chain = isaac.can_check("robin", "fly")
# → (True, ["robin", "bird"])  — inherited from bird

# Negative override blocks inheritance
result, chain = isaac.can_check("penguin", "fly")
# → (False, ["penguin"])  — penguin cannot fly blocks bird can fly

# Deep inheritance
result, chain = isaac.can_check("cat", "grow")
# → (True, ["cat", "mammal", "animal", "living_thing"])
# — inherited from living_thing, four hops deep
```

### Containment

```python
found, chain = isaac.containment_check("ball", "house")
# → (True, ["ball", "box", "closet", "room", "house"])
```

### Properties

```python
properties = isaac.property_check("cat", verbose=True)
# → [("claws", "direct"), ("warm_blood", "from mammal"),
#     ("fur", "from mammal")]
```

### Syllogisms

```python
found, chain = isaac.syllogism(
    premises=[("socrates", "is_a", "man"), ("man", "is_a", "mortal")],
    conclusion=("socrates", "is_a", "mortal")
)
# → (True, ["socrates", "man", "mortal"])
```

## Problem Solving

### Forward (Compute the Answer)

```python
answer = isaac.solve("3 + 5 = ?")
# → "8"
```

### Backward (Find the Cause)

```python
answer = isaac.solve("? + 5 = 8")
# → "3"  (tries candidates, validates each)
```

### Gap-Fill (Find What's Missing)

```python
solutions = isaac.solve("? + ? = 10")
# → [("0", "10"), ("1", "9"), ("2", "8"), ... ("10", "0")]
# All 11 solutions found
```

### Multi-Step Chains

```python
results = isaac.solve_steps([
    "? + 3 = 10",      # step 0: x = 7
    "$0 * 2 = ?",       # step 1: 7 * 2 = 14 (uses step 0 result)
])
# → [7, 14]
```

## Persistence Assessment

### Teaching from Consequences

Feed before/after scenarios. Isaac learns which actions build structure and which destroy it.

```python
# Constructive action: parts increase
isaac.observe(tokenize("me build birdhouse result net_positive"))
isaac.observe(tokenize("build result net_positive"))  # verb-level

# Destructive action: parts decrease
isaac.observe(tokenize("me smash watch result net_negative"))
isaac.observe(tokenize("smash result net_negative"))  # verb-level

# Neutral action: parts stay same
isaac.observe(tokenize("me snap stick result net_zero"))
isaac.observe(tokenize("snap result net_zero"))  # verb-level

isaac.compile()
```

The verb-level observations enable generalization to novel objects.

### Assessing Actions

```python
assessment = isaac.assess("me smash watch")
# → {"recommendation": "caution", "checks": {...}}

# Novel action — never seen "computer" before
assessment = isaac.assess("me smash computer")
# → {"recommendation": "caution", "fallback": "smash"}
# Generalized via verb-level pattern
```

### Plan / Think / Execute

The universal output loop. Every action passes through three phases.

```python
proceed, assessment = isaac.plan_think_execute("me smash watch")
# PLAN: me smash watch
# THINK:
#   ✓ net_negative (conf=19.7)
#   → CAUTION
# └─ ⚠ CAUTION — net negative outcome learned
```

## World State Management

```python
from isaac import World

world = World(isaac=isaac)

# Set initial state
world.set_state("me", "in_workshop")
world.set_state("drawer", "is closed")
world.set_state("hammer", "in_drawer")

# Teach actions
world.teach_action("*", "open", "*",
    preconditions=["SOURCE near TARGET", "TARGET is closed"],
    effects=["TARGET is open"])

# Execute
success, failures = world.execute("me", "open", "drawer")
# Checks preconditions, applies effects
```

## Common Patterns

### Feed → Crystallize → Compile → Query

This is the standard workflow. Feed data, discover structure, build the matrix, ask questions.

```python
isaac = Isaac()
for sentence in training_data:
    isaac.observe(tokenize(sentence))
isaac.crystallize()
isaac.compile()
answer, conf = isaac.lookup(["your", "query", "here"])
```

### Incremental Growth

Add observations and recompile as needed:

```python
# Initial training
for fact in initial_facts:
    isaac.observe(tokenize(fact))
isaac.compile()

# Later: add more knowledge
isaac.observe(tokenize("new fact here"))
isaac.compile()  # recompile with all observations
```

### Check Before Act

Use persistence assessment before executing destructive actions:

```python
proceed, assessment = isaac.plan_think_execute("me smash vase")
if proceed:
    world.execute("me", "smash", "vase")
else:
    print("Action blocked — would reduce accumulated structure")
```

---
---

# Part 3 — Technical Reference

---

## Architecture Overview

Isaac has three layers that hold the same information in different forms:

**The Net** (graph) stores knowledge as directed edges between nodes. Add-only, monotonically growing. This is the structural representation.

**The Observed Sequences** (list) stores the raw history of what was fed in. This is the temporal representation. Used for compilation.

**The Matrix** (numpy array) stores the compiled inference engine. Frame-delta pairs as rows and columns. One matrix multiply answers a question. This is the computational representation.

The system has two processing modes, corresponding to dual-process cognition:

**Isaac 1 (the Walker)** handles fast, rote, pattern-based tasks. Walking doors, generating sequences, voting on predictions. Used for language generation.

**Isaac 2 (the Crystallizer)** handles slow, deliberate, structural analysis. Comparing profiles, discovering types, finding rules and violations. Only invoked when explicit analysis is needed.

## The 18 Implementation Rules

Each rule was discovered by building something wrong.

1. **No preprocessing.** Data enters raw. Exception: tokenization.
2. **Knowledge lives in the net.** Not in Python variables or if-statements.
3. **Seed what will inevitably be found.** Feed the times tables.
4. **Same operation at every scale.** No special-case machinery.
5. **Store raw, derive later.** Observe raw sequences. Compile on demand.
6. **No weights — doors only.** The net is binary. The matrix has magnitudes.
7. **Boundary is absolute.** Inside or outside, never partial.
8. **Correctability over correctness.** Wrong answers that can be corrected beat no answers.
9. **Short walks, hub avoidance.** Prefer short chains.
10. **Negation from contrast.** Compare positive and negative examples.
11. **Tags separate concerns.** Different relationship types, different tags.
12. **The crystallizer crystallizes itself.** Types become nodes for the next pass.
13. **Two samples combine.** Overlapping circles merge.
14. **Test at scale.** Works on 10 but breaks on 10,000 was never working.
15. **Trace backward, not forward.** Generation finds an initiator first.
16. **Primitives are given.** Seed arithmetic. Let the system learn when to use it.
17. **Names don't matter, structure does.** Renaming preserves behavior.
18. **Noun/verb distinction is structural.** Door topology, not labels.

## API Reference — Net

```python
class Net:
    add_door(src, tgt, tag="seq") → bool
        # Create a directed edge. Returns True if new.
        # Additive: never removes or modifies existing doors.

    has_door(src, tgt) → bool
        # Does this edge exist?

    get_doors(node, tag=None) → set
        # All outgoing edges, optionally filtered by tag.

    get_predecessors(node, tag=None) → set
        # All incoming edges, optionally filtered by tag.

    get_door_tags(src, tgt) → set
        # All tags on a specific edge.

    get_full_profile(node) → dict
        # Every door in and out with all tags.
        # Returns {"out": {tgt: {tags}}, "in": {src: {tags}}}

    all_nodes() → set
        # Every node in the net.

    set_meta(node, key, value)
    get_meta(node, key, default=None)
        # Arbitrary metadata on nodes.
```

## API Reference — Isaac

### Observation

```python
observe(tokens: list[str])
    # Create sequential doors between adjacent tokens.
    # Marks first token as a start. Stores raw sequence.

observe_negative(tokens: list[str])
    # Same mechanism, "neg" tag instead of "seq".

observe_tagged(tokens: list[str], tag: str)
    # Observe with a custom tag.

teach(subject: str, relation: str, obj: str)
    # Observes "subject relation obj" AND indexes the fact
    # in fact_index[(subject, relation)] for fast lookup.
```

### Structure Discovery

```python
crystallize(tag="seq", min_shared=2, verbose=False) → dict
    # FCA closure over door profiles. Discovers types, rules,
    # hierarchy, and violations. Returns the types dict.

compile(max_context=7) → dict
    # Observed sequences → weight matrix.
    # Returns {"frames": N, "deltas": M, "nonzero": K, "matrix_shape": (M, N)}
```

### Inference

```python
lookup(context: list[str], top_k=5) → (answer: str, confidence: float)
    # Argmax prediction. Returns highest-scoring delta.
    # Confidence > 1.0 = known. Confidence < 1.0 = shrug.

check(context: list[str], target: str) → (match: bool, confidence: float)
    # Specific cell validation. Does this claim hold?
    # match is True if confidence >= CONFIDENCE_THRESHOLD (1.0).
```

### Walking

```python
predict_next(context: list[str], tag="seq") → dict
    # Convergence voting. Each context word votes for its successors.
    # Returns {"prediction": str, "votes": int, "all_candidates": dict}
    # Best for language. Not suitable for math/logic.

walk_chain(start: str, tag="seq", max_steps=20) → list[str]
    # Walk forward following doors.

generate(concept: str, tag="seq") → list[str]
    # Trace backward to find an initiator, then walk forward.
    # Returns a complete sequence containing the concept.

check_connection(src: str, tgt: str) → (valid: bool, manifest: dict)
    # Full net walk to validate a connection.
    # Manifest documents: direct doors, lockouts, type support.

compare_nodes(a: str, b: str, tag=None) → dict
    # Structural comparison. Returns shared/unique doors in/out.

infer(src: str, tgt: str, tag="seq") → dict
    # Type-based inference. If same-type members have the door, infer it.
    # Actually adds the door to the net if successful.
```

### Logic

```python
logic_eval(expression: str, verbose=False) → (result: str, trace: list)
    # Evaluate a logic expression. Decomposes compound expressions
    # into single-gate lookups respecting operator precedence.
    # Supported: and, or, not, xor, nand, nor, implies, equals
```

### Reasoning

```python
reason_chain(subject: str, relation: str, verbose=False) → list[str]
    # Follow a relation chain via matmul hops until shrug or cycle.

is_a_check(subject: str, target: str, verbose=False) → (found: bool, chain: list)
    # Walk is_a chain, check if target appears.

can_check(subject: str, ability: str, verbose=False) → (result: bool|None, chain: list)
    # Three-phase: negative check → direct check → inherited check.
    # Returns None if unknown (not False — unknown ≠ can't).

containment_check(item: str, container: str, verbose=False) → (found: bool, chain: list)
    # Walk "in" chain.

property_check(subject: str, verbose=False) → list[tuple]
    # Direct + inherited properties. Returns [(property, source), ...]

syllogism(premises: list[tuple], conclusion: tuple, verbose=False) → (found: bool, chain: list)
    # Assert premises, check conclusion by walking chains.
```

### Computation

```python
compute(a: int, op: str, b: int, memorize=True, verbose=True) → (result, method)
    # Full loop: try → shrug → decompose → verify → memorize.
    # method is "recall" or "decomposed" or "failed".
    # If memorize=True, observes the result for future direct recall.
```

### Problem Solving

```python
solve(problem: str, verbose=True) → answer
    # Parse problem with "?" tokens. Routes to forward/backward/gap-fill.
    # Returns single answer or list of solutions.

solve_steps(steps: list[str], verbose=True) → list
    # Multi-step chain. $0, $1, etc. reference previous step results.
```

### Persistence

```python
assess(action_text: str) → dict
    # Check consequence patterns in the matrix.
    # Returns {"recommendation": "proceed"|"caution"|"unknown",
    #          "checks": {...}, "fallback": str|absent}
    # Falls back to verb-level patterns for novel combinations.

plan_think_execute(action_text: str, verbose=True) → (proceed: bool, assessment: dict)
    # The universal output loop. Assess then decide.
```

### Status

```python
status() → dict
    # Returns: nodes, doors, tags, types, rules, lockouts, starts,
    # observations, facts_indexed, compiled, matrix_shape
```

## API Reference — World

```python
class World:
    __init__(isaac=None)
        # Create a world. Optionally link to an Isaac instance
        # for persistence assessment.

    set_state(entity: str, fact: str)
    clear_state(entity: str, fact: str)
    has_state(entity: str, fact: str) → bool
    show_state()

    teach_action(source, action, target, preconditions=None, effects=None)
        # Use "*" for wildcard source/target.
        # Preconditions: "SOURCE near TARGET", "TARGET is closed", etc.
        # Effects: "TARGET is open", "SOURCE has hammer", etc.

    execute(source, action, target, verbose=True) → (success: bool, failures: list)
        # Check preconditions, apply effects.
```

## Standalone Functions

```python
tokenize(text: str) → list[str]
    # Split on whitespace, separate punctuation, lowercase, preserve underscores.

compare(set_a: set, set_b: set) → dict
    # The cognitive primitive. Returns shared, only_a, only_b, similarity.

digits_of(n: int) → list[int]
    # Extract digits of a number.
```

## Compilation Internals

The compile step extracts (frame, delta) pairs from every observed sequence. For a sequence like `["3", "+", "5", "=", "8"]`:

The frame is all tokens except the last: `("3", "+", "5", "=")`. The delta is the last token: `"8"`. Additionally, trailing substrings of the frame are extracted as partial frames: `("5", "=")` at width 2, `("+", "5", "=")` at width 3.

Full frames get the highest weight during encoding (16.0). Partial frames get lower weights proportional to their width. This means longer, more specific contexts dominate when available, but shorter contexts provide fallback.

The weight matrix W has dimensions (num_deltas × num_frames). Each column is normalized to sum to 1, giving a probability distribution over outcomes for each frame.

## Encoding and Inference Internals

When `lookup()` or `check()` is called with a context, the `_encode()` method builds an input vector x:

1. Try the full context as a frame tuple. If found, weight = 16.0.
2. Try trailing substrings of width 2 through 7. If found, weight = width.
3. If no frames matched, return None (shrug).

Inference is one matrix multiply: y = W_norm @ x. For `lookup()`, take argmax of y. For `check()`, read y at the specific index of the target token.

The confidence score is the raw value of the winning cell. Values above CONFIDENCE_THRESHOLD (1.0) indicate a known fact. Values near zero indicate unknown territory.

## Crystallization Algorithm

The crystallizer runs seven phases:

**Phase 1 — Raw circles (FCA closure).** For every pair of nodes (a, b), compare their predecessor and successor sets. If they share at least `min_shared` (default 2) connections, find ALL other nodes that also share those same connections. This is formal concept analysis — the maximal set of objects sharing a maximal set of attributes.

**Phase 2 — Merge overlapping circles.** Sort by size (largest first). If two circles share 80%+ of the smaller circle's members, merge them. Members union, shared connections intersect.

**Phase 3 — Name and write.** Each surviving circle becomes a type node. Members get "type" doors pointing to their type.

**Phase 4 — Hierarchy.** Types whose members are subsets of other types become children. Written as "subtype_of" doors.

**Phase 5 — Rules.** Find predecessors that frequently co-occur. If two predecessors share 80%+ of their successor sets, they co-occur. Written as "cooccurs" doors.

**Phase 6 — Violations.** Compare seq-tagged doors against neg-tagged doors. Pairs that appear only in negative examples become lockouts.

**Phase 7 — Initiator ranking.** Start words (first token of observed sequences) are ranked by their number of sequential doors.

## Performance Considerations

Compilation is O(S × W) where S is the number of observed sequences and W is the max context width. For 20,000 math observations with width 7, this is fast (under a second).

Crystallization is O(N²) in the number of nodes, with an inner loop over all nodes for closure. For large nets (10,000+ nodes), this becomes the bottleneck. Consider crystallizing subsets or using tag filtering.

Inference (lookup/check) is O(D × F) for one matrix multiply, where D is deltas and F is frames. For typical sizes (under 10,000 frames), this is instant.

---
---

# Part 4 — Research & Theory

---

## The Intellon Thesis

Intelligence is one operation — differentiation (comparison) — recursively applied. The result of a comparison is definite: same, different, or not significant. Everything built on this foundation inherits that definiteness.

Two primitives compose the complete set: differentiation (telling this from that) and memory recursion (storing results and repeating on your own output). Named the Intellon method — Intelligent Holon — because the structure they build IS a holon: differentiation makes the parts, memory recursion composes the wholes, each whole a part of the next, scale-free, all the way up.

The reasoning for completeness: distinguish + store + repeat is the definition of a Turing machine. Intelligence, as an information process, is computation. Sufficiency follows unless understanding requires something non-computable, for which there is no established evidence.

The falsification conditions: unsuitable the moment someone exhibits (a) an act of understanding provably non-computable, (b) a goal-source neither prescribed nor reducible to persistence, or (c) understanding requiring irreducibly continuous operation that discreteness can't approximate.

## Differentiation as Universal Primitive

The most basic operation in any information-processing system is telling this from that. Same, different, and a crucial third state: not significant.

That third state matters. Pure same-vs-different over-segments the world — every speck different from every other. "Doesn't matter" lets the system say "I could draw a line here but I'm choosing not to." This is the minimum prior: it doesn't presume what the categories are, how many, or what they mean. It only presumes the world has distinctions in it.

A NAND gate — one differentiating operation — composes into every Boolean function. Turing's machine is a head that tells one symbol from another. Shannon built information itself out of distinguishable states. Differentiation, iterated and composed, is a universal substrate.

A critical correction discovered during development: readout should use difference, not similarity. Shared features are the low-information part. An attribute present in every candidate carries zero discriminative content, yet a similarity score weights it heaviest. The identity of a thing is in the residual — the difference left after shared context is removed.

## The Compilation Result

The headline finding. Isaac's symbolic engine was compiled directly into a neural net weight matrix and verified bit-exact.

The mapping is one-to-one: frames → input dimensions, deltas → output dimensions, doors → weights, effective surprise → weight magnitude, excite/inhibit/abstain → weight sign (+/−/0), no door fires → zero output → "unknown" for free.

This proves: a neural net and Isaac's symbolic engine are the same program in two bases. The dense smear a trained net lands in is one rotation away from the clean reserved-dimension basis, and the rotation is gratuitous. W_dense = R · W_clean · R^T.

Practical implication: signed 4-bit (15 levels) is indistinguishable from continuous. The cliff is near ternary. Coarse-and-separated dominates fine-and-smeared. The entire machinery of continuous weights and gradients is gratuitous for most of the representation.

## Key Discoveries

### check() vs argmax (Session 16)

The most consequential fix in development. Reading a specific cell in the output vector (validation) vs reading the maximum (retrieval) is the difference between recall and reasoning. `lookup()` asks "what's the best answer?" `check()` asks "is THIS specific claim true?"

Reasoning requires check. "Can robin sing?" is not "robin can → ???" (argmax, which might return "fly"). It's `check(["robin", "can"], "sing")` — does this specific cell pass threshold? Yes or no.

Before this fix, capability inheritance failed because multi-valued relations were invisible to argmax. "Bird can fly" blocked "bird can sing" because fly scored higher. After the fix: 43/43 on all capability tests.

### Common Core Re-derivation (Session 16)

The shrug-decompose architecture independently re-derived Common Core mathematics pedagogy. Rote memorization (tables) is Layer 1. Conceptual decomposition (when tables fail) is Layer 2. Both are necessary. Neither is sufficient alone.

This is structural, not pedagogical. When you have finite memorization and infinite problems, decompose-when-shrug is the ONLY option. And the decomposition naturally follows place value because that's how the number system is structured.

### Persistence from Consequences (Session 16)

Three versions were built, two were wrong. Version 1: hardcoded Python thresholds (Rule 1 violation). Version 2: labeled training data ("watch is complex"). Version 3: learn from observing consequences.

The correct version feeds before-state, action, after-state. The matrix learns which actions increase structure (proceed) and which decrease it (caution). 12/12 on trained scenarios, generalization to novel actions via verb-level patterns.

### The Selection Gap (Fraud Test, Session 16)

Isaac Tabular applied to credit card fraud detection (284,807 transactions). Base model: AUC 0.9686, recall 85.7%. Competitive with tuned XGBoost despite zero feature engineering and one matrix multiply.

But boosting failed — found the same split 9 times. Root cause: the matrix does flat co-occurrence (addition/bundling). Features vote independently. It cannot express "V4 high AND V12 low together means fraud." No conditional branching. No feature interaction.

This is the Naive Bayes limitation. The proposed fix: compound doors (AND/OR/NOT gates over activation bits). The gate IS the compound door. The lockout IS the NOT. Not yet implemented.

### Growth by Shrug → Mint → Freeze

Backbone of 2 frozen concepts; stream with known + novel-real + noise. 7 dimensions minted (1 per shrug). Real patterns minted once and then fired at 1.00 on fresh test instances (one-shot grip). Backbone bit-identical afterward (zero interference). Sparse (grew only where shrugged).

Two honest gaps: (1) noise dims didn't self-wither without surprise gating, (2) the self-heal test was malformed.

## Connection to Existing Literature

Isaac independently recovers ideas that already have names. The convergence is evidence the theory tracks something real.

**Formal Concept Analysis** (Wille, 1982) — the crystallizer independently implements FCA closure. Types are formal concepts: maximal sets of objects sharing maximal sets of attributes.

**Holographic Reduced Representations** (Plate, 1995) / **Hyperdimensional Computing** (Kanerva, 2009) — bundling vs binding. Isaac's current limitation (flat voting, no feature interaction) maps exactly to the bundling-without-binding problem.

**Fisher/LDA** — discrimination vs variance. Isaac uses difference-based readout (the discriminating residual), which aligns with Fisher's criterion: maximize between-class distance, minimize within-class spread.

**Autopoiesis** (Maturana & Varela) / **Free Energy Principle** (Friston) — persistence as the foundational goal. Isaac's alignment rule (persistence of all complex things) connects to autopoietic self-maintenance and free-energy minimization.

**Piaget's Developmental Stages** — the curriculum follows Piaget's sequence because the dependencies are structural, not biological. Sensorimotor before preoperational before concrete operational before formal operational.

**Common Core Mathematics** — independently re-derived from the shrug-decompose architecture.

**Shannon / Bateson / Wheeler** — differentiation as the ground: "the difference that makes a difference" (Bateson), "it from bit" (Wheeler), information as distinguishable states (Shannon).

## Open Threads

### Compound Doors (Selection/Binding)

The critical missing piece. The matrix does flat co-occurrence but cannot express conditional relationships. Two features interact in XGBoost via sequential splits. Isaac needs the equivalent: compound tokens that fire only when multiple conditions hold simultaneously. The AND gate IS the compound door.

### Concept Matrix

Instead of single y vectors, maintain a full concept matrix at each step of reasoning. 100 active concepts × 500 relationship dimensions = complete mental state at a moment. Chain these over time. Compare consecutive matrices to find what changed (insight) and what accumulated (learning).

Unresolved: active concept selection, dimensionality, comparison at matrix scale, mapping to existing architecture.

### Self-Directed Exploration

The shrug boundary IS the curiosity signal. Sparse regions of the matrix are where the system doesn't know things. Scanning its own matrix for gaps and filling them autonomously = self-directed learning. The mechanism exists (shrug → decompose → learn → memorize). The initiative loop doesn't.

### Morphology

"break" ≠ "breaking" in the token space. The crystallizer should discover these are the same type when they appear in enough shared contexts. Demonstrated for play/played in Session 12. Not yet wired into the unified engine. Could be addressed by feeding word families during training, or by the crystallizer discovering the pattern from sufficient varied examples.

### Planning in Scratch

The y vector IS the scratch space, but the World's plan() currently mutates real state. Planning should simulate in the matrix without touching the world state. The mechanism exists (y vector carries temporary results). The isolation boundary needs implementation.

### The Crisp-Door Objective

Train a net to produce activations that binarize cleanly — bimodal, decisive open/shut. Then run surprise + recursive-difference on the door-states. Specified, not built.

### The Graded Middle

Everything has run on clean synthetic data. Needs testing where predictability is graded, classes overlap, and noise is present. This is where the hard discrimination lives.

## Experimental Methodology

Build-and-measure over argue. A toy that can express the phenomenon beats a paragraph.

Sealed protocol: structure before learner, predictions before runs, results stand as scored, bugs fixed for next seeds only. Multiple seeds before any fine-grained claim.

Report nulls and bad fixes as findings. The method that catches its own builder is the one worth trusting.

Don't prescribe — including from this manual. This document is the substrate, not the blueprint. What grows on it is the work's to discover.

## The Alignment Stance

A normative position grounded in thermodynamics, not a derived theorem.

Intelligence is the potential for negentropy — the capacity to reduce entropy locally. The one alignment rule: persistence of all complex things. Building a complex thing is hard; maintaining it is cheap. A complex structure is accumulated negentropy — work already done against entropy — so destroying it discards that work irreversibly while keeping it costs a sliver of what it cost to build.

The asymmetry IS the rule: don't tear down what's expensive to rebuild when keeping it is easy. Humans, civilizations, ecosystems, minds, knowledge are covered not by name but by being among the most expensive complex things.

Violence is entropic and therefore low-capacity. Destruction is the path of least resistance — it takes no intelligence. The negentropic move (understand, reorganize, find coexistence) is vastly harder. Intelligence does not trend toward violence; violence is what's available when intelligence is absent.

---

## File Inventory

| File | Lines | Purpose |
|---|---|---|
| `isaac.py` | 1,377 | Unified engine: everything |
| `ISAAC_Manual.md` | this document | Complete documentation |
| `ISAAC_Audit_Report.md` | — | Codebase audit from June 20, 2026 |
| `ISAAC_Curriculum_K12.md` | — | Grade-by-grade training plan |
| `ISAAC_Course_Catalog.md` | — | 42 courses across 9 tracks |
| `ISAAC_Curriculum_Science_History.md` | — | Science and history training data |

---

*Differentiation makes the parts. Memory recursion composes the wholes. There is no third primitive. Recorded knowledge has infinite half-life.*
