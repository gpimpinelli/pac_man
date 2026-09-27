"""
Pac-Man clone using the MiniLibX (mlx) library.

This module implements a basic Pac-Man style movement engine utilizing
the Model-View-Controller (MVC) architectural pattern, enhanced with Pydantic.
"""
import mlx
from typing import Any
from .renderer import Renderer
from dataclasses import dataclass
from ..model import MazeAdapter, GameModel, GameState

def rgb_to_mlx(r: int, g: int, b: int) -> int:
    """Convert RGB (0-255) color channels to a 24-bit MLX integer color."""
    return (r << 16) | (g << 8) | b


@dataclass
class MenuButton:
    name: str
    x: int
    y: int
    w: int
    h: int
    is_hovered: bool = False

# ==========================================
# 2. VIEW (Graphics Engine and Rendering)
# ==========================================
class GameView:
    """Handle window creation, rendering, and MLX graphical outputs."""

    def __init__(self, config: Any) -> None:
        """Initialize the MLX graphical environment using validated config."""
        self.config = config
        
        self.m = mlx.Mlx()
        
        # mlx_init: Establish a connection to the X-Server
        self.mlx_ptr = self.m.mlx_init()
        
        # mlx_new_window: Create a new window on the screen
        self.win_ptr = self.m.mlx_new_window(
            self.mlx_ptr,
            self.config.width,
            self.config.height,
            self.config.title
        )
        
        # mlx_new_image: Create an off-screen image buffer in memory
        self.img = self.m.mlx_new_image(
            self.mlx_ptr,
            self.config.width,
            self.config.height
        )

        # mlx_get_data_addr: Retrieve the memory address of the image
        self.data, self.bfp, self.size_line, _ = self.m.mlx_get_data_addr(self.img)
        
        self.bytes_per_pixel = self.bfp // 8
        self.buffer_size = self.config.height * self.size_line
        
        # Background buffer cache (Night Blue)
        bg_bytes = bytes([0x22, 0x05, 0x05, 0xFF])
        self._bg_buffer = bg_bytes * (self.buffer_size // self.bytes_per_pixel)
        
        # 1. Renderer Principale (a tutto schermo)
        self.main_renderer = Renderer(self)

        self.active_buttons: list[MenuButton] = []

        # Renderer Minimap
        minimap_size = 200
        padding = 50

        self.minimap_renderer = Renderer(
            self, 
            view_x=padding,
            view_y=padding,
            view_w=minimap_size, 
            view_h=minimap_size,
            tile_size=10
        )
        

    def _background_menu(
        self, padding: tuple[int, int], w: int, h: int, color: int=0x222222
    ) -> None:
        new_w = w - (padding[0] * 2)
        new_h = h - (padding[1] * 2)

        self.draw_rect_fast(
            coords=(padding[0], padding[1]), 
            w=new_w, 
            h=new_h, 
            color=color
        )

    def draw_button(self) -> None:
        text_color = 0xFFFFFF
        
        for btn in self.active_buttons:
            text_width = len(btn.name) * 10
            text_x = btn.x + ((btn.w - text_width) // 2)
            text_y = btn.y + (btn.h // 2) - 10
            
            self.m.mlx_string_put(
                self.mlx_ptr, 
                self.win_ptr, 
                text_x, 
                text_y, 
                text_color, 
                btn.name
            )

    def draw_menu(self, w: int, h: int, selected_index: int) -> None: 
        # Reset the list each frame before adding buttons
        self.active_buttons.clear()
        # menu panel
        padding_menu: tuple[int, int] = (w // 4, h // 4)
        self._background_menu(padding_menu, w, h, 0xFFB8FF)
        
        menu_x = padding_menu[0]
        menu_y = padding_menu[1]
        
        menu_w = w - (menu_x * 2)
        menu_h = h - (menu_y * 2)
        
        # general rule for button
        num_buttons = 4
        btn_w = 200
        btn_h = 50
        gap = 20
        btn_color = 0x555555
        button_name = ("START", "HIGHSCORES", "SETTINGS", "EXIT")
        
        # calculate for center of button
        total_block_height = (num_buttons * btn_h) + ((num_buttons - 1) * gap)
        
        # caluclate start_x for draw button
        start_x = menu_x + ((menu_w - btn_w) // 2)
        
        # caluclate start_x for draw button
        start_y = menu_y + ((menu_h - total_block_height) // 2)
        
        # draw button
        for i in range(num_buttons):
            current_y = start_y + (i * (btn_h + gap))
            
            # Highlight selected button
            if i == selected_index:
                color = 0x888888
            else:
                color = btn_color

            self.draw_rect_fast(
                coords=(start_x, current_y), 
                w=btn_w, 
                h=btn_h, 
                color=color
            )
            new_botton = MenuButton(
                name= button_name[i], 
                x=start_x, 
                y=current_y, 
                w=btn_w, 
                h=btn_h
            )
            self.active_buttons.append(new_botton)

    def clear(self) -> None:
        """Wipe the screen buffer instantly 
         using a pre-calculated byte array."""
        self.data[0:self.buffer_size] = self._bg_buffer

    def draw_rect_fast(
        self, coords: tuple[int, int], w: int, h: int, color: int
    ) -> None:
        """
        Draw a solid rectangle in the image buffer using direct byte manipulation.
        """
        b_ch = color & 0xFF
        g_ch = (color >> 8) & 0xFF
        r_ch = (color >> 16) & 0xFF

        x0, y0 = max(0, coords[0]), max(0, coords[1])
        x1, y1 = min(
            coords[0] + w, self.config.width), min(coords[1] + h, self.config.height
        )
        actual_w = x1 - x0
        
        if actual_w <= 0 or y1 <= y0:
            return

        row_bytes = bytes([b_ch, g_ch, r_ch, 0xFF] * actual_w)
        row_len = actual_w * self.bytes_per_pixel

        for row in range(y0, y1):
            start = row * self.size_line + x0 * self.bytes_per_pixel
            self.data[start: start + row_len] = row_bytes


    def position_in_minimap(
        self,
        x: int,
        y: int,
        size: int,
        color: int
    )  -> None:
        # Calculate the logical positoni in pixe of mini map
        logical_x = x / self.main_renderer.tile_size
        logical_y = y / self.main_renderer.tile_size

        # Convert the logical position to scaled pixels on the mini-map
        mini_px = (
            self.minimap_renderer.offset_x + (logical_x * self.minimap_renderer.tile_size)
            )
        mini_py = (
            self.minimap_renderer.offset_y + (logical_y * self.minimap_renderer.tile_size)
        )

        # Calculate the player’s size proportionally
        ratio = self.minimap_renderer.tile_size / self.main_renderer.tile_size
        mini_size = max(2, int(size * ratio))
        self.minimap_renderer.draw_player(mini_px, mini_py, mini_size, color)


    def render(self, model: GameModel)  -> None:
        """
        Extract data from the Model and render it to the window.
        """
        # mlx_sync: Force X11 to finish 
        # draw_player(self, x: float, y: float, size: int, color: int)
        # reading the image buffer before we overwrite it
        self.m.mlx_sync(self.mlx_ptr, mlx.Mlx.SYNC_IMAGE_WRITABLE, self.img)
        self.clear()
        
        # Draw the main map
        self.main_renderer.draw_maze(model.maze)

        # Draw the player
        self.main_renderer.draw_player(
            model.player.x + self.main_renderer.offset_x,
            model.player.y + self.main_renderer.offset_y,
            model.size, 
            model.player.color
        )
        for ghost in model.ghosts:
            self.main_renderer.draw_player(
                ghost.x + self.main_renderer.offset_x,
                ghost.y + self.main_renderer.offset_y,
                model.size,
                ghost.color
            )

        # Draw the mini map
        self.minimap_renderer.draw_maze(model.maze)

        # Move the player to the new coordinates
        self.position_in_minimap(
            model.player.x, model.player.y, model.size, model.player.color
        )
        for ghost in model.ghosts:
            self.position_in_minimap(ghost.x, ghost.y, model.size, ghost.color)

        # Draw MENU
        if model.state in (GameState.START_MENU, GameState.GAME_OVER):
            self.draw_menu(
                w=self.config.width,
                h=self.config.height,
                selected_index=model.selected_button_index
            )

        # mlx_put_image_to_window: 
        # Dump the completed off-screen image buffer onto the active window
        self.m.mlx_put_image_to_window(self.mlx_ptr, self.win_ptr, self.img, 0, 0)

        # Draw text on top of buttons
        if model.state in (GameState.START_MENU, GameState.GAME_OVER):
            self.draw_button()
            