"""
Intellon v4 — Training Pipeline

Ingests data into the system. Supports WordNet, text files, CSV, JSON.
Training mode = high trust: data enters at specified tier, not trial.

The order matters. Each layer provides reference frames for the next.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any
import json
import csv
import os

from .models import Node, Tier, NodeFlag, Definition, Pointer

if TYPE_CHECKING:
    from .librarian import Librarian
    from .engine import Engine


# --------------------------------------------------------------------------
# WordNet Import
# --------------------------------------------------------------------------

def load_wordnet(librarian: Librarian, words: list[str] | None = None,
                 tier: Tier = Tier.IMPORTANT, limit: int | None = None,
                 engine: Any = None) -> dict[str, str]:
    """
    Import WordNet entries as dictionary-entry nodes AND process them.

    Each word:
      1. Gets stored as a node with definitions and pointers (librarian)
      2. Gets its definitions processed through the engine (register sees them)

    The register differentiates "feline mammal usually having thick soft fur"
    against everything it already knows. By the tenth noun definition, it
    has seen the pattern of what a noun definition looks like.

    Args:
        librarian: The librarian to load into.
        words: Specific words to import. None = core vocabulary.
        tier: Trust tier for imported nodes.
        limit: Max words to import (for testing).
        engine: If provided, process definitions through full assignment cycle.
    """
    from nltk.corpus import wordnet as wn

    librarian.set_training_mode(True, tier)
    registry: dict[str, str] = {}

    if words is None:
        words = CORE_VOCABULARY

    if limit:
        words = words[:limit]

    # First pass: create all word nodes with definitions, process each one
    for word in words:
        synsets = wn.synsets(word)
        if not synsets:
            continue

        # Check if node already exists
        existing_ids = librarian.recognize(word)
        if existing_ids:
            registry[word] = existing_ids[0]
            continue

        # Look up char node IDs for character pointers
        char_ptrs = []
        for ch in word:
            ch_ids = librarian.recognize(ch)
            if ch_ids:
                char_ptrs.append(ch_ids[0])

        node = Node(
            name=word,
            tier=tier,
            flags={NodeFlag.ACTIVE},
            char_pointers=char_ptrs,
        )

        # One definition per synset
        pos_map = {"n": "noun", "v": "verb", "a": "adjective", "r": "adverb", "s": "adjective_satellite"}
        for i, syn in enumerate(synsets, 1):
            defn_text = syn.definition()
            pos_tag = syn.pos()
            pos_name = pos_map.get(pos_tag, pos_tag)

            defn_pointers = [Pointer(target=f"__pos_{pos_name}__", relation="part_of_speech")]
            node.add_definition(defn_text, pointers=defn_pointers)

        librarian.store_node(node)
        registry[word] = node.id

        # Process through engine — the register sees the word and its definitions
        if engine is not None:
            # Feed the primary definition as text so the register differentiates it
            primary_def = synsets[0].definition()
            pos_name = pos_map.get(synsets[0].pos(), "")
            engine.process(f"{word} is a {pos_name}. {word}: {primary_def}")

    # Second pass: wire up relationship pointers between nodes
    for word in words:
        if word not in registry:
            continue
        node = librarian.get_node(registry[word])
        if not node:
            continue

        synsets = wn.synsets(word)
        for syn in synsets:
            for hyper in syn.hypernyms():
                lemma = hyper.lemmas()[0].name().replace("_", " ")
                if lemma in registry:
                    node.pointers.append(Pointer(target=registry[lemma], relation="is_a"))

            for hypo in syn.hyponyms():
                lemma = hypo.lemmas()[0].name().replace("_", " ")
                if lemma in registry:
                    node.pointers.append(Pointer(target=registry[lemma], relation="has_type"))

            for lemma_obj in syn.lemmas():
                lemma = lemma_obj.name().replace("_", " ")
                if lemma != word and lemma in registry:
                    node.pointers.append(Pointer(target=registry[lemma], relation="synonym"))

            for mero in syn.part_meronyms():
                lemma = mero.lemmas()[0].name().replace("_", " ")
                if lemma in registry:
                    node.pointers.append(Pointer(target=registry[lemma], relation="has_part"))

            for holo in syn.part_holonyms():
                lemma = holo.lemmas()[0].name().replace("_", " ")
                if lemma in registry:
                    node.pointers.append(Pointer(target=registry[lemma], relation="part_of"))

        # Deduplicate pointers
        seen = set()
        unique = []
        for p in node.pointers:
            key = (p.target, p.relation)
            if key not in seen:
                seen.add(key)
                unique.append(p)
        node.pointers = unique

    librarian.set_training_mode(False)
    return registry


# --------------------------------------------------------------------------
# Text File Processing
# --------------------------------------------------------------------------

def load_text_file(engine: "Engine", filepath: str,
                   tier: Tier = Tier.VALIDATED) -> dict[str, Any]:
    """
    Process a text file sentence by sentence through the engine.
    Each sentence runs the full assignment cycle.

    Returns stats about what was processed.
    """
    engine.librarian.set_training_mode(True, tier)

    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    stats = process_text(engine, text)

    engine.librarian.set_training_mode(False)
    return stats


def process_text(engine: "Engine", text: str) -> dict[str, Any]:
    """
    Process raw text through the engine. Splits into sentences,
    processes each one. Returns stats.
    """
    # Simple sentence splitting (period, question mark, exclamation)
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]

    stats = {
        "sentences_processed": 0,
        "nodes_before": engine.librarian.node_count,
        "stubs_created": 0,
        "notepad_records": 0,
    }

    for sentence in sentences:
        if len(sentence) < 2:
            continue
        result = engine.process(sentence)
        stats["sentences_processed"] += 1
        stats["stubs_created"] += len(result.stubs)
        stats["notepad_records"] += len(result.notepad)

    stats["nodes_after"] = engine.librarian.node_count
    stats["nodes_created"] = stats["nodes_after"] - stats["nodes_before"]
    return stats


# --------------------------------------------------------------------------
# CSV Import
# --------------------------------------------------------------------------

def load_csv(engine: "Engine", filepath: str,
             tier: Tier = Tier.VALIDATED,
             text_columns: list[str] | None = None) -> dict[str, Any]:
    """
    Process a CSV file. Each row's text columns get processed through the engine.
    If text_columns not specified, processes all string-valued columns.
    """
    engine.librarian.set_training_mode(True, tier)

    stats = {
        "rows_processed": 0,
        "nodes_before": engine.librarian.node_count,
        "stubs_created": 0,
    }

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cols = text_columns or list(row.keys())
            for col in cols:
                val = row.get(col, "")
                if val and isinstance(val, str) and len(val) > 1:
                    result = engine.process(val)
                    stats["stubs_created"] += len(result.stubs)
            stats["rows_processed"] += 1

    stats["nodes_after"] = engine.librarian.node_count
    engine.librarian.set_training_mode(False)
    return stats


# --------------------------------------------------------------------------
# JSON Import
# --------------------------------------------------------------------------

def load_json(engine: "Engine", filepath: str,
              tier: Tier = Tier.VALIDATED) -> dict[str, Any]:
    """
    Process a JSON file. Handles both arrays of strings and
    arrays of objects (processes all string values).
    """
    engine.librarian.set_training_mode(True, tier)

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    stats = {
        "items_processed": 0,
        "nodes_before": engine.librarian.node_count,
        "stubs_created": 0,
    }

    items = data if isinstance(data, list) else [data]
    for item in items:
        texts = _extract_strings(item)
        for text in texts:
            if len(text) > 1:
                result = engine.process(text)
                stats["stubs_created"] += len(result.stubs)
        stats["items_processed"] += 1

    stats["nodes_after"] = engine.librarian.node_count
    engine.librarian.set_training_mode(False)
    return stats


def _extract_strings(obj: Any) -> list[str]:
    """Recursively extract all string values from a nested structure."""
    strings = []
    if isinstance(obj, str):
        strings.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            strings.extend(_extract_strings(v))
    elif isinstance(obj, list):
        for item in obj:
            strings.extend(_extract_strings(item))
    return strings


# --------------------------------------------------------------------------
# PDF Import
# --------------------------------------------------------------------------

def load_pdf(engine: "Engine", filepath: str,
             tier: Tier = Tier.VALIDATED) -> dict[str, Any]:
    """
    Extract text from a PDF and process it through the engine.
    """
    try:
        import fitz  # pymupdf
    except ImportError:
        return {"error": "pymupdf not installed. Run: pip install pymupdf"}

    engine.librarian.set_training_mode(True, tier)

    doc = fitz.open(filepath)
    all_text = []
    for page in doc:
        all_text.append(page.get_text())
    doc.close()

    text = "\n".join(all_text)
    stats = process_text(engine, text)
    stats["pages"] = len(all_text)

    engine.librarian.set_training_mode(False)
    return stats


# --------------------------------------------------------------------------
# Universal File Loader
# --------------------------------------------------------------------------

def load_file(engine: "Engine", filepath: str,
              tier: Tier = Tier.VALIDATED) -> dict[str, Any]:
    """
    Auto-detect file type and load accordingly.
    Supports: .txt, .csv, .tsv, .json, .pdf
    """
    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".pdf":
        return load_pdf(engine, filepath, tier)
    elif ext in (".csv", ".tsv"):
        return load_csv(engine, filepath, tier)
    elif ext == ".json":
        return load_json(engine, filepath, tier)
    elif ext in (".txt", ".md", ".text", ""):
        return load_text_file(engine, filepath, tier)
    else:
        # Try as text
        return load_text_file(engine, filepath, tier)


# --------------------------------------------------------------------------
# Core Vocabulary
# --------------------------------------------------------------------------

# These are the words loaded by default when no word list is specified.
# Chosen for: high frequency, diverse parts of speech, relationship richness.
# This is NOT the full training set — it's the seed that everything else
# builds on. WordNet will connect these through hypernym/hyponym chains.

CORE_VOCABULARY = [
    # Determiners & pronouns
    "the", "a", "an", "this", "that", "it", "he", "she", "they", "we",
    "i", "you", "my", "your", "his", "her", "its",
    # Common verbs
    "be", "is", "are", "was", "were", "have", "has", "had",
    "do", "does", "did", "go", "went", "come", "came",
    "say", "said", "make", "made", "take", "took",
    "see", "saw", "know", "knew", "think", "thought",
    "get", "got", "give", "gave", "find", "found",
    "run", "ran", "walk", "sit", "sat", "stand", "stood",
    "eat", "drink", "sleep", "read", "write", "speak",
    # Common nouns
    "person", "man", "woman", "child", "boy", "girl",
    "cat", "dog", "bird", "fish", "animal",
    "house", "room", "door", "window", "wall", "floor",
    "tree", "water", "air", "fire", "earth",
    "time", "day", "night", "year", "week", "month",
    "hand", "eye", "head", "face", "body",
    "food", "book", "word", "name", "number",
    "thing", "place", "way", "world", "life",
    # Common adjectives
    "good", "bad", "big", "small", "old", "new", "young",
    "long", "short", "high", "low", "hot", "cold",
    "true", "false", "right", "wrong", "same", "different",
    "first", "last", "next",
    # Common adverbs & prepositions
    "not", "very", "also", "just", "now", "then",
    "here", "there", "up", "down", "in", "out", "on", "off",
    "with", "from", "to", "for", "at", "by", "about",
    # Conjunctions
    "and", "or", "but", "if", "when", "because", "while",
    # Question words
    "what", "who", "where", "when", "why", "how",
    # Numbers as words
    "one", "two", "three", "four", "five",
    "six", "seven", "eight", "nine", "ten",
    "hundred", "thousand",
]
