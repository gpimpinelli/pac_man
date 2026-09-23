import os
import mlx
import time
from .entity import Direction
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

    
    def calc_rail(self) -> tuple[int, int]:
        col = int(self.player.x - self.offset_x) // self.tile_size
        row = int(self.player.y - self.offset_y) // self.tile_size
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

        if self.player.desired_dir and self.player.desired_dir != self.player.current_dir:
            is_opposite = (
                (self.player.current_dir == Direction.LEFT and self.player.desired_dir == Direction.RIGHT) or
                (self.player.current_dir == Direction.RIGHT and self.player.desired_dir == Direction.LEFT) or
                (self.player.current_dir == Direction.UP and self.player.desired_dir == Direction.DOWN) or
                (self.player.current_dir == Direction.DOWN and self.player.desired_dir == Direction.UP)
            )
            
 
            if is_opposite:
                # Inverti istantaneamente senza calcolare il centro
                self.player.current_dir = self.player.desired_dir
                self.player.desired_dir = None
            else:
                can_turn = False
                col = int((self.player.x - self.offset_x) // self.tile_size)
                row = int((self.player.y - self.offset_y) // self.tile_size)
                current_cell = self.maze.get_cell(col, row)
                if current_cell and not current_cell.is_solid:
                    match self.player.desired_dir:
                        case Direction.UP:
                            can_turn = not current_cell.has_wall_north
                        case Direction.DOWN:
                            can_turn = not current_cell.has_wall_south
                        case Direction.LEFT:
                            can_turn = not current_cell.has_wall_west
                        case Direction.RIGHT:
                            can_turn = not current_cell.has_wall_east
            
                rail_x, rail_y = self.calc_rail()
                if can_turn:
                    if self.player.current_dir in (Direction.LEFT, Direction.RIGHT):
                        dist_from_center = abs(self.player.x - rail_x)
                    else:
                        dist_from_center = abs(self.player.y - rail_y)
                    tolerance = 6.0
                    if self.player.current_dir is None or dist_from_center <= tolerance:
                        self.player.x = rail_x
                        self.player.y = rail_y
                        self.player.current_dir = self.player.desired_dir
                        self.player.desired_dir = None
 
        # 1. Wall check for STRAIGHT movement (this was missing!)
        # The `can_turn` block above only validates walls when desired_dir
        # differs from player.current_dir (i.e. when turning). If the player keeps
        # holding the same direction, that block is skipped entirely and
        # nothing ever stopped movement into a wall/solid cell.
        if self.player.current_dir is not None:
            col = int((self.player.x - self.offset_x) // self.tile_size)
            row = int((self.player.y - self.offset_y) // self.tile_size)
            cell = self.maze.get_cell(col, row)
 
            blocked = cell is None or cell.is_solid
            if not blocked:
                match self.player.current_dir:
                    case Direction.UP:
                        blocked = cell.has_wall_north
                    case Direction.DOWN:
                        blocked = cell.has_wall_south
                    case Direction.LEFT:
                        blocked = cell.has_wall_west
                    case Direction.RIGHT:
                        blocked = cell.has_wall_east
 
            if blocked:
                # Snap flush to the tile center/rail and stop.
                self.player.x, self.player.y = self.calc_rail()
                self.player.current_dir = None
 
        # 2. Movement logic
        match self.player.current_dir:
            case Direction.UP:
                self.player.y -= self.player.speed * dt
            case Direction.DOWN:
                self.player.y += self.player.speed * dt
            case Direction.LEFT:
                self.player.x -= self.player.speed * dt
            case Direction.RIGHT:
                self.player.x += self.player.speed * dt
