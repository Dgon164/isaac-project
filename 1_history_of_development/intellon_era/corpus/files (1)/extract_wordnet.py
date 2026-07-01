#!/usr/bin/env python3
"""
Extract WordNet data to JSON for Intellon e-series.
Run once: python3 extract_wordnet.py
Requires: pip install nltk
Output: wordnet_full.json (~43MB) in the same directory
"""

import json
import os
import sys

try:
    import nltk
except ImportError:
    print("ERROR: nltk not installed. Run: pip install nltk")
    sys.exit(1)

# Download WordNet data if not present
print("Checking NLTK data...")
nltk.download('wordnet', quiet=True)
nltk.download('omw-1.4', quiet=True)

from nltk.corpus import wordnet as wn

print("Extracting WordNet entries...")
entries = []

for synset in wn.all_synsets():
    pos = synset.pos()
    definition = synset.definition()
    examples = synset.examples()
    synset_id = synset.name()
    hypernyms = [h.name() for h in synset.hypernyms()]

    for lemma in synset.lemmas():
        word = lemma.name().replace('_', ' ')
        antonyms = [a.name().replace('_', ' ') for a in lemma.antonyms()]
        synonyms = [l.name().replace('_', ' ') for l in synset.lemmas() if l.name() != lemma.name()]

        entry = {
            "word": word,
            "pos": pos,
            "sense": synset_id,
            "def": definition,
        }
        if hypernyms:
            entry["hypernyms"] = hypernyms
        if antonyms:
            entry["antonyms"] = antonyms
        if synonyms:
            entry["synonyms"] = synonyms
        if examples:
            entry["examples"] = examples

        entries.append(entry)

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wordnet_full.json")
print(f"Writing {len(entries):,} entries to {out_path}...")

with open(out_path, "w") as f:
    json.dump(entries, f)

size_mb = os.path.getsize(out_path) / (1024 * 1024)
print(f"Done. {size_mb:.1f} MB")

# Quick sanity check
unique_words = len(set(e["word"] for e in entries))
unique_synsets = len(set(e["sense"] for e in entries))
print(f"  Entries: {len(entries):,}")
print(f"  Unique words: {unique_words:,}")
print(f"  Unique synsets: {unique_synsets:,}")
