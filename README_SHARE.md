# ISAAC v1 alpha — shared package

A symbolic learning engine in one Python file: learns from raw
observation, keeps everything with receipts, refuses honestly,
induces rules (and rules about rules) from its own experience, and
consults classic solvers as certified instruments.

## Run it (Windows/Linux/Mac, Python 3.12)

    pip install numpy clingo z3-solver sympy
    python rebuild/run_gates.py --jobs 0

That one command runs the whole verification suite — every claim in
the docs maps to a row; green is an exit-code fact, not prose. Rows
needing external corpora (CLOTH exams, ARC-AGI) print SKIP unless
you fetch them (CLOTH: CMU's CLOTH.zip into data/cloth/; ARC:
github.com/fchollet/ARC-AGI into data/arc-agi/).

## Talk to him

    python code/talk.py

Teach in plain sentences, ask questions, `why` shows the receipt,
`asks` shows his own open questions, `play` runs a self-challenge
session. `quit` saves his mind to one small file.

## Read, in order

1. PARTS_MANIFEST_2026-08-30.md — every part, where it lives, its
   test, its honest grade
2. HANDOFF_PROPOSAL_v2_2026-08-23.md — the full program, claims
   typed and scoped
3. TEARDOWN_2026-08-23.md — the hostile review that shaped it
4. SYMBOLIC_SYSTEMS_PRIMER_2026-08-30.md — the history this builds on
5. rebuild/RUN_LEDGER.md — every measured number with its commit

Wrongs are kept on the record with their corrections. Anything not
reproducible by a command should be treated as false.
