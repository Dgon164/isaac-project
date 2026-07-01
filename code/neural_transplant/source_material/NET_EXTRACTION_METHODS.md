# Extracting Information from Neural Nets — Methods & Findings

*A shareable write-up of a technique for reading structure out of trained neural
networks, evidence that it transfers across independently-trained nets, and what
untrained random "reservoirs" tell you. Numbers are from a hard tabular benchmark
(forest cover type, 581k rows, 54 features, 7 classes) and are included as
supporting detail, not as the point. The point is the method.*

---

## The short version

You extract from a net by **crystallizing its activations into boxes**
(membership) and **centroids** (where the real signal is), **turning units into
crisp "doors"** to mine higher-order structure, **gating everything by
surprise-against-chance** rather than by frequency, **confirming features by their
recurrence across independently-trained nets**, and using **untrained random
reservoirs** as the zero-training baseline that tells you what was linearly present
before any learning happened.

---

## 1. Crystallization — read the net instead of running its classifier

A trained net's hidden layers do the real work; the final classification layer is
just a linear readout on top of them. So instead of using that readout, treat each
hidden unit as a coordinate and describe each class as a **box** in activation
space: for every unit, the range of values that class occupies, plus its median
(center). Classify a new point by (a) how many of its activations fall inside each
class's box — *membership* — and (b) how close it sits to each box's center — the
*tiebreak*. You have replaced the net's opaque output layer with a transparent,
inspectable geometric one. **The net becomes a lens that produces features; the box
reads them.**

This is what produced usable accuracy in our tests — reading boxes off a *trained*
net's activations works because the net has already done the partitioning and the
implicit feature-combining a raw box can't. (For reference: raw single boxes floored
near chance-plus; crystallizing a trained net reached the ~0.72–0.75 range on a
benchmark where the net itself ceilinged at ~0.83 and a random forest at ~0.95.)

---

## 2. The key practical finding: membership and distance are two different jobs

