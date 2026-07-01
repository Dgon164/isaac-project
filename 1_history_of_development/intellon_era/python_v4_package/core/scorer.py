"""
Intellon v4 — Scoring Engine

Every response gets a score. The system optimizes this score.

    score = (relevant_facts × prompt_coverage²) / log(words + 1) × speed

This rewards:
  - Correctness: verified relevant facts = higher numerator
  - Coverage: addressing the prompt = squared multiplier
  - Brevity: log penalty — soft discount, not crushing
  - Speed: faster processing = bonus multiplier

The score is computed entirely from the register's notepad.
Only facts RELEVANT to the prompt count — no gaming by
triggering unrelated rule matches.
"""

from __future__ import annotations
import math
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .models import Node, Tier, NodeFlag, DiffResult

if TYPE_CHECKING:
    from .engine import Engine
    from .librarian import Librarian


@dataclass
class ResponseScore:
    """Score breakdown for a single response."""
    # Raw counts from the register
    rules_matched: int = 0          # SAME against rule/meta nodes
    rules_checked: int = 0          # total comparisons against rule nodes
    facts_confirmed: int = 0        # SAME against knowledge nodes
    facts_checked: int = 0          # total comparisons against knowledge nodes
    words_used: int = 0             # response word count
    words_verified: int = 0         # words the system recognizes in its own output
    processing_ms: float = 0.0      # how long it took
    relevant_facts: int = 0         # facts connected to prompt words (not all facts)
    prompt_coverage: float = 0.0    # ratio of prompt keywords addressed

    # Computed scores
    precision: float = 0.0          # verified_words / total_words
    accuracy: float = 0.0           # facts_confirmed / facts_checked
    structure: float = 0.0          # rules_matched / rules_checked
    density: float = 0.0            # (rules + facts) / words
    speed_bonus: float = 1.0        # faster = higher

    # Final
    score: float = 0.0
    explanation: str = ""

    @property
    def grade(self) -> str:
        """Letter grade for quick readability."""
        if self.score >= 50: return "S"
        if self.score >= 30: return "A"
        if self.score >= 15: return "B"
        if self.score >= 8: return "C"
        if self.score >= 3: return "D"
        return "F"


@dataclass
class ScoreBoard:
    """Cumulative tracking of system performance."""
    total_score: float = 0.0
    total_responses: int = 0
    total_rules_matched: int = 0
    total_facts_confirmed: int = 0
    total_words: int = 0
    best_score: float = 0.0
    best_response: str = ""
    best_prompt: str = ""
    streak: int = 0                 # consecutive improvements
    longest_streak: int = 0
    history: list[float] = field(default_factory=list)

    @property
    def average_score(self) -> float:
        return self.total_score / self.total_responses if self.total_responses else 0.0

    @property
    def words_per_fact(self) -> float:
        return self.total_words / self.total_facts_confirmed if self.total_facts_confirmed else float('inf')


