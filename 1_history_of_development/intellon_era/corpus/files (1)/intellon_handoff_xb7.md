# Intellon xb.7 — Handoff Document

**Date:** April 5, 2026
**Version:** xb.7 (unified pipeline + grammar learning)
**Status:** 457 tests passing, all prior functionality intact
**Prior build:** xb.6 (385 tests, documented in intellon_handoff_xb6.md)

---

## What Changed (xb.6 → xb.7)

### Unified Input Pipeline
All non-command input now flows through one function: `_processInput(input, opts)`. Four stages execute on every input regardless of source:

1. **Recognition** (`_recognize`) — classifies input as structured, sentence, or token. Checks scaffold (`REL_TYPES`) first, then learned patterns.
2. **Context** (`_updateContext`) — updates focus pointer and entity tracking. Generalizes the discourse system to all input, not just comprehend.
3. **Integration** — routes to `link()` for structured, `_parseSentence()` for sentences, `ingest()` for tokens. Existing handlers unchanged.
4. **Observation** (`_observe`) — records what role each token played and what structural pattern appeared. Every input is both content and training data.

### Observation Recording
- **Role nodes** (`_role_<word>`) — accumulate role counts per word. Dominant role is best guess.
- **Pattern nodes** (`_pattern_<key>`) — accumulate structural pattern counts. Promote through trust lifecycle.
- **Inferential learning** — when 3 tokens arrive and outer two are known entities with a promoted entity-connector-entity pattern, the middle token gets inferred as probable connector.

### Pattern Emergence
- `_getDominantRole(word)` — returns the role a word most often plays
- `_matchPattern(tokens)` — builds role sequence, checks promoted `_pattern_` nodes
- `_recognize` checks scaffold first, then learned patterns, then fallback
- Pattern must be at least working-standard (seen 2+ times) for recognition

### Comprehend Through Pipeline
`comprehend()` routes each sentence through `_processInput` with `{ parse: true }`.

### Inspection Commands
- `roles <word>` — learned role distribution with percentages and trust
- `patterns` — all learned structural patterns with counts and active status

---

## What's Next — Priority Order

### FIRST PRIORITY: Storage Migration (Track 5)

Everything lives in memory as a tree of JavaScript Maps. Works at 77K nodes. Cannot scale to Wikipedia (22GB raw, 50-100M relationships) or support multiple clients.

#### The Current Problem

The Trie class does two things at once:
1. **Address scheme** — "dog" → `100.111.103` (char codes joined by dots)
2. **Storage container** — physical tree of TrieNode objects, each holding a Map of children

These should be separate. The address scheme is a function. The storage is a database.

#### Three Types of Navigation (Same Nodes, Different Lenses)

1. **Structural** — spelling relationships. "dog" and "door" share prefix `100.111`. Becomes a string prefix query on address column.
2. **Conceptual** — pointer graph. `dog is_a animal`, `animal is_a organism`. Walk the pointers.
3. **Functional** — role and pattern data. "dog" as entity, "is_a" as connector. Observed behavior.

The trie doesn't need to be physical. It's conceptual. The database stores rows keyed by address string.

#### Target Architecture

Replace Trie internals with SQLite via `better-sqlite3` (synchronous, single file, billions of rows).

```
nodes
  address     TEXT PRIMARY KEY
  name        TEXT
  value       TEXT (JSON)
  trust       TEXT
  createdBy   TEXT
  accessCount INTEGER
  timestamp   INTEGER
  lastAccess  INTEGER
  space       TEXT ('node' or 'working')

pointers
  id          INTEGER PRIMARY KEY
  source_addr TEXT
  type        TEXT
  target_addr TEXT
  sources     TEXT (JSON array — provenance, see Track 4)

  INDEX on source_addr
  INDEX on target_addr
  INDEX on type

senses
  parent_addr TEXT
  sense_num   INTEGER
  address     TEXT
  (same columns as nodes)
```

**API stays the same.** `get(addr)`, `set(addr, node)`, `has(addr)`. Nothing in IntellonSystem changes except Trie internals.

**`allNodes()` gets replaced** with specific queries:
- `findByTrust(level)` — housekeeping
- `findByCreator(type)` — discovery review
- `findWithPointers()` — selfTest, selectSeed
- `countRelationships()` — stats
- `findByPrefix(prefix)` — structural navigation

#### Wikipedia Processing Model

Working space is the scratchpad:

1. Load one Wikipedia page
2. Comprehend through unified pipeline
3. Pipeline creates working nodes, records observations
4. Useful facts link into permanent node space
5. Flush working space
6. Next page

5000 words in, maybe 20 facts out. Permanent storage grows incrementally. Working space stays small. As the system learns more, later pages produce richer connections.

#### Multi-Client Consideration

SQLite on disk = multiple processes can read the same knowledge base. Graph becomes shared infrastructure.

#### Implementation Steps

**Step 1:** StorageEngine class. Same API as Trie. Wraps SQLite. All 457 tests must pass.

**Step 2:** Replace every `allNodes()` call with targeted query methods.

**Step 3:** Move pointers from arrays on Node objects to rows in pointers table.

**Step 4:** Replace `_discoveryIndex` and `_reverseIndex` Maps with database queries.

**Step 5:** Verify at scale with full WordNet (77K nodes). Benchmark.

---

### SECOND PRIORITY: Context and Provenance (Track 4)

