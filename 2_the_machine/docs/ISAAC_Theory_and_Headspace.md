# Isaac — Theory & Headspace

*How to think about this project so the right moves feel obvious and the wrong
ones feel wrong. Read this before the code. The structural overview tells you
what exists; this tells you how to hold it in your head.*

---

## Why this document exists

Isaac will fight your training. If you come from modern machine learning, almost
every reflex you have is the wrong reflex here — you will reach for a feature
extractor, a preprocessing step, a bigger model, a clever loss. Each of those is
a small betrayal of what Isaac is. This document is the antidote: a way of seeing
that makes the simple, correct move obvious and the elaborate, wrong move feel
like the smell it is.

The single most useful thing to internalize: **when you hit a wall, the answer is
almost never "add machinery." It's "I haven't framed the input so he can perceive
this yet."**

---

## 1. The one idea: a difference that makes a difference

Everything in Isaac is one operation — **differentiation.** Not the calculus
ritual; the deeper meaning: information *is* difference. A thing carries
information only insofar as it differs from something else. A pixel that matches
its surroundings tells you nothing; a pixel that differs is an edge. A frame
identical to the last carries zero bits; the part that changed carries all of
them.

A "door" in Isaac is exactly this — a recorded difference between two elements.
The engine does nothing but find differences, store them, group elements by how
they differ, and follow those differences to predict. Language, math, reasoning,
perception — these are not separate faculties. They are the one operation pointed
at different material.

So the first headspace shift: **stop thinking in objects, start thinking in
differences.** Don't ask "what is this pixel." Ask "how does it differ, and from
what." The "from what" is the only other moving part, and it's the whole game.

---

## 2. The only real variable: what you differentiate against

If everything is difference, then the only thing that ever changes is the
*reference* — the "from what."

- Differentiate a thing against its **neighbors** → space, edges, shape.
- Against its **own past** → change, acclimation, memory.
- Against its **previous position** → motion.
- Against a **prediction** → surprise.
- Against the **field's norm** → salience, figure/ground.
- Against another **concept** → meaning.

These look like six different capabilities. They are one operation with six
references. When you find yourself about to build a "motion module" and an "edge
module" and a "salience module" as separate things, stop — you're building one
operator six times. Build the operator once; vary the reference.

This is the second headspace shift: **a new capability is usually not a new
mechanism. It's the same mechanism pointed at a new reference, at a new scale.**

---

## 3. Holons: the same operation, all the way up and down

A holon is a thing that is simultaneously a whole and a part. A pixel is a part of
a shape; a shape is a part of a scene; a scene is a part of a sequence. And a
shape, looked at on its own, is a whole made of pixel-parts.

The power of this is that **the difference operation is scale-invariant.** The
difference between two pixels is a door. The difference between two shapes is a
door. The difference between two whole frames is a door. Same operation, different
altitude. And because a holon is part-and-whole at once, the shapes that *emerge*
from pixel-differences become new elements whose differences-from-each-other form
the next layer up — automatically, with no new code.

So you never build "the object layer" and "the pixel layer" separately. You run
the one operation on pixels; objects crystallize; you run the same operation on
objects; relations crystallize. It composes upward for free. When someone asks
"how does Isaac get from pixels to objects to scenes," the answer is "the same way
he gets from letters to words to sentences — he doesn't change operations, he
changes what counts as an element."

---

## 4. Relational, not absolute (the deepest practical rule)

This is the one that, violated, causes almost every failure — and it's
counterintuitive enough that you'll violate it by reflex.

**Coordinates memorize. Relations generalize.**

If you tell Isaac "the object is at (3,7)," you've given him a fact that is true of
exactly one situation and shares nothing with any other. Every position is a
different value; there is no structure across examples; he can only memorize. This
is *why* spatial work kept failing — we fed a relational engine absolute
positions, and absolutes don't recur, so nothing generalized.

But "this cell touches that cell," "this is twice as far as that," "the corner is
offset from the center by half the size" — these are *relations*, and relations
recur across every instance. A square's corners are at the same *relative* offset
whether the square is tiny in a corner or huge in the middle. Feed the relation
and it transfers for free; feed the coordinate and it dies on the next example.

