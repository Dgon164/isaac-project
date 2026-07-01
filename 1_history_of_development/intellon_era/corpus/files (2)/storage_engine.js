const Database = require('better-sqlite3');
const Node = require('./intellon_node.js');

// StorageEngine — drop-in replacement for Trie
// Write-through cache preserves reference semantics (get returns same object)
// SQLite backing for persistence, indexed queries, and future partial caching

class StorageEngine {
  static _db = null;
  static _stmts = {};

  static init(dbPath = ':memory:') {
    if (StorageEngine._db) return;
    const db = new Database(dbPath);
    db.pragma('journal_mode = WAL');
    db.pragma('synchronous = NORMAL');

    db.exec(`
      CREATE TABLE IF NOT EXISTS nodes (
        address     TEXT NOT NULL,
        space       TEXT NOT NULL,
        name        TEXT NOT NULL,
        value       TEXT,
        trust       TEXT NOT NULL,
        createdBy   TEXT,
        accessCount INTEGER DEFAULT 0,
        timestamp   INTEGER,
        lastAccess  INTEGER,
        mode        TEXT,
        macro       TEXT,
        errors      TEXT,
        PRIMARY KEY (address, space)
      );

      CREATE TABLE IF NOT EXISTS pointers (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        source_addr TEXT NOT NULL,
        source_space TEXT NOT NULL,
        type        TEXT NOT NULL,
        target_addr TEXT NOT NULL,
        sources     TEXT,
        UNIQUE(source_addr, source_space, type, target_addr)
      );

      CREATE TABLE IF NOT EXISTS senses (
        parent_addr  TEXT NOT NULL,
        parent_space TEXT NOT NULL,
        sense_num    INTEGER NOT NULL,
        address      TEXT NOT NULL,
        name         TEXT,
        value        TEXT,
        trust        TEXT,
        createdBy    TEXT,
        accessCount  INTEGER DEFAULT 0,
        timestamp    INTEGER,
        lastAccess   INTEGER,
        mode         TEXT,
        macro        TEXT,
        errors       TEXT,
        PRIMARY KEY (parent_addr, parent_space, sense_num)
      );

      CREATE TABLE IF NOT EXISTS sense_pointers (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        parent_addr   TEXT NOT NULL,
        parent_space  TEXT NOT NULL,
        sense_num     INTEGER NOT NULL,
        type          TEXT NOT NULL,
        target_addr   TEXT NOT NULL,
        UNIQUE(parent_addr, parent_space, sense_num, type, target_addr)
      );

      CREATE INDEX IF NOT EXISTS idx_pointers_source ON pointers(source_addr, source_space);
      CREATE INDEX IF NOT EXISTS idx_pointers_target ON pointers(target_addr);
      CREATE INDEX IF NOT EXISTS idx_pointers_type ON pointers(type);
      CREATE INDEX IF NOT EXISTS idx_nodes_trust ON nodes(trust);
      CREATE INDEX IF NOT EXISTS idx_nodes_createdBy ON nodes(createdBy);
      CREATE INDEX IF NOT EXISTS idx_nodes_space ON nodes(space);
      CREATE INDEX IF NOT EXISTS idx_nodes_name ON nodes(name);
      CREATE INDEX IF NOT EXISTS idx_senses_parent ON senses(parent_addr, parent_space);
    `);

    StorageEngine._db = db;
    StorageEngine._prepareStatements(db);
  }

