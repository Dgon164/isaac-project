"""
Intellon v4 — Curriculum

Structured training data delivered in foundational order.
Each layer provides reference frames for the next.

Order:
  1. ASCII         (boot — already done)
  2. Logic         (truth tables — deterministic facts)
  3. Math          (equations — deterministic facts)
  4. Comparison    (ordering facts)
  5. Words         (user loads via WordNet)
  6. Structures    (grammar, patterns — user provides)

The register discovers patterns by differentiating across observations.
"2 + 3 = 5" vs "4 + 1 = 5" → same operator, same result, different inputs.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any

from .models import Node, Tier, NodeFlag, Definition, Pointer

if TYPE_CHECKING:
    from .engine import Engine
    from .librarian import Librarian


# ======================================================================
# Curriculum Runner
# ======================================================================

def run_curriculum(engine: "Engine", through_phase: int = 4,
                   on_progress: Any = None) -> dict[str, Any]:
    """
    Run the training curriculum up to the specified phase.
    Phase 0: Meta-knowledge (scoring criteria, language rules, strategies)
    Phase 1: Logic (truth tables)
    Phase 2: Math (arithmetic equations)
    Phase 3: Comparison (ordering)

    on_progress(phase_name, item_index, total_items) callback for UI.

    Returns stats about what was trained.
    """
    from .meta import load_meta_knowledge, resolve_deferred_pointers

    stats = {
        "phases_completed": 0,
        "total_observations": 0,
        "nodes_before": engine.librarian.node_count,
    }

    # Phase 0: Meta-knowledge — scoring criteria and language rules as nodes
    if on_progress:
        on_progress("Meta-knowledge", 1, 1)
    meta_reg = load_meta_knowledge(engine.librarian)
    resolve_deferred_pointers(engine.librarian, meta_reg)
    stats["meta_nodes"] = len(meta_reg)

    # Process each meta node through the engine so the register sees it
    engine.librarian.set_training_mode(True, Tier.IMPORTANT)
    for key, node_id in meta_reg.items():
        node = engine.librarian.get_node(node_id)
        if node and node.definitions:
            defn = node.definitions[0]
            if isinstance(defn.content, str):
                engine.process(f"{node.name}: {defn.content}")
                stats["total_observations"] += 1
    engine.librarian.set_training_mode(False)

    phases = [
        (1, "Logic", LOGIC_OBSERVATIONS),
        (2, "Arithmetic", MATH_OBSERVATIONS),
        (3, "Comparison", COMPARISON_OBSERVATIONS),
    ]

    for phase_num, phase_name, observations in phases:
        if phase_num > through_phase:
            break

        engine.librarian.set_training_mode(True, Tier.IMPORTANT)

        for i, obs in enumerate(observations):
            if on_progress:
                on_progress(phase_name, i + 1, len(observations))

            # Process each observation through the engine
            # The register will differentiate, create stubs, find patterns
            result = engine.process(obs)
            stats["total_observations"] += 1

        stats["phases_completed"] = phase_num

    engine.librarian.set_training_mode(False)
    stats["nodes_after"] = engine.librarian.node_count
    stats["nodes_created"] = stats["nodes_after"] - stats["nodes_before"]
    return stats


# ======================================================================
# Phase 1: Logic — Truth Tables
# ======================================================================
# Raw facts. The register compares these and discovers:
# - AND only produces true when both inputs are true
# - OR produces true when any input is true
# - NOT flips the value
# - XOR produces true when inputs differ

LOGIC_OBSERVATIONS = [
    # AND truth table
    "true and true = true",
    "true and false = false",
    "false and true = false",
    "false and false = false",

    # OR truth table
    "true or true = true",
    "true or false = true",
    "false or true = true",
    "false or false = false",

    # NOT
    "not true = false",
    "not false = true",

    # XOR
    "true xor true = false",
    "true xor false = true",
    "false xor true = true",
    "false xor false = false",

    # Equivalence
    "true eq true = true",
    "true eq false = false",
    "false eq true = false",
    "false eq false = true",

    # Patterns — same operator, different inputs, same structure
    "true and true = true. true or true = true",
    "false and false = false. false or false = false",
    "true and false = false. true or false = true",
    "not true = false. not false = true",

    # Negation chains
    "not not true = true",
    "not not false = false",

    # Combined
    "true and true = true. not true = false",
    "false or false = false. not false = true",
]


# ======================================================================
# Phase 2: Arithmetic — Equations
# ======================================================================
# Start with single digits. The register sees patterns:
# "2 + 3 = 5" vs "3 + 2 = 5" → same result, swapped inputs (commutativity)
# "5 - 3 = 2" vs "2 + 3 = 5" → inverse relationship

MATH_OBSERVATIONS = [
    # Addition basics
    "0 + 0 = 0",
    "0 + 1 = 1",
    "1 + 0 = 1",
    "1 + 1 = 2",
    "1 + 2 = 3",
    "2 + 1 = 3",
    "2 + 2 = 4",
    "2 + 3 = 5",
    "3 + 2 = 5",
    "3 + 3 = 6",
    "3 + 4 = 7",
    "4 + 3 = 7",
    "4 + 5 = 9",
    "5 + 5 = 10",

    # Subtraction basics
    "1 - 0 = 1",
    "1 - 1 = 0",
    "2 - 1 = 1",
    "3 - 1 = 2",
    "3 - 2 = 1",
    "5 - 2 = 3",
    "5 - 3 = 2",
    "7 - 3 = 4",
    "7 - 4 = 3",
    "10 - 5 = 5",

    # Addition and subtraction pairs — inverse relationship
    "2 + 3 = 5. 5 - 3 = 2",
    "4 + 3 = 7. 7 - 3 = 4",
    "1 + 4 = 5. 5 - 4 = 1",
    "3 + 6 = 9. 9 - 6 = 3",

    # Multiplication basics
    "0 * 1 = 0",
    "1 * 0 = 0",
    "1 * 1 = 1",
    "2 * 1 = 2",
    "1 * 2 = 2",
    "2 * 2 = 4",
    "2 * 3 = 6",
    "3 * 2 = 6",
    "3 * 3 = 9",
    "3 * 4 = 12",
    "4 * 3 = 12",
    "4 * 5 = 20",
    "5 * 5 = 25",

    # Division basics
    "2 / 1 = 2",
    "2 / 2 = 1",
    "4 / 2 = 2",
    "6 / 2 = 3",
    "6 / 3 = 2",
    "9 / 3 = 3",
    "12 / 3 = 4",
    "12 / 4 = 3",
    "20 / 4 = 5",
    "25 / 5 = 5",

    # Multiplication and division pairs — inverse relationship
    "2 * 3 = 6. 6 / 3 = 2",
    "3 * 4 = 12. 12 / 4 = 3",
    "4 * 5 = 20. 20 / 5 = 4",
    "5 * 5 = 25. 25 / 5 = 5",

    # Identity elements
    "5 + 0 = 5",
    "0 + 5 = 5",
    "5 - 0 = 5",
    "5 * 1 = 5",
    "1 * 5 = 5",
    "5 / 1 = 5",

    # Commutativity patterns (pairs for register to compare)
    "2 + 3 = 5. 3 + 2 = 5",
    "4 + 7 = 11. 7 + 4 = 11",
    "2 * 3 = 6. 3 * 2 = 6",
    "4 * 5 = 20. 5 * 4 = 20",

    # Multi-digit (generalization)
    "10 + 20 = 30",
    "15 + 15 = 30",
    "25 + 25 = 50",
    "50 + 50 = 100",
    "99 + 1 = 100",
    "100 - 1 = 99",
    "10 * 10 = 100",
    "100 / 10 = 10",

    # Decimal
    "1.5 + 1.5 = 3",
    "2.5 + 2.5 = 5",
    "3.7 + 1.3 = 5",
    "10.5 - 0.5 = 10",
]


# ======================================================================
# Phase 3: Comparison — Ordering
# ======================================================================

COMPARISON_OBSERVATIONS = [
    # Greater than
    "2 gt 1 = true",
    "5 gt 3 = true",
    "10 gt 1 = true",
    "1 gt 2 = false",
    "3 gt 5 = false",
    "3 gt 3 = false",

    # Less than
    "1 lt 2 = true",
    "3 lt 5 = true",
    "1 lt 10 = true",
    "2 lt 1 = false",
    "5 lt 3 = false",
    "3 lt 3 = false",

    # Greater than or equal
    "2 gte 1 = true",
    "3 gte 3 = true",
    "5 gte 5 = true",
    "1 gte 2 = false",

    # Less than or equal
    "1 lte 2 = true",
    "3 lte 3 = true",
    "5 lte 5 = true",
    "2 lte 1 = false",

    # Equality
    "3 eq 3 = true",
    "5 eq 5 = true",
    "3 eq 4 = false",

    # Not equal
    "3 neq 4 = true",
    "5 neq 3 = true",
    "3 neq 3 = false",

    # Inverse pairs for register to discover
    "2 gt 1 = true. 1 lt 2 = true",
    "5 gt 3 = true. 3 lt 5 = true",
    "1 gt 2 = false. 2 lt 1 = false",

    # Ordering sequences
    "1 lt 2 = true. 2 lt 3 = true. 1 lt 3 = true",
    "3 gt 2 = true. 2 gt 1 = true. 3 gt 1 = true",
]
