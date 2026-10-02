import sys
from pathlib import Path
from .config_parser import ConfigParser
from .controller import GameController


def main() -> None:
    """Entry point for the Pac-Man game."""
    argv = sys.argv
    if len(argv) != 2:
        print(
            "Usage: 'make run' "
            "or 'uv run python -m src.pac_man config.json'"
        )
        return

    try:
        config = ConfigParser(path=Path(argv[1]))
    except Exception as e:
        print(f"[ERROR] Could not load config: {e}")
        return

    game = GameController(config_data=config.data)
    game.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception:
        sys.exit(1)
