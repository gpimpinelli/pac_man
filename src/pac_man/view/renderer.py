from ..model import MazeAdapter
from .colors import Colors
from src.pac_man.utils import cell_to_pixel, center_in_pixel
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .game_view import GameView


class Renderer:
    def __init__(
        self,
        view: "GameView",
        view_x: int = 0,
        view_y: int = 0,
        view_w: int = None,
        view_h: int = None,
        tile_size: int = 48
    ) -> None:
        self.view: "GameView" = view
        
        # Salviamo i parametri di layout della finestra per usarli dopo
        self.view_x = view_x
        self.view_y = view_y
        self.view_w = view_w
        self.view_h = view_h
        
        self.tile_size: int = tile_size
        self.offset_x: int = 0
        self.offset_y: int = 0
 
    def update_layout(self, maze: MazeAdapter) -> None:
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
        self.update_layout(maze)
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
                        (cx,
                        cy + tile_size - wall_thick),
                        tile_size,
                        wall_thick,
                        Colors.MAZE_WALLS
                    )
                if cell.has_wall_west:
                    draw_rect(
                        (cx, cy), wall_thick, tile_size, Colors.MAZE_WALLS
                    )
                if cell.has_wall_east:
                    draw_rect(
                        (cx + tile_size - wall_thick,
                        cy),
                        wall_thick,
                        tile_size,
                        Colors.MAZE_WALLS
                    )

                if cell.has_pacgum:
                    # max(default, value -> 1/8 of the cell)
                    size = max(2, tile_size // 8)
                    px, py = center_in_pixel((cx, cy), tile_size, size)
                    draw_rect((px,py), size, size, Colors.AMBRA)
                
                if cell.has_super_pacgum:
                    # max(default, value -> 1/8 of the cell)
                    size = max(4, tile_size // 6)
                    px, py = center_in_pixel((cx, cy), tile_size, size)
                    # TODO change the color
                    draw_rect((px,py), size, size, Colors.SUPER_PACGUM)


    def draw_player(self, x: float, y: float, size: int, color: int) -> None:
        
        # TRUCCO 2.5D: Spostiamo il disegno verso l'alto di 20 pixel, 
        # ma senza alterare la vera 'y' del GameModel!
        # offset_visivo_y = y - 20 
        
        self.view.draw_rect_fast(
            (int(x) - size // 2, 
            int(y) - size // 2),
            size, 
            size, 
            color
        )