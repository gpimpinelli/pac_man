import os
import mlx
import time
from .entity import Direction, Entity
from .maze_adapter import MazeAdapter
from typing import Optional, Any
from pydantic import BaseModel, Field, ConfigDict
from .entity import Ghost, GhostState, Player, PlayerState


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

    
    def calc_rail(self, entity: Entity) -> tuple[int, int]:
        col = int(entity.x - self.offset_x) // self.tile_size
        row = int(entity.y - self.offset_y) // self.tile_size
        return(
            self.offset_x + (col + 0.5) * self.tile_size,
            self.offset_y + (row + 0.5) * self.tile_size
        )

    def check_and_eat_gum(self) -> None:
        """Controlla la cella attuale e mangia la pallina se presente."""
        col = int((self.player.x - self.offset_x) // self.tile_size)
        row = int((self.player.y - self.offset_y) // self.tile_size)
        
        c = self.maze.get_cell(col, row)
        
        if c is None:
            return

        if c.has_pacgum:
            c.remove_gum(is_super=False)
            # TODO: Aggiungere punteggio base (es. self.score += 10)
            pass
            
        elif c.has_super_pacgum:
            c.remove_gum(is_super=True)
            # TODO: Aggiungere punteggio alto e attivare power-up
            pass


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

        # TODO
        # In futuro, per i fantasmi basterà fare questo!
        for ghost in self.ghosts:
            ghost.update_intention(self)
            self._handle_steering(ghost, dt)
            self._apply_movement(ghost, dt)
            self._handle_wall_collisions(ghost)

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
                col = int((entity.x - self.offset_x) // self.tile_size)
                row = int((entity.y - self.offset_y) // self.tile_size)
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
            col = int((entity.x - self.offset_x) // self.tile_size)
            row = int((entity.y - self.offset_y) // self.tile_size)
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
 
