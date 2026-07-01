"""
Intellon v4 — Meta Knowledge

Scoring criteria, assessment rules, and learning strategies as NODES.
Not hardcoded Python — knowledge the system reads, uses, and can extend.

These nodes tell the system HOW to evaluate, HOW to learn,
and HOW to improve. The system can create new criteria nodes
from its own experience.

Boot order: load these AFTER curriculum and BEFORE evaluation.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from .models import Node, Tier, NodeFlag, Definition, Pointer

if TYPE_CHECKING:
    from .librarian import Librarian


def load_meta_knowledge(librarian: "Librarian") -> dict[str, str]:
    """
    Load scoring criteria and assessment knowledge as nodes.
    Returns registry of logical name → node ID.
    """
    librarian.set_training_mode(True, Tier.IMPORTANT)
    registry: dict[str, str] = {}

    # ================================================================
    # Category: Scoring Dimensions
    # ================================================================

    _make_meta(librarian, registry, "scoring", "scoring",
               "Evaluation of generated output across multiple dimensions. "
               "Each dimension measures a different aspect of quality. "
               "Higher scores mean better output.",
               pointers_to=["accuracy_criterion", "fluency_criterion",
                            "completeness_criterion", "relevance_criterion",
                            "coherence_criterion"])

    # ================================================================
    # Individual Criteria
    # ================================================================

    _make_meta(librarian, registry, "accuracy_criterion", "accuracy",
               "The information in the output matches stored knowledge. "
               "Words used correctly according to their definitions. "
               "Relationships stated match pointer relationships in the network. "
               "Measure: count words with valid definitions, check relationship claims "
               "against stored pointers. Higher ratio of verified claims = higher accuracy.")

    _make_meta(librarian, registry, "fluency_criterion", "fluency",
               "The output reads like natural language. "
               "A fluent sentence has: a subject, a verb, proper word order. "
               "Articles (a, an, the) appear before nouns. "
               "Verbs connect subjects to objects or descriptions. "
               "Prepositions connect nouns to context. "
               "Measure: check for article-noun pairs, subject-verb presence, "
               "match against known sentence patterns. "
               "More structural matches = higher fluency.")

    _make_meta(librarian, registry, "completeness_criterion", "completeness",
               "The output fully addresses what was asked. "
               "Key words from the prompt should be addressed in the response, "
               "either directly or through a known relationship. "
               "A question about a cat should mention cats or felines. "
               "A request to describe should include properties and relationships. "
               "Measure: count prompt key words addressed in response. "
               "Higher coverage = higher completeness.")

    _make_meta(librarian, registry, "relevance_criterion", "relevance",
               "Everything in the output relates to the prompt. "
               "No unrelated information. No filler. "
               "Each word should connect to the prompt through known relationships. "
               "Measure: for each response word, check if it connects to any "
               "prompt word through pointers. Higher connection ratio = higher relevance.")

    _make_meta(librarian, registry, "coherence_criterion", "coherence",
               "The words in the output belong together. "
               "Words that have appeared in sessions together are coherent. "
               "Words that share pointer targets are coherent. "
               "Words from unrelated domains are incoherent. "
               "Measure: pairwise co-occurrence and shared targets between "
               "response words. Higher overlap = higher coherence.")

    # ================================================================
    # Category: Sentence Structure Rules
    # ================================================================

    _make_meta(librarian, registry, "sentence_structure", "sentence structure",
               "A well-formed English sentence follows structural patterns. "
               "The system discovers these patterns through differentiation "
               "across many examples.")

    _make_meta(librarian, registry, "rule_subject_verb", "subject verb rule",
               "A sentence needs a subject and a verb. "
               "The subject is usually a noun or pronoun. "
               "The verb describes what the subject does or is. "
               "Example: 'The cat ran.' Subject=cat, verb=ran. "
               "Missing subject or verb = incomplete sentence.",
               pointers_to=["sentence_structure"])

    _make_meta(librarian, registry, "rule_article_noun", "article noun rule",
               "Articles (a, an, the) come before nouns. "
               "'a' before consonant sounds. 'an' before vowel sounds. "
               "'the' for specific known things. "
               "Example: 'a cat', 'an animal', 'the dog'. "
               "Noun without article may be acceptable in some contexts.",
               pointers_to=["sentence_structure"])

    _make_meta(librarian, registry, "rule_word_order", "word order rule",
               "English word order is typically: subject verb object. "
               "'The cat ate the fish.' Subject=cat, verb=ate, object=fish. "
               "Adjectives come before nouns: 'the big cat' not 'the cat big'. "
               "Adverbs can be flexible but usually near the verb.",
               pointers_to=["sentence_structure"])

    _make_meta(librarian, registry, "rule_punctuation", "punctuation rule",
               "Sentences end with a period, question mark, or exclamation mark. "
               "Questions end with a question mark. "
               "Statements end with a period. "
               "Commas separate items in a list or clauses.",
               pointers_to=["sentence_structure"])

    # ================================================================
    # Category: Response Strategies
    # ================================================================

    _make_meta(librarian, registry, "response_strategies", "response strategies",
               "Different prompts need different response strategies. "
               "The system should match the prompt type to the best strategy.")

    _make_meta(librarian, registry, "strategy_definition", "definition strategy",
               "When asked 'what is X' or 'define X' or 'describe X': "
               "Find X in the network. Return its primary definition. "
               "Include part of speech if known. "
               "Include key relationships (is_a, has_part). "
               "Format: 'X is a [pos]. [definition]. [relationships].'",
               pointers_to=["response_strategies"])

    _make_meta(librarian, registry, "strategy_comparison", "comparison strategy",
               "When asked about differences or similarities between X and Y: "
               "Find both X and Y in the network. "
               "Compare their definitions, relationships, and properties. "
               "Report what is SAME and what is DIFFERENT. "
               "Format: 'X and Y are both [shared]. X is [unique to X] while Y is [unique to Y].'",
               pointers_to=["response_strategies"])

    _make_meta(librarian, registry, "strategy_computation", "computation strategy",
               "When asked to compute (math, logic, comparison): "
               "Identify the operator and operands. "
               "Find the stored result or compute from known rules. "
               "Return just the answer for direct questions. "
               "Format: '[answer]' or '[operand] [operator] [operand] = [answer]'",
               pointers_to=["response_strategies"])

    _make_meta(librarian, registry, "strategy_enumeration", "enumeration strategy",
               "When asked to list, name, or enumerate: "
               "Find the category in the network. "
               "Follow has_type pointers to find members. "
               "Return known members. "
               "Format: '[member1], [member2], and [member3].'",
               pointers_to=["response_strategies"])

    # ================================================================
    # Category: Self-Improvement
    # ================================================================

    _make_meta(librarian, registry, "self_improvement", "self improvement",
               "The system improves by comparing its outputs to its own criteria. "
               "Each evaluation creates nodes. Each correction adds knowledge. "
               "Better criteria lead to better evaluation lead to better output. "
               "The system can create new criteria from patterns it discovers.")

    _make_meta(librarian, registry, "criterion_creation", "criterion creation",
               "When the system repeatedly fails on a specific pattern, "
               "it should create a new criterion node that captures what went wrong. "
               "The new criterion becomes part of future evaluations. "
               "Example: if responses consistently lack verbs, create a criterion "
               "that specifically checks for verb presence and weights it highly.",
               pointers_to=["self_improvement"])

    _make_meta(librarian, registry, "strategy_creation", "strategy creation",
               "When the system encounters a prompt type it has no strategy for, "
               "it should create a new strategy node from the traceback of its attempt. "
               "The new strategy becomes available for future similar prompts. "
               "Strategy nodes should describe: when to use, what to look for, "
               "how to assemble the response.",
               pointers_to=["self_improvement"])

    librarian.set_training_mode(False)
    return registry


def _make_meta(librarian: "Librarian", registry: dict[str, str],
               key: str, name: str, content: str,
               pointers_to: list[str] | None = None):
    """Create a meta-knowledge node and register it."""

    # Look up char pointers
    char_ptrs = []
    for ch in name:
        ch_ids = librarian.recognize(ch)
        if ch_ids:
            char_ptrs.append(ch_ids[0])

    node = Node(
        name=name,
        tier=Tier.IMPORTANT,
        flags={NodeFlag.ACTIVE},
        char_pointers=char_ptrs,
    )
    node.add_definition(content, pointers=[
        Pointer(target="__type_meta__", relation="is_a"),
    ])

    # Wire pointers to other meta nodes (deferred — they might not exist yet)
    if pointers_to:
        node._deferred_pointers = pointers_to

    librarian.store_node(node)
    registry[key] = node.id


def resolve_deferred_pointers(librarian: "Librarian", registry: dict[str, str]):
    """Wire up pointers that reference other meta nodes by key."""
    for key, node_id in registry.items():
        node = librarian.get_node(node_id)
        if not node:
            continue
        deferred = getattr(node, "_deferred_pointers", None)
        if deferred:
            for target_key in deferred:
                if target_key in registry:
                    node.pointers.append(
                        Pointer(target=registry[target_key], relation="related_to"))
            del node._deferred_pointers
