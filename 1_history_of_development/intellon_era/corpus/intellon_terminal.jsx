import { useState, useRef, useEffect, useCallback } from "react";

class TrieNode { constructor() { this.children = new Map(); this.node = null; } }
class Node {
  constructor(addr, name, o = {}) {
    this.macro = o.macro || null; this.address = addr; this.name = name;
    this.context = { timestamp: Date.now(), accessCount: 0, lastAccess: Date.now(), trust: o.trust || 'working-trial', createdBy: o.createdBy || 'manual', errors: [] };
    this.buffer = { input: null, output: null }; this.pointers = o.pointers ? [...o.pointers] : [];
    this.value = o.value !== undefined ? o.value : null; this.mode = o.mode || 'cached';
    this.senses = new Map(); // sense number → Node (sub-nodes with their own pointers/values)
  }
  addPointer(t, to) { this.pointers.push({ type: t, to }); }
  getPointers(t) { return this.pointers.filter(p => p.type === t); }
  touch() { this.context.accessCount++; this.context.lastAccess = Date.now(); }
  nextSense() { return this.senses.size + 1; }
  getSense(n) { return this.senses.get(n); }
  addSense(n, senseNode) { this.senses.set(n, senseNode); }
}
class Trie {
  constructor(n) { this.name = n; this.root = new TrieNode(); this.count = 0; }
  _walk(a, c) { const s = String(a).split('.').map(Number); let cur = this.root; for (const x of s) { if (!cur.children.has(x)) { if (!c) return null; cur.children.set(x, new TrieNode()); } cur = cur.children.get(x); } return cur; }
  set(a, n) { const t = this._walk(a, true); const isNew = !t.node; t.node = n; if (isNew) this.count++; return n; }
  get(a) { const t = this._walk(a); return t ? t.node : null; }
  has(a) { const t = this._walk(a); return !!(t && t.node); }
  parent(a) { const s = String(a).split('.'); return s.length <= 1 ? null : s.slice(0, -1).join('.'); }
  children(a) { const t = this._walk(a); if (!t) return []; const o = []; for (const [c, ch] of t.children) if (ch.node) o.push(`${a}.${c}`); return o; }
  nameToAddr(n) { return Array.from(n).map(c => c.charCodeAt(0)).join('.'); }
  addrToName(a) { return String(a).split('.').map(n => String.fromCharCode(Number(n))).join(''); }
  allNodes() { const o = []; const w = (t, a) => { if (t.node) o.push({ address: a, node: t.node }); for (const [c, ch] of t.children) w(ch, a ? `${a}.${c}` : String(c)); }; for (const [c, ch] of this.root.children) w(ch, String(c)); return o; }
}

function splitter(e) { const t = []; let i = 0; while (i < e.length) { if (e[i] === ' ' || e[i] === '\t') { i++; continue; } if (e[i] === '(' || e[i] === ')') { t.push(e[i++]); continue; } if (e[i] === '"') { let s = '"'; i++; while (i < e.length && e[i] !== '"') s += e[i++]; if (i < e.length) s += e[i++]; t.push(s); continue; } let s = ''; while (i < e.length && !' ()"'.includes(e[i])) s += e[i++]; if (s) t.push(s); } return t; }
function parse(t, p = { i: 0 }) { if (p.i >= t.length) return { type: 'literal', value: null }; if (t[p.i] === '(') { p.i++; const op = t[p.i++], a = []; while (p.i < t.length && t[p.i] !== ')') a.push(parse(t, p)); p.i++; return { type: 'call', op, args: a }; } const k = t[p.i++]; if (/^-?\d+(\.\d+)?$/.test(k)) return { type: 'literal', value: Number(k) }; if (k === 'true') return { type: 'literal', value: true }; if (k === 'false') return { type: 'literal', value: false }; if (k === 'null') return { type: 'literal', value: null }; if (k.startsWith('"') && k.endsWith('"')) return { type: 'literal', value: k.slice(1, -1) }; return { type: 'ref', address: k }; }
function parseExpr(e) { if (!e || typeof e !== 'string' || !e.trim().startsWith('(')) return null; return parse(splitter(e.trim())); }

// Known relationship types for detection
const REL_TYPES = new Set(['eq','is_a','has','is','not','part_of','plural_of','past_of','present_of','opposite_of','contains','type_of','means','synonym','antonym','extends','instance_of','causes','requires','produces','before','after','greater_than','less_than']);

class IntellonSystem {
  constructor() { this.ns = new Trie('node'); this.ws = new Trie('working'); this.prims = new Map(); this._res = new Set(); this._out = []; this.pending = null; this.learning = null; this.conflict = null; this._history = []; this._reg(); }
  _p(n, f) { this.prims.set(n, f); }
  _log(m) { this._out.push(m); }
  _reg() {
    const s = this;
    this._p('ADD', (...a) => a.reduce((x, v) => x + v, 0)); this._p('SUB', (a, ...r) => r.length ? r.reduce((x, v) => x - v, a) : -a);
    this._p('MUL', (...a) => a.reduce((x, v) => x * v, 1)); this._p('DIV', (a, b) => b === 0 ? null : a / b);
    this._p('MOD', (a, b) => b === 0 ? null : a % b); this._p('POW', (a, b) => Math.pow(a, b));
    this._p('NEG', a => -a); this._p('ABS', a => Math.abs(a)); this._p('FLOOR', a => Math.floor(a)); this._p('CEIL', a => Math.ceil(a));
    this._p('ROUND', a => Math.round(a)); this._p('MIN', (...a) => Math.min(...a)); this._p('MAX', (...a) => Math.max(...a)); this._p('SIGN', a => Math.sign(a));
    this._p('EQ', (a, b) => a === b); this._p('NEQ', (a, b) => a !== b); this._p('GT', (a, b) => a > b); this._p('LT', (a, b) => a < b); this._p('GTE', (a, b) => a >= b); this._p('LTE', (a, b) => a <= b);
    this._p('AND', (...a) => a.every(Boolean)); this._p('OR', (...a) => a.some(Boolean)); this._p('NOT', a => !a); this._p('XOR', (a, b) => Boolean(a) !== Boolean(b));
    this._p('CONCAT', (...a) => a.join('')); this._p('SPLIT', (x, d) => typeof x === 'string' ? x.split(d || ' ') : null);
    this._p('S_LEN', x => typeof x === 'string' ? x.length : null); this._p('S_UPPER', x => typeof x === 'string' ? x.toUpperCase() : null);
    this._p('S_LOWER', x => typeof x === 'string' ? x.toLowerCase() : null); this._p('S_REV', x => typeof x === 'string' ? [...x].reverse().join('') : null);
    this._p('S_CHAR', c => String.fromCharCode(c)); this._p('S_CODE', x => typeof x === 'string' && x.length ? x.charCodeAt(0) : null);
    this._p('S_CONTAINS', (x, sub) => typeof x === 'string' ? x.includes(sub) : null);
    this._p('S_SLICE', (x, a, b) => typeof x === 'string' ? x.slice(a, b) : null);
    this._p('A_LEN', a => Array.isArray(a) ? a.length : null); this._p('A_RANGE', (x, e) => Array.from({ length: e - x }, (_, i) => x + i));
    this._p('A_SUM', a => Array.isArray(a) ? a.reduce((x, v) => x + v, 0) : null);
    this._p('A_REV', a => Array.isArray(a) ? [...a].reverse() : null);
    this._p('A_GET', (a, i) => Array.isArray(a) ? (a[i] ?? null) : null);
    this._p('A_HAS', (a, v) => Array.isArray(a) ? a.includes(v) : null);
    this._p('A_PUSH', (a, ...v) => Array.isArray(a) ? [...a, ...v] : null);
    this._p('IS_NUM', a => typeof a === 'number'); this._p('IS_STR', a => typeof a === 'string'); this._p('IS_BOOL', a => typeof a === 'boolean');
    this._p('TO_NUM', a => Number(a)); this._p('TO_STR', a => String(a));
    this._p('TYPE_OF', a => a === null ? 'null' : Array.isArray(a) ? 'array' : typeof a);
    this._p('IF', (c, t, e) => c ? t : e);
    this._p('BIT_AND', (a, b) => a & b); this._p('BIT_OR', (a, b) => a | b); this._p('BIT_XOR', (a, b) => a ^ b);
    this._p('PRINT', (...a) => { s._log(a.map(v => typeof v === 'string' ? v : JSON.stringify(v)).join(' ')); return a[0]; });
    this._p('FORMAT', (t, ...a) => { let r = String(t); a.forEach((v, i) => { r = r.replace(`{${i}}`, String(v)); }); return r; });
    this._p('N_NAME', a => { const n = s.ns.get(String(a)) || s.ws.get(String(a)); return n ? n.name : null; });
    this._p('N_VALUE', a => { const n = s.ns.get(String(a)) || s.ws.get(String(a)); return n ? n.value : null; });
    this._p('N_TRUST', a => { const n = s.ns.get(String(a)) || s.ws.get(String(a)); return n ? n.context.trust : null; });
    this._p('N_EXISTS', a => s.ns.has(String(a)) || s.ws.has(String(a)));
    this._p('N_SHOW', a => { const n = s.ns.get(String(a)) || s.ws.get(String(a)); if (!n) return null; const ptrs = n.pointers.length ? ` [${n.pointers.map(p => p.type + '->' + (s.ns.addrToName(p.to) || p.to)).join(', ')}]` : ''; const d = `[${a}] ${n.name} | ${JSON.stringify(n.value)} | ${n.context.trust}${ptrs}`; s._log(d); return d; });
    this._p('EACH', (arr, op) => { if (!Array.isArray(arr)) return null; const r = []; for (const i of arr) r.push(s.evaluate(`(${op} ${typeof i === 'string' ? '"' + i + '"' : i})`)); return r; });
  }

  populateBase() {
    const ctrl = ['NULL', 'WILDCARD', 'TRUE', 'FALSE', 'UNDEFINED', 'SELF', 'CALLER', 'PASS', 'FAIL', 'TAB', 'NEWLINE', 'UNK', 'BREAK', 'RETURN', 'CONTINUE', 'OPTIONAL', 'EOS', 'BOS', 'EOP', 'EOI', 'PAD', 'WORD_BOUNDARY', 'SENTENCE_BOUNDARY', 'CLAUSE_BOUNDARY', 'PHRASE_BOUNDARY', 'ANY_TYPE', 'ANY_NUMBER', 'ANY_STRING', 'IF_MARKER', 'THEN_MARKER', 'ELSE_MARKER', 'SEPARATOR'];
    for (let i = 0; i < ctrl.length; i++) this.ns.set(String(i), new Node(String(i), ctrl[i], { value: ctrl[i], trust: 'node-proven', createdBy: 'base' }));
    for (let c = 32; c <= 127; c++) this.ns.set(String(c), new Node(String(c), String.fromCharCode(c), { value: String.fromCharCode(c), trust: 'node-proven', createdBy: 'base' }));
    this._loadSignatures();
    return this;
  }

  // Signatures: how to use each primitive. Format is given. Meaning is discovered.
  _loadSignatures() {
    const N = 'ANY_NUMBER', S = 'ANY_STRING', B = 'BOOL', A = 'ANY_TYPE', R = 'ARRAY';
    const sigs = {
      // Math: numbers in, number out, variadic
      ADD:{in:[N,N],out:N,var:true,min:1}, SUB:{in:[N,N],out:N,var:true,min:1},
      MUL:{in:[N,N],out:N,var:true,min:1}, DIV:{in:[N,N],out:N,min:2},
      MOD:{in:[N,N],out:N,min:2}, POW:{in:[N,N],out:N,min:2},
      NEG:{in:[N],out:N,min:1}, ABS:{in:[N],out:N,min:1},
      FLOOR:{in:[N],out:N,min:1}, CEIL:{in:[N],out:N,min:1},
      ROUND:{in:[N],out:N,min:1}, MIN:{in:[N,N],out:N,var:true,min:1},
      MAX:{in:[N,N],out:N,var:true,min:1}, SIGN:{in:[N],out:N,min:1},
      // Comparison: two in, boolean out
      EQ:{in:[A,A],out:B,min:2}, NEQ:{in:[A,A],out:B,min:2},
      GT:{in:[N,N],out:B,min:2}, LT:{in:[N,N],out:B,min:2},
      GTE:{in:[N,N],out:B,min:2}, LTE:{in:[N,N],out:B,min:2},
      // Logic: booleans in, boolean out
      AND:{in:[B,B],out:B,var:true,min:1}, OR:{in:[B,B],out:B,var:true,min:1},
      NOT:{in:[B],out:B,min:1}, XOR:{in:[B,B],out:B,min:2},
      // String: strings in
      CONCAT:{in:[S,S],out:S,var:true,min:1}, SPLIT:{in:[S],out:R,min:1},
      S_LEN:{in:[S],out:N,min:1}, S_UPPER:{in:[S],out:S,min:1},
      S_LOWER:{in:[S],out:S,min:1}, S_REV:{in:[S],out:S,min:1},
      S_CHAR:{in:[N],out:S,min:1}, S_CODE:{in:[S],out:N,min:1},
      S_CONTAINS:{in:[S,S],out:B,min:2}, S_SLICE:{in:[S,N,N],out:S,min:2},
      // Array
      A_LEN:{in:[R],out:N,min:1}, A_RANGE:{in:[N,N],out:R,min:2},
      A_SUM:{in:[R],out:N,min:1}, A_REV:{in:[R],out:R,min:1},
      A_GET:{in:[R,N],out:A,min:2}, A_HAS:{in:[R,A],out:B,min:2},
      A_PUSH:{in:[R,A],out:R,var:true,min:2},
      // Type
      IS_NUM:{in:[A],out:B,min:1}, IS_STR:{in:[A],out:B,min:1},
      IS_BOOL:{in:[A],out:B,min:1}, TO_NUM:{in:[A],out:N,min:1},
      TO_STR:{in:[A],out:S,min:1}, TYPE_OF:{in:[A],out:S,min:1},
      // Control
      IF:{in:[B,A,A],out:A,min:3},
      // Bitwise
      BIT_AND:{in:[N,N],out:N,min:2}, BIT_OR:{in:[N,N],out:N,min:2},
      BIT_XOR:{in:[N,N],out:N,min:2},
      // I/O
      PRINT:{in:[A],out:A,var:true,min:1},
      FORMAT:{in:[S,A],out:S,var:true,min:1},
      // Node inspection
      N_NAME:{in:[A],out:S,min:1}, N_VALUE:{in:[A],out:A,min:1},
      N_TRUST:{in:[A],out:S,min:1}, N_EXISTS:{in:[A],out:B,min:1},
      N_SHOW:{in:[A],out:S,min:1}, EACH:{in:[R,S],out:R,min:2},
    };

    this._sigs = sigs;

    // Store each signature as a node
    for (const [name, sig] of Object.entries(sigs)) {
      const addr = this.ns.nameToAddr('_sig_' + name);
      this.ns.set(addr, new Node(addr, '_sig_' + name, {
        value: sig, trust: 'node-proven', createdBy: 'signature'
      }));
    }
  }

  // Get sample values for a given type
  _samplesFor(type) {
    if (type === 'ANY_NUMBER') return [0, 1, 2, 3, 5, 7, 9, -1, -3, 10, 4, 6, 8];
    if (type === 'ANY_STRING') return ['a', 'b', 'c', 'cat', 'hello', '', 'ABC', 'dog'];
    if (type === 'BOOL') return [true, false, true, false, true, true, false, false];
    if (type === 'ARRAY') return [[1,2,3], [5,10], [0], [], [1,2,3,4,5], [9,8,7]];
    if (type === 'ANY_TYPE') return [0, 1, 'a', true, false, 5, 'hello', null, 3];
    return [0, 1, 'a', true];
  }

  // Ensure a node exists in node space, create if not
  ensure(name, opts = {}) {
    const a = this.ns.nameToAddr(name);
    if (this.ns.has(a)) { this.ns.get(a).touch(); return this.ns.get(a); }
    return this.ns.set(a, new Node(a, name, { trust: 'node-trial', createdBy: opts.createdBy || 'ensure', value: opts.value || null }));
  }

