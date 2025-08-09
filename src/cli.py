import argparse, os, sys
from .monitor import monitor
from .model_training import train_and_save
from .utils import load_config, setup_logger
import pandas as pd

def die(msg: str, code: int = 2):
    print(f"[FATAL] {msg}", file=sys.stderr)
    sys.exit(code)

def main():
    parser = argparse.ArgumentParser(description="Drift Monitoring CLI")
    sub = parser.add_subparsers(dest="cmd")

    mon = sub.add_parser("run-monitor", help="Run drift monitor")
    mon.add_argument("--config", required=True)

    initm = sub.add_parser("init-model", help="Train initial model on baseline")
    initm.add_argument("--config", required=True)

    args = parser.parse_args()
    if args.cmd == "run-monitor":
        if not os.path.exists(args.config):
            die(f'Config not found: {args.config}. Did you mount the repo and run from project root?')
        monitor(args.config)
    elif args.cmd == "init-model":
        if not os.path.exists(args.config):
            die(f'Config not found: {args.config}.')
        cfg = load_config(args.config)
        setup_logger(cfg["output_dirs"]["logs_dir"])
        baseline_path = cfg["data"]["baseline_path"]
        if not os.path.exists(baseline_path):
            die(f'Baseline not found: {baseline_path}. Generate data first: "python -m src.data_generator --out data"')
        df = pd.read_csv(baseline_path)
        train_and_save(
            df,
            target=cfg["retraining"]["target"],
            numeric_cols=cfg["retraining"]["numeric_columns"],
            cat_cols=cfg["retraining"]["cat_columns"],
            models_dir=cfg["output_dirs"]["models_dir"],
            registry_path=cfg["output_dirs"]["registry_path"],
            model_type=cfg["retraining"]["model_type"],
            test_size=cfg["retraining"]["test_size"],
            random_state=cfg["retraining"]["random_state"],
            extra_meta={"notes": "Initial model"}
        )
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
