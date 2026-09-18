from mazegenerator import MazeGenerator

def main() -> None:
    maze = MazeGenerator()
    repr(maze)
    print(maze.hex())

# MazeGenerator(
    # size: tuple[int, int] = (15, 15), 
    # perfect: bool = False, 
    # entry_cell: tuple[int, int] = (0, 0), 
    # exit_cell: tuple[int, int] = (-1, -1), 
    # seed: int = 0
# ) -> None
if __name__ == "__main__":
    main()
    #help(MazeGenerator)