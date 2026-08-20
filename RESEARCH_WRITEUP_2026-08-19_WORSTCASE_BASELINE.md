# THE WORST-CASE BASELINE — day zero on a new net, and the two cures it earned
*(2026-08-19. Owner directive: "i think we need a new net to see how he
works. worst case and go from there." Probe:
`rebuild/worstcase_baseline.py`. Engine: v0.1.2-alpha1. All material
INVENTED — florbs, grinths, zims — so nothing anywhere is recall.)*

## The day-zero report card (after the cures; before-values in brackets)

| area | result |
|---|---|
| birth | v2 birth certificate 1,131 bytes, round-trips |
| language | generate 3/3; **complete 3/3 [was 0/3]**; unknown-word shrug YES [briefly lost mid-cure, restored by the stranger guard] |
| math | in-table 6/6; beyond-the-tables shrugs 2/2 (honest boundary) |
| discovery | 2/2 planted laws UNDERSTOOD to the coefficient (`+1.00*x0*x1`, `+3.00*x0 -2.00*x2`); pure noise NO RULE, accounting 0/0/100 |
| memory | **3/3 survive resurrection [was 2/3]**; node count identical through death |
| speed | teach 16 sentences <1ms; 338 table lines ~0s; v2 save 0.01s, load 0.01s; day-end body 26KB |
| battery | 15/15 capability areas after both surgeries |

## FINDING 1 (cured): THE PERIOD WAS THE POISON — every prefix is a lesson

Day zero reproduced the diagnosis campaign's mechanical wound in a
~20-node mind: `"a grinth eats" → None` when taught WITH the period,
`→ 'seeds' (conf 18)` when taught WITHOUT it. Root cause read directly
from `_compile`: **only the final token of a sequence was ever compiled
as a delta** — so every punctuated sentence taught the matrix exactly
one thing: "everything leads to `.`". Math only ever worked because
table lines end with the answer.

The cure (isaac.py `_compile`): every position compiles as a delta
with the same frame+window treatment the final position always had;
the final prefix reproduces the old counts exactly, interior positions
only add. `_pair_counts_rule=2` forces stale final-only caches to
rebuild on any loaded mind. Courts: the reproducer flipped
(punctuated == unpunctuated == 'seeds'); the pindle flipped (a fact
taught ONCE is answerable — **10 meetings failed before the cure**);
full battery 15/15 including test_boot's delta-compile exactness.

**THE BIG IMPLICATION, filed loudly:** the study era's dose findings
("one reading is not answerable; dose = hundreds of meetings") and the
real-exam scores (9.3/100) were measured THROUGH this bug — real exam
text is punctuated. The paraphrase cliff's "code fails silent" half
was this. **A0/A2 must re-run CLOTH on the cured engine before any
conclusion about his language capability stands.** The entire language
column of the old report card is now suspect in his favor.

## FINDING 2 (cured): THE STRANGER GUARD — power bought confabulation, honesty took it back

The compile cure created a NEW wound the same hour: window frames
generalized (`a _ is an → animal`), so `"a wug is an ___"` — a word he
has never seen — got the population answer instead of a shrug. Cure:
`lookup()` shrugs when any context token was never observed anywhere
in the net. Courts: wug shrugs again; all completions stay 3/3
(known-word roads untouched); battery 15/15. FILED, not yet done:
`check()` and `predict_next()` deserve the same guard; the guard is
mechanical honesty (stranger-detection), not understanding-on-his-
behalf.

## FINDING 3 (exonerated): resurrection was never the problem

The "late fact lost through resurrection" in the first run was the
dose/period wound wearing a costume — the pindle was never answerable
BEFORE the save either (court: asked pre-save). The v2 body's
equivalence court had already said item-for-item EXACT; day zero
confirms it behaviorally: 3/3 survive, node counts identical.

## FINDING 4 (open, filed): type-blend confabulation in generation

Pre-cure, `generate('grinth')` produced "the grinth eats moss ." —
fluent, grammatical, and FALSE (grinths eat seeds; florbs eat moss).
Generation walks type-level doors and can blend siblings' attributes
into confident falsehoods. Not re-courted post-cure; belongs to the
language rung (A6/S2 — the sentence court's fluency-vs-truth
distinction: every transition lived is necessary but not sufficient).

## Costs and watch-items

- Every-prefix compile multiplies pair counts (day-zero matrix 65×420
  → 93×872). Trivial here; at study-era scale compile cost grows with
  line length × positions — the speed rungs own the measurement.
- The old 07-03 plain-sum blind spot did NOT reproduce on the 2-term
  case (exact to the coefficient); the original pathology was 5-var
  positively-correlated mixing — that exact case still needs its
  court before "cured" is claimed.

## What "worst case and go from there" bought in one session

A 123-node mind small enough to autopsy completely reproduced two
already-diagnosed wounds, got both cured with receipts, exonerated
the body, and left the study-era language scores standing in doubt —
in his favor. The new net IS the instrument: every future engine
surgery re-runs this baseline as its floor court.
