import json
from pathlib import Path
from pydantic import BaseModel, model_validator


class HighscoreManager(BaseModel):
    """It manages the persistency and validation of the record's ranking

    Initialization of the record's manager and existent scores loader
    Args:
        filepath (str | Path): Path to the scores JSON file.
    """

    filepath: Path = Path("highscore.json")
    scores: list[dict[str, object]] = []

    is_new_highscore: bool = False

    @model_validator(mode="after")
    def init_load(self) -> "HighscoreManager":
        self.load()
        return self

    def load(self) -> None:
        if not self.filepath.is_file():
            self.scores = []
            return
        try:
            with self.filepath.open("r", encoding="utf-8") as f:
                raw_data = json.load(f)
        except (json.JSONDecodeError, OSError):
            print("[WARNING] Record file not valid, standings reset")
            self.scores = []
            return

        if not isinstance(raw_data, list):
            print(
                "[WARNING] Highscore data is not a list, resetting standings."
            )
            self.scores = []
            return

        # list[dict] -> [{"name": clean_name, "score": raw_score}]
        loaded_scores = []
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
        """Name validation: max 10 char, only alfanumerics and spaces."""

        if not isinstance(name, str):
            return "PLAYER"

        clean_name = ""
        for char in name:
            if char.isalnum() or char == " ":
                clean_name += char
        clean_name = clean_name.strip()[:10]
        if len(clean_name) > 0:
            return clean_name
        else:
            return "PLAYER"

    def save(self) -> None:
        """Saves current highscores to the JSON file."""
        try:
            with self.filepath.open("w", encoding="utf-8") as f:
                json.dump(self.scores, f, indent=4)
        except OSError as e:
            print(f"[ERROR] Could not save highscores to {self.filepath}: {e}")

    def is_highscore(self, score: int) -> bool:
        """Checks if a score qualifies for the top 10 rankings.
        Args:
            score (int): The score to evaluate.
        Returns:
            bool: True if it qualifies for the top 10, False otherwise.
        """
        if not isinstance(score, int) or isinstance(score, bool) or score < 0:
            return False
        if len(self.scores) < 10:
            return True
        return bool(score > int(self.scores[-1]["score"]))

    def add_score(self, name: str, score: int) -> bool:

        def _score(x) -> int:
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
