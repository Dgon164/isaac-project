# Intellon v6 Node Architecture — Complete Handoff

**Date:** April 1, 2026
**Purpose:** Full context transfer for continuation in a new chat session. Every decision, file, result, and pending item is documented below. Nothing should need to be re-derived.

---

## 1. Project Summary

We are building a node-based intelligence architecture called the Intellon Machine v6. The system receives unlabeled input/output observation pairs and a set of 60 callable tools whose behavior is unknown. Through structured experimentation, it discovers reusable procedures, inverse relationships, algebraic properties, and behavioral overlaps — then uses that knowledge to solve novel problems.

The project has gone through three phases:
- **Dev phase (a-series):** Proved the node architecture works with batch processing
- **Training phase (b-series):** Started incremental learning, discovered the conflict-driven approach
- **Foundation rebuild (c-series):** Rebuilt with holonic principle, address book, overlap maps, reverse lookups

The c-series is the current codebase. It supersedes a-series and b-series in architecture but the b-series LearningSession class has not yet been ported to the new foundation.

---

## 2. Source Documents

### 2.1 Original Methodology (read-only, project file)
**File:** `/mnt/project/intellon_v6_methodology.docx`
**What it is:** The complete v6 specification — 60 tools, 190 seed observations across 8 phases, 6-phase discovery algorithm, verification procedures. This is the reference implementation that the node architecture must match or exceed.
**Key numbers:** 60 tools across 10 domains (arithmetic, comparison, logic, type checking, type conversion, string, sequence, bitwise). 190 observations in foundational order. 8 algebra problems for inverse reasoning.

### 2.2 Node Architecture Design Proposal
**File:** `/mnt/user-data/outputs/intellon_node_design_proposal.md`
**Status:** v3 — updated with holonic principle, partial-reference behavior model, address book, connection lookup tables, tiered rumination, chain discovery
**Sections:** 14 sections, 11 open questions, 11 experiments
**This is the architectural spec.** All code should conform to it.

### 2.3 Dev Test Plan (completed)
**File:** `/mnt/user-data/outputs/intellon_v6_test_plan.md`
**Status:** All 10 tests passed in a.5. Completed.

### 2.4 Training Test Plan
**File:** `/mnt/user-data/outputs/intellon_training_test_plan.md`
**Status:** 11 tests defined across 6 implementation phases. Tests 1-2 partially implemented in b.1 (pre-foundation-rebuild). None implemented on the c-series foundation yet.

---

## 3. Architecture Decisions (Chronological, All Binding)

These decisions were made during development and are reflected in the design proposal. They are not suggestions — they are the architecture.

### D1: Holonic Principle
Every node is simultaneously a whole and a part. The `type` field (base|logic|tool|concept|ghost) is a tag for human reference, not a structural boundary. All discovery, comparison, and maintenance operates on a single uniform pool of nodes. No code should contain `for (const nm of toolNames)` style loops that filter by type. The address book's `allNodes` is the single pool.

### D2: Partial-Reference Behavior Model
When two nodes share behavior on an input domain, the overlapping node references the other for shared cases and stores only its unique divergences. Example: AND agrees with EQ on 3/4 boolean cases. AND references EQ for (T,T), (T,F), (F,T) and owns only the (F,F) divergence where AND returns F but EQ returns T.

### D3: One-Hop Depth Per Node
Each node only looks one hop away. Resolution happens through traversal, not deep lookahead. If AND references EQ for the (T,T) case, AND doesn't know what EQ does internally. It just asks EQ. The network resolves by walking the chain node by node.

### D4: Rumination Discovers Shortcuts
If rumination finds A→B→C always resolves to C for a given domain, it can add a direct A→C shortcut — as long as the shortcut doesn't change the path or result. Shortcuts are caches, not replacements. The original path remains. If B changes, the shortcut is invalidated.

### D5: Address Book is the Single Global Structure
One flat phonebook: byName, byId, allNodes, byDomain. Every node registers at creation. Every connection triggers reverse-lookup notification. The domain index enables relevance filtering (not type filtering) for holonic comparison.

