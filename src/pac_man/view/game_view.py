"""Game view module managing windows, backbuffers, and rendering."""

from dataclasses import dataclass
from typing import Any
import mlx
from .sprites_manager import SpriteManager
from ..model import Direction, GameModel, GameState, GhostState
from .colors import Colors
from .layout import ViewLayout
from .renderer import Renderer


@dataclass
class MenuButton:
    """Represents a clickable or selectable graphical menu button.

    Attributes:
        name (str): Label displayed inside the button.
        x (int): Horizontal pixel position of the button top-left.
        y (int): Vertical pixel position of the button top-left.
        w (int): Width of the button rectangle in pixels.
        h (int): Height of the button rectangle in pixels.
    """

    name: str
    x: int
    y: int
    w: int
    h: int


class GameView:
    """Handles window creation, software backbuffering, and MiniLibX rendering.

    Attributes:
        config (Any): Window and framerate configurations.
        layout (ViewLayout): Responsive UI layout and dimensions.
        m (mlx.Mlx): MiniLibX graphics interface wrapper.
        mlx_ptr (Any): MiniLibX application handle.
        sprites (SpriteManager): Preloaded sprite asset manager.
        win_ptr (Any): MiniLibX window handle.
        img (Any): Software frame backbuffer image.
        data (Any): Raw byte buffer pointer for direct pixel manipulation.
        bfp (int): Bits per pixel returned by MiniLibX.
        size_line (int): Line stride in bytes.
        bytes_per_pixel (int): Bytes per pixel (e.g. 4 for 32-bit ARGB).
        buffer_size (int): Total buffer size in bytes.
        main_renderer (Renderer): Renderer for the primary gameplay viewport.
        minimap_renderer (Renderer): Renderer for the corner minimap viewport.
        active_buttons (list[MenuButton]): Current frame menu buttons.
        anim_tick (int): Monotonic frame tick used for animations.
    """

    cheat_mode_command: tuple[str, ...] = (
        "",
        "",
        "[ 1 ] Toggle Invincibility",
        "[ 2 ] Skip Current Level",
        "[ 3 ] Freeze / Unfreeze Ghosts",
        "[ 4 ] Increase Player Speed",
        "[ 5 ] Add +1 Extra Life",
        "[ 6 ] Exit Cheat Mode",
    )

    game_rules: str = """OBJECTIVE:
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

    def __init__(self, config: Any, layout: ViewLayout | None = None) -> None:
        """Initialize the MiniLibX window, offscreen image, and renderers.

        Args:
            config (Any): Game configuration object.
            layout (ViewLayout | None): Precalculated layout geometry metrics.
        """
        self.config = config
        self.layout = (
            layout or ViewLayout.from_window_size(config.width, config.height)
        )

        self.m = mlx.Mlx()
        self.mlx_ptr = self.m.mlx_init()
        if not self.mlx_ptr:
            raise RuntimeError("Unable to connect to X11/MiniLibX display.")

        # Delegate sprite loading to SpriteManager
        self.sprites = SpriteManager(self.m, self.mlx_ptr)

        self.win_ptr = self.m.mlx_new_window(
            self.mlx_ptr,
            self.config.width,
            self.config.height,
            self.config.title
        )
        if not self.win_ptr:
            raise RuntimeError("Unable to create game window")

        self.img = self.m.mlx_new_image(
            self.mlx_ptr, self.config.width, self.config.height
        )
        self.data, self.bfp, self.size_line, _ = (
            self.m.mlx_get_data_addr(self.img)
        )

        self.bytes_per_pixel = self.bfp // 8
        self.buffer_size = self.config.height * self.size_line

        bg_color = Colors.BACKGROUND
        b_ch = bg_color & 0xFF
        g_ch = (bg_color >> 8) & 0xFF
        r_ch = (bg_color >> 16) & 0xFF
        bg_bytes = bytes([b_ch, g_ch, r_ch, 0xFF])
        self._bg_buffer = bg_bytes * (self.buffer_size // self.bytes_per_pixel)

        self.main_renderer = Renderer(
            self, tile_size=self.layout.main_tile_size
        )
        self.active_buttons: list[MenuButton] = []
        self.anim_tick: int = 0

        mini = self.layout.minimap
        self.minimap_renderer = Renderer(
            self,
            view_x=mini.padding,
            view_y=mini.padding,
            view_w=mini.size,
            view_h=mini.size,
            tile_size=mini.tile_size,
        )

        self._last_frame_key: object = None
        self._startup_frames: int = 5

    def _background_menu(self, color: int = Colors.MENU_BG) -> None:
        """Draw the background bounding box for menu overlays.

        Args:
            color (int): RGB color value for the menu box.
        """
        menu = self.layout.menu
        new_w = self.config.width - (menu.padding_x * 2)
        new_h = self.config.height - (menu.padding_y * 2)
        self.draw_rect_fast(
            coords=(menu.padding_x, menu.padding_y),
            w=new_w,
            h=new_h,
            color=color,
        )

    def draw_button(self, current_state: GameState) -> None:
        """Render text labels on active menu buttons.

        Args:
            current_state (GameState): Current game state context.
        """
        char_w = self.layout.menu.char_width_approx
        for btn in self.active_buttons:
            text_width = len(btn.name) * char_w
            text_x = btn.x + ((btn.w - text_width) // 2)
            text_y = btn.y + (btn.h // 2) - 10
            self.m.mlx_string_put(
                self.mlx_ptr,
                self.win_ptr,
                text_x,
                text_y,
                Colors.TEXT_WHITE,
                btn.name,
            )

    def draw_menu(self, button_lst: tuple[str, ...]) -> None:
        """Render a single-button overlay window (e.g. back button).

        Args:
            button_lst (tuple[str, ...]): Tuple containing the button label.
        """
        self.active_buttons.clear()
        self._background_menu(Colors.MENU_BG)

        menu = self.layout.menu
        menu_w = self.config.width - (menu.padding_x * 2)
        menu_h = self.config.height - (menu.padding_y * 2)

        btn_x = menu.padding_x + (menu_w - menu.btn_w) // 2
        btn_y = menu.padding_y + menu_h - menu.btn_h - 20

        self.draw_rect_fast(
            coords=(btn_x, btn_y),
            w=menu.btn_w,
            h=menu.btn_h,
            color=Colors.BUTTON_NORMAL,
        )
        self.active_buttons.append(
            MenuButton(
                name=button_lst[0],
                x=btn_x,
                y=btn_y,
                w=menu.btn_w,
                h=menu.btn_h,
            )
        )

    def draw_text(self, text: list[str], is_highscores: bool = False) -> None:
        """Render multiple lines of text centered inside the menu box.

        Args:
            text (list[str]): Lines of text to render.
            is_highscores (bool): True if rendering highscores with custom
                line spacing.
        """
        menu = self.layout.menu
        menu_w = self.config.width - (menu.padding_x * 2)
        menu_h = self.config.height - (menu.padding_y * 2)

        line_height = menu.line_h_normal
        if is_highscores:
            line_height = menu.line_h_highscores

        total_text_height = len(text) * line_height
        start_y = menu.padding_y + max(20, (menu_h - total_text_height) // 2)

        for i, line in enumerate(text):
            text_width = len(line) * menu.char_width_approx
            text_x = menu.padding_x + ((menu_w - text_width) // 2)
            text_y = start_y + (line_height * i)

            self.m.mlx_string_put(
                self.mlx_ptr,
                self.win_ptr,
                text_x,
                text_y,
                Colors.TEXT_WHITE,
                line,
            )

    def draw_main_menu(
        self,
        selected_index: int,
        button_lst: tuple[str, ...],
        is_enter_name: bool = False,
    ) -> None:
        """Render vertically stacked menu buttons with hover highlights.

        Args:
            selected_index (int): Currently highlighted button index.
            button_lst (tuple[str, ...]): Button label strings.
            is_enter_name (bool): True if rendering highscore name prompt.
        """
        self.active_buttons.clear()
        self._background_menu(Colors.MENU_BG)

        menu = self.layout.menu
        menu_w = self.config.width - (menu.padding_x * 2)
        menu_h = self.config.height - (menu.padding_y * 2)

        num_buttons = len(button_lst)
        total_block_height = (
            (num_buttons * menu.btn_h) + (num_buttons - 1) * menu.gap
        )
        start_x = menu.padding_x + ((menu_w - menu.btn_w) // 2)
        start_y = menu.padding_y + ((menu_h - total_block_height) // 2)

        for i in range(num_buttons):
            current_y = start_y + (i * (menu.btn_h + menu.gap))
            draw_bg = True
            color = Colors.BUTTON_NORMAL

            if is_enter_name and i == 0:
                draw_bg = False
            elif i == selected_index:
                color = Colors.BUTTON_HOVER

            if draw_bg:
                self.draw_rect_fast(
                    coords=(start_x, current_y),
                    w=menu.btn_w,
                    h=menu.btn_h,
                    color=color,
                )

            self.active_buttons.append(
                MenuButton(
                    name=button_lst[i],
                    x=start_x,
                    y=current_y,
                    w=menu.btn_w,
                    h=menu.btn_h,
                )
            )

    def clear(self) -> None:
        """Clear backbuffer memory to solid background color."""
        self.data[0: self.buffer_size] = self._bg_buffer

    def draw_rect_fast(
        self, coords: tuple[int, int], w: int, h: int, color: int
    ) -> None:
        """Quickly fill a clipped rectangular area directly into the buffer.

        Args:
            coords (tuple[int, int]): (x, y) top-left corner coordinates.
            w (int): Rectangle width in pixels.
            h (int): Rectangle height in pixels.
            color (int): RGB fill color.
        """
        b_ch = color & 0xFF
        g_ch = (color >> 8) & 0xFF
        r_ch = (color >> 16) & 0xFF

        x0, y0 = max(0, coords[0]), max(0, coords[1])
        x1, y1 = min(coords[0] + w, self.config.width), min(
            coords[1] + h, self.config.height
        )
        actual_w = x1 - x0

        if actual_w <= 0 or y1 <= y0:
            return

        row_bytes = bytes([b_ch, g_ch, r_ch, 0xFF] * actual_w)
        row_len = actual_w * self.bytes_per_pixel

        for row in range(y0, y1):
            start = row * self.size_line + x0 * self.bytes_per_pixel
            self.data[start:start + row_len] = row_bytes

    def print_game_info(self, x: int, y: int, text: list[str]) -> None:
        """Render informational HUD text lines using mlx_string_put.

        Args:
            x (int): Horizontal origin in pixels.
            y (int): Vertical origin in pixels.
            text (list[str]): Text lines to display.
        """
        line_height = self.layout.hud.line_height
        for i, line in enumerate(text):
            text_y = int(y) + (line_height * i)
            self.m.mlx_string_put(
                self.mlx_ptr,
                self.win_ptr,
                int(x),
                text_y,
                Colors.TEXT_WHITE,
                line
            )

    def draw_main_sprites(self, model: GameModel) -> None:
        """Render Pac-Man and ghost sprites in the primary game viewport.

        Args:
            model (GameModel): Current game model state.
        """
        if model.state not in (
            GameState.PLAYING,
            GameState.DEATH_PAUSE,
            GameState.CHEAT_MODE,
            GameState.LEVEL_COMPLETE,
        ):
            return

        offset = self.layout.sprite_offset

        if model.player.current_dir is None:
            current_pacman_sprite = self.sprites.pacman_ball
        else:
            p_dir = model.player.current_dir
            is_close = (self.anim_tick // 6) % 2 == 0
            sprites_dict = (
                self.sprites.pacman_semi if is_close else self.sprites.pacman
            )
            current_pacman_sprite = sprites_dict.get(
                p_dir, self.sprites.pacman_ball
            )

        px = int(model.player.x + self.main_renderer.offset_x) - offset
        py = int(model.player.y + self.main_renderer.offset_y) - offset
        self.m.mlx_put_image_to_window(
            self.mlx_ptr, self.win_ptr, current_pacman_sprite, px, py
        )

        for i, ghost in enumerate(model.ghosts):
            gx = int(ghost.x + self.main_renderer.offset_x) - offset
            gy = int(ghost.y + self.main_renderer.offset_y) - offset
            current_ghost_sprite = None

            if ghost.state in (GhostState.CHASE, GhostState.SCATTER):
                g_dir = Direction.UP
                if ghost.current_dir:
                    g_dir = ghost.current_dir
                current_ghost_sprite = self.sprites.ghosts_normal[i].get(
                    g_dir, self.sprites.ghosts_normal[i][Direction.UP]
                )
            elif ghost.state == GhostState.FRIGHTENED:
                current_ghost_sprite = self.sprites.frightened
            elif ghost.state == GhostState.EATEN:
                current_ghost_sprite = self.sprites.eaten

            if current_ghost_sprite:
                self.m.mlx_put_image_to_window(
                    self.mlx_ptr, self.win_ptr, current_ghost_sprite, gx, gy
                )

    def draw_minimap_sprites(self, model: GameModel) -> None:
        """Render miniature entity icons onto the corner minimap.

        Args:
            model (GameModel): Current game model state.
        """
        if model.state not in (
            GameState.PLAYING,
            GameState.DEATH_PAUSE,
            GameState.CHEAT_MODE,
            GameState.LEVEL_COMPLETE,
        ):
            return

        ratio = self.minimap_renderer.tile_size / self.main_renderer.tile_size
        offset = self.layout.minimap.sprite_offset

        mini_px = int(
            self.minimap_renderer.offset_x + (model.player.x * ratio)
        )
        mini_py = int(
            self.minimap_renderer.offset_y + (model.player.y * ratio)
        )
        self.m.mlx_put_image_to_window(
            self.mlx_ptr,
            self.win_ptr,
            self.sprites.mini_pacman,
            mini_px - offset,
            mini_py - offset,
        )

        for ghost in model.ghosts:
            mini_gx = int(self.minimap_renderer.offset_x + (ghost.x * ratio))
            mini_gy = int(self.minimap_renderer.offset_y + (ghost.y * ratio))
            self.m.mlx_put_image_to_window(
                self.mlx_ptr,
                self.win_ptr,
                self.sprites.mini_ghost_red,
                mini_gx - offset,
                mini_gy - offset,
            )

    def draw_finish_sprite(self, sprites: int) -> None:
        """Render centered game over or victory banner sprite.

        Args:
            sprites (int): MiniLibX image buffer handle of the banner.
        """
        sw = self.layout.finish_sprite_w
        sh = self.layout.finish_sprite_h
        x = (self.config.width - sw) // 2
        y = (self.config.height // 2) - (sh // 2) - sh
        self.m.mlx_put_image_to_window(
            self.mlx_ptr, self.win_ptr, sprites, x, y
        )

    def draw_hud(self, model: GameModel, actual_bottom_y: int) -> None:
        """Render HUD metrics, cheat indicators, and life heart icons.

        Args:
            model (GameModel): Current game model state.
            actual_bottom_y (int): Vertical coordinate baseline from minimap.
        """
        if model.state in (
            GameState.START_MENU,
            GameState.HIGHSCORES,
            GameState.INSTRUCTIONS,
            GameState.GAME_OVER,
            GameState.ENTER_NAME,
            GameState.PAUSE,
        ):
            return

        hud = self.layout.hud
        game_info = [
            f"Score: {model.player.score}",
            f"Level: {model.current_level_index + 1}",
            f"Time: {int(model.level_time_remaining)}",
            "[6] CHEAT [ESC] PAUSE",
        ]

        if model.state == GameState.CHEAT_MODE:
            game_info.extend(self.cheat_mode_command)

        start_y = actual_bottom_y + hud.offset_from_bottom
        self.print_game_info(
            x=self.minimap_renderer.view_x,
            y=start_y,
            text=game_info,
        )

        total_text_lines = len(game_info)

        heart_x_start = self.minimap_renderer.view_x + hud.inner_padding_x
        heart_y = start_y + (hud.line_height * total_text_lines) + 10
        total_heart_step = hud.heart_size + hud.heart_spacing

        for i in range(model.player.lives):
            self.m.mlx_put_image_to_window(
                self.mlx_ptr,
                self.win_ptr,
                self.sprites.heart,
                heart_x_start + (i * total_heart_step),
                heart_y,
            )

    def render(self, model: GameModel) -> None:
        """Compose and draw full game frame to MiniLibX window.

        Args:
            model (GameModel): Complete simulation state to render.
        """
        self.anim_tick += 1
        if getattr(self, "_startup_frames", 0) > 0:
            self._last_frame_key = None
            self._startup_frames -= 1

        minimap_pixel_height = (
            model.maze.height * self.minimap_renderer.tile_size
        )
        actual_bottom_y = self.minimap_renderer.offset_y + minimap_pixel_height

        static_states = (
            GameState.START_MENU,
            GameState.GAME_OVER,
            GameState.ENTER_NAME,
            GameState.HIGHSCORES,
            GameState.INSTRUCTIONS,
            GameState.CHEAT_MODE,
            GameState.PAUSE,
        )

        if model.state in static_states:
            key = (
                model.state,
                model.selected_button_index,
                model.player.lives,
                tuple(model.menu_options),
                tuple(model.highscore_manager.top_scores_text),
            )
            if key == self._last_frame_key:
                return
            self._last_frame_key = key
        else:
            self._last_frame_key = None

        # 1. Image Buffer
        self.clear()
        self.main_renderer.update_layout(model.maze)
        self.minimap_renderer.update_layout(model.maze)

        self.main_renderer.draw_maze(model.maze)
        self.minimap_renderer.draw_maze(model.maze)

        if model.state in (
            GameState.START_MENU,
            GameState.GAME_OVER,
            GameState.ENTER_NAME,
            GameState.PAUSE,
        ):
            self.draw_main_menu(
                selected_index=model.selected_button_index,
                button_lst=model.menu_options,
                is_enter_name=(model.state == GameState.ENTER_NAME),
            )
        elif model.state in (GameState.HIGHSCORES, GameState.INSTRUCTIONS):
            self.draw_menu(button_lst=model.menu_options)

        self.m.mlx_put_image_to_window(
            self.mlx_ptr, self.win_ptr, self.img, 0, 0
        )

        self.draw_main_sprites(model)
        self.draw_minimap_sprites(model)

        if model.state == GameState.ENTER_NAME:
            sprites = self.sprites.gameover
            if model.current_level_index >= len(model.config_data["levels"]):
                sprites = self.sprites.win
            self.draw_finish_sprite(sprites)

        if model.state in (
            GameState.START_MENU,
            GameState.GAME_OVER,
            GameState.ENTER_NAME,
            GameState.PAUSE,
        ):
            self.draw_button(model.state)
        elif model.state in (GameState.HIGHSCORES, GameState.INSTRUCTIONS):
            text = (
                model.highscore_manager.top_scores_text
                if model.state == GameState.HIGHSCORES
                else self.game_rules.split("\n")
            )
            self.draw_text(
                text=text, is_highscores=(model.state == GameState.HIGHSCORES)
            )
            self.draw_button(model.state)

        self.draw_hud(model, actual_bottom_y)

        if hasattr(self.m, "mlx_do_sync"):
            self.m.mlx_do_sync(self.mlx_ptr)
