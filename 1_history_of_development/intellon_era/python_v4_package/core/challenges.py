"""
Intellon v4 — Challenge Generators

Two sources of test challenges:

1. AUTO-GENERATED from the system's own knowledge
   If it stored "cat is_a feline", it should answer "cat is a ___" → "feline"
   If it stored "2 + 3 = 5", it should answer "2 + 3 = ?" → "5"
   Tests what the system SHOULD know based on what it's been trained on.

2. STANDARD BENCHMARKS from established datasets
   BoolQ, ARC, CommonsenseQA, etc.
   Tests against known baselines.
"""

from __future__ import annotations
import random
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .librarian import Librarian
    from .engine import Engine


# ======================================================================
# Auto-Generated Challenges (from system's own knowledge)
# ======================================================================

def generate_challenges(librarian: "Librarian", count: int = 50,
                        types: list[str] | None = None) -> list[tuple[str, str]]:
    """
    Generate test challenges from what the system already knows.

    Types:
      "definition"   — "cat: ___" → first definition
      "relationship"  — "cat is_a ___" → "feline"
      "equation"      — "2 + 3 = ___" → "5"
      "completion"    — "the ___ ran" → fill from known patterns
      "boolean"       — "true and false = ___" → "false"
      "comparison"    — "5 gt 3 = ___" → "true"

    Returns list of (input, expected_answer) tuples.
    """
    all_types = types or ["definition", "relationship", "equation", "boolean", "comparison"]
    challenges = []

    generators = {
        "definition": _gen_definition,
        "relationship": _gen_relationship,
        "equation": _gen_equation,
        "boolean": _gen_boolean,
        "comparison": _gen_comparison,
    }

    # Generate evenly across types
    per_type = max(count // len(all_types), 1)
    for challenge_type in all_types:
        gen = generators.get(challenge_type)
        if gen:
            challenges.extend(gen(librarian, per_type))

    random.shuffle(challenges)
    return challenges[:count]


def _gen_definition(librarian: "Librarian", count: int) -> list[tuple[str, str]]:
    """Generate "word: ___" challenges from stored definitions."""
    challenges = []
    nodes = librarian.get_all_nodes()
    candidates = [n for n in nodes if n.definitions and n.name
                  and len(n.name) > 1 and not n.name.startswith("__")]

    random.shuffle(candidates)
    for node in candidates[:count]:
        defn = node.definitions[0]
        if isinstance(defn.content, str) and len(defn.content) > 5:
            # Truncate definition for the expected answer
            answer = defn.content.split(".")[0].strip()
            if len(answer) > 3:
                challenges.append((f"Define: {node.name}", answer))

    return challenges


def _gen_relationship(librarian: "Librarian", count: int) -> list[tuple[str, str]]:
    """Generate relationship challenges from stored pointers."""
    challenges = []
    nodes = librarian.get_all_nodes()
    candidates = [n for n in nodes if n.pointers and n.name
                  and len(n.name) > 1 and not n.name.startswith("__")]

    # Relationship type to question template
    templates = {
        "is_a": ("{word} is a type of ___", None),
        "has_type": ("What is a type of {word}?", None),
        "synonym": ("A synonym of {word} is ___", None),
        "part_of": ("{word} is part of ___", None),
        "has_part": ("What is part of {word}?", None),
        "inverse_of": ("The inverse of {word} is ___", None),
    }

    random.shuffle(candidates)
    for node in candidates:
        if len(challenges) >= count:
            break
        for ptr in node.pointers:
            if ptr.relation in templates:
                target = librarian.get_node(ptr.target)
                if target and target.name and not target.name.startswith("__"):
                    template, _ = templates[ptr.relation]
                    question = template.format(word=node.name)
                    challenges.append((question, target.name))
                    break

    return challenges


def _gen_equation(librarian: "Librarian", count: int) -> list[tuple[str, str]]:
    """Generate arithmetic challenges from stored equations."""
    # These are deterministic — we know the answers
    equations = [
        ("1 + 1 = ?", "2"), ("2 + 3 = ?", "5"), ("3 + 4 = ?", "7"),
        ("4 + 5 = ?", "9"), ("5 + 5 = ?", "10"), ("3 + 2 = ?", "5"),
        ("7 + 4 = ?", "11"), ("10 + 20 = ?", "30"), ("25 + 25 = ?", "50"),
        ("5 - 2 = ?", "3"), ("7 - 3 = ?", "4"), ("10 - 5 = ?", "5"),
        ("3 - 1 = ?", "2"), ("100 - 1 = ?", "99"),
        ("2 * 3 = ?", "6"), ("3 * 4 = ?", "12"), ("4 * 5 = ?", "20"),
        ("5 * 5 = ?", "25"), ("10 * 10 = ?", "100"),
        ("6 / 2 = ?", "3"), ("9 / 3 = ?", "3"), ("12 / 4 = ?", "3"),
        ("20 / 5 = ?", "4"), ("25 / 5 = ?", "5"),
    ]
    random.shuffle(equations)
    return equations[:count]


def _gen_boolean(librarian: "Librarian", count: int) -> list[tuple[str, str]]:
    """Generate boolean logic challenges."""
    logic = [
        ("true and true = ?", "true"), ("true and false = ?", "false"),
        ("false and true = ?", "false"), ("false and false = ?", "false"),
        ("true or true = ?", "true"), ("true or false = ?", "true"),
        ("false or true = ?", "true"), ("false or false = ?", "false"),
        ("not true = ?", "false"), ("not false = ?", "true"),
        ("true xor true = ?", "false"), ("true xor false = ?", "true"),
        ("false xor true = ?", "true"), ("false xor false = ?", "false"),
    ]
    random.shuffle(logic)
    return logic[:count]


def _gen_comparison(librarian: "Librarian", count: int) -> list[tuple[str, str]]:
    """Generate comparison challenges."""
    comparisons = [
        ("5 gt 3 = ?", "true"), ("3 gt 5 = ?", "false"),
        ("1 lt 2 = ?", "true"), ("2 lt 1 = ?", "false"),
        ("3 eq 3 = ?", "true"), ("3 eq 4 = ?", "false"),
        ("3 neq 4 = ?", "true"), ("3 neq 3 = ?", "false"),
        ("5 gte 5 = ?", "true"), ("5 lte 5 = ?", "true"),
        ("2 gt 1 = ?", "true"), ("10 gt 1 = ?", "true"),
        ("1 lt 10 = ?", "true"), ("3 gt 3 = ?", "false"),
    ]
    random.shuffle(comparisons)
    return comparisons[:count]


# ======================================================================
# Standard Benchmark Loaders
# ======================================================================

def load_boolq(count: int = 100) -> list[tuple[str, str]]:
    """
    BoolQ — yes/no reading comprehension questions.
    Requires: pip install datasets
    """
    from datasets import load_dataset
    ds = load_dataset("boolq", split=f"validation[:{count}]")
    challenges = []
    for row in ds:
        question = row["question"]
        answer = "true" if row["answer"] else "false"
        challenges.append((question, answer))
    return challenges


def load_arc_easy(count: int = 100) -> list[tuple[str, str]]:
    """
    ARC-Easy — elementary science questions with multiple choice.
    Requires: pip install datasets
    """
    from datasets import load_dataset
    ds = load_dataset("ai2_arc", "ARC-Easy", split=f"test[:{count}]")
    challenges = []
    for row in ds:
        question = row["question"]
        choices = row["choices"]
        try:
            answer_idx = choices["label"].index(row["answerKey"])
            answer = choices["text"][answer_idx]
            challenges.append((question, answer))
        except (ValueError, IndexError):
            continue
    return challenges


def load_commonsense_qa(count: int = 100) -> list[tuple[str, str]]:
    """
    CommonsenseQA — common sense reasoning.
    Requires: pip install datasets
    """
    from datasets import load_dataset
    ds = load_dataset("commonsense_qa", split=f"validation[:{count}]")
    challenges = []
    for row in ds:
        question = row["question"]
        choices = row["choices"]
        answer_key = row["answerKey"]
        try:
            answer_idx = choices["label"].index(answer_key)
            answer = choices["text"][answer_idx]
            challenges.append((question, answer))
        except (ValueError, IndexError):
            continue
    return challenges


def load_simple_arithmetic(count: int = 100) -> list[tuple[str, str]]:
    """
    Auto-generated arithmetic questions at various difficulty levels.
    No external dataset needed.
    """
    import random as rng
    challenges = []
    ops = [("+", lambda a, b: a + b),
           ("-", lambda a, b: a - b),
           ("*", lambda a, b: a * b)]

    for _ in range(count):
        op_sym, op_fn = rng.choice(ops)
        if op_sym == "*":
            a, b = rng.randint(1, 12), rng.randint(1, 12)
        elif op_sym == "-":
            a = rng.randint(1, 100)
            b = rng.randint(0, a)  # no negatives
        else:
            a, b = rng.randint(0, 100), rng.randint(0, 100)

        answer = op_fn(a, b)
        challenges.append((f"{a} {op_sym} {b} = ?", str(answer)))

    return challenges


# ======================================================================
# Available benchmark info (for UI)
# ======================================================================

BENCHMARKS = {
    "auto": {
        "name": "Auto-Generated (from knowledge)",
        "description": "Tests what the system should know based on its own stored data",
        "loader": None,  # uses generate_challenges()
    },
    "arithmetic": {
        "name": "Arithmetic",
        "description": "Random arithmetic problems (add, subtract, multiply)",
        "loader": load_simple_arithmetic,
    },
    "boolq": {
        "name": "BoolQ",
        "description": "Yes/no reading comprehension (requires: pip install datasets)",
        "loader": load_boolq,
    },
    "arc_easy": {
        "name": "ARC-Easy",
        "description": "Elementary science questions (requires: pip install datasets)",
        "loader": load_arc_easy,
    },
    "commonsense": {
        "name": "CommonsenseQA",
        "description": "Common sense reasoning (requires: pip install datasets)",
        "loader": load_commonsense_qa,
    },
}
