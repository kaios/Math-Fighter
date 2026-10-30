"""Anti-aliased, outlined drawing helpers used by the procedural sprites."""

import math

import pygame
from pygame import gfxdraw

from .config import INK

# Rendering quality. Fighters are drawn at QUALITY["ss"] times the size and scaled
# down, which smooths every edge. The main loop lowers it if a machine is too slow.
QUALITY = {"ss": 2, "skip_aa": False}


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def darker(c, k=0.72):
    return tuple(max(0, int(v * k)) for v in c[:3])


def lighter(c, k=0.35):
    return mix(c, (255, 255, 255), k)


def _ipts(pts):
    return [(int(x + 0.5), int(y + 0.5)) for x, y in pts]


def fill_poly(surf, pts, color):
    if len(pts) < 3:
        return
    p = _ipts(pts)
    gfxdraw.filled_polygon(surf, p, color)
    if not QUALITY["skip_aa"]:      # not needed when the drawing gets scaled down anyway
        gfxdraw.aapolygon(surf, p, color)


def fill_circle(surf, c, r, color):
    x, y, r = int(round(c[0])), int(round(c[1])), max(1, int(round(r)))
    gfxdraw.filled_circle(surf, x, y, r, color)
    if not QUALITY["skip_aa"]:
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

    def __init__(self, surf, ol=2.5, flash=0.0, ink=INK, rim=None):
        self.surf, self.ol, self.flash, self.ink, self.rim = surf, ol, flash, ink, rim

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
        lx, ly = self.LIGHT

        def shifted(k, size):
            return capsule_pts((p1[0] + lx * r1 * k, p1[1] + ly * r1 * k),
                               (p2[0] + lx * r2 * k, p2[1] + ly * r2 * k), r1 * size, r2 * size)

        # coloured stage light along the shadow side, then shadow, base and highlight
        if self.rim:
            fill_poly(self.surf, capsule_pts(p1, p2, r1, r2), mix(darker(col, 0.7), self.rim, 0.75))
            fill_poly(self.surf, shifted(0.09, 0.93), darker(col, 0.78))
        else:
            fill_poly(self.surf, capsule_pts(p1, p2, r1, r2), darker(col, 0.78))
        fill_poly(self.surf, shifted(0.17, 0.82), col)
        fill_poly(self.surf, shifted(0.46, 0.2), lighter(col, 0.2))

    def ribbon(self, points, widths, color, outline=True):
        pts = ribbon_pts(points, widths)
        self.poly(pts, color, outline)
        return pts


_fonts = {}


def get_font(size):
    if size not in _fonts:
        _fonts[size] = pygame.font.Font(None, size)
    return _fonts[size]


def outlined_text(size, text, color, outline=(0, 0, 0), width=3):
    """Text with an outline. Rendered at twice the size and scaled down, which
    gives smooth edges and even letter spacing."""
    font = get_font(size * 2)
    base = font.render(text, True, color)
    w2 = width * 2
    if not width:
        return pygame.transform.smoothscale(base, (max(1, base.get_width() // 2),
                                                   max(1, base.get_height() // 2)))
    out = font.render(text, True, outline)
    surf = pygame.Surface((base.get_width() + w2 * 2, base.get_height() + w2 * 2), pygame.SRCALPHA)
    step = max(1, w2 // 3)
    for dx in range(-w2, w2 + 1, step):
        for dy in range(-w2, w2 + 1, step):
            if dx * dx + dy * dy <= w2 * w2 + 1:
                surf.blit(out, (dx + w2, dy + w2))
    surf.blit(base, (w2, w2))
    return pygame.transform.smoothscale(surf, (surf.get_width() // 2, surf.get_height() // 2))


_glows = {}


def glow_sprite(radius, color):
    """Soft round light, added to the picture with add_glow."""
    radius = max(4, int(radius) // 4 * 4)
    key = (radius, color)
    img = _glows.get(key)
    if img is None:
        if len(_glows) > 300:
            _glows.clear()
        img = pygame.Surface((radius * 2, radius * 2))
        for r in range(radius, 0, -2):
            k = (1 - r / radius) ** 2
            pygame.draw.circle(img, tuple(int(c * k) for c in color), (radius, radius), r)
        _glows[key] = img
    return img


def add_glow(surf, c, radius, color):
    img = glow_sprite(radius, color)
    surf.blit(img, (c[0] - img.get_width() // 2, c[1] - img.get_height() // 2),
              special_flags=pygame.BLEND_RGB_ADD)


_shadows = {}


def soft_shadow(w, h, alpha=90):
    """Blurred ground shadow."""
    key = (w, h, alpha)
    img = _shadows.get(key)
    if img is None:
        small = pygame.Surface((w, h), pygame.SRCALPHA)
        for i in range(24, 0, -1):
            k = i / 24
            rect = pygame.Rect(0, 0, int(w * k), int(h * k))
            rect.center = (w // 2, h // 2)
            pygame.draw.ellipse(small, (0, 0, 0, int(alpha * (1 - k) ** 0.8)), rect)
        img = pygame.transform.smoothscale(pygame.transform.smoothscale(small, (w // 2, h // 2)), (w, h))
        _shadows[key] = img
    return img


def vgradient(size, top, bottom):
    w, h = size
    surf = pygame.Surface((w, h))
    for y in range(h):
        pygame.draw.line(surf, mix(top, bottom, y / max(1, h - 1)), (0, y), (w, y))
    return surf
