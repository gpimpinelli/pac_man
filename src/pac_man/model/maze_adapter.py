"""Adapter module for external MazeGenerator package.

Transforms the external bitmask maze into a Pac-Man compatible grid
with Cell objects, pellets, power pellets, and entity spawn points.
"""

from enum import IntFlag, auto
from pydantic import BaseModel, ConfigDict, Field
from mazegenerator import MazeGenerator

class Direction(IntFlag):
    NONE  = 0
    WEST = auto()   # 1
    SOUTH = auto()  # 2
    EAST  = auto()  # 4
    NORTH = auto()  # 8

    ALL_WALLS =  WEST | SOUTH | EAST | NORTH # 15


class Cell(BaseModel):
    """
    Represents a single cell in the Pac-Man maze grid.
    Initializes a cell at grid coordinates (x, y).

    Args:
        x (int): Horizontal coordinate in the grid.
        y (int): Vertical coordinate in the grid.
        wall_code (int): 4-bit wall mask from MazeGenerator.
    """

    model_config = ConfigDict(frozen=True)
    x: int = Field(default=1, ge=0)
    y: int = Field(default=1, ge=0)
    wall_code: Direction = Field(default=Direction.NONE)

    # Gameplay attributes
    has_pacgum: bool = False
    has_super_pacgum: bool = False

    def has_wall(self, direction: Direction) -> bool:
        return bool(self._wall_cod & direction)

    @property
    def has_wall_north(self) -> bool:
        """Returns True if the cell has a wall to the North."""
        return self.has_wall(Direction.NORTH)

    @property
    def has_wall_east(self) -> bool:
        """Returns True if the cell has a wall to the East."""
        return self.has_wall(Direction.EAST)

    @property
    def has_wall_south(self) -> bool:
        """Returns True if the cell has a wall to the South."""
        return self.has_wall(Direction.SOUTH)

    @property
    def has_wall_west(self) -> bool:
        """Returns True if the cell has a wall to the West."""
        return self.has_wall(Direction.WEST)

    @property
    def is_solid(self) -> bool:
        """Returns True if this cell is an obstacle (e.g. 42 logo)."""
        return (self.wall_code & Direction.ALL_WALLS) == Direction.ALL_WALLSK


class MazeAdapter(BaseModel):
    """
    Adapts external MazeGenerator to the Pac-Man game domain
    Initializes the adapter and generates the maze grid.

    Args:
        width (int): Number of horizontal cells.
        height (int): Number of vertical cells.
        seed (int): Seed for maze reproducibility (0 = random).
    """
    width: int = Field(..., gt=0)
    height: int = Field(..., gt=0)
    seed: int = Field(default=42 gt=0)

    # Grid of Cell objects: self.grid[y][x]
    grid: list[list[Cell]] = Field(default_factory=list)

    # Entity spawn coordinates (x, y)
    player_spawn: tuple[int, int] = (0, 0)
    ghost_spawns: list[tuple[int, int]] = Field(default_factory=list)

    # Total number of pellets left to eat for winning the level
    total_pacgums: int = 0
    
    @model_validator('after')
    def init_and_generate_maze(self) -> Self:
        self.generate()
        return self

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
