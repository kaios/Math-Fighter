"""Particles, hit sparks, floating text, projectiles and screen shake."""

import math
import random

import pygame

from .draw import fill_circle, fill_poly, lighter, outlined_text


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "size", "grav", "kind",
                 "spin", "ang")

    def __init__(self, x, y, vx, vy, life, color, size, grav=0.0, kind="dot"):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life = self.max_life = life
        self.color, self.size, self.grav, self.kind = color, size, grav, kind
        self.spin = random.uniform(-8, 8)
        self.ang = random.uniform(0, math.tau)

    def update(self, dt):
        self.vy += self.grav * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.ang += self.spin * dt
        self.life -= dt
        return self.life > 0

    def draw(self, surf):
        k = max(0.0, self.life / self.max_life)
        if self.kind == "streak":
            sp = math.hypot(self.vx, self.vy) or 1
            ln = self.size * 3 * k + 2
            x2, y2 = self.x - self.vx / sp * ln, self.y - self.vy / sp * ln
            pygame.draw.line(surf, self.color, (self.x, self.y), (x2, y2), max(1, int(self.size * k)))
        elif self.kind == "ring":
            r = int(self.size * (1.6 - k))
            if r > 1:
                pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), r,
                                   max(1, int(6 * k)))
        elif self.kind == "star":
            r = self.size * (0.4 + 0.6 * k)
            pts = []
            for i in range(8):
                a = self.ang + i * math.pi / 4
                rr = r if i % 2 == 0 else r * 0.35
                pts.append((self.x + math.cos(a) * rr, self.y + math.sin(a) * rr))
            fill_poly(surf, pts, self.color)
        else:
            fill_circle(surf, (self.x, self.y), max(1, self.size * k), self.color)


class Popup:
    def __init__(self, text, x, y, color, font, life=1.0, rise=60):
        self.img = outlined_text(font, text, color, (20, 10, 30), 4)
        self.x, self.y, self.life, self.max_life, self.rise = x, y, life, life, rise

    def update(self, dt):
        self.life -= dt
        return self.life > 0

    def draw(self, surf):
        k = 1 - self.life / self.max_life
        s = 1.0 + 0.6 * max(0.0, 0.15 - k) / 0.15  # pop in
        img = self.img
        if s != 1.0:
            img = pygame.transform.smoothscale(img, (int(img.get_width() * s), int(img.get_height() * s)))
        if self.life < 0.3:
            img = img.copy()
            img.set_alpha(int(255 * self.life / 0.3))
        surf.blit(img, img.get_rect(center=(self.x, self.y - self.rise * k)))


class Projectile:
    """Energy ball carrying the attacker's math symbol."""

    def __init__(self, x, y, target_x, direction, color, symbol, font, on_arrive, passes=False):
        self.x, self.y = x, y
        self.target_x, self.dir = target_x, direction
        self.color, self.symbol = color, outlined_text(font, symbol, (255, 255, 255), color, 3)
        self.on_arrive, self.passes = on_arrive, passes
        self.arrived = False
        self.t = 0.0
        self.trail = []

    def update(self, dt, fx):
        self.t += dt
        self.x += 950 * dt * self.dir
        self.trail = ([(self.x, self.y)] + self.trail)[:10]
        if random.random() < 0.8:
            fx.add(Particle(self.x, self.y + random.uniform(-12, 12), -self.dir * random.uniform(40, 160),
                            random.uniform(-40, 40), 0.35, lighter(self.color, 0.4), 5))
        if not self.arrived and (self.x - self.target_x) * self.dir >= 0:
            self.arrived = True
            self.on_arrive()
            if not self.passes:
                return False
        return -100 < self.x < 1380

    def draw(self, surf):
        for i, (x, y) in enumerate(self.trail[::-1]):
            k = (i + 1) / len(self.trail)
            fill_circle(surf, (x, y), 20 * k, self.color)
        pulse = 1 + 0.12 * math.sin(self.t * 30)
        fill_circle(surf, (self.x, self.y), 30 * pulse, self.color)
        fill_circle(surf, (self.x, self.y), 22 * pulse, lighter(self.color, 0.6))
        surf.blit(self.symbol, self.symbol.get_rect(center=(self.x, self.y)))


class Effects:
    def __init__(self):
        self.parts, self.popups, self.projectiles = [], [], []
        self.shake_t = 0.0
        self.shake_amp = 0.0
        self.flash = 0.0
        self.flash_color = (255, 255, 255)

    def add(self, p):
        self.parts.append(p)

    def shake(self, amp=12, t=0.3):
        self.shake_amp, self.shake_t = max(self.shake_amp, amp), max(self.shake_t, t)

    def screen_flash(self, color=(255, 255, 255), amount=0.6):
        self.flash, self.flash_color = amount, color

    def offset(self):
        if self.shake_t <= 0:
            return 0, 0
        a = self.shake_amp * min(1.0, self.shake_t / 0.3)
        return random.uniform(-a, a), random.uniform(-a, a)

    def hit_spark(self, x, y, color=(255, 230, 120), big=False):
        n = 26 if big else 14
        for _ in range(n):
            a = random.uniform(0, math.tau)
            sp = random.uniform(250, 700 if big else 500)
            self.add(Particle(x, y, math.cos(a) * sp, math.sin(a) * sp, random.uniform(0.2, 0.4),
                              color, random.uniform(3, 6), 600, "streak"))
        for _ in range(6 if big else 3):
            a = random.uniform(0, math.tau)
            sp = random.uniform(60, 220)
            self.add(Particle(x, y, math.cos(a) * sp, math.sin(a) * sp, 0.5, (255, 255, 255),
                              random.uniform(10, 16), 0, "star"))
        self.add(Particle(x, y, 0, 0, 0.3, color, 70 if big else 45, 0, "ring"))

    def block_spark(self, x, y):
        self.hit_spark(x, y, (120, 200, 255))
        self.add(Particle(x, y, 0, 0, 0.35, (180, 230, 255), 60, 0, "ring"))

    def aura(self, x, y, color, spread=60):
        self.add(Particle(x + random.uniform(-spread, spread), y + random.uniform(-10, 30),
                          random.uniform(-15, 15), random.uniform(-260, -120), random.uniform(0.3, 0.6),
                          color, random.uniform(4, 8)))

    def text(self, text, x, y, color, font, life=1.0, rise=60):
        self.popups.append(Popup(text, x, y, color, font, life, rise))

    def update(self, dt):
        self.parts = [p for p in self.parts if p.update(dt)]
        self.popups = [p for p in self.popups if p.update(dt)]
        self.projectiles = [p for p in self.projectiles if p.update(dt, self)]
        self.shake_t = max(0.0, self.shake_t - dt)
        if self.shake_t == 0:
            self.shake_amp = 0
        self.flash = max(0.0, self.flash - dt * 3)

    def draw(self, surf):
        for p in self.projectiles:
            p.draw(surf)
        for p in self.parts:
            p.draw(surf)

    def draw_top(self, surf):
        for p in self.popups:
            p.draw(surf)
        if self.flash > 0:
            ov = pygame.Surface(surf.get_size())
            ov.fill(self.flash_color)
            ov.set_alpha(int(180 * self.flash))
            surf.blit(ov, (0, 0))
