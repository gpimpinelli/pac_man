"""Adapter module for external MazeGenerator package.

Transforms the external bitmask maze into a Pac-Man compatible grid
with Cell objects, pellets, power pellets, and entity spawn points.
"""

from mazegenerator import MazeGenerator
from dataclasses import dataclass
from enum import IntFlag, auto
from collections import deque


class Direction(IntFlag):
    """Bitmask flags representing wall configurations for a cell."""

    NONE = 0
    NORTH = auto()  # 1
    EAST = auto()  # 2
    SOUTH = auto()  # 4
    WEST = auto()  # 8

    ALL_WALLS = WEST | SOUTH | EAST | NORTH  # 15


@dataclass(slots=True)
class Cell:
    """Represents a single cell in the Pac-Man maze grid.

    Args:
        coords (tuple[int, int]): Horizontal and vertical grid coordinates.
        wall_code (Direction): 4-bit wall mask from MazeGenerator.
        has_pacgum (bool): Whether a normal pellet is present.
        has_super_pacgum (bool): Whether an energizer power pellet is present.
    """

    coords: tuple[int, int]
    wall_code: Direction = Direction.NONE

    # Gameplay attributes
    has_pacgum: bool = False
    has_super_pacgum: bool = False

    def _has_wall(self, direction: Direction) -> bool:
        """Check whether the cell has a wall in the specified direction.

        Args:
            direction (Direction): Cardinal direction flag to test.

        Returns:
            bool: True if wall bit is set, False otherwise.
        """
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
        """Remove a standard pellet or super pellet from this cell.

        Args:
            is_super_gum (bool): True if removing a super pellet, False for
                a standard pacgum.
        """
        if is_super_gum:
            self.has_super_pacgum = False
        else:
            self.has_pacgum = False


class MazeAdapter:
    """Adapts external MazeGenerator to the Pac-Man game domain."""

    def __init__(
        self,
        width: int = 15,
        height: int = 15,
        seed: int = 42
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
        """Check whether all pellets in the maze have been eaten.

        Returns:
            bool: True if total_pacgums is 0, False otherwise.
        """
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
            (self.width - 1, self.height - 1),
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

    def breath_first_search(
        self,
        start: tuple[int, int] | None = None,
        dest: tuple[int, int] | None = None,
    ) -> list[tuple[int, int]]:
        """Find the shortest path between start and destination coordinates.

        Uses Breadth-First Search across open maze corridors.

        Args:
            start (tuple[int, int] | None): Starting cell grid coordinates.
            dest (tuple[int, int] | None): Destination cell grid coordinates.

        Returns:
            list[tuple[int, int]]: List of cell coordinates from start to dest,
                or empty list if unreachable.
        """
        if not (start and dest):
            return []

        start_cell = self.get_cell(start[0], start[1])
        dest_cell = self.get_cell(dest[0], dest[1])

        if not start_cell or not dest_cell:
            return []

        came_from: dict[tuple[int, int], tuple[int, int] | None] = {}
        queue: deque[Cell] = deque([start_cell])
        came_from[start_cell.coords] = None

        while queue:
            current = queue.popleft()
            if current.coords == dest_cell.coords:
                break

            if not current.has_wall_north:
                n_coords = (current.coords[0], current.coords[1] - 1)
                if n_coords not in came_from:
                    neighbor = self.get_cell(n_coords[0], n_coords[1])
                    if neighbor is not None:
                        queue.append(neighbor)
                        came_from[n_coords] = current.coords
            if not current.has_wall_south:
                n_coords = (current.coords[0], current.coords[1] + 1)
                if n_coords not in came_from:
                    neighbor = self.get_cell(n_coords[0], n_coords[1])
                    if neighbor is not None:
                        queue.append(neighbor)
                        came_from[n_coords] = current.coords
            if not current.has_wall_east:
                n_coords = (current.coords[0] + 1, current.coords[1])
                if n_coords not in came_from:
                    neighbor = self.get_cell(n_coords[0], n_coords[1])
                    if neighbor is not None:
                        queue.append(neighbor)
                        came_from[n_coords] = current.coords
            if not current.has_wall_west:
                n_coords = (current.coords[0] - 1, current.coords[1])
                if n_coords not in came_from:
                    neighbor = self.get_cell(n_coords[0], n_coords[1])
                    if neighbor is not None:
                        queue.append(neighbor)
                        came_from[n_coords] = current.coords

        if dest_cell.coords not in came_from:
            return []

        path: list[tuple[int, int]] = []
        current_step: tuple[int, int] | None = dest_cell.coords

        while current_step is not None:
            path.append(current_step)
            current_step = came_from.get(current_step)

        path.reverse()

        return path

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