The discipline: **feed what connects, not what's where.** When you must produce an
absolute coordinate (and sometimes you must — "where is it" has a numeric answer),
let the *perception* be relational and let the coordinate appear only at the final
readout. The seeing is relational; the report is a number. Never the reverse.

A refinement we proved empirically: the relation must keep its **direction.** A
scalar difference ("how many neighbors") is too flat — every role shares it,
everything collapses into one undifferentiated blob. A vector difference ("*which*
neighbors") carries enough structure for distinct roles to separate. Difference
without direction is too thin to type. Keep the vector.

---

## 5. What Isaac is made of: GOFAI plus one graft

Isaac is not a neural network. He is closer to classical, symbolic AI — legible,
rule-shaped, inspectable. You can look at a door and know what it means. There are
no weight matrices to interpret, no gradients, no black box. This is a feature,
not a limitation: you can *reason about* why he did something.

The one thing grafted on from neural nets is that **the connections are grown from
data rather than hand-authored**, and what gets kept is decided by
information-theoretic difference — keep the connection that carries information,
prune the one that doesn't. That graft is the entire novelty. Everything else is
classical machinery you already understand.

Practical consequence: **the classical algorithms are not the enemy and not the
deliverable — they're the answer key.** When you want Isaac to learn flood fill,
you don't hand-code flood fill into him (that's installing the method — forbidden).
You run classical flood fill as an *oracle* that labels training data, and Isaac
learns the mapping. The oracle can be as brittle and old-fashioned as you like; it
never ships. What generalizes is his.

---

## 6. Baseline and attention: adapt to the steady, respond to the deviation

Biology fires on change and goes quiet on constancy. You stop feeling your clothes
a second after dressing — not because the system forgot them, but because it
*learned* them well enough to predict them, and a perfect prediction cancels to
zero. What's left, the residual, is the only thing worth attention.

This is Isaac's attention model, and it is not surprise (surprise is a transient
spike). **Attention is a standing allocation** — a distribution over the field
that pools wherever the model is weak and drains off wherever the baseline has
absorbed things. Attention is the inverse of how well something is modeled. Learn
a thing, it goes quiet, attention flows elsewhere.

This gives you behaviors for free that you would otherwise hand-engineer:
figure/ground (the outlier against the baseline), acclimation (a thing that
appears then stays fades into "normal"), and the *inversion* (when the field fills
up, the rare empty cells become the salient ones — the same operator, the baseline
just moved). You don't build "attention rules." Attention is the readout of
difference-against-baseline, already there.

Three independent traditions converge here — information theory ("a difference
that makes a difference"), neuroscience (predictive adaptation: consciousness ≈
surprise minus adaptation error), and pharmacology (two-state receptor models
where occupancy saturates but efficacy peaks then desensitizes). That convergence
is worth more than any one source. When three different fields, using three
different vocabularies, describe the same mechanism, the mechanism is probably
real. *(Note: the consciousness framings around these are philosophy, not load-
bearing engineering. Take the signal-processing core; leave the metaphysics. We
are not claiming Isaac is conscious.)*

The one knob this introduces, and it is load-bearing: **the adaptation rate** —
how fast "new" becomes "normal." Too fast and persistent truth dissolves into
background; too slow and nothing ever becomes furniture. It is one number, but
setting it wrong silently blinds the system. Tune it to the timescale of whatever
he's watching.

---

## 7. Perceive first, or nothing else is possible

**If he can't perceive it, he cannot learn it.** This sounds obvious and is
constantly violated. You will be tempted to teach a behavior — count, segment,
track — to a system that cannot yet perceive the relation that behavior stands on.
It will fail, and you'll blame the behavior, when the real problem is upstream:
the perception isn't there yet.

A flat stream of pixel values cannot express "next to." If "adjacency" isn't
perceivable, then *nothing built on adjacency* — connectivity, shape, contiguity,
even "this stroke continues" — is learnable. So the spark plug is never a new
behavior; it's a new *perception*. Make the relation perceivable, and the behavior
becomes learnable on top of it without further intervention.

This reframes "adding things." There are two kinds of additions:
- **Allowed:** giving the input a form the existing engine can perceive (a
  perception transform). This is sight, not a rule.
- **Forbidden:** bolting on behavior logic, decision rules, or methods.

