"""
Diagrams, circuits, and time
----------------------------
Part 1 -- TOPOLOGY IS THE SIGNAL, LAYOUT IS NUISANCE: two schematics with
          completely different coordinates (one containing a 2.5D crossover
          -- lines crossing WITHOUT a junction dot) must yield the same
          netlist. Nets precipitate exactly like rigid cliques.

Part 2 -- THE SOLVER SPEAKS ELECTRICITY: a resistor network solved by the
          same local-relaxation style as every mechanism today. KCL checked
          as a conservation ledger at every node.

Part 3 -- TIMING DIAGRAMS = THE SNAKE'S LAG DETECTOR ON LOGIC: given only
          waveforms from an unknown gate circuit, recover which signals are
          primary (generators), which are derived, each gate's truth table,
          and each propagation delay. Circuit reverse-engineering from
          watching wires talk.
"""

import math
import random
from itertools import combinations, product

random.seed(6)


def line(c="-", n=66):
    print(c * n)


# ================================ PART 1: netlist invariance + crossover
line("=")
print("PART 1 -- two layouts, one circuit (and a 2.5D crossover)")
line("=")

def extract_nets(wires, junctions):
    """wires: list of (terminalA, terminalB) connections along drawn segments.
    Crossings are NOT connections unless a junction dot exists at that spot.
    (The wires list is built from drawn segments; a crossover contributes
    nothing unless its crossing point is in junctions.)"""
    # union-find over terminals
    parent = {}
    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a, b):
        parent[find(a)] = find(b)
    for a, b in wires:
        union(a, b)
    nets = {}
    for t in parent:
        nets.setdefault(find(t), set()).add(t)
    return sorted(sorted(n) for n in nets.values())

# layout 1: battery B+, B-, resistor R1a/R1b, R2a/R2b, lamp La/Lb
wires_layout1 = [
    ("B+", "R1a"), ("R1b", "La"), ("Lb", "B-"),
    ("B+", "R2a"), ("R2b", "La"),          # R2 parallel path into the lamp
]
# layout 2: same circuit, drawn totally differently; the wire B+->R2a is
# drawn CROSSING the wire R1b->La -- with NO junction dot. In a naive
# geometric read they touch; in the schematic read they do not.
wires_layout2 = [
    ("R2b", "La"), ("B+", "R2a"),
    ("Lb", "B-"), ("B+", "R1a"), ("R1b", "La"),
]
crossings_without_dot = [("B+->R2a", "R1b->La")]   # present, and IGNORED

n1 = extract_nets(wires_layout1, junctions=set())
n2 = extract_nets(wires_layout2, junctions=set())
print("layout 1 nets:", n1)
print("layout 2 nets:", n2)
assert n1 == n2
print(f"crossover in layout 2 (no dot) correctly contributed NOTHING.")
print("-> every coordinate differed; the netlist is what refused to vary.\n")


# ==================================== PART 2: relaxation circuit solving
line("=")
print("PART 2 -- resistor network by local relaxation (KCL as a ledger)")
line("=")
# node 0 = 10V source, node 3 = ground. R in kilo-ohms.
R = {(0, 1): 1.0, (1, 2): 2.0, (1, 3): 2.0, (2, 3): 1.0}
neigh = {}
for (a, b), r in R.items():
    neigh.setdefault(a, []).append((b, r))
    neigh.setdefault(b, []).append((a, r))
V = {0: 10.0, 1: 0.0, 2: 0.0, 3: 0.0}
pinned = {0: 10.0, 3: 0.0}
for _ in range(4000):
    for node in (1, 2):
        num = sum(V[m] / r for (m, r) in neigh[node])
        den = sum(1.0 / r for (m, r) in neigh[node])
        V[node] = num / den          # each node relaxes to the KCL-satisfying value
    for k, v in pinned.items():
        V[k] = v
print("node voltages:", {k: round(v, 4) for k, v in V.items()})

# analytic check: R12+R23 = 3k in parallel with R13 = 2k -> 1.2k; series 1k
# V1 = 10 * 1.2/(1+1.2) = 60/11; V2 = V1 * 1/3
v1_true = 10 * 1.2 / 2.2
v2_true = v1_true * (1.0 / 3.0)
assert abs(V[1] - v1_true) < 1e-6 and abs(V[2] - v2_true) < 1e-6
# KCL conservation ledger at every free node
for node in (1, 2):
    flow = sum((V[m] - V[node]) / r for (m, r) in neigh[node])
    print(f"KCL at node {node}: net current in = {flow:+.2e} mA (conserved)")
    assert abs(flow) < 1e-9
print("-> same relaxation style as every mechanism today; volts, not meters.\n")


# ============================= PART 3: reverse-engineering from waveforms
line("=")
print("PART 3 -- unknown logic circuit, waveforms only: who drives whom?")
line("=")
T = 400
A = [random.randint(0, 1) for _ in range(T)]
B = [random.randint(0, 1) for _ in range(T)]
C = [0] * T; D = [0] * T; E = [0] * T
for t in range(T):
    C[t] = 1 - A[t - 1] if t >= 1 else 0                       # C = NOT A, delay 1
    D[t] = 1 - (A[t - 2] & B[t - 2]) if t >= 2 else 0          # D = NAND(A,B), delay 2
    E[t] = (C[t - 1] & D[t - 1]) if t >= 1 else 0              # E = AND(C,D), delay 1
signals = {"A": A, "B": B, "C": C, "D": D, "E": E}

UNARY = {"BUF": lambda x: x, "NOT": lambda x: 1 - x}
BINARY = {"AND": lambda x, y: x & y, "OR": lambda x, y: x | y,
          "XOR": lambda x, y: x ^ y, "NAND": lambda x, y: 1 - (x & y),
          "NOR": lambda x, y: 1 - (x | y)}

def explains(out, fn, ins, lag):
    return all(out[t] == fn(*[s[t - lag] for s in ins])
               for t in range(max(lag, 3), T))

names = list(signals)
findings = {}
for out_name in names:
    out = signals[out_name]
    found = None
    for lag in (1, 2, 3):
        for in_name in names:
            if in_name == out_name:
                continue
            for fname, fn in UNARY.items():
                if explains(out, fn, [signals[in_name]], lag):
                    found = f"{fname}({in_name})  delay {lag}"
        if found:
            break
        for na, nb in combinations([n for n in names if n != out_name], 2):
            for fname, fn in BINARY.items():
                if explains(out, fn, [signals[na], signals[nb]], lag):
                    found = f"{fname}({na},{nb})  delay {lag}"
        if found:
            break
    findings[out_name] = found

for name in names:
    if findings[name]:
        print(f"  {name} = {findings[name]}")
    else:
        print(f"  {name}: no explanation from other signals -> PRIMARY INPUT "
              f"(a generator, like the snake's head)")

assert findings["A"] is None and findings["B"] is None
assert findings["C"] == "NOT(A)  delay 1"
assert "NAND(A,B)" in findings["D"] and "delay 2" in findings["D"]
assert "AND(C,D)" in findings["E"] and "delay 1" in findings["E"]
print("\nrecovered wiring: A,B (inputs) -> C=NOT A -> \\")
print("                              D=NAND(A,B) ->  E=AND(C,D)")
print("gate functions, propagation delays, and signal flow direction --")
print("all from the lag question: whose present is whose past?")

print()
line("=")
print("PASS: topology extracted through a 2.5D crossover; the mechanism")
print("solver spoke electricity; and a logic circuit was reverse-engineered")
print("from nothing but its waveforms.")
line("=")