  static _prepareStatements(db) {
    const s = {};
    s.upsertNode = db.prepare(`INSERT OR REPLACE INTO nodes (address, space, name, value, trust, createdBy, accessCount, timestamp, lastAccess, mode, macro, errors) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`);
    s.getNode = db.prepare('SELECT * FROM nodes WHERE address = ? AND space = ?');
    s.hasNode = db.prepare('SELECT 1 FROM nodes WHERE address = ? AND space = ?');
    s.countNodes = db.prepare('SELECT COUNT(*) as cnt FROM nodes WHERE space = ?');
    s.getPointers = db.prepare('SELECT type, target_addr, sources FROM pointers WHERE source_addr = ? AND source_space = ?');
    s.deletePointers = db.prepare('DELETE FROM pointers WHERE source_addr = ? AND source_space = ?');
    s.insertPointer = db.prepare('INSERT OR IGNORE INTO pointers (source_addr, source_space, type, target_addr, sources) VALUES (?, ?, ?, ?, ?)');
    s.getSenses = db.prepare('SELECT * FROM senses WHERE parent_addr = ? AND parent_space = ?');
    s.upsertSense = db.prepare(`INSERT OR REPLACE INTO senses (parent_addr, parent_space, sense_num, address, name, value, trust, createdBy, accessCount, timestamp, lastAccess, mode, macro, errors) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`);
    s.deleteSenses = db.prepare('DELETE FROM senses WHERE parent_addr = ? AND parent_space = ?');
    s.deleteSensePointersForSense = db.prepare('DELETE FROM sense_pointers WHERE parent_addr = ? AND parent_space = ? AND sense_num = ?');
    s.insertSensePointer = db.prepare('INSERT OR IGNORE INTO sense_pointers (parent_addr, parent_space, sense_num, type, target_addr) VALUES (?, ?, ?, ?, ?)');
    s.deleteAllNodes = db.prepare('DELETE FROM nodes WHERE space = ?');
    s.deleteAllPointers = db.prepare('DELETE FROM pointers WHERE source_space = ?');
    s.deleteAllSenses = db.prepare('DELETE FROM senses WHERE parent_space = ?');
    s.deleteAllSensePointers = db.prepare('DELETE FROM sense_pointers WHERE parent_space = ?');
    StorageEngine._stmts = s;
  }

  static reset() {
    if (StorageEngine._db) {
      StorageEngine._db.close();
      StorageEngine._db = null;
      StorageEngine._stmts = {};
    }
  }

  constructor(name) {
    this.name = name;
    this.space = name;
    this._cache = new Map();
    this._count = 0;
    this._reverseIdx = new Map();   // targetAddr → [{sourceAddr, sourceName, rel}]
    this._discoveryIdx = new Map(); // word → Set<discovery_addr>
    if (!StorageEngine._db) StorageEngine.init();
  }

  get count() { return this._count; }

  // ---- Index maintenance ----
  addReverseEntry(targetAddr, sourceAddr, sourceName, rel) {
    if (!this._reverseIdx.has(targetAddr)) this._reverseIdx.set(targetAddr, []);
    this._reverseIdx.get(targetAddr).push({ sourceAddr, sourceName, rel });
  }

  getReverseEntries(targetAddr) {
    return this._reverseIdx.get(targetAddr) || [];
  }

  addDiscoveryRef(word, addr) {
    if (!this._discoveryIdx.has(word)) this._discoveryIdx.set(word, new Set());
    this._discoveryIdx.get(word).add(addr);
  }

  getDiscoveryRefs(word) {
    return this._discoveryIdx.get(word) || null;
  }

  // ---- Pure string functions (unchanged from Trie) ----
  nameToAddr(n) { return Array.from(n).map(c => c.charCodeAt(0)).join('.'); }
  addrToName(a) { return String(a).split('.').map(n => String.fromCharCode(Number(n))).join(''); }
  parent(a) { const s = String(a).split('.'); return s.length <= 1 ? null : s.slice(0, -1).join('.'); }

  // ---- Children ----
  children(a) {
    const prefix = a + '.';
    const depth = String(a).split('.').length + 1;
    const results = [];
    for (const [addr] of this._cache) {
      if (addr.startsWith(prefix) && addr.split('.').length === depth) {
        results.push(addr);
      }
    }
    return results;
  }

  // ---- Serialization ----
  _serializeValue(v) {
    if (v === null || v === undefined) return null;
    return JSON.stringify(v);
  }
  _deserializeValue(s) {
    if (s === null || s === undefined) return null;
    try { return JSON.parse(s); } catch { return s; }
  }

  // ---- set: store Node in cache + SQLite ----
  set(a, n) {
    const isNew = !this._cache.has(a);
    this._cache.set(a, n);
    if (isNew) this._count++;
    this._persistNode(a, n);
    return n;
  }

