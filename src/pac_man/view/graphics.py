"""
Pac-Man clone using the MiniLibX (mlx) library.

This module implements a basic Pac-Man style movement engine utilizing
the Model-View-Controller (MVC) architectural pattern, enhanced with Pydantic.
"""

import os
import mlx
import time
from enum import Enum, auto
from ..model import MazeAdapter
from .renderer import Renderer
from typing import Optional, Any
from pydantic import BaseModel, Field, ConfigDict

# ==========================================
# CONSTANTS AND KEY MAPPINGS
# ==========================================
KEY_ESC = 65307

EVENT_KEY_PRESS = 2
EVENT_DESTROY = 17
EVENT_CLIENT_MESSAGE = 33
KEY_PRESS_MASK = 1 << 0
STRUCTURE_NOTIFY_MASK = 1 << 17

class Direction(Enum):
    """Represent the four possible movement directions."""
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()

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

def rgb_to_mlx(r: int, g: int, b: int) -> int:
    """Convert RGB (0-255) color channels to a 24-bit MLX integer color."""
    return (r << 16) | (g << 8) | b


# ==========================================
# CONFIGURATION
# ==========================================
class GameConfig(BaseModel):
    """Centralized, validated configuration for the game."""
    width: int = Field(default=1024, gt=0, description="Window width in pixels.")
    height: int = Field(default=764, gt=0, description="Window height in pixels.")
    title: str = Field(default="Pac-Man 42", min_length=1, description="Window title.")
    target_fps: int = Field(default=60, gt=0, le=240, description="Target frames per second.")


