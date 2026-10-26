"""Headless playthroughs of the whole game flow with a bot answering questions."""

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from mathfighter import scenes  # noqa: E402
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
        """Bot: attack whenever allowed, answer every question (right or wrong)."""
        g = self.g
        seen = set()
        for _ in range(max_ticks):
            sc = g.scene
            seen.add(type(sc).__name__)
            if isinstance(sc, Battle):
                if sc.state == "neutral" and sc.player_turn:
                    press(g, pygame.K_SPACE)
                elif sc.state == "question" and sc.q_left < 4.5:
                    ans = sc.q.answer if correct else sc.q.answer + 1
                    for ch in str(ans):
                        press(g, 0, ch)
                    press(g, pygame.K_RETURN)
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
        self.assertTrue(g.opponents[-1].shadow)
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
                press(self.g, 0, str(b.q.answer))
                press(self.g, pygame.K_RETURN)
            self.tick()
        # wait (no input) for the CPU to attack and the 5 second timer to run out
        for _ in range(2000):
            self.tick()
            if b.p.hits >= 1:
                break
        self.assertEqual(b.p.hits, 1)
        self.assertLess(b.p.hits, MAX_HITS)
        self.assertTrue(b.result["timeout"])


if __name__ == "__main__":
    unittest.main()
