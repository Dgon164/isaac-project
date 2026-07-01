# Dim Scanning — Concept Document

## For use in future SIS development sessions

---

## The Goal

Take any dim. Pull its activation pattern across the full context as a single string. Do the same for any other dim. Compare the two strings. That's it. That's the whole operation.

The system already stores per-position concept heatmaps (the `dim_channel` — a list of `{dim_name: weight}` dicts, one per token position). This document describes how to use that data for single-pass dim×dim comparison across an entire context window, replacing the current O(maps² × dims²) pairwise snapshot approach with something simpler, faster, and more aligned with the architecture.

---

## What a dim activation string looks like

Every dim that appears anywhere in a context has a position-indexed activation pattern. For a context of N tokens, the activation string is length N. Each position holds the weight at which that dim fired (0 if it didn't fire at that position).

Example — a 50-position context window with three dims:

```
dog:      00000000000000000012000000000000000000000110000000
fish:     00000000000000000000000011000000000000000000001200
mammals:  00000000000000000012000001200000000000000110001200
```

These are not binary bitmasks. They carry weight information. `1` means truth_weight ≈ 1.0. `2` means truth_weight ≈ 2.0 (boosted by multiple evidence sources). `0` means the dim did not fire at that position. Negative values (if using signed representation) mean contested claims.

But structurally they behave like bitmasks: two strings, same length, compare position by position.

---

## The operation

Given two dim activation strings of equal length:

1. **AND / overlap**: positions where BOTH dims fire (both nonzero). This is the co-activation signal. If `dog` and `mammals` both fire at positions 18-19 and 40-41, they co-activate there. That means something — probably that a sentence at those positions said something like "dogs are mammals."

2. **XOR / divergence**: positions where ONE fires and the other doesn't. This is the differentiation signal. Where `dog` fires but `mammals` doesn't, the text mentioned dogs without the mammal context. Where `mammals` fires but `dog` doesn't, something else was being called a mammal.

3. **NOR / silence**: positions where NEITHER fires. Irrelevant to this comparison. Skip.

This is the Comparator's SHARED / DIVERGENT / ABSENT trichotomy, applied to activation strings instead of dim-sets. Same operation. Different input.

---

## What it finds

### Different dims, overlapping patterns → function similarity

If `dog` and `fish` produce activation strings that overlap at the same structural positions across many sentences, they play the same role. The system doesn't know they're both animals. It discovered they occupy the same slot in the same kind of sentence.

### Different dims, non-overlapping patterns → complementary roles

If `dog` fires in the first half of the context and `fish` fires in the second half with no overlap, they're contextually separated. Different topics, different sections, different documents. That's structural information about the text.

### Same dim, different structural signature → role variation

If `dog` fires at position 3 (subject slot) in one sentence and position 7 (object slot) in another, the activation string captures both. The shape of the string tells you how the concept behaves across different syntactic roles. Two contexts where the same dim has different activation shapes are using that concept differently.

### Same dim, same structural signature → confirmation

If `dog` fires at the same structural slot across many sentences, that's strong evidence of a consistent role. The activation string is regular. The concept is stable in this corpus.

---

## Why this replaces pairwise snapshot comparison

The current `_check_activation_map_similarity` works like this:

```
for each pair of snapshots (a, b):          # O(maps²)
    for each dim_x in snapshot_a:           # O(dims_a)
        for each dim_y in snapshot_b:       # O(dims_b)
            intersect positions             # O(positions)
```

This is O(maps² × dims² × positions). At 1000 snapshots with 50 dims each, that's ~1.25 billion set intersections. It doesn't scale.

The activation string approach inverts the loop:

```
for each dim_x in the context:              # O(unique_dims)
    build activation string across ALL positions   # O(positions), one pass
for each pair of dims (x, y):               # O(dims²)
    compare two strings position-wise       # O(positions)
```

This is O(dims² × positions). No snapshot iteration. The snapshot boundaries don't matter for the comparison — a dim's activation string spans the entire context, and sentence/paragraph/context structure is already encoded in where the activations fall.

For a 50,000-position context with 500 unique dims: 250,000 dim pairs × 50,000 positions = 12.5 billion position checks. Still large, but the inner operation is a single-pass array comparison (effectively a bitwise AND), which is orders of magnitude faster than set intersection on arbitrary data structures. And most dim pairs will early-exit with zero overlap.

Further optimization: sparse representation. Most dims fire at very few positions relative to the full context. Store each dim's activation as a sorted list of (position, weight) pairs instead of a dense array. Intersection of two sorted lists is O(min(len_a, len_b)). A dim that fires at 20 positions out of 50,000 only costs 20 comparisons per pairing, not 50,000.

---

## How it fits the architecture

### It's the Comparator

The activation string comparison is SHARED / DIVERGENT / ABSENT on positional activation data. It's not a new operation. It's the existing operation pointed at a new input — which is exactly how SIS extends (Lesson: one operation, many inputs).

### It's stored, not computed

The dim_channel already stores the per-position concept heatmap. The activation string for any dim is a read query over that stored data: scan the heatmap at every position, extract the weight for the dim of interest (or 0 if absent). No precomputation needed. No aggregation at storage time (Lesson 29). The string is derived on demand from the raw heatmap.

### It respects the one door

The activation strings are observations. They don't create claims, don't bypass feed_text, don't assert anything. If the comparison finds that `dog` and `fish` co-activate, that's a proposed observation — a `dim_function_similarity` node with zero evidence weight, waiting for the researcher or theorist to do something with it. Or waiting for more data to accumulate evidence.

### It's the crystallizer's job

The crystallizer already does compression, erosion, and skimming. Scanning dim pairs across the full context heatmap is crystallizer work — it's looking for structural overlap in observed data. No new layer needed. No new mechanism. The crystallizer gets a new input to compare, and comparison is what it does.

---

## What this is NOT

- **Not a parser.** It doesn't interpret what the activations mean. It observes where they co-occur.
- **Not a filter.** It doesn't discard non-overlapping dims. It surfaces overlapping ones as candidates. Everything stays in the heatmap.
- **Not a scorer.** It doesn't compute a single similarity number for two dims. It produces the overlap pattern — which positions, with what weights. The pattern IS the result. Downstream queries interpret it for their specific purpose.
- **Not prescriptive.** It doesn't decide which dim pairs are "interesting." It checks all of them. Most will have zero overlap. That's fine. The ones that do overlap are surfaced as proposed structure. The system decides what to do with them through evidence accumulation, not through a relevance filter.

---

## Implementation path

1. **Build `dim_activation_string(context_map, dim_name)`** — scans the context's dim_channel data, returns sparse list of `(position, weight)` for positions where the dim fires.

2. **Build `compare_dim_activations(string_a, string_b)`** — sorted-list intersection. Returns shared positions with both weights, count of shared, count of divergent on each side. This is the Comparator on activation strings.

3. **Replace `_check_activation_map_similarity`** with a context-level scan: for each context_map, extract all unique dims, build activation strings, run pairwise comparison across dims. Surface overlapping pairs as `dim_function_similarity` proposals with the shared positions as evidence.

4. **Same-dim comparison across contexts**: take a dim's activation string from context A and the same dim's activation string from context B. Different shapes = the concept plays different structural roles in different texts. Same shape = stable role. Both are useful observations.

5. **Cross-context dim×dim comparison**: take dim X from context A and dim Y from context B. If they overlap in structural position (e.g., both fire at subject slots), they're function-similar across different texts. This is the strongest form of the discovery — it generalizes across corpora.

---

## The expected result

Most dim pairs will show zero overlap. That's correct and informative — most concepts don't co-activate.

A small number of dim pairs will show positional overlap. These fall into predictable categories:

- **Categorical siblings** (dog/fish, hawk/salmon): same structural role, different content. The system discovers they're "the same kind of thing" without knowing what kind.
- **Hierarchical pairs** (dog/mammals, fish/animals): the category dim fires wherever any member dim fires, plus elsewhere. Subset pattern.
- **Structural pairs** (function_word/verb): positional co-activation from words that carry multiple roles.
- **Surprising pairs**: dims that co-activate for reasons the system didn't anticipate and the operator didn't prescribe. These are the discoveries. The system surfaces them; the theorist layer (or the human operator, for now) decides what they mean.

The 4-7:1 compression band applies here too. Out of N unique dims, the number of meaningfully overlapping pairs should be roughly N/4 to N/7. If it's much higher, the comparison threshold is too loose. If it's much lower (or zero), the context doesn't have enough repeated structure to find patterns. The ratio is a health check on the scanning parameters, same as it is for lift thresholds.

---

## Summary

One dim. One string. One comparison. Across the whole context. That's the operation. Everything else — which dims to compare, what the overlap means, whether it's significant — is downstream. The substrate observes the co-activation pattern. It does not interpret it.
