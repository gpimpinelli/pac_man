from typing import Optional
from .direction import Direction
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field, ConfigDict


class Entity(BaseModel, ABC):
    # x and y are in pixel
    x: float = 0.0
    y: float = 0.0

    speed: float = 125.0
    current_dir: Optional[Direction] = None
    desired_dir: Optional[Direction] = None
    coords_spawn: tuple[int, int] = (0, 0)
    color: int = Field(default=0xFFFFFF)
    
    model_config = ConfigDict(validate_assignment=False)

    @abstractmethod
    def update_intention(self, game_state) -> None:
        pass