# Isaac — Crystallization Pipeline

## Specification v2.0 — June 20, 2026

---

## Architecture

Three zones. Two modes.

```
         ACTIVE (real-time)                    IDLE (consolidation)
         ─────────────────                     ────────────────────

  ┌───────────┐                                ┌──────────────────┐
  │  STAGE 1  │   Sensory cortex               │   CONSOLIDATE    │
  │   SENSE   │   Raw → structured             │                  │
  └─────┬─────┘                                │  Full O(n²) over │
        │                                      │  dirty regions.  │
        ▼                                      │  New types. New  │
  ┌─────────────────────────────┐              │  merges. Reorg   │
  │         THINK               │              │  hierarchy. Run  │
  │  ┌─────┐ ┌─────┐ ┌─────┐   │              │  when nothing is │
  │  │  2  │↔│  3  │↔│  4  │   │              │  waiting.        │
  │  │Store│ │Route│ │Eval │   │              │                  │
  │  └──┬──┘ └──┬──┘ └──┬──┘   │              │  This is sleep.  │
  │     └───────┴───────┘      │              └──────────────────┘
  │     concurrent loop         │                       │
  │     small working set       │                       │
  │     O(k²), k = active      │                       ▼
  └─────────────┬───────────────┘              [NET GLOBALLY UPDATED]
                │                              [HIERARCHY REORGANIZED]
                ▼                              [DIRTY SET CLEARED]
  ┌───────────────┐
  │    STAGE 5    │   Motor cortex / basal ganglia
  │     ACT       │   Commit → execute → feedback
  └───────┬───────┘
          │
          └──────→ STAGE 1 (proprioception / feedback)
```

---

## The Two Modes

### Active Mode — Real-Time Processing

Triggered by: observation or query arriving.

The 2/3/4 loop crystallizes ONLY the working set. The query tokens,
the relevant net region, the active inference trace. Nothing else.

Uses existing types and structure as-is. Does not try to discover
new global patterns. Does not reorganize the hierarchy. Just processes
with what it already knows.

Complexity: O(k²) where k = working set size (typically 10-30 tokens).
Real-time. Microseconds.

### Idle Mode — Consolidation (Sleep)

Triggered by: no active queries pending.

Runs the full crystallization over the dirty set — all observations
that arrived since the last consolidation. Discovers new types that
span multiple active sessions. Finds merges. Reorganizes the hierarchy.
Updates rules. Recompiles affected matrix regions.

This is why brains sleep. The O(n²) comparison is the RIGHT operation
for consolidation — finding global patterns across everything. You just
don't do it while someone is waiting for an answer.

Complexity: O(d²) where d = dirty set size. In the worst case (no
consolidation for a long time), d approaches n. In practice,
consolidation runs often enough that d stays small.

Priority: dirty regions first, then expanding outward. Can be
interrupted by an incoming query (wake up) and resumed later.

---

## Stage Definitions

### Stage 1 — SENSE (Sensory Cortex)

**When:** Data arrives from outside.

**What:** Raw input → crystallized input. First feature extraction.
Tokenize, build local door profiles, find local patterns WITHIN
this batch only.

**Input:** Raw text / token sequences.

**Output:** Structured tokens with local profiles, ready for the Think loop.

**Implementation:**
```python
def _sense(self, tokens):
    """Stage 1: crystallize raw input locally."""
    # Build local profiles for new tokens
    # Find obvious local types (within this batch)
    # Tag tokens with their local context
    # Add to dirty set for later consolidation
    # Create sequential doors in the net (current observe behavior)
```

**Complexity:** O(k²) where k = unique tokens in batch.

---

### Stage 2 — STORE (Hippocampus)

**When:** Always active within the Think loop.

**What:** Memory formation and retrieval. Stores new doors. Retrieves
existing structure. Pattern completion — given partial input, retrieves
the full stored pattern.

**In the active loop:** Stores new observations. Retrieves existing
types for comparison. Does NOT reorganize the type hierarchy — that's
consolidation work.

**In consolidation:** Full reorganization. New types discovered.
Existing types merged. Hierarchy updated. This is the expensive pass,
done in idle mode only.

**Implementation:**
```python
def _store(self, findings):
    """Stage 2: integrate findings into net (within active loop)."""
    # Add new doors from current observation
    # Retrieve relevant existing types (those sharing structure)
    # Slot new tokens into existing types if match is clear
    # Flag ambiguous cases for consolidation
    # Update dirty set
```

