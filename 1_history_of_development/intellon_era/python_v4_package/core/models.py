"""
Intellon v4 — Core Data Structures

Everything in the system is a node. Nodes are passive concept pointer packets.
A node is a dictionary entry: name, numbered definitions, character-level
pointers, concept pointers, and a trust tier.
Differentiation records are the atomic unit of knowledge.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, IntEnum
from typing import Any
import uuid


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class DiffResult(Enum):
    SAME = "SAME"
    DIFFERENT = "DIFFERENT"


class Tier(IntEnum):
    """Trust hierarchy. Nodes move UP through tiers as they prove themselves."""
    INITIATOR = 1   # System axioms. Never deleted, never demoted.
    IMPORTANT = 2   # Critical knowledge. Never deleted, can be updated.
    VALIDATED = 3   # Confirmed working set. Reasonable certainty.
    TRIAL = 4       # New, unproven. Every new node starts here.


class NodeFlag(Enum):
    """Classification tags — what kind of thing is this node. Orthogonal to tier."""
    FOUNDATION = "foundation"   # Auto-loaded in every assignment
    TRUSTED = "trusted"
    ACTIVE = "active"
    STUB = "stub"               # Raw, just created by register
    REVIEW = "review"           # Flagged for conflict review
    DORMANT = "dormant"
    ARCHIVED = "archived"


# ---------------------------------------------------------------------------
# Pointer & Constraint
# ---------------------------------------------------------------------------

@dataclass
class Pointer:
    target: str            # node address
    relation: str          # is_a, part_of, contradicts, used_with, char_of, see_also, etc.


@dataclass
class Constraint:
    subject: str
    relation: str
    object: str
    polarity: bool         # True = must hold, False = must not hold


# ---------------------------------------------------------------------------
# Definition
# ---------------------------------------------------------------------------

@dataclass
class Definition:
    """A single numbered definition within a node. Like def 1, def 2 in a dictionary."""
    number: int
    content: Any = None
    pointers: list[Pointer] = field(default_factory=list)   # concept pointers for THIS definition
    see_also: list[str] = field(default_factory=list)        # node addresses for cross-references


# ---------------------------------------------------------------------------
# Origin & Context
# ---------------------------------------------------------------------------

@dataclass
class Origin:
    session_id: str
    inputs: list[str]      # addresses of input nodes
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class NodeContext:
    where: str             # positional info
    when: datetime
    surrounding: list[str] # addresses of co-occurring nodes


# ---------------------------------------------------------------------------
# Node — the dictionary entry
# ---------------------------------------------------------------------------

@dataclass
class Node:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""                                              # headword: "cat", "a", "ran", "+"
    definitions: list[Definition] = field(default_factory=list)  # numbered definitions
    char_pointers: list[str] = field(default_factory=list)       # node addresses for each character
    pointers: list[Pointer] = field(default_factory=list)        # node-level pointers (not definition-specific)
    constraints: list[Constraint] = field(default_factory=list)
    tier: Tier = Tier.TRIAL
    flags: set[NodeFlag] = field(default_factory=set)
    tallies: dict[str, int] = field(default_factory=dict)
    origin: Origin | None = None
    context: list[NodeContext] = field(default_factory=list)

    # -- Convenience: content property for backward compatibility --
    # Existing code reads/writes node.content. Route it through definitions.
    @property
    def content(self) -> Any:
        """Primary content: first definition's content, or name if no definitions."""
        if self.definitions:
            return self.definitions[0].content
        return self.name or None

    @content.setter
    def content(self, value: Any):
        """Set content on the first definition. Creates one if needed."""
        if self.definitions:
            self.definitions[0].content = value
        else:
            self.definitions.append(Definition(number=1, content=value))
        # If name is empty and value is a simple string, use it as name
        if not self.name and isinstance(value, str):
            self.name = value

    def has_flag(self, flag: NodeFlag) -> bool:
        return flag in self.flags

    def tally(self, category: str, amount: int = 1):
        self.tallies[category] = self.tallies.get(category, 0) + amount

    def add_definition(self, content: Any, pointers: list[Pointer] | None = None) -> Definition:
        """Add a new numbered definition."""
        num = len(self.definitions) + 1
        defn = Definition(number=num, content=content, pointers=pointers or [])
        self.definitions.append(defn)
        return defn

    def get_definition(self, number: int) -> Definition | None:
        """Get a definition by its number."""
        for d in self.definitions:
            if d.number == number:
                return d
        return None


# ---------------------------------------------------------------------------
# Differentiation Record
# ---------------------------------------------------------------------------

@dataclass
class DiffRecord:
    slot_a: str            # node address
    slot_b: str            # node address
    aspect: str            # what was compared
    result: DiffResult
    detail: str            # specifics of sameness or difference
    position: int | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Assignment & Return Package
# ---------------------------------------------------------------------------

@dataclass
class Assignment:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    foundation: list[Node] = field(default_factory=list)
    context: list[Node] = field(default_factory=list)
    input_raw: Any = None
    metadata: dict = field(default_factory=lambda: {
        "recognized": [],
        "flagged": [],
    })


@dataclass
class VerificationResult:
    passed: bool
    iterations: int = 0
    conflicts: list[DiffRecord] = field(default_factory=list)


@dataclass
class ReturnPackage:
    session_id: str
    notepad: list[DiffRecord] = field(default_factory=list)
    stubs: list[Node] = field(default_factory=list)
    synthesis: Node | None = None
    verification: VerificationResult = field(default_factory=lambda: VerificationResult(passed=True))
    requests: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Protocol Messages
# ---------------------------------------------------------------------------

class MessageType(Enum):
    ASSIGN = "ASSIGN"
    REQUEST = "REQUEST"
    DELIVER = "DELIVER"
    RETURN = "RETURN"


@dataclass
class ProtocolMessage:
    direction: str         # "lib->reg" or "reg->lib"
    msg_type: MessageType
    payload: Any = None
