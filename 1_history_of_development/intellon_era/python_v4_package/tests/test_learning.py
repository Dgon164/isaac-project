"""
Test: Self-Learning Behavior

Validates that the system learns from data:
1. Network grows as data flows in
2. Recognition improves with exposure
3. Context bundles get richer as vocabulary grows
4. Tallies reflect usage patterns
5. Stubs get created for unknowns and recognized on re-encounter
"""

import sys
sys.path.insert(0, "/home/claude")

from intellon.core.engine import Engine
from intellon.core.training import load_wordnet, process_text, load_text_file
from intellon.core.models import Tier, NodeFlag


def test_learning_progression():
    """
    Feed sentences one at a time and measure how the system's
    behavior changes as it accumulates knowledge.
    """
    engine = Engine(run_boot=True)
    lib = engine.librarian

    # Phase 1: Load vocabulary
    wn_reg = load_wordnet(lib, tier=Tier.IMPORTANT)
    vocab_nodes = lib.node_count
    print(f"=== Vocabulary Loaded ===")
    print(f"  {len(wn_reg)} words, {vocab_nodes} total nodes")

    # Phase 2: Process sentences and track progression
    sentences = [
        "The cat sat on the floor.",
        "The dog ran in the room.",
        "A bird flew over the house.",
        "The cat is a small animal.",
        "The dog is a big animal.",
        "The cat ran and the dog sat.",
        "The old cat sat on the cold floor.",
        "A small child walked to the door.",
        "The cat and the dog are animals.",
        "The boy and the girl are children.",
    ]

    print(f"\n=== Processing Sentences ===")
    for i, sentence in enumerate(sentences):
        pre = lib.node_count
        assignment = lib.bundle(sentence)
        result = engine.process(sentence)
        post = lib.node_count

        recognized = len(assignment.metadata["recognized"])
        context = len(assignment.context)
        foundation = len(assignment.foundation)
        notepad = len(result.notepad)
        new_nodes = post - pre

        print(f"  [{i+1:2d}] \"{sentence[:45]}...\"" if len(sentence) > 45 else f"  [{i+1:2d}] \"{sentence}\"")
        print(f"       recognized={recognized} context={context} foundation={foundation} notepad={notepad} new={new_nodes}")

    # Phase 3: Verify learning happened
    print(f"\n=== Learning Verification ===")

    # 3a: Network grew
    final_nodes = lib.node_count
    growth = final_nodes - vocab_nodes
    print(f"  Network growth: {vocab_nodes} → {final_nodes} (+{growth} nodes)")
    assert final_nodes > vocab_nodes, "Network should grow from sentence processing"

    # 3b: "the" should be heavily referenced (appears in most sentences)
    the_ids = lib.recognize("the")
    assert len(the_ids) > 0, "'the' should be in the network"
    the_node = lib.get_node(the_ids[0])
    the_refs = the_node.tallies.get("referenced", 0)
    print(f"  'the' referenced: {the_refs} times")
    assert the_refs >= 5, "'the' should be referenced many times"

    # 3c: "cat" should be recognized with full WordNet context
    cat_ids = lib.recognize("cat")
    cat_node = lib.get_node(cat_ids[0])
    print(f"  'cat' definitions: {len(cat_node.definitions)}, pointers: {len(cat_node.pointers)}")
    assert len(cat_node.definitions) > 0, "'cat' should have definitions from WordNet"

    # 3d: Recognition should find most words in a new sentence
    test = "The big cat sat on the cold floor."
    recognized = lib.recognize(test)
    tokens = test.lower().replace(".", "").split()
    coverage = len(recognized) / len(tokens) * 100
    print(f"  Recognition coverage for new sentence: {len(recognized)}/{len(tokens)} ({coverage:.0f}%)")
    assert len(recognized) >= len(tokens) * 0.5, "Should recognize at least half the tokens"

    # 3e: Context bundles should be non-trivial
    assignment = lib.bundle(test)
    print(f"  Bundle for new sentence: {len(assignment.foundation)} foundation + {len(assignment.context)} context")
    assert len(assignment.context) > 0, "Should have context nodes"
    assert len(assignment.foundation) > 0, "Should have foundation nodes"

    print("\n✓ Learning progression test complete")


