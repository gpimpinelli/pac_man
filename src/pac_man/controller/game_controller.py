"""Controller module coordinating user input, game loop, and view rendering."""

import os
import time
import signal
from typing import Any
from enum import IntEnum
from pydantic import BaseModel, Field
from ..view import GameView
from ..view.layout import ViewLayout
from ..model import GameModel, Direction, GameState, PlayerState, Player


class GameConfig(BaseModel):
    """Configuration settings for window dimensions and framerate.

    Attributes:
        width (int): Window width in pixels.
        height (int): Window height in pixels.
        title (str): Window title caption.
        target_fps (int): Maximum frames rendered per second.
    """

    width: int = Field(default=1024, gt=0)
    height: int = Field(default=764, gt=0)
    title: str = Field(default="Pac-Man 42", min_length=1)
    target_fps: int = Field(default=60, gt=0, le=240)


class GameController:
    """Manages the main game loop, OS events, and links model with view.

    Attributes:
        config (GameConfig): Window and display configurations.
        layout (ViewLayout): Dynamic UI layout calculations.
        last_time (float): Timestamp of last frame execution.
        view (GameView): Graphical view and sprite manager.
        model (GameModel): Core simulation and state container.
    """

    class Key(IntEnum):
        """Standard MiniLibX and X11 keyboard keycodes."""

        ESC = 65307
        ENTER = 65293
        BACKSPACE = 65288
        SPACE = 32
        UP = 65362
        DOWN = 65364
        LEFT = 65361
        RIGHT = 65363

        ONE = 49
        TWO = 50
        THREE = 51
        FOUR = 52
        FIVE = 53
        SIX = 54

        W = 119
        S = 115
        A = 97
        D = 100

    class EventType(IntEnum):
        """X11 hook event types supported by MiniLibX."""

        KEY_PRESS = 2
        DESTROY = 17
        CLIENT_MESSAGE = 33

    class EventMask(IntEnum):
        """X11 event mask bits."""

        KEY_PRESS = 1 << 0
        STRUCTURE_NOTIFY = 1 << 17

    KEYS_MAP: dict[int, Direction] = {
        Key.UP: Direction.UP,
        Key.W: Direction.UP,
        Key.DOWN: Direction.DOWN,
        Key.S: Direction.DOWN,
        Key.LEFT: Direction.LEFT,
        Key.A: Direction.LEFT,
        Key.RIGHT: Direction.RIGHT,
        Key.D: Direction.RIGHT,
    }

    def __init__(self, config_data: dict[str, Any] | None = None) -> None:
        """Initialize game controller, view, model, and event bindings.

        Args:
            config_data (dict[str, Any] | None): Validated configuration data.
        """
        self.config = GameConfig(width=1680, height=900, target_fps=60)

        self.layout = ViewLayout.from_window_size(
            self.config.width,
            self.config.height,
        )

        self.last_time = time.perf_counter()

        self.view = GameView(self.config, self.layout)

        self.model = GameModel(
            screen_width=self.config.width,
            screen_height=self.config.height,
            tile_size=self.layout.main_tile_size,
            config_data=config_data or {},
        )

        self.model.size = self.layout.sprite_offset
        self.setup_hooks()

    @property
    def player(self) -> Player:
        """Get the active player instance from the model.

        Returns:
            Player: The player entity.
        """
        return self.model.player

    def setup_hooks(self) -> None:
        """
        Register keyboard input, window close, and frame update hooks.

        m.mlx_mouse_hide(self.view.mlx_ptr) hide the mouse cursor over the
        game window

        In WSLg, Linux graphics are bridged to Windows via Microsoft's
        Weston/RDP compositor. When an X11 application requests an empty,
        invisible cursor, Windows' RDP driver intentionally renders a
        semi-transparent
        """
        signal.signal(signal.SIGINT, self._handle_sigint)
        m = self.view.m
        win = self.view.win_ptr

        m.mlx_hook(win, self.EventType.DESTROY, 0, self.close_game, None)
        m.mlx_hook(
            win,
            self.EventType.DESTROY,
            self.EventMask.STRUCTURE_NOTIFY,
            self.close_game,
            None,
        )
        m.mlx_hook(
            win, self.EventType.CLIENT_MESSAGE, 0, self.close_game, None
        )
        m.mlx_hook(
            win,
            self.EventType.CLIENT_MESSAGE,
            self.EventMask.STRUCTURE_NOTIFY,
            self.close_game,
            None,
        )
        m.mlx_hook(
            win,
            self.EventType.KEY_PRESS,
            self.EventMask.KEY_PRESS,
            self.on_key_press,
            None,
        )
        m.mlx_loop_hook(self.view.mlx_ptr, self.update_game, None)

    def _handle_sigint(self, signum: int, frame: Any) -> None:
        """Force a clean application exit upon receiving a SIGINT signal.

        Args:
            signum (int): The specific signal number received from the OS.
            frame (Any): The current stack frame at the time of interruption.
        """
        print("\n[SIGINT] CTRL+C received. Terminating the program...")
        self.close_game()

    def close_game(self, *args: Any) -> None:
        """Terminate the game window and exit application cleanly.

        Args:
            *args (Any): MiniLibX event parameters.
        """
        print("Closing game...")
        self.view.m.mlx_destroy_window(self.view.mlx_ptr, self.view.win_ptr)
        os._exit(0)

    def _handle_menu_selection(self) -> None:
        """Execute action corresponding to currently selected menu option."""
        options = self.model.menu_options
        if not options:
            return

        selected_text = options[self.model.selected_button_index]
        if selected_text in ("START", "RETRY"):
            self.model._load_level(is_first=True)
            self.player.lives = self.model.config_data.get("lives", 3)
            self.player.score = 0
            self.player.state = PlayerState.ALIVE
            self.model.state = GameState.DEATH_PAUSE

        elif selected_text == "SAVE SCORE":
            name = "PLAYER"
            if self.model.name_input:
                name = self.model.name_input.strip()
            self.model.highscore_manager.add_score(
                name, self.player.score
            )
            self.model.name_input = ""
            self.model.state = GameState.GAME_OVER
            self.model.selected_button_index = 0

        elif selected_text == "RESUME":
            self.model.state = GameState.PLAYING
            self.last_time = time.perf_counter()

        elif selected_text == "HIGHSCORES":
            self.model.state = GameState.HIGHSCORES
            self.model.selected_button_index = 0

        elif selected_text == "INSTRUCTIONS":
            self.model.state = GameState.INSTRUCTIONS
            self.model.selected_button_index = 0

        elif selected_text in ("MAIN MENU", "EXIT"):
            if selected_text == "EXIT":
                self.close_game()
            else:
                self.model.state = GameState.START_MENU
                self.model.selected_button_index = 0

        elif selected_text == "ENTER TO GO BACK":
            self.model.state = GameState.START_MENU
            self.model.selected_button_index = 0

    def _pause_game(self, action: Direction | None) -> None:
        """Unpause game on player input when waiting in death/ready state.

        Args:
            action (Direction | None): Player movement direction inputted.
        """
        if action:
            self.player.desired_dir = action
            self.player.state = PlayerState.ALIVE
            self.model.state = GameState.PLAYING
            self.last_time = time.perf_counter()

    def on_key_press(self, keycode: int, *args: Any) -> None:
        """Handle keyboard key press events from MiniLibX window hook.

        Args:
            keycode (int): Pressed keycode value.
            *args (Any): Additional MiniLibX hook arguments.
        """
        action = self.KEYS_MAP.get(keycode)

        if self.model.state == GameState.PLAYING:
            if action:
                self.player.desired_dir = action
            elif keycode == self.Key.SIX:
                self.model.state = GameState.CHEAT_MODE
            elif (
                keycode in
                (self.Key.ESC, 27, ord("p"), ord("P"), ord("q"), ord("Q"))
            ):
                self.model.state = GameState.PAUSE
                self.model.selected_button_index = 0

        elif self.model.state == GameState.CHEAT_MODE:
            match keycode:
                case self.Key.ONE:
                    self.model.toggle_invincible()
                case self.Key.TWO:
                    self.model.level_skip()
                case self.Key.THREE:
                    self.model._freeze_ghosts()
                case self.Key.FOUR:
                    self.model.increase_speed()
                case self.Key.FIVE:
                    self.model.add_lives()
                case self.Key.SIX:
                    self.player.reset_movement()
                    self.model.state = GameState.DEATH_PAUSE

        elif self.model.state == GameState.DEATH_PAUSE:
            self._pause_game(action)

        elif self.model.state == GameState.ENTER_NAME:
            if keycode in (self.Key.ENTER, 13):
                self.model.selected_button_index = 2
                self._handle_menu_selection()
            elif keycode in (self.Key.UP, self.Key.DOWN):
                if self.model.selected_button_index == 0:
                    self.model.selected_button_index = 1
                else:
                    self.model.selected_button_index = (
                        3 - self.model.selected_button_index
                    )
            elif (
                (97 <= keycode <= 122)
                or (48 <= keycode <= 57)
                or keycode == self.Key.SPACE
            ):
                if len(self.model.name_input) < 10:
                    self.model.name_input += chr(keycode).upper()
            elif keycode in (self.Key.BACKSPACE, 65288):
                self.model.name_input = self.model.name_input[:-1]

        elif self.model.state in (
            GameState.GAME_OVER,
            GameState.START_MENU,
            GameState.HIGHSCORES,
            GameState.INSTRUCTIONS,
            GameState.PAUSE,
        ):
            if self.model.state == GameState.PAUSE and keycode in (
                self.Key.ESC,
                27,
                ord("p"),
                ord("P"),
            ):
                self.model.state = GameState.PLAYING
                self.last_time = time.perf_counter()
                return

            options = self.model.menu_options
            num_buttons = len(options) if options else 1

            if action == Direction.UP:
                self.model.selected_button_index = (
                    self.model.selected_button_index - 1
                ) % num_buttons
            elif action == Direction.DOWN:
                self.model.selected_button_index = (
                    self.model.selected_button_index + 1
                ) % num_buttons
            elif keycode in (self.Key.ENTER, 13, self.Key.SPACE):
                self._handle_menu_selection()

        return

    def update_game(self, *args: Any) -> None:
        """MiniLibX loop hook updating physics at target framerate.

        Args:
            *args (Any): MiniLibX loop callback arguments.
        """
        current_time = time.perf_counter()
        dt = current_time - self.last_time
        frame_duration = 1.0 / self.config.target_fps

        if dt < frame_duration:
            return

        self.last_time = current_time
        self.model.update(dt)
        self.view.render(self.model)

    def run(self) -> None:
        """Start the MiniLibX graphical event loop."""
        print(
            f"{self.config.title} Engine Running. "
            "Press arrows or WASD to move. ESC to pause."
        )
        self.view.m.mlx_loop(self.view.mlx_ptr)


if __name__ == "__main__":
    game = GameController()
    game.run()
