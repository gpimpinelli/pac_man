from ..model import MazeAdapter, Cell
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .graphics import GameView

COLOR_WALL = 0x2121DE
COLOR_PACGUM = 0xFFB8AE
COLOR_SUPER_PACGUM = 0xFFFF00


class Renderer:
    def __init__(self, view: "GameView", maze: MazeAdapter) -> None:
        self.view: "GameView" = view
        self.maze: MazeAdapter = maze
        self.tile_size: int = 0
        self.offset_x: int = 0
        self.offset_y: int = 0

        self.setup_layout(maze)

    def setup_layout(self, maze: MazeAdapter) -> None:
        self.maze = maze

        screen_w = self.view.config.width
        screen_h = self.view.config.height
        margin = 40
        
        self.tile_size = min(
            (screen_w - 2 * margin) // maze.width,
            (screen_h - 2 * margin) // maze.height
        )
        # Offset x & y is the margin left-right-bottom-up of the screen
        # to center the maze in the screen
        self.offset_x = (screen_w - maze.width * self.tile_size) // 2
        self.offset_y = (screen_h - maze.height * self.tile_size) // 2
    
    def cell_to_pixel(self, cell_x: int, cell_y: int) -> tuple[int, int]:
        return (
            self.offset_x + cell_x * self.tile_size,
            self.offset_y + cell_y * self.tile_size
        )

    def draw_maze(self, maze: MazeAdapter) -> None:
        # Optimization: save the method's refernce in a local variable
        draw_rect = self.view.draw_rect_fast
        # Cell dimension in pixel
        tile_size = self.tile_size
        # Cell's wall dimension in pixel based on the cell dimension
        wall_thick = max(2, tile_size // 10)
        
        for row in maze.grid:
            for cell in row:
                cx, cy = self.cell_to_pixel(cell.x, cell.y)
                
                if cell.is_solid:
                    draw_rect(
                        cx, cy, tile_size, tile_size, COLOR_WALL
                    )
                    continue

                if cell.has_wall_north:
                    draw_rect(
                        cx, cy, tile_size, wall_thick, COLOR_WALL
                    )
                if cell.has_wall_south:
                    draw_rect(
                        cx,
                        cy + tile_size - wall_thick,
                        tile_size,
                        wall_thick,
                        COLOR_WALL
                    )
                if cell.has_wall_west:
                    draw_rect(
                        cx, cy, wall_thick, tile_size, COLOR_WALL
                    )
                if cell.has_wall_east:
                    draw_rect(
                        cx + tile_size - wall_thick,
                        cy,
                        wall_thick,
                        tile_size,
                        COLOR_WALL
                    )

                if cell.has_pacgum:
                    # max(default, value -> 1/8 of the cell)
                    size = max(4, tile_size // 8)
                    px = cx + (tile_size - size) // 2
                    py = cy + (tile_size - size) // 2
                    draw_rect(px,py, size, size, COLOR_PACGUM)
                
    
                
        
        
        