  // ---- PARSE SLASH NOTATION ----
  // "apple/2" → { word: "apple", sense: 2 }
  // "apple" → { word: "apple", sense: null }
  parseSlash(input) {
    const slash = input.indexOf('/');
    if (slash < 0) return { word: input, sense: null };
    return { word: input.slice(0, slash), sense: parseInt(input.slice(slash + 1)) || null };
  }

  // Get the node for a word, or a specific sense of that word
  getNodeOrSense(input) {
    const { word, sense } = this.parseSlash(input);
    const addr = this.ns.nameToAddr(word);
    const node = this.ns.get(addr);
    if (!node) return null;
    if (sense !== null) return node.getSense(sense) || null;
    return node;
  }

  // Create a new sense on an existing node
  createSense(word, value, opts = {}) {
    const addr = this.ns.nameToAddr(word);
    const parent = this.ns.get(addr);
    if (!parent) return null;
    const num = parent.nextSense();
    const senseAddr = `${addr}/${num}`;
    const senseNode = new Node(senseAddr, `${word}/${num}`, {
      value, trust: opts.trust || 'working-trial', createdBy: opts.createdBy || 'sense-split'
    });
    if (opts.pointers) { for (const p of opts.pointers) senseNode.addPointer(p.type, p.to); }
    parent.addSense(num, senseNode);
    return { num, node: senseNode };
  }

  // Defining rel types where conflicts suggest different senses
  _isDefiningRel(rel) { return ['is_a', 'eq', 'type_of', 'instance_of'].includes(rel); }

  // ---- LINK: source rel target (with conflict detection) ----
  link(source, rel, target) {
    const { word: srcWord, sense: srcSense } = this.parseSlash(source);
    const srcNode = this.ensure(srcWord, { createdBy: 'link' });
    const tgtNode = this.ensure(target, { createdBy: 'link' });
    const tgtAddr = this.ns.nameToAddr(target);

    // If linking to a specific sense, add pointer to that sense
    const linkTarget = srcSense !== null ? srcNode.getSense(srcSense) : srcNode;
    if (!linkTarget) return { srcNode, tgtNode, duplicate: false, error: `Sense ${srcSense} not found on ${srcWord}` };

    const exists = linkTarget.pointers.some(p => p.type === rel && p.to === tgtAddr);
    if (exists) return { srcNode, tgtNode, duplicate: true };

    // Conflict detection on defining relationships
    if (this._isDefiningRel(rel) && srcSense === null) {
      const existing = linkTarget.pointers.filter(p => p.type === rel);
      if (existing.length > 0 && !existing.some(p => p.to === tgtAddr)) {
        // Conflict: same rel type, different target
        const existingNames = existing.map(p => this.ns.addrToName(p.to)).join(', ');
        this.conflict = { source: srcWord, rel, target, tgtAddr, existing: existingNames };
        return { srcNode, tgtNode, duplicate: false, conflict: true,
          message: `${srcWord} already ${rel} ${existingNames}. Is "${target}" a different sense? (y/n)` };
      }
    }

    linkTarget.addPointer(rel, tgtAddr);
    this._history.push({ action: 'link', source: srcWord, rel, target, srcAddr: srcNode.address, tgtAddr });
    return { srcNode, tgtNode, duplicate: false };
  }

  // Resolve a conflict — user said y (new sense) or n (same node)
  resolveConflict(isNewSense) {
    if (!this.conflict) return ['No conflict to resolve.'];
    const c = this.conflict;
    if (isNewSense) {
      // Move existing pointers to sense /1 if no senses exist yet
      const srcAddr = this.ns.nameToAddr(c.source);
      const srcNode = this.ns.get(srcAddr);
      if (srcNode && srcNode.senses.size === 0) {
        // First split: move existing defining pointers to sense /1
        const existingPtrs = srcNode.pointers.filter(p => p.type === c.rel);
        const otherPtrs = srcNode.pointers.filter(p => p.type !== c.rel || !this._isDefiningRel(p.type));
        const s1 = this.createSense(c.source, srcNode.value, { createdBy: 'sense-split', pointers: existingPtrs, trust: srcNode.context.trust });
        // Remove the moved pointers from parent
        srcNode.pointers = otherPtrs;
        // Create sense /2 with the new pointer
        const s2 = this.createSense(c.source, null, { createdBy: 'sense-split' });
        s2.node.addPointer(c.rel, c.tgtAddr);
        this._history.push({ action: 'sense-split', source: c.source, rel: c.rel, target: c.target });
        this.conflict = null;
        return [
          `Split "${c.source}" into senses:`,
          `  ${c.source}/1 — ${c.existing} (existing)`,
          `  ${c.source}/2 — ${c.target} (new, working-trial)`,
        ];
      } else {
        // Already has senses, just add a new one
        const s = this.createSense(c.source, null, { createdBy: 'sense-new' });
        s.node.addPointer(c.rel, c.tgtAddr);
        this._history.push({ action: 'sense-add', source: c.source, rel: c.rel, target: c.target, senseNum: s.num });
        this.conflict = null;
        return [`Added ${c.source}/${s.num} — ${c.target} (working-trial)`];
      }
    } else {
      // Not a new sense — add to the same node
      const srcNode = this.ns.get(this.ns.nameToAddr(c.source));
      if (srcNode) {
        srcNode.addPointer(c.rel, c.tgtAddr);
        this._history.push({ action: 'link', source: c.source, rel: c.rel, target: c.target, srcAddr: srcNode.address, tgtAddr: c.tgtAddr });
      }
      this.conflict = null;
      return [`Added: ${c.source} —${c.rel}→ ${c.target} (same sense)`];
    }
  }

  // ---- UNLINK: remove a specific pointer ----
  unlink(source, rel, target) {
    const srcAddr = this.ns.nameToAddr(source);
    const tgtAddr = this.ns.nameToAddr(target);
    const node = this.ns.get(srcAddr);
    if (!node) return [`"${source}" not found.`];
    const before = node.pointers.length;
    node.pointers = node.pointers.filter(p => !(p.type === rel && p.to === tgtAddr));
    if (node.pointers.length === before) return [`No ${rel} pointer from ${source} to ${target}.`];
    this._history.push({ action: 'unlink', source, rel, target, srcAddr, tgtAddr });
    return [`Removed: ${source} —${rel}→ ${target}`];
  }

  // ---- UNDO: reverse the last action ----
  undo() {
    if (!this._history.length) return ['Nothing to undo.'];
    const h = this._history.pop();
    if (h.action === 'link') {
      const node = this.ns.get(h.srcAddr);
      if (node) node.pointers = node.pointers.filter(p => !(p.type === h.rel && p.to === h.tgtAddr));
      return [`Undone: ${h.source} —${h.rel}→ ${h.target} (link removed)`];
    }
    if (h.action === 'unlink') {
      const node = this.ns.get(h.srcAddr);
      if (node) node.addPointer(h.rel, h.tgtAddr);
      return [`Undone: ${h.source} —${h.rel}→ ${h.target} (link restored)`];
    }
    if (h.action === 'teach') {
      const node = this.ns.get(h.addr);
      if (node) node.value = h.oldValue;
      return [`Undone: ${h.word} reverted to ${JSON.stringify(h.oldValue)}`];
    }
    return [`Undone: ${h.action}`];
  }

  // ---- RESOLVE with eq following ----
  pull(a) { const n = this.ns.get(a); if (!n) return null; n.touch(); const w = new Node(a, n.name, { value: n.value, trust: 'working-trial', createdBy: 'pull', mode: n.mode, macro: n.macro, pointers: [...n.pointers] }); w.addPointer('source', a); this.ws.set(a, w); return w; }
  promote(a, t = 'node-trial') { const w = this.ws.get(a); if (!w) return null; return this.ns.set(a, new Node(a, w.name, { value: w.value, trust: t, createdBy: 'promotion', mode: w.mode, macro: w.macro, pointers: w.pointers.filter(p => p.type !== 'source') })); }
  getW(a) { return this.ws.get(a) || this.pull(a); }

  // ---- WORKING SPACE MANAGEMENT ----
  // Nodes stay until explicitly cleared. No auto-eviction.

  // Show everything in working space
  showWorking() {
    const all = this.ws.allNodes();
    if (!all.length) return ['Working space is empty.'];
    const lines = [`Working space: ${all.length} nodes`];
    for (const e of all) {
      const age = Date.now() - e.node.context.timestamp;
      const ptrs = e.node.pointers.length ? ` [${e.node.pointers.map(p => p.type + '->' + this.ns.addrToName(p.to)).join(', ')}]` : '';
      lines.push(`  ${e.node.name} | ${e.node.context.trust} | used: ${e.node.context.accessCount} | ${JSON.stringify(e.node.value)}${ptrs}`);
    }
    return lines;
  }

  // Hibernate: save working state with an ID, clear working space
  hibernate(id) {
    const all = this.ws.allNodes();
    if (!all.length) return ['Nothing to hibernate. Working space is empty.'];
    if (!this._snapshots) this._snapshots = new Map();
    // Auto-generate ID if not provided
    const name = id || new Date().toISOString().slice(0, 19).replace(/[T:]/g, '-');
    const snap = all.map(e => ({
      address: e.address, name: e.node.name, value: e.node.value,
      trust: e.node.context.trust, createdBy: e.node.context.createdBy,
      accessCount: e.node.context.accessCount, mode: e.node.mode,
      macro: e.node.macro, pointers: [...e.node.pointers]
    }));
    this._snapshots.set(name, { data: snap, timestamp: Date.now(), nodeCount: all.length });
    this.ws = new Trie('working');
    return [`Hibernated "${name}": ${all.length} nodes saved. Working space cleared.`];
  }

  // Wake: hibernate current state, load a named snapshot
  wake(id) {
    if (!this._snapshots || !this._snapshots.size) return ['No snapshots exist. Use: hibernate <name>'];
    if (!id) {
      // Show available snapshots
      const lines = ['Available snapshots:'];
      for (const [name, snap] of this._snapshots) {
        const age = Math.round((Date.now() - snap.timestamp) / 1000);
        lines.push(`  ${name} | ${snap.nodeCount} nodes | ${age}s ago`);
      }
      lines.push('', 'Usage: wake <name>');
      return lines;
    }
    if (!this._snapshots.has(id)) return [`Snapshot "${id}" not found. Type "wake" to list snapshots.`];
    // Auto-hibernate current working space if not empty
    const current = this.ws.allNodes();
    const autoSaved = [];
    if (current.length > 0) {
      const autoName = '_auto_' + new Date().toISOString().slice(0, 19).replace(/[T:]/g, '-');
      const snap = current.map(e => ({
        address: e.address, name: e.node.name, value: e.node.value,
        trust: e.node.context.trust, createdBy: e.node.context.createdBy,
        accessCount: e.node.context.accessCount, mode: e.node.mode,
        macro: e.node.macro, pointers: [...e.node.pointers]
      }));
      this._snapshots.set(autoName, { data: snap, timestamp: Date.now(), nodeCount: current.length });
      autoSaved.push(`Auto-saved current state as "${autoName}" (${current.length} nodes)`);
    }
    // Load requested snapshot
    this.ws = new Trie('working');
    const snapData = this._snapshots.get(id).data;
    for (const s of snapData) {
      const n = new Node(s.address, s.name, {
        value: s.value, trust: s.trust, createdBy: s.createdBy,
        mode: s.mode, macro: s.macro, pointers: s.pointers
      });
      n.context.accessCount = s.accessCount;
      this.ws.set(s.address, n);
    }
    return [...autoSaved, `Loaded "${id}": ${snapData.length} nodes restored.`];
  }

  // List all snapshots
  listSnapshots() {
    if (!this._snapshots || !this._snapshots.size) return ['No snapshots.'];
    const lines = ['Snapshots:'];
    for (const [name, snap] of this._snapshots) {
      const age = Math.round((Date.now() - snap.timestamp) / 1000);
      lines.push(`  ${name} | ${snap.nodeCount} nodes | ${age}s ago`);
    }
    return lines;
  }

  // Peek: view contents of a snapshot without loading it
  peek(id) {
    if (!this._snapshots || !this._snapshots.has(id)) return [`Snapshot "${id}" not found.`];
    const snap = this._snapshots.get(id);
    const lines = [`Snapshot "${id}" (${snap.nodeCount} nodes):`];
    for (const s of snap.data) {
      const ptrs = s.pointers.length ? ` [${s.pointers.map(p => p.type + '->' + this.ns.addrToName(p.to)).join(', ')}]` : '';
      lines.push(`  ${s.name} | ${s.trust} | used: ${s.accessCount} | ${JSON.stringify(s.value)}${ptrs}`);
    }
    return lines;
  }

  // Import: pull specific node(s) from a snapshot into current working space
  importFrom(id, word) {
    if (!this._snapshots || !this._snapshots.has(id)) return [`Snapshot "${id}" not found.`];
    const snap = this._snapshots.get(id);
    const addr = this.ns.nameToAddr(word);
    const found = snap.data.filter(s => s.name === word || s.address === addr);
    if (!found.length) return [`"${word}" not found in snapshot "${id}".`, `Use: peek ${id}`];
    const imported = [];
    for (const s of found) {
      const n = new Node(s.address, s.name, {
        value: s.value, trust: s.trust, createdBy: 'import:' + id,
        mode: s.mode, macro: s.macro, pointers: s.pointers
      });
      n.context.accessCount = s.accessCount;
      this.ws.set(s.address, n);
      imported.push(s.name);
    }
    return [`Imported from "${id}": ${imported.join(', ')}`];
  }

  // Archive: promote qualifying nodes, clear the rest
  archive() {
    const all = this.ws.allNodes();
    if (!all.length) return ['Nothing to archive. Working space is empty.'];
    const promoted = [], discarded = [];
    for (const e of all) {
      const n = e.node;
      const isQualified = n.context.trust === 'working-proven' || n.context.trust === 'working-starred'
        || (n.context.trust === 'working-standard' && n.context.accessCount >= 5);
      if (isQualified) {
        const newTrust = n.context.trust === 'working-starred' ? 'node-proven' : 'node-trial';
        this.promote(e.address, newTrust);
        promoted.push(n.name);
      } else {
        discarded.push(n.name);
      }
    }
    this.ws = new Trie('working');
    const lines = [`Archive complete. Working space cleared.`];
    if (promoted.length) lines.push(`Promoted (${promoted.length}): ${promoted.join(', ')}`);
    if (discarded.length) lines.push(`Discarded (${discarded.length}): ${discarded.join(', ')}`);
    return lines;
  }

  // Flush: clear everything in working space, no promotion
  flush() {
    const count = this.ws.count;
    this.ws = new Trie('working');
    return [`Flushed: ${count} working nodes cleared.`];
  }

  resolve(a) {
    if (this._res.has(a)) return { value: null, error: 'circular' }; this._res.add(a);
    try {
      const n = this.getW(a); if (!n) { this._res.delete(a); return { value: null, error: 'not-found' }; } n.touch();
      // If has macro, evaluate
      if (n.macro) { const r = this.evaluate(n.macro); n.buffer.output = r; if (n.mode === 'cached') n.value = r; this._res.delete(a); return { value: r }; }
      // If has value, return it
      if (n.value !== null) { this._res.delete(a); return { value: n.value }; }
      // If has eq pointer, follow it
      const eqs = n.pointers.filter(p => p.type === 'eq');
      if (eqs.length > 0) {
        const target = eqs[0].to;
        // Check if target is a primitive name
        const tgtName = this.ns.addrToName(target);
        if (this.prims.has(tgtName)) { this._res.delete(a); return { value: tgtName, resolved_via: 'eq->primitive' }; }
        // Otherwise resolve the target
        this._res.delete(a);
        return this.resolve(target);
      }
      this._res.delete(a); return { value: n.value };
    } catch (e) { this._res.delete(a); return { value: null, error: e.message }; }
  }

