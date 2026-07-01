"""
Test: PARTIAL DOOR OVERLAP recognition (recursive) in his actual net.
Concepts are wired as nodes with 'part' doors to their constituents; recognition
is by fraction-of-doors-present, carried up the tower. No numpy harness deciding —
the scoring is isaac.recognize_doors over his Net's doors.

Run:  python test_partial_doors.py
"""
import sys
from isaac import Isaac


def build(isaac):
    net = isaac.net
    L2 = {"rainbow": ["arch", "ramp"], "flag": ["stripe", "fall"],
          "target": ["arch", "zigzag"], "wave": ["zigzag", "stripe"]}
    L3 = {"poster": ["rainbow", "flag"], "banner": ["wave", "target"]}
    for concept, parts in {**L2, **L3}.items():
        for p in parts:
            net.add_door(concept, p, tag="part")


def show(title, fired):
    print(f"  {title}")
    for c, s in sorted(fired.items(), key=lambda kv: -kv[1]):
        print(f"     {c:<10} {s:.3f}")


def main():
    isaac = Isaac()
    build(isaac)
    print("=" * 56)
    print("  PARTIAL DOOR OVERLAP — recursive recognition in his net")
    print("=" * 56)

    # 1) FULL: all four L1 parts present -> everything fires at 1.0
    show("full input {arch, ramp, stripe, fall}:",
         isaac.recognize_doors({"arch", "ramp", "stripe", "fall"}))

    # 2) PARTIAL + RECURSIVE: destroy 'arch' -> rainbow half-supported, poster
    #    still wins from the rest, confidence carried up (0.5 + 1.0)/2 = 0.75
    print()
    show("arch MISSING {ramp, stripe, fall} (the cascade):",
         isaac.recognize_doors({"ramp", "stripe", "fall"}))

    # 3) YOUR CASE: a concept with 12 doors, 10 present -> 10/12 = 0.833
    isaac2 = Isaac()
    for i in range(12):
        isaac2.net.add_door("bigthing", f"d{i}", tag="part")
    fired = isaac2.recognize_doors({f"d{i}" for i in range(10)}, threshold=0.5)
    print(f"\n  12 doors, 10 present -> bigthing = {fired.get('bigthing'):.3f}  (= 10/12)")

    # quick checks
    f_full = isaac.recognize_doors({"arch", "ramp", "stripe", "fall"})
    f_part = isaac.recognize_doors({"ramp", "stripe", "fall"})
    ok = (abs(f_full.get("poster", 0) - 1.0) < 1e-9
          and abs(f_part.get("rainbow", 0) - 0.5) < 1e-9
          and abs(f_part.get("poster", 0) - 0.75) < 1e-9
          and abs(fired.get("bigthing", 0) - 10/12) < 1e-9)
    print("\n  checks:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
