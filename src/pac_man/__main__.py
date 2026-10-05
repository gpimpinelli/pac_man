"""Main entry point execution for the Pac-Man package."""

import sys
from pathlib import Path
from .config_parser import ConfigParser
from .controller import GameController


def main() -> None:
    """Validate command line arguments, load configuration, and start game."""
    argv = sys.argv
    if len(argv) == 2:
        config_path = Path(argv[1])
    elif len(argv) == 1 and Path("config.json").exists():
        config_path = Path("config.json")
    else:
        print(
            "Usage: pac-man <config.json>\n"
            "   or: python3 -m pac_man <config.json>\n"
            "   or: make run"
        )
        return

    try:
        config = ConfigParser(path=config_path)
        game = GameController(config_data=config.data)
        game.run()
    except Exception as e:
        print(f"[FATAL ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception:
        sys.exit(1)
