# ISAAC Codebase Audit — June 20, 2026

## The Numbers

7,034 lines across 11 Python files. The compile step is reimplemented 7 times. The lookup/check inference is reimplemented 6 times. 3 files are superseded. The core engine file has a broken compile path. The manual documents capabilities that aren't implemented.

---

## File-by-File Audit

### isaac_clean.py — 1,218 lines — CORE BUT BROKEN

The intended single source of truth. Contains: Net class, compare() primitive, Isaac class with observe/crystallize/walk/compile/predict.

**What works:**
- Net class (data structure) — correct, complete
- compare() — correct
- observe(), observe_negative(), observe_tagged() — correct
- crystallize() (7-phase FCA closure) — correct
- predict_next() (walker voting) — works for language, never worked for math (by design)
- walk_chain(), generate() — correct for text generation
- check_connection() (manifest validation) — correct
- compare_nodes(), infer() — correct
- matrix_predict() — correct IF compile produces good data

**What's broken:**
- `compile()` calls `_extract_sequences()` which walks the graph to reconstruct sequences. Shared nodes create crossover paths. 48 observations → 34,882 chimeric sequences. The matrix built from this is useless. Every built-in matrix test fails.
- `_extract_sequences()` — the root cause. Should be deleted entirely.

**What's missing:**
- No Engine class (lookup/check with specific-cell reading)
- No logic evaluation
- No reasoning chains
- No problem solving
- No decompose-when-shrug
- No persistence assessment
- Built-in tests call predict_next() for math/logic (wrong inference path)

**Verdict:** Keep Net, compare, observe, crystallize, generation. Fix compile to use observed_sequences. Add Engine capabilities. Remove _extract_sequences and walker-based math/logic tests.

---

### isaac_core.py — 1,437 lines — DEAD, DELETE

The parser version. Contains a full expression interpreter (Evaluator class) with operator precedence, prefix notation, if/then/else, function definitions, loops. Correctly identified as a Rule 1 violation — a conventional interpreter wearing ISAAC's coat.

Also contains a Reasoner class with useful inference logic (query, inheritance, transitivity, deduction, syllogisms, analogy). These capabilities were reimplemented in logic_reasoning.py using the matrix path instead of the walker path.

**Verdict:** Delete. Everything valuable was rebuilt correctly elsewhere.

---

### feed_math.py — 324 lines — WORKS, MERGE

Feeds 100×100 multiplication and addition tables. Compiles to matrix (from observed_sequences — correct). Tests recall: 16/16 perfect. Tests shrug boundary. Tests structure discovery (commutativity, identity, zero property).

**Duplicated:** compile step, lookup function.

**Unique value:** Math table generation, structure discovery tests, shrug boundary verification.

**Verdict:** Merge data generation into curriculum/test suite. Compile and lookup go into unified engine.

---

### test_matrix_think.py — 356 lines — WORKS, MERGE

Multi-step matrix processing. Demonstrates chained matmuls with y vector as scratch space. Tests: scratch variable passing between steps, multi-step computation (e.g., (3+5) then (result×2)).

**Duplicated:** compile step, lookup function.

**Unique value:** Multi-step chaining pattern, y-vector-as-scratch demonstration.

**Verdict:** Merge chaining logic into unified engine. Keep as test case.

---

### decompose_shrug.py — 398 lines — WORKS, MERGE

The growth loop. Try → shrug → decompose into known pieces → chain lookups → verify → memorize. 6/6 correct on multi-digit multiplication (137×48, 999×999, etc.).

**Duplicated:** compile step, matrix_lookup function.

**Unique value:** digits_of() (tokenization-level decomposition), decompose_multiply(), decompose_add(), compute() (the full loop), growth cycle demonstration (decompose → memorize → direct recall next time).

**Verdict:** Merge decomposition capabilities into unified engine. This is a core mechanism, not a test.

---

### logic_reasoning.py — 795 lines — WORKS, MERGE (HIGHEST PRIORITY)

The most complete inference engine. Has the Engine class with:
- lookup() — argmax retrieval
- check() — specific cell validation (the critical check-not-argmax discovery)
- logic_eval() — compound logic decomposition into single-gate lookups
- reason_chain() — chained matmul hops for taxonomy/containment
- is_a_check(), can_check() — with negative override before inheritance
- containment_check(), property_check()
- syllogism()

All tests pass: 12/12 logic gates, 6/6 compound logic, 7/7 is-a chains, 9/9 capability inheritance, 4/4 containment.

**Duplicated:** compile step, the entire build_system() function.

**Unique value:** The Engine class IS the inference layer. check() vs lookup() is the session's key discovery. The negative-first capability check order. Everything here belongs in the core.

**Verdict:** Engine class moves into isaac_clean.py as the primary inference mechanism. compile() fixed. Data generation becomes test infrastructure.

---

### problem_solving.py — 429 lines — WORKS, MERGE

Forward/backward/gap-fill problem solving. Solver class wraps the Engine.

**Duplicated:** compile step, entire build setup.

**Unique value:** Solver class with solve() (parses ? tokens, routes to forward/backward/gap-fill), _solve_single(), _solve_multi() (finds all solutions for ? + ? = 10), solve_steps() (multi-step chains with $0/$1 scratch references), solve_word_problem().

**Verdict:** Merge Solver into unified engine. This extends Engine naturally.

---

### world_state.py — 599 lines — WORKS, MERGE

World state management. World class with entities, states, actions, preconditions, effects. Plans by recursive precondition decomposition.

**Duplicated:** compile step (for the persistence check portion).

**Unique value:** World class is self-contained state manager. Action teaching, execution with precondition checking, recursive planning. The dollhouse demonstration (Nick builds a birdhouse).

