from enum import Enum, auto


class Direction(Enum):
    """Represent the four possible movement directions."""

    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()


KEYS_MAP = {
    65362: Direction.UP,  # Up Arrow
    119: Direction.UP,  # w
    65364: Direction.DOWN,  # Down Arrow
    115: Direction.DOWN,  # s
    65361: Direction.LEFT,  # Left Arrow
    97: Direction.LEFT,  # a
    65363: Direction.RIGHT,  # Right Arrow
    100: Direction.RIGHT,  # d
}
