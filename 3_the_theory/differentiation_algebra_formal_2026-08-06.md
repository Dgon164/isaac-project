# The Differentiation Algebra: A Formal Treatment
## Generalization and proofs for the collider loop, the typed ledger, and the census bridge
### Companion to HANDOFF-collider-session.md · 2026-08-06

---

## 0. Purpose and structure

This document generalizes the differentiator and the collision-to-closure loop into a formal theory and proves its core properties. It is organized in two tiers, deliberately separated:

**Tier 1 (exact).** Comparands are sets (extendable to multisets). Every claim is proven outright. The theorems here are unconditional: no false positives, canonical fixed point, evidence-relative completeness, forced posits.

**Tier 2 (statistical).** Comparands are signals; shared parts are estimated against nulls. The theorems weaken to bounded claims conditional on admissibility. The admissibility suite of the handoff is restated here as formal properties, and each empirical failure in the record (the naive peel, the naive null on memory-data) is identified as the violation of a named property.

## The Laws

Stated as laws — short, universal, each standing on a numbered proof below. The exact tier proves I–VII outright; VIII–X govern the noisy, continuous, and layered realizations; the coda is the limit.

**I. Identity.** A thing is what distinguishes it; what no evidence separates is one thing. [Thm 3.4]
**II. Conservation.** Comparison reveals and never creates: operations conserve their operands, and nothing enters the books that was not inside an observation. [Def 1.3; splitting invariant]
**III. Witness.** Nothing is certified without lineage to observation. A posit names; it never testifies. [Thms 3.3, 5.2]
**IV. Canonicity.** What is there does not depend on how you look; any fair search finds the same content. [Thm 3.2]
**V. Refinement.** Evidence sharpens and never corrupts: new observation splits the known, never merges it, never falsifies what was soundly held. [Thm 3.4a–c]
**VI. Accounting.** Every whole must balance against its parts; an imbalance is not an error but a real thing, and must be named. [Thms 4.1, 5.1]
**VII. Detection.** Everything witnessed is priced — as itself, inside a whole, or inside a deficit. Nothing real in evidence is invisible; only isolation is contingent. [Prop 3.5]
**VIII. Medium (conditional).** Nothing certifies except against what nothing looks like in its own medium; an unmatched null refuses rather than answers. [P2]
**IX. Grain (conditional).** On continuous quantity, identity exists only at a declared grain. [6b.3]
**X. Levels (conditional).** Every whole is a comparand; the one operation applies at every level; the ascent route changes cost, never content. [Def 10.4; Prop 10.8]
**Coda — the Hunt.** Every named quarry is eventually caught; the quarry list is never empty. [Prop 7.8]

The separation is the defensibility of the whole: Tier 1 is unassailable; Tier 2 is an implementation of Tier 1 with quantified slack. A conflation of the tiers is the only way the program's claims can be made to look overreaching, so the document never conflates them.

---

# TIER 1 — THE EXACT THEORY

## 1. Definitions

**Definition 1.1 (Universe, comparand, carrier).** Fix a set U (the universe of possible content). A *comparand* is a finite nonempty subset A ⊆ U. Given a finite family of *observed* comparands 𝒜 = {A₁, …, Aₙ}, the *carrier* is V = A₁ ∪ … ∪ Aₙ. Optionally a *scope* S ⊇ V may be declared.

**Definition 1.2 (Differentiator).** The differentiator is the map
D(A, B) = ( A ∩ B , A \ B , B \ A )
called the *shared bin* and the two *residue bins*. Relative to a declared scope S, the *absent bin* of a pair is S \ (A ∪ B). The three bins of D are the lattice operations meet and relative complement; the absent bin is complement relative to scope. Nothing else is ever used.

**Definition 1.3 (Conservation).** For any collision, A = (A ∩ B) ⊎ (A \ B) and B = (A ∩ B) ⊎ (B \ A), disjointly. (Immediate from the definitions; recorded because the implementation checks it on every collision and because Tier 2 will lose it and must account for the loss.)

**Definition 1.4 (Ledger, origins, status).** The *ledger* L is a set of entries, each a comparand tagged with an *origin* and carrying *provenance*:
- **observed** — a member of 𝒜; the immutable add-only layer; provenance is the witness itself.
- **derived** — a nonempty bin of some collision between ledger entries; provenance is the pair of parent entries and the bin type.
- **posited** — minted by the accountability audit (Definition 1.8); provenance is the audit deficit that forced it.

Independently of origin, an entry has the *status* **atomic** iff no collision with any current pool element splits it (produces two nonempty bins from it). Atomicity is provisional and revocable: it is indexed to the current pool, not to the entry.

**Definition 1.5 (The loop).** The *pool* P is the set of ledger entries eligible for collision (posited entries are excluded; see Definition 1.9). A *pass* collides every unordered pair in P and mints (adds to the ledger, with provenance) every nonempty bin not already present. A *fixed point* is a pass that mints nothing. A collision *strategy* is any rule selecting the order of collisions; a strategy is *fair* iff every pair that could produce a new mint is eventually collided.

**Definition 1.6 (Difference closure).** ℛ(𝒜) is the smallest family of subsets of V containing 𝒜 and closed under ∩ and \. **Corrected by prosecution (second review, 08-06):** this family is NOT a ring — it is not closed under union. Counterexample: for A = {1,2}, B = {1,3}, the closure is exactly {{1},{2},{3},{1,2},{1,3}}; neither {2,3} nor A ∪ B ever appears. The structural reason is a one-line theorem, the **splitting invariant**: ∩ and \ both output subsets of their first operand, so every member of ℛ(𝒜) is a subset of some generator — the loop splits and never glues, and the exact tier is deflationary *by construction* (the Tier 1 ancestor of admissibility property P1). Wherever earlier drafts invoked closure under finite union, the valid justification is successive differences: A \ (X₁ ∪ … ∪ Xₖ) = (((A \ X₁) \ X₂) … ) \ Xₖ, using \ alone. ℛ(𝒜) sits inside the genuine ring of unions-of-cells, so the bound |ℛ(𝒜)| ≤ 2^(2ⁿ−1) stands as a (loose) ceiling. The closure is a Boolean algebra relative to V only if V is itself a generator, and relative to a scope S only if S is adjoined; the differentiator alone never manufactures the scope — Theorem 5.2 lives in this gap.

**Definition 1.7 (Cells).** For x ∈ V, let sig(x) = { i : x ∈ Aᵢ } ⊆ {1,…,n}, the *signature* of x. The *cell* of x is [x] = { y ∈ V : sig(y) = sig(x) }. The cells partition V; they are the nonempty regions of the Venn diagram of 𝒜, excluding the outer region. There are at most 2ⁿ − 1 of them. Two elements are called *evidence-separated* iff some Aᵢ contains one and not the other, i.e. iff their signatures differ.

**Definition 1.8 (Accountability audit).** An observed entry A *passes the audit* relative to the current ledger iff A equals the disjoint union of the atomic-status entries contained in it. The *deficit* of A is R(A) = A \ ⋃{ X ∈ L : X atomic, X ⊆ A }.

**Definition 1.9 (Posit and quarantine).** When an audit is run under *partial extraction* (any ledger state short of fixed point, or any restriction of the pool) and R(A) ≠ ∅, the audit mints R(A) with origin posited — exactly the deficit, never a rounder object. **Quarantine rule (typing):** posited entries do not join the collision pool and cannot appear in the provenance chain of any derived entry. A posit is *discharged* when a later observed-or-derived entry equals it, at which point the entry is re-typed and the posit's history is retained as reinforcement.

---

## 2. Structural lemmas

**Lemma 2.1 (Closure).** Every entry ever minted by the loop lies in ℛ(𝒜), and consequently every entry is a union of cells.

*Proof.* Strong induction on the generation step k of the ledger Lₖ. **Base (k = 0):** L₀ = 𝒜 ⊆ ℛ(𝒜) by definition, and each Aᵢ = ⋃{ [x] : i ∈ sig(x) }, a union of cells. **Step:** assume every entry of Lₖ lies in ℛ(𝒜) and is a union of cells; a new entry E at step k+1 arises in one of two ways. *Derivation:* E is a nonempty bin of D(X, Y) with X, Y ∈ Lₖ; since ℛ(𝒜) is closed under ∩ and \, E ∈ ℛ(𝒜), and because distinct cells are disjoint, ∩ and \ of unions-of-cells are unions-of-cells. *Posit:* E = R(A) = A \ ⋃ⱼ Xⱼ over finitely many entries of Lₖ; by successive differences, E = (((A \ X₁) \ X₂) … ) \ Xₖ ∈ ℛ(𝒜), using closure under \ alone — a union of cells by the same disjointness argument. ∎

