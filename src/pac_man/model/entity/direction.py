"""Direction enumeration and keyboard mapping for Pac-Man."""

from enum import Enum, auto


class Direction(Enum):
    """Represent the four possible movement directions."""

    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()


KEYS_MAP: dict[int, Direction] = {
    65362: Direction.UP,
    119: Direction.UP,
    65364: Direction.DOWN,
    115: Direction.DOWN,
    65361: Direction.LEFT,
    97: Direction.LEFT,
    65363: Direction.RIGHT,
    100: Direction.RIGHT,
}