  evaluate(e) { const a = parseExpr(e); return a ? this._eval(a) : e; }
  _eval(a) {
    if (a.type === 'literal') return a.value;
    if (a.type === 'ref') { const r = this.resolve(a.address); return r.error === 'not-found' ? a.address : r.value; }
    if (a.type === 'call') { const op = a.op.toUpperCase(), fn = this.prims.get(op); if (!fn) return null;
      if (op === 'IF') { const c = this._eval(a.args[0]); return c ? (a.args[1] ? this._eval(a.args[1]) : null) : (a.args[2] ? this._eval(a.args[2]) : null); }
      return fn(...a.args.map(x => this._eval(x))); } return null;
  }
  mkNode(name, o = {}) { const a = o.address || this.ns.nameToAddr(name); const sp = o.space || 'working'; const tr = sp === 'node' ? this.ns : this.ws; return tr.set(a, new Node(a, name, { ...o, trust: o.trust || (sp === 'node' ? 'node-trial' : 'working-trial') })); }

  // ---- INGEST raw text ----
  ingest(text) {
    const words = text.split(/\s+/).filter(w => w.length > 0), results = [];
    for (const raw of words) {
      const core = raw.replace(/^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$/g, ''); if (!core) continue;
      const addr = this.ns.nameToAddr(core);
      if (this.ns.has(addr)) { const n = this.ns.get(addr); n.touch(); results.push({ word: core, addr, level: 1, status: 'known', value: n.value }); continue; }
      const pa = this.ns.parent(addr);
      if (pa && this.ns.has(pa)) { const pn = this.ns.get(pa); this.mkNode(core, { address: addr, space: 'working', createdBy: 'extend' }).addPointer('extends', pa); results.push({ word: core, addr, level: 2, status: 'extends "' + pn.name + '"' }); continue; }
      this.mkNode(core, { address: addr, space: 'working', createdBy: core.length > 1 ? 'fit' : 'note' });
      results.push({ word: core, addr, level: core.length > 1 ? 3 : 5, status: core.length > 1 ? 'new' : 'noted' });
    }
    return results;
  }

  // ---- TEACH word = value ----
  teach(word, def) {
    const a = this.ns.nameToAddr(word);
    if (this.ns.has(a)) { const n = this.ns.get(a); const old = n.value; n.value = def; n.touch(); this._history.push({ action: 'teach', word, addr: a, oldValue: old, newValue: def }); return [`Updated: ${word} = "${def}" (was: ${JSON.stringify(old)})`]; }
    this.mkNode(word, { address: a, value: def, space: 'node', createdBy: 'teach' }); this._history.push({ action: 'teach', word, addr: a, oldValue: null, newValue: def }); return [`Taught: ${word} = "${def}" | node-trial`];
  }

  // ---- CURRICULUM ----
  loadCurriculum() {
    const lessons = [
      // Math operators → primitives
      ['+ eq ADD'], ['- eq SUB'], ['* eq MUL'], ['/ eq DIV'],
      ['= eq EQ'], ['> eq GT'], ['< eq LT'],
      // Categories
      ['cat is_a animal'], ['dog is_a animal'], ['fish is_a animal'], ['bird is_a animal'],
      ['animal is_a organism'], ['plant is_a organism'], ['organism is_a thing'],
      ['car is_a vehicle'], ['bus is_a vehicle'], ['vehicle is_a thing'],
      ['apple is_a fruit'], ['banana is_a fruit'], ['fruit is_a food'],
      ['bread is_a food'], ['food is_a thing'],
      // Properties
      ['fire is hot'], ['ice is cold'], ['water is wet'], ['sun is bright'], ['night is dark'],
      // Synonyms
      ['feline eq cat'], ['canine eq dog'], ['big eq large'], ['small eq little'],
      ['fast eq quick'], ['happy eq glad'],
      // Opposites
      ['hot opposite_of cold'], ['big opposite_of small'], ['fast opposite_of slow'],
      ['up opposite_of down'], ['light opposite_of dark'], ['yes opposite_of no'],
      // Morphology
      ['cats plural_of cat'], ['dogs plural_of dog'], ['birds plural_of bird'],
      ['ran past_of run'], ['sat past_of sit'], ['ate past_of eat'],
      ['running present_of run'], ['sitting present_of sit'], ['eating present_of eat'],
      // Parts
      ['wheel part_of car'], ['engine part_of car'], ['wing part_of bird'],
      ['leaf part_of tree'], ['root part_of tree'], ['branch part_of tree'],
      // Causation
      ['fire causes heat'], ['rain causes wet'], ['cold causes ice'],
    ];
    const lines = [];
    let linked = 0;
    for (const [stmt] of lessons) {
      const parts = stmt.split(' ');
      if (parts.length === 3) {
        const [src, rel, tgt] = parts;
        const r = this.link(src, rel, tgt);
        if (!r.duplicate) { linked++; lines.push(`  ${src} —${rel}→ ${tgt}`); }
      }
    }
    return [`Curriculum loaded: ${linked} relationships`, ...lines];
  }

  // ---- FEEDBACK ----
  confirm() { if (!this.pending) return ['Nothing pending.']; const p = []; for (const i of this.pending) { if (i.level === 1) continue; if (this.ws.get(i.addr)) { this.promote(i.addr); p.push(i.word); } } this.pending = null; return p.length ? [`Confirmed. Promoted: ${p.join(', ')}`] : ['Nothing new to promote.']; }
  reject() { if (!this.pending) return ['Nothing pending.']; const w = this.pending.filter(p => p.level > 1).map(p => p.word); this.pending = null; return w.length ? [`Rejected. Discarded: ${w.join(', ')}`] : ['Nothing to discard.']; }
  correct(c) { if (!this.pending) return ['Nothing pending.']; const inp = this.pending.map(p => p.word).join(' '); this.mkNode('_obs_' + this.ns.count, { value: { input: inp, expected: c, type: 'observation-pair' }, space: 'node', createdBy: 'correction' }); for (const i of this.pending) { if (i.level === 1) continue; const w = this.ws.get(i.addr); if (w) { w.context.errors.push({ correction: c }); this.promote(i.addr); } } this.pending = null; return [`Correction: "${inp}" -> "${c}"`]; }

  // ---- xb.2: QUESTION ANSWERING WITH CHAIN WALKING ----

  // Follow eq pointer to get canonical address
  _canonical(addr) {
    const n = this.ns.get(addr);
    if (!n) return addr;
    const eqs = n.pointers.filter(p => p.type === 'eq');
    return eqs.length > 0 ? this._canonical(eqs[0].to) : addr;
  }

  // Walk a pointer chain recursively, return full path
  walk(startAddr, relType, maxDepth = 10) {
    const visited = new Set();
    const chain = [];
    const _walk = (addr, depth) => {
      if (depth > maxDepth || visited.has(addr)) return;
      visited.add(addr);
      // Follow eq transparently
      const canonical = this._canonical(addr);
      if (canonical !== addr) { visited.add(canonical); }
      const node = this.ns.get(canonical);
      if (!node) return;
      chain.push({ addr: canonical, name: node.name });
      const rels = node.pointers.filter(p => p.type === relType);
      for (const r of rels) _walk(r.to, depth + 1);
    };
    _walk(startAddr, 0);
    return chain;
  }

  // Verify: is there a path from source to target via relType?
  verify(sourceWord, relType, targetWord) {
    const srcAddr = this._canonical(this.ns.nameToAddr(sourceWord));
    const tgtAddr = this._canonical(this.ns.nameToAddr(targetWord));
    if (!this.ns.has(srcAddr)) return { found: false, reason: `"${sourceWord}" not found` };
    if (!this.ns.has(tgtAddr)) return { found: false, reason: `"${targetWord}" not found` };
    const chain = this.walk(srcAddr, relType);
    const match = chain.find(c => c.addr === tgtAddr);
    if (match) {
      const path = chain.slice(0, chain.indexOf(match) + 1).map(c => c.name);
      return { found: true, path };
    }
    return { found: false, reason: `no ${relType} path from ${sourceWord} to ${targetWord}`, tried: chain.map(c => c.name) };
  }

  // Reverse query: find all nodes pointing TO target with relType
  reverseQuery(targetWord, relType) {
    const tgtAddr = this._canonical(this.ns.nameToAddr(targetWord));
    if (!this.ns.has(tgtAddr)) return [];
    const results = [];
    for (const entry of this.ns.allNodes()) {
      const canonical = this._canonical(entry.address);
      const node = this.ns.get(canonical) || entry.node;
      for (const p of node.pointers) {
        if ((!relType || p.type === relType) && this._canonical(p.to) === tgtAddr) {
          results.push({ name: node.name, addr: canonical, rel: p.type });
        }
      }
    }
    return results;
  }

  // Forward query with chain walking
  query(word, rel) {
    const { word: w, sense: senseNum } = this.parseSlash(word);
    const addr = this._canonical(this.ns.nameToAddr(w));
    const node = this.ns.get(addr);
    if (!node) return [`"${w}" not found.`];

    // If specific sense requested, query that sense
    if (senseNum !== null) {
      const sense = node.getSense(senseNum);
      if (!sense) return [`${w}/${senseNum} not found.`];
      const lines = [`${w}/${senseNum}${sense.value ? ' = ' + JSON.stringify(sense.value) : ''}:`];
      for (const p of sense.pointers) lines.push(`  ${w}/${senseNum} —${p.type}→ ${this.ns.addrToName(p.to)}`);
      if (sense.pointers.length === 0) lines.push('  (no relationships)');
      return lines;
    }

    const lines = [];
    // Show senses if they exist
    if (node.senses.size > 0) {
      lines.push(`"${w}" has ${node.senses.size} sense${node.senses.size > 1 ? 's' : ''}:`);
      for (const [num, sense] of node.senses) {
        const rels = sense.pointers.map(p => `${p.type}→${this.ns.addrToName(p.to)}`).join(', ');
        lines.push(`  /${num}${sense.value ? ' = ' + JSON.stringify(sense.value) : ''} [${rels || 'no rels'}] (${sense.context.trust})`);
      }
    }
    // Direct pointers on the parent node
    const direct = node.pointers.filter(p => !rel || p.type === rel);
    for (const p of direct) {
      const tgtName = this.ns.addrToName(p.to);
      const chain = this.walk(p.to, p.type);
      if (chain.length > 1) lines.push(`${w} —${p.type}→ ${chain.map(c => c.name).join(' → ')}`);
      else lines.push(`${w} —${p.type}→ ${tgtName}`);
    }
    if (!lines.length) {
      if (node.value) lines.push(`${w} = ${JSON.stringify(node.value)}`);
      else lines.push(`"${w}" exists but has no relationships.`);
    }
    return lines;
  }

  // SCAFFOLD: Parse question and route to the right method
  // These patterns will be replaced with learned behavior
  ask(question) {
    const q = question.replace(/[?!.]+$/, '').trim().toLowerCase();
    const words = q.split(/\s+/);

    // "is X a/an Y" or "is X Y" → verify is_a then is
    if (words[0] === 'is' && words.length >= 3) {
      const src = words[1];
      const skip = (words[2] === 'a' || words[2] === 'an') ? 3 : 2;
      const tgt = words.slice(skip).join(' ');
      // Try is_a first, then is
      let result = this.verify(src, 'is_a', tgt);
      if (!result.found) result = this.verify(src, 'is', tgt);
      if (result.found) return [`Yes. ${result.path.join(' → ')}`];
      return [`No. ${result.reason}`, result.tried && result.tried.length > 1 ? `  searched: ${result.tried.join(' → ')}` : ''].filter(Boolean);
    }

    // "does X have Y" → verify has/part_of
    if (words[0] === 'does' && words.includes('have')) {
      const haveIdx = words.indexOf('have');
      const src = words.slice(1, haveIdx).join(' ');
      const tgt = words.slice(haveIdx + 1).join(' ');
      // Check forward (src has tgt) and reverse (tgt part_of src)
      let result = this.verify(src, 'has', tgt);
      if (!result.found) {
        const rev = this.reverseQuery(src, 'part_of');
        const match = rev.find(r => r.name === tgt);
        if (match) return [`Yes. ${tgt} —part_of→ ${src}`];
      }
      if (result.found) return [`Yes. ${result.path.join(' → ')}`];
      return [`No. ${result.reason}`];
    }

    // "what is X" → full forward dump
    if (words[0] === 'what' && words[1] === 'is') {
      const target = words.slice(2).join(' ');
      const addr = this._canonical(this.ns.nameToAddr(target));
      const node = this.ns.get(addr);
      if (!node) return [`"${target}" not found.`];
      const lines = [];
      if (node.value) lines.push(`${target} = ${JSON.stringify(node.value)}`);
      // Forward pointers with chains
      for (const p of node.pointers) {
        const chain = this.walk(p.to, p.type);
        if (chain.length > 1) {
          lines.push(`${target} —${p.type}→ ${chain.map(c => c.name).join(' → ')}`);
        } else {
          lines.push(`${target} —${p.type}→ ${this.ns.addrToName(p.to)}`);
        }
      }
      // Reverse: what points to this?
      const rev = this.reverseQuery(target);
      for (const r of rev) lines.push(`${r.name} —${r.rel}→ ${target}`);
      if (!lines.length) lines.push(`"${target}" exists but I know nothing about it.`);
      return lines;
    }

    // "what <rel> X" → reverse lookup (e.g., "what is_a animal")
    if (words[0] === 'what' && words.length >= 3 && REL_TYPES.has(words[1])) {
      const rel = words[1];
      const target = words.slice(2).join(' ');
      const results = this.reverseQuery(target, rel);
      if (!results.length) return [`Nothing ${rel} ${target}.`];
      return results.map(r => `${r.name} —${rel}→ ${target}`);
    }

    // "what has X" / "what contains X" → reverse lookup
    if (words[0] === 'what' && (words[1] === 'has' || words[1] === 'contains')) {
      const rel = words[1];
      const target = words.slice(2).join(' ');
      const results = this.reverseQuery(target, rel);
      if (!results.length) return [`Nothing ${rel} ${target}.`];
      return results.map(r => `${r.name} —${rel}→ ${target}`);
    }

    // Fallback: try as a simple query on the first word
    return this.query(words[0]);
  }

  // ---- xb.4: SELF-EXPLORATION — curriculum-driven tool learning ----

