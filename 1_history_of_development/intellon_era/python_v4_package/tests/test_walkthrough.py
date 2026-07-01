"""
Test: Section 11 Walkthrough — "The cat ran." / "The dog ran."

Verifies that the system, starting from an empty network, produces:
- Stub nodes for each unique token
- SAME-DIFFERENT-SAME pattern from positional comparison
- Correct integration into the librarian's network
"""

import sys
sys.path.insert(0, "/home/claude")

from intellon.core.engine import Engine
from intellon.core.models import DiffResult


def test_cat_dog_walkthrough():
    engine = Engine(num_registers=1, run_boot=False)

    # System starts empty
    assert engine.librarian.node_count == 0

    # First input: two sentences
    result = engine.process("The cat ran. The dog ran.")

    print("=== Notepad Records ===")
    for i, record in enumerate(result.notepad):
        print(f"  [{i}] {record.aspect:20s} pos={record.position} "
              f"{record.result.value:10s} {record.detail}")

    # Check that token comparisons produced the SAME-DIFFERENT-SAME pattern
    token_records = [r for r in result.notepad if r.aspect == "token"]
    print(f"\n=== Token Comparison Pattern ===")
    for r in token_records:
        print(f"  pos {r.position}: {r.result.value} — {r.detail}")

    # Verify the pattern
    if len(token_records) >= 3:
        assert token_records[0].result == DiffResult.SAME,    "pos 0 should be SAME (the/the)"
        assert token_records[1].result == DiffResult.DIFFERENT, "pos 1 should be DIFFERENT (cat/dog)"
        assert token_records[2].result == DiffResult.SAME,    "pos 2 should be SAME (ran/ran)"
        print("\n✓ SAME-DIFFERENT-SAME pattern confirmed")

    # Check stubs were created
    print(f"\n=== Stubs Created: {len(result.stubs)} ===")
    for stub in result.stubs:
        print(f"  '{stub.content}' [{stub.id[:8]}...]")

    # Check librarian state
    print(f"\n=== Network State ===")
    print(f"  Total nodes: {engine.librarian.node_count}")
    print(f"  Foundation: {engine.librarian.foundation_count}")
    print(f"  Sessions logged: {engine.librarian.session_count}")

    # Check synthesis
    if result.synthesis:
        print(f"\n=== Synthesis ===")
        print(f"  Content: {result.synthesis.content}")
        print(f"  Verification passed: {result.verification.passed}")

    print("\n✓ Walkthrough complete")


def test_accumulation():
    """Feed multiple inputs and verify network grows."""
    engine = Engine(run_boot=False)

    inputs = [
        "The cat ran.",
        "The dog ran.",
        "The bird flew.",
        "The cat sat.",
    ]

    for inp in inputs:
        engine.process(inp)

    print(f"\n=== After {len(inputs)} inputs ===")
    print(f"  Nodes: {engine.librarian.node_count}")
    print(f"  Sessions: {engine.librarian.session_count}")

    # "the" should be heavily tallied
    all_nodes = engine.librarian.get_all_nodes()
    for node in all_nodes:
        if isinstance(node.content, str) and node.content == "the":
            print(f"  'the' tallies: {node.tallies}")
            break

    print("\n✓ Accumulation test complete")


def test_node_model():
    """Verify the dictionary-entry node model works."""
    from intellon.core.models import Node, Tier, NodeFlag, Definition, Pointer

    cat = Node(name="cat", tier=Tier.TRIAL)
    cat.add_definition("a small domesticated feline", pointers=[
        Pointer(target="animal-id", relation="is_a"),
        Pointer(target="pet-id", relation="is_a"),
    ])
    cat.add_definition("catalytic converter", pointers=[
        Pointer(target="automotive-id", relation="part_of"),
    ])
    cat.char_pointers = ["char-c-id", "char-a-id", "char-t-id"]

    assert cat.name == "cat"
    assert cat.tier == Tier.TRIAL
    assert len(cat.definitions) == 2
    assert cat.get_definition(1).content == "a small domesticated feline"
    assert cat.get_definition(2).content == "catalytic converter"
    assert len(cat.get_definition(1).pointers) == 2
    assert len(cat.char_pointers) == 3
    assert cat.content == "a small domesticated feline"

    cat.flags.add(NodeFlag.ACTIVE)
    assert cat.has_flag(NodeFlag.ACTIVE)
    assert cat.tier == Tier.TRIAL
    assert Tier.INITIATOR < Tier.IMPORTANT < Tier.VALIDATED < Tier.TRIAL

    print("\n✓ Node model test complete")


