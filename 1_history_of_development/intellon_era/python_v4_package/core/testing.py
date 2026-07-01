"""
Intellon v4 — Testing & Feedback

The learning loop:
  1. System receives a challenge (input + expected output)
  2. System processes the input, produces its best response
  3. Register compares response to expected answer
  4. SAME = reinforce. DIFFERENT = gap analysis.
  5. Gap analysis creates a traceback node:
     - What the input looked like (structure)
     - What the system produced
     - What it should have produced
     - What was missing or wrong
  6. Traceback nodes get bundled as context for future similar inputs

This is how the system learns to get better at processing,
not just accumulate more data.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable
import time

from .models import (
    Node, Tier, NodeFlag, DiffRecord, DiffResult,
    Definition, Pointer, Origin,
)

if TYPE_CHECKING:
    from .engine import Engine
    from .librarian import Librarian


# ======================================================================
# Challenge / Test Result
# ======================================================================

@dataclass
class ChallengeResult:
    """Result of a single test challenge."""
    input_text: str
    expected: str
    produced: str
    passed: bool
    same_count: int = 0
    diff_count: int = 0
    gap_analysis: str = ""
    traceback_node_id: str | None = None
    processing_time: float = 0.0


@dataclass
class TestReport:
    """Summary of a test batch."""
    total: int = 0
    passed: int = 0
    failed: int = 0
    results: list[ChallengeResult] = field(default_factory=list)
    traceback_nodes_created: int = 0

    @property
    def accuracy(self) -> float:
        return self.passed / self.total if self.total > 0 else 0.0


# ======================================================================
# Challenge System
# ======================================================================

class Challenger:
    """
    Presents challenges to the system and processes feedback.
    Creates traceback nodes from failures that improve future performance.
    """

    def __init__(self, engine: "Engine"):
        self.engine = engine
        self._history: list[ChallengeResult] = []

    def challenge(self, input_text: str, expected: str) -> ChallengeResult:
        """
        Present a challenge: process the input, compare to expected.
        On failure, run gap analysis and create a traceback node.
        """
        lib = self.engine.librarian
        t0 = time.perf_counter()

        # Step 1: Process the input normally
        result = self.engine.process(input_text)

        # Step 2: Extract what the system produced
        produced = self._extract_response(result)

        # Step 3: Compare produced vs expected through the register
        register = self.engine._get_register()
        from .models import Assignment

        # Create temporary nodes for comparison
        expected_node = Node(name="expected")
        expected_node.content = expected

        produced_node = Node(name="produced")
        produced_node.content = produced

        assignment = Assignment(
            foundation=list(lib._nodes[addr] for addr in lib._foundation if addr in lib._nodes),
            context=[expected_node, produced_node],
            input_raw={"type": "challenge_compare"},
        )
        register.load_assignment(assignment)
        records = register.compare(expected_node, produced_node)
        package = register.hand_back()

        same_count = sum(1 for r in records if r.result == DiffResult.SAME)
        diff_count = sum(1 for r in records if r.result == DiffResult.DIFFERENT)

        # Step 4: Did it pass?
        # Content match is the primary check
        content_records = [r for r in records if r.aspect == "content"]
        passed = any(r.result == DiffResult.SAME for r in content_records)

        # Also check token-level if both are strings
        if not passed and isinstance(expected, str) and isinstance(produced, str):
            exp_tokens = expected.lower().split()
            prod_tokens = produced.lower().split()
            if exp_tokens == prod_tokens:
                passed = True

        elapsed = time.perf_counter() - t0

        challenge_result = ChallengeResult(
            input_text=input_text,
            expected=expected,
            produced=produced,
            passed=passed,
            same_count=same_count,
            diff_count=diff_count,
            processing_time=elapsed,
        )

        # Step 5: Gap analysis on failure
        if not passed:
            traceback = self._gap_analysis(input_text, expected, produced, records, result)
            challenge_result.gap_analysis = traceback.content if traceback else ""
            challenge_result.traceback_node_id = traceback.id if traceback else None

        self._history.append(challenge_result)
        return challenge_result

    def run_test_batch(self, challenges: list[tuple[str, str]],
                       on_progress: Callable | None = None) -> TestReport:
        """
        Run a batch of challenges: [(input, expected), ...]
        Returns a TestReport with accuracy and details.
        """
        report = TestReport()

        for i, (input_text, expected) in enumerate(challenges):
            result = self.challenge(input_text, expected)
            report.results.append(result)
            report.total += 1
            if result.passed:
                report.passed += 1
            else:
                report.failed += 1
                if result.traceback_node_id:
                    report.traceback_nodes_created += 1

            if on_progress:
                on_progress(i + 1, len(challenges), result)

        return report

    def _extract_response(self, result) -> str:
        """Extract the system's response from a ReturnPackage."""
        if result.synthesis and isinstance(result.synthesis.content, dict):
            # If there's a pattern, that's the response
            pattern = result.synthesis.content.get("pattern")
            if pattern and pattern.get("pattern_str"):
                return pattern["pattern_str"]

            # Otherwise return the node comparison summary
            nc = result.synthesis.content.get("node_comparisons", {})
            if nc:
                return f"same={nc.get('same', 0)} different={nc.get('different', 0)}"

        # Fallback: list of SAME aspects from notepad
        if result.notepad:
            same_aspects = [r.detail for r in result.notepad if r.result == DiffResult.SAME]
            if same_aspects:
                return "; ".join(same_aspects[:5])

        return "(no response)"

    def _gap_analysis(self, input_text: str, expected: str, produced: str,
                      comparison_records: list[DiffRecord], original_result) -> Node | None:
        """
        Analyze WHY the system got it wrong.
        Creates a traceback node with structural information about the mistake.
        """
        lib = self.engine.librarian

        # What aspects were DIFFERENT between expected and produced?
        diffs = [r for r in comparison_records if r.result == DiffResult.DIFFERENT]
        diff_aspects = [r.aspect for r in diffs]
        diff_details = [r.detail for r in diffs]

        # What was in the notepad that led to the wrong answer?
        notepad_sames = sum(1 for r in original_result.notepad if r.result == DiffResult.SAME)
        notepad_diffs = sum(1 for r in original_result.notepad if r.result == DiffResult.DIFFERENT)

        # What context did the system have?
        # (We can infer from stubs — if lots of stubs, it didn't know key words)
        unknown_words = [s.name for s in original_result.stubs if s.name]

        # Build the gap description
        gap_parts = []

        if unknown_words:
            gap_parts.append(f"unknown words: {', '.join(unknown_words[:10])}")

        if "content" in diff_aspects:
            gap_parts.append(f"content mismatch: produced '{produced[:50]}' expected '{expected[:50]}'")

        if "sequential" in diff_aspects:
            # Token-level differences
            seq_diffs = [r for r in diffs if r.aspect == "sequential"]
            positions = [r.position for r in seq_diffs if r.position is not None]
            if positions:
                gap_parts.append(f"wrong at positions: {positions[:10]}")

        gap_parts.append(f"notepad: {notepad_sames}S {notepad_diffs}D")

        gap_description = "; ".join(gap_parts) if gap_parts else "unknown gap"

        # Create the traceback node
        traceback = Node(
            name=f"traceback",
            tier=Tier.TRIAL,
            flags={NodeFlag.ACTIVE},
            origin=Origin(
                session_id=original_result.session_id,
                inputs=[],
            ),
        )

        # Store the structural pattern of this mistake
        traceback_content = {
            "type": "traceback",
            "input_structure": self._extract_structure(input_text),
            "expected": expected,
            "produced": produced,
            "gap": gap_description,
            "unknown_words": unknown_words,
            "diff_aspects": diff_aspects,
        }
        traceback.content = traceback_content

        # Point to relevant nodes — the words involved
        for word in input_text.lower().split():
            clean = word.strip(".,!?;:'\"")
            ids = lib.recognize(clean)
            if ids:
                traceback.pointers.append(Pointer(target=ids[0], relation="traceback_context"))

        lib.store_node(traceback)
        return traceback

    def _extract_structure(self, text: str) -> str:
        """
        Extract the structural pattern of an input.
        "The cat ran." → "DET NOUN VERB" (if known)
        Falls back to token count and shape.
        """
        lib = self.engine.librarian
        tokens = text.lower().strip(".,!?").split()
        structure = []

        for token in tokens:
            clean = token.strip(".,!?;:'\"")
            ids = lib.recognize(clean)
            if ids:
                node = lib.get_node(ids[0])
                if node and node.definitions:
                    # Check part of speech from definition pointers
                    for defn in node.definitions[:1]:
                        for ptr in defn.pointers:
                            if ptr.relation == "part_of_speech":
                                pos = ptr.target.replace("__pos_", "").replace("__", "")
                                structure.append(pos)
                                break
                        else:
                            structure.append("known")
                        break
                else:
                    structure.append("known")
            else:
                structure.append("unknown")

        return " ".join(structure)

    @property
    def history(self) -> list[ChallengeResult]:
        return list(self._history)

    @property
    def accuracy(self) -> float:
        if not self._history:
            return 0.0
        passed = sum(1 for r in self._history if r.passed)
        return passed / len(self._history)


# ======================================================================
# Built-in test sets
# ======================================================================

# Basic comprehension: does it recognize patterns?
PATTERN_TESTS = [
    ("The cat ran. The dog ran.", "the [cat|dog] ran"),
    ("The cat sat. The cat ran.", "the cat [sat|ran]"),
    ("A big cat. A small cat.", "a [big|small] cat"),
]

# Vocabulary: does it know these words?
VOCABULARY_TESTS = [
    ("cat is a noun.", "noun"),
    ("run is a verb.", "verb"),
    ("big is a adjective.", "adjective"),
]

# Relationship: does it understand connections?
RELATIONSHIP_TESTS = [
    ("A cat is a type of what?", "animal"),
    ("What is the opposite of big?", "small"),
    ("Is a cat an animal?", "true"),
]

# Arithmetic: does it know math?
ARITHMETIC_TESTS = [
    ("2 + 3 =", "5"),
    ("5 - 2 =", "3"),
    ("3 * 4 =", "12"),
]
