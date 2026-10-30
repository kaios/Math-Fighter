import unittest

from mathfighter import progress
from mathfighter.mathq import ADD, DIV, MUL, OPS, SUB

DAY = "2026-10-30"


class ProgressTests(unittest.TestCase):
    def test_answers_are_counted_per_operation_and_day(self):
        d = {}
        progress.answered(d, ADD, True, 2.0, DAY, 1)
        progress.answered(d, ADD, True, 4.0, DAY, 2)
        progress.answered(d, ADD, False, 5.0, DAY, 0)
        progress.answered(d, MUL, True, 1.0, DAY, 1)
        rows = {r[0]: r for r in progress.op_stats(d)}
        self.assertEqual(rows[ADD], (ADD, 3, 2, 3.0))
        self.assertEqual(rows[MUL], (MUL, 1, 1, 1.0))
        self.assertEqual(rows[SUB], (SUB, 0, 0, None))
        self.assertEqual(progress.totals(d), (4, 3))
        self.assertEqual(progress.recent_days(d, DAY)[-1], (DAY, 4, 3))
        self.assertEqual(progress.bests(d)["fastest"], 1.0)

    def test_streak_best_and_milestones(self):
        d = {}
        events = [progress.answered(d, ADD, True, 1.0, DAY, i + 1) for i in range(10)]
        self.assertEqual(events[4]["milestone"], 5)
        self.assertFalse(events[4]["best_streak"])     # not news until there is a real record to beat
        self.assertTrue(events[5]["best_streak"])
        self.assertEqual(progress.bests(d)["streak"], 10)
        self.assertFalse(progress.answered(d, ADD, True, 1.0, DAY, 3)["best_streak"])

    def test_weakest_operation_needs_enough_answers(self):
        d = {}
        self.assertIsNone(progress.weakest_op(d))
        for i in range(10):
            progress.answered(d, ADD, True, 1.0, DAY, 1)
            progress.answered(d, DIV, i < 3, 1.0, DAY, 1)
        self.assertEqual(progress.weakest_op(d), DIV)

    def test_best_score_is_per_level(self):
        d = {}
        self.assertTrue(progress.record_run(d, 2, 500))
        self.assertFalse(progress.record_run(d, 2, 400))
        self.assertTrue(progress.record_run(d, 3, 100))
        self.assertEqual(progress.bests(d)["scores"], {"2": 500, "3": 100})

    def test_daily_streak(self):
        d = {}
        self.assertEqual(progress.daily_finish(d, "2026-10-28", 100)["streak"], 1)
        self.assertEqual(progress.daily_finish(d, "2026-10-29", 90)["streak"], 2)
        again = progress.daily_finish(d, "2026-10-29", 300)         # a replay doesn't add a day
        self.assertEqual(again["streak"], 2)
        self.assertTrue(again["new_best"])
        self.assertEqual(progress.daily_status(d, "2026-10-29")["today"], 300)
        self.assertEqual(progress.daily_status(d, "2026-10-30")["streak"], 2)   # still alive today
        self.assertEqual(progress.daily_status(d, "2026-10-31")["streak"], 0)   # missed a day
        self.assertEqual(progress.daily_finish(d, "2026-11-02", 10)["streak"], 1)
        self.assertEqual(progress.bests(d)["day_streak"], 2)

    def test_daily_theme_rotates_and_respects_settings(self):
        days = [f"2026-10-{n:02d}" for n in range(1, 11)]
        themes = {progress.daily_theme(x, OPS) for x in days}
        self.assertEqual(themes, set(OPS) | {"mix"})
        for x in days:
            self.assertIn(progress.daily_theme(x, (ADD,)), (ADD, "mix"))

    def test_broken_save_data_does_not_crash(self):
        d = {"progress": "junk"}
        progress.answered(d, ADD, True, 1.0, DAY, 1)
        self.assertEqual(progress.totals(d), (1, 1))
        d = {"progress": {"ops": 3, "days": None}}
        self.assertEqual(progress.totals(d), (0, 0))


if __name__ == "__main__":
    unittest.main()
