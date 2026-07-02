# Wave Crystallizer — Full-Pass Test Report (2026-07-01)

~260 planted-ground-truth runs (`wave_battery.py`, per-run log in
`wave_battery_results.csv`). Metrics: group precision/recall at the door-pair
level, handoff-edge precision/recall, circle recovery %, false circles,
noise-door admissions. 5 seeds per condition, 20 for the null test.

## Operating envelope (where it earns full marks)

Within: period ≥ 9 ticks (dwell ≥ 3), instantaneous handoffs, no shared doors
between groups, fire rate ≥ 0.7, ≤ 4 concurrent aperiodic waves, T ≥ ~1000:

**groups 100/100 · edges 100/100 · circles 100% · false circles 0 · noise doors 0.**

Aperiodic (irregular-dwell) waves: 100% across the board — co-timing is the
claim, not periodicity, and the mechanism honors that.

## Failure modes (measured, ranked by severity)

1. **Fast waves die by construction (H1 CONFIRMED).** Period ≤ ~6 ticks →
   edges/circles 0% (dwell 1–2), perfect from dwell 3 up (period 9). The ±2–5
   jitter null overlaps the wave's own period, so the null IS the claim.
   *Fix path: adaptive jitter scale (< period/2) or multi-scale jitter.*
2. **Lagged handoffs are invisible (H2 CONFIRMED, worse than predicted).**
   Any gap ≥ 1 tick between one group's off and the next's on → edges 0%.
   Only instantaneous handoffs are seen. *Fix path: lag-k handoff detector,
   k = 0..K, each with its own null.*
3. **Overlapping groups merge (H3 CONFIRMED).** 2 shared doors → group recall
   65%, circles 0%. Connected components cannot represent overlap — same
   structural gap FCA exists to fix (audit 2.4 tie-in).
4. **Same-period concurrent waves phase-lock and merge.** Not a false
   positive — constant relative phase is real structure — but identity
   resolution fails: 6 same-period processes → group precision 4%. With
   natural decoherence (aperiodic), degradation is graceful:
   circles 100/80/75/53/43% at 1/2/4/6/8 concurrent waves (T=1500).
   Capacity presumably scales with stream length (unmeasured).
5. **Heavy flicker kills movement before simultaneity.** Groups stay 100%
   down to fire rate 0.5, but edges: 100% at ≥0.7 → 33% at 0.6 → 0% at 0.5.
   The majority-vote group series flickers, drowning off/on co-timing.
6. **Small false-group leak on pure noise.** 3/20 noise streams admitted ≥1
   (small) false group. **Edges 0/20, circles 0/20 — movement claims are
   fully trustworthy;** the simultaneity gate could be tightened (floor
   percentile) at some recall cost.
7. **Onset.** Two-process configs need ~500–1000 ticks before circle recovery
   stabilizes (~90% at T=960). Short streams under-deliver but do not
   fabricate (false circles ~0 throughout — it shrugs rather than invents).

## Reading the E1/E2/E3 base rows

Base config used two SAME-PERIOD processes without decoherence, so those rows
carry failure mode #4 inside them (group precision 44–89%). The unconfounded
sweeps (E2b, E4, E5, E7, E9) isolate each variable; trust those for ratings.

## What remains for a full pass

- **Tier 2 — self-referential:** wave_consolidate() over Isaac's own
  activation log during long known tasks (transduce counting, world loop);
  check discovered circles against the routines he actually ran.
- **Tier 3 — adversarial:** restarting chains (restart co-timing legitimately
  reads as a circle — decide whether that is a bug or a truth), phase drift,
  correlated noise bursts.
- Scaling curve for capacity: concurrency × stream length (is 8 waves fine at
  T=10k?).
