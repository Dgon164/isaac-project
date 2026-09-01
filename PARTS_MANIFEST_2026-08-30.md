# THE PARTS MANIFEST — Isaac v1 alpha
**2026-08-30. The owner's completeness criterion: "all the parts for an AGI,
implemented. they dont have to be good, but they have to be present and
functional." This table is that claim, made checkable: every part → where it
lives → the court that proves it functions → its honest grade. The full gate
(`python rebuild/run_gates.py --slow --jobs 0`) runs every court: 17/17 PASS,
93.8s, this commit.**

| # | part | where it lives | court (gate row) | grade |
|---|---|---|---|---|
| 1 | Perception / input | observe(), ingest(), read via talk.py | battery, worstcase | functional (text; numeric via discover; barcode/vision = parked seed) |
| 2 | The log (layer 1) | observed_sequences, append-only | onefile courts, parts_courts | solid |
| 3 | The net (layer 2) | graph + column-sparse table | battery, scale_eval, cloth | solid at current scale |
| 4 | The facts layer (layer 3) | facts store: origin-stamped typed claims, ground vs rule kinds | parts_courts | functional, new |
| 5 | Learning | observe→consolidate→compile; every-prefix counts | battery, scale_eval | solid |
| 6 | Recall / answering | lookup/check/topk/cloze + stranger guards | scale_eval, selection, cloth | solid; verbatim-shaped (known) |
| 7 | Multi-step reasoning | reducer (taught precedence, exact-fact gate) | pemdas | functional; fallback declared built-in |
| 8 | Native composition search | s0 probe (bidirectional, certified resolve) | s0_composition_probe | **experiment WON: 100/100 fwd, 20/20 reverse** — probe-grade, engine integration next |
| 9 | Outsourced inference | ask_logic: facts+admitted rules → clingo → independent replay → CERTIFIED / SOLVER-DERIVED | ask_logic_court, bridge probes | functional; rule admission carries trust (boundary red-lettered) |
| 10 | Law consistency | z3 scan over the findings ledger; conflicts become findings | z3_law_scan | functional |
| 11 | Discovery (science) | discover(): nulls, held-out, rivals, verdicts | battery discovery+rivalry | solid — the exemplar subsystem |
| 12 | Self-questions | ask queue: every refusal files a deduped ask | parts_courts | functional, new |
| 13 | Feedback (world half) | correlation binder: acts+responses bind by recurrence over background null, fused episodes | binder_court | functional, v1 null |
| 14 | Feedback (grades) | good/marginal/bad on answers + connections | selection_feedback | functional; generalization limited (known) |
| 15 | Self-challenge | playland: 4 game modes under the quarantine law | playland_court (leak probe) | functional, new |
| 16 | Goals / planning A→B | seek() over act nodes, standing plans | battery boot section | functional (flow-level) |
| 17 | Consequence assessment | assess() → proceed/caution/unknown | battery persistence | functional |
| 18 | Generation | generate(): most-traveled doors | worstcase gen-truth | functional, truth-checked |
| 19 | Persistence / body | one-file v2, journal format, torn-tail recovery | onefile courts | solid (journal wiring still DESIGNED) |
| 20 | Interface | talk.py: teach/ask/logic/asks/play/grade/why | smoke-tested; roads stamped | functional |
| 21 | Honesty machinery | refusals w/ named reasons, receipts, claim scoping, wrongs kept | every court; W7 rule | the identity — enforced by exit codes |
| 22 | The gate itself | run_gates.py: 17 rows, exit code = verdict | mutation-verified | solid |

**Not parts of v1 (named open experiments, on the record):** schema induction under
a cost curve (the Cyc bet); unseen-text comprehension; mechanism-strata rules; the
ledger/collider working space (W-phase, needs the Def 1.5/1.8 amendments signed);
barcode grounding curriculum (parked seed).

**The loop, closed:** perceive → log → derive → answer (recall → reduce → search →
solver → refuse) → refusals file asks → asks drive seeking and solver trips →
certified answers land in the facts layer → world responses bind by correlation →
grades adjust rankings → play manufactures practice when the world is quiet →
consolidate → again.
