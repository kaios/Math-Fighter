"""Main loop, screen scaling and tournament progression."""

import os
import random
import sys

import pygame

from .config import FPS, H, TITLE, W
from .characters import ROSTER, RYU

ON_ANDROID = "ANDROID_ARGUMENT" in os.environ or hasattr(sys, "getandroidapilevel")


class Game:
    def __init__(self):
        pygame.mixer.pre_init(22050, -16, 1, 512)
        pygame.init()
        pygame.display.set_caption(TITLE)
        from .ui import portrait
        pygame.display.set_icon(portrait(ROSTER[0], 64))
        flags = pygame.SCALED | (pygame.FULLSCREEN if ON_ANDROID else pygame.RESIZABLE)
        self.screen = pygame.display.set_mode((W, H), flags)
        self.clock = pygame.time.Clock()
        from .audio import Audio  # after pygame.init so the mixer is ready
        self.audio = Audio()
        self.touch = ON_ANDROID
        self.seen_howto = False
        self.level = 1
        self.player = ROSTER[0]
        self.opponents = []
        self.stage = 0
        self.reset_stats()
        from .scenes import Title
        self.scene = Title(self)
        self.running = True

    def reset_stats(self):
        self.stats = {"asked": 0, "correct": 0, "best": 99.0}

    # ---------------------------------------------------------- progression --
    def goto(self, scene):
        self.scene = scene

    def to_title(self):
        from .scenes import Title
        self.goto(Title(self))

    def start_tournament(self, player, first_cpu):
        """The CPU's pick is the first opponent; the other two follow in random
        order and the final stage is the boss, Ninja Ryu. No repeats."""
        self.player = player
        rest = [f for f in ROSTER if f not in (player, first_cpu)]
        random.shuffle(rest)
        self.opponents = [first_cpu] + rest + [RYU]
        self.stage = 0
        self.reset_stats()
        from .scenes import Versus
        self.goto(Versus(self))

    def start_battle(self):
        from .battle import Battle
        self.goto(Battle(self))

    def match_over(self, won):
        from .scenes import Champion, GameOver, Versus
        if not won:
            self.goto(GameOver(self))
        elif self.stage >= len(self.opponents) - 1:
            self.goto(Champion(self))
        else:
            self.stage += 1
            self.goto(Versus(self))

    # ----------------------------------------------------------------- loop --
    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 1 / 20)
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.running = False
                elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_m and \
                        type(self.scene).__name__ != "Battle":
                    self.audio.toggle()
                elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_AC_BACK:
                    self.to_title()
                else:
                    if ev.type == pygame.MOUSEBUTTONDOWN:
                        self.touch = True
                    self.scene.handle(ev)
            self.scene.update(dt)
            self.audio.update()
            self.scene.draw(self.screen)
            pygame.display.flip()
        pygame.quit()


def main():
    Game().run()
