# Isaac — Implementation Rules and Lessons

## What We Have Learned About How to Build This System

These rules were discovered through building, breaking, rebuilding, and testing. Each one corresponds to a specific failure or breakthrough. They are not theoretical preferences — they are empirical constraints on correct implementation.

---

## Rule 1: No Preprocessing. Ever.

**The failure:** The original Session 10 built `_detect_patterns()`, `_classify_question()`, and `_find_subject()`. These extracted structured relationships from text before the walker observed it. Three versions were written, each making the same mistake.

**Why it's wrong:** Preprocessing means running code on the input that makes decisions about structure before the net sees the raw data. "X is Y" being parsed into a property relationship is a decision. "What" being classified as a question word is a decision. Skipping "the" because it's in a determiner list is a decision. All of these decisions are Isaac 2's job — structural analysis that should happen AFTER observation, by comparing what's in the net, not before.

**The rule:** Text enters as tokens. Tokens become sequential doors. That is ALL observation does. If you find yourself writing code that looks at input and decides what kind of thing it is before calling observe(), you are preprocessing. Stop.

**The test:** Can you remove the code and still call observe() on the same input? If yes, the code was preprocessing. If no, the code IS observation.

---

## Rule 2: The Net Is the Knowledge. Not Your Code.

**The failure:** Early implementations put knowledge in Python — lists of determiners, adjective ordering rules, verb classification logic. This knowledge lived in the code, not in the net.

**Why it's wrong:** Knowledge in code can't be discovered, corrected, extended, or reasoned about by the system. Knowledge in the net can. A list of determiners in Python is invisible to the walker. A set of doors from "the"/"a"/"an" to noun-type words IS the determiner concept, walkable and discoverable.

**The rule:** If the system needs to know something, put it in the net as doors. If you need adjective classes, seed them as class-tagged doors. If you need word order constraints, they should emerge as lockouts from negative examples. If you need morphological rules, they should emerge from type membership comparison.

**The exception:** Tokenization (splitting text into words, separating punctuation) is pre-net processing that is acceptable because it defines what a NODE is, not what a DOOR means.

---

## Rule 3: If It Will Be Discovered Later, You Can Give It a Hand Now.

**The insight:** The designer said: "if this is something that will be discovered or built later inevitably, then we can just give it a hand."

**What it means:** Seeding the net with known knowledge is NOT preprocessing. `seed_class("size", ["big", "small"])` adds doors to the net. Those doors are walked exactly like any other doors. The walker doesn't know whether a door was observed, seeded, or crystallized — it walks them all the same way.

**The distinction:** Teaching adds doors. Preprocessing runs code. Teaching says "big and small are the same class" by adding class-tagged doors. Preprocessing says "if the word is in the adjective list, route it differently" by adding Python logic.

**The rule:** When you know something the crystallizer will eventually discover, you can seed it. The knowledge must live in the net as doors, not in the code as logic.

---

## Rule 4: Same Operation at Every Scale.

**Claim 8.** Every time you find yourself building a special-case handler, a new algorithm, or a different mechanism for a specific situation, stop and ask: is this the Comparator applied at a different scale?

**Confirmed instances:**
- Nodes compared → type groups (circles)
- Circles compared → hierarchy (classes)
- Types compared → parent/child (recursive stabilization)
- Predecessors compared → co-occurrence rules
- Tag sets compared → violations and lockouts
- Crystallizer output compared against itself → condensation

**The rule:** If a new capability cannot be expressed as "take two sets, compare them (shared/absent), act on the result," it probably violates the architecture. Redesign until it can.

---

## Rule 5: Store Raw, Derive on Demand.

**Claim 9.** Don't aggregate at storage time. The raw observations support all current AND future derivations. The moment you compute a summary and store it instead of the raw data, you lose the ability to derive things you haven't thought of yet.

**Concrete example:** Weights were the Isaac 2 version of aggregation. A weight of +5 on a pointer meant "seen 5 times, all positive." But that weight destroyed the individual observations. You couldn't ask "in what contexts was this seen?" or "which of those 5 observations was wrong?" You could only ask "how many times?"

**The rule:** Observe stores doors. Crystallize derives types, rules, hierarchies. The derivations are tagged doors added to the net — they don't replace the raw observations. Both coexist. The raw seq doors and the crystallized type doors are both in the net, walked through different gates.

---

## Rule 6: Doors Exist or They Don't. No Weights.

**The removal:** Isaac 2 used 64-bit packed pointers with 8-bit signed weights (-127 to +127). The walker drops all of this.

**Why weights are unnecessary:** The strength of a pattern is computable from the graph structure. How many predecessors does "cat" have? How many of them are in the determiner type? The answer is a walk, not a stored number. Storing the number prevents the system from discovering that the same connection has different significance in different contexts.

**Why weights are harmful:** A weight is a compression. +5 means "seen 5 times, all positive." But what if one of those 5 observations was wrong? You can't undo one observation from a weight. With doors, you can: each observation is a separate structural fact, and error correction adds the right doors without needing to modify the wrong ones.