### D6: Tiered Rumination
- **Tier 1:** Correction queue — runs to completion, always finite
- **Tier 2:** Broad maintenance — budgeted, fixed pass count. Overlap discovery, enrichment propagation, shortcut caching, pruning
- **Tier 3:** Handoff to play. System doesn't wait for all broad checks.

### D7: Work → Ruminate → Play Ordering
Strict priority. Work produces flags. Rumination clears flags. Play generates new knowledge on a clean foundation. Never reversed.

### D8: Conflicts Drive Discovery
When the system discovers EQ from boolean observations before AND, that's correct — EQ does work on booleans. The system doesn't fight this. During rumination, it compares EQ against all boolean-domain peers, discovers AND agrees on 3/4 cases, and maps the overlap. AND becomes "like EQ except when both inputs are false." Conflicts are information, not errors.

### D9: base_10 is Perceived, Not Constructed
The base_10 node is an environmental input perceived from seed data. Place value understanding gets attached later. Perception first, comprehension after.

### D10: Composite Numbers via Right-Peel Decomposition
Numbers built from discovered procedures: 15 = MUL(1,10)+5. Uses right-peel: n = floor(n/10)*10 + n%10. Negatives via NEG, decimals via DIV. Left-peel was tried and caused infinite recursion with large place multipliers.

### D11: Logic as Architect-Scaffolded Infrastructure
AND/OR/NOT/XOR are flagged as structural connectives during Layer 1 boot. This is a deliberate design decision. The system self-learns domain knowledge but reasoning infrastructure is provided by the architect. Analogous to biological innate reasoning primitives.

### D12: EQ/NEQ as Valid Structural Primitives
If EQ and NEQ discover boolean observations before AND/OR, that's acceptable. EQ means "are these the same?" — arguably more fundamental than "both true." The system can use EQ/NEQ as structural connectives. Synonymy between EQ↔AND is discovered during rumination.

---

## 4. Code Artifacts — Complete Inventory

### 4.1 Active Codebase (c-series)

**`/mnt/user-data/outputs/intellon_c1_tests.jsx`** — Foundation
- Node class with: execute, step trace, versioning, staleness, overlap maps, forward/reverse lookups, address book integration
- AddressBook class with: byName, byId, allNodes, byDomain, domain indexing, reverse lookup notifications, shared domain peer queries
- 12 tools (subset for structure testing)
- **27/27 tests, 15 ops, 0.9ms**
- Tests: registration, domain index, forward connections, reverse lookups, overlap maps (AND↔EQ 3 agree 1 diverge), holonic principle, existing features (canAccept, inverse, excludes, staleness, execute), describe, edge cases

**`/mnt/user-data/outputs/intellon_c2_tests.jsx`** — Discovery Pipeline
- Full 60 tools, all 190 seed observations (minus Place Value phase from original, which was folded into Arithmetic)
- `runDiscovery(book, concepts)` — profiles tools, creates nodes in book, greedy split-cluster matching, L0 and L1 discovery, inverse discovery, property discovery, behavioral overlap mapping via domain peers
- **28/28 tests, 12,469 ops, 5.0ms**
- Key metrics: 40 procedures, 6 inverse pairs, 7 synonyms, 58 overlaps, 67 total nodes, 97% observation coverage (154/158)
- AND↔EQ overlap: 3 agree, 1 diverge on boolean domain
- EQ boolean overlaps: NEQ(a:0 d:9), AND(a:3 d:1), OR(a:1 d:3), XOR(a:0 d:4)
- Commutative: ADD, MUL, MIN, MAX, BIT_AND, BIT_OR, BIT_XOR, A_GET (8 tools)
- Reverse lookup verified: SUB knows ADD has it as inverse, commutative node knows its 8 referrers

### 4.2 Prior Codebase (superseded but referenced)

**`/mnt/user-data/outputs/intellon_a5_tests.jsx`** — Dev phase final
- Batch discovery, number factory, inverse solver, correction queue, basic rumination
- **57/57 tests, 12,675 ops, 4.4ms, 97 nodes, 97% coverage, 8/8 algebra solves**
- This was the benchmark. c.2 matches its discovery results (40 procedures, 97% coverage) on the new foundation.

