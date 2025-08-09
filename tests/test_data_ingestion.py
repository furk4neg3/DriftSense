import os
from src.data_generator import main as gen_main
from src.data_ingestion import CSVIngestion

def test_csv_ingestion(tmp_path):
    out = tmp_path / "data"
    gen_main(str(out))
    ing = CSVIngestion(str(out / "stream"), "stream_*.csv")
    batches = list(ing.stream_batches())
    assert len(batches) == 30
    assert set(["f1","f2","f3","cat","y"]).issubset(set(batches[0].columns))
