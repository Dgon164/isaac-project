# Track 5: Storage Migration — Proposal v2

**Date:** April 5, 2026
**Baseline:** xb.7 (457 tests, 4763 lines)
**Goal:** Replace in-memory Trie with SQLite. Session-based parallel compute. Wikipedia-scale capacity.

---

## The Problem

The Trie is a physical tree of Maps holding Node objects. Every node, every pointer, every sense lives in JavaScript heap memory. This works at 77K nodes (7.4 seconds, ~1GB). It cannot work at Wikipedia scale (50-100M relationships, 22GB raw text).

Three specific bottlenecks:

1. **allNodes()** — walks the entire tree to produce a flat array. Called 15+ places: stats, nodes, rels, housekeeping, selectSeed, showPatterns, showDiscoveries, test assertions. Every call is O(n) over the full graph.

2. **Pointer storage** — pointers live as arrays on Node objects. Finding "who points to X" requires either the `_reverseIndex` Map or a full scan. The reverse index is maintained manually in `link()` and is not persisted.

3. **Memory ceiling** — JavaScript Maps carry overhead per entry. At 77K nodes the system uses ~1GB. At 1M nodes it would need ~13GB of heap just for the trie structure.

---

## Architecture: Three-Layer Storage

### Layer 1: Main Database (`knowledge.db`)

The permanent, canonical knowledge base. Lives on disk. Can grow to hundreds of gigabytes. Shared by all sessions as read-only infrastructure during processing. Only written to during end session — a curated commit of verified findings.

This file is never dirty. If every edge machine catches fire, `knowledge.db` is intact. It represents what the system knows — tested, verified, trusted.

Multiple processes can read it simultaneously. Writes are serialized through SQLite's native write lock — one end session commits at a time.

### Layer 2: Hibernate Files (`session_<name>.db`)

Local SQLite files, one per session. Live on the edge machine's disk. When a session hibernates, its entire in-memory working space dumps to this file. When the session wakes, the file loads back into RAM and processing resumes.

These files are the session's checkpoint. The edge machine can crash, reboot, lose power — the hibernate file survives. The session reloads and picks up where it left off. Compute time is lost only back to the last hibernate, not from the beginning.

Hibernate files are disposable. Once a session runs end session and commits its findings to the main database, the hibernate file can be deleted. It served its purpose.

Each session has its own file: `session_geology.db`, `session_grammar.db`, `session_engineering.db`. Dozens can exist on disk simultaneously. They cost nothing when not loaded.

### Layer 3: Working Space (`:memory:`)

Pure RAM. The active scratchpad for a running session. Created via SQLite's `ATTACH DATABASE ':memory:' AS working`. Never touches disk during normal operation. Fast reads, fast writes, zero I/O overhead.

When the session hibernates, this space dumps to the hibernate file. When the process ends or the session is shelved, this space simply ceases to exist. No cleanup, no fragmentation, no disk scrubbing.

### How They Interact

```
Boot
  │
  ├── Open knowledge.db (read-only during processing)
  │
  ├── Check for hibernate file
  │     ├── Found → load into :memory:, resume processing
  │     └── Not found → fresh :memory:, start new session
  │
  ├── Process (read knowledge.db, write to :memory:)
  │
  ├── Hibernate (periodic or on demand)
  │     └── Dump :memory: → session_<name>.db on local disk
  │
  ├── End Session (when work is complete)
  │     ├── Review working space contents
  │     ├── Evaluate significance (trust, reinforcement, novelty)
  │     ├── Curate findings — only meaningful results survive
  │     ├── Batch commit to knowledge.db
  │     ├── Produce session summary (what changed and why)
  │     └── Delete hibernate file
  │
  └── Shelve / Switch
        ├── Hibernate current session → dumps to local file, drops :memory:
        └── Wake different session → loads its hibernate file into :memory:
```

---

## Session Manager

The session manager controls which sessions are active, hibernated, or completed. It is the orchestration layer above the storage engine.

### Session States

