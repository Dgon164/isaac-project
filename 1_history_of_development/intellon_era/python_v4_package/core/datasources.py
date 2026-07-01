"""
Intellon v4 — Data Sources

Large-scale knowledge loaders for:
  - Full WordNet (84K+ single-word lemmas with relationships)
  - Brown Corpus (57K sentences of real American English across 15 genres)
  - ConceptNet (common-sense knowledge graph — from downloaded CSV)

These supplement the core vocabulary loader in training.py.
Training sequence: Curriculum → WordNet → Brown Corpus → ConceptNet → user data
"""

from __future__ import annotations
import os
import csv
import time
from typing import TYPE_CHECKING, Any, Callable

from .models import Node, Tier, NodeFlag, Pointer

if TYPE_CHECKING:
    from .engine import Engine
    from .librarian import Librarian


# ======================================================================
# Full WordNet
# ======================================================================

def load_wordnet_full(librarian: "Librarian", tier: Tier = Tier.IMPORTANT,
                      include_phrases: bool = False,
                      engine: Any = None,
                      on_progress: Callable | None = None) -> dict[str, Any]:
    """
    Load ALL of WordNet — every single-word English lemma with
    definitions and relationship pointers. Each word's primary
    definition is processed through the engine so the register
    sees and differentiates it.
    """
    from nltk.corpus import wordnet as wn
    from .training import load_wordnet

    # Gather all lemmas
    all_lemmas = set()
    for syn in wn.all_synsets():
        for lemma in syn.lemmas():
            name = lemma.name().replace("_", " ")
            if not name.isascii() or len(name) < 2:
                continue
            if not include_phrases and " " in name:
                continue
            all_lemmas.add(name)

    words = sorted(all_lemmas)
    total = len(words)

    if on_progress:
        on_progress("Indexing", 0, total)

    stats = {
        "total_lemmas": total,
        "nodes_before": librarian.node_count,
    }

    # Load in batches for progress reporting
    batch_size = 2000
    registry = {}
    for i in range(0, total, batch_size):
        batch = words[i:i + batch_size]
        batch_reg = load_wordnet(librarian, words=batch, tier=tier, engine=engine)
        registry.update(batch_reg)
        if on_progress:
            on_progress("Loading", min(i + batch_size, total), total)

    stats["words_imported"] = len(registry)
    stats["nodes_after"] = librarian.node_count
    stats["nodes_created"] = stats["nodes_after"] - stats["nodes_before"]
    return stats


# ======================================================================
# Brown Corpus
# ======================================================================

def load_brown_corpus(engine: "Engine", categories: list[str] | None = None,
                      max_sentences: int | None = None,
                      tier: Tier = Tier.VALIDATED,
                      on_progress: Callable | None = None) -> dict[str, Any]:
    """
    Load the Brown Corpus — 57K sentences of real American English
    across 15 genres (news, fiction, academic, government, etc.).

    This is the standard balanced sample of English. Each sentence
    runs through the full assignment cycle — the register differentiates,
    discovers patterns, creates stubs for unknown words.

    Args:
        categories: Which genres to load. None = all.
            Options: adventure, belles_lettres, editorial, fiction,
            government, hobbies, humor, learned, lore, mystery,
            news, religion, reviews, romance, science_fiction
        max_sentences: Limit number of sentences (for testing).
        on_progress: Callback(category, current, total).

    Requires: nltk.download('brown')
    """
    import nltk
    nltk.download("brown", quiet=True)
    from nltk.corpus import brown

    engine.librarian.set_training_mode(True, tier)

    available = brown.categories()
    cats = categories or available

    stats = {
        "categories": cats,
        "sentences_processed": 0,
        "nodes_before": engine.librarian.node_count,
        "stubs_created": 0,
        "notepad_records": 0,
    }

    total_sents = sum(len(brown.sents(categories=c)) for c in cats)
    if max_sentences:
        total_sents = min(total_sents, max_sentences)

    processed = 0
    for cat in cats:
        sents = brown.sents(categories=cat)
        for sent_tokens in sents:
            if max_sentences and processed >= max_sentences:
                break

            # Brown corpus gives tokenized sentences — rejoin
            sentence = " ".join(sent_tokens)
            # Clean up tokenization artifacts
            sentence = sentence.replace(" ,", ",").replace(" .", ".")
            sentence = sentence.replace(" ;", ";").replace(" :", ":")
            sentence = sentence.replace("`` ", '"').replace(" ''", '"')

            if len(sentence) < 5:
                continue

            result = engine.process(sentence)
            stats["sentences_processed"] += 1
            stats["stubs_created"] += len(result.stubs)
            stats["notepad_records"] += len(result.notepad)
            processed += 1

            if on_progress and processed % 100 == 0:
                on_progress(cat, processed, total_sents)

        if max_sentences and processed >= max_sentences:
            break

    engine.librarian.set_training_mode(False)
    stats["nodes_after"] = engine.librarian.node_count
    stats["nodes_created"] = stats["nodes_after"] - stats["nodes_before"]
    return stats


# ======================================================================
# ConceptNet
# ======================================================================

