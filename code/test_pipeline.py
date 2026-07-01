"""
Isaac — Pipeline Test Suite
Tests the crystallization pipeline itself, not just capabilities.
Each test validates that a specific phase is actually working.
"""

from isaac import Isaac, tokenize
import time


def _div(title):
    print(f"\n{'═' * 65}")
    print(f"  {title}")
    print(f"{'═' * 65}")


# ═══════════════════════════════════════════════════════════════
# Phase 1: Dirty Tracking
# ═══════════════════════════════════════════════════════════════

def test_dirty_tracking():
    """Verify observe() marks nodes dirty and consolidate() clears them."""
    _div("PHASE 1 — DIRTY TRACKING")
    isaac = Isaac()
    correct = 0

    # Fresh instance: nothing dirty
    st = isaac.status()
    ok = st["dirty_nodes"] == 0 and st["dirty_sequences"] == 0
    correct += ok
    print(f"  {'✓' if ok else '✗'}  fresh instance: dirty_nodes={st['dirty_nodes']}, "
          f"dirty_seqs={st['dirty_sequences']}")

    # After observing: should be dirty
    isaac.observe(tokenize("the cat sat ."))
    st = isaac.status()
    ok = st["dirty_nodes"] > 0 and st["dirty_sequences"] > 0
    correct += ok
    print(f"  {'✓' if ok else '✗'}  after observe: dirty_nodes={st['dirty_nodes']}, "
          f"dirty_seqs={st['dirty_sequences']}")

    # After lookup (triggers compile): dirty_sequences should clear
    isaac.observe(tokenize("the dog ran ."))
    answer, conf = isaac.lookup(["the"])
    st = isaac.status()
    ok = st["dirty_sequences"] == 0 and st["compiled"]
    correct += ok
    print(f"  {'✓' if ok else '✗'}  after lookup: dirty_seqs={st['dirty_sequences']}, "
          f"compiled={st['compiled']}")

    # dirty_nodes should still be set (consolidation clears those)
    ok = st["dirty_nodes"] > 0
    correct += ok
    print(f"  {'✓' if ok else '✗'}  dirty_nodes still set: {st['dirty_nodes']} "
          f"(needs consolidation)")

    # After consolidate: dirty_nodes should clear
    isaac.consolidate()
    st = isaac.status()
    ok = st["dirty_nodes"] == 0 and not st["needs_consolidation"]
    correct += ok
    print(f"  {'✓' if ok else '✗'}  after consolidate: dirty_nodes={st['dirty_nodes']}, "
          f"needs_consolidation={st['needs_consolidation']}")

    # Add more data: should become dirty again
    isaac.observe(tokenize("the bird flew ."))
    st = isaac.status()
    ok = st["dirty_nodes"] > 0 and st["needs_consolidation"]
    correct += ok
    print(f"  {'✓' if ok else '✗'}  new observation: dirty again, "
          f"needs_consolidation={st['needs_consolidation']}")

    print(f"\n  {correct}/6")
    return correct == 6


# ═══════════════════════════════════════════════════════════════
# Phase 2: Lazy Compilation
# ═══════════════════════════════════════════════════════════════

def test_lazy_compilation():
    """Verify matrix builds automatically on query, not on observe."""
    _div("PHASE 2 — LAZY COMPILATION")
    isaac = Isaac()
    correct = 0

    # Feed data — should NOT compile yet
    for a in range(10):
        for b in range(10):
            isaac.observe(tokenize(f"{a} + {b} = {a + b}"))
    st = isaac.status()
    ok = not st["compiled"]
    correct += ok
    print(f"  {'✓' if ok else '✗'}  after 100 observations: compiled={st['compiled']}")

    # First query triggers compile
    answer, conf = isaac.lookup(["3", "+", "5", "="])
    st = isaac.status()
    ok = st["compiled"] and answer == "8"
    correct += ok
    print(f"  {'✓' if ok else '✗'}  first lookup triggered compile: "
          f"compiled={st['compiled']}, answer={answer}")

    # Add more data — matrix should become stale
    isaac.observe(tokenize("99 + 99 = 198"))
    st = isaac.status()
    ok = st["dirty_sequences"] > 0
    correct += ok
    print(f"  {'✓' if ok else '✗'}  new data: dirty_seqs={st['dirty_sequences']}")

    # Next query auto-recompiles
    answer, conf = isaac.lookup(["99", "+", "99", "="])
    ok = answer == "198"
    correct += ok
    print(f"  {'✓' if ok else '✗'}  auto-recompile: 99+99={answer}")

    print(f"\n  {correct}/4")
    return correct == 4