---

### Stage 3 — ROUTE (Thalamus)

**When:** Always active within the Think loop.

**What:** Central relay. Routes input to the right stored patterns.
Routes stored patterns to evaluation. Decides what gets attention
and what gets filtered. This is the matrix — context meets stored
knowledge, produces activation.

**In the active loop:** Encode the current context. Find matching
frames. Produce the activation vector. Incremental matrix update
for any new observations not yet compiled.

**In consolidation:** Full matrix recompilation of dirty regions.
Pre-compute commonly accessed patterns.

**Implementation:**
```python
def _route(self, context):
    """Stage 3: find relevant knowledge for this context."""
    # Incremental matrix update if dirty sequences exist
    # Encode context into activation vector
    # Find matching frames (exact + type-level)
    # Return activation: which deltas are candidates
```

---

### Stage 4 — EVALUATE (Prefrontal Cortex)

**When:** Always active within the Think loop.

**What:** Executive function. Is this answer good? Does the trace
make sense? Should I commit or keep thinking? Should I decompose
and try again? This is check-not-argmax. This is persistence
assessment. This is where the system decides it doesn't know
something (shrug) rather than guessing.

**In the active loop:** Validate the inference result. Cross-check
if possible. Assess confidence. Decide: commit, decompose, or shrug.

**In consolidation:** Review past traces. Learn which patterns of
confidence/trace predict correct vs incorrect results.

**Implementation:**
```python
def _evaluate(self, result, trace, context):
    """Stage 4: validate result before committing."""
    # Confidence check — is this above threshold?
    # Consistency check — does the trace look like known-good traces?
    # Cross-check if possible (commutative verify, alternate path)
    # Decision: commit → Stage 5
    #           decompose → back to _route with simpler sub-problems
    #           shrug → return unknown
```

---

### The Think Loop

Stages 2, 3, and 4 are not called in sequence. They're a loop.

```python
def _think(self, context=None, new_findings=None, max_cycles=5):
    """The concurrent 2/3/4 loop. Runs until convergence."""

    for cycle in range(max_cycles):
        # STORE: integrate anything new
        if new_findings:
            self._store(new_findings)
            new_findings = None

        # ROUTE: find relevant knowledge
        if context is not None:
            activation = self._route(context)
        else:
            break  # observation only, no query

        # EVALUATE: is the result good?
        result = self._evaluate(activation, trace, context)

        if result.confident:
            return result  # converged — send to Stage 5

        if result.should_decompose:
            # Break into sub-problems, re-enter the loop
            sub_results = []
            for sub_context in result.sub_problems:
                sub = self._think(context=sub_context)
                sub_results.append(sub)
            # Reassemble and evaluate again
            new_findings = self._assemble(sub_results)
            context = None  # now evaluating the assembled result
            continue

        if result.shrug:
            return result  # don't know — honest unknown

    return result  # max cycles reached
```

---

### Stage 5 — ACT (Motor Cortex / Basal Ganglia)

**When:** The Think loop has converged on a result.

**What:** Commit gate. The basal ganglia decides go/no-go. If go,
structure the output and execute. The result feeds back to Stage 1
as a new observation (the growth cycle).

**Implementation:**
```python
def _act(self, result):
    """Stage 5: commit and output."""
    # Go/no-go gate (persistence assessment for actions)
    # Structure the output (format for the domain)
    # If novel result (from decomposition):
    #   feed back to Stage 1 as new observation (memorize)
    #   mark dirty for next consolidation
    # Return to caller
```

---

### Consolidation (Sleep)

```python
def consolidate(self, max_time=None):
    """Full crystallization of dirty regions. Run when idle.

    This is the O(n²) pass — but only over the dirty set, and only
    when nothing is waiting. Can be interrupted and resumed.
    """
    # Get dirty set (all changes since last consolidation)
    # Phase 1: Compare dirty nodes against each other
    #          → new types within the dirty set
    # Phase 2: Compare dirty types against existing types
    #          → merges, new hierarchy levels
    # Phase 3: Compare dirty nodes against existing types
    #          → slot into existing types, expand type membership
    # Phase 4: Recompile matrix for dirty regions
    # Phase 5: Update rules and lockouts from new contrasts
    # Phase 6: Clear dirty set (or mark as clean)
    # Phase 7: Re-rank initiators
    #
    # Can be called with max_time to limit duration.
    # Tracks progress so it can resume where it left off.
```

