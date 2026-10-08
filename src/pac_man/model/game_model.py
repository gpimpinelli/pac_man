"""Core game model managing game state, physics, and game rules."""

import math
import random
from typing import Any
from enum import Enum, auto
from pydantic import (
    BaseModel,
    ConfigDict,
    model_validator,
    Field,
    PrivateAttr,
)
from pac_man.utils import pixel_to_cell, cell_to_pixel
from .maze_adapter import Cell, MazeAdapter
from .highscores import HighscoreManager
from .entity import Ghost, GhostState, Player, PlayerState, Direction, Entity


class GameState(Enum):
    """Enumeration of overall game application states."""

    START_MENU = auto()
    PLAYING = auto()
    DEATH_PAUSE = auto()
    GAME_OVER = auto()
    HIGHSCORES = auto()
    INSTRUCTIONS = auto()
    ENTER_NAME = auto()
    CHEAT_MODE = auto()
    LEVEL_COMPLETE = auto()
    PAUSE = auto()


class GameModel(BaseModel):
    """Manages game state, maze layout, entities, and physics simulations.

    Attributes:
        size (int): Grid scale reference size.
        screen_width (int): Viewport width in pixels.
        screen_height (int): Viewport height in pixels.
        maze (Any): MazeAdapter instance managing the grid.
        state (GameState): Current game lifecycle state.
        tile_size (int): Dimension of each grid tile in pixels.
        config_data (dict[str, Any]): Parsed JSON configuration parameters.
        ghosts (list[Ghost]): List of active ghost entities.
        selected_button_index (int): Index of currently highlighted menu item.
        highscore_manager (HighscoreManager): Score persistence manager.
        name_input (str): Current text buffer for highscore entry.
        level_time_remaining (float): Countdown timer for current level.
        level_transition_timer (float): Delay timer between levels.
        current_level_index (int): 0-indexed current game level.
    """

    size: int = 16

    # Environment constraints
    screen_width: int = Field(..., gt=0)
    screen_height: int = Field(..., gt=0)

    maze: Any = Field(default=None)

    state: GameState = GameState.START_MENU

    tile_size: int = Field(default=48)

    config_data: dict[str, Any] = Field(default_factory=dict)

    _player: Player | None = PrivateAttr(default=None)

    @property
    def player(self) -> Player:
        """Get the active player instance.

        Returns:
            Player: The player entity.
        """
        assert self._player is not None
        return self._player

    @player.setter
    def player(self, value: Player) -> None:
        """Set the active player instance.

        Args:
            value (Player): The player entity to set.
        """
        self._player = value

    ghosts: list[Ghost] = Field(default_factory=list)

    selected_button_index: int = 0

    # HIGHSCORE
    highscore_manager: HighscoreManager = Field(
        default_factory=HighscoreManager
    )

    name_input: str = ""

    level_time: float = 0.0

    level_time_remaining: float = 0.0

    level_transition_timer: float = 0.0

    current_level_index: int = 9

    model_config = ConfigDict(validate_assignment=False)

    @model_validator(mode="after")
    def create_entity(self) -> "GameModel":
        """Initialize game maze, highscores, and entities after model setup.

        Returns:
            GameModel: The initialized game model instance.
        """
        self.highscore_manager = HighscoreManager(
            filepath=self.config_data.get(
                "highscore_filename", "highscores.json"
            )
        )

        levels_list = self.config_data.get(
            "levels", [{"width": 15, "height": 15}]
        )
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
        self.player = Player(lives=(self.config_data["lives"] - 1))

        x_pixel = float(spawn_x + half_tile)
        y_pixel = float(spawn_y + half_tile)
        self.player.x = x_pixel
        self.player.y = y_pixel
        self.player.coords_spawn = (x_pixel, y_pixel)

        for coords in self.maze.ghost_spawns:
            coords_pixel: tuple[int, int] = cell_to_pixel(
                coords, (0, 0), self.tile_size
            )
            x_pixel = float(coords_pixel[0] + half_tile)
            y_pixel = float(coords_pixel[1] + half_tile)
            self.ghosts.append(
                Ghost(
                    x=x_pixel,
                    y=y_pixel,
                    state=GhostState.SCATTER,
                    coords_spawn=(x_pixel, y_pixel),
                )
            )
        self._apply_level_speeds()
        return self

    def _spawn_entities(
        self, entity: Entity, coords: tuple[int, int]
    ) -> None:
        """Position an entity at the center of the specified grid cell.

        Args:
            entity (Entity): The entity to reposition.
            coords (tuple[int, int]): Target grid coordinates (col, row).
        """
        half_tile = self.tile_size // 2
        if isinstance(entity, Player):
            coords_pixel = cell_to_pixel(
                coords,
                (0, 0),
                self.tile_size,
            )
        else:
            coords_pixel = cell_to_pixel(
                coords, (0, 0), self.tile_size
            )
        entity.x = float(coords_pixel[0] + half_tile)
        entity.y = float(coords_pixel[1] + half_tile)
        entity.coords_spawn = (entity.x, entity.y)

    def _change_ghosts_state(self, new_state: GhostState) -> None:
        """Update behavioral state of all non-eaten ghosts.

        Args:
            new_state (GhostState): Target state to apply.
        """
        for ghost in self.ghosts:
            if ghost.state != GhostState.EATEN and ghost.state != new_state:
                ghost.state = new_state

    def _calc_rail(self, entity: Entity) -> tuple[float, float]:
        """Calculate the center line (rail) coordinates of current tile.

        Args:
            entity (Entity): The entity whose position is sampled.

        Returns:
            tuple[float, float]: Center (x, y) coordinates of the tile.
        """
        col, row = pixel_to_cell((entity.x, entity.y), (0, 0), self.tile_size)
        return (
            float((col + 0.5) * self.tile_size),
            float((row + 0.5) * self.tile_size)
        )

    @property
    def menu_options(self) -> tuple[str, ...]:
        """Get the available interactive menu options for current state.

        Returns:
            tuple[str, ...]: Tuple of action labels for active menu screen.
        """
        if self.state == GameState.START_MENU:
            return ("START", "HIGHSCORES", "INSTRUCTIONS", "EXIT")
        elif self.state == GameState.GAME_OVER:
            return ("RETRY", "MAIN MENU", "EXIT")
        elif self.state == GameState.PAUSE:
            return ("RESUME", "MAIN MENU", "EXIT")
        elif self.state == GameState.ENTER_NAME:
            display_name = "Insert Name"
            if self.name_input:
                display_name = self.name_input
            return ("", display_name, "SAVE SCORE")
        elif self.state in (GameState.HIGHSCORES, GameState.INSTRUCTIONS):
            return ("ENTER TO GO BACK",)
        return ()

    def remove_super(self) -> None:
        """Cancel Pac-Man super energized mode and revert ghosts to chase."""
        self.player.remove_super()
        self._change_ghosts_state(GhostState.CHASE)

    def _apply_level_speeds(self) -> None:
        """Set player and ghost speeds from the current level's base speed.

        Discards any cheat-mode speed boost or leftover super-mode bonus.
        """
        base_speed = 80 * (1.02**self.current_level_index)
        self.player.speed = base_speed + 10
        for i, ghost in enumerate(self.ghosts):
            ghost.speed = base_speed + 2 * i

    def _load_level(self, is_first: bool = False) -> None:
        """Load and initialize a maze level from configuration.

        Args:
            is_first (bool): True if starting level 0 with fixed seed.
        """
        if is_first:
            self.current_level_index = 0

        levels_list = self.config_data.get(
            "levels", [{"width": 15, "height": 15}]
        )

        # Clamp level index to the last configured level
        if self.current_level_index >= len(levels_list):
            self.current_level_index = len(levels_list) - 1

        current_level = levels_list[self.current_level_index]
        w = current_level["width"]
        h = current_level["height"]

        if is_first:
            seed = self.config_data.get("seed", 42)
        else:
            seed = random.randint(0, 100000)

        # Reset Game
        # ====================================================================
        self._reset_game()
        self.maze = MazeAdapter(width=w, height=h, seed=seed)

        # Spawn Entities
        # ====================================================================
        self._spawn_entities(self.player, self.maze.player_spawn)
        for i in range(len(self.ghosts)):
            self._spawn_entities(self.ghosts[i], self.maze.ghost_spawns[i])

        # Apply Level Speeds
        # ====================================================================
        self._apply_level_speeds()

        base_time = self.config_data.get("level_max_time", 180)
        self.level_time = (
            base_time * (1.05**self.current_level_index)
        )
        self.level_time_remaining = self.level_time

    def _reset_game(self) -> None:
        """Reset player and ghost positions to spawn points and pause play."""
        self.player.reset_movement()
        self.remove_super()

        self.player.x, self.player.y = self.player.coords_spawn
        for ghost in self.ghosts:
            ghost.set_frozen(False)
            ghost.reset_movement()
            ghost.respawn_timer = 0.0
            ghost.state = GhostState.SCATTER
            ghost.x, ghost.y = ghost.coords_spawn

        self.state = GameState.DEATH_PAUSE

    def _freeze_game(self) -> None:
        """Stop movement (used at level complete)."""
        self.player.reset_movement()
        for ghost in self.ghosts:
            ghost.set_frozen(True)

    def _freeze_ghosts(self) -> None:
        """Halt all ghost movements immediately."""
        for ghost in self.ghosts:
            ghost.freeze()

    def _check_entity_collisions(self) -> list[int]:
        """Check for collisions between player and ghosts within hitbox radius.

        Returns:
            list[int]: Indices of colliding ghosts in self.ghosts.
        """
        hitbox_radius = self.tile_size * 0.5

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
        """Detect and consume pellets at Pac-Man's current grid position."""
        col, row = pixel_to_cell(
            (self.player.x, self.player.y), (0, 0), self.tile_size
        )

        cell: Cell = self.maze.get_cell(col, row)

        if cell is None:
            return

        if cell.has_pacgum:
            cell.remove_gum(is_super_gum=False)
            self.player.score += int(
                self.config_data["points_per_pacgum"]
                * self.player.multiplicator
            )
            self.maze.total_pacgums -= 1

        elif cell.has_super_pacgum:
            cell.remove_gum(is_super_gum=True)
            self.player.score += int(
                self.config_data["points_per_super_pacgum"]
                * self.player.multiplicator
            )
            if not self.player.is_super:
                self.player.speed += 25

            self.player.super_timer = (
                (self.level_time // 7) +
                (1.5 * self.current_level_index)
            )
            self._change_ghosts_state(GhostState.FRIGHTENED)
            self.maze.total_pacgums -= 1

    def level_skip(self) -> None:
        """Cheat command to skip directly to the next level."""
        self.current_level_index += 1
        if self.current_level_index >= len(self.config_data["levels"]):
            self.state = GameState.ENTER_NAME
        else:
            self._load_level(is_first=False)

    def add_lives(self) -> None:
        """Cheat command to grant an extra life to the player."""
        self.player.add_lives()

    def increase_speed(self) -> None:
        """Cheat command to increase player movement speed."""
        print(f"[CHEAT] Player speed: {self.player.speed}")
        self.player.increase_player_speed()
        print(f"[CHEAT] Increased Player speed: {self.player.speed}")

    def toggle_invincible(self) -> None:
        """Cheat command to toggle player invulnerability mode."""
        self.player.toggle_invincible()
        print(f"[CHEAT] Invincibility: {self.player.is_invincible}")

    def _handle_player_death(self) -> None:
        """Process player life loss, game over transition, or level reset."""
        self.player.lives -= 1
        self.player.state = PlayerState.DEAD

        if not self.player.has_lives or self.current_level_index >= len(
            self.config_data["levels"]
        ):
            self.state = GameState.ENTER_NAME
        else:
            self._reset_game()
            # Reset level timer to maximum upon respawn
            # base_time = self.config_data.get("level_max_time", 180)
            self.level_time_remaining = self.level_time

    def update(self, dt: float) -> None:
        """Advance game physics, handle input, AI steering, and collisions.

        Args:
            dt (float): Elapsed delta time in seconds since last frame.
        """
        if self.state not in (
            GameState.PLAYING,
            GameState.CHEAT_MODE,
            GameState.LEVEL_COMPLETE,
        ):
            return

        if self.state == GameState.LEVEL_COMPLETE:
            self.level_transition_timer -= dt

            if self.level_transition_timer <= 0:
                self.current_level_index += 1
                if self.current_level_index >= len(self.config_data["levels"]):
                    self.state = GameState.ENTER_NAME
                else:
                    self.state = GameState.DEATH_PAUSE
                    self._load_level(is_first=False)
            return

        if self.state == GameState.CHEAT_MODE:
            return

        self.level_time_remaining -= dt

        if self.level_time_remaining <= 0:
            self.level_time_remaining = 0.0
            self._handle_player_death()
            return

        scatter_duration = 7 * (1.10**self.current_level_index)

        if self.level_time_remaining < self.level_time - scatter_duration:
            for ghost in self.ghosts:
                if ghost.state == GhostState.SCATTER:
                    ghost.state = GhostState.CHASE

        self.player.update_intention(self)
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
                    continue

                tolerance = max(ghost.speed * dt, 4.0)
                if (
                    abs(ghost.x - ghost.coords_spawn[0]) <= tolerance
                    and abs(ghost.y - ghost.coords_spawn[1]) <= tolerance
                ):

                    ghost.x, ghost.y = ghost.coords_spawn
                    ghost.reset_movement()
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

            if self.player.is_super and collided_ghost.state not in (
                GhostState.SCATTER,
                GhostState.CHASE,
            ):
                # Pac-Man eats frightened ghost
                self.player.multiplicator = 1.5
                self.player.score += int(
                    self.config_data["points_per_ghost"]
                    * self.player.multiplicator
                )
                collided_ghost.state = GhostState.EATEN

            elif self.player.is_invincible:
                continue

            else:
                # Ghost catches Pac-Man
                self._handle_player_death()
                break

        if self.maze.finish_pacgums():
            self._freeze_game()
            self.level_transition_timer = 3.0
            self.state = GameState.LEVEL_COMPLETE
            return

        if self.player.is_super:
            self.player.super_timer -= dt

            if self.player.super_timer <= 0:
                self.player.super_timer = 0.0
                self._change_ghosts_state(GhostState.CHASE)
                self.player.speed -= 25

        if not self.player.is_super:
            self.player.multiplicator = 1.0

    def _handle_steering(self, entity: Entity, dt: float) -> None:
        """Guide entity turning into perpendicular corridors when aligned.

        Args:
            entity (Entity): The entity to steer.
            dt (float): Elapsed delta time in seconds.
        """
        if entity.desired_dir and entity.desired_dir != entity.current_dir:
            is_opposite = (
                (
                    entity.current_dir == Direction.LEFT
                    and entity.desired_dir == Direction.RIGHT
                )
                or (
                    entity.current_dir == Direction.RIGHT
                    and entity.desired_dir == Direction.LEFT
                )
                or (
                    entity.current_dir == Direction.UP
                    and entity.desired_dir == Direction.DOWN
                )
                or (
                    entity.current_dir == Direction.DOWN
                    and entity.desired_dir == Direction.UP
                )
            )

            if is_opposite:
                entity.current_dir = entity.desired_dir
                entity.desired_dir = None
                return
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
                    if entity.current_dir in (Direction.LEFT, Direction.RIGHT):
                        dist_from_center = abs(entity.x - rail_x)
                    else:
                        dist_from_center = abs(entity.y - rail_y)
                    # ================== Avoid Snap Jitter ==================
                    # Calculate the exact distance traveled this frame
                    tolerance = entity.speed * dt
                    if (
                        entity.current_dir is None
                        or dist_from_center <= tolerance
                    ):
                        entity.x = rail_x
                        entity.y = rail_y
                        entity.current_dir = entity.desired_dir
                        entity.desired_dir = None

    def _apply_movement(self, entity: Entity, dt: float) -> None:
        """Translate entity coordinates according to its current direction.

        Args:
            entity (Entity): Entity to translate.
            dt (float): Elapsed delta time in seconds.
        """
        match entity.current_dir:
            case Direction.UP:
                entity.y -= entity.speed * dt
            case Direction.DOWN:
                entity.y += entity.speed * dt
            case Direction.LEFT:
                entity.x -= entity.speed * dt
            case Direction.RIGHT:
                entity.x += entity.speed * dt

    def _handle_wall_collisions(self, entity: Entity) -> None:
        """Halt entity movement and snap to rail when meeting a solid wall.

        Args:
            entity (Entity): Entity to collide against maze walls.
        """
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
                        if entity.y <= rail_y:
                            must_stop = True
                    case Direction.DOWN:
                        if entity.y >= rail_y:
                            must_stop = True
                    case Direction.LEFT:
                        if entity.x <= rail_x:
                            must_stop = True
                    case Direction.RIGHT:
                        if entity.x >= rail_x:
                            must_stop = True

                # Snap flush to the tile center/rail and stop.
                if must_stop:
                    entity.x, entity.y = self._calc_rail(entity)
                    entity.current_dir = None