| State | RAM | Disk | Main DB | Description |
|-------|-----|------|---------|-------------|
| **Active** | `:memory:` loaded | Hibernate file updated periodically | Read-only | Currently processing |
| **Hibernated** | Nothing | Hibernate file on disk | Not accessed | Shelved, can resume |
| **Completed** | Nothing | Hibernate file deleted | Findings committed | Done, results in main DB |
| **New** | Empty `:memory:` | No file yet | Read-only | Fresh start |

### Commands

```
session new <name>          Create new session, attach empty :memory:
session list                Show all sessions (active, hibernated, completed)
session switch <name>       Hibernate current, wake target
session hibernate           Dump current :memory: to session file
session end                 Curate, commit findings to main DB, cleanup
session status              Show current session's stats (nodes, pointers, runtime)
session delete <name>       Delete a hibernated session's file (discard work)
```

### Parallel Sessions

Multiple sessions can be active simultaneously if RAM allows. Each gets its own `:memory:` attach with a unique alias (`working_geology`, `working_grammar`). They all read from the same `knowledge.db`. They never write to each other's space.

On a machine with 24GB allocated:
- Main database pages cached: ~2-4GB
- Each active session: ~1-2GB depending on working set size
- Practical limit: 8-12 active sessions, unlimited hibernated

When RAM gets tight, the session manager hibernates the least recently active session automatically. Or the user shelves sessions manually.

### End Session: The Curated Commit

End session is not a dump. It's a review. The session has been processing — maybe thousands of Wikipedia pages, generating working nodes, recording observations, building temporary chains. Most of that is scaffolding. The valuable output is:

1. **New facts** — nodes and pointers that don't exist in the main database, with sufficient trust (promoted past working-trial at minimum)
2. **Reinforced facts** — existing facts in the main database that the session encountered independently, bumping their source count (Track 4 provenance)
3. **Discoveries** — cross-domain connections found by ruminate during the session
4. **Learned patterns** — grammar patterns, role observations that matured past scaffold during the session

The end session process:
1. Walk all working space nodes
2. Filter by trust level — only working-standard or above survive
3. Check against main database for duplicates and reinforcements
4. Batch commit new nodes and pointers in a single transaction
5. Record source/provenance tags on all committed pointers (Track 4)
6. Generate a session summary: what was processed, what was learned, what was committed
7. Drop the `:memory:` attach, delete the hibernate file

The session summary is itself stored as a node in the main database — a record of what happened, traceable.

---

## Schema

### Main Database (`knowledge.db`)

```sql
CREATE TABLE nodes (
  address     TEXT PRIMARY KEY,
  name        TEXT NOT NULL,
  value       TEXT,              -- JSON-serialized
  trust       TEXT NOT NULL,
  createdBy   TEXT,
  accessCount INTEGER DEFAULT 0,
  timestamp   INTEGER,
  lastAccess  INTEGER,
  mode        TEXT,
  macro       TEXT               -- JSON-serialized if present
);

CREATE TABLE pointers (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  source_addr TEXT NOT NULL,
  type        TEXT NOT NULL,
  target_addr TEXT NOT NULL,
  sources     TEXT,              -- JSON array for Track 4 provenance
  UNIQUE(source_addr, type, target_addr)
);

CREATE TABLE senses (
  parent_addr TEXT NOT NULL,
  sense_num   INTEGER NOT NULL,
  address     TEXT NOT NULL,
  name        TEXT,
  value       TEXT,
  trust       TEXT,
  createdBy   TEXT,
  accessCount INTEGER DEFAULT 0,
  timestamp   INTEGER,
  lastAccess  INTEGER,
  mode        TEXT,
  macro       TEXT,
  PRIMARY KEY (parent_addr, sense_num)
);

CREATE TABLE sessions (
  name        TEXT PRIMARY KEY,
  status      TEXT NOT NULL,     -- 'active', 'hibernated', 'completed'
  created     INTEGER,
  lastActive  INTEGER,
  description TEXT,
  summary     TEXT               -- JSON: end session report
);

CREATE INDEX idx_pointers_source ON pointers(source_addr);
CREATE INDEX idx_pointers_target ON pointers(target_addr);
CREATE INDEX idx_pointers_type ON pointers(type);
CREATE INDEX idx_nodes_trust ON nodes(trust);
CREATE INDEX idx_nodes_createdBy ON nodes(createdBy);
CREATE INDEX idx_nodes_name ON nodes(name);
```

