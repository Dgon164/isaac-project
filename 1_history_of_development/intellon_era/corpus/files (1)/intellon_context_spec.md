# Intellon Track 4 — Context & Provenance

**Date:** April 5, 2026
**Depends on:** xb.7 (457 tests, unified pipeline)
**Goal:** Every fact knows where it came from. Queries can ask "why do you believe this?"

---

## The Problem

All facts currently sit in the same graph with equal standing. "Frodo is_a hobbit" and "dog is_a animal" are indistinguishable in authority. If you load a fantasy novel and a biology textbook, the system can't tell you which claims are supported by what.

## The Principle

Context is provenance, not a fiction label. "Frodo is_a hobbit" is true — that IS what Frodo is. The context tag says where the fact came from: Lord of the Rings. "Hobbits exist" as a general claim only holds if you trace through LOTR context. "Dogs exist" holds through WordNet, biology texts, and hundreds of observed sentences — multiple independent sources, much stronger.

Trust builds from source diversity. A fact with one source from one fiction book is weaker than a fact with ten sources across different contexts. The existing trust lifecycle already handles reinforcement — source tagging adds the ability to explain WHY trust is high or low.

---

## Design

### Pointer Extension

Currently a pointer is: `{ type: string, to: string }`

After: `{ type: string, to: string, source: string|null }`

The source field is optional. Null means no provenance recorded (backward compatible with all existing pointers). A source string is the name of the context — typically a filename, a session ID, or a user-specified label.

### link() Change

```javascript
// Current
link(source, rel, target)

// After
link(source, rel, target, opts = {})
// opts.source = context label (e.g. 'lord_of_the_rings', 'wordnet', 'manual')
```

When opts.source is provided, the pointer gets the source field. When not provided, source is null (same as current behavior). This is fully backward compatible — no existing code breaks.

### load Command

```
load intellon_facts.txt                          # source = filename
load lotr_facts.txt --context lord_of_the_rings  # source = explicit label
```

When loading a file, every `link()` call passes the filename (or explicit label) as the source. The source propagates through the pipeline: `exec()` → `_processInput()` → `link()`.

### Duplicate Handling with Sources

Currently, if `dog is_a animal` already exists, `link()` returns `{ duplicate: true }`.

After: if the pointer exists but with a different source, add the new source. A pointer can have multiple sources. This is reinforcement from independent origins.

Options for source storage on pointers:
- **Option A:** Single source field, first one wins → simple but loses data
- **Option B:** Source is an array → `{ type: 'is_a', to: addr, sources: ['wordnet', 'biology_101'] }`
- **Option C:** Multiple pointers allowed if sources differ → more pointers but each is simple

**Recommendation: Option B.** One pointer per relationship, sources accumulate as an array. Deduplication still works (same type + same target = same pointer), but source data grows. This directly maps to trust: more sources = stronger fact.

### Querying with Context

```
gather dog                        # all facts, all contexts (current behavior)
gather dog --context general      # only facts with no specific context (or multi-sourced)
gather dog --context lotr         # only facts from LOTR context
gather dog --source               # show sources alongside facts
```

The `--source` flag adds provenance to the display:

```
GATHER: dog
  dog —is_a→ animal [wordnet, biology_101, manual]
  dog —has→ fur [manual]
  dog —resembles→ wolf [learned]
```

### Source-Weighted Trust

A fact's effective trust is the combination of:
- Its node trust level (existing lifecycle)
- Its source count (new)
- Its source diversity (new — different types of sources are stronger than multiple from the same type)

This doesn't replace the existing trust lifecycle. It augments it. A fact that's been reinforced from 5 independent sources gets trust bumped 5 times — the lifecycle handles the rest.

### Context Nodes

Each unique context/source gets a node in the graph: `_context_lord_of_the_rings`, `_context_wordnet`, etc. These nodes can have their own metadata:

```javascript
{
  name: '_context_lord_of_the_rings',
  value: {
    type: 'fiction',           // optional user-provided label
    factCount: 347,            // how many facts from this source
    loadedAt: timestamp,
    filepath: 'lotr_facts.txt' // original file
  }
}
```

Context nodes are queryable: `contexts` command lists all known contexts with fact counts. `context lord_of_the_rings` shows details.

### Cross-Context Reasoning

When the system walks a chain and crosses contexts, it should note the transition:

```
is Frodo a person?
  frodo —is_a→ hobbit [lord_of_the_rings]
  hobbit —is_a→ creature [lord_of_the_rings]
  creature —is_a→ living_thing [wordnet]
  → Yes (via lord_of_the_rings → wordnet)
```

The answer is "yes" but the system can report that the claim depends on LOTR context for the first two hops. If the user only trusts general/wordnet context, the chain breaks at "hobbit."

---

## Implementation Steps

### Step 1: Pointer Source Field
- Extend pointer structure: `{ type, to, sources: [] }`
- Update `link()` to accept `opts.source` and store it
- Update duplicate detection: same type + same target = same pointer, but append new source
- Backward compatible: existing pointers get `sources: []` (empty = no provenance)

### Step 2: Load with Context
- `loadFile()` passes source label through to exec/pipeline/link
- `_processInput` passes `opts.source` through to `link()`
- Default source for load = filename
- `--context` flag for explicit label

### Step 3: Context Display
- `gather --source` shows sources on each pointer
- `contexts` command lists all known contexts
- `context <name>` shows details for a specific context

### Step 4: Source-Weighted Queries
- `gather --context <name>` filters to specific context
- `gather --context general` filters to multi-sourced or unsourced facts
- Chain walking reports context transitions

---

## What This Does NOT Do

- Does not classify content as fiction/nonfiction (that's a user label, not system inference)
- Does not prevent cross-context contamination (the system walks all pointers by default — filtering is opt-in)
- Does not change how ruminate works (ruminate walks everything, discoveries note sources)
- Does not add permissions or access control (all contexts are readable by default)

---

## Open Questions

**Q1: Should observation data (_role_, _pattern_ nodes) be context-tagged?** Recommendation: no. Structural patterns are universal — the way language works doesn't change between fiction and non-fiction. Role observations from LOTR text are just as valid for grammar learning as from Wikipedia.

**Q2: Should the pipeline auto-detect context from content?** For example, if the system encounters "Frodo" and has LOTR context loaded, should it auto-tag new Frodo facts with LOTR context? Recommendation: not yet. Auto-detection requires confidence thresholds and could mis-tag. Let the user specify context explicitly. The system can suggest context matches but shouldn't assume.

**Q3: How to handle conflicting facts across contexts?** "Elves are immortal" (LOTR) vs "Elves are not real" (general). These aren't contradictions — they're true in different contexts. The existing contradiction detection should NOT fire across different contexts. Only flag contradictions within the same context or in the general space.

---

## Files Modified

| File | Change |
|------|--------|
| `intellon.js` | Extend pointer structure, update link(), load, gather, add context commands |
| `intellon_handoff_xb8.md` | Next handoff |
