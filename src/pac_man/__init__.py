"""Pac-Man package recreation in Python with MiniLibX graphical interface."""

from .controller import GameController


def main() -> None:
    """Launch the Pac-Man game with default configuration settings."""
    game = GameController()
    game.run()
