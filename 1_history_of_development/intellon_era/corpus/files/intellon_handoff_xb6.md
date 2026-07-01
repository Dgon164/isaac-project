# Intellon xb.6 — Handoff Document

**Date:** April 5, 2026
**Version:** xb.6 (ruminate + Node.js + WordNet)
**Status:** 385 tests passing, 43 tools trusted, 10 verified, 0 broken
**Prior build:** xb.5 (343 tests, documented in intellon_handoff_xb5.md)

---

## What Changed (xb.5 → xb.6)

### Platform: Node.js Extraction
- IntellonSystem extracted from JSX artifact into standalone Node.js module
- CLI: `node intellon.js` (REPL), `node intellon.js --test`, `node intellon.js "command"`
- Exports `{ IntellonSystem, Node, Trie, TrieNode }` for programmatic use
- JSX artifact preserved as-is for browser use

### Ruminate: Self-Directed Discovery
The system's idle-time thinking loop. Gather → propose → interrogate, recursive.

- **`housekeeping()`** — walks all nodes, verifies pointers, bumps trust, flags failures
- **`selectSeed()`** — scores nodes by pointer type DIVERSITY, not just count. Nodes with 2+ different relationship types rank highest. Pure taxonomy hubs are skipped.
- **`propose(gatherResult)`** — follows ALL pointer types outward (except eq). Builds multi-hop chains. Prefers paths that cross different relationship types (cross-type = interesting).
- **`interrogate(proposal)`** — checks for NOT blocks, missing nodes, and whether the terminus is already reachable via single-type walk. Already-walkable chains are skipped — no redundant data.
- **`play(seed, maxDepth)`** — recursive loop. Each gap becomes a new seed. Depth-limited.
- **`ruminate(seedWord?)`** — housekeeping + seed selection + play. Stores discoveries as `_discover_` nodes with `createdBy: 'self-discover'`, metadata only, NO redundant pointers.
- **`showDiscoveries()`** — lists pending discovery nodes for review.

### Compose: Multi-Inheritance Working Concepts
- **`compose(name, bases)`** — creates a working-space node with `base` pointers to each base concept.
- **Gather follows all bases.** `gather` on a composed node follows every `base` pointer, gathers each base, and merges all results. The composed concept IS the union of all its bases.
- **Contradiction detection.** On compose, walks each base's chain looking for NOT pointers that conflict with another base's reachable nodes. Reports contradictions but still creates the node.
- **Inherits everything.** Direct pointers, chains, reverse pointers, negatives — all merge. `compose sports_car car fast` inherits `is_a vehicle` from car, `opposite_of slow` from fast, `wheel part_of` from car's children.
- **Working space by default.** Composed concepts live in working memory. They fade if unused. If they earn trust through use, they promote like any other node.
- Command: `compose <n> <base1> <base2> ...`

### Scaling Optimization
Three O(n²) bottlenecks removed:
- **`_autoAssociate`**: was scanning all nodes on every `link()` call. Now uses `_discoveryIndex` (Map: word → Set<discovery_addr>) for O(1) lookup.
- **`selectSeed`**: was comparing every node against every other node for incoming pointers. Now does a single pass to build incoming type/count maps.
- **`gather` reverse query**: was scanning all nodes to find who points to this node. Now uses `_reverseIndex` (Map: targetAddr → [{sourceAddr, sourceName, rel}]) for O(1) lookup, maintained incrementally in `link()`.

**Performance results:**

| Scale | Before | After | Speedup |
|-------|--------|-------|---------|
| 5K facts | 30s | 1s | 30x |
| 10K facts | ~2min | 1.5s | ~80x |
| 50K facts | would not finish | 6s | ∞ |
| 77K facts (full WordNet is_a) | would not finish | 7.4s | ∞ |

System handles 77K nodes, 33K relationships, 10K auto sense splits in 7.4 seconds.

### Data Loading
- **`load <filepath>`** — reads facts from a file, one per line. `#` and `//` for comments.
- **Auto-sense splitting** — when load encounters a defining relationship conflict (e.g. `twilight is_a light` then `twilight is_a decline`), automatically creates senses `/1`, `/2` instead of prompting.
- Three ways to ingest: pipe stdin, `load` command, or one-at-a-time in REPL.

### Auto-Association & Passive Validation
- **`_autoAssociate(source, rel, target)`** — fires after every successful `link()` call.
- Finds siblings: other nodes sharing the same target via the same relationship type.
- Validates discoveries: scans all `_discover_` nodes, checks if the new data touches any node in a discovery's chain. If yes, bumps the discovery's trust.
- Contradiction detection: if a `not` pointer is added between two nodes in a discovery chain, the discovery is flagged with an error and trust reset.
- **Full trust lifecycle proven:** A discovery climbs from `working-trial` → `working-standard` → `working-proven` → `node-trial` → `node-proven` purely through incoming data reinforcement. No explicit confirmation needed.
- **bumpTrust fix:** Nodes already in node space now promote directly (working-proven → node-trial) instead of failing silently through the ws→ns promote path.

