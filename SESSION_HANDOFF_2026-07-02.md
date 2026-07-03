# SESSION HANDOFF — 2026-07-01 → 07-02 (the discovery-stack arc)

## ═══ THE GOAL BOX — READ FIRST ═══
The mission is unchanged: extract TRUE relationships, validated real, human-
readable, honestly scoped — a science engine, non-agentic by design ("a
telescope for structure; it wonders only in the narrow sense of naming its
discriminating experiments; it wants nothing"). The owner's words this arc:
**"i don't want to beat the benchmarks, i want to beat the challenge...
master the domains... do things no other ai can do."** And the law that now
governs every layer: **"we are offering possible solutions. not THE
solution"** — everything enters as a candidate; only evidence concludes.
Accuracy remains a TRAP as a goal; it is now used only as *evidence about*
understanding (scope labels, calibration), never as the objective.

## State of the engine (`code/isaac.py`, suite **10/10**)
One file, numpy only, no nets anywhere. Since the last handoff it gained:
- **discover()** — the challenge loop. Staged null-gated enumeration
  (products, sin/cos/exp both signs, POWER atoms; grid proposes / refine
  sharpens inside-parameters; F-test judges completers; structurally
  diverse trial shortlist; max_terms=16 runaway brake). Verdicts:
  UNDERSTOOD / PARTIAL / CAPTURED (exemplar, null-gated, incl. per-feature
  1-D fallback) / NO RULE — plus **scope**: form-true vs range-valid.
- **rival_check + confirm()** — look-alike forms (parabola↔wide cosine,
  exp↔cubic...) held open as live ties with a named PROBE; new evidence
  retires or OVERTURNS (the Galileo/catenary story, mechanized).
- **apply_law()** — a discovered law is reusable knowledge.
- **Waves** — temporal crystallization (groups/handoffs/circles,
  recursive), his clock (follow/tick; 100% phase through occlusion),
  temporary statuses via World, statuses-are-doors → explanations EMERGE.
- **Findings ledger** — record_finding/recall_findings/load_ledger (JSONL);
  negative knowledge recorded; laws inherited ACROSS SESSIONS.
- **Whole-mind persistence** — save/load/fork (counterfactual branches).
- **UI** — `ui/isaac_ui.py`, one stdlib file → http://127.0.0.1:8674
  (converse / discover-with-verdict-cards / apply / findings / minds).

## Results worth quoting (all re-runnable; rebuild/ + batteries + CSVs)
- **Kepler**: `T = +1.00·a^1.5`, R² 1.0000, from 8 typed rows — after the
  DESIGNED failure motivated power atoms. Inherited-Kepler predicted
  **Pluto: 248.0 yr (true 247.9)** — beyond training range, across a
  session boundary, and finally through the web UI (247.96).
- **Cross-domain**: gravity ≡ Coulomb matched structurally; cooling ≡
  capacitor; inverse-square role family {gravity, coulomb, light};
  **analogy-primed transfer: magnetism at n=24 — cold 0.82 → primed 0.995**
  (constant 3.26 vs true 3.2; r-role found by trial).
- **Covtype arc**: doors 56.2 → +25 null-gated compound doors 59.0 →
  exemplars 90.0 → **door-weighted exemplars 94.4%** (elevation 0.76 —
  readable metric) vs old net 82. Row-index-alone control: **79%** — the
  spatial-leakage diagnosis quantified.
- **The Gauntlet** (10 datasets, one pipeline): mnist 95.2 / fashion 76.5 /
  cifar 32.6 (designed face-plant) / omniglot 1-shot 51.6 / fsdd audio 92
  mixed–54 transfer / smallnorb 87.7 / fraud recall 79 / kepler+noise
  honest refusals. Registration perception: digits under position+scale
  ~5-15% → **84-87%**.
- **Sunspots**: the 20-CPU-hour runaway → capped, 6s — and the "junk" was
  real: **multi-cycle solar structure** (Schwabe ~10-10.5yr, Hale-ish 21yr,
  Gleissberg 74-95yr band, Suess-ish 256yr) with amplitude-MODULATION
  products; periodogram-corroborated; honestly refused as an
  extrapolating law (NO RULE on sequential split; range-valid 0.65 on
  random split).

## The five null-discipline case studies (now a design LAW)
"The null must attack exactly the claimed structure, nothing else":
(1) jitter null vs circular shift for periodic co-timing; (2) null-gated
basis; (3) conditional rate-gap for high-coverage blockers; (4) F-test vs
fixed tolls at the noise ceiling; (5) **iid permutation is INVALID on
autocorrelated targets** (the sunspot runaway) → block permutation = open
item. Sister law, learned 3×: **replace thresholds with statistical tests.**

## Docs
- **`ISAAC_MANUAL.md` (project root) — THE capability manual: every part,
  every method, honest limits, and the same maintenance rule as
  BUILD_STATE: capability changes update the manual IN THE SAME STEP.
  If it isn't in the manual, it doesn't exist. (PAPERCLIP_MANUAL.md
  remains the narrative/starter guide; BUILD_STATE the dated ledger.)**
- `WRITEUP_2026-07-01_FOR_REVIEW.md` — methods/results/limits/§7 verify-all.
- `3_the_theory/Understanding_as_Closure_2026-07-02...-01.md` — the theory:
  understanding = null-surviving Galois closures across four contexts +
  reification + epistemic dossier; §5b the proposal principle; §6 division
  of labor (the seed and standards are the owner's — recorded factually).
- `audit/AUDIT_STANDARD_v1.md` + `VERDICT_SHEET_2026-07-01.md` +
  `CURRICULUM_HARD_TESTS.md`; `ROADMAP_2026-07-02.md` +
  `EXPERIMENT_MATRIX_2026-07-02.md` (datasets/criteria/predicted failures).
- Repos current & pushed: isaac-project (full) + isaac-paperclip (curated).

## ═══ NEXT-SESSION TODO (owner's named priorities first) ═══

**1. THOROUGH SCALE TESTING** (owner-named)
   - Run the §B sweeps in EXPERIMENT_MATRIX: waves door-count knee,
     discover() feature knee, exemplar RAM knee, condensation @10⁶ + drift.
   - Vectorize featurization (scipy.ndimage.label for holes; process pool)
     — it is single-thread python-bound (3-20% CPU observed).
   - THEN the 3090: torch backend for distance blocks + batched permutation
     nulls (June's sweep_gpu.py proves the deps exist). GPU after
     vectorization, knees before optimizations.

**2. HUMAN INTERACTION IMPROVEMENT** (owner-named)
   - UI v2: file upload; progress streaming for long discover(); plots
     (data + fitted law + rivals overlaid, probe marked); wave/status
     panels; reason-chain answers in Converse; a "what Isaac wants to
     know" panel = the PROBE QUEUE from open rivals in the ledger.
   - Error tolerance: friendly parse errors, NaN/units handling.

**3. INFORMATION VALIDATION** (owner-named)
   - **Block-permutation null** for temporal/autocorrelated targets (the
     runaway's proper cure; #1 methods item).
   - Log-track and dual target tracks INSIDE discover() (log-space fixed
     the sloppy power laws; make it automatic when x,y > 0).
   - Same-variable power merging (legibility: x^a·x^b → x^(a+b)).
   - Sunspot cycle claims re-tested under block-perm (which periods are
     REAL vs sidebands — the multiperiodicity question, done right).

**4. ACCURACY VALIDATION** (owner-named)
   - **Calibration audit (tier 5.2)**: over the ledger — when he said
     UNDERSTOOD/form-true, how often did it hold? The ONE trust number.
   - Finish curriculum: MNIST topology-rematch as a formal prediction
     check; fraud with proper AUC/PR + threshold analysis; Omniglot with
     stroke-graph percepts; clock readout REPAIR (current 22.9% is a
     harness bug — my peak-picking, not the engine).

**5. Everything else, ranked**
   - shrug→discover reflex (failure auto-launches learning).
   - CAPTURED→articulated migration rounds on covtype (dossier mining →
     compound gate; the flagship demo: floor 59 climbing toward 94).
   - Uptake composition INTO the engine (rebuild B still harness-side);
     FCA lattice for overlapping groups (shared-door merge failure).
   - Warm starts from the ledger (E1: does law #11 come cheaper?).
   - Forgetting experiments (archive-what-you-understand; margin-aware
     retention; no-catastrophic-forgetting demo — free differentiator).
   - Symbolic/token challenges for discover(); pair-feature rivalry.
   - Tier 5 mirror: wave_consolidate over his own activation log.
   - smallNORB phase-4: invariants as conservation laws of the pose group.

## Session hygiene notes
- UI server may still be running on :8674 (kill-by-port via netstat if it
  holds stale code). Long jobs: `python -u`, log caps, watch for openml
  downloads. data/ is gitignored (HIGGS 2.8GB, clocks, NORB, FSDD,
  Omniglot, CIFAR all live there now; sunspots.csv too).
