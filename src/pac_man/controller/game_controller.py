import os
import time
from typing import Any
from ..view import GameView
from pydantic import BaseModel, Field
from ..model import GameModel, Direction, GameState
from src.pac_man.model.entity import PlayerState
from enum import IntEnum


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
    game_rules: str = (
        """OBJECTIVE:
Eat all the Pac-Gums in the maze to clear the level
and advance before time runs out. Avoid the ghosts!

    Move Up:    [ W ] or [ UP ARROW ]
    Move Left:  [ A ] or [ LEFT ARROW ]
    Move Down:  [ S ] or [ DOWN ARROW ]
    Move Right: [ D ] or [ RIGHT ARROW ]
    Pause/Menu: [ ESC ] or [ P ]

    Collect regular dots (Pac-Gums) to gain score.
    Collect corner Super Pac-Gums to turn ghosts blue!
    While blue, ghosts will flee: touch them to eat
    them and send them back to their corner!
    You start with 3 lives. Colliding with a normal 
    ghost costs 1 life and respawns you in the center."""
    )

# ==========================================
# 3. CONTROLLER (Input, Loop, and Integration)
# ==========================================
class GameController:
    """Orchestrate the game loop, user inputs, and component integration."""
    # ==========================================
    # CONSTANTS AND KEY MAPPINGS
    # ==========================================
    
    class Key(IntEnum):
        ESC = 65307
        ENTER = 65293
        BACKSPACE = 65288
        SPACE = 32
        UP = 65362
        DOWN = 65364
        LEFT = 65361
        RIGHT = 65363
        W = 119
        S = 115
        A = 97
        D = 100

    class EventType(IntEnum):
        KEY_PRESS = 2
        DESTROY = 17
        CLIENT_MESSAGE = 33

    class EventMask(IntEnum):
        KEY_PRESS = 1 << 0
        STRUCTURE_NOTIFY = 1 << 17

    KEYS_MAP = {
        Key.UP: Direction.UP,
        Key.W: Direction.UP,
        Key.DOWN: Direction.DOWN,
        Key.S: Direction.DOWN,
        Key.LEFT: Direction.LEFT,
        Key.A: Direction.LEFT,
        Key.RIGHT: Direction.RIGHT,
        Key.D: Direction.RIGHT,
    }

    def __init__(self, config_data: dict[str, Any] = None):
        """Initialize the Controller using Pydantic configurations."""
        
        self.config = GameConfig(width=1640, height=1000, target_fps=60)

        self.last_time = time.perf_counter()
        
        self.view = GameView(self.config)

        # Instantiate Model dynamically from config parameters
        self.model = GameModel(
            screen_width=self.config.width,
            screen_height=self.config.height,
            tile_size=self.view.main_renderer.tile_size,
            config_data=config_data
        )

        self.model.size = int(self.view.main_renderer.tile_size * 0.5)
        
        self.setup_hooks()
        
    def setup_hooks(self):
        """Register MLX event listeners to Controller methods."""
        m = self.view.m
        win = self.view.win_ptr
        
        # mlx_hook: Bind X11 events
        m.mlx_hook(win, self.EventType.DESTROY, 0, self.close_game, None)
        m.mlx_hook(
            win, self.EventType.DESTROY, self.EventMask.STRUCTURE_NOTIFY, self.close_game, None
        )
        m.mlx_hook(win, self.EventType.CLIENT_MESSAGE, 0, self.close_game, None)
        m.mlx_hook(
            win,
            self.EventType.CLIENT_MESSAGE,
            self.EventMask.STRUCTURE_NOTIFY,
            self.close_game,
            None
        )
        
        # mlx_hook: Bind keyboard press events
        m.mlx_hook(
            win, self.EventType.KEY_PRESS, self.EventMask.KEY_PRESS, self.on_key_press, None
        )
        
        # mlx_loop_hook: Main function for MLX infinite loop
        m.mlx_loop_hook(self.view.mlx_ptr, self.update_game, None)

    def close_game(self, *args):
        """Handle game shutdown and memory cleanup."""
        print("Closing game...")
        self.view.m.mlx_destroy_window(self.view.mlx_ptr, self.view.win_ptr)
        os._exit(0)

    def _handle_menu_selection(self) -> None:
        options = self.model.menu_options
        if not options:
            return
            
        selected_text = options[self.model.selected_button_index]
        if selected_text in ("START", "RETRY"):
            self.model._load_level(is_first=True)
            self.model.player.lives = self.model.config_data.get("lives", 3)
            self.model.player.score = 0
            self.model.player.state = PlayerState.ALIVE
            self.model.state = GameState.DEATH_PAUSE
            
        elif selected_text == "SAVE SCORE":
            if self.model.name_input.strip():
                self.model.highscore_manager.add_score(
                    self.model.name_input, self.model.player.score
                )

            self.model.name_input = ""
            self.model.state = GameState.GAME_OVER
            self.model.selected_button_index = 0
        
        elif selected_text == "HIGHSCORES":
            self.model.state = GameState.HIGHSCORES
            self.model.selected_button_index = 0

        elif selected_text == "INSTRUCTIONS":
            self.model.state = GameState.INSTRUCTIONS
            self.model.selected_button_index = 0
            
        elif selected_text == "MAIN MENU" or selected_text == "EXIT":
            if selected_text == "EXIT":
                self.close_game()
            else:
                self.model.state = GameState.START_MENU
                self.model.selected_button_index = 0

        elif selected_text == "ENTER TO GO BACK":
            self.model.state = GameState.START_MENU
            self.model.selected_button_index = 0


    def on_key_press(self, keycode: int, *args):
        if keycode in (self.Key.ESC, 27, ord('q'), ord('Q')):
            self.close_game()
            
        action = self.KEYS_MAP.get(keycode)

        if self.model.state == GameState.PLAYING:
            if action:
                self.model.player.desired_dir = action
                
        elif self.model.state == GameState.DEATH_PAUSE:
            if action:
                self.model.player.desired_dir = action
                self.model.player.state = PlayerState.ALIVE
                self.model.state = GameState.PLAYING
                self.last_time = time.perf_counter()

        elif self.model.state == GameState.ENTER_NAME:
            if keycode in (self.Key.ENTER, 13):
                self.model.selected_button_index = 2
                self._handle_menu_selection()
            
            elif keycode in (self.Key.UP, self.Key.DOWN):
                if self.model.selected_button_index == 0:
                    self.model.selected_button_index = 1
                else:
                    # Alterna elegantemente tra 1 e 2
                    self.model.selected_button_index = 3 - self.model.selected_button_index

            elif (
                (97 <= keycode <= 122) or (48 <= keycode <= 57) or keycode == self.key.SPACE
            ):
                # Limite di 10 caratteri per non sbordare
                if len(self.model.name_input) < 10:
                    self.model.name_input += chr(keycode).upper()

            elif keycode == 65288:
                self.model.name_input = self.model.name_input[:-1]
                
        elif self.model.state in (
            GameState.GAME_OVER,
            GameState.START_MENU,
            GameState.HIGHSCORES,
            GameState.INSTRUCTIONS
        ):
            options = self.model.menu_options
            num_buttons = len(options) if options else 1

            if action == Direction.UP:
                self.model.selected_button_index = (self.model.selected_button_index - 1) % num_buttons
            elif action == Direction.DOWN:
                self.model.selected_button_index = (self.model.selected_button_index + 1) % num_buttons
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