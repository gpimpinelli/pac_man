import json
from pathlib import Path


class HighscoreManager:
    """It manages the persistency and validation of the record's ranking"""

    def __init__(self, filepath: str | Path = "highscores.json") -> None:
        """
        Initialization of the record's manager and existent scores loader
        Args:
            filepath (str | Path): Path to the scores JSON file.
        """
        self.filepath: Path = Path(filepath)
        self.scores: list[dict[str, object]] = []
        self.load()

    def load(self) -> None:
        if not self.filepath.is_file():
            self.scores = []
            return
        try:
            with self.filepath.open("r", encoding="utf-8") as f:
                raw_data = json.load(f)
        except (json.JSONDecodeError, OSError):
            print(
                "[WARNING] Record file not valid, standings reset"
            )
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
            


# ============================================================================
# TODO (Next steps for HighscoreManager):
# 1. In load(): validate score (int >= 0), sort descending, keep top 10.
# 2. In _sanitize_name(): filter alnum/spaces, max 10 chars, fallback "PLAYER".
# 3. Method save(): write self.scores to self.filepath using json.dump().
# 4. Method is_highscore(score): check if a score qualifies for Top 10.
# 5. Method add_score(name, score): add new record, sort, keep top 10, save.
# ============================================================================