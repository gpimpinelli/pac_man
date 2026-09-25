from pydantic import BaseModel, Field, ConfigDict
from abc import ABC, abstractmethod
from typing import Optional
from .direction import Direction


class Entity(BaseModel, ABC):
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