### Working Space (`:memory:` or hibernate file)

Same schema as main database nodes/pointers/senses tables, no sessions table. When hibernating, the in-memory tables are copied to the session file. When waking, the session file's tables are loaded into the `:memory:` attach.

---

## StorageEngine API

The StorageEngine wraps all three layers. IntellonSystem calls the same methods it always has — it doesn't know whether it's hitting RAM or disk.

### Core Methods (Same as Trie)

| Method | Behavior |
|--------|----------|
| `get(addr)` | Check working space first, then main DB. Reconstruct Node with pointers attached. |
| `set(addr, node)` | Write to working space (:memory:). Never writes to main DB directly. |
| `has(addr)` | Check working space, then main DB. |
| `parent(addr)` | Pure string operation — unchanged. |
| `children(addr)` | Query both spaces, merge results. |
| `nameToAddr(name)` | Pure function — unchanged. |
| `addrToName(addr)` | Pure function — unchanged. |

### Query Methods (Replace allNodes)

| Method | Replaces | Query |
|--------|----------|-------|
| `findByPrefix(prefix)` | `allNodes().filter(name starts with)` | `WHERE name LIKE ? \|\| '%'` |
| `findByCreator(type)` | `allNodes().filter(createdBy)` | `WHERE createdBy = ?` |
| `findNodesWithPointers()` | `allNodes().filter(pointers.length)` | `JOIN pointers` |
| `findSeedCandidates()` | `selectSeed()` scoring loop | `GROUP BY source_addr HAVING COUNT(DISTINCT type) >= 2` |
| `countPointers()` | `allNodes().reduce(sum pointers)` | `SELECT COUNT(*) FROM pointers` |
| `findKnowledgeNodes()` | `allNodes().filter(address has dot)` | `WHERE address LIKE '%.%'` |
| `reverseQuery(addr)` | `_reverseIndex.get(addr)` | `SELECT * FROM pointers WHERE target_addr = ?` |

### Session Methods

| Method | Behavior |
|--------|----------|
| `hibernate(name)` | Copy all `:memory:` tables to `session_<name>.db` |
| `wake(name)` | Load `session_<name>.db` tables into `:memory:` |
| `endSession(name)` | Curate, batch commit to main DB, cleanup |
| `newSession(name)` | Fresh `:memory:` attach |
| `switchSession(from, to)` | `hibernate(from)` then `wake(to)` |
| `listSessions()` | Query sessions table in main DB |

### Ingestion

All writes during processing go to the working space (`:memory:`). The `loadFile()` function wraps all inserts in a single transaction for speed:

```javascript
db.prepare('BEGIN').run();
// ... 77,000 inserts ...
db.prepare('COMMIT').run();
```

Individual REPL commands auto-commit.

---

## Implementation Steps

### Step 1: StorageEngine class

Build `StorageEngine` wrapping `better-sqlite3`. Implements the core API (get, set, has, parent, children, nameToAddr, addrToName). Single database file, no sessions yet. Node objects reconstructed with pointers on `get()`. Pointers written to their own table on `set()`.

**Validation gate:** 457 tests pass with zero test code changes.

### Step 2: Replace allNodes() call sites

Every `allNodes()` call replaced with a specific query method. Map each call site to the query it actually needs. Remove `allNodes()` from the codebase entirely.

**Validation gate:** 457 tests still pass.

### Step 3: Remove _reverseIndex and _discoveryIndex

Both Maps removed from IntellonSystem. Reverse lookups become `SELECT FROM pointers WHERE target_addr = ?`. Discovery lookups become name-based queries on discovery nodes.

**Validation gate:** 457 tests still pass.

### Step 4: Three-layer storage

Split single database into the three-layer model: `knowledge.db` on disk, `:memory:` attach for working space, hibernate files for session persistence. The `ns` and `ws` Tries in IntellonSystem both route through StorageEngine — `ns` reads/writes main DB, `ws` reads/writes `:memory:`.