**Lemma 2.2 (Refinement is well-founded).** Say the ledger's *grain* is the partition of V generated by its atomic-status entries together with the cells' common refinement bound. Each productive mint strictly refines the family of ledger sets or adds a new union-of-cells not previously present; since ℛ(𝒜) restricted to subsets of V is finite (at most 2^(2ⁿ−1) unions of at most 2ⁿ−1 cells), only finitely many productive mints are possible.

*Proof.* By Lemma 2.1 every mintable object is a union of cells, of which there are finitely many; a mint by definition adds an object not already in the ledger; the ledger grows strictly and is bounded above by |ℛ(𝒜)|. ∎

**Lemma 2.2b (Fixed-point closure).** At a fixed point, the ledger L* is closed under nonempty bins: for all X, Y ∈ L*, every nonempty component of D(X, Y) is itself an entry of L*.

*Proof.* Immediate from Definition 1.5: the fixed-point pass collides every unordered pair in the pool and mints nothing not already present; hence each nonempty bin of each pair was already an entry. ∎

*Remark (methodological, load-bearing).* Lemma 2.2b is the *entire* formal content of "fixed point" available to downstream proofs. In particular, no proof conducted at a fixed point may appeal to what further collisions "would eventually" produce — a fixed point is defined by the absence of further productive collisions, so any such appeal is incoherent, not merely informal. Every argument below reasons over the static closed structure L* only, and fairness enters the mathematics at exactly this one point.

**Lemma 2.3 (Fixed-point atoms are cells).** At any fixed point of a fair strategy, the atomic-status entries are exactly the cells of 𝒜.

*Proof.* (⟹) Let X ∈ L* be atomic. Each generator Aᵢ remains in the pool (the observed layer is add-only), and by atomicity no pool element splits X, so X ∩ Aᵢ ∈ {∅, X} for every i — i.e. X ⊆ Aᵢ or X ∩ Aᵢ = ∅. Hence for all x, y ∈ X and all i: x ∈ Aᵢ ⟺ y ∈ Aᵢ, so sig is constant on X and X ⊆ C for a unique cell C. By Lemma 2.1, X is a union of cells; a nonempty union of pairwise-disjoint cells contained in a single cell is that cell. X = C.
(⟸) *Coverage, without process reasoning.* Fix x ∈ V and let 𝒮ₓ = { E ∈ L* : x ∈ E }, nonempty since some generator contains x. Choose M ∈ 𝒮ₓ of minimal cardinality. Suppose some P ∈ L* splits M (both M ∩ P and M \ P nonempty): by Lemma 2.2b both are entries of L*, each a strict subset of M, and x lies in exactly one of them — a member of 𝒮ₓ of strictly smaller cardinality, contradicting minimality. So M is atomic and covers x; the atomic entries cover V. *Disjointness:* if distinct atomics X ≠ Y satisfy X ∩ Y ≠ ∅, then either X ∩ Y is a proper nonempty subset of X — so the pair (X, Y) splits X — or X ⊆ Y properly, so the pair splits Y; either contradicts atomicity. The atomics therefore partition V. By (⟹) each atomic is a cell; the atomic covering x is then a cell containing x, and the cell containing x is unique, so it is [x]. Every cell arises this way, and the atomic entries are exactly the cells. ∎

*Note.* The former version of this proof (and its external formalization) argued coverage by asserting that fair collisions "would eventually isolate" uncovered elements — an appeal to future process made *at* a fixed point, where no future process exists. The repair above replaces it with a minimality argument over the closed static structure, using fairness only through Lemma 2.2b. This closes what §"soft spots" previously flagged as the coverage gap; the lemma is now proven at full rigor.

---

## 3. The four core theorems

**Theorem 3.1 (Termination).** Under any fair strategy, the loop reaches a fixed point in finitely many passes; the total number of productive mints is bounded by |ℛ(𝒜)| ≤ 2^(2ⁿ−1), and the number of atomic entries at fixed point is at most 2ⁿ − 1, with n the number of observed comparands.

*Proof.* Immediate from Lemma 2.2: each pass either mints (strictly growing a finitely-bounded ledger) or is a fixed point. ∎

*Remark (bounds are content, not cost).* The doubly-exponential ledger bound is the latent layer of the handoff's §3: the intermediates are the derived record. The atom bound is small (2ⁿ − 1); the ledger bound prices full provenance, not the answer. In practice the loop mints far fewer than the bound because only witnessed regions are nonempty.

**Theorem 3.2 (Confluence; canonicity of the fixed point).** All fair strategies reach the same fixed point atom set, namely the cells of 𝒜. The fixed point is therefore a property of the evidence, not of the procedure.

*Proof.* Lemma 2.3 makes no reference to the strategy beyond fairness. ∎

*Corollary 3.2.1 (Confluence as admissibility test).* Contrapositively: if two fair collision orders yield different terminal atom sets, at least one operator in use is not the exact differentiator (it deposits, deletes, or mis-bins). Order-sensitivity is the signature of an inadmissible component. (This is the six-shuffle demonstration of the handoff's §2, now with its logical status fixed: the demo instantiates a theorem, and the production test inherits the theorem's contrapositive.)

**Theorem 3.3 (Soundness; no false positives).** Every entry of observed or derived origin is a nonempty element of ℛ(𝒜): it is witnessed, via its provenance chain, as a finite ∩/\ combination of observed comparands. In the exact tier a false mint — an entry with no realization in the evidence — is impossible by construction.

*Proof.* Lemma 2.1 plus the mint rule (only nonempty bins mint). Provenance is the certificate: unwinding it rewrites the entry as an explicit term over 𝒜. ∎

**Theorem 3.4 (Completeness relative to evidence; the identity criterion).** At the canonical fixed point, x and y lie in the same atom iff they are not evidence-separated: no observed comparand contains one without the other. Hence the atoms are precisely the equivalence classes of functional indistinguishability with respect to the evidence, and:
(a) *Monotonicity.* Adding a new observed comparand can only split atoms, never merge, delete, or alter them.
(b) *Revocable atomicity.* "Atomic" is correctly a status: it asserts only that current evidence does not separate the entry's elements, a claim the next observation may revoke — and may only revoke by refinement.
(c) *Persistence.* No extension of the evidence can convert a sound entry into an unsound one: right grounds cannot ground a wrong higher order.

*Proof.* The main claim is Definition 1.7 plus Lemma 2.3: atoms are cells, and cells are signature classes. (a): a new generator A_{n+1} refines each cell C into C ∩ A_{n+1} and C \ A_{n+1}, discarding empty parts; no other change to the partition is possible. (b) restates (a) at the entry level. (c): soundness of an entry is its membership in ℛ(𝒜), and ℛ(𝒜) ⊆ ℛ(𝒜 ∪ {A_{n+1}}) — witnesses are never invalidated by more evidence. ∎

*Remark (scope of the claim).* Theorem 3.4 characterizes the idealized limit — a fair strategy run to closure — and is **not** the theory's commitment. The theory claims something weaker and more defensible: not that every atom will be derived, but that every atom is *detectable*, as a single or as part of a larger whole. That weaker claim is Proposition 3.5; it holds unconditionally at every ledger state, needs no fairness hypothesis and no budget, and it is what the certified-lower-bound regime (Theorem 4.2) actually relies on.

**Proposition 3.5 (Detectability without isolation).** Every atom of the evidence lies beneath at least one observed comparand, and at every ledger state — closure reached or not — it is priced by the books: it is either isolated (an atomic entry), or a constituent of a composite entry, or part of an audit deficit. In all three cases its content is contained in a witnessed whole and enters that whole's accounting. No atom is invisible; only its *isolation* is contingent on collision history and budget.