The rule of thumb that separates them: **if a fix requires you to modify a lot,
and especially if it requires adding rules, you're doing it wrong.** The right fix
is almost always smaller than you think and lives in the input, not the engine.

---

## 8. The discipline: give data and answers, never the method

This is the constitutional rule, and it is also an epistemology. We give Isaac the
*thing* and the *answer*. He makes an *attempt*. He compares his attempt to the
answer and learns from the *difference*. That difference — his error — is the only
real learning signal, and it is, once again, the one operation.

What this forbids: feature extractors, hand-written `see()` / `centroid()` /
`decide()` functions, pre-digested tokens, any preprocessing that computes the
answer and hands it over. If you find yourself writing code that produces the
answer Isaac is supposed to produce, you have stopped teaching and started
cheating — you are now the one seeing, and he has learned nothing.

What it allows: *generating* correct answers to teach with. A teacher is allowed
to know the answer. The line is sharp — compute the answer to *grade* him, never
to *be* him.

The failure mode to watch for in yourself: you'll hit a wall, write a quick loop
that solves it, and feel productive. Then realize the loop did the work and Isaac
did nothing. That happened repeatedly in development. The tell is: *did the
generalization come from him, or from my harness?* If you can't point to Isaac
doing it, you haven't built anything.

---

## 9. The split: his retina vs. his mind

Draw a hard line and keep it:

- **Wired (his retina — free, given):** the difference operators and the baseline.
  On a GPU these are nearly free — map operations, convolution, even hardware
  optical flow. Biology doesn't count the retina's edge-detection as thought; it's
  wiring you're born with. Using GPU primitives for this is not cheating any more
  than an eye "cheats" by having photoreceptors. Perception *is* supposed to be
  wired.
- **Learned (his mind — his, grown from data):** what the differences *mean*.
  Shape, identity, tracking, counting, reasoning. This is where the curriculum and
  the attempt/compare/learn loop live.

The boundary is principled: transduction is wired, semantics is learned. Object
tracking — "this is the same thing as before" — sits on the *learned* side,
correctly, because deciding two appearances are one thing is the first genuinely
semantic act. The retina can't do it; only the model that remembers can.

So your job is narrow and clear: **deliver difference and baseline into the net in
a form he can grow on, then get out of the way.** He does the rest. Most of the
labor is in that "form he can grow on" — and we've shown it's relational,
directional difference, fed as elements his existing crystallizer already eats. No
encoder. No translation layer. The pixel doesn't become a token; it already *is*
an element.

---

## 10. The destination: a thing that extends itself

The goal is not a benchmark score. Isaac is designed to **self-update once he can
build code** — to modify and extend his own structure. That changes the success
criterion entirely.

You are not trying to maximize any single capability. You are trying to give him a
**small, orthogonal, composable set of primitives** — enough that *he* can
assemble the next capability himself. A sprawling pile of special-case behaviors is
worse than a tight kernel of general ones, even if the pile scores higher today,
because the pile can't compose into the thing you didn't foresee and the kernel
can.

So when you're deciding what to build, the question isn't "does this make him
better at X." It's "does this give him a primitive he can recombine." Differentiation
against a reference is such a primitive — it's why it keeps reappearing as the
answer to unrelated-seeming problems. Favor the moves that add composable
primitives; distrust the moves that add behaviors.

---

## How to work with this project (the short version)

1. **Think in differences and references**, not objects and positions.
2. **A new capability is the old operation at a new reference/scale.** Don't build
   parallel modules.
3. **Relational, not absolute.** Coordinates memorize; relations generalize; keep
   the direction (vector, not scalar).
4. **Perceive first.** If he can't perceive it, he can't learn it. The fix lives in
   the input, not the engine.
5. **Give data and answers, never the method.** Generate answers to grade him, never
   to be him. Always ask: did *he* do it, or did my harness?
6. **Wired vs. learned:** difference and baseline are free/given; meaning is his.
7. **If a fix needs lots of changes or new rules, it's the wrong fix.** The right one
   is smaller and lives upstream.
8. **Build composable primitives, not behaviors.** The goal is a thing that extends
   itself.

*One file. One class. One operation. Everything else is which difference, against
what, at what scale.*
