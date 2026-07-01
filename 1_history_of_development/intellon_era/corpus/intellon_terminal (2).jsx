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

    // xb.5: Relationship inspection primitives (work on word names, not addresses)
    this._p('N_HAS_PTR', (name, rel) => {
      if (typeof name !== 'string' || typeof rel !== 'string') return null;
      const addr = s._canonical(s.ns.nameToAddr(name));
      const n = s.ns.get(addr); if (!n) return false;
      return n.pointers.some(p => p.type === rel);
    });
    this._p('N_PTR', (name, rel) => {
      if (typeof name !== 'string' || typeof rel !== 'string') return null;
      const addr = s._canonical(s.ns.nameToAddr(name));
      const n = s.ns.get(addr); if (!n) return null;
      const p = n.pointers.find(p => p.type === rel);
      return p ? s.ns.addrToName(p.to) : null;
    });
    this._p('N_CHAIN', (name, rel) => {
      if (typeof name !== 'string' || typeof rel !== 'string') return null;
      const addr = s._canonical(s.ns.nameToAddr(name));
      if (!s.ns.has(addr)) return null;
      const chain = s.walk(addr, rel);
      return chain.map(c => c.name);
    });
    this._p('N_VERIFY', (source, rel, target) => {
      if (typeof source !== 'string' || typeof rel !== 'string' || typeof target !== 'string') return null;
      return s.verify(source, rel, target).found;
    });
    this._p('N_GATHER', name => {
      if (typeof name !== 'string') return null;
      const g = s.gather(name);
      if (!g) return null;
      const parts = [];
      if (g.direct.length) parts.push('Direct: ' + g.direct.map(d => `${d.rel}→${d.target}`).join(', '));
      if (g.chains.filter(c => c.depth > 1).length) parts.push('Chains: ' + g.chains.filter(c => c.depth > 1).map(c => c.path.join('→')).join('; '));
      if (g.negatives.length) parts.push('NOT: ' + g.negatives.map(n => n.target).join(', '));
      if (g.reverse.length) parts.push('Reverse: ' + g.reverse.map(r => `${r.source}—${r.rel}`).join(', '));
      return parts.join(' | ') || 'no relationships';
    });
    this._p('N_INFER', name => {
      if (typeof name !== 'string') return null;
      const g = s.gather(name);
      if (!g) return null;
      // Find chain endpoints that don't have direct pointers
      const directTargets = new Set(g.direct.map(d => d.targetAddr));
      const negTargets = new Set(g.negatives.map(n => n.targetAddr));
      const inferred = [];
      for (const c of g.chains) {
        for (let i = 1; i < c.addrs.length; i++) {
          if (!directTargets.has(c.addrs[i]) && !negTargets.has(c.addrs[i])) {
            inferred.push(`${c.rel}→${c.path[i]}`);
          }
        }
      }
      return [...new Set(inferred)]; // deduplicate
    });
  }

  populateBase() {
    const ctrl = ['NULL', 'WILDCARD', 'TRUE', 'FALSE', 'UNDEFINED', 'SELF', 'CALLER', 'PASS', 'FAIL', 'TAB', 'NEWLINE', 'UNK', 'BREAK', 'RETURN', 'CONTINUE', 'OPTIONAL', 'EOS', 'BOS', 'EOP', 'EOI', 'PAD', 'WORD_BOUNDARY', 'SENTENCE_BOUNDARY', 'CLAUSE_BOUNDARY', 'PHRASE_BOUNDARY', 'ANY_TYPE', 'ANY_NUMBER', 'ANY_STRING', 'IF_MARKER', 'THEN_MARKER', 'ELSE_MARKER', 'SEPARATOR'];
    for (let i = 0; i < ctrl.length; i++) this.ns.set(String(i), new Node(String(i), ctrl[i], { value: ctrl[i], trust: 'node-proven', createdBy: 'base' }));
    for (let c = 32; c <= 127; c++) this.ns.set(String(c), new Node(String(c), String.fromCharCode(c), { value: String.fromCharCode(c), trust: 'node-proven', createdBy: 'base' }));
    this._loadSignatures();
    this._loadOperationalCycle();
    return this;
  }

  // SCAFFOLD: Operational cycle as macros — observe/question/deduce/verify
  // These are composed from primitives. Eventually the system discovers these compositions itself.
  _loadOperationalCycle() {
    const macros = [
      ['observe', '(N_GATHER {0})',
        'Scan a node — returns everything known: direct pointers, chains, negatives, reverse'],
      ['question', '(IF (N_VERIFY {0} {1} {2}) (CONCAT "CONFIRMED: " {0} " —" {1} "→ " {2}) (CONCAT "UNCONFIRMED: no " {1} " path from " {0} " to " {2}))',
        'Challenge a claim — is there a verified path?'],
      ['deduce', '(N_INFER {0})',
        'Infer — what can be concluded by chain walking that is not directly stated?'],
      ['verify_fact', '(N_VERIFY {0} {1} {2})',
        'Verify a specific claim — returns true/false'],
      ['has_property', '(N_HAS_PTR {0} {1})',
        'Check if a node has a specific relationship type'],
      ['follow', '(N_PTR {0} {1})',
        'Follow a single pointer — returns target name'],
      ['chain', '(N_CHAIN {0} {1})',
        'Walk a full chain — returns array of names'],
    ];
    for (const [name, expr, desc] of macros) {
      const addr = this.ns.nameToAddr(name);
      this.ns.set(addr, new Node(addr, name, {
        macro: expr, mode: 'live', trust: 'node-proven',
        createdBy: 'operational-cycle', value: desc
      }));
    }
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
      // Relationship inspection (work on word names)
      N_HAS_PTR:{in:[S,S],out:B,min:2}, N_PTR:{in:[S,S],out:S,min:2},
      N_CHAIN:{in:[S,S],out:R,min:2}, N_VERIFY:{in:[S,S,S],out:B,min:3},
      N_GATHER:{in:[S],out:S,min:1}, N_INFER:{in:[S],out:R,min:1},
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
  // Serialize a JS value back to expression syntax for macro substitution
  _valToExpr(v) {
    if (v === null) return 'null';
    if (typeof v === 'boolean') return String(v);
    if (typeof v === 'number') return String(v);
    if (typeof v === 'string') return `"${v}"`;
    if (Array.isArray(v)) return `(A_PUSH ${v.map(x => this._valToExpr(x)).join(' ')})`;  // SCAFFOLD: array literal
    return String(v);
  }
  _eval(a) {
    if (a.type === 'literal') return a.value;
    if (a.type === 'ref') { const r = this.resolve(a.address); return r.error === 'not-found' ? a.address : r.value; }
    if (a.type === 'call') {
      const op = a.op.toUpperCase(), fn = this.prims.get(op);
      // If not a primitive, check for macro node
      if (!fn) {
        const macroAddr = this.ns.nameToAddr(a.op);
        const macroNode = this.ns.get(macroAddr);
        if (macroNode && macroNode.macro) {
          // Evaluate args first, then substitute into macro template
          const evalArgs = a.args.map(x => this._eval(x));
          let expr = macroNode.macro;
          for (let i = 0; i < evalArgs.length; i++) {
            expr = expr.split(`{${i}}`).join(this._valToExpr(evalArgs[i]));
          }
          macroNode.touch();
          return this.evaluate(expr);
        }
        return null;
      }
      if (op === 'IF') { const c = this._eval(a.args[0]); return c ? (a.args[1] ? this._eval(a.args[1]) : null) : (a.args[2] ? this._eval(a.args[2]) : null); }
      return fn(...a.args.map(x => this._eval(x)));
    } return null;
  }
  mkNode(name, o = {}) { const a = o.address || this.ns.nameToAddr(name); const sp = o.space || 'working'; const tr = sp === 'node' ? this.ns : this.ws; return tr.set(a, new Node(a, name, { ...o, trust: o.trust || (sp === 'node' ? 'node-trial' : 'working-trial') })); }

  // ---- INGEST raw text ----
  ingest(text) {
    const words = text.split(/\s+/).filter(w => w.length > 0), results = [];
    const cleanWords = [];
    for (const raw of words) {
      const core = raw.replace(/^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$/g, ''); if (!core) continue;
      cleanWords.push(core);
      const addr = this.ns.nameToAddr(core);
      if (this.ns.has(addr)) { const n = this.ns.get(addr); n.touch(); results.push({ word: core, addr, level: 1, status: 'known', value: n.value }); continue; }
      const pa = this.ns.parent(addr);
      if (pa && this.ns.has(pa)) { const pn = this.ns.get(pa); this.mkNode(core, { address: addr, space: 'working', createdBy: 'extend' }).addPointer('extends', pa); results.push({ word: core, addr, level: 2, status: 'extends "' + pn.name + '"' }); continue; }
      this.mkNode(core, { address: addr, space: 'working', createdBy: core.length > 1 ? 'fit' : 'note' });
      results.push({ word: core, addr, level: core.length > 1 ? 3 : 5, status: core.length > 1 ? 'new' : 'noted' });
    }
    // Track adjacency for multi-word input
    if (cleanWords.length > 1) this._trackAdjacency(cleanWords);
    return results;
  }

  // ---- xb.5: ADJACENCY TRACKING ----
  // Record which words appear together and in what positions.
  // Raw data for grammar learning.
  _trackAdjacency(words) {
    for (let i = 0; i < words.length; i++) {
      const w = words[i].toLowerCase();
      const adjName = '_adj_' + w;
      const adjAddr = this.ns.nameToAddr(adjName);
      let adjNode = this.ns.get(adjAddr);
      if (!adjNode) {
        adjNode = this.mkNode(adjName, { address: adjAddr, space: 'node', createdBy: 'adjacency', value: { right: {}, left: {}, positions: [], count: 0 } });
      }
      const v = adjNode.value;
      if (!v.right) v.right = {};
      if (!v.left) v.left = {};
      if (!v.positions) v.positions = [];

      // Track position
      v.count = (v.count || 0) + 1;
      v.positions.push(i);

      // Right adjacency: what follows this word
      if (i < words.length - 1) {
        const next = words[i + 1].toLowerCase();
        v.right[next] = (v.right[next] || 0) + 1;
      }

      // Left adjacency: what precedes this word
      if (i > 0) {
        const prev = words[i - 1].toLowerCase();
        v.left[prev] = (v.left[prev] || 0) + 1;
      }

      adjNode.touch();
    }
  }

  // Display adjacency data for a word
  showAdjacency(word) {
    const w = word.toLowerCase();
    const adjName = '_adj_' + w;
    const adjAddr = this.ns.nameToAddr(adjName);
    const adjNode = this.ns.get(adjAddr);
    if (!adjNode || !adjNode.value) return [`No adjacency data for "${word}". Ingest some text first.`];
    const v = adjNode.value;
    const lines = [`ADJACENCY: ${w} (seen ${v.count}x)`];

    // Right neighbors (what follows)
    const rightEntries = Object.entries(v.right || {}).sort((a, b) => b[1] - a[1]);
    if (rightEntries.length) {
      lines.push('  Followed by:');
      for (const [neighbor, count] of rightEntries) {
        lines.push(`    → ${neighbor} (${count}x)`);
      }
    }

    // Left neighbors (what precedes)
    const leftEntries = Object.entries(v.left || {}).sort((a, b) => b[1] - a[1]);
    if (leftEntries.length) {
      lines.push('  Preceded by:');
      for (const [neighbor, count] of leftEntries) {
        lines.push(`    ${neighbor} → (${count}x)`);
      }
    }

    // Positions
    if (v.positions && v.positions.length) {
      lines.push(`  Positions: ${v.positions.join(', ')}`);
    }

    return lines;
  }

  // ---- xb.5: SENTENCE COMPREHENSION + ENTITY/STATE TRACKING ----
  // SCAFFOLD: Pattern-based sentence parsing. Eventually learned from data.

  // Discourse context — tracks entities across sentences
  _initDiscourse() {
    if (!this._discourse) {
      this._discourse = {
        entities: [],       // ordered list of mentioned entities (most recent last)
        states: new Map(),  // entity → current state working node
      };
    }
  }

  // SCAFFOLD: Strip articles and common noise words
  _stripArticle(word) {
    return ['the', 'a', 'an', 'this', 'that', 'these', 'those'].includes(word.toLowerCase()) ? null : word;
  }

  // SCAFFOLD: Pronoun resolution — backwards search for most recent entity
  _resolveReference(word) {
    this._initDiscourse();
    const w = word.toLowerCase();
    const pronouns = ['it', 'they', 'he', 'she', 'its', 'their', 'his', 'her'];
    if (pronouns.includes(w)) {
      // Return most recent entity
      if (this._discourse.entities.length > 0) {
        return this._discourse.entities[this._discourse.entities.length - 1];
      }
      return null;
    }
    return word;
  }

  // Track an entity mention in discourse
  _mentionEntity(name) {
    this._initDiscourse();
    const n = name.toLowerCase();
    // Move to end if already tracked
    this._discourse.entities = this._discourse.entities.filter(e => e !== n);
    this._discourse.entities.push(n);
    // Ensure entity has a state node in working space
    if (!this._discourse.states.has(n)) {
      const stateNode = this.mkNode('_state_' + n, {
        space: 'working', createdBy: 'comprehend',
        value: { entity: n, properties: {}, actions: [] }
      });
      this._discourse.states.set(n, stateNode);
    }
    return n;
  }

  // Get or create entity state
  _getEntityState(name) {
    this._initDiscourse();
    const n = name.toLowerCase();
    if (!this._discourse.states.has(n)) this._mentionEntity(n);
    const stateNode = this._discourse.states.get(n);
    // State node might have been cleared — recreate if needed
    if (!stateNode || !stateNode.value) {
      const newNode = this.mkNode('_state_' + n, {
        space: 'working', createdBy: 'comprehend',
        value: { entity: n, properties: {}, actions: [] }
      });
      this._discourse.states.set(n, newNode);
      return newNode.value;
    }
    return stateNode.value;
  }

  // Set a property on an entity state
  _setEntityProp(entity, prop, value) {
    const state = this._getEntityState(entity);
    state.properties[prop] = value;
    return state;
  }

  // Record an action
  _addEntityAction(entity, action, object) {
    const state = this._getEntityState(entity);
    state.actions.push({ action, object, time: Date.now() });
    // Check for causal effects via curriculum
    const causeAddr = this._canonical(this.ns.nameToAddr(action));
    const causeNode = this.ns.get(causeAddr);
    if (causeNode) {
      const effects = causeNode.pointers.filter(p => p.type === 'causes');
      for (const e of effects) {
        const effectName = this.ns.addrToName(e.to);
        this._setEntityProp(entity, effectName, true);
      }
    }
    return state;
  }

  // SCAFFOLD: Parse a single sentence into entity/state updates
  // Returns { subject, rel/action, object/property, type }
  _parseSentence(words) {
    if (words.length < 2) return null;

    // Resolve pronouns but keep articles for pattern matching
    const resolved = words.map(w => {
      const r = this._resolveReference(w);
      return r || w;
    });

    // Strip leading articles from subject only
    let startIdx = 0;
    while (startIdx < resolved.length && ['the', 'a', 'an', 'this', 'that'].includes(resolved[startIdx].toLowerCase())) startIdx++;
    if (startIdx >= resolved.length) return null;

    const subject = resolved[startIdx].toLowerCase();
    const rest = resolved.slice(startIdx + 1);
    if (rest.length === 0) return null;

    const verb = rest[0].toLowerCase();
    const results = [];

    // SCAFFOLD patterns — labeled for future replacement with learned parsing

    // Pattern: "X is a/an Y" → is_a relationship
    if (['is', 'are', 'was', 'were'].includes(verb) && rest.length >= 3 && ['a', 'an'].includes(rest[1].toLowerCase())) {
      const obj = rest.slice(2).map(w => this._stripArticle(w) || w).filter(w => !['a','an'].includes(w.toLowerCase())).join(' ').toLowerCase();
      results.push({ subject, rel: 'is_a', object: obj, type: 'classify' });
      return results;
    }

    // Pattern: "X is/was Y" → property
    if (['is', 'are', 'was', 'were'].includes(verb) && rest.length >= 2) {
      const obj = rest.slice(1).map(w => this._stripArticle(w) || w).join(' ').toLowerCase();
      results.push({ subject, rel: 'is', object: obj, type: 'property' });
      return results;
    }

    // Pattern: "X has/have Y" → has relationship
    if (['has', 'have', 'had'].includes(verb) && rest.length >= 2) {
      const obj = rest.slice(1).map(w => this._stripArticle(w) || w).filter(w => !['a','an','the'].includes(w.toLowerCase())).join(' ').toLowerCase();
      results.push({ subject, rel: 'has', object: obj, type: 'possession' });
      return results;
    }

    // Pattern: "X verb Y" → action
    if (rest.length >= 2) {
      const obj = rest.slice(1).map(w => this._stripArticle(w) || w).filter(w => !['the','a','an'].includes(w.toLowerCase())).join(' ').toLowerCase();
      results.push({ subject, action: verb, object: obj, type: 'action' });
      return results;
    }

    // Pattern: "X verb" → intransitive action
    if (rest.length === 1) {
      results.push({ subject, action: verb, object: null, type: 'action' });
      return results;
    }

    return null;
  }

  // Comprehend text: split into sentences, parse each, update entities
  comprehend(text) {
    this._initDiscourse();
    // Split on sentence boundaries
    const sentences = text.split(/[.!?]+/).map(s => s.trim()).filter(s => s.length > 0);
    const lines = [];

    for (const sent of sentences) {
      const words = sent.split(/\s+/).filter(w => w.length > 0);
      if (words.length === 0) continue;

      // Also ingest for adjacency tracking
      const cleanWords = words.map(w => w.replace(/^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$/g, '')).filter(w => w);
      if (cleanWords.length > 1) this._trackAdjacency(cleanWords);

      const parsed = this._parseSentence(cleanWords);
      if (!parsed || parsed.length === 0) {
        lines.push(`  ? "${sent}" (no pattern matched)`);
        continue;
      }

      for (const p of parsed) {
        // Track entity
        this._mentionEntity(p.subject);

        if (p.type === 'classify') {
          // is_a → create relationship
          this.link(p.subject, 'is_a', p.object);
          lines.push(`  ${p.subject} —is_a→ ${p.object}`);
        } else if (p.type === 'property') {
          // is → set property on entity state
          this._setEntityProp(p.subject, p.object, true);
          this.link(p.subject, 'is', p.object);
          lines.push(`  ${p.subject} is ${p.object}`);
        } else if (p.type === 'possession') {
          this.link(p.subject, 'has', p.object);
          lines.push(`  ${p.subject} —has→ ${p.object}`);
        } else if (p.type === 'action') {
          this._addEntityAction(p.subject, p.action, p.object);
          if (p.object) {
            this._mentionEntity(p.object);
            lines.push(`  ${p.subject} ${p.action} ${p.object}`);
          } else {
            lines.push(`  ${p.subject} ${p.action}`);
          }
        }
      }
    }

    return lines.length ? ['COMPREHEND:', ...lines] : ['No sentences parsed.'];
  }

  // Show entity state
  showEntity(name) {
    this._initDiscourse();
    const n = name.toLowerCase();
    if (!this._discourse.states.has(n)) return [`No entity state for "${name}".`];
    const state = this._getEntityState(n);
    const lines = [`ENTITY: ${n}`];

    const props = Object.entries(state.properties);
    if (props.length) {
      lines.push('  Properties:');
      for (const [k, v] of props) lines.push(`    ${k}: ${JSON.stringify(v)}`);
    }

    if (state.actions.length) {
      lines.push('  Actions:');
      for (const a of state.actions) {
        lines.push(`    ${a.action}${a.object ? ' ' + a.object : ''}`);
      }
    }

    if (!props.length && !state.actions.length) {
      lines.push('  (no state recorded)');
    }

    // Also show node-level relationships
    const g = this.gather(n);
    if (g && g.direct.length) {
      lines.push('  Relationships:');
      for (const d of g.direct) lines.push(`    ${n} —${d.rel}→ ${d.target}`);
    }

    return lines;
  }

  // Show all tracked entities
  showEntities() {
    this._initDiscourse();
    if (!this._discourse.entities.length) return ['No entities tracked. Try: comprehend <text>'];
    const lines = ['ENTITIES:'];
    for (const e of this._discourse.entities) {
      const state = this._getEntityState(e);
      const propCount = Object.keys(state.properties).length;
      const actionCount = state.actions.length;
      lines.push(`  ${e} | ${propCount} properties | ${actionCount} actions`);
    }
    return lines;
  }

  // Clear discourse context
  clearDiscourse() {
    this._discourse = null;
    return ['Discourse context cleared.'];
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

  // ---- xb.5: GATHER — the system's attention ----

  // Walk outward from a node, collect everything reachable.
  // Returns structured context: direct pointers, chains, negatives, reverse, senses, and a set of all reachable addresses.
  gather(word, maxDepth = 5) {
    const { word: w, sense: senseNum } = this.parseSlash(word);
    const rawAddr = this.ns.nameToAddr(w);
    const canonAddr = this._canonical(rawAddr);
    // Use raw node first — we want to see eq pointers as direct pointers
    const rawNode = this.ns.get(rawAddr);
    const canonNode = this.ns.get(canonAddr);
    if (!rawNode && !canonNode) return null;

    const result = {
      name: w, addr: rawAddr, canonAddr, node: rawNode || canonNode,
      direct: [],      // one-hop pointers: { rel, target, targetAddr }
      chains: [],       // walked paths: { rel, path: [names], addrs: [addrs], depth }
      negatives: [],    // not pointers: { target, targetAddr }
      reverse: [],      // what points here: { source, sourceAddr, rel }
      ancestors: new Set(), // all reachable addresses (for overlap)
      senseResults: new Map() // sense# → gather result (without senses recursion)
    };

    // If a specific sense, gather from that sense node
    const baseNode = rawNode || canonNode;
    const targetNode = (senseNum !== null) ? baseNode.getSense(senseNum) : baseNode;
    if (!targetNode) return null;

    // Collect direct pointers from the raw node
    for (const p of targetNode.pointers) {
      const tgtName = this.ns.addrToName(p.to);
      const canonTo = this._canonical(p.to);
      if (p.type === 'not') {
        result.negatives.push({ target: tgtName, targetAddr: canonTo });
      } else {
        result.direct.push({ rel: p.type, target: tgtName, targetAddr: canonTo });
      }
    }

    // If canonical differs, also collect the canonical node's pointers
    if (canonAddr !== rawAddr && canonNode) {
      for (const p of canonNode.pointers) {
        const tgtName = this.ns.addrToName(p.to);
        const canonTo = this._canonical(p.to);
        // Avoid duplicates
        if (p.type === 'not') {
          if (!result.negatives.some(n => n.targetAddr === canonTo)) {
            result.negatives.push({ target: tgtName, targetAddr: canonTo });
          }
        } else {
          if (!result.direct.some(d => d.rel === p.type && d.targetAddr === canonTo)) {
            result.direct.push({ rel: p.type, target: tgtName, targetAddr: canonTo });
          }
        }
      }
    }

    // Walk chains for each relationship type found in direct pointers
    const relTypes = new Set(result.direct.map(d => d.rel));
    const negativeAddrs = new Set(result.negatives.map(n => n.targetAddr));

    for (const relType of relTypes) {
      if (relType === 'eq') continue; // eq is structural, not a chain to walk
      // Walk this rel type starting from canonical address (where the real hierarchy lives)
      const visited = new Set();
      const chain = [];
      const _walkGather = (a, depth) => {
        if (depth > maxDepth || visited.has(a)) return;
        visited.add(a);
        const canonical = this._canonical(a);
        if (canonical !== a) visited.add(canonical);
        // Skip if this address is blocked by a not pointer
        if (negativeAddrs.has(canonical)) return;
        const n = this.ns.get(canonical);
        if (!n) return;
        chain.push({ addr: canonical, name: n.name });
        result.ancestors.add(canonical);
        // Also check not pointers on intermediate nodes to block further walking
        const intermediateNots = new Set(n.pointers.filter(p => p.type === 'not').map(p => this._canonical(p.to)));
        const rels = n.pointers.filter(p => p.type === relType);
        for (const r of rels) {
          const nextCanon = this._canonical(r.to);
          if (!intermediateNots.has(nextCanon)) {
            _walkGather(r.to, depth + 1);
          }
        }
      };
      _walkGather(canonAddr, 0);

      if (chain.length > 1) {
        // Replace the first entry name with the query word for clarity
        chain[0].name = w;
        result.chains.push({
          rel: relType,
          path: chain.map(c => c.name),
          addrs: chain.map(c => c.addr),
          depth: chain.length - 1
        });
      }
    }

    // Also add both addresses to ancestors
    result.ancestors.add(rawAddr);
    result.ancestors.add(canonAddr);

    // Reverse query: what points TO this node?
    // Use raw nodes — don't canonicalize the scanner, or we lose eq pointers
    const allNodes = this.ns.allNodes();
    for (const entry of allNodes) {
      const n = entry.node;
      const entryAddr = entry.address;
      if (entryAddr === rawAddr || entryAddr === canonAddr) continue; // skip self
      for (const p of n.pointers) {
        const pTo = this._canonical(p.to);
        if (pTo === rawAddr || pTo === canonAddr) {
          // Avoid duplicate reverse entries
          if (!result.reverse.some(r => r.sourceAddr === entryAddr && r.rel === p.type)) {
            result.reverse.push({ source: n.name, sourceAddr: entryAddr, rel: p.type });
          }
        }
      }
    }

    // Gather senses if present and no specific sense requested
    if (senseNum === null && baseNode.senses.size > 0) {
      for (const [num, senseNode] of baseNode.senses) {
        const senseGather = {
          direct: [], chains: [], negatives: [], ancestors: new Set()
        };
        for (const p of senseNode.pointers) {
          const tgtName = this.ns.addrToName(p.to);
          const canonTo = this._canonical(p.to);
          if (p.type === 'not') {
            senseGather.negatives.push({ target: tgtName, targetAddr: canonTo });
          } else {
            senseGather.direct.push({ rel: p.type, target: tgtName, targetAddr: canonTo });
            // Walk chains from sense pointers
            const senseChain = this.walk(canonTo, p.type, maxDepth);
            if (senseChain.length > 0) {
              senseGather.chains.push({ rel: p.type, path: [w + '/' + num, ...senseChain.map(c => c.name)], depth: senseChain.length });
              for (const c of senseChain) senseGather.ancestors.add(c.addr);
            }
          }
        }
        result.senseResults.set(num, senseGather);
        // Merge sense ancestors into main ancestors
        for (const a of senseGather.ancestors) result.ancestors.add(a);
      }
    }

    return result;
  }

  // Format gather result for display
  gatherDisplay(word) {
    const g = this.gather(word);
    if (!g) return [`"${word}" not found.`];
    const lines = [`GATHER: ${g.name}`];

    // Direct
    if (g.direct.length) {
      lines.push('  Direct:');
      for (const d of g.direct) lines.push(`    ${g.name} —${d.rel}→ ${d.target}`);
    }

    // Chains (only show chains longer than direct)
    const shownChains = g.chains.filter(c => c.depth > 1);
    if (shownChains.length) {
      lines.push('  Chains:');
      for (const c of shownChains) lines.push(`    ${c.path.join(' → ')} (via ${c.rel}, depth ${c.depth})`);
    }

    // Negatives
    if (g.negatives.length) {
      lines.push('  Negatives:');
      for (const n of g.negatives) lines.push(`    ${g.name} —NOT→ ${n.target}`);
    }

    // Reverse
    if (g.reverse.length) {
      lines.push('  Reverse:');
      for (const r of g.reverse) lines.push(`    ${r.source} —${r.rel}→ ${g.name}`);
    }

    // Senses
    if (g.senseResults.size > 0) {
      lines.push(`  Senses: ${g.senseResults.size}`);
      for (const [num, sg] of g.senseResults) {
        const rels = sg.direct.map(d => `${d.rel}→${d.target}`).join(', ');
        const nots = sg.negatives.length ? ` | NOT: ${sg.negatives.map(n => n.target).join(', ')}` : '';
        lines.push(`    /${num}: ${rels || 'no pointers'}${nots}`);
        for (const c of sg.chains.filter(ch => ch.depth > 1)) {
          lines.push(`      ${c.path.join(' → ')} (via ${c.rel})`);
        }
      }
    }

    if (g.direct.length === 0 && g.reverse.length === 0 && g.negatives.length === 0 && g.senseResults.size === 0) {
      lines.push('  (no relationships found)');
    }

    return lines;
  }

  // Relate: gather two nodes, find overlap, propose connections, report blocks
  relate(wordA, wordB) {
    const gA = this.gather(wordA);
    const gB = this.gather(wordB);
    if (!gA) return { error: `"${wordA}" not found` };
    if (!gB) return { error: `"${wordB}" not found` };

    const result = {
      a: gA, b: gB,
      known: [],     // direct pointers between A and B
      shared: [],    // common ancestors with the rel type and paths from each
      proposed: [],  // transitive connections that don't exist as direct pointers
      blocked: []    // not pointers preventing connections
    };

    const addrB = gB.canonAddr;
    const addrA = gA.canonAddr;
    const rawAddrB = gB.addr;
    const rawAddrA = gA.addr;
    const isAddrB = (a) => a === addrB || a === rawAddrB;
    const isAddrA = (a) => a === addrA || a === rawAddrA;

    // Known: direct pointers from A to B or B to A
    for (const d of gA.direct) {
      if (isAddrB(d.targetAddr)) result.known.push({ from: gA.name, rel: d.rel, to: gB.name, direction: 'A→B' });
    }
    for (const d of gB.direct) {
      if (isAddrA(d.targetAddr)) result.known.push({ from: gB.name, rel: d.rel, to: gA.name, direction: 'B→A' });
    }

    // Shared: walk both ancestors, find intersection per rel type
    // Group chains by rel type for each side
    const chainsByRelA = new Map();
    const chainsByRelB = new Map();
    for (const c of gA.chains) {
      if (!chainsByRelA.has(c.rel)) chainsByRelA.set(c.rel, []);
      chainsByRelA.get(c.rel).push(c);
    }
    for (const c of gB.chains) {
      if (!chainsByRelB.has(c.rel)) chainsByRelB.set(c.rel, []);
      chainsByRelB.get(c.rel).push(c);
    }

    // For each rel type present in both, find common addresses
    for (const [rel, chainsA] of chainsByRelA) {
      const chainsB = chainsByRelB.get(rel);
      if (!chainsB) continue;
      const addrsA = new Set(chainsA.flatMap(c => c.addrs));
      for (const chainB of chainsB) {
        for (let i = 0; i < chainB.addrs.length; i++) {
          if (addrsA.has(chainB.addrs[i]) && !isAddrA(chainB.addrs[i])) {
            const ancestor = chainB.path[i];
            // Find the path from A to this ancestor
            const pathA = chainsA.find(c => c.addrs.includes(chainB.addrs[i]));
            if (pathA) {
              const idxA = pathA.addrs.indexOf(chainB.addrs[i]);
              result.shared.push({
                ancestor,
                ancestorAddr: chainB.addrs[i],
                rel,
                pathFromA: pathA.path.slice(0, idxA + 1),
                pathFromB: chainB.path.slice(0, i + 1)
              });
            }
          }
        }
      }
    }

    // Deduplicate shared by ancestor address + rel
    const seen = new Set();
    result.shared = result.shared.filter(s => {
      const key = s.ancestorAddr + ':' + s.rel;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });

    // Proposed: transitive connections A could have via chains that it doesn't have as direct pointers
    // For each chain A walks, check if B appears anywhere (or vice versa)
    // If A chains to X and B chains to X via same rel, and A doesn't directly point to B's ancestors, propose
    for (const s of result.shared) {
      // If A reaches ancestor Z via is_a, and B reaches Z via is_a,
      // but A doesn't directly point to any of B's chain — propose nothing (they're siblings, not parent-child)
      // HOWEVER: if A chains to Z and Z chains to somewhere B has a direct pointer, that might be a proposal
      // For now: propose if B is IN A's chain (transitive reachability)
      for (const c of gA.chains) {
        if (c.addrs.some(isAddrB)) {
          const exists = gA.direct.some(d => isAddrB(d.targetAddr) && d.rel === c.rel);
          if (!exists) {
            result.proposed.push({ from: gA.name, rel: c.rel, to: gB.name, via: c.path.join(' → ') });
          }
        }
      }
      for (const c of gB.chains) {
        if (c.addrs.some(isAddrA)) {
          const exists = gB.direct.some(d => isAddrA(d.targetAddr) && d.rel === c.rel);
          if (!exists) {
            result.proposed.push({ from: gB.name, rel: c.rel, to: gA.name, via: c.path.join(' → ') });
          }
        }
      }
    }

    // Blocked: not pointers from A that match anything in B's tree, or vice versa
    for (const neg of gA.negatives) {
      if (gB.ancestors.has(neg.targetAddr) || isAddrB(neg.targetAddr)) {
        result.blocked.push({ from: gA.name, blocked: neg.target, reason: `${gA.name} —NOT→ ${neg.target}` });
      }
    }
    for (const neg of gB.negatives) {
      if (gA.ancestors.has(neg.targetAddr) || isAddrA(neg.targetAddr)) {
        result.blocked.push({ from: gB.name, blocked: neg.target, reason: `${gB.name} —NOT→ ${neg.target}` });
      }
    }

    // Also check sense-level negatives
    for (const [num, sg] of gA.senseResults) {
      for (const neg of sg.negatives) {
        if (gB.ancestors.has(neg.targetAddr) || isAddrB(neg.targetAddr)) {
          result.blocked.push({ from: `${gA.name}/${num}`, blocked: neg.target, reason: `${gA.name}/${num} —NOT→ ${neg.target}` });
        }
      }
    }

    return result;
  }

  // Format relate result for display
  relateDisplay(wordA, wordB) {
    const r = this.relate(wordA, wordB);
    if (r.error) return [r.error];
    const lines = [`RELATE: ${r.a.name} ↔ ${r.b.name}`];

    if (r.known.length) {
      lines.push('  Known:');
      for (const k of r.known) lines.push(`    ${k.from} —${k.rel}→ ${k.to}`);
    } else {
      lines.push('  Known: (no direct connection)');
    }

    if (r.shared.length) {
      lines.push('  Shared:');
      for (const s of r.shared) {
        lines.push(`    ${s.pathFromA.join(' → ')} ← ${s.rel} → ${s.pathFromB.join(' → ')} (ancestor: ${s.ancestor})`);
      }
    }

    if (r.proposed.length) {
      lines.push('  Proposed:');
      for (const p of r.proposed) lines.push(`    ${p.from} —${p.rel}→ ${p.to} (via ${p.via})`);
    }

    if (r.blocked.length) {
      lines.push('  Blocked:');
      for (const b of r.blocked) lines.push(`    ${b.reason}`);
    }

    if (!r.known.length && !r.shared.length && !r.proposed.length && !r.blocked.length) {
      lines.push('  No connections found between these nodes.');
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

  // ---- xb.5: SELF-TESTING — the system proves itself ----

  selfTest() {
    const lines = ['SELF-TEST', ''];
    let passed = 0, failed = 0, total = 0;
    const findings = [];

    // Collect all knowledge nodes (skip base layer, signatures, profiles, internal nodes)
    const allEntries = this.ns.allNodes().filter(e => {
      if (!e.address.includes('.')) return false; // base layer nodes (single number)
      const n = e.node.name;
      if (n.startsWith('_sig_') || n.startsWith('_prof_') || n.startsWith('obs')) return false;
      return e.node.pointers.length > 0;
    });

    if (!allEntries.length) {
      return ['No knowledge to test. Try: curriculum'];
    }

    // Test each relationship
    for (const entry of allEntries) {
      const node = entry.node;
      const name = node.name;

      // Test each pointer
      for (const ptr of node.pointers) {
        const targetName = this.ns.addrToName(ptr.to);
        const targetNode = this.ns.get(this._canonical(ptr.to));
        total++;

        // Check 1: target exists
        if (!targetNode) {
          failed++;
          findings.push({ source: name, rel: ptr.type, target: targetName, reason: 'target node missing' });
          lines.push(`  FAIL: ${name} —${ptr.type}→ ${targetName} (target missing)`);
          continue;
        }

        // Check 2: for is_a chains, verify the chain walks correctly
        if (ptr.type === 'is_a') {
          const v = this.verify(name, 'is_a', targetName);
          if (v.found) {
            passed++;
            this.bumpTrust(entry.address);
            this.bumpTrust(this._canonical(ptr.to));
          } else {
            failed++;
            findings.push({ source: name, rel: 'is_a', target: targetName, reason: 'chain broken' });
            lines.push(`  FAIL: ${name} —is_a→ ${targetName} (chain broken)`);
          }
          continue;
        }

        // Check 3: for eq pointers, verify resolution
        if (ptr.type === 'eq') {
          const resolved = this._canonical(entry.address);
          const targetCanon = this._canonical(ptr.to);
          if (resolved === targetCanon || this.ns.has(targetCanon)) {
            passed++;
            this.bumpTrust(entry.address);
          } else {
            failed++;
            findings.push({ source: name, rel: 'eq', target: targetName, reason: 'eq target unreachable' });
            lines.push(`  FAIL: ${name} —eq→ ${targetName} (unreachable)`);
          }
          continue;
        }

        // Check 4: for opposite_of, verify both sides exist
        if (ptr.type === 'opposite_of') {
          // Check reverse exists too
          const reverseNode = this.ns.get(this._canonical(ptr.to));
          if (reverseNode) {
            const hasReverse = reverseNode.pointers.some(p =>
              p.type === 'opposite_of' && this._canonical(p.to) === this._canonical(entry.address)
            );
            if (hasReverse) {
              passed++;
              this.bumpTrust(entry.address);
              this.bumpTrust(this._canonical(ptr.to));
            } else {
              // One-way opposite — still valid but note it
              passed++;
              this.bumpTrust(entry.address);
            }
          } else {
            failed++;
            findings.push({ source: name, rel: 'opposite_of', target: targetName, reason: 'target missing' });
            lines.push(`  FAIL: ${name} —opposite_of→ ${targetName} (target missing)`);
          }
          continue;
        }

        // Check 5: for not pointers, verify the negative is consistent
        if (ptr.type === 'not') {
          // A not pointer is valid if there's no contradicting positive path
          const contradicts = this.verify(name, 'is_a', targetName);
          if (contradicts.found) {
            failed++;
            findings.push({ source: name, rel: 'not', target: targetName, reason: 'contradicts is_a chain' });
            lines.push(`  FAIL: ${name} —not→ ${targetName} (but is_a chain exists!)`);
          } else {
            passed++;
            this.bumpTrust(entry.address);
          }
          continue;
        }

        // Default: pointer exists and target exists — pass
        passed++;
        this.bumpTrust(entry.address);
      }

      // Also check senses
      for (const [num, sense] of node.senses) {
        for (const ptr of sense.pointers) {
          const targetName = this.ns.addrToName(ptr.to);
          const targetNode = this.ns.get(this._canonical(ptr.to));
          total++;
          if (!targetNode) {
            failed++;
            findings.push({ source: `${name}/${num}`, rel: ptr.type, target: targetName, reason: 'target missing' });
            lines.push(`  FAIL: ${name}/${num} —${ptr.type}→ ${targetName} (target missing)`);
          } else {
            passed++;
          }
        }
      }
    }

    // Store findings as nodes
    for (const f of findings) {
      const fName = `_finding_${this.ns.count}`;
      this.mkNode(fName, {
        value: f, space: 'node', createdBy: 'selftest',
        trust: 'node-trial'
      });
    }

    // Summary
    lines.push('');
    const pct = total > 0 ? Math.round((passed / total) * 100) : 0;
    lines.push(`${total} checks: ${passed} passed, ${failed} failed (${pct}%)`);
    if (findings.length) {
      lines.push(`${findings.length} finding${findings.length > 1 ? 's' : ''} logged.`);
    }
    if (failed === 0) lines.push('ALL CHECKS PASSED');

    return lines;
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

    // === xb.5 T50: GATHER ===
    section('xb.5 Gather');
    // Set up test data — load curriculum first
    this.loadCurriculum();
    // Gather a node with direct pointers and chains
    const gCat = this.gather('cat');
    check('T50.1 gather exists', gCat !== null, true);
    check('T50.2 gather name', gCat.name, 'cat');
    check('T50.3 has direct', gCat.direct.length > 0, true);
    check('T50.4 direct is_a', gCat.direct.some(d => d.rel === 'is_a' && d.target === 'animal'), true);
    check('T50.5 has chains', gCat.chains.length > 0, true);
    check('T50.6 chain reaches organism', gCat.chains.some(c => c.path.includes('organism')), true);
    check('T50.7 chain reaches thing', gCat.chains.some(c => c.path.includes('thing')), true);
    check('T50.8 has reverse', gCat.reverse.length > 0, true);
    check('T50.9 reverse from feline', gCat.reverse.some(r => r.source === 'feline' && r.rel === 'eq'), true);
    check('T50.10 ancestors includes animal', gCat.ancestors.has(this._canonical(this.ns.nameToAddr('animal'))), true);
    // Gather unknown node
    const gNone = this.gather('zzzznonexistent');
    check('T50.11 null for unknown', gNone, null);

    // === xb.5 T51: GATHER DISPLAY ===
    section('xb.5 Gather Display');
    const gdLines = this.gatherDisplay('cat');
    check('T51.1 has header', gdLines[0].includes('GATHER: cat'), true);
    check('T51.2 shows direct', gdLines.some(l => l.includes('is_a') && l.includes('animal')), true);
    check('T51.3 shows chain', gdLines.some(l => l.includes('organism')), true);
    const gdMiss = this.gatherDisplay('zzzznoexist');
    check('T51.4 missing node', gdMiss[0].includes('not found'), true);

    // === xb.5 T52: NOT POINTERS ===
    section('xb.5 Not Pointers');
    this.link('cat', 'not', 'vehicle');
    const gCatNot = this.gather('cat');
    check('T52.1 has negatives', gCatNot.negatives.length > 0, true);
    check('T52.2 not vehicle', gCatNot.negatives.some(n => n.target === 'vehicle'), true);
    // Verify not pointers show in display
    const gdNot = this.gatherDisplay('cat');
    check('T52.3 display shows not', gdNot.some(l => l.includes('NOT') && l.includes('vehicle')), true);
    // Clean up
    this.unlink('cat', 'not', 'vehicle');

    // === xb.5 T53: RELATE ===
    section('xb.5 Relate');
    // Relate cat and dog — should share ancestor 'animal'
    const relCD = this.relate('cat', 'dog');
    check('T53.1 no error', relCD.error === undefined, true);
    check('T53.2 has shared', relCD.shared.length > 0, true);
    check('T53.3 shared ancestor animal', relCD.shared.some(s => s.ancestor === 'animal'), true);
    // Relate cat and banana — should share distant ancestor 'thing'
    const relCB = this.relate('cat', 'banana');
    check('T53.4 cat-banana shared', relCB.shared.length > 0, true);
    check('T53.5 shared thing', relCB.shared.some(s => s.ancestor === 'thing'), true);
    // Relate with unknown
    const relBad = this.relate('cat', 'zzzznoexist');
    check('T53.6 error on unknown', relBad.error !== undefined, true);

    // === xb.5 T54: RELATE DISPLAY ===
    section('xb.5 Relate Display');
    const rdLines = this.relateDisplay('cat', 'dog');
    check('T54.1 header', rdLines[0].includes('RELATE: cat'), true);
    check('T54.2 shows shared', rdLines.some(l => l.includes('animal')), true);

    // === xb.5 T55: RELATE WITH NOT POINTERS (BLOCKED) ===
    section('xb.5 Relate Blocked');
    this.link('cat', 'not', 'vehicle');
    const relCV = this.relate('cat', 'car');
    check('T55.1 blocked exists', relCV.blocked.length > 0, true);
    check('T55.2 blocked vehicle', relCV.blocked.some(b => b.blocked === 'vehicle'), true);
    this.unlink('cat', 'not', 'vehicle');

    // === xb.5 T56: GATHER VIA EQ ===
    section('xb.5 Gather EQ');
    // feline eq cat, so gathering feline should follow eq and show cat's chains
    const gFeline = this.gather('feline');
    check('T56.1 feline exists', gFeline !== null, true);
    check('T56.2 feline has eq', gFeline.direct.some(d => d.rel === 'eq' && d.target === 'cat'), true);

    // === xb.5 T57: GATHER DEPTH ===
    section('xb.5 Gather Depth');
    const gShallow = this.gather('cat', 1);
    const gDeep = this.gather('cat', 10);
    check('T57.1 shallow has chains', gShallow.chains.length > 0, true);
    // Shallow should have shorter paths than deep
    const shallowMax = Math.max(...gShallow.chains.map(c => c.depth), 0);
    const deepMax = Math.max(...gDeep.chains.map(c => c.depth), 0);
    check('T57.2 deep goes further', deepMax >= shallowMax, true);

    // === xb.5 T58: TEMPLATE ARG MACROS ===
    section('xb.5 Template Macros');
    this.createMacro('ztdouble', '(MUL 2 {0})');
    check('T58.1 double 5', this.evaluate('(ztdouble 5)'), 10);
    check('T58.2 double 0', this.evaluate('(ztdouble 0)'), 0);
    check('T58.3 double -3', this.evaluate('(ztdouble -3)'), -6);
    check('T58.4 double 100', this.evaluate('(ztdouble 100)'), 200);

    // === xb.5 T59: MULTI-ARG MACROS ===
    section('xb.5 Multi-Arg Macros');
    this.createMacro('ztadd3', '(ADD {0} {1} {2})');
    check('T59.1 add3', this.evaluate('(ztadd3 1 2 3)'), 6);
    check('T59.2 add3 zeros', this.evaluate('(ztadd3 0 0 0)'), 0);
    this.createMacro('ztdist', '(ABS (SUB {0} {1}))');
    check('T59.3 distance', this.evaluate('(ztdist 10 3)'), 7);
    check('T59.4 distance reversed', this.evaluate('(ztdist 3 10)'), 7);

    // === xb.5 T60: MACRO COMPOSITION — macros calling macros ===
    section('xb.5 Macro Composition');
    this.createMacro('ztquadruple', '(ztdouble (ztdouble {0}))');
    check('T60.1 quadruple 3', this.evaluate('(ztquadruple 3)'), 12);
    check('T60.2 quadruple 5', this.evaluate('(ztquadruple 5)'), 20);
    this.createMacro('ztoct', '(ztdouble (ztquadruple {0}))');
    check('T60.3 octuple 2', this.evaluate('(ztoct 2)'), 16);

    // === xb.5 T61: MACROS WITH STRINGS ===
    section('xb.5 String Macros');
    this.createMacro('ztshout', '(S_UPPER {0})');
    check('T61.1 shout hello', this.evaluate('(ztshout "hello")'), 'HELLO');
    check('T61.2 shout cat', this.evaluate('(ztshout "cat")'), 'CAT');
    this.createMacro('ztgreet', '(CONCAT "Hello, " {0} "!")');
    check('T61.3 greet world', this.evaluate('(ztgreet "world")'), 'Hello, world!');

    // === xb.5 T62: MACROS WITH CONDITIONALS ===
    section('xb.5 Conditional Macros');
    this.createMacro('ztclamp', '(IF (GT {0} {1}) {1} {0})');
    check('T62.1 clamp 10 to 5', this.evaluate('(ztclamp 10 5)'), 5);
    check('T62.2 clamp 3 to 5', this.evaluate('(ztclamp 3 5)'), 3);
    this.createMacro('ztispos', '(GT {0} 0)');
    check('T62.3 ispos 5', this.evaluate('(ztispos 5)'), true);
    check('T62.4 ispos -1', this.evaluate('(ztispos -1)'), false);

    // === xb.5 T63: MACROS ARE NODES — trust and touch ===
    section('xb.5 Macro Nodes');
    const dblAddr = this.ns.nameToAddr('ztdouble');
    const dblNode = this.ns.get(dblAddr);
    check('T63.1 macro is node', dblNode !== null, true);
    check('T63.2 has macro field', dblNode.macro, '(MUL 2 {0})');
    check('T63.3 mode is live', dblNode.mode, 'live');
    check('T63.4 touched by use', dblNode.context.accessCount > 0, true);

    // === xb.5 T64: MACRO VIA EXEC ===
    section('xb.5 Macro Exec');
    const mexec1 = this.exec('macro zttriple (MUL 3 {0})');
    check('T64.1 macro created', mexec1[0].includes('Macro created'), true);
    const mexec2 = this.exec('(zttriple 7)');
    check('T64.2 exec evaluates', mexec2.some(l => l.includes('21')), true);

    // === xb.5 T65: RELATIONSHIP INSPECTION PRIMITIVES ===
    section('xb.5 Rel Inspection Prims');
    // Curriculum is loaded from T50 tests
    check('T65.1 has_ptr true', this.evaluate('(N_HAS_PTR "cat" "is_a")'), true);
    check('T65.2 has_ptr false', this.evaluate('(N_HAS_PTR "cat" "color")'), false);
    check('T65.3 ptr target', this.evaluate('(N_PTR "cat" "is_a")'), 'animal');
    check('T65.4 ptr null', this.evaluate('(N_PTR "cat" "color")'), null);
    check('T65.5 chain', this.evaluate('(N_CHAIN "cat" "is_a")'), ['cat', 'animal', 'organism', 'thing']);
    check('T65.6 verify true', this.evaluate('(N_VERIFY "cat" "is_a" "organism")'), true);
    check('T65.7 verify false', this.evaluate('(N_VERIFY "cat" "is_a" "vehicle")'), false);
    const gatherStr = this.evaluate('(N_GATHER "cat")');
    check('T65.8 gather returns string', typeof gatherStr === 'string', true);
    check('T65.9 gather has content', gatherStr.includes('is_a') && gatherStr.includes('animal'), true);
    const inferred = this.evaluate('(N_INFER "cat")');
    check('T65.10 infer returns array', Array.isArray(inferred), true);
    check('T65.11 infer finds organism', inferred.some(i => i.includes('organism')), true);

    // === xb.5 T66: OPERATIONAL CYCLE MACROS ===
    section('xb.5 Operational Cycle');
    // observe — returns gather summary
    const obsResult = this.evaluate('(observe "cat")');
    check('T66.1 observe returns', typeof obsResult === 'string', true);
    check('T66.2 observe has data', obsResult.includes('animal'), true);
    // question — challenges a claim
    const qYes = this.evaluate('(question "cat" "is_a" "animal")');
    check('T66.3 question confirmed', qYes.includes('CONFIRMED'), true);
    const qNo = this.evaluate('(question "cat" "is_a" "vehicle")');
    check('T66.4 question unconfirmed', qNo.includes('UNCONFIRMED'), true);
    // deduce — inferences
    const deduced = this.evaluate('(deduce "cat")');
    check('T66.5 deduce returns array', Array.isArray(deduced), true);
    check('T66.6 deduce has inference', deduced.length > 0, true);
    // verify_fact — boolean
    check('T66.7 verify_fact true', this.evaluate('(verify_fact "cat" "is_a" "organism")'), true);
    check('T66.8 verify_fact false', this.evaluate('(verify_fact "cat" "is_a" "food")'), false);
    // has_property — check relationship existence
    check('T66.9 has_property', this.evaluate('(has_property "cat" "is_a")'), true);
    check('T66.10 has_property no', this.evaluate('(has_property "cat" "color")'), false);
    // follow — single pointer hop
    check('T66.11 follow', this.evaluate('(follow "cat" "is_a")'), 'animal');
    // chain — full walk
    const chainResult = this.evaluate('(chain "cat" "is_a")');
    check('T66.12 chain result', chainResult, ['cat', 'animal', 'organism', 'thing']);

    // === xb.5 T67: CYCLE MACROS ARE NODES ===
    section('xb.5 Cycle as Nodes');
    const obsAddr = this.ns.nameToAddr('observe');
    const obsNode = this.ns.get(obsAddr);
    check('T67.1 observe is node', obsNode !== null, true);
    check('T67.2 has macro', obsNode.macro !== null, true);
    check('T67.3 has description', typeof obsNode.value === 'string', true);
    check('T67.4 trust proven', obsNode.context.trust, 'node-proven');
    check('T67.5 created by cycle', obsNode.context.createdBy, 'operational-cycle');
    // All 7 cycle macros exist
    const cycleMacros = ['observe', 'question', 'deduce', 'verify_fact', 'has_property', 'follow', 'chain'];
    for (const cm of cycleMacros) {
      check(`T67.6 ${cm} exists`, this.ns.has(this.ns.nameToAddr(cm)), true);
    }

    // === xb.5 T68: CYCLE COMPOSITION ===
    section('xb.5 Cycle Composition');
    // Build new macro from cycle macros
    this.createMacro('ztcheck_isa', '(IF (verify_fact {0} "is_a" {1}) (CONCAT {0} " IS " {1}) (CONCAT {0} " is NOT " {1}))');
    check('T68.1 check cat animal', this.evaluate('(ztcheck_isa "cat" "animal")'), 'cat IS animal');
    check('T68.2 check cat vehicle', this.evaluate('(ztcheck_isa "cat" "vehicle")'), 'cat is NOT vehicle');
    // Compose observe with other ops
    this.createMacro('ztquick_look', '(CONCAT "Node: " {0} " | " (observe {0}))');
    const ql = this.evaluate('(ztquick_look "dog")');
    check('T68.3 quick_look has node', ql.includes('Node: dog'), true);
    check('T68.4 quick_look has data', ql.includes('is_a'), true);

    // === xb.5 T69: SELF-TEST — all pass ===
    section('xb.5 Self-Test');
    // Curriculum is loaded from T50
    const st1 = this.selfTest();
    check('T69.1 has summary', st1.some(l => l.includes('checks:')), true);
    check('T69.2 all passed', st1.some(l => l.includes('ALL CHECKS PASSED')), true);
    check('T69.3 no failures', !st1.some(l => l.includes('FAIL')), true);

    // === xb.5 T70: SELF-TEST — detects contradiction ===
    section('xb.5 Self-Test Contradiction');
    // Add a not pointer that contradicts an is_a chain
    // cat is_a animal (exists), now add cat not animal — contradiction
    this.link('cat', 'not', 'animal');
    const st2 = this.selfTest();
    check('T70.1 has failure', st2.some(l => l.includes('FAIL')), true);
    check('T70.2 contradiction found', st2.some(l => l.includes('contradicts') || l.includes('FAIL')), true);
    // Clean up
    this.unlink('cat', 'not', 'animal');
    // Verify clean after fix
    const st3 = this.selfTest();
    check('T70.3 clean after fix', st3.some(l => l.includes('ALL CHECKS PASSED')), true);

    // === xb.5 T71: SELF-TEST VIA EXEC ===
    section('xb.5 Self-Test Exec');
    const stExec = this.exec('selftest');
    check('T71.1 exec works', stExec.some(l => l.includes('checks:')), true);

    // === xb.5 T72: ADJACENCY TRACKING ===
    section('xb.5 Adjacency');
    this.ingest('the cat sat on the mat');
    const adjThe = this.ns.get(this.ns.nameToAddr('_adj_the'));
    check('T72.1 adj node created', adjThe !== null, true);
    check('T72.2 adj has value', adjThe.value !== null, true);
    check('T72.3 the→cat', adjThe.value.right['cat'], 1);
    check('T72.4 the→mat', adjThe.value.right['mat'], 1);
    check('T72.5 the count', adjThe.value.count, 2);
    const adjCat = this.ns.get(this.ns.nameToAddr('_adj_cat'));
    check('T72.6 cat preceded by the', adjCat.value.left['the'], 1);
    check('T72.7 cat followed by sat', adjCat.value.right['sat'], 1);
    // Ingest again — counts should accumulate
    this.ingest('the cat ran');
    const adjThe2 = this.ns.get(this.ns.nameToAddr('_adj_the'));
    check('T72.8 the→cat accumulated', adjThe2.value.right['cat'], 2);
    check('T72.9 the count accumulated', adjThe2.value.count, 3);

    // === xb.5 T73: ADJACENCY DISPLAY ===
    section('xb.5 Adjacency Display');
    const adjDisplay = this.showAdjacency('the');
    check('T73.1 has header', adjDisplay[0].includes('ADJACENCY: the'), true);
    check('T73.2 shows followers', adjDisplay.some(l => l.includes('cat')), true);
    const adjMiss = this.showAdjacency('zzzznoexist');
    check('T73.3 missing word', adjMiss[0].includes('No adjacency'), true);

    // === xb.5 T74: ADJACENCY VIA EXEC ===
    section('xb.5 Adjacency Exec');
    const adjExec = this.exec('adjacency cat');
    check('T74.1 exec works', adjExec[0].includes('ADJACENCY'), true);

    // === xb.5 T75: POSITION TRACKING ===
    section('xb.5 Positions');
    const adjSat = this.ns.get(this.ns.nameToAddr('_adj_sat'));
    check('T75.1 sat position', adjSat.value.positions.includes(2), true);
    // "the" appeared at positions 0 and 4 in first sentence, 0 in second
    check('T75.2 the positions', adjThe2.value.positions.length, 3);

    // === xb.5 T76: SENTENCE COMPREHENSION ===
    section('xb.5 Comprehension');
    this.clearDiscourse();
    const comp1 = this.comprehend('cat was hungry.');
    check('T76.1 parsed', comp1[0].includes('COMPREHEND'), true);
    check('T76.2 property set', comp1.some(l => l.includes('hungry')), true);
    // Check entity state
    const catState = this._getEntityState('cat');
    check('T76.3 entity has property', catState.properties['hungry'], true);

    // === xb.5 T77: PRONOUN RESOLUTION ===
    section('xb.5 Pronouns');
    const comp2 = this.comprehend('it ate food.');
    check('T77.1 pronoun resolved', comp2.some(l => l.includes('cat')), true);
    // cat should have the action
    const catState2 = this._getEntityState('cat');
    check('T77.2 action recorded', catState2.actions.some(a => a.action === 'ate'), true);
    check('T77.3 action object', catState2.actions.some(a => a.object === 'food'), true);

    // === xb.5 T78: IS_A PARSING ===
    section('xb.5 Is_a Parsing');
    this.clearDiscourse();
    this.comprehend('parrot is a bird.');
    const parrotAddr = this._canonical(this.ns.nameToAddr('parrot'));
    const parrotNode = this.ns.get(parrotAddr);
    check('T78.1 is_a created', parrotNode.pointers.some(p => p.type === 'is_a' && this.ns.addrToName(p.to) === 'bird'), true);

    // === xb.5 T79: MULTI-SENTENCE ===
    section('xb.5 Multi-Sentence');
    this.clearDiscourse();
    const comp3 = this.comprehend('bird is a animal. bird has wings. bird is small.');
    check('T79.1 multiple parsed', comp3.length >= 4, true);
    const birdState = this._getEntityState('bird');
    check('T79.2 bird is small', birdState.properties['small'], true);
    check('T79.3 bird has wings', this.verify('bird', 'has', 'wings').found, true);

    // === xb.5 T80: ENTITY DISPLAY ===
    section('xb.5 Entity Display');
    const entDisplay = this.showEntity('bird');
    check('T80.1 has header', entDisplay[0].includes('ENTITY: bird'), true);
    check('T80.2 shows properties', entDisplay.some(l => l.includes('small')), true);
    const entList = this.showEntities();
    check('T80.3 entities listed', entList.some(l => l.includes('bird')), true);

    // === xb.5 T81: ENTITY VIA EXEC ===
    section('xb.5 Entity Exec');
    this.clearDiscourse();
    this.exec('comprehend the cat sat on the mat.');
    const entExec = this.exec('entity cat');
    check('T81.1 exec entity', entExec[0].includes('ENTITY'), true);
    const entsExec = this.exec('entities');
    check('T81.2 exec entities', entsExec.some(l => l.includes('cat')), true);

    // === xb.5 T82: DISCOURSE CLEAR ===
    section('xb.5 Discourse Clear');
    this.clearDiscourse();
    check('T82.1 cleared', this._discourse, null);

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
      const isCmd = t.startsWith('(') || ['help','stats','nodes','base','controls','prims','curriculum','rels','working','archive','flush','snapshots','test','selftest','entities','cleardiscourse','undo','explore','exploreall'].includes(t) || /^(show|create|resolve|addr|read|teach|unlink|query|macro|predict|explore|links|hibernate|wake|peek|import|gather|relate|adjacency|comprehend|entity) /.test(t) || t === 'hibernate' || t === 'wake';
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
      const isCmd = t.startsWith('(') || ['help','stats','nodes','base','controls','prims','curriculum','rels','working','archive','flush','snapshots','test','selftest','entities','cleardiscourse','undo','explore','exploreall'].includes(t) || /^(show|create|resolve|addr|read|teach|unlink|query|macro|predict|explore|links|hibernate|wake|peek|import|gather|relate|adjacency|comprehend|entity) /.test(t) || t === 'hibernate' || t === 'wake';
      if (!isCmd) return this.correct(t);
      this.pending = null;
    }

    // Commands
    if (t === 'help') return ['INTELLON xb.5','','QUESTIONS (learning loop):','  is cat an animal?            verify — walks chains','  what is cat?                 forward — everything known','  → y = correct, n = wrong, 3 wrongs = teach me','','GATHER & RELATE:','  gather cat                   everything known about cat','  relate cat dog               overlap search between two nodes','  how does cat relate to dog?  natural language relate','','COMPREHEND:','  comprehend <text>            parse sentences, track entities','  entity <n>                   show entity state','  entities                     list tracked entities','  cleardiscourse               reset entity tracking','','SELF-LEARNING:','  explore ADD                  experiment with a primitive','  explore                      experiment with ALL primitives','  predict ADD 4 6              predict output from profile','  macro double (MUL 2 {0})     create a composed operation','  selftest                     verify all knowledge','','RELATIONSHIPS:','  cat is_a animal              source rel target','  cat not vehicle              negative pointer (antifact)','  unlink / undo                remove or reverse','  curriculum                   load starter set','','INSPECT:','  (ADD 1 2 3)  stats  nodes  rels  prims  test','  adjacency <word>  query <word>  show <addr>','  (observe "cat")  (deduce "cat")  (question "cat" "is_a" "animal")','','WORKING SPACE:','  working  hibernate  wake  peek  import  archive  flush'];
    if (t === 'test') return this.runTests();
    if (t === 'selftest') return this.selfTest();
    if (t.startsWith('explore ')) return this.explore(t.slice(8).trim());
    if (t === 'explore' || t === 'exploreall') return this.exploreAll();
    if (t.startsWith('macro ')) { const rest = t.slice(6).trim(), sp = rest.indexOf(' '); if (sp < 0) return ['Usage: macro <name> <expression>']; return this.createMacro(rest.slice(0, sp), rest.slice(sp + 1).trim()); }
    if (t.startsWith('predict ')) { const parts = t.slice(8).trim().split(/\s+/); const name = parts[0]; const args = parts.slice(1).map(a => /^-?\d+(\.\d+)?$/.test(a) ? Number(a) : a === 'true' ? true : a === 'false' ? false : a); const r = this.predict(name, args); return [`Prediction for (${name} ${parts.slice(1).join(' ')}):`, `  result: ${JSON.stringify(r.prediction)}`, `  type: ${r.predictedType || 'unknown'}`, `  confidence: ${r.confidence}`, `  properties: ${r.properties ? r.properties.join(', ') : 'none'}`]; }
    if (t === 'stats') return [`Nodes: ${this.ns.count} | Working: ${this.ws.count} | Prims: ${this.prims.size} | Rels: ${this.ns.allNodes().reduce((s,e)=>s+e.node.pointers.length,0)}`];
    if (t === 'prims') { const n = [...this.prims.keys()], l = []; for (let i = 0; i < n.length; i += 8) l.push(n.slice(i, i + 8).join('  ')); return l; }
    if (t === 'curriculum') return this.loadCurriculum();
    if (t.startsWith('gather ')) return this.gatherDisplay(t.slice(7).trim());
    if (t.startsWith('relate ')) { const parts = t.slice(7).trim().split(/\s+/); if (parts.length < 2) return ['Usage: relate <word1> <word2>']; return this.relateDisplay(parts[0], parts[1]); }
    if (t.startsWith('adjacency ')) return this.showAdjacency(t.slice(10).trim());
    if (t.startsWith('comprehend ')) return this.comprehend(t.slice(11).trim());
    if (t.startsWith('entity ')) return this.showEntity(t.slice(7).trim());
    if (t === 'entities') return this.showEntities();
    if (t === 'cleardiscourse') return this.clearDiscourse();
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

    // SCAFFOLD: "how does X relate to Y" → relate command
    const howRelate = t.toLowerCase().match(/^how\s+does?\s+(\S+)\s+relate\s+to\s+(\S+)/);
    if (howRelate) return this.relateDisplay(howRelate[1], howRelate[2]);

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
  const [history, setHistory] = useState([{ type: 'sys', lines: ['INTELLON xb.5', `Nodes: ${SYS.ns.count} | Prims: ${SYS.prims.size}`, '', 'Type "gather cat" after loading curriculum.', 'Type "relate cat dog" to find connections.', 'Type "help" for commands  |  "test" to verify', ''] }]);
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
