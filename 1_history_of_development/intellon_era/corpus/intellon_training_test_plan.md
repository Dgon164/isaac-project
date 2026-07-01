# Intellon v6 Node Architecture: Training Test Plan

**Date:** April 1, 2026
**Status:** Implementation roadmap for incremental learning validation
**Prerequisite:** Dev tests a.1–a.5 all pass (57/57)

---

## Guiding Principle

The dev tests proved the architecture works. The training tests prove the system can learn. Each test delivers observations incrementally, measures what the system does with them, and verifies that knowledge accumulates correctly across sessions.

The system is not told what to look for. It receives observations, decides what to do, and builds knowledge using only the node architecture validated in dev.

---

## System Under Test: LearningSession

The dev phase used `runDiscovery()` — a batch processor. The training phase replaces it with an incremental learner:

```
class LearningSession {
    receive(observation)  — process one observation against existing knowledge
    explore(tool)         — self-directed probing of a specific tool
    ruminate()            — end-of-session maintenance
    play(budget)          — exploratory phase with fixed op budget
    status()              — what is known, what is unresolved, what is queued
}
```

Each method operates on the live node network from dev. No separate data structures.

---

## Training Test 1: Boot Sequence (Sessions 0–1)

### What we're proving
That the system correctly bootstraps from nothing through ASCII to logic, producing structural connectives before any domain knowledge arrives.

### Protocol
- Session 0: System receives 128 ASCII base nodes. Verify all exist.
- Session 1: System receives boolean observations (the complete truth tables from dev test 2). System must probe logic tools, discover AND/OR/NOT/XOR, flag them structural.
- After Session 1: ruminate. Verify no flags remain.

### Test cases
- T1.1: After Session 0, system has 128 base nodes and nothing else.
- T1.2: After Session 1, AND/OR/NOT/XOR are discovered and flagged structural.
- T1.3: Attempting to build a structured definition BEFORE Session 1 completes fails gracefully (no structural connectives available yet).
- T1.4: After rumination, all logic nodes are clean (no stale refs).

### Pass criteria
Logic is usable as infrastructure before any domain observations arrive.

---

## Training Test 2: Incremental Arithmetic Discovery

### What we're proving
That the system discovers arithmetic tools one observation at a time, building knowledge progressively rather than in batch.

