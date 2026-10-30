"""Headless playthroughs of the whole game flow with a bot answering questions."""

import os
import tempfile
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["MATHFIGHTER_DATA"] = tempfile.mkdtemp(prefix="mathfighter-test-")  # don't touch the real save

import pygame  # noqa: E402

from mathfighter import drill, menus, progress, save, scenes  # noqa: E402
from mathfighter.draw import QUALITY  # noqa: E402
from mathfighter.battle import Battle  # noqa: E402
from mathfighter.characters import ROSTER  # noqa: E402
from mathfighter.config import MAX_HITS  # noqa: E402
from mathfighter.game import Game  # noqa: E402

DT = 1 / 30
QUALITY["ss"] = 1     # the quick drawing path; test_every_scene_draws_at_high_quality checks the other


def press(game, key, uni=""):
    game.scene.handle(pygame.event.Event(pygame.KEYDOWN, key=key, unicode=uni, mod=0))


class FlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.game = Game()  # one window for all tests

    def setUp(self):
        self.g = self.game
        self.g.level = 1
        self.g.save.clear()
        self.g.streak = 0
        self.g.player = ROSTER[0]
        self.g.seen_howto = False
        self.g.to_title()

    def tick(self, n=1):
        for _ in range(n):
            self.g.scene.update(DT)
            self.g.scene.draw(self.g.screen)

    def to_battle(self, level=1, pick=0):
        g = self.g
        press(g, pygame.K_RETURN)               # title -> main menu
        press(g, pygame.K_RETURN)               # tournament -> how to play
        press(g, pygame.K_RETURN)               # -> difficulty
        press(g, 0, str(level))
        press(g, pygame.K_RETURN)               # -> select
        press(g, 0, str(pick + 1))
        press(g, pygame.K_RETURN)               # CPU roulette
        for _ in range(400):
            if isinstance(g.scene, scenes.Versus):
                break
            self.tick()
        self.assertIsInstance(g.scene, scenes.Versus)
        press(g, pygame.K_RETURN)
        self.tick(30)  # Versus ignores input during its first 0.8s
        press(g, pygame.K_RETURN)
        self.assertIsInstance(g.scene, Battle)

    def play(self, correct, max_ticks=60000):
        """Bot: answer every question (right or wrong). Turns run by themselves."""
        g = self.g
        seen = set()
        for _ in range(max_ticks):
            sc = g.scene
            seen.add(type(sc).__name__)
            if isinstance(sc, Battle):
                if sc.state == "question" and sc.q_left < sc.q_time - 0.5:
                    ans = sc.q.answer if correct else sc.q.answer + 1
                    for ch in str(ans):
                        press(g, 0, ch)
            elif isinstance(sc, (scenes.Champion, scenes.GameOver)):
                return sc, seen
            self.tick()
        self.fail("game did not finish")

    def test_perfect_player_wins_tournament_without_repeat_opponents(self):
        self.to_battle(level=2, pick=0)
        g = self.g
        opp = [f.key for f in g.opponents]
        self.assertEqual(len(opp), 4)
        self.assertEqual(len(set(opp)), 4)
        self.assertNotIn(g.player.key, opp)
        self.assertTrue(g.opponents[-1].boss)
        self.assertEqual(g.opponents[-1].name, "Ninja Ryu")
        sc, seen = self.play(correct=True)
        self.assertIsInstance(sc, scenes.Champion)
        self.assertEqual(g.stage, 3)
        self.assertEqual(g.stats["asked"], g.stats["correct"])
        # Champion -> new high score name -> top 10 -> credits -> THE END -> next level
        self.assertGreater(g.score, 0)
        self.tick(40)
        press(g, pygame.K_RETURN)
        self.assertIsInstance(g.scene, scenes.NameEntry)
        for ch in "ACE":
            press(g, 0, ch)
        press(g, pygame.K_RETURN)
        self.assertIsInstance(g.scene, scenes.HighScores)
        self.assertEqual(g.scene.highlight, 0)
        self.assertEqual(save.load()["scores"][0]["name"], "ACE")
        self.assertEqual(save.load()["scores"][0]["score"], g.score)
        press(g, pygame.K_RETURN)
        self.assertIsInstance(g.scene, scenes.Credits)
        press(g, pygame.K_RETURN)   # skip scroll
        self.tick(60)
        press(g, pygame.K_RETURN)
        self.assertIsInstance(g.scene, scenes.Difficulty)
        self.assertEqual(g.level, 3)

    def test_wrong_answers_lose_and_can_retry(self):
        self.to_battle(level=1, pick=3)
        sc, _ = self.play(correct=False)
        self.assertIsInstance(sc, scenes.GameOver)
        self.assertEqual(self.g.stage, 0)
        press(self.g, pygame.K_RETURN)
        self.assertIsInstance(self.g.scene, scenes.Versus)

    def test_timeout_counts_as_hit_on_player(self):
        self.to_battle(level=1, pick=1)
        b = self.g.scene
        for _ in range(2000):
            if b.state == "neutral":
                break
            if b.state == "question":
                for ch in str(b.q.answer):
                    press(self.g, 0, ch)
            self.tick()
        # wait (no input) for the CPU to attack and the 5 second timer to run out
        for _ in range(2000):
            self.tick()
            if b.p.hits >= 1:
                break
        self.assertEqual(b.p.hits, 1)
        self.assertLess(b.p.hits, MAX_HITS)
        self.assertTrue(b.result["timeout"])

    def test_answers_check_without_enter_and_defense_uses_attacker_math(self):
        self.to_battle(level=3, pick=0)
        b = self.g.scene
        for _ in range(2000):
            if b.state == "neutral":
                break
            if b.state == "question":
                for ch in str(b.q.answer):
                    press(self.g, 0, ch)
            self.tick()
        self.assertNotEqual(b.p.fd.op, b.c.fd.op)
        b.ask("attack")
        self.assertEqual(b.q.op, b.p.fd.op)
        digits = str(b.q.answer)
        for ch in digits[:-1]:
            press(self.g, 0, ch)
            self.assertEqual(b.state, "question")   # not enough digits yet
        press(self.g, 0, digits[-1])
        self.assertEqual(b.state, "action")         # checked on the last digit
        self.assertTrue(b.result["correct"])
        b.ask("defend")
        self.assertEqual(b.q.op, b.c.fd.op)
        self.assertEqual(b.q_time, 5.0)

    def test_turns_alternate_without_pressing_attack(self):
        self.to_battle(level=1, pick=2)
        b = self.g.scene
        modes = []
        for _ in range(4000):
            if b.state == "question":       # answering right away moves on to the action
                modes.append(b.mode)
                for ch in str(b.q.answer):
                    press(self.g, 0, ch)
            if len(modes) >= 4:
                break
            self.tick()
        self.assertEqual(modes, ["attack", "defend", "attack", "defend"])

    def test_final_boss_is_ninja_ryu_with_mixed_math_and_3_seconds(self):
        g = self.g
        self.to_battle(level=2, pick=1)
        g.stage = 3
        g.start_battle()
        b = g.scene
        self.assertEqual(b.c.fd.name, "Ninja Ryu")
        ops = set()
        for _ in range(60):
            b.ask("defend")
            self.assertEqual(b.q_time, 3.0)
            ops.add(b.q.op)
        self.assertEqual(ops, {"+", "-", "x", "/"})
        b.ask("attack")
        self.assertEqual(b.q.op, b.p.fd.op)
        self.assertEqual(b.q_time, 5.0)


    def test_beating_legend_unlocks_fractions_bonus_level(self):
        g = self.g
        self.assertFalse(g.bonus_unlocked)
        d = scenes.Difficulty(g)
        self.assertEqual(d.top, 5)
        g.level = 5
        g.goto(scenes.Credits(g))
        press(g, pygame.K_RETURN)   # skip scroll
        self.tick(60)
        press(g, pygame.K_RETURN)
        self.assertIsInstance(g.scene, scenes.Difficulty)
        self.assertEqual(g.level, 6)
        self.assertTrue(save.load().get("bonus"))      # remembered for next time
        self.assertEqual(g.scene.top, 6)
        g.scene.handle(pygame.event.Event(pygame.KEYDOWN, key=0, unicode="6", mod=0))
        self.assertEqual(g.scene.sel, 6)

    def test_fraction_answers_are_typed_numerator_then_denominator(self):
        self.g.unlock_bonus()
        self.to_battle(level=6, pick=0)
        b = self.g.scene
        for _ in range(2000):
            if b.state == "neutral":
                break
            if b.state == "question":
                for ch in b.q.digits:
                    press(self.g, 0, ch)
            self.tick()
        b.ask("attack")
        self.assertTrue(b.q.is_fraction)
        self.assertEqual(b.q_time, 8.0)
        num, den = str(b.q.answer).split("/")
        for ch in num + den:
            press(self.g, 0, ch)
        self.assertTrue(b.result["correct"])

    def test_music_toggle_keeps_sound_effects(self):
        g = self.g
        on = g.audio.music_on
        g.toggle_music()
        self.assertEqual(g.audio.music_on, not on)
        self.assertEqual(save.load().get("music"), not on)
        g.toggle_music()
        self.assertEqual(g.audio.music_on, on)


    def test_name_entry_limits_to_10_characters_and_m_is_a_letter(self):
        g = self.g
        g.score, g.level = 1234, 2
        music = g.audio.music_on
        g.end_run(lambda: scenes.Title(g))
        self.assertIsInstance(g.scene, scenes.NameEntry)
        for ch in "MATHEMATICIAN":                       # 13 letters, with M in it
            g.dispatch(pygame.event.Event(pygame.KEYDOWN, key=ord(ch.lower()), unicode=ch, mod=0))
        self.assertEqual(g.scene.name, "MATHEMATIC")     # cut at 10
        self.assertEqual(g.audio.music_on, music)        # typing M didn't switch the music
        press(g, pygame.K_RETURN)
        self.assertIsInstance(g.scene, scenes.HighScores)
        press(g, pygame.K_RETURN)
        self.assertIsInstance(g.scene, scenes.Title)
        self.assertEqual(save.load()["last_name"], "MATHEMATIC")

    def test_zero_score_skips_name_entry(self):
        g = self.g
        g.score = 0
        g.end_run(lambda: scenes.Title(g))
        self.assertIsInstance(g.scene, scenes.Title)


    # ------------------------------------------------------- special moves
    def answer_after(self, b, seconds):
        b.ask("attack")
        b.q_left = b.q_time - seconds
        for ch in b.q.digits:
            press(self.g, 0, ch)
        for _ in range(400):
            if b.state != "action":
                break
            self.tick()

    def ready_battle(self):
        self.to_battle(level=1, pick=0)
        b = self.g.scene
        for _ in range(2000):        # get through the intro and the first automatic question
            if b.state == "question":
                for ch in b.q.digits:
                    press(self.g, 0, ch)
            if b.state == "neutral":
                break
            self.tick()
        b.c.hits = 0
        b.wait = 99
        return b

    def test_answer_within_2_seconds_is_a_special_move_taking_two_health(self):
        b = self.ready_battle()
        self.answer_after(b, 1.5)
        self.assertEqual(b.exchange["tier"], 1)
        self.assertEqual(b.c.hits, 2)

    def test_faster_answer_earns_the_super_version(self):
        b = self.ready_battle()
        before = self.g.score
        self.answer_after(b, 0.5)
        self.assertEqual(b.exchange["tier"], 2)
        self.assertEqual(b.c.hits, 2)
        fast = self.g.score - before
        b.c.hits = 0
        before = self.g.score
        self.answer_after(b, 1.5)
        self.assertGreater(fast, self.g.score - before)

    def test_slower_answer_is_a_normal_one_health_hit(self):
        b = self.ready_battle()
        self.answer_after(b, 3.0)
        self.assertEqual(b.exchange["tier"], 0)
        self.assertEqual(b.c.hits, 1)

    def test_special_knockout_does_not_go_past_empty(self):
        b = self.ready_battle()
        b.c.hits = 7
        self.answer_after(b, 0.5)
        self.assertEqual(b.c.hits, 8)
        self.assertEqual(b.state, "ko")

    def test_every_fighter_has_a_special_move_that_runs(self):
        from mathfighter.characters import RYU
        from mathfighter.specials import make_special
        g = self.g
        for fd in ROSTER + [RYU]:
            hits = []
            move = make_special(fd.key, 400, 400, 900, 1, fd.theme, 2, lambda: hits.append(1))
            b_fx = scenes.Effects()
            for _ in range(400):
                alive = move.update(DT, b_fx)
                move.draw(g.screen)
                if not alive:
                    break
            self.assertEqual(hits, [1], fd.key)

    # --------------------------------------------------- settings and menus
    def test_math_settings_limit_the_questions(self):
        g = self.g
        for op in ("-", "x", "/"):
            g.toggle_op(op)
        self.assertEqual(g.allowed_ops, ("+",))
        g.toggle_op("+")                      # the last one can't be switched off
        self.assertEqual(g.allowed_ops, ("+",))
        self.to_battle(level=2, pick=2)       # Dax, who normally asks subtraction
        b = g.scene
        for mode in ("attack", "defend"):
            for _ in range(20):
                b.ask(mode)
                self.assertEqual(b.q.op, "+")

    def test_main_menu_reaches_every_screen(self):
        g = self.g
        press(g, pygame.K_RETURN)
        self.assertIsInstance(g.scene, menus.MainMenu)
        for row, kind in ((0, scenes.HowTo), (1, menus.Options), (2, menus.Options), (3, menus.ProgressScreen),
                          (4, scenes.HighScores), (5, menus.Options)):
            g.goto(menus.MainMenu(g))
            for _ in range(row):
                press(g, pygame.K_DOWN)
            press(g, pygame.K_RETURN)
            self.assertIsInstance(g.scene, kind)
            self.tick(2)

    def test_every_scene_draws_at_high_quality(self):
        g = self.g
        QUALITY["ss"] = 2
        try:
            self.to_battle(level=2, pick=1)
            self.tick(30)
            g.goto(menus.MainMenu(g))
            self.tick(3)
            g.goto(menus.ProgressScreen(g))
            self.tick(3)
            g.goto(drill.Drill(g, "practice"))
            self.tick(50)
        finally:
            QUALITY["ss"] = 1

    # -------------------------------------------------- practice and daily
    def run_drill(self, d, wrong_first=False, answers=None):
        g = self.g
        n = 0
        for _ in range(8000):
            if g.scene is not d:
                return
            if d.state == "question":
                if answers is not None and n >= answers:
                    return
                n += 1
                digits = d.q.digits
                if wrong_first and n == 1:
                    digits = "9" * len(digits) if digits != "9" * len(digits) else "1" * len(digits)
                for ch in digits:
                    press(g, 0, ch)
            self.tick()

    def test_practice_has_no_timer_and_missed_questions_come_back(self):
        g = self.g
        g.set_level(2)
        d = drill.Drill(g, "practice")
        g.goto(d)
        for _ in range(60):
            self.tick()
            if d.state == "question":
                break
        d.elapsed = 1000.0                     # waiting forever never times out
        self.tick(5)
        self.assertEqual(d.state, "question")
        self.run_drill(d, wrong_first=True, answers=7)
        self.assertEqual(d.asked, 7)
        self.assertEqual(d.right, 6)
        self.assertEqual(d.redo, [])           # it was asked again
        self.assertEqual(progress.totals(g.save)[0], 7)
        press(g, pygame.K_ESCAPE)
        self.assertIsInstance(g.scene, drill.DrillSummary)

    def test_daily_challenge_is_the_same_all_day_and_keeps_a_streak(self):
        g = self.g
        g.set_level(1)
        a = drill.Drill(g, "daily")
        b = drill.Drill(g, "daily")
        self.assertEqual(a.queue, b.queue)
        self.assertEqual(len(a.queue), 10)
        g.goto(a)
        self.run_drill(a)
        self.assertIsInstance(g.scene, drill.DrillSummary)
        st = progress.daily_status(g.save, g.today())
        self.assertEqual(st["streak"], 1)
        self.assertEqual(st["today"], a.score)
        self.assertGreater(a.score, 0)


if __name__ == "__main__":
    unittest.main()
