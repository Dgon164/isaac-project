# The walk — handoff, 2026-09-12

Read `docs/ARCHITECTURE.md` first (the owner's spec). This file is
what got built against it today, what the numbers actually say, and
where the next session should start.

## The mode (read this before building anything)

Owner, this session, verbatim:

    "we are not doing this again. screw the providence. screw the
     science lets just build shit and see what happens. im tired of
     perfection getting in the way of good enough. build a working
     prototype then refine."

    "as stupid simple as possible. if it feels wrong, its probably
     right so long as it works."

    "you are adding provenance again."   (said when a comparison
     printed WHY an answer changed instead of just WHAT changed)

No courts. No gate rows. No ledger entries. No mutation-verification.
Build the thing, run it on real data, show the transcript, fix what
breaks by running it. A plain commit is fine; ceremony is not.

## What exists

All in `walk/`, branch `record-repair`, pushed through 06ca481.

    engine/core.py    the store, the item record, the walk, the cycle
    engine/linker.py  prose -> items with references
    mind.py           THE THING. ~350 lines. load, ask, learn, correct
    bed.py            SQuAD curriculum bench, -jobs N
    course.py         five-arm curriculum experiment
    overlap.py        do articles reinforce or interfere
    library.json      built dictionary (11MB, gitignored, auto-builds)
    store.json        his persistent store (gitignored)

Run it:

    python walk/mind.py walk/engine/messy.txt walk/materials.csv walk/conditions.csv
    python walk/bed.py 999999 -jobs 12
    python walk/course.py 2000
    python walk/overlap.py 10 -jobs 12

Data already on disk (nothing to download — owner is bandwidth limited,
this is a HARD RULE):

    SQuAD v2    C:\Users\jtwee\Downloads\New folder (3)\intellon\train-v2.0.json
    WordNet     C:\Users\jtwee\Downloads\New folder (3)\intellon\wordnet_full.json
    enwiki      C:\Users\jtwee\Downloads\New folder\enwiki-*.xml.bz2  (26 GB)

## How mind.py works, in full

1. **Fill.** A sentence becomes an item pointing at every term it
   names; every term points back. A CSV row becomes an item; the table
   name and every column header become spine items pointing at all
   rows. Same header in two tables = one spine = cross-table compare.
2. **Ask.** Bag = the question's words + their thesaurus pull. Walk
   from every bag word the store knows, depth one per step, nothing
   pulled twice. Anything reached sharing nothing with the bag is a
   tangent, not an answer. Score = shared words, own words before
   dictionary words. Top three.
3. **Gate.** Conditions carry `value, against, context`. Numbers
   compare (`2900 > melting_point_k 533`), lists attack (`hcl attacks
   cu`). The answer carries the comparison, never a verdict word.
4. **Field.** One run per context-holon, never mixed: all of apcp's
   boundaries together, all of sugar's together. Survivors ranked by
   cost then density.
5. **Loop.** Never serve a stored answer — always rerun. A repeat
   question gets one extra section: agrees, or the diff (then-not-now
   / now-not-then). A changed answer mints a lesson item.
6. **Correct.** `no: <truth>` marks the last top answer wrong (kept,
   not deleted) and stores your line tagged human.
7. **Redo.** Re-asks every stored run against today's store and
   rewrites changed answers in place. His past corrects itself.

## The numbers (all on this machine, today)

**Full SQuAD, 86,821 questions, each article alone:**

    59.9% top1   73.2% top3   22 seconds at -jobs 12   (3859 q/s)

No model, no training, one bag of words. 12 workers = 6.7x over serial,
answers bit-identical at every width (asks are pure reads).

**Per-article spread (440 articles):** min 9.6, q1 50.6, median 61.1,
q3 71.1, max 94.4. Random half-vs-half over 20 draws differs 0.0–3.2
points (mean 1.1). So: the aggregate is stable ±1.5, the per-article
number is not, and *which articles you sample dominates any subset
score.* The first-5000 sample read 52.5 for exactly this reason.

**Articles sharing one store (pool of 10):** 57.7% top1 — worse.

    foreign article STOLE the top spot, wrong:  7017  (8.1%)
    foreign article gave the RIGHT answer:        42  (0.05%)

Interference beats reinforcement **170:1** on this corpus. SQuAD's 440
articles are deliberately eclectic, so neighbors share vocabulary but
not facts. A full-merge (all 440 in one store) run was launched and is
the open measurement.

**The curriculum experiment (course.py, 2000 questions):**

    PRE    (before the material)   0.0%    <- clean zero. no bluffing.
    TEST   (standard)             51.5%
    POST   (after the loop)       51.5%    <- IDENTICAL. see below.
    FINAL  (answers given)        96.0%

Shuffling question order changed nothing (FINAL 96.0 -> 95.5).

## The one thing that is known broken

**Run residue is inert for retrieval.** POST equals TEST to the
question. Runs go into the store and add links, but they carry no
*words*, and answers are scored by word overlap — so the bridges a run
builds are invisible to ranking. Lessons and given keys DO carry words
(that is why FINAL jumps to 96, and why `redo` works).

So "he learns as he processes" is **not true yet**. Making every run
leave residue the next answer can stand on is the gate on every
learning-curve claim. Fix this first or every "accuracy rises with
hours run" result will be zero.

## The four directions the owner named for next session

His words: *"perhaps we should explore a complex domain mastery. or
even slightly related domain mastery? we also need to figure out how
to teach meta rules and information training, and transitive and
translatable concepts for generality, as well as work on the
vocabulary to make it easier for it to use."*

**1. Domain mastery (complex, or slightly-related).** The overlap
numbers make this the sharpest experiment available: on an eclectic
corpus neighbors interfere 170:1. The prediction worth testing is that
in a *coherent* domain (all rocketry, all chemistry, all one Wikipedia
category) pooled articles should REINFORCE — accuracy going up with
store size instead of down. If that flips, domain mastery is real and
measurable; if it does not, the walk needs something beyond word
overlap before depth helps. overlap.py already counts both directions;
it needs a domain-coherent corpus, and the 26 GB enwiki dump can
supply one by category with a streaming reader.

**2. Meta rules + information training.** Level 2 exists in the big
engine (`code/isaac.py`: structure_hunt, meta_hunt, induce_op_shaped)
and mines rules from its own record. Nothing of that is wired to the
walk. The natural bridge: runs and lessons are already items in the
store, so the miner has a record to read — but see "known broken"
above, the residue has to carry words first.

**3. Transitive / translatable concepts.** The thesaurus is currently
ONE hop, capped at 50 neighbors. Transitivity = walking the dictionary
more than one hop (fame -> popular -> well-known), which is the same
walk already written, just run over the library instead of the store.
Cheap to try, and the bench grades it in 22 seconds.

**4. Vocabulary.** The dominant miss is the paraphrase gap: question
says "grow up," the sentence says "born and raised." The library
widened today (definitions + examples + antonyms, 134,894 words) for
+28 answers — small. Bigger levers untried: WordNet hypernyms (is-a
chains), the 26 GB corpus as its own co-occurrence thesaurus, and
letting the question's *kind* word (when/where/who) select what kind
of answer counts.

## Standing rules that bit this session

- **Never download anything.** Owner is bandwidth limited. Everything
  needed is already on disk.
- **Always `cd /c/Users/jtwee/Documents/isaac-project` first.** The
  default cwd is a Downloads folder holding a June-era copy of the
  engine; commands run from there silently import the wrong Isaac.
- **Never launch ui/isaac_workspace.py on this machine** (atexit-saves
  the mind path at import).
- Plain 1980s/90s engineering words. Bug, root cause, lookup table.
- Report results in chat, in detail, not only to a file.
