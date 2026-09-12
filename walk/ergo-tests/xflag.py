#!/usr/bin/env python3
"""
xflag.py -- the translation flag as one signed byte.

    sign  negative -> held in Isaac, never emitted
          positive -> travels, subject to what the target supports
          zero     -> unused on purpose (see note at bottom)

The seven low bits mean different things depending on the sign.

    POSITIVE side -- what a target must SUPPORT to hold this item
        bit 0   negation
        bit 1   conditional rules with priority
        bit 2   grouped aggregates
        bit 3   recursion over cycles
        bit 4   variables in the slot position
        bit 5   multi-valued slots
        bit 6   spare

    NEGATIVE side -- WHY it stays in Isaac
        bit 0   judged 0
        bit 1   record about Isaac's own run, not about the world
        bit 2   still mid-derivation, no settled value
        bit 3   held back deliberately
        bit 4   too costly to translate
        bit 5   spare
        bit 6   spare

One byte per item. Reading it costs a sign test and an AND.
"""

# ---- positive side: requirements
NEG, RULE, AGG, REC, METASLOT, MULTI = 1, 2, 4, 8, 16, 32
REQ_NAME = {NEG: "negation", RULE: "rules", AGG: "aggregates",
            REC: "recursion", METASLOT: "slot variables", MULTI: "multi-valued slots"}

# ---- negative side: reasons for holding
H_ZERO, H_SELF, H_UNSETTLED, H_DELIBERATE, H_COSTLY = 1, 2, 4, 8, 16
HOLD_NAME = {H_ZERO: "judged 0", H_SELF: "about Isaac's own run",
             H_UNSETTLED: "mid-derivation", H_DELIBERATE: "held back",
             H_COSTLY: "too costly to translate"}


def held(byte):
    return byte < 0


def bits(byte):
    """low seven bits, sign stripped"""
    return (-byte if byte < 0 else byte) & 0x7F


def make(hold_reasons=0, requirements=0):
    if hold_reasons:
        return -(hold_reasons & 0x7F)
    return requirements & 0x7F


def explain(byte):
    b = bits(byte)
    table = HOLD_NAME if held(byte) else REQ_NAME
    names = [n for k, n in table.items() if b & k]
    kind = "HELD" if held(byte) else "TRAVELS"
    return "%s (%s)" % (kind, ", ".join(names) if names else
                        ("no reason recorded" if held(byte) else "plain fact"))


def route(byte, target_supports):
    """Returns (send?, note)."""
    if held(byte):
        return False, "held: " + explain(byte)
    gap = bits(byte) & ~target_supports
    if gap:
        missing = [n for k, n in REQ_NAME.items() if gap & k]
        return False, "target lacks: " + ", ".join(missing)
    return True, "sent"


if __name__ == "__main__":
    ERGO = NEG | RULE | AGG | REC | METASLOT | MULTI
    PROLOG = RULE | AGG | REC
    TURTLE = 0

    items = [
        ("steel/conducts_heat",      make(requirements=0)),
        ("steel/galvanic_safe_with", make(requirements=NEG)),
        ("claim later_read",         make(requirements=NEG | RULE)),
        ("rule coverage",            make(requirements=AGG)),
        ("rule missing_axis",        make(requirements=RULE | METASLOT)),
        ("depends chain",            make(requirements=REC)),
        ("steel/supplier_code",      make(hold_reasons=H_ZERO)),
        ("steel/pass_count",         make(hold_reasons=H_SELF)),
        ("nylon/fatigue_est",        make(hold_reasons=H_UNSETTLED | H_COSTLY)),
    ]

    print("%-24s %5s  %s" % ("item", "byte", "meaning"))
    for name, f in items:
        print("%-24s %5d  %s" % (name, f, explain(f)))

    for tname, mask in [("ergo", ERGO), ("prolog", PROLOG), ("turtle", TURTLE)]:
        sent = [n for n, f in items if route(f, mask)[0]]
        print("\n--- %s ---  sent %d of %d" % (tname, len(sent), len(items)))
        for n, f in items:
            ok, note = route(f, mask)
            if not ok:
                print("    %-24s %s" % (n, note))