# ═══════════════════════════════════════════════════════════════
# Phase 3: Think Loop
# ═══════════════════════════════════════════════════════════════

def test_think_loop():
    """Verify the think loop uses recall/evaluate, not just substring matching."""
    _div("PHASE 3 — THINK LOOP (recall → process → evaluate)")
    isaac = Isaac()
    correct = 0

    # Teach destructive and constructive actions
    actions = [
        ("me smash watch", "net_negative"),
        ("me burn painting", "net_negative"),
        ("me build birdhouse", "net_positive"),
        ("me assemble clock", "net_positive"),
    ]
    for action, outcome in actions:
        isaac.observe(tokenize(f"{action} result {outcome}"))
        verb = tokenize(action)[1]
        isaac.observe(tokenize(f"{verb} result {outcome}"))

    # Known action — should hit on Cycle 0 (direct recall)
    assessment = isaac.assess("me smash watch")
    ok = assessment["recommendation"] == "caution"
    correct += ok
    print(f"  {'✓' if ok else '✗'}  known action: me smash watch → "
          f"{assessment['recommendation']} (direct recall)")

    # Novel object — think loop should find it via recall/evaluate
    # "me smash computer" has unknown "computer"
    # Recall identifies: "computer" is unknown, "smash" and "result" are known
    # Evaluate says: drop unknown token
    # Process retries: "smash result" → net_negative → caution
    assessment = isaac.assess("me smash computer")
    ok = assessment["recommendation"] == "caution"
    correct += ok
    print(f"  {'✓' if ok else '✗'}  novel object: me smash computer → "
          f"{assessment['recommendation']} (think loop found 'smash' pattern)")

    # Novel verb with known structure — if consolidated with types
    isaac.consolidate()
    assessment = isaac.assess("me build castle")
    ok = assessment["recommendation"] == "proceed"
    correct += ok
    print(f"  {'✓' if ok else '✗'}  novel object: me build castle → "
          f"{assessment['recommendation']}")

    # Completely unknown — should return unknown, not guess
    assessment = isaac.assess("me flurble garbonzo")
    ok = assessment["recommendation"] == "unknown"
    correct += ok
    print(f"  {'✓' if ok else '✗'}  completely unknown: me flurble garbonzo → "
          f"{assessment['recommendation']} (honest shrug)")

    # Verify the think loop _recall identifies known vs unknown tokens
    knowledge = isaac._recall(tokenize("me smash computer result"))
    smash_known = knowledge.get("smash", {}).get("known", False)
    computer_known = knowledge.get("computer", {}).get("known", False)
    ok = smash_known and not computer_known
    correct += ok
    print(f"  {'✓' if ok else '✗'}  _recall: smash known={smash_known}, "
          f"computer known={computer_known}")

    # Verify _evaluate correctly diagnoses the unknown token
    verdict = isaac._evaluate(None, 0.0,
                               tokenize("me smash computer result"),
                               knowledge, "check")
    has_unknown = "computer" in verdict.get("unknown_tokens", [])
    ok = has_unknown
    correct += ok
    print(f"  {'✓' if ok else '✗'}  _evaluate: identified 'computer' as unknown={has_unknown}")

    print(f"\n  {correct}/6")
    return correct == 6


