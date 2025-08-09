from typing import Dict
import logging

logger = logging.getLogger(__name__)

try:
    from river.drift import ADWIN, PageHinkley, KSWIN
except Exception as e:
    raise ImportError(f"River drift module not available as expected: {e}")

def _try_import_ddm():
    try:
        from river.drift.binary import DDM
        return DDM
    except Exception:
        return None

class ConceptDriftDetector:
    def __init__(self, detector: str = "adwin", adwin_delta: float = 0.002, ddm_warning_level: float = 2.0, ddm_out_control_level: float = 3.0,
                 kswin_alpha: float = 0.005, kswin_window_size: int = 100, kswin_stat_size: int = 30,
                 ph_delta: float = 0.005, ph_lambda: float = 50.0, ph_alpha: float = 0.999):
        name = detector.lower()
        self.detector_name = name
        self._warning_supported = False
        if name == "adwin":
            self.detector = ADWIN(delta=adwin_delta)
        elif name == "ddm":
            DDM = _try_import_ddm()
            if DDM is None:
                logger.warning("DDM not available in this River version. Falling back to PageHinkley.")
                self.detector_name = "pagehinkley"
                self.detector = PageHinkley(delta=ph_delta, lambda_=ph_lambda, alpha=ph_alpha)
            else:
                self.detector = DDM(warning_level=ddm_warning_level, out_control_level=ddm_out_control_level)
                self._warning_supported = True
        elif name == "pagehinkley":
            self.detector = PageHinkley(delta=ph_delta, lambda_=ph_lambda, alpha=ph_alpha)
        elif name == "kswin":
            self.detector = KSWIN(alpha=kswin_alpha, window_size=kswin_window_size, stat_size=kswin_stat_size)
        else:
            raise ValueError(f"Unsupported detector: {detector}")

    def update(self, error: int) -> Dict:
        change = self.detector.update(int(error))
        in_drift = bool(change) or bool(getattr(self.detector, "change_detected", False))
        in_warning = bool(getattr(self.detector, "warning_detected", False)) if self._warning_supported else False
        return {"change_detected": in_drift, "warning_detected": in_warning}
