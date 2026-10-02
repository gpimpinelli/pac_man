from .controller import GameController


def main() -> None:
    game = GameController()
    game.run()
