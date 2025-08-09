import os
import argparse
import numpy as np
import pandas as pd
np.random.seed(42)

def generate_day(n=2000, mean_shift=0.0, var_scale=1.0, cat_probs=(0.6, 0.4), concept=False):
    f1 = np.random.normal(loc=0.0 + mean_shift, scale=1.0 * var_scale, size=n)
    f2 = np.random.normal(loc=1.0 + mean_shift, scale=1.5 * var_scale, size=n)
    f3 = np.random.normal(loc=-1.0 + mean_shift, scale=0.5 * var_scale, size=n)
    cat = np.random.choice(["A","B"], size=n, p=cat_probs)
    lin = 1.5*f1 - 1.0*f2 + 0.8*f3 + (cat=="A")*0.5 + (cat=="B")*(-0.5)
    if concept:
        lin = -1.2*f1 + 1.4*f2 - 0.5*f3 + (cat=="A")*(-0.3) + (cat=="B")*(0.7) + 0.3
    prob = 1/(1+np.exp(-lin))
    y = (np.random.rand(n) < prob).astype(int)
    return pd.DataFrame({"f1":f1, "f2":f2, "f3":f3, "cat":cat, "y":y})

def main(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    stream_dir = os.path.join(out_dir, "stream")
    os.makedirs(stream_dir, exist_ok=True)
    # Baseline days 1–7
    dfs = []
    for day in range(1, 8):
        df = generate_day(n=2000, mean_shift=0.0, var_scale=1.0, cat_probs=(0.7,0.3), concept=False)
        df["day"] = day
        dfs.append(df)
        df.to_csv(os.path.join(stream_dir, f"stream_{day:04d}.csv"), index=False)
    pd.concat(dfs, ignore_index=True).to_csv(os.path.join(out_dir, "train.csv"), index=False)
    # Data drift days 8–15
    for day in range(8, 16):
        df = generate_day(n=2000, mean_shift=0.8, var_scale=1.3, cat_probs=(0.5,0.5), concept=False)
        df["day"] = day
        df.to_csv(os.path.join(stream_dir, f"stream_{day:04d}.csv"), index=False)
    # Concept drift days 16–30
    for day in range(16, 31):
        df = generate_day(n=2000, mean_shift=1.0, var_scale=1.4, cat_probs=(0.45,0.55), concept=True)
        df["day"] = day
        df.to_csv(os.path.join(stream_dir, f"stream_{day:04d}.csv"), index=False)
    print(f"Wrote baseline and stream to {out_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="data")
    args = parser.parse_args()
    main(args.out)