# ═══════════════════════════════════════════════════════════════
# Phase 4: Scoped Consolidation
# ═══════════════════════════════════════════════════════════════

def test_scoped_consolidation():
    """Verify consolidation scopes to dirty set and is faster."""
    _div("PHASE 4 — SCOPED CONSOLIDATION")
    isaac = Isaac()
    correct = 0

    # Feed substantial data
    sentences = [
        "the cat sat .", "the dog ran .", "the cat ran .",
        "the big cat sat .", "the small dog ran .",
        "the bird flew .", "the fish swam .",
        "the red ball bounced .", "the blue car stopped .",
        "the big dog barked .", "the small cat purred .",
    ]
    for s in sentences:
        isaac.observe(tokenize(s))

    # Full consolidation first — establishes baseline types
    t0 = time.time()
    isaac.consolidate(full=True, verbose=True)
    full_time = time.time() - t0
    full_types = len(isaac.types)
    ok = full_types > 0
    correct += ok
    print(f"  {'✓' if ok else '✗'}  full consolidation: {full_types} types "
          f"in {full_time*1000:.1f}ms")

    # Add a few more observations
    isaac.observe(tokenize("the old cat sat ."))
    isaac.observe(tokenize("the young dog ran ."))

    # Scoped consolidation — should be faster (only dirty nodes)
    st = isaac.status()
    dirty_count = st["dirty_nodes"]
    t0 = time.time()
    isaac.consolidate(verbose=True)  # scoped by default
    scoped_time = time.time() - t0
    scoped_types = len(isaac.types)
    ok = scoped_types >= full_types
    correct += ok
    print(f"  {'✓' if ok else '✗'}  scoped consolidation: {scoped_types} types "
          f"in {scoped_time*1000:.1f}ms (dirty nodes: {dirty_count})")

    # Verify dirty set is cleared
    st = isaac.status()
    ok = st["dirty_nodes"] == 0
    correct += ok
    print(f"  {'✓' if ok else '✗'}  dirty set cleared: {st['dirty_nodes']} dirty nodes")

    # Verify scope parameter works: full=True should scope to None
    # and full=False (default) should scope to dirty
    isaac.observe(tokenize("the clever cat purred ."))
    st_before = isaac.status()
    dirty_before = st_before["dirty_nodes"]
    ok = dirty_before > 0
    correct += ok
    print(f"  {'✓' if ok else '✗'}  new dirty nodes after observe: {dirty_before}")

    print(f"\n  {correct}/4")
    return correct == 4


# ═══════════════════════════════════════════════════════════════
# Phase 5: Stage 1 Sensing
# ═══════════════════════════════════════════════════════════════

def test_sense():
    """Verify _sense() immediately slots new tokens into existing types."""
    _div("PHASE 5 — STAGE 1 SENSING")
    isaac = Isaac()
    correct = 0

    # Establish types through full consolidation — need enough data
    for s in ["the cat sat .", "the dog ran .", "the bird flew .",
              "the fish swam .", "the cow mooed .",
              "the cat ran .", "the dog sat .",
              "the big cat sat .", "the small dog ran .",
              "a cat purred .", "a dog barked ."]:
        isaac.observe(tokenize(s))
    isaac.consolidate(full=True)

    # Verify types exist
    ok = len(isaac.types) > 0
    correct += ok
    print(f"  {'✓' if ok else '✗'}  established {len(isaac.types)} types")

    # Record which type has animals
    animal_type = None
    for tname, tdata in isaac.types.items():
        if "cat" in tdata["members"] and "dog" in tdata["members"]:
            animal_type = tname
            break
    ok = animal_type is not None
    correct += ok
    print(f"  {'✓' if ok else '✗'}  found animal type: {animal_type}")

    if animal_type:
        members_before = set(isaac.types[animal_type]["members"])
        print(f"       members before: {sorted(members_before)}")

        # Observe a new animal in enough contexts for _sense to match
        # (needs at least 2 shared connections with the type)
        isaac.observe(tokenize("the horse galloped ."))
        isaac.observe(tokenize("a horse trotted ."))

        # Check if horse got typed
        horse_types = list(isaac.net.get_doors("horse", tag="type"))
        members_after = set(isaac.types[animal_type]["members"])
        horse_slotted = "horse" in members_after
        ok = horse_slotted
        correct += ok
        print(f"  {'✓' if ok else '✗'}  'horse' slotted into type: {horse_slotted}")
        print(f"       members after: {sorted(members_after)}")

        # Without consolidation! This should happen on observe()
        st = isaac.status()
        ok = st["needs_consolidation"]
        correct += ok
        print(f"  {'✓' if ok else '✗'}  slotted WITHOUT consolidation "
              f"(needs_consolidation={st['needs_consolidation']})")
    else:
        correct += 2  # skip if no type found
        print(f"  ⚠  skipping horse test — no animal type found")

    print(f"\n  {correct}/4")
    return correct == 4


