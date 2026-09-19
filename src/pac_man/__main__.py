import sys
from .map_parser import MapParser
from mazegenerator import MazeGenerator

# MazeGenerator(
    # size: tuple[int, int] = (15, 15), 
    # perfect: bool = False, 
    # entry_cell: tuple[int, int] = (0, 0), 
    # exit_cell: tuple[int, int] = (-1, -1), 
    # seed: int = 0
# ) -> None

def main() -> None:
    argv = sys.argv
    if len(argv) != 2:
        print("Invalid number of argv")
        return 1
    
    parser = MapParser(path=argv[1])
    print(parser.json)
    maze = MazeGenerator(seed=42)
    repr(maze)
    for line in maze._maze:
        print(line)


if __name__ == "__main__":
    main()
    #help(MazeGenerator)