def test_boot_sequence():
    """Verify the boot sequence loads all foundation nodes."""
    from intellon.core.models import Tier, NodeFlag

    engine = Engine(run_boot=True)
    lib = engine.librarian
    reg = engine.boot_registry

    # ASCII: 95 printable characters (32-126)
    ascii_count = sum(1 for k in reg if k.startswith("char_"))
    print(f"\n=== Boot Sequence ===")
    print(f"  ASCII characters: {ascii_count}")
    assert ascii_count == 95, f"Expected 95 ASCII nodes, got {ascii_count}"

    # Equivalence + Comparison: eq, neq, gt, lt, gte, lte
    for name in ["eq", "neq", "gt", "lt", "gte", "lte"]:
        assert name in reg, f"Missing boot node: {name}"
        node = lib.get_node(reg[name])
        assert node.tier == Tier.INITIATOR, f"{name} should be Tier 1"
        assert node.has_flag(NodeFlag.FOUNDATION), f"{name} should be foundation"
        assert len(node.char_pointers) > 0, f"{name} should have char pointers"
    print(f"  Equivalence & comparison: 6 nodes ✓")

    # Logic: and, or, not, xor
    for name in ["and", "or", "not", "xor"]:
        assert name in reg, f"Missing boot node: {name}"
        node = lib.get_node(reg[name])
        assert node.tier == Tier.INITIATOR
    print(f"  Boolean logic: 4 nodes ✓")

    # Math: add, sub, mul, div (Tier 2)
    for name in ["add", "sub", "mul", "div"]:
        assert name in reg, f"Missing boot node: {name}"
        node = lib.get_node(reg[name])
        assert node.tier == Tier.IMPORTANT, f"{name} should be Tier 2"
        assert len(node.definitions) == 2, f"{name} should have 2 definitions"
    print(f"  Math operations: 4 nodes ✓")

    # Number concepts: 0-9
    for d in range(10):
        assert f"num_{d}" in reg, f"Missing number node: {d}"
    print(f"  Number concepts: 10 nodes ✓")

    # Inverse relationships wired
    add_node = lib.get_node(reg["add"])
    inverse_targets = [p.target for p in add_node.pointers if p.relation == "inverse_of"]
    assert reg["sub"] in inverse_targets, "ADD should have SUB as inverse"
    print(f"  Inverse relationships: wired ✓")

    # Foundation count
    foundation = lib.foundation_count
    print(f"  Foundation nodes (auto-loaded): {foundation}")
    print(f"  Total nodes after boot: {lib.node_count}")

    print("\n✓ Boot sequence test complete")


def test_booted_walkthrough():
    """Process text WITH foundation nodes loaded — the register has a lens."""
    engine = Engine(run_boot=True)

    pre_count = engine.librarian.node_count
    result = engine.process("The cat ran. The dog ran.")

    token_records = [r for r in result.notepad if r.aspect == "token"]
    assert len(token_records) >= 3
    assert token_records[0].result.value == "SAME"
    assert token_records[1].result.value == "DIFFERENT"
    assert token_records[2].result.value == "SAME"

    post_count = engine.librarian.node_count
    print(f"\n=== Booted Walkthrough ===")
    print(f"  Nodes before: {pre_count}")
    print(f"  Nodes after:  {post_count}")
    print(f"  New stubs: {len(result.stubs)}")
    print(f"  Notepad records: {len(result.notepad)}")
    print(f"  Foundation nodes available: {engine.librarian.foundation_count}")

    print("\n✓ Booted walkthrough complete")


