SHELL := /bin/bash

.PHONY: help demo build docker-run test lint format typecheck ci

help:
	@echo "Targets: demo, build, docker-run, test, lint, format, typecheck, ci"

build:
	docker build -t drift-monitor:latest .

demo: build
	bash scripts/run_demo.sh

docker-run:
	docker run --rm -v $(PWD)/data:/app/data -v $(PWD)/models:/app/models -v $(PWD)/logs:/app/logs -v $(PWD)/outputs:/app/outputs drift-monitor:latest

test:
	pytest -q --maxfail=1 --disable-warnings

lint:
	ruff check .
	black --check .

format:
	black .

typecheck:
	mypy src

ci: lint typecheck test
