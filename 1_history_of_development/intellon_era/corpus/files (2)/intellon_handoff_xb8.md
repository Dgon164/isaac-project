# Intellon xb.8 — Handoff Document

**Date:** April 5, 2026
**Version:** xb.8 (SQLite storage + sessions + hypotheses + provenance)
**Status:** 457 tests passing, all prior functionality intact
**Prior build:** xb.7 (457 tests, documented in intellon_handoff_xb7.md)

---

## What Changed (xb.7 → xb.8)

### Storage Migration (Track 5)
The in-memory Trie is gone. Replaced with StorageEngine backed by SQLite via `better-sqlite3`.

- **Write-through cache** preserves reference semantics — `get()` returns the same object, mutations without `set()` work exactly as before. Cache is the truth for active nodes. SQLite is the persistence layer.
- **`allNodes()` eliminated** — replaced with `entries()`, `filter()`, `find()`, `reduce()`, `countPointers()`. Every call site now says what it actually needs.
- **`_reverseIndex` and `_discoveryIndex` Maps** moved from IntellonSystem into StorageEngine as `addReverseEntry/getReverseEntries` and `addDiscoveryRef/getDiscoveryRefs`.
- **Persistent database** — `node intellon.js --db knowledge.db` writes to disk. Knowledge survives restarts. `sync()` persists all cached mutations. Auto-syncs on quit.
- **`loadFromDb()`** — on startup with `--db`, existing nodes load from disk into cache with full pointer and sense reconstruction, including reverse and discovery index rebuilds.

### Three-Layer Storage Architecture
1. **Main database** (`knowledge.db`) — permanent, on disk. Only written via `sync()` or `session end`. Never dirty during processing.
2. **Hibernate files** (`session_<name>.db`) — local SQLite files per session. `hibernateToFile()` dumps working space. `wakeFromFile()` restores. Disposable after `session end`.
3. **Working space** (cache only) — ephemeral. Dies with the process unless hibernated.

### Session Manager
Multiple independent work sessions, each with their own problem and working state.

| Command | What |
|---------|------|
| `session new <n>` | Start fresh session (auto-saves current if active) |
| `session save <n>` | Dump working space to session file |
| `session load <n>` | Restore session from file |
| `session switch <n>` | Save current, load target |
| `session end` | Curated commit — trust-filtered promotion to main DB, cleanup |
| `session list` | List session files with sizes and ages |
| `session status` | Show active session and working space stats |
| `session delete <n>` | Remove a session file |

Auto-saves active session on quit. Auto-syncs main DB on quit when `--db` is used.

**End session curated commit:** Only nodes at `working-standard` trust or above get promoted. New nodes go to `node-trial`. Existing nodes get touched. Low-trust nodes are discarded. Session file is deleted after commit.

### Hypothesis System
The system predicts relationships based on structural reasoning, then validates against incoming data.

`hypothesize <topic>` generates predictions:

1. **Inheritance** — siblings share a parent and a sibling has property X → topic probably has X too
2. **Parent property** — parent has property X → topic (as child) probably inherits X
3. **Contradiction resolution** — topic claims NOT X but parent connects to X → there must be a resolving mechanism
4. **Distinguishing property** — topic has X but parent doesn't → X either distinguishes topic or is undiscovered in siblings

Hypotheses are stored as `_hyp_<topic>_<n>` nodes with `createdBy: 'hypothesis'` at `working-trial` trust.

**Validation is automatic.** `_autoAssociate` fires on every `link()` call. When incoming data matches a hypothesis prediction exactly → trust bumps, status becomes `confirmed`. When a `not` pointer contradicts → status becomes `contradicted`, error flagged. When tangentially related data arrives → trust bumps slightly.

`hypotheses` and `hypotheses <topic>` show results: confirmed, contradicted, open.

**What this proves:** The system reasoned first, then encountered data. Timestamps prove the prediction preceded the confirmation. It's not memorization — it's structural inference validated by reality.

### Context & Provenance (Track 4)
Every pointer can carry a `sources` array tracking where the fact came from.

- `load file.txt` — auto-tags all pointers with filename as context
- `load file.txt --context wordnet` — explicit context label
- Duplicate pointers from different sources accumulate sources: `[biology, zoology]`
- `gather cat --source` — shows provenance on each pointer
- Trust correlates with independent source count — more sources = stronger fact

**`_loadContext` flow:** `loadFile()` sets `this._loadContext` before processing, `link()` reads it and attaches to new pointers or appends to existing pointers, `loadFile()` clears it after processing. Clean, no signature changes to `link()`.

---

## Key Design Decisions (xb.8)

**D: Write-through cache, not pure SQLite.** The Trie worked by reference — `get()` returned the actual stored object. Dozens of code paths mutate nodes after `get()` without calling `set()`. The cache preserves this. SQLite is the backing store. Later, partial caching (LRU eviction) can be added without changing the API.

**D: `allNodes()` must die.** Every replacement call site now declares what it needs. This is better code AND enables SQL optimization when partial caching arrives.

**D: Indexes belong to the storage engine.** `_reverseIndex` and `_discoveryIndex` are secondary indexes on the data. They should be managed alongside the data, not as separate Maps on the consumer.

**D: Main database is never dirty during processing.** All writes go to working space. Only `session end` and `sync` touch the main database. Crash mid-processing = no corruption.

**D: Hibernate is a file, not RAM.** Session state persists on the edge machine's disk. Crash and restart = reload hibernate file and resume. Multiple sessions hibernated simultaneously cost only disk space.

**D: Hypotheses use the same infrastructure as discoveries.** Same `_autoAssociate` validation, same trust lifecycle, same index for fast lookup. No new machinery — just a new `createdBy` type.