**Validation gate:** 457 tests still pass. Hibernate/wake cycle preserves state.

### Step 5: Session manager

Build the session commands: new, list, switch, hibernate, end, status, delete. End session implements the curated commit — trust filtering, duplicate detection, batch write, summary generation.

**Validation gate:** Can create a session, process data, hibernate, wake, switch sessions, and end session with findings committed to main DB.

### Step 6: Scale verification

1. Load full WordNet (77K nodes) in a session
2. Run ruminate at scale
3. End session — verify curated commit
4. Start new session, verify it can read WordNet data from main DB
5. Run multiple sessions simultaneously
6. Benchmark: load time, query time, hibernate/wake time, end session time

### Step 7: Track 4 hook

The `sources` column on the pointers table is already there. Wire `link()` to pass source labels through. Wire `loadFile()` to tag all facts with file source. Wire `gather --context` to filter by source. This is cleanup — the infrastructure is already in place from Step 1.

---

## What Changes in IntellonSystem

1. **Constructor:** `this.ns = new Trie('node')` and `this.ws = new Trie('working')` → `this.storage = new StorageEngine(dbPath)` with methods that route to the correct layer
2. **`_reverseIndex` and `_discoveryIndex`:** Removed entirely
3. **`allNodes()` callers:** Replaced with specific query calls
4. **`link()`:** Reverse index maintenance removed (database handles it)
5. **`_autoAssociate()`:** Discovery index lookups become database queries
6. **`hibernate()` / `wake()`:** Now session-level operations — dump/load `:memory:` to/from file
7. **New:** `endSession()` — curated commit path
8. **New:** Session management commands in `exec()`

Everything else — `gather`, `relate`, `compose`, `ruminate`, `comprehend`, the unified pipeline — stays the same.

---

## Risk Assessment

**Low risk:** The core API contract is clear and well-tested. 457 tests define exact behavior. If tests pass, migration is correct.

**Medium risk:** Performance characteristics change. In-memory Map is O(1). SQLite indexed lookup is O(log n) with disk I/O. Mitigation: working space is `:memory:` so hot-path operations stay in RAM. Main DB reads go through SQLite's page cache.

**Medium risk:** Transaction discipline. `link()` does multiple operations that should be atomic. Missing transactions = slow writes and potential inconsistency. Mitigation: explicit transaction wrapping in all multi-step operations.

**Low risk:** `better-sqlite3` is synchronous — no async refactoring needed.

**Low risk:** Session isolation. Sessions share `knowledge.db` read-only and have independent working spaces. No cross-contamination possible by design.

---

## What This Does NOT Do

- Does not change any algorithm or discovery logic
- Does not change the address scheme
- Does not change the CLI or command interface (adds session commands)
- Does not require changes to the existing 457 tests
- Does not affect the v6 Machine methodology document
- Does not implement Track 4 fully (just puts the infrastructure in place)
- Does not build a distributed system (sessions are local to one machine, main DB is a single file)

---

## Success Criteria

1. **457/457 tests pass** with zero test code changes
2. **allNodes() is gone** from the codebase entirely
3. **_reverseIndex and _discoveryIndex Maps are gone**
4. **WordNet loads** in a session at equal or better speed
5. **Hibernate/wake cycle** preserves session state across process restarts
6. **Session switching** works — hibernate one, wake another, no data loss
7. **End session** curates findings and commits to main DB cleanly
8. **Multiple sessions** can run simultaneously without interference
9. **Main database is never dirty** — only end session writes to it
10. **Track 4 ready** — pointers table has sources column

---

## What This Proves

Current AI loads one massive model, runs one inference, throws away all intermediate work. This architecture runs persistent workers that:

- Accumulate knowledge independently across parallel sessions
- Share a common knowledge base without locking conflicts
- Can be paused, resumed, shelved, and restarted at will
- Commit only verified findings to permanent storage
- Run on commodity hardware — no GPU cluster, no 700GB model weights
- Scale by adding sessions, not by adding hardware

Dozens of sessions, each working different problems, sharing one growing knowledge base, on one machine with 24GB of RAM and a 5TB drive. That's the proof of concept.