**The rule:** A door is present or absent. There is no "how much." Strength, frequency, confidence — all derivable from graph structure at query time, not stored on edges.

---

## Rule 7: The Boundary Is Absolute.

**Isaac 1 does not analyze.** It observes, walks, generates, recombines. It does NOT examine its own structure, discover types, compute rules, or reason about why something worked or failed.

**Isaac 2 does not do rote recall.** It compares, discovers, crystallizes, reasons. It does NOT generate sentences, walk sequential doors for output, or handle routine interactions.

**The failure mode:** Blurring the boundary. Putting analytical code in the walker ("detect what kind of sentence this is"). Putting generation code in the crystallizer ("produce a sentence that matches this type pattern").

**The rule:** When Isaac 1 has no doors and no path, it escalates to Isaac 2. When Isaac 2 discovers a pattern, it crystallizes it into doors that Isaac 1 can walk. The result of analysis is always: new doors in the net. Never: direct output to the user.

---

## Rule 8: Correctability Over Correctness.

**Claim 7.** Design for error recovery, not error avoidance.

**What this means in practice:** The system WILL generate "is old woman walked." That's fine. What matters is:
- The error is detectable (type hierarchy shows "is" in wrong position)
- The error is diagnosable (predicate word used as initiator)
- The error is correctable (add the right doors, apply lockout)
- The correction compounds (lockout prevents ALL similar errors, not just this one)

**The anti-pattern:** Building elaborate validation to prevent errors before they happen. Checking every generation step against every rule. This is preprocessing in disguise — you're analyzing output before it's produced.

**The rule:** Generate. If wrong, correct. If repeatedly wrong, crystallize the error pattern into a lockout. Each mistake makes the system better. Preventing mistakes prevents learning.

---

## Rule 9: Keep Walks Short. Hub Nodes Are the Enemy.

**The failure:** s9 generation traced one long backward path through the entire net. At scale (500+ nodes), hub nodes ("the" with 184 connections, "." with 222) connected everything to everything. Long walks through hubs produced garbled cross-sentence output.

**The solution:** Grouped generation. Each concept is its own chain of 2-4 words. A chain traces backward from one anchor to one initiator. It never walks far enough to cross a sentence boundary through a hub node.

**The rule:** Design walks to be short. If a walk might pass through a hub node and emerge in unrelated territory, the walk is too long. Break it into smaller walks. The grouped generation mechanism exists specifically because of this constraint.

**The generalization:** This applies to all walks, not just generation. Comprehension walks should be bounded. Type discovery walks should be bounded. Any unbounded walk through a growing net will eventually hit a hub and produce garbage.

---

## Rule 10: Negative Meaning Comes from Contrast, Not Storage.

**The insight:** The system has no concept of "not." No negative weights, no anti-doors, no boolean flags marking things as false.

**How negation works:** Observe good sentences with "seq" tag. Observe bad sentences with "neg" tag. The Comparator runs on the two tag sets. The DIFFERENCE is the negative meaning. Doors in neg but not seq are violations. Doors in seq but not neg are rules.

**Why this matters:** Negative knowledge is always relative to positive knowledge. "Wrong" is defined by contrast with "right." As the positive set grows, what counts as a violation may change. A door that was neg-only becomes ambiguous when it's also observed in a good sentence. The system's understanding of wrongness evolves with its understanding of correctness.

**The rule:** Never store "this is bad" as a label. Store the observation with a different tag. Let the comparison derive the negative meaning. The tag separation plus the Comparator IS negation.

---

## Rule 11: Tags Separate Concerns. The Gate Is a Tag Filter.

**The design:** The same net holds sequential structure (seq), semantic properties (prop), negative examples (neg), type membership (type), violations (lockout). All coexisting on the same nodes and doors.

**Why tags, not separate nets:** Because the same word participates in all of these simultaneously. "Cat" has seq doors (word order), prop doors (properties), type doors (membership), and potentially lockout doors (violations). Putting these in separate nets would lose the connections between them.

**The gate mechanism:** `get_doors(node, tag="seq")` returns only seq-tagged doors. `get_doors(node, tag="type")` returns only type-tagged doors. The tag parameter IS the gate. No separate gate module, no gate scores, no gate learning. Just a filter on which doors to walk.

**The rule:** When adding a new kind of knowledge to the system, add a new tag. Don't build a new data structure. The net is the universal container. Tags are the separators.

---

## Rule 12: The Crystallizer Crystallizes Itself.

**The breakthrough:** 459 raw circles were too many to be useful. But running the same comparison operation on the circles themselves — merging overlapping circles, building hierarchy from subset relationships, recursively assigning parents — collapsed them to 59 roots at 5 levels deep.

**The principle:** If the output of an operation can be fed back as input to the same operation, do it. Keep going until the output stabilizes (no new discoveries). This is recursive stabilization.

**Concrete phases:**
1. Merge: circles with 80%+ member overlap → union (same pattern, different samples)
2. Hierarchy: circles whose members are 80%+ contained in a larger circle → parent/child
3. Recursive: if a type's predecessor is a member of another type → sub-behavior. Loop until stable.

