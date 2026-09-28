import os
import time
from ..view import GameView
from pydantic import BaseModel, Field
from ..model import MazeAdapter, GameModel, Direction, GameState
from src.pac_man.model.entity import PlayerState

# ==========================================
# CONSTANTS AND KEY MAPPINGS
# ==========================================
KEY_ESC = 65307
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
    width: int = Field(
        default=1024, gt=0, description="Window width in pixels."
    )
    height: int = Field(
        default=764, gt=0, description="Window height in pixels."
    )
    title: str = Field(
        default="Pac-Man 42", min_length=1, description="Window title."
    )
    target_fps: int = Field(
        default=60, gt=0, le=240, description="Target frames per second."
    )

# ==========================================
# 3. CONTROLLER (Input, Loop, and Integration)
# ==========================================
class GameController:
    """Orchestrate the game loop, user inputs, and component integration."""

    def __init__(self):
        """Initialize the Controller using Pydantic configurations."""
        
        self.config = GameConfig(width=1640, height=1000, target_fps=60)
        self.last_time = time.perf_counter()
        self.maze = MazeAdapter(seed=900, width=7, height=7)
        
        self.view = GameView(self.config)

        # Instantiate Model dynamically from config parameters
        self.model = GameModel(
            screen_width=self.config.width,
            screen_height=self.config.height,
            maze=self.maze,
            tile_size=self.view.main_renderer.tile_size,
        )

        self.model.size = int(self.view.main_renderer.tile_size * 0.5)
        
        self.setup_hooks()
        
    def setup_hooks(self):
        """Register MLX event listeners to Controller methods."""
        m = self.view.m
        win = self.view.win_ptr
        
        # mlx_hook: Bind X11 events
        m.mlx_hook(win, EVENT_DESTROY, 0, self.close_game, None)
        m.mlx_hook(
            win, EVENT_DESTROY, STRUCTURE_NOTIFY_MASK, self.close_game, None
        )
        m.mlx_hook(win, EVENT_CLIENT_MESSAGE, 0, self.close_game, None)
        m.mlx_hook(
            win,
            EVENT_CLIENT_MESSAGE,
            STRUCTURE_NOTIFY_MASK,
            self.close_game,
            None
        )
        
        # mlx_hook: Bind keyboard press events
        m.mlx_hook(
            win, EVENT_KEY_PRESS, KEY_PRESS_MASK, self.on_key_press, None
        )
        
        # mlx_loop_hook: Main function for MLX infinite loop
        m.mlx_loop_hook(self.view.mlx_ptr, self.update_game, None)

    def close_game(self, *args):
        """Handle game shutdown and memory cleanup."""
        print("Closing game...")
        self.view.m.mlx_destroy_window(self.view.mlx_ptr, self.view.win_ptr)
        os._exit(0)

    def _handle_menu_selection(self) -> None:
        """Execute the action corresponding to the selected menu button."""
        match self.model.selected_button_index:
            case 0:
                self.model._reset_game()
                self.model.player.lives = 3
                self.model.player.state = PlayerState.ALIVE
                self.model.state = GameState.DEATH_PAUSE
            case 1:
                # TODO lead to highscores page
                print("Open Highscores...")
            case 2:
                # TODO lead to settings page
                print("Open Settings")
            case 3:
                self.close_game()
            case _:
                pass

    def on_key_press(self, keycode: int, *args):
        """Process keyboard input and update the model state."""
        if keycode in (KEY_ESC, 27, ord('q'), ord('Q')):
            self.close_game()
            
        action = KEYS_MAP.get(keycode)

        if self.model.state == GameState.PLAYING:
            if action:
                self.model.player.desired_dir = action
                
        elif self.model.state == GameState.DEATH_PAUSE:
            if action:
                self.model.player.desired_dir = action
                self.model.player.state = PlayerState.ALIVE
                self.model.state = GameState.PLAYING
                self.last_time = time.perf_counter()

        # getattr(obj, variable, default)
        elif (
            self.model.state == GameState.ENTER_NAME
            and getattr(
                self.model.highscore_manager, 'is_new_highscore', False
            )
        ):
            if keycode in (65293, 13):
                self.model.highscore_manager.add_score(
                    self.model.name_input,
                    self.model.player.score
                )
            elif ((97 <= keycode <= 122)
                  or (48 <= keycode <= 57)
                  or keycode == 32
            ):
                if len(self.model.name_input) < 10:
                    char = chr(keycode).upper()
                    self.model.name_input += char
            elif keycode == 65288:
                self.model.name_input = self.model.name_input[:-1]
                
        elif self.model.state in (GameState.GAME_OVER, GameState.START_MENU):
            num_buttons = 4

            if action == Direction.UP:
                self.model.selected_button_index = (
                    (self.model.selected_button_index - 1) % num_buttons
                )
            elif action == Direction.DOWN:
                self.model.selected_button_index = (
                    (self.model.selected_button_index + 1) % num_buttons
                )
            elif keycode in (65293, 13, 32):
                self._handle_menu_selection()
                
        return 0

    def update_game(self, *args):
        """
        update_game:
            1) Manage the frame rate,
            2) Trigger physics updates and Execute rendering.
        """
        current_time = time.perf_counter()
        dt = current_time - self.last_time
        frame_duration = 1.0 / self.config.target_fps

        if dt < frame_duration:
            return 0

        self.last_time = current_time

        # model.update(dt) UPDATE the game only in PLAYING state
        self.model.update(dt)

        if (self.model.player.state == PlayerState.DEAD
                and self.model.player.has_lives):
            pass

        # Always render the screen
        self.view.render(self.model)
        return 0

    def run(self):
        """Launch the game engine and start the event loop."""
        print(
            f"{self.config.title} Engine Running. "
            "Premi frecce o WASD per muoverti. ESC per uscire."
        )
        self.view.m.mlx_loop(self.view.mlx_ptr)

# ==========================================
# EXECUTION
# ==========================================
if __name__ == "__main__":
    game = GameController()
    game.run()