**`/mnt/user-data/outputs/intellon_b1_tests.jsx`** — Training phase (pre-rebuild)
- LearningSession class with incremental receive/discover/ruminate
- Conflict-driven discovery approach
- **17/17 tests, 1,476 ops, 1.7ms**
- EQ/NEQ discovered from boolean observations (natural behavior, not forced)
- ADD/SUB/MUL discovered incrementally at 3 observations each
- Rumination discovers ADD↔SUB inverse and properties
- **NOT YET PORTED TO c-series foundation.** The LearningSession class still uses `this.toolNames` and `this.toolNodes` instead of the address book. Porting this is the next step.

### 4.3 Other Files

**`/mnt/user-data/outputs/intellon_v6.jsx`** — Original v6 simulation (React, runs the methodology spec as-is)
**`/mnt/user-data/outputs/intellon_a1_test1_2.jsx`** — First node prototype
**`/mnt/user-data/outputs/intellon_a1_tests.jsx`** — a.2 (discovery into nodes)
**`/mnt/user-data/outputs/intellon_a3_tests.jsx`** — a.3 (composition, numbers)
**`/mnt/user-data/outputs/intellon_a4_tests.jsx`** — a.4 (inverse solver, staleness, rumination)

---

## 5. Key Data Structures (c-series)

### AddressBook
```javascript
class AddressBook {
    byName    // { "ADD": node } — O(1) name lookup
    byId      // { 200: node } — O(1) id lookup
    allNodes  // [node, ...] — single holonic pool
    byDomain  // { "number_concept": [node, ...] } — relevance filter for comparison

    register(node)                    // auto-called on node creation
    indexDomains(node)                // updates byDomain when takes slots change
    getSharedDomainPeers(node)        // returns nodes sharing ≥1 input domain
    notifyConnection(src, tgt, qual)  // triggers reverse lookup update on target
    resolve(name)                     // name → node
    get(id)                           // id → node
}
```

### Node
```javascript
class Node {
    id, type, value, label, structural
    definition: { slots: [], procedure: [] }
    connections    // Map: targetId → { target, weight, qualifier }
    _reverse       // Map: sourceId → [{ source, qualifier, weight }]
    overlaps       // [{ target, domain, agrees, diverges }]
    excludes       // [node, ...]
    _obsCount, _execLog, _version, _refVersions, _book

    // Slots
    addSlot(role, connective, members, confidence)  // auto-indexes domain if role="takes"
    getSlots(role)

    // Connections (forward)
    addConnection(target, qualifier, weight)  // notifies book → target reverse lookup
    getConnection(qualifier)                  // first match
    getAllConnections(qualifier?)              // all matches (or all if no qualifier)

    // Reverse lookups
    getReverse(qualifier?)  // "who points to me?"

    // Overlaps
    addOverlap(target, domain, agrees, diverges)  // replaces existing same target+domain
    getOverlap(target, domain?)

    // Execution
    execute(...inputs)     // tool: callTool. base: return value. ghost: run procedure steps.
    canAccept(input, resolver)
    inverse()              // follows "inverse" connection
    relatedTo(target)      // checks excludes, connections, slots, overlaps

    // Maintenance
    checkStaleness()       // returns list of refs whose version changed
    markSeen(ref) / markAllSeen()
    describe()             // full self-description including overlaps and reverse count
}
```

### Observation Shape
```javascript
{ t: "b", a: value, b: value, o: value }  // binary
{ t: "u", i: value, o: value }             // unary
```

### Procedure Step Args
```javascript
{ type: "input" }                // the observation's input
{ type: "step", step: N }       // result of step N
{ type: "ref", node: nodeRef }  // another node's execute() result
{ type: "value", value: V }     // literal constant
```

---

## 6. Research Findings

### F1: Boolean Domain Has Massive Tool Overlap
EQ and NEQ are universal matchers that claim boolean observations before AND/OR/XOR get a chance. This is correct behavior. EQ(T,T)=T genuinely matches an AND observation. The system handles this through overlap mapping during rumination, not by hacking the discovery order.

