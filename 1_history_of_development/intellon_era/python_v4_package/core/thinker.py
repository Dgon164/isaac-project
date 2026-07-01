"""
Intellon v4 — Autonomous Thinker

The system's self-directed processing loop. When there's no external input,
the system picks its own assignments from what it already knows and looks
for patterns, connections, contradictions, and deeper structure.

The librarian selects what to examine. The register does the work.
Results go back to the librarian. Same cycle, self-generated input.

Think of it as the system's idle thoughts — always running, always looking.
"""

from __future__ import annotations
import random
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable
from enum import Enum

from .models import Node, Tier, NodeFlag, DiffResult, Pointer

if TYPE_CHECKING:
    from .engine import Engine


class ThoughtType(Enum):
    COMPARE_SIBLINGS = "compare_siblings"       # Compare nodes that share a pointer target
    COMPARE_SAME_TIER = "compare_same_tier"     # Compare nodes at the same tier
    EXPLORE_STUBS = "explore_stubs"             # Re-examine trial/stub nodes against known nodes
    TEST_RELATIONSHIP = "test_relationship"     # Verify a pointer relationship still holds
    CROSS_DEFINITION = "cross_definition"       # Compare definitions across different words
    PATTERN_HUNT = "pattern_hunt"               # Look for structural similarities


@dataclass
class Thought:
    """A single autonomous processing result."""
    thought_type: ThoughtType
    description: str
    nodes_involved: list[str] = field(default_factory=list)  # node names
    discovery: str | None = None        # What was found, if anything
    pattern: str | None = None          # Pattern string if discovered
    records_produced: int = 0
    timestamp: float = field(default_factory=time.time)


