"""Menus and story screens: title, how to play, difficulty, character select,
versus, game over, champion, credits."""

import math
import random

import pygame

from .battle import Actor
from .characters import ROSTER
from .config import __version__, CREDITS_NAME, GOLD, GREEN, H, MAX_LEVEL, RED, W, WHITE
from .draw import darker, fill_circle, fill_poly, lighter, mix, vgradient
from .effects import Effects, Particle
from .mathq import ADD, DIV, DISPLAY, MUL, OP_NAMES, SUB, make_question
from .stages import STAGES
from .ui import panel, text, text_img

CONFIRM = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)


def blink(t, speed=2.5):
    return int(t * speed) % 2 == 0


class Scene:
    def __init__(self, game):
        self.game = game
        self.t = 0.0

    def handle(self, ev):
        pass

    def update(self, dt):
        self.t += dt

    def draw(self, surf):
        pass


def starfield_bg(top, bottom):
    bg = vgradient((W, H), top, bottom)
    rng = random.Random(5)
    for _ in range(120):
        bg.set_at((rng.randint(0, W - 1), rng.randint(0, H - 1)), (255, 255, 255))
    return bg


def draw_rays(surf, center, t, color, n=16, alpha=40):
    layer = pygame.Surface((W, H), pygame.SRCALPHA)
    cx, cy = center
    for i in range(n):
        a = t * 0.2 + i * math.tau / n
        b = a + math.tau / n / 2
        pts = [(cx, cy), (cx + math.cos(a) * 1600, cy + math.sin(a) * 1600),
               (cx + math.cos(b) * 1600, cy + math.sin(b) * 1600)]
        pygame.draw.polygon(layer, (*color, alpha), pts)
    surf.blit(layer, (0, 0))


