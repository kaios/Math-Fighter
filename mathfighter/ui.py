"""Text, panels, buttons and the touch keypad (for phones / tablets)."""

import pygame

from .config import H, W, WHITE
from .draw import outlined_text
from .sprite import POSES, Rig

_fonts = {}
_text_cache = {}


def font(size):
    if size not in _fonts:
        _fonts[size] = pygame.font.Font(None, size)
    return _fonts[size]


def text_img(s, size, color=WHITE, outline=(15, 10, 25), ow=3):
    key = (s, size, color, outline, ow)
    img = _text_cache.get(key)
    if img is None:
        if len(_text_cache) > 600:
            _text_cache.clear()
        img = outlined_text(font(size), s, color, outline, ow) if ow else font(size).render(s, True, color)
        _text_cache[key] = img
    return img


def text(surf, s, size, color=WHITE, center=None, outline=(15, 10, 25), ow=3, **anchor):
    img = text_img(s, size, color, outline, ow)
    if center is not None:
        anchor = {"center": center}
    r = img.get_rect(**anchor)
    surf.blit(img, r)
    return r


def panel(surf, rect, color=(20, 15, 40), alpha=200, border=(255, 255, 255), radius=16, width=3):
    r = pygame.Rect(rect)
    s = pygame.Surface(r.size, pygame.SRCALPHA)
    pygame.draw.rect(s, (*color, alpha), s.get_rect(), border_radius=radius)
    surf.blit(s, r.topleft)
    if border:
        pygame.draw.rect(surf, border, r, width, border_radius=radius)


_portraits = {}


def portrait(fd, size=96):
    """Head-and-shoulders picture of a fighter, cropped from the rig."""
    key = (fd.key, size)
    if key not in _portraits:
        k = max(1.0, size / 150)  # render big portraits at full detail
        surf = pygame.Surface((int(420 * k), int(520 * k)), pygame.SRCALPHA)
        rig = Rig(fd)
        pose = dict(POSES["stance"])
        pose.update(saf=10, eaf=20, sab=5, eab=20)
        rig.draw(surf, 200 * k, 500 * k, 1, 1.25 * k, pose, t=0.5)
        hx, hy = rig.points["head"]
        crop = pygame.Rect(0, 0, int(150 * k), int(150 * k))
        crop.center = (hx - 2 * k, hy + 18 * k)
        crop = crop.clip(surf.get_rect())
        _portraits[key] = pygame.transform.smoothscale(surf.subsurface(crop), (size, size))
    return _portraits[key]


class Keypad:
    """On-screen number pad. Shown automatically when the game is touched."""

    KEYS = ["7", "8", "9", "4", "5", "6", "1", "2", "3", "DEL", "0"]

    def __init__(self, x=W - 300, y=H - 330, size=88, gap=8):
        self.rects = []
        for i, k in enumerate(self.KEYS):
            r = pygame.Rect(x + (i % 3) * (size + gap), y + (i // 3) * (size * 0.8 + gap), size, int(size * 0.8))
            self.rects.append((k, r))
        self.pressed = None
        self.pressed_t = 0.0

    def hit(self, pos):
        for k, r in self.rects:
            if r.collidepoint(pos):
                self.pressed, self.pressed_t = k, 0.12
                return k
        return None

    def draw(self, surf, dt=0.0):
        self.pressed_t = max(0.0, self.pressed_t - dt)
        for k, r in self.rects:
            down = self.pressed == k and self.pressed_t > 0
            col = (220, 90, 90) if k == "DEL" else (60, 60, 110)
            if down:
                col = tuple(min(255, c + 70) for c in col)
            panel(surf, r, col, 220, WHITE, 12, 2)
            text(surf, k, 44 if len(k) == 1 else 32, center=r.center)


class Button:
    def __init__(self, rect, label, color=(230, 60, 80), size=40):
        self.rect, self.label, self.color, self.size = pygame.Rect(rect), label, color, size

    def hit(self, pos):
        return self.rect.collidepoint(pos)

    def draw(self, surf, pulse=0.0):
        r = self.rect.inflate(int(pulse * 8), int(pulse * 8))
        panel(surf, r, self.color, 230, WHITE, 18, 3)
        text(surf, self.label, self.size, center=r.center)
