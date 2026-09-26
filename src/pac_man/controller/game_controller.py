import os
import time
from src.pac_man.utils import cell_to_pixel
from pydantic import BaseModel, Field
from enum import Enum, auto
from ..model import MazeAdapter, GameModel, Direction
from ..view import GameView
from src.pac_man.model.entity import Ghost, GhostState

# ==========================================
# CONSTANTS AND KEY MAPPINGS
# ==========================================
KEY_ESC = 65307
COLORS = [0xFF0000, 0xFFB8FF, 0x00FFFF, 0xFFB852]
EVENT_KEY_PRESS = 2
EVENT_DESTROY = 17
EVENT_CLIENT_MESSAGE = 33
KEY_PRESS_MASK = 1 << 0
STRUCTURE_NOTIFY_MASK = 1 << 17

KEYS_MAP = {
    65362: Direction.UP,    # Up Arrow
    119:   Direction.UP,    # w
    65364: Direction.DOWN,  # Down Arrow
    115:   Direction.DOWN,  # s
    65361: Direction.LEFT,  # Left Arrow
    97:    Direction.LEFT,  # a
    65363: Direction.RIGHT, # Right Arrow
    100:   Direction.RIGHT  # d
}

# ==========================================
# CONFIGURATION
# ==========================================
class GameConfig(BaseModel):
    """Centralized, validated configuration for the game."""
    width: int = Field(default=1024, gt=0, description="Window width in pixels.")
    height: int = Field(default=764, gt=0, description="Window height in pixels.")
    title: str = Field(default="Pac-Man 42", min_length=1, description="Window title.")
    target_fps: int = Field(default=60, gt=0, le=240, description="Target frames per second.")


class GameState(Enum):
    START_MENU = auto()
    PLAYING = auto()
    DEATH_PAUSE = auto()  # Sostituisce la logica del timer + started=False
    GAME_OVER = auto()
    SETTINGS = auto()

# ==========================================
# 3. CONTROLLER (Input, Loop, and Integration)
# ==========================================
class GameController:
    """Orchestrate the game loop, user inputs, and component integration."""

    def __init__(self):
        """Initialize the Controller using Pydantic configurations."""
        
        self.config = GameConfig(width=1640, height=1000, target_fps=60)
        self.last_time = time.perf_counter()
        self.maze = MazeAdapter(seed=900, width=15, height=15)
        
        # Pass the config block to the View
        self.view = GameView(self.config, self.maze)

        # Instantiate Model dynamically from config parameters
        self.model = GameModel(
            screen_width=self.config.width,
            screen_height=self.config.height,
            maze=self.maze,
            tile_size=self.view.main_renderer.tile_size,
            offset_x=self.view.main_renderer.offset_x,
            offset_y=self.view.main_renderer.offset_y,
        )

        spawn_x, spawn_y = cell_to_pixel(
            self.maze.player_spawn,
            (self.view.main_renderer.offset_x,
            self.view.main_renderer.offset_y),
            self.view.main_renderer.tile_size,
        )
        self.model.size = int(self.view.main_renderer.tile_size * 0.5)
        
        half_tile = self.view.main_renderer.tile_size // 2
        
        x_pixel = float(spawn_x + half_tile)
        y_pixel = float(spawn_y + half_tile)
        self.model.player.x = x_pixel
        self.model.player.y = y_pixel
        self.model.player.coords_spawn = (x_pixel, y_pixel)

        speed = 100

        for coords, c in zip(self.maze.ghost_spawns, COLORS):
            coords_pixel: tuple[int, int] = cell_to_pixel(coords, (self.view.main_renderer.offset_x, self.view.main_renderer.offset_y), self.view.main_renderer.tile_size)
            x_pixel = float(coords_pixel[0] + half_tile)
            y_pixel = float(coords_pixel[1] + half_tile)
            self.model.ghosts.append(
                Ghost(
                    x=x_pixel,
                    y=y_pixel,
                    color=c,
                    speed=speed,
                    state=GhostState.CHASE,
                    coords_spawn=(x_pixel, y_pixel),
                )
            )
            speed += 2

        self.setup_hooks()
        
    def setup_hooks(self):
        """Register MLX event listeners to Controller methods."""
        m = self.view.m
        win = self.view.win_ptr
        
        # mlx_hook: Bind X11 events
        m.mlx_hook(win, EVENT_DESTROY, 0, self.close_game, None)
        m.mlx_hook(win, EVENT_DESTROY, STRUCTURE_NOTIFY_MASK, self.close_game, None)
        m.mlx_hook(win, EVENT_CLIENT_MESSAGE, 0, self.close_game, None)
        m.mlx_hook(win, EVENT_CLIENT_MESSAGE, STRUCTURE_NOTIFY_MASK, self.close_game, None)
        
        # mlx_hook: Bind keyboard press events
        m.mlx_hook(win, EVENT_KEY_PRESS, KEY_PRESS_MASK, self.on_key_press, None)
        
        # mlx_loop_hook: Main function for MLX infinite loop
        m.mlx_loop_hook(self.view.mlx_ptr, self.update_game, None)

    def close_game(self, *args):
        """Handle game shutdown and memory cleanup."""
        print("Closing game...")
        self.view.m.mlx_destroy_window(self.view.mlx_ptr, self.view.win_ptr)
        os._exit(0)

    def on_key_press(self, keycode: int, *args):
        """Process keyboard input and update the model state."""
        if keycode in (KEY_ESC, 27, ord('q'), ord('Q')):
            self.close_game()
            
        action = KEYS_MAP.get(keycode)
        if action:
            self.model.player.desired_dir = action
            if not self.model.started:
                self.model.started = True
                self.last_time = time.perf_counter()
        return 0

    def update_game(self, *args):
        """Manage the frame rate, trigger physics updates, and execute rendering."""
        current_time = time.perf_counter()
        dt = current_time - self.last_time
        frame_duration = 1.0 / self.config.target_fps

        if dt < frame_duration:
            return 0

        self.last_time = current_time

        self.model.update(dt)
        self.view.render(self.model)

        if self.maze.finish_game():
            # TODO
            # mandare al livello successivo.
            # se finiti i livelli o vite
            print("Hai vinto")
            print(self.model.player.score)

            return 0
        return 0

    def run(self):
        """Launch the game engine and start the event loop."""
        print(f"{self.config.title} Engine Running. Premi frecce o WASD per muoverti. ESC per uscire.")
        self.view.m.mlx_loop(self.view.mlx_ptr)

# ==========================================
# EXECUTION
# ==========================================
if __name__ == "__main__":
    game = GameController()
    game.run()