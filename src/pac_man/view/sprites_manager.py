"""Sprite loader and asset cache for Pac-Man graphical assets."""

import os
from typing import Any
from ..model import Direction


class SpriteManager:
    """Loads and caches XPM image assets using MiniLibX.

    Attributes:
        m (Any): MiniLibX wrapper instance.
        mlx_ptr (Any): MiniLibX application pointer.
        sprites_dir (str): Base directory containing regular sprites.
        mini_sprites_dir (str): Subdirectory containing minimap sprites.
        pacman (dict[Direction, Any]): Full open-mouth Pac-Man sprites.
        pacman_semi (dict[Direction, Any]): Half-closed mouth Pac-Man sprites.
        pacman_ball (Any): Closed ball Pac-Man sprite for idle state.
        ghosts_normal (list[dict[Direction, Any]]): Directional ghost sprites.
        frightened (Any): Blue frightened ghost sprite.
        eaten (Any): Eaten ghost eyes sprite.
        heart (Any): Life indicator heart sprite.
        gameover (Any): Game over banner sprite.
        win (Any): Level clear / win banner sprite.
        mini_pacman (Any): Scaled Pac-Man sprite for minimap.
        mini_ghost_red (Any): Scaled ghost sprite for minimap.
    """

    def __init__(self, mlx: Any, mlx_ptr: Any) -> None:
        """Initialize the sprite manager and preload all game sprites.

        Args:
            mlx (Any): MiniLibX wrapper instance.
            mlx_ptr (Any): MiniLibX application pointer.
        """
        self.m = mlx
        self.mlx_ptr = mlx_ptr

        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.sprites_dir = os.path.join(current_dir, "sprites")
        self.mini_sprites_dir = os.path.join(self.sprites_dir, "mini")

        self.pacman = {
            Direction.UP: self._load("pacman_up.xpm"),
            Direction.DOWN: self._load("pacman_down.xpm"),
            Direction.LEFT: self._load("pacman_left.xpm"),
            Direction.RIGHT: self._load("pacman_right.xpm"),
        }

        self.pacman_semi = {
            Direction.UP: self._load("close_up.xpm"),
            Direction.DOWN: self._load("close_down.xpm"),
            Direction.LEFT: self._load("close_left.xpm"),
            Direction.RIGHT: self._load("close_right.xpm"),
        }

        self.pacman_ball = self._load("pacman_ball.xpm")

        ghost_colors = ["red", "pink", "blu", "orange"]
        self.ghosts_normal = []
        for color in ghost_colors:
            self.ghosts_normal.append(
                {
                    Direction.UP: self._load(f"{color}_up.xpm"),
                    Direction.DOWN: self._load(f"{color}_down.xpm"),
                    Direction.LEFT: self._load(f"{color}_left.xpm"),
                    Direction.RIGHT: self._load(f"{color}_right.xpm"),
                }
            )

        self.frightened = self._load("ghost_eaten.xpm")
        self.eaten = self._load("eaten.xpm")
        self.heart = self._load("heart.xpm")
        self.gameover = self._load("gameover.xpm")
        self.win = self._load("win.xpm")

        self.mini_pacman = self._load_mini("pacman_right.xpm")
        self.mini_ghost_red = self._load_mini("red_up.xpm")

    def _load(self, filename: str) -> Any:
        """Load an XPM file from the standard sprites folder.

        Args:
            filename (str): Name of the XPM sprite file.

        Returns:
            Any: Pointer to the loaded MiniLibX image buffer.
        """
        path = os.path.join(self.sprites_dir, filename)
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Sprite not found: '{path}'")

        img_data = self.m.mlx_xpm_file_to_image(self.mlx_ptr, path)
        if not img_data or not img_data[0]:
            raise RuntimeError(f"File sprite corrupted or not valid: '{path}")
        return img_data[0]

    def _load_mini(self, filename: str) -> Any:
        """Load an XPM file from the minimap mini sprites folder.

        Args:
            filename (str): Name of the mini XPM sprite file.

        Returns:
            Any: Pointer to the loaded MiniLibX image buffer.
        """
        path = os.path.join(self.mini_sprites_dir, filename)
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Sprite not found: '{path}'")

        img_data = self.m.mlx_xpm_file_to_image(self.mlx_ptr, path)
        if not img_data or not img_data[0]:
            raise RuntimeError(f"File sprite corrupted or not valid: '{path}")
        return img_data[0]
