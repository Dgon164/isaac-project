"""
Snake. 1s and 0s. Four buttons.
"""

import numpy as np
import time
from isaac import Isaac

GW, GH = 15, 15
BUTTONS = ["up", "down", "left", "right"]
DIRS = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
OPP = {"up": "down", "down": "up", "left": "right", "right": "left"}


class Snake:
    def __init__(self):
        self.reset()

    def reset(self):
        cx, cy = GW // 2, GH // 2
        self.body = [(cx, cy), (cx - 1, cy), (cx - 2, cy)]
        self.dir = "right"
        self.food = None
        self._place_food()
        self.alive = True
        self.score = 0
        self.steps = 0

    def _place_food(self):
        empty = [(x, y) for x in range(GW) for y in range(GH)
                 if (x, y) not in self.body]
        if empty:
            self.food = empty[np.random.randint(len(empty))]

    def press(self, button):
        if not self.alive:
            return self.screen(), False
        if button in DIRS and button != OPP.get(self.dir):
            self.dir = button
        dx, dy = DIRS[self.dir]
        nh = (self.body[0][0] + dx, self.body[0][1] + dy)
        if (nh[0] < 0 or nh[0] >= GW or nh[1] < 0 or nh[1] >= GH
                or nh in self.body):
            self.alive = False
            return self.screen(), False
        self.body.insert(0, nh)
        self.steps += 1
        if nh == self.food:
            self.score += 1
            self._place_food()
        else:
            self.body.pop()
        return self.screen(), True

    def screen(self):
        """1s and 0s. That's it."""
        g = np.zeros((GH, GW), dtype=np.uint8)
        for bx, by in self.body:
            g[by, bx] = 1
        if self.food:
            g[self.food[1], self.food[0]] = 1
        return g


def demo(game, isaac):
    """Get 3 apples then die. Isaac watches the screen and the buttons."""
    game.reset()
    apples = 0
    print("  DEMO:", end="", flush=True)

    while game.alive:
        isaac.observe_matrix(game.screen())

        if apples < 3:
            head = game.body[0]
            food = game.food
            dx, dy = food[0] - head[0], food[1] - head[1]
            prefs = []
            if dx > 0: prefs.append("right")
            elif dx < 0: prefs.append("left")
            if dy > 0: prefs.append("down")
            elif dy < 0: prefs.append("up")
            for d in BUTTONS:
                if d not in prefs: prefs.append(d)
            button = game.dir
            for d in prefs:
                if d == OPP.get(game.dir): continue
                ddx, ddy = DIRS[d]
                nx, ny = head[0] + ddx, head[1] + ddy
                if 0 <= nx < GW and 0 <= ny < GH and (nx, ny) not in game.body:
                    button = d
                    break
        else:
            button = "left"

        isaac.observe([f"b_{button}"])
        screen, alive = game.press(button)
        isaac.observe_matrix(screen)

        if game.score > apples:
            apples = game.score
            print(f" apple {apples}", end="", flush=True)

    print(f" died. ({game.steps} steps)")


def pick(isaac):
    """Isaac picks a button. No help."""
    best = None
    best_score = -1
    for b in BUTTONS:
        _, conf = isaac.lookup([f"b_{b}"])
        if conf > best_score:
            best_score = conf
            best = b
    if best_score <= 0:
        return BUTTONS[np.random.randint(4)]
    return best


def arcade(n_games=200):
    print(f"Snake — {GW}x{GH} grid, 1s and 0s, four buttons")
    print("=" * 50)

    isaac = Isaac()
    game = Snake()

    demo(game, isaac)
    isaac.consolidate()
    st = isaac.status()
    print(f"  {st['observations']:,} obs, {st['nodes']} nodes, "
          f"{st['doors']} doors, {len(isaac.types)} types\n")

    print("PLAYING")
    print("-" * 50)
    scores = []
    best = 0

    for g in range(n_games):
        game.reset()
        while game.alive:
            isaac.observe_matrix(game.screen())
            button = pick(isaac)
            isaac.observe([f"b_{button}"])
            screen, alive = game.press(button)
            isaac.observe_matrix(screen)

        scores.append(game.score)
        if game.score > best:
            best = game.score

        if (g + 1) % 10 == 0:
            isaac.consolidate()

        if g < 10 or (g + 1) % 10 == 0:
            recent = scores[-10:]
            print(f"  {g + 1:>4d}: score={game.score:>3d}  "
                  f"steps={game.steps:>4d}  avg10={np.mean(recent):.1f}  "
                  f"best={best}")

    print(f"\n  first 10: {np.mean(scores[:10]):.1f}")
    print(f"  last 10:  {np.mean(scores[-10:]):.1f}")
    print(f"  best:     {best}")
    st = isaac.status()
    print(f"  obs: {st['observations']:,}  nodes: {st['nodes']}  "
          f"doors: {st['doors']}  types: {len(isaac.types)}")


if __name__ == "__main__":
    arcade()
