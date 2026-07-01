"""
Intellon v4 — Boot Sequence

Loads the axioms. ASCII characters, equivalence, comparison, boolean logic,
and basic math. These are the system's reference frame — without them the
register processes in a vacuum.

Boot order matters. Each layer provides reference frames for the next.
  Layer 1: ASCII characters (the atoms)
  Layer 2: Equivalence and comparison (the comparison primitives)
  Layer 3: Boolean logic (combining comparison results)
  Layer 4: Basic math (Tier 2 — important but not axiomatic)
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from .models import Node, Tier, NodeFlag, Definition, Pointer

if TYPE_CHECKING:
    from .librarian import Librarian


def boot(librarian: Librarian) -> dict[str, str]:
    """
    Run the full boot sequence. Returns a map of logical names to node IDs
    for reference (e.g. {"char_a": "...", "eq": "...", "add": "..."}).
    """
    librarian.set_training_mode(True, Tier.INITIATOR)
    registry: dict[str, str] = {}

    # Layer 1: ASCII characters
    char_ids = _boot_ascii(librarian, registry)

    # Layer 2: Equivalence and comparison
    _boot_equivalence(librarian, registry, char_ids)
    _boot_comparison(librarian, registry, char_ids)

    # Layer 3: Boolean logic
    _boot_logic(librarian, registry, char_ids)

    # Layer 4: Basic math (Tier 2, not axiomatic)
    librarian.set_training_mode(True, Tier.IMPORTANT)
    _boot_math(librarian, registry, char_ids)

    librarian.set_training_mode(False)
    return registry


# --------------------------------------------------------------------------
# Layer 1: ASCII
# --------------------------------------------------------------------------

def _boot_ascii(librarian: Librarian, registry: dict[str, str]) -> dict[str, str]:
    """
    Create a node for every printable ASCII character (32-126).
    These are the atoms. Everything builds from here.
    Returns char -> node_id mapping.
    """
    char_ids: dict[str, str] = {}

    for code in range(32, 127):
        char = chr(code)
        node = Node(
            name=char,
            tier=Tier.INITIATOR,
            flags={NodeFlag.FOUNDATION, NodeFlag.ACTIVE},
        )
        node.add_definition(f"ASCII character {code}", pointers=[
            Pointer(target="__type_char__", relation="is_a"),
        ])
        # Characters are atomic — no char_pointers (they ARE the base)

        librarian.store_node(node)
        char_ids[char] = node.id
        registry[f"char_{code}"] = node.id

    return char_ids


def _make_char_pointers(name: str, char_ids: dict[str, str]) -> list[str]:
    """Build character pointer list for a named node."""
    return [char_ids[c] for c in name if c in char_ids]


# --------------------------------------------------------------------------
# Layer 2: Equivalence & Comparison
# --------------------------------------------------------------------------

def _boot_equivalence(librarian: Librarian, registry: dict[str, str], char_ids: dict[str, str]):
    """EQ and NEQ — the comparison primitives."""

    eq = Node(
        name="eq",
        tier=Tier.INITIATOR,
        flags={NodeFlag.FOUNDATION, NodeFlag.ACTIVE},
        char_pointers=_make_char_pointers("eq", char_ids),
    )
    eq.add_definition(
        "Two things are the same if no differentiation produces DIFFERENT",
        pointers=[Pointer(target="__type_operator__", relation="is_a")],
    )
    librarian.store_node(eq)
    librarian.set_foundation(eq.id)
    registry["eq"] = eq.id

    neq = Node(
        name="neq",
        tier=Tier.INITIATOR,
        flags={NodeFlag.FOUNDATION, NodeFlag.ACTIVE},
        char_pointers=_make_char_pointers("neq", char_ids),
    )
    neq.add_definition(
        "Two things are different if any differentiation produces DIFFERENT",
        pointers=[Pointer(target="__type_operator__", relation="is_a")],
    )
    # Cross-reference
    neq.pointers.append(Pointer(target=eq.id, relation="inverse_of"))
    eq.pointers.append(Pointer(target=neq.id, relation="inverse_of"))

    librarian.store_node(neq)
    librarian.set_foundation(neq.id)
    registry["neq"] = neq.id


def _boot_comparison(librarian: Librarian, registry: dict[str, str], char_ids: dict[str, str]):
    """GT, LT, GTE, LTE — ordering primitives."""

    comparisons = [
        ("gt", "A is greater than B. Ordering: A comes after B."),
        ("lt", "A is less than B. Ordering: A comes before B."),
        ("gte", "A is greater than or equal to B."),
        ("lte", "A is less than or equal to B."),
    ]

    for name, definition in comparisons:
        node = Node(
            name=name,
            tier=Tier.INITIATOR,
            flags={NodeFlag.FOUNDATION, NodeFlag.ACTIVE},
            char_pointers=_make_char_pointers(name, char_ids),
        )
        node.add_definition(
            definition,
            pointers=[Pointer(target="__type_operator__", relation="is_a")],
        )
        librarian.store_node(node)
        librarian.set_foundation(node.id)
        registry[name] = node.id

    # Cross-references: gt <-> lt, gte <-> lte
    gt_node = librarian.get_node(registry["gt"])
    lt_node = librarian.get_node(registry["lt"])
    gte_node = librarian.get_node(registry["gte"])
    lte_node = librarian.get_node(registry["lte"])

    gt_node.pointers.append(Pointer(target=lt_node.id, relation="inverse_of"))
    lt_node.pointers.append(Pointer(target=gt_node.id, relation="inverse_of"))
    gte_node.pointers.append(Pointer(target=lte_node.id, relation="inverse_of"))
    lte_node.pointers.append(Pointer(target=gte_node.id, relation="inverse_of"))


# --------------------------------------------------------------------------
# Layer 3: Boolean Logic
# --------------------------------------------------------------------------

def _boot_logic(librarian: Librarian, registry: dict[str, str], char_ids: dict[str, str]):
    """AND, OR, NOT, XOR — combining comparison results."""

    logic_ops = [
        ("and", "True if both A and B are true. False otherwise."),
        ("or", "True if A or B (or both) are true. False only if both false."),
        ("not", "True becomes false. False becomes true. Unary."),
        ("xor", "True if exactly one of A, B is true. False if both same."),
    ]

    for name, definition in logic_ops:
        node = Node(
            name=name,
            tier=Tier.INITIATOR,
            flags={NodeFlag.FOUNDATION, NodeFlag.ACTIVE},
            char_pointers=_make_char_pointers(name, char_ids),
        )
        node.add_definition(
            definition,
            pointers=[Pointer(target="__type_logic__", relation="is_a")],
        )
        librarian.store_node(node)
        librarian.set_foundation(node.id)
        registry[name] = node.id

    # NOT is inverse of itself
    not_node = librarian.get_node(registry["not"])
    not_node.pointers.append(Pointer(target=not_node.id, relation="inverse_of"))


# --------------------------------------------------------------------------
# Layer 4: Basic Math (Tier 2)
# --------------------------------------------------------------------------

def _boot_math(librarian: Librarian, registry: dict[str, str], char_ids: dict[str, str]):
    """Basic arithmetic operations. Tier 2 (Important), not axioms."""

    math_ops = [
        ("add", "Combine two quantities. A plus B.", "addition"),
        ("sub", "Remove quantity B from A. A minus B.", "subtraction"),
        ("mul", "Repeat A, B times. A times B.", "multiplication"),
        ("div", "Split A into B equal parts. A divided by B.", "division"),
    ]

    for name, definition, long_name in math_ops:
        node = Node(
            name=name,
            tier=Tier.IMPORTANT,
            flags={NodeFlag.ACTIVE},
            char_pointers=_make_char_pointers(name, char_ids),
        )
        node.add_definition(
            definition,
            pointers=[Pointer(target="__type_math__", relation="is_a")],
        )
        # Also store the long name as a second definition / alias
        node.add_definition(long_name)
        librarian.store_node(node)
        registry[name] = node.id

    # Inverse pairs: add <-> sub, mul <-> div
    add_node = librarian.get_node(registry["add"])
    sub_node = librarian.get_node(registry["sub"])
    mul_node = librarian.get_node(registry["mul"])
    div_node = librarian.get_node(registry["div"])

    add_node.pointers.append(Pointer(target=sub_node.id, relation="inverse_of"))
    sub_node.pointers.append(Pointer(target=add_node.id, relation="inverse_of"))
    mul_node.pointers.append(Pointer(target=div_node.id, relation="inverse_of"))
    div_node.pointers.append(Pointer(target=mul_node.id, relation="inverse_of"))

    # Number concept nodes (0-9 as concepts, not just characters)
    for digit in range(10):
        name = str(digit)
        node = Node(
            name=name,
            tier=Tier.IMPORTANT,
            flags={NodeFlag.ACTIVE},
            char_pointers=_make_char_pointers(name, char_ids),
        )
        node.add_definition(
            f"The number {digit}",
            pointers=[Pointer(target="__type_number__", relation="is_a")],
        )
        librarian.store_node(node)
        registry[f"num_{digit}"] = node.id
