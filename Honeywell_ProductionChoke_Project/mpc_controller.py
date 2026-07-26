"""
Simplified MPC controller: brute-force grid search over feasible choke moves.

Requires a `predictive_model` callable with signature:
    Q_pred, WHP_pred, FLP_pred, BHP_pred = predictive_model(choke_position, state)

`predictive_model` is swapped for the real identified dynamic model once
step-test data from the Honeywell simulator is available. This file has
no dependency on where that model comes from.
"""
import numpy as np


def choose_next_choke(
    current_choke,
    predictive_model,
    state,
    target_Q,
    limits,  # dict: WHP_min, WHP_max, FLP_min, FLP_max, BHP_min, BHP_max
    max_move=5.0,  # % per step, per spec
    choke_bounds=(0.0, 100.0),
    search_resolution=0.5,
    terminal_feasibility_fn=None,
):
    """
    Returns (best_choke, info).
    info['trail'] is a list of every candidate evaluated, its predicted
    outcome, whether it was feasible, and why -- this IS the rationale
    the problem statement asks us to provide.

    `terminal_feasibility_fn(u) -> (feasible: bool, reason: str)` is an
    optional extra check on where the system will eventually SETTLE if u
    were held indefinitely (not just its value one hour from now). This
    matters for lagged/sluggish dynamics: a move can look safe one step
    ahead while still being headed toward a future violation. Without
    this, the controller can walk the choke into a state that only
    reveals its infeasibility hours later.
    """
    lo = max(choke_bounds[0], current_choke - max_move)
    hi = min(choke_bounds[1], current_choke + max_move)
    candidates = np.arange(lo, hi + search_resolution / 2, search_resolution)

    trail = []
    best = None

    for u in candidates:
        Q_pred, WHP_pred, FLP_pred, BHP_pred = predictive_model(u, state)

        violations = []
        if not (limits["WHP_min"] <= WHP_pred <= limits["WHP_max"]):
            violations.append(f"WHP {WHP_pred:.1f} outside [{limits['WHP_min']},{limits['WHP_max']}]")
        if not (limits["FLP_min"] <= FLP_pred <= limits["FLP_max"]):
            violations.append(f"FLP {FLP_pred:.1f} outside [{limits['FLP_min']},{limits['FLP_max']}]")
        if not (limits["BHP_min"] <= BHP_pred <= limits["BHP_max"]):
            violations.append(f"BHP {BHP_pred:.1f} outside [{limits['BHP_min']},{limits['BHP_max']}]")

        if terminal_feasibility_fn is not None:
            term_ok, term_reason = terminal_feasibility_fn(u)
            if not term_ok:
                violations.append(f"terminal: {term_reason}")

        feasible = len(violations) == 0
        cost = abs(Q_pred - target_Q) if feasible else np.inf

        entry = {
            "candidate": round(float(u), 3),
            "predicted": {"Q": Q_pred, "WHP": WHP_pred, "FLP": FLP_pred, "BHP": BHP_pred},
            "feasible": feasible,
            "cost": cost,
            "reason": "OK" if feasible else "; ".join(violations),
        }
        trail.append(entry)

        if feasible and (best is None or cost < best["cost"]):
            best = entry

    if best is None:
        return current_choke, {"trail": trail, "note": "No feasible candidate found; holding position."}

    return best["candidate"], {"trail": trail, "note": "OK"}
