import pandas as pd
from src.data_generator import main as gen_main
from src.model_training import train_and_save

def test_train_and_save(tmp_path):
    out = tmp_path / "data"
    gen_main(str(out))
    df = pd.read_csv(out / "train.csv")
    model_path, meta = train_and_save(df, "y", ["f1","f2","f3"], ["cat"], str(tmp_path / "models"), str(tmp_path / "models" / "registry.csv"))
    assert "model_v1.joblib" in model_path
    assert meta["auc"] > 0.5
