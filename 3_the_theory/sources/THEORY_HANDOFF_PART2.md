# The Differentiation Theory — Handoff, Part II

*Continuation of THEORY_HANDOFF.md. Everything built and learned since Part I,
with the real numbers recorded so this is an actual checkpoint. Same rule as
before: plain explanation, honest about what's confirmed and what's still open,
named anchors attached. Read Part I first — this assumes it.*

---

## 0. The one-line update

Part I laid out the theory. Part II is where it started **running as code that
checks out** — and where one correction reorganized everything: the core
operation is *difference*, not *similarity*, and the whole stack was quietly
computing the wrong one. Also: ISAAC's engine was compiled directly into a
weight matrix and verified bit-exact, which makes "grow a net from meanings"
no longer a thesis but a demonstrated fact.

---

## 1. The correction that reorganized everything: difference, not similarity

The single most important thing in Part II. Every readout, every match, every
"which concept is this" was being computed as **overlap** — how much is *shared*.
That is exactly backwards. Shared features are the *low*-information part: an
attribute present in every candidate carries zero discriminative content. Yet a
similarity score weights it *heaviest*, because it's the biggest pile of matching
bits. The identity of a thing is not in what it shares — it's in the **residual**,
the difference left after the shared context is removed.

Stated as the law it is: **same is *some* meaning (it places you in the
category), different is *all* the meaning (it tells you which one).** And the
operation is **recursive persistent differentiation**: differentiate to fix the
superset, then *throw the superset away as settled context* and differentiate
again on what varies *within* it, and recurse. At each level the shared part
isn't down-weighted — it's **removed**, because it's no longer a difference, it's
the frame. You don't re-count "feline" when you're inside feline asking
tiger-or-lion.

This kills the problem that ate most of Part II's early experiments — the
"bulk outvotes the discriminator" wall — at the root, because in a difference
operation the bulk is never in the sum at all. There's no vote for it to win.

**Measured:** a recursive-differentiation readout against a similarity readout,
same encoder, leave-one-out exact-ID on the animal task: **similarity 0.113 →
recursive-diff 0.295** (2.6×, chance 0.062), with the should-resolve cases that
similarity left at zero finally resolving (tiger 0→0.47, eagle 0.14→0.98, bear
0.50→0.99). The principle is confirmed. The remaining failures (zebra, lion stay
0; horse regressed) are **implementation brittleness** — I used a hard greedy
single-attribute split with no backtracking, so one misread derails it. The fix
is a robust descent that respects the known superset→subset order (OOP structure
as the tree shape) and keeps more than one branch alive. Principle: solid.
Greedy implementation: brittle. Those are different things.

Anchors: this is Fisher/LDA's "discrimination lives in the few separating
directions" and decision-tree information-gain, rederived from the primitive.
The repeated failure mode — me reaching for similarity — is worth flagging for
the next reader: it's the default pull, and it's wrong every time.

---

## 2. Persistence collapses the two primitives into one

Part I named differentiation as the floor. Part II hit the question of where
*significance* and *use* come from, and the answer turned out to fold back into
differentiation through one observation: **a differentiation that doesn't persist
is inert.** A single same/different event builds nothing — abstraction requires
*two* distinctions to compare, so the first has to still exist when the second
arrives. The entire constructive program (mint a dim, take a residual against
what you already have, build concepts on concepts) is *differentiation against
stored prior differentiation*. The dictionary **is** persisted differentiations.

So persistence is not a second primitive beside differentiation — it's the
condition that makes differentiation *compose*. Memory is what turns the
complete-but-inert operation into a builder. And the third state
(not-significant) was always presupposing it: "not significant" means "not
different *from what I already hold* in a way that matters." Significance is the
comparison of the new difference against the persisted ones.