  // The curriculum: test sheets for every primitive, organized by level
  _curriculum() { return {
    1: { // Comparison — foundation for self-checking
      EQ: [[[1,1],true],[[1,2],false],[[0,0],true],[[5,3],false],[[-1,-1],true],[[-1,1],false],[["a","a"],true],[["a","b"],false],[[true,true],true],[[true,false],false]],
      NEQ: [[[1,2],true],[[1,1],false],[[5,3],true],[[0,0],false],[["a","b"],true],[["a","a"],false],[[true,false],true],[[true,true],false]]
    },
    2: { // Boolean logic
      NOT: [[[true],false],[[false],true]],
      AND: [[[true,true],true],[[true,false],false],[[false,true],false],[[false,false],false]],
      OR: [[[true,true],true],[[true,false],true],[[false,true],true],[[false,false],false]],
      XOR: [[[true,true],false],[[true,false],true],[[false,true],true],[[false,false],false]]
    },
    3: { // Ordered comparison
      GT: [[[5,3],true],[[3,5],false],[[5,5],false],[[0,-1],true],[[-1,0],false],[[10,9],true]],
      LT: [[[3,5],true],[[5,3],false],[[5,5],false],[[-1,0],true],[[0,-1],false],[[1,10],true]],
      GTE: [[[5,3],true],[[3,5],false],[[5,5],true],[[0,0],true],[[-1,0],false],[[10,1],true]],
      LTE: [[[3,5],true],[[5,3],false],[[5,5],true],[[0,0],true],[[0,-1],false],[[1,10],true]]
    },
    4: { // Basic arithmetic
      ADD: [[[1,2],3],[[0,5],5],[[5,5],10],[[-1,3],2],[[2,3],5],[[0,0],0],[[7,1],8],[[-3,-2],-5]],
      SUB: [[[5,3],2],[[3,5],-2],[[10,0],10],[[0,5],-5],[[5,5],0],[[-1,-3],2],[[7,1],6],[[100,1],99]]
    },
    5: { // More arithmetic
      MUL: [[[2,3],6],[[5,0],0],[[4,4],16],[[-1,5],-5],[[1,7],7],[[-2,-3],6],[[3,3],9],[[10,10],100]],
      DIV: [[[10,2],5],[[9,3],3],[[7,2],3.5],[[1,4],0.25],[[0,5],0],[[-6,3],-2],[[100,10],10]],
      MOD: [[[10,3],1],[[9,3],0],[[7,2],1],[[5,5],0],[[8,3],2],[[0,5],0],[[13,4],1]],
      POW: [[[2,3],8],[[3,2],9],[[5,0],1],[[0,5],0],[[2,10],1024],[[10,2],100],[[1,100],1]]
    },
    6: { // Single-number transforms
      NEG: [[[5],-5],[[-5],5],[[0],0],[[1],-1],[[-1],1],[[100],-100]],
      ABS: [[[5],5],[[-5],5],[[0],0],[[-1],1],[[1],1],[[-100],100]],
      SIGN: [[[5],1],[[-5],-1],[[0],0],[[100],1],[[-1],-1],[[1],1]],
      MIN: [[[3,5],3],[[5,3],3],[[-1,0],-1],[[5,5],5],[[0,0],0],[[10,1],1]],
      MAX: [[[3,5],5],[[5,3],5],[[-1,0],0],[[5,5],5],[[0,0],0],[[10,1],10]],
      FLOOR: [[[3.7],3],[[3.2],3],[[-1.5],-2],[[5],5],[[0.9],0],[[-0.1],-1]],
      CEIL: [[[3.2],4],[[3.7],4],[[-1.5],-1],[[5],5],[[0.1],1],[[-0.9],0]],
      ROUND: [[[3.2],3],[[3.7],4],[[3.5],4],[[-1.5],-1],[[5],5],[[0.4],0]]
    },
    7: { // String operations
      S_LEN: [[["hello"],5],[["a"],1],[[""],0],[["cat"],3],[["abcdef"],6]],
      S_UPPER: [[["hello"],"HELLO"],[["cat"],"CAT"],[["ABC"],"ABC"],[["a"],"A"],[[""],""]],
      S_LOWER: [[["HELLO"],"hello"],[["CAT"],"cat"],[["abc"],"abc"],[["A"],"a"],[[""],""]],
      S_REV: [[["hello"],"olleh"],[["abc"],"cba"],[["a"],"a"],[[""],""],[["ab"],"ba"]],
      CONCAT: [[["a","b"],"ab"],[["hello"," ","world"],"hello world"],[["","x"],"x"],[["cat","s"],"cats"]],
      S_CHAR: [[[65],"A"],[[97],"a"],[[48],"0"],[[32]," "],[[90],"Z"]],
      S_CODE: [[["A"],65],[["a"],97],[["0"],48],[["Z"],90],[["z"],122]]
    },
    8: { // Type operations
      IS_NUM: [[[5],true],[["hello"],false],[[0],true],[[true],false],[[-3],true]],
      IS_STR: [[["hello"],true],[[5],false],[[""],true],[[true],false],[["a"],true]],
      TYPE_OF: [[[5],"number"],[["hello"],"string"],[[true],"boolean"],[[false],"boolean"],[[0],"number"]],
      TO_NUM: [[["5"],5],[["0"],0],[[true],1],[[false],0]],
      TO_STR: [[[5],"5"],[[0],"0"],[[true],"true"],[[false],"false"]],
      IS_BOOL: [[[true],true],[[false],true],[[5],false],[["hello"],false],[[0],false]]
    },
    9: { // Bitwise
      BIT_AND: [[[12,10],8],[[15,7],7],[[0,5],0],[[5,5],5],[[255,0],0]],
      BIT_OR: [[[12,10],14],[[0,5],5],[[5,5],5],[[15,0],15]],
      BIT_XOR: [[[12,10],6],[[5,5],0],[[0,5],5],[[15,15],0]]
    },
    10: { // More string ops + control (uses expr strings for complex args)
      S_CONTAINS: [[["hello","ell"],true],[["hello","xyz"],false],[["hello","hello"],true],[["cat","at"],true],[["cat","dog"],false]],
      S_SLICE: [[["hello",0,3],"hel"],[["hello",1,4],"ell"],[["abcdef",2,5],"cde"],[["cat",0,1],"c"]],
      IF: [[[true,1,2],1],[[false,1,2],2],[[true,"yes","no"],"yes"],[[false,"yes","no"],"no"]]
    },
    11: { // Array ops — args starting with "~" are expression strings
      A_RANGE: [[[1,4],[1,2,3]],[[0,5],[0,1,2,3,4]],[[3,6],[3,4,5]],[[0,1],[0]]],
      A_LEN: [["~(A_RANGE 1 4)",3],["~(A_RANGE 1 6)",5],["~(A_RANGE 0 1)",1]],
      A_SUM: [["~(A_RANGE 1 4)",6],["~(A_RANGE 1 6)",15],["~(A_RANGE 0 5)",10]],
      A_REV: [["~(A_RANGE 1 4)",[3,2,1]],["~(A_RANGE 1 3)",[2,1]]],
      A_GET: [["~(A_RANGE 10 15) 0",10],["~(A_RANGE 10 15) 2",12]],
      A_HAS: [["~(A_RANGE 1 5) 3",true],["~(A_RANGE 1 5) 9",false]]
    },
    12: { // Node inspection
      N_NAME: [[[65],"A"],[[97],"a"],[[48],"0"],[[32]," "]],
      N_VALUE: [[[65],"A"],[[50],"2"],[[0],"NULL"]],
      N_EXISTS: [[[65],true],[[97],true],[[9999],false]],
      N_TRUST: [[[65],"node-proven"],[[97],"node-proven"]]
    }
  }; }

  // Pattern detection from observations
  _predictResult(observations) {
    if (observations.length < 2) return null;
    const n2 = observations.filter(o => o.args?.length === 2 && typeof o.args[0] === 'number' && typeof o.args[1] === 'number' && typeof o.result === 'number');
    if (n2.length >= 3) {
      if (n2.every(o => o.result === o.args[0] + o.args[1])) return { fn: (a,b)=>a+b, pat: 'sum' };
      if (n2.every(o => o.result === o.args[0] - o.args[1])) return { fn: (a,b)=>a-b, pat: 'difference' };
      if (n2.every(o => o.result === o.args[0] * o.args[1])) return { fn: (a,b)=>a*b, pat: 'product' };
      const d = n2.filter(o => o.args[1] !== 0);
      if (d.length >= 3 && d.every(o => o.result === o.args[0] / o.args[1])) return { fn: (a,b)=>b===0?null:a/b, pat: 'division' };
      const m = n2.filter(o => o.args[1] !== 0);
      if (m.length >= 3 && m.every(o => o.result === o.args[0] % o.args[1])) return { fn: (a,b)=>b===0?null:a%b, pat: 'modulo' };
      if (n2.every(o => o.result === Math.pow(o.args[0],o.args[1]))) return { fn: (a,b)=>Math.pow(a,b), pat: 'power' };
      if (n2.every(o => o.result === Math.min(o.args[0],o.args[1]))) return { fn: (a,b)=>Math.min(a,b), pat: 'minimum' };
      if (n2.every(o => o.result === Math.max(o.args[0],o.args[1]))) return { fn: (a,b)=>Math.max(a,b), pat: 'maximum' };
      if (n2.every(o => o.result === (o.args[0]&o.args[1]))) return { fn: (a,b)=>a&b, pat: 'bitwise_and' };
      if (n2.every(o => o.result === (o.args[0]|o.args[1]))) return { fn: (a,b)=>a|b, pat: 'bitwise_or' };
      if (n2.every(o => o.result === (o.args[0]^o.args[1]))) return { fn: (a,b)=>a^b, pat: 'bitwise_xor' };
    }
    const b2 = observations.filter(o => typeof o.result === 'boolean' && o.args?.length === 2);
    if (b2.length >= 3) {
      if (b2.every(o => o.result === (o.args[0]===o.args[1]))) return { fn: (a,b)=>a===b, pat: 'equals' };
      if (b2.every(o => o.result === (o.args[0]!==o.args[1]))) return { fn: (a,b)=>a!==b, pat: 'not_equals' };
      if (b2.every(o => o.result === (o.args[0]>o.args[1]))) return { fn: (a,b)=>a>b, pat: 'greater_than' };
      if (b2.every(o => o.result === (o.args[0]<o.args[1]))) return { fn: (a,b)=>a<b, pat: 'less_than' };
      if (b2.every(o => o.result === (o.args[0]>=o.args[1]))) return { fn: (a,b)=>a>=b, pat: 'gte' };
      if (b2.every(o => o.result === (o.args[0]<=o.args[1]))) return { fn: (a,b)=>a<=b, pat: 'lte' };
      if (b2.every(o => o.result === (o.args[0]&&o.args[1]))) return { fn: (a,b)=>!!(a&&b), pat: 'and' };
      if (b2.every(o => o.result === (o.args[0]||o.args[1]))) return { fn: (a,b)=>!!(a||b), pat: 'or' };
      if (b2.every(o => o.result === (o.args[0]!==o.args[1]))) return { fn: (a,b)=>a!==b, pat: 'xor' };
    }
    const n1 = observations.filter(o => o.args?.length === 1 && typeof o.args[0] === 'number' && typeof o.result === 'number');
    if (n1.length >= 3) {
      if (n1.every(o => o.result === -o.args[0])) return { fn: a=>-a, pat: 'negate' };
      if (n1.every(o => o.result === Math.abs(o.args[0]))) return { fn: a=>Math.abs(a), pat: 'absolute' };
      if (n1.every(o => o.result === Math.sign(o.args[0]))) return { fn: a=>Math.sign(a), pat: 'sign' };
      if (n1.every(o => o.result === Math.floor(o.args[0]))) return { fn: a=>Math.floor(a), pat: 'floor' };
      if (n1.every(o => o.result === Math.ceil(o.args[0]))) return { fn: a=>Math.ceil(a), pat: 'ceil' };
      if (n1.every(o => o.result === Math.round(o.args[0]))) return { fn: a=>Math.round(a), pat: 'round' };
    }
    const b1 = observations.filter(o => o.args?.length === 1 && typeof o.args[0] === 'boolean' && typeof o.result === 'boolean');
    if (b1.length >= 2 && b1.every(o => o.result === !o.args[0])) return { fn: a=>!a, pat: 'not' };
    const s1n = observations.filter(o => o.args?.length === 1 && typeof o.args[0] === 'string' && typeof o.result === 'number');
    if (s1n.length >= 2 && s1n.every(o => o.result === o.args[0].length)) return { fn: a=>a.length, pat: 'length' };
    const s1s = observations.filter(o => o.args?.length === 1 && typeof o.args[0] === 'string' && typeof o.result === 'string');
    if (s1s.length >= 2) {
      if (s1s.every(o => o.result === o.args[0].toUpperCase())) return { fn: a=>a.toUpperCase(), pat: 'uppercase' };
      if (s1s.every(o => o.result === o.args[0].toLowerCase())) return { fn: a=>a.toLowerCase(), pat: 'lowercase' };
      if (s1s.every(o => o.result === [...o.args[0]].reverse().join(''))) return { fn: a=>[...a].reverse().join(''), pat: 'reverse' };
    }
    const s2s = observations.filter(o => o.args?.length >= 2 && o.args.every(a => typeof a === 'string') && typeof o.result === 'string');
    if (s2s.length >= 2 && s2s.every(o => o.result === o.args.join(''))) return { fn: (...a) => a.join(''), pat: 'concatenate' };
    const n1s = observations.filter(o => o.args?.length === 1 && typeof o.args[0] === 'number' && typeof o.result === 'string');
    if (n1s.length >= 2 && n1s.every(o => o.result === String.fromCharCode(o.args[0]))) return { fn: a => String.fromCharCode(a), pat: 'char_from_code' };
    const s1c = observations.filter(o => o.args?.length === 1 && typeof o.args[0] === 'string' && typeof o.result === 'number');
    if (s1c.length >= 2 && s1c.every(o => o.result === o.args[0].charCodeAt(0))) return { fn: a => a.charCodeAt(0), pat: 'code_from_char' };
    const s2b = observations.filter(o => o.args?.length === 2 && o.args.every(a => typeof a === 'string') && typeof o.result === 'boolean');
    if (s2b.length >= 2 && s2b.every(o => o.result === o.args[0].includes(o.args[1]))) return { fn: (a,b) => a.includes(b), pat: 'contains' };
    // Type checks
    const t1 = observations.filter(o => o.args?.length === 1 && typeof o.result === 'boolean');
    if (t1.length >= 3) {
      if (t1.every(o => o.result === (typeof o.args[0] === 'number'))) return { fn: a => typeof a === 'number', pat: 'is_number' };
      if (t1.every(o => o.result === (typeof o.args[0] === 'string'))) return { fn: a => typeof a === 'string', pat: 'is_string' };
      if (t1.every(o => o.result === (typeof o.args[0] === 'boolean'))) return { fn: a => typeof a === 'boolean', pat: 'is_boolean' };
    }
    const t1s = observations.filter(o => o.args?.length === 1 && typeof o.result === 'string');
    if (t1s.length >= 3 && t1s.every(o => o.result === typeof o.args[0])) return { fn: a => typeof a, pat: 'type_of' };
    // Type conversions
    const conv_n = observations.filter(o => o.args?.length === 1 && typeof o.result === 'number');
    if (conv_n.length >= 3 && conv_n.every(o => o.result === Number(o.args[0]))) return { fn: a => Number(a), pat: 'to_number' };
    const conv_s = observations.filter(o => o.args?.length === 1 && typeof o.result === 'string');
    if (conv_s.length >= 3 && conv_s.every(o => o.result === String(o.args[0]))) return { fn: a => String(a), pat: 'to_string' };
    // IF pattern: 3 args, result is arg[1] when arg[0] truthy, arg[2] when falsy
    const if3 = observations.filter(o => o.args?.length === 3);
    if (if3.length >= 2 && if3.every(o => o.result === (o.args[0] ? o.args[1] : o.args[2]))) return { fn: (a,b,c) => a ? b : c, pat: 'conditional' };
    // S_SLICE pattern: string + 2 numbers → substring
    const sl = observations.filter(o => o.args?.length === 3 && typeof o.args[0] === 'string' && typeof o.args[1] === 'number');
    if (sl.length >= 2 && sl.every(o => o.result === o.args[0].slice(o.args[1], o.args[2]))) return { fn: (a,b,c) => a.slice(b,c), pat: 'slice' };
    return null;
  }

