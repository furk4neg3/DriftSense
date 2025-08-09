import numpy as np
import pandas as pd
from src.drift_detection import compute_drift_numeric, compute_drift_categorical

def test_numeric_drift_detects_shift():
    base = pd.Series(np.random.normal(0,1,2000))
    curr = pd.Series(np.random.normal(1.0,1.3,2000))
    res = compute_drift_numeric(base, curr, {"ks_pvalue_lt":0.05,"js_divergence_gt":0.1,"psi_gt":0.25})
    assert res["breach"] is True

def test_categorical_drift_detects_shift():
    base = pd.Series(np.random.choice(["A","B"], size=2000, p=[0.7,0.3]))
    curr = pd.Series(np.random.choice(["A","B"], size=2000, p=[0.5,0.5]))
    res = compute_drift_categorical(base, curr, {"chi2_pvalue_lt":0.05,"js_divergence_gt":0.1,"psi_gt":0.25})
    assert res["breach"] is True