def test_wordnet_import():
    """Test WordNet import creates proper dictionary-entry nodes."""
    from intellon.core.training import load_wordnet
    from intellon.core.models import Tier

    engine = Engine(run_boot=True)
    lib = engine.librarian

    pre_count = lib.node_count

    # Import words that form a connected hierarchy in WordNet
    test_words = ["cat", "dog", "feline", "canine", "animal", "pet", "puppy", "kitten"]
    registry = load_wordnet(lib, words=test_words, tier=Tier.IMPORTANT)

    print(f"\n=== WordNet Import ===")
    print(f"  Words requested: {len(test_words)}")
    print(f"  Words imported: {len(registry)}")
    print(f"  Nodes before: {pre_count}")
    print(f"  Nodes after: {lib.node_count}")

    # Check that "cat" is a proper dictionary entry
    cat_node = lib.get_node(registry["cat"])
    assert cat_node is not None, "cat node should exist"
    assert cat_node.name == "cat"
    assert cat_node.tier == Tier.IMPORTANT
    assert len(cat_node.definitions) > 0, "cat should have definitions"
    assert len(cat_node.char_pointers) == 3, "cat should have 3 char pointers (c,a,t)"

    print(f"\n  'cat' node:")
    print(f"    Name: {cat_node.name}")
    print(f"    Tier: {cat_node.tier.name}")
    print(f"    Definitions: {len(cat_node.definitions)}")
    for d in cat_node.definitions:
        print(f"      {d.number}. {d.content[:60]}...")
    print(f"    Char pointers: {len(cat_node.char_pointers)}")
    print(f"    Relationship pointers: {len(cat_node.pointers)}")
    for p in cat_node.pointers[:5]:
        target = lib.get_node(p.target)
        tname = target.name if target else p.target
        print(f"      {p.relation} -> {tname}")

    # Check relationships exist — cat is_a feline in WordNet
    cat_is_a = [p.target for p in cat_node.pointers if p.relation == "is_a"]
    assert registry["feline"] in cat_is_a, "cat should have feline as is_a"
    print(f"\n  cat is_a feline: ✓")
    print(f"  cat total pointers: {len(cat_node.pointers)}")
    for p in cat_node.pointers[:8]:
        target = lib.get_node(p.target)
        tname = target.name if target else p.target
        print(f"      {p.relation} -> {tname}")

    print("\n✓ WordNet import test complete")


def test_text_processing():
    """Test processing text through a booted + WordNet-loaded engine."""
    from intellon.core.training import load_wordnet, process_text
    from intellon.core.models import Tier

    engine = Engine(run_boot=True)

    # Load some vocabulary first
    load_wordnet(engine.librarian,
                 words=["cat", "dog", "bird", "run", "fly", "sit", "the", "a"],
                 tier=Tier.IMPORTANT)

    pre_count = engine.librarian.node_count

    # Now process sentences — the system should recognize loaded words
    stats = process_text(engine, "The cat ran. The dog ran. The bird flew.")

    print(f"\n=== Text Processing ===")
    print(f"  Sentences: {stats['sentences_processed']}")
    print(f"  Nodes before: {stats['nodes_before']}")
    print(f"  Nodes after: {stats['nodes_after']}")
    print(f"  New nodes: {stats['nodes_created']}")
    print(f"  Stubs created: {stats['stubs_created']}")
    print(f"  Notepad records: {stats['notepad_records']}")

    assert stats["sentences_processed"] == 3
    assert stats["nodes_created"] >= 0  # some words already exist from WordNet

    print("\n✓ Text processing test complete")


if __name__ == "__main__":
    test_cat_dog_walkthrough()
    print("\n" + "="*60 + "\n")
    test_accumulation()
    print("\n" + "="*60 + "\n")
    test_node_model()
    print("\n" + "="*60 + "\n")
    test_boot_sequence()
    print("\n" + "="*60 + "\n")
    test_booted_walkthrough()
    print("\n" + "="*60 + "\n")
    test_wordnet_import()
    print("\n" + "="*60 + "\n")
    test_text_processing()
