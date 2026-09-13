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
    misses.py         every question in one bin: right, close, lost tie,
                      fewer words, shares nothing, no path, not stored
    pairs.py          the general lesson in the graded runs: mine half
                      the articles, test as a thesaurus on the other half
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
6. **Correct.** `no: <truth>` grades the last question through
   `grade()`: a graded run is filed with his pick, the verdict, the
   right item, its rank, and which question words it had and lacked.
   The wrong pick is refused for that question (relevance -1; the
   scorer sets refused items aside). The right item earns the run and
   takes as its own only the specific words it lacked -- a word the
   store never held or naming one item. A truth the store never held
   becomes an answer sentence.
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
not facts.

**All 440 articles in ONE store (pool=all):** 47.9% top1, 58.8% top3.

    store size   top1    reinforce   interfere   time (86,821 q)
    1 article    59.9%      --          --         22 s
    10           57.7%     0.05%       8.1%       166 s
    440          47.9%     0.7%       33.3%      8628 s  (2.4 h)

All three rows were measured BEFORE the rarity tie-break, so the curve
is internally consistent but its top row is 59.9, not 63.8. Do not
compare 47.9 against a post-tie-break number; rerun the pool sweep if
the absolute values matter. (Rarity should help most exactly where
this hurts, so the curve may well flatten — untested, one command.)

Two things fall out of that table and both matter more than the score:

**(a) THE STORE-SIZE INDIFFERENCE PROPERTY DOES NOT SURVIVE PROSE.**
`docs/ARCHITECTURE.md` says adding 50 unrelated items changed nothing
"because nothing on the path pointed at them" — true, and `walk_court`
still proves it on the rocket tables, where the noise was genuinely
disconnected. Real prose is not disconnected: every article is wired to
every other through ordinary shared words, so the walk reaches
essentially the whole store on every question. Cost went 22 s -> 8628 s
(392x) for 440x the store — i.e. roughly LINEAR in store size per
question, not indifferent. Any plan that ends with "put all of
Wikipedia in one store and walk it" has to solve this first. The walk
needs something that keeps it local (a relevance gate that actually
cuts, holonic packaging so a context is walked as a unit, or refs that
distinguish "names the same word" from "is about the same thing").

**(b) Reinforcement is real, small, and GROWS with store size.**
0.05% -> 0.7% is 14x, and the interference:reinforcement ratio improves
170:1 -> 48:1 as the store grows. So cross-article help exists and is
not noise; it is simply swamped by vocabulary collisions on a corpus
built to have none. That is precisely the case domain mastery tests.

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

## What he gets wrong, exactly (misses.py, all 86,821)

    RIGHT            63.8%
    CLOSE            13.7%   key in his 2nd or 3rd
    LOST TIE          4.9%   right sentence ties the winner, loses the break
    FEWER WORDS      11.7%   right sentence is in the field, shares fewer
                             question words than the winner
    SHARES NOTHING    4.4%   reached, but no word in common with the
                             question or its thesaurus pull -- the real
                             paraphrase gap ("grow up" / "born and raised")
    NO PATH           0.04%
    NOT STORED        1.3%   the linker lost it
    NOTHING           0.1%

The answer sentence is in the store 98.5% of the time and the walk
reaches it when it is there. Misses are ranking. And a good part of
the ranking misses are the linker's, not his -- four bugs the examples
exposed, each measured alone on the 5k sample (base 59.1, NOT LANDED,
owner's call):

    accent fold      59.9   Beyonce != beyonc: the regex stops at the
                            accent, so the question never matched the
                            article; the one unaccented sentence got
                            rarity 1.0 and won every tie
    digits as terms  61.1   numbers are not terms; half the keys are
    unique names     60.2   sentence names restart per paragraph: 352
                            sentences silently overwritten corpus-wide
    abbrev split     60.6   "St. John's" is three sentences
    the four         64.2   NOT STORED -> 0
    + crude stemmer  65.0   -s -ed -ing -ies; SHARES NOTHING 4.8 -> 2.5

## The feedback path, measured (curve.py TAUGHT arm)

Grade the first half of an article's questions with their keys, exam
the second half, never graded. 10,057 exam questions:

    how much the right item takes     re-asked      unseen
    earns only (second tier)          73.3%         +14
    takes specific words (K=1)        82.2%         +10   <- shipped
    takes specific words (K=3)        88.0%          +4
    takes every missing word          95.8%         -32

At 20,000: re-ask 86.3%, unseen +43 (plain residue is +47). Feedback
on a question teaches that question, hard. It does not transfer: the
more the right item takes, the more it steals from its neighbours.

## The lesson that IS general (pairs.py)

When a question uses a word the article never uses and the right
sentence was found anyway, pair the question word with the sentence's
words. Scored by how much the two keep each other's company, the top
of the list is morphology and spelling, mined from his own graded
record with no dictionary: begin->began (87 articles), honor->honour,
license->licence, convinced->persuaded, death->mortality,
weigh->pounds, announce->announced, die->died, win->won.

Tested honestly -- mined on 221 articles, applied as a thesaurus on
the other 221, which never contributed a pair (41,622 questions):

    thesaurus                       top1
    wordnet (127k words)            62.7%
    wordnet + best 100 mined        62.8%
    wordnet + best 300 mined        62.9%
    wordnet + best 1000 mined       63.3%
    wordnet + best 3000 mined       63.4%   +310 answers
    best 3000 mined, NO wordnet     63.2%   beats wordnet alone
    nothing at all                  62.4%

Monotone in how many pairs he keeps, still rising at 3000 (out of
478,798 mined -- the cut is the next knob). And the line that matters:
**3,000 pairs mined from his own graded record beat the entire
installed 127k-word WordNet.** The dictionary is worth 0.3 points; his
own record is worth 0.8 and climbing. Learn the thesaurus from
feedback; the installed one was never doing much.

## The four directions the owner named (09-12)

His words: *"perhaps we should explore a complex domain mastery. or
even slightly related domain mastery? we also need to figure out how
to teach meta rules and information training, and transitive and
translatable concepts for generality, as well as work on the
vocabulary to make it easier for it to use."*

**1. Domain mastery (complex, or slightly-related).** The overlap
numbers make this the sharpest experiment available: on an eclectic
corpus neighbors interfere 170:1 at ten articles and 48:1 at 440, while
reinforcement grows 14x. The prediction worth testing is that
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
