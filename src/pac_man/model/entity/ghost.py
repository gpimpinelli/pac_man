from .entity import Entity
from enum import Enum, auto


class GhostState(Enum):
    SCATTER = auto()    # Pattuglia il suo angolo
    CHASE = auto()      # Insegue Pac-Man
    FRIGHTENED = auto() # Blu e vulnerabile
    EATEN = auto()      # Solo gli occhi che tornano alla base


class Ghost(Entity):
    state: GhostState = GhostState.SCATTER

    def update_intention(self, game_state) -> None:
        match self.state:
            case GhostState.CHASE:
                pass
            case GhostState.SCATTER:
                pass


if __name__ == "__main__":
    ghost = Ghost
    print(type(ghost), ghost)
