import random
import unittest

from mathfighter.mathq import ADD, DIV, MIX, MUL, SUB, QuestionMaker, make_question


class MathQuestionTests(unittest.TestCase):
    def test_answers_are_correct_whole_and_non_negative(self):
        rng = random.Random(1)
        for op in (ADD, SUB, MUL, DIV):
            for level in range(1, 6):
                for _ in range(500):
                    q = make_question(op, level, rng)
                    self.assertGreaterEqual(q.answer, 0)
                    if op == ADD:
                        self.assertEqual(q.a + q.b, q.answer)
                    elif op == SUB:
                        self.assertEqual(q.a - q.b, q.answer)
                    elif op == MUL:
                        self.assertEqual(q.a * q.b, q.answer)
                    else:
                        self.assertNotEqual(q.b, 0)
                        self.assertEqual(q.b * q.answer, q.a)

    def test_harder_levels_have_bigger_numbers(self):
        rng = random.Random(2)
        for op in (ADD, SUB, MUL, DIV):
            avg = [sum(make_question(op, lv, rng).answer for _ in range(300)) / 300
                   for lv in (1, 5)]
            self.assertLess(avg[0], avg[1])

    def test_no_immediate_repeats(self):
        qm = QuestionMaker(ADD, 1, random.Random(3))
        prev = None
        for _ in range(200):
            q = qm.next()
            self.assertNotEqual(q, prev)
            prev = q

    def test_mixed_uses_all_four_operations(self):
        qm = QuestionMaker(MIX, 3, random.Random(4))
        self.assertEqual({qm.next().op for _ in range(200)}, {ADD, SUB, MUL, DIV})


if __name__ == "__main__":
    unittest.main()
