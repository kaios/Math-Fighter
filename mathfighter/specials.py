"""Each fighter's own special move, and the cut-in banner that announces it.

tier 1 = special (fast answer), tier 2 = super (very fast answer): the same move,
but bigger. Every move travels from the attacker to the target, calls on_arrive
once when it connects, and then finishes. They live in Effects.projectiles.
"""

import math
import random

import pygame

from .draw import add_glow, fill_poly, lighter
from .effects import Particle
from .ui import portrait, text, text_img


class Special:
    def __init__(self, x, y, target_x, direction, color, tier, on_arrive):
        self.x0, self.y = x, y
        self.x = x
        self.target_x, self.dir = target_x, direction
        self.color, self.tier, self.on_arrive = color, tier, on_arrive
        self.arrived = False
        self.t = 0.0

    speed = 900
    linger = 0.0        # seconds it stays visible after hitting

    @property
    def progress(self):
        d = abs(self.target_x - self.x0) or 1
        return min(1.0, abs(self.x - self.x0) / d)

    def update(self, dt, fx):
        self.t += dt
        if not self.arrived:
            self.x += self.speed * dt * self.dir
            self.fly(dt, fx)
            if (self.x - self.target_x) * self.dir >= 0:
                self.x = self.target_x
                self.arrived = True
                self.arrive_t = self.t
                self.on_arrive()
        return not self.arrived or self.t - self.arrive_t < self.linger

    def fly(self, dt, fx):
        pass

    def draw(self, surf):
        pass


def _star(cx, cy, r, ang, points=4, inner=0.3):
    pts = []
    for i in range(points * 2):
        a = ang + i * math.pi / points
        rr = r if i % 2 == 0 else r * inner
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    return pts


def _cross(cx, cy, r, ang, w=0.3):
    """A + shape (turned 45 degrees it is a ×)."""
    pts = []
    for i in range(4):
        a = ang + i * math.pi / 2
        c, s = math.cos(a), math.sin(a)
        for fx, fy in ((w, -w), (1, -w), (1, w)):
            pts.append((cx + (fx * c - fy * s) * r, cy + (fx * s + fy * c) * r))
    return pts


class PlusBlaster(Special):
    """Kai: spinning blazing plus signs."""
    speed = 980

    def __init__(self, *a):
        super().__init__(*a)
        self.size = 46 if self.tier < 2 else 66
        self.trail = []

    def fly(self, dt, fx):
        self.trail = ([(self.x, self.y)] + self.trail)[:12]
        for _ in range(3 if self.tier < 2 else 6):
            fx.add(Particle(self.x, self.y + random.uniform(-26, 26), -self.dir * random.uniform(60, 240),
                            random.uniform(-70, 40), random.uniform(0.25, 0.5),
                            random.choice([(255, 210, 90), (255, 130, 40), (255, 240, 180)]),
                            random.uniform(4, 9), -120))

    def draw(self, surf):
        for i, (x, y) in enumerate(self.trail):
            k = 1 - i / max(1, len(self.trail))
            if i % 3 == 0:
                fill_poly(surf, _cross(x, y, self.size * 0.55 * k, self.t * 9), (255, 130, 40))
        add_glow(surf, (self.x, self.y), self.size * 3, (150, 80, 20))
        fill_poly(surf, _cross(self.x, self.y, self.size, self.t * 9, 0.34), (255, 140, 40))
        fill_poly(surf, _cross(self.x, self.y, self.size * 0.72, self.t * 9, 0.22), (255, 244, 200))


