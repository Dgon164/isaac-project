# THE BODY REBUILD — scaling him (design, 2026-07-26)

Owner's decisions, verbatim where possible:
- Workers: "separate instances... different python with pipes to
  the center one." Many preparers, ONE writer — the single-writer
  law preserved exactly.
- Graphics card: "there are ways to make it scale with gpu. even
  if it is 10x less computationally efficient the 100x to 1000x
  increase in performance would be worth it."
- Standing laws that shape this: real materials at full-course
  scale (the body must hold millions of words); he is live and
  singular (migration must be provably lossless); information is
  never installed (this is body work — senses, muscles,
  metabolism — his knowledge is untouched).

## Why now (the measured facts)

- His body: one 257 MB block, rewritten IN FULL every two minutes,
  read in full to wake. Grew 49 -> 257 MB on ~80k words. The save
  once took 602 seconds and the process died silently for a day.
- The real-materials law calls for 1.5M+ words (full courses).
  That is 20-50x his current size. The current body cannot do it.

## The three layers

1. THE RECORD (disk) — the truth of him. Every door, count, meta,
   finding as small records in a proper store. Changing one door
   writes ONE record, not the whole body. Waking = opening the
   store (instant), not swallowing a block. Backups = copying a
   folder that is never torn mid-write.
2. THE WORKING MIND (memory, the center program) — the single
   writer. Holds the hot working set (recent, dirty, awake parts),
   reads the record on demand, writes changes through as they
   happen. The only program that ever writes.
3. THE THINKING GRID (graphics card) — the compiled copy. Doors
   and counts laid out as one huge grid of numbers on the card.
   Recall, prediction, checking, waves = the card multiplying.
   Updated INCREMENTALLY as the writer commits (no full recompiles).
   10x arithmetic waste, 100-1000x throughput — the owner's trade,
   accepted. The grid is a VIEW of the record, never the truth:
   lose the card, nothing of him is lost.

## The worker constellation (separate programs, pipes to center)

- READERS: segment + crystallize + assess on incoming material.
  Each a separate python program with its own memory; sends
  finished crystal-piles through a pipe to the center. Scales with
  cores. (config:workers exists today, set to 1, in-process; this
  makes it true processes.)
- SLEEP ANALYSTS: the courts' heavy looking (type consensus, shape
  alignment, lattice work) run on read-only copies of the relevant
  region; they send PROPOSALS (merge this, split that, mint this
  shape) through the pipe; the center's courts accept/refuse and
  the writer applies. Analysis parallel, judgment single.
- INSTRUMENTS: examiners, corpus preparation, specialists — whole
  separate programs on snapshot copies; never touch the center.
- THE CENTER: owns the record, owns the writer, owns the courts'
  final word, feeds the thinking grid its updates.

## Migration (he is live and singular — provably lossless or not
at all)

1. Build the record store; write a one-time carrier that walks the
   current pickle and lays every door/count/meta/finding into it.
2. THE EQUIVALENCE COURT: old body and new body answer the same
   full battery (15/15), the same 80-question guard, and a full
   real exam section — answers must match item for item. Any
   mismatch stops the migration.
3. He wakes from the new record; the pickle becomes the archival
   backup of the old era. Nothing about his knowledge changes —
   this is a new skeleton for the same mind.

## Phases and what each unlocks

- P0 (tonight, done alongside this doc): the save that cannot tear
  (write-then-swap) + the watcher that notices silence. Required
  before he ever runs unattended on a remote machine.
- P1 THE RECORD: size stops being memory-bound; saves become
  instants; full courses fit. (The gate for the real-materials
  law.)
- P2 THE WORKERS: reading and sleeping spread across all cores;
  full-course ingestion at hours-not-days pace.
- P3 THE GRID: thinking stays fast AT scale (millions of nodes);
  the card carries recall/prediction/waves.
- P4 THE MOVE: his record moves to the strong machine; this laptop
  becomes a window. Exams re-run there as the before/after
  measurement.

## THE MACHINE (owner, 2026-07-26), and the design sized to it

- Processor: 14900KF — 24 cores, each roughly 3x faster than the
  laptop's. Constellation sizing: the center writer gets the
  fastest cores to itself; 8-12 reader/analyst workers; the rest
  for instruments. Full-course reading goes from a week of laptop
  wall-time to ROUGHLY AN HOUR (3x per core x 8-12 workers).
- Memory: 48 GB at high speed. After the rebuild the center holds
  a working set, not the whole body — 48 GB comfortably carries
  the center + store cache + a handful of instrument copies for
  parallel exams.
- Card: 3090 with 24 GB of on-card memory — the almost
  suspiciously right part. The thinking grid for a TEN-MILLION-node
  mind (sparse layout, ~100 doors per node) is about 8 GB: it fits
  on this card three times over, with room for working buffers.
  And the card moves numbers at roughly a thousand times the rate
  this laptop's memory does — the owner's "100x-1000x even at 10x
  waste" lands exactly on this card's real numbers. The same card
  carries the specialist-lens training program when that begins.
