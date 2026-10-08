import json
from typing import Any
from pathlib import Path
from pydantic import BaseModel, Field, model_validator

NUMERIC_RULES: dict[str, dict[str, int]] = {
    "lives": {"default": 3, "min": 1, "max": 9},
    "seed": {"default": 42, "min": 0, "max": 2_147_483_647},
    "level_max_time": {"default": 90, "min": 10, "max": 3600},
    "points_per_pacgum": {"default": 10, "min": 0, "max": 100_000},
    "points_per_super_pacgum": {"default": 50, "min": 0, "max": 100_000},
    "points_per_ghost": {"default": 200, "min": 0, "max": 100_000},
}


class ConfigParser(BaseModel):
    """Parser and validator for Pac-Man JSON configuration files.

    Loads JSON configuration files, strips line comments (# and //),
    validates numeric constraints, and clamps invalid/missing settings
    to safe defaults in accordance with project specifications.

    Attributes:
        path (Path): Path to the JSON configuration file.
        data (dict): Validated configuration key-value pairs.
    """

    path: Path
    data: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def post_init(self) -> "ConfigParser":
        """Load and parse the JSON configuration file after initialization.

        Reads the file, removes comments, decodes JSON, and validates
        all configuration fields against game rules.

        Returns:
            ConfigParser: The validated ConfigParser instance.

        Raises:
            ValueError: If the file does not exist or contains invalid JSON.
        """
        file_path = Path(self.path)

        if not file_path.is_file():
            raise ValueError(f"File not found: '{file_path}'")

        lines: list[str] = []
        try:
            with file_path.open("r", encoding="utf-8") as f:
                for line in f:
                    if "//" in line:
                        line = line.split("//")[0]
                    if "#" in line:
                        line = line.split("#")[0]
                    clean_line = line.strip()
                    if not clean_line:
                        continue
                    lines.append(clean_line)
            content = "\n".join(lines)
            if not content:
                print(
                    "[CONFIG WARNING] Config file is empty, "
                    "using all default values."
                )
                self.data = {}
            else:
                self.data = json.loads(content)
        except (json.JSONDecodeError, OSError) as e:
            print(
                f"[CONFIG WARNING] Error parsing JSON: {e}. "
                "Using all default values."
            )
            self.data = {}

        self._validate_config()

        return self

    def _validate_config(self) -> None:
        """Validate configuration values and clamp to safe defaults.

        Ensures all expected numeric keys exist, fall within valid ranges,
        checks highscore filename, and guarantees at least 10 valid levels.
        """
        # Parsing numeric elements
        for key, rule in NUMERIC_RULES.items():
            value = self.data.get(key)
            if value is None:
                print(
                    f"[CONFIG WARNING] Key '{key}' missing, "
                    f"using default: {rule['default']}"
                )
                self.data[key] = rule["default"]
                continue

            if not isinstance(value, int) or isinstance(value, bool):
                # '!r' calls repr() to show quotes and exact types
                # in the warning log
                print(
                    f"[CONFIG WARNING] Invalid type for '{key}' ({value!r}), "
                    f"using default: {rule['default']}"
                )
                self.data[key] = rule["default"]
                continue

            if value < rule["min"]:
                print(
                    f"[CONFIG WARNING] Value for '{key}' ({value}) "
                    f"below minimum, clamped to: {rule['min']}"
                )
                self.data[key] = rule["min"]
            elif value > rule["max"]:
                print(
                    f"[CONFIG WARNING] Value for '{key}' "
                    f"({value}) exceeds maximum, clamped to: {rule['max']}"
                )
                self.data[key] = rule["max"]

        # Parsing elements that are not numbers
        # ====================================================================
        #                        highscore_filename
        # ====================================================================
        hs_file = self.data.get("highscore_filename")
        if not isinstance(hs_file, str) or not hs_file.strip():
            print(
                "[CONFIG WARNING] Key 'highscore_filename' missing or "
                "invalid, using default: 'highscores.json'"
            )
            self.data["highscore_filename"] = "highscores.json"

        # ====================================================================
        #                              levels
        # ====================================================================
        levels_raw = self.data.get("levels")
        if not isinstance(levels_raw, list):
            print(
                "[CONFIG WARNING] Key 'levels' is missing or not a list, "
                "fallback to default levels generation."
            )
            levels_raw = []

        validated_levels: list[dict[str, int]] = []
        for i, lvl in enumerate(levels_raw):
            if not isinstance(lvl, dict):
                print(
                    f"[CONFIG WARNING] Level #{i + 1} is not a valid object, "
                    "defaulting to 15x15."
                )
                validated_levels.append({"width": 15, "height": 15})
                continue

            width = lvl.get("width")
            height = lvl.get("height")

            if (
                not isinstance(width, int)
                or isinstance(width, bool) or width < 15
            ):
                print(
                    f"[CONFIG WARNING] Level #{i + 1} "
                    f"'width' ({width!r}) invalid, defaulting to 15."
                )
                width = 15
            elif width % 2 == 0:
                print(
                    f"[CONFIG WARNING] Level #{i + 1} 'width' ({width}) "
                    f"is even, adjusted to odd: {width + 1}."
                )
                width += 1

            # Checking 'height': must be int, >= 15 and odd
            if (
                not isinstance(height, int)
                or isinstance(height, bool) or height < 15
            ):
                print(
                    f"[CONFIG WARNING] Level #{i + 1} "
                    f"'height' ({height!r}) invalid, defaulting to 15."
                )
                height = 15
            elif height % 2 == 0:
                print(
                    f"[CONFIG WARNING] Level #{i + 1} 'height' ({height}) "
                    f"is even, adjusted to odd: {height + 1}."
                )
                height += 1

            validated_levels.append({"width": width, "height": height})

        # Ensure at least 10 levels as required by subject (Chapter VI.7)
        while len(validated_levels) < 10:
            lvl_num = len(validated_levels) + 1
            # Assign size based on the current level
            size = min(15 + (((lvl_num - 1) // 2) * 2), 25)
            print(
                f"[CONFIG WARNING] Levels count is below 10. "
                f"Adding default level #{lvl_num} ({size}x{size})."
            )
            validated_levels.append({"width": size, "height": size})

        self.data["levels"] = validated_levels
