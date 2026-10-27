"""The four fighters, plus the final boss Ninja Ryu."""

from dataclasses import dataclass

from .mathq import ADD, DIV, MIX, MUL, SUB


@dataclass(frozen=True)
class Fighter:
    key: str
    name: str
    title: str
    op: str
    female: bool
    hair_style: str          # spiky | swept | long | twintails | hood
    bio: str
    special: str
    theme: tuple             # UI color
    skin: tuple
    hair: tuple
    eyes: tuple
    top: tuple               # shirt / jacket / gi
    top2: tuple              # secondary outfit color
    pants: tuple
    boots: tuple
    accent: tuple            # headband / scarf / sash / ribbons
    height: float = 1.0
    boss: bool = False


KAI = Fighter(
    key="kai", name="Kai Blaze", title="The Addition Ace", op=ADD, female=False,
    hair_style="spiky", special="Plus Blaster",
    bio="A fiery dojo champion. He piles up numbers faster than anyone!",
    theme=(255, 120, 40), skin=(250, 214, 180), hair=(235, 70, 35), eyes=(150, 60, 20),
    top=(250, 140, 40), top2=(255, 240, 220), pants=(250, 140, 40), boots=(60, 45, 40),
    accent=(220, 30, 40), height=1.0)

DAX = Fighter(
    key="dax", name="Dax Steel", title="The Subtraction Knight", op=SUB, female=False,
    hair_style="swept", special="Minus Slash",
    bio="A cool city guardian. He takes away his rival's power, one number at a time.",
    theme=(60, 140, 255), skin=(214, 166, 126), hair=(40, 50, 110), eyes=(40, 120, 220),
    top=(40, 70, 150), top2=(190, 205, 225), pants=(35, 40, 70), boots=(25, 25, 35),
    accent=(240, 245, 255), height=1.05)

LUNA = Fighter(
    key="luna", name="Luna Shade", title="The Division Ninja", op=DIV, female=True,
    hair_style="long", special="Split Shuriken",
    bio="A silent moonlight ninja. She splits every problem into equal parts!",
    theme=(170, 90, 255), skin=(252, 222, 200), hair=(205, 195, 245), eyes=(140, 60, 220),
    top=(80, 45, 130), top2=(40, 25, 70), pants=(60, 35, 100), boots=(30, 20, 45),
    accent=(230, 40, 80), height=0.97)

MIRA = Fighter(
    key="mira", name="Mira Nova", title="The Multiplication Star", op=MUL, female=True,
    hair_style="twintails", special="Times Tornado",
    bio="A super star from the sky. Her power multiplies with every hit!",
    theme=(255, 80, 170), skin=(255, 226, 205), hair=(255, 105, 180), eyes=(30, 170, 160),
    top=(40, 190, 180), top2=(255, 255, 255), pants=(255, 90, 160), boots=(255, 255, 255),
    accent=(255, 220, 60), height=0.95)

ROSTER = [KAI, LUNA, DAX, MIRA]


# Final boss (stage 4). Not selectable.
RYU = Fighter(
    key="ryu", name="Ninja Ryu", title="The Grand Master", op=MIX, female=False,
    hair_style="hood", special="Four Storm Strike",
    bio="Master of the Math Tournament. He strikes with all four kinds of math!",
    theme=(220, 40, 50), skin=(236, 198, 162), hair=(34, 32, 42), eyes=(245, 185, 40),
    top=(44, 44, 56), top2=(96, 96, 112), pants=(38, 38, 48), boots=(26, 26, 32),
    accent=(215, 30, 45), height=1.08, boss=True)