### F2: Discovery Cost Dominates, Reasoning is Nearly Free
~5,200 ops for profiling 60 tools. 40 ops for all 8 algebra solves (0.3% of total). Maintenance is essentially zero when the knowledge base is clean. The architecture prediction is confirmed: pay once to build knowledge, then reason through pointer traversal.

### F3: Transfer Learning Not Measurable at Current Scale
ADD, SUB, MUL all confirm at exactly 3 observations (the threshold). No measurable transfer. Each tool is learned independently. This is a legitimate negative finding at this scale — transfer may appear with larger observation sets or higher thresholds.

### F4: Right-Peel Number Decomposition
n = floor(n/10)*10 + n%10 works for arbitrary numbers. Left-peel (extracting leading digits first) caused infinite recursion because the place multiplier (10, 100, 1000) requires knowing the number's magnitude first.

### F5: 4 Uncovered Observations
97% coverage = 154/158. The 4 uncovered observations are likely edge cases in mixed clusters where the greedy pass left stragglers below the minimum match threshold. Worth examining to understand what the algorithm can't disambiguate.

### F6: Overlap Map Density
7 synonyms and 58 overlaps from 60 tools. ADD alone has overlap relationships with 17 other tools on the number domain. The boolean domain is cleaner: AND has 2 overlaps (EQ: 3 agree 1 diverge, NEQ: 1 agree 3 diverge). This density is expected — many numeric tools agree on simple cases like (0,0) but diverge on everything else.

---

## 7. What Has Been Proven

| Claim | Evidence | Status |
|---|---|---|
| Nodes can self-describe using logic connectives | a.5 Test 10.5: ADD describes takes, gives, inverse, commutative, identity | ✅ Proven |
| Reference-based composition works | a.5 Test 5: PLACE_WORTH references TENS_DIGIT as black box | ✅ Proven |
| Inverse reasoning through pointer traversal | a.5 Test 7: 8/8 algebra solves, 40 ops total | ✅ Proven |
| Version-based staleness detection | a.4 Tests 8-9: detects enriched references, rumination clears | ✅ Proven |
| Holonic pool — no type boundaries | c.1 Tests C1.15-16: all types in same pool, domain peers cross types | ✅ Proven |
| Address book with domain indexing | c.2 Test C2.3: 41 number, 19 string, 13 boolean, 17 array indexed | ✅ Proven |
| Reverse lookups maintained by book | c.2 Tests C2.15-16: SUB knows ADD's inverse, commutative knows its 8 referrers | ✅ Proven |
| Behavioral overlap mapping | c.2 Tests C2.17-19: AND↔EQ 3/4 agree, 7 synonyms, 58 overlaps across system | ✅ Proven |
| Full pipeline on new foundation matches dev results | c.2: 40 procedures, 97% coverage, 6 inverse pairs — matches a.5 | ✅ Proven |
| Incremental learning works | b.1: ADD confirmed at 3 obs, recognized instantly after | ✅ Proven (pre-rebuild) |
| Conflicts drive natural discovery | b.1: EQ/NEQ discover first from booleans, AND never independently discovered | ✅ Proven |
| Deterministic: second run matches | a.5 Test 10.8: identical tools, inverses, properties | ✅ Proven |

---

## 8. What Needs to Be Built Next

### Phase 3: c.3 — Overlap Mapping in Rumination
Add overlap discovery to tiered rumination (currently overlap mapping is done as a post-discovery step in c.2, not as part of the rumination cycle). After discovery confirms EQ from boolean observations, rumination Tier 2 compares EQ against all boolean-domain peers via `book.getSharedDomainPeers()`. This is the mechanism that discovers AND↔EQ overlap organically rather than as a batch step.

### Phase 4: c.4 — Incremental LearningSession on New Foundation
Port the `LearningSession` class from b.1 onto the c-series foundation. Replace `this.toolNames` and `this.toolNodes` with address book lookups. Route all node creation through `new Node({...}, book)`. The discovery logic (receive → check confirmed → add to pending → try discover) stays the same. The infrastructure underneath changes.

