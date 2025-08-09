import os
import pandas as pd
import numpy as np
import logging
from typing import List
from .utils import load_config, ensure_dir, setup_logger, list_stream_files
from .data_ingestion import CSVIngestion
from .drift_detection import compute_drift_numeric, compute_drift_categorical, summarize_breaches
from .concept_drift import ConceptDriftDetector
from .model_training import load_latest_model, train_and_save
from .alerting import alert
from .visualization import plot_metric_over_time

logger = logging.getLogger(__name__)

def _split_cols(df: pd.DataFrame, numeric_cols: List[str], cat_cols: List[str]):
    num = [c for c in numeric_cols if c in df.columns]
    cat = [c for c in cat_cols if c in df.columns]
    return num, cat

def monitor(config_path: str):
    cfg = load_config(config_path)
    setup_logger(cfg["output_dirs"]["logs_dir"])
    # Load baseline
    if not os.path.exists(cfg["data"]["baseline_path"]):
        raise FileNotFoundError(f'Baseline not found: {cfg["data"]["baseline_path"]}. Run data generator and init-model first.')
    baseline = pd.read_csv(cfg["data"]["baseline_path"])
    numeric_cols = cfg["retraining"]["numeric_columns"]
    cat_cols = cfg["retraining"]["cat_columns"]
    target = cfg["retraining"]["target"]
    numeric_cols, cat_cols = _split_cols(baseline, numeric_cols, cat_cols)
    # Ingestion
    ingestion = CSVIngestion(cfg["data"]["stream_dir"], cfg["data"]["stream_pattern"])
    # Concept drift
    cdcfg = cfg["concept_drift"]
    concept = ConceptDriftDetector(detector=cdcfg["detector"], adwin_delta=cdcfg["adwin_delta"],
                                   ddm_warning_level=cdcfg["ddm_warning_level"], ddm_out_control_level=cdcfg["ddm_out_control_level"])
    # Load model
    model = load_latest_model(cfg["output_dirs"]["models_dir"])
    if model is None:
        logger.warning("No model found in models/. Did you run init-model?")
    # State
    data_drift_windows = []
    concept_drift_windows = []
    per_feature_history = {c: [] for c in numeric_cols + cat_cols}
    consecutive_breaches = 0
    # Stream files
    stream_files = list_stream_files(cfg["data"]["stream_dir"], cfg["data"]["stream_pattern"]) or []
    if not stream_files:
        raise FileNotFoundError(f'No stream files found under {cfg["data"]["stream_dir"]}. Did you run data_generator?')
    thresholds = cfg["drift"]["thresholds"]
    aggregate_rule = cfg["drift"].get("aggregate_rule", "any")
    for i, path in enumerate(stream_files, start=1):
        df = pd.read_csv(path)
        logger.info(f"Processing {path} ({len(df)} rows)")
        # Data drift per feature
        per_feature = {}
        for c in numeric_cols:
            per_feature[c] = compute_drift_numeric(baseline[c], df[c], thresholds)
            per_feature_history[c].append(per_feature[c]["js_divergence"] if per_feature[c]["js_divergence"] is not None else np.nan)
        for c in cat_cols:
            per_feature[c] = compute_drift_categorical(baseline[c], df[c], thresholds)
            per_feature_history[c].append(per_feature[c]["js_divergence"] if per_feature[c]["js_divergence"] is not None else np.nan)
        data_drift = summarize_breaches(per_feature, aggregate_rule)
        data_drift_windows.append(int(data_drift))
        # Concept drift (if labels available and model present)
        concept_drift = False
        if cdcfg.get("enabled", True) and model is not None and target in df.columns:
            X = df[numeric_cols + cat_cols].copy()
            y = df[target].astype(int).values
            y_pred = model.predict(X)
            errs = (y_pred != y).astype(int)
            for e in errs:
                res = concept.update(int(e))
                if res["change_detected"]:
                    concept_drift = True
                    break
        concept_drift_windows.append(int(concept_drift))
        logger.info(f"Data drift: {data_drift} | Concept drift: {concept_drift}")
        # Retraining logic
        retrain_reason = None
        retrain_on = cfg["retraining"]["retrain_on"]
        trigger = ((retrain_on == "data_drift" and data_drift) or
                   (retrain_on == "concept_drift" and concept_drift) or
                   (retrain_on == "either" and (data_drift or concept_drift)))
        if trigger:
            consecutive_breaches += 1
        else:
            consecutive_breaches = 0
        if cfg["retraining"]["enabled"] and consecutive_breaches >= cfg["retraining"]["min_drift_windows"]:
            retrain_reason = "data_drift" if data_drift else "concept_drift" if concept_drift else "either"
            if cfg["retraining"]["strategy"] == "append":
                new_baseline = pd.concat([baseline, df], ignore_index=True)
            else:
                new_baseline = df.copy()
            baseline = new_baseline
            models_dir = cfg["output_dirs"]["models_dir"]
            registry_path = cfg["output_dirs"]["registry_path"]
            model_path, meta = train_and_save(
                baseline, target, numeric_cols, cat_cols, models_dir, registry_path,
                model_type=cfg["retraining"]["model_type"],
                test_size=cfg["retraining"]["test_size"],
                random_state=cfg["retraining"]["random_state"],
                extra_meta={"notes": f"Auto-retrain due to {retrain_reason} at window {i}"}
            )
            from joblib import load
            model = load(model_path)
            consecutive_breaches = 0
            alert(cfg, "Auto-Retraining Triggered", f"Reason: {retrain_reason} at window {i}\nNew model: {model_path}")
        # Charts
        charts_dir = cfg["output_dirs"]["charts_dir"]
        ensure_dir(charts_dir)
        for c in per_feature_history:
            vals = per_feature_history[c]
            out = os.path.join(charts_dir, f"js_{c}.png")
            plot_metric_over_time(vals, thresholds.get("js_divergence_gt"), title=f"JS divergence for {c}", out_path=out, ylabel="JS", xlabel="window")
        out = os.path.join(charts_dir, "data_drift_flags.png")
        plot_metric_over_time(data_drift_windows, threshold=None, title="Data drift flags over time", out_path=out, ylabel="drift_flag")
        out = os.path.join(charts_dir, "concept_drift_flags.png")
        plot_metric_over_time(concept_drift_windows, threshold=None, title="Concept drift flags over time", out_path=out, ylabel="drift_flag")

    if any(data_drift_windows) or any(concept_drift_windows):
        alert(cfg, "Drift Monitoring Summary", f"Data drift windows: {sum(data_drift_windows)}/{len(data_drift_windows)} | Concept drift windows: {sum(concept_drift_windows)}/{len(concept_drift_windows)}")