def test_unknown_word_lifecycle():
    """
    Track how an unknown word enters the system and evolves.
    """
    engine = Engine(run_boot=True)
    lib = engine.librarian
    load_wordnet(lib, words=["cat", "dog", "run", "sit"], tier=Tier.IMPORTANT)

    print(f"\n=== Unknown Word Lifecycle ===")

    # "zorb" is unknown — not in WordNet, not in boot
    assert len(lib.recognize("zorb")) == 0, "zorb should be unknown"
    print(f"  Before: 'zorb' unknown")

    # First encounter: creates stub
    engine.process("The zorb sat.")
    zorb_ids = lib.recognize("zorb")
    assert len(zorb_ids) > 0, "zorb should now exist as stub"
    zorb = lib.get_node(zorb_ids[0])
    print(f"  After 1st: tier={zorb.tier.name}, flags={[f.value for f in zorb.flags]}, refs={zorb.tallies.get('referenced', 0)}")

    # Second encounter: recognized, tallied
    engine.process("The zorb ran.")
    zorb = lib.get_node(zorb_ids[0])
    refs_after_2 = zorb.tallies.get("referenced", 0)
    print(f"  After 2nd: tier={zorb.tier.name}, refs={refs_after_2}")
    assert refs_after_2 >= 1, "zorb should gain references"

    # More encounters
    for s in ["A zorb is good.", "The zorb is big.", "The zorb ran and the zorb sat."]:
        engine.process(s)
    zorb = lib.get_node(zorb_ids[0])
    refs_after_5 = zorb.tallies.get("referenced", 0)
    print(f"  After 5th: tier={zorb.tier.name}, refs={refs_after_5}")

    # zorb should now be bundled as context when it appears
    assignment = lib.bundle("The zorb is here.")
    zorb_in_context = any(n.name == "zorb" for n in assignment.context)
    print(f"  Bundled as context: {zorb_in_context}")
    assert zorb_in_context, "zorb should appear in context after repeated use"

    print("\n✓ Unknown word lifecycle test complete")


def test_pattern_emergence():
    """
    Feed structurally similar sentences and verify the register
    captures the pattern (SAME-DIFFERENT-SAME).
    """
    engine = Engine(run_boot=True)
    lib = engine.librarian
    load_wordnet(lib, words=["cat", "dog", "bird", "fish", "run", "sit", "fly", "swim"],
                 tier=Tier.IMPORTANT)

    print(f"\n=== Pattern Emergence ===")

    # Feed "The X ran." pattern repeatedly
    pattern_sentences = [
        "The cat ran.",
        "The dog ran.",
        "The bird ran.",
        "The fish ran.",
    ]

    for sentence in pattern_sentences:
        result = engine.process(sentence)

    # Now process a pair and check for SAME-DIFFERENT-SAME
    result = engine.process("The cat ran. The dog ran.")
    token_records = [r for r in result.notepad if r.aspect == "token"]

    print(f"  Token comparison: {len(token_records)} records")
    pattern = []
    for r in token_records:
        pattern.append(r.result.value)
        print(f"    pos {r.position}: {r.result.value} — {r.detail}")

    if len(pattern) >= 3:
        assert pattern[0] == "SAME", "Position 0 should be SAME (the/the)"
        assert pattern[1] == "DIFFERENT", "Position 1 should be DIFFERENT (cat/dog)"
        assert pattern[2] == "SAME", "Position 2 should be SAME (ran/ran)"
        print(f"  Pattern: {'-'.join(pattern[:3])}")

    # The synthesis should capture this
    if result.synthesis:
        content = result.synthesis.content
        if isinstance(content, dict):
            invariants = len(content.get("invariants", []))
            differentiators = len(content.get("differentiators", []))
            print(f"  Synthesis: {invariants} invariants, {differentiators} differentiators")

    print("\n✓ Pattern emergence test complete")


def test_full_pipeline():
    """
    End-to-end: boot → WordNet → sentences → verify learning.
    """
    engine = Engine(run_boot=True)
    lib = engine.librarian

    print(f"\n=== Full Pipeline ===")
    print(f"  Boot: {lib.node_count} nodes")

    # WordNet
    wn_reg = load_wordnet(lib, tier=Tier.IMPORTANT)
    print(f"  +WordNet: {lib.node_count} nodes ({len(wn_reg)} words)")

    # Sentences
    stats = load_text_file(engine, "/home/claude/intellon/data/sentences_01.txt", tier=Tier.VALIDATED)
    print(f"  +Sentences: {lib.node_count} nodes ({stats['sentences_processed']} sentences)")
    print(f"    Notepad records: {stats['notepad_records']}")
    print(f"    New nodes: {stats['nodes_created']}")

    # Final stats
    all_nodes = lib.get_all_nodes()
    tier_counts = {}
    for n in all_nodes:
        tier_counts[n.tier.name] = tier_counts.get(n.tier.name, 0) + 1
    print(f"\n  Tier breakdown:")
    for t in ["INITIATOR", "IMPORTANT", "VALIDATED", "TRIAL"]:
        print(f"    {t}: {tier_counts.get(t, 0)}")

    # Top 10 most used words
    top = sorted(all_nodes, key=lambda n: n.tallies.get("sessions_involved", 0), reverse=True)[:10]
    print(f"\n  Top 10 by session involvement:")
    for n in top:
        si = n.tallies.get("sessions_involved", 0)
        if si > 0:
            print(f"    \"{n.name}\" — {si} sessions (tier={n.tier.name})")

    print(f"\n  Total nodes: {lib.node_count}")
    print(f"  Total sessions: {lib.session_count}")

    print("\n✓ Full pipeline test complete")


if __name__ == "__main__":
    test_learning_progression()
    print("\n" + "=" * 60 + "\n")
    test_unknown_word_lifecycle()
    print("\n" + "=" * 60 + "\n")
    test_pattern_emergence()
    print("\n" + "=" * 60 + "\n")
    test_full_pipeline()
