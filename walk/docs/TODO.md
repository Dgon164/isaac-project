# Todo — from step one to a full system

Ordered by what depends on what. Sizes are honest: "small" means a
day's build on top of core.py, "large" means an unsolved problem.

## 1. The bench — small, first

A set of questions with known answers, run after every change. The
rocket question is the first entry. Each entry records: goal term,
context, expected survivors, expected rejections with reasons.

Why first: nothing else on this list can be judged working without it.
Library filling in particular will produce plausible garbage and only a
bench catches it.

## 2. Feedback into the library — small

A run's results become items. Every rejection with its reason, every
survivor with its rank, the whole trace — stored with the context and
tag "run". A miss between prediction and reality opens an axis on the
item that was wrong, rather than being discarded.

Depends on: core.py (done), the bench (to confirm it doesn't corrupt).

## 3. The linker — large, the real work

Turns source material into items with references. This is "filling."
The engine walks references; if the references aren't there, the walk
stops. Every quality problem downstream is a linking problem here.

Three sources, in order of difficulty:
  - tables: a row becomes an item, columns become content, one column
    (element, material, category) becomes the reference. Proven today
    by hand; automating it is small.
  - equations and relations: "X depends on A, B, C" becomes an item
    pointing at A, B, C. Medium. The handbook today was written by hand.
  - prose: a sentence becomes an item pointing at the things it names.
    Large. This is where language lives, and it is the same job as
    filling — not a separate system.

## 4. Verification and challenges — medium

Distinct from the bench. The bench asks "does it still give the known
answer." Verification asks "is the known answer right." Two tools:
  - cross-check against Ergo via the emitter. Disagreement is a bug
    with a trace on both sides.
  - challenge questions: ones where the expected answer is "I can't
    tell" or "the list is open." A system that returns a confident
    winner on those is wrong even if the winner is right.

## 5. Human interface — small to start

Question in, transcript out, correction back in. A terminal is enough
for a long time. The transcript from core.py already prints every pull,
gate, and verdict, so the interface is mostly a way to type a correction
and have it land as an item with tag "human."

Later: the step function you asked for — one pull per keypress, state
visible between.

## 6. Language — large, deferred

Not built separately. It is (3) applied to prose, plus (5) accepting
prose instead of a goal term. Building it as its own thing is how it
gets disconnected from the store.

## Not on the list

Processing — that's core.py, step one, done.
Ergo — kept as a check under (4), not a component.

## What's proven and what isn't

Proven today: the walk, the gates, the ranking, the trace, indifference
to library size, one rule reproducing a mode list. All on tables.

Not proven: any of it on prose. The linker for tables is mechanical;
the linker for sentences is the open question, and everything under
"language" rests on it.
