"""Player entity representation and state management for Pac-Man."""

from typing import Any
from enum import Enum, auto
from .entity import Entity


class PlayerState(Enum):
    """Lifecycle states of the Pac-Man player."""

    ALIVE = auto()
    DYING = auto()
    DEAD = auto()


class Player(Entity):
    """Represents the Pac-Man player character.

    Attributes:
        lives (int): Remaining lives count.
        score (int): Accumulated score.
        multiplicator (float): Score multiplier factor.
        super_timer (float): Remaining duration of energized super mode.
        state (PlayerState): Current lifecycle state.
        is_invincible (bool): Cheat mode flag granting invulnerability.
    """

    lives: int = 3
    score: int = 0
    multiplicator: float = 1.0
    super_timer: float = 0.0
    state: PlayerState = PlayerState.ALIVE
    is_invincible: bool = False

    @property
    def is_super(self) -> bool:
        """Check whether Pac-Man is currently in energized super mode.

        Returns:
            bool: True if super timer is active, False otherwise.
        """
        return self.super_timer > 0.0

    @property
    def is_dead(self) -> bool:
        """Check whether Pac-Man is dead.

        Returns:
            bool: True if state is DEAD, False otherwise.
        """
        return self.state == PlayerState.DEAD

    @property
    def has_lives(self) -> bool:
        """Check whether Pac-Man has remaining lives.

        Returns:
            bool: True if lives > 0, False otherwise.
        """
        return self.lives > 0

    def toggle_invincible(self) -> None:
        """Toggle invincibility cheat mode flag."""
        self.is_invincible = not self.is_invincible

    def add_lives(self) -> None:
        """Increase player lives by 1 up to a maximum cap of 7."""
        if self.lives < 7:
            self.lives += 1

    def increase_player_speed(self) -> None:
        """Increase movement speed by 10 up to a maximum cap of 300."""
        if self.speed < 300:
            self.speed += 10

    def remove_super(self) -> None:
        """Immediately reset energized super mode timer to zero."""
        self.super_timer = 0.0

    def update_intention(self, game_state: Any) -> None:
        """Update player movement intentions based on current lifecycle state.

        Args:
            game_state (Any): Current game model or state context.
        """
        match self.state:
            case PlayerState.ALIVE:
                ...

            case PlayerState.DYING:
                self.desired_dir = None
                self.current_dir = None

            case PlayerState.DEAD:
                self.desired_dir = None
                self.current_dir = None