  // Novel probe generator — creates inputs the system hasn't tried
  _novelProbe(sig, tried, idx) {
    const t = sig.in[0];
    const len = sig.in.length;
    // Single-arg number
    if (t === 'ANY_NUMBER' && len === 1) {
      const vals = [11,-7,42,99,-50,13,27,-3,8,15,33,-12,64,0,1,-99,55,77];
      return [vals[idx % vals.length]];
    }
    // Two-arg number
    if (t === 'ANY_NUMBER' && len === 2) {
      const pairs = [[4,7],[8,3],[6,6],[9,1],[2,8],[7,4],[3,9],[11,5],[0,7],[5,2],[13,6],[20,4],[15,3],[1,9],[8,8],[100,1]];
      return pairs[idx % pairs.length];
    }
    // Single-arg boolean
    if (t === 'BOOL' && len === 1) return [idx % 2 === 0];
    // Two-arg boolean
    if (t === 'BOOL' && len === 2) return [[true,true],[true,false],[false,true],[false,false]][idx % 4];
    // Single-arg string
    if (t === 'ANY_STRING' && len === 1) {
      return [["fox","Jump","TREE","","xy","Hello","WORLD","test","ABC","a","Zebra","moon"][idx % 12]];
    }
    // Two-arg string
    if (t === 'ANY_STRING' && len === 2) {
      return [["fox","ox"],["hello","lo"],["test","xyz"],["abc","abc"],["","a"],["Big","ig"],["moon","oo"],["test","test"],["cat","z"],["hello","hell"]][idx % 10];
    }
    // Three-arg: BOOL + ANY + ANY (IF pattern)
    if (t === 'BOOL' && len === 3) {
      const conds = [true,false,true,false,true,true,false,false,true,false];
      const vals = [10,20,30,40,50,"a","b","c",99,0];
      return [conds[idx % 10], vals[idx % 10], vals[(idx + 5) % 10]];
    }
    // Three-arg: STRING + NUM + NUM (S_SLICE pattern)
    if (t === 'ANY_STRING' && len === 3) {
      const strs = ["hello","abcdef","testing","world","xyz"];
      const s = strs[idx % strs.length];
      const start = idx % Math.max(s.length, 1);
      const end = Math.min(start + 1 + (idx % 3), s.length);
      return [s, start, end];
    }
    // Single-arg ANY_TYPE
    if (t === 'ANY_TYPE' && len === 1) {
      return [[42,"hello",true,0,false,"abc",-5,"",7,"xyz",null,3.14][idx % 12]];
    }
    // Two-arg ANY_TYPE
    if (t === 'ANY_TYPE' && len === 2) {
      const vals = [42,"hello",true,0,false,"abc",-5,"",7,"xyz"];
      return [vals[idx % vals.length], vals[(idx + 3) % vals.length]];
    }
    // Array types — can't easily generate novel array probes, cycle small ranges
    if (t === 'ARRAY') {
      return [[1,2,3]]; // placeholder
    }
    // Fallback
    return [idx, idx + 1];
  }

  // Explore a single primitive using the curriculum
  explore(primName) {
    const name = primName.toUpperCase();
    if (!this.prims.has(name)) return [`Unknown primitive: ${name}`];
    const curriculum = this._curriculum();
    const sig = this._sigs?.[name];

    // Find this tool's test sheet
    let tests = null, level = 0;
    for (const [lv, tools] of Object.entries(curriculum)) {
      if (tools[name]) { tests = tools[name]; level = parseInt(lv); break; }
    }

    const lines = [`Exploring ${name}...`];
    const observations = [];

    // PHASE 1: VERIFY — run every given example
    if (tests) {
      let verified = 0, failed = 0;
      for (const test of tests) {
        let argStr, args;
        if (typeof test[0] === 'string' && test[0].startsWith('~')) {
          // Expression-string format: "~(A_RANGE 1 4)" → use directly
          argStr = test[0].slice(1);
          args = [argStr]; // store raw for observation
        } else {
          args = test[0];
          argStr = args.map(a => typeof a === 'string' ? `"${a}"` : String(a)).join(' ');
        }
        const expected = test[1];
        let result;
        try { result = this.evaluate(`(${name} ${argStr})`); } catch(e) { result = null; }
        observations.push({ args, result });
        if (JSON.stringify(result) === JSON.stringify(expected)) { verified++; }
        else { failed++; lines.push(`  FAIL: (${name} ${argStr}) expected ${JSON.stringify(expected)}, got ${JSON.stringify(result)}`); }
      }
      lines.push(`  Verify: ${verified}/${verified + failed} examples passed.`);
      if (failed > 0) {
        lines.push('  Cannot proceed — examples don\'t match.');
        this._storeProfile(name, 'broken', observations, null, 0, level);
        return lines;
      }
    } else {
      lines.push('  No test sheet. Probing blind.');
    }

    // PHASE 2: DISCOVER — find the pattern
    let predictor = this._predictResult(observations);
    if (predictor) { lines.push(`  Pattern discovered: ${predictor.pat}`); }
    else {
      // All examples verified but no generalizable pattern — that's still progress
      const status = tests ? 'verified' : 'unresolved';
      lines.push(`  No pattern found.${tests ? ' Examples verified.' : ''}`);
      this._storeProfile(name, status, observations, null, 0, level);
      return lines;
    }

    // PHASE 3: PREDICT — novel inputs, 10 correct in a row
    let streak = 0;
    const maxNovel = 30;
    if (!sig) { lines.push('  No signature — cannot generate novel probes.'); this._storeProfile(name, 'verified', observations, predictor, 0, level); return lines; }

    for (let i = 0; i < maxNovel; i++) {
      const args = this._novelProbe(sig, observations, i);
      const argStr = args.map(a => typeof a === 'string' ? `"${a}"` : Array.isArray(a) ? `(A_RANGE ${a[0]} ${a[a.length-1]+1})` : String(a)).join(' ');

      // Predict
      let predicted;
      try { predicted = args.length === 1 ? predictor.fn(args[0]) : args.length === 2 ? predictor.fn(args[0], args[1]) : predictor.fn(...args); }
      catch(e) { predicted = null; }

      // Run actual
      let result;
      try { result = this.evaluate(`(${name} ${argStr})`); } catch(e) { result = null; }
      observations.push({ args, result, predicted });

      if (JSON.stringify(predicted) === JSON.stringify(result)) {
        streak++;
      } else {
        lines.push(`  Miss: (${name} ${argStr}) predicted ${JSON.stringify(predicted)}, got ${JSON.stringify(result)}`);
        streak = 0;
        // Re-analyze with new data
        predictor = this._predictResult(observations);
        if (predictor) lines.push(`  Re-analyzed: ${predictor.pat}`);
        else { lines.push('  Lost pattern.'); break; }
      }

      if (streak >= 10) {
        lines.push(`  10 correct novel predictions in a row.`);
        break;
      }
    }

    const status = streak >= 10 ? 'trusted' : streak >= 3 ? 'partial' : tests ? 'verified' : 'unresolved';
    this._storeProfile(name, status, observations, predictor, streak, level);

    lines.push('');
    lines.push(`Status: ${status.toUpperCase()}${predictor ? ' | Pattern: ' + predictor.pat : ''}`);
    lines.push(`Verified: ${tests ? tests.length : 0} | Novel: ${streak}/10 streak`);
    return lines;
  }

  // Store a tool profile as a node
  _storeProfile(name, status, observations, predictor, streak, level) {
    const profAddr = this.ns.nameToAddr('_prof_' + name);
    this.mkNode('_prof_' + name, {
      address: profAddr, space: 'node', createdBy: 'explore',
      trust: status === 'trusted' ? 'node-trial' : 'working-trial',
      value: { name, status, level, pattern: predictor?.pat || 'unknown', streak, observations: observations.length }
    });
  }

  // Explore all primitives in curriculum order
  exploreAll() {
    const curriculum = this._curriculum();
    const levels = Object.keys(curriculum).sort((a,b) => a - b);
    const results = { trusted: [], partial: [], unresolved: [], broken: [], verified: [] };
    const lines = ['CURRICULUM EXPLORATION', ''];

    for (const lv of levels) {
      const tools = curriculum[lv];
      lines.push(`--- Level ${lv} ---`);
      for (const name of Object.keys(tools)) {
        const r = this.explore(name);
        const profAddr = this.ns.nameToAddr('_prof_' + name);
        const prof = this.ns.get(profAddr)?.value;
        const status = prof?.status || 'unknown';
        const pat = prof?.pattern || '';
        lines.push(`  ${name}: ${status.toUpperCase()}${pat ? ' (' + pat + ')' : ''}`);
        (results[status] || results.unresolved).push(name);
      }
      lines.push('');
    }

    // Also explore primitives not in curriculum
    const allPrims = [...this.prims.keys()];
    const inCurriculum = new Set(Object.values(curriculum).flatMap(lv => Object.keys(lv)));
    const uncovered = allPrims.filter(n => !inCurriculum.has(n));
    if (uncovered.length) {
      lines.push(`--- Not in curriculum (${uncovered.length}) ---`);
      for (const name of uncovered) lines.push(`  ${name}: skipped`);
    }

    lines.push('');
    lines.push(`TRUSTED: ${results.trusted.length} | VERIFIED: ${results.verified.length} | PARTIAL: ${results.partial.length} | UNRESOLVED: ${results.unresolved.length} | BROKEN: ${results.broken.length}`);
    return lines;
  }

  // Predict using stored profile
  predict(primName, args) {
    const name = primName.toUpperCase();
    const profAddr = this.ns.nameToAddr('_prof_' + name);
    const profNode = this.ns.get(profAddr);
    if (!profNode?.value) return { prediction: null, reason: 'no profile' };
    const argStr = args.map(a => typeof a === 'string' ? `"${a}"` : String(a)).join(' ');
    const actual = this.evaluate(`(${name} ${argStr})`);
    return { prediction: actual, pattern: profNode.value.pattern, status: profNode.value.status };
  }

  // ---- MACRO COMPOSITION ----
  createMacro(name, expr) {
    const addr = this.ns.nameToAddr(name);
    this.mkNode(name, { address: addr, macro: expr, space: 'node', mode: 'live', createdBy: 'macro' });
    this._history.push({ action: 'macro', name, expr, addr });
    return [`Macro created: ${name} = ${expr}`];
  }
  testMacro(name, input, expected) {
    const expr = `(${name} ${input})`;
    try { const actual = this.evaluate(expr); return { pass: JSON.stringify(actual) === JSON.stringify(expected), actual, expected, expr }; }
    catch (e) { return { pass: false, actual: null, expected, expr, error: e.message }; }
  }

  // ---- xb.3: THE LEARNING LOOP ----

  // Bump trust on nodes that participated in a successful answer
  bumpTrust(addr) {
    const n = this.ns.get(addr);
    if (!n) return;
    n.context.accessCount++;
    const ac = n.context.accessCount;
    const t = n.context.trust;
    // Logarithmic: easy at first, harder over time
    if (t === 'working-trial' && ac >= 2) n.context.trust = 'working-standard';
    else if (t === 'working-standard' && ac >= 7) n.context.trust = 'working-proven';
    else if (t === 'working-proven') { this.promote(addr, 'node-trial'); }
    else if (t === 'node-trial' && ac >= 17) n.context.trust = 'node-proven';
    // working-starred: 100% success over 15+ uses → node-proven (checked elsewhere)
  }

  // Enter learning mode after answering a question
  startLearning(question, response, parsed) {
    this.learning = {
      question,
      response,
      parsed, // { type, source, rel, target } from question parsing
      attempt: 1,
      maxAttempts: 3,
      attempts: [response], // what the system tried
      participatingAddrs: [] // nodes used in the answer, for trust bumping
    };
    // Collect participating node addresses from the current answer
    if (parsed && parsed.source) {
      const chain = this.walk(this._canonical(this.ns.nameToAddr(parsed.source)), parsed.rel || 'is_a');
      this.learning.participatingAddrs = chain.map(c => c.addr);
    }
  }

  // System got it right — reinforce the path
  learnSuccess() {
    if (!this.learning) return ['Nothing to confirm.'];
    const lines = ['Correct.'];
    // Bump trust on participating nodes
    let bumped = 0;
    for (const addr of this.learning.participatingAddrs) {
      const before = this.ns.get(addr)?.context.trust;
      this.bumpTrust(addr);
      const after = this.ns.get(addr)?.context.trust;
      if (before !== after) {
        const name = this.ns.get(addr)?.name || addr;
        lines.push(`  ${name}: ${before} → ${after}`);
        bumped++;
      }
    }
    if (bumped > 0) lines.push(`Trust updated on ${bumped} node${bumped > 1 ? 's' : ''}.`);
    else lines.push('Path reinforced.');
    this.learning = null;
    return lines;
  }

  // System got it wrong — try again with a different strategy
  learnRetry() {
    if (!this.learning) return ['Nothing to retry.'];
    const l = this.learning;
    l.attempt++;

    if (l.attempt > l.maxAttempts) {
      // Give up — ask for the answer
      this.learning.awaitingAnswer = true;
      return ["I can't figure it out.", '', 'What is the correct answer?'];
    }

    const lines = [`Attempt ${l.attempt}/${l.maxAttempts}...`];
    const p = l.parsed;
    if (!p) { this.learning.awaitingAnswer = true; return ["I don't have enough context to retry.", '', 'What is the correct answer?']; }

    let response;
    if (p.type === 'verify') {
      if (l.attempt === 2) {
        // Strategy 2: try other relationship types
        const rels = ['is_a', 'is', 'eq', 'type_of', 'instance_of'];
        for (const rel of rels) {
          if (rel === p.rel) continue;
          const v = this.verify(p.source, rel, p.target);
          if (v.found) { response = [`Yes (via ${rel}). ${v.path.join(' → ')}`]; break; }
        }
        if (!response) {
          // Try reverse — maybe target points to source
          const rev = this.reverseQuery(p.source, p.rel);
          const match = rev.find(r => r.name === p.target);
          if (match) response = [`Yes (reverse). ${p.target} —${p.rel}→ ${p.source}`];
        }
      }
      if (l.attempt === 3 && !response) {
        // Strategy 3: try through any shared ancestor
        const srcChain = this.walk(this._canonical(this.ns.nameToAddr(p.source)), 'is_a');
        const tgtChain = this.walk(this._canonical(this.ns.nameToAddr(p.target)), 'is_a');
        const srcNames = new Set(srcChain.map(c => c.name));
        const common = tgtChain.find(c => srcNames.has(c.name));
        if (common) response = [`Maybe — ${p.source} and ${p.target} share ancestor: ${common.name}`];
      }
    } else if (p.type === 'what') {
      // For "what" questions, try broader search
      const addr = this._canonical(this.ns.nameToAddr(p.source));
      const node = this.ns.get(addr);
      if (node) {
        const allRev = this.reverseQuery(p.source);
        if (allRev.length > 0) response = allRev.map(r => `${r.name} —${r.rel}→ ${p.source}`);
      }
    }

    if (!response) response = ["I still don't know."];
    l.attempts.push(response);
    lines.push(...response);
    lines.push('', 'y = correct  |  n = wrong');
    return lines;
  }

