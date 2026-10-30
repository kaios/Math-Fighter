"""Math question generation for each operation and difficulty level: 1-5,
plus the bonus level 6 (fractions)."""

import random
from dataclasses import dataclass
from fractions import Fraction

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


FRACTION_LEVEL = 6
DENOMS = [2, 3, 4, 5, 6, 8, 10, 12]


@dataclass(frozen=True)
class Question:
    a: object          # int, or Fraction on the bonus level
    b: object
    op: str
    answer: object

    @property
    def text(self):
        return f"{self.a} {DISPLAY[self.op]} {self.b} = ?"

    @property
    def digits(self):
        """What the player types: the digits of the answer. A fraction is
        typed numerator then denominator (3/4 is 3, 4); the slash is shown."""
        return str(self.answer).replace("/", "")

    @property
    def is_fraction(self):
        return isinstance(self.answer, Fraction)


def make_fraction_question(op, rng=random):
    """Bonus level. Answers are proper fractions (between 0 and 1) in
    simplest form, with small denominators."""
    while True:
        d1 = rng.choice(DENOMS)
        if op in (ADD, SUB):
            related = [d for d in DENOMS if d != d1 and (d % d1 == 0 or d1 % d == 0)]
            d2 = d1 if rng.random() < 0.5 or not related else rng.choice(related)
        else:
            d1, d2 = rng.choice(DENOMS[:6]), rng.choice(DENOMS[:6])
        a = Fraction(rng.randint(1, d1 - 1), d1)
        b = Fraction(rng.randint(1, d2 - 1), d2)
        r = {ADD: a + b, SUB: a - b, MUL: a * b, DIV: a / b if b else 0}[op]
        if 0 < r < 1 and r.denominator <= 24:
            return Question(a, b, op, r)


def make_question(op, level, rng=random):
    if int(level) >= FRACTION_LEVEL:
        return make_fraction_question(op, rng)
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
    """Avoids asking the same question twice in a row. With op=MIX, or an
    operation that is switched off, each question uses a random allowed one."""

    def __init__(self, op, level, rng=None, allowed=OPS):
        self.op, self.level = op, level
        self.rng = rng or random.Random()
        self.allowed = tuple(allowed) or OPS     # parents can switch operations off
        self.recent = []

    def next(self):
        for _ in range(20):
            op = self.op if self.op in self.allowed else self.rng.choice(self.allowed)
            q = make_question(op, self.level, self.rng)
            if q not in self.recent:
                break
        self.recent = (self.recent + [q])[-6:]
        return q