**Known issue:** plan() mutates real state instead of simulating in scratch (y vector). Identified in handoff, not fixed.

**Verdict:** Merge. Fix planning to simulate in scratch.

---

### persistence_consequences.py — 487 lines — WORKS BUT INCOMPLETE, MERGE

Persistence learned from consequences. Feeds before/after scenarios, learns which actions destroy structure.

**Duplicated:** compile step, lookup/check functions.

**Unique value:** Scenario-based learning, assess(), plan_think_execute() (the universal output loop).

**Known issue:** Novel-token generalization doesn't work. "Me smash computer" returns UNKNOWN because no frames contain "computer." The verb-level fallback ("smash result" → net_negative) described in the manual is not implemented. The frames always include the object: ("smash", "watch", "result") exists but ("smash", "result") does not, because no observation has "smash" directly adjacent to "result."

**Verdict:** Merge. Implement the verb-level fallback. This is where the generalization mechanism needs to be wired.

---

### persistence.py — 457 lines — DEAD, DELETE

First version. Hardcoded Python functions measuring complexity and applying thresholds. Rule 1 violation — knowledge in code, not in the net.

**Verdict:** Delete.

---

### persistence_learned.py — 534 lines — DEAD, DELETE

Second version. Label-based training ("watch is complex"). Better than persistence.py but superseded by persistence_consequences.py which learns from observation alone.

**Verdict:** Delete.

---

## Duplication Map

| Capability | Files that implement it |
|---|---|
| Net class | isaac_clean, isaac_core |
| compare() | isaac_clean, isaac_core |
| observe() | isaac_clean, isaac_core |
| crystallize() | isaac_clean, isaac_core |
| compile (from observed_sequences) | feed_math, test_matrix_think, decompose_shrug, logic_reasoning, problem_solving, world_state, persistence_consequences |
| compile (from graph walking) | isaac_clean (BROKEN) |
| lookup/argmax | decompose_shrug, logic_reasoning, persistence_consequences, persistence_learned, test_matrix_think, feed_math |
| check/specific-cell | logic_reasoning, persistence_consequences |
| matrix_predict | isaac_clean |

The compile step alone accounts for ~200 lines of duplicated code across 7 files. Each copy is slightly different (different max_ngram, different frame construction, different normalization).

---

## What the Manual Documents but Code Doesn't Implement

1. **Verb-level generalization.** Manual Part 3 says "smash result → net_negative (learned from smash watch)" and claims 10/10 novel predictions. The code returns UNKNOWN for all novel combinations because no partial verb-only frames exist in the matrix.

2. **Morphology grouping.** "Smash" and "smashed" should be recognized as the same type. The crystallizer can do this if they appear in enough shared contexts. Not wired.

3. **Planning in scratch.** The y vector should be the simulation space. plan() currently mutates real state.

4. **Self-directed exploration.** Scanning the matrix for gaps (low confidence regions), trying novel combinations, crystallizing results. The mechanism exists (shrug → decompose → learn). The initiative loop doesn't.

5. **The creation loop.** Generate → observe own output → crystallize → correct → try again.

---

## Dead Code to Remove

| File | Lines | Reason |
|---|---|---|
| isaac_core.py | 1,437 | Parser violation (Rule 1). Superseded by isaac_clean.py |
| persistence.py | 457 | Hardcoded rules. Superseded by persistence_consequences.py |
| persistence_learned.py | 534 | Label-based learning. Superseded by persistence_consequences.py |
| _extract_sequences() | ~25 | Broken graph walking in isaac_clean.py |
| Built-in walker math/logic tests | ~80 | Call predict_next() instead of matrix check() |

**Total dead code: 2,533 lines (36% of the codebase).**

---

## The Unified Version

One file. One Isaac class. One compile. One inference engine. Everything else is data and tests.

**Core (always present):**
- Net — the data structure
- compare() — the primitive
- observe(), observe_negative(), observe_tagged() — data in
- crystallize() — type/rule/lockout discovery
- compile() — observed_sequences → weight matrix (FIXED)
- lookup() — argmax retrieval
- check() — specific cell validation
- walk/generate — text generation from doors
- check_connection — manifest validation

**Inference (extends core):**
- logic_eval() — compound logic decomposition
- reason_chain() — chained matmul hops
- is_a_check(), can_check(), containment_check(), property_check()
- syllogism()

**Computation (extends core):**
- decompose_multiply(), decompose_add()
- compute() — try → shrug → decompose → verify → memorize
- solve() — forward/backward/gap-fill with ? tokens
- solve_steps() — multi-step chains

**World (extends core):**
- World class — state, actions, preconditions, effects
- plan() — recursive decomposition (fix: simulate in scratch)
- plan_think_execute() — the universal output loop

**Assessment (extends core):**
- assess() — consequence-based evaluation
- persistence check via learned patterns

**Estimated size:** ~1,200-1,500 lines for the unified engine. ~500-800 lines for tests and data generation. Down from 7,034 total.

---

## The Three Real Faults to Fix

1. **compile() uses graph walking instead of observed_sequences.** Straightforward code fix. Every standalone file already does it right.

2. **Novel-token generalization is described but not implemented.** Needs the verb-level fallback: when full frames miss, try progressively shorter frames that drop the novel token. ("me smash computer result" → miss → "smash computer result" → miss → try without the unknown token → "smash result" → if that existed, hit.) This requires either generating verb-only observations during training, or building partial-match fallback into the lookup.

3. **Morphology gap.** "Smash" ≠ "smashed." Either feed enough varied forms so the crystallizer groups them, or add explicit morphological observations during training ("smash form smashed", "smash form smashing").

---

*Differentiation makes the parts. Memory recursion composes the wholes. Garbage collection removes what doesn't serve either.*
