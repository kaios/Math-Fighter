"""Global game constants."""

# Logical resolution. The window is scaled (pygame.SCALED) to any screen size,
# so this also works on phones/tablets in landscape.
W, H = 1280, 720
FPS = 60
TITLE = "Math Fighter"
__version__ = "1.3.0"

# Rules
ANSWER_TIME = 5.0        # seconds to answer each question
COUNTER_WINDOW = 2.5     # answer a defense question this fast to counter attack
BOSS_ANSWER_TIME = 3.0   # seconds to block the final boss (counter window shrinks to match)
TURN_PAUSE = 0.8         # seconds between one exchange and the next question
ROUND_TIME = 99          # seconds per round
MAX_HITS = 8             # 8 strikes and you are out
ROUNDS_TO_WIN = 2        # best of 3
MAX_LEVEL = 5            # Legend; beating it unlocks the bonus level
BONUS_LEVEL = 6          # fractions
FRACTION_ANSWER_TIME = 8.0  # fractions take longer to work out and type

# Arena
GROUND_Y = 610
PLAYER_HOME_X = 490
CPU_HOME_X = 790

# Credits
CREDITS_NAME = "Shawn Rapaz"

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
INK = (24, 18, 32)
GOLD = (255, 205, 60)
RED = (230, 50, 60)
GREEN = (70, 220, 110)
BLUE = (70, 150, 255)
