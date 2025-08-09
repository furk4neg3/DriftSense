#!/usr/bin/env bash
set -euo pipefail

echo "[info] Building Docker image drift-monitor:latest"
docker build -t drift-monitor:latest .

mkdir -p data models logs outputs

echo "[info] Generating synthetic data inside the container"
docker run --rm -v "$(pwd)/data:/app/data" drift-monitor:latest python -m src.data_generator --out data

echo "[info] Training initial model"
docker run --rm -v "$(pwd)/data:/app/data" -v "$(pwd)/models:/app/models" -v "$(pwd)/logs:/app/logs" drift-monitor:latest python -m src.cli init-model --config config.yaml

echo "[info] Running drift monitor"
docker run --rm -v "$(pwd)/data:/app/data" -v "$(pwd)/models:/app/models" -v "$(pwd)/logs:/app/logs" -v "$(pwd)/outputs:/app/outputs" drift-monitor:latest

echo "[done] Charts at ./outputs/charts, models at ./models"
