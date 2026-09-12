# Isaac on Ergo — the build, re-evaluated

Everything below was run today, not argued. Where something failed, the
failure is recorded and the fix is what stands.

## 1. What holds

- Ergo runs local, free, inside Python. Session stays alive for the life
  of a worker. Insert and delete work mid-run. One engine per process.
- Explicit negation, rule priority, cycles, aggregates, variable slot
  names, and derivation traces all work. Nothing needed was missing.
- One store, two contexts, same facts, different answers, truth never
  touched. The astronaut case runs.
- The ask-return cycle runs with no question list written in advance.
- Rejection at each gate prunes the question space. 25 materials to 12
  in one pass; dead candidates ask nothing further.
- One rule — load against capacity at a point — reproduced every answer
  the three-mode version gave, with the mode names falling out as
  descriptions rather than inputs.

## 2. The item record

Every item Isaac holds carries:

    truth       +1 / -1 / 0 / null    what Isaac holds about it
    relevance   signed, graded        per context, sorts and gates
    native      one flag              never leaves Isaac
    tag         where it came from    for the derivation trace

Truth and relevance are never combined. Relevance orders a list and
cuts it. Truth is carried through as is.

Truth 0 means: present, recorded that it appeared, not for this work.
Native covers 0 and also records about Isaac's own run — pass count,
first-seen tick — which are true and still never leave.

Relevance is not a property of the item. It is looked up by item and
context. The same fact is required in one question and refused in
another. Negative relevance is a refusal, not a low weight; it is a
claim about the reasoner, not the world, and comes from a different
source than observations — it is given, not learned.

## 3. The cycle

    ask      form a question from one open term
    return   Ergo answers; new terms appear
    reject   any candidate that fails a gate is dropped and asks nothing more
    persist  what survives every gate is a valid answer
    rank     survivors ordered by secondary goals

The question type is read off the term's kind, and the kind is read
off the data (derived quantity, run condition, material property,
material). No question is scripted.

What was missing and is now in: rejection. Without it the cycle crawled
breadth-first through every material with equal priority. With it, a
melted candidate is gone and the list shrinks at each step.

Persistence returns a set, not a winner. Where the set is decided by
physics, Isaac can find the gate himself (a surface reaching a melting
point). Where the set is decided by preference — toxicity, supply,
cryogenics — someone states the threshold, and that threshold must be
marked as an input in the record, because nothing in the output
distinguishes the two.

## 4. The failure rule

    fail when   load(point, t) > capacity(point, t)

Everything else is a way of moving one of those two numbers:

    lowers capacity   heat softening, melting, embrittlement
    raises load       material removed (corrosion, erosion, ablation),
                      area reduced, pressure or speed increased

There is no mode list. "Melting" is what it is called when capacity
reaches zero. "Corrosion" is what it is called when the wall thins.
The names come out of the run; they do not go in.

Load and capacity are quantities with their own inputs, not constants
from a chart. The moment either is controllable — a throat that opens,
a wall that is cooled, a system that responds to load — the question
is about the control loop, not a lookup. Fixed geometry was an
assumption of the test, not a property of the world.

## 5. The library

Tables are built once and held. Material charts, reaction products,
boiling points, the handbook of which quantities appear together —
this is most of the volume and none of it changes.

Each category carries a mark: closed or open. "Failure mechanisms for
solid surfaces: 3 known, open." A query that runs past the end of an
open list returns with a flag, not a clean answer. This is what stops
"no limit" from meaning "none in my list."

The remaining errors — a mechanism nobody recorded, a nuance in how two
things interact — are found when a prediction misses reality. That is
the learning path and it is Isaac's, not the library's.

## 6. Emission

Isaac keeps his own form. Each target gets an emitter. Ergo's emitter
loses nothing; Prolog's loses priority; RDF's loses negation and every
rule. The emitter reports what it could not carry, and that count is
how a candidate engine is ranked.

Native items are checked first and never offered. Value 0 is never
offered. Everything else goes through the target's emitter and is
either rendered in that target's language or dropped with a note.

Two lessons from today, both silent failures:

    @{tag} and @!{tag} differ; the second makes a rule strict and lets
    a default and its exception both hold at once with no error.

    Loading a second file replaces the first unless written as
    ['a.ergo', +'b.ergo'].

## 7. Build order

1. Item record with the four fields. Emitter for Ergo only.
2. The cycle: ask, return, reject, persist, rank. One goal term in,
   ordered survivor set out. Transcript printed at every step.
3. The failure rule as load against capacity, with both as functions
   of inputs. No mode list anywhere.
4. Library with category marks. Open lists flag on overrun.
5. The return path: a miss between prediction and result opens an
   axis in the store rather than being discarded.
6. A second emitter, to prove the item record is target-independent.

Each step is testable on its own and each one was run in some form
today. Nothing here depends on a step that was not.

## 8. Not settled — for later, not now

- Whether relevance composes along a chain of reasoning, or is only
  ever applied at one step.
- How a category's open/closed mark gets set the first time, before any
  prediction has missed.
- Whether the `asked` marker — a contentless note that a question was
  settled — should leave Isaac, or whether re-filtering per tick is the
  smaller cost.
- The query scoring that was proposed and then replaced by rejection.
  Rejection may be enough. It may not be, on a problem with no hard
  gates at all.
