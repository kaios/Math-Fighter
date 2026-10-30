"""The four tournament arenas. Static scenery is pre-rendered once; weather,
lights and particles animate on top every frame."""

import math
import random

import pygame
from pygame import gfxdraw

from .config import H, W
from .draw import add_glow, darker, fill_circle, fill_poly, mix, outlined_text, vgradient


def _mountains(surf, rng, base_y, height, color):
    pts = [(0, H)]
    x = 0
    while x <= W + 80:
        pts.append((x, base_y - rng.uniform(0.35, 1.0) * height))
        x += rng.uniform(60, 160)
    pts.append((W, H))
    fill_poly(surf, pts, color)


def _floor(surf, top_y, near, far, line, lines=True):
    h = H - top_y
    for i in range(h):
        pygame.draw.line(surf, mix(far, near, i / h), (0, top_y + i), (W, top_y + i))
    if lines:
        vx = W / 2
        for k in range(-14, 15):
            x2 = vx + k * 150
            pygame.draw.aaline(surf, line, (vx + k * 30, top_y), (x2, H))
        y, gap = top_y, 6
        while y < H:
            pygame.draw.line(surf, line, (0, int(y)), (W, int(y)))
            y += gap
            gap *= 1.45


_vignette = None


def _get_vignette():
    """Darkens the corners a little, which pulls the eye to the fighters."""
    global _vignette
    if _vignette is None:
        small = pygame.Surface((64, 36))
        for y in range(36):
            for x in range(64):
                d = math.hypot((x - 31.5) / 32, (y - 17.5) / 18)
                v = int(255 * (1 - 0.42 * max(0.0, d - 0.55) ** 1.5 / 0.7))
                small.set_at((x, y), (v, v, v))
        _vignette = pygame.transform.smoothscale(small, (W, H))
    return _vignette


