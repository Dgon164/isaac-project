# THEORY vs ENGINE — the reconciliation audit
**2026-08-23. Owner: "I've lost control of Isaac. I don't know what is
still implemented or designed... what I know vs what it is doing are
different and that's a problem."**

This document is the map that closes that gap. Column 1 is YOUR theory
(the differentiation algebra: how information is found, stored, used).
Column 2 is what the code in THIS repo (`code/isaac.py`, v0.1.2-alpha1)
actually does today. Every row gets one of four verdicts:
**AS-DESIGNED** / **DIVERGENT** (does something different, named) /
**DESIGNED-ONLY** (paper, no code) / **MISSING**.

Scope note — there are three engines; this audit covers the canonical
one (this repo). The June original (`Documents/isaac_project`) is the
closure-theory era, archived. dc's engine is the product engine anna
runs on (law discovery + audit faces; separately maintained). Part of
regaining control is ruling that ONE of these is Isaac and the others
are archive/product — recommendation at the end.

---

## A. How information is FOUND

| your theory | what the engine does | verdict |
|---|---|---|
| Differentiation: D(A,B) = shared / only-A / only-B is THE finding operation | `compare()` exists and is exactly D — but it is NOT the main path. The main finder is **co-occurrence counting**: observe sequences → count (context-window → next-token) pairs → normalized weight matrix. Frequency statistics, not differentiation. `compare()` is load-bearing only in the type-forming step and diagnostics | **DIVERGENT — the central divergence.** The primary brain is a statistical instrument your theory would type as Tier 2, but it has never been typed, gated, or audited as one |
| The collider loop: collide all pairs, mint every nonempty bin, run to closure | Nothing runs collisions to closure. The type-former (`consolidate`) does ONE grouping pass over shared-edge profiles, connected-components style, first-acceptable-match kept (deliberately order-dependent for speed) | **MISSING** (approximated by a mechanism with three named divergences: no closure, no order-independence, groups cannot overlap) |
| Certification against matched nulls | `discover()` (the numeric law module) does this properly: null-gated term admission, held-out validation, verdicts, rival forms kept live with deciding experiments | **AS-DESIGNED — but only for numeric laws.** Language/graph content has no null anywhere |
| k-ary lenses (pairwise-blind structure needs arity-matched instruments) | No lens machinery in the engine. Hand-coded lenses exist in the anna product wrapper only | **DESIGNED-ONLY** (lens loop charter, 07-30) |
| Deficit-aiming (spend search where the books point) | No books, so no aiming. Search is budget-capped scans | **MISSING** |

## B. How information is STORED

| your theory | what the engine does | verdict |
|---|---|---|
| Typed ledger: every entry observed / derived / posited, with provenance chains | The graph has nodes, tagged edges, counts, metadata — but **no origin typing and no provenance chains**. You cannot ask "why does this edge exist" and get a lineage. EXCEPTION: the findings ledger (laws) DOES carry provenance, verdicts, rivals — one subsystem got it right | **DIVERGENT** (laws: AS-DESIGNED; everything else: untyped) |
| Add-only; supersession, never deletion | Mostly honored: observed sequences are append-only, superseded types stay on the record, wrongs kept. Named exception: `remove_door()` deletes edges during type-index cleanup | **MOSTLY AS-DESIGNED** (one named deletion path) |
| Atoms = what the evidence cannot split; overlap is native | Types are connected components of shared-edge clusters — coarser than your atoms, and **cannot overlap** (measured limit, on the known-bug list). Your cells fix this in principle | **DIVERGENT** |
| Posits: a failed audit mints exactly the deficit, quarantined until discharged | Nothing mints posits. When he can't account for something, the information evaporates (a low-confidence return value, no record). The failure-node design (07-31) and repair grammar (08-02) describe this — never built | **DESIGNED-ONLY** |
| Conservation: operations reveal, never create; checked per operation | Nothing checks conservation anywhere in the engine | **MISSING** |

