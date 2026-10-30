"""Practice mode and the daily challenge: math without health bars.

Practice has no timer, and a missed question comes back a little later. The daily
challenge is a fixed set of timed questions, the same all day, for a score."""

import random
from datetime import date

import pygame

from . import progress
from .battle import (ATTACK_MOVES, PTS_CORRECT, PTS_SPECIAL, PTS_SPEED, PTS_SUPER, Actor, draw_question_panel,
                     draw_result_strip, question_time, special_tier)
from .characters import ROSTER
from .config import (ANSWER_TIME, DAILY_QUESTIONS, CPU_HOME_X, GOLD, GREEN, GROUND_Y, H, PLAYER_HOME_X,
                     SPECIAL_DAMAGE, SPECIAL_WINDOW, SUPER_WINDOW, TURN_PAUSE, W, WHITE)
from .effects import Effects
from .mathq import DISPLAY, MIX, OP_NAMES, QuestionMaker
from .scenes import CONFIRM, Scene, blink, starfield_bg
from .specials import CutIn, make_special
from .stages import STAGES
from .ui import Keypad, panel, text

REPEAT_AFTER = 3     # a missed practice question comes back this many questions later


def theme_name(theme):
    return "All four mixed" if theme == MIX else OP_NAMES[theme]


class Drill(Scene):
    DONE_RECT = pygame.Rect(W - 170, 110, 150, 56)

    def __init__(self, game, mode):
        super().__init__(game)
        self.mode = mode
        self.level = game.level
        self.day = game.today()
        ordinal = date.fromisoformat(self.day).toordinal()
        if mode == "daily":
            self.theme = progress.daily_theme(self.day, game.allowed_ops)
            rng = random.Random(f"{self.day}:{self.level}:{self.theme}")
            maker = QuestionMaker(self.theme, self.level, rng, allowed=game.allowed_ops)
            self.queue = [maker.next() for _ in range(DAILY_QUESTIONS)]
            self.maker = None
            self.stage = STAGES[ordinal % len(STAGES)]()
        else:
            self.maker = QuestionMaker(MIX, self.level, allowed=game.allowed_ops)
            self.queue = []
            self.stage = STAGES[self.level % len(STAGES)]()
        others = [f for f in ROSTER if f is not game.player]
        self.p = Actor(game.player, PLAYER_HOME_X, 1)
        self.c = Actor(random.choice(others), CPU_HOME_X, -1)
        for a in (self.p, self.c):
            a.rim, a.reflect = self.stage.rim, self.stage.reflect
        self.fx = Effects()
        self.keypad = Keypad()
        self.redo = []           # (question number it is due at, question)
        self.asked = self.right = self.score = self.best_run = self.run = 0
        self.specials = 0
        self.state, self.state_t = "intro", 0.0
        self.q = None
        self.typed = ""
        self.result = None
        self.cutin = None
        self.exchange = None
        self.score_pop = None
        game.audio.play_music(self.stage.music_key)

    # ------------------------------------------------------------------ flow
    def next_question(self):
        if self.mode == "daily":
            return self.queue[self.asked] if self.asked < len(self.queue) else None
        if self.redo and self.redo[0][0] <= self.asked:
            return self.redo.pop(0)[1]
        return self.maker.next()

    def ask(self):
        q = self.next_question()
        if q is None:
            self.finish()
            return
        self.q = q
        self.typed = ""
        self.elapsed = 0.0
        self.q_time = question_time(q) if self.mode == "daily" else None
        self.result = None
        self.p.play("charge")
        self.state, self.state_t = "question", 0.0
        self.game.audio.play("select")

    def submit(self, timeout=False):
        q = self.q
        correct = not timeout and self.typed == q.digits
        limit = self.q_time or question_time(q)
        tier = special_tier(self.elapsed, limit) if correct else 0
        self.asked += 1
        self.announce(self.game.answered(q.op, correct, self.elapsed, tier > 0))
        self.result = {"correct": correct, "q": q, "timeout": timeout, "t": 0.0, "typed": self.typed}
        self.game.audio.play("correct" if correct else "wrong")
        if correct:
            self.right += 1
            self.run += 1
            self.best_run = max(self.best_run, self.run)
            self.specials += 1 if tier else 0
            if self.mode == "daily":
                pts = PTS_CORRECT + int(PTS_SPEED * max(0.0, 1 - self.elapsed / limit))
                pts += {0: 0, 1: PTS_SPECIAL, 2: PTS_SUPER}[tier]
                self.score += pts * self.level
                self.score_pop = [pts * self.level, 0.0]
        else:
            self.run = 0
            if self.mode == "practice":
                self.redo.append((self.asked + REPEAT_AFTER, q))
        self.exchange = {"outcome": "hit" if correct else "miss", "tier": tier, "dodged": False}
        self.p.play(self.p.special_anim if tier else random.choice(ATTACK_MOVES))
        if tier:
            self.cutin = CutIn(self.p.fd, tier, 1)
            self.game.audio.play("super" if tier == 2 else "special")
        self.state, self.state_t = "action", 0.0

    def announce(self, events):
        x, y = self.p.home, GROUND_Y - 340
        if events.get("best_streak"):
            self.fx.text("NEW BEST STREAK!", x, y, (255, 240, 120), 44, 1.4)
        elif events.get("milestone"):
            self.fx.text(f"{events['milestone']} IN A ROW!", x, y, (255, 240, 120), 44, 1.2)

    def finish(self):
        g = self.game
        title, lines = "PRACTICE COMPLETE!", []
        if self.mode == "daily":
            res = progress.daily_finish(g.save, self.day, self.score)
            title = "DAILY CHALLENGE COMPLETE!"
            lines.append((f"Score: {self.score:,}", GOLD))
            if res["new_best"]:
                lines.append(("NEW PERSONAL BEST!", (255, 240, 120)))
            lines.append((f"Daily streak: {res['streak']} day{'s' if res['streak'] != 1 else ''} in a row", WHITE))
        pct = int(100 * self.right / self.asked) if self.asked else 0
        lines.append((f"Correct: {self.right} of {self.asked}  ({pct}%)", WHITE))
        lines.append((f"Most in a row: {self.best_run}", WHITE))
        if self.specials:
            lines.append((f"Special moves: {self.specials}", WHITE))
        weak = progress.weakest_op(g.save)
        if weak:
            lines.append((f"Next, try practising {OP_NAMES[weak].lower()}.", (160, 220, 255)))
        elif self.mode == "daily":
            lines.append(("Come back tomorrow for a new challenge!", (160, 220, 255)))
        g.store()
        g.goto(DrillSummary(g, title, lines))

    def leave(self):
        """ESC or DONE: practice shows its summary; a daily challenge isn't counted."""
        if self.mode == "practice" and self.asked:
            self.finish()
            return
        from .menus import MainMenu
        self.game.store()
        self.game.goto(MainMenu(self.game))

    # ----------------------------------------------------------------- input
    def handle(self, ev):
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                self.leave()
            elif self.state == "question":
                if ev.unicode and ev.unicode.isdigit():
                    self.type_digit(ev.unicode)
                elif ev.key == pygame.K_BACKSPACE:
                    self.typed = self.typed[:-1]
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self.DONE_RECT.collidepoint(ev.pos):
                self.leave()
            elif self.state == "question":
                k = self.keypad.hit(ev.pos)
                if k == "DEL":
                    self.typed = self.typed[:-1]
                elif k:
                    self.type_digit(k)

    def type_digit(self, d):
        self.typed += d
        if len(self.typed) >= len(self.q.digits):
            self.submit()

    # ---------------------------------------------------------------- update
    def on_event(self, actor, e):
        ex = self.exchange
        if actor is not self.p or not ex:
            return
        if e in ("hit", "jab"):
            self.impact(e == "hit")
        elif e == "fire":
            hx, hy = actor.point("hand_f")
            tx = self.c.point("chest")[0] + 30
            self.game.audio.play("fire")
            self.fx.projectiles.append(make_special(actor.fd.key, hx, hy, tx, 1, actor.fd.theme,
                                                    ex["tier"], lambda: self.impact(True)))

    def impact(self, final):
        ex = self.exchange
        x, y = self.c.point("chest")
        if ex["outcome"] == "hit":
            self.c.play("hit")
            self.c.flash = 1.0 if final else 0.6
            self.fx.hit_spark(x + 20, y, big=final)
            self.game.audio.play("bighit" if final else "hit")
            if final:
                self.fx.shake(10 + 6 * ex["tier"], 0.3)
                label = f"SPECIAL! -{SPECIAL_DAMAGE}" if ex["tier"] else "HIT!"
                self.fx.text(label, x, y - 90, GOLD, 64, 1.0)
        elif not ex["dodged"]:
            ex["dodged"] = True
            self.c.play("dodge")
            self.game.audio.play("whoosh")
            self.fx.text("MISS!", x, y - 90, (200, 200, 220), 64)

    def update(self, dt):
        self.t += dt
        if self.cutin:
            self.stage.update(dt)
            self.cutin.update(dt)
            if self.cutin.done:
                self.cutin = None
            return
        self.state_t += dt
        self.stage.update(dt)
        for a in (self.p, self.c):
            for e in a.update(dt):
                self.on_event(a, e)
        self.fx.update(dt)
        if self.result:
            self.result["t"] += dt
        if self.score_pop:
            self.score_pop[1] += dt
        if self.state == "intro":
            if self.state_t > 1.2:
                self.ask()
        elif self.state == "question":
            self.elapsed += dt
            if self.q_time and self.elapsed >= self.q_time:
                self.submit(timeout=True)
        elif self.state == "action":
            if (self.state_t > 0.6 and self.p.settled and self.c.settled and not self.fx.projectiles):
                self.state, self.state_t = "pause", 0.0
        elif self.state == "pause":
            if self.state_t > TURN_PAUSE:
                self.ask()

    # ------------------------------------------------------------------ draw
    def draw(self, surf):
        self.stage.draw(surf)
        order = (self.c, self.p)
        for a in order:
            a.draw(surf)
        self.fx.draw(surf)
        self.stage.draw_front(surf)
        ox, oy = self.fx.offset()
        if ox or oy:
            surf.scroll(int(ox), int(oy))
        if self.cutin:
            self.cutin.draw(surf)
        self.draw_hud(surf)
        if self.state == "question":
            self.draw_question(surf)
        elif self.result and self.result["t"] < 1.6:
            draw_result_strip(surf, self.result)
        self.fx.draw_top(surf)
        if self.state == "intro":
            msg = "PRACTICE" if self.mode == "practice" else "DAILY CHALLENGE"
            text(surf, msg, 100, GOLD, center=(W // 2, H // 2 - 40), ow=6)

    def draw_hud(self, surf):
        panel(surf, (16, 14, 460, 92), (15, 10, 35), 215, GOLD, 14, 3)
        if self.mode == "daily":
            n = min(self.asked + (1 if self.state == "question" else 0), DAILY_QUESTIONS)
            text(surf, f"DAILY: {theme_name(self.theme).upper()}", 32, GOLD, midleft=(34, 38), ow=2)
            text(surf, f"Question {n} of {DAILY_QUESTIONS}", 32, WHITE, midleft=(34, 78), ow=2)
            text(surf, f"{self.score:,}", 46, GOLD, midright=(458, 72), ow=3)
            if self.score_pop and self.score_pop[1] < 1.0:
                text(surf, f"+{self.score_pop[0]:,}", 30, (255, 255, 180), midright=(458, 34), ow=2)
        else:
            text(surf, "PRACTICE  -  no timer", 32, GOLD, midleft=(34, 38), ow=2)
            text(surf, f"Correct {self.right} of {self.asked}", 32, WHITE, midleft=(34, 78), ow=2)
            text(surf, f"{self.run} in a row", 32, WHITE, midright=(458, 78), ow=2)
        panel(surf, self.DONE_RECT, (30, 30, 60), 210, WHITE, 10, 2)
        text(surf, "DONE" if self.mode == "practice" else "QUIT", 32, center=self.DONE_RECT.center, ow=2)
        if not self.game.touch:
            text(surf, "ESC", 22, (210, 210, 230), center=(W - 95, 178), ow=2)
        text(surf, f"LEVEL {self.level}", 26, (230, 230, 240), center=(W // 2, H - 18))

    def draw_question(self, surf):
        k = (self.q_time or question_time(self.q)) / ANSWER_TIME
        hints = []
        if self.q.is_fraction:
            hints.append(("SIMPLEST FORM", (150, 230, 255)))
        if self.q_time:       # no countdowns in practice: there is no rush
            if self.elapsed <= SUPER_WINDOW * k:
                hints.append(("SUPER SPECIAL!", (255, 225, 90)))
            elif self.elapsed <= SPECIAL_WINDOW * k:
                hints.append(("SPECIAL MOVE!", WHITE))
        left = self.q_time - self.elapsed if self.q_time else None
        marks = [(SPECIAL_WINDOW * k, WHITE), (SUPER_WINDOW * k, GOLD)] if self.q_time else []
        head = f"{OP_NAMES[self.q.op]}  {DISPLAY[self.q.op]}"
        draw_question_panel(surf, self.q, self.typed, head, (255, 200, 60), left, self.q_time, hints, marks)
        if self.game.touch:
            self.keypad.draw(surf, 1 / 60)


class DrillSummary(Scene):
    def __init__(self, game, title, lines):
        super().__init__(game)
        self.title, self.lines = title, lines
        self.bg = starfield_bg((10, 20, 60), (50, 30, 90))
        self.actor = Actor(game.player, 240, 1, 1.15)
        self.actor.play("victory")
        game.audio.play("confirm")
        game.audio.play_music("menu")

    def handle(self, ev):
        if self.t > 0.4 and ((ev.type == pygame.KEYDOWN and (ev.key in CONFIRM or ev.key == pygame.K_ESCAPE)) or
                             (ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1)):
            from .menus import MainMenu
            self.game.goto(MainMenu(self.game))

    def update(self, dt):
        super().update(dt)
        self.actor.update(dt)

    def draw(self, surf):
        surf.blit(self.bg, (0, 0))
        pygame.draw.rect(surf, (35, 25, 60), (0, 650, W, 70))
        self.actor.draw(surf, 650)
        text(surf, self.title, 72, GOLD, center=(W // 2, 70), ow=5)
        panel(surf, (470, 140, 750, 450), (10, 10, 30), 210)
        for i, (line, col) in enumerate(self.lines):
            text(surf, line, 42, col, midleft=(510, 190 + i * 58), ow=3)
        if blink(self.t):
            text(surf, "Press ENTER to continue", 44, GREEN, center=(845, 650), ow=3)
