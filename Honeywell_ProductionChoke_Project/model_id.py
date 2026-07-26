"""
Dynamic model identification from open-loop step-test data.

Model form (per output channel y in {Q, WHP, FLP, BHP}):
    y[k+1] = a*y[k] + b*u[k] + c

Fit by ordinary least squares on the full step-test CSV, then validated
two ways:
  1. One-step-ahead prediction (sanity check on fit quality)
  2. Full open-loop trajectory simulation, feeding predictions back in
     (this is the realistic test -- it's what the MPC will actually do
     when forecasting several steps ahead)
"""
import os
import numpy as np
import pandas as pd

CHANNELS = ["Q", "WHP", "FLP", "BHP"]

# Resolve the step-test CSV relative to this file first (so the project runs
# out-of-the-box for anyone who clones/unzips it), falling back to the
# original dev path if present.
_HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV_PATH = os.path.join(_HERE, "CSv_honeywell.csv")
if not os.path.exists(DEFAULT_CSV_PATH) and os.path.exists("/mnt/user-data/uploads/CSv_honeywell.csv"):
    DEFAULT_CSV_PATH = "/mnt/user-data/uploads/CSv_honeywell.csv"


def load_step_test_data(csv_path):
    df = pd.read_csv(csv_path)
    df.columns = ["t", "u", "Q", "WHP", "FLP", "BHP"]
    return df


def fit_arx1(df, channel):
    """Fit y[k+1] = a*y[k] + b*u[k] + c via least squares. Returns (a, b, c, r2)."""
    y = df[channel].values
    u = df["u"].values
    y_next = y[1:]
    y_curr = y[:-1]
    u_curr = u[:-1]

    X = np.column_stack([y_curr, u_curr, np.ones_like(y_curr)])
    coeffs, *_ = np.linalg.lstsq(X, y_next, rcond=None)
    a, b, c = coeffs

    y_pred_1step = X @ coeffs
    ss_res = np.sum((y_next - y_pred_1step) ** 2)
    ss_tot = np.sum((y_next - y_next.mean()) ** 2)
    r2_1step = 1 - ss_res / ss_tot

    return {"a": a, "b": b, "c": c, "r2_1step": r2_1step}


def simulate_open_loop(model_params, u_sequence, y0):
    """Feed the model its own predictions forward -- realistic multi-step test."""
    y = [y0]
    for u_k in u_sequence[:-1]:
        a, b, c = model_params["a"], model_params["b"], model_params["c"]
        y.append(a * y[-1] + b * u_k + c)
    return np.array(y)


if __name__ == "__main__":
    df = load_step_test_data(DEFAULT_CSV_PATH)

    models = {}
    print(f"{'Channel':6s} {'a':>8s} {'b':>8s} {'c':>10s} {'R2 (1-step)':>12s} {'R2 (open-loop)':>15s}")
    for ch in CHANNELS:
        m = fit_arx1(df, ch)
        models[ch] = m

        y_sim = simulate_open_loop(m, df["u"].values, df[ch].values[0])
        y_actual = df[ch].values
        ss_res = np.sum((y_actual - y_sim) ** 2)
        ss_tot = np.sum((y_actual - y_actual.mean()) ** 2)
        r2_openloop = 1 - ss_res / ss_tot

        print(f"{ch:6s} {m['a']:8.4f} {m['b']:8.4f} {m['c']:10.3f} {m['r2_1step']:12.4f} {r2_openloop:15.4f}")
        models[ch]["r2_openloop"] = r2_openloop