## C. How information is USED

| your theory | what the engine does | verdict |
|---|---|---|
| Accounting audit: every whole balances against parts; imbalance is a real named thing | Not in the engine. (anna's reconciliation feature does sum-audits — on CLIENT data, product side. The engine never audits ITSELF) | **MISSING in engine** |
| Answers carry certificates (witness lineage) | Matrix answers carry a confidence number only. NEW exceptions: the expression reducer returns worked derivations; `discover()` returns full receipts | **PARTIAL** (new reducer + laws yes; general answering no) |
| Level tower: ledgers become comparands; structure vs filling separated | The idea mechanism (repeated wholes become single units, recursively, order kept, exact unzip) is a real cousin of block ascent. Cross-dataset law families exist harness-side only. No ledger-collides-ledger anywhere | **PARTIAL** |
| The known / resolvable / inferred scheduler | The job queue is mechanical FIFO with a priority lane. No epistemic triage exists | **MISSING** |
| Grain declared before atoms on continuous quantity | `discover()` has noise floors; anna passes client tolerance through. The engine's general path has no grain concept | **PARTIAL** |

## D. The inverse list — engine mechanisms with NO place in your theory
*(This is the drift itself: things that grew for good reasons and were
never placed. Your own §9 placement-proof method — load / ablation /
verdict — is the right tool; these need placement verdicts from you.)*

1. **The prediction matrix** (the main brain). Proposed placement:
   a Tier-2 instrument — powerful, fast, and honest ONLY if typed as
   statistical and audited (its confidence is a frequency, not a
   certificate). It earned CLOTH 85%; it stays — but under the theory,
   not instead of it.
2. **First-acceptable-match type assignment** (speed doctrine).
   Explicitly order-dependent — your confluence theorem makes
   order-dependence the signature of an inadmissible operator. Either
   it gets a measured drift bound (shuffle tests) or it's scheduled
   for replacement by the collider.
3. **Entry budgets, hub ejection, segment sizes** — speed heuristics,
   fine as budget policy, never typed as such.
4. **The expression reducer** (new, 08-20) — closest new code to your
   theory: exact-fact gate, interim ledger, refusal with named failing
   step. Proposed placement: keep; it is the miniature of the working
   space.
5. **Motherese delivery, idea-mint thresholds** — teaching-protocol
   machinery; harmless; needs re-measurement post compile-fix anyway.

---

## The bottom line, in three sentences

Your theory IS implemented somewhere: `discover()` implements Tier 2
honestly for numeric laws, the findings ledger has real provenance, and
the 08-06 collider code implemented Tier 1 exactly — but that code is
not on this machine. The engine's main path — the thing that answered
1,108 exam questions — is a frequency matrix that grew during the
speed era and was never placed under the theory. Nothing here is
mysterious or unfixable: every divergence is named above, and the
collider working space (already specced by your own formal document)
is the single build that puts the exact tier in charge with the matrix
as its typed instrument.

## The control rules going forward (proposed)

1. **This document is THE MAP.** Maintained same-commit as the manual:
   any mechanism added, changed, or removed updates its row.
2. **No unplaced mechanisms.** Every component carries a placement
   verdict: implements theory element X / typed instrument with named
   duties / scheduled for removal. (Your §9 discipline, aimed at the
   engine permanently.)
3. **One engine ruling (owner decision needed):** this repo = Isaac;
   June = archive; dc = anna's product engine. Or say otherwise.
4. **The gap-closing build** = W0 collider working space + its
   property suite (confluence shuffles, conservation checks, deflation
   tests) as the permanent regression gate — already proposed, now
   also the control-restoration move.

## What I need from you

(a) Read columns and veto/confirm the placement proposals in D.
(b) The one-engine ruling (3 above).
(c) The collider code from the 08-06 session if it exists anywhere —
    otherwise W0 builds fresh from your formal document.