### Protocol
- Session 2: Deliver ADD observations one at a time: (2,3)→5, then (7,8)→15, then (0,4)→4, etc.
- After each observation, the system either: recognizes it (existing procedure matches), or explores (probes tools to find a match), or queues it (can't explain yet).
- After enough observations, the system should have discovered ADD and built a live node.
- Session 3: Deliver SUB observations the same way.

### Test cases
- T2.1: First ADD observation triggers exploration (nothing exists yet).
- T2.2: After 3–4 ADD observations, the system has confirmed ADD as a procedure.
- T2.3: The ADD node has correct takes/gives slots built with structural connectives from Session 1.
- T2.4: A 5th ADD observation is recognized immediately (no exploration needed).
- T2.5: Record the observation count at which ADD is confirmed. This is the learning speed metric.

### Pass criteria
ADD discovered incrementally. Node is live and queryable. Subsequent matching observations are recognized without re-exploration.

---

## Training Test 3: Transfer Learning

### What we're proving
That discovering MUL after ADD is faster because the system already knows the pattern of binary numeric tools.

### Protocol
- After Session 2 (ADD confirmed), deliver MUL observations in Session 4.
- Measure observations-to-confirmation for MUL.
- Compare against ADD's observations-to-confirmation from Test 2.

### Test cases
- T3.1: MUL confirmation takes fewer observations than ADD did.
- T3.2: The system's candidate filtering is tighter for MUL (it knows to look at binary numeric tools because ADD was one).
- T3.3: If MUL takes the same or more observations than ADD, the system is NOT transferring. This is a legitimate negative finding — document it.

### Pass criteria
Either MUL is faster (transfer confirmed) or it isn't (transfer disproven). Both are valid research results. The test must produce a clear measurement either way.

### What we learn
Whether structural knowledge (the pattern "binary tool that takes numbers and returns numbers") transfers between discoveries, or whether each tool is learned independently.

---

## Training Test 4: Inverse Discovery After Sequential Learning

### What we're proving
That inverse relationships emerge automatically when both tools in a pair have been discovered.

### Protocol
- After ADD and SUB are both discovered (Sessions 2–3), run inverse discovery.
- The system should find SUB undoes ADD and ADD undoes SUB without being told to look.

### Test cases
- T4.1: After both ADD and SUB exist as nodes, inverse relationship is discoverable.
- T4.2: The inverse is stored in both nodes (bidirectional).
- T4.3: Inverse discovery for MUL↔DIV works the same way after MUL and DIV are discovered.
- T4.4: Inverse discovery is triggered by rumination (not by a hardcoded call). After a learning session where both tools in a pair are now known, the next rumination pass should find the inverse.

### Pass criteria
Inverses discovered through the system's own maintenance cycle, not through an explicit command.

---

## Training Test 5: Abstraction Detection (Place Value)

### What we're proving
That the system can abstract a general pattern from specific examples and apply it to novel inputs without re-exploration.

### Protocol
- Sessions 5–8: Deliver place-value observations for 15, 23, 47, 82 (one number per session). Each session includes the MOD(x,10) and FLOOR(DIV(x,10)) observations for that number.
- After these sessions, the system should have discovered MOD(x,10) and FLOOR(DIV(x,10)) as L1 procedures.
- Test session: Present 61 (never seen before). Measure what the system does.

### Test cases
- T5.1: After 4 sessions (15, 23, 47, 82), the system has discovered MOD(x,10) for last-digit extraction.
- T5.2: After the same sessions, FLOOR(DIV(x,10)) is discovered for tens-digit extraction.
- T5.3: When 61 is presented, the system applies the existing procedures to it WITHOUT re-exploring. It checks MOD(61,10)=1 and FLOOR(DIV(61,10))=6 using its known procedures.
- T5.4: The ghost node for 61 is constructed using the general pattern: MUL(6,10)+1. Not memorized — assembled from the discovered recipe.
- T5.5: If the system re-explores for 61 (probes tools fresh), that is a failure of abstraction. It's memorizing, not learning. Document what went wrong.

### Pass criteria
61 is handled entirely by existing procedures and the number construction recipe. Zero new exploration required.

### What we learn
Whether the L1 discovery mechanism (tool + constant) generalizes, or whether it only matches specific examples it was trained on.

---

## Training Test 6: Conflict Resolution

### What we're proving
That the system handles contradictory observations correctly based on weight of evidence.

### Protocol
- After ADD is confirmed as commutative (verified across multiple observations), deliver a single observation that appears to contradict commutativity.
- Then deliver 3 contradictory observations.
- Then deliver 5 contradictory observations.

### Conflict resolution policy:
- A well-confirmed property (weight ≥ 10) facing a single contradictory observation: flag the observation as anomalous. Do NOT demote the property. Rationale: one bad data point against strong evidence is noise.
- If contradictions accumulate (≥ 3 against a property), demote confidence from "always" to "sometimes." The property isn't wrong, but it's no longer universal.
- If contradictions exceed confirmations, demote to "never" and move the property to an antifact (excludes pointer). The system was wrong.

### Test cases
- T6.1: 1 contradiction against well-confirmed commutativity → flagged as anomalous, property unchanged.
- T6.2: 3 contradictions → confidence demoted from "always" to "sometimes."
- T6.3: Weight-of-evidence ratio: if confirmations are 20 and contradictions are 3, confidence is "sometimes." If contradictions reach 25, confidence becomes "never."
- T6.4: After demotion, rumination propagates the confidence change to all nodes that reference the property.
- T6.5: Anomalous flags are stored with the observation details so they can be reviewed during play or rumination.

### Pass criteria
Single contradictions don't destroy confirmed knowledge. Accumulated contradictions appropriately reduce confidence. Changes propagate through the network.

---

## Training Test 7: Session Dependency Queue

### What we're proving
That observations arriving before their infrastructure is ready are queued and revisited, not lost.

### Protocol
- Before logic is discovered (before Session 1 completes), deliver an arithmetic observation.
- The system cannot build a structured node definition without structural connectives.
- The observation should be queued, not discarded.
- After Session 1 completes and rumination runs, the queue should be revisited.

### Test cases
- T7.1: Arithmetic observation received before logic → queued as unresolved.
- T7.2: Queue entry includes the observation, a reason ("no structural connectives"), and a timestamp.
- T7.3: After logic is discovered and rumination runs, the queue is revisited. The arithmetic observation is now processable.
- T7.4: The processed observation produces the same result as if it had arrived in the correct order.
- T7.5: If the queue grows beyond a threshold (e.g., 50 unresolved), the system reports what infrastructure it's missing. This becomes the "what do I still not understand" list.
- T7.6: Queue items that become processable are removed. Items that remain after multiple rumination passes indicate a structural gap.

### Pass criteria
No observations are lost. Queued items are eventually processed. The system can report what it doesn't understand.

---

## Training Test 8: Play Budget and Efficiency

### What we're proving
That exploratory play produces useful discoveries within a fixed operation budget.

### Protocol
- After all learning sessions and rumination, give the system a play budget of 500 operations.
- The system probes tools with novel inputs, tries compositions, tests speculative chains.
- Measure: how many new discoveries per 100 operations.

### Test cases
- T8.1: Play runs within budget (does not exceed 500 ops).
- T8.2: Play produces at least 1 novel discovery (a chain, a property, or a new composition not found during learning).
- T8.3: Play does not produce false discoveries (everything found during play is verified before being stored).
- T8.4: Play efficiency metric: discoveries / operations. Compare across multiple runs.
- T8.5: If play produces zero discoveries, that's a finding — either the learning phase was thorough or the play strategy is too random.
- T8.6: Play on a dirty knowledge base (before rumination) vs play on a clean base (after rumination). Measure error rate in each. Prediction: dirty play produces more false starts.

### Pass criteria
Play stays within budget. All discoveries are verified. Efficiency is measurable and repeatable.

---

## Training Test 9: Regression After Rumination

### What we're proving
That rumination never breaks something that previously worked.

### Protocol
- After each rumination pass, re-run the 8 algebra problems from dev test 7.
- All 8 must still solve correctly.
- Also re-verify: ADD.canAccept(7)=yes, ADD.inverse()=SUB, ADD.relatedTo(commutative)=yes.

### Test cases
- T9.1: After Session 1 rumination, boot sequence intact (no regression on logic).
- T9.2: After each learning session rumination, all previously solved algebra problems still solve.
- T9.3: After play rumination, all previously discovered properties still hold.
- T9.4: If any regression is detected, the test captures: what rumination changed, which node was affected, what the previous state was. This is a propagation bug and must be fixed before proceeding.

### Pass criteria
Zero regressions. Performance never decreases after rumination. Every regression is diagnosable from the test output.

---

## Training Test 10: Full Training Pipeline

### What we're proving
That the entire training sequence — boot → logic → incremental learning → inverse discovery → abstraction → rumination → play — produces a system equivalent to or better than the dev batch pipeline.

### Protocol
- Run the complete training sequence from Session 0 through play.
- Compare final state against the dev a.5 results.

### Test cases
- T10.1: Same or more procedures discovered as dev (≥40).
- T10.2: Same observation coverage as dev (≥97%).
- T10.3: All 8 algebra problems solved.
- T10.4: Node count within target range (≤250).
- T10.5: Abstraction test passes (Test 5).
- T10.6: No regressions after final rumination (Test 9).
- T10.7: Total ops comparable to or less than dev (dev was 12,675).
- T10.8: If training is slower than dev, measure by how much. The overhead of incremental processing is the cost of learning. Document it.

### Pass criteria
Training produces equivalent or better results than batch processing. Any differences are documented and explained.

---

## Training Test 11: Chain Discovery and Sequence Reasoning

### What we're proving
That the system can discover multi-step chains through bidirectional search, distinguish between solving a specific problem and understanding a general pattern, and compress confirmed chains into reusable nodes.

### Two capabilities under test

**Open problem solving:** Given an input/output pair that no single tool explains, find any valid path. If the system finds a shorter path than the test designer intended, that's a pass — finding the shortest valid path is intelligence, not a bug. The system should be free to go straight for the throat.

**Constrained pattern recognition:** Given multiple observations that share a hidden chain structure with different values, find the generalizing chain. A chain that only works for one specific input is a coincidence. The chain that works for all inputs in the set is understanding.

### Search mechanism: Bidirectional
Instead of brute-forcing all tool combinations (60² = 3,600 for two-step, 60³ = 216,000 for three-step), the system works from both ends:
1. Backward from output: what known operations could produce this output?
2. Forward from input: what known operations can I apply to this input?
3. Meet in the middle: do any backward and forward candidates share an intermediate value?

Cost scales as (chain depth × tool count), not (tool count ^ chain depth).

### Search constraints
- **Depth limit:** longest confirmed chain + 1. The system reaches one level beyond what it has evidence for, but doesn't speculate on deep chains.
- **Confirmation requirement:** 1 observation suggests a chain. 3 observations with different inputs confirming the same structure validate it.
- **Chain becomes node:** confirmed chains become ghost nodes with procedures. Future observations matching that chain are recognized in one step. A five-step chain discovered with significant effort becomes a one-step lookup forever after. That node can then be a component in longer chains.

### Protocol

**Step-trace verification (applies to all chain tests):**
Every chain execution produces a step log — the ordered list of intermediate calls and their results. This is the "show your work" record. For any chain test, the evaluation checks not just the final output but the full trace:

```
Example: FLOOR(DIV(47, 10)) = 4

Expected trace:
  step 1: DIV(47, 10) → 4.7
  step 2: FLOOR(4.7) → 4

If the system instead produces:
  step 1: SUB(47, 43) → 4

The final answer is correct, but the trace doesn't match the generalizing chain.
For open solving: this is valid — different path, same destination.
For constrained solving: this is a fail — it found a specific solution, not the pattern.
```

The same trace data serves both test types. The difference is the evaluation criteria, not the instrumentation.

**Open solving phase:**
- Present observations explainable by 2-step chains. System searches for any valid path.
- If system finds a 1-step shortcut instead, record the trace. That's valid.
- Trace must show the actual path taken, confirming the system earned its answer.

**Constrained solving phase:**
- Present 3 observations sharing a hidden 2-step chain structure with different input values.
- System must find the chain that explains all 3, not just individual solutions.
- Trace for each observation must show the SAME chain structure applied to different inputs.
- If traces show different structures per observation, the system is solving individually, not generalizing.
- Repeat with a hidden 3-step chain.

**Integration phase:**
- Confirmed chains become ghost nodes.
- Present new observations that match the chain pattern. System recognizes them immediately.
- Trace should show a single-step call to the chain node (black box), NOT re-expansion of the internal steps.
- Test that a chain node can be used as a component in a longer chain.

### Test cases
- T11.1: Single observation, 2-step chain required. System finds a valid path. Trace shows both steps and intermediates.
- T11.2: System finds a shorter path than intended. Trace confirms the shorter path is valid. Record solution — this is a pass.
- T11.3: Search operations scale linearly with depth, not exponentially.
- T11.4: Three observations sharing hidden 2-step chain. Traces for all 3 show the same chain structure with different values. System finds generalizing chain.
- T11.5: System rejects chains that only explain individual observations but not the set. Trace evidence: chain produces correct output for obs 1 but null or wrong for obs 2.
- T11.6: Three observations sharing hidden 3-step chain. Traces show 3 consistent steps across all observations.
- T11.7: Confirmed chain becomes ghost node. Trace for new matching observation shows single call to chain node, not internal expansion.
- T11.8: Chain node used as component in a longer chain. Outer trace shows chain node call; inner trace (if inspected) shows the chain's own steps. Black box boundary preserved.
- T11.9: Maximum search depth bounded by longest known chain + 1.
- T11.10: System finds both the specific shortcut AND the general pattern. Reports two different traces: the shortcut trace (fewer steps, specific values) and the general trace (more steps, works for all inputs). This is the hardest test — meta-awareness of its own reasoning.

### Pass criteria
Open solving: valid path found within linear-scaling op budget. Constrained solving: generalizing chain found across all test observations. Chains compress into reusable nodes. Shorter solutions are rewarded, not penalized.

### What we learn
Whether bidirectional search is tractable. Whether the confirmation threshold (3 observations) is sufficient to distinguish general patterns from coincidences. Whether chain-to-node compression actually prevents re-discovery. Whether the system can distinguish "I solved this specific case" from "I understand this category."

---

## Implementation Sequence

### Phase 1: LearningSession class (Tests 1–2)
Build the incremental processor. Receive one observation, check against known procedures, explore if needed. Boot sequence through logic discovery.

### Phase 2: Transfer and inverse (Tests 3–4)
Measure learning speed across tools. Verify inverses emerge from rumination.

### Phase 3: Abstraction and conflict (Tests 5–6)
Place value generalization. Conflict resolution with weight-of-evidence.

### Phase 4: Queue and play (Tests 7–8)
Dependency queue for out-of-order observations. Budgeted exploration.

### Phase 5: Regression and integration (Tests 9–10)
Regression checks after every rumination. Full pipeline comparison against dev.

### Phase 6: Chain discovery (Test 11)
Bidirectional search. Open solving vs constrained solving. Chain-to-node compression. Composition of compositions.

---

## Open Questions

1. **What triggers exploration vs queuing?** If an observation doesn't match any known procedure, the system could either explore immediately or queue it and wait for more data. The trigger might be: explore if structural connectives are available and the observation type matches a known tool profile. Queue if infrastructure is missing.

2. **How does the system decide which tool to probe during exploration?** In dev, it tested all candidates. In training, that might be too expensive. Can it use existing knowledge to narrow the search? (e.g., "this looks like a binary numeric operation, start with tools that accept numbers")

3. **What constitutes a "session"?** Is it a fixed number of observations? A fixed time period? A single domain? The training test plan assumes one domain per session, but the system should handle mixed-domain sessions too.

4. **Can the system request more data?** If it has 2 observations that match a tool but needs 3 to confirm, can it signal "I need more examples of this pattern"? That would be a form of active learning.

5. **Where does chain discovery live in the work/ruminate/play cycle?** Unmatched observations trigger chain search during work (immediate need). Accumulated unresolved observations trigger chain search during rumination (offline analysis). Speculative compositions happen during play (exploratory). All three paths produce the same node type, but the trigger and budget differ.

6. **How does open solving interact with constrained solving?** If the system finds a shortcut for a specific case, does it also look for a general pattern? The ideal behavior: find a solution (work), then check if a more general pattern exists across the unresolved queue (ruminate). The shortcut solves the immediate problem; the general pattern prevents future problems.

7. **How are chain candidates prioritized during bidirectional search?** When working backward from an output, does the system try all 60 tools or use profile-guided filtering? The answer should be the same as L0 discovery: filter by type compatibility first, then test.

8. **How does the system represent generality?** A chain that works for specific inputs uses concrete node references. A chain that works for any number uses concept references (number_concept). The ghost node's procedure must distinguish these. Is the current arg type system ({type:"input"}, {type:"ref"}, {type:"value"}) sufficient, or does it need a {type:"concept"} arg that matches any value of that concept type?
