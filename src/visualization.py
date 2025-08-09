import os
import matplotlib.pyplot as plt

def plot_metric_over_time(values, threshold=None, title="metric over time", out_path=None, ylabel="value", xlabel="window"):
    plt.figure()
    plt.plot(range(1, len(values)+1), values, marker="o")
    if threshold is not None:
        plt.axhline(threshold, linestyle="--")
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    if out_path:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        plt.savefig(out_path, bbox_inches="tight")
    plt.close()
