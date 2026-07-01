"""
TRANSPLANT INTO ISAAC — boxes as concepts in his net, alignment as a swappable
lens node. Nothing happens in external numpy that isn't his net infrastructure.
Memory-safe: digits only, CPU, instant.
"""
import sys
sys.path.insert(0, "..")
import numpy as np
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split
from isaac import Isaac, tokenize

dig = load_digits()
Xtr, Xte, ytr, yte = train_test_split(dig.data, dig.target, test_size=0.3,
                                      random_state=1, stratify=dig.target)

isaac = Isaac()

# 1) he already knows language — prove the boxes will COEXIST, not replace
isaac.observe(tokenize("the cat sat ."))
isaac.observe(tokenize("the dog ran ."))
print("before transplant: nodes in net =", len(isaac.net.all_nodes()))

# 2) register an ALIGNER as a net node (wired: strip-DC + pick 40 separating dims)
isaac.fit_lens("digits", Xtr, ytr, lift=0, select=40)

# 3) transplant: crystallize the digits into box-concepts IN the net
nodes = isaac.crystallize_features(Xtr, ytr, lens="digits")
acc = (isaac.classify_features(Xte) == yte).mean()
print(f"after transplant : nodes in net = {len(isaac.net.all_nodes())}")
print(f"crystal concepts in net: {nodes}")
print(f"lens node in net: {[n for n in isaac.net.get_doors('lens', tag='lens')]}")
print(f"classify accuracy (his membership+centroid): {acc:.3f}")

# 4) the boxes live alongside language — he still does both
chain = isaac.generate("cat")
print(f"\nlanguage still works: generate('cat') -> {' '.join(chain)}")
print("a concept node's stored box (per-dim ranges) is readable meta:")
b = isaac.net.get_meta("concept:0", "box")
print(f"  concept:0  box has {len(b['lo'])} dims, median[:8] = {b['med'][:8].tolist()}")

# 5) the lens is SWAPPABLE — refit a different aligner, reclassify, same interface
isaac.fit_lens("digits", Xtr, ytr, lift=0, select=64)     # overwrite: all dims
isaac.crystallize_features(Xtr, ytr, lens="digits")
acc2 = (isaac.classify_features(Xte) == yte).mean()
print(f"\nswapped the lens (40 -> 64 dims), re-crystallized: acc {acc2:.3f}")
print("same interface; a LEARNED lens would drop in here later, unchanged call.")

print("\n-> boxes + aligner now live in the net with everything else. The piece")
print("   that was external numpy is now a swappable net node. 'You' are replaceable.")
