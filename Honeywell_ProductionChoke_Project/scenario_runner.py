"""
Closed-loop scenario runner.

Wires the identified ARX(1,1) models (model_id.py) into the simplified
MPC controller (mpc_controller.py) and runs the three required
demonstration scenarios.

NOTE ON THE PROCESS PROXY: no live simulator object was supplied (only the
reference CSV), so the validated identified model is used as the process
proxy for these runs -- i.e. `process_step` and `predictive_model` share
the same fitted equations. This is standard practice when a live
simulator isn't accessible, and it is the same artifact the deliverables
require us to produce anyway (not extra infrastructure). If the real
Honeywell simulator becomes available, only `process_step` below needs to
be swapped for `simulator.step(u)` -- the controller and everything else
is unchanged.
"""
import pandas as pd

from model_id import load_step_test_data, fit_arx1, CHANNELS, DEFAULT_CSV_PATH
from mpc_controller import choose_next_choke

LIMITS = {
    "WHP_min": 150, "WHP_max": 350,
    "FLP_min": 100, "FLP_max": 250,
    "BHP_min": 2900, "BHP_max": 3450,
}


def build_predictive_model(models):
    def predictive_model(u, state):
        out = {}
        for ch in CHANNELS:
            a, b, c = models[ch]["a"], models[ch]["b"], models[ch]["c"]
            out[ch] = a * state[ch] + b * u + c
        return out["Q"], out["WHP"], out["FLP"], out["BHP"]
    return predictive_model


def build_terminal_feasibility_fn(models, limits):
    """
    Closed-form steady-state check for a first-order ARX model:
    y_ss(u) = (b*u + c) / (1 - a)
    Rejects any candidate whose eventual settling point (if u were held
    forever) would violate a constraint -- catches violations a one-step
    lookahead misses under lagged dynamics.
    """
    def terminal_feasibility_fn(u):
        for ch in ["WHP", "FLP", "BHP"]:
            a, b, c = models[ch]["a"], models[ch]["b"], models[ch]["c"]
            y_ss = (b * u + c) / (1 - a)
            lo, hi = limits[f"{ch}_min"], limits[f"{ch}_max"]
            if not (lo <= y_ss <= hi):
                return False, f"{ch} steady-state {y_ss:.1f} outside [{lo},{hi}]"
        return True, "OK"
    return terminal_feasibility_fn


def run_scenario(name, models, y0_state, u0, target_fn, n_hours):
    """
    target_fn(hour) -> target Q at that hour (lets Scenario B change target mid-run)
    """
    predictive_model = build_predictive_model(models)
    process_step = predictive_model  # see module docstring: same fitted model used as proxy
    terminal_feasibility_fn = build_terminal_feasibility_fn(models, LIMITS)

    state = dict(y0_state)
    choke = u0
    rows = []
    rejections_seen = []

    for hour in range(n_hours):
        target = target_fn(hour)
        next_choke, info = choose_next_choke(
            current_choke=choke,
            predictive_model=predictive_model,
            state=state,
            target_Q=target,
            limits=LIMITS,
            terminal_feasibility_fn=terminal_feasibility_fn,
        )
        rejected = [t for t in info["trail"] if not t["feasible"]]
        if rejected:
            rejections_seen.append((hour, len(rejected), rejected[0]["reason"]))

        Q, WHP, FLP, BHP = process_step(next_choke, state)
        state = {"Q": Q, "WHP": WHP, "FLP": FLP, "BHP": BHP}
        choke = next_choke

        rows.append({
            "scenario": name, "hour": hour, "target_Q": target, "choke": choke,
            "Q": Q, "WHP": WHP, "FLP": FLP, "BHP": BHP, "note": info["note"],
        })

    df = pd.DataFrame(rows)

    # Verification: constraints must never be violated in the applied trajectory
    assert (df["WHP"].between(LIMITS["WHP_min"], LIMITS["WHP_max"])).all(), "WHP violated!"
    assert (df["FLP"].between(LIMITS["FLP_min"], LIMITS["FLP_max"])).all(), "FLP violated!"
    assert (df["BHP"].between(LIMITS["BHP_min"], LIMITS["BHP_max"])).all(), "BHP violated!"
    assert (df["choke"].diff().abs().dropna() <= 5.0001).all(), "Ramp-rate limit violated!"

    return df, rejections_seen


if __name__ == "__main__":
    df_hist = load_step_test_data(DEFAULT_CSV_PATH)
    models = {ch: fit_arx1(df_hist, ch) for ch in CHANNELS}

    results = {}

    # Scenario A: Startup to Target
    y0_A = {"Q": 75.6, "WHP": 287.7, "FLP": 199.5, "BHP": 3249.7}  # steady-state @ u=20%
    df_A, rej_A = run_scenario("A_startup_to_target", models, y0_A, u0=20,
                                target_fn=lambda h: 120, n_hours=40)
    results["A"] = (df_A, rej_A)

    # Scenario B: Target Tracking (start from A's end state, step target up)
    y0_B = df_A.iloc[-1][["Q", "WHP", "FLP", "BHP"]].to_dict()
    u0_B = df_A.iloc[-1]["choke"]
    df_B, rej_B = run_scenario("B_target_tracking", models, y0_B, u0=u0_B,
                                target_fn=lambda h: 120 if h < 15 else 145, n_hours=40)
    results["B"] = (df_B, rej_B)

    # Scenario C: Infeasible Target (request far more than can be produced safely)
    y0_C = {"Q": 75.6, "WHP": 287.7, "FLP": 199.5, "BHP": 3249.7}
    df_C, rej_C = run_scenario("C_infeasible_target", models, y0_C, u0=20,
                                target_fn=lambda h: 220, n_hours=40)
    results["C"] = (df_C, rej_C)

    for name, (df, rej) in results.items():
        print(f"--- Scenario {name} ---")
        print(f"  final choke={df['choke'].iloc[-1]:.1f}%  final Q={df['Q'].iloc[-1]:.1f} bbl/hr  "
              f"final BHP={df['BHP'].iloc[-1]:.1f} psi  target={df['target_Q'].iloc[-1]}")
        print(f"  constraint checks: PASSED (asserted above)")
        print(f"  hours with rejected candidates: {len(rej)}"
              + (f"  e.g. hour {rej[0][0]}: {rej[0][1]} rejected -- {rej[0][2]}" if rej else ""))
        print()

    df_all = pd.concat([results[k][0] for k in results], ignore_index=True)
    df_all.to_csv("scenario_results.csv", index=False)
    print("Saved scenario_results.csv")
