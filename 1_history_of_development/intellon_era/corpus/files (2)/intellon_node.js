class Node {
  constructor(addr, name, o = {}) {
    this.macro = o.macro || null; this.address = addr; this.name = name;
    this.context = { timestamp: Date.now(), accessCount: 0, lastAccess: Date.now(), trust: o.trust || 'working-trial', createdBy: o.createdBy || 'manual', errors: [] };
    this.buffer = { input: null, output: null }; this.pointers = o.pointers ? [...o.pointers] : [];
    this.value = o.value !== undefined ? o.value : null; this.mode = o.mode || 'cached';
    this.senses = new Map();
  }
  addPointer(t, to) { this.pointers.push({ type: t, to }); }
  getPointers(t) { return this.pointers.filter(p => p.type === t); }
  touch() { this.context.accessCount++; this.context.lastAccess = Date.now(); }
  nextSense() { return this.senses.size + 1; }
  getSense(n) { return this.senses.get(n); }
  addSense(n, senseNode) { this.senses.set(n, senseNode); }
}

module.exports = Node;