# ==========================================
# 1. MODEL (Physics, Data, and Rules)
# ==========================================
class GameModel(BaseModel):
    """
    Manage the game logic, state, and entity physics.
    Inherits from Pydantic's BaseModel for rigid data initialization.
    """
    # Environment constraints
    screen_width: int = Field(..., gt=0)
    screen_height: int = Field(..., gt=0)
    
    maze: Any

    # Player state & constraints
    x: float = Field(default=50.0, ge=0.0, description="Player X coordinate.")
    y: float = Field(default=150.0, ge=0.0, description="Player Y coordinate.")
    size: int = Field(default=40, gt=0, description="Player width/height in pixels.")
    speed: float = Field(default=180.0, gt=0.0, description="Movement speed (pixels/sec).")
    
    # default_factory is used if a function call is needed, 
    # but here a static call is fine since it evaluates to a simple int.
    color: int = Field(default=rgb_to_mlx(255, 255, 0))
    
    current_dir: Optional[Direction] = Field(default=None)
    desired_dir: Optional[Direction] = Field(default=None)
    started: bool = Field(default=False)

    # Disable assignment validation for performance during the 60fps loop
    model_config = ConfigDict(validate_assignment=False)
    
    tile_size: int = Field(default=32)
    offset_x: int = Field(ge=0)
    offset_y: int = Field(ge=0)
    
    def calc_rail(self) -> tuple[int, int]:
        col = int(self.x - self.offset_x) // self.tile_size
        row = int(self.y - self.offset_y) // self.tile_size
        return(
            self.offset_x + (col + 0.5) * self.tile_size,
            self.offset_y + (row + 0.5) * self.tile_size
        )

    def update(self, dt: float):
        """
        Update the player position and handle collisions.
 
        Args:
            dt: Delta time elapsed since the last frame, in seconds.
        """
        if not self.started:
            return   
 
 
        if self.desired_dir and self.desired_dir != self.current_dir:
            is_opposite = (
                (self.current_dir == Direction.LEFT and self.desired_dir == Direction.RIGHT) or
                (self.current_dir == Direction.RIGHT and self.desired_dir == Direction.LEFT) or
                (self.current_dir == Direction.UP and self.desired_dir == Direction.DOWN) or
                (self.current_dir == Direction.DOWN and self.desired_dir == Direction.UP)
            )
            
 
            if is_opposite:
                # Inverti istantaneamente senza calcolare il centro
                self.current_dir = self.desired_dir
                self.desired_dir = None
            else:
                can_turn = False
                col = int((self.x - self.offset_x) // self.tile_size)
                row = int((self.y - self.offset_y) // self.tile_size)
                current_cell = self.maze.get_cell(col, row)
                if current_cell and not current_cell.is_solid:
                    match self.desired_dir:
                        case Direction.UP:
                            can_turn = not current_cell.has_wall_north
                        case Direction.DOWN:
                            can_turn = not current_cell.has_wall_south
                        case Direction.LEFT:
                            can_turn = not current_cell.has_wall_west
                        case Direction.RIGHT:
                            can_turn = not current_cell.has_wall_east
            
                rail_x, rail_y = self.calc_rail()
                if can_turn:
                    if self.current_dir in (Direction.LEFT, Direction.RIGHT):
                        dist_from_center = abs(self.x - rail_x)
                    else:
                        dist_from_center = abs(self.y - rail_y)
                    tolerance = 6.0
                    if self.current_dir is None or dist_from_center <= tolerance:
                        self.x = rail_x
                        self.y = rail_y
                        self.current_dir = self.desired_dir
                        self.desired_dir = None
 
        # 1. Wall check for STRAIGHT movement (this was missing!)
        # The `can_turn` block above only validates walls when desired_dir
        # differs from current_dir (i.e. when turning). If the player keeps
        # holding the same direction, that block is skipped entirely and
        # nothing ever stopped movement into a wall/solid cell.
        if self.current_dir is not None:
            col = int((self.x - self.offset_x) // self.tile_size)
            row = int((self.y - self.offset_y) // self.tile_size)
            cell = self.maze.get_cell(col, row)
 
            blocked = cell is None or cell.is_solid
            if not blocked:
                match self.current_dir:
                    case Direction.UP:
                        blocked = cell.has_wall_north
                    case Direction.DOWN:
                        blocked = cell.has_wall_south
                    case Direction.LEFT:
                        blocked = cell.has_wall_west
                    case Direction.RIGHT:
                        blocked = cell.has_wall_east
 
            if blocked:
                # Snap flush to the tile center/rail and stop.
                self.x, self.y = self.calc_rail()
                self.current_dir = None
 
        # 2. Movement logic
        match self.current_dir:
            case Direction.UP:
                self.y -= self.speed * dt
            case Direction.DOWN:
                self.y += self.speed * dt
            case Direction.LEFT:
                self.x -= self.speed * dt
            case Direction.RIGHT:
                self.x += self.speed * dt
 
        # 3. Screen-edge safety clamp (last-resort guard; maze border cells
        # should already be walled/solid so this normally never triggers)
        if self.x <= 0:
            self.x = 0.0
            if self.current_dir == Direction.LEFT:
                self.current_dir = None
                
        elif self.x + self.size >= self.screen_width:
            self.x = float(self.screen_width - self.size)
            if self.current_dir == Direction.RIGHT:
                self.current_dir = None
 
        if self.y <= 0:
            self.y = 0.0
            if self.current_dir == Direction.UP:
                self.current_dir = None
                
        elif self.y + self.size >= self.screen_height:
            self.y = float(self.screen_height - self.size)
            if self.current_dir == Direction.DOWN:
                self.current_dir = None


# ==========================================
# 2. VIEW (Graphics Engine and Rendering)
# ==========================================
class GameView:
    """Handle window creation, rendering, and MLX graphical outputs."""

    def __init__(self, config: GameConfig, maze: MazeAdapter):
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
        padding = 40
        
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
        self.main_renderer.draw_player(model.x, model.y, model.size, model.color)
        
        # Draw the mini map
        self.minimap_renderer.draw_maze(model.maze)
        
        # Calculate the logical positoni in pixe of mini map
        logical_x = (model.x - self.main_renderer.offset_x) / self.main_renderer.tile_size
        logical_y = (model.y - self.main_renderer.offset_y) / self.main_renderer.tile_size

        # Convert the logical position to scaled pixels on the mini-map
        mini_px = self.minimap_renderer.offset_x + (logical_x * self.minimap_renderer.tile_size)
        mini_py = self.minimap_renderer.offset_y + (logical_y * self.minimap_renderer.tile_size)

        # Calculate the player’s size proportionally
        ratio = self.minimap_renderer.tile_size / self.main_renderer.tile_size
        mini_size = max(2, int(model.size * ratio))

        # Move the player to the new coordinates
        self.minimap_renderer.draw_player(mini_px, mini_py, mini_size, model.color)

        # mlx_put_image_to_window: Dump the completed off-screen image buffer onto the active window
        self.m.mlx_put_image_to_window(self.mlx_ptr, self.win_ptr, self.img, 0, 0)


# ==========================================
# 3. CONTROLLER (Input, Loop, and Integration)
# ==========================================
class GameController:
    """Orchestrate the game loop, user inputs, and component integration."""

    def __init__(self):
        """Initialize the Controller using Pydantic configurations."""
        
        self.config = GameConfig(width=1640, height=1000, target_fps=60)
        self.last_time = time.perf_counter()
        self.maze = MazeAdapter(seed=900)
        
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

        spawn_x, spawn_y = self.view.main_renderer.cell_to_pixel(
            self.maze.player_spawn[0], self.maze.player_spawn[1]
        )
        self.model.x = float(spawn_x + self.view.main_renderer.tile_size // 2)
        self.model.y = float(spawn_y + self.view.main_renderer.tile_size // 2)
        self.model.size = int(self.view.main_renderer.tile_size * 0.5)
        
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
            self.model.desired_dir = action
            if not self.model.started:
                self.model.started = True
                self.last_time = time.perf_counter()
        return 0

    def update_game(self, *args):
        """Manage the frame rate, trigger physics updates, and execute rendering."""
        current_time = time.perf_counter()
        dt = current_time - self.last_time
        frame_duration = 1.0 / self.config.target_fps
        self.view.render(self.model)

        if dt < frame_duration:
            return 0

        self.last_time = current_time

        self.model.update(dt)
        self.view.render(self.model)
        
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