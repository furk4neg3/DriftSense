import os
import re

def next_version(models_dir: str) -> int:
    files = [f for f in os.listdir(models_dir) if f.startswith("model_v") and f.endswith(".joblib")]
    nums = []
    for f in files:
        m = re.search(r"model_v(\d+)\.joblib", f)
        if m:
            nums.append(int(m.group(1)))
    return (max(nums) + 1) if nums else 1
