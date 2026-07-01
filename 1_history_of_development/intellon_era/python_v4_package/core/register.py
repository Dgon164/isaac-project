"""
Intellon v4 — Register

A stateless processing unit. Performs differentiation, comparison, note-taking,
synthesis, and internal verification. Knows only what it is handed. Retains
nothing between assignments.
"""

from __future__ import annotations
from typing import Any, Callable
import uuid

from .models import (
    Node, NodeFlag, Tier, DiffRecord, DiffResult, Assignment, ReturnPackage,
    VerificationResult, Origin, Pointer, Constraint,
)


class Register:
    """
    Three slots + notepad. That's it.
    
    The request_fn callback is the librarian channel — the register calls it
    with a node address and gets back a Node. This is the only way the register
    can reach outside itself.
    """

    def __init__(self, request_fn: Callable[[str], Node | None] | None = None):
        self.slot_a: Node | None = None
        self.slot_b: Node | None = None
        self.center: Node | None = None
        self.notepad: list[DiffRecord] = []
        self._request_fn = request_fn
        self._session_id: str = ""
        self._stubs: list[Node] = []
        self._requests_made: list[str] = []

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    def load_assignment(self, assignment: Assignment):
        """Begin a new session. Wipe everything, load fresh."""
        self._reset()
        self._session_id = assignment.id
        self.center = Node(
            id=f"input-{assignment.id}",
            name=str(assignment.input_raw) if isinstance(assignment.input_raw, str) else "",
        )
        self.center.content = assignment.input_raw
        # Foundation nodes loaded first, then context — stored for processing
        self._foundation_nodes = list(assignment.foundation)
        self._context_nodes = list(assignment.context)

    def _reset(self):
        self.slot_a = None
        self.slot_b = None
        self.center = None
        self.notepad = []
        self._stubs = []
        self._requests_made = []
        self._foundation_nodes = []
        self._context_nodes = []
        self._session_id = ""

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    def compare(self, node_a: Node, node_b: Node) -> list[DiffRecord]:
        """
        The primitive. Compare two nodes across all applicable levels.
        Returns one or more DiffRecords, all appended to notepad.
        """
        records = []

        # Identity check
        records.append(DiffRecord(
            slot_a=node_a.id, slot_b=node_b.id,
            aspect="identity",
            result=DiffResult.SAME if node_a.id == node_b.id else DiffResult.DIFFERENT,
            detail=f"{'same' if node_a.id == node_b.id else 'different'} address",
        ))

        # Content check
        content_same = node_a.content == node_b.content
        records.append(DiffRecord(
            slot_a=node_a.id, slot_b=node_b.id,
            aspect="content",
            result=DiffResult.SAME if content_same else DiffResult.DIFFERENT,
            detail=f"a='{node_a.content}' b='{node_b.content}'",
        ))

        # Sequential content comparison (if both have iterable content)
        if isinstance(node_a.content, (list, tuple, str)) and isinstance(node_b.content, (list, tuple, str)):
            records.extend(self._compare_sequential(node_a, node_b))

        # Pointer overlap
        a_targets = {p.target for p in node_a.pointers}
        b_targets = {p.target for p in node_b.pointers}
        overlap = a_targets & b_targets
        if a_targets or b_targets:
            records.append(DiffRecord(
                slot_a=node_a.id, slot_b=node_b.id,
                aspect="pointer_overlap",
                result=DiffResult.SAME if overlap else DiffResult.DIFFERENT,
                detail=f"shared={overlap}" if overlap else "no shared pointers",
            ))

        # Constraint compatibility
        if node_a.constraints and node_b.constraints:
            conflicts = self._check_constraint_compat(node_a, node_b)
            records.append(DiffRecord(
                slot_a=node_a.id, slot_b=node_b.id,
                aspect="constraint_compatibility",
                result=DiffResult.SAME if not conflicts else DiffResult.DIFFERENT,
                detail=f"conflicts={conflicts}" if conflicts else "compatible",
            ))

        # Structural comparison (shape)
        shape_same = (len(node_a.pointers) == len(node_b.pointers))
        records.append(DiffRecord(
            slot_a=node_a.id, slot_b=node_b.id,
            aspect="structure",
            result=DiffResult.SAME if shape_same else DiffResult.DIFFERENT,
            detail=f"a_ptrs={len(node_a.pointers)} b_ptrs={len(node_b.pointers)}",
        ))

        self.notepad.extend(records)
        return records

    def _compare_sequential(self, node_a: Node, node_b: Node) -> list[DiffRecord]:
        """Position-by-position comparison for ordered content."""
        records = []
        seq_a = list(node_a.content) if isinstance(node_a.content, str) else node_a.content
        seq_b = list(node_b.content) if isinstance(node_b.content, str) else node_b.content
        max_len = max(len(seq_a), len(seq_b))

        for i in range(max_len):
            a_val = seq_a[i] if i < len(seq_a) else None
            b_val = seq_b[i] if i < len(seq_b) else None
            same = a_val == b_val
            records.append(DiffRecord(
                slot_a=node_a.id, slot_b=node_b.id,
                aspect="sequential",
                result=DiffResult.SAME if same else DiffResult.DIFFERENT,
                detail=f"pos {i}: a='{a_val}' b='{b_val}'",
                position=i,
            ))
        return records

    def _check_constraint_compat(self, node_a: Node, node_b: Node) -> list[str]:
        """Check if any constraints directly conflict."""
        conflicts = []
        for ca in node_a.constraints:
            for cb in node_b.constraints:
                if (ca.subject == cb.subject and ca.relation == cb.relation
                        and ca.object == cb.object and ca.polarity != cb.polarity):
                    conflicts.append(f"{ca.subject}.{ca.relation}.{ca.object}")
        return conflicts

    def compare_tokens(self, tokens_a: list[str], tokens_b: list[str]) -> list[DiffRecord]:
        """
        Convenience: compare two token sequences positionally.
        This is the cat/dog level operation.
        """
        records = []
        max_len = max(len(tokens_a), len(tokens_b))
        for i in range(max_len):
            a = tokens_a[i] if i < len(tokens_a) else None
            b = tokens_b[i] if i < len(tokens_b) else None
            same = a == b
            records.append(DiffRecord(
                slot_a="input_a", slot_b="input_b",
                aspect="token",
                result=DiffResult.SAME if same else DiffResult.DIFFERENT,
                detail=f"a='{a}' b='{b}'",
                position=i,
            ))
        self.notepad.extend(records)
        return records

    # ------------------------------------------------------------------
    # Slot management
    # ------------------------------------------------------------------

    def swap(self, slot: str, content: Node):
        if slot == "a":
            self.slot_a = content
        elif slot == "b":
            self.slot_b = content
        elif slot == "center":
            self.center = content
        else:
            raise ValueError(f"Unknown slot: {slot}")

    # ------------------------------------------------------------------
    # External requests (via librarian channel)
    # ------------------------------------------------------------------

    def request(self, address: str) -> Node | None:
        """Ask the librarian for a node by address."""
        if self._request_fn is None:
            return None
        self._requests_made.append(address)
        return self._request_fn(address)

    # ------------------------------------------------------------------
    # Stub creation
    # ------------------------------------------------------------------

    def create_stub(self, content: Any, context_info: str = "") -> Node:
        """
        Create a raw, unclassified node for something unknown.
        The register has zero authority over this node after creation.
        """
        stub = Node(
            name=content if isinstance(content, str) else "",
            flags={NodeFlag.STUB},
            tier=Tier.TRIAL,
            origin=Origin(
                session_id=self._session_id,
                inputs=[self.center.id] if self.center else [],
            ),
        )
        if not isinstance(content, str):
            stub.content = content
        self._stubs.append(stub)
        return stub

    # ------------------------------------------------------------------
    # Synthesis
    # ------------------------------------------------------------------

    def synthesize(self) -> Node | None:
        """
        Produce a new node from the constraint space on the notepad.

        Reads the notepad and extracts:
        - Token-level patterns (SAME positions = frame, DIFFERENT = variable slots)
        - Node comparison summaries (what matched, what didn't)
        """
        if not self.notepad:
            return None

        synthesis_content = {}

        # --- Token pattern extraction ---
        token_records = [r for r in self.notepad if r.aspect == "token"]
        if token_records:
            pattern = self._extract_token_pattern(token_records)
            synthesis_content["pattern"] = pattern

        # --- Node comparison summary ---
        node_records = [r for r in self.notepad if r.aspect not in ("token", "sequential")]
        if node_records:
            same_count = sum(1 for r in node_records if r.result == DiffResult.SAME)
            diff_count = sum(1 for r in node_records if r.result == DiffResult.DIFFERENT)
            synthesis_content["node_comparisons"] = {
                "total": len(node_records),
                "same": same_count,
                "different": diff_count,
            }
            by_aspect: dict[str, list[DiffRecord]] = {}
            for r in node_records:
                by_aspect.setdefault(r.aspect, []).append(r)
            synthesis_content["aspects"] = {
                asp: {"same": sum(1 for x in recs if x.result == DiffResult.SAME),
                      "diff": sum(1 for x in recs if x.result == DiffResult.DIFFERENT)}
                for asp, recs in by_aspect.items()
            }

        synthesis_content["record_count"] = len(self.notepad)

        synthesis = Node(
            name="synthesis",
            flags={NodeFlag.STUB},
            tier=Tier.TRIAL,
            origin=Origin(
                session_id=self._session_id,
                inputs=[self.center.id] if self.center else [],
            ),
        )
        synthesis.content = synthesis_content
        return synthesis

    def _extract_token_pattern(self, token_records: list[DiffRecord]) -> dict:
        """
        From positional token comparisons, extract the structural pattern.

        "the cat ran" vs "the dog ran" produces:
          frame: ["the", None, "ran"]
          slots: {1: ["cat", "dog"]}
          pattern_str: "the [cat|dog] ran"
        """
        by_pos = sorted(token_records, key=lambda r: r.position or 0)

        frame: list[str | None] = []
        slots: dict[int, list[str]] = {}

        for rec in by_pos:
            pos = rec.position if rec.position is not None else len(frame)
            a_val, b_val = self._parse_token_detail(rec.detail)

            while len(frame) <= pos:
                frame.append(None)

            if rec.result == DiffResult.SAME:
                frame[pos] = a_val
            else:
                frame[pos] = None
                if pos not in slots:
                    slots[pos] = []
                if a_val and a_val not in slots[pos]:
                    slots[pos].append(a_val)
                if b_val and b_val not in slots[pos]:
                    slots[pos].append(b_val)

        parts = []
        for i, f in enumerate(frame):
            if f is not None:
                parts.append(f)
            else:
                fillers = slots.get(i, [])
                parts.append(f"[{'|'.join(fillers) if fillers else '?'}]")

        return {
            "frame": frame,
            "slots": {str(k): v for k, v in slots.items()},
            "pattern_str": " ".join(parts),
        }

    @staticmethod
    def _parse_token_detail(detail: str) -> tuple[str | None, str | None]:
        """Parse \"a='xxx' b='yyy'\" into (xxx, yyy)."""
        a_val = b_val = None
        try:
            parts = detail.split("' b='")
            if len(parts) == 2:
                a_val = parts[0].split("a='")[1] if "a='" in parts[0] else None
                b_val = parts[1].rstrip("'") if parts[1] else None
                if a_val == "None":
                    a_val = None
                if b_val == "None":
                    b_val = None
        except (IndexError, ValueError):
            pass
        return a_val, b_val

    # ------------------------------------------------------------------
    # Verification
    # ------------------------------------------------------------------

    def verify(self, synthesis: Node) -> VerificationResult:
        """
        Compare synthesis against every constraint on the notepad.
        Zero conflicts = pass. Any conflict triggers iteration.
        
        Three dimensions:
        - Logical consistency: does output contradict any diff result?
        - Structural completeness: all required components present?
        - Syntactic validity: satisfies foundation rules?
        """
        conflicts = []
        iterations = 0
        max_iterations = 10

        while iterations < max_iterations:
            iterations += 1
            round_conflicts = []

            for record in self.notepad:
                conflict = self._check_synthesis_against(synthesis, record)
                if conflict:
                    round_conflicts.append(conflict)

            if not round_conflicts:
                return VerificationResult(passed=True, iterations=iterations)

            conflicts = round_conflicts
            # Attempt correction — refine synthesis based on conflicts
            synthesis = self._correct_synthesis(synthesis, conflicts)

        return VerificationResult(
            passed=False,
            iterations=iterations,
            conflicts=conflicts,
        )

    def _check_synthesis_against(self, synthesis: Node, record: DiffRecord) -> DiffRecord | None:
        """
        Check if a synthesis contradicts a specific notepad record.
        Override this with domain-specific logic as the system matures.
        """
        # Base implementation: structural check
        # The real power comes when foundation nodes define what "contradiction" means
        return None  # No conflict detected in base scaffold

    def _correct_synthesis(self, synthesis: Node, conflicts: list[DiffRecord]) -> Node:
        """
        Adjust synthesis to resolve detected conflicts.
        Override with real correction logic.
        """
        # Add conflict info to synthesis for traceability
        if isinstance(synthesis.content, dict):
            synthesis.content["unresolved_conflicts"] = [
                {"aspect": c.aspect, "detail": c.detail} for c in conflicts
            ]
        return synthesis

    # ------------------------------------------------------------------
    # Hand back
    # ------------------------------------------------------------------

    def hand_back(self) -> ReturnPackage:
        """Package everything and return to librarian."""
        synthesis = self.synthesize()
        verification = self.verify(synthesis) if synthesis else VerificationResult(passed=True)

        package = ReturnPackage(
            session_id=self._session_id,
            notepad=list(self.notepad),
            stubs=list(self._stubs),
            synthesis=synthesis,
            verification=verification,
            requests=list(self._requests_made),
        )
        self._reset()
        return package
