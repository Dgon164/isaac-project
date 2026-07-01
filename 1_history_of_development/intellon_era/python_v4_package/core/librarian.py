"""
Intellon v4 — Librarian

The sole authority over the knowledge structure. Sees the full picture.
Does NOT reason, evaluate meaning, or resolve conflicts.
Five functions: recognition, delivery, integration, mapping, conflict detection.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import uuid

from .models import (
    Node, NodeFlag, Tier, DiffRecord, Assignment, ReturnPackage,
    Pointer, Origin, NodeContext,
)


@dataclass
class TransactionRecord:
    session_id: str
    timestamp: datetime
    input_assignment: Assignment
    requests_made: list[str]
    stubs_created: list[str]
    synthesis_id: str | None
    verification_passed: bool
    integration_result: str  # "accepted", "conflict", "merged"


@dataclass
class Conflict:
    new_node_id: str
    existing_node_id: str
    aspect: str
    detail: str


class Librarian:
    """
    Index clerk + cartographer. Never reasons. Never interprets.
    """

    def __init__(self):
        # The network: all nodes by address
        self._nodes: dict[str, Node] = {}
        # Word/token index for recognition: content -> [node addresses]
        self._index: dict[str, list[str]] = {}
        # Foundation node addresses (auto-loaded in every assignment)
        self._foundation: set[str] = set()
        # Transaction log (append-only)
        self._log: list[TransactionRecord] = []
        # Pending conflict assignments
        self._conflict_queue: list[Assignment] = []
        # Promotion thresholds
        self.promotion_threshold_sessions: int = 20
        self.promotion_threshold_diversity: int = 10
        self.demotion_dormant_sessions: int = 50
        # Cascade control
        self.cascade_limit: int = 5
        # Training mode: when True, new nodes enter at _training_tier instead of TRIAL
        self._training_mode: bool = False
        self._training_tier: Tier = Tier.TRIAL
        # Adaptive bundling: top-k selection with rolling time optimization
        self._top_k: int = 25              # max context nodes to send
        self._walk_depth: int = 2          # how many pointer levels to explore
        self._time_history: list[float] = []  # rolling processing times
        self._time_window: int = 20        # how many samples to average

    # ------------------------------------------------------------------
    # Node storage
    # ------------------------------------------------------------------

    def store_node(self, node: Node):
        """Add or update a node in the network."""
        self._nodes[node.id] = node
        # Index the content for recognition
        self._index_node(node)

    def get_node(self, address: str) -> Node | None:
        return self._nodes.get(address)

    def _index_node(self, node: Node):
        """Index node by name for fast lookup during recognition."""
        key = node.name.lower().strip() if node.name else ""
        if key:
            if key not in self._index:
                self._index[key] = []
            if node.id not in self._index[key]:
                self._index[key].append(node.id)

    # ------------------------------------------------------------------
    # Recognition — the word lookup
    # ------------------------------------------------------------------

    def recognize(self, raw_input: Any) -> list[str]:
        """
        Pattern-match input against known node identifiers.
        This is a word lookup, not semantic retrieval.
        "the cat ran" -> look up "the" (miss), "cat" (hit), "ran" (miss).
        """
        recognized = []

        if isinstance(raw_input, str):
            tokens = raw_input.lower().split()
            for token in tokens:
                clean = token.strip(".,!?;:'\"")
                if clean in self._index:
                    recognized.extend(self._index[clean])
        elif isinstance(raw_input, list):
            for item in raw_input:
                recognized.extend(self.recognize(item))

        return list(set(recognized))  # deduplicate

    def _walk_connections(self, addresses: list[str], depth: int = 2) -> list[str]:
        """
        From recognized nodes, walk pointers and SCORE each candidate.
        Returns only top-k most relevant nodes, not everything reachable.
        Depth and k adapt based on rolling average processing time.
        """
        if not addresses:
            return list(addresses)

        # Score every reachable node
        scores: dict[str, float] = {}
        # Recognized nodes get base score
        for addr in addresses:
            scores[addr] = 10.0

        frontier = set(addresses)
        visited = set(addresses)

        for level in range(self._walk_depth):
            next_frontier = set()
            decay = 1.0 / (level + 1)  # deeper = less relevant

            for addr in frontier:
                node = self._nodes.get(addr)
                if not node:
                    continue
                for ptr in node.pointers:
                    target = ptr.target
                    if target not in self._nodes:
                        continue

                    target_node = self._nodes[target]

                    # Score based on:
                    # 1. Hop distance (closer = higher)
                    hop_score = 5.0 * decay

                    # 2. Co-occurrence with recognized words (sessions_involved)
                    usage_score = min(target_node.tallies.get("sessions_involved", 0) / 10.0, 3.0)

                    # 3. Relationship type (is_a, synonym more useful than distant relations)
                    rel_weights = {"is_a": 2.0, "synonym": 2.0, "has_type": 1.5,
                                   "part_of": 1.0, "has_part": 1.0, "inverse_of": 1.5}
                    rel_score = rel_weights.get(ptr.relation, 0.5)

                    # 4. Definition richness (more definitions = more useful context)
                    def_score = min(len(target_node.definitions) / 5.0, 1.0)

                    total = hop_score + usage_score + rel_score + def_score

                    if target not in scores or total > scores[target]:
                        scores[target] = total

                    if target not in visited:
                        visited.add(target)
                        next_frontier.add(target)

            frontier = next_frontier
            if not frontier:
                break

        # Take top k by score
        ranked = sorted(scores.items(), key=lambda x: -x[1])
        top_addrs = [addr for addr, score in ranked[:self._top_k]]

        return top_addrs

    # ------------------------------------------------------------------
    # Adaptive tuning
    # ------------------------------------------------------------------

    def report_processing_time(self, elapsed: float):
        """Called after each register cycle. Adjusts k and depth to hit target time."""
        self._time_history.append(elapsed)
        if len(self._time_history) > self._time_window:
            self._time_history.pop(0)

        if len(self._time_history) < 3:
            return  # Not enough data yet

        avg = sum(self._time_history) / len(self._time_history)

        # Target: 50-200ms per processing cycle
        if avg > 0.2 and self._top_k > 5:
            # Too slow — tighten
            self._top_k = max(5, self._top_k - 5)
            if self._top_k <= 10 and self._walk_depth > 1:
                self._walk_depth = max(1, self._walk_depth - 1)
                self._top_k = min(self._top_k + 10, 50)
        elif avg < 0.05 and self._top_k < 100:
            # Fast — loosen
            self._top_k = min(100, self._top_k + 5)
            if self._top_k >= 40 and self._walk_depth < 4:
                self._walk_depth += 1

    # ------------------------------------------------------------------
    # Bundling
    # ------------------------------------------------------------------

    def bundle(self, raw_input: Any) -> Assignment:
        """
        Full recognition + bundling pipeline.
        1. Recognize input tokens against index
        2. Walk connections from recognized nodes
        3. Gather foundation nodes
        4. Package into assignment
        """
        recognized_addrs = self.recognize(raw_input)
        context_addrs = self._walk_connections(recognized_addrs)

        foundation_nodes = [
            self._nodes[addr] for addr in self._foundation
            if addr in self._nodes
        ]
        context_nodes = [
            self._nodes[addr] for addr in context_addrs
            if addr in self._nodes
        ]
        flagged = [
            addr for addr in context_addrs
            if addr in self._nodes and self._nodes[addr].has_flag(NodeFlag.REVIEW)
        ]

        return Assignment(
            foundation=foundation_nodes,
            context=context_nodes,
            input_raw=raw_input,
            metadata={
                "recognized": recognized_addrs,
                "flagged": flagged,
            },
        )

    # ------------------------------------------------------------------
    # Delivery (register request channel)
    # ------------------------------------------------------------------

    def deliver(self, address: str) -> Node | None:
        """Respond to a register's mid-process request."""
        node = self._nodes.get(address)
        if node:
            node.tally("delivered")
        return node

    # ------------------------------------------------------------------
    # Integration
    # ------------------------------------------------------------------

    def integrate(self, package: ReturnPackage) -> str:
        """
        Process everything a register hands back.
        - Classify and place stub nodes
        - Check synthesis for novelty and consistency
        - Connect, flag, timestamp, log
        Returns: "accepted", "conflict", or "observation"
        """
        result = "observation"

        # 1. Integrate stub nodes
        for stub in package.stubs:
            self._classify_stub(stub, package.session_id)

        # 2. Integrate synthesis if present
        if package.synthesis:
            conflicts = self._check_network_conflicts(package.synthesis)
            if conflicts:
                result = "conflict"
                for conflict in conflicts:
                    self._create_conflict_assignment(conflict, package)
            else:
                self._accept_synthesis(package.synthesis, package.session_id)
                result = "accepted"

        # 3. Update tallies for all nodes that were part of this session
        self._update_session_tallies(package)

        # 4. Log
        self._log.append(TransactionRecord(
            session_id=package.session_id,
            timestamp=datetime.utcnow(),
            input_assignment=Assignment(id=package.session_id),  # simplified
            requests_made=package.requests,
            stubs_created=[s.id for s in package.stubs],
            synthesis_id=package.synthesis.id if package.synthesis else None,
            verification_passed=package.verification.passed,
            integration_result=result,
        ))

        return result

    def _classify_stub(self, stub: Node, session_id: str):
        """
        Take a raw stub from a register and give it a place in the network.
        Assign tier, flags, check for duplicates, connect to related nodes.
        """
        # Check if we already have a node with identical name
        existing = self._find_duplicate(stub)
        if existing:
            # Merge: update tallies and context on existing node
            existing.tally("referenced")
            existing.tally(f"session_{session_id}")
            if NodeFlag.STUB in existing.flags:
                existing.flags.discard(NodeFlag.STUB)
                existing.flags.add(NodeFlag.ACTIVE)
            return

        # New node: classify and store
        stub.flags.discard(NodeFlag.STUB)
        stub.flags.add(NodeFlag.ACTIVE)
        if self._training_mode:
            stub.tier = self._training_tier
        else:
            stub.tier = Tier.TRIAL
        stub.tally("created")
        self.store_node(stub)

    def _find_duplicate(self, node: Node) -> Node | None:
        """Check if a node with the same name already exists."""
        key = node.name.lower().strip() if node.name else ""
        if key and key in self._index:
            for addr in self._index[key]:
                existing = self._nodes.get(addr)
                if existing and existing.name.lower() == node.name.lower():
                    return existing
        return None

    def _check_network_conflicts(self, synthesis: Node) -> list[Conflict]:
        """
        Check a synthesis against the existing network.
        Does NOT resolve — just detects.
        """
        conflicts = []

        if not synthesis.constraints:
            return conflicts

        for constraint in synthesis.constraints:
            # Look for nodes that contradict this constraint
            for addr, node in self._nodes.items():
                if node.has_flag(NodeFlag.TRUSTED):
                    for existing_c in node.constraints:
                        if (existing_c.subject == constraint.subject
                                and existing_c.relation == constraint.relation
                                and existing_c.object == constraint.object
                                and existing_c.polarity != constraint.polarity):
                            conflicts.append(Conflict(
                                new_node_id=synthesis.id,
                                existing_node_id=node.id,
                                aspect=f"{constraint.subject}.{constraint.relation}",
                                detail=f"new={constraint.polarity} existing={existing_c.polarity}",
                            ))
        return conflicts

    def _create_conflict_assignment(self, conflict: Conflict, original_package: ReturnPackage):
        """Bundle both sides of a conflict for register resolution."""
        new_node = self._nodes.get(conflict.new_node_id) or original_package.synthesis
        existing_node = self._nodes.get(conflict.existing_node_id)

        if new_node and existing_node:
            assignment = Assignment(
                foundation=[
                    self._nodes[addr] for addr in self._foundation
                    if addr in self._nodes
                ],
                context=[new_node, existing_node],
                input_raw={
                    "type": "conflict_resolution",
                    "new_node": conflict.new_node_id,
                    "existing_node": conflict.existing_node_id,
                    "aspect": conflict.aspect,
                },
                metadata={
                    "recognized": [conflict.new_node_id, conflict.existing_node_id],
                    "flagged": [conflict.existing_node_id],
                },
            )
            self._conflict_queue.append(assignment)

            # Flag existing node for review
            if existing_node:
                existing_node.flags.add(NodeFlag.REVIEW)

    def _accept_synthesis(self, synthesis: Node, session_id: str):
        """Accept a synthesis into the network."""
        synthesis.flags.discard(NodeFlag.STUB)
        synthesis.flags.add(NodeFlag.ACTIVE)
        synthesis.tally("accepted")
        self.store_node(synthesis)

    def _update_session_tallies(self, package: ReturnPackage):
        """Update usage tallies for nodes involved in this session."""
        seen_addrs = set()
        for record in package.notepad:
            seen_addrs.add(record.slot_a)
            seen_addrs.add(record.slot_b)
        for addr in seen_addrs:
            node = self._nodes.get(addr)
            if node:
                node.tally("referenced")
                node.tally("sessions_involved")

    # ------------------------------------------------------------------
    # Conflict queue
    # ------------------------------------------------------------------

    def has_pending_conflicts(self) -> bool:
        return len(self._conflict_queue) > 0

    def next_conflict_assignment(self) -> Assignment | None:
        if self._conflict_queue:
            return self._conflict_queue.pop(0)
        return None

    # ------------------------------------------------------------------
    # Foundation promotion / demotion
    # ------------------------------------------------------------------

    def set_training_mode(self, enabled: bool, tier: Tier = Tier.TRIAL):
        """Enable/disable training mode. Trusted data enters at specified tier."""
        self._training_mode = enabled
        self._training_tier = tier

    def promote(self, address: str):
        """Move a node up one tier (lower number = higher trust). Add foundation flag."""
        node = self._nodes.get(address)
        if node and node.tier > Tier.INITIATOR:
            node.tier = Tier(node.tier - 1)
            if node.tier == Tier.INITIATOR:
                node.flags.add(NodeFlag.FOUNDATION)
                self._foundation.add(address)

    def demote(self, address: str):
        """Move a node down one tier. Remove foundation flag if demoted from Initiator."""
        node = self._nodes.get(address)
        if node and node.tier < Tier.TRIAL:
            if node.tier == Tier.INITIATOR:
                node.flags.discard(NodeFlag.FOUNDATION)
                self._foundation.discard(address)
            node.tier = Tier(node.tier + 1)

    def set_foundation(self, address: str):
        """Mark a node as foundation (auto-loaded in every assignment). Does not change tier."""
        node = self._nodes.get(address)
        if node:
            node.flags.add(NodeFlag.FOUNDATION)
            self._foundation.add(address)

    def check_promotions(self):
        """
        Background cartography: check which nodes should be promoted or demoted.
        Based on cross-session diversity of use.
        Tier 1 (Initiator) nodes are never demoted.
        """
        for addr, node in self._nodes.items():
            sessions = node.tallies.get("sessions_involved", 0)

            # Promote: enough diverse usage without contradiction
            if node.tier > Tier.IMPORTANT and sessions >= self.promotion_threshold_sessions:
                session_keys = [k for k in node.tallies if k.startswith("session_")]
                if len(session_keys) >= self.promotion_threshold_diversity:
                    self.promote(addr)

            # Demote: dormant non-initiator nodes
            elif (node.tier > Tier.INITIATOR
                    and node.tier < Tier.TRIAL
                    and node.tallies.get("referenced", 0) == 0
                    and node.tallies.get("delivered", 0) > self.demotion_dormant_sessions):
                self.demote(addr)

    # ------------------------------------------------------------------
    # Archive
    # ------------------------------------------------------------------

    def archive(self, address: str):
        node = self._nodes.get(address)
        if node:
            node.flags.add(NodeFlag.ARCHIVED)
            node.flags.discard(NodeFlag.ACTIVE)

    # ------------------------------------------------------------------
    # Stats / inspection
    # ------------------------------------------------------------------

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    @property
    def foundation_count(self) -> int:
        return len(self._foundation)

    @property
    def session_count(self) -> int:
        return len(self._log)

    def get_all_nodes(self) -> list[Node]:
        return list(self._nodes.values())

    def get_log(self) -> list[TransactionRecord]:
        return list(self._log)
