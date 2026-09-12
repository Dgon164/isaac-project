# Isaac — the architecture, plainly

## The claim

General intelligence is not a special mechanism. It is what you get when
a store of linked information is walked by a simple loop that asks,
returns, rejects, and keeps what survives — and when the results of each
walk go back into the store. Nothing in the loop is clever. The
intelligence is in the links, and the links are built up over time from
the walks themselves.

You do not need to be brilliant or trained. You need to follow the
latent information — the connections that are already in the material —
until you arrive.

## What exists

Three things, and only three:

    the store        every item Isaac holds, each pointing at others
    the tables       reference material read in whole, on the spot
    the question     what is being asked right now

Nothing else is available to the loop. It cannot see the whole store.
It sees what the current item points at, one layer out, and that is
all. This is a constraint on purpose: it is what keeps the walk bounded
and the reasoning checkable.

## The record

Every item carries:

    name        a variable. only recognisability matters.
    kind        what sort of thing it is. read off the data.
    content     a value, a row, a sentence, a relation.
    truth       +1 true, -1 false, 0 present-but-not-for-this, null unassessed
    native      a flag: this never leaves Isaac
    tag         where it came from
    refs        what it points at — the one layer

Truth is what Isaac holds about the item. It is never modified by anything
else in the record.

Relevance is separate from the record. It is a signed, graded number
looked up by item and context. The same item is required in one question
and refused in another. Relevance sorts and gates; it never changes
truth. Negative relevance is a refusal, and it is a claim about the
reasoner, not the world — it comes from outside the evidence and is not
revised by learning.

## The walk

Pull the current item. Pull everything it points at. Read all of it —
reading is free. Use what bears on the question. Leave the rest on the
desk, set aside, in case a later question needs it. Anything pulled that
has not been pulled before goes on the open list.

Take the next open item. Repeat.

That is the whole walk. It is depth one per step, and it settles on its
own because the store is finite and nothing is pulled twice. On the
rocket tables it settled at 23 pulls. On a forum post it settled at 92.
Adding 50 unrelated items to the store changed nothing, because nothing
on the path pointed at them.

There is no cutoff, no cap, no frequency filter, no pruning of the walk
itself. Every one of those was tried and every one made it worse.

## The cycle

    ask       form a question from one open item. the question type is
              read off the item's kind, not chosen by hand.
    return    the answer arrives. new items appear.
    reject    any candidate that fails a gate is dropped and asks
              nothing further. this is the only pruning, and it comes
              from the data, not from the walk.
    persist   what survives every gate is a valid answer.
    rank      survivors are ordered by secondary goals — cost, mass,
              workability, whatever the question cares about.

Persistence returns a set, not a winner. Where the gate is physical —
a surface reaching a melting point — Isaac finds it. Where the gate is a
preference — toxicity, supply — someone states the threshold, and the
record marks it as given.

## Meaning is connection

An item that touches many things has a lot of meaning and a lot of
reach. Copper in the forum post touched four sentences; it was the
subject. The system found that by counting references, with nothing
added. Common does not mean unimportant. Common means central.

On a small corpus this puts some filler words next to the subjects.
That is not a problem to fix. It separates on its own as the corpus
grows, because the subjects keep being connected to the topic and the
filler does not.

## Failure, in general

Everything breaks the same way: something concentrated overwhelms the
integrity of what it is made of.

    fail when   load at a point   >   capacity at that point

There is no list of failure modes. Melting is what it is called when
capacity reaches zero. Corrosion is what it is called when material is
removed and the load rises on what is left. The names come out of the
run; they do not go in. One comparison reproduced every answer that a
three-mode version gave.

Load and capacity are quantities with inputs, not constants. When
either can be controlled — a throat that opens, a wall that is cooled,
a system that responds to pressure — the question is about the control
loop, not a lookup. The same shape covers a nozzle, a government, and
a currency; only the variables change.

## Just in time

Nothing is built until something asks for it. Nothing is fetched until
the walk arrives at it. Nothing is optimised until it fails.

This is not laziness. It is the only way to keep the reasoning
attached to the question. Every pre-built shortcut is a guess about
what will matter, and every guess made today was wrong on contact:
the frequency cut removed the subject; the melting-only handbook said
carbon had no limit; the fixed geometry said capacity only goes down.
The walk, left alone, did not make those mistakes. The additions did.

Take the easy path. Make the code good and the design plain. Take
things to their extreme and see what happens. Most of the time it
works. When it does not, that is information, and it goes in the store.

## Filling and learning

The engine walks references. Putting the references there is Isaac's
job, and it is the whole job.

    tables     a row becomes an item. one column becomes the reference.
               mechanical.
    relations  "X depends on A, B, C" becomes an item pointing at A, B, C.
    prose      a sentence becomes an item pointing at every term it
               names. every term becomes an item pointing back at every
               sentence that names it.

No parser. No model. The forum post became 114 linked items with a
regular expression and a stop list. Whether it is good enough is not
decided in advance; it is decided by asking questions and seeing what
comes back.

Learning is feedback. Every run's result — the survivors, the
rejections with reasons, the whole trace — goes back into the store as
items with tag "run". When a prediction misses reality, the miss opens
an axis on the item that was wrong. The library does not have a
separate training step. It has runs, and runs leave residue.

Categories carry a mark: open or closed. A query that runs off the end
of an open list returns with a flag, not a clean answer. This is what
keeps "no limit" from meaning "none in my list."

## Emission and checking

Isaac keeps his own form. An outside engine gets an emitter, and the
emitter reports what it could not carry. Ergo carries everything;
plain Prolog loses priorities; RDF loses negation and every rule.
Native items and value 0 are never offered to any of them.

Ergo is not a component. It is a check: point both engines at the same
map, ask the same question, and a disagreement is a bug with a trace on
both sides.

## What is proven

On tables: the walk, the gates, the ranking, the trace, indifference to
store size, one rule replacing a mode list, two contexts on one store
with truth untouched.

On prose: the linker builds, the walk settles, connection count finds
the subject.

## What is not

Whether the prose links are good enough to answer a question that
crosses sources. Whether relevance composes along a chain. How a
category's open/closed mark is first set. What the human interface
looks like past a terminal.

None of those are built. They are built when something asks for them.