  _persistNode(a, n) {
    const s = StorageEngine._stmts;
    const db = StorageEngine._db;

    db.transaction(() => {
      s.upsertNode.run(
        a, this.space, n.name,
        this._serializeValue(n.value),
        n.context.trust,
        n.context.createdBy,
        n.context.accessCount,
        n.context.timestamp,
        n.context.lastAccess,
        n.mode || null,
        n.macro ? (typeof n.macro === 'string' ? n.macro : JSON.stringify(n.macro)) : null,
        n.context.errors && n.context.errors.length > 0 ? JSON.stringify(n.context.errors) : null
      );

      s.deletePointers.run(a, this.space);
      for (const p of n.pointers) {
        s.insertPointer.run(a, this.space, p.type, p.to, p.sources ? JSON.stringify(p.sources) : null);
      }

      s.deleteSenses.run(a, this.space);
      for (const [num, senseNode] of n.senses) {
        s.upsertSense.run(
          a, this.space, num, senseNode.address, senseNode.name,
          this._serializeValue(senseNode.value),
          senseNode.context.trust,
          senseNode.context.createdBy,
          senseNode.context.accessCount,
          senseNode.context.timestamp,
          senseNode.context.lastAccess,
          senseNode.mode || null,
          senseNode.macro ? (typeof senseNode.macro === 'string' ? senseNode.macro : JSON.stringify(senseNode.macro)) : null,
          senseNode.context.errors && senseNode.context.errors.length > 0 ? JSON.stringify(senseNode.context.errors) : null
        );
        s.deleteSensePointersForSense.run(a, this.space, num);
        for (const p of senseNode.pointers) {
          s.insertSensePointer.run(a, this.space, num, p.type, p.to);
        }
      }
    })();
  }

  // ---- get: return cached reference ----
  get(a) {
    return this._cache.get(a) || null;
  }

  // ---- has: check cache ----
  has(a) {
    return this._cache.has(a);
  }

  // ---- Query methods (replace allNodes) ----

  // All entries as array [{address, node}, ...]
  entries() {
    const o = [];
    for (const [address, node] of this._cache) {
      o.push({ address, node });
    }
    return o;
  }

  // Iterate all entries, calling fn({address, node}) for each
  forEach(fn) {
    for (const [address, node] of this._cache) {
      fn({ address, node });
    }
  }

  // Filter entries by predicate, returns [{address, node}, ...]
  filter(predicate) {
    const results = [];
    for (const [address, node] of this._cache) {
      const entry = { address, node };
      if (predicate(entry)) results.push(entry);
    }
    return results;
  }

  // Find single entry by predicate
  find(predicate) {
    for (const [address, node] of this._cache) {
      const entry = { address, node };
      if (predicate(entry)) return entry;
    }
    return null;
  }

  // Reduce over all entries
  reduce(fn, init) {
    let acc = init;
    for (const [address, node] of this._cache) {
      acc = fn(acc, { address, node });
    }
    return acc;
  }

  // Count total pointers across all nodes in this space
  countPointers() {
    let total = 0;
    for (const [, node] of this._cache) {
      total += node.pointers.length;
    }
    return total;
  }

  // ---- Flush: clear this space entirely ----
  flush() {
    this._cache.clear();
    this._reverseIdx.clear();
    this._discoveryIdx.clear();
    this._count = 0;
    const s = StorageEngine._stmts;
    StorageEngine._db.transaction(() => {
      s.deleteAllSensePointers.run(this.space);
      s.deleteAllSenses.run(this.space);
      s.deleteAllPointers.run(this.space);
      s.deleteAllNodes.run(this.space);
    })();
  }

  // ---- Sync: persist all cached nodes to SQLite ----
  sync() {
    StorageEngine._db.transaction(() => {
      for (const [addr, node] of this._cache) {
        this._persistNode(addr, node);
      }
    })();
  }

