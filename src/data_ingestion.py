from typing import Iterator, Dict, Any
import os
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class CSVIngestion:
    def __init__(self, stream_dir: str, pattern: str):
        self.stream_dir = stream_dir
        self.pattern = pattern

    def stream_batches(self) -> Iterator[pd.DataFrame]:
        files = [f for f in sorted(os.listdir(self.stream_dir)) if f.startswith("stream_") and f.endswith(".csv")]
        for f in files:
            path = os.path.join(self.stream_dir, f)
            df = pd.read_csv(path)
            df["__batch_file"] = f
            yield df

class KafkaIngestion:
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg
        logger.warning("Kafka ingestion is a stub.")

    def stream_batches(self) -> Iterator[pd.DataFrame]:
        raise NotImplementedError("Kafka ingestion not implemented.")

class APIIngestion:
    def __init__(self, url: str):
        self.url = url
        logger.warning("API ingestion is a stub.")

    def stream_batches(self) -> Iterator[pd.DataFrame]:
        raise NotImplementedError("API ingestion not implemented.")