class Scorer:
    """
    Scores every response using the register's own differentiation results.
    Maintains a running scoreboard.
    """

    def __init__(self, engine: "Engine"):
        self.engine = engine
        self.board = ScoreBoard()

    def score_response(self, prompt: str, response: str,
                       processing_time: float = 0.0) -> ResponseScore:
        """
        Score a response by running it through the register against
        the system's knowledge. Returns detailed breakdown.
        """
        lib = self.engine.librarian
        result = ResponseScore()

        # Tokenize response
        tokens = [t.strip(".,!?;:'\"").lower() for t in response.split() if t.strip(".,!?;:'\"")]
        result.words_used = len(tokens) if tokens else 1  # avoid div by zero
        result.processing_ms = processing_time * 1000

        if not tokens:
            result.explanation = "empty response"
            return result

        # Count verified words (system recognizes its own output)
        for token in tokens:
            ids = lib.recognize(token)
            if ids:
                result.words_verified += 1

        # Identify prompt keywords (skip function words)
        skip = {"a", "an", "the", "is", "are", "was", "what", "how", "why",
                "who", "where", "when", "do", "does", "did", "can", "will",
                "of", "in", "on", "at", "to", "for", "with", "by", "about",
                "it", "be", "this", "that", "and", "or", "but", "not"}
        prompt_tokens = [t.strip(".,!?;:'\"").lower() for t in prompt.split()
                         if t.strip(".,!?;:'\"").lower() not in skip]

        # Build set of node IDs relevant to the prompt
        prompt_node_ids = set()
        for token in prompt_tokens:
            ids = lib.recognize(token)
            for nid in ids:
                prompt_node_ids.add(nid)
                node = lib.get_node(nid)
                if node:
                    # Include direct pointer targets — one hop of relevance
                    for ptr in node.pointers[:20]:
                        prompt_node_ids.add(ptr.target)

        # Run the response through the engine to get notepad records
        engine_result = self.engine.process(response)

        # Classify notepad records — only count RELEVANT matches
        for record in engine_result.notepad:
            ctx_node = lib.get_node(record.slot_b)
            if not ctx_node:
                continue

            is_rule = self._is_rule_node(ctx_node)
            is_fact = self._is_fact_node(ctx_node)
            is_relevant = ctx_node.id in prompt_node_ids

            if is_rule:
                result.rules_checked += 1
                if record.result == DiffResult.SAME:
                    result.rules_matched += 1
            elif is_fact:
                result.facts_checked += 1
                if record.result == DiffResult.SAME:
                    result.facts_confirmed += 1
                    if is_relevant:
                        result.relevant_facts += 1

        # Prompt coverage: how many key prompt words addressed in response?
        response_set = set(tokens)
        response_node_ids = set()
        for t in tokens:
            ids = lib.recognize(t)
            for nid in ids:
                response_node_ids.add(nid)
                node = lib.get_node(nid)
                if node:
                    for ptr in node.pointers[:10]:
                        response_node_ids.add(ptr.target)

        addressed = 0
        for word in prompt_tokens:
            if word in response_set:
                addressed += 1
            else:
                ids = lib.recognize(word)
                if ids and any(nid in response_node_ids for nid in ids):
                    addressed += 0.7
        result.prompt_coverage = addressed / len(prompt_tokens) if prompt_tokens else 0.5

        # Compute component scores
        result.precision = result.words_verified / result.words_used
        result.accuracy = result.facts_confirmed / result.facts_checked if result.facts_checked else 0.0
        result.structure = result.rules_matched / result.rules_checked if result.rules_checked else 0.0
        result.density = result.relevant_facts / result.words_used

        # Speed bonus: under 100ms = 2x, under 50ms = 3x, over 500ms = 0.5x
        if result.processing_ms < 50:
            result.speed_bonus = 3.0
        elif result.processing_ms < 100:
            result.speed_bonus = 2.0
        elif result.processing_ms < 200:
            result.speed_bonus = 1.5
        elif result.processing_ms < 500:
            result.speed_bonus = 1.0
        else:
            result.speed_bonus = 0.5

        # FINAL SCORE
        # relevant_facts × prompt_coverage² / log(words+1) × speed
        # - Only facts connected to the prompt count (no gaming)
        # - Coverage squared so ignoring the question kills score
        # - Log softly discounts length without crushing long accurate answers
        # - Speed rewards efficiency
        coverage_sq = result.prompt_coverage ** 2
        log_words = math.log(result.words_used + 1)
        raw = (result.relevant_facts * coverage_sq) / log_words
        result.score = raw * result.speed_bonus

        # Build explanation
        parts = []
        parts.append(f"{result.relevant_facts}rf×{result.prompt_coverage:.0%}cov²/log({result.words_used}+1)")
        if result.speed_bonus != 1.0:
            parts.append(f"×{result.speed_bonus:.0f}spd")
        parts.append(f"= {result.score:.1f}")
        if result.precision >= 0.8:
            parts.append("precise")
        if result.density >= 0.5:
            parts.append("dense")
        if result.prompt_coverage >= 0.8:
            parts.append("on-topic")
        if result.prompt_coverage < 0.3:
            parts.append("off-topic")
        result.explanation = " | ".join(parts)

        # Update scoreboard
        self._update_board(prompt, response, result)

        return result

    def _is_rule_node(self, node: Node) -> bool:
        """Is this a rule/meta/structure node?"""
        # Check if it's a meta-knowledge node
        if isinstance(node.content, dict):
            ntype = node.content.get("type")
            if ntype in ("evaluation", "reinforcement", "correction",
                         "observation", "traceback"):
                return True

        # Check for meta pointer
        for defn in node.definitions:
            for ptr in defn.pointers:
                if ptr.target == "__type_meta__":
                    return True

        # Check name patterns
        rule_names = {"accuracy", "fluency", "completeness", "relevance",
                      "coherence", "scoring", "sentence structure",
                      "eq", "neq", "gt", "lt", "gte", "lte",
                      "and", "or", "not", "xor"}
        return node.name.lower() in rule_names

    def _is_fact_node(self, node: Node) -> bool:
        """Is this a knowledge/fact node?"""
        # Has definitions from WordNet = knowledge
        if node.definitions and node.tier in (Tier.IMPORTANT, Tier.VALIDATED):
            for defn in node.definitions:
                if isinstance(defn.content, str) and len(defn.content) > 5:
                    return True

        # Has relationship pointers = structural knowledge
        if node.pointers and node.tier <= Tier.VALIDATED:
            fact_relations = {"is_a", "has_type", "synonym", "part_of",
                              "has_part", "inverse_of"}
            for ptr in node.pointers:
                if ptr.relation in fact_relations:
                    return True

        return False

    def _update_board(self, prompt: str, response: str, result: ResponseScore):
        """Update the cumulative scoreboard."""
        self.board.total_score += result.score
        self.board.total_responses += 1
        self.board.total_rules_matched += result.rules_matched
        self.board.total_facts_confirmed += result.facts_confirmed
        self.board.total_words += result.words_used

        if result.score > self.board.best_score:
            self.board.best_score = result.score
            self.board.best_response = response[:100]
            self.board.best_prompt = prompt[:100]

        # Streak tracking
        if self.board.history and result.score > self.board.history[-1]:
            self.board.streak += 1
            self.board.longest_streak = max(self.board.longest_streak, self.board.streak)
        else:
            self.board.streak = 0

        self.board.history.append(result.score)
        # Keep last 1000
        if len(self.board.history) > 1000:
            self.board.history = self.board.history[-1000:]

    def format_board(self) -> str:
        """Format the scoreboard for display."""
        b = self.board
        lines = [
            f"SCORE: {b.total_score:.0f}",
            f"Responses: {b.total_responses}",
            f"Avg score: {b.average_score:.1f}",
            f"Best: {b.best_score:.1f} ({b.best_prompt[:30]}...)",
            f"Rules matched: {b.total_rules_matched}",
            f"Facts confirmed: {b.total_facts_confirmed}",
            f"Words/fact: {b.words_per_fact:.1f}",
            f"Streak: {b.streak} (best: {b.longest_streak})",
        ]
        # Trend
        if len(b.history) >= 10:
            recent = b.history[-10:]
            older = b.history[-20:-10] if len(b.history) >= 20 else b.history[:10]
            trend = sum(recent) / len(recent) - sum(older) / len(older)
            if trend > 0:
                lines.append(f"Trend: ↑ improving (+{trend:.1f})")
            elif trend < 0:
                lines.append(f"Trend: ↓ declining ({trend:.1f})")
            else:
                lines.append("Trend: → steady")

        return "\n".join(lines)
