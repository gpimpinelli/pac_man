import math
import random
from .entity import Entity
from .direction import Direction
from enum import Enum, auto
from src.pac_man.utils import pixel_to_cell

class GhostState(Enum):
    SCATTER = auto()    # Pattuglia il suo angolo
    CHASE = auto()      # Insegue Pac-Man
    FRIGHTENED = auto() # Blu e vulnerabile
    EATEN = auto()      # Solo gli occhi che tornano alla base


class Ghost(Entity):
    state: GhostState = GhostState.SCATTER
    last_decision_cell: tuple[int, int] = (-1, -1)

    @property
    def is_already_eaten(self) -> bool:
        """Check if the ghost have state = GhostState.EATEN"""
        return self.state == GhostState.EATEN

    def _evaluate_path(
        self,
        game_state,
        possible_dirs: list[Direction],
        cell_col: int,
        cell_row: int,
        short: bool = True
    ) -> None:

        curr_coords = pixel_to_cell(
            (self.x, self.y), (0, 0), game_state.tile_size
        )
        best_dist = float("inf") if short else -1.0
        best_dir = possible_dirs[0]
        for d in possible_dirs:
            test_col, test_row= curr_coords
            match d:
                case Direction.UP: test_row -= 1
                case Direction.DOWN: test_row += 1
                case Direction.RIGHT: test_col += 1
                case Direction.LEFT: test_col -= 1

            dist = math.dist((test_col, test_row), (cell_col, cell_row))

            if (
                (short and dist < best_dist) or (not short and dist >= best_dist)
            ):
                best_dist = dist
                best_dir = d

        self.desired_dir = best_dir

    def update_intention(self, game_state) -> None:
        col, row = pixel_to_cell(
            (self.x, self.y), (0, 0), game_state.tile_size
        )

        if (
            (col, row) == self.last_decision_cell and self.current_dir is not None
        ):
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
                player_col, player_row = pixel_to_cell(
                    (game_state.player.x, game_state.player.y),
                    (0, 0),
                    game_state.tile_size
                )
                self._evaluate_path(
                    game_state=game_state,
                    possible_dirs=possible_dirs,
                    cell_col=player_col,
                    cell_row=player_row
                )

            case GhostState.FRIGHTENED:
                player_col, player_row = pixel_to_cell(
                    (game_state.player.x, game_state.player.y),
                    (0, 0),
                    game_state.tile_size
                )
                self._evaluate_path(
                    game_state=game_state,
                    possible_dirs=possible_dirs,
                    cell_col=player_col,
                    cell_row=player_row,
                    short=False
                )

            case GhostState.EATEN:
                spawn_col, spawn_row = pixel_to_cell(
                    self.coords_spawn, (0, 0), game_state.tile_size
                )
                self._evaluate_path(
                    game_state=game_state,
                    possible_dirs=possible_dirs,
                    cell_col=spawn_col,
                    cell_row=spawn_row
                )

        self.last_decision_cell = (col, row)

        if self.current_dir is None:
            self.current_dir = self.desired_dir

if __name__ == "__main__":
    ghost = Ghost()
    print(type(ghost), ghost)