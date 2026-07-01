"""
Intellon v4 — Engine

Orchestrates the assignment cycle: input → librarian bundles → register
processes → librarian integrates → output.
"""

from __future__ import annotations
from typing import Any
import time

from .models import Node, ReturnPackage, Assignment
from .register import Register
from .librarian import Librarian
from .boot import boot


class Engine:
    """
    Top-level coordinator. Owns one librarian and N registers.
    Runs the assignment cycle described in Section 3.1.
    """

    def __init__(self, num_registers: int = 1, run_boot: bool = True):
        self.librarian = Librarian()
        self.registers: list[Register] = []
        for _ in range(num_registers):
            reg = Register(request_fn=self.librarian.deliver)
            self.registers.append(reg)
        self._cascade_count: int = 0
        self.boot_registry: dict[str, str] = {}

        if run_boot:
            self.boot_registry = boot(self.librarian)

    # ------------------------------------------------------------------
    # Main cycle
    # ------------------------------------------------------------------

    def process(self, raw_input: Any) -> ReturnPackage:
        """
        Full assignment cycle for a single input.
        
        1. Librarian recognizes and bundles
        2. Register loads and processes
        3. Register hands back
        4. Librarian integrates
        5. Conflict resolution if needed
        6. Return result
        """
        # Step 1-3: Bundle
        assignment = self.librarian.bundle(raw_input)

        # Step 4: Assign to first available register
        register = self._get_register()
        register.load_assignment(assignment)

        # Step 5-9: Register processes
        t0 = time.perf_counter()
        package = self._run_register(register, assignment)
        elapsed = time.perf_counter() - t0

        # Report timing so librarian can adapt bundle size
        self.librarian.report_processing_time(elapsed)

        # Step 10-12: Librarian integrates
        result = self.librarian.integrate(package)

        # Step 13: Conflict resolution loop
        self._cascade_count = 0
        while (self.librarian.has_pending_conflicts()
               and self._cascade_count < self.librarian.cascade_limit):
            self._cascade_count += 1
            conflict_assignment = self.librarian.next_conflict_assignment()
            if conflict_assignment:
                conflict_reg = self._get_register()
                conflict_reg.load_assignment(conflict_assignment)
                conflict_package = self._run_register(conflict_reg, conflict_assignment)
                self.librarian.integrate(conflict_package)

        # Background maintenance
        self.librarian.check_promotions()

        return package

    def _run_register(self, register: Register, assignment: Assignment) -> ReturnPackage:
        """
        Execute register processing for an assignment.
        
        Default implementation: tokenize input, create stubs for unknowns,
        compare token sequences. Override or extend for richer processing.
        """
        raw = assignment.input_raw

        if isinstance(raw, str):
            return self._process_text(register, assignment)
        elif isinstance(raw, dict) and raw.get("type") == "conflict_resolution":
            return self._process_conflict(register, assignment)
        else:
            # Generic: just hand back what we have
            return register.hand_back()

    def _process_text(self, register: Register, assignment: Assignment) -> ReturnPackage:
        """
        Text processing: tokenize, create stubs, compare sequences.
        This implements the walkthrough from Section 11.
        """
        raw = assignment.input_raw
        if not isinstance(raw, str):
            return register.hand_back()

        # Tokenize
        sentences = [s.strip() for s in raw.split(".") if s.strip()]
        all_tokens: list[list[str]] = []

        for sentence in sentences:
            tokens = sentence.lower().split()
            all_tokens.append(tokens)

            # Create stubs for each token
            for token in tokens:
                clean = token.strip(".,!?;:'\"")
                existing = self.librarian.get_node(clean)
                if not existing:
                    # Check if any context node matches
                    found = False
                    for ctx_node in assignment.context:
                        if ctx_node.name.lower() == clean:
                            found = True
                            break
                    if not found:
                        register.create_stub(clean, f"token in: {raw}")

        # Compare sentences pairwise
        for i in range(len(all_tokens)):
            for j in range(i + 1, len(all_tokens)):
                register.compare_tokens(all_tokens[i], all_tokens[j])

        # Compare against context nodes
        for ctx_node in assignment.context:
            if register.center:
                register.compare(register.center, ctx_node)

        return register.hand_back()

    def _process_conflict(self, register: Register, assignment: Assignment) -> ReturnPackage:
        """Resolve a conflict between two nodes."""
        if len(assignment.context) >= 2:
            register.compare(assignment.context[0], assignment.context[1])
        return register.hand_back()

    def _get_register(self) -> Register:
        """Get an available register. Simple round-robin for now."""
        # All registers are stateless, so any will do
        return self.registers[0]

    # ------------------------------------------------------------------
    # Multi-input processing
    # ------------------------------------------------------------------

    def process_batch(self, inputs: list[Any]) -> list[ReturnPackage]:
        """Process multiple inputs sequentially."""
        return [self.process(inp) for inp in inputs]

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    @property
    def stats(self) -> dict:
        return {
            "nodes": self.librarian.node_count,
            "foundation_nodes": self.librarian.foundation_count,
            "sessions": self.librarian.session_count,
            "registers": len(self.registers),
        }
