from .entity import Entity
from enum import Enum, auto


class PlayerState(Enum):
    ALIVE = auto()
    DYING = auto()  # Durante l'animazione in cui Pac-Man si chiude su se stesso
    DEAD = auto()   # Quando l'animazione è finita, in attesa di respawn


class Player(Entity):
    lives: int
    score: int = 0
    multiplicator: int = 1
    super_timer: float = 0.0
    state: PlayerState = PlayerState.ALIVE

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