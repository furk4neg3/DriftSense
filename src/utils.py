import os
import re
import json
import time
import yaml
import logging
from typing import Dict, Any

def _expand_env(obj):
    if isinstance(obj, dict):
        return {k: _expand_env(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_expand_env(v) for v in obj]
    if isinstance(obj, str):
        return os.path.expandvars(obj)
    return obj

def load_config(path: str) -> Dict[str, Any]:
    with open(path, "r") as f:
        raw = yaml.safe_load(f)
    return _expand_env(raw)

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def setup_logger(logs_dir: str):
    ensure_dir(logs_dir)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(os.path.join(logs_dir, "run.log")),
            logging.StreamHandler()
        ]
    )

def list_stream_files(stream_dir: str, pattern: str):
    files = [os.path.join(stream_dir, f) for f in os.listdir(stream_dir) if f.startswith("stream_") and f.endswith(".csv")]
    def key(f):
        m = re.search(r"(\d+)", os.path.basename(f))
        return int(m.group(1)) if m else 0
    return sorted(files, key=key)

def read_json(path: str):
    with open(path, "r") as f:
        return json.load(f)

def write_json(path: str, obj: Any):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)