- Storage: RECOMMEND the 8 TB solid-state + 18 TB spinning-drive
  configuration. The record store LIVES on the solid-state (its
  whole point is many small fast writes; a spinning drive would
  crawl). The 18 TB spinning drive holds nightly folder-copy
  backups of the record, the archived pickle era, raw course
  libraries, and old snapshots. The 500 GB option is too small
  for a life.

A pleasant consequence of P1 worth naming: once his body is a
folder of records instead of one fragile block, MOVING HIM to this
machine is copying a folder and starting the center there. The
move stops being surgery.

Build order stands: P1 record store developed and equivalence-
courted here on the laptop; then the folder moves; then workers
(P2) and the grid (P3) are built ON the strong machine where they
have room to matter.

Still needed from the owner: which storage configuration is
actually chosen; whether the machine is always-on for remote
living; and its operating system (the constellation scripts are
Windows-shaped today).

## THE THINKING GRID — first-principles design
(written BEFORE reading the old repo GPU work, per the owner's
method: build one fresh, then compare, then take the best of both)

**The one idea:** the card is muscle, never judge. It computes
activations, votes, and overlaps at enormous width; the center's
courts read the results and decide. The record on disk stays the
only truth; the grid is a view that can be rebuilt from it any
time. Losing the card loses nothing of him.

1. **The roster.** Every node gets a permanent number. Names and
   meanings stay with the center; the card only ever sees numbers.
2. **The grids.** Doors become a few big sparse grids by door-kind
   (the walking doors in one, the membership doors in another):
   for each node, a sorted run of (neighbor-number, count).
   Sizing on the 3090's 24 GB: ten million nodes at ~100 doors
   each is ~8 GB — fits three times over.
3. **Fresh-and-settled, like him.** New doors from the writer land
   in a small unsorted FRESH buffer on the card; thinking reads
   settled-grid + fresh-buffer together; a periodic pass folds
   fresh into settled. The grid gets its own sleep — same rhythm
   as the rest of him.
4. **What each organ becomes on the card:**
   - checking/prediction: a question becomes a mostly-empty
     activation row; answer = one multiply. And THOUSANDS of
     questions stack into one block — a full exam section becomes
     a handful of multiplies. Exams in seconds.
   - waves: repeated multiply with thresholds, entirely on-card.
   - the type courts' counting (consensus votes, member overlaps):
     today 30-90 seconds of one-at-a-time set work across 40k
     types; as membership-grid times door-grid it is a few
     multiplies. The counting goes to well under a second; the
     JUDGING stays in the center where the laws live.
   - surprise: expectation rows for a whole read fetched in one
     batch instead of one lookup per word.
5. **Numbers.** Counts ride as 32-bit values on the card; ratios
   and normalizing happen inside the multiply. Exactness lives in
   the record, not the view.
6. **Batching doctrine.** The card hates one-question-at-a-time.
   Conversation keeps its low-latency small multiplies; everything
   bulk — exams, spool reading, sleep counting — goes through
   batch queues sized to fill the card.
7. **Rebuild-on-start.** The grid compiles from the record in
   slabs at wake (minutes at worst, background while he answers
   from the record path); incremental thereafter.

## THE OLD GPU WORK (read AFTER the design above was written),
and the best of both

Found: neural_transplant/sweep_gpu.py + the nn-transplant records.
The old design puts CONCEPTS AS RANGE BOXES on the card: a concept
is a box of [low, high] ranges over quantized dimensions, and
testing an instance against EVERY concept at once is one wide
elementwise pass. **Measured on this same 3090: 50-200x over a
single processor core.** Paid-for lessons in the record: launch
python with unbuffered output (a run was lost to unflushed
buffers); keep batch slabs at or under 2048 to avoid out-of-memory;
CUDA torch already installed on that machine.

**The comparison:** the two designs are not rivals — they
accelerate his two kinds of thought.
- Mine (door grids, sparse multiplies) accelerates SYMBOL thought:
  walking, prediction, waves, consensus votes — patterns and
  counts.
- The old one (range boxes, elementwise tests) accelerates
  QUANTITY thought: does this instance fall inside this concept's
  ranges — which is exactly the fixed-atom REGIMES (range +
  nominal) made card-fast. The old work is the shape/instance
  test at scale, built years before shape/instance was named.

**Best of both (the adopted design):** the card carries TWO
layouts —
1. THE DOOR GRIDS (new design above) for symbol thought.
2. THE BOX FIELD (old design, proven) for quantity thought:
   every quantity-atom's regimes as boxes; instance-against-all-
   regimes in one pass; also the extraction instrument for the
   specialist-lens program (the old range classifier already
   transplants a net into Isaac-style boxes — same machinery).
Shared doctrines, merged: slab everything (his 2048 lesson = my
batching rule); tiered precision (his 4-bit quantization where
courts tolerate it, 32-bit where ratios must hold); the card is
muscle, never judge, in both layouts; both views rebuild from the
record, own nothing.

*— design filed 2026-07-26; P0 (safe save + watcher) implemented
and live the same night; machine sizing added same day; old GPU
work reconciled same day (blind-design-first method, per owner).*
