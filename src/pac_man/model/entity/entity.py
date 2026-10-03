from typing import Optional, Any
from .direction import Direction
from abc import ABC, abstractmethod
from pydantic import BaseModel, ConfigDict


class Entity(BaseModel, ABC):
    # x and y are in pixel
    x: float = 0.0
    y: float = 0.0

    speed: float = 125.0
    current_dir: Optional[Direction] = None
    desired_dir: Optional[Direction] = None
    coords_spawn: tuple[float, float] = (0, 0)

    model_config = ConfigDict(validate_assignment=False)

    @abstractmethod
    def update_intention(self, game_state: Any) -> None:
        pass

    def reset_movement(self) -> None:
        self.current_dir = None
        self.desired_dir = None
