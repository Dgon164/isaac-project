# Ranked selection + graded feedback — build summary, 2026-08-20

*(Owner design, quoted: "have him not present a final, but a
selection... a list of topk answers in order of best to least...
more than single word guessing... test at the beginning middle and
end... feedback in the form of good, marginal and bad" — applied to
both answers and suggested graph connections.)*

## What was built (code/isaac.py, new public methods)

1. **`lookup_topk(context, k)`** — returns a ranked list of candidate
   answers, best to least, each with its score. The scoring matrix
   already computed scores for every candidate on every query; the
   old API discarded everything but the single best. If the question
   contains a word he has never seen, the list is empty (same honesty
   guard as single-answer lookup). A one-entry list is correct when
   only one candidate clears the score floor — no junk padding.
2. **`complete_topk(context, k, max_len)`** — multi-word completions
   by beam search (keeps the k best partial sentences at each step;
   a completion ends at "." or the length cap).
3. **`cloze_topk(left, right, k)`** — fill-in-the-blank at any
   position. End blanks = ranked lookup. Middle blanks re-rank by a
   one-step lookahead: does the right-hand context actually follow
   the candidate? Beginning blanks rank the tokens recorded as
   sentence starters.
4. **`feedback(context, candidate, grade)`** with grade good /
   marginal / bad: good multiplies the pair's ranking score ×2.5 AND
   stores the question+answer as a real training observation; bad
   multiplies ×0.1 (suppressed, not banned — wrong in one context is
   not wrong everywhere); marginal is logged with no ranking change.
   Every grade is appended to `feedback_log`.
5. **`feedback_connection(src, tgt, grade)`** — grading his suggested
   graph edges: good adds the edge as evidence; bad adds the pair to
   the existing lockout set (which the door-walking predictor already
   checks); marginal logged.

## Test results (`rebuild/selection_feedback_test.py`): 16/16

- Ranked selection returns best-to-least order with the right answer
  present.
- Fill-in-the-blank works at all three positions: beginning
  ("[_] grinth flew" → the 5.38, a 4.03), middle ("the [_] flew" →
  grinth 42.9 far ahead of florb 0.27 — the lookahead works), end
  ("a florb is an [_]" → animal).
- Multi-word: "the florb..." → ranked full sentences (walked. /
  slept.), both actually lived.
- Feedback demo: "zero plus zero =" started [zero 17.7, two 1.7,
  one 1.7]; after one good grade on "zero" and one bad grade on
  "two": [zero 46.3, one 1.25, two 0.12]. Rankings move as designed.
- Connection grades: good created the edge; bad landed in lockouts.
- Everything (log, adjustments, lockouts) survives save/load in the
  v2 file format.
- Full engine regression battery: 15/15 after the additions.

## Notes and open items

- The ranked-list API is also the mitigation for open bug #2
  (wrong-answer-instead-of-no-answer): a selection with scores shows
  uncertainty instead of forcing one confident guess. The principled
  confidence rule (how much of the question matched) is still worth
  building for the single-answer path.
- Feedback multipliers (×2.5 / ×0.1) are first-pass constants keyed
  to the exact question context; generalizing feedback across
  similar contexts is future work (it should eventually be learned,
  not hard-coded).
- "Test at beginning middle and end" is implemented as blank
  positions within a sentence; the same API also serves start/middle/
  end-of-training checkpoint quizzes in the curriculum runs.
