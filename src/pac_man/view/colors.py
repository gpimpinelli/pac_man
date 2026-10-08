"""Color constants used across UI rendering and maze graphics."""

from enum import IntEnum


class Colors(IntEnum):
    """Hex RGB color codes for graphical surfaces and text."""

    BACKGROUND = 0x151E2E
    MENU_BG = 0x1F4E5B
    MAZE_WALLS = 0x43658B
    BUTTON_NORMAL = 0x43658B
    BUTTON_HOVER = 0x5C80A6

    INPUT_HOVER = 0xFFEAB7

    PACGUM = 0xD9734E
    AMBRA = 0xE09F3E
    SUPER_PACGUM = 0xC84B5B

    TEXT_DARK = 0x151E2E
    TEXT_WHITE = 0xFFFFFF
