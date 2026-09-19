import io
import json
from pathlib import Path
from pydantic import BaseModel, Field, model_validator


class MapParser(BaseModel):
    path: Path
    json_data: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def post_init(self) -> "MapParser":
        file_path = Path(self.path)

        if not file_path.is_file():
            raise ValueError(f"File not found: '{file_path}'")

        lines: list[str] = []
        try:
            with file_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line_clean = line.strip()
                    if not line_clean or line_clean.startswith(("#", "//")):
                        continue
                    lines.append(line)

                self.json_data = json.loads("\n".join(lines))
        except json.JSONDecodeError as e:
            raise ValueError(f"Error parsing JSON: {e}")

        # Insert protected methnd for valid config json

        return self

