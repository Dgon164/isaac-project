"""
REBUILD B — Composition: uptake edges vs membership-only.

OLD (current isaac.py behavior): a whole is a SET of member parts.
  _crystallize() stores {"members": ...} — no record of who consumes what from
  whom. Leading suspect for the system-wide symptom: "structures assemble fine
  but never behave differently than their parts, across every experiment."

NEW: a whole = parts + UPTAKE EDGES (provider --affordance--> consumer).
  Emergence = interlocking affordances: one part's output is the enabling
  condition of another's uptake. Configuration IS the edge set.
  An affordance is OPERABLE at the whole level iff its provider's requirements
  are recursively satisfied through the edges.

Tests (audit standard 2.3):
  (a) emergent function operable at whole level
  (b) inoperable in every individual part
  (c) inoperable in the dismantled aggregate (same parts, no arrangement)
      — and membership-only CANNOT even represent the difference
  (d) same parts, different arrangement -> different whole, different behavior
      — membership-only gives them the same identity, by construction
  (e) formation deterministic: assembly order does not change the whole
  (f) decomposition recovers the parts
  (g) wholes are first-class: engine + wheels compose upward into car,
      which affords locomotion (new capability at the new level)
"""
from itertools import permutations


class Part:
    """A part declares affordances: offers = {affordance: set(required inputs)}."""
    def __init__(self, name, offers):
        self.name, self.offers = name, offers

    def operable(self):
        """What this part can do ALONE: offers with no requirements."""
        return {f for f, req in self.offers.items() if not req}


# ------------------------------------------------- OLD: membership-only whole
class MembershipWhole:
    def __init__(self, parts):
        self.parts = set(parts)

    def identity(self):
        return frozenset(p.name for p in self.parts)

    def operable(self):
        """No arrangement stored -> the only possible semantics is an
        unstructured union of what the parts can each do alone."""
        out = set()
        for p in self.parts:
            out |= p.operable()
        return out


# ------------------------------------------------ NEW: uptake-edge whole
class UptakeWhole:
    """Whole = parts + uptake edges (provider, affordance, consumer)."""
    def __init__(self, parts, edges):
        self.parts = {p.name: p for p in parts}
        self.edges = set(edges)

    def identity(self):
        return (frozenset(self.parts), frozenset(self.edges))

    def decompose(self):
        return set(self.parts.values())

    def operable(self):
        """Fixed-point propagation: affordance F of part P becomes operable when
        every requirement of P's offer arrives via an uptake edge from a part
        whose provided affordance is itself operable."""
        live = set()   # (part, affordance) pairs currently operable
        changed = True
        while changed:
            changed = False
            for pname, p in self.parts.items():
                for f, req in p.offers.items():
                    if (pname, f) in live:
                        continue
                    ok = all(
                        any((src, need, pname) in self.edges and (src, need) in live
                            for src in self.parts)
                        for need in req
                    )
                    if ok:
                        live.add((pname, f))
                        changed = True
        return {f for _, f in live}

    def as_part(self, name):
        """First-class: the whole re-enters composition as a part offering its
        EMERGENT affordances (operable at whole, in no part alone)."""
        alone = set().union(*(p.operable() for p in self.parts.values()))
        emergent = self.operable() - alone
        return Part(name, {f: set() for f in self.operable()} |
                          {f: set() for f in emergent})


# --------------------------------------------------------------------- tests
def main():
    print("=" * 72)
    print("REBUILD B — uptake-edge composition vs membership-only")
    print("=" * 72)

    tank = Part("tank", {"fuel": set()})
    spark = Part("spark", {"ignition": set()})
    piston = Part("piston", {"torque": {"fuel", "ignition"}})
    parts = [tank, spark, piston]

    good_edges = {("tank", "fuel", "piston"), ("spark", "ignition", "piston")}
    bad_edges = {("tank", "fuel", "spark"), ("spark", "ignition", "tank")}  # rewired

    engine = UptakeWhole(parts, good_edges)
    miswired = UptakeWhole(parts, bad_edges)
    pile = UptakeWhole(parts, set())            # dismantled: same parts, no edges

    # (a) emergent function operable at whole
    a = "torque" in engine.operable()
    print(f"\n(a) whole affords torque:                 {a}   "
          f"(engine.operable = {sorted(engine.operable())})")

    # (b) inoperable in every individual part
    b = all("torque" not in p.operable() for p in parts)
    print(f"(b) torque inoperable in every part:      {b}")

    # (c) inoperable in dismantled aggregate — and OLD cannot represent the difference
    c_new = "torque" not in pile.operable()
    old_engine, old_pile = MembershipWhole(parts), MembershipWhole(parts)
    c_old_blind = old_engine.identity() == old_pile.identity()
    print(f"(c) dismantled pile lacks torque [NEW]:   {c_new}")
    print(f"    OLD: engine and dismantled pile are THE SAME OBJECT: {c_old_blind}"
          f"   <- membership-only cannot see arrangement, by construction")

    # (d) same parts, different arrangement
    d_new = (miswired.identity() != engine.identity()
             and "torque" not in miswired.operable())
    d_old = MembershipWhole(parts).identity() == MembershipWhole(parts).identity()
    print(f"(d) rewired whole differs + loses torque [NEW]: {d_new}")
    print(f"    OLD: rewired and correct whole identical:   {d_old}")

    # (e) deterministic formation: assembly order irrelevant
    ids = set()
    for perm in permutations(good_edges):
        for pperm in permutations(parts):
            ids.add(UptakeWhole(list(pperm), set(perm)).identity())
    e = len(ids) == 1
    print(f"(e) same whole from every assembly order: {e}   "
          f"({len(ids)} distinct identity from 12 orders)")

    # (f) decomposition recovers the parts
    f_ok = {p.name for p in engine.decompose()} == {"tank", "spark", "piston"}
    print(f"(f) decomposition recovers parts:         {f_ok}")

    # (g) wholes are first-class: compose upward
    wheels = Part("wheels", {"traction": set()})
    frame = Part("frame", {"locomotion": {"torque", "traction"}})
    car = UptakeWhole([engine.as_part("engine"), wheels, frame],
                      {("engine", "torque", "frame"),
                       ("wheels", "traction", "frame")})
    g = "locomotion" in car.operable()
    print(f"(g) engine composes upward -> car moves:  {g}   "
          f"(car.operable = {sorted(car.operable())})")

    print("-" * 72)
    verdict = all([a, b, c_new, d_new, e, f_ok, g])
    print(f"NEW passes (a)-(g): {verdict}")
    print(f"OLD (membership-only): fails (c) and (d) BY CONSTRUCTION — "
          f"cannot distinguish engine / pile / miswired.")
    print(f"REBUILD B VERDICT: {'WORKS' if verdict else 'BROKEN'}")
    return verdict


if __name__ == "__main__":
    main()
