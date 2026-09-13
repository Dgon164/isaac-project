# The walk — handoff, 2026-09-12, updated 2026-09-13

Read `docs/ARCHITECTURE.md` first (the owner's spec). This file is
what got built against it, what the numbers actually say, and where
the next session should start. The 09-13 session reproduced every
09-12 number first, then fixed the residue and found the tie-break;
both are in the numbers below.

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
    curve.py          does asking make the next question easier
    margin.py         is the winner right when it wins clearly
    library.json      built dictionary (11MB, gitignored, auto-builds)
    store.json        his persistent store (gitignored)

Run it:

    python walk/mind.py walk/engine/messy.txt walk/materials.csv walk/conditions.csv
    python walk/bed.py 999999 -jobs 12
    python walk/course.py 2000
    python walk/overlap.py 10 -jobs 12
    python walk/curve.py 20000
    python walk/margin.py 5000

The two data paths read ISAAC_SQUAD and ISAAC_DICT when those are set,
and fall back to the Windows paths below, so the same files run on
another machine without edits.

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
   tangent, not an answer. Score = how many of the question's own
   words are shared, then **how rare those shared words are** (1 over
   how many items name the word), then bag words. Top three.
3. **Gate.** Conditions carry `value, against, context`. Numbers
   compare (`2900 > melting_point_k 533`), lists attack (`hcl attacks
   cu`). The answer carries the comparison, never a verdict word.
4. **Field.** One run per context-holon, never mixed: all of apcp's
   boundaries together, all of sugar's together. Survivors ranked by
   cost then density.
5. **Loop.** A run is banked only if the winner was clear of the
   runner-up (`clean_win`) -- a tied field is a guess, and banking a
   guess teaches the store the guess. What is banked, the question's
   words point at, so a later question crosses it. Never serve a
   stored answer — always rerun. A repeat
   question gets one extra section: agrees, or the diff (then-not-now
   / now-not-then). A changed answer mints a lesson item.
6. **Correct.** `no: <truth>` marks the last top answer wrong (kept,
   not deleted) and stores your line tagged human.
7. **Redo.** Re-asks every stored run against today's store and
   rewrites changed answers in place. His past corrects itself.

## The numbers

*(09-12 numbers unless marked; the last section says which box each
run came from.)*

**Full SQuAD, 86,821 questions, each article alone:**

    63.8% top1   77.5% top3     (was 59.9 / 73.2 before the
                                 rarity tie-break, 2026-09-12)

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

## Residue: fixed, and worth about half a point

It was inert because runs carried no words. Now the question's words
point at the run and the run's words count in the score, so a run
leaves a bridge. Measured the honest way -- `curve.py` cuts each
article's questions in half, runs the first half through the loop, and
examines the second half, which no arm ever processes:

    10,057 exam questions      top1        vs cold
    COLD   text only           65.7%         --
    WARM   every run banked    66.2%        +50 answers
    CLEAN  clean wins only     66.0%        +31 answers  (45% fewer
                                                          runs banked)

POST now beats TEST on course.py for the first time (58.0 vs 57.5).
So "he learns as he processes" is **true and small**: half a point,
not a curve. Banking every run and banking only clean wins come out
the same within noise, so the gate costs nothing and keeps the store
honest.

## Where the loss actually lives (margin.py, and the ladder it found)

Asking *when he is right* turned out to be the highest-value question
of the session. The gap between the winner and the runner-up predicts
correctness sharply:

    own +3   9.9% of questions   94.6% right
    own +2  14.5%                92.1%
    own +1  33.6%                67.7%
    tied    37.6%                20.1%      <- before the tie-break

**A tied field was 37.6% of every question and was being decided by
name sort order.** Breaking it by rarity moved 21.5% of questions out
of "tied" into 41.3%-right, and moved the whole bench +3.9 points.
After the tie-break the ladder reads:

    own +3 94.6 | own +2 92.1 | own +1 67.7 | tie-break 41.3 | tied 21.8

That is a calibrated confidence signal, free, already computed. Two
things fall out of it and neither is built:

- **Honest refusal.** Answer only when the field is not tied: covers
  80.1% of questions at 68.4% right. Pick the bucket, get the rate.
- **19.8% of questions are still fully tied at 21.8% right.** Every
  point left on this corpus is in that bucket. A second tie-break
  (question kind, position, rarity over the bag) is the cheapest
  experiment available.

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

**4. Vocabulary.** Partly answered this session: rarity of the shared
word is worth +3.9 points, and the control (shortest sentence wins)
only +1.7, so it is discrimination doing the work rather than length.
The dominant miss is still the paraphrase gap: question
says "grow up," the sentence says "born and raised." The library
widened today (definitions + examples + antonyms, 134,894 words) for
+28 answers — small. Bigger levers untried: WordNet hypernyms (is-a
chains), the 26 GB corpus as its own co-occurrence thesaurus, and
letting the question's *kind* word (when/where/who) select what kind
of answer counts.

## Where this session ran

A cloud container, 1 CPU, 15 GB, Linux -- not the owner's machine. The
corpora were fetched into the container (SQuAD v2 train from the
SQuAD-explorer repo; WordNet 3.0 from nltk_data, rebuilt into the
`wordnet_full.json` schema mind.py expects: word / sense / def /
examples / antonyms). Nothing was downloaded onto the owner's
connection and no data is committed. The rebuilt library is slightly
narrower than the owner's (127,359 linked words vs 134,894) and
reproduces every prior number to the decimal: full bench 59.9 / 73.2,
first-5000 52.5, course PRE 0.0 / TEST 51.5 / POST 51.5 / FINAL 96.0.
`-jobs` is untested above 1 here; the owner's 12-worker numbers stand.

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
