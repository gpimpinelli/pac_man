"""
Pac-Man clone using the MiniLibX (mlx) library.

This module implements a basic Pac-Man style movement engine utilizing
the Model-View-Controller (MVC) architectural pattern, enhanced with Pydantic.
"""

import os
import mlx
import time
from enum import Enum, auto
from ..model import MazeAdapter, GameModel
from .renderer import Renderer
from typing import Optional, Any
from pydantic import BaseModel, Field, ConfigDict


def rgb_to_mlx(r: int, g: int, b: int) -> int:
    """Convert RGB (0-255) color channels to a 24-bit MLX integer color."""
    return (r << 16) | (g << 8) | b


# ==========================================
# 2. VIEW (Graphics Engine and Rendering)
# ==========================================
class GameView:
    """Handle window creation, rendering, and MLX graphical outputs."""

    def __init__(self, config: Any, maze: MazeAdapter):
        """Initialize the MLX graphical environment using validated config."""
        self.config = config
        
        self.m = mlx.Mlx()
        
        # mlx_init: Establish a connection to the X-Server
        self.mlx_ptr = self.m.mlx_init()
        
        # mlx_new_window: Create a new window on the screen
        self.win_ptr = self.m.mlx_new_window(self.mlx_ptr, self.config.width, self.config.height, self.config.title)
        
        # mlx_new_image: Create an off-screen image buffer in memory
        self.img = self.m.mlx_new_image(self.mlx_ptr, self.config.width, self.config.height)
        
        # mlx_get_data_addr: Retrieve the memory address of the image
        self.data, self.bfp, self.size_line, _ = self.m.mlx_get_data_addr(self.img)
        
        self.bytes_per_pixel = self.bfp // 8
        self.buffer_size = self.config.height * self.size_line
        
        # Background buffer cache (Night Blue)
        bg_bytes = bytes([0x22, 0x05, 0x05, 0xFF])
        self._bg_buffer = bg_bytes * (self.buffer_size // self.bytes_per_pixel)

        # --- GESTIONE RENDERER (La View è proprietaria della grafica) ---
        
        # 1. Renderer Principale (a tutto schermo)
        self.main_renderer = Renderer(self, maze)

        # 2. Renderer Minimappa (in alto a destra)
        minimap_size = 200
        padding = 50
        
        self.minimap_renderer = Renderer(
            self, 
            maze, 
            view_x=self.config.width - minimap_size - padding, 
            view_y=padding, 
            view_w=minimap_size, 
            view_h=minimap_size,
            tile_size=10
        )

    def clear(self):
        """Wipe the screen buffer instantly using a pre-calculated byte array."""
        self.data[0:self.buffer_size] = self._bg_buffer

    def draw_rect_fast(self, x: int, y: int, w: int, h: int, color: int):
        """
        Draw a solid rectangle in the image buffer using direct byte manipulation.
        """
        b_ch = color & 0xFF
        g_ch = (color >> 8) & 0xFF
        r_ch = (color >> 16) & 0xFF

        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(x + w, self.config.width), min(y + h, self.config.height)
        actual_w = x1 - x0
        
        if actual_w <= 0 or y1 <= y0:
            return

        row_bytes = bytes([b_ch, g_ch, r_ch, 0xFF] * actual_w)
        row_len = actual_w * self.bytes_per_pixel

        for row in range(y0, y1):
            start = row * self.size_line + x0 * self.bytes_per_pixel
            self.data[start: start + row_len] = row_bytes


    def position_in_minimap(self, x: int, y: int, size: int, color: int):
        # Calculate the logical positoni in pixe of mini map
        logical_x = (x - self.main_renderer.offset_x) / self.main_renderer.tile_size
        logical_y = (y - self.main_renderer.offset_y) / self.main_renderer.tile_size

        # Convert the logical position to scaled pixels on the mini-map
        mini_px = self.minimap_renderer.offset_x + (logical_x * self.minimap_renderer.tile_size)
        mini_py = self.minimap_renderer.offset_y + (logical_y * self.minimap_renderer.tile_size)

        # Calculate the player’s size proportionally
        ratio = self.minimap_renderer.tile_size / self.main_renderer.tile_size
        mini_size = max(2, int(size * ratio))
        self.minimap_renderer.draw_player(mini_px, mini_py, mini_size, color)


    def render(self, model: GameModel):
        """
        Extract data from the Model and render it to the window.
        """
        # mlx_sync: Force X11 to finish rdraw_player(self, x: float, y: float, size: int, color: int)eading the image buffer before we overwrite it
        self.m.mlx_sync(self.mlx_ptr, mlx.Mlx.SYNC_IMAGE_WRITABLE, self.img)
        self.clear()
        
        # Draw the main map
        self.main_renderer.draw_maze(model.maze)

        # Draw the player
        self.main_renderer.draw_player(model.player.x, model.player.y, model.size, model.player.color)
        for ghost in model.ghosts:
            self.main_renderer.draw_player(ghost.x, ghost.y, model.size, ghost.color)

        # Draw the mini map
        self.minimap_renderer.draw_maze(model.maze)

        # Move the player to the new coordinates
        self.position_in_minimap(model.player.x, model.player.y, model.size, model.player.color)
        for ghost in model.ghosts:
            self.position_in_minimap(ghost.x, ghost.y, model.size, ghost.color)

        # mlx_put_image_to_window: Dump the completed off-screen image buffer onto the active window
        self.m.mlx_put_image_to_window(self.mlx_ptr, self.win_ptr, self.img, 0, 0)
