"""Renderer module drawing maze geometry, corridors, and pellets."""

from typing import TYPE_CHECKING
from ..model import MazeAdapter
from .colors import Colors
from pac_man.utils import cell_to_pixel, center_in_pixel

if TYPE_CHECKING:
    from .game_view import GameView


class Renderer:
    """Renders maze corridors, walls, and pellets within a specified viewport.

    Attributes:
        view (GameView): Parent view instance containing image buffers.
        view_x (int): Horizontal pixel offset of this viewport.
        view_y (int): Vertical pixel offset of this viewport.
        view_w (int | None): Custom viewport width or None for full screen.
        view_h (int | None): Custom viewport height or None for full screen.
        tile_size (int): Size of individual maze cells in pixels.
        offset_x (int): Computed horizontal centering offset.
        offset_y (int): Computed vertical centering offset.
    """

    def __init__(
        self,
        view: "GameView",
        view_x: int = 0,
        view_y: int = 0,
        view_w: int | None = None,
        view_h: int | None = None,
        tile_size: int = 40,
    ) -> None:
        """Initialize renderer viewport geometry and tile scaling.

        Args:
            view (GameView): Target view container.
            view_x (int): Left origin coordinate.
            view_y (int): Top origin coordinate.
            view_w (int | None): Bounding box width.
            view_h (int | None): Bounding box height.
            tile_size (int): Dimension of each cell in pixels.
        """
        self.view: "GameView" = view

        self.view_x = view_x
        self.view_y = view_y
        self.view_w = view_w
        self.view_h = view_h

        self.tile_size: int = tile_size
        self.offset_x: int = 0
        self.offset_y: int = 0

    def update_layout(self, maze: MazeAdapter) -> None:
        """Recalculate maze centering offsets based on viewport dimensions.

        Args:
            maze (MazeAdapter): Active maze adapter.
        """
        screen_w = (
            self.view_w if self.view_w is not None else self.view.config.width
        )
        screen_h = (
            self.view_h if self.view_h is not None else self.view.config.height
        )

        self.offset_x = (
            self.view_x + (screen_w - maze.width * self.tile_size) // 2
        )
        self.offset_y = (
            self.view_y + (screen_h - maze.height * self.tile_size) // 2
        )

    def draw_maze(self, maze: MazeAdapter) -> None:
        """Rasterize maze walls, solid cells, and pacgums into backbuffer.

        Args:
            maze (MazeAdapter): Maze adapter providing grid and pellet data.
        """
        # self.update_layout(maze)
        # Optimization: save the method's refernce in a local variable
        draw_rect = self.view.draw_rect_fast
        # Cell dimension in pixel
        tile_size = self.tile_size
        # Cell's wall dimension in pixel based on the cell dimension
        wall_thick = max(2, tile_size // 10)

        for row in maze.grid:
            for cell in row:
                cx, cy = cell_to_pixel(
                    cell.coords, (self.offset_x, self.offset_y), self.tile_size
                )

                if cell.is_solid:
                    draw_rect(
                        (cx, cy), tile_size, tile_size, Colors.MAZE_WALLS
                    )
                    continue

                if cell.has_wall_north:
                    draw_rect(
                        (cx, cy), tile_size, wall_thick, Colors.MAZE_WALLS
                    )
                if cell.has_wall_south:
                    draw_rect(
                        (cx, cy + tile_size - wall_thick),
                        tile_size,
                        wall_thick,
                        Colors.MAZE_WALLS,
                    )
                if cell.has_wall_west:
                    draw_rect(
                        (cx, cy), wall_thick, tile_size, Colors.MAZE_WALLS
                    )
                if cell.has_wall_east:
                    draw_rect(
                        (cx + tile_size - wall_thick, cy),
                        wall_thick,
                        tile_size,
                        Colors.MAZE_WALLS,
                    )

                if cell.has_pacgum:
                    # max(default, value -> 1/8 of the cell)
                    size = max(2, tile_size // 8)
                    px, py = center_in_pixel((cx, cy), tile_size, size)
                    draw_rect((px, py), size, size, Colors.AMBRA)

                if cell.has_super_pacgum:
                    # max(default, value -> 1/8 of the cell)
                    size = max(4, tile_size // 6)
                    px, py = center_in_pixel((cx, cy), tile_size, size)
                    draw_rect((px, py), size, size, Colors.SUPER_PACGUM)