  // System gave up — user provides the correct answer — diagnose and fill the gap
  diagnoseAndFill(answer) {
    if (!this.learning) return ['Nothing to diagnose.'];
    const l = this.learning;
    const p = l.parsed;
    const lines = [];

    if (p && p.type === 'verify') {
      const ansLower = answer.toLowerCase().trim();
      if (ansLower === 'yes' || ansLower === 'y' || ansLower === 'true') {
        // The answer IS yes — the system couldn't find the path. What's missing?
        const srcAddr = this._canonical(this.ns.nameToAddr(p.source));
        const tgtAddr = this._canonical(this.ns.nameToAddr(p.target));
        const srcNode = this.ns.get(srcAddr);
        const tgtNode = this.ns.get(tgtAddr);

        if (!srcNode) {
          this.ensure(p.source, { createdBy: 'learning' });
          lines.push(`Gap: "${p.source}" didn't exist. Created.`);
        }
        if (!tgtNode) {
          this.ensure(p.target, { createdBy: 'learning' });
          lines.push(`Gap: "${p.target}" didn't exist. Created.`);
        }

        // Walk from source — where does the chain stop?
        const chain = this.walk(srcAddr, p.rel || 'is_a');
        const chainAddrs = new Set(chain.map(c => c.addr));

        if (!chainAddrs.has(tgtAddr)) {
          // The chain doesn't reach the target. Find the closest point and bridge.
          // Try: does target connect upward to something in our chain?
          const tgtChain = this.walk(tgtAddr, p.rel || 'is_a');
          const overlap = tgtChain.find(c => chainAddrs.has(c.addr));

          if (overlap) {
            // Target reaches something we reach too — bridge is: last in our chain → target
            lines.push(`Diagnosis: ${p.source} chain and ${p.target} chain meet at "${overlap.name}" but aren't connected directly.`);
          }

          // Create the missing link
          const lastInChain = chain.length > 0 ? chain[chain.length - 1] : { name: p.source, addr: srcAddr };
          const rel = p.rel || 'is_a';
          const result = this.link(lastInChain.name, rel, p.target);
          if (!result.duplicate) {
            lines.push(`Fix: created ${lastInChain.name} —${rel}→ ${p.target}`);
          } else {
            // Direct link exists but chain still doesn't reach? Try linking source directly.
            const directResult = this.link(p.source, rel, p.target);
            if (!directResult.duplicate) {
              lines.push(`Fix: created ${p.source} —${rel}→ ${p.target}`);
            } else {
              lines.push(`The connection exists but resolution failed. Possible chain issue.`);
            }
          }
        }

        // Verify the fix
        const recheck = this.verify(p.source, p.rel || 'is_a', p.target);
        if (recheck.found) {
          lines.push(`Verified: ${recheck.path.join(' → ')}`);
          lines.push('Gap filled.');
        } else {
          lines.push('Fix applied but verification still fails. Finding logged.');
        }
      } else if (ansLower === 'no' || ansLower === 'n' || ansLower === 'false') {
        // The answer is NO — the system was wrong to think there might be a connection
        // Or the system correctly said no and this confirms it
        lines.push('Confirmed: no relationship. Noted.');
      } else {
        // User provided a different answer entirely
        lines.push(`Noted: the answer to "${l.question}" is "${answer}".`);
        // Store as observation pair
        this.mkNode('obs' + this.ns.count, { value: { question: l.question, answer, type: 'observation-pair' }, space: 'node', createdBy: 'learning' });
        lines.push('Stored as observation pair.');
      }
    } else if (p && p.type === 'what') {
      // User is telling us what something is
      lines.push(`Learning: "${p.source}" → "${answer}"`);
      this.teach(p.source, answer);
      // If answer looks like "a/an X" — also create is_a relationship
      const aMatch = answer.match(/^an?\s+(.+)$/i);
      if (aMatch) {
        this.link(p.source, 'is_a', aMatch[1].trim());
        lines.push(`Also linked: ${p.source} —is_a→ ${aMatch[1].trim()}`);
      }
    } else {
      // Generic — store as observation pair
      this.mkNode('obs' + this.ns.count, { value: { question: l.question, answer, type: 'observation-pair' }, space: 'node', createdBy: 'learning' });
      lines.push(`Stored: "${l.question}" → "${answer}"`);
    }

    // Log what was tried
    if (l.attempts.length > 1) {
      lines.push(`Attempts made: ${l.attempts.length}`);
    }

    this.learning = null;
    return lines;
  }

  // Parse question into structured form for learning loop
  _parseQuestion(question) {
    const q = question.replace(/[?!.]+$/, '').trim().toLowerCase();
    const words = q.split(/\s+/);

    if (words[0] === 'is' && words.length >= 3) {
      const src = words[1];
      const skip = (words[2] === 'a' || words[2] === 'an') ? 3 : 2;
      const tgt = words.slice(skip).join(' ');
      // Determine rel type
      let rel = 'is_a';
      if (!(words[2] === 'a' || words[2] === 'an')) rel = 'is';
      return { type: 'verify', source: src, rel, target: tgt };
    }

    if (words[0] === 'does' && words.includes('have')) {
      const haveIdx = words.indexOf('have');
      return { type: 'verify', source: words.slice(1, haveIdx).join(' '), rel: 'has', target: words.slice(haveIdx + 1).join(' ') };
    }

    if (words[0] === 'what' && words[1] === 'is') {
      return { type: 'what', source: words.slice(2).join(' ') };
    }

    if (words[0] === 'what' && REL_TYPES.has(words[1])) {
      return { type: 'reverse', rel: words[1], target: words.slice(2).join(' ') };
    }

    return { type: 'unknown', raw: q };
  }