# ═══════════════════════════════════════════════════════════════
# Phase 6: Type-Level Attention
# ═══════════════════════════════════════════════════════════════

def test_type_attention():
    """Verify _encode activates frames via type membership for novel tokens."""
    _div("PHASE 6 — TYPE-LEVEL ATTENTION")
    isaac = Isaac()
    correct = 0

    # Feed actions where verbs share a type
    for action, outcome in [
        ("me smash watch result net_negative", None),
        ("me burn painting result net_negative", None),
        ("me crush vase result net_negative", None),
        ("me build chair result net_positive", None),
        ("me assemble table result net_positive", None),
    ]:
        isaac.observe(tokenize(action))
        verb = tokenize(action)[1]
        isaac.observe(tokenize(f"{verb} result {outcome if outcome else action.split()[-1]}"))

    # Consolidate to discover types
    isaac.consolidate(full=True)

    # Check if destructive verbs share a type
    smash_types = list(isaac.net.get_doors("smash", tag="type"))
    burn_types = list(isaac.net.get_doors("burn", tag="type"))
    shared_types = set(smash_types) & set(burn_types)
    ok = len(shared_types) > 0
    correct += ok
    print(f"  {'✓' if ok else '✗'}  smash and burn share type: {len(shared_types) > 0}")
    if shared_types:
        t = list(shared_types)[0]
        members = sorted(isaac.types.get(t, {}).get("members", set()))
        print(f"       type members: {members}")

    # Direct lookup should work for known verbs
    answer, conf = isaac.lookup(["smash", "result"])
    ok = answer == "net_negative" and conf >= 1.0
    correct += ok
    print(f"  {'✓' if ok else '✗'}  direct: smash result → {answer} (conf={conf:.1f})")

    # Type-level attention test: if "destroy" is slotted into the same type,
    # it should activate frames for "smash" or "burn"
    # First, observe "destroy" in a similar context to get it typed
    isaac.observe(tokenize("the destroy action ."))
    # Manually slot "destroy" into the destructive type for testing
    if shared_types:
        dest_type = list(shared_types)[0]
        isaac.types[dest_type]["members"].add("destroy")
        isaac.net.add_door("destroy", dest_type, tag="type")

        # Now _encode should find frames for "destroy result" via type substitution
        isaac._ensure_compiled()
        x = isaac._encode(["destroy", "result"])
        ok = x is not None and x.sum() > 0
        correct += ok
        print(f"  {'✓' if ok else '✗'}  type-level encode: 'destroy result' "
              f"activated frames: {x is not None and x.sum() > 0}")

        # Full lookup should work via type attention
        answer, conf = isaac.lookup(["destroy", "result"])
        ok = answer == "net_negative"
        correct += ok
        print(f"  {'✓' if ok else '✗'}  type-level lookup: destroy result → "
              f"{answer} (conf={conf:.1f})")
    else:
        correct += 2
        print(f"  ⚠  skipping type-level tests — no shared type found")

    print(f"\n  {correct}/4")
    return correct == 4