---

## Public API Changes

The public API stays almost identical. The pipeline is internal.

```python
# Before (manual steps)
isaac = Isaac()
isaac.observe(tokens)       # just stores
isaac.crystallize()         # manual, O(n²)
isaac.compile()             # manual, batch
answer = isaac.lookup(ctx)  # one matmul

# After (automatic pipeline)
isaac = Isaac()
isaac.observe(tokens)       # Stage 1 → sense
                            # Stage 2 → store (incremental)
                            # dirty set updated

answer = isaac.lookup(ctx)  # _think() loop:
                            #   Stage 3 → route (incremental compile + encode)
                            #   Stage 4 → evaluate (validate)
                            #   Stage 5 → act (commit)

isaac.consolidate()         # run when idle — full crystallization
                            # of dirty regions. The O(n²), offline.
```

### Methods That Stay the Same
- `observe(tokens)` — same call, now triggers Stage 1 + incremental Stage 2
- `observe_negative(tokens)` — same
- `teach(subject, relation, obj)` — same
- `lookup(context)` — same return value, now goes through Think loop
- `check(context, target)` — same return value, now goes through Think loop
- `can_check()`, `is_a_check()`, `containment_check()` — same
- `compute()`, `solve()`, `logic_eval()` — same
- `assess()`, `plan_think_execute()` — same
- `generate()`, `predict_next()` — same (walker, not matrix)
- `status()` — same, plus dirty set size

### Methods Added
- `consolidate(max_time=None)` — run idle-mode crystallization
- `_sense(tokens)` — Stage 1 (internal)
- `_think(context, findings)` — Stages 2/3/4 loop (internal)
- `_act(result)` — Stage 5 (internal)
- `_store(findings)` — Stage 2 (internal)
- `_route(context)` — Stage 3 (internal)
- `_evaluate(result, trace, context)` — Stage 4 (internal)

### Methods Removed
- `crystallize()` — replaced by automatic Stages 1/2 + `consolidate()`
- `compile()` — replaced by incremental compilation in Stage 3

### New State
- `_dirty_sequences` — list of observation indices not yet consolidated
- `_dirty_nodes` — set of nodes with new doors since last consolidation
- `_type_profiles` — cached profiles for existing types (avoid recomputing)
- `_consolidation_progress` — where we left off if interrupted

---

## Complexity Summary

| Situation | Before | After |
|---|---|---|
| Single observation | O(1) | O(k²) Stage 1, k ≈ 5-10 |
| Query | O(F) matmul | O(F) matmul + O(t) validation |
| Type discovery after 100 observations | O(n²), n = all nodes | O(d²), d = dirty nodes only |
| Bulk feed 10,000 math facts | O(1) then O(n²) crystallize | O(1) per fact, consolidate later |
| Full consolidation | O(n²) always | O(d²) dirty only, interruptible |

Active-mode processing never exceeds O(k²) where k is the working set.
Consolidation handles the O(n²) offline, scoped to dirty regions.

---

## Implementation Plan

### Phase 1: Dirty Tracking
Add `_dirty_sequences`, `_dirty_nodes`. Mark dirty on every `observe()`.
This doesn't change any behavior — just tracks what's new.

### Phase 2: Incremental Compilation
Replace `compile()` with incremental update in `_route()`. Only process
sequences in `_dirty_sequences`. Extend existing W matrix instead of
rebuilding from scratch.

### Phase 3: Think Loop
Wire `lookup()` and `check()` through `_think()`. Stage 3 does the
incremental compile + encode. Stage 4 validates. Stage 5 commits.
Verify all existing tests still pass.

### Phase 4: Consolidate
Implement `consolidate()` as the idle-mode full crystallization.
Scoped to dirty set. Interruptible. Verify that running `consolidate()`
after bulk observation produces the same types as the old `crystallize()`.

### Phase 5: Stage 1 Intelligence
Add local crystallization to `_sense()`. Currently observe() just
creates doors. After this, it also finds local types within the batch.
This is optional — the system works without it, just benefits from it.

### Phase 6: Type-Level Attention
Stage 3 uses discovered types to activate frames for novel tokens.
"smash computer" → "smash" typed as destructive → activate all
destructive verb frames. This eliminates the training-side verb-level
workaround.

---

*Active mode: crystallize the working set. Real-time.*
*Idle mode: crystallize the dirty set. The rest can wait.*
*Same function. Different scope. Different urgency.*
