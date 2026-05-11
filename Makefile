.PHONY: install debug

install:
	uv sync

run:
	uv run nemo-scrape

debug:
	DEBUG=1 uv run nemo-scrape