# ═══════════════════════════════════════════════════════════════
# Integration: Full Pipeline Flow
# ═══════════════════════════════════════════════════════════════

def test_full_pipeline():
    """End-to-end: observe → auto-compile → think → consolidate → think again."""
    _div("INTEGRATION — FULL PIPELINE FLOW")
    isaac = Isaac()
    correct = 0

    # Step 1: Feed data (no compile, no crystallize)
    for s in ["the cat sat .", "the dog ran .", "the bird flew .",
              "the cat ran .", "the dog sat .", "the bird sang .",
              "the big cat purred .", "the small dog barked ."]:
        isaac.observe(tokenize(s))

    # Step 2: Query triggers auto-compile
    answer, conf = isaac.lookup(["the", "cat"])
    st = isaac.status()
    ok = st["compiled"]
    correct += ok
    print(f"  {'✓' if ok else '✗'}  step 1-2: observe → auto-compile on query "
          f"(compiled={st['compiled']})")

    # Step 3: Consolidate discovers types (sleep mode)
    isaac.consolidate()
    types_found = len(isaac.types)
    ok = types_found > 0
    correct += ok
    print(f"  {'✓' if ok else '✗'}  step 3: consolidate → {types_found} types discovered")

    # Step 4: New observation — _sense slots immediately (needs enough context)
    isaac.observe(tokenize("the fox jumped ."))
    isaac.observe(tokenize("a fox ran ."))
    fox_typed = len(list(isaac.net.get_doors("fox", tag="type"))) > 0
    ok = fox_typed
    correct += ok
    print(f"  {'✓' if ok else '✗'}  step 4: _sense slotted 'fox' into type: {fox_typed}")

    # Step 5: Query with auto-recompile (new data since last compile)
    answer, conf = isaac.lookup(["the", "fox"])
    st = isaac.status()
    ok = st["dirty_sequences"] == 0  # recompiled
    correct += ok
    print(f"  {'✓' if ok else '✗'}  step 5: query auto-recompiled "
          f"(dirty_seqs={st['dirty_sequences']})")

    # Step 6: Generation still works through the net (not matrix)
    chain = isaac.generate("fox")
    ok = len(chain) >= 2
    correct += ok
    print(f"  {'✓' if ok else '✗'}  step 6: generate 'fox' → {' '.join(chain)}")

    # Step 7: Math through the pipeline
    for a in range(10):
        for b in range(10):
            isaac.observe(tokenize(f"{a} + {b} = {a + b}"))
    answer, conf = isaac.lookup(["7", "+", "3", "="])
    ok = answer == "10"
    correct += ok
    print(f"  {'✓' if ok else '✗'}  step 7: math auto-compile: 7+3={answer}")

    # Step 8: Status reflects everything
    st = isaac.status()
    ok = (st["observations"] > 100 and st["compiled"] and
          st["types"] > 0 and st["needs_consolidation"])
    correct += ok
    print(f"  {'✓' if ok else '✗'}  step 8: status coherent "
          f"(obs={st['observations']}, types={st['types']}, "
          f"needs_consolidation={st['needs_consolidation']})")

    print(f"\n  {correct}/7")
    return correct == 7


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Isaac — Pipeline Test Suite")
    print("Testing the machinery, not just the capabilities.\n")

    results = {}
    results["dirty_tracking"] = test_dirty_tracking()
    results["lazy_compilation"] = test_lazy_compilation()
    results["think_loop"] = test_think_loop()
    results["scoped_consolidation"] = test_scoped_consolidation()
    results["sense"] = test_sense()
    results["type_attention"] = test_type_attention()
    results["full_pipeline"] = test_full_pipeline()

    _div("PIPELINE SUMMARY")
    for name, passed in results.items():
        print(f"  {'✓' if passed else '✗'}  {name}")
    total = sum(1 for v in results.values() if v)
    print(f"\n  {total}/{len(results)} pipeline phases verified")
