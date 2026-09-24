import math
import random
from .entity import Entity
from .direction import Direction
from enum import Enum, auto


class GhostState(Enum):
    SCATTER = auto()    # Pattuglia il suo angolo
    CHASE = auto()      # Insegue Pac-Man
    FRIGHTENED = auto() # Blu e vulnerabile
    EATEN = auto()      # Solo gli occhi che tornano alla base


class Ghost(Entity):
    state: GhostState = GhostState.SCATTER
    last_decision_cell: tuple[int, int] = (-1, -1)

    def update_intention(self, game_state) -> None:
        col = int((self.x - game_state.offset_x) // game_state.tile_size)
        row = int((self.y - game_state.offset_y) // game_state.tile_size)

        if (col, row) == self.last_decision_cell and self.current_dir is not None:
            return

        cell = game_state.maze.get_cell(col, row)
        if cell is None or cell.is_solid:
            return

        possible_dirs = []
        if not cell.has_wall_north:
            possible_dirs.append(Direction.UP)
        if not cell.has_wall_west:
            possible_dirs.append(Direction.LEFT)
        if not cell.has_wall_east:
            possible_dirs.append(Direction.RIGHT)
        if not cell.has_wall_south:
            possible_dirs.append(Direction.DOWN)

        opposite_map = {
            Direction.UP: Direction.DOWN,
            Direction.DOWN: Direction.UP,
            Direction.LEFT: Direction.RIGHT,
            Direction.RIGHT: Direction.LEFT
        }

        if self.current_dir in opposite_map and len(possible_dirs) > 1:
            opposite = opposite_map[self.current_dir]
            if opposite in possible_dirs:
                possible_dirs.remove(opposite)

        if not possible_dirs:
            return

        match self.state:
            case GhostState.SCATTER:
                self.desired_dir = random.choice(possible_dirs)

            case GhostState.CHASE:
                pass

            case GhostState.FRIGHTENED:
                # TODO: Scapperà (sceglierà la distanza MAGGIORE anziché minore)
                pass

            case GhostState.EATEN:
                # TODO: Tornerà alla base (il target sarà la cella della tana)
                pass
            
        # Fuori dal match block: viene eseguito per tutti gli stati
        self.last_decision_cell = (col, row)

        if self.current_dir is None:
            self.current_dir = self.desired_dir


if __name__ == "__main__":
    ghost = Ghost()
    print(type(ghost), ghost)