def load_conceptnet(librarian: "Librarian", filepath: str,
                    max_assertions: int | None = None,
                    min_weight: float = 1.0,
                    tier: Tier = Tier.VALIDATED,
                    on_progress: Callable | None = None) -> dict[str, Any]:
    """
    Load ConceptNet assertions from a local CSV file.

    ConceptNet is a common-sense knowledge graph with relationships like:
      cat IsA animal, car UsedFor transportation, rain Causes wet

    Download the English assertions file from:
      https://github.com/commonsense/conceptnet5/wiki/Downloads
      → conceptnet-assertions-5.7.0.csv.gz (or latest)
      → gunzip it to get the CSV

    The CSV format is: URI, relation, start, end, metadata_json
    We filter to English-only and create pointer relationships.

    Args:
        filepath: Path to the ConceptNet assertions CSV.
        max_assertions: Limit (for testing).
        min_weight: Minimum edge weight to include (higher = more confident).
        on_progress: Callback(current, total).
    """
    import json

    librarian.set_training_mode(True, tier)

    # Map ConceptNet relations to our pointer relations
    RELATION_MAP = {
        "/r/IsA": "is_a",
        "/r/PartOf": "part_of",
        "/r/HasA": "has_part",
        "/r/UsedFor": "used_for",
        "/r/CapableOf": "capable_of",
        "/r/AtLocation": "at_location",
        "/r/Causes": "causes",
        "/r/HasProperty": "has_property",
        "/r/MadeOf": "made_of",
        "/r/ReceivesAction": "receives_action",
        "/r/CreatedBy": "created_by",
        "/r/Synonym": "synonym",
        "/r/Antonym": "antonym",
        "/r/DerivedFrom": "derived_from",
        "/r/RelatedTo": "related_to",
        "/r/SimilarTo": "similar_to",
        "/r/DefinedAs": "defined_as",
        "/r/HasContext": "has_context",
        "/r/HasSubevent": "has_subevent",
        "/r/HasPrerequisite": "has_prerequisite",
        "/r/MotivatedByGoal": "motivated_by",
        "/r/Desires": "desires",
        "/r/HasFirstSubevent": "starts_with",
        "/r/HasLastSubevent": "ends_with",
    }

    stats = {
        "assertions_read": 0,
        "assertions_loaded": 0,
        "nodes_before": librarian.node_count,
        "relations_created": 0,
        "skipped_non_english": 0,
        "skipped_low_weight": 0,
    }

    # Count lines for progress
    total_lines = 0
    if on_progress:
        with open(filepath, "r", encoding="utf-8") as f:
            for _ in f:
                total_lines += 1

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            stats["assertions_read"] += 1

            if max_assertions and stats["assertions_loaded"] >= max_assertions:
                break

            if len(row) < 5:
                continue

            uri, relation, start, end, meta_json = row[0], row[1], row[2], row[3], row[4]

            # Filter to English only
            if not start.startswith("/c/en/") or not end.startswith("/c/en/"):
                stats["skipped_non_english"] += 1
                continue

            # Check weight
            try:
                meta = json.loads(meta_json)
                weight = meta.get("weight", 0)
                if weight < min_weight:
                    stats["skipped_low_weight"] += 1
                    continue
            except (json.JSONDecodeError, KeyError):
                pass

            # Extract word names
            start_word = start.split("/")[3].replace("_", " ")
            end_word = end.split("/")[3].replace("_", " ")

            if not start_word.isascii() or not end_word.isascii():
                continue

            # Map relation
            our_relation = RELATION_MAP.get(relation, "related_to")

            # Get or create nodes
            start_node = _get_or_create_node(librarian, start_word, tier)
            end_node = _get_or_create_node(librarian, end_word, tier)

            # Add pointer if not duplicate
            existing = {(p.target, p.relation) for p in start_node.pointers}
            if (end_node.id, our_relation) not in existing:
                start_node.pointers.append(Pointer(target=end_node.id, relation=our_relation))
                stats["relations_created"] += 1

            stats["assertions_loaded"] += 1

            if on_progress and stats["assertions_read"] % 10000 == 0:
                on_progress(stats["assertions_read"], total_lines)

    librarian.set_training_mode(False)
    stats["nodes_after"] = librarian.node_count
    stats["nodes_created"] = stats["nodes_after"] - stats["nodes_before"]
    return stats


def _get_or_create_node(librarian: "Librarian", name: str, tier: Tier) -> Node:
    """Get existing node or create a new one."""
    ids = librarian.recognize(name)
    if ids:
        node = librarian.get_node(ids[0])
        if node:
            return node

    # Look up char pointers
    char_ptrs = []
    for ch in name:
        ch_ids = librarian.recognize(ch)
        if ch_ids:
            char_ptrs.append(ch_ids[0])

    node = Node(
        name=name,
        tier=tier,
        flags={NodeFlag.ACTIVE},
        char_pointers=char_ptrs,
    )
    librarian.store_node(node)
    return node


# ======================================================================
# Available Brown Corpus categories (for UI)
# ======================================================================

BROWN_CATEGORIES = [
    "adventure", "belles_lettres", "editorial", "fiction",
    "government", "hobbies", "humor", "learned", "lore",
    "mystery", "news", "religion", "reviews", "romance",
    "science_fiction",
]