*Proof.* An atom is a cell C with sig(C) ≠ ∅ (Definition 1.7), so C ⊆ Aᵢ for every i ∈ sig(C). Fix such an Aᵢ and any ledger state. Definition 1.8's audit subtracts *atomic-status* entries only, so exactly two cases arise: either C equals a found atomic entry (isolated), or C is disjoint from every found atomic (cells are disjoint, and atomics are cells or unions thereof), hence C ⊆ R(Aᵢ) — priced in the deficit, which is itself evidence-real by Theorem 5.1(a). If C additionally lies inside a composite derived entry, that composite is a further witnessed whole containing it (Theorem 3.3), but it is not a separate audit line. In every case C's content is contained in a witnessed whole and enters the accounting. ∎ *(Wording corrected by second review: an earlier draft described a three-way audit decomposition the definition does not perform; the detectability claim was and is unaffected.)*

*Remark.* Theorem 3.4 is the Myhill–Nerode structure (states identical iff no experiment separates them) arrived at from the differentiator alone; the loop is then a partition-refinement algorithm in the Paige–Tarjan family, with two additions the classical setting lacks: full provenance on every refinement, and the posit channel of §5. By the three-plate standard, the convergence is validation; the additions are the contribution.

---

## 4. Accountability

**Theorem 4.1 (Partition identity).** At the canonical fixed point, every ledger entry — in particular every observed comparand — equals the disjoint union of the atoms contained in it, and this decomposition is unique. The audit of Definition 1.8 passes for every entry, with deficit ∅.

*Proof.* Every entry is a union of cells (Lemma 2.1); at fixed point atoms are the cells (Lemma 2.3); distinct cells are disjoint, and the set of cells under a given entry is determined by the entry, giving uniqueness. ∎

**Theorem 4.2 (Full closure never posits).** The posit operation is unrealizable at the canonical fixed point: every audit deficit is empty. Positing is definable only under partial extraction. Consequently, for any process whose output is a certified lower bound on extraction (any real census), positing is the permanent companion operation rather than an exceptional one.

*Proof.* First sentence: Theorem 4.1. Second: immediate. Third: a certified-lower-bound regime is by definition never known to be at fixed point, so audits may carry nonempty deficits at any stage. ∎

---

## 5. The posit calculus

**Theorem 5.1 (Posits are forced, exact, and unique).** Under partial extraction, suppose observed entry A fails its audit with deficit R = R(A) ≠ ∅. Then:
(a) R ∈ ℛ(𝒜): the deficit is itself a real element of the evidence ring — the books' failure to balance is not noise about the books but an object in them.
(b) R is the unique minimal object whose adjunction balances A's audit; any strictly larger candidate imports unwitnessed content and any smaller one leaves the audit failing. "One posit per accounting failure, carrying exactly the leftover, never rounder" is therefore not a discipline imposed on the operation but the only version of the operation that exists.

*Proof.* (a) R = A \ ⋃ Xⱼ = (((A \ X₁) \ X₂) … ) \ Xₖ over ledger entries Xⱼ — successive differences, closure under \ alone. (b) A balances iff the adjoined object equals A minus the union of the already-found atoms under A, which is R; set-theoretic equality has one solution. ∎

**Theorem 5.2 (Quarantine preserves soundness; scope inflation is the one hazard).** With the quarantine rule of Definition 1.9 in force, Theorem 3.3 extends verbatim to the full system with posits active: every certified (observed/derived) entry retains an observed-lineage witness, and no posit can launder itself into support. Moreover the quarantine is necessary, not prudential, in exactly one place: a posit taken against a *declared scope* S ⊋ V (an absent-bin audit) is an element of ℛ(𝒜 ∪ {S}), not of ℛ(𝒜) — its reality is conditional on the scope declaration, which is an assumption, not evidence. Carrier-relative posits (Theorem 5.1) are evidence-real; scope-relative posits are hypothesis-real. The typing must distinguish them or soundness acquires a hidden premise.

*Proof.* First claim: the provenance chains of observed/derived entries are unchanged by the presence of quarantined entries (they cannot appear in them, by the rule), so the Theorem 3.3 certificate construction goes through. Second claim: by construction S ∉ ℛ(𝒜) in general (Definition 1.6 remark), and S \ (…) terms require S. ∎

*Remark (the Pauli arc, typed).* The neutrino-shaped exhibit of posit_demo.py is the intended semantics of discharge: books fail → exact deficit minted as target → later witness arrives → entry re-typed with the posit's full history as reinforcement. Theorem 5.1(b) is why the 26-year wait converges on *the same* entry rather than a stranger.

---

## 6. The three reality classes, formally placed

