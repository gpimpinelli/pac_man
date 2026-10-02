from .entity import Entity
from enum import Enum, auto


class PlayerState(Enum):
    ALIVE = auto()
    DYING = auto()
    DEAD = auto()


class Player(Entity):
    lives: int
    score: int = 0
    multiplicator: int = 1
    super_timer: float = 0.0
    state: PlayerState = PlayerState.ALIVE
    is_invincible: bool = False

    @property
    def is_super(self) -> bool:
        """Calcola automaticamente lo stato booleano basandosi sul timer"""
        return self.super_timer > 0.0

    @property
    def is_dead(self) -> bool:
        return self.state == PlayerState.DEAD

    @property
    def has_lives(self) -> bool:
        return self.lives > 0

    def toggle_invincible(self) -> bool:
        self.is_invincible = not self.is_invincible

    def add_lives(self) -> None:
        if self.lives < 7:
            self.lives += 1

    def increase_player_speed(self) -> None:
        if self.speed < 300:
            self.speed += 10

    def remove_super(self) -> None:
        self.super_timer = 0.0

    def update_intention(self, game_state) -> None:
        match self.state:
            case PlayerState.ALIVE:
                pass
            case PlayerState.DYING:
                pass
            case PlayerState.DEAD:
                pass
