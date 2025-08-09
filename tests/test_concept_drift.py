from src.concept_drift import ConceptDriftDetector

def test_adwin_accepts_stream():
    ad = ConceptDriftDetector(detector="adwin", adwin_delta=0.01)
    for _ in range(500):
        ad.update(0)
    changed = False
    for _ in range(500):
        res = ad.update(1)
        if res["change_detected"]:
            changed = True
            break
    assert changed is True
