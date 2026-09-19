.PHONY: install run debug clean lint lint-strict

install:
	uv sync
	
run:
	uv run python -m src.pac_man config.json

debug:
	uv run python -m pdb -m src.pac_man config.json

clean:
	rm -rf */__pycache__ __pycache__
	rm -rf */mypy_cache mypy_cache
	uv cache clean

lint:
	uv run flake8 src/pac_man 
	uv run mypy src/pac_man --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	uv run flake8 src/pac_man 
	uv run mypy src/pac_man --strict