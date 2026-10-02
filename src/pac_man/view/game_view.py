from dataclasses import dataclass
import os
from typing import Any
import mlx

from src.pac_man.model.entity import GhostState
from ..model import Direction, GameModel, GameState
from .colors import Colors
from .layout import ViewLayout
from .renderer import Renderer


@dataclass
class MenuButton:
    name: str
    x: int
    y: int
    w: int
    h: int


class GameView:
    """Handle window creation, rendering, and MLX graphical outputs."""

    cheat = ("Press [ 6 ] -> CHEAT",)

    cheat_mode_command: tuple[str, ...] = (
        "",
        "",
        "[ 1 ] Toggle Invincibility",
        "[ 2 ] Skip Current Level",
        "[ 3 ] Freeze / Unfreeze Ghosts",
        "[ 4 ] Add +1 Extra Life",
        "[ 5 ] Increase Player Speed",
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
        self.config = config
        self.layout = layout or ViewLayout.from_window_size(
            config.width, config.height
        )

        self.m = mlx.Mlx()
        self.mlx_ptr = self.m.mlx_init()

        current_dir = os.path.dirname(os.path.abspath(__file__))
        sprites_dir = os.path.join(current_dir, "sprites")

        def load_sprite(filename: str):
            base_name = os.path.splitext(filename)[0]
            path = os.path.join(sprites_dir, f"{base_name}.xpm")
            return self.m.mlx_xpm_file_to_image(self.mlx_ptr, path)[0]

        # 1. Carica Pac-Man
        self.pacman_sprites = {
            Direction.UP: load_sprite("pacman_up.xpm"),
            Direction.DOWN: load_sprite("pacman_down.xpm"),
            Direction.LEFT: load_sprite("pacman_left.xpm"),
            Direction.RIGHT: load_sprite("pacman_right.xpm"),
        }

        # 2. Carica i 4 fantasmi
        ghost_colors = ["red", "pink", "blu", "orange"]
        self.ghost_normal_sprites = []
        for color in ghost_colors:
            self.ghost_normal_sprites.append(
                {
                    Direction.UP: load_sprite(f"{color}_up.xpm"),
                    Direction.DOWN: load_sprite(f"{color}_down.xpm"),
                    Direction.LEFT: load_sprite(f"{color}_left.xpm"),
                    Direction.RIGHT: load_sprite(f"{color}_right.xpm"),
                }
            )

        # 3. Carica sprite speciali e UI
        self.sprite_frightened = load_sprite("ghost_eaten.xpm")
        self.sprite_eaten = load_sprite("eaten.xpm")
        self.sprite_heart = load_sprite("heart.xpm")
        self.sprite_gameover = load_sprite("gameover.xpm")
        self.sprite_win = load_sprite("win.xpm")

        # Inizializzazione Finestra e Buffer
        self.win_ptr = self.m.mlx_new_window(
            self.mlx_ptr, self.config.width, self.config.height, self.config.title
        )
        self.img = self.m.mlx_new_image(
            self.mlx_ptr, self.config.width, self.config.height
        )
        self.data, self.bfp, self.size_line, _ = self.m.mlx_get_data_addr(
            self.img
        )

        self.bytes_per_pixel = self.bfp // 8
        self.buffer_size = self.config.height * self.size_line

        bg_color = Colors.BACKGROUND
        b_ch = bg_color & 0xFF
        g_ch = (bg_color >> 8) & 0xFF
        r_ch = (bg_color >> 16) & 0xFF
        bg_bytes = bytes([b_ch, g_ch, r_ch, 0xFF])
        self._bg_buffer = bg_bytes * (self.buffer_size // self.bytes_per_pixel)

        # Renderers
        self.main_renderer = Renderer(
            self,
            tile_size=self.layout.main_tile_size
        )
        self.active_buttons: list[MenuButton] = []

        mini = self.layout.minimap
        self.minimap_renderer = Renderer(
            self,
            view_x=mini.padding,
            view_y=mini.padding,
            view_w=mini.size,
            view_h=mini.size,
            tile_size=mini.tile_size,
        )

        mini_sprites_dir = os.path.join(sprites_dir, "mini")

        def load_mini_sprite(filename: str):
            path = os.path.join(mini_sprites_dir, filename)
            return self.m.mlx_xpm_file_to_image(self.mlx_ptr, path)[0]

        self.mini_pacman = load_mini_sprite("pacman_right.xpm")
        self.mini_ghost_red = load_mini_sprite("red_up.xpm")

        self._last_frame_key: object = None
        self._startup_frames: int = 5

    def _background_menu(self, color: int = Colors.MENU_BG) -> None:
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
        menu = self.layout.menu
        menu_w = self.config.width - (menu.padding_x * 2)
        menu_h = self.config.height - (menu.padding_y * 2)

        line_height = (
            menu.line_h_highscores if is_highscores else menu.line_h_normal
        )
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
        self.active_buttons.clear()
        self._background_menu(Colors.MENU_BG)

        menu = self.layout.menu
        menu_w = self.config.width - (menu.padding_x * 2)
        menu_h = self.config.height - (menu.padding_y * 2)

        num_buttons = len(button_lst)
        total_block_height = (num_buttons * menu.btn_h) + (
            (num_buttons - 1) * menu.gap
        )
        start_x = menu.padding_x + ((menu_w - menu.btn_w) // 2)
        start_y = menu.padding_y + ((menu_h - total_block_height) // 2)

        for i in range(num_buttons):
            current_y = start_y + (i * (menu.btn_h + menu.gap))
            draw_bg = True
            color = Colors.BUTTON_NORMAL

            if is_enter_name and i == 0:
                draw_bg = False
            elif is_enter_name and i == 1:
                color = (
                    Colors.BUTTON_NORMAL
                    if i != selected_index
                    else Colors.BUTTON_HOVER
                )
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
        self.data[0 : self.buffer_size] = self._bg_buffer

    def draw_rect_fast(
        self, coords: tuple[int, int], w: int, h: int, color: int
    ) -> None:
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
            self.data[start : start + row_len] = row_bytes

    def print_game_info(self, x: int, y: int, text: list[str]) -> None:
        line_height = self.layout.hud.line_height
        for i, line in enumerate(text):
            text_y = int(y) + (line_height * i)
            self.m.mlx_string_put(
                self.mlx_ptr, self.win_ptr, int(x), text_y, Colors.TEXT_WHITE, line
            )

    def draw_main_sprites(self, model: GameModel) -> None:
        # Include anche LEVEL_COMPLETE così Pac-Man e i fantasmi restano visibili durante l'attesa
        if model.state not in (
            GameState.PLAYING,
            GameState.DEATH_PAUSE,
            GameState.CHEAT_MODE,
            GameState.LEVEL_COMPLETE,
        ):
            return

        offset = self.layout.sprite_offset
        default_pacman = self.pacman_sprites[Direction.RIGHT]
        current_pacman_sprite = self.pacman_sprites.get(
            model.player.current_dir, default_pacman
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
                g_dir = ghost.current_dir if ghost.current_dir else Direction.UP
                current_ghost_sprite = self.ghost_normal_sprites[i][g_dir]
            elif ghost.state == GhostState.FRIGHTENED:
                current_ghost_sprite = self.sprite_frightened
            elif ghost.state == GhostState.EATEN:
                current_ghost_sprite = self.sprite_eaten

            if current_ghost_sprite:
                self.m.mlx_put_image_to_window(
                    self.mlx_ptr, self.win_ptr, current_ghost_sprite, gx, gy
                )

    def draw_minimap_sprites(self, model: GameModel) -> None:
        if model.state not in (
            GameState.PLAYING,
            GameState.DEATH_PAUSE,
            GameState.CHEAT_MODE,
            GameState.LEVEL_COMPLETE,
        ):
            return

        ratio = self.minimap_renderer.tile_size / self.main_renderer.tile_size
        offset = self.layout.minimap.sprite_offset

        mini_px = int(self.minimap_renderer.offset_x + (model.player.x * ratio))
        mini_py = int(self.minimap_renderer.offset_y + (model.player.y * ratio))
        self.m.mlx_put_image_to_window(
            self.mlx_ptr,
            self.win_ptr,
            self.mini_pacman,
            mini_px - offset,
            mini_py - offset,
        )

        for ghost in model.ghosts:
            mini_gx = int(
                self.minimap_renderer.offset_x + (ghost.x * ratio)
            )
            mini_gy = int(
                self.minimap_renderer.offset_y + (ghost.y * ratio)
            )
            self.m.mlx_put_image_to_window(
                self.mlx_ptr,
                self.win_ptr,
                self.mini_ghost_red,
                mini_gx - offset,
                mini_gy - offset,
            )

    def draw_finish_sprite(self, sprites: int) -> None:
        sw = self.layout.finish_sprite_w
        sh = self.layout.finish_sprite_h
        x = (self.config.width - sw) // 2
        y = (self.config.height // 2) - (sh // 2) - sh
        self.m.mlx_put_image_to_window(
            self.mlx_ptr, self.win_ptr, sprites, x, y
        )

    def draw_hud(self, model: GameModel, actual_bottom_y: int) -> None:
        # Non mostrare l'HUD nei menu
        if model.state in (
            GameState.START_MENU,
            GameState.HIGHSCORES,
            GameState.INSTRUCTIONS,
            GameState.GAME_OVER,
            GameState.ENTER_NAME,
        ):
            return

        hud = self.layout.hud
        game_info = [
            f"Score: {model.player.score}",
            f"Level: {model.current_level_index + 1}",
            f"Time: {int(model.level_time_remaining)}",
            f"{self.cheat[0]}",
        ]

        if model.state == GameState.CHEAT_MODE:
            game_info.extend(self.cheat_mode_command)

        start_y = actual_bottom_y + hud.offset_from_bottom
        self.print_game_info(
            x=self.minimap_renderer.view_x,
            y=start_y,
            text=game_info,
        )

        # Stampa dei cuori posizionati in modo FISSO sotto le prime 4 righe
        heart_x_start = self.minimap_renderer.view_x + hud.inner_padding_x
        heart_y = start_y + (hud.line_height * 4) + 10
        total_heart_step = hud.heart_size + hud.heart_spacing

        for i in range(model.player.lives):
            self.m.mlx_put_image_to_window(
                self.mlx_ptr,
                self.win_ptr,
                self.sprite_heart,
                heart_x_start + (i * total_heart_step),
                heart_y,
            )

    def render(self, model: GameModel) -> None:
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
        )

        # Gestione cache frame statici (senza disegnare i cuori all'interno)
        if model.state in static_states:
            key = (
                self.cheat,
                model.state,
                model.selected_button_index,
                model.player.lives,
                model.player.speed,
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
        ):
            self.draw_main_menu(
                selected_index=model.selected_button_index,
                button_lst=model.menu_options,
                is_enter_name=(model.state == GameState.ENTER_NAME),
            )
        elif model.state in (GameState.HIGHSCORES, GameState.INSTRUCTIONS):
            self.draw_menu(button_lst=model.menu_options)

        # 2. Presentazione finestra
        self.m.mlx_put_image_to_window(
            self.mlx_ptr, self.win_ptr, self.img, 0, 0
        )

        # 3. Sprites entità (visibili anche in LEVEL_COMPLETE)
        self.draw_main_sprites(model)
        self.draw_minimap_sprites(model)

        if model.state == GameState.ENTER_NAME:
            sprites = self.sprite_gameover
            if model.current_level_index >= len(model.config_data["levels"]):
                sprites = self.sprite_win
            self.draw_finish_sprite(sprites)

        # 4. Elementi interattivi e Testi
        if model.state in (
            GameState.START_MENU,
            GameState.GAME_OVER,
            GameState.ENTER_NAME,
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

        # 5. HUD e Cuori
        self.draw_hud(model, actual_bottom_y)

        if hasattr(self.m, "mlx_do_sync"):
            self.m.mlx_do_sync(self.mlx_ptr)