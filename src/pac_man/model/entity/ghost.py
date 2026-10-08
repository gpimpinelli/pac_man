"""Ghost entity representation and AI behaviors for Pac-Man."""

import math
import random
from enum import Enum, auto
from typing import Any
from pac_man.utils import pixel_to_cell
from .entity import Entity
from .direction import Direction


class GhostState(Enum):
    """Behavioral states of a ghost entity."""

    SCATTER = auto()
    CHASE = auto()
    FRIGHTENED = auto()
    EATEN = auto()


class Ghost(Entity):
    """Represents a ghost antagonist with state-driven AI movement.

    Attributes:
        state (GhostState): Current behavioral AI state.
        last_decision_cell (tuple[int, int]): Grid coordinates where the last
            routing decision was evaluated.
        respawn_timer (float): Time remaining before ghost returns to action.
        is_frozen (bool): Cheat flag freezing ghost movement.
        initial_speed (float): Ghost speed before freezing.
    """

    state: GhostState = GhostState.SCATTER
    last_decision_cell: tuple[int, int] = (-1, -1)
    respawn_timer: float = 0.0
    is_frozen: bool = False
    initial_speed: float = 0.0

    @property
    def is_already_eaten(self) -> bool:
        """Check whether the ghost has been eaten and is returning to spawn.

        Returns:
            bool: True if the ghost state is EATEN, False otherwise.
        """
        return self.state == GhostState.EATEN

    def set_frozen(self, frozen: bool) -> None:
        """Set the frozen state idempotently."""
        if frozen == self.is_frozen:
            return
        self.is_frozen = frozen
        if frozen:
            self.initial_speed = self.speed
            self.speed = 0.0
        else:
            self.speed = self.initial_speed

    def freeze(self) -> None:
        """Toggle freeze cheat mode."""
        self.set_frozen(not self.is_frozen)
        print(f"[CHEAT] speed: {self.speed}")

    def _evaluate_path(
        self,
        game_state: Any,
        possible_dirs: list[Direction],
        cell_col: int,
        cell_row: int,
        short: bool = True,
    ) -> None:
        """Evaluate candidate directions and choose the best path to target.

        Args:
            game_state (Any): Current game model context.
            possible_dirs (list[Direction]): List of non-blocked directions.
            cell_col (int): Target column grid coordinate.
            cell_row (int): Target row grid coordinate.
            short (bool): True to minimize distance (chase), False to maximize
                distance (flee).
        """
        curr_coords = pixel_to_cell(
            (self.x, self.y), (0, 0), game_state.tile_size
        )
        best_dist = float("inf") if short else -1.0
        best_dir = possible_dirs[0]
        for d in possible_dirs:
            test_col, test_row = curr_coords
            match d:
                case Direction.UP:
                    test_row -= 1
                case Direction.DOWN:
                    test_row += 1
                case Direction.RIGHT:
                    test_col += 1
                case Direction.LEFT:
                    test_col -= 1

            dist = math.dist((test_col, test_row), (cell_col, cell_row))

            if (
                (short and dist < best_dist)
                or (not short and dist >= best_dist)
            ):
                best_dist = dist
                best_dir = d

        self.desired_dir = best_dir

    def update_intention(self, game_state: Any) -> None:
        """Update ghost movement intention based on state and maze geometry.

        Args:
            game_state (Any): Current game model or state context.
        """
        if self.is_frozen:
            self.desired_dir = None
            return

        col, row = pixel_to_cell(
            (self.x, self.y), (0, 0), game_state.tile_size
        )

        if (
            (col, row) == self.last_decision_cell
            and self.current_dir is not None
        ):
            return

        cell = game_state.maze.get_cell(col, row)
        if cell is None or cell.is_solid:
            return

        possible_dirs: list[Direction] = []
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
            Direction.RIGHT: Direction.LEFT,
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
                if game_state.player:
                    player_col, player_row = pixel_to_cell(
                        (game_state.player.x, game_state.player.y),
                        (0, 0),
                        game_state.tile_size,
                    )
                    self._evaluate_path(
                        game_state=game_state,
                        possible_dirs=possible_dirs,
                        cell_col=player_col,
                        cell_row=player_row,
                    )

            case GhostState.FRIGHTENED:
                if game_state.player:
                    player_col, player_row = pixel_to_cell(
                        (game_state.player.x, game_state.player.y),
                        (0, 0),
                        game_state.tile_size,
                    )
                    self._evaluate_path(
                        game_state=game_state,
                        possible_dirs=possible_dirs,
                        cell_col=player_col,
                        cell_row=player_row,
                        short=False,
                    )

            case GhostState.EATEN:
                current_cell = pixel_to_cell(
                    (self.x, self.y), (0, 0), game_state.tile_size
                )
                spawn_cell = pixel_to_cell(
                    self.coords_spawn, (0, 0), game_state.tile_size
                )
                path = game_state.maze.breath_first_search(
                    current_cell, spawn_cell
                )
                if path and len(path) > 1:
                    next_step = path[1]
                    dx = next_step[0] - current_cell[0]
                    dy = next_step[1] - current_cell[1]

                    target_dir = None
                    if dx == 1:
                        target_dir = Direction.RIGHT
                    elif dx == -1:
                        target_dir = Direction.LEFT
                    elif dy == 1:
                        target_dir = Direction.DOWN
                    elif dy == -1:
                        target_dir = Direction.UP

                    if target_dir in possible_dirs:
                        self.desired_dir = target_dir
                    else:
                        self.desired_dir = possible_dirs[0]
                else:
                    self.desired_dir = random.choice(possible_dirs)

        self.last_decision_cell = (col, row)

        if self.current_dir is None:
            self.current_dir = self.desired_dir
