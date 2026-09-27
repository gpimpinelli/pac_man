"""Adapter module for external MazeGenerator package.

Transforms the external bitmask maze into a Pac-Man compatible grid
with Cell objects, pellets, power pellets, and entity spawn points.
"""

from mazegenerator import MazeGenerator
from dataclasses import dataclass
from enum import IntFlag, auto

class Direction(IntFlag):
    NONE  = 0
    NORTH = auto()  # 1
    EAST  = auto()  # 2
    SOUTH = auto()  # 4
    WEST = auto()   # 8

    ALL_WALLS =  WEST | SOUTH | EAST | NORTH # 15


@dataclass(slots=True)
class Cell:
    """
    Represents a single cell in the Pac-Man maze grid.
    Initializes a cell at grid coordinates (x, y).

    Args:
        x (int): Horizontal coordinate in the grid.
        y (int): Vertical coordinate in the grid.
        wall_code (int): 4-bit wall mask from MazeGenerator.
    """

    coords: tuple[int, int]
    wall_code: Direction = Direction.NONE


    # Gameplay attributes
    has_pacgum: bool = False
    has_super_pacgum: bool = False

    def _has_wall(self, direction: Direction) -> bool:
        return bool(self.wall_code & direction)

    @property
    def has_wall_north(self) -> bool:
        """Returns True if the cell has a wall to the North."""
        return self._has_wall(Direction.NORTH)

    @property
    def has_wall_east(self) -> bool:
        """Returns True if the cell has a wall to the East."""
        return self._has_wall(Direction.EAST)

    @property
    def has_wall_south(self) -> bool:
        """Returns True if the cell has a wall to the South."""
        return self._has_wall(Direction.SOUTH)

    @property
    def has_wall_west(self) -> bool:
        """Returns True if the cell has a wall to the West."""
        return self._has_wall(Direction.WEST)

    @property
    def is_solid(self) -> bool:
        """Returns True if this cell is an obstacle (e.g. 42 logo)."""
        return (self.wall_code & Direction.ALL_WALLS) == Direction.ALL_WALLS

    def remove_gum(self, is_super_gum: bool) -> None:
        if is_super_gum:
            self.has_super_pacgum = False
        else:
            self.has_pacgum = False

class MazeAdapter:
    """Adapts external MazeGenerator to the Pac-Man game domain."""

    def __init__(
        self, width: int = 15, height: int = 15, seed: int = 42
    ) -> None:
        """Initializes the adapter and generates the maze grid.

        Args:
            width (int): Number of horizontal cells.
            height (int): Number of vertical cells.
            seed (int): Seed for maze reproducibility (0 = random).
        """
        self.width: int = width
        self.height: int = height
        self.seed: int = seed

        # Grid of Cell objects: self.grid[y][x]
        self.grid: list[list[Cell]] = []

        # Entity spawn coordinates (x, y)
        self.player_spawn: tuple[int, int] = (0, 0)
        self.ghost_spawns: list[tuple[int, int]] = []

        # Total number of pellets left to eat for winning the level
        self.total_pacgums: int = 0

        self.generate()

    def finish_pacgums(self) -> bool:
        return self.total_pacgums == 0

    def generate(self) -> None:
        """Generates and populates the Pac-Man maze using MazeGenerator."""
        try:
            generator = MazeGenerator(
                size=(self.width, self.height),
                perfect=False,
                seed=self.seed,
            )
            # MazeGenerator init a 2D mtrx of int in ._maze
            raw_maze = generator._maze
        except Exception as e:
            print(f"[MAZE ERROR] Failed to generate maze: {e}")
            # Fallback -> if mazegenerator does not work
            raw_maze = [
                [0 for _ in range(self.width)] for _ in range(self.height)
            ]

        self.grid = []
        for y in range(self.height):
            row: list[Cell] = []
            for x in range(self.width):
                raw_code = raw_maze[y][x]
                # & AND bitwise operator: return 1 if both are 1
                # comparing raw_code(binary value) with ALL_WALL.value(1111)
                wall_code = Direction(raw_code & Direction.ALL_WALLS.value)
                cell = Cell(coords=(x, y), wall_code=wall_code)
                row.append(cell)
            self.grid.append(row)

        # Positions are (x=0, y=0) -> (width, height)
        self.player_spawn = (self.width // 2, self.height // 2)
        self.ghost_spawns = [
            (0, 0),
            (self.width - 1, 0),
            (0, self.height - 1),
            (self.width - 1, self.height - 1)
        ]

        self.total_pacgums = 0
        for row in self.grid:
            for cell in row:
                # Pass solid cell and player spawn
                if cell.is_solid or cell.coords == self.player_spawn:
                    continue
                # Super pacgum if cell is a ghost spawn
                if cell.coords in self.ghost_spawns:
                    cell.has_super_pacgum = True
                    self.total_pacgums += 1
                else:
                    cell.has_pacgum = True
                    self.total_pacgums += 1

    def get_cell(self, x: int, y: int) -> Cell | None:
        """Returns the Cell at (x, y), or None if out of bounds.
        Args:
            x (int): Horizontal cell coordinate.
            y (int): Vertical cell coordinate.
        Returns:
            Cell | None: The cell at (x, y) or None.
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        return None


if __name__ == "__main__":
    adapter = MazeAdapter(width=15, height=15, seed=42)
    print("=== TEST MAZE ADAPTER ===")
    print(f"Dimensioni labirinto: {adapter.width}x{adapter.height}")
    print(f"Player spawn (Centro): {adapter.player_spawn}")
    print(f"Ghost spawns (4 angoli): {adapter.ghost_spawns}")
    print(f"Totale pacgum da mangiare: {adapter.total_pacgums}")

    # Visualizzazione ASCII del labirinto
    print("\n--- Anteprima Griglia (P=Pacman, G=Ghost/SuperPacgum, .=Pacgum, #=Muro solido) ---")
    for y in range(adapter.height):
        line = ""
        for x in range(adapter.width):
            c = adapter.get_cell(x, y)
            if c is None:
                line += " "
            elif (x, y) == adapter.player_spawn:
                line += "P "
            elif (x, y) in adapter.ghost_spawns:
                line += "G "
            elif c.is_solid:
                line += "# "
            elif c.has_super_pacgum:
                line += "O "
            elif c.has_pacgum:
                line += ". "
            else:
                line += "  "
        print(line)