  // ---- Load: populate cache from existing SQLite data ----
  // Call after init() when opening a persistent database
  loadFromDb() {
    const db = StorageEngine._db;
    const rows = db.prepare('SELECT * FROM nodes WHERE space = ?').all(this.space);
    if (rows.length === 0) return 0;

    const allPtrs = db.prepare('SELECT source_addr, type, target_addr, sources FROM pointers WHERE source_space = ?').all(this.space);
    const ptrMap = new Map();
    for (const p of allPtrs) {
      if (!ptrMap.has(p.source_addr)) ptrMap.set(p.source_addr, []);
      ptrMap.get(p.source_addr).push(p);
    }

    const allSenseRows = db.prepare('SELECT * FROM senses WHERE parent_space = ?').all(this.space);
    const senseMap = new Map();
    for (const sr of allSenseRows) {
      if (!senseMap.has(sr.parent_addr)) senseMap.set(sr.parent_addr, []);
      senseMap.get(sr.parent_addr).push(sr);
    }

    const allSPtrs = db.prepare('SELECT * FROM sense_pointers WHERE parent_space = ?').all(this.space);
    const sptrMap = new Map();
    for (const sp of allSPtrs) {
      const key = `${sp.parent_addr}:${sp.sense_num}`;
      if (!sptrMap.has(key)) sptrMap.set(key, []);
      sptrMap.get(key).push(sp);
    }

    for (const row of rows) {
      const node = new Node(row.address, row.name, {
        value: this._deserializeValue(row.value),
        trust: row.trust,
        createdBy: row.createdBy,
        mode: row.mode,
        macro: row.macro ? (row.macro.startsWith('{') || row.macro.startsWith('[') ? JSON.parse(row.macro) : row.macro) : null,
      });
      node.context.accessCount = row.accessCount || 0;
      node.context.timestamp = row.timestamp;
      node.context.lastAccess = row.lastAccess;
      node.context.errors = row.errors ? JSON.parse(row.errors) : [];

      // Load pointers
      const ptrs = ptrMap.get(row.address) || [];
      node.pointers = ptrs.map(p => ({
        type: p.type, to: p.target_addr,
        ...(p.sources ? { sources: JSON.parse(p.sources) } : {})
      }));

      // Rebuild reverse index from pointers
      for (const p of node.pointers) {
        this.addReverseEntry(p.to, row.address, row.name, p.type);
      }

      // Load senses
      const senseRows = senseMap.get(row.address) || [];
      for (const sr of senseRows) {
        const sn = new Node(sr.address, sr.name, {
          value: this._deserializeValue(sr.value),
          trust: sr.trust, createdBy: sr.createdBy, mode: sr.mode, macro: sr.macro || null,
        });
        sn.context.accessCount = sr.accessCount || 0;
        sn.context.timestamp = sr.timestamp;
        sn.context.lastAccess = sr.lastAccess;
        sn.context.errors = sr.errors ? JSON.parse(sr.errors) : [];
        sn.pointers = (sptrMap.get(`${row.address}:${sr.sense_num}`) || [])
          .map(p => ({ type: p.type, to: p.target_addr }));
        node.senses.set(sr.sense_num, sn);
      }

      // Rebuild discovery index
      if (row.createdBy === 'self-discover' && node.value && node.value.chain) {
        const chainWords = new Set();
        if (node.value.source) chainWords.add(node.value.source);
        if (node.value.terminus) chainWords.add(node.value.terminus);
        for (const w of chainWords) {
          this.addDiscoveryRef(w, row.address);
        }
      }

      this._cache.set(row.address, node);
      this._count++;
    }

    return rows.length;
  }

  // ---- Hibernate: dump this space to a standalone SQLite file ----
  hibernateToFile(filepath) {
    const sessionDb = new Database(filepath);
    sessionDb.pragma('journal_mode = WAL');

    sessionDb.exec(`
      CREATE TABLE nodes (
        address TEXT PRIMARY KEY, name TEXT NOT NULL, value TEXT,
        trust TEXT NOT NULL, createdBy TEXT, accessCount INTEGER DEFAULT 0,
        timestamp INTEGER, lastAccess INTEGER, mode TEXT, macro TEXT, errors TEXT
      );
      CREATE TABLE pointers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_addr TEXT NOT NULL, type TEXT NOT NULL, target_addr TEXT NOT NULL, sources TEXT,
        UNIQUE(source_addr, type, target_addr)
      );
      CREATE TABLE senses (
        parent_addr TEXT NOT NULL, sense_num INTEGER NOT NULL,
        address TEXT NOT NULL, name TEXT, value TEXT, trust TEXT, createdBy TEXT,
        accessCount INTEGER DEFAULT 0, timestamp INTEGER, lastAccess INTEGER,
        mode TEXT, macro TEXT, errors TEXT,
        PRIMARY KEY (parent_addr, sense_num)
      );
      CREATE TABLE sense_pointers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        parent_addr TEXT NOT NULL, sense_num INTEGER NOT NULL,
        type TEXT NOT NULL, target_addr TEXT NOT NULL,
        UNIQUE(parent_addr, sense_num, type, target_addr)
      );
    `);

    const insNode = sessionDb.prepare('INSERT INTO nodes VALUES (?,?,?,?,?,?,?,?,?,?,?)');
    const insPtr = sessionDb.prepare('INSERT INTO pointers (source_addr, type, target_addr, sources) VALUES (?,?,?,?)');
    const insSense = sessionDb.prepare('INSERT INTO senses VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)');
    const insSPtr = sessionDb.prepare('INSERT INTO sense_pointers (parent_addr, sense_num, type, target_addr) VALUES (?,?,?,?)');

    sessionDb.transaction(() => {
      for (const [addr, node] of this._cache) {
        insNode.run(
          addr, node.name, this._serializeValue(node.value),
          node.context.trust, node.context.createdBy, node.context.accessCount,
          node.context.timestamp, node.context.lastAccess,
          node.mode || null,
          node.macro ? (typeof node.macro === 'string' ? node.macro : JSON.stringify(node.macro)) : null,
          node.context.errors && node.context.errors.length > 0 ? JSON.stringify(node.context.errors) : null
        );
        for (const p of node.pointers) {
          insPtr.run(addr, p.type, p.to, p.sources ? JSON.stringify(p.sources) : null);
        }
        for (const [num, sn] of node.senses) {
          insSense.run(
            addr, num, sn.address, sn.name, this._serializeValue(sn.value),
            sn.context.trust, sn.context.createdBy, sn.context.accessCount,
            sn.context.timestamp, sn.context.lastAccess,
            sn.mode || null,
            sn.macro ? (typeof sn.macro === 'string' ? sn.macro : JSON.stringify(sn.macro)) : null,
            sn.context.errors && sn.context.errors.length > 0 ? JSON.stringify(sn.context.errors) : null
          );
          for (const p of sn.pointers) {
            insSPtr.run(addr, num, p.type, p.to);
          }
        }
      }
    })();

    const count = this._cache.size;
    sessionDb.close();
    return count;
  }

