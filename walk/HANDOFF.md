# The walk — handoff, 2026-09-12, updated 2026-09-13 (six times)

> ## 2026-09-13, on the owner's PC (TurtlePC, 32 threads) -- READ THIS BOX FIRST
> **There is no C version.** Searched every branch of this repo, Documents,
> both Downloads folders and isaac-full.zip: no .c or .go source anywhere,
> and no C compiler installed (Go only). The box below was wrong about
> that; do not hunt again. **The compiled option is `walk/go/bench.go`**:
> bed.py ported line for line -- same store, same walk, same score --
> every one of the 86,821 top answers identical to python (top3 count
> one off; a 2nd/3rd place on one question).
>
>     cd walk/go && go build -o bench.exe .        (6s, once)
>     walk/go/bench.exe 999999 -jobs 24            all of squad in 0.7s
>
>     full squad, 86,821 q      wall      q/s
>     python, 1 core           229.5s      378
>     python, -jobs 24          16.7s     5192
>     go, 1 core                 9.0s     9676    25x python
>     go, -jobs 8                1.3s    64867
>     go, -jobs 24               0.7s   133227    24x python's best
>     go, -jobs 32               0.6s   150073
>
> Two port lessons that would bite any future port: (1) python 3.12's
> sum() is compensated (Neumaier); naive adding differs in the last bit
> and flips ties (55 of 5000 answers moved). (2) rarity must be summed
> in ONE fixed order for every sentence. (3) python lowercases the
> Turkish dotted I with the full mapping, Go with the simple one. All
> three are handled in bench.go.
>
> **The unfinished court ran** (tools.py court, 221 held-out articles,
> 41,622 q, ~10s an arm at 24 jobs). Kinds as committed HURT:
>
>     wordnet 62.7 | his thesaurus 63.2 | nothing 62.4
>     his reading dictionary alone 62.8
>     thes+kinds 60.5 | kinds alone 60.1 | all three 60.4
>
> and because load_dictionary() loads tools.json by default, the full
> bench at 3aea2c5 had silently dropped to 61.9 (committed unmeasured).
> **Fix landed: kinds is the SECOND tie-break, after rarity** (score
> tuple own, rare, fit, bag -- one line in score_all):
>
>     his thesaurus + his kinds  63.5   <- best arm
>     all three of his           63.4
>     his kinds alone            63.1   (beats wordnet now)
>     his thesaurus + reading    63.1   (reading adds nothing on top of
>                                        his thesaurus: same signal)
>
> Everything re-measured on the new score, all 86,821. The full bench
> includes the 221 articles his tools were mined from, so the clean
> number is the court's 63.5, not the 64.7:
>
>     bench      64.7 top1 / 78.1 top3        (63.8 / 77.5 before)
>     misses     RIGHT 64.7  CLOSE 13.4  LOST TIE 4.5  FEWER WORDS 12.5
>                SHARES NOTHING 3.5  NOT STORED 1.3  NOTHING 0.1
>                tie-break vs the old order: fixed 5603, broke 2700
>     margin     own+3 12.7% @95.0 | own+2 15.6% @91.9 | own+1 33.6% @72.2
>                broken by tie-break 29.7% @38.6 | tied 7.4% @23.8
>                (fully tied was 19.8%: kinds broke most of it)
>                answer only on a clear winner: covers 92.5% at 68.0%
>     curve      COLD 66.7  WARM 67.2 (+51)  CLEAN 67.1 (+37)  TAUGHT 67.1
>                (10,057 held-out exam q; residue still true and small)
>     overlap    pool=10: 63.2 (was 57.7); stole 6437 (7.4%) vs gave the
>                right answer 45 (0.1%) = 143:1 (was 170:1); gap to a
>                single article 1.5 pts (was 2.2)
>
> Not rerun: the 440-in-one-store run (2.4h in python). The Go bench
> fills one store per article; pooling needs overlap.py ported too.
>
> **HE PICKS HIS OWN TOOLS NOW (owner ruling, same day: "we dont design
> him, we discover him and he discovers himself").** Every tool is a
> switch (thesaurus / reading dictionary / kinds off-second-first = 12
> toolsets). `tools.py learn` runs all 12 on every graded question of his
> half and files right/wrong under the context: level 1 = question kind,
> level 2 = kind + how many question words the store knows. That table is
> the SELECTOR, saved in tools.json; `mind.select()` reads it and answers
> with the reason (his pick's count vs the runner-up). mind.py prints
> `tools: level 1, when: thes+kinds-second right 2288/3279 vs ...` on
> every answer. Court on the held-out half (all 12 fixed + his choice):
>
>     best fixed (thes+kinds-second)   63.5   26425
>     HIS CHOICE, level 1              63.5   26427   thes 69%, thes+kinds-second 24%
>     HIS CHOICE, level 2 over 1       63.5   26410   (the first small dip)
>     none                             62.4
>
> He picks thes alone for what/how/where/other and thes+kinds for
> when/which/who/why, from counts, not from me. Level 2 is his "confused
> nuance" layer: more contexts, thinner records, 17 answers worse. Do not
> revert it; feed it. The hand-set default (thes+kinds-second) only
> applies when he has no record for a question.
>
> **ATTENTION, BY HIS OWN DIFFERENTIATION (owner, same day: "you compare
> the two answers to each other, and see what difference in the question
> selects between them. when you identify the difference thing, that is
> your attention word... not selecting because you were clever").** A
> word with no record is FLAGGED probably attention. On every graded
> question he holds the right answer and the one he gave (or nearly gave)
> side by side: a question word in the right one and not the other is
> what SELECTS (what he was missing); a question word in the other and
> not the right one is what TRIPPED him. Selects more than trips:
> attention. Trips more: fluff. Level 1 = the word, level 2 = kind of
> question / word. `no:` corrections do the same live and print it:
>
>     fewer words -- picked h000_nylon_melts_useless, right is s009_graphite...
>     compared with h000_nylon_melts_useless: selects apcp | trips material nozzle
>
> 17,996 words assessed on his half. His attention: first, century,
> between, population, government, world, since, president, modern,
> french, state, power, largest, battle. His fluff: year, name, type,
> city, american, country, and every topic word (beyonce, chopin,
> napoleon, victoria) because the topic is in every sentence and so
> trips him. His summaries: "evolved romanesque architecture succeeded
> renaissance"; "characteristics include pointed arch ribbed? vault?
> flying buttress?". The record is walk/attention.json (gitignored,
> rebuilt by `tools.py learn` in 11 min at -jobs 24).
>
> Two switches use it: `trip` (words that trip him do not count) and
> `att` (attention hits rank, second or first) -- 72 toolsets. THE COURT,
> held-out half: neither helps there. thes 63.2 -> thes+trip 62.6 ->
> thes+att-second 61.7; best fixed is still thes+kinds-second 63.5.
> **AND HIS CHOICE DROPPED: 62.8 (was 63.5). He picked thes+trip 85% of
> the time.** Why: his selector's record was made on the same articles
> his attention record came from, so on those articles trip looked
> right; on new articles it is not. That is the owner's predicted dip
> (a new layer, more noise). The fix is his, not a revert: the
> selector's experience of a tool must come from articles the tool was
> not learned on (build tools on one part of his half, record the
> selector on the other part), and when his pick is wrong more often
> than a plain toolset would have been, that is a graded run about the
> selector -- the level-up correction. Neither is built yet.
>
> Definitions that failed on the way, all mine, none in the code now:
> carried/left (what askers kept -- a corpus statistic, not his work);
> recovery-from-the-store (one rare word brings a sentence back);
> drop-word-and-re-ask (swamped by "not asked"). Applying verdicts to
> the question's words with a bad table collapses everything to ~34%.

> ## ⛔ FOR THE NEXT SESSION (local, on the owner's machine)
> *(09-13: done. The C version does not exist; the court ran. See the box above.)*
> This box ran on ONE 1 GHz core in a cloud container -- nothing that
> follows is your machine. The owner has a C version and the corpora
> on his own disk; NEITHER is in any repo, and this session never saw
> them. First: `git pull origin record-repair`, then find the C version
> before touching anything speed-related; it may supersede walk/ for
> the engine core. Second: run the one unfinished court below with
> `-jobs 12` (two minutes for you; hours here).

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
    tools.py          THE TOOLS HE BUILDS HIMSELF: learn / court
    tools.json        what he built (committed, 53 KB): his thesaurus,
                      3000 pairs; his kinds table
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

## His own tools (owner 09-13: "have him build his own thesaurus,
## and dictionary, and reference tables") -- BUILT, court UNFINISHED

Three tools, none installed, all mined from his own record or read
off the text he was given. `mind.py` loads `walk/tools.json` first
and only falls back to wordnet when he has built nothing
(`load_dictionary(wordnet=True)` forces the installed one, for
comparison).

    THESAURUS   from graded runs: (question word the article never
                used -> word in the right sentence), kept when the two
                keep each other's company across articles. 3000 pairs.
    DICTIONARY  from reading, per store, no feedback: the words of the
                text that keep each other's company across its own
                sentences (read_dictionary; kept on the store; bag
                expansion uses it).
    KINDS       from graded runs: the question's kind word against what
                the right sentence carried, as log odds vs what he
                picked wrongly. Learned table (rows = kind, cols = what
                the sentence carries):

                          year   number   name   percent   money
                when      1.02    0.87    0.34   -0.20    -0.03
                how much  0.55    0.78    0.17    1.27     1.64
                how many  0.48    0.72    0.22    0.50     1.03
                who       0.46    0.38    0.41   -0.15    -0.04
                where     0.41    0.35    0.41   -0.24     0.00

                It came out the way a person would write it, and nobody
                wrote it. In the score it decides among candidates
                sharing the same number of question words, before
                rarity (score tuple: own, fit, rare, bag).

The court (learn on 221 articles, test on the other 221 which never
contributed anything) got ONE arm done before this box ran out of
patience:

    wordnet (installed)          62.7%   126 s serial
    his thesaurus                pairs.py measured 63.2% (3000 pairs)
    his thesaurus + kinds        UNMEASURED
    nothing                      62.4% (pairs.py)
    his kinds alone              UNMEASURED
    his dictionary from reading  UNMEASURED
    all three of his             UNMEASURED

RUN THIS FIRST (tools.json is committed; no relearn needed):

    python walk/tools.py court 999999 -jobs 12

If kinds hurts, drop `fit` from the score tuple in score_all (one
line) -- the table is still a good reference item to keep. If the
reading dictionary helps, it costs nothing and needs no feedback: it
is the strongest "he builds his own" result available, because it
needs no keys at all.

## The four directions the owner named (09-12), where they stand


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