See `intellon_context_spec.md`. Fits naturally into storage migration — the `sources` column on pointers table IS the provenance system.

- Every pointer gets optional `sources` array
- `load` tags all facts with file source
- `--context` flag for explicit labeling
- Queries filter by context or report provenance
- Trust correlates with independent source count
- Cross-context contradictions don't fire

Context is provenance, not a fiction label. "Frodo is_a hobbit" is true. The source tag says where it came from.

---

### THIRD PRIORITY: Track 3 Continuation

Pipeline infrastructure is built. Next steps:
- Feed tagged corpus at volume
- Let patterns mature past scaffold
- Enable parse gating for all input once patterns are reliable
- Equivalence discovery (`is_a` = `is a` = `is an`)
- Eventually remove Phase 10 bodge

---

### From Prior Handoffs (Still Pending)
- Review command for discoveries
- Ruminate on idle/timer
- Store exploration observations as nodes/pointers

---

## Key Design Decisions (xb.7)

**D: One pipeline, difficulty gradient.** Structured input is easy. Natural language is hard. Same four stages.

**D: Every input is training data.** Processing a fact also records roles and patterns.

**D: Inference from clues, not rules.** Best guesses as working-trial. Trust lifecycle handles promotion.

**D: Scaffolds stay until replaced.** Starting clues, not permanent rules.

**D: No separate concept nodes.** Entities updated directly. Focus pointer says which is current.

**D: The trie is conceptual, not physical.** Address scheme stays. Storage becomes database.

**D: Working space is the scratchpad.** Process, compress, flush, repeat.

---

## Test Summary

```
457 tests: 457 passed, 0 failed

New in xb.7:
  xb.7 Pipeline Routing (T110)       xb.7 Recognition (T111)
  xb.7 Pipeline via Exec (T112)      xb.7 Parse Gating (T113)
  xb.7 Role Observation (T114)       xb.7 Pattern Observation (T115)
  xb.7 Context & Focus (T116)        xb.7 Dominant Role (T117)
  xb.7 Pattern Matching (T118)       xb.7 Learned Recognition (T119)
  xb.7 Inferential Learning (T120)   xb.7 End-to-End Learning (T121)

All prior 385 tests unchanged.
```

---

## Architecture

### Unified Pipeline Flow
```
_processInput(input, opts)
  │
  ├── _recognize(tokens)
  │     ├── scaffold: REL_TYPES check
  │     ├── learned: _matchPattern
  │     └── fallback: sentence or token
  │
  ├── Integration
  │     ├── structured → link()
  │     ├── sentence + parse → _parseSentence() → link()
  │     └── token → ingest()
  │
  ├── _updateContext(result)
  │
  └── _observe(tokens, recognition, result, opts)
        ├── structured: entity/connector roles + pattern
        ├── parsed: entity/action/connector/reference roles
        └── tokens (3-token): infer middle role if outer are entities
```

### Current Storage → Target Storage
```
CURRENT                              TARGET
Trie ('node')                        SQLite file
  └── TrieNode tree (Maps)             ├── nodes table
        └── Node objects               ├── pointers table
                                       └── indexes
_reverseIndex: Map                   → query on pointers
_discoveryIndex: Map                 → query on nodes

API unchanged: get(), set(), has(), nameToAddr(), addrToName()
```

---

## Internal Node Types

| Prefix | Created By | Purpose |
|--------|-----------|---------|
| `_adj_` | adjacency | Word co-occurrence data |
| `_role_` | observe | Per-word role accumulation |
| `_pattern_` | observe | Structural pattern accumulation |
| `_discover_` | ruminate | Self-discovered chains |
| `_state_` | comprehend | Entity state in discourse |
| `_sig_` | explore | Primitive signatures |
| `_prof_` | explore | Primitive profiles |

---

## Files for Handoff

| File | Required | Description |
|------|----------|-------------|
| `intellon.js` | **YES** | The code. ~4763 lines. 457 tests. |
| `intellon_handoff_xb7.md` | **YES** | This document. |
| `intellon_context_spec.md` | **YES** | Context/provenance spec (Track 4). |
| `intellon_facts_full.txt` | **YES** | Sample fact file for testing. |
| `wordnet_to_facts.py` | if needed | Converts WordNet to fact files. |
| `extract_wordnet.py` | if needed | Generates WordNet JSON from NLTK. |
| `tag_corpus.py` | if needed | Generates tagged corpus from NLTK. |
| `intellon_v6_methodology.docx` | reference | v6 methodology (project reference). |

---

## How to Continue

1. Copy files to `C:\Users\jtwee\intellon\`
2. `node intellon.js --test` → verify 457/457
3. **Start Track 5:** `npm install better-sqlite3`
4. Build StorageEngine with same API as Trie
5. All 457 tests must pass identically against new storage
6. Replace `allNodes()` with targeted queries
7. Move pointers to own table
8. Verify at scale with full WordNet
9. Track 4 (context) drops in on pointer table

---

## User Context

- **Platform:** Windows, Node.js 24, Python 3.13
- **Local path:** `C:\Users\jtwee\intellon\`
- **Memory:** 1GB current, 24GB allocated
- **Storage:** 5TB available
- **Data sources:** WordNet (77K nodes), Wikipedia (22GB target), Gutenberg, tagged corpus
- **Key preferences:** Discussion before implementation. No workarounds. Failures are findings. A pointer is a pointer. If you're making it more complicated, you're patching a flaw. Complexity ≠ usability.
