import math
from .entity import Direction, Entity
from .maze_adapter import Cell
from typing import Any
from pydantic import BaseModel, Field, ConfigDict
from .entity import Ghost, GhostState, Player, PlayerState
from src.pac_man.utils import pixel_to_cell


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
    
    maze: Any

    started: bool = Field(default=False)

    # Disable assignment validation for performance during the 60fps loop
    model_config = ConfigDict(validate_assignment=False)
    
    tile_size: int = Field(default=32)
    offset_x: int = Field(ge=0)
    offset_y: int = Field(ge=0)

    player: Player = Field(default_factory=Player)
    ghosts: list[Ghost] = Field(default_factory=list)

    def _change_ghosts_state(self, new_state: GhostState) -> None:
        for ghost in self.ghosts:
            if new_state != ghost.state:
                ghost.state = new_state
    
    def calc_rail(self, entity: Entity) -> tuple[int, int]:
        col, row = pixel_to_cell((entity.x, entity.y), (self.offset_x, self.offset_y), self.tile_size)
        return(
            self.offset_x + (col + 0.5) * self.tile_size,
            self.offset_y + (row + 0.5) * self.tile_size
        )

    def _reset_game(self) -> None:
        self._freeze_game()

        self.player.x, self.player.y = self.player.coords_spawn
        for ghost in self.ghosts:
            ghost.x, ghost.y = ghost.coords_spawn

        self.started = False

    def _freeze_game(self) -> None:
        self.player.current_dir = None
        self.player.desired_dir = None

        for ghost in self.ghosts:
            ghost.current_dir = None
            ghost.desired_dir = None


    def _check_entity_collisions(self) -> int:
        """Check if entitis collides"""
        hitbox_radius = self.tile_size * 0.25

        i = 0
        while i < len(self.ghosts):
            dist = math.dist(
                (self.player.x, self.player.y),
                (self.ghosts[i].x, self.ghosts[i].y)
            )
            if dist <= hitbox_radius:
                return (i)
            i += 1
        return -1

    def _check_and_eat_gum(self) -> None:
        """Check the current cell and eat the pac gum"""
        col, row = pixel_to_cell((self.player.x, self.player.y), (self.offset_x, self.offset_y), self.tile_size)
        
        cell: Cell = self.maze.get_cell(col, row)
        
        if cell is None:
            return

        if cell.has_pacgum:
            cell.remove_gum(is_super_gum=False)
            # TODO insert score taken from config.json
            self.player.score += 10
            self.maze.total_pacgums -= 1
            
        elif cell.has_super_pacgum:
            cell.remove_gum(is_super_gum=True)
            # TODO insert score taken from config.json
            self.player.score += 100
            self.player.super_timer = 30.0
            self._change_ghosts_state(GhostState.FRIGHTENED)
            self.maze.total_pacgums -= 1


    def update(self, dt: float):
        """
        Update the player position and handle collisions.
        Args:
            dt: Delta time elapsed since the last frame, in seconds.
        """
        if not self.started:
            return

        self._handle_steering(self.player, dt)
        self._apply_movement(self.player, dt)
        self._handle_wall_collisions(self.player)

        for ghost in self.ghosts:
            ghost.update_intention(self)
            self._handle_steering(ghost, dt)
            self._apply_movement(ghost, dt)
            self._handle_wall_collisions(ghost)

        self._check_and_eat_gum()

        ghost_index = self._check_entity_collisions()
        if (
            ghost_index != -1
            and self.player.is_super
            and not self.ghosts[ghost_index].is_already_eaten
        ):
            self.player.score += 200
            self.ghosts[ghost_index].state = GhostState.EATEN

        elif ghost_index != -1 and not self.player.is_super:
            self.player.lives -= 1
            self.player.state = PlayerState.DEAD
            self._reset_game()

        if (
            hasattr(self.player, 'super_timer')
            and self.player.super_timer > 0
        ):
            self.player.super_timer -= dt

            if self.player.super_timer <= 0:
                self.player.super_timer = 0.0
                self._change_ghosts_state(GhostState.CHASE)

        # if self.player.state == PlayerState.DEAD:
        #     if self.player.lives > 0:
        #         self.player.state = PlayerState.ALIVE
        #     self.started = False

    def _handle_steering(self, entity: Entity, dt: float):
        if entity.desired_dir and entity.desired_dir != entity.current_dir:
            is_opposite = (
                (entity.current_dir == Direction.LEFT and entity.desired_dir == Direction.RIGHT) or
                (entity.current_dir == Direction.RIGHT and entity.desired_dir == Direction.LEFT) or
                (entity.current_dir == Direction.UP and entity.desired_dir == Direction.DOWN) or
                (entity.current_dir == Direction.DOWN and entity.desired_dir == Direction.UP)
            )

            if is_opposite and isinstance(entity, Player):
                # Inverti istantaneamente senza calcolare il centro
                entity.current_dir = entity.desired_dir
                entity.desired_dir = None
            else:
                can_turn = False
                col, row = pixel_to_cell((entity.x, entity.y), (self.offset_x, self.offset_y), self.tile_size)
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
            
                rail_x, rail_y = self.calc_rail(entity)
                if can_turn:
                    if entity.current_dir in (Direction.LEFT, Direction.RIGHT):
                        dist_from_center = abs(entity.x - rail_x)
                    else:
                        dist_from_center = abs(entity.y - rail_y)
                    # ================== Avoid Snap Jitter ==================
                    # Calculate the exact distance traveled this frame
                    tolerance = entity.speed * dt
                    if entity.current_dir is None or dist_from_center <= tolerance:
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
            col, row = pixel_to_cell((entity.x, entity.y), (self.offset_x, self.offset_y), self.tile_size)
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
                rail_x, rail_y = self.calc_rail(entity)
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
                    entity.x, entity.y = self.calc_rail(entity)
                    entity.current_dir = None 