def polish(bg, rays=None):
    """Finishing touches on a stage painting: light shafts, a soft focus so the
    scenery sits behind the sharp fighters, and the vignette."""
    if rays:
        (ox, oy), color, count = rays
        low = pygame.Surface((W // 4, H // 4))
        rng = random.Random(4)
        for i in range(count):
            a = math.tau * i / count + rng.uniform(-0.1, 0.1)
            d = rng.uniform(0.05, 0.11)
            pts = [(ox / 4, oy / 4),
                   (ox / 4 + math.cos(a - d) * 500, oy / 4 + math.sin(a - d) * 500),
                   (ox / 4 + math.cos(a + d) * 500, oy / 4 + math.sin(a + d) * 500)]
            pygame.draw.polygon(low, color, pts)
        low.fill((0, 0, 0), (0, 540 // 4, W // 4, H // 4))      # light shafts stay above the floor
        low = pygame.transform.smoothscale(pygame.transform.smoothscale(low, (W // 16, H // 16)), (W, H))
        bg.blit(low, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
    soft = pygame.transform.smoothscale(pygame.transform.smoothscale(bg, (W // 2, H // 2)), (W, H))
    soft.set_alpha(200)
    bg.blit(soft, (0, 0))
    bg.blit(_get_vignette(), (0, 0), special_flags=pygame.BLEND_RGB_MULT)


class Stage:
    name = ""
    location = ""
    music_key = 0
    rim = None        # colour of the stage light on the fighters
    reflect = 0       # strength of the fighters' reflection on the floor
    rays = None       # light shafts: (origin, colour, how many)

    def __init__(self):
        self.rng = random.Random(self.name)
        self.bg = pygame.Surface((W, H))
        self.build(self.bg)
        polish(self.bg, self.rays)
        self.t = 0.0
        self.parts = []

    def build(self, surf):
        pass

    def update(self, dt):
        self.t += dt

    def draw(self, surf, ox=0, oy=0):
        surf.blit(self.bg, (ox * 0.5, oy * 0.5))

    def draw_front(self, surf):
        pass


class SakuraTemple(Stage):
    name = "Sakura Temple"
    location = "Kyoto Mountains, Japan"
    music_key = 0
    rim = (255, 170, 110)
    rays = ((900, 300), (60, 38, 24), 14)

    def build(self, s):
        rng = self.rng
        s.blit(vgradient((W, H), (255, 150, 90), (255, 210, 160)), (0, 0))
        top = vgradient((W, 300), (120, 70, 160), (255, 150, 100))
        s.blit(top, (0, 0))
        fill_circle(s, (900, 300), 120, (255, 236, 170))
        fill_circle(s, (900, 300), 100, (255, 246, 210))
        for i in range(6):  # clouds
            cx, cy = rng.randint(0, W), rng.randint(60, 260)
            for j in range(5):
                fill_circle(s, (cx + j * 40, cy + rng.randint(-10, 10)), rng.randint(22, 40),
                            (255, 190, 170))
        _mountains(s, rng, 420, 200, (170, 100, 150))
        _mountains(s, rng, 470, 130, (130, 70, 120))
        # pagoda
        px, py = 260, 470
        for i in range(5):
            w = 170 - i * 26
            y = py - i * 58
            pygame.draw.rect(s, (90, 40, 60), (px - w // 2 + 20, y - 40, w - 40, 42))
            fill_poly(s, [(px - w // 2 - 30, y - 30), (px + w // 2 + 30, y - 30), (px + w // 2 - 10, y - 55),
                          (px - w // 2 + 10, y - 55)], (60, 25, 45))
        pygame.draw.line(s, (60, 25, 45), (px, py - 290), (px, py - 340), 5)
        # cherry trees
        for tx in (60, 520, 1150):
            pygame.draw.line(s, (80, 45, 50), (tx, 560), (tx + 20, 400), 16)
            pygame.draw.line(s, (80, 45, 50), (tx + 15, 450), (tx + 70, 400), 9)
            for _ in range(40):
                fill_circle(s, (tx + rng.randint(-90, 120), 400 + rng.randint(-90, 40)),
                            rng.randint(16, 30), rng.choice([(255, 170, 200), (255, 190, 215), (240, 140, 180)]))
        # torii gate
        gx = 760
        red = (205, 40, 40)
        pygame.draw.rect(s, red, (gx - 120, 360, 22, 200))
        pygame.draw.rect(s, red, (gx + 98, 360, 22, 200))
        fill_poly(s, [(gx - 170, 345), (gx + 170, 345), (gx + 150, 365), (gx - 150, 365)], (40, 20, 25))
        pygame.draw.rect(s, red, (gx - 150, 365, 300, 18))
        pygame.draw.rect(s, red, (gx - 130, 400, 260, 12))
        _floor(s, 555, (200, 170, 160), (150, 110, 120), (170, 140, 140))

    def update(self, dt):
        super().update(dt)
        if random.random() < dt * 14:
            self.parts.append([random.uniform(-100, W), -10, random.uniform(40, 110), random.uniform(50, 90),
                               random.uniform(0, 6.28)])
        for p in self.parts:
            p[0] += p[2] * dt + math.sin(self.t * 2 + p[4]) * 0.8
            p[1] += p[3] * dt
            p[4] += dt * 3
        self.parts = [p for p in self.parts if p[1] < H]

    def draw_front(self, surf):
        for x, y, _, _, a in self.parts:
            w = 6 * abs(math.cos(a)) + 2
            pygame.draw.polygon(surf, (255, 180, 210), [(x - w, y), (x, y - 4), (x + w, y), (x, y + 4)])


class NeonRooftop(Stage):
    name = "Neon Rooftop"
    location = "Downtown Number City"
    music_key = 1
    rim = (255, 70, 190)
    reflect = 70

    def build(self, s):
        rng = self.rng
        s.blit(vgradient((W, H), (10, 8, 40), (70, 30, 100)), (0, 0))
        for _ in range(140):
            x, y = rng.randint(0, W), rng.randint(0, 380)
            s.set_at((x, y), (255, 255, rng.randint(180, 255)))
        fill_circle(s, (1080, 110), 50, (250, 245, 220))
        fill_circle(s, (1062, 98), 46, (40, 25, 80))
        self.windows = []
        for layer, col in enumerate(((35, 25, 70), (25, 18, 50), (15, 12, 32))):
            x = -20
            while x < W:
                w = rng.randint(60, 130)
                h = rng.randint(160 + layer * 50, 330 + layer * 60) - layer * 90
                top = 560 - h
                pygame.draw.rect(s, col, (x, top, w, h))
                if layer > 0:
                    for wy in range(top + 14, 550, 22):
                        for wx in range(x + 10, x + w - 12, 18):
                            if rng.random() < 0.35:
                                c = rng.choice([(255, 220, 120), (120, 220, 255), (255, 160, 220)])
                                pygame.draw.rect(s, darker(c, 0.5 + layer * 0.25), (wx, wy, 8, 10))
                                if layer == 2 and rng.random() < 0.15:
                                    self.windows.append((wx, wy, c))
                x += w + rng.randint(2, 20)
        # rooftop floor & railing
        _floor(s, 560, (60, 55, 80), (35, 30, 55), (80, 75, 110))
        for x in range(0, W, 40):
            pygame.draw.line(s, (90, 90, 120), (x, 520), (x, 560), 3)
        pygame.draw.line(s, (120, 120, 150), (0, 520), (W, 520), 5)
        pygame.draw.rect(s, (50, 45, 70), (60, 380, 110, 150))
        fill_poly(s, [(50, 380), (180, 380), (115, 340)], (40, 35, 60))
        self.signs = [(outlined_text(90, "+", (255, 255, 255), (255, 60, 150), 5), (330, 200), (255, 60, 150)),
                      (outlined_text(90, "×", (255, 255, 255), (60, 220, 255), 5), (640, 150), (60, 220, 255)),
                      (outlined_text(90, "÷", (255, 255, 255), (180, 90, 255), 5), (930, 230), (180, 90, 255)),
                      (outlined_text(90, "\u2212", (255, 255, 255), (255, 210, 60), 5), (1180, 280), (255, 210, 60))]

    def draw(self, surf, ox=0, oy=0):
        super().draw(surf, ox, oy)
        for i, (img, (x, y), c) in enumerate(self.signs):
            on = math.sin(self.t * 3 + i * 1.7) > -0.85 or (int(self.t * 20) % 2 == 0)
            if on:
                glow = 96 + 12 * math.sin(self.t * 5 + i)
                add_glow(surf, (x, y), glow, tuple(v // 2 for v in c))
                surf.blit(img, img.get_rect(center=(x, y)))
        for i, (wx, wy, c) in enumerate(self.windows):
            if math.sin(self.t * 0.7 + i * 2.3) > 0.6:
                pygame.draw.rect(surf, c, (wx, wy, 8, 10))
        # blimp
        bx = (self.t * 30) % (W + 400) - 200
        pygame.draw.ellipse(surf, (60, 50, 90), (bx, 60, 160, 50))
        pygame.draw.rect(surf, (90, 80, 120), (bx + 60, 105, 40, 12))
        if int(self.t * 2) % 2:
            fill_circle(surf, (bx + 160, 85), 4, (255, 60, 60))


class MagmaCrater(Stage):
    name = "Magma Crater"
    location = "Mount Calculus Volcano"
    music_key = 2
    rim = (255, 120, 30)
    reflect = 35
    rays = ((640, 120), (70, 24, 4), 12)

    def build(self, s):
        rng = self.rng
        s.blit(vgradient((W, H), (60, 10, 20), (230, 90, 40)), (0, 0))
        for _ in range(8):
            cx, cy = rng.randint(0, W), rng.randint(40, 250)
            for j in range(6):
                fill_circle(s, (cx + j * 45, cy + rng.randint(-15, 15)), rng.randint(30, 50), (90, 40, 45))
        # volcano
        fill_poly(s, [(360, 560), (585, 215), (695, 215), (950, 560)], (110, 45, 45))
        fill_poly(s, [(640, 215), (695, 215), (950, 560), (700, 560)], (85, 35, 38))
        fill_poly(s, [(585, 215), (695, 215), (680, 232), (600, 232)], (255, 150, 40))
        for x0, bend in ((612, -1), (648, 1), (668, 1)):  # lava rivers
            pts = []
            for i in range(12):
                k = i / 11
                pts.append((x0 + bend * k * 110 + math.sin(k * 7 + x0) * 14, 230 + k * 300))
            pygame.draw.lines(s, (255, 90, 30), False, pts, 9)
            pygame.draw.lines(s, (255, 200, 80), False, pts, 3)
        _mountains(s, rng, 520, 120, (50, 20, 25))
        _floor(s, 555, (90, 50, 45), (50, 25, 30), (70, 35, 35), lines=False)
        self.cracks = []
        for _ in range(9):
            x, y = rng.randint(0, W), rng.randint(575, 700)
            pts = [(x, y)]
            for _ in range(5):
                x += rng.randint(15, 45)
                y += rng.randint(-10, 10)
                pts.append((x, y))
            self.cracks.append(pts)
        for _ in range(30):
            x, y = rng.randint(0, W), rng.randint(570, 715)
            pygame.draw.ellipse(s, (65, 35, 35), (x, y, rng.randint(20, 60), rng.randint(8, 18)))

    def update(self, dt):
        super().update(dt)
        if random.random() < dt * 30:
            self.parts.append([random.uniform(0, W), H + 5, random.uniform(-20, 20), random.uniform(-120, -50),
                               random.uniform(2, 4), random.uniform(2, 5)])
        for p in self.parts:
            p[0] += p[2] * dt + math.sin(self.t * 3 + p[1] * 0.01) * 0.5
            p[1] += p[3] * dt
            p[4] -= dt
        self.parts = [p for p in self.parts if p[4] > 0]

    def draw(self, surf, ox=0, oy=0):
        super().draw(surf, ox, oy)
        glow = int(180 + 70 * math.sin(self.t * 2))
        for i, pts in enumerate(self.cracks):
            g = int(180 + 70 * math.sin(self.t * 2 + i))
            pygame.draw.lines(surf, (255, g // 2 + 40, 20), False, pts, 5)
            pygame.draw.lines(surf, (255, 230, 120), False, pts, 2)
        # smoke puffs from the crater
        for i in range(5):
            k = (self.t * 0.15 + i / 5) % 1
            fill_circle(surf, (640 + math.sin(k * 6 + i) * 30, 200 - k * 220), 25 + k * 45,
                        mix((120, 70, 70), (180, 110, 100), k))
        fill_circle(surf, (640, 215), 18 + glow // 40, (255, glow // 2 + 60, 40))

    def draw_front(self, surf):
        for x, y, _, _, life, size in self.parts:
            fill_circle(surf, (x, y), size * min(1, life), (255, 160 + int(min(1, life) * 60), 60))


class AuroraPalace(Stage):
    name = "Aurora Ice Palace"
    location = "The Frozen North Pole"
    music_key = 3
    rim = (110, 235, 220)
    reflect = 90
    rays = ((640, -140), (18, 42, 46), 12)

    def build(self, s):
        rng = self.rng
        s.blit(vgradient((W, H), (5, 10, 40), (40, 80, 140)), (0, 0))
        for _ in range(180):
            s.set_at((rng.randint(0, W), rng.randint(0, 400)), (230, 240, 255))
        _mountains(s, rng, 480, 160, (90, 120, 170))
        _mountains(s, rng, 520, 100, (130, 160, 210))
        # ice palace
        ice, ice2 = (170, 210, 245), (120, 170, 220)
        pygame.draw.rect(s, ice2, (470, 300, 340, 260))
        for i, (x, w, h) in enumerate(((440, 70, 330), (770, 70, 330), (590, 100, 400))):
            pygame.draw.rect(s, ice, (x, 560 - h, w, h))
            fill_poly(s, [(x - 10, 560 - h), (x + w + 10, 560 - h), (x + w // 2, 560 - h - 90)], (220, 240, 255))
        for x in range(500, 790, 50):
            pygame.draw.rect(s, (90, 140, 200), (x, 380, 18, 34), border_radius=8)
        pygame.draw.rect(s, (60, 100, 160), (610, 460, 60, 100), border_top_left_radius=30, border_top_right_radius=30)
        # crystals
        for x in (60, 170, 1100, 1220, 980):
            h = rng.randint(90, 180)
            fill_poly(s, [(x - 22, 560), (x, 560 - h), (x + 22, 560)], (180, 230, 255))
            fill_poly(s, [(x, 560), (x, 560 - h), (x + 22, 560)], (130, 190, 240))
        _floor(s, 555, (200, 230, 250), (140, 180, 225), (225, 245, 255))

    def update(self, dt):
        super().update(dt)
        if random.random() < dt * 30:
            self.parts.append([random.uniform(0, W), -5, random.uniform(-20, 20), random.uniform(40, 90),
                               random.uniform(1.5, 3.5), random.uniform(0, 6)])
        for p in self.parts:
            p[0] += p[2] * dt + math.sin(self.t + p[5]) * 0.4
            p[1] += p[3] * dt
        self.parts = [p for p in self.parts if p[1] < H]

    def draw(self, surf, ox=0, oy=0):
        surf.blit(self.bg, (ox * 0.5, oy * 0.5))
        for band, (col, base) in enumerate((((60, 255, 160), 120), ((120, 140, 255), 170), ((200, 90, 255), 210))):
            top, bot = [], []
            for x in range(0, W + 40, 40):
                y = base + math.sin(x * 0.006 + self.t * 0.6 + band) * 40 + math.sin(x * 0.017 - self.t) * 15
                top.append((x, y - 40))
                bot.append((x, y + 30))
            pts = [(int(x), int(y)) for x, y in top + bot[::-1]]
            gfxdraw.filled_polygon(surf, pts, (*col, 45))

    def draw_front(self, surf):
        for x, y, _, _, size, _ in self.parts:
            fill_circle(surf, (x, y), size, (245, 250, 255))


STAGES = [SakuraTemple, NeonRooftop, MagmaCrater, AuroraPalace]
