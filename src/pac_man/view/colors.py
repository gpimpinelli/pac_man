from enum import IntEnum


class Colors(IntEnum):
    BACKGROUND = 0x151E2E      # Blu notte molto scuro / lavagna
    MENU_BG = 0x1F4E5B         # Dark Teal
    MAZE_WALLS = 0x43658B      # Blu ardesia medio / denim polveroso
    BUTTON_NORMAL = 0x43658B   # Blu ardesia (colore tasto predefinito)
    BUTTON_HOVER = 0x5C80A6    # Azzurro acciaio chiaro / carta da zucchero (tasto in hover)

    INPUT_HOVER = 0xFFEAB7     # Giallo crema pastello / avorio caldo

    PACGUM = 0xD9734E          # Arancione terracotta caldo / ruggine
    AMBRA = 0xE09F3E          # Giallo ambra dorato (ottimo per pallini normali o punteggio)
    SUPER_PACGUM = 0xC84B5B    # Rosso corallo profondo / lampone (ottimo per super palline o nemici)

    TEXT_DARK = 0x151E2E       # Blu notte (per testo su sfondi chiari)
    TEXT_WHITE = 0xFFFFFF      # Bianco puro (massimo contrasto)