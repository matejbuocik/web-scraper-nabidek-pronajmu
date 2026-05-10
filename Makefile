.PHONY: install debug

install:
	uv sync

run:
	uv run python src/main.py

debug:
	DEBUG=1 uv run python src/main.py
