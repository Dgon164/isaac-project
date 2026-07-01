"""
Intellon v4 — Self Judge

Scores the system's own output by differentiating it against
what it knows about language. No external LLM needed.

Scoring dimensions:
  - Recognition: how many output words does the system know?
  - Structure: does it match known sentence patterns?
  - Relationships: are the word connections valid?
  - Completeness: does it address the prompt words?
  - Coherence: do the words belong together based on co-occurrence?

Each score comes from the register doing what it does:
comparing the output against stored knowledge and counting
SAME vs DIFFERENT.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from .models import Node, Tier, NodeFlag, DiffResult

if TYPE_CHECKING:
    from .engine import Engine
    from .librarian import Librarian


class SelfJudge:
    """
    Scores output using the system's own knowledge network.
    The scoring IS differentiation — the native operation.
    """

    def __init__(self, engine: "Engine"):
        self.engine = engine
        self._call_count = 0

    def evaluate(self, prompt: str, response: str) -> "EvalScore":
        """Score a response against what the system knows."""
        from .evaluator import EvalScore

        self._call_count += 1
        lib = self.engine.librarian

        if not response or response in ("(unknown)", "(no relevant knowledge)"):
            return EvalScore(accuracy=1, fluency=1, completeness=1, relevance=1,
                             note="No response produced")

        # Tokenize
        response_tokens = [t.strip(".,!?;:'\"").lower() for t in response.split() if t.strip(".,!?;:'\"")]
        prompt_tokens = [t.strip(".,!?;:'\"").lower() for t in prompt.split() if t.strip(".,!?;:'\"")]

        if not response_tokens:
            return EvalScore(accuracy=1, fluency=1, completeness=1, relevance=1,
                             note="Empty response")

        # === RECOGNITION: how many words does the system know? ===
        known_count = 0
        known_nodes = []
        for token in response_tokens:
            ids = lib.recognize(token)
            if ids:
                known_count += 1
                node = lib.get_node(ids[0])
                if node:
                    known_nodes.append(node)

        recognition_ratio = known_count / len(response_tokens) if response_tokens else 0

        # === STRUCTURE: does it match known patterns? ===
        structure_score = self._score_structure(response_tokens, lib)

        # === RELATIONSHIPS: are word connections valid? ===
        relationship_score = self._score_relationships(known_nodes, lib)

        # === COMPLETENESS: does it address the prompt? ===
        completeness_score = self._score_completeness(prompt_tokens, response_tokens, lib)

        # === COHERENCE: do the words belong together? ===
        coherence_score = self._score_coherence(known_nodes, lib)

        # Combine into standard scores (1-10 scale)
        accuracy = max(1, min(10, round(
            recognition_ratio * 5 +      # known words
            relationship_score * 3 +      # valid connections
            coherence_score * 2           # words belong together
        )))

        fluency = max(1, min(10, round(
            structure_score * 6 +         # matches known patterns
            (1 if response.endswith(".") else 0) +  # ends with period
            min(len(response_tokens) / 3, 3)  # reasonable length
        )))

        completeness = max(1, min(10, round(
            completeness_score * 7 +      # addresses prompt
            min(len(response_tokens) / 5, 3)  # enough content
        )))

        relevance = max(1, min(10, round(
            completeness_score * 4 +      # prompt words covered
            coherence_score * 3 +         # words relate to each other
            recognition_ratio * 3         # using known vocabulary
        )))

        # Build explanation
        notes = []
        if recognition_ratio < 0.5:
            notes.append(f"many unknown words ({known_count}/{len(response_tokens)})")
        if structure_score < 0.3:
            notes.append("doesn't match known sentence patterns")
        if completeness_score < 0.3:
            notes.append("doesn't address the prompt")
        if relationship_score > 0.5:
            notes.append("word relationships are valid")
        if structure_score > 0.6:
            notes.append("follows known structure")
        if not notes:
            notes.append("adequate response")

        return EvalScore(
            accuracy=accuracy,
            fluency=fluency,
            completeness=completeness,
            relevance=relevance,
            note="; ".join(notes),
        )

    def _score_structure(self, tokens: list[str], lib: "Librarian") -> float:
        """
        Check if the token sequence matches known sentence patterns.
        Compare against stored synthesis/pattern nodes.
        """
        if not tokens:
            return 0.0

        scores = []

        # Check for article-noun, article-adjective-noun patterns
        has_article = any(t in ("a", "an", "the") for t in tokens)
        has_verb = False
        has_noun = False

        for token in tokens:
            ids = lib.recognize(token)
            if not ids:
                continue
            node = lib.get_node(ids[0])
            if not node or not node.definitions:
                continue
            for defn in node.definitions[:1]:
                for ptr in defn.pointers:
                    if ptr.relation == "part_of_speech":
                        pos = ptr.target
                        if "verb" in pos:
                            has_verb = True
                        if "noun" in pos:
                            has_noun = True

        # Score based on structural completeness
        structure = 0.0
        if has_article:
            structure += 0.25
        if has_verb:
            structure += 0.35
        if has_noun:
            structure += 0.25
        if len(tokens) >= 3:
            structure += 0.15

        # Check against stored pattern nodes
        for node in lib.get_all_nodes():
            if not isinstance(node.content, dict):
                continue
            pattern = node.content.get("pattern")
            if not pattern:
                continue
            frame = pattern.get("frame", [])
            if not frame or len(frame) != len(tokens):
                continue
            # Count how many frame positions match
            matches = sum(1 for f, t in zip(frame, tokens) if f is not None and f == t)
            if matches > 0:
                pattern_score = matches / len(frame)
                structure = max(structure, pattern_score)

        return min(structure, 1.0)

    def _score_relationships(self, nodes: list[Node], lib: "Librarian") -> float:
        """
        Check if the words in the response have valid relationships.
        Words that point to each other = good. Unrelated words = less good.
        """
        if len(nodes) < 2:
            return 0.5  # Not enough to judge

        # Count how many node pairs have pointers between them
        node_ids = {n.id for n in nodes}
        connections = 0
        pairs = 0

        for i, node_a in enumerate(nodes):
            for node_b in nodes[i + 1:]:
                pairs += 1
                # Check if a points to b or b points to a
                a_targets = {p.target for p in node_a.pointers}
                b_targets = {p.target for p in node_b.pointers}
                if node_b.id in a_targets or node_a.id in b_targets:
                    connections += 1
                # Also check shared targets (both point to same thing)
                elif a_targets & b_targets:
                    connections += 0.5

        return connections / pairs if pairs > 0 else 0.5

    def _score_completeness(self, prompt_tokens: list[str], response_tokens: list[str],
                            lib: "Librarian") -> float:
        """
        How well does the response address the prompt?
        Check if prompt's key words (nouns, verbs) are addressed.
        """
        if not prompt_tokens:
            return 0.5

        # Find meaningful prompt words (skip articles, prepositions)
        skip = {"a", "an", "the", "is", "are", "was", "what", "how", "why",
                "who", "where", "when", "do", "does", "did", "can", "will",
                "of", "in", "on", "at", "to", "for", "with", "by", "about"}

        key_prompt_words = [t for t in prompt_tokens if t not in skip]
        if not key_prompt_words:
            return 0.5

        # How many key prompt words appear in response (directly or via relationship)?
        addressed = 0
        response_set = set(response_tokens)
        response_node_ids = set()
        for t in response_tokens:
            ids = lib.recognize(t)
            if ids:
                response_node_ids.add(ids[0])
                node = lib.get_node(ids[0])
                if node:
                    response_node_ids.update(p.target for p in node.pointers)

        for word in key_prompt_words:
            if word in response_set:
                addressed += 1
            else:
                # Check if addressed via relationship
                ids = lib.recognize(word)
                if ids and ids[0] in response_node_ids:
                    addressed += 0.7

        return addressed / len(key_prompt_words) if key_prompt_words else 0.5

    def _score_coherence(self, nodes: list[Node], lib: "Librarian") -> float:
        """
        Do the words in the response belong together?
        Check co-occurrence: have these nodes appeared in sessions together before?
        """
        if len(nodes) < 2:
            return 0.5

        # Check if nodes have overlapping session tallies
        session_sets = []
        for node in nodes:
            sessions = {k for k in node.tallies if k.startswith("session_")}
            session_sets.append(sessions)

        if not session_sets:
            return 0.3

        # Pairwise session overlap
        overlaps = 0
        pairs = 0
        for i in range(len(session_sets)):
            for j in range(i + 1, len(session_sets)):
                pairs += 1
                overlap = session_sets[i] & session_sets[j]
                if overlap:
                    overlaps += 1

        return overlaps / pairs if pairs > 0 else 0.3

    @property
    def calls_made(self) -> int:
        return self._call_count
