#!/usr/bin/env python3
"""
Convert WordNet JSON to Intellon fact files with sense support.

For multi-sense words, outputs each sense as a separate is_a statement.
The Intellon load command auto-splits these into /1, /2, etc.

Usage:
  python3 wordnet_to_facts.py                        # defaults
  python3 wordnet_to_facts.py --max-senses 3         # max 3 senses per word
  python3 wordnet_to_facts.py --max 5000             # limit total facts
  python3 wordnet_to_facts.py --no-multi-word         # skip "ice cream" etc
  python3 wordnet_to_facts.py --rels is_a             # only is_a
  python3 wordnet_to_facts.py --rels is_a,opposite_of,eq  # multiple types

Output: intellon_facts.txt — loadable with: load intellon_facts.txt
"""

import json
import argparse
import os
import sys
from collections import defaultdict

def extract_parent(hypernym_id):
    return hypernym_id.split('.')[0].replace('_', ' ')

def main():
    parser = argparse.ArgumentParser(description='Convert WordNet to Intellon facts')
    parser.add_argument('--input', default='wordnet_full.json', help='WordNet JSON file')
    parser.add_argument('--output', default='intellon_facts.txt', help='Output facts file')
    parser.add_argument('--max', type=int, default=0, help='Max total facts (0 = unlimited)')
    parser.add_argument('--max-senses', type=int, default=5, help='Max senses per word')
    parser.add_argument('--rels', default='is_a,opposite_of,eq', help='Relationship types')
    parser.add_argument('--min-word-len', type=int, default=2, help='Min word length')
    parser.add_argument('--no-multi-word', action='store_true', help='Skip multi-word entries')
    args = parser.parse_args()

    input_path = args.input
    if not os.path.exists(input_path):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        input_path = os.path.join(script_dir, args.input)
    if not os.path.exists(input_path):
        print(f"ERROR: Cannot find {args.input}")
        sys.exit(1)

    print(f"Reading {input_path}...")
    with open(input_path) as f:
        entries = json.load(f)
    print(f"  {len(entries):,} entries loaded")

    rel_types = set(args.rels.split(','))

    # Group by word to handle senses
    word_entries = defaultdict(list)
    for e in entries:
        word = e['word']
        if len(word) < args.min_word_len:
            continue
        if args.no_multi_word and ' ' in word:
            continue
        word_entries[word].append(e)

    facts = []
    seen = set()
    sense_splits = 0

    for word, word_group in word_entries.items():
        # Deduplicate by sense ID
        seen_senses = set()
        unique_senses = []
        for e in word_group:
            if e['sense'] not in seen_senses:
                seen_senses.add(e['sense'])
                unique_senses.append(e)

        # Limit senses per word
        senses_to_use = unique_senses[:args.max_senses]

        if len(senses_to_use) > 1:
            sense_splits += 1

        for i, entry in enumerate(senses_to_use):
            # is_a from hypernyms
            if 'is_a' in rel_types and entry.get('hypernyms'):
                parent = extract_parent(entry['hypernyms'][0])  # primary hypernym
                if len(parent) >= args.min_word_len:
                    fact = f"{word} is_a {parent}"
                    if fact not in seen:
                        seen.add(fact)
                        facts.append(fact)

            # opposite_of from antonyms (only for first sense to avoid noise)
            if 'opposite_of' in rel_types and i == 0 and entry.get('antonyms'):
                for ant in entry['antonyms'][:2]:  # max 2 antonyms
                    if len(ant) >= args.min_word_len:
                        fact = f"{word} opposite_of {ant}"
                        reverse = f"{ant} opposite_of {word}"
                        if fact not in seen and reverse not in seen:
                            seen.add(fact)
                            facts.append(fact)

            # eq from synonyms (only for first sense)
            if 'eq' in rel_types and i == 0 and entry.get('synonyms'):
                for syn in entry['synonyms'][:2]:  # max 2 synonyms
                    if len(syn) >= args.min_word_len:
                        fact = f"{word} eq {syn}"
                        reverse = f"{syn} eq {word}"
                        if fact not in seen and reverse not in seen:
                            seen.add(fact)
                            facts.append(fact)

        if args.max and len(facts) >= args.max:
            facts = facts[:args.max]
            break

    # Write output
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(f"# Intellon facts from WordNet\n")
        f.write(f"# {len(facts):,} relationships from {len(word_entries):,} words\n")
        f.write(f"# Multi-sense words: {sense_splits:,} (max {args.max_senses} senses each)\n")
        f.write(f"# Auto-splits into senses on load\n\n")
        for fact in facts:
            f.write(fact + '\n')

    # Stats
    rel_counts = {}
    for fact in facts:
        parts = fact.split(' ', 2)
        if len(parts) >= 2:
            rel = parts[1]
            rel_counts[rel] = rel_counts.get(rel, 0) + 1

    print(f"\nWritten {len(facts):,} facts to {args.output}")
    print(f"  Multi-sense words: {sense_splits:,}")
    for rel, count in sorted(rel_counts.items(), key=lambda x: -x[1]):
        print(f"  {rel}: {count:,}")
    size_kb = os.path.getsize(args.output) / 1024
    print(f"  File size: {size_kb:.1f}KB")

if __name__ == '__main__':
    main()