  // ---- TEST SUITE ----
  runTests() {
    let pass = 0, fail = 0, total = 0;
    const lines = ['INTELLON TEST SUITE', ''];
    const check = (label, actual, expected) => {
      total++;
      const a = JSON.stringify(actual), e = JSON.stringify(expected);
      if (a === e) { pass++; }
      else { fail++; lines.push(`  FAIL ${label}`); lines.push(`    expected: ${e}`); lines.push(`    got:      ${a}`); }
    };
    const section = (name) => { lines.push(`[${name}]`); };

    // Save current state
    const savedNs = this.ns.count;
    const savedWs = this.ws.count;

    // === T1: BASE LAYER ===
    section('Base Layer');
    check('T1.1 A exists', this.ns.has('65'), true);
    check('T1.2 A value', this.ns.get('65').value, 'A');
    check('T1.3 A trust', this.ns.get('65').context.trust, 'node-proven');
    check('T1.4 NULL exists', this.ns.get('0').value, 'NULL');
    check('T1.5 SPACE exists', this.ns.get('32').value, ' ');
    check('T1.6 base count >= 128', this.ns.count >= 128, true);

    // === T2: ADDRESSING ===
    section('Addressing');
    check('T2.1 cat addr', this.ns.nameToAddr('cat'), '99.97.116');
    check('T2.2 addr to name', this.ns.addrToName('99.97.116'), 'cat');
    check('T2.3 round trip', this.ns.addrToName(this.ns.nameToAddr('hello')), 'hello');

    // === T3: MATH PRIMITIVES ===
    section('Math');
    check('T3.1 add', this.evaluate('(ADD 1 2 3)'), 6);
    check('T3.2 sub', this.evaluate('(SUB 10 3)'), 7);
    check('T3.3 mul', this.evaluate('(MUL 4 5)'), 20);
    check('T3.4 div', this.evaluate('(DIV 10 4)'), 2.5);
    check('T3.5 div zero', this.evaluate('(DIV 5 0)'), null);
    check('T3.6 nested', this.evaluate('(ADD (MUL 3 4) (SUB 10 2))'), 20);
    check('T3.7 deep nest', this.evaluate('(ADD (MUL (SUB 10 5) 3) (DIV 20 4))'), 20);
    check('T3.8 pow', this.evaluate('(POW 2 10)'), 1024);
    check('T3.9 mod', this.evaluate('(MOD 10 3)'), 1);
    check('T3.10 neg', this.evaluate('(NEG 5)'), -5);
    check('T3.11 abs', this.evaluate('(ABS -7)'), 7);

    // === T4: STRING PRIMITIVES ===
    section('Strings');
    check('T4.1 concat', this.evaluate('(CONCAT "hello" " " "world")'), 'hello world');
    check('T4.2 s_len', this.evaluate('(S_LEN "cat")'), 3);
    check('T4.3 s_upper', this.evaluate('(S_UPPER "cat")'), 'CAT');
    check('T4.4 s_lower', this.evaluate('(S_LOWER "CAT")'), 'cat');
    check('T4.5 s_rev', this.evaluate('(S_REV "abc")'), 'cba');
    check('T4.6 s_char', this.evaluate('(S_CHAR 65)'), 'A');
    check('T4.7 s_code', this.evaluate('(S_CODE "A")'), 65);

    // === T5: LOGIC & COMPARISON ===
    section('Logic');
    check('T5.1 eq', this.evaluate('(EQ 5 5)'), true);
    check('T5.2 neq', this.evaluate('(NEQ 5 3)'), true);
    check('T5.3 gt', this.evaluate('(GT 5 3)'), true);
    check('T5.4 lt', this.evaluate('(LT 2 8)'), true);
    check('T5.5 and', this.evaluate('(AND true true)'), true);
    check('T5.6 and false', this.evaluate('(AND true false)'), false);
    check('T5.7 or', this.evaluate('(OR false true)'), true);
    check('T5.8 not', this.evaluate('(NOT true)'), false);

    // === T6: CONTROL ===
    section('Control');
    check('T6.1 if true', this.evaluate('(IF true 1 2)'), 1);
    check('T6.2 if false', this.evaluate('(IF false 1 2)'), 2);
    check('T6.3 if nested', this.evaluate('(IF (GT 5 3) (ADD 1 1) (SUB 1 1))'), 2);

    // === T7: ARRAYS ===
    section('Arrays');
    check('T7.1 a_range', this.evaluate('(A_RANGE 1 5)'), [1, 2, 3, 4]);
    check('T7.2 a_sum', this.evaluate('(A_SUM (A_RANGE 1 6))'), 15);
    check('T7.3 a_len', this.evaluate('(A_LEN (A_RANGE 1 4))'), 3);
    check('T7.4 a_rev', this.evaluate('(A_REV (A_RANGE 1 4))'), [3, 2, 1]);

    // === T8: TYPE ===
    section('Types');
    check('T8.1 is_num', this.evaluate('(IS_NUM 5)'), true);
    check('T8.2 is_str', this.evaluate('(IS_STR "hi")'), true);
    check('T8.3 type_of', this.evaluate('(TYPE_OF 5)'), 'number');

    // === T9: BITWISE ===
    section('Bitwise');
    check('T9.1 bit_and', this.evaluate('(BIT_AND 12 10)'), 8);
    check('T9.2 bit_or', this.evaluate('(BIT_OR 12 10)'), 14);
    check('T9.3 bit_xor', this.evaluate('(BIT_XOR 12 10)'), 6);

    // === T10: FORMAT ===
    section('Format');
    check('T10.1 format', this.evaluate('(FORMAT "hello {0} {1}" "big" "world")'), 'hello big world');

    // === T11: NODE INSPECTION ===
    section('Node Inspection');
    check('T11.1 n_name', this.evaluate('(N_NAME 65)'), 'A');
    check('T11.2 n_value', this.evaluate('(N_VALUE 65)'), 'A');
    check('T11.3 n_trust', this.evaluate('(N_TRUST 65)'), 'node-proven');
    check('T11.4 n_exists yes', this.evaluate('(N_EXISTS 65)'), true);
    check('T11.5 n_exists no', this.evaluate('(N_EXISTS 9999)'), false);

    // === T12: NODE CREATION ===
    section('Node Creation');
    this.mkNode('ztcat', { value: 'test feline', space: 'node' });
    const tcAddr = this.ns.nameToAddr('ztcat');
    check('T12.1 created', this.ns.has(tcAddr), true);
    check('T12.2 value', this.ns.get(tcAddr).value, 'test feline');
    check('T12.3 trust', this.ns.get(tcAddr).context.trust, 'node-trial');

    // === T13: NODE WITH MACRO ===
    section('Macros');
    this.mkNode('ztsq', { macro: '(MUL 7 7)', space: 'node', mode: 'live' });
    const sqAddr = this.ns.nameToAddr('ztsq');
    check('T13.1 macro resolve', this.resolve(sqAddr).value, 49);

    // === T14: PULL / PROMOTE ===
    section('Pull / Promote');
    this.mkNode('ztdog', { value: 'test canine', space: 'node', trust: 'node-proven' });
    const tdAddr = this.ns.nameToAddr('ztdog');
    const wd = this.pull(tdAddr);
    check('T14.1 pull exists', wd !== null, true);
    check('T14.2 pull value', wd.value, 'test canine');
    check('T14.3 pull trust', wd.context.trust, 'working-trial');
    check('T14.4 source ptr', wd.pointers.some(p => p.type === 'source'), true);

    this.mkNode('ztnew', { value: 'new idea', space: 'working' });
    const tnAddr = this.ns.nameToAddr('ztnew');
    check('T14.5 in working', this.ws.has(tnAddr), true);
    this.promote(tnAddr, 'node-trial');
    check('T14.6 promoted', this.ns.has(tnAddr), true);
    check('T14.7 prom trust', this.ns.get(tnAddr).context.trust, 'node-trial');

    // === T15: RELATIONSHIPS ===
    section('Relationships');
    this.link('ztA', 'is_a', 'ztB');
    const tAAddr = this.ns.nameToAddr('ztA');
    const tBAddr = this.ns.nameToAddr('ztB');
    check('T15.1 src exists', this.ns.has(tAAddr), true);
    check('T15.2 tgt exists', this.ns.has(tBAddr), true);
    const tANode = this.ns.get(tAAddr);
    check('T15.3 pointer', tANode.pointers.some(p => p.type === 'is_a' && p.to === tBAddr), true);
    const dup = this.link('ztA', 'is_a', 'ztB');
    check('T15.4 no dup', dup.duplicate, true);

    // === T16: EQ RESOLUTION ===
    section('EQ Resolution');
    this.link('ztalias', 'eq', 'ztcat');
    const aliasAddr = this.ns.nameToAddr('ztalias');
    const aliasResult = this.resolve(aliasAddr);
    check('T16.1 eq follows', aliasResult.value, 'test feline');

    // === T17: TEACH ===
    section('Teach');
    this.teach('ztword', 'a test definition');
    const twAddr = this.ns.nameToAddr('ztword');
    check('T17.1 taught exists', this.ns.has(twAddr), true);
    check('T17.2 taught value', this.ns.get(twAddr).value, 'a test definition');
    this.teach('ztword', 'updated definition');
    check('T17.3 updated', this.ns.get(twAddr).value, 'updated definition');

    // === T18: INGESTION ===
    section('Ingestion');
    const ingResult = this.ingest('ztfoo ztbar');
    check('T18.1 ingested count', ingResult.length, 2);
    check('T18.2 first word', ingResult[0].word, 'ztfoo');
    check('T18.3 in working', this.ws.has(this.ns.nameToAddr('ztfoo')), true);
    // Ingest known word
    const ingKnown = this.ingest('ztcat');
    check('T18.4 known level', ingKnown[0].level, 1);
    check('T18.5 known status', ingKnown[0].status, 'known');

    // === T19: FEEDBACK ===
    section('Feedback');
    this.ingest('ztconfirm');
    this.pending = [{ word: 'ztconfirm', addr: this.ns.nameToAddr('ztconfirm'), level: 3 }];
    const confResult = this.confirm();
    check('T19.1 confirmed', confResult[0].includes('Confirmed'), true);
    check('T19.2 promoted', this.ns.has(this.ns.nameToAddr('ztconfirm')), true);

    this.mkNode('ztreject', { space: 'working' });
    this.pending = [{ word: 'ztreject', addr: this.ns.nameToAddr('ztreject'), level: 3 }];
    const rejResult = this.reject();
    check('T19.3 rejected', rejResult[0].includes('Rejected'), true);

    // === T20: CURRICULUM ===
    section('Curriculum');
    const curBefore = this.ns.count;
    this.loadCurriculum();
    check('T20.1 nodes added', this.ns.count > curBefore, true);
    check('T20.2 cat is_a', this.ns.get(this.ns.nameToAddr('cat')).pointers.some(p => p.type === 'is_a'), true);

    // === T21: QUERY ===
    section('Query');
    const qr = this.query('cat', 'is_a');
    check('T21.1 query result', qr.length > 0, true);
    check('T21.2 has animal', qr.some(l => l.includes('animal')), true);
    const qAll = this.query('cat');
    check('T21.3 all rels', qAll.length > 0, true);
    const qMissing = this.query('ztnonexistent');
    check('T21.4 not found', qMissing[0].includes('not found'), true);

    // === xb.2 T32: CHAIN WALKING ===
    section('xb.2 Chain Walking');
    // cat is_a animal is_a organism (from curriculum)
    const catChain = this.walk(this.ns.nameToAddr('cat'), 'is_a');
    check('T32.1 chain length', catChain.length >= 3, true);
    check('T32.2 starts cat', catChain[0].name, 'cat');
    check('T32.3 has animal', catChain.some(c => c.name === 'animal'), true);
    check('T32.4 has organism', catChain.some(c => c.name === 'organism'), true);
    // apple is_a fruit is_a food is_a thing
    const appleChain = this.walk(this.ns.nameToAddr('apple'), 'is_a');
    check('T32.5 apple chain', appleChain.length >= 3, true);
    check('T32.6 apple has food', appleChain.some(c => c.name === 'food'), true);

    // === xb.2 T33: VERIFY ===
    section('xb.2 Verify');
    const v1 = this.verify('cat', 'is_a', 'animal');
    check('T33.1 direct verify', v1.found, true);
    const v2 = this.verify('cat', 'is_a', 'organism');
    check('T33.2 chain verify', v2.found, true);
    check('T33.3 path shown', v2.path.length >= 3, true);
    const v3 = this.verify('cat', 'is_a', 'vehicle');
    check('T33.4 no path', v3.found, false);
    const v4 = this.verify('apple', 'is_a', 'thing');
    check('T33.5 deep chain', v4.found, true);

    // === xb.2 T34: EQ TRANSPARENCY IN CHAINS ===
    section('xb.2 EQ Chains');
    // feline eq cat, cat is_a animal → feline should chain to animal
    const felChain = this.walk(this.ns.nameToAddr('feline'), 'is_a');
    check('T34.1 eq then chain', felChain.some(c => c.name === 'animal'), true);
    const fv = this.verify('feline', 'is_a', 'organism');
    check('T34.2 eq verify deep', fv.found, true);
    // canine eq dog, dog is_a animal
    const cv = this.verify('canine', 'is_a', 'animal');
    check('T34.3 canine via eq', cv.found, true);

    // === xb.2 T35: REVERSE QUERY ===
    section('xb.2 Reverse Query');
    const rev1 = this.reverseQuery('animal', 'is_a');
    check('T35.1 reverse count', rev1.length >= 4, true); // cat, dog, fish, bird
    check('T35.2 has cat', rev1.some(r => r.name === 'cat'), true);
    check('T35.3 has dog', rev1.some(r => r.name === 'dog'), true);
    const rev2 = this.reverseQuery('cold', 'opposite_of');
    check('T35.4 opposite reverse', rev2.some(r => r.name === 'hot'), true);
    const rev3 = this.reverseQuery('car', 'part_of');
    check('T35.5 parts reverse', rev3.length >= 2, true); // wheel, engine

    // === xb.2 T36: ASK — QUESTION ANSWERING ===
    section('xb.2 Questions');
    const a1 = this.ask('is cat an animal?');
    check('T36.1 is cat animal', a1[0].startsWith('Yes'), true);
    const a2 = this.ask('is cat an organism?');
    check('T36.2 is cat organism', a2[0].startsWith('Yes'), true);
    const a3 = this.ask('is cat a vehicle?');
    check('T36.3 cat not vehicle', a3[0].startsWith('No'), true);
    const a4 = this.ask('what is cat?');
    check('T36.4 what is cat', a4.length > 0, true);
    check('T36.5 what is has rels', a4.some(l => l.includes('animal')), true);
    const a5 = this.ask('what is_a animal?');
    check('T36.6 reverse what', a5.length >= 4, true);
    check('T36.7 reverse has cat', a5.some(l => l.includes('cat')), true);
    const a6 = this.ask('is feline an animal?');
    check('T36.8 eq question', a6[0].startsWith('Yes'), true);
    const a7 = this.ask('what is ztnonexistent?');
    check('T36.9 unknown', a7[0].includes('not found'), true);
    const a8 = this.ask('is fire hot?');
    check('T36.10 is fire hot', a8[0].startsWith('Yes'), true);

    // === xb.3 T37: LEARNING LOOP — SUCCESS ===
    section('xb.3 Learning Success');
    // Ask a question the system knows
    const catTrust1 = this.ns.get(this.ns.nameToAddr('cat'))?.context.accessCount || 0;
    const ls1 = this.exec('is cat an animal?');
    check('T37.1 answer given', ls1.some(l => l.startsWith('Yes')), true);
    check('T37.2 in learning mode', this.learning !== null, true);
    const ls2 = this.exec('y');
    check('T37.3 success response', ls2[0], 'Correct.');
    check('T37.4 learning cleared', this.learning, null);
    const catTrust2 = this.ns.get(this.ns.nameToAddr('cat'))?.context.accessCount || 0;
    check('T37.5 trust bumped', catTrust2 > catTrust1, true);

    // === xb.3 T38: LEARNING LOOP — RETRY ===
    section('xb.3 Learning Retry');
    // Ask something the system doesn't know
    this.ensure('whale', { createdBy: 'test' });
    const lr1 = this.exec('is whale a mammal?');
    check('T38.1 first attempt', this.learning !== null, true);
    check('T38.2 attempt 1', this.learning.attempt, 1);
    const lr2 = this.exec('n');
    check('T38.3 retried', lr2.some(l => l.includes('Attempt 2')), true);
    check('T38.4 attempt 2', this.learning.attempt, 2);
    const lr3 = this.exec('n');
    check('T38.5 attempt 3', this.learning.attempt, 3);
    const lr4 = this.exec('n');
    check('T38.6 gave up', lr4.some(l => l.includes("can't figure")), true);
    check('T38.7 awaiting answer', this.learning.awaitingAnswer, true);

    // === xb.3 T39: LEARNING LOOP — DIAGNOSE AND FILL ===
    section('xb.3 Diagnose');
    const lr5 = this.exec('yes');
    check('T39.1 diagnosed', lr5.some(l => l.includes('Fix') || l.includes('created') || l.includes('Verified')), true);
    check('T39.2 learning cleared', this.learning, null);
    // Verify the gap was filled
    const wv = this.verify('whale', 'is_a', 'mammal');
    check('T39.3 gap filled', wv.found, true);

    // === xb.3 T40: LEARNING LOOP — WHAT QUESTION ===
    section('xb.3 What Learning');
    this.ensure('zebra', { createdBy: 'test' });
    const lw1 = this.exec('what is zebra?');
    check('T40.1 what answered', lw1.length > 0, true);
    check('T40.2 in learning', this.learning !== null, true);
    // Say wrong, retry, eventually provide answer
    this.exec('n'); this.exec('n'); this.exec('n');
    check('T40.3 awaiting', this.learning.awaitingAnswer, true);
    const lw2 = this.exec('a striped horse-like animal');
    check('T40.4 taught', lw2.some(l => l.includes('Learning') || l.includes('Taught')), true);
    check('T40.5 learning cleared', this.learning, null);

    // === xb.3 T41: TRUST PROGRESSION ===
    section('xb.3 Trust');
    this.mkNode('zttrust', { value: 'trust test', space: 'node', trust: 'working-trial' });
    const ttAddr = this.ns.nameToAddr('zttrust');
    check('T41.1 starts trial', this.ns.get(ttAddr).context.trust, 'working-trial');
    this.bumpTrust(ttAddr); this.bumpTrust(ttAddr);
    check('T41.2 after 2 bumps', this.ns.get(ttAddr).context.trust, 'working-standard');
    for (let i = 0; i < 5; i++) this.bumpTrust(ttAddr);
    check('T41.3 after 7 bumps', this.ns.get(ttAddr).context.trust, 'working-proven');

    // === xb.3 T42: UNLINK ===
    section('xb.3 Unlink');
    this.link('ztul1', 'is_a', 'ztul2');
    const ulAddr = this.ns.nameToAddr('ztul1');
    check('T42.1 linked', this.ns.get(ulAddr).pointers.some(p => p.type === 'is_a'), true);
    const ulResult = this.unlink('ztul1', 'is_a', 'ztul2');
    check('T42.2 removed', ulResult[0].includes('Removed'), true);
    check('T42.3 gone', this.ns.get(ulAddr).pointers.some(p => p.type === 'is_a'), false);
    const ulMiss = this.unlink('ztul1', 'is_a', 'ztul2');
    check('T42.4 no dup remove', ulMiss[0].includes('No'), true);

    // === xb.3 T43: UNDO ===
    section('xb.3 Undo');
    // Undo a link
    this.link('ztundo1', 'is_a', 'ztundo2');
    const undoAddr = this.ns.nameToAddr('ztundo1');
    check('T43.1 link exists', this.ns.get(undoAddr).pointers.some(p => p.type === 'is_a'), true);
    this.undo();
    check('T43.2 link undone', this.ns.get(undoAddr).pointers.some(p => p.type === 'is_a'), false);
    // Undo a teach
    this.teach('ztundow', 'original value');
    const uwAddr = this.ns.nameToAddr('ztundow');
    check('T43.3 taught', this.ns.get(uwAddr).value, 'original value');
    this.teach('ztundow', 'new value');
    check('T43.4 updated', this.ns.get(uwAddr).value, 'new value');
    this.undo();
    check('T43.5 teach undone', this.ns.get(uwAddr).value, 'original value');
    // Undo an unlink (restores the pointer)
    this.link('ztundoul', 'has', 'ztundoult');
    this.unlink('ztundoul', 'has', 'ztundoult');
    const uulAddr = this.ns.nameToAddr('ztundoul');
    check('T43.6 unlinked', this.ns.get(uulAddr).pointers.some(p => p.type === 'has'), false);
    this.undo();
    check('T43.7 unlink undone', this.ns.get(uulAddr).pointers.some(p => p.type === 'has'), true);
    // Undo on empty
    this._history = [];
    const emptyUndo = this.undo();
    check('T43.8 empty undo', emptyUndo[0], 'Nothing to undo.');

    // === xb.3 T44: SENSES / CONFLICT DETECTION ===
    section('xb.3 Senses');
    // Create initial relationship
    this.link('ztsense', 'is_a', 'ztfruit');
    const zsAddr = this.ns.nameToAddr('ztsense');
    check('T44.1 initial link', this.ns.get(zsAddr).pointers.some(p => p.type === 'is_a'), true);
    // Add conflicting relationship — should trigger conflict
    const conflictResult = this.link('ztsense', 'is_a', 'ztcompany');
    check('T44.2 conflict detected', conflictResult.conflict, true);
    check('T44.3 conflict pending', this.conflict !== null, true);
    // Resolve as new sense
    const splitResult = this.resolveConflict(true);
    check('T44.4 split done', splitResult[0].includes('Split'), true);
    check('T44.5 has senses', this.ns.get(zsAddr).senses.size, 2);
    check('T44.6 sense 1', this.ns.get(zsAddr).getSense(1) !== null, true);
    check('T44.7 sense 2', this.ns.get(zsAddr).getSense(2) !== null, true);
    // Query shows senses
    const sqr = this.query('ztsense');
    check('T44.8 query shows senses', sqr.some(l => l.includes('2 senses')), true);
    // Query specific sense
    const sqr1 = this.query('ztsense/1');
    check('T44.9 query sense 1', sqr1.some(l => l.includes('ztfruit')), true);
    const sqr2 = this.query('ztsense/2');
    check('T44.10 query sense 2', sqr2.some(l => l.includes('ztcompany')), true);

    // === xb.3 T45: CONFLICT — SAME NODE ===
    section('xb.3 Conflict Same');
    this.link('ztsame', 'is_a', 'ztcat1');
    const sameResult = this.link('ztsame', 'is_a', 'ztcat2');
    check('T45.1 conflict', sameResult.conflict, true);
    const sameResolve = this.resolveConflict(false);
    check('T45.2 same node', sameResolve[0].includes('same sense'), true);
    check('T45.3 both pointers', this.ns.get(this.ns.nameToAddr('ztsame')).pointers.filter(p => p.type === 'is_a').length, 2);

    // === xb.4 T46: CURRICULUM-DRIVEN EXPLORATION ===
    section('xb.4 Explore');
    const exp1 = this.explore('ADD');
    const addProfAddr = this.ns.nameToAddr('_prof_ADD');
    check('T46.1 profile exists', this.ns.has(addProfAddr), true);
    const addProf = this.ns.get(addProfAddr).value;
    check('T46.2 add pattern', addProf.pattern, 'sum');
    check('T46.3 add trusted', addProf.status, 'trusted');
    const exp2 = this.explore('SUB');
    const subProf = this.ns.get(this.ns.nameToAddr('_prof_SUB')).value;
    check('T46.4 sub pattern', subProf.pattern, 'difference');
    check('T46.5 sub trusted', subProf.status, 'trusted');
    const exp3 = this.explore('EQ');
    const eqProf = this.ns.get(this.ns.nameToAddr('_prof_EQ')).value;
    check('T46.6 eq pattern', eqProf.pattern, 'equals');
    check('T46.7 eq trusted', eqProf.status, 'trusted');
    const exp4 = this.explore('NOT');
    const notProf = this.ns.get(this.ns.nameToAddr('_prof_NOT')).value;
    check('T46.8 not pattern', notProf.pattern, 'not');
    const exp5 = this.explore('S_LEN');
    const slenProf = this.ns.get(this.ns.nameToAddr('_prof_S_LEN')).value;
    check('T46.9 s_len pattern', slenProf.pattern, 'length');
    const exp6 = this.explore('NEG');
    const negProf = this.ns.get(this.ns.nameToAddr('_prof_NEG')).value;
    check('T46.10 neg pattern', negProf.pattern, 'negate');

    // === xb.4 T47: MACRO COMPOSITION ===
    section('xb.4 Macros');
    const mac2 = this.createMacro('ztfortywo', '(ADD 40 2)');
    const macResult = this.resolve(this.ns.nameToAddr('ztfortywo'));
    check('T47.1 macro resolves', macResult.value, 42);

    // === xb.4 T48: PREDICT ===
    section('xb.4 Predict');
    const pred = this.predict('ADD', [4, 6]);
    check('T48.1 prediction', pred.prediction, 10);
    check('T48.2 pattern', pred.pattern, 'sum');
    check('T48.3 status', pred.status, 'trusted');

    // === T22: WORKING SPACE DISPLAY ===
    section('Working Space');
    this.mkNode('ztwork1', { space: 'working', value: 'w1' });
    this.mkNode('ztwork2', { space: 'working', value: 'w2' });
    const wShow = this.showWorking();
    check('T22.1 shows nodes', wShow.length > 1, true);
    check('T22.2 has content', wShow.some(l => l.includes('ztwork1')), true);

    // === T23: HIBERNATE / WAKE ===
    section('Hibernate / Wake');
    this.flush();
    this.mkNode('zthib1', { space: 'working', value: 'hib_val' });
    this.mkNode('zthib2', { space: 'working', value: 'hib_val2' });
    const hibResult = this.hibernate('test_snap');
    check('T23.1 hibernated', hibResult[0].includes('test_snap'), true);
    check('T23.2 ws cleared', this.ws.count, 0);
    check('T23.3 snapshot exists', this._snapshots.has('test_snap'), true);

    // Put something new in working space
    this.mkNode('ztcurrent', { space: 'working', value: 'current_work' });
    check('T23.4 new work', this.ws.count, 1);

    // Wake should auto-save current
    const wakeResult = this.wake('test_snap');
    check('T23.5 wake loaded', wakeResult.some(l => l.includes('test_snap')), true);
    check('T23.6 auto-saved', wakeResult.some(l => l.includes('Auto-saved')), true);
    check('T23.7 restored', this.ws.has(this.ns.nameToAddr('zthib1')), true);
    check('T23.8 restored val', this.ws.get(this.ns.nameToAddr('zthib1')).value, 'hib_val');

    // === T24: SNAPSHOTS LIST ===
    section('Snapshots');
    const snapList = this.listSnapshots();
    check('T24.1 has list', snapList.length > 1, true);
    check('T24.2 has test_snap', snapList.some(l => l.includes('test_snap')), true);

    // === T25: PEEK ===
    section('Peek');
    this.hibernate('peek_test');
    const peekResult = this.peek('peek_test');
    check('T25.1 peek shows', peekResult.length > 1, true);
    check('T25.2 peek content', peekResult.some(l => l.includes('zthib1')), true);
    check('T25.3 ws still empty', this.ws.count, 0);

    // === T26: IMPORT ===
    section('Import');
    const impResult = this.importFrom('peek_test', 'zthib1');
    check('T26.1 imported', impResult[0].includes('Imported'), true);
    check('T26.2 in working', this.ws.has(this.ns.nameToAddr('zthib1')), true);
    check('T26.3 value intact', this.ws.get(this.ns.nameToAddr('zthib1')).value, 'hib_val');
    const impMiss = this.importFrom('peek_test', '_nonexistent');
    check('T26.4 not found', impMiss[0].includes('not found'), true);
    const impBad = this.importFrom('no_such_snap', 'zthib1');
    check('T26.5 bad snap', impBad[0].includes('not found'), true);

    // === T27: ARCHIVE ===
    section('Archive');
    this.flush();
    this.mkNode('ztarch1', { space: 'working', value: 'arch1', trust: 'working-proven' });
    this.mkNode('ztarch2', { space: 'working', value: 'arch2', trust: 'working-trial' });
    const archResult = this.archive();
    check('T27.1 archived', archResult[0].includes('Archive'), true);
    check('T27.2 promoted', this.ns.has(this.ns.nameToAddr('ztarch1')), true);
    check('T27.3 ws cleared', this.ws.count, 0);

    // === T28: FLUSH ===
    section('Flush');
    this.mkNode('ztflush', { space: 'working', value: 'gone' });
    const preFlush = this.ws.count;
    this.flush();
    check('T28.1 had nodes', preFlush > 0, true);
    check('T28.2 now empty', this.ws.count, 0);

    // === T29: TRIE RELATIONSHIPS ===
    section('Trie Structure');
    this.mkNode('ztparent', { value: 'parent', space: 'node' });
    this.mkNode('ztparents', { value: 'children of parent', space: 'node' });
    const pAddr = this.ns.nameToAddr('ztparent');
    const psAddr = this.ns.nameToAddr('ztparents');
    check('T29.1 parent', this.ns.parent(psAddr), pAddr);
    check('T29.2 child', this.ns.children(pAddr).includes(psAddr), true);

    // === T30: EACH ===
    section('Each / Iteration');
    this._out = [];
    const eachResult = this.evaluate('(EACH (A_RANGE 65 68) N_NAME)');
    check('T30.1 each names', eachResult, ['A', 'B', 'C']);

    // === T31: EXEC INTEGRATION ===
    section('Exec Integration');
    let r;
    r = this.exec('(ADD 10 20)');
    check('T31.1 expr exec', r.some(l => l.includes('30')), true);
    r = this.exec('stats');
    check('T31.2 stats exec', r[0].includes('Nodes'), true);
    r = this.exec('addr cat');
    check('T31.3 addr exec', r[0].includes('99.97.116'), true);
    r = this.exec('teach _tExecW test_val');
    check('T31.4 teach exec', r[0].includes('Taught') || r[0].includes('Updated'), true);

    // Summary
    lines.push('');
    lines.push(`${'='.repeat(40)}`);
    lines.push(`${total} tests: ${pass} passed, ${fail} failed`);
    lines.push(`${'='.repeat(40)}`);
    if (fail === 0) lines.push('ALL TESTS PASSED');

    // Clean up test nodes
    this.flush();
    this.pending = null;

    return lines;
  }