**D: Provenance via `_loadContext`, not parameter threading.** `link()` is called from 20+ places. Adding an `opts` parameter to all of them is invasive. Instance-level `_loadContext` is set/cleared by `loadFile()` and checked by `link()`. Clean, minimal change surface.

---

## Files for Handoff

| File | Required | Description |
|------|----------|-------------|
| `intellon.js` | **YES** | Main system. ~5204 lines. 457 tests. |
| `storage_engine.js` | **YES** | SQLite-backed StorageEngine. ~548 lines. |
| `intellon_node.js` | **YES** | Node class (shared dependency). ~17 lines. |
| `intellon_handoff_xb8.md` | **YES** | This document. |
| `intellon_context_spec.md` | reference | Original Track 4 spec (now implemented). |
| `intellon_track5_proposal_v2.md` | reference | Storage migration proposal with session architecture. |
| `intellon_facts_full.txt` | **YES** | Sample fact file for testing. |
| `wordnet_to_facts.py` | if needed | Converts WordNet to fact files. |
| `extract_wordnet.py` | if needed | Generates WordNet JSON from NLTK. |
| `tag_corpus.py` | if needed | Generates tagged corpus from NLTK. |

---

## How to Continue

1. Copy files to `C:\Users\jtwee\intellon\`
2. `npm install better-sqlite3`
3. `node intellon.js --test` → verify 457/457
4. `node intellon.js --db knowledge.db` → persistent mode
5. `load intellon_facts.txt` → test provenance tagging
6. `gather dog --source` → verify provenance shows
7. `hypothesize cat` → test hypothesis generation
8. Add more facts → watch hypotheses validate
9. `session new geology` → test session workflow
10. `session end` → test curated commit

### Scale Testing
```bash
python wordnet_to_facts.py --max 5000 --max-senses 3 --no-multi-word
node intellon.js --db knowledge.db
load intellon_facts.txt --context wordnet
sync
quit
# Restart — data persists:
node intellon.js --db knowledge.db
gather dog --source
```

---

## What's Next

### FIRST PRIORITY: Scale Verification
- Load full WordNet (77K nodes) with `--db`
- Benchmark: load time, query time, hibernate/wake, session end
- Verify provenance tags survive sync/reload cycle
- Test multiple sessions switching on same knowledge base

### SECOND PRIORITY: Track 3 Continuation
- Feed tagged corpus at volume
- Let patterns mature past scaffold
- Enable parse gating for all input once patterns are reliable
- Eventually remove Phase 10 bodge

### THIRD PRIORITY: Hypothesis Refinement
- Track prediction accuracy over time (% confirmed vs contradicted)
- Use prediction history to weight future hypotheses (inheritance predictions succeed 60% of the time → adjust confidence)
- Generate hypotheses automatically before each `loadFile()` batch
- Cross-session hypothesis tracking — predictions from one session validated by another

### From Prior Handoffs (Still Pending)
- Review command for discoveries
- Ruminate on idle/timer
- Store exploration observations as nodes/pointers

---

## Architecture

### Storage Layers
```
                    ┌─────────────────┐
                    │   IntellonSystem │
                    │                 │
                    │  ns ──→ StorageEngine('node')
                    │           │ _cache (Map)
                    │           │ _reverseIdx (Map)
                    │           │ _discoveryIdx (Map)
                    │           └──→ SQLite (knowledge.db or :memory:)
                    │
                    │  ws ──→ StorageEngine('working')
                    │           │ _cache (Map)
                    │           └──→ SQLite (shared db, space='working')
                    │
                    │  Session files: session_<name>.db (standalone SQLite)
                    └─────────────────┘
```

### Hypothesis Flow
```
hypothesize(topic)
  │
  ├── gather(topic) — what do I know?
  │
  ├── find parents (is_a pointers)
  │     ├── find siblings (who else is_a parent?)
  │     │     └── sibling has X, topic doesn't → INHERIT prediction
  │     └── parent has X, topic doesn't → PARENT prediction
  │
  ├── find contradictions (not pointers vs parent properties)
  │     └── topic NOT X but parent connects to X → RESOLVE prediction
  │
  ├── find distinguishing properties (topic has X, parent doesn't)
  │     └── X unique to topic or undiscovered in siblings → DISTINGUISH
  │
  └── store as _hyp_ nodes, index for _autoAssociate
        │
        └── incoming data triggers validation automatically
              ├── exact match → CONFIRMED (trust bumps)
              ├── NOT match → CONTRADICTED (error flagged)
              └── tangential → trust bump (data touches area)
```

### Provenance Flow
```
loadFile('facts.txt', --context 'wordnet')
  │
  ├── this._loadContext = 'wordnet'
  │
  ├── for each statement:
  │     exec(stmt) → link(source, rel, target)
  │       │
  │       ├── new pointer: { type, to, sources: ['wordnet'] }
  │       └── duplicate pointer: append 'wordnet' to sources array
  │
  └── this._loadContext = null
```

---

## Test Summary

```
457 tests: 457 passed, 0 failed

All tests from xb.7 unchanged and passing.
No new test sections added (hypothesis and provenance tested manually).
```

---

## User Context

- **Platform:** Windows, Node.js 24, Python 3.13
- **Local path:** `C:\Users\jtwee\intellon\`
- **Memory:** 1GB current, 24GB allocated
- **Storage:** 5TB available
- **Dependencies:** `better-sqlite3` (npm install)
- **Data sources:** WordNet (77K nodes), Wikipedia (22GB target), Gutenberg, tagged corpus
- **Key preferences:** Discussion before implementation. No workarounds. Failures are findings. A pointer is a pointer. Complexity ≠ usability.
