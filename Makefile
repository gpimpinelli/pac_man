.PHONY: install run debug clean lint lint-strict package

install:
	uv sync
	
run:
	uv run python -m src.pac_man config.json

debug:
	uv run python -m pdb -m src.pac_man config.json

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +
	uv cache clean

lint:
	uv run flake8 src/pac_man 
	uv run mypy src/pac_man --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	uv run flake8 src/pac_man 
	uv run mypy src/pac_man --strict

package:
	uv run python build_package.py