**The rule:** Always ask: can the crystallizer's output be crystallized further? If yes, loop. The number of passes needed is itself informative — more passes means deeper structure.

---

## Rule 13: Two Random Samples of the Same Thing Combine.

**The designer's insight:** "You have two random sample sets of the same thing. A has 95% of the things and B has 95% of the things and together they have 90% overlap, and the answer space for what is missing in both to get 99% is there."

**What it means:** FCA closure from different seed pairs produces circles that are ALMOST the same but not quite. Each captures most of the true group with a different few members missing. The union of their members is closer to the true group than either alone.

**The implementation:** During merge, take the union of members (fuller picture) and the intersection of structural requirements (what they agree on).

**The caution:** Intersection of preds/succs can be too aggressive. If one circle found "the" as a predecessor and another found "a", the intersection loses both. Majority vote (70%+) preserves what most circles agree on.

**The rule:** When multiple discoveries point to the same pattern, merge them. The combined view is better than any individual view. But use majority agreement on structure, not unanimous agreement.

---

## Rule 14: Test With Real Data Early and at Scale.

**The failure:** The s9 walker passed all 18 unit tests. It failed at scale because unit tests used small nets (10-30 words) that didn't have hub nodes dense enough to cause problems.

**What scale testing revealed:**
- Hub contamination in long walks (→ grouped generation fix)
- "Is" being used as an initiator (→ crystallizer initiator ranking fix)
- Missing modifier doors for unseen combinations (→ type inference fix)
- Chain length explosion through dense hubs (→ max_back limit)

**The rule:** Unit tests verify mechanism. Scale tests verify behavior. Both are necessary. After any architectural change, run the stress test (379+ sentences) and check for regressions. The problems that matter only appear at scale.

---

## Rule 15: Don't Build Forward When You Should Trace Backward.

**The failure:** The original Session 10 attempted forward generation — start from a determiner, walk forward through the net, collect words. This is wrong because forward walks have no goal. They wander.

**The correct approach:** Start from the concept (the anchor — the thing you want to say). Walk BACKWARD to find what precedes it. The walk has a goal: reach an initiator. The backward direction constrains the walk — you're looking for a specific structural position, not wandering through possibilities.

**The rule:** Generation is backward tracing, not forward walking. The concept is the destination you reverse-engineer a path to. The initiator is the start you discover by walking backward from the concept.

---

## Rule 16: Information Only Enters, Never Leaves.

**The one rule from which the architecture follows.** The net grows monotonically. Doors are added but never removed. Error correction adds the right doors — it does not delete the wrong ones. The wrong doors remain in the net but become structurally irrelevant as more correct doors accumulate around them.

**Why this matters:** Deletion is a decision. It requires knowing what's wrong and being sure. The system is never sure. But it can always add more information, and more information makes the net more accurate without requiring certainty about what to remove.

**The rule:** No delete operations on the net. No modify operations on doors. Add only. If something is wrong, add more context that makes the wrong thing irrelevant, don't try to remove it.

---

## Rule 17: The Name Doesn't Matter. The Structure Does.

**The observation:** The crystallizer names types like `the→?[64]` and `?→?[27]`. These names are ugly and uninformative. It doesn't matter. The TYPE is its member set, its pred/succ signature, and its position in the hierarchy. The name is a display convenience.

**The anti-pattern:** Trying to make the crystallizer produce human-readable names like "noun" or "adjective." That would require the crystallizer to know what nouns and adjectives ARE, which is exactly what it's supposed to be discovering.

**The rule:** Let discovery produce structural descriptions, not labels. The human can label them after the fact. The system operates on structure, not names. `the→?[64]` IS the noun type whether or not anyone calls it that.

---

## Rule 18: The Distinction Between Nouns and Verbs Is Structural, Not Tagged.

**The discovery:** Nouns have determiners as direct predecessors (the→cat, a→dog). Verbs have nouns as predecessors (cat→ran, dog→barked). The walker doesn't need POS tags to tell them apart — the door pattern IS the distinction.

**In generation:** `_standalone_chain("cat")` checks if "cat" has a start-word predecessor. It does ("the"). So it's noun-like: chain = ["the", "cat"]. `_standalone_chain("ran")` checks for start-word predecessors. None. So it's verb-like: chain = ["ran"].

**The rule:** If you're about to add a POS tag, a word-class label, or a linguistic category to the system, stop. Check whether the distinction already exists in the door structure. It almost certainly does. Use the structure, not a label.

---

## Summary

These 18 rules reduce to a handful of principles:

1. **The net is everything.** All knowledge lives there as doors. Not in code, not in labels, not in weights.
2. **One operation.** Comparison. Applied at every scale. If you're building something that isn't comparison, you're probably wrong.
3. **Observe raw, derive later.** Don't make decisions during input. Make decisions during crystallization.
4. **Errors are information.** Don't prevent them. Learn from them. Correct them. Compound the corrections.
5. **Short walks, tagged doors, recursive self-improvement.** Keep it local, keep it separated, keep it looping.
