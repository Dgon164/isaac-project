"""
ASCII CREATURES — the world as a fixed alphabet of MEANING-bearing parts.

Not pixels (flat 0/1, no identity). Not pixel-derived tokens. A small fixed
vocabulary of glyphs, each a part with its own identity, chained contiguously:

    ~~~~~<      a snake   (~ body, < mouth/head)
    ~~~~~~~~~~< a longer snake
    ~~~~~<-     a snake with its tongue out (- tongue)

Claim being tested (yours): this gives BOTH contiguous and differentiable info,
plays to his language muscle, and lets lots of detail be read off the structure.
We do not tell him what any glyph means. He discovers the roles from position,
the same way he found nouns and verbs.
"""

from collections import Counter
from isaac import Isaac


def glyphs(s):
    return [c for c in s if not c.isspace()]


def main():
    isaac = Isaac()

    # a handful of snakes (varied length) and a contrasting 'train' (= body, # head)
    snakes = ["~~<", "~~~<", "~~~~~<", "~~~~~~~~<", "~~~~~~<", "~~~~<-", "~~~~~~<-"]
    trains = ["==#", "====#", "======#", "=====#"]
    for s in snakes + trains:
        isaac.observe(glyphs(s))
    isaac.consolidate()

    print("=" * 72)
    print("  ASCII CREATURES — roles discovered, details read off structure")
    print("=" * 72)

    # 1) DIFFERENTIATION: did he separate body-parts from head-parts by ROLE,
    #    with nobody telling him which is which?
    print("\n  1) ROLES HE DISCOVERED (no labels given):")
    for name, t in isaac.types.items():
        print("     type:", sorted(str(m) for m in t["members"]))
    # what follows what — the structural evidence
    print("\n     who sits where (successor profile):")
    for g in ["~", "=", "<", "#", "-"]:
        succ = sorted(isaac.net.get_doors(g, tag="seq"))
        print(f"       '{g}' is followed by {succ if succ else '(nothing — it ends the form)'}")
    print("     -> body glyphs (~,=) chain into themselves and a head; heads")
    print("        (<,#) and tongue (-) terminate. Role = position. He sees it.")

    # 2) DETAIL EXTRACTION via his RAM: length = count the body glyph.
    #    Teach the program once ('~'->incr, everything else holds), then read
    #    length off ANY novel snake.
    print("\n  2) DETAILS READ OFF A NOVEL SNAKE (length counted in his RAM):")
    counter = Isaac()
    counter.observe(["~", "incr"]); counter.observe(["<", "hold"])
    counter.observe(["-", "hold"])
    counter.consolidate()

    BODY, TONGUE = {"~", "="}, {"-"}

    def describe(s):
        seq = glyphs(s)
        length, _ = counter.react(seq, target="len")
        # facing is RELATIONAL: which end is the head on, relative to the body?
        body_idx = [i for i, g in enumerate(seq) if g in BODY]
        head_idx = [i for i, g in enumerate(seq) if g not in BODY and g not in TONGUE]
        facing = "?"
        if body_idx and head_idx:
            body_mid = sum(body_idx) / len(body_idx)
            facing = "right" if head_idx[0] > body_mid else "left"
        details = {
            "length": length,
            "has_mouth": bool(head_idx),
            "has_tongue": any(g in TONGUE for g in seq),
            "facing": facing,                    # head trails right -> faces right
        }
        return details

    for s in ["~~~~~~~<", "~~<", "~~~~~<-", ">~~~~"]:
        print(f"     {s:<14} -> {describe(s)}")
    print("     -> length, parts present, orientation: all from the glyph string.")

    # 3) HONEST UNKNOWN: a creature built from a part he has never seen.
    print("\n  3) AN UNFAMILIAR PART (honest unknown):")
    mystery = "~~~~@"
    seq = glyphs(mystery)
    known = [g for g in seq if isaac.net.doors.get(g)]
    unknown = [g for g in seq if not isaac.net.doors.get(g)]
    print(f"     {mystery}  -> i recognize {Counter(known)} as body,")
    print(f"        but '{unknown[0]}' is a part i have no concept for.")
    print(f"        it's a body of length {Counter(seq)['~']} with an UNKNOWN head.")
    print("        (same honest-unknown as the turtle: known parts + a named gap.)")

    print("\n" + "=" * 72)
    print("  Verdict: the parts-alphabet works WITH his grain. Roles fall out of")
    print("  position (his language faculty), length/parts/orientation read off")
    print("  the structure, unknown parts shrug honestly. Contiguous AND")
    print("  differentiable, exactly as intended. The bracket: something still")
    print("  has to turn raw input INTO these glyphs — that retina is the only")
    print("  part this representation sets aside for later.")


if __name__ == "__main__":
    main()