### WordNet Integration
- `extract_wordnet.py` generates `wordnet_full.json` (207K entries, 38MB)
- `wordnet_to_facts.py` converts to loadable fact files with controls:
  - `--max-senses 3` limits senses per word
  - `--rels is_a,opposite_of,eq` selects relationship types
  - `--no-multi-word` skips compound terms
  - `--max 2000` limits total facts
- Multi-sense words produce multiple is_a statements that auto-split on load

---

## Key Design Decisions (xb.6)

**D: Compose is one operation, not narrowing plus combining.** A composed concept IS all of its bases simultaneously. Remove any base and it's a different concept. This is inherited constraints — the concept only exists at the intersection. `fast_red_car` without `car` isn't a fast red car. Without `fast` it's a different thing.

**D: Composed nodes don't copy.** They point to bases and walk. Gather follows `base` pointers and merges everything. No duplication. The same principle as "store once, walk to find."

**D: A pointer is a pointer.** No "functional" vs "structural" distinction. `is_a`, `causes`, `has`, `opposite_of` are all the same thing — node, relationship, node. The system doesn't categorize them. It walks everything.

**D: No redundant data.** Store each fact once as a single hop. Walk at query time. Ruminate does NOT materialize transitive shortcuts. If `human is_a primate is_a mammal`, the system walks — it does NOT store `human is_a mammal`. At scale (24GB), duplicating walkable data would be catastrophic.

**D: Discoveries are metadata, not pointers.** `_discover_` nodes store the chain description and gap info. They don't create new pointers in the graph. The graph stays minimal. Discoveries are for review.

**D: Cross-type chains are the interesting discoveries.** A chain that uses the same relationship type throughout (is_a → is_a → is_a) is already walkable. A chain that crosses types (causes → produces → is_a) reveals non-obvious connections. Seed selection weights diversity for this reason.

**D: Complexity ≠ usability.** Knowing how to swim beats knowing heart surgery for most contexts. Any piece of information is valuable depending on context. The system doesn't privilege "functional" knowledge over "taxonomic" knowledge.

**D: The trie IS the answer.** "Is flower sometimes a rose?" doesn't need a new pointer type. Rose is one branch under flower. The branching factor answers the question. `is_a` + `not` remains a genuine contradiction.

**D: Ruminate = gather → propose → interrogate, recursive.** The attempt IS the gather. The answer IS the proposal. Three functions, one loop. Same shape as the learning loop, but the system is both questioner and answerer.

---

## Test Summary

```
385 tests: 385 passed, 0 failed

New sections added in xb.6:
  xb.6 Housekeeping, Seed Selection, Propose, Interrogate,
  Play, Ruminate, Discoveries, Self-Discover Nodes,
  Auto-Associate, Discovery Contradiction, Trust Lifecycle,
  Compose, Compose Gather, Compose Contradiction

All prior test sections (343) unchanged.
```

---

## What Ruminate Discovers (Demo)

Given WordNet taxonomy (77K is_a) plus functional relationships:

| Discovery | Chain | Type |
|-----------|-------|------|
| sun → dark | sun→light→dark | produces+opposite_of |
| combustion → somesthesia | combustion→heat→expansion→pressure→somesthesia | causes+produces+is_a |
| heat → electricity | heat→expansion→pressure→motion→rotation→electricity | causes+produces |
| engine → oxygen | engine→fuel→energy→oxygen | requires+has |

At 77K nodes: combustion walks through causal chains into WordNet taxonomy and discovers that pressure is a type of bodily sensation (somesthesia). Cross-domain, non-obvious, genuinely discovered across the full knowledge graph.

---

## Commands Added

```
ruminate                    run full ruminate cycle (auto-select seeds)
ruminate <word>             ruminate on a specific area
discoveries                 show pending self-discover nodes
load <filepath>             load facts from file (auto-sense-split)
compose <n> <b1> <b2> ...   create concept inheriting from all bases
```

---

## Files

| File | Description |
|------|-------------|
| `intellon.js` | **THE CODE.** Node.js CLI + full system. ~4191 lines. 385 tests. |
| `intellon_terminal.jsx` | Browser artifact (xb.5, preserved). ~3421 lines. |
| `wordnet_to_facts.py` | Converts wordnet_full.json to loadable fact files. |
| `extract_wordnet.py` | Generates wordnet_full.json from NLTK (~38MB). |
| `tag_corpus.py` | Generates tagged_corpus.json from Brown/Gutenberg corpora. |
| `intellon_facts_full.txt` | Sample fact file: 1500 is_a + 300 opposite_of + 200 eq + 28 functional. |
| `intellon_project_spec.md` | Foundation spec with 18 rules. |
| `intellon_project_plan.md` | Phase plan (10 phases complete + ruminate). |
| `intellon_tool_curriculum.md` | Test sheets for all primitives. |
| `intellon_handoff_xb5.md` | Prior handoff. |
| `intellon_handoff_xb6.md` | This document. |
| `intellon_v6_methodology.docx` | v6 methodology (project reference). |