class SplitShuriken(Special):
    """Luna: one shuriken divides in flight into 2, then 4 (8 for the super)."""
    speed = 760

    def blades(self):
        k = self.progress
        n = 1 if k < 0.3 else 2 if k < 0.6 else (4 if self.tier < 2 else 8)
        spread = 150 if self.tier < 2 else 210
        # they fan out, then close in together on the target
        s = math.sin(min(1.0, k) * math.pi) * spread
        for i in range(n):
            off = 0 if n == 1 else (i / (n - 1) - 0.5) * 2
            yield self.x - abs(off) * 60 * self.dir * (1 - k), self.y + off * s

    def fly(self, dt, fx):
        for x, y in self.blades():
            if random.random() < 0.6:
                fx.add(Particle(x, y, -self.dir * random.uniform(30, 120), random.uniform(-30, 30), 0.3,
                                (205, 160, 255), random.uniform(3, 5)))

    def draw(self, surf):
        r = 30 if self.tier < 2 else 38
        for x, y in self.blades():
            add_glow(surf, (x, y), r * 2.2, (90, 40, 150))
            fill_poly(surf, _star(x, y, r, self.t * 20), (225, 225, 240))
            fill_poly(surf, _star(x, y, r * 0.55, self.t * 20 + 0.4), (170, 90, 255))


class MinusSlash(Special):
    """Dax: a blade of light (a long minus sign) cuts across the arena."""
    speed = 2100
    linger = 0.3

    def fly(self, dt, fx):
        for _ in range(5):
            fx.add(Particle(self.x, self.y + random.uniform(-16, 16), self.dir * random.uniform(100, 500),
                            random.uniform(-50, 50), 0.3, (190, 225, 255), random.uniform(3, 5), 0, "streak"))

    def bars(self):
        return (0,) if self.tier < 2 else (-70, 0, 70)

    def draw(self, surf):
        fade = 1.0
        if self.arrived:
            fade = max(0.0, 1 - (self.t - self.arrive_t) / self.linger)
        tip = self.x + (60 + (1 - fade) * 200) * self.dir
        for dy in self.bars():
            y = self.y + dy
            h = 15 * fade + 2
            a = (self.x0, y)
            b = (tip, y)
            add_glow(surf, b, 90, (40, 90, 170))
            fill_poly(surf, [(a[0], y - 1), (b[0] - 40 * self.dir, y - h), (b[0], y),
                             (b[0] - 40 * self.dir, y + h), (a[0], y + 1)], (90, 170, 255))
            fill_poly(surf, [(a[0], y), (b[0] - 30 * self.dir, y - h * 0.45), (b[0], y),
                             (b[0] - 30 * self.dir, y + h * 0.45)], (240, 250, 255))


class TimesTornado(Special):
    """Mira: a whirling tornado full of × signs rolls across the floor."""
    speed = 620
    linger = 0.15

    def __init__(self, *a):
        super().__init__(*a)
        self.big = 1.0 if self.tier < 2 else 1.35

    def fly(self, dt, fx):
        fx.add(Particle(self.x + random.uniform(-30, 30), self.base() + 8, random.uniform(-90, 90),
                        random.uniform(-160, -40), 0.4, (255, 190, 225), random.uniform(3, 6), 200))

    def base(self):
        return self.y + 140

    def draw(self, surf):
        rings = 11
        h = 290 * self.big
        base = self.base()
        add_glow(surf, (self.x, base - h / 2), 170 * self.big, (90, 25, 60))
        for i in range(rings):
            k = i / (rings - 1)
            w = (26 + 170 * k * k) * self.big
            sway = math.sin(self.t * 7 + k * 5) * 14
            rect = pygame.Rect(0, 0, int(w), int(w * 0.28 + 6))
            rect.center = (int(self.x + sway), int(base - k * h))
            col = lighter(self.color, 0.2 + 0.5 * (i % 2))
            pygame.draw.ellipse(surf, col, rect, 4)
        n = 6 if self.tier < 2 else 10
        for i in range(n):
            k = (i + 0.5) / n
            a = self.t * 11 + i * 2.1
            w = (20 + 85 * k * k) * self.big
            x = self.x + math.cos(a) * w
            y = base - k * h + math.sin(a) * w * 0.2
            fill_poly(surf, _cross(x, y, 17, math.pi / 4 + self.t * 6, 0.28), (255, 255, 255))


