import os
import mlx
import time
from enum import Enum, auto
from src.model import MazeAdapter
from src.view import Renderer, rgb_to_mlx
from typing import Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class Direction(Enum):
    """Represent the four possible movement directions."""
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()

KEYS_MAP = {
    65362: Direction.UP,    # Up Arrow
    119:   Direction.UP,    # w
    65364: Direction.DOWN,  # Down Arrow
    115:   Direction.DOWN,  # s
    65361: Direction.LEFT,  # Left Arrow
    97:    Direction.LEFT,  # a
    65363: Direction.RIGHT, # Right Arrow
    100:   Direction.RIGHT  # d
}


# ==========================================
# 1. MODEL (Physics, Data, and Rules)
# ==========================================
class GameModel(BaseModel):
    """
    Manage the game logic, state, and entity physics.
    Inherits from Pydantic's BaseModel for rigid data initialization.
    """
    # Environment constraints
    screen_width: int = Field(..., gt=0)
    screen_height: int = Field(..., gt=0)
    
    maze: Any

    # Player state & constraints
    x: float = Field(default=50.0, ge=0.0, description="Player X coordinate.")
    y: float = Field(default=150.0, ge=0.0, description="Player Y coordinate.")
    size: int = Field(default=40, gt=0, description="Player width/height in pixels.")
    speed: float = Field(default=180.0, gt=0.0, description="Movement speed (pixels/sec).")
    
    # default_factory is used if a function call is needed, 
    # but here a static call is fine since it evaluates to a simple int.
    color: int = Field(default=rgb_to_mlx(255, 255, 0))
    
    current_dir: Optional[Direction] = Field(default=None)
    desired_dir: Optional[Direction] = Field(default=None)
    started: bool = Field(default=False)

    # Disable assignment validation for performance during the 60fps loop
    model_config = ConfigDict(validate_assignment=False)
    
    tile_size: int = Field(default=32)
    offset_x: int = Field(ge=0)
    offset_y: int = Field(ge=0)
    
    def calc_rail(self) -> tuple[int, int]:
        col = int(self.x - self.offset_x) // self.tile_size
        row = int(self.y - self.offset_y) // self.tile_size
        return(
            self.offset_x + (col + 0.5) * self.tile_size,
            self.offset_y + (row + 0.5) * self.tile_size
        )

    def update(self, dt: float):
        """
        Update the player position and handle collisions.
 
        Args:
            dt: Delta time elapsed since the last frame, in seconds.
        """
        if not self.started:
            return   
 
 
        if self.desired_dir and self.desired_dir != self.current_dir:
            is_opposite = (
                (self.current_dir == Direction.LEFT and self.desired_dir == Direction.RIGHT) or
                (self.current_dir == Direction.RIGHT and self.desired_dir == Direction.LEFT) or
                (self.current_dir == Direction.UP and self.desired_dir == Direction.DOWN) or
                (self.current_dir == Direction.DOWN and self.desired_dir == Direction.UP)
            )
            
 
            if is_opposite:
                # Inverti istantaneamente senza calcolare il centro
                self.current_dir = self.desired_dir
                self.desired_dir = None
            else:
                can_turn = False
                col = int((self.x - self.offset_x) // self.tile_size)
                row = int((self.y - self.offset_y) // self.tile_size)
                current_cell = self.maze.get_cell(col, row)
                if current_cell and not current_cell.is_solid:
                    match self.desired_dir:
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
                    if self.current_dir in (Direction.LEFT, Direction.RIGHT):
                        dist_from_center = abs(self.x - rail_x)
                    else:
                        dist_from_center = abs(self.y - rail_y)
                    tolerance = 6.0
                    if self.current_dir is None or dist_from_center <= tolerance:
                        self.x = rail_x
                        self.y = rail_y
                        self.current_dir = self.desired_dir
                        self.desired_dir = None
 
        # 1. Wall check for STRAIGHT movement (this was missing!)
        # The `can_turn` block above only validates walls when desired_dir
        # differs from current_dir (i.e. when turning). If the player keeps
        # holding the same direction, that block is skipped entirely and
        # nothing ever stopped movement into a wall/solid cell.
        if self.current_dir is not None:
            col = int((self.x - self.offset_x) // self.tile_size)
            row = int((self.y - self.offset_y) // self.tile_size)
            cell = self.maze.get_cell(col, row)
 
            blocked = cell is None or cell.is_solid
            if not blocked:
                match self.current_dir:
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
                self.x, self.y = self.calc_rail()
                self.current_dir = None
 
        # 2. Movement logic
        match self.current_dir:
            case Direction.UP:
                self.y -= self.speed * dt
            case Direction.DOWN:
                self.y += self.speed * dt
            case Direction.LEFT:
                self.x -= self.speed * dt
            case Direction.RIGHT:
                self.x += self.speed * dt
 
        # 3. Screen-edge safety clamp (last-resort guard; maze border cells
        # should already be walled/solid so this normally never triggers)
        if self.x <= 0:
            self.x = 0.0
            if self.current_dir == Direction.LEFT:
                self.current_dir = None
                
        elif self.x + self.size >= self.screen_width:
            self.x = float(self.screen_width - self.size)
            if self.current_dir == Direction.RIGHT:
                self.current_dir = None
 
        if self.y <= 0:
            self.y = 0.0
            if self.current_dir == Direction.UP:
                self.current_dir = None
                
        elif self.y + self.size >= self.screen_height:
            self.y = float(self.screen_height - self.size)
            if self.current_dir == Direction.DOWN:
                self.current_dir = None