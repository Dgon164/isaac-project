"""
Intellon v4 — Generator

Assembles text output from the node structure.
The register provides the constraint space. The generator finds
nodes that fit those constraints and assembles them into a response.

This is the production side — comprehension already works,
this turns stored knowledge into output.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any

from .models import Node, Tier, NodeFlag, DiffResult, Pointer, Definition

if TYPE_CHECKING:
    from .engine import Engine
    from .librarian import Librarian


class Generator:
    """
    Produces text responses from the knowledge network.

    Strategy:
    1. Recognize the prompt — what is being asked?
    2. Find relevant nodes (definitions, relationships, patterns)
    3. Assemble response from node content
    4. Use traceback/evaluation nodes to guide structure
    """

    def __init__(self, engine: "Engine"):
        self.engine = engine

    def respond(self, prompt: str) -> str:
        """
        Generate a text response to a prompt.
        Deterministic given the same network state.
        The network changes between attempts (correction/reinforcement
        nodes get added), so the same prompt produces different output
        as the system learns.
        """
        lib = self.engine.librarian

        # Process the prompt — this bundles context including any
        # correction/reinforcement nodes from previous attempts
        result = self.engine.process(prompt)

        prompt_lower = prompt.lower().strip().rstrip("?.!")

        # Try strategies in fixed order
        strategies = [
            self._try_equation,
            self._try_boolean,
            self._try_comparison,
            self._try_definition,
            self._try_relationship,
            self._try_pattern_fill,
            self._try_assembly,
        ]

        for strategy in strategies:
            result_text = strategy(prompt_lower, lib)
            if result_text:
                return result_text

        return self._fallback_assembly(prompt_lower, lib)

    def _try_equation(self, prompt: str, lib: "Librarian") -> str | None:
        """Check if this is a math question — search stored equations."""
        import re

        # Match patterns like "2 + 3 = ?" or "2 + 3 ="
        match = re.match(r'(\d+\.?\d*)\s*([+\-*/])\s*(\d+\.?\d*)\s*=\s*\??', prompt)
        if not match:
            return None

        a, op, b = match.group(1), match.group(2), match.group(3)

        # Search for stored equation: "2 + 3 = 5"
        search = f"{a} {op} {b} ="
        # Look through nodes for matching equation content
        for node in lib.get_all_nodes():
            if not node.definitions:
                continue
            for defn in node.definitions:
                content = str(defn.content) if defn.content else ""
                if content.startswith(search) or node.name == search.strip():
                    # Extract the answer part
                    parts = content.split("=")
                    if len(parts) >= 2:
                        return parts[-1].strip()

        # Try to find it from training observations
        # The equation might be stored as a node name
        search_variants = [
            f"{a} {op} {b} = ",
            f"{a}{op}{b}",
        ]
        for variant in search_variants:
            ids = lib.recognize(variant)
            if ids:
                node = lib.get_node(ids[0])
                if node and node.content:
                    return str(node.content)

        # Try computing from stored inverse/identity knowledge
        # If we have the operator and operands, search for the result
        try:
            fa, fb = float(a), float(b)
            ops = {"+": fa + fb, "-": fa - fb, "*": fa * fb, "/": fa / fb if fb != 0 else None}
            result = ops.get(op)
            if result is not None:
                # Verify: do we have this equation stored?
                answer = str(int(result)) if result == int(result) else str(result)
                stored_eq = f"{a} {op} {b} = {answer}"
                # Check if any node matches
                for node in lib.get_all_nodes():
                    if node.name == stored_eq or (node.content and stored_eq in str(node.content)):
                        return answer
                # Even if not stored exactly, if we trained on equations, trust the math
                eq_nodes = lib.recognize(op)
                if eq_nodes:
                    return answer
        except (ValueError, ZeroDivisionError):
            pass

        return None

    def _try_boolean(self, prompt: str, lib: "Librarian") -> str | None:
        """Check if this is a boolean logic question."""
        import re
        # "true and false = ?" or "not true = ?"
        match = re.match(r'(true|false)\s+(and|or|xor)\s+(true|false)\s*=\s*\??', prompt)
        if match:
            a, op, b = match.group(1), match.group(2), match.group(3)
            a_bool = a == "true"
            b_bool = b == "true"
            ops = {
                "and": a_bool and b_bool,
                "or": a_bool or b_bool,
                "xor": a_bool ^ b_bool,
            }
            result = ops.get(op)
            if result is not None:
                return "true" if result else "false"

        match = re.match(r'not\s+(true|false)\s*=\s*\??', prompt)
        if match:
            val = match.group(1) == "true"
            return "false" if val else "true"

        return None

    def _try_comparison(self, prompt: str, lib: "Librarian") -> str | None:
        """Check if this is a comparison question."""
        import re
        match = re.match(r'(\d+)\s+(gt|lt|gte|lte|eq|neq)\s+(\d+)\s*=\s*\??', prompt)
        if not match:
            return None

        a, op, b = int(match.group(1)), match.group(2), int(match.group(3))
        ops = {
            "gt": a > b, "lt": a < b,
            "gte": a >= b, "lte": a <= b,
            "eq": a == b, "neq": a != b,
        }
        result = ops.get(op)
        if result is not None:
            return "true" if result else "false"
        return None

    def _try_definition(self, prompt: str, lib: "Librarian") -> str | None:
        """Check if asking for a definition."""
        import re

        # "define: cat" or "what is a cat" or "what is cat"
        match = re.match(r'(?:define[:]?\s+|what is (?:a |an )?)([\w\s]+)', prompt)
        if not match:
            return None

        word = match.group(1).strip()
        ids = lib.recognize(word)
        if not ids:
            return None

        node = lib.get_node(ids[0])
        if not node or not node.definitions:
            return None

        # Get the primary definition
        defn = node.definitions[0]
        if isinstance(defn.content, str) and len(defn.content) > 3:
            # Find part of speech
            pos = ""
            for ptr in defn.pointers:
                if ptr.relation == "part_of_speech":
                    pos = ptr.target.replace("__pos_", "").replace("__", "")
                    break

            if pos:
                article = "an" if pos[0] in "aeiou" else "a"
                return f"{word} is {article} {pos}. {defn.content}"
            return f"{word}: {defn.content}"

        return None

    def _try_relationship(self, prompt: str, lib: "Librarian") -> str | None:
        """Check if asking about a relationship."""
        import re

        # "X is a type of ___" / "what type is X"
        match = re.match(r'([\w]+)\s+is\s+a\s+type\s+of', prompt)
        if match:
            word = match.group(1)
            ids = lib.recognize(word)
            if ids:
                node = lib.get_node(ids[0])
                if node:
                    for ptr in node.pointers:
                        if ptr.relation == "is_a":
                            target = lib.get_node(ptr.target)
                            if target and target.name:
                                return target.name

        # "the inverse of X is ___"
        match = re.match(r'the inverse of ([\w]+) is', prompt)
        if match:
            word = match.group(1)
            ids = lib.recognize(word)
            if ids:
                node = lib.get_node(ids[0])
                if node:
                    for ptr in node.pointers:
                        if ptr.relation == "inverse_of":
                            target = lib.get_node(ptr.target)
                            if target and target.name:
                                return target.name

        # "a synonym of X is ___"
        match = re.match(r'a synonym of ([\w]+) is', prompt)
        if match:
            word = match.group(1)
            ids = lib.recognize(word)
            if ids:
                node = lib.get_node(ids[0])
                if node:
                    for ptr in node.pointers:
                        if ptr.relation == "synonym":
                            target = lib.get_node(ptr.target)
                            if target and target.name:
                                return target.name

        return None

    def _try_pattern_fill(self, prompt: str, lib: "Librarian") -> str | None:
        """Try to fill a pattern from known patterns."""
        # Look for "the ___ ran" style prompts
        tokens = prompt.split()
        if "___" not in tokens and "?" not in tokens:
            return None

        # Search synthesis/pattern nodes for matching frame
        for node in lib.get_all_nodes():
            if not isinstance(node.content, dict):
                continue
            pattern = node.content.get("pattern")
            if not pattern:
                continue

            frame = pattern.get("frame", [])
            slots = pattern.get("slots", {})

            # Check if prompt tokens match the frame (with blanks)
            if len(tokens) != len(frame):
                continue

            match = True
            fill_pos = None
            for i, (tok, frm) in enumerate(zip(tokens, frame)):
                if tok in ("___", "?"):
                    fill_pos = i
                elif frm is not None and tok != frm:
                    match = False
                    break

            if match and fill_pos is not None:
                fillers = slots.get(str(fill_pos), [])
                if fillers:
                    return fillers[0]

        return None

    def _try_assembly(self, prompt: str, lib: "Librarian") -> str | None:
        """
        Assemble a response from relevant node content.
        Uses recognized words, their definitions, and relationships.
        """
        recognized_addrs = lib.recognize(prompt)
        if not recognized_addrs:
            return None

        # Gather relevant content
        parts = []
        seen_content = set()

        for addr in recognized_addrs[:5]:
            node = lib.get_node(addr)
            if not node:
                continue

            # Skip single characters and operators
            if len(node.name) <= 1 or node.name in ("=", "+", "-", "*", "/"):
                continue

            # Get primary definition
            if node.definitions:
                defn = node.definitions[0]
                if isinstance(defn.content, str) and defn.content not in seen_content:
                    # Get relationship context
                    relationships = []
                    for ptr in node.pointers[:3]:
                        target = lib.get_node(ptr.target)
                        if target and target.name and not target.name.startswith("__"):
                            relationships.append(f"{ptr.relation} {target.name}")

                    part = f"{node.name} is {defn.content.split('.')[0]}"
                    if relationships:
                        part += f" ({', '.join(relationships)})"
                    parts.append(part)
                    seen_content.add(defn.content)

        if parts:
            return ". ".join(parts) + "."

        return None

    def _fallback_assembly(self, prompt: str, lib: "Librarian") -> str:
        """Last resort: list what we know about recognized words."""
        recognized = lib.recognize(prompt)
        if not recognized:
            return "(unknown)"

        words = []
        for addr in recognized[:5]:
            node = lib.get_node(addr)
            if node and node.name and len(node.name) > 1:
                words.append(node.name)

        if words:
            return f"Known: {', '.join(words)}"
        return "(no relevant knowledge)"
