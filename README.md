*This project has been created as part of the 42 curriculum by gipimpin - gpecelli*

# 🟡 Pac-Man 42

A Pac-Man clone built in Python using the **MiniLibX (mlx)** library, following the MVC architectural pattern. Mazes are procedurally generated each game using a configurable seed.

---

## 📋 Requirements

- Linux / WSL (Ubuntu 24.04 recommended)
- Python 3.10+
- [`uv`](https://github.com/astral-sh/uv) package manager

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
make install

# 2. Run the game
make run
```

> The game reads `config.json` from the project root by default.  
> You can also pass a custom config file directly:
> ```bash
> uv run python -m src.pac_man my_config.json
> ```

---

## 🎮 Controls

| Action         | Keys                        |
|----------------|-----------------------------|
| Move Up        | `W` or `↑`                  |
| Move Down      | `S` or `↓`                  |
| Move Left      | `A` or `←`                  |
| Move Right     | `D` or `→`                  |
| Navigate Menu  | `↑` / `↓`                   |
| Confirm / Enter| `ENTER` or `SPACE`          |
| Quit           | `ESC` or `Q`                |

---

## ⚙️ Configuration — `config.json`

All game parameters are controlled via `config.json` in the project root.  
The file supports `//` and `#` line comments.  
Invalid or missing values are automatically **clamped to safe defaults** — the game will never crash due to a bad config.

### Full example

```json
{
    "highscore_filename": "highscores.json",
    "lives": 3,
    "seed": 42,
    "level_max_time": 180,
    "points_per_pacgum": 10,
    "points_per_super_pacgum": 50,
    "points_per_ghost": 200,
    "levels": [
        { "width": 15, "height": 15 },
        { "width": 15, "height": 15 },
        { "width": 17, "height": 17 },
        { "width": 17, "height": 17 },
        { "width": 19, "height": 19 },
        { "width": 19, "height": 19 },
        { "width": 21, "height": 21 },
        { "width": 21, "height": 21 },
        { "width": 23, "height": 23 },
        { "width": 25, "height": 25 },
        { "width": 27, "height": 27 }
    ]
}
```

### Parameter reference

| Key | Type | Default | Min | Max | Description |
|-----|------|---------|-----|-----|-------------|
| `lives` | `int` | `3` | `1` | `9` | Number of lives at game start |
| `seed` | `int` | `42` | `0` | `2147483647` | Maze generation seed — same seed = same maze every time |
| `level_max_time` | `int` | `90` | `10` | `3600` | Time limit per level in **seconds** |
| `points_per_pacgum` | `int` | `10` | `0` | `100000` | Points earned per regular Pac-Gum eaten |
| `points_per_super_pacgum` | `int` | `50` | `0` | `100000` | Points earned per Super Pac-Gum eaten |
| `points_per_ghost` | `int` | `200` | `0` | `100000` | Points earned per ghost eaten while frightened |
| `highscore_filename` | `string` | `"highscores.json"` | — | — | Path to the highscores save file |
| `levels` | `array` | *(see below)* | — | — | List of level definitions (minimum 10 required) |

### Levels

Each level entry defines the **maze size**:

```json
{ "width": 15, "height": 15 }
```

- Both `width` and `height` must be **odd integers ≥ 15** (required by the maze generator).
- If an even number is provided, it is automatically incremented by 1.
- The game requires **at least 10 levels**. If fewer are defined, defaults are added automatically.

### Screen size & resolution

The window size is currently fixed at **1640 × 1000 px** and is designed for Full HD screens or larger.  
If you need to adapt it to a smaller screen, edit the `GameConfig` in [`src/pac_man/controller/game_controller.py`](src/pac_man/controller/game_controller.py):

```python
# Line ~93 — change width and height to match your screen
self.config = GameConfig(width=1640, height=1000, target_fps=60)
```

> **Tip:** The maze and tile sizes scale automatically based on window dimensions, so the game adapts to any resolution you set here.

---

## 🛠️ Make targets

| Command | Description |
|---------|-------------|
| `make install` | Install all Python dependencies via `uv` |
| `make run` | Run the game with `config.json` |
| `make debug` | Run the game under the Python debugger (`pdb`) |
| `make clean` | Remove `__pycache__`, `.mypy_cache` and `uv` cache |
| `make lint` | Run `flake8` + `mypy` (standard) |
| `make lint-strict` | Run `flake8` + `mypy --strict` |

---

## 📁 Project structure

```
pac_man/
├── config.json              ← Game configuration
├── highscores.json          ← Saved high scores
├── Makefile
├── en.subject.pdf
└── src/pac_man/
    ├── __main__.py          ← Entry point
    ├── config_parser.py     ← JSON config loader & validator
    ├── controller/
    │   └── game_controller.py
    ├── model/               ← Game logic (maze, entities, physics)
    └── view/
        ├── game_view.py     ← Rendering & MLX interface
        ├── colors.py        ← Color palette
        └── sprites/         ← XPM sprite files
```

---

## 🎯 How to play

1. **Eat all Pac-Gums** (dots) in the maze to complete the level and advance.
2. **Super Pac-Gums** (corner dots) turn all ghosts **blue and frightened** — chase and eat them for bonus points!
3. **Avoid ghosts** in normal state — each collision costs one life.
4. If you run out of lives or time, it's **Game Over**.
5. At game over, you can **save your name and score** to the highscores board.