**The convergence with Boris Kriger (Feb 2026, "Unified Structural Theory of
Complex Systems").** Independently rederived ~a month after he published.
His central claim: *persistence* — a system's capacity to maintain structural
viability over time — is the primary organizing principle, substrate-independent,
with cyclical closure ("cognitive prediction loops are cycles") as a consequence.
His bootstrap from nothing literally *starts* from distinguishability
("distinguishable properties → variation → gradients → flows → structure") — i.e.
from differentiation, with persistence built on top. So: differentiation is the
substrate (more fundamental); persistence is the *selector* (what survives), and
persistence is a candidate answer to the frontier Part I left open — *which cut
first / what matters*. The lineage to actually raid: autopoiesis (Maturana &
Varela), dissipative structures (Prigogine), autocatalytic sets (Kauffman), and
the free energy principle / active inference (Friston: persist by minimizing
surprise — prediction-error-as-significance, formalized).

**The sublinear / negentropic necessity** (a real theorem worth stating). The
cost of storing-and-operating a structure must be *less* than what the structure
buys, or persisting it is a net loss and it's selected out. Storage and
permutation-complexity grow one way; value grows another; persistence is only
stable where value grows *faster* than cost — i.e., **cost must be sublinear in
the structure it supports.** So any persisting intelligence or life is, *by
definition*, negentropic / sublinear, or it isn't persisting. And the
autocatalytic dictionary *achieves* sublinearity by construction: each new
concept is stored as its *residual* against existing overlaps, so cost-per-concept
*falls* as the dictionary fills. Overlap is how you stay negentropic. The
representation exists in the form it does because that's the only form cheap
enough to survive. (Strong, falsifiable edge: domains whose structure is
*irreducibly* incompressible admit no persistent intelligence at all.)

---

## 3. Significance and use, resolved (mostly)

Three moves closed most of the "use" gap from Part I:

**Significance is overlap pointed at the present.** Relevance isn't a value you
*assign* — it's the projection of the current context onto your known dims. Heart
surgery isn't *less important* in the middle of the ocean; its dimensions just
don't intersect what the situation activates. It's *orthogonal*, not demoted —
full magnitude, wrong direction. Significance is the overlap operator aimed at
self-versus-situation. No value module needed, the same way ISAAC needs no
honesty module.

**Reality constrains a sparse subspace; the rest is free.** The hard axes
(physics, causality) pin a *few* dimensions absolutely and ignore everything
orthogonal. "Never prescribe" is forced, not chosen: prescription loses on the
hard axes (reality overrules) and is gratuitous on the soft ones (you've fenced
off free space for nothing). You observe which dims are load-bearing; the
enormous remainder reality leaves alone is where exploration happens.

**Desire is the loss, and that's not mysterious.** A desired end-state is just a
Venn circle — a constraint that invalidates outputs landing outside it. Control =
prediction toward that circle. The target is the loss; subgoals that serve it are
*planning*, which is the net's job to learn (a forward model good enough to
chain state→action→state→goal), not the designer's job to prescribe. Not rogue,
not exotic — means-end reasoning. The one irreducible addition over pure
prediction is "where does the circle come from," and the answer is: the loss
gives the outer circle; self-maintenance gives self-drawn circles only if you
want goals the system sets for itself.

---

## 4. Development is the build-order of the stack (Piaget, generalized)

The "which cut first" frontier has an empirical answer hiding in developmental
psychology. Piaget's four stages, read through the machinery, are the *order the
dictionary has to come online in*, because each layer is built from the one
below:

