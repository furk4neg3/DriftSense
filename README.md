# DriftSense - Production-Ready Concept & Data Drift Monitoring (with Auto-Retraining)

A clean, extensible, **Docker-first** system for detecting **data drift** and **concept drift** in ML pipelines, triggering **auto-retraining**, tracking **model versions**, and sending **alerts**. Includes a realistic **30-day synthetic stream** that injects both feature and label drift.

> **Why it matters:** Drift erodes model ROI. DriftSense turns blind spots into a feedback loop: detect → alert → retrain → version → observe.

---

## Table of Contents

* [What You Get](#what-you-get)
* [Live Demo (One Command)](#live-demo-one-command)
* [Features](#features)
* [Architecture](#architecture)
* [How It Works](#how-it-works)
* [Screenshots & GIF](#screenshots--gif)
* [Quickstart](#quickstart)

  * [Docker](#docker)
  * [Local Dev](#local-dev)
* [Configuration](#configuration)
* [Alerting](#alerting)
* [Project Layout](#project-layout)
* [Extensibility](#extensibility)
* [Design Notes & Trade-offs](#design-notes--trade-offs)
* [Performance & Scaling](#performance--scaling)
* [Security & Privacy](#security--privacy)
* [CI & Quality Gates](#ci--quality-gates)
* [Troubleshooting](#troubleshooting)
* [Roadmap](#roadmap)
* [Contributing](#contributing)
* [License](#license)

---

## What You Get

* **Drift detection**

  * *Data drift:* KS test, Jensen–Shannon divergence, Population Stability Index (PSI), Chi-square for categoricals
  * *Concept drift:* ADWIN (default), optional DDM (auto-fallback to PageHinkley), KSWIN — powered by `river`
* **Auto-retraining** on configurable triggers (data drift, concept drift, or either) with append/replace strategies
* **Model registry & versioning:** `models/model_v{n}.joblib` + `models/registry.csv` with training metadata
* **Monitoring outputs:** drift flags & per-feature charts in `outputs/charts/`
* **Alerting:** Slack webhook + SMTP email (dry-run until you add secrets)
* **Realistic data:** synthetic 30-day stream with both feature distribution shifts and a changed label decision function
* **Production hygiene:** Dockerfile, Make targets, unit tests, typed-ish code, GitHub Actions CI, Codecov, ruff/black/mypy
* **Sanitized repo:** no raw data committed, secrets read from env, `.env.example` provided

---

## Live Demo (One Command)

```bash
make demo
# or
scripts/run_demo.sh
```

This will:

1. Build the Docker image → 2) Generate synthetic data in `./data` → 3) Train baseline → 4) Run the monitor.

Outputs:

* Charts in `./outputs/charts/`
* Versioned models in `./models/`
* Logs in `./logs/`

---

## Features

* **Multi-test data drift:** combine KS, JS-divergence, PSI, and Chi-square; aggregate rule configurable (any/majority)
* **Concept drift detectors:** ADWIN (probabilistic guarantees), DDM (if available in your `river` version), PageHinkley/KSWIN fallbacks
* **Streaming-friendly:** works batch-per-window (CSV today), stubs included for Kafka/API
* **Auto-retrain:** triggered after N consecutive drift windows to avoid flapping
* **Model governance:** registry records version, metrics, timestamp, data size, and notes
* **Fail-fast UX:** clear console errors when config/data/stream is missing
* **Batteries included:** synthetic stream generator to validate end-to-end flow

---

## Architecture

```
Data → [Ingestion] → [Drift Detection] → [Alerts]
        |                              ↘
        └───────────> [Auto-Retrain] → [Model Registry/Versioning] → [Monitor Again]
```

**Modules**

* `data_ingestion.py` — CSV batches (stubs for Kafka/API)
* `drift_detection.py` — per-feature stats (KS/JS/PSI/Chi-square)
* `concept_drift.py` — ADWIN / DDM / PageHinkley / KSWIN (via `river`)
* `model_training.py` — preprocessing pipeline + LogisticRegression baseline + versioning
* `monitor.py` — orchestrates detection, alerting, retraining, and charting
* `alerting.py` — Slack & email (dry-run until secrets are set)
* `visualization.py` — line charts over windows
* `data_generator.py` — 30-day synthetic stream with controlled drifts
* `cli.py` — `init-model`, `run-monitor`

---

## How It Works

1. **Baseline**

   * Train on `data/train.csv` (days 1–7). Registry captures metrics (AUC/ACC) and metadata.
2. **Streaming windows**

   * Each `data/stream/stream_XXXX.csv` is a window/day; per-feature drift stats are computed against the baseline.
3. **Concept drift**

   * If labels are present and a model exists, feed 0/1 prediction errors to a drift detector (ADWIN by default).
4. **Trigger & retrain**

   * When thresholds breach for the configured number of consecutive windows, retrain (append or replace strategy).
5. **Version & alert**

   * Save `model_v{n}.joblib`, update `models/registry.csv`, and alert Slack/email (when configured).

---

## Screenshots & GIF

* **Drift chart (example):** `docs/drift_chart.png`
* **Flow GIF (micro):** `docs/demo.gif`

---

## Quickstart

### Docker

```bash
# Build
docker build -t drift-monitor:latest .

# Generate synthetic data into your host ./data
mkdir -p data models logs outputs
docker run --rm -v "$(pwd)/data:/app/data" drift-monitor:latest \
  python -m src.data_generator --out data

# Train initial model
docker run --rm \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/models:/app/models" \
  -v "$(pwd)/logs:/app/logs" \
  drift-monitor:latest \
  python -m src.cli init-model --config config.yaml

# Run the monitor
docker run --rm \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/models:/app/models" \
  -v "$(pwd)/logs:/app/logs" \
  -v "$(pwd)/outputs:/app/outputs" \
  drift-monitor:latest
```

**One-liner**

```bash
make demo    # or: scripts/run_demo.sh
```

### Local Dev

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
python -m src.data_generator --out data
python -m src.cli init-model --config config.yaml
python -m src.cli run-monitor --config config.yaml
```

---

## Configuration

`config.yaml` (secrets read from env; see `.env.example`):

```yaml
drift:
  thresholds:
    ks_pvalue_lt: 0.05
    js_divergence_gt: 0.10
    psi_gt: 0.25
  aggregate_rule: any   # or: majority

concept_drift:
  detector: adwin       # ddm (fallbacks if unavailable), pagehinkley, kswin
  adwin_delta: 0.002

retraining:
  enabled: true
  retrain_on: either    # data_drift | concept_drift | either
  strategy: append      # append | replace
  min_drift_windows: 1

alerting:
  slack:
    enabled: false
    webhook_url: "${SLACK_WEBHOOK_URL}"
  email:
    enabled: false
    smtp_host: "${SMTP_HOST}"
    smtp_port: "${SMTP_PORT}"
    username: "${SMTP_USERNAME}"
    password: "${SMTP_PASSWORD}"
    from_addr: "${EMAIL_FROM}"
    to_addrs: ["${EMAIL_TO}"]
```

**Environment variables**

```
SLACK_WEBHOOK_URL="YOUR_WEBHOOK_HERE"
SMTP_HOST="smtp.example.com"
SMTP_PORT="587"
SMTP_USERNAME="user@example.com"
SMTP_PASSWORD="REDACTED"
EMAIL_FROM="alerts@example.com"
EMAIL_TO="alerts@example.com"
```

---

## Alerting

* **Slack**: set `alerting.slack.enabled: true` and provide `SLACK_WEBHOOK_URL`.
* **Email**: set `alerting.email.enabled: true` and provide SMTP env vars. If unset, alerts log as dry-runs.

---

## Project Layout

```
.
├── config.yaml
├── Dockerfile
├── Makefile
├── README.md
├── requirements.txt
├── requirements-dev.txt
├── docs/
│   ├── drift_chart.png
│   └── demo.gif
├── src/
│   ├── alerting.py
│   ├── cli.py
│   ├── concept_drift.py
│   ├── data_ingestion.py
│   ├── data_generator.py
│   ├── drift_detection.py
│   ├── model_training.py
│   ├── monitor.py
│   ├── utils.py
│   └── visualization.py
├── tests/
│   ├── test_concept_drift.py
│   ├── test_data_ingestion.py
│   ├── test_drift_detection.py
│   ├── test_model_training.py
│   └── test_versioning.py
├── .github/workflows/ci.yml
├── .env.example
├── .gitignore
├── LICENSE (MIT)
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
└── CHANGELOG.md
```

---

## Extensibility

* **New detectors:** add a function in `drift_detection.py` or plug a new `river` detector in `concept_drift.py`.
* **Different models:** extend `build_pipeline()` in `model_training.py` (e.g., RandomForest/XGBoost) and record custom metrics.
* **Streaming sources:** implement Kafka/APIs in `data_ingestion.py` (we ship stubs & interfaces).
* **Dashboards:** add a FastAPI/Flask service that renders charts in real time (Plotly/Altair).

---

## Design Notes & Trade-offs

* **Aggregation rule** — `any` is safer for regulated use-cases; `majority` reduces noise in high-dimensional feature spaces.
* **Consecutive windows** — `min_drift_windows` avoids retrain flapping on transient noise.
* **Versioning** — filesystem registry is simple and reliable; swap for MLflow/model registry later without changing the monitor loop.
* **Detectors** — ADWIN chosen as default for solid theoretical guarantees on mean changes; DDM availability varies by `river` version, so we auto-fallback.

---

## Performance & Scaling

* Current reference runs per-window on batches (2000 rows in demo). For higher throughput:

  * Move ingestion to Kafka; compute metrics on sliding windows
  * Parallelize per-feature stats (e.g., joblib/dask)
  * Persist intermediate histograms/bins to avoid recomputation

---

## Security & Privacy

* **No secrets in repo** — all read from env (`.env.example` provided)
* **PII** — keep features anonymized; export only aggregate metrics to logs/alerts
* **Images** — Docker runs non-root by default (user `runner`)

---

## CI & Quality Gates

* **GitHub Actions** runs on push/PR: ruff, black --check, mypy (lenient), pytest with coverage
* **Codecov** upload for visibility on PRs
* **Fail-fast** errors for missing config/data ensure broken environments fail quickly

---

## Troubleshooting

* **`ImportError: DDM` in `river`** — we import DDM from `river.drift.binary` when present; otherwise **fallback to PageHinkley** automatically.
* **"Baseline not found"** — run the generator: `python -m src.data_generator --out data` then `python -m src.cli init-model --config config.yaml`.
* **No stream files** — ensure `data/stream/stream_*.csv` exists (the generator creates 30 files).
* **Permissions with Docker volumes** — consider `chmod -R 777 data models logs outputs` once, or run container with `--user root`.

---

## Roadmap

* [ ] Web dashboard (FastAPI + Plotly) with live metrics
* [ ] Model registry integration (MLflow, SageMaker, or custom DB)
* [ ] Advanced drift tests (MMD, EMD) & explainability hooks
* [ ] Kafka connector & API simulation service

---

## Contributing

Pull requests welcome! See [CONTRIBUTING.md](CONTRIBUTING.md). Please follow ruff/black/mypy and keep tests green.

## License

MIT — see [LICENSE](LICENSE).
