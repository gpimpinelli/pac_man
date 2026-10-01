import math
import random
from typing import Any
from ..view import Colors
from enum import Enum, auto
from .maze_adapter import Cell, MazeAdapter
from .highscores import HighscoreManager
from src.pac_man.utils import pixel_to_cell, cell_to_pixel
from pydantic import BaseModel, ConfigDict, model_validator, Field
from .entity import Ghost, GhostState, Player, PlayerState, Direction, Entity

COLORS = [Colors.BACKGROUND, Colors.BACKGROUND, Colors.BACKGROUND, Colors.BACKGROUND]

class GameState(Enum):
    START_MENU = auto()
    PLAYING = auto()
    DEATH_PAUSE = auto()
    GAME_OVER = auto()
    HIGHSCORES = auto()
    INSTRUCTIONS = auto()
    ENTER_NAME = auto()
    CHEAT_MODE = auto()


# ==========================================
# 1. MODEL (Physics, Data, and Rules)
# ==========================================
class GameModel(BaseModel):
    """
    Manage the game logic, state, and entity physics.
    Inherits from Pydantic's BaseModel for rigid data initialization.
    """
    size: int = 16

    # Environment constraints
    screen_width: int = Field(..., gt=0)
    screen_height: int = Field(..., gt=0)
    
    maze: Any = Field(default=None)

    state: GameState = GameState.START_MENU

    tile_size: int = Field(default=48)

    config_data: dict[str, Any] = Field(default_factory=dict)

    player: Player | None = None
    ghosts: list[Ghost] = Field(default_factory=list)

    selected_button_index: int = 0

    # HIGHSCORE
    highscore_manager: HighscoreManager = Field(default_factory=HighscoreManager)

    name_input: str = ""

    level_time_remaining: float = 0.0

    current_level_index: int = 9

    # Disable assignment validation for performance during the 60fps loop
    model_config = ConfigDict(validate_assignment=False)


    @model_validator(mode='after')
    def create_entity(self):
        # 1. Inizializza l'HighscoreManager
        self.highscore_manager = HighscoreManager(filepath=self.config_data.get("highscore_filename", "highscores.json"))
        
        # 2. CREA IL LABIRINTO INIZIALE (Sfondo del menu)
        # Prendi le misure dal primo livello indicato nel config (o usa default se assente)
        levels_list = self.config_data.get("levels", [{"width": 15, "height": 15}])
        w = levels_list[0]["width"]
        h = levels_list[0]["height"]
        seed = self.config_data.get("seed", 42)
        
        self.maze = MazeAdapter(width=w, height=h, seed=seed)

        spawn_x, spawn_y = cell_to_pixel(
            self.maze.player_spawn,
            (0, 0),
            self.tile_size,
        )

        half_tile = self.tile_size // 2
        speed = 90 * (1.02 ** self.current_level_index)
        self.player = Player(lives=(self.config_data["lives"] - 1), speed= speed + 10)

        x_pixel = float(spawn_x + half_tile)
        y_pixel = float(spawn_y + half_tile)
        self.player.x = x_pixel
        self.player.y = y_pixel
        self.player.coords_spawn = (x_pixel, y_pixel)

        for coords, c in zip(self.maze.ghost_spawns, COLORS):
            coords_pixel: tuple[int, int] = cell_to_pixel(
                coords, (0, 0), self.tile_size
                )
            x_pixel = float(coords_pixel[0] + half_tile)
            y_pixel = float(coords_pixel[1] + half_tile)
            self.ghosts.append(
                Ghost(
                    x=x_pixel,
                    y=y_pixel,
                    color=c,
                    speed=speed,
                    state=GhostState.SCATTER,
                    coords_spawn=(x_pixel, y_pixel),
                )
            )
            speed += 2
        return self

    def _spawn_entities(self, entity: Entity, coords: tuple[int, int]):
        half_tile = self.tile_size // 2
        if isinstance(entity, Player):
            coords_pixel = cell_to_pixel(
                coords,
                (0, 0),
                self.tile_size,
            )
        else:
            coords_pixel: tuple[int, int] = cell_to_pixel(
                coords, (0, 0), self.tile_size
            )
        entity.x = float(coords_pixel[0] + half_tile)
        entity.y = float(coords_pixel[1] + half_tile)
        entity.coords_spawn = (entity.x, entity.y)

    def _change_ghosts_state(self, new_state: GhostState) -> None:
        for ghost in self.ghosts:
            if ghost.state != GhostState.EATEN and ghost.state != new_state:
                ghost.state = new_state

    def _calc_rail(self, entity: Entity) -> tuple[int, int]:
        col, row = pixel_to_cell((entity.x, entity.y), (0, 0), self.tile_size)
        return(
            (col + 0.5) * self.tile_size,
            (row + 0.5) * self.tile_size
        )

    @property
    def menu_options(self) -> tuple[str, ...]:
        if self.state == GameState.START_MENU:
            return ("START", "HIGHSCORES", "INSTRUCTIONS", "EXIT")
        elif self.state == GameState.GAME_OVER:
            return ("RETRY", "MAIN MENU", "EXIT")
        elif self.state == GameState.ENTER_NAME:
            display_name = self.name_input if self.name_input else "Insert Name"
            return ("", display_name, "SAVE SCORE")
        elif self.state in (GameState.HIGHSCORES, GameState.INSTRUCTIONS):
            return ("ENTER TO GO BACK",)
        return ()

    def remove_super(self):
        self.player.remove_super()
        self._change_ghosts_state(GhostState.CHASE)


    def _load_level(self, is_first: bool = False) -> None:
        if is_first:
            self.current_level_index = 0
            
        levels_list = self.config_data.get("levels", [{"width": 15, "height": 15}])
        
        # Evita errori se il giocatore supera l'ultimo livello disponibile
        if self.current_level_index >= len(levels_list):
            self.current_level_index = len(levels_list) - 1
            
        current_level = levels_list[self.current_level_index]
        w = current_level["width"]
        h = current_level["height"]
        
        seed = self.config_data.get("seed", 42) if is_first else random.randint(0, 100000)
        
        self._reset_game()
        self.maze = MazeAdapter(width=w, height=h, seed=seed)
        
        self._spawn_entities(self.player, self.maze.player_spawn)
        for i in range(len(self.ghosts)):
            self._spawn_entities(self.ghosts[i], self.maze.ghost_spawns[i])
            
        base_time = self.config_data.get("level_max_time", 180)
        self.level_time_remaining = base_time * (1.05 ** self.current_level_index)

    def _reset_game(self) -> None:
        self._freeze_game()
        self.remove_super()

        self.player.x, self.player.y = self.player.coords_spawn
        for ghost in self.ghosts:
            ghost.state = GhostState.SCATTER
            ghost.x, ghost.y = ghost.coords_spawn

        self.state = GameState.DEATH_PAUSE

    def _freeze_game(self) -> None:
        self.player.current_dir = None
        self.player.desired_dir = None

        for ghost in self.ghosts:
            ghost.current_dir = None
            ghost.desired_dir = None

    def _check_entity_collisions(self) -> list[int]:
        """Check if entitis collides"""
        hitbox_radius = self.tile_size * 0.4

        i = 0
        collisions_detected: list[int] = []
        while i < len(self.ghosts):
            dist = math.dist(
                (self.player.x, self.player.y),
                (self.ghosts[i].x, self.ghosts[i].y)
            )
            if dist <= hitbox_radius:
                collisions_detected.append(i)
            i += 1
        return collisions_detected

    def _check_and_eat_gum(self) -> None:
        """Check the current cell and eat the pac gum"""
        col, row = pixel_to_cell(
            (self.player.x, self.player.y), (0, 0), self.tile_size
        )
        
        cell: Cell = self.maze.get_cell(col, row)
        
        if cell is None:
            return

        if cell.has_pacgum:
            cell.remove_gum(is_super_gum=False)
            self.player.score += int(self.config_data["points_per_pacgum"] * self.player.multiplicator)
            self.maze.total_pacgums -= 1
            
        elif cell.has_super_pacgum:
            cell.remove_gum(is_super_gum=True)
            self.player.score += int(self.config_data["points_per_super_pacgum"] * self.player.multiplicator)
            self.player.super_timer = (self.config_data["level_max_time"] // 7) + (1.5 * self.current_level_index)
            self.player.speed += 25
            self._change_ghosts_state(GhostState.FRIGHTENED)
            self.maze.total_pacgums -= 1
    
    def level_skip(self) -> None:
        self.current_level_index += 1
        if self.current_level_index >= len(self.config_data["levels"]):
            self.state = GameState.ENTER_NAME
        else:
            self._load_level(is_first=False)
        
    def add_lives(self) -> None:
        self.player.add_lives()
        
    def toggle_invincible(self) -> None:
        self.player.toggle_invincible()
        print(f"[CHEAT] Invincibility: {self.player.is_invincible}")

    def update(self, dt: float):
        """
        Update the player position and handle collisions.
        Args:
            dt: Delta time elapsed since the last frame, in seconds.
        """

        if self.state != GameState.PLAYING or self.state == GameState.GAME_OVER:
            return

        self.level_time_remaining -= dt

        if self.level_time_remaining <= 0:
            self.level_time_remaining = 0.0
            
            self.player.lives -= 1
            self.player.state = PlayerState.DEAD
            
            if (
                not self.player.has_lives
                or self.current_level_index >= len(self.config_data["levels"])
            ):
                self.state = GameState.ENTER_NAME
            else:
                self._reset_game()
                self.level_time_remaining = float(self.config_data.get("level_max_time", 180))
            return

        if self.level_time_remaining < self.config_data["level_max_time"] - 7:
            for ghost in self.ghosts:
                if ghost.state == GhostState.SCATTER:
                    ghost.state = GhostState.CHASE

        self._handle_steering(self.player, dt)
        self._apply_movement(self.player, dt)
        self._handle_wall_collisions(self.player)

        for ghost in self.ghosts:
            if ghost.state == GhostState.EATEN:
                if ghost.respawn_timer > 0:
                    ghost.respawn_timer -= dt
                    if ghost.respawn_timer <= 0:
                        ghost.respawn_timer = 0.0
                        ghost.state = GhostState.CHASE
                    # until the timer is > 0, ghost state not change
                    continue
                
                tolerance = max(ghost.speed * dt, 4.0)
                if (abs(ghost.x - ghost.coords_spawn[0]) <= tolerance and 
                    abs(ghost.y - ghost.coords_spawn[1]) <= tolerance):

                    ghost.x, ghost.y = ghost.coords_spawn
                    ghost.current_dir = None
                    ghost.desired_dir = None
                    ghost.respawn_timer = 2.0
                    continue

            ghost.update_intention(self)
            self._handle_steering(ghost, dt)
            self._apply_movement(ghost, dt)
            self._handle_wall_collisions(ghost)

        self._check_and_eat_gum()

        collisions_detected: list[int] = self._check_entity_collisions()
        for ghost_index in collisions_detected:
            if self.player.state == PlayerState.DEAD:
                break

            collided_ghost = self.ghosts[ghost_index]
            if collided_ghost.state == GhostState.EATEN:
                continue

            if self.player.is_super and collided_ghost.state not in (GhostState.SCATTER, GhostState.CHASE):
                # Pac-Man mangia il fantasma
                self.player.multiplicator = 1.5
                self.player.score += int(self.config_data["points_per_ghost"] * self.player.multiplicator)
                collided_ghost.state = GhostState.EATEN

            elif self.player.is_invincible:
                continue

            else:
                # Il fantasma mangia Pac-Man
                self.player.lives -= 1
                self.player.state = PlayerState.DEAD
                if not self.player.has_lives:
                    self.state = GameState.ENTER_NAME
                else:
                    self._reset_game()
                break

        if self.maze.finish_pacgums():
            self.current_level_index += 1
            if self.current_level_index >= len(self.config_data["levels"]):
                self.state = GameState.ENTER_NAME
                return 0
            self.state = GameState.DEATH_PAUSE
            self._load_level(is_first=False)
            return 0

        if (
            hasattr(self.player, 'super_timer')
            and self.player.super_timer > 0
        ):
            self.player.super_timer -= dt
            
            if self.player.super_timer <= 0:
                self.player.super_timer = 0.0
                self._change_ghosts_state(GhostState.CHASE)
                self.player.speed -= 25

        if not self.player.is_super:
            self.player.multiplicator = 1

    def _handle_steering(self, entity: Entity, dt: float):
        if entity.desired_dir and entity.desired_dir != entity.current_dir:
            is_opposite = (
                (entity.current_dir == Direction.LEFT and
                    entity.desired_dir == Direction.RIGHT) or
                (entity.current_dir == Direction.RIGHT and
                    entity.desired_dir == Direction.LEFT) or
                (entity.current_dir == Direction.UP and
                    entity.desired_dir == Direction.DOWN) or
                (entity.current_dir == Direction.DOWN and
                    entity.desired_dir == Direction.UP)
            )

            if is_opposite and isinstance(entity, Player):
                entity.current_dir = entity.desired_dir
                entity.desired_dir = None
            else:
                can_turn = False
                col, row = pixel_to_cell(
                    (entity.x, entity.y), (0, 0), self.tile_size
                )
                current_cell = self.maze.get_cell(col, row)
                if current_cell and not current_cell.is_solid:
                    match entity.desired_dir:
                        case Direction.UP:
                            can_turn = not current_cell.has_wall_north
                        case Direction.DOWN:
                            can_turn = not current_cell.has_wall_south
                        case Direction.LEFT:
                            can_turn = not current_cell.has_wall_west
                        case Direction.RIGHT:
                            can_turn = not current_cell.has_wall_east
            
                rail_x, rail_y = self._calc_rail(entity)
                if can_turn:
                    if (
                        entity.current_dir in (Direction.LEFT, Direction.RIGHT)
                    ):
                        dist_from_center = abs(entity.x - rail_x)
                    else:
                        dist_from_center = abs(entity.y - rail_y)
                    # ================== Avoid Snap Jitter ==================
                    # Calculate the exact distance traveled this frame
                    tolerance = entity.speed * dt
                    if (
                        entity.current_dir is None or dist_from_center <= tolerance
                    ):
                        entity.x = rail_x
                        entity.y = rail_y
                        entity.current_dir = entity.desired_dir
                        entity.desired_dir = None

    def _apply_movement(self, entity: Entity, dt: float):
        match entity.current_dir:
            case Direction.UP:
                entity.y -= entity.speed * dt
            case Direction.DOWN:
                entity.y += entity.speed * dt
            case Direction.LEFT:
                entity.x -= entity.speed * dt
            case Direction.RIGHT:
                entity.x += entity.speed * dt

    def _handle_wall_collisions(self, entity: Entity):
        if entity.current_dir is not None:
            col, row = pixel_to_cell(
                (entity.x, entity.y), (0, 0), self.tile_size
            )
            cell = self.maze.get_cell(col, row)
 
            blocked = cell is None or cell.is_solid
            if not blocked:
                match entity.current_dir:
                    case Direction.UP:
                        blocked = cell.has_wall_north
                    case Direction.DOWN:
                        blocked = cell.has_wall_south
                    case Direction.LEFT:
                        blocked = cell.has_wall_west
                    case Direction.RIGHT:
                        blocked = cell.has_wall_east
 
            if blocked:
                rail_x, rail_y = self._calc_rail(entity)
                must_stop = False
                match entity.current_dir:
                    case Direction.UP:
                        if entity.y <= rail_y: must_stop = True
                    case Direction.DOWN:
                        if entity.y >= rail_y: must_stop = True
                    case Direction.LEFT:
                        if entity.x <= rail_x: must_stop = True
                    case Direction.RIGHT:
                        if entity.x >= rail_x: must_stop = True
               
                # Snap flush to the tile center/rail and stop.
                if must_stop: 
                    entity.x, entity.y = self._calc_rail(entity)
                    entity.current_dir = None 
