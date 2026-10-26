"""Renders assets/icon.png (used for the Android and desktop builds)."""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pygame  # noqa: E402

from mathfighter.characters import ROSTER  # noqa: E402
from mathfighter.ui import portrait, text  # noqa: E402

pygame.init()
size = 512
icon = pygame.Surface((size, size), pygame.SRCALPHA)
pygame.draw.rect(icon, (255, 120, 40), icon.get_rect(), border_radius=90)
pygame.draw.rect(icon, (255, 255, 255), icon.get_rect(), 14, border_radius=90)
icon.blit(portrait(ROSTER[0], 440), (36, 20))
text(icon, "+ − × ÷", 110, (255, 230, 80), center=(size // 2, size - 70), ow=6)
out = os.path.join(os.path.dirname(__file__), "..", "assets", "icon.png")
pygame.image.save(icon, out)
print("wrote", os.path.normpath(out))
