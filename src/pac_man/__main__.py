import sys
from .config_parser import ConfigParser
from .controller import GameController
from mazegenerator import MazeGenerator

# MazeGenerator(
    # size: tuple[int, int] = (15, 15), 
    # perfect: bool = False, 
    # entry_cell: tuple[int, int] = (0, 0), 
    # exit_cell: tuple[int, int] = (-1, -1), 
    # seed: int = 0
# ) -> None

def main() -> None:
    """Entry point for the Pac-Man game."""
    argv = sys.argv
    if len(argv) != 2:
        print("Usage: 'make run' "
              "or 'uv run python -m src.pac_man config.json'"
        )
        return

    try:
        config = ConfigParser(path=argv[1])
    except Exception as e:
        print(f"[ERROR] Could not load config: {e}")
        return

    game = GameController(config_data=config.data)
    game.run()
    
    #maze = MazeGenerator(seed=42)
    #repr(maze)
    #for line in maze._maze:
    #    print(line)


if __name__ == "__main__":
    main()
    # help(MazeGenerator)