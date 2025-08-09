import os
from src.versioning import next_version

def test_next_version(tmp_path):
    models = tmp_path / "models"
    models.mkdir()
    assert next_version(str(models)) == 1
    open(models / "model_v1.joblib","wb").close()
    assert next_version(str(models)) == 2