**Key change:** b.1's `_tryDiscover` iterates `this.toolNames`. c.4 should iterate `book.allNodes` filtered by `book.byDomain` relevance. This is the holonic principle in practice.

### Phase 5+: Training Tests 3-11
- **Test 3: Transfer learning** — measure observations-to-confirmation for MUL vs ADD
- **Test 4: Inverse discovery** — inverses emerge from rumination, not hardcoded
- **Test 5: Abstraction detection** — feed 15, 23, 47, 82 then present 61 cold
- **Test 6: Conflict resolution** — weight-of-evidence policy for contradictory observations
- **Test 7: Session dependency queue** — observations that arrive before their infrastructure
- **Test 8: Play budget** — 500 ops, measure discoveries-per-100-ops
- **Test 9: Regression after rumination** — re-run algebra problems, verify zero regressions
- **Test 10: Full training pipeline** — match or exceed dev a.5 results
- **Test 11: Chain discovery** — bidirectional search, open vs constrained solving, step-trace verification

### Features Not Yet Implemented
- Number factory on c-series (exists in a.5, not ported)
- Inverse solver on c-series (exists in a.5, not ported)
- Tiered rumination with budget (designed in spec, not coded)
- Play mode (designed in spec, not coded)
- Chain discovery / bidirectional search (designed in spec, not coded)
- Shortcut caching in rumination (designed in spec, not coded)
- Confidence updating (designed in spec, not coded: "always" → "sometimes" → "never")
- Session dependency queue (designed in training plan, not coded)

---

## 9. Version History

| Version | What | Tests | Ops | Time | Key Metric |
|---|---|---|---|---|---|
| a.1 | Node class + logic infrastructure | 18/18 | — | — | — |
| a.2 | Discovery into nodes + properties/inverses | 42/42 | — | — | — |
| a.3 | Execute, reference composition, number factory | 70/70 | 5,225 | 3.2ms | — |
| a.4 | Inverse solver, staleness, correction queue, rumination | 46/46 | 5,227 | 3.9ms | — |
| a.5 | Full pipeline integration | 57/57 | 12,675 | 4.4ms | 97 nodes, 97% coverage, 8/8 algebra |
| b.1 | Incremental LearningSession, conflict-driven | 17/17 | 1,476 | 1.7ms | EQ/NEQ first, ADD at 3 obs |
| **c.1** | **Foundation rebuild: Node + AddressBook + overlaps** | **27/27** | **15** | **0.9ms** | **AND↔EQ: 3 agree, 1 diverge** |
| **c.2** | **Full 60-tool discovery through address book** | **28/28** | **12,469** | **5.0ms** | **40 proc, 7 syn, 58 overlap, 97% cov** |

---

## 10. File Manifest

| File | Lines | Purpose | Status |
|---|---|---|---|
| `/mnt/project/intellon_v6_methodology.docx` | — | Original v6 spec (read-only) | Reference |
| `/mnt/user-data/outputs/intellon_node_design_proposal.md` | ~720 | Architecture spec v3 | **Active — the spec** |
| `/mnt/user-data/outputs/intellon_training_test_plan.md` | ~365 | Training tests 1-11 | **Active — the roadmap** |
| `/mnt/user-data/outputs/intellon_v6_test_plan.md` | ~450 | Dev tests 1-10 | Completed |
| `/mnt/user-data/outputs/intellon_c1_tests.jsx` | ~711 | Foundation: Node + AddressBook | **Active — 27/27** |
| `/mnt/user-data/outputs/intellon_c2_tests.jsx` | ~505 | Discovery pipeline on new foundation | **Active — 28/28** |
| `/mnt/user-data/outputs/intellon_b1_tests.jsx` | ~670 | Incremental learning (pre-rebuild) | **Reference for c.4 port** |
| `/mnt/user-data/outputs/intellon_a5_tests.jsx` | ~872 | Dev final (batch pipeline) | **Reference for comparison** |
| `/mnt/user-data/outputs/intellon_v6.jsx` | ~1200 | Original v6 simulation | Reference |
| `/mnt/user-data/outputs/intellon_a1_test1_2.jsx` | — | Early prototype | Archive |
| `/mnt/user-data/outputs/intellon_a1_tests.jsx` | — | a.2 | Archive |
| `/mnt/user-data/outputs/intellon_a3_tests.jsx` | — | a.3 | Archive |
| `/mnt/user-data/outputs/intellon_a4_tests.jsx` | — | a.4 | Archive |

