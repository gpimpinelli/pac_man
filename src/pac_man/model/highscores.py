"""Highscore persistence and leaderboard management for Pac-Man."""

import json
from typing import Any
from pathlib import Path
from pydantic import BaseModel, model_validator


class HighscoreManager(BaseModel):
    """Manages persistence, validation, and ranking of top player scores.

    Attributes:
        filepath (Path): Path to the scores JSON file.
        scores (list[dict[str, Any]]): List of validated score entries.
        is_new_highscore (bool): Flag indicating if last game made top 10.
    """

    filepath: Path = Path("highscore.json")
    scores: list[dict[str, Any]] = []
    is_new_highscore: bool = False

    @model_validator(mode="after")
    def init_load(self) -> "HighscoreManager":
        """Load persistent scores from disk after model initialization.

        Returns:
            HighscoreManager: Initialized highscore manager instance.
        """
        self.load()
        return self

    def load(self) -> None:
        """Load and parse existing highscores from the JSON file.

        Clamps corrupted or invalid files gracefully without throwing
        unhandled exceptions, resetting the leaderboard if unreadable.
        """
        if not self.filepath.is_file():
            self.scores = []
            return
        try:
            with self.filepath.open("r", encoding="utf-8") as f:
                raw_data = json.load(f)
        except (json.JSONDecodeError, OSError):
            print(
                "[WARNING] Highscore file corrupted or invalid, "
                "standings reset."
            )
            self.scores = []
            return

        if not isinstance(raw_data, list):
            print(
                "[WARNING] Highscore data is not a list, resetting standings."
            )
            self.scores = []
            return

        loaded_scores: list[dict[str, Any]] = []
        for item in raw_data:
            if not isinstance(item, dict):
                continue
            raw_name = item.get("name")
            clean_name = self._sanitize_name(raw_name)
            raw_score = item.get("score")
            if type(raw_score) is not int or raw_score < 0:
                continue
            loaded_scores.append({"name": clean_name, "score": raw_score})

        loaded_scores.sort(key=lambda item: int(item["score"]), reverse=True)
        self.scores = loaded_scores[:10]

    @property
    def top_scores_text(self) -> list[str]:
        """Format the top 10 scores into human-readable strings.

        Returns:
            list[str]: Formatted lines for display in the main menu.
        """
        scores_list = self.scores

        if not scores_list:
            return ["NO SCORES YET"]

        formatted_scores = []
        for i, item in enumerate(scores_list):
            name = item.get("name", "PLAYER")
            score = item.get("score", 0)
            formatted_scores.append(f"{i + 1:2}. {name:<10} - {score:05}")

        return formatted_scores

    def _sanitize_name(self, name: object) -> str:
        """Sanitize player name to max 10 alphanumeric and space characters.

        Args:
            name (object): Raw player name input.

        Returns:
            str: Cleaned, truncated uppercase name, defaulting to 'PLAYER'.
        """
        if not isinstance(name, str):
            return "PLAYER"

        clean_name = ""
        for char in name:
            if char.isalnum() or char == " ":
                clean_name += char
        clean_name = clean_name.strip()[:10]
        if len(clean_name) > 0:
            return clean_name
        return "PLAYER"

    def save(self) -> None:
        """Save current highscores to the JSON file on disk."""
        try:
            with self.filepath.open("w", encoding="utf-8") as f:
                json.dump(self.scores, f, indent=4)
        except OSError as e:
            print(f"[ERROR] Could not save highscores to {self.filepath}: {e}")

    def is_highscore(self, score: int) -> bool:
        """Check whether a score qualifies for the top 10 rankings.

        Args:
            score (int): Score value to evaluate.

        Returns:
            bool: True if the score enters the top 10, False otherwise.
        """
        if not isinstance(score, int) or isinstance(score, bool) or score < 0:
            return False
        if len(self.scores) < 10:
            return True
        return bool(score > int(self.scores[-1]["score"]))

    def add_score(self, name: str, score: int) -> bool:
        """Add a new score to the leaderboard if eligible and save to disk.

        Args:
            name (str): Player name.
            score (int): Final score achieved.

        Returns:
            bool: True if score was added to top 10, False otherwise.
        """
        def _score(x: dict[str, Any]) -> int:
            s = x.get("score")
            return s if isinstance(s, int) else 0

        if not self.is_highscore(score):
            return False
        clean_name = self._sanitize_name(name)
        self.scores.append({"name": clean_name, "score": score})
        self.scores.sort(key=_score, reverse=True)
        self.scores = self.scores[:10]
        self.save()
        return True
