# Isaac — Project

This project is organized as **four parts**, the way the builder thinks about it.
Three things, plus the story of making them:

| part | folder | one line |
|---|---|---|
| **The story** | `4_the_story/` | where it came from, and why — the builder's, personal. |
| **The theory** | `3_the_theory/` | the conceptual framework — *machine-independent*. Why structure exists, what comparison is, meaning as topology. |
| **The machine** | `2_the_machine/` | Isaac — the running thing that bets on the theory. Code + docs + the empirical evidence. |
| **The history** | `1_history_of_development/` | how it came to be — the lineage, design proposals, session diary. |

Plus `overviews/` (consolidated master briefings that span all four) and four meta
files at the root: this `README.md`, `FILE_LOCATIONS.txt` (the full map),
`REVIEW_NOTES.md` (a corpus review), and `TODO.md`.

> **The one distinction that organizes everything:** *theory ≠ machine ≠ claims.*
> The **theory** is the framework (it would be true even if Isaac were never built).
> The **machine** is Isaac. The **claims** are the empirical findings that test the
> bet — those live as *evidence* inside `2_the_machine/`, not inside the theory, so
> the theory stays clean.

## Start here

1. `4_the_story/THE_STORY_OF_ISAAC.md` — what it is and where it came from.
2. `3_the_theory/Latent_Theory_of_Informational_Structure.docx` — **the keystone.**
   The single consolidated theory; everything else in `3_the_theory/sources/` is a
   chapter of it expanded.
3. `2_the_machine/docs/ISAAC_BUILD_STATE.md` — what works right now.
4. `2_the_machine/docs/ISAAC_THEORY_OF_OPERATION.md` — how the engine works.
5. Run it (below).
6. `1_history_of_development/handoffs/SESSION_HANDOFF_2026-06-24b.md` — latest state
   and the open frontier.

## Run it

```
cd 2_the_machine/code
python isaac.py            # core engine self-test — expect 6/6
```
Requires Python 3 + numpy. On Windows prefix with `PYTHONUTF8=1` if box-drawing
characters error. The demos live beside `isaac.py` and import it directly.

## The one-line version

One file, one class, one operation. Everything is *which* difference, against
*what*, at *what* scale. Differentiation makes the parts; memory recursion composes
the wholes. There is no third primitive.