def logo(surf, cy, t):
    bob = math.sin(t * 2) * 6
    a = text_img("MATH", 150, GOLD, (120, 30, 20), 8)
    b = text_img("FIGHTER", 150, (255, 90, 70), (60, 10, 30), 8)
    x = W // 2 - (a.get_width() + b.get_width() + 30) // 2
    surf.blit(a, a.get_rect(midleft=(x, cy + bob)))
    surf.blit(b, b.get_rect(midleft=(x + a.get_width() + 30, cy - bob)))
    text(surf, "TOURNAMENT OF NUMBERS", 44, WHITE, center=(W // 2, cy + 80), outline=(30, 20, 70), ow=4)


class Title(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.bg = starfield_bg((20, 10, 60), (120, 40, 110))
        self.actors = []
        for i, fd in enumerate(ROSTER):
            a = Actor(fd, 240 + i * 270, 1 if i < 2 else -1, 0.95)
            a.anim.update(i * 0.3)
            self.actors.append(a)
        game.audio.play_music("menu")

    def handle(self, ev):
        if (ev.type == pygame.KEYDOWN and ev.key in CONFIRM) or \
                (ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1):
            self.game.audio.play("confirm")
            self.game.goto(HowTo(self.game) if not self.game.seen_howto else Difficulty(self.game))

    def update(self, dt):
        super().update(dt)
        for a in self.actors:
            a.update(dt)

    def draw(self, surf):
        surf.blit(self.bg, (0, 0))
        draw_rays(surf, (W // 2, 160), self.t, (255, 200, 120), alpha=22)
        for sym, x, y, c in (("+", 120, 120, (255, 120, 40)), ("÷", 1160, 140, (170, 90, 255)),
                             ("\u2212", 160, 330, (60, 140, 255)), ("×", 1120, 340, (255, 80, 170))):
            text(surf, sym, 120, c, center=(x, y + math.sin(self.t * 2 + x) * 10), ow=5)
        pygame.draw.rect(surf, (40, 20, 60), (0, 640, W, 80))
        for a in self.actors:
            a.draw(surf, 650)
        logo(surf, 170, self.t)
        if blink(self.t):
            msg = "TAP TO START" if self.game.touch else "PRESS ENTER TO START"
            text(surf, msg, 56, WHITE, center=(W // 2, 335), ow=4)
        text(surf, "F11: Full screen    M: Sound on/off    ESC: Pause", 26, (200, 190, 230),
             center=(W // 2, H - 20), ow=2)
        text(surf, f"v{__version__}", 22, (170, 160, 200), bottomright=(W - 10, H - 6), ow=2)


class HowTo(Scene):
    LINES = [
        ("Pick a fighter. Each one fights with a different kind of math!", WHITE),
        ("Press SPACE to attack. Answer the question in 5 seconds to land a hit.", GOLD),
        ("When the CPU attacks, answer ITS math question fast to BLOCK. Too slow = hit!", (120, 200, 255)),
        ("Answer a defense question in under 2.5 seconds for a COUNTER attack!", (255, 160, 220)),
        ("Type every digit of the answer (50 is 5 then 0). No ENTER needed!", WHITE),
        ("8 hits and you're down. Win 2 rounds to beat a stage. Each round is 99 seconds.", WHITE),
        ("Win all 4 stages to become the MATH TOURNAMENT CHAMPION!", GREEN),
    ]

    def __init__(self, game):
        super().__init__(game)
        self.bg = starfield_bg((15, 20, 60), (40, 70, 120))
        game.seen_howto = True

    def handle(self, ev):
        if (ev.type == pygame.KEYDOWN and ev.key in CONFIRM) or \
                (ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1):
            self.game.audio.play("confirm")
            self.game.goto(Difficulty(self.game))

    def draw(self, surf):
        surf.blit(self.bg, (0, 0))
        text(surf, "HOW TO PLAY", 96, GOLD, center=(W // 2, 80), ow=5)
        panel(surf, (90, 150, W - 180, 470), (10, 10, 30), 200)
        for i, (line, col) in enumerate(self.LINES):
            text(surf, line, 36, col, midleft=(130, 200 + i * 62), ow=3)
        if blink(self.t):
            text(surf, "Press ENTER to continue", 46, WHITE, center=(W // 2, H - 50))


class Difficulty(Scene):
    NAMES = ["Rookie", "Fighter", "Warrior", "Master", "Legend"]
    COLORS = [(80, 200, 120), (100, 180, 255), (255, 200, 60), (255, 130, 50), (230, 50, 80)]

    def __init__(self, game, message=None):
        super().__init__(game)
        self.sel = game.level
        self.message = message
        self.bg = starfield_bg((30, 10, 50), (90, 30, 90))
        rng = random.Random(9)
        self.examples = {lv: "    ".join(make_question(op, lv, rng).text.replace(" = ?", "")
                                       for op in (ADD, SUB, MUL, DIV)) for lv in range(1, 6)}
        self.rects = [pygame.Rect(140 + i * 210, 250, 170, 200) for i in range(5)]
        game.audio.play_music("menu")

    def choose(self):
        self.game.level = self.sel
        self.game.audio.play("confirm")
        self.game.goto(Select(self.game))

    def handle(self, ev):
        g = self.game
        if ev.type == pygame.KEYDOWN:
            if ev.key in (pygame.K_LEFT, pygame.K_a):
                self.sel = max(1, self.sel - 1)
                g.audio.play("select")
            elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                self.sel = min(MAX_LEVEL, self.sel + 1)
                g.audio.play("select")
            elif ev.unicode in ("1", "2", "3", "4", "5"):
                self.sel = int(ev.unicode)
                g.audio.play("select")
            elif ev.key in CONFIRM:
                self.choose()
            elif ev.key == pygame.K_ESCAPE:
                g.to_title()
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            for i, r in enumerate(self.rects):
                if r.collidepoint(ev.pos):
                    if self.sel == i + 1:
                        self.choose()
                    else:
                        self.sel = i + 1
                        g.audio.play("select")

    def draw(self, surf):
        surf.blit(self.bg, (0, 0))
        text(surf, "CHOOSE YOUR LEVEL", 90, GOLD, center=(W // 2, 80), ow=5)
        if self.message:
            text(surf, self.message, 40, GREEN, center=(W // 2, 160), ow=3)
        else:
            text(surf, "1 = easy   ...   5 = hardest", 40, WHITE, center=(W // 2, 160), ow=3)
        for i, r in enumerate(self.rects):
            lv = i + 1
            on = lv == self.sel
            rr = r.inflate(24, 24) if on else r
            if on:
                rr = rr.move(0, int(math.sin(self.t * 5) * 4))
            panel(surf, rr, self.COLORS[i] if on else darker(self.COLORS[i], 0.45), 235,
                  WHITE if on else (150, 150, 170), 18, 4 if on else 2)
            text(surf, str(lv), 120, WHITE, center=(rr.centerx, rr.centery - 20), ow=5)
            text(surf, self.NAMES[i], 38, WHITE, center=(rr.centerx, rr.bottom - 32), ow=3)
        panel(surf, (140, 500, W - 280, 110), (10, 10, 30), 200)
        text(surf, f"Level {self.sel}: {self.NAMES[self.sel - 1]}", 44, self.COLORS[self.sel - 1],
             center=(W // 2, 530))
        text(surf, "Examples:   " + self.examples[self.sel], 38, WHITE, center=(W // 2, 580))
        text(surf, "LEFT / RIGHT or 1-5 to choose,  ENTER to start", 32, (210, 200, 240),
             center=(W // 2, H - 40), ow=2)


class Select(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.sel = 0
        self.bg = starfield_bg((10, 10, 40), (60, 20, 70))
        self.actors = [Actor(fd, 0, 1, 0.82) for fd in ROSTER]
        for i, a in enumerate(self.actors):
            a.anim.update(i * 0.35)
        self.cards = [pygame.Rect(70 + i * 290, 120, 270, 400) for i in range(4)]
        self.phase = "choose"
        self.roll_t = 0.0
        self.roll_idx = 0
        self.cpu = None
        self.fx = Effects()

    def choose(self):
        self.phase = "cpu"
        self.game.audio.play("confirm")
        a = self.actors[self.sel]
        a.play("victory")
        self.others = [i for i in range(4) if i != self.sel]
        self.cpu = random.choice(self.others)
        self.step_i = 0
        self.next_step = 0.0
        self.roll_idx = self.others[0]

    def handle(self, ev):
        g = self.game
        if self.phase != "choose":
            if self.phase == "done" and ((ev.type == pygame.KEYDOWN and ev.key in CONFIRM) or
                                         (ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1)):
                self.start()
            return
        if ev.type == pygame.KEYDOWN:
            if ev.key in (pygame.K_LEFT, pygame.K_a):
                self.sel = (self.sel - 1) % 4
                g.audio.play("select")
            elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                self.sel = (self.sel + 1) % 4
                g.audio.play("select")
            elif ev.unicode in ("1", "2", "3", "4"):
                self.sel = int(ev.unicode) - 1
                g.audio.play("select")
            elif ev.key in CONFIRM:
                self.choose()
            elif ev.key == pygame.K_ESCAPE:
                g.goto(Difficulty(g))
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            for i, r in enumerate(self.cards):
                if r.collidepoint(ev.pos):
                    if self.sel == i:
                        self.choose()
                    else:
                        self.sel = i
                        g.audio.play("select")

    def start(self):
        self.game.start_tournament(ROSTER[self.sel], ROSTER[self.cpu])

    def update(self, dt):
        super().update(dt)
        for a in self.actors:
            a.update(dt)
        self.fx.update(dt)
        if self.phase == "cpu":
            self.roll_t += dt
            if self.roll_t >= self.next_step:
                self.step_i += 1
                self.roll_idx = self.others[self.step_i % 3]
                self.game.audio.play("select")
                self.next_step = self.roll_t + 0.06 + 0.025 * self.step_i
                if self.step_i >= 12 and self.roll_idx == self.cpu:
                    self.phase = "done"
                    self.done_t = 0.0
                    self.actors[self.cpu].play("victory")
                    self.game.audio.play("fight")
                    r = self.cards[self.cpu]
                    for _ in range(40):
                        a = random.uniform(0, math.tau)
                        sp = random.uniform(100, 400)
                        self.fx.add(Particle(r.centerx, r.centery, math.cos(a) * sp, math.sin(a) * sp,
                                             0.8, ROSTER[self.cpu].theme, 6, 300, "star"))
        elif self.phase == "done":
            self.done_t += dt
            if self.done_t > 2.6:
                self.start()

    def draw(self, surf):
        surf.blit(self.bg, (0, 0))
        title = "CHOOSE YOUR FIGHTER" if self.phase == "choose" else "THE CPU IS CHOOSING..."
        if self.phase == "done":
            title = f"CPU CHOOSES {ROSTER[self.cpu].name.upper()}!"
        text(surf, title, 80, GOLD, center=(W // 2, 60), ow=5)
        for i, (r, a) in enumerate(zip(self.cards, self.actors)):
            fd = a.fd
            is_p = i == self.sel
            is_c = self.phase != "choose" and i == self.roll_idx
            rr = r.inflate(14, 14) if (is_p or is_c) else r
            border = GOLD if is_p else (RED if is_c else (120, 120, 150))
            bgc = fd.theme if (is_p or is_c) else darker(fd.theme, 0.35)
            panel(surf, rr, darker(bgc, 0.55), 235, border, 18, 5 if (is_p or is_c) else 2)
            if is_p or is_c:
                glow = pygame.Surface(rr.size, pygame.SRCALPHA)
                pygame.draw.circle(glow, (*fd.theme, 70), (rr.w // 2, rr.h // 2 + 20), 120)
                surf.blit(glow, rr.topleft)
            text(surf, DISPLAY[fd.op], 110, lighter(fd.theme, 0.3), center=(rr.right - 46, rr.y + 56), ow=4)
            a.x = rr.centerx - 10
            clip = surf.get_clip()
            surf.set_clip(rr.inflate(-6, -6))
            a.draw(surf, rr.bottom - 80)
            surf.set_clip(clip)
            text(surf, fd.name.upper(), 36, WHITE, center=(rr.centerx, rr.bottom - 52), ow=3)
            text(surf, OP_NAMES[fd.op].upper(), 28, lighter(fd.theme, 0.4), center=(rr.centerx, rr.bottom - 22), ow=2)
            if is_p:
                text(surf, "YOU", 40, GOLD, midleft=(rr.x + 14, rr.y + 30), ow=3)
            if is_c:
                text(surf, "CPU", 40, RED, midleft=(rr.x + 14, rr.y + 30), ow=3)
        fd = ROSTER[self.sel]
        panel(surf, (70, 545, W - 140, 120), (10, 10, 30), 210, fd.theme)
        text(surf, f"{fd.name} - {fd.title}", 44, lighter(fd.theme, 0.3), midleft=(96, 578))
        text(surf, fd.bio, 32, WHITE, midleft=(96, 618))
        text(surf, f"Attacks and counters with {OP_NAMES[fd.op].upper()}.  Special move: {fd.special}", 28,
             (220, 220, 240), midleft=(96, 648), ow=2)
        self.fx.draw(surf)
        if self.phase == "choose":
            text(surf, "LEFT / RIGHT to choose,  ENTER to fight!", 30, (210, 200, 240),
                 center=(W // 2, H - 22), ow=2)


class Versus(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.p = Actor(game.player, 300, 1, 1.25)
        self.c = Actor(game.opponents[game.stage], 980, -1, 1.25)
        self.stage = STAGES[game.stage]
        self.bg_p = game.player.theme
        self.bg_c = game.opponents[game.stage].theme
        game.audio.play("fight")

    def handle(self, ev):
        if self.t > 0.8 and ((ev.type == pygame.KEYDOWN and ev.key in CONFIRM) or
                             (ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1)):
            self.game.start_battle()

    def update(self, dt):
        super().update(dt)
        self.p.update(dt)
        self.c.update(dt)
        if self.t > 4.0:
            self.game.start_battle()

    def draw(self, surf):
        k = min(1.0, self.t / 0.4)
        surf.fill(darker(self.bg_c, 0.5))
        off = int((1 - k) * 700)
        fill_poly(surf, [(-off, 0), (W * 0.58 - off, 0), (W * 0.42 - off, H), (-off, H)], darker(self.bg_p, 0.5))
        for i in range(12):
            y = (i * 70 + self.t * 300) % (H + 60) - 30
            pygame.draw.line(surf, darker(self.bg_p, 0.65), (0 - off, y), (W * 0.45 - off, y), 6)
            y2 = (i * 70 - self.t * 300) % (H + 60) - 30
            pygame.draw.line(surf, darker(self.bg_c, 0.65), (W * 0.55 + off, y2), (W + off, y2), 6)
        self.p.x = 300 - off
        self.c.x = 980 + off
        self.p.draw(surf, 650)
        self.c.draw(surf, 650)
        g = self.game
        text(surf, g.player.name.upper(), 56, WHITE, center=(300 - off, 680), ow=4)
        text(surf, self.c.fd.name.upper(), 56, WHITE, center=(980 + off, 680), ow=4)
        s = 1 + 0.08 * math.sin(self.t * 8)
        text(surf, "VS", int(170 * s), GOLD, center=(W // 2, H // 2), outline=(120, 20, 20), ow=8)
        label = "FINAL STAGE" if g.stage == 3 else f"STAGE {g.stage + 1} of 4"
        panel(surf, (W // 2 - 330, 20, 660, 120), (10, 10, 30), 220, GOLD)
        text(surf, label, 52, GOLD, center=(W // 2, 56))
        text(surf, f"{self.stage.name}  -  {self.stage.location}", 36, WHITE, center=(W // 2, 106))


class GameOver(Scene):
    def __init__(self, game):
        super().__init__(game)
        game.audio.stop_music()

    def handle(self, ev):
        if ev.type == pygame.KEYDOWN:
            if ev.key in CONFIRM:
                self.game.audio.play("confirm")
                self.game.goto(Versus(self.game))
            elif ev.key == pygame.K_ESCAPE:
                self.game.to_title()
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if ev.pos[1] < H - 140:
                self.game.goto(Versus(self.game))
            else:
                self.game.to_title()

    def draw(self, surf):
        surf.fill((15, 5, 20))
        k = min(1.0, self.t / 0.6)
        text(surf, "GAME OVER", int(140 * (0.6 + 0.4 * k)), RED, center=(W // 2, 200), ow=7)
        text(surf, "Don't give up! Every math champion keeps practicing.", 40, WHITE, center=(W // 2, 320))
        st = self.game.stats
        text(surf, f"Correct answers: {st['correct']} / {st['asked']}", 40, GOLD, center=(W // 2, 380))
        if blink(self.t):
            text(surf, "Press ENTER to try this stage again", 50, GREEN, center=(W // 2, 490))
        text(surf, "ESC for the title screen", 36, (200, 200, 220), center=(W // 2, 600))


def draw_trophy(surf, cx, cy, t):
    gold, dark = (255, 200, 50), (190, 130, 20)
    fill_poly(surf, [(cx - 90, cy - 150), (cx + 90, cy - 150), (cx + 70, cy - 40), (cx + 25, cy),
                     (cx - 25, cy), (cx - 70, cy - 40)], gold)
    fill_poly(surf, [(cx + 20, cy - 150), (cx + 90, cy - 150), (cx + 70, cy - 40), (cx + 25, cy)], dark)
    for s in (-1, 1):
        pygame.draw.arc(surf, gold, (cx + s * 95 - 40, cy - 140, 80, 80),
                        math.radians(-90 if s > 0 else 90), math.radians(90 if s > 0 else 270), 10)
    pygame.draw.rect(surf, gold, (cx - 14, cy, 28, 50))
    pygame.draw.rect(surf, dark, (cx - 60, cy + 50, 120, 30), border_radius=6)
    pygame.draw.rect(surf, (90, 50, 20), (cx - 80, cy + 80, 160, 30), border_radius=6)
    text(surf, "1", 80, WHITE, center=(cx, cy - 90), outline=dark, ow=4)
    a = t * 3
    fill_circle(surf, (cx - 45 + math.cos(a) * 6, cy - 120), 8, (255, 255, 230))


class Champion(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.actor = Actor(game.player, 330, 1, 1.2)
        self.actor.play("victory")
        self.fx = Effects()
        self.bg = starfield_bg((10, 10, 50), (60, 30, 90))
        game.audio.play_music("menu")
        game.audio.play("confirm")

    def handle(self, ev):
        if self.t > 1.0 and ((ev.type == pygame.KEYDOWN and ev.key in CONFIRM) or
                             (ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1)):
            self.game.goto(Credits(self.game))

    def update(self, dt):
        super().update(dt)
        self.actor.update(dt)
        self.fx.update(dt)
        if random.random() < dt * 2.5:
            x, y = random.uniform(150, W - 150), random.uniform(80, 350)
            col = random.choice([(255, 90, 90), (255, 220, 80), (90, 200, 255), (200, 120, 255), (120, 255, 150)])
            for _ in range(50):
                a = random.uniform(0, math.tau)
                sp = random.uniform(60, 320)
                self.fx.add(Particle(x, y, math.cos(a) * sp, math.sin(a) * sp, random.uniform(0.8, 1.4), col,
                                     random.uniform(2, 4), 120))
            self.game.audio.play("block")

    def draw(self, surf):
        surf.blit(self.bg, (0, 0))
        draw_rays(surf, (900, 380), self.t, (255, 220, 120), 20, 30)
        self.fx.draw(surf)
        pygame.draw.rect(surf, (40, 25, 60), (0, 650, W, 70))
        self.actor.draw(surf, 650)
        draw_trophy(surf, 900, 450, self.t)
        text(surf, "CONGRATULATIONS!", 70, GOLD, center=(W // 2, 70), ow=5)
        text(surf, "MATH TOURNAMENT CHAMPION!", 84, WHITE, center=(W // 2, 145), outline=(140, 60, 20), ow=6)
        st = self.game.stats
        pct = int(100 * st["correct"] / st["asked"]) if st["asked"] else 0
        text(surf, f"{self.game.player.name}  -  Level {self.game.level}", 40, lighter(self.game.player.theme, 0.3),
             center=(900, 590))
        text(surf, f"Correct answers: {st['correct']} / {st['asked']}  ({pct}%)", 36, WHITE, center=(900, 630))
        if blink(self.t) and self.t > 1.0:
            text(surf, "Press ENTER", 40, GREEN, center=(900, 690))


class Credits(Scene):
    LINES = [("MATH FIGHTER", 96, GOLD), ("", 40, WHITE), ("Created by", 44, (200, 200, 230)),
             (CREDITS_NAME, 80, WHITE), ("", 30, WHITE), ("and", 44, (200, 200, 230)),
             ("Claude", 80, (255, 170, 110))]

    def __init__(self, game):
        super().__init__(game)
        self.bg = starfield_bg((0, 0, 10), (20, 10, 40))
        self.height = sum(int(s * 1.25) for _, s, _ in self.LINES)
        self.scroll_time = 9.0

    def handle(self, ev):
        if (ev.type == pygame.KEYDOWN and ev.key in CONFIRM) or \
                (ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1):
            if self.t < self.scroll_time:
                self.t = self.scroll_time
            else:
                g = self.game
                old = g.level
                g.level = min(MAX_LEVEL, g.level + 1)
                msg = (f"Champion! Now try level {g.level}!" if g.level > old
                       else "You beat the hardest level! Play again?")
                g.audio.play("confirm")
                g.goto(Difficulty(g, msg))

    def draw(self, surf):
        surf.blit(self.bg, (0, 0))
        if self.t < self.scroll_time:
            k = self.t / self.scroll_time
            y = H + 40 - k * (H / 2 + self.height / 2 + 40)
            y = max(y, H / 2 - self.height / 2)
            for line, size, col in self.LINES:
                if line:
                    text(surf, line, size, col, center=(W // 2, int(y + size / 2)), ow=3)
                y += int(size * 1.25)
        else:
            k = min(1.0, (self.t - self.scroll_time) / 1.5)
            col = mix((0, 0, 10), WHITE, k)
            text(surf, "THE END", 150, col, center=(W // 2, H // 2 - 40), outline=(0, 0, 0), ow=4)
            if k >= 1 and blink(self.t):
                text(surf, "Press ENTER to continue", 50, GOLD, center=(W // 2, H // 2 + 100))