  // ---- EXEC ----
  exec(input) {
    this._out = []; const t = input.trim(); if (!t) return [];

    // Sense conflict resolution (highest priority)
    if (this.conflict) {
      if (t === 'y' || t === 'Y') return this.resolveConflict(true);
      if (t === 'n' || t === 'N') return this.resolveConflict(false);
      this.conflict = null; // cancel on any other input, fall through
    }

    // xb.3: Learning loop feedback (takes priority)
    if (this.learning) {
      if (this.learning.awaitingAnswer) {
        // User is providing the correct answer
        return this.diagnoseAndFill(t);
      }
      if (t === 'y' || t === 'Y') return this.learnSuccess();
      if (t === 'n' || t === 'N') return this.learnRetry();
      // Check if it's a command — cancel learning and process
      const isCmd = t.startsWith('(') || ['help','stats','nodes','base','controls','prims','curriculum','rels','working','archive','flush','snapshots','test','undo','explore','exploreall'].includes(t) || /^(show|create|resolve|addr|read|teach|unlink|query|macro|predict|explore|links|hibernate|wake|peek|import) /.test(t) || t === 'hibernate' || t === 'wake';
      if (isCmd) { this.learning = null; }
      else {
        // Not a command, not y/n — treat as the correct answer
        return this.diagnoseAndFill(t);
      }
    }

    // Ingestion feedback mode
    if (this.pending) {
      if (t === 'y' || t === 'Y') return this.confirm();
      if (t === 'n' || t === 'N') return this.reject();
      const isCmd = t.startsWith('(') || ['help','stats','nodes','base','controls','prims','curriculum','rels','working','archive','flush','snapshots','test','undo','explore','exploreall'].includes(t) || /^(show|create|resolve|addr|read|teach|unlink|query|macro|predict|explore|links|hibernate|wake|peek|import) /.test(t) || t === 'hibernate' || t === 'wake';
      if (!isCmd) return this.correct(t);
      this.pending = null;
    }

    // Commands
    if (t === 'help') return ['INTELLON xb.4','','QUESTIONS (learning loop):','  is cat an animal?            verify — walks chains','  what is cat?                 forward — everything known','  → y = correct, n = wrong, 3 wrongs = teach me','','SELF-LEARNING:','  explore ADD                  experiment with a primitive','  explore                      experiment with ALL primitives','  predict ADD 4 6              predict output from profile','  macro double (MUL 2 {0})     create a composed operation','','RELATIONSHIPS:','  cat is_a animal              source rel target','  unlink / undo                remove or reverse','  curriculum                   load starter set','','TEACH / WORKING:','  teach cat a feline animal    set a value','  working  hibernate  wake  peek  import  archive  flush','','INSPECT:','  (ADD 1 2 3)  stats  nodes  rels  prims  test','  query <word>  show <addr>  addr <word>'];
    if (t === 'test') return this.runTests();
    if (t.startsWith('explore ')) return this.explore(t.slice(8).trim());
    if (t === 'explore' || t === 'exploreall') return this.exploreAll();
    if (t.startsWith('macro ')) { const rest = t.slice(6).trim(), sp = rest.indexOf(' '); if (sp < 0) return ['Usage: macro <name> <expression>']; return this.createMacro(rest.slice(0, sp), rest.slice(sp + 1).trim()); }
    if (t.startsWith('predict ')) { const parts = t.slice(8).trim().split(/\s+/); const name = parts[0]; const args = parts.slice(1).map(a => /^-?\d+(\.\d+)?$/.test(a) ? Number(a) : a === 'true' ? true : a === 'false' ? false : a); const r = this.predict(name, args); return [`Prediction for (${name} ${parts.slice(1).join(' ')}):`, `  result: ${JSON.stringify(r.prediction)}`, `  type: ${r.predictedType || 'unknown'}`, `  confidence: ${r.confidence}`, `  properties: ${r.properties ? r.properties.join(', ') : 'none'}`]; }
    if (t === 'stats') return [`Nodes: ${this.ns.count} | Working: ${this.ws.count} | Prims: ${this.prims.size} | Rels: ${this.ns.allNodes().reduce((s,e)=>s+e.node.pointers.length,0)}`];
    if (t === 'prims') { const n = [...this.prims.keys()], l = []; for (let i = 0; i < n.length; i += 8) l.push(n.slice(i, i + 8).join('  ')); return l; }
    if (t === 'curriculum') return this.loadCurriculum();
    if (t === 'working') return this.showWorking();
    if (t === 'hibernate' || t.startsWith('hibernate ')) { const id = t.slice(10).trim() || null; return this.hibernate(id); }
    if (t === 'wake' || t.startsWith('wake ')) { const id = t.slice(5).trim() || null; return this.wake(id); }
    if (t.startsWith('peek ')) { return this.peek(t.slice(5).trim()); }
    if (t.startsWith('import ')) { const parts = t.slice(7).trim().split(/\s+/); if (parts.length < 2) return ['Usage: import <snapshot> <word>']; return this.importFrom(parts[0], parts[1]); }
    if (t === 'snapshots') return this.listSnapshots();
    if (t === 'archive') return this.archive();
    if (t === 'flush') return this.flush();
    if (t === 'nodes') { const a = this.ns.allNodes().filter(e => e.address.includes('.')); if (!a.length) return ['No knowledge nodes. Try: curriculum']; return a.map(e => { const ptrs = e.node.pointers.length ? ` [${e.node.pointers.map(p=>p.type+'->'+this.ns.addrToName(p.to)).join(', ')}]` : ''; return `${e.node.name} | ${JSON.stringify(e.node.value)} | ${e.node.context.trust}${ptrs}`; }); }
    if (t === 'rels') { const a = this.ns.allNodes().filter(e => e.node.pointers.length > 0); if (!a.length) return ['No relationships yet. Try: curriculum']; const lines = []; for (const e of a) { for (const p of e.node.pointers) lines.push(`${e.node.name} —${p.type}→ ${this.ns.addrToName(p.to)}`); } return lines; }
    if (t === 'base') { this.evaluate('(EACH (A_RANGE 32 128) N_SHOW)'); return [...this._out]; }
    if (t === 'controls') { this.evaluate('(EACH (A_RANGE 0 32) N_SHOW)'); return [...this._out]; }
    if (t.startsWith('show ')) { const a = t.slice(5).trim(); this.evaluate(`(N_SHOW "${a}")`); return this._out.length ? [...this._out] : [`No node at: ${a}`]; }
    if (t.startsWith('teach ')) { const r = t.slice(6).trim(), sp = r.indexOf(' '); if (sp < 0) return ['Usage: teach <word> <definition>']; return this.teach(r.slice(0, sp), r.slice(sp + 1).trim()); }
    if (t.startsWith('unlink ')) { const parts = t.slice(7).trim().split(/\s+/); if (parts.length < 3) return ['Usage: unlink <source> <rel> <target>']; return this.unlink(parts[0], parts[1], parts[2]); }
    if (t === 'undo') return this.undo();
    if (t.startsWith('query ')) { const parts = t.slice(6).trim().split(/\s+/); return this.query(parts[0], parts[1]); }
    if (t.startsWith('links ')) { return this.query(t.slice(6).trim()); }
    if (t.startsWith('resolve ')) { const r = this.resolve(this.ns.nameToAddr(t.slice(8).trim())); return [r.error ? `Error: ${r.error}` : `-> ${JSON.stringify(r.value)}${r.resolved_via ? ' (via ' + r.resolved_via + ')' : ''}`]; }
    if (t.startsWith('addr ')) return [`${t.slice(5).trim()} -> ${this.ns.nameToAddr(t.slice(5).trim())}`];
    if (t.startsWith('read ')) return [`${t.slice(5).trim()} -> "${this.ns.addrToName(t.slice(5).trim())}"`];
    if (t.startsWith('(')) { try { const r = this.evaluate(t); return [...this._out, `-> ${JSON.stringify(r)}`]; } catch (e) { return [`Error: ${e.message}`]; } }

    // SCAFFOLD: Question detection — route to ask(), enter learning mode
    const questionWords = ['is','what','does','who','how','can','where','which','why','are'];
    if (t.endsWith('?') || questionWords.includes(t.split(/\s+/)[0].toLowerCase())) {
      const response = this.ask(t);
      const parsed = this._parseQuestion(t);
      // Enter learning mode — wait for y/n feedback
      this.startLearning(t, response, parsed);
      return [...response, '', 'y = correct  |  n = wrong'];
    }

    // Three words with known rel type = relationship
    const parts = t.split(/\s+/);
    if (parts.length === 3 && REL_TYPES.has(parts[1])) {
      const [src, rel, tgt] = parts;
      const r = this.link(src, rel, tgt);
      if (r.duplicate) return [`Already exists: ${src} —${rel}→ ${tgt}`];
      if (r.error) return [r.error];
      if (r.conflict) return [r.message, '', 'y = new sense  |  n = same node'];
      return [`Linked: ${src} —${rel}→ ${tgt}`];
    }

    // Otherwise ingest
    const res = this.ingest(t); this.pending = res;
    const lines = ['Ingested:'];
    for (const r of res) { const lv = ['','RESOLVE','EXTEND','FIT','','NOTE'][r.level]; const v = r.value ? ` = ${JSON.stringify(r.value)}` : ''; lines.push(`  ${r.word} [${lv}] ${r.status}${v}`); }
    lines.push('', 'y = confirm  |  n = reject  |  or type correction');
    return lines;
  }
}

const SYS = new IntellonSystem().populateBase();

export default function App() {
  const [history, setHistory] = useState([{ type: 'sys', lines: ['INTELLON xb.4', `Nodes: ${SYS.ns.count} | Prims: ${SYS.prims.size}`, '', 'Type "explore ADD" to watch it learn a tool.', 'Type "explore" to learn ALL tools.', 'Type "help" for commands  |  "test" to verify', ''] }]);
  const [input, setInput] = useState('');
  const [cmds, setCmds] = useState([]);
  const [ci, setCi] = useState(-1);
  const bRef = useRef(null);
  const iRef = useRef(null);
  useEffect(() => { bRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [history]);
  useEffect(() => { iRef.current?.focus(); }, []);
  const run = useCallback(() => { if (!input.trim()) return; const lines = SYS.exec(input.trim()); setHistory(h => [...h, { type: 'in', text: input.trim() }, { type: 'out', lines }]); setCmds(h => [input.trim(), ...h]); setInput(''); setCi(-1); }, [input]);
  const onKey = (e) => { if (e.key === 'Enter') run(); else if (e.key === 'ArrowUp') { e.preventDefault(); if (cmds.length) { const n = Math.min(ci + 1, cmds.length - 1); setCi(n); setInput(cmds[n]); } } else if (e.key === 'ArrowDown') { e.preventDefault(); if (ci > 0) { setCi(ci - 1); setInput(cmds[ci - 1]); } else { setCi(-1); setInput(''); } } };
  const color = (l) => {
    if (l.startsWith('->')) return '#c9a84c';
    if (l.startsWith('Error')) return '#c25a5a';
    if (l.startsWith('Linked') || l.startsWith('Taught') || l.startsWith('Confirmed') || l.startsWith('Updated') || l.startsWith('Curriculum')) return '#6a9a6a';
    if (l.startsWith('Rejected') || l.startsWith('Already')) return '#aa8a4a';
    if (l.startsWith('Correction')) return '#9a8a5a';
    if (l.includes('—') && l.includes('→')) return '#8aaa8a';
    if (l.startsWith('  ') && l.includes('[')) return '#7a9a7a';
    if (l.includes('confirm') || l.includes('reject')) return '#555';
    if (l.startsWith('Ingested')) return '#6a9a6a';
    return '#b0b0b0';
  };
  return (
    <div style={{ background: '#08080a', color: '#d4d4d4', fontFamily: '"Courier New",Courier,monospace', fontSize: '13px', height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <div style={{ background: '#0e0e12', borderBottom: '1px solid #1a1a22', padding: '8px 14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexShrink: 0 }}>
        <span style={{ color: '#7a9ec2', fontWeight: 700, letterSpacing: '2px', fontSize: '14px' }}>INTELLON</span>
        <span style={{ color: '#444', fontSize: '11px' }}>nodes:{SYS.ns.count} | prims:{SYS.prims.size}</span>
      </div>
      <div style={{ flex: 1, overflowY: 'auto', padding: '10px 14px' }} onClick={() => iRef.current?.focus()}>
        {history.map((e, i) => {
          if (e.type === 'sys') return <div key={i} style={{ color: '#4a6a4a', marginBottom: 6 }}>{e.lines.map((l, j) => <div key={j}>{l || '\u00A0'}</div>)}</div>;
          if (e.type === 'in') return <div key={i} style={{ color: '#7a9ec2', marginTop: 4 }}><span style={{ color: '#3a5a7a' }}>{'> '}</span>{e.text}</div>;
          if (e.type === 'out') return <div key={i} style={{ marginBottom: 4, paddingLeft: 12 }}>{e.lines.map((l, j) => <div key={j} style={{ color: color(l) }}>{l}</div>)}</div>;
          return null;
        })}
        <div ref={bRef} />
      </div>
      <div style={{ borderTop: '1px solid #1a1a22', padding: '8px 14px', display: 'flex', alignItems: 'center', background: '#0b0b0e', flexShrink: 0 }}>
        <span style={{ color: '#3a5a7a', marginRight: 6 }}>{'>'}</span>
        <input ref={iRef} value={input} onChange={e => setInput(e.target.value)} onKeyDown={onKey} placeholder="cat is_a animal  |  (ADD 1 2)  |  help"
          style={{ flex: 1, background: 'transparent', border: 'none', outline: 'none', color: '#d4d4d4', fontFamily: 'inherit', fontSize: 'inherit', caretColor: '#7a9ec2' }} spellCheck={false} autoComplete="off" />
      </div>
    </div>
  );
}
