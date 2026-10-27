"""Main loop, screen scaling and tournament progression."""

import os
import random
import sys

import pygame

from .config import FPS, H, TITLE, W
from . import highscores, save
from .characters import ROSTER, RYU

ON_ANDROID = "ANDROID_ARGUMENT" in os.environ or hasattr(sys, "getandroidapilevel")

# pygame.SCALED only scales by whole numbers (1x, 2x...) unless this hint is set,
# so a 1280x720 game would stay 1280x720 in a bigger window and just add borders.
# With it, the game fills any window size (keeping its 16:9 shape). Linear
# filtering keeps the picture smooth at in-between sizes.
os.environ["SDL_HINT_RENDER_SCALE_QUALITY"] = "1"
os.environ.setdefault("SDL_RENDER_SCALE_QUALITY", "linear")


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
        self.save = save.load()
        from .audio import Audio  # after pygame.init so the mixer is ready
        self.audio = Audio(music_on=self.save.get("music", True))
        self.touch = ON_ANDROID
        self.seen_howto = False
        self.level = 1
        self.player = ROSTER[0]
        self.opponents = []
        self.stage = 0
        self.score = 0
        self.reset_stats()
        from .scenes import Title
        self.scene = Title(self)
        self.running = True

    @property
    def bonus_unlocked(self):
        return bool(self.save.get("bonus"))

    def unlock_bonus(self):
        self.save["bonus"] = True
        save.store(self.save)

    def toggle_music(self):
        """Music on/off; sound effects always stay on. Remembered between games."""
        self.save["music"] = self.audio.toggle_music()
        save.store(self.save)

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
        self.score = 0
        from .scenes import Versus
        self.goto(Versus(self))

    def start_battle(self):
        from .battle import Battle
        self.goto(Battle(self))

    def end_run(self, then):
        """The run is over (lost, or won the tournament). A top-10 score asks
        for a name first; then(), which makes the next scene, comes after."""
        from .scenes import NameEntry
        if highscores.qualifies(self.save, self.score):
            self.goto(NameEntry(self, then))
        else:
            self.goto(then())

    def record_score(self, name):
        place = highscores.add(self.save, name, self.score, self.level, self.player.name)
        self.save["last_name"] = name.strip()[:highscores.NAME_LEN]
        save.store(self.save)
        return place

    def match_over(self, won):
        from .scenes import Champion, GameOver, Versus
        if not won:
            self.end_run(lambda: GameOver(self))
        elif self.stage >= len(self.opponents) - 1:
            self.goto(Champion(self))
        else:
            self.stage += 1
            self.goto(Versus(self))

    # ----------------------------------------------------------------- loop --
    def dispatch(self, ev):
        """Global keys first, everything else goes to the current scene."""
        if ev.type == pygame.QUIT:
            self.running = False
        elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_F11:
            pygame.display.toggle_fullscreen()
        elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_m and \
                not getattr(self.scene, "text_input", False):   # M is a letter when typing a name
            self.toggle_music()
        elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_AC_BACK:
            self.to_title()
        else:
            if ev.type == pygame.MOUSEBUTTONDOWN:
                self.touch = True
            self.scene.handle(ev)

    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 1 / 20)
            for ev in pygame.event.get():
                self.dispatch(ev)
            self.scene.update(dt)
            self.audio.update()
            self.scene.draw(self.screen)
            pygame.display.flip()
        pygame.quit()


def main():
    Game().run()