- **Sensorimotor** = minting the first dims from raw covariation (object
  permanence = minting a *persistence* dim that isn't in the input).
- **Preoperational** = the dictionary fills but operations aren't online —
  bundling without binding (conservation failure = collapsing a 2-D quantity to
  one axis; over-regularization = a rule minted but not yet bound against
  exceptions).
- **Concrete operational** = binding + reversible set-algebra over *present*
  structure (conservation solved, class-inclusion navigable).
- **Formal operational** = operating on constructed dims themselves —
  generation and prediction over the *absent and abstract*.

And the deeper claim, yours: these four are **substrate-independent** — the same
transition runs over language (structure → rules → semantics → specifics) and over
*any* new domain (chess, law, music) from scratch. Adults are at different rungs
in different domains simultaneously. So "which distinction first" is answered the
same way everywhere: structure before rules before meaning before nuance, because
each is built from the last. The stages are the salience ordering, and the
salience ordering is the dependency graph of the dictionary. (Honest seam:
Piaget's rigid global stages are wrong in detail — Spelke/core-knowledge,
neo-Piagetians — but that *refines* the reading: domains mint on their own ragged
schedules, which your frame predicts better than uniform stages did.)

---

## 5. ISAAC compiled to weights and dims — the headline result

The big concrete advance. ISAAC's actual engine was reviewed, run, and
**compiled directly into a neural net**, verified bit-exact against his symbolic
engine. This is the inverse of Part I's decompilation: instead of reading
meanings *out* of a trained net, we wrote ISAAC's learned meanings *into* a net,
with no training.

His learner, run on the sealed corpus, grounds exactly two doors from
co-variation with no English seed:
`('picks','up') → MENTIONED_OBJ_VANISHED` at **38.6 effective orders of
surprise**, and `('sets','down') → MENTIONED_OBJ_APPEARED` at 17.9. That's the
whole grounded lexicon, and it's already a weight table.

The mapping (one-to-one):

| ISAAC engine | Net |
|---|---|
| frame (sentence minus names — the residual) | input dimension, reserved |
| delta (world-change) | output dimension, reserved |
| door (frame → delta) | weight `W[delta, frame]` |
| effective surprise | weight **magnitude** |
| excite / inhibit / abstain | weight **sign** (+ / − / 0) |
| no door fires | zero output → **"unknown"** for free |
| `find_mention` (string identity) | encoder's **differentiation** step |
| `frame_of` (residue) | encoder's **subtraction** — *different is all the meaning* |
| surprise gate (`annotate`) | the **learning rule** that sets the weights |
| belief supersession (last wins) | recurrent **state** (the *persistent*) |

**Verified:** the compiled 2×2 signed weight matrix, run as one matmul
`y = W @ x` with belief supersession, reproduces ISAAC's symbolic answers
**39/39** on the sealed test stream, including 27 honest "unknowns" where no door
fired. The net *is* the engine.

Three things this nails:
- **Grow-not-convert, made literal.** The weights were *set* by the surprise
  gate (recorded co-occurrence evidence), not *found* by gradient descent. The
  net is compiled from meanings.
- **Reserved-dim, signed code** — the clean basis the whole conversation kept
  arriving at, now populated by a real learned engine.
- **The dense/clean relationship is a basis rotation.** `W_dense = R·W_clean·Rᵀ`
  takes this legible matrix and tangles it into the gradient-friendly smear a
  trained net lands in. Your clean net and a conventional trained net are *the
  same program in two bases* — the smear is one optional rotation away, and it's
  gratuitous.

(The encoder — tokenize, compare, subtract bindings — stays a *program*, not a
matmul. It's the "real program" Part I's overview flagged: perception is genuine
sequential computation. The compiled object is encoder-program → reserved-dim
vector → signed matrix → recurrent belief slot.)

---

## 6. The self-growing net — the shrug is the growth signal

How the compiled backbone *grows*. The loop, corrected through several rounds:

**An abstain (a shrug) is the growth signal.** Zero output means no existing dim
explains this — which is the residual, which is exactly where a new dim belongs.
ISAAC's honesty *is* his growth signal: he points at where he's blind, and that's
the only place capacity is ever added.

**Mint on *every* shrug, immediately, no admission gate.** This was a real
correction. You can't gate on recurrence ("has this happened before") because the
thing you'd check against doesn't exist until you've stored it — *the dim is the
memory*. Comparison requires both terms to be in the net, so every shrug must mint
or the next identical observation shrugs again with nothing to recognize it by.
Minting everything is the only policy that can't miss the rare-but-real thing, and
the cost of being wrong is just an unused name. **Asymmetric in the right
direction.** The surprise gate isn't a bouncer — it *annotates* (records support),
and the validation is downstream: real patterns grip (consistent gradient), noise
slips (no consistent gradient to hold a dim).

**Gradient descent opens only on the new dim; the backbone is frozen.** This
cures, *by construction*, the three walls Part II kept hitting: no catastrophic
forgetting / no "averaging affects everything" (the gradient can't smear into
frozen weights), no gradient starvation (the new dim gets *all* the gradient,
nothing to dilute it), no readout bulk-domination (the new concept has its own
reserved channel). **Sparse by construction**: a connection exists only because a
shrug forced it.

**Epistemic humility as the policy.** A novel observation could be a one-off, a
rare-but-real pattern to be discovered later, or a sensor glitch — and you *can't*
tell which at intake, because only the future distinguishes them. So you don't
sort: name it, store it, hold it as *pending*. It either recurs (and becomes a
discovered rare pattern, now with something to match against) or it doesn't (and
costs only a name). And the confusion *thins as the map fills* — a richer
dictionary leaves less ambiguous middle ground for a new thing to be mistaken
into. The system earns its discrimination by accumulating structure.