class FourStorm(Special):
    """Ninja Ryu: all four math symbols circle him, then strike one by one."""
    speed = 700
    SYMS = ("+", "−", "×", "÷")
    COLS = ((255, 150, 60), (90, 170, 255), (255, 90, 180), (180, 110, 255))

    def spots(self):
        k = self.progress
        for i, (sym, col) in enumerate(zip(self.SYMS, self.COLS)):
            a = self.t * 7 + i * math.pi / 2
            r = 95 * (1 - k) + 12
            lag = i * 42 * (1 - k)
            yield (self.x - lag * self.dir + math.cos(a) * r, self.y + math.sin(a) * r * 0.8, sym, col)

    def fly(self, dt, fx):
        for x, y, _, col in self.spots():
            if random.random() < 0.5:
                fx.add(Particle(x, y, random.uniform(-50, 50), random.uniform(-50, 50), 0.3,
                                lighter(col, 0.4), random.uniform(3, 6)))

    def draw(self, surf):
        for x, y, sym, col in self.spots():
            add_glow(surf, (x, y), 72, tuple(c // 2 for c in col))
            img = text_img(sym, 70, (255, 255, 255), col, 4)
            surf.blit(img, img.get_rect(center=(x, y)))


MOVES = {"kai": PlusBlaster, "luna": SplitShuriken, "dax": MinusSlash, "mira": TimesTornado, "ryu": FourStorm}


def make_special(key, *args):
    return MOVES[key](*args)


class CutIn:
    """Freeze-frame banner: the fighter's face and the name of the move."""
    TIME = 0.8

    def __init__(self, fd, tier, side=1):
        self.fd, self.tier, self.side = fd, tier, side
        self.t = 0.0
        self.face = portrait(fd, 300, 215).copy()
        # fade the bottom of the picture away instead of a hard cut
        fade = pygame.Surface(self.face.get_size(), pygame.SRCALPHA)
        fh = self.face.get_height()
        for y in range(fh):
            a = 255 if y < fh * 0.6 else int(255 * (1 - (y - fh * 0.6) / (fh * 0.4)))
            pygame.draw.line(fade, (255, 255, 255, a), (0, y), (self.face.get_width(), y))
        self.face.blit(fade, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        if side < 0:
            self.face = pygame.transform.flip(self.face, True, False)
        self.dim = None

    @property
    def done(self):
        return self.t >= self.TIME

    def update(self, dt):
        self.t += dt

    def draw(self, surf):
        w, h = surf.get_size()
        t = self.t
        ein = min(1.0, t / 0.14)
        eout = min(1.0, max(0.0, (self.TIME - t) / 0.12))
        k = (1 - (1 - ein) ** 3) * eout
        if self.dim is None:
            self.dim = pygame.Surface((w, h))
        self.dim.set_alpha(int(150 * k))
        surf.blit(self.dim, (0, 0))
        cy, half = 360, int(135 * k)
        slant = 90
        theme = self.fd.theme
        fill_poly(surf, [(0, cy - half + slant), (w, cy - half - slant), (w, cy + half - slant),
                         (0, cy + half + slant)], tuple(c // 2 for c in theme))
        fill_poly(surf, [(0, cy - half + slant - 8), (w, cy - half - slant - 8), (w, cy - half - slant),
                         (0, cy - half + slant)], lighter(theme, 0.5))
        fill_poly(surf, [(0, cy + half + slant), (w, cy + half - slant), (w, cy + half - slant + 8),
                         (0, cy + half + slant + 8)], lighter(theme, 0.5))
        if half < 12:
            return
        for i in range(14):                               # speed lines
            y = cy - half + (i * 37) % (half * 2)
            x = (i * 193 + t * 2600 * self.side) % (w + 300) - 150
            pygame.draw.line(surf, lighter(theme, 0.3), (x, y + 60 - i * 8), (x + 180, y + 60 - i * 8 - 25), 3)
        slide = int((1 - k) * 500) * self.side
        fx = 80 if self.side > 0 else w - 380
        surf.blit(self.face, (fx - slide, cy - 160))
        label = "SUPER SPECIAL!" if self.tier >= 2 else "SPECIAL MOVE!"
        tx = 700 if self.side > 0 else w - 700
        col = (255, 225, 90) if self.tier >= 2 else (255, 255, 255)
        text(surf, label, 52, col, center=(tx + slide, cy - 60), ow=4)
        text(surf, self.fd.special.upper(), 96, (255, 255, 255), center=(tx + slide, cy + 20),
             outline=tuple(c // 3 for c in theme), ow=6)
