from .entity import Entity
from enum import Enum, auto


class PlayerState(Enum):
    ALIVE = auto()
    DYING = auto()  # Durante l'animazione in cui Pac-Man si chiude su se stesso
    DEAD = auto()   # Quando l'animazione è finita, in attesa di respawn


class Player(Entity):
    lives: int = 3
    score: int = 0
    multiplicator: int = 1
    super_timer: float = 0.0
    state: PlayerState = PlayerState.ALIVE

    def update_intention(self, game_state) -> None:
        match self.state:
            case ALIVE:
                pass
            case DYING:
                pass
            case DEAD:
                pass