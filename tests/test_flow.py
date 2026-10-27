"""Headless playthroughs of the whole game flow with a bot answering questions."""

import os
import tempfile
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["MATHFIGHTER_DATA"] = tempfile.mkdtemp(prefix="mathfighter-test-")  # don't touch the real save

import pygame  # noqa: E402

from mathfighter import save, scenes  # noqa: E402
from mathfighter.battle import Battle  # noqa: E402
from mathfighter.config import MAX_HITS  # noqa: E402
from mathfighter.game import Game  # noqa: E402

DT = 1 / 30


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
        self.g.seen_howto = False
        self.g.to_title()

    def tick(self, n=1):
        for _ in range(n):
            self.g.scene.update(DT)
            self.g.scene.draw(self.g.screen)

    def to_battle(self, level=1, pick=0):
        g = self.g
        press(g, pygame.K_RETURN)               # title -> how to play
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
        # Champion -> credits -> THE END -> difficulty at a higher level
        self.tick(40)
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


if __name__ == "__main__":
    unittest.main()
