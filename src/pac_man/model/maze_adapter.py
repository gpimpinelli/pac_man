"""Adapter module for external MazeGenerator package.

Transforms the external bitmask maze into a Pac-Man compatible grid
with Cell objects, pellets, power pellets, and entity spawn points.
"""

from mazegenerator import MazeGenerator


class Cell:
    """Represents a single cell in the Pac-Man maze grid."""

    WALL_NORTH = 1
    WALL_EAST = 2
    WALL_SOUTH = 4
    WALL_WEST = 8
    SOLID_BLOCK = 15

    def __init__(self, x: int, y: int, wall_code: int = 0) -> None:
        """Initializes a cell at grid coordinates (x, y).

        Args:
            x (int): Horizontal coordinate in the grid.
            y (int): Vertical coordinate in the grid.
            wall_code (int): 4-bit wall mask from MazeGenerator.
        """
        self.x: int = x
        self.y: int = y
        self.wall_code: int = wall_code

        # Gameplay attributes
        self.has_pacgum: bool = False
        self.has_super_pacgum: bool = False

    @property
    def has_wall_north(self) -> bool:
        """Returns True if the cell has a wall to the North."""
        return bool(self.wall_code & self.WALL_NORTH)

    @property
    def has_wall_east(self) -> bool:
        """Returns True if the cell has a wall to the East."""
        return bool(self.wall_code & self.WALL_EAST)

    @property
    def has_wall_south(self) -> bool:
        """Returns True if the cell has a wall to the South."""
        return bool(self.wall_code & self.WALL_SOUTH)

    @property
    def has_wall_west(self) -> bool:
        """Returns True if the cell has a wall to the West."""
        return bool(self.wall_code & self.WALL_WEST)

    @property
    def is_solid(self) -> bool:
        """Returns True if this cell is an obstacle (e.g. 42 logo)."""
        return self.wall_code == self.SOLID_BLOCK


class MazeAdapter:
    """Adapts external MazeGenerator to the Pac-Man game domain."""

    def __init__(
        self, width: int = 15, height: int = 15, seed: int = 0
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

    def generate(self) -> None:
        """Generates and populates the Pac-Man maze using MazeGenerator."""
        # ====================================================================
        # TODO 1: Safe MazeGenerator Instantiation
        # - Wrap MazeGenerator(size=(self.width, self.height),
        #   perfect=False, seed=self.seed) in a try/except block.
        # - If an exception occurs, print an error and handle gracefully
        #   (Subject V.4 requirement: no crash!).
        # ====================================================================

        # ====================================================================
        # TODO 2: Populate self.grid with Cell objects
        # - Loop over y in range(self.height) and x in range(self.width).
        # - Read the wall_code from raw_maze[y][x].
        # - Create Cell(x, y, wall_code) and append to self.grid.
        # ====================================================================

        # ====================================================================
        # TODO 3: Define Spawns (Subject Chapter VI.1)
        # - Pac-Man starts in the middle:
        #   self.player_spawn = (self.width // 2, self.height // 2)
        # - 4 Ghosts start in the 4 corners:
        #   (0, 0), (self.width - 1, 0),
        #   (0, self.height - 1), (self.width - 1, self.height - 1)
        # ====================================================================

        # ====================================================================
        # TODO 4: Place Pacgums & Super-Pacgums (Subject Chapter VI.1)
        # - Place Super-Pacgums in the 4 corners:
        #   cell.has_super_pacgum = True
        # - Place normal Pacgums in corridor cells:
        #   - Skip solid cells (cell.is_solid)
        #   - Skip the player spawn point
        #   - Skip the 4 ghost corner spawns (they have Super-Pacgums!)
        # - Count and update self.total_pacgums with the number of pellets.
        # ====================================================================
        pass

    def get_cell(self, x: int, y: int) -> Cell | None:
        """Returns the Cell at (x, y), or None if out of bounds.

        Args:
            x (int): Horizontal cell coordinate.
            y (int): Vertical cell coordinate.

        Returns:
            Cell | None: The cell at (x, y) or None.
        """
        # ====================================================================
        # TODO 5: Out of bounds check
        # - If 0 <= x < self.width and 0 <= y < self.height:
        #       return self.grid[y][x]
        # - Otherwise return None.
        # ====================================================================
        pass
