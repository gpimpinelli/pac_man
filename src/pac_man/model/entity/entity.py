"""Base entity representation for movable objects in Pac-Man."""

from typing import Optional, Any
from abc import ABC, abstractmethod
from pydantic import BaseModel, ConfigDict
from .direction import Direction


class Entity(BaseModel, ABC):
    """Abstract base class representing a movable entity.

    Attributes:
        x (float): Current horizontal position in pixels.
        y (float): Current vertical position in pixels.
        speed (float): Movement speed in pixels per second.
        current_dir (Optional[Direction]): Currently moving direction.
        desired_dir (Optional[Direction]): Requested next direction.
        coords_spawn (tuple[float, float]): Spawn coordinates in pixels.
    """

    x: float = 0.0
    y: float = 0.0

    speed: float = 80.0
    current_dir: Optional[Direction] = None
    desired_dir: Optional[Direction] = None
    coords_spawn: tuple[float, float] = (0, 0)

    model_config = ConfigDict(validate_assignment=False)

    @abstractmethod
    def update_intention(self, game_state: Any) -> None:
        """Update desired movement direction based on game state.

        Args:
            game_state (Any): Current game model or state context.
        """
        pass

    def reset_movement(self) -> None:
        """Reset current and desired movement directions to None."""
        self.current_dir = None
        self.desired_dir = None
