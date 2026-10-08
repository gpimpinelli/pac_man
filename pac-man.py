#!/usr/bin/env python3
"""Launcher for Pac-Man 42.

Enables launching the game via:
    python3 pac-man.py config.json
as specified in Chapter V.1 of the 42 subject.
"""

import sys
from pathlib import Path

# Add src to sys.path so pac_man is consistently resolved as root package
sys.path.insert(0, str(Path(__file__).parent / "src"))

from pac_man.__main__ import main  # noqa: E402

if __name__ == "__main__":
    main()
