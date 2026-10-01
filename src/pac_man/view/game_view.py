"""
Pac-Man clone using the MiniLibX (mlx) library.

This module implements a basic Pac-Man style movement engine utilizing
the Model-View-Controller (MVC) architectural pattern, enhanced with Pydantic.
"""
import os
import mlx
from typing import Any
from .colors import Colors
from .renderer import Renderer
from dataclasses import dataclass
from ..model import GameModel, GameState, HighscoreManager, Direction
from src.pac_man.model.entity import GhostState



@dataclass
class MenuButton:
    name: str
    x: int
    y: int
    w: int
    h: int

# ==========================================
# 2. VIEW (Graphics Engine and Rendering)
# ==========================================
class GameView:
    """Handle window creation, rendering, and MLX graphical outputs."""
    cheat = ("Press [ 6 ] -> CHEAT",)

    cheat_mode_command: str = (
        "",
        "",
        "[ 1 ] Toggle Invincibility",
        "[ 2 ] Skip Current Level",
        "[ 3 ] Freeze / Unfreeze Ghosts",
        "[ 4 ] Add +1 Extra Life",
        "[ 5 ] Increase Player Speed",
        "[ 6 ] Exit Cheat Mode"
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
    def __init__(self, config: Any) -> None:
        """Initialize the MLX graphical environment using validated config."""
        self.config = config
        
        self.m = mlx.Mlx()
        
        # mlx_init: Establish a connection to the X-Server
        self.mlx_ptr = self.m.mlx_init()

        current_dir = os.path.dirname(os.path.abspath(__file__))
        sprites_dir = os.path.join(current_dir, "sprites")

     
        def load_sprite(filename: str):
            # Sostituisce l'estensione .png con .xpm
            base_name = os.path.splitext(filename)[0]
            path = os.path.join(sprites_dir, f"{base_name}.xpm")
            
            # Usa la funzione XPM del wrapper
            return self.m.mlx_xpm_file_to_image(self.mlx_ptr, path)[0]

        # 1. Carica Pac-Man
        self.pacman_sprites = {
            Direction.UP: load_sprite("pacman_up.xpm"),
            Direction.DOWN: load_sprite("pacman_down.xpm"),
            Direction.LEFT: load_sprite("pacman_left.xpm"),
            Direction.RIGHT: load_sprite("pacman_right.xpm"),
        }

        ghost_colors = ["red", "pink", "blu", "orange"]
        self.ghost_normal_sprites = []

        # 2. Carica i 4 fantasmi (nota l'uso della 'f' per interpolare la stringa)
        for color in ghost_colors:
            sprites_per_dir = {
                Direction.UP: load_sprite(f"{color}_up.xpm"),
                Direction.DOWN: load_sprite(f"{color}_down.xpm"),
                Direction.LEFT: load_sprite(f"{color}_left.xpm"),
                Direction.RIGHT: load_sprite(f"{color}_right.xpm"),
            }
            self.ghost_normal_sprites.append(sprites_per_dir)

        # 3. Carica gli sprites speciali
        self.sprite_frightened = load_sprite("ghost_eaten.xpm") 
        self.sprite_eaten = load_sprite("eaten.xpm")
        
        # 4. Load heart sprite
        self.sprite_heart = load_sprite("heart.xpm")

        self.sprite_gameover = load_sprite("gameover.xpm")

        self.sprite_win = load_sprite("win.xpm")

        # mlx_new_window: Create a new window on the screen
        self.win_ptr = self.m.mlx_new_window(
            self.mlx_ptr,
            self.config.width,
            self.config.height,
            self.config.title
        )
        
        # mlx_new_image: Create an off-screen image buffer in memory
        self.img = self.m.mlx_new_image(
            self.mlx_ptr,
            self.config.width,
            self.config.height
        )

        # mlx_get_data_addr: Retrieve the memory address of the image
        self.data, self.bfp, self.size_line, _ = self.m.mlx_get_data_addr(self.img)
        
        self.bytes_per_pixel = self.bfp // 8
        self.buffer_size = self.config.height * self.size_line
        
        bg_color = Colors.BACKGROUND
        
        b_ch = bg_color & 0xFF
        g_ch = (bg_color >> 8) & 0xFF
        r_ch = (bg_color >> 16) & 0xFF
        
        bg_bytes = bytes([b_ch, g_ch, r_ch, 0xFF])
        self._bg_buffer = bg_bytes * (self.buffer_size // self.bytes_per_pixel)

        self.main_renderer = Renderer(self)

        self.active_buttons: list[MenuButton] = []

        # Menu padding
        self.padding_menu: tuple[int, int] = (
            self.config.width // 4 + 100,
            self.config.height // 4 - 50
        )

        # Renderer Minimap
        minimap_size = 200
        padding = 50

        self.minimap_renderer = Renderer(
            self, 
            view_x=padding,
            view_y=padding,
            view_w=minimap_size, 
            view_h=minimap_size,
            tile_size=10
        )

        mini_sprites_dir = os.path.join(sprites_dir, "mini")
        
        def load_mini_sprite(filename: str):
            path = os.path.join(mini_sprites_dir, filename)
            return self.m.mlx_xpm_file_to_image(self.mlx_ptr, path)[0]

        self.mini_pacman = load_mini_sprite("pacman_right.xpm")
        self.mini_ghost_red = load_mini_sprite("red_up.xpm")


        self._last_frame_key: object = None
        self._startup_frames: int = 5

    def _background_menu(
        self, padding: tuple[int, int], w: int, h: int, color: int=Colors.MENU_BG
    ) -> None:
        new_w = w - (padding[0] * 2)
        new_h = h - (padding[1] * 2)

        self.draw_rect_fast(
            coords=(padding[0], padding[1]),
            w=new_w,
            h=new_h, 
            color=color
        )

    def draw_button(self, current_state: GameState) -> None:
        
        for i, btn in enumerate(self.active_buttons):
            text_color = Colors.TEXT_WHITE
            
            if current_state == GameState.ENTER_NAME and i == 0:
                text_color = Colors.TEXT_WHITE

            if current_state == GameState.ENTER_NAME and i == 1:
                text_color = Colors.TEXT_WHITE

            text_width = len(btn.name) * 10
            text_x = btn.x + ((btn.w - text_width) // 2)
            text_y = btn.y + (btn.h // 2) - 10
            
            self.m.mlx_string_put(
                self.mlx_ptr, 
                self.win_ptr, 
                text_x, 
                text_y,
                text_color, 
                btn.name
            )

    def draw_menu(
            self, w: int, h: int,
            button_lst: tuple[str, ...]
    ) -> None:
        """Disegna solo lo sfondo del menu highscores nel buffer dell'immagine."""
        self.active_buttons.clear()
        # Creiamo un helper che accetta il nome, unisce il path, 
        # lo codifica e restituisce SOLO il puntatore dell'immagine [0]

        self._background_menu(self.padding_menu, w, h, Colors.MENU_BG)

        menu_w = w - (self.padding_menu[0] * 2)
        menu_h = h - (self.padding_menu[1] * 2)

        btn_w, btn_h = 200, 50
        btn_x = self.padding_menu[0] + (menu_w - btn_w) // 2
        btn_y = self.padding_menu[1] + menu_h - btn_h - 20

        self.draw_rect_fast(
            coords=(btn_x, btn_y),
            w=btn_w,
            h=btn_h, 
            color=Colors.BUTTON_NORMAL
        )
        self.active_buttons.append(
            MenuButton(name=button_lst[0], x=btn_x, y=btn_y, w=btn_w, h=btn_h)
        )

    def draw_text(self, w: int, h: int, text: list[str], is_highscores: bool = False) -> None:
        """Disegna il testo centrato direttamente sulla finestra (dopo il put_image)."""
        menu_w = w - (self.padding_menu[0] * 2)
        menu_h = h - (self.padding_menu[1] * 2)

        line_height = 30 if is_highscores else 20
        total_text_height = len(text) * line_height

        # Calcola la coordinata Y di partenza per centrare le righe anche verticalmente
        start_y = self.padding_menu[1] + max(20, (menu_h - total_text_height) // 2)

        for i, line in enumerate(text):
            # Stima della larghezza del font bitmap predefinito (~10 px per carattere)
            text_width = len(line) * 10
            
            # Centratura orizzontale esatta rispetto al box del menu
            text_x = self.padding_menu[0] + ((menu_w - text_width) // 2)
            text_y = start_y + (line_height * i)

            self.m.mlx_string_put(
                self.mlx_ptr,
                self.win_ptr,
                text_x,
                text_y,
                Colors.TEXT_WHITE,
                line
            )

    def draw_main_menu(
            self,
            w: int,
            h: int,
            selected_index: int,
            button_lst: tuple[str, ...],
            is_enter_name: bool = False
    ) -> None: 
        
        self.active_buttons.clear()
        self._background_menu(self.padding_menu, w, h, Colors.MENU_BG)
        
        menu_x = self.padding_menu[0]
        menu_y = self.padding_menu[1]
        
        menu_w = w - (menu_x * 2)
        menu_h = h - (menu_y * 2)
        
        num_buttons = len(button_lst)
        btn_w = 200
        btn_h = 50
        gap = 20

        
        total_block_height = (num_buttons * btn_h) + ((num_buttons - 1) * gap)
        start_x = menu_x + ((menu_w - btn_w) // 2)
        start_y = menu_y + ((menu_h - total_block_height) // 2)
        
        for i in range(num_buttons):
            current_y = start_y + (i * (btn_h + gap))
            
            draw_bg = True
            color = Colors.BUTTON_NORMAL

            if is_enter_name and i == 0:
                # Non disegna il rettangolo, mostrando direttamente il rosa del menu
                draw_bg = False
            elif is_enter_name and i == 1:
                # Sfondo bianco per l'input; diventa leggermente grigio se selezionato
                color = Colors.BUTTON_NORMAL if i != selected_index else Colors.BUTTON_HOVER
            elif i == selected_index:
                color = Colors.BUTTON_HOVER

            if draw_bg:
                self.draw_rect_fast(
                    coords=(start_x, current_y), 
                    w=btn_w, 
                    h=btn_h, 
                    color=color
                )
            
            new_button = MenuButton(
                name=button_lst[i],
                x=start_x, 
                y=current_y, 
                w=btn_w, 
                h=btn_h
            )
            self.active_buttons.append(new_button)

    def clear(self) -> None:
        """Wipe the screen buffer instantly 
         using a pre-calculated byte array."""
        self.data[0:self.buffer_size] = self._bg_buffer

    def draw_rect_fast(
        self, coords: tuple[int, int], w: int, h: int, color: int
    ) -> None:
        """
        Draw a solid rectangle in the image buffer using direct byte manipulation.
        """
        b_ch = color & 0xFF
        g_ch = (color >> 8) & 0xFF
        r_ch = (color >> 16) & 0xFF

        x0, y0 = max(0, coords[0]), max(0, coords[1])
        x1, y1 = min(
            coords[0] + w, self.config.width), min(coords[1] + h, self.config.height
        )
        actual_w = x1 - x0
        
        if actual_w <= 0 or y1 <= y0:
            return
        # Creiamo un helper che accetta il nome, unisce il path, 
        # lo codifica e restituisce SOLO il puntatore dell'immagine [0]

        row_bytes = bytes([b_ch, g_ch, r_ch, 0xFF] * actual_w)
        row_len = actual_w * self.bytes_per_pixel

        for row in range(y0, y1):
            start = row * self.size_line + x0 * self.bytes_per_pixel
            self.data[start: start + row_len] = row_bytes

    def position_in_minimap(
        self,
        x: int,
        y: int,
        size: int,
        color: int
    )  -> None:
        # Calculate the logical positoni in pixe of mini map
        logical_x = x / self.main_renderer.tile_size
        logical_y = y / self.main_renderer.tile_size

        # Convert the logical position to scaled pixels on the mini-map
        mini_px = (
            self.minimap_renderer.offset_x + (logical_x * self.minimap_renderer.tile_size)
            )
        mini_py = (
            self.minimap_renderer.offset_y + (logical_y * self.minimap_renderer.tile_size)
        )

        # Calculate the player’s size proportionally
        ratio = self.minimap_renderer.tile_size / self.main_renderer.tile_size
        mini_size = max(2, int(size * ratio))
        self.minimap_renderer.draw_player(mini_px, mini_py, mini_size, color)

    def print_game_info(
        self,
        x: int,
        y: int,
        text: list[str]
    ) -> None:
        line_height = 20
        for i, line in enumerate(text):
            text_y = int(y) + (line_height * i)
            # MLX supporta il testo solo tramite string_put sulla finestra, non sull'immagine
            self.m.mlx_string_put(
                self.mlx_ptr,
                self.win_ptr,
                int(x),
                text_y,
                Colors.TEXT_WHITE,
                line
            )

    def draw_main_sprites(self, model: GameModel) -> None:
        """Disegna gli sprites principali passando l'offset come parametro."""

        if model.state not in (GameState.PLAYING, GameState.DEATH_PAUSE, GameState.CHEAT_MODE):
            return
        
        offset = 16
        default_pacman = self.pacman_sprites[Direction.RIGHT]
        current_pacman_sprite = self.pacman_sprites.get(model.player.current_dir, default_pacman)
        
        px = int(model.player.x + self.main_renderer.offset_x) - offset
        py = int(model.player.y + self.main_renderer.offset_y) - offset
        
        self.m.mlx_put_image_to_window(self.mlx_ptr, self.win_ptr, current_pacman_sprite, px, py)

        # 2. Stampa dei 4 Fantasmi
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
                self.m.mlx_put_image_to_window(self.mlx_ptr, self.win_ptr, current_ghost_sprite, gx, gy)

    def draw_minimap_sprites(self, model: GameModel) -> None:
        """Disegna i mini-sprites sulla minimappa usando le proporzioni corrette."""
        if model.state not in (GameState.PLAYING, GameState.DEATH_PAUSE, GameState.CHEAT_MODE):
            return

        # Calcola la proporzione tra minimappa (10) e mappa vera (32)
        ratio = self.minimap_renderer.tile_size / self.main_renderer.tile_size
        
        # Offset per centrare il mini-sprite da 10x10 (metà = 5)
        offset = 5 

        # 1. Mini Pac-Man
        # Moltiplichiamo la x/y vera per il ratio per ottenere i pixel scalati
        mini_px = int(self.minimap_renderer.offset_x + (model.player.x * ratio))
        mini_py = int(self.minimap_renderer.offset_y + (model.player.y * ratio))
        
        self.m.mlx_put_image_to_window(
            self.mlx_ptr, self.win_ptr, self.mini_pacman, mini_px - offset, mini_py - offset
        )

        # 2. Mini Fantasmi
        for ghost in model.ghosts:
            mini_gx = int(self.minimap_renderer.offset_x + (ghost.x * ratio))
            mini_gy = int(self.minimap_renderer.offset_y + (ghost.y * ratio))
            
            # Qui puoi aggiungere la logica per cambiare sprite se il fantasma è EATEN o FRIGHTENED
            current_mini = self.mini_ghost_red
            
            self.m.mlx_put_image_to_window(
                self.mlx_ptr, self.win_ptr, current_mini, mini_gx - offset, mini_gy - offset
            )

    def draw_finish_sprite(self, model: GameModel, sprites: int) -> None:
        """Disegna il logo di Game Over centrato nella parte alta dello schermo."""
        sprite_width = 300  
        sprite_height = 129
        
        x = (self.config.width - sprite_width) // 2
        
        y = self.config.height // 2 - (sprite_height // 2) - sprite_height

        self.m.mlx_put_image_to_window(self.mlx_ptr, self.win_ptr, sprites, x, y)

    def render(self, model: GameModel) -> None:
        """Extract data from the Model and render it to the window."""
        if getattr(self, "_startup_frames", 0) > 0:
            self._last_frame_key = None
            self._startup_frames -= 1

        static_states = (
            GameState.START_MENU,
            GameState.GAME_OVER,
            GameState.ENTER_NAME,
            GameState.HIGHSCORES,
            GameState.INSTRUCTIONS,
            GameState.CHEAT_MODE,
        )

        minimap_pixel_height = model.maze.height * self.minimap_renderer.tile_size
        actual_bottom_y = self.minimap_renderer.offset_y + minimap_pixel_height
        
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
                # no change
                # Draw Heart sprites in the game background
                heart_x_start = self.minimap_renderer.view_x + 10
                heart_y = actual_bottom_y + 20 + 20 * 4
                heart_size = 16
                for i in range(model.player.lives):
                    self.m.mlx_put_image_to_window(
                        self.mlx_ptr,
                        self.win_ptr,
                        self.sprite_heart,
                        heart_x_start + i * (heart_size + 4),
                        heart_y
                    )
                return
            self._last_frame_key = key
        else:
            # if state != static state always reset to None
            self._last_frame_key = None

        # 1. Pulisci l'intero buffer di memoria
        self.clear()

        self.main_renderer.update_layout(model.maze)
        self.minimap_renderer.update_layout(model.maze)

        self.main_renderer.draw_maze(model.maze)
        self.minimap_renderer.draw_maze(model.maze)
        # 2. Disegna maze e personaggi sul buffer principale
        # self.main_renderer.draw_maze(model.maze)
        # self.main_renderer.draw_player(
        #     model.player.x + self.main_renderer.offset_x,
        #     model.player.y + self.main_renderer.offset_y,
        #     model.size,
        #     model.player.color,
        # )
        # for ghost in model.ghosts:
        #     self.main_renderer.draw_player(
        #         ghost.x + self.main_renderer.offset_x,
        #         ghost.y + self.main_renderer.offset_y,
        #         model.size,
        #         ghost.color,
        #     )


        # 3. Disegna minimappa


        # for ghost in model.ghosts:
        #     self.position_in_minimap(ghost.x, ghost.y, model.size, ghost.color)

        # 4. Menu
        if model.state in (
            GameState.START_MENU,
            GameState.GAME_OVER,
            GameState.ENTER_NAME
        ):
            self.draw_main_menu(
                w=self.config.width,
                h=self.config.height,
                selected_index=model.selected_button_index,
                button_lst=model.menu_options,
                is_enter_name=(model.state == GameState.ENTER_NAME),
            )
        elif model.state in (GameState.HIGHSCORES, GameState.INSTRUCTIONS):
            self.draw_menu(
                w=self.config.width,
                h=self.config.height,
                button_lst=model.menu_options,
            )

        self.m.mlx_put_image_to_window(self.mlx_ptr, self.win_ptr, self.img, 0, 0)

        self.draw_main_sprites(model)
        self.draw_minimap_sprites(model)

        if model.state == GameState.ENTER_NAME:
            sprites = self.sprite_gameover
            if model.current_level_index >= len(model.config_data["levels"]):
                sprites = self.sprite_win
            self.draw_finish_sprite(model, sprites)

        if model.state in (
            GameState.START_MENU,
            GameState.GAME_OVER,
            GameState.ENTER_NAME,
        ):
            self.draw_button(model.state)
        elif model.state in (GameState.HIGHSCORES, GameState.INSTRUCTIONS):
            if model.state == GameState.HIGHSCORES:
                text = model.highscore_manager.top_scores_text
            else:
                text = self.game_rules.split("\n")
            self.draw_text(
                w=self.config.width, h=self.config.height, text=text,
                is_highscores=(model.state == GameState.HIGHSCORES)
            )
            self.draw_button(model.state)

        if model.state not in (GameState.START_MENU, GameState.HIGHSCORES, GameState.INSTRUCTIONS):
            
            game_info = [
                f"Score: {model.player.score}",
                f"Level: {model.current_level_index + 1}",
                f"Time: {int(model.level_time_remaining)}",
                f"{self.cheat[0]}"
            ]

            # Espandi il testo se sei nel cheat mode
            if model.state == GameState.CHEAT_MODE:
                game_info.extend(self.cheat_mode_command)

            self.print_game_info(
                x=self.minimap_renderer.view_x,
                y=actual_bottom_y + 20,
                text=game_info
            )
            
        if hasattr(self.m, 'mlx_do_sync'):
            self.m.mlx_do_sync(self.mlx_ptr)
