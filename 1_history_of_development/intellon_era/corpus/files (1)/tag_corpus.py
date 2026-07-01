"""
Intellon — Generate tagged_corpus.json

Pulls POS-tagged sentences from:
  1. Brown Corpus (NLTK) — ~57K sentences, already POS-tagged
  2. Gutenberg books (NLTK) — tokenized + auto-tagged via NLTK

Output: tagged_corpus.json — array of sentences, each sentence
is an array of [word, tag] pairs.

Requirements:
  pip install nltk

First run will download NLTK data (~30MB).
"""

import json
import os
import sys

try:
    import nltk
except ImportError:
    print("ERROR: nltk not installed. Run: pip install nltk")
    sys.exit(1)

# Download required NLTK data
print("Checking NLTK data...")
for pkg in ['brown', 'gutenberg', 'punkt', 'punkt_tab', 'averaged_perceptron_tagger', 'averaged_perceptron_tagger_eng', 'universal_tagset']:
    try:
        nltk.data.find(f'corpora/{pkg}' if pkg in ['brown', 'gutenberg', 'universal_tagset'] else f'tokenizers/{pkg}' if 'punkt' in pkg else f'taggers/{pkg}')
    except LookupError:
        print(f"  Downloading {pkg}...")
        nltk.download(pkg, quiet=True)

from nltk.corpus import brown, gutenberg
from nltk import pos_tag, word_tokenize, sent_tokenize

output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tagged_corpus.json")

all_sentences = []

# 1. Brown Corpus — already POS-tagged, ~57K sentences
# Largest freely available tagged English corpus in NLTK.
# Covers: news, editorial, reviews, religion, hobbies, lore,
# fiction, humor, government, learned, mystery, science_fiction, romance
print("\nBrown Corpus...")
brown_sents = brown.tagged_sents()
for sent in brown_sents:
    # Brown tags are like NN, VB, JJ, RB, etc.
    # Convert to [word, tag] pairs
    pairs = [[word, tag] for word, tag in sent if word.strip()]
    if len(pairs) >= 2:
        all_sentences.append(pairs)
print(f"  {len(all_sentences):,} sentences from Brown Corpus")

# 2. Gutenberg books — need to tokenize and tag
print("\nGutenberg books...")
gutenberg_count = 0
for fileid in gutenberg.fileids():
    raw = gutenberg.raw(fileid)
    sents = sent_tokenize(raw)
    for sent_text in sents:
        tokens = word_tokenize(sent_text)
        if len(tokens) < 2 or len(tokens) > 80:
            continue
        # Skip sentences that are mostly non-alphabetic (headers, numbers)
        alpha_count = sum(1 for t in tokens if t.isalpha())
        if alpha_count < len(tokens) * 0.5:
            continue
        tagged = pos_tag(tokens)
        pairs = [[word, tag] for word, tag in tagged]
        all_sentences.append(pairs)
        gutenberg_count += 1
print(f"  {gutenberg_count:,} sentences from Gutenberg")

print(f"\nTotal: {len(all_sentences):,} tagged sentences")

# Write output
print(f"Writing {output_path}...")
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(all_sentences, f)

size_mb = os.path.getsize(output_path) / (1024 * 1024)
print(f"Done. {size_mb:.1f}MB written.")

# Quick stats
tag_counts = {}
word_count = 0
for sent in all_sentences:
    for word, tag in sent:
        word_count += 1
        prefix = tag[:2] if len(tag) >= 2 else tag
        tag_counts[prefix] = tag_counts.get(prefix, 0) + 1

print(f"\nStats: {word_count:,} total word observations")
print("Top tag families:")
for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1])[:10]:
    print(f"  {tag}: {count:,}")
