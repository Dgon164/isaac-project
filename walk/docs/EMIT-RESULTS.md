# One map, three targets

`emit.py` takes the same `isaac_map.json` and writes Ergo, plain Prolog, or
RDF triples. Isaac's own form knows nothing about any of them. Each emitter
reports what it could not carry.

    [ergo]    30 lines out, 2 withheld as 0, 0 not carried
    [prolog]  28 lines out, 2 withheld as 0, 6 not carried
    [turtle]  19 lines out, 2 withheld as 0, 7 not carried

## What each target dropped

**Ergo** — nothing. Explicit negation, rule priorities and frames all have
a direct home.

**Plain Prolog** — three negatives had to become a separate `neg_slot`
relation rather than a real negation, both claims lost their priority, and
the supersession was dropped entirely.

**RDF** — the three negatives vanished (RDF has no negation), and every rule
went with them (RDF carries no rules at all).

## What that costs, measured

The Prolog emission was run on XSB. Same facts, same map:

    isa steel material:   YES        (matches Ergo)
    agree:                [transfers_force]   (matches)
    differ:               [reversible]        (matches)
    open axes:            3, same three       (matches)
    withheld leaked:      NO                  (matches)

    POSITIVE nylon suitable_for hot_section:  YES
    NEGATIVE nylon suitable_for hot_section:  YES     <-- both

In Ergo the same query gives No to the positive and Yes to the negative,
because the supersession resolves it. In Prolog both hold at once. The
contradiction is sitting in the store and nothing complains.

So the structural work carries everywhere. Class transitivity, the 0
withholding, the open-axis records and the comparison rules all survived all
three targets unchanged. What does not carry is the part that decides between
two conflicting claims.

## Suggested reading of this

Isaac keeping his own form, with emitters on top, looks better than storing
natively in Ergo's form. Two reasons:

1. Ergo has no home for the value 0 by design, since you rule it never leaves.
   Storing natively in Ergo would mean Isaac carries three values, not four.
2. The loss report is itself worth having. "How much of Isaac survives in
   target X" comes out as a number, not an opinion, so a candidate engine can
   be ranked by running the emitter at it rather than by reading its manual.

Adding a target means writing one function of about thirty lines. Nothing in
the map changes.