Whether an activation falls inside a class's range is **coarse** — it barely changes
when you change numeric resolution (it's monotone-invariant). But the **distance to
the class center** carries most of the discriminative signal. In one direct test,
sharpening the centroid distance (full resolution, instead of a coarse quantized
grid) jumped accuracy from 0.589 to 0.738 — and the membership test contributed
*nothing* to that gain. Weighting each feature in the distance by how much it
separates the classes pushed it a little further (0.748).

**Transferable lesson:** when you extract from a net, spend your resolution on the
*centroid distances*, not on the boundaries. The walls do membership; the center
does discrimination; don't blur the center.

---

## 3. Doors — turning fuzzy activations into discrete features

Threshold each unit (fires / doesn't) and a hidden unit becomes a binary **door**.
Once units are doors, you can mine which doors **co-activate** — which combinations
fire together to mark a class — and promote stable combinations to new higher-order
features. This is how you get *symbolic* structure out of a *continuous* net: the
net produces door-states, you read door-sets.

**Critical caveat (learned the hard way):** this only works if the doors are
**crisp**. Units that sit near their threshold produce "flapping" doors, and the
structure you mine off them is noise. A net with decisive, bimodal activations is a
good door-maker; a mushy one isn't. If door-mining overfits, suspect the doors
before the miner.

---

## 4. The gate that actually matters — surprise, not frequency

When mining co-activations, the naive move is to keep the **frequent** or the
**"pure"** combinations. This overfits badly: you find tiny pockets that look
perfect by luck. Replacing the frequency/purity gate with a **surprise** gate fixes
it. Surprise = how much more often a combination co-occurs (or concentrates a class)
than chance would predict, **corrected for how many candidates you searched** —
because searching many candidates manufactures apparent surprise by chance, and you
have to pay that back (a "look-elsewhere" correction: subtract the log of the number
of candidates examined).

In our runs this flipped mined composites from *hurting* accuracy to *helping* it,
and kept well-supported, moderately-concentrated features instead of tiny pure-by-
luck pockets. On a clean synthetic with a planted relationship plus a common-but-
meaningless decoy, surprise separated the real one (high) from the decoy (≈0), while
plain frequency-counting ranked the *meaningless* one highest.

**This is the single most transferable piece:** extract by surprise-against-chance,
and pay for your search.

---

## 5. It transfers across nets — with a sharp caveat

Run several **independently-trained** nets on the **same inputs**, and you can match
their internal features by *what fires together on the same data*: same input, two
nets, units that co-activate on the same examples are encoding the same thing. The
genuinely real features show up **across** independent nets; one net's private
quirks don't. That recurrence is the basis for *trusting* an extracted feature — a
distinction that's real shows up no matter which net you look through; a coincidence
lives in one and vanishes in the next. (The proper tool for matching is canonical
correlation, which finds shared *directions*, not just shared single neurons, since
a feature can be one unit in net A and a combination of units in net B.)

**The caveat we measured:** "shared across nets" is **broader** than "useful."
A large part of what's shared is just the **input's own geometry**, which *any*
projection preserves — even a *random untrained* one. In one test a random
projection shared dozens of strong directions with a trained net. So cross-net
agreement tells you a feature is **real**, but you still need a **separate** test
that it's **discriminative** for your task. Recurrence and usefulness are two
filters, not one — and the most decorrelated pair of trained nets shared only a
handful of strong directions (close to the task's true signal dimensionality),
which is the tight, meaningful set.

---

## 6. The reservoir findings (untrained random projections)

A **reservoir** is an *untrained* random projection: multiply the input by a fixed
random matrix, apply a nonlinearity, and read boxes off *that* — no learning at all.
What we found:

- A **single** random projection reads above chance but **weakly** — it preserves
  the input's linear structure and nothing more.
- **Voting across several independent reservoirs** improves it: different random
  lenses have decorrelated errors, so the vote cancels noise. (Ensembling
  decorrelated random projections is the right way to use them; single ones are
  noisy.)
- On hard data with many **categorical / binary** features, raw reservoirs stayed
  weak — random projections of binary flags don't expose much structure.

**Why reservoirs are worth running anyway:**
1. A random lens is a real **zero-training baseline** — it tells you how much
   structure is **linearly present** before any learning.
2. The **gap** between reservoir performance and trained-net performance is a clean
   measure of **how much the training actually bought you** versus what was there
   for free.
3. Reservoirs are decorrelated by construction, which makes them the honest test
   bed for the cross-net recurrence idea above (agreement among random lenses is
   the null; agreement among trained lenses above that null is learned structure).

---

## 7. Putting it together (the workflow)

1. **Crystallize** — read class boxes (membership + centroid) off a trained net's
   activations instead of using its output layer.
2. **Resolve on the centroid** — that's where the discrimination is; weight the
   distance by per-feature separation.
3. **Binarize to doors** — only if the units are crisp; mine co-activation
   structure across door-sets.
4. **Gate by surprise** — keep combinations that beat chance, corrected for search
   size; never gate by raw frequency or purity.
5. **Confirm across nets** — trust features that recur across independently-trained
   nets (match by co-firing / canonical correlation), then separately confirm
   they're discriminative.
6. **Baseline with reservoirs** — untrained random projections tell you what was
   linearly free, and the trained-minus-reservoir gap is what learning earned.

---

## Honest limits (so the method isn't oversold)

- Crystallization reads what the net encodes; it can't exceed the net's own ceiling,
  and the net can't exceed the data's information floor. On a Bayes-limited problem
  the whole stack plateaus where the data does — extraction makes the structure
  *legible*, it doesn't add signal that isn't there.
- Door-mining is only as good as the doors' crispness.
- Cross-net recurrence proves "real," not "useful" — keep the two filters separate.
- Reservoir strength is data-dependent; weak on binary/categorical-heavy inputs.

---

*Method note. The numbers are illustrative of the techniques, not the headline; the
techniques — crystallize, resolve-on-centroid, crisp doors, surprise-gating,
cross-net recurrence, reservoir baselining — are the transferable part.*
