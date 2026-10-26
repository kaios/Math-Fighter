"""Anti-aliased, outlined drawing helpers used by the procedural sprites."""

import math

import pygame
from pygame import gfxdraw

from .config import INK


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def darker(c, k=0.72):
    return tuple(max(0, int(v * k)) for v in c[:3])


def lighter(c, k=0.35):
    return mix(c, (255, 255, 255), k)


def _ipts(pts):
    return [(int(round(x)), int(round(y))) for x, y in pts]


def fill_poly(surf, pts, color):
    if len(pts) < 3:
        return
    p = _ipts(pts)
    gfxdraw.filled_polygon(surf, p, color)
    gfxdraw.aapolygon(surf, p, color)


def fill_circle(surf, c, r, color):
    x, y, r = int(round(c[0])), int(round(c[1])), max(1, int(round(r)))
    gfxdraw.filled_circle(surf, x, y, r, color)
    gfxdraw.aacircle(surf, x, y, r, color)


def capsule_pts(p1, p2, r1, r2, steps=7):
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    d = math.hypot(dx, dy) or 0.001
    ux, uy = dx / d, dy / d
    base = math.atan2(uy, ux)
    pts = []
    for i in range(steps + 1):  # cap around p2: from +normal through +dir to -normal
        a = base - math.pi / 2 + math.pi * i / steps
        pts.append((p2[0] + math.cos(a) * r2, p2[1] + math.sin(a) * r2))
    for i in range(steps + 1):  # cap around p1
        a = base + math.pi / 2 + math.pi * i / steps
        pts.append((p1[0] + math.cos(a) * r1, p1[1] + math.sin(a) * r1))
    return pts


def ribbon_pts(points, widths):
    """Tapered strip along a polyline (hair tails, scarves, sashes)."""
    left, right = [], []
    n = len(points)
    for i, (x, y) in enumerate(points):
        a = points[max(0, i - 1)]
        b = points[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 0.001
        nx, ny = -dy / d, dx / d
        w = widths[i] / 2
        left.append((x + nx * w, y + ny * w))
        right.append((x - nx * w, y - ny * w))
    return left + right[::-1]


class Pen:
    """Draws filled shapes with a dark ink outline (cel / anime style).

    `flash` turns every fill white (hit flash). `ol` is outline thickness."""

    LIGHT = (-0.45, -0.65)  # light comes from the upper left

    def __init__(self, surf, ol=2.5, flash=0.0, ink=INK):
        self.surf, self.ol, self.flash, self.ink = surf, ol, flash, ink

    def c(self, color):
        if self.flash > 0:
            return mix(color, (255, 255, 255), self.flash)
        return color

    def poly(self, pts, color, outline=True):
        if outline:
            self.outline_poly(pts)
        fill_poly(self.surf, pts, self.c(color))

    def outline_poly(self, pts):
        w = max(1, int(round(self.ol * 2)))
        p = _ipts(pts)
        pygame.draw.lines(self.surf, self.ink, True, p, w)
        r = self.ol
        for q in p:
            fill_circle(self.surf, q, r, self.ink)

    def circle(self, c, r, color, outline=True):
        if outline:
            fill_circle(self.surf, c, r + self.ol, self.ink)
        fill_circle(self.surf, c, r, self.c(color))

    def chain(self, segs, shade=True):
        """segs: list of (p1, p2, r1, r2, color). Outlines first so joints merge."""
        for p1, p2, r1, r2, _ in segs:
            fill_poly(self.surf, capsule_pts(p1, p2, r1 + self.ol, r2 + self.ol), self.ink)
        for p1, p2, r1, r2, col in segs:
            self.capsule(p1, p2, r1, r2, col, shade)

    def capsule(self, p1, p2, r1, r2, color, shade=True):
        col = self.c(color)
        if not shade:
            fill_poly(self.surf, capsule_pts(p1, p2, r1, r2), col)
            return
        fill_poly(self.surf, capsule_pts(p1, p2, r1, r2), darker(col, 0.78))
        lx, ly = self.LIGHT
        o1, o2 = r1 * 0.28, r2 * 0.28
        fill_poly(self.surf, capsule_pts((p1[0] + lx * o1, p1[1] + ly * o1),
                                         (p2[0] + lx * o2, p2[1] + ly * o2),
                                         r1 * 0.72, r2 * 0.72), col)

    def ribbon(self, points, widths, color, outline=True):
        pts = ribbon_pts(points, widths)
        self.poly(pts, color, outline)
        return pts


def outlined_text(font, text, color, outline=(0, 0, 0), width=3):
    base = font.render(text, True, color)
    out = font.render(text, True, outline)
    w, h = base.get_width() + width * 2, base.get_height() + width * 2
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for dx in range(-width, width + 1):
        for dy in range(-width, width + 1):
            if dx * dx + dy * dy <= width * width + 1:
                surf.blit(out, (dx + width, dy + width))
    surf.blit(base, (width, width))
    return surf


def vgradient(size, top, bottom):
    w, h = size
    surf = pygame.Surface((w, h))
    for y in range(h):
        pygame.draw.line(surf, mix(top, bottom, y / max(1, h - 1)), (0, y), (w, y))
    return surf
