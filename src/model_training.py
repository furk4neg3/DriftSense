from typing import Dict, Tuple
import os
import time
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, accuracy_score
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from joblib import dump, load
import logging

logger = logging.getLogger(__name__)

def build_pipeline(numeric_cols, cat_cols, model_type="logistic_regression", random_state=42):
    transformers = []
    if numeric_cols:
        transformers.append(("num", StandardScaler(with_mean=True), numeric_cols))
    if cat_cols:
        transformers.append(("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols))
    pre = ColumnTransformer(transformers)
    if model_type == "logistic_regression":
        clf = LogisticRegression(max_iter=1000, n_jobs=None, random_state=random_state)
    else:
        raise ValueError("Unsupported model_type: %s" % model_type)
    pipe = Pipeline([("pre", pre), ("clf", clf)])
    return pipe

def train_and_save(df: pd.DataFrame, target: str, numeric_cols, cat_cols, models_dir: str, registry_path: str,
                   model_type="logistic_regression", test_size=0.2, random_state=42, extra_meta: Dict = None) -> Tuple[str, Dict]:
    X = df[numeric_cols + cat_cols].copy()
    y = df[target].astype(int).values
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, stratify=y, random_state=random_state)
    pipe = build_pipeline(numeric_cols, cat_cols, model_type, random_state)
    pipe.fit(X_train, y_train)
    y_pred_proba = pipe.predict_proba(X_test)[:,1]
    y_pred = (y_pred_proba >= 0.5).astype(int)
    auc = roc_auc_score(y_test, y_pred_proba)
    acc = accuracy_score(y_test, y_pred)
    os.makedirs(models_dir, exist_ok=True)
    cur_versions = [f for f in os.listdir(models_dir) if f.startswith("model_v") and f.endswith(".joblib")]
    next_version = 1
    if cur_versions:
        nums = []
        for f in cur_versions:
            try:
                n = int(f.split("_v")[1].split(".")[0])
                nums.append(n)
            except Exception:
                pass
        if nums:
            next_version = max(nums) + 1
    model_path = os.path.join(models_dir, f"model_v{next_version}.joblib")
    dump(pipe, model_path)
    meta = {
        "version": next_version,
        "model_path": model_path,
        "model_type": model_type,
        "timestamp": int(time.time()),
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "auc": float(auc),
        "accuracy": float(acc),
        "numeric_cols": list(numeric_cols),
        "cat_cols": list(cat_cols),
    }
    if extra_meta:
        meta.update(extra_meta)
    reg_cols = ["version","model_path","model_type","timestamp","train_rows","test_rows","auc","accuracy","numeric_cols","cat_cols","notes"]
    notes = extra_meta.get("notes") if extra_meta else ""
    row = {
        "version": next_version,
        "model_path": model_path,
        "model_type": model_type,
        "timestamp": meta["timestamp"],
        "train_rows": meta["train_rows"],
        "test_rows": meta["test_rows"],
        "auc": meta["auc"],
        "accuracy": meta["accuracy"],
        "numeric_cols": ",".join(meta["numeric_cols"]),
        "cat_cols": ",".join(meta["cat_cols"]),
        "notes": notes or "",
    }
    if os.path.exists(registry_path):
        reg = pd.read_csv(registry_path)
        reg = pd.concat([reg, pd.DataFrame([row])], ignore_index=True)
    else:
        reg = pd.DataFrame([row], columns=reg_cols)
    reg.to_csv(registry_path, index=False)
    logger.info(f"Saved model to {model_path} (AUC={auc:.3f}, ACC={acc:.3f})")
    return model_path, meta

def load_latest_model(models_dir: str):
    cur_versions = [f for f in os.listdir(models_dir) if f.startswith("model_v") and f.endswith(".joblib")]
    if not cur_versions:
        return None
    nums = []
    for f in cur_versions:
        try:
            n = int(f.split("_v")[1].split(".")[0])
            nums.append((n, f))
        except Exception:
            pass
    if not nums:
        return None
    nums.sort()
    latest = nums[-1][1]
    return load(os.path.join(models_dir, latest))