**Common but real.** Cells of high witness multiplicity: |sig(x)| large, and (in the loop's dynamics) minted repeatedly as the shared bin across diverse parent pairs. Reinforcement count is a canonical statistic of the fixed point, not an add-on: for cell C, its shared-bin multiplicity is determined by how many entry pairs contain it, which Lemma 2.1 fixes as a function of the evidence.

**Rare but real.** *Proposition 6.1 (single-witness structural cap).* A cell C with |sig(C)| = 1 — contained in exactly one generator — can never arise as the shared bin of two entries with disjoint generator-support; every appearance of C in a derivation is as a residue. *Proof:* a shared bin of entries X, Y lies in X ∩ Y; if C's sole generator is Aᵢ, then C ⊆ X ∩ Y forces both X and Y to have Aᵢ in their provenance support. ∎ — Hence single-witness reality is carried by recurrence-as-residue until a second witness arrives, and the add-only layer is what makes the eventual second witness reinforce rather than re-mint (Theorem 5.1(b) again). Directed collisions against the low-count tail change discovery *rate*, not discoverability: by Theorem 3.2 the terminal atom set is strategy-independent; exploration budget buys time-to-isolation only. That the framework can say precisely what exploration buys — and what it cannot — is a feature.

**Missed but real.** Theorems 5.1–5.2. The x-component is an object, its minting is forced, its quarantine is what keeps the rest deflationary.

**Theorem 6.2 (Reflexive closure of the triad).** Fix a ledger state L under partial extraction and let 𝔈 denote the canonical fixed-point atom set of the full evidence (Theorem 3.2: well-defined independently of any procedure). Define K(L) = atoms isolated in L (known), and note every audit deficit in L is a union of not-yet-isolated atoms. Then the differentiator applied to the pair (𝔈, K(L)) at the level of atom sets yields:
- shared bin = K(L): the known;
- residue of 𝔈 = atoms real in evidence but unisolated in L: the resolvable — reachable by further collisions (Theorem 3.2 guarantees the loop will isolate them);
- absent bin (relative to the audit's scope) = content visible only as deficit: the inferred, entering the books exactly when an audit prices it.
Partition identity at this level — an epistemic state is known ⊎ resolvable ⊎ inferred-deficit, no fourth bin — is Theorem 4.1 applied to the state itself. The scheduler policy (exploit the known, directed-collide the resolvable, build detectors for the inferred) is then the unique origin-respecting assignment of the three collision modes to the three bins.

*Proof sketch.* The bin identifications are definitional once 𝔈 and K(L) are taken as comparands over the universe of atoms; partition identity is inherited because atom sets are sets. The claim's content is that no fourth epistemic category is constructible from the differentiator's vocabulary — which holds because D has three bins and Theorem 3.2 makes 𝔈 canonical. What never registers in any audit against any declared scope costs nothing and is, by the framework's realism, not yet anyone's problem. ∎

**Definition 6.3 (Irreducible k-ary structure).** A structure over components X₁, …, X_k is *irreducible k-ary* iff the components jointly constitute it while every proper sub-collection carries no trace of it. Conceptually: a thing that exists only when k constituents coincide — fire is 3-ary (heat, fuel, oxidizer), flight is 4-ary (lift, weight, thrust, drag). Statistically (Tier 2): joint dependence nonzero, every proper subset independent; parity-type constructions (a component equal to a product of signs of others) realize this at every k, and the planted triple of the record is exactly 3-ary parity.

**Proposition 6.4 (Pairwise blindness).** For irreducible k-ary structure with k ≥ 3, every binary collision among the involved components certifies null — by definition, since proper sub-collections are traceless. Detection therefore requires either an instrument of arity ≥ k (the group lens: products/compositions over the family, gated by a k-ary null) or an accounting deficit pointing at the involved components. The binary differentiator is not thereby incomplete: D is the *operator*, and the lens family carries the arity. (Exhibit: best pairwise score 0.013 among the three planted columns; the product lens with triple-null gate certified exactly the planted triple, 1 of 2,024 candidates, at 0.927.)

*Remark (the triad is the operator's arity, not the world's).* The three bins of D are a fact about comparison — two comparands against a scope have exactly three outcomes — and the reflexive closure (Theorem 6.2) inherits that fact about the *operation*. Nothing in the theory asserts that the world's structures come in threes: constitutive arities are unbounded, and higher arities are combinatorially rarer to find — candidate k-tuples grow as C(F, k) while real ones are sparse. That growth is the formal ground of the aim-first doctrine: full enumeration only at toy scale; at census scale, spend k-ary checks where deficits point. Conflating the triad (bins of the operator) with a claim of universal three-ness in the world would be a category error the document explicitly disowns.

## 6b. The axes of quantity — the seam between the tiers

**Definition 6b.1 (Valuation).** Fix the universe U. A *valuation* assigns each comparand a function U → 𝕍 for an ordered value structure 𝕍 with meet = min and residue = monus (truncated subtraction). Three valuations matter: **Boolean** 𝕍 = {0,1} (presence: the current Tier 1, where min = ∩ and monus = \), **count** 𝕍 = ℕ (multisets), and **amount** 𝕍 = ℝ₊ (weighted content). The differentiator is unchanged across all three — D(A,B) = (min(A,B), A ∸ B, B ∸ A) — so the tiers are not two theories but two valuations of one operator, with ℕ the exact intermediate.

**Proposition 6b.2 (Count valuation; the linear audit) — REVISED BY PROSECUTION.** Under 𝕍 = ℕ the natural grain is 1 and conservation (Definition 1.3) becomes conservation of token counts — stoichiometric conservation as an instance (Lavoisier's law at valuation ℕ). *Confluence:* empirically supported at 200/200 randomized multiset families × 3 shuffled strategies; proof still owed. *Atom characterization — the original conjecture is false:* atoms at grain 1 are NOT in general unit multisets. Counterexample (found by the suite): family {2:3, 1:4} and {0:3} — disjoint supports, so no collision grinds multiplicity; the fixed point is the observed pair, each its own atom, and units never mint. The correct principle is Theorem 3.4's own: atoms are the *min/monus-indistinguishability classes under the evidence* — a multiset whose internal copies no comparand separates is one atom, exactly as functional indistinguishability requires. Where the evidence supplies multiplicity gradients (e.g. {a:2}, {a:3}), units emerge; where it doesn't, coarser atoms stand, revocable by the next observation. Full characterization of count-valuation atoms, and the conditions for the integer-linear audit A = Σ nᵢ·atomᵢ, are now *named open problems* with a counterexample pinning their boundary.

**Proposition 6b.3 (Amount valuation; grain as a precondition of "atom").** Under 𝕍 = ℝ₊ no natural grain exists; atoms are well-defined only relative to a declared grain, and confluence (P3) holds only relative to a pre-registered grain schedule. The σ-fold doctrine is therefore not Tier 2 hygiene but the condition under which "atom" refers to anything on the amount axis — the formal location of the grain problem the record found empirically ("closure differentiates along the coefficient axis; atoms emerge at grain values").

**Proposition 6b.4 (Ratio adds no primitive).** Ratio, rate, density, concentration — the intensive quantities — are shared structure under *quotient lenses* (normalization by total, time, volume). The intensive/extensive distinction is recovered as a theorem: intensive properties are the invariants under quotient lenses; extensive properties are their residues. Composites with equal ratios and different amounts are level-appropriate instances of one structure with scale as filling — the structure/filler law on the quantity axes.

**Proposition 6b.5 (Composition underdetermines identity; isomer blindness).** Two composites may agree on type support, count vector, and amount, and differ in *arrangement* — the relational structure among tokens (isomers: one formula, many molecules). A composition census is provably arrangement-blind, exactly as pairwise collision is parity-blind (Proposition 6.4); arrangement is k-ary relational structure and demands relational lenses. The identity of a composite is the tuple ⟨type support, count vector, arrangement⟩, with amount quotiented out by ratio lenses. A finite type alphabet (the 118) therefore bounds nothing about the composite space; it bounds only the base of the tower.

**Proposition 6b.6 (Compression; counts as representation).** Storing each distinct entry once with a multiplicity counter, instead of repeated instances, is the ℕ-valuation applied to the ledger itself — the theory as its own storage layer. Consequences: (i) *Mint-and-count is compression.* Extracting a recurring group and replacing instances with references is the operation of every compressor (run-length, dictionary, grammar-based); the accounted fraction and the compression ratio are one number in different units — the MDL/Kolmogorov convergence ("comprehension is compression"). A trained network is a lossy compressor billing for the answer and never the books; the ledger is a compressor with provenance — same dividend, plus receipts. (ii) *Typed counters are mandatory.* The reality discriminator is a predicate on the count *vector* (shared-bin count vs residue count, counts per parent class; diversity = that vector's entropy); a single total counter compresses away the statistic that separates real groups from slicing artifacts. (iii) *Canonical ≠ minimal; the claim level is: workable, not minimal.* The atom basis is canonical, not smallest: hierarchical dictionaries over derived entries can beat flat atom listings, and the smallest-grammar problem is NP-hard, so optimality is never claimed — workability is claimed and is provable (lossless at exact valuations, bounded, strictly smaller than the flat record whenever anything recurs). The derived layer with its provenance is exactly the candidate dictionary (the grammar's nonterminals); an MDL-selected economical representation is a *view* over the ledger while the atoms remain its *content* — economy and truth coexist without conflict because every candidate representation is provenance-valid. (iv) *Lossless condition.* Counting presupposes an identity gate: exact in the Boolean/ℕ valuations (compression lossless by construction); in ℝ the counter is quantization at declared grain and the collapse is billed to the audit's error budget like all Tier 2 slack.

*Remark (placement).* This section is the seam: Boolean → ℕ → ℝ₊ is the ladder from the exact tier to the census's weighted medium, and Prop 7.8(c)'s count/mass distinction is the ℕ-axis and ℝ₊-axis of one bookkeeping. Every axis reuses the operator; what changes is the carrier and valuation — the recursion claim extended across quantity itself.

---

# TIER 2 — THE STATISTICAL REALIZATION

## 7. What changes and what is preserved

**Definition 7.1 (Statistical comparands).** Comparands are now columns/signals X: Ω → ℝ; "shared part" is an estimated common component; "empty bin" is replaced by *certification against a null*: a bin counts as nonempty iff a dependence score exceeds a gate calibrated on a null ensemble. Conservation (Definition 1.3) is lost exactly to estimation error, and every Tier 2 pathology is an unaccounted conservation leak.

**Definition 7.2 (Admissibility).** A Tier 2 component (operator, null, gate, schedule) is *admissible* iff it satisfies:
(P1) **Deflation / report-never-deposit.** For any collection containing known-independent columns, applying the component leaves every independent pair certifying null (up to the gate's declared false-positive rate α). Operators may remove or report dependence; they may not create it.
(P2) **Null–medium matching.** The null ensemble's invariance transformations preserve the data's own dependence class (its "medium"): the null must generate counterfactuals that differ from the data only in the alignment under test. For iid columns, permutation suffices; for columns with memory, the null must preserve each column's autocorrelation (e.g. circular shifts) and break only cross-alignment.
(P3) **Confluence.** Terminal certified structure is invariant under fair reorderings of the pipeline, up to declared tolerance (Corollary 3.2.1's Tier 2 image).
(P4) **Approximate reconstruction.** Every observed column decomposes as certified parts + residue with an explicit error budget; the audit of Definition 1.8 survives as a budgeted identity, and deficits beyond budget mint posits (with quarantine, unchanged — Theorem 5.2 needs no weakening, being a typing theorem).
(P5) **Pre-registration.** Gates, grain (σ-fold), increment/decrement schedules, and stopping rules are frozen before contact with evaluation truth.

**Proposition 7.3 (Diagnosis of the record's two violations).** The naive peel violates (P1): subtracting a latent estimated on the same data injects the estimator's error as a common component across all touched columns — a deposit — which the census then certifies (observed: precision 1.000 → 0.603). The naive timepoint-shuffle on AR columns violates (P2): permutation destroys each column's memory, so the null ensemble is a *different medium* whose dependence scores are systematically low, mis-calibrating the gate (observed: 36 false pairs on 12 independent columns). Both failures are thus attributable to named inadmissible components, both were predicted by the corresponding property, and both repairs restore the property: split-half estimation restores (P1) by independence (below); the circular-shift null restores (P2) by construction.

**Proposition 7.4 (Split-half deflation).** Partition samples into halves H_A, H_B. Estimate the latent ℓ̂_A on H_A only and subtract it on H_B (and symmetrically). Then on H_B the subtraction error ε = ℓ̂_A − ℓ is a function of H_A alone, hence statistically independent of every column's H_B values given independence of halves; the subtraction therefore cannot increase any H_B cross-column dependence in expectation, and induced spurious dependence is O(‖ε‖²) concentrated at the estimator's own variance rate — below any gate calibrated with matching grain, for sufficient n. Deflationary by construction, with the residual leak *quantified* rather than denied. ∎ (sketch)

**Proposition 7.5 (False-certification bound).** For an admissible configuration, the probability that any fixed independent pair is certified is at most α (gate level) + λ (deposit leakage, per P1/7.4) + μ (null mis-calibration, per P2); with (P1), (P2) enforced, λ and μ are driven toward 0 and the standing zero-false-positive record is the empirical shadow of this bound at small α, not a streak. The Tier 1 statement "false mints are impossible" is recovered in the limit of exact operators — which is precisely the sense in which Tier 2 implements Tier 1.

**Remark 7.6 (Indicator precondition and the true complement).** Tier 2 extraction bootstraps from an *indicator*: any above-null trace under any lens, or any shape-blind dependence deficit in the books. The foundry (spooling random lenses, keeping split-half winners) shows the lens *family* is growable whenever an indicator exists at all, so the binding precondition is the indicator, not the lens set. The in-principle complement of the method is data engineered so that no efficiently computable indicator exists below computational hardness bounds — which is a serviceable definition of encryption. The method works on natural data because nature does not encrypt. (Declined territory, kept as the boundary statement.)

**Remark 7.7 (The differential census prediction, stated as a measurement).** If trained network layers approximate unaudited mint-and-peel — the same loop with no books, superposition as many unaudited passes, gradient descent billing for the answer and never the provenance — then the layerwise accounted-fraction under an admissible census should increase with depth and correlate with early-exit confidence. This is the point where the analogy stops being framing and becomes an experiment with a sign prediction.

**Proposition 7.8 (Asymptotic completeness; the sum).** Fix a real component σ with positive-probability indicator and effect size δ_σ > 0. Under an admissible configuration with consistent estimators, matched null, and a summable gate schedule (Σₙ αₙ < ∞): P(σ uncertified after n samples) ≤ e^(−c(δ_σ)·n) for some c(δ_σ) > 0, and Borel–Cantelli grants, almost surely, only finitely many false certifications ever. Consequently:
(a) *Finite or bounded-below spectra:* for finitely many components, or effect sizes bounded away from zero, P(any component remaining) ≤ Σ_σ e^(−c(δ_σ)n) → 0 — a union bound; the certified structure converges almost surely to the true structure.
(b) *Pointwise, not uniform:* if the effect-size spectrum accumulates at zero, every fixed component is eventually certified, but at every finite n mass remains below the 1/√n floor. Uniform completeness fails permanently — Theorem 4.2 is the pointwise/uniform gap, not a finite-n artifact, and no limit retires it. Every named quarry is eventually discharged; the quarry list is never empty.
(c) *Mass completeness:* if the spectrum is square-summable (finite total signal), the accounted fraction converges to 1 even for infinite component count — the residual vanishes in mass while never vanishing in count. The census's fidelity number and its x-component list obey different convergences, and both statements are true simultaneously.
Hypotheses (a)–(c) locate three doctrines as load-bearing limit conditions rather than hygiene: the indicator precondition (zero-indicator components are untouched by n → ∞), null–medium matching under stationarity (drift breaks accumulation), and the pre-registered summable schedule (fixed α over unboundedly many tests accumulates false positives, voiding the Borel–Cantelli half). ∎ (sketch; concentration and consistency hypotheses to be written out with 7.4/7.5)

---

## 8. Theory–exhibit correspondence

| Formal result | Exhibit in the record |
|---|---|
| Thm 3.1 Termination | collider.py — closure in three passes on (abcd, a, cd, de) |
| Thm 3.2 Confluence | collider.py — six shuffled orders, one atom set |
| Cor 3.2.1 Order-sensitivity test | admissibility suite (specified; property-test build) |
| Thm 3.3 Soundness | typed_collider.py — provenance chains; standing zero-FP record |
| Thm 3.4 Completeness/identity (limit) | grain behavior; revocable atomic status |
| Prop 3.5 Detectability without isolation | certified-lower-bound regime; posit ledger as named quarries |
| Thm 4.1 Partition identity | typed_collider.py — accountability audit |
| Thm 4.2 Closure never posits | first implementation attempt (the theorem that "fell out") |
| Thm 5.1 Forced exact posits | posit_demo.py — deficit minted, never rounder |
| Thm 5.2 Quarantine soundness | posit quarantine rule; discharge-and-reinforce arc |
| Prop 6.1 Single-witness cap | neutrino/26-year arc; residue-carried reality |
| Thm 6.2 Reflexive triad | scheduler policy: exploit / directed-collide / detect |
| Prop 6.4 Pairwise blindness of k-ary | three_fixes.py — group lens, 1 of 2,024 triples certified |
| Prop 7.3 (P1) violation | mint_peel.py — precision 1.000 → 0.603, preserved as record |
| Prop 7.3 (P2) violation | three_fixes.py — 36 false pairs under naive null |
| Prop 7.4 Split-half deflation | split-half minting repair |
| Prop 7.5 FP bound | zero-FP standing fact under admissible configs |
| Rem 7.6 Indicator precondition | lens_bootstrap.py — invisible → posited → foundry → observable |

---

## 9. Placement proofs — every component against the whole

Each component of the system is now proved into its position: its *load* (which results cite it), its *ablation* (the minimal counterexample showing what breaks without it), and its *verdict*. A component whose ablation breaks nothing is decoration and is removed; a component whose ablation breaks a theorem is load-bearing; a component whose ablation breaks only the idealization is graded honestly as such. The analysis does not rubber-stamp: two components below turn out NOT to carry the theory's core commitment, and saying so is what makes the rest of the section credible.

**P-1 (The three bins; why D has exactly this shape).** *Claim:* relative to a scope S ⊇ A ∪ B, the bins of D(A,B) plus the absent bin are exactly the cells of the two-generator family {A, B} — the four signature classes (in both; in A only; in B only; in neither). They are exhaustive, disjoint, and minimal: no fifth region exists over two comparands, and dropping any bin loses one signature class entirely. *Proof:* sig(x) over two generators takes exactly four values; each bin is one value's preimage. ∎ *Consequence (self-similarity):* D is the n = 2 instance of the theory's own fixed point — a single collision computes the canonical atom set of a two-element evidence family, and the loop is nothing but the inductive extension of the base case to n. The operator is not a design choice the theory uses; it is the theory at its smallest size. *Verdict:* constitutive.

**P-2 (Shared bin ∩) — CORRECTED BY PROSECUTION.** The original placement claim — shared bin load-bearing for isolating multi-witness cells — was *disproven by the first run of the property suite* (Surface 3 operating as designed). Counterexample: residue-only closure on {ab, ac} isolates a via the chain ab \ ac = b, then ab \ b = a. The underlying identity: **X ∩ Y = X \ (X \ Y)** — relative complement regenerates intersection in two steps (verified on 2,000 randomized pairs; the count-valuation analog a ∸ (a ∸ b) = min(a, b) holds identically). *Corrected verdict:* the shared bin is an **accelerator** — provenance depth 1 instead of 2 — not load-bearing; the residue operator alone is the minimal complete generator of the ring, in both Boolean and count valuations. Note what survived unchanged: Proposition 3.5 (detectability) was never at stake, and P-1's claim that D's three bins are the canonical n = 2 *cell decomposition* stands — what falls is only the independence of the bins as generators. The record keeps the original overclaim and its prosecution deliberately, per the standing doctrine on preserved failures.

**P-3 (Residue bins \).** *Load:* isolation of every cell whose signature excludes some witnessing generator — in particular every single-witness cell C = Aᵢ \ ⋃ⱼ≠ᵢ Aⱼ. *Ablation:* intersection-only closure on {abcd, a} is the meet-semilattice {abcd, a}; bcd never mints; and because posits are quarantined from the pool, bcd is not merely slow to isolate but *unisolable forever* — the rare-but-real class dies structurally. *Verdict:* load-bearing; jointly with P-2, the two bin classes partition the isolation work by signature type (∩ isolates the multiply-witnessed, \ isolates the remainders), which is the precise sense in which neither is redundant.

**P-4 (The nonempty-mint gate).** *Load:* the "nonempty" clause of Theorem 3.3 — the exact tier's entire defense against false positives is that only inhabited bins mint. *Ablation:* mint empty bins and soundness fails definitionally (entries witnessing nothing). *Tier 2 image:* the null-calibrated certification gate IS this component under noise — "nonempty" becomes "above the null." The gate is therefore not Tier 2 hygiene bolted on; it is the statistical realization of a Tier 1 load-bearing clause. *Verdict:* constitutive; its Tier 2 image inherits the load.

**P-5 (Add-only; never delete).** *Load:* discharge uniqueness (Theorem 5.1(b)'s convergence onto the same entry), reinforcement continuity, and order-independence extended to *temporal* order. *Ablation:* allow decay-to-deletion at any threshold. Then a single-witness residue deleted at time t is re-minted as a provenance-less stranger when the second witness arrives at t′ > t, while under the schedule t″ > t′ it is reinforced instead — the terminal ledger now depends on the arrival schedule. By Corollary 3.2.1's signature, schedule-dependence is the mark of an inadmissible component: deletion makes *time* an inadmissible collision order. *Verdict:* load-bearing. (Decay-to-floor is admissible; it reorders priority, not existence.)

**P-6 (Provenance).** *Load:* Theorem 3.3's certificate is constructive only through the parent chain; the reality discriminator (shared-across-diverse-parents vs one-chain residue) is a predicate *on* provenance; and the quarantine rule is enforceable only if posited origin is recorded. *Ablation:* drop provenance and the ledger is a bag of sets — soundness degrades to a nonconstructive existence claim, derived and posited become indistinguishable, quarantine becomes undefinable, and by the collapse of Theorem 5.2 hidden premises enter support silently. One removed component forfeits three results. *Verdict:* load-bearing, maximally cited.

**P-7 (Atomic as status, not origin).** *Load:* consistency with monotonicity. *Ablation:* make atomicity permanent. Pool {ab}: ab is atomic. Adjoin the observation a: Theorem 3.4(a) forces the refinement {a, b}; permanence forbids it. The system must then either reject evidence or hold a contradiction — so permanent atomicity is not a stricter version of the design but an inconsistent one. *Proof:* the two-line derivation above. ∎ *Verdict:* forced.

**P-8 (The conservation check).** *Load:* the semantics of the audit. Under conservation (Definition 1.3 verified per collision), a nonempty deficit *entails* unextracted real content (Theorem 5.1(a)). *Ablation:* admit one leaking operator (A ≠ shared ⊎ residue) and the entailment weakens to "real content OR leak" — the posit calculus loses its meaning, because a posit may now name the operator's error instead of the world's structure. This is not hypothetical: the naive peel is exactly an unconserved operator, and its deposits were certified as discoveries. The conservation check is what makes audit failure *about the world*. *Verdict:* load-bearing; the separator between discovery and defect.

**P-9 (Fairness).** *Load:* Theorems 3.1/3.2 only — reaching the canonical limit. *Ablation:* an unfair strategy stalls short of closure with coarse atoms; but Proposition 3.5 is untouched, since detectability holds at every state. *Verdict:* NOT load-bearing for the theory's commitment; it is the hypothesis of the idealization and nothing else. (This grades the component exactly as the correction of 08-06 requires: isolation is contingent, detection is not.)

**P-10 (The posit quarantine).** *Load:* the informativeness of accounting. *Ablation (circularity proof):* let posits serve as support. Then every failing audit repairs itself — mint the deficit, count it as support, books balance — so audit failure occurs never, carries zero information, and Theorem 4.2 trivializes: partial extraction becomes indistinguishable from closure, and the missed-but-real class is undetectable *by the very operation that was built to detect it*. The quarantine is not caution about posits; it is what keeps the books capable of failing, and a book that cannot fail cannot inform. *Verdict:* load-bearing; the one deposit in the stack is admissible only because it is inert.

**P-11 (Binary operator vs k-ary operators).** *Exact tier:* binary collisions generate the full ring (Lemma 2.1) and reach every cell (Lemma 2.3), so a k-ary differentiator — computing the 2ᵏ − 1 internal cells of k comparands in one step — adds speed and no content: by confluence it lands on the same fixed point. Verdict there: accelerator. *Statistical tier:* the grading inverts. Certification, unlike algebra, fails pairwise on irreducible k-ary structure (Proposition 6.4), so arity-k instruments become *necessary*, not convenient. The component's place is thus judged against what is being done: against expressibility (Tier 1) binary is complete; against certifiability under noise (Tier 2) it is not, and the group lens is the arity the medium demands. *Verdict:* binary constitutive as operator; k-ary lenses load-bearing in Tier 2 only.

**P-12 (Split-half estimation).** *Necessity:* exhibited by the record — the same-data peel deposits (precision 1.000 → 0.603); a proof-by-actual-counterexample, preserved deliberately. *Sufficiency:* Proposition 7.4. *Verdict:* load-bearing for (P1) in Tier 2.

**P-13 (Null–medium matching).** *Necessity:* exhibited — the naive shuffle on memory-bearing data certified 36 false pairs, and would have silently voided the standing record had the data not been iid until now. *Sufficiency:* the circular-shift run (zero false, true dependency retained). *Verdict:* load-bearing for (P2); "the null travels with the loop" and "the null matches the medium" are one component seen twice.

**P-14 (Pre-registration).** *Load:* the interpretability of Proposition 7.5's α — a gate tuned after contact with truth is a fitted parameter, and the false-certification bound stops referring to anything. *Ablation:* forking-paths selection; the bound survives syntactically and dies semantically. *Verdict:* load-bearing for the meaning, rather than the mechanics, of every Tier 2 number.

**P-15 (The level tower; self-application).** *Load:* mintability of inter-dataset rules — invariant structure whose per-dataset fillings differ (§10). *Ablation:* restrict the system to one level (raw comparands only, pool-merging allowed). Then any rule of the form "shared structure, dataset-indexed parameter" is unmintable: the merged shared bin on the relation is empty whenever the fillings conflict (minimal counterexample: y = 2x and y = 5x — merging destroys exactly what the collision of ledgers preserves), while span-irreducible content across datasets remains detectable only in joint books that a single-level system never opens. *Proof of admissibility:* ledgers are sets of typed entries, so D applies verbatim; every level-2 mint carries provenance into level-1 provenance, so Theorem 3.3's certificate construction lifts by composition, and quarantine typing lifts unchanged. Self-application adds no new operator — only a new comparand type. *Verdict:* load-bearing for cross-rule structure; inert for cross-content (pool merging suffices there), and the criterion separating the two cases is itself formal: merge iff the shared thing survives in raw coordinates, ascend iff it exists only in structure coordinates.

**Placement summary.**

| Component | Load | Ablation breaks | Verdict |
|---|---|---|---|
| Three bins of D | everything downstream | the operator itself | constitutive (P-1) |
| Shared bin ∩ | provenance-depth acceleration | nothing (∩ is \-derivable) | accelerator — corrected by suite (P-2) |
| Residue bins \ | isolation of remainders | rare-but-real dies structurally | load-bearing (P-3) |
| Nonempty gate | soundness clause | Thm 3.3; Tier 2 gate | constitutive (P-4) |
| Add-only layer | discharge continuity | temporal order-dependence | load-bearing (P-5) |
| Provenance | certificates, discriminator, quarantine | Thms 3.3, 5.2 + discriminator | load-bearing (P-6) |
| Atomic-as-status | consistency | contradiction with monotonicity | forced (P-7) |
| Conservation check | audit semantics | posit meaning (leak vs world) | load-bearing (P-8) |
| Fairness | the limit only | idealization only | NOT load-bearing (P-9) |
| Posit quarantine | informative accounting | audits can't fail → can't inform | load-bearing (P-10) |
| Binary operator | Tier 1 completeness | nothing (k-ary = accelerator) | constitutive / tier-graded (P-11) |
| k-ary lenses | Tier 2 certifiability | Prop 6.4 blindness unbreakable | load-bearing, Tier 2 (P-11) |
| Split-half | (P1) deflation | deposit record | load-bearing (P-12) |
| Null matching | (P2) calibration | 36 false pairs | load-bearing (P-13) |
| Pre-registration | semantic validity of bounds | forking paths | load-bearing (P-14) |
| Level tower | inter-dataset rules | conflicting-filling rules unmintable | load-bearing for cross-rules (P-15) |

---

## 10. Inter-dataset structure — the level tower

**Definition 10.1 (Dataset, witness span).** A *dataset* is an evidence family 𝒜ᵢ with its own carrier. For structure σ realizable over a collection of datasets, the *witness span* of σ is the minimal number of datasets jointly required to witness it. Span 1 is intra-dataset; span k ≥ 2 is inter-dataset, *irreducibly* so when every proper sub-collection is traceless — Proposition 6.4 restated one holon up, with datasets as the components.

**Proposition 10.2 (Cross-content: merging suffices).** For structure that exists in raw coordinates, the merged family ⋃ᵢ 𝒜ᵢ generates ℛ(⋃𝒜ᵢ), and the span-k content is exactly ℛ(⋃𝒜ᵢ) \ ⋃ᵢ ℛ(𝒜ᵢ) — elements every one of whose provenance chains draws parents from k distinct families. All Tier 1 theorems apply verbatim to the merged family; dataset boundaries are administrative, not algebraic. ∎

**Proposition 10.3 (Cross-rules: merging provably fails).** There exist rules of the form ⟨shared structure S, dataset-indexed filling θᵢ⟩ that are (a) present in no single dataset (each holds only its instance S(θᵢ)), and (b) destroyed by merging whenever the fillings conflict — the merged shared bin on the relation is empty. *Proof by minimal counterexample:* D₁ realizes y = 2x, D₂ realizes y = 5x. No common relation survives the merged pool (the instances contradict), yet each dataset's ledger certifies its own proportionality. The invariant "y ∝ x, slope free" is therefore witnessable only by colliding the *ledgers*. ∎ — This is the structure-set/filler-set law in load-bearing form: what no single dataset contains is the knowledge that the filling is a free parameter of a shared form.

**Definition 10.4 (Level-2 comparands; the tower).** A fixed-point (or partial) ledger is a set of typed entries and is therefore a valid comparand. *Level 2* runs the identical loop with per-dataset ledgers as observed comparands; the shared bin of a ledger collision is the invariant structure, the residues are the dataset-specific fillings. Nothing else changes: provenance composes (a level-2 certificate unwinds through level-1 certificates), the audit, posit, and quarantine rules lift verbatim, and levels iterate — a level-2 ledger is again a comparand. Each dataset is one *observation* of the meta-structure; the machinery re-enters with n = number of datasets. An instance is not a concept, but a concept becomes an instance by exactly this type coercion.

**Proposition 10.5 (Span blindness).** An irreducibly span-k rule is invisible to every analysis over fewer than k datasets, by definition — including every intra-dataset census and every pairwise dataset comparison for k ≥ 3 (curvature across datasets needs three points as surely as a triple-parity needs three columns). Detection requires joint books of span ≥ k or a level-2 accounting deficit pointing at the family. ∎

**Worked instance (10.6): social structure from personal sheets.** Individual-level records do not explain geopolitics, and the formalism says precisely why, in three stacked mechanisms. (i) *Span:* macro-structures (blocs, markets, institutions) have witness span in the millions — invisible to any individual or small sample by Proposition 10.5, for the same reason triple-parity is pairwise-blind. (ii) *Aggregate lenses:* rates, flows, and balances are lenses over the merged population pool; no sheet under any lens shows a trade deficit, though every sheet prices its fragment of one (Prop 3.5: the atoms are detectable in the whole they constitute). The foundry's duty here is forging population-arity instruments. (iii) *Minted vocabulary:* "nation," "market," "institution" are derived objects — recurring shared bins across vast sheet families — so geopolitical rules are level-2 structure over concepts-become-instances; the individual does not explain geopolitics because geopolitics is not written in the individual's type. — The claim "the individual doesn't explain X" then has two formally distinct readings, and the audit arbitrates: *emergent-but-present* (in the sheets, certifiable after merge + aggregate lenses + tower) versus *genuinely unwitnessed* (the closed-room treaty leaves no trace in personal sheets — a deficit whose posit names a missing dataset class, not a missing lens). If lenses and tower still leave the books unbalanced, the quarry is different evidence, and the posit should say so. — *Prior-art anchor for the level-2 null:* comparative social science has carried this exact P2 failure under the name **Galton's problem** since 1889 — societies treated as independent samples when they share descent and diffusion, so naive-null cross-cultural correlations over-certify. Societies are the memory-bearing columns of social data; the doctrine "the null matches the medium" rederives the known disease and supplies the repair schema.

**Proposition 10.8 (Block ascent; largest holons as next-level comparands).** Understanding a whole proceeds by selecting, at each level, the *largest stable holons* — certified recurring entries, diverse-parented, maximal (not properly contained in another certified recurring entry within scope) — and treating them as the observed comparands of the next level. *Guarantee:* block choice affects efficiency, never truth. By confluence and the composition of provenance through levels, every admissible chunking reaches representations of the same underlying content; the atoms remain beneath every block, recoverable on demand, and the canonical structure is invariant to the ascent route. Chunking is therefore a *view*; content is invariant — the "workable, not minimal" claim at the level-ascent layer. Largest-block selection is the right default (maximal compression dividend per 6b.6, minimal provenance depth above) while optimal selection is grammar-hard and never claimed. *Corollary (safe improvement):* upgrading a system's chunking policy invalidates nothing already learned — selection is swappable at zero migration cost, and recurrence at the level above re-grades block choices continuously (blocks that stop earning their place are bypassed, never deleted).

**Context and the constraint grid (10.7).** A level-L object is not intelligible by itself, and not through its members: members underdetermine the whole (many populations are consistent with one macro-structure), and the whole underdetermines the members. What renders it intelligible is its *constraint context* — for a society: geography, climate, resources, cultures, access and information. Formally: the constraint context is an evidence family over the *possibility space* of the object (where settlement can occur, what can grow, who can reach whom), and Definition 1.7 applies verbatim with constraints as generators. The "understandable grid" is the cell decomposition of that family: **focal points** are high-signature cells (many constraints coincide — confluence, flat land, defensibility, corridor: the common-but-real class in geographic clothing); **barriers** are cell boundaries (where signatures flip); **networks and corridors** are the adjacency structure the residue geometry permits. *Explanation is location:* to explain a holon is to place it in the atoms of its constraint field. This adds no operator — it is the differentiator with a different carrier, which is the recursion claim in load-bearing form. — The full explanation then has exactly two components, per the standing law: the constraints define the shape (the cell decomposition) and the needs select the filling (which agents and cultures occupy the slots). Neither alone explains; misattribution between them — crediting the filling with what the shape forced, or the reverse — is a named failure class for level-2 social analysis. — Consequently the tower is a *lattice*, not a ladder: explanation flows sideways through heterogeneous cross-class collisions (society ⊗ terrain, society ⊗ resource-map, society ⊗ information-network), licensed because comparands need no common type, only a shared plane — here spatial coordinates, which is why geocoding is the alignment-lens duty of this instance and must pass split-half like any translator.

**Admissibility at level 2 (Tier 2).** Two components acquire sharpened duties. (i) *The alignment lens:* datasets arrive in different schemas/coordinates; the translator between them is itself a lens, is forgeable by the foundry, and must pass split-half *across datasets* — estimated on some datasets, validated on others — or alignment error deposits as fake invariance. (ii) *The level-2 null:* unrelated datasets share enormous generic structure (noise floors, near-Gaussian marginals, power laws), so a naive null certifies banalities — "both contain variance" — as discoveries. The null ensemble at level 2 must be *generic unrelated datasets*, so that only structure exceeding what strangers share can certify. Same doctrine, the null matches the medium; at level 2 the medium is datasets-in-general, and that ensemble must be built before any level-2 number means anything.

**Scarcity, relocated honestly.** At level 1, n counts samples; at level 2, n counts datasets, and is usually small. A span-3 rule witnessed by four datasets sits at the 1/√n floor, and most meta-rules live near the unfalsifiable-posit boundary until the dataset count grows. The framework's response is unchanged — mint the quarantined posit, name the quarry, wait for witnesses — but the wall is relocated, not escaped, and the document says so.

---

## 11. What the proof does and does not claim

Claimed, unconditionally (Tier 1): the loop terminates; its answer is canonical and procedure-independent; every certified object is witnessed; every atom is detectable — as a single or as part of a larger whole — at every ledger state, with isolation contingent only on budget (Prop 3.5, the theory's actual commitment); at the closure limit the atoms are exactly the evidence's indistinguishability classes (Thm 3.4, the idealization); evidence growth is monotone refinement; irreducible k-ary structure is pairwise-blind and demands arity-matched instruments or deficit aiming (Prop 6.4); cross-content inter-dataset structure reduces to pool merging (Prop 10.2) while cross-rule structure demands the level tower, at which the identical machinery re-enters with ledgers as comparands (Props 10.3–10.5); audits close at closure; posits are forced, exact, unique, and safely quarantined; the triad closes reflexively with no fourth bin.

Claimed, conditionally (Tier 2): under admissibility (P1)–(P5), false certification is bounded by declared, shrinkable terms; both recorded violations are property violations with property-restoring repairs; the exact theory is the zero-error limit; and in the sampling limit the census is strongly consistent — every fixed real component is eventually certified and false certifications are almost surely finite (Prop 7.8), with completeness pointwise (and in mass, for square-summable spectra) but never uniform over accumulating spectra.

Not claimed: anything about data below the indicator floor or the 1/√n floor (posits there are unfalsifiable and are not minted); anything against adversarially encrypted data (the acknowledged complement); that any particular real dataset's extraction is complete (Theorem 4.2 says the opposite is the permanent working condition — which is why the posit ledger, the list of named quarries, is the honest form of the fidelity report).

---

*End of formal treatment. The next enforcement step is unchanged from the handoff: the admissibility suite as executable property tests — (P1) deflation, (P2) null-matching, (P3) confluence, (P4) budgeted reconstruction — since every theorem above tells the tests exactly what to assert.*

---

## 12. The disproof program

The theory has been assumed correct and prosecuted twice; this section makes prosecution the standing method. Three attack surfaces, pre-registered outcomes, and declared kill conditions.

**Surface 1 — the mathematics.** (1a) *Executable properties:* every Tier 1 theorem as a property test over randomized families and fair strategies — confluence, soundness, atoms = cells, audit closure at fixed point, posit exactness/uniqueness, quarantine integrity — run continuously as a counterexample search. (1b) *Degenerate instantiation:* empty family, singleton, exact duplicates, nested chains, n = 1, A = V, fully disjoint families; every theorem must survive its edges. (1c) *Machine formalization:* Lean/Coq for §§1–5 — the adversary that accepts nothing; the exact tier is small enough to feed it whole.

**Surface 2 — the statistics.** (2a) *Null battery:* each dependence class (iid, AR, long-range, heteroskedastic, regime-switching) × {naive null, matched null}, pre-registered prediction per cell: naive fails by class, matched holds; a matched-null failure is a K2 event or a new wall. (2b) *Deflation attack:* worst-case peel targets where split-half independence is violated by construction (halves sharing drift); predicted breakage and predicted repair (block splits — the null-matching doctrine applied to the split itself). (2c) *Forking-paths simulation:* a post-hoc tuning agent versus a pre-registered pipeline on identical data — P5's load measured, not asserted. (2d) *Escalating adversarial games:* planted structure plus decoy traps, adversary strengthening toward indicator-free construction; predicted degradation profile: performance falls exactly as the indicator weakens and not before. The boundary's location is thereby measured; a wall where the map says it is, is evidence, and a wall found early is a discovery.

**Surface 3 — the placement map.** Run all fifteen ablations of §9 and demand the breakage match each prediction exactly. Less breakage than predicted: the necessity claim was overreach — demote the component. More: the dependency map is incomplete — extend it. Different: something unmapped is load-bearing — find it. This surface aims disproof at the document itself.

**Kill conditions (declared in advance; any one suffices).**
K1 — a reproducible confluence violation with every component passing the admissibility suite.
K2 — false certification under an admissible configuration exceeding the Prop 7.5 bound at statistical significance.
K3 — a planted, indicator-bearing structure that no foundry-grown lens certifies under unbounded budget (the indicator-suffices invariant fails).
K4 — an audit deficit discharging to anything other than its exact posited leftover (5.1(b) uniqueness fails).
K5 — any failure the framework cannot attribute to a named inadmissible component: vocabulary exhaustion. Both recorded failures were in-framework diagnosable; a break the triad cannot name is the true falsifier.

**Outcome epistemics (pre-committed).** Every attack terminates in one of three states, and each attack pre-registers which it predicts: *survives* (logged evidence); *breaks with in-framework diagnosis and repair* (the record's existing pattern — this strengthens the theory, being science performed on itself); *breaks without diagnosis* (kill condition — the boundary map gains a wall or the theory loses a tier, and that response is committed to now, not negotiated later). Pre-registration of expected outcomes is what separates disproof attempts from demonstrations wearing disproof costumes.

**Priority (lethality per unit cost).** Property tests first — cheapest, deadliest, and they guard everything after. Then the null battery (the K2 hunt), the ablation-prediction runs (Surface 3), the adversarial games (2d), and machine formalization as the capstone. The program is complete when every theorem has faced its strongest available adversary and the kill-condition log is either empty or the document has been amended to say what died.

**Execution record — second prosecution (2026-08-06, external adversarial review).** A full adversarial read of this document found: (1) a genuine formal defect — Definition 1.6's claim that the ∩/\-closure is a ring closed under union is FALSE (counterexample: generators {1,2}, {1,3}; the closure never contains {2,3} or the union). Repair: ring language removed; every justification that invoked union-closure replaced by successive differences (\ alone suffices); and the diagnosis yielded a new one-line theorem, the **splitting invariant** — every ledger entry is a subset of some generator, the loop splits and never glues, so the exact tier is deflationary by construction: admissibility property P1's Tier 1 ancestor, hidden under the false claim. (2) A descriptive mismatch between the audit definition (atomics only) and Prop 3.5's proof language (three-way decomposition); reworded to the correct two-case argument, claim unaffected. The review confirmed all core theorems, the repaired Lemma 2.3, the placement map post-corrections, both suite prosecutions, and the tier separation as standing. Kill-condition log: still empty — justifications were repaired; no theorem fell. *Methodological note:* the property suite could not have caught defect (1): it tests conclusions (union-of-cells held throughout, and is true) while the defect lived in a written justification. The defect class that only a reader or a proof assistant catches is now demonstrated in this document's own history — which raises Lean from capstone to scheduled.

**Execution record — first run (2026-08-06, tier1_property_suite.py).** Surface 1a and Surface 3 spot checks executed. Results: 550 randomized Boolean families × 3 independent shuffled strategies each, plus 6 degenerate families — ALL core theorems held (T3.1 termination, T3.2 confluence, L2.1 soundness, L2.2b closure, L2.3 atoms = cells both directions, D1.3 conservation per collision, T4.1 audit closure, T5.1 forced-exact posits under random partial extraction; largest ledger 301 entries, largest atom set 9). Kill-condition log: empty. Two prosecutions succeeded against the DOCUMENT, not the theory: (1) P-2's necessity claim disproven — ∩ is \-derivable (X ∩ Y = X \ (X \ Y)); component demoted to accelerator; (2) 6b.2's unit-atom conjecture disproven by the disjoint-support counterexample; replaced by the indistinguishability-class principle, with the correct characterization now a named open problem. Count-valuation confluence: 200/200. Both corrections strengthen the theory's central claims (Myhill–Nerode structure; Surface 3 functioning as designed) while shrinking the document's overclaims — which is the disproof program returning exactly the kind of result it exists to return.
