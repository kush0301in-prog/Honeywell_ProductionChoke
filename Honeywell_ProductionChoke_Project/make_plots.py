import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

df = pd.read_csv("scenario_results.csv")

LIMITS = {"WHP_min": 150, "WHP_max": 350, "FLP_min": 100, "FLP_max": 250, "BHP_min": 2900, "BHP_max": 3450}

for scenario in df["scenario"].unique():
    d = df[df["scenario"] == scenario]
    fig, axes = plt.subplots(3, 2, figsize=(12, 8))
    fig.suptitle(f"Scenario: {scenario}", fontsize=13, fontweight="bold")

    ax = axes[0, 0]
    ax.plot(d["hour"], d["target_Q"], "--", label="Target Q", color="gray")
    ax.plot(d["hour"], d["Q"], label="Actual Q", color="tab:blue")
    ax.set_ylabel("Oil Rate (bbl/hr)"); ax.legend(); ax.grid(alpha=0.3)

    ax = axes[0, 1]
    ax.plot(d["hour"], d["choke"], color="tab:orange")
    ax.set_ylabel("Choke Position (%)"); ax.grid(alpha=0.3)

    ax = axes[1, 0]
    ax.plot(d["hour"], d["WHP"], color="tab:green")
    ax.axhline(LIMITS["WHP_min"], color="red", ls=":", lw=1)
    ax.axhline(LIMITS["WHP_max"], color="red", ls=":", lw=1)
    ax.set_ylabel("WHP (psi)"); ax.grid(alpha=0.3)

    ax = axes[1, 1]
    ax.plot(d["hour"], d["FLP"], color="tab:purple")
    ax.axhline(LIMITS["FLP_min"], color="red", ls=":", lw=1)
    ax.axhline(LIMITS["FLP_max"], color="red", ls=":", lw=1)
    ax.set_ylabel("FLP (psi)"); ax.grid(alpha=0.3)

    ax = axes[2, 0]
    ax.plot(d["hour"], d["BHP"], color="tab:red")
    ax.axhline(LIMITS["BHP_min"], color="red", ls=":", lw=1, label="limit")
    ax.axhline(LIMITS["BHP_max"], color="red", ls=":", lw=1)
    ax.set_ylabel("BHP (psi)"); ax.set_xlabel("Time (hr)"); ax.legend(); ax.grid(alpha=0.3)

    axes[2, 1].axis("off")

    for ax in axes.flat:
        if ax.has_data():
            ax.set_xlabel("Time (hr)")

    plt.tight_layout()
    plt.savefig(f"plots_{scenario}.png", dpi=110)
    print(f"saved plots_{scenario}.png")
