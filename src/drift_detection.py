from typing import Dict, Tuple
import numpy as np
import pandas as pd
from scipy import stats
import logging

logger = logging.getLogger(__name__)

def _histogram(a: np.ndarray, bins: int = 20):
    a = a[~np.isnan(a)]
    if a.size == 0:
        return np.zeros(bins), np.linspace(0,1,bins+1)
    hist, bin_edges = np.histogram(a, bins=bins, density=True)
    hist = hist / (hist.sum() + 1e-12)
    return hist, bin_edges

def jensen_shannon_divergence(p: np.ndarray, q: np.ndarray) -> float:
    p = p / (p.sum() + 1e-12)
    q = q / (q.sum() + 1e-12)
    m = 0.5 * (p + q)
    def kl(a, b):
        a = np.where(a==0, 1e-12, a); b = np.where(b==0, 1e-12, b)
        return np.sum(a * np.log(a / b))
    return 0.5 * (kl(p, m) + kl(q, m))

def population_stability_index(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    expected = expected[~np.isnan(expected)]
    actual = actual[~np.isnan(actual)]
    if expected.size == 0 or actual.size == 0:
        return np.nan
    quantiles = np.quantile(expected, np.linspace(0, 1, bins + 1))
    quantiles[0] = -np.inf; quantiles[-1] = np.inf
    e_counts = np.histogram(expected, bins=quantiles)[0]
    a_counts = np.histogram(actual, bins=quantiles)[0]
    e_prop = e_counts / (e_counts.sum() + 1e-12)
    a_prop = a_counts / (a_counts.sum() + 1e-12)
    psi = np.sum((a_prop - e_prop) * np.log((a_prop + 1e-12) / (e_prop + 1e-12)))
    return psi

def chi_square_test(expected_counts: np.ndarray, observed_counts: np.ndarray) -> Tuple[float, float]:
    mask = expected_counts > 0
    e = expected_counts[mask]; o = observed_counts[mask]
    if e.sum() == 0 or o.sum() == 0:
        return np.nan, np.nan
    chi2, p = stats.chisquare(f_obs=o, f_exp=e * (o.sum() / (e.sum() + 1e-12)))
    return chi2, p

def ks_test(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    x = x[~np.isnan(x)]; y = y[~np.isnan(y)]
    if x.size == 0 or y.size == 0:
        return np.nan, np.nan
    stat, p = stats.ks_2samp(x, y, alternative='two-sided', mode='auto')
    return stat, p

def compute_drift_numeric(baseline: pd.Series, current: pd.Series, thresholds: Dict) -> Dict:
    stat_ks, p_ks = ks_test(baseline.values, current.values)
    hist_base, bins = _histogram(baseline.values, bins=20)
    hist_curr, _ = np.histogram(current.values, bins=bins, density=True)
    hist_curr = hist_curr / (hist_curr.sum() + 1e-12)
    js = jensen_shannon_divergence(hist_base, hist_curr)
    psi = population_stability_index(baseline.values, current.values, bins=10)
    breach = (
        (p_ks==p_ks and p_ks < thresholds.get("ks_pvalue_lt", 0.05)) or
        (js==js and js > thresholds.get("js_divergence_gt", 0.1)) or
        (psi==psi and psi > thresholds.get("psi_gt", 0.25))
    )
    return {"ks_stat": float(stat_ks) if stat_ks==stat_ks else None,
            "ks_pvalue": float(p_ks) if p_ks==p_ks else None,
            "js_divergence": float(js) if js==js else None,
            "psi": float(psi) if psi==psi else None,
            "breach": bool(breach)}

def compute_drift_categorical(baseline: pd.Series, current: pd.Series, thresholds: Dict) -> Dict:
    base_counts = baseline.value_counts(); curr_counts = current.value_counts()
    cats = sorted(set(base_counts.index).union(set(curr_counts.index)))
    e = np.array([base_counts.get(c, 0) for c in cats]).astype(float)
    o = np.array([curr_counts.get(c, 0) for c in cats]).astype(float)
    e_prop = e / (e.sum() + 1e-12); o_prop = o / (o.sum() + 1e-12)
    js = jensen_shannon_divergence(e_prop, o_prop)
    chi2, p = chi_square_test(e, o)
    psi = np.sum((o_prop - e_prop) * np.log((o_prop + 1e-12) / (e_prop + 1e-12)))
    breach = (
        (p==p and p < thresholds.get("chi2_pvalue_lt", 0.05)) or
        (js==js and js > thresholds.get("js_divergence_gt", 0.1)) or
        (psi==psi and psi > thresholds.get("psi_gt", 0.25))
    )
    return {"chi2": float(chi2) if chi2==chi2 else None,
            "chi2_pvalue": float(p) if p==p else None,
            "js_divergence": float(js) if js==js else None,
            "psi": float(psi) if psi==psi else None,
            "breach": bool(breach)}

def summarize_breaches(per_feature: Dict[str, Dict], rule: str = "any") -> bool:
    breaches = [m.get("breach", False) for m in per_feature.values()]
    if not breaches:
        return False
    if rule == "any":
        return any(breaches)
    if rule == "majority":
        return sum(breaches) >= (len(breaches) / 2.0)
    return any(breaches)
