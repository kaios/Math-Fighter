"""Text, panels, buttons and the touch keypad (for phones / tablets)."""

import pygame

from .config import H, W, WHITE
from .draw import get_font, lighter, outlined_text
from .sprite import POSES, Rig

_text_cache = {}
_panels = {}


font = get_font


def text_img(s, size, color=WHITE, outline=(15, 10, 25), ow=3):
    key = (s, size, color, outline, ow)
    img = _text_cache.get(key)
    if img is None:
        if len(_text_cache) > 600:
            _text_cache.clear()
        img = outlined_text(size, s, color, outline, ow)
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
    """Rounded panel with a soft shine on top. Drawn big and scaled down for
    smooth corners, and cached because the same panels come back every frame."""
    r = pygame.Rect(rect)
    key = (r.size, color, alpha, border, radius, width)
    img = _panels.get(key)
    if img is None:
        if len(_panels) > 200:
            _panels.clear()
        w2, h2 = max(2, r.w * 2), max(2, r.h * 2)
        big = pygame.Surface((w2, h2), pygame.SRCALPHA)
        pygame.draw.rect(big, (*color, alpha), big.get_rect(), border_radius=radius * 2)
        sheen = pygame.Surface((w2, h2), pygame.SRCALPHA)
        top = lighter(color, 0.45)
        for y in range(h2 // 2):
            k = 1 - y / (h2 / 2)
            pygame.draw.line(sheen, (*top, int(70 * k * k)), (0, y), (w2, y))
        mask = pygame.Surface((w2, h2), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=radius * 2)
        sheen.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        big.blit(sheen, (0, 0))
        if border:
            pygame.draw.rect(big, border, big.get_rect(), width * 2, border_radius=radius * 2)
        img = pygame.transform.smoothscale(big, r.size)
        _panels[key] = img
    surf.blit(img, r.topleft)


_portraits = {}


def portrait(fd, size=96, crop_size=150):
    """Head-and-shoulders picture of a fighter, cropped from the rig."""
    key = (fd.key, size, crop_size)
    if key not in _portraits:
        k = max(1.0, size / 150)  # render big portraits at full detail
        surf = pygame.Surface((int(420 * k), int(520 * k)), pygame.SRCALPHA)
        rig = Rig(fd)
        pose = dict(POSES["stance"])
        pose.update(saf=10, eaf=20, sab=5, eab=20)
        rig.draw(surf, 200 * k, 500 * k, 1, 1.25 * k, pose, t=0.5)
        hx, hy = rig.points["head"]
        crop = pygame.Rect(0, 0, int(crop_size * k), int(crop_size * k))
        crop.center = (hx - 2 * k, hy + (18 + (crop_size - 150) * 0.2) * k)
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