**Measured:** backbone of 2 frozen concepts; stream with known + novel-real +
noise. 7 dims minted (1 per shrug); real patterns C/D/E minted *once* and then
fired (one-shot grip), hitting **1.00** on fresh test instances; **backbone
bit-identical** afterward (zero interference — the forgetting problem gone by
construction); sparse (grew only where shrugged). Two honest gaps: noise dims
*didn't* self-wither — they persist and misfire (70%) unless the recorded
surprise is **applied at decision time** as a confidence floor (your "record
don't gate, apply stakes at decision time" — I recorded but didn't apply); and
the mis-mint self-heal test was *malformed* (shuffle minted a clean dim; the
"confound" only ever co-occurred with one outcome, so GD correctly kept it), so
that claim is **untested**, not shown.

---

## 7. The sealed experiment stack (the real numbers)

All multi-seed or sealed where it mattered; pre-registered predictions where
noted; honest hit/miss. The recurring caveat: most of these ran on *clean*
synthetic structure (easy mode) — they show the mechanisms work when structure is
present and clean, not yet how they bend under graded, messy, natural input.

**Selectivity threshold** (condense the code onto concept-specific lines). A
*normalized, frozen* threshold (fire only above 0.5 std) condensed the code:
active fraction 59% → 31%, **selectivity 0.28 → 0.60**, accuracy preserved, ~no
dead units. The *naive* trainable −0.5 bias did almost nothing (arbitrary scale,
optimized away). Pushed to 80/20 (top-20% / kWTA): **sparsity ≠ selectivity** —
fixed-threshold gives concept-specific lines *with* dead-unit waste; kWTA gives
clean sparsity *without* selectivity (units stay polysemantic). Sweet spot is the
gentle band.

