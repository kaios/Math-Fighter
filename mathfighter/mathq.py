"""Math question generation for each operation and difficulty level (1-5)."""

import random
from dataclasses import dataclass

ADD, SUB, MUL, DIV = "+", "-", "x", "/"
OPS = (ADD, SUB, MUL, DIV)
MIX = "mix"   # the final boss asks a random one of the four each time

# Symbols as shown on screen.
DISPLAY = {ADD: "+", SUB: "\u2212", MUL: "×", DIV: "÷", MIX: "?"}
OP_NAMES = {ADD: "Addition", SUB: "Subtraction", MUL: "Multiplication", DIV: "Division",
            MIX: "Mixed"}

# (range for a, range for b) per level. For SUB the pair is (result, b) and
# for DIV it is (divisor, quotient) so answers are always whole and >= 0.
RANGES = {
    ADD: {1: ((1, 5), (1, 5)), 2: ((1, 10), (1, 10)), 3: ((10, 40), (2, 9)),
          4: ((10, 60), (10, 39)), 5: ((100, 499), (10, 99))},
    SUB: {1: ((0, 5), (1, 5)), 2: ((0, 10), (1, 10)), 3: ((10, 40), (2, 9)),
          4: ((10, 60), (10, 39)), 5: ((100, 399), (10, 99))},
    MUL: {1: ((1, 3), (1, 5)), 2: ((2, 5), (1, 10)), 3: ((2, 10), (2, 10)),
          4: ((3, 12), (3, 12)), 5: ((11, 20), (3, 9))},
    DIV: {1: ((1, 3), (1, 5)), 2: ((2, 5), (1, 10)), 3: ((2, 10), (2, 10)),
          4: ((3, 12), (3, 12)), 5: ((3, 9), (11, 20))},
}


@dataclass(frozen=True)
class Question:
    a: int
    b: int
    op: str
    answer: int

    @property
    def text(self):
        return f"{self.a} {DISPLAY[self.op]} {self.b} = ?"


def make_question(op, level, rng=random):
    level = max(1, min(5, int(level)))
    (lo1, hi1), (lo2, hi2) = RANGES[op][level]
    x, y = rng.randint(lo1, hi1), rng.randint(lo2, hi2)
    if op == ADD:
        return Question(x, y, op, x + y)
    if op == SUB:
        return Question(x + y, y, op, x)
    if op == MUL:
        if rng.random() < 0.5:
            x, y = y, x
        return Question(x, y, op, x * y)
    return Question(x * y, x, op, y)


class QuestionMaker:
    """Avoids asking the same question twice in a row. With op=MIX each
    question uses a random one of the four operations."""

    def __init__(self, op, level, rng=None):
        self.op, self.level = op, level
        self.rng = rng or random.Random()
        self.recent = []

    def next(self):
        for _ in range(20):
            op = self.rng.choice(OPS) if self.op == MIX else self.op
            q = make_question(op, self.level, self.rng)
            if q not in self.recent:
                break
        self.recent = (self.recent + [q])[-6:]
        return q