  // ---- Wake: load from a session file into this space ----
  wakeFromFile(filepath) {
    const sessionDb = new Database(filepath, { readonly: true });
    const rows = sessionDb.prepare('SELECT * FROM nodes').all();
    const allPtrs = sessionDb.prepare('SELECT * FROM pointers').all();
    const allSenses = sessionDb.prepare('SELECT * FROM senses').all();
    const allSPtrs = sessionDb.prepare('SELECT * FROM sense_pointers').all();
    sessionDb.close();

    // Build lookup maps
    const ptrMap = new Map();
    for (const p of allPtrs) {
      if (!ptrMap.has(p.source_addr)) ptrMap.set(p.source_addr, []);
      ptrMap.get(p.source_addr).push(p);
    }
    const senseMap = new Map();
    for (const sr of allSenses) {
      if (!senseMap.has(sr.parent_addr)) senseMap.set(sr.parent_addr, []);
      senseMap.get(sr.parent_addr).push(sr);
    }
    const sptrMap = new Map();
    for (const sp of allSPtrs) {
      const key = `${sp.parent_addr}:${sp.sense_num}`;
      if (!sptrMap.has(key)) sptrMap.set(key, []);
      sptrMap.get(key).push(sp);
    }

    // Reconstruct nodes and set into this space
    for (const row of rows) {
      const node = new Node(row.address, row.name, {
        value: this._deserializeValue(row.value),
        trust: row.trust, createdBy: row.createdBy,
        mode: row.mode,
        macro: row.macro ? (row.macro.startsWith('{') || row.macro.startsWith('[') ? JSON.parse(row.macro) : row.macro) : null,
      });
      node.context.accessCount = row.accessCount || 0;
      node.context.timestamp = row.timestamp;
      node.context.lastAccess = row.lastAccess;
      node.context.errors = row.errors ? JSON.parse(row.errors) : [];

      const ptrs = ptrMap.get(row.address) || [];
      node.pointers = ptrs.map(p => ({
        type: p.type, to: p.target_addr,
        ...(p.sources ? { sources: JSON.parse(p.sources) } : {})
      }));

      const senseRows = senseMap.get(row.address) || [];
      for (const sr of senseRows) {
        const sn = new Node(sr.address, sr.name, {
          value: this._deserializeValue(sr.value),
          trust: sr.trust, createdBy: sr.createdBy, mode: sr.mode, macro: sr.macro || null,
        });
        sn.context.accessCount = sr.accessCount || 0;
        sn.context.timestamp = sr.timestamp;
        sn.context.lastAccess = sr.lastAccess;
        sn.context.errors = sr.errors ? JSON.parse(sr.errors) : [];
        sn.pointers = (sptrMap.get(`${row.address}:${sr.sense_num}`) || [])
          .map(p => ({ type: p.type, to: p.target_addr }));
        node.senses.set(sr.sense_num, sn);
      }

      this.set(row.address, node);

      // Rebuild reverse index
      for (const p of node.pointers) {
        this.addReverseEntry(p.to, row.address, row.name, p.type);
      }
    }

    return rows.length;
  }
}

module.exports = { StorageEngine, Node };