**tanh excite/inhibit/abstain** (the signed three-state as activation). Threshold
tanh at 0.8. Dense baseline: selectivity 0.08 (total smear). pos (excite-only):
0.530 acc / 0.634 sel. inhib (inhibit-only): 0.539 / 0.637 — **inhibition carries
the same information as excitation**; "sure it's absent" is as discriminative as
"sure it's present." ternary (both): best accuracy of the three (0.560), 28%
active, **0 dead units** (each unit can fire either side, so none is stranded —
the signed three-state doesn't waste capacity). On *clean* signal: every
condition hits **100%** accuracy, and the thresholded versions get it with
selectivity 0.83 and the ternary with 0.73 — same function, clean legible code,
zero accuracy cost. Cleaning the signal made the *similarity* readout worse
(sharper bulk), which is what proved exact-ID is a *readout* problem, not signal.

**PREDICT + ID** (sealed, pre-registered). next-token 0.325 vs unigram baseline
0.120 (HIT). next-**category** (using ID'd classes) **1.000** vs token 0.325 —
**ID enables PREDICT**, the solution stack made visible (HIT). ID recovered the
token classes perfectly from distributional overlap, unsupervised (HIT). Surprise
= reliance: low-surprise predictions ran at 0.00 accuracy, high at 0.33, and
abstentions were 100% the noise tokens — calibrated, but *underpowered* (the clean
grammar left no uncertain middle to triage).

**Feedback dims** (interaction constraints, higher-order). Lift token doors to
class-interaction rules via ID. The class-interaction matrix recovered the grammar
exactly (valid transitions 361 orders of surprise, impossible ones exactly 0),
unsupervised. The payoff — **generalization to unseen-valid**: a combination
*forbidden in training* ("a fish", count 0) was accepted as valid **100%** by the
feedback dims via the class rule, where token doors accepted it **0%**. Impossible
interactions rejected 100%. Headline validity: feedback 1.000 vs token-only
0.928, the gap being exactly the held-out generalization. Feedback dims = the
composition-validity / "what can interact with what" structure, and they buy
compositional generalization neither token doors nor similarity can.

**Negative examples** (the inhibit half, "don't do this"). Standard nets hate
negatives (the negative gradient smears into siblings; softmax says "unlikely"
not "forbidden"). This architecture doesn't. A negative is an *inhibitory reserved
dim*. Results: a specific prohibition ("a fish" forbidden) carved an **exception**
that overrode the general DET→NOUN rule for that case only, leaving siblings ("a
cat", "the fish") valid; the interaction matrix gained a **third state** —
valid(+) / forbidden(−) / pending(0), so "told wrong" is now distinct from "never
seen"; and the positive matrix was **bit-identical** after the negatives went in
— *zero interference*, the structural property dense nets can't have, because the
prohibition lives in a reserved channel that can't reach the positive weights.
Honest note: the exception *override* was coded (specific beats general by fiat),
not an emergent weight competition — the emergent version is untested.

---

## 8. Updated frontier — confirmed vs still open

**Confirmed in Part II:**
- The operation is difference, not similarity (2.6× on exact-ID; the principle is
  right, the greedy implementation is brittle).
- Differentiation-that-persists is one primitive, and the autocatalytic dictionary
  is sublinear by construction (the survivable regime).
- ISAAC's engine compiles to a reserved-dim signed weight matrix, bit-exact.
- Growth via shrug→mint→frozen-backbone→local-GD is interference-free and sparse
  by construction (backbone bit-identical; one-shot grip).
- ID enables PREDICT; feedback dims generalize to unseen-valid and reject
  impossible; negatives integrate as inhibitory dims with zero interference and a
  real three-state epistemics.

**Still open:**
- **The robust readout.** Recursive differentiation is right but the greedy
  hard-split implementation is brittle. Needs superset→subset-ordered descent with
  backtracking (OOP structure as tree shape).
- **The graded middle.** Everything ran on clean synthetic structure. The
  surprise gate's reliance, ID's class recovery, feedback dims' valid/forbidden
  call — all untested where predictability is *graded* and classes *overlap*,
  which is where the hard discrimination actually lives.
- **Stakes at decision time.** The growth loop needs the recorded surprise applied
  as a confidence floor so noise dims stay silent (records, not voters). Specified,
  not yet wired.
- **Emergent override.** Make a negative an actual inhibitory *weight* that must
  out-pull the excitatory rule numerically, rather than a coded specificity rule.
  This is also the bridge to the next piece.
- **The decision-translation nodes (the "second part").** The output/decision
  intermediary nodes that turn implicit competition into an explicit decision —
  flagged but not yet built.
- **The use-loop, fully closed.** Multi-step prediction chained toward a goal
  Venn; the forward model deep enough to plan. ISAAC's active phases.
- **Self-heal, properly tested.** A real confound, the inspected dim actually
  mis-born, and watch GD pull it toward the features it needs.

---

## 9. Method, reinforced

The discipline that made Part II trustworthy, and the failures that proved it
working: sealed/pre-registered runs (predictions written before results);
multi-seed before any fine-grained claim (single-seed fireworks were repeatedly
just variance); honest hit/miss including *underpowered* hits and *malformed*
tests called as such; catching my own bugs (the IDF readout that backfired
because the feature wasn't learned; the no-op D(x) readout; the mis-mint test that
couldn't see what it claimed to test; the inherited noise level that poisoned the
selectivity runs until you caught it). And the standing caveat to carry forward:
**clean synthetic worlds are easy mode** — the mechanisms are confirmed where
structure is present and clean; the graded, overlapping, noisy regime is where
they'll be properly tested, and that testing is still ahead.

*Two files are the working proof, both runnable: `compile_isaac.py` (engine →
weights, verified 39/39) and `grow.py` (shrug → mint → frozen-backbone growth).
The sealed experiments — `selectivity.py`, `tanh80_clean.py`, `recdiff.py`,
`sealed_predict_id.py`, `feedback_dims.py`, `negatives.py` — are each a single
checkable claim.*

*Recorded knowledge has infinite half-life. The save point holds.*
