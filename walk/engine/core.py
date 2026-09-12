#!/usr/bin/env python3
"""
core.py -- the custom semantic engine, step one.

Three things exist: the store, the tables, and the current question.
Each step pulls one item and everything it points at. Nothing deeper.
The loop asks, returns, rejects, and ranks what persists.
Every step prints. Every answer carries its trace.
"""

from collections import OrderedDict

# ============================================================ the record
class Item:
    __slots__ = ("name", "kind", "content", "truth", "native", "tag", "refs")

    def __init__(self, name, kind, content=None, truth=1, native=False,
                 tag="", refs=()):
        self.name = name        # a variable; only recognisability matters
        self.kind = kind        # read by the cycle to choose the question
        self.content = content  # a value, a table row, a relation list
        self.truth = truth      # +1 / -1 / 0 / None
        self.native = native    # never leaves Isaac
        self.tag = tag          # where it came from
        self.refs = tuple(refs) # what it points at -- the one layer

    def __repr__(self):
        t = {1: "+1", -1: "-1", 0: " 0", None: "null"}[self.truth]
        return "%s[%s %s]" % (self.name, self.kind, t)


# ============================================================ the store
class Store:
    def __init__(self):
        self.items = OrderedDict()
        self.relevance = {}      # (context, name) -> signed int

    def put(self, item):
        self.items[item.name] = item
        return item

    def get(self, name):
        return self.items.get(name)

    def rel(self, context, name):
        return self.relevance.get((context, name), 0)

    def set_rel(self, context, name, value):
        self.relevance[(context, name)] = value

    def fetch(self, name):
        """one layer: the item and everything it points at. no deeper."""
        item = self.get(name)
        if item is None:
            return None, []
        layer = [self.get(r) for r in item.refs if self.get(r)]
        return item, layer


# ============================================================ the desk
class Desk:
    """what is pulled and in play, what is pulled and set aside."""
    def __init__(self):
        self.in_play = OrderedDict()
        self.set_aside = OrderedDict()
        self.trace = []

    def take(self, item, context, store):
        r = store.rel(context, item.name)
        if item.native:
            self.set_aside[item.name] = (item, "native")
        elif r < 0:
            self.set_aside[item.name] = (item, "refused %d" % r)
        elif r == 0 and item.truth == 0:
            self.set_aside[item.name] = (item, "present, not for this")
        else:
            self.in_play[item.name] = item
        return item.name in self.in_play


# ============================================================ the cycle
class Cycle:
    def __init__(self, store, context, goal, gates, rank_by, verbose=True):
        self.store, self.context, self.goal = store, context, goal
        self.gates = gates          # list of (name, fn(item)->(ok, why))
        self.rank_by = rank_by      # fn(item) -> sortable
        self.desk = Desk()
        self.open = [goal]
        self.resolved = set()
        self.candidates = OrderedDict()
        self.rejected = OrderedDict()
        self.verbose = verbose
        self.step_no = 0

    def say(self, *a):
        if self.verbose:
            print(*a)

    def step(self):
        """one ask/return. returns False when nothing is open."""
        while self.open:
            name = self.open.pop(0)
            if name in self.resolved:
                continue
            break
        else:
            return False
        self.resolved.add(name)
        self.step_no += 1

        item, layer = self.store.fetch(name)
        if item is None:
            self.say("  %2d  %-22s (not in store -> open axis)" % (self.step_no, name))
            self.desk.trace.append((name, "open_axis", []))
            return True

        used = self.desk.take(item, self.context, self.store)
        pulled = []
        for ref in layer:
            self.desk.take(ref, self.context, self.store)
            pulled.append(ref.name)
            if ref.name not in self.resolved and ref.name not in self.open:
                self.open.append(ref.name)

        self.desk.trace.append((name, item.kind, pulled))
        self.say("  %2d  %-22s %-18s pulled %d  %s"
                 % (self.step_no, name, item.kind, len(pulled),
                    "" if used else "[set aside]"))

        if item.kind == "material" and used:
            self.candidates[name] = item
        return True

    def reject_pass(self):
        """run every gate over every candidate. dead ones ask nothing more."""
        for gname, gate in self.gates:
            dead = []
            for cname, cand in list(self.candidates.items()):
                ok, why = gate(cand, self.desk)
                if not ok:
                    dead.append((cname, why))
            for cname, why in dead:
                self.rejected[cname] = (gname, why)
                del self.candidates[cname]
                self.open = [o for o in self.open if o != cname]
            self.say("  gate %-14s rejected %2d, %2d persist"
                     % (gname, len(dead), len(self.candidates)))

    def run(self, max_steps=200):
        self.say("goal: %s   context: %s" % (self.goal, self.context))
        self.say("---- pull")
        while self.step() and self.step_no < max_steps:
            pass
        self.say("---- reject")
        self.reject_pass()
        self.say("---- persist and rank")
        ranked = sorted(self.candidates.values(), key=self.rank_by)
        for c in ranked:
            self.say("  %-18s %s" % (c.name, self.rank_by(c)))
        return ranked

    def why(self, name):
        """the trace for one candidate: how it was reached, what killed it."""
        path = [t for t in self.desk.trace if name in t[2] or t[0] == name]
        verdict = self.rejected.get(name, ("persisted", ""))
        return path, verdict