class Thinker:
    """
    Autonomous processing loop. Picks assignments, runs them through
    the engine, and reports discoveries.
    """

    def __init__(self, engine: "Engine"):
        self.engine = engine
        self._running = False
        self._paused = False
        self._thoughts: list[Thought] = []
        self._thought_count = 0
        self._discovery_count = 0
        self._on_thought: Callable[[Thought], None] | None = None
        self._cycle_delay = 0.5   # seconds between thoughts
        self._max_history = 200   # keep last N thoughts

    @property
    def thoughts(self) -> list[Thought]:
        return list(self._thoughts)

    @property
    def is_running(self) -> bool:
        return self._running and not self._paused

    def set_callback(self, fn: Callable[[Thought], None]):
        """Set a callback for when a thought completes."""
        self._on_thought = fn

    def start(self):
        self._running = True
        self._paused = False

    def stop(self):
        self._running = False

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def tick(self) -> Thought | None:
        """
        Run one thinking cycle. Called by the main loop (GUI or otherwise).
        Returns a Thought if something was processed, None if idle/paused.
        """
        if not self._running or self._paused:
            return None

        lib = self.engine.librarian
        if lib.node_count < 10:
            return None  # Not enough material to think about

        # Pick a thought type based on what's available
        thought = self._pick_and_execute()
        if thought:
            self._thoughts.append(thought)
            if len(self._thoughts) > self._max_history:
                self._thoughts.pop(0)
            self._thought_count += 1
            if thought.discovery:
                self._discovery_count += 1
            if self._on_thought:
                self._on_thought(thought)

        return thought

    def _pick_and_execute(self) -> Thought | None:
        """Select a thought type and execute it."""
        lib = self.engine.librarian
        all_nodes = lib.get_all_nodes()

        # Weight thought types by what's likely productive
        # More stubs = more stub exploration, more pointers = more relationship testing
        stubs = [n for n in all_nodes if n.tier == Tier.TRIAL and n.name]
        connected = [n for n in all_nodes if n.pointers and n.tier <= Tier.IMPORTANT]
        defined = [n for n in all_nodes if len(n.definitions) > 1 and n.name]

        options = []
        if len(connected) >= 2:
            options.append((ThoughtType.COMPARE_SIBLINGS, 3))
            options.append((ThoughtType.TEST_RELATIONSHIP, 2))
        if len(stubs) >= 1 and len(connected) >= 1:
            options.append((ThoughtType.EXPLORE_STUBS, 3))
        if len(defined) >= 2:
            options.append((ThoughtType.CROSS_DEFINITION, 2))
            options.append((ThoughtType.PATTERN_HUNT, 2))
        if len(all_nodes) >= 20:
            options.append((ThoughtType.COMPARE_SAME_TIER, 1))

        if not options:
            return None

        # Weighted random selection
        types, weights = zip(*options)
        thought_type = random.choices(types, weights=weights, k=1)[0]

        if thought_type == ThoughtType.COMPARE_SIBLINGS:
            return self._think_compare_siblings(connected)
        elif thought_type == ThoughtType.EXPLORE_STUBS:
            return self._think_explore_stubs(stubs, connected)
        elif thought_type == ThoughtType.TEST_RELATIONSHIP:
            return self._think_test_relationship(connected)
        elif thought_type == ThoughtType.CROSS_DEFINITION:
            return self._think_cross_definition(defined)
        elif thought_type == ThoughtType.PATTERN_HUNT:
            return self._think_pattern_hunt(defined)
        elif thought_type == ThoughtType.COMPARE_SAME_TIER:
            return self._think_compare_same_tier(all_nodes)

        return None

    # ------------------------------------------------------------------
    # Thought implementations
    # ------------------------------------------------------------------

    def _think_compare_siblings(self, connected: list[Node]) -> Thought | None:
        """
        Find two nodes that point to the same target (siblings)
        and compare them. e.g., "cat" and "dog" both is_a "animal".
        """
        lib = self.engine.librarian

        # Build target -> [nodes] map
        target_map: dict[str, list[Node]] = {}
        for node in connected:
            for ptr in node.pointers:
                target_map.setdefault(ptr.target, []).append(node)

        # Find targets with 2+ siblings
        sibling_groups = [(t, nodes) for t, nodes in target_map.items() if len(nodes) >= 2]
        if not sibling_groups:
            return None

        target_id, siblings = random.choice(sibling_groups)
        a, b = random.sample(siblings, 2)

        # Run comparison through the register
        register = self.engine._get_register()
        from .models import Assignment
        assignment = Assignment(
            foundation=list(lib._nodes[addr] for addr in lib._foundation if addr in lib._nodes),
            context=[a, b],
            input_raw={"type": "autonomous", "subtype": "compare_siblings"},
        )
        register.load_assignment(assignment)
        records = register.compare(a, b)
        package = register.hand_back()
        lib.integrate(package)

        # Analyze what we found
        same = [r for r in records if r.result == DiffResult.SAME]
        diff = [r for r in records if r.result == DiffResult.DIFFERENT]

        target_node = lib.get_node(target_id)
        target_name = target_node.name if target_node else "?"

        discovery = None
        if len(same) > len(diff):
            discovery = f"\"{a.name}\" and \"{b.name}\" are more alike than different ({len(same)}S/{len(diff)}D) — both connected to \"{target_name}\""
        elif same:
            shared = [r.aspect for r in same]
            discovery = f"\"{a.name}\" and \"{b.name}\" share: {', '.join(set(shared))}"

        return Thought(
            thought_type=ThoughtType.COMPARE_SIBLINGS,
            description=f"Comparing siblings \"{a.name}\" and \"{b.name}\" (both → {target_name})",
            nodes_involved=[a.name, b.name, target_name],
            discovery=discovery,
            records_produced=len(records),
        )

    def _think_explore_stubs(self, stubs: list[Node], connected: list[Node]) -> Thought | None:
        """
        Take a trial node and compare it against established nodes
        to see if we can learn anything about it.
        """
        lib = self.engine.librarian
        stub = random.choice(stubs)

        # Pick a few established nodes to compare against
        comparisons = random.sample(connected, min(3, len(connected)))

        register = self.engine._get_register()
        from .models import Assignment
        assignment = Assignment(
            foundation=list(lib._nodes[addr] for addr in lib._foundation if addr in lib._nodes),
            context=[stub] + comparisons,
            input_raw={"type": "autonomous", "subtype": "explore_stub"},
        )
        register.load_assignment(assignment)

        all_records = []
        matches = []
        for comp in comparisons:
            records = register.compare(stub, comp)
            all_records.extend(records)
            same_count = sum(1 for r in records if r.result == DiffResult.SAME)
            if same_count > 0:
                matches.append((comp.name, same_count))

        package = register.hand_back()
        lib.integrate(package)

        discovery = None
        if matches:
            best = max(matches, key=lambda x: x[1])
            discovery = f"\"{stub.name}\" shares {best[1]} similarities with \"{best[0]}\""

        return Thought(
            thought_type=ThoughtType.EXPLORE_STUBS,
            description=f"Exploring stub \"{stub.name}\" against {len(comparisons)} known nodes",
            nodes_involved=[stub.name] + [c.name for c in comparisons],
            discovery=discovery,
            records_produced=len(all_records),
        )

    def _think_test_relationship(self, connected: list[Node]) -> Thought | None:
        """
        Pick a relationship pointer and verify it by comparing
        the two endpoints. Does the relationship still make sense?
        """
        lib = self.engine.librarian

        # Pick a node with pointers
        node = random.choice(connected)
        if not node.pointers:
            return None

        ptr = random.choice(node.pointers)
        target = lib.get_node(ptr.target)
        if not target:
            return None

        register = self.engine._get_register()
        from .models import Assignment
        assignment = Assignment(
            foundation=list(lib._nodes[addr] for addr in lib._foundation if addr in lib._nodes),
            context=[node, target],
            input_raw={"type": "autonomous", "subtype": "test_relationship"},
        )
        register.load_assignment(assignment)
        records = register.compare(node, target)
        package = register.hand_back()
        lib.integrate(package)

        same = sum(1 for r in records if r.result == DiffResult.SAME)
        diff = sum(1 for r in records if r.result == DiffResult.DIFFERENT)

        discovery = None
        if same > 0:
            discovery = f"\"{node.name}\" {ptr.relation} \"{target.name}\" confirmed ({same} shared aspects)"
        else:
            discovery = f"\"{node.name}\" {ptr.relation} \"{target.name}\" — no shared aspects found, weak link?"

        return Thought(
            thought_type=ThoughtType.TEST_RELATIONSHIP,
            description=f"Testing: \"{node.name}\" {ptr.relation} \"{target.name}\"",
            nodes_involved=[node.name, target.name],
            discovery=discovery,
            records_produced=len(records),
        )

    def _think_cross_definition(self, defined: list[Node]) -> Thought | None:
        """
        Compare definitions across different words. Do any words
        share definition content that might indicate a relationship?
        """
        lib = self.engine.librarian
        a, b = random.sample(defined, 2)

        # Compare first definitions as a starting point
        register = self.engine._get_register()
        from .models import Assignment
        assignment = Assignment(
            foundation=list(lib._nodes[addr] for addr in lib._foundation if addr in lib._nodes),
            context=[a, b],
            input_raw={"type": "autonomous", "subtype": "cross_definition"},
        )
        register.load_assignment(assignment)
        records = register.compare(a, b)
        package = register.hand_back()
        lib.integrate(package)

        # Check for content overlap in definitions
        a_words = set()
        b_words = set()
        for d in a.definitions:
            if isinstance(d.content, str):
                a_words.update(d.content.lower().split())
        for d in b.definitions:
            if isinstance(d.content, str):
                b_words.update(d.content.lower().split())

        overlap = a_words & b_words - {"a", "an", "the", "of", "to", "in", "or", "and", "is", "that", "with", "for", "by", "on", "as", "be"}
        discovery = None
        if len(overlap) >= 3:
            shared = sorted(overlap)[:6]
            discovery = f"\"{a.name}\" and \"{b.name}\" share definition words: {', '.join(shared)}"

            # Wire a pointer if we found meaningful overlap and none exists
            existing_targets = {p.target for p in a.pointers}
            if b.id not in existing_targets and len(overlap) >= 5:
                a.pointers.append(Pointer(target=b.id, relation="definition_overlap"))
                discovery += " → new connection created"

        return Thought(
            thought_type=ThoughtType.CROSS_DEFINITION,
            description=f"Cross-referencing definitions: \"{a.name}\" vs \"{b.name}\"",
            nodes_involved=[a.name, b.name],
            discovery=discovery,
            records_produced=len(records),
        )

    def _think_pattern_hunt(self, defined: list[Node]) -> Thought | None:
        """
        Look for structural patterns — nodes with the same number
        of definitions, same pointer structure, same tier.
        """
        lib = self.engine.librarian

        # Group by definition count
        by_def_count: dict[int, list[Node]] = {}
        for n in defined:
            dc = len(n.definitions)
            by_def_count.setdefault(dc, []).append(n)

        # Find groups with 2+ members
        groups = [(dc, nodes) for dc, nodes in by_def_count.items() if len(nodes) >= 2 and dc > 1]
        if not groups:
            return None

        dc, group = random.choice(groups)
        sample = random.sample(group, min(2, len(group)))
        a, b = sample[0], sample[1] if len(sample) > 1 else sample[0]

        register = self.engine._get_register()
        from .models import Assignment
        assignment = Assignment(
            foundation=list(lib._nodes[addr] for addr in lib._foundation if addr in lib._nodes),
            context=[a, b],
            input_raw={"type": "autonomous", "subtype": "pattern_hunt"},
        )
        register.load_assignment(assignment)
        records = register.compare(a, b)
        package = register.hand_back()
        lib.integrate(package)

        same = [r for r in records if r.result == DiffResult.SAME]

        discovery = None
        if len(same) >= 2:
            aspects = list(set(r.aspect for r in same))[:4]
            discovery = f"\"{a.name}\" and \"{b.name}\" ({dc} defs each) share structure: {', '.join(aspects)}"

        return Thought(
            thought_type=ThoughtType.PATTERN_HUNT,
            description=f"Pattern hunting: \"{a.name}\" vs \"{b.name}\" ({dc} definitions each)",
            nodes_involved=[a.name, b.name],
            discovery=discovery,
            records_produced=len(records),
        )

    def _think_compare_same_tier(self, all_nodes: list[Node]) -> Thought | None:
        """Compare two random nodes at the same tier."""
        lib = self.engine.librarian

        # Pick a tier with enough nodes
        by_tier: dict[int, list[Node]] = {}
        for n in all_nodes:
            if n.name and len(n.name) > 1:
                by_tier.setdefault(int(n.tier), []).append(n)

        viable = [(t, nodes) for t, nodes in by_tier.items() if len(nodes) >= 2]
        if not viable:
            return None

        tier_val, group = random.choice(viable)
        a, b = random.sample(group, 2)

        register = self.engine._get_register()
        from .models import Assignment
        assignment = Assignment(
            foundation=list(lib._nodes[addr] for addr in lib._foundation if addr in lib._nodes),
            context=[a, b],
            input_raw={"type": "autonomous", "subtype": "compare_same_tier"},
        )
        register.load_assignment(assignment)
        records = register.compare(a, b)
        package = register.hand_back()
        lib.integrate(package)

        same = [r for r in records if r.result == DiffResult.SAME]
        tier_name = Tier(tier_val).name

        discovery = None
        if len(same) >= 2:
            aspects = list(set(r.aspect for r in same))[:4]
            discovery = f"\"{a.name}\" ≈ \"{b.name}\" (both {tier_name}): share {', '.join(aspects)}"

        return Thought(
            thought_type=ThoughtType.COMPARE_SAME_TIER,
            description=f"Comparing {tier_name} nodes: \"{a.name}\" vs \"{b.name}\"",
            nodes_involved=[a.name, b.name],
            discovery=discovery,
            records_produced=len(records),
        )

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    @property
    def stats(self) -> dict:
        return {
            "thoughts": self._thought_count,
            "discoveries": self._discovery_count,
            "running": self._running,
            "paused": self._paused,
        }
