import unittest

from mathfighter import highscores


class HighScoreTests(unittest.TestCase):
    def test_keeps_best_10_in_order(self):
        data = {}
        for s in (50, 300, 120, 900, 10, 75, 640, 220, 410, 5, 999, 1):
            if highscores.qualifies(data, s):
                highscores.add(data, f"P{s}", s, 1, "Kai Blaze")
        scores = [r["score"] for r in highscores.table(data)]
        self.assertEqual(scores, [999, 900, 640, 410, 300, 220, 120, 75, 50, 10])
        self.assertFalse(highscores.qualifies(data, 10))     # must beat 10th place
        self.assertTrue(highscores.qualifies(data, 11))

    def test_place_and_name_rules(self):
        data = {}
        self.assertEqual(highscores.add(data, "AMY", 500, 3, "Mira Nova"), 0)
        self.assertEqual(highscores.add(data, "BOB", 500, 3, "Dax Steel"), 1)   # tie: older stays ahead
        self.assertEqual(highscores.add(data, "  CHRISTOPHER  ", 900, 5, "Luna Shade"), 0)
        self.assertEqual(highscores.add(data, "   ", 100, 1, "Kai Blaze"), 3)
        names = [r["name"] for r in highscores.table(data)]
        self.assertEqual(names, ["CHRISTOPHE", "AMY", "BOB", "PLAYER"])

    def test_zero_never_qualifies_and_bad_data_is_ignored(self):
        self.assertFalse(highscores.qualifies({}, 0))
        data = {"scores": [{"name": "X"}, "junk", {"name": "OK", "score": 40}]}
        self.assertEqual([r["name"] for r in highscores.table(data)], ["OK"])


if __name__ == "__main__":
    unittest.main()
