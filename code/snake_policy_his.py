"""
THE COMBINE, MADE HIS — the last bit of Python set-logic removed.

snake_policy.py left one thing in the harness: the boolean combine
    good = (not blocked) and toward_food
was Python's `and`/`not`. He already HAS logic gates (logic_eval over taught
truth tables), so here the combine runs in HIM:

    per direction d:
       b = check( blocked? )         <- his perception (negative)
       t = check( toward food? )     <- his perception (positive)
       good = logic_eval('( not b ) and t')   <- HIS AND/NOT gates
    survival fallback uses his NOT as well.

Now every step of the move — perceive, negate, combine — is his. The harness
only loops the four directions and reads the board.
"""

from isaac import Isaac, tokenize
from snake_policy import (N, DIRS, sgn, random_scene,
                          neighbor_content, toward_food, teach, render)


def teach_logic(isaac):
    """Seed the truth tables he reasons over (AND, NOT)."""
    for a in ["true", "false"]:
        for b in ["true", "false"]:
            av, bv = a == "true", b == "true"
            isaac.observe(tokenize(f"{a} and {b} = {'true' if av and bv else 'false'}"))
        isaac.observe(tokenize(f"not {a} = {'false' if a == 'true' else 'true'}"))
    isaac.consolidate()


def tf(x):
    return "true" if x else "false"


def his_move(isaac, cells, food, verbose=False):
    (hr, hc), (fr, fc) = cells[0], food
    food_ctx = [f"food_dx_{sgn(fc - hc)}", f"food_dy_{sgn(fr - hr)}"]

    chosen = set()
    for d in DIRS:
        b, _ = isaac.check(["neighbor", neighbor_content(cells, food, d)], "blocked")
        t, _ = isaac.check(food_ctx, f"go_{d}")
        good, _ = isaac.logic_eval(f"( not {tf(b)} ) and {tf(t)}")     # HIS gates
        if verbose:
            print(f"      {d:<5}: blocked={tf(b):<5} toward={tf(t):<5} "
                  f"-> (not blocked) and toward = {good}")
        if good == "true":
            chosen.add(d)
    if chosen:
        return chosen, "toward food"

    safe = set()                                   # survival: his NOT only
    for d in DIRS:
        b, _ = isaac.check(["neighbor", neighbor_content(cells, food, d)], "blocked")
        s, _ = isaac.logic_eval(f"not {tf(b)}")
        if s == "true":
            safe.add(d)
    return safe, "survival (no open move toward food)"


def main():
    isaac = Isaac()
    teach(isaac)          # food module (positive) + block module (negative)
    teach_logic(isaac)    # AND / NOT truth tables

    print("=" * 72)
    print("  THE COMBINE, MADE HIS  (perceive + negate + AND/NOT, all in him)")
    print("=" * 72)

    # same scoring as before — does making the combine his keep it correct?
    n = 400
    suicidal = optimal = had_choice = 0
    for _ in range(n):
        cells, food = random_scene()
        chosen, _ = his_move(isaac, cells, food)
        open_dirs = {d for d in DIRS if neighbor_content(cells, food, d) in ("empty", "food")}
        good = {d for d in DIRS if d in open_dirs and toward_food(cells, food, d)}
        if chosen & (set(DIRS) - open_dirs):
            suicidal += 1
        if good:
            had_choice += 1
            if chosen == good:
                optimal += 1
    print(f"\n  on {n} novel scenes (combine now via his logic gates):")
    print(f"    never moved into a body/wall : {(n-suicidal)/n:5.0%}")
    print(f"    exactly the safe food-ward moves : {optimal/max(had_choice,1):5.0%}")

    # show his gates firing on the body-blocks-food case
    print("\n  HIS LOGIC, STEP BY STEP  (food up-right, body directly UP):")
    cells = [(6, 6), (5, 6), (4, 6)]
    food = (3, 9)
    print(render(cells, food))
    chosen, why = his_move(isaac, cells, food, verbose=True)
    print(f"    -> his move: {sorted(chosen)}  ({why})")
    print("       'up' lost the AND (blocked=true -> not true=false -> false);")
    print("       'right' won it (blocked=false, toward=true -> true). His gates.")

    print("\n" + "=" * 72)
    print("  Nothing of mine is left in the decision: he perceives blocked/toward")
    print("  with check(), negates and ANDs them with his own logic, and the move")
    print("  falls out. End to end his.")


if __name__ == "__main__":
    main()
