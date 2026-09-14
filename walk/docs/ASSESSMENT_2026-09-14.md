# Isaac, the walk: an assessment of his working model as of 2026-09-14

Medium depth. Everything quoted below is a real transcript or real data from
this machine at savepoint `walk-2026-09-14` plus the day's commits through
2a0712a. Nothing is described from memory; where a number appears, the
script that produced it is named so it can be rerun.

Owner's question: a breakdown of his working model, and specifically the
"meta-rules that classify the situation, then pick object-level rules",
with an example problem and the library data he queries and returns.

---

## 1. What he is, in one paragraph

A store of items with references, walked by one loop. An item has a name, a
kind, content, a truth mark (+1 / -1 / 0 / null), a native flag, a tag and a
list of references. Prose becomes sentence items that point at the terms
they name; a table row becomes an item whose column headers become spines
pointing at every row. A question becomes a bag of its words plus what his
thesaurus adds; he walks from every bag word the store knows, depth one per
step, nothing pulled twice, until it settles. What is reached is ranked, and
the ranking rule and the tools that feed it are chosen by him, per kind of
question, from his own record of when each was right. Every answer leaves a
sense reading behind, and every correction is filed and comes back.

---

## 2. The working model, layer by layer

### 2.1 Object level: the data and the one loop

| piece | what it is | where |
|---|---|---|
| item | name, kind, content, truth, native, tag, refs | engine/core.py |
| linker | sentence -> item + term items both ways; CSV row -> item + spines | engine/linker.py, mind.link_table |
| walk | from the seeds, depth one per step, nothing pulled twice | mind.walk |
| score | per reached sentence or row: (own words shared, rarity of the shared words, fit to the question's kind, bag words shared); highest first; name breaks the last tie | mind.score_all |
| gates | numbers compare (`2900 > melting_point_k 533`), lists attack (`hcl attacks cu`); survivors ranked by cost then density, one run per context-holon | mind.gate, mind.field |
| residue | a clear-win answer is banked as a run item the question's words point at; a repeat question gets the diff | mind.residue, compare_runs |
| relevance | (context, item) -> signed int; -1 refused, +1 confirmed; the scorer sets refused aside and puts confirmed first | core.Store.rel, score_all |

### 2.2 Object-level rules he fills himself (the tools)

All of these have contents that come only from his own graded record or from
what he read; the builders are code, the contents are his.

| tool | built from | what it does in an answer |
|---|---|---|
| thesaurus (3000 pairs) | question words the article never used, paired with words of the right sentence, kept when they keep company across articles | widens the bag |
| kinds table | question kind vs what the right sentence carried (year/number/name/percent/money), log odds against his wrong picks | the `fit` term of the score |
| reading dictionary | words of a store that keep company across its own sentences; no feedback needed | widens the bag, per store |
| venn | question words as constraints, loose first; a word that cuts nothing is not attention; one that would leave nothing is dropped | reorders his field by survivors (a switch; he leaves it off) |
| lens chain | random conjunctions over words-only atoms, readout = right sentence vs every other in his field, chained on what stays wrong | breaks the exact ties his score leaves (not yet a switch) |
| attention record | selects / trips per word, from his compare of the right answer and his pick | printed as the why; feeds nothing in the score now |
| confirmations | +1 for a told-right or key-confirmed answer, -1 for a refused pick, per question context | a confirmed answer stands on rerun |

### 2.3 Meta-rules: classify the situation, then pick the object-level rules

This is the layer the owner asked about. What he can currently *see* about a
situation is small, and it is worth being exact about it.

**Situation features he reads before answering**

1. The kind word of the question: who / when / where / how many / how much /
   how / what / which / why / other. (`mind.kind`)
2. How many of the question's words the store knows, capped at 4.
   (`mind.context_at`, level 2 = `kind/known`)
3. Whether a confirmed answer already exists for this exact context.

**The pick: the selector.** For the context, his record holds, per toolset,
`[right, asked, seconds]`. Toolsets are the 24 settings of his switches
(thesaurus on/off, reading on/off, kinds off/second/first, venn on/off).
He ranks by right rate, then less time, and states the reason:

    tools: level 1, what: thes right 14282/22433 in 3.9ms
           vs thes+kinds-second 14213/22433 in 4.2ms

His current picks by kind: thesaurus alone for what / how / where / other /
why; thesaurus plus kinds for when / which / who; thesaurus plus reading
plus kinds for how many; thesaurus plus kinds-first for how much.

**Rules about the pick (his settings, chosen by him with `tools.py tune`):**
a context needs 100 graded asks before it counts (he moved this from my 20);
rank right first then quicker (he refused quick-first: -418, and right-only:
-9); trust the coarse record before the fine one (he moved this from
finest-first: +10). Each decision is filed with predicted-versus-found.

**Situation features he reads after answering (the sense line)**

    sense: maybe (gap 1 of 21 in the field) | 3 words known, 0 not |
           support 7 from human | 0.20ms, 124 pulls, 374 lookups,
           0 writes | store 165 | agrees

`sure / likely / maybe / guess / nothing` comes from the margin between winner
and runner-up, calibrated on the exam (three words clear is right 95% of the
time, tied 22%). A confirmed answer reads `sure`. Pulls and lookups are his
load. `agrees / differs` is against his own last answer to the same question.

**Meta-rules that change the action**

| if the situation is | then he |
|---|---|
| critic score > 2.0, or he said `guess` | investigates before deciding: failed words, translations, satisfied constraints, agreement under all 24 settings; decides, or says don't know |
| a correction arrives | refuses the pick for this context, confirms the told-right item, gives it the specific words it lacked, compares the two for his attention record, re-asks under all 24 settings and files each into the selector, stamps the verdict on the last sense reading |
| the same question again | always reruns; reports agrees or the diff; a changed answer mints a lesson |
| a tied field | does not bank the run (a guess is not a lesson) |
| (word problems) a known shape | applies the shape's meaning; `understood` |
| (word problems) no known shape | takes the nearest shape by closeness only where his record says that closeness has been right; otherwise `not understood`, asks |
| (word problems) a number missing | asks for it by name instead of answering |

That is the whole meta layer. It classifies on the kind word, the words
known, the margin, the critic, and (for problems) the shape. It does not yet
classify on structure, on word type, on the role a quantity plays, or on
what a sentence is about.

---

## 3. The worked example: a question against his rocketry store

The store: `walk/engine/messy.txt` (forum prose), `walk/materials.csv`
(12 materials, 7 columns), `walk/conditions.csv` (apcp / sugar / black powder
conditions), plus the runs and lessons of earlier sessions. 165 items.

### 3.1 The query, and the library data he pulls

Question: `what nozzle material for apcp`

    question words: ['apcp', 'material', 'nozzle']
    thesaurus pulls: {'material': ['materials', 'war']}
    seeds: ['apcp', 'material', 'materials', 'nozzle']
    reached 124 items; candidates 21

The seed items and what they point at (this is the library, as items):

    apcp       term   refs ['s008_apcp_different_story', 's009_graphite_everyone_uses',
                            's011_wouldnt_try_apcp', 'apcp_flame_temperature',
                            'apcp_wall_stress_mpa', 'apcp_exhaust_hcl']
    material   term   refs ['h000_nylon_melts_useless', 'run_001', 'run_002']
    materials  table  refs ['lead', 'aluminum', 'steel', 'copper', 'titanium', 'nickel']
    nozzle     term   refs ['s000_tried_copper_nozzle', 's010_someone_tried_cat',
                            'h000_nylon_melts_useless', 'run_001', 'run_002']

Note the thesaurus pull `material -> war`: a pair mined from his SQuAD
record that is noise here. It cost nothing, because `war` is not in this
store. Note also `material -> materials`: that pull is what reaches the
table.

A table row, as an item, with its spines:

    copper   {'melting_point_k': '1358', 'oxidation_onset_k': '500',
              'yield_strength_mpa': '210', 'density': '8960',
              'thermal_conductivity': '400', 'cost_per_kg': '9.0', 'made_of': 'cu'}
             refs ['cu', 's000_tried_copper_nozzle', 's006_copper_pulls_heat',
                   's007_thats_copper_one', 's008_apcp_different_story', 'materials']

The situation, as his meta layer sees it, and what it picked:

    level 1 context what    -> thes 14282/22433 3.9ms, thes+kinds-second 14213/22433 4.2ms
    level 2 context what/3  -> thes 2529/4322 3.7ms,   thes+kinds-second 2513/4322 4.0ms
    his kinds row for 'what': year .433, number .387, name .313, percent .446, money .26
    his settings: min_record 100, rank right,quick, levels coarsest-first

Coarsest-first means the level-1 row decides: `thes`.

### 3.2 The return

    tools: level 1, what: thes right 14282/22433 in 3.9ms vs thes+kinds-second ...
    attention: material 28>13, nozzle 13>1 | dropped: apcp
    sense: maybe (gap 1 of 21 in the field) | 3 words known, 0 not | support 7 from human
           | 0.20ms, 124 pulls, 374 lookups, 0 writes | store 165 | agrees
    1. [human] nylon melts at 533 k, it is useless as a nozzle material
    2. [messy.txt] oh and someone tried a cat litter nozzle (bentonite) rammed in ...
    3. [messy.txt] ok so i tried a copper nozzle on my sugar motor last weekend ...
    apcp: 12 candidates, 8 fail, 4 survive
      x steel      apcp_flame_temperature 2900 > melting_point_k 1783
      x aluminum   apcp_exhaust_hcl attacks al
      x nylon      apcp_flame_temperature 2900 > melting_point_k 533
      x copper     apcp_exhaust_hcl attacks cu
      ...
      v graphite         cost 15.0  density 1800
      v silicon_carbide  cost 25.0  density 3200
      v tungsten         cost 35.0  density 19300
      v zirconia         cost 60.0  density 6000
    (walked 124 items from apcp, material, materials, nozzle)

Reading it by layer:

- The **object level** found 21 candidates and ranked a human-told sentence
  first because it shares two question words (`nozzle`, `material`), score
  `(2, 0.53, 0.0, 3)`. The right sentence for a person, "graphite is what
  everyone uses for apcp throats", shares one word (`apcp`) and says
  `throats`, not `nozzle`. This is the paraphrase gap, and it is his
  dominant failure class on every corpus.
- The **gates** did the part he is best at: the table answered the real
  question. Eight materials fail a stated condition with the comparison
  shown; four survive, ranked by cost. Graphite is first. The answer carries
  the reason as the comparison, never as a verdict word.
- The **venn line** says which words did the cutting (`material 28>13,
  nozzle 13>1`) and that `apcp` was dropped: no sentence in the field that
  survived the first two cuts also had it. That is the honest trace of the
  miss.
- The **sense line** says `maybe`: one word clear of the runner-up, which on
  the exam is right about two thirds of the time. Support 7 from a
  human-told item. Cost 0.2 ms.

### 3.3 The correction, and the second ask

    no: graphite
    under every setting, 0 of 24 would have been right
    his pick for this kind of question is now thes (...)
    he said maybe; not. when he says maybe he is right 0 of 1
    fewer words -- picked h000_nylon_melts_useless, right is s009_graphite_everyone_uses
    compared with h000_nylon_melts_useless: selects apcp | trips material nozzle
    learned: s009_graphite_everyone_uses now answers to material nozzle
    refused for this question: h000_nylon_melts_useless

Every line is a different meta-rule firing. "0 of 24 would have been right"
is the important one: no choice of tools could have fixed this, so it is not
a selection problem, it is a vocabulary problem (`throats` / `nozzle`), and
the repair that follows is the vocabulary repair: the right sentence takes
the two words it lacked.

    what nozzle material for apcp
    sense: sure (gap 0 of 20 in the field) | ... | store 168 | differs
    1. [messy.txt] graphite is what everyone uses for apcp throats.
    changed since last time:
      then, not now: h000_nylon_melts_useless
      now, not then: s009_graphite_everyone_uses

Now `sure`, because the answer is confirmed for this context, and `differs`,
because he compared with his own last answer and says so.

---

## 4. A second example, where the meta layer cannot see the problem

From `walk/look.py` on held-out articles (his critic objected, he looked):

    x What is an alloy?   [key: a mixture of metals or a mixture of a metal and another element]
        failed by the answer: nothing; every word that could cut, cut
          s006_mangalloy_alloy_steel     satisfies 1 (alloy); wins 4 of 24 settings
          s003_pig_iron_hard             satisfies 1 (alloy); wins 4 of 24 settings
          s001_however_small_amounts     satisfies 1 (alloy); wins 8 of 24 settings

Every candidate satisfies the one content word. The defining sentence, "An
alloy is a mixture of metals", is not in his top five, because `alloy` is in
every sentence of the article. Nothing his meta layer reads distinguishes the
sentence that *defines* a word from the sentences that *use* it. Where the
word sits and what follows it would. That feature does not exist yet. This
is the clearest single statement of where the meta-rules are thin.

---

## 5. A third example: a word problem through the shape map

`walk/shapes.py`. His map, learned from 120 labeled problems:

    15x  a - b   subtract  there were N T on the table . P took N of them . how many T remain ?
    11x  a * b   multiply  a shelf holds N T . how many T do N shelves hold ?
     9x  a // b  divide    P shares N T equally among N friends . how many T does each friend get ?

Three situations and what he does in each:

    understood   shape seen before -> apply its meaning        120 / 120 right
    analogy      nearest shape, said as such with closeness    right only at 20-34% alike (60/60);
                                                               0/60 at 35-49% alike; so he now
                                                               refuses to guess there and asks
    ask          a number is missing -> "How many marbles?"    30 / 30

The inverted calibration is the day's cleanest finding: surface likeness
(shared word pairs) runs *against* meaning on "how many more X than Y",
which looks like the "gives N more" shape and means the reverse. He caught
it in his own record and stopped trusting that band. The structure that
would fix it is the role of each number (a holding, a transfer, a group
size), not the words around it.

---

## 6. Evaluation

### 6.1 What holds, with the number and the script

| capability | measure | script |
|---|---|---|
| answer from prose, each article alone | 64.7% top1 / 78.1% top3 on 86,821 SQuAD questions | bed.py |
| the same, compiled | 0.4 s for all of SQuAD (24 goroutines) | go/bench.exe |
| his own tool choice vs the best fixed setting | 26433 vs 26425 on the held-out 41,622 | tools.py court |
| he sets his own settings | kept 2 of my 3 defaults, moved 2, all with predicted-vs-found | tools.py tune |
| calibrated confidence | own+3 right 95%, own+1 72%, tied 22% | margin.py |
| he learns as he processes | +0.5 pt on held-out questions after a warm-up half | curve.py |
| come back to what he got wrong | 62.5% -> 99.6% on the second pass, 99.7% by the eighth; regressions 0 once rights are kept | loops.py |
| critic as a sensor | right to object 57% (objects on 28%) to 80% (objects on 4%) | lens.py, look.py |
| refusal when he looks and cannot decide | 58 of 68 "don't know"s were on wrong answers | look.py |
| read a textbook and check it | 494 of 643 Python Tutorial examples verified against the book | school.py |
| parts of a thing, learned | tuples and defs: 10/10 locators on the lesson; RUN 40/40, READ 38/40 on new defs | parts.py |
| make things and know what he made | 11/12 made right, 11/12 judged right; a list called a tuple caught and relearned | create.py |
| word problems | quantities 96%, unknown 100%, asks 50/50; relation 92% with the correction loop | problems.py |
| shapes and analogy | understood 120/120; analogy trusted only where his record says | shapes.py |
| word types | 147,306 typed from WordNet; his own noun 68% agreement, verb 54% | wordtypes.py |

### 6.2 What does not hold, with the number

| weakness | measure | note |
|---|---|---|
| paraphrase gap | 4.4% share nothing, 11.7% fewer words, of all misses | the dominant class on every corpus |
| store-size locality | 1 article 59.9% -> 10 articles 57.7% -> 440 articles 47.9%, cost roughly linear | prose wires everything to everything |
| word-level atoms exhausted | three independent runs: lens +0.25 pt, attention 0, venn negative | the next atoms must be structural |
| the look re-uses the same senses | 22% -> 22% when the critic objects | it needs a new sense to look with |
| the meta layer sees two features | kind word, words known | no structure, role, type, topic |
| definition questions | "what is X" fails when X is in every sentence | position and what follows |
| context key collisions | 15 of 26 survivors in the retry loop | two questions, same words, different answers |
| my hand still in him | tie margin 10%, OBJECT_AT 2.0, option lists, MIN_ATT, the caps, the grader | named, not yet his |

### 6.3 The honest one-line verdict

He retrieves and ranks by words, chooses his own tools and settings from his
own record with reasons, senses and calibrates his own answers, and repairs
what he is told. He does not yet see structure: not the shape of a sentence
beyond its words, not the role a quantity plays, not the type of a word he
reads unless told. Every measured ceiling this week traces to that one gap,
and the meta-rules cannot classify a situation on a feature they cannot see.

---

## 7. What would give the meta layer more to classify on

In the order the evidence points:

1. **Position and structure atoms** for the lens and the look: where a word
   sits, what precedes and follows it, whether the sentence is about the word
   or merely uses it. Predicted to move definition questions first.
2. **Word types into the shapes**: a thing is any noun, a person is a
   capitalized word he does not know, verbs get a slot; shapes stop being
   tied to templates. `wordtypes.json` exists; the stemmer is the missing
   piece for verbs.
3. **Quantity roles** in the shape map: holding / transfer in / transfer out /
   group size / count of groups, learned by aligning slots across shapes
   that meant the same thing. That is the slot-level "A is like B".
4. **Composition**: join a signature from one template with a body from
   another, graded by running it. The one-parameter no-return function he
   cannot make is the standing example.
5. **The context key**: exact question rather than sorted words, or both
   levels, to end the collisions.

Each of these adds a feature the meta layer can read, which is the only way
"classify the situation" gets better than "read the kind word".
