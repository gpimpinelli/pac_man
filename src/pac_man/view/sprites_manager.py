import os
from typing import Any
from ..model import Direction


class SpriteManager:
    def __init__(self, mlx: Any, mlx_ptr: Any):
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
        path = os.path.join(self.sprites_dir, filename)
        return self.m.mlx_xpm_file_to_image(self.mlx_ptr, path)[0]

    def _load_mini(self, filename: str) -> Any:
        path = os.path.join(self.mini_sprites_dir, filename)
        return self.m.mlx_xpm_file_to_image(self.mlx_ptr, path)[0]