---

## What's Next

### Immediate
- **Ruminate on idle/timer.** Currently user-triggered. Should auto-run when the system has downtime.
- **Review command.** Walk through discoveries one-by-one with y/n. Confirmed discoveries promote, denied ones get discarded.
- **Track 3: Grammar from corpus data.** Feed tagged corpus through adjacency tracking. Let the system discover grammar patterns from observation. Path to removing Phase 10 bodge.

### Data Pipeline
- **Full WordNet load.** Test performance at scale with 150K+ relationships.
- **Tagged corpus → adjacency.** 57K sentences of co-occurrence data feeds grammar learning.

### From Prior Handoff (Still Pending)
- Remove Phase 10 bodge (hardcoded grammar patterns → learned from adjacency data)
- Store exploration observations as nodes/pointers (not JSON blobs)
- Self-directed exploration choosing what primitives to explore next
- Expand curriculum to uncovered primitives

### The Big Leap
The system ruminates on its own adjacency data. It notices "the" always precedes nouns. It proposes "the is_a article." Grammar learned from data, not from `_parseSentence`. The same gather → propose → interrogate loop, applied to language structure instead of knowledge structure.

---

## Architecture

### Ruminate Flow
```
ruminate(seed?)
  │
  ├── housekeeping()
  │     verify pointers, bump trust, evict stale
  │
  ├── selectSeed()  (or use provided seed)
  │     score by pointer type diversity
  │     require 2+ different rel types
  │
  └── play(seed)  ← recursive
        │
        ├── gather(seed)       ← attention, all pointer types
        │
        ├── propose(context)   ← walk outward, build chains
        │     prefer cross-type paths
        │     skip eq pointers
        │
        └── interrogate(proposal) ← check for problems
              │
              ├── blocked by NOT → skip
              ├── already walkable → skip (no redundant data)
              ├── missing nodes → recurse or store partial
              └── clean → store as discovery (metadata only)
```

### Passive Validation Flow
```
link(source, rel, target)
  │
  └── _autoAssociate(source, rel, target)
        │
        ├── find siblings (same target, same rel type)
        │
        └── scan _discover_ nodes
              │
              ├── new data touches chain node → bumpTrust
              │     working-trial(2) → standard(7) → proven(8) → node-trial(17) → node-proven
              │
              └── NOT between chain nodes → flag contradiction, reset trust
```

---

## How to Continue

1. Copy files to `C:\Users\jtwee\intellon\`
2. Run `node intellon.js --test` to verify 385/385
3. Generate WordNet data: `python extract_wordnet.py` (if not already done)
4. Convert: `python wordnet_to_facts.py --max 5000 --max-senses 3 --no-multi-word`
5. Run: `node intellon.js`
6. `load intellon_facts.txt` → loads taxonomy + auto-splits senses
7. Add functional relationships manually or via file
8. `ruminate` → watch it discover cross-type connections
9. `discoveries` → review what it found
10. Build from here

---

## User Context

- **Platform:** Windows, Node.js 24, Python 3.13
- **Local path:** `C:\Users\jtwee\intellon\`
- **Memory:** 1GB current, 24GB allocated for this project
- **Storage:** 5TB available for data ingestion
- **Data files:** wordnet_full.json (~38MB), tagged_corpus.json (size varies)
- **Key preferences:** Discussion before implementation. No workarounds. Failures are findings. Complexity ≠ usability. A pointer is a pointer. NLP is just the door — structured reasoning over real data is the goal.

## Data Sources for Scale Testing

**Free, ready to use:**
- **Project Gutenberg** — 70K+ public domain books, free bulk download (gutenberg.org). More text than months of processing.
- **Wikipedia dumps** — full English Wikipedia ~22GB raw text. Structured, factual, cross-referenced. Close to how the system thinks naturally. (dumps.wikimedia.org)
- **NLTK corpora** — already accessible via `tag_corpus.py` and `extract_wordnet.py`.

**Engineering/technical data (for the real use case):**
- **MatWeb** — free material property database. Structured spec sheet data, maps directly to nodes.
- **Engineering Toolbox** — structured reference tables for mechanical/thermal/fluid properties.
- **NASA Technical Reports Server (NTRS)** — public domain technical papers and data.

**Priority order for testing:**
1. WordNet (already working, 77K nodes in 7s)
2. Tagged corpus (Track 3 — grammar learning)
3. Wikipedia subset (scale test — structured factual data)
4. Project Gutenberg (full NLP stress test)
5. Engineering property databases (real use case)