---

## 11. Critical Implementation Notes

### The AddressBook Pattern
Every `new Node({...})` call should pass the book as second argument: `new Node({type:"tool", label:"ADD"}, book)`. This auto-registers the node. If you create nodes without the book, they work standalone but don't participate in holonic comparison, domain indexing, or reverse lookups.

### Domain Index Auto-Update
When a node gets `addSlot("takes", ...)`, the book's domain index auto-updates. You don't need to manually call `indexDomains()` — it's triggered by addSlot when role is "takes".

### Reverse Lookups are Automatic
When node A calls `addConnection(nodeB, "inverse", 5)`, the book notifies nodeB, and nodeB's `_reverse` map updates. You never need to manually maintain reverse lookups. Query them with `nodeB.getReverse("inverse")` to find "who has me as their inverse."

### Overlap Maps are Bidirectional
When computing overlaps between A and B, store the map on BOTH nodes. The diverge entries need to be perspective-swapped for the second node (A's r1 is B's r2 and vice versa).

### The 158 vs 190 Observation Count
The original methodology describes 190 observations across 8 phases. The c-series code uses 158 observations across 6 phases (Arithmetic, Comparison & Logic, Types & Conversion, Strings, Sequences, Bitwise). The Place Value phase and Algebra (Inverse) phase are not in the PHASES array — Place Value observations are folded into Arithmetic, and Algebra problems are handled separately by the inverse solver. The 97% coverage is 154/158, not 154/190.

### EQ Claims Boolean Observations
This is expected and correct. When boolean observations arrive, EQ matches them because EQ genuinely works on booleans. AND/OR/XOR may never be independently "discovered" from observations — they're discovered as behavioral overlaps of EQ during rumination. The system understands AND as "like EQ except on (F,F)." This is the architecture working as designed (Decision D8, D12).

---

## 12. Open Questions from Design Proposal

1. Should connective type be fixed at creation or mutable?
2. Should concept nodes be pre-built or discovered?
3. What is the relationship between confidence levels and connection weights?
4. How does the system decide when to create a new concept node vs adding to existing?
5. How are number construction templates generalized?
6. What happens when a referenced node is destroyed or invalidated?
7. Can place value understanding generalize recursively?
8. What triggers the transition between work, rumination, and play?
9. Overlap maps are one-hop only (resolved). Remaining: does rumination create shortcuts for stable multi-hop paths?
10. What is the granularity of overlap domains (type-level or sub-range)?
11. How are shortcuts validated when intermediate nodes change?

---

## 13. Resumption Instructions

To continue this work:

1. **Read this handoff first.** It contains everything.
2. **Read the design proposal** (`intellon_node_design_proposal.md`) for architectural details.
3. **Read the training test plan** (`intellon_training_test_plan.md`) for what needs to be built.
4. **The active codebase is c.1 and c.2.** c.2 is the working system. Start from there.
5. **Next step is c.3 or c.4** depending on priority:
   - c.3: Move overlap mapping into tiered rumination (cleaner architecture)
   - c.4: Port LearningSession from b.1 onto c-series foundation (more features sooner)
6. **b.1 is the reference** for how incremental learning works. The LearningSession class needs to be adapted to use the address book instead of direct tool maps.
7. **a.5 is the benchmark.** Any new pipeline should match: 40+ procedures, 97%+ coverage, 8/8 algebra solves, deterministic.
8. **The user cares about:** correctness over speed, conflicts as information not errors, the holonic principle (no type boundaries), and building within the purposeful limitations rather than hacking around them.
