"""
Open-loop step-test harness.

Works with ANY simulator object exposing:
    Q, WHP, FLP, BHP = simulator.step(choke_position)

Swap in the real Honeywell simulator here once obtained -- no other
code in this file needs to change.
"""
import pandas as pd


def run_step_test(simulator, choke_sequence, dt_hours=1.0):
    """
    Drive `simulator` through a sequence of choke positions (%, 0-100),
    logging Q, WHP, FLP, BHP at each control step.

    Parameters
    ----------
    simulator : object with .step(choke_position) -> (Q, WHP, FLP, BHP)
    choke_sequence : list[float]   choke opening (%) applied at each step
    dt_hours : float               control interval (spec default: 1 hour)

    Returns
    -------
    pd.DataFrame with columns: time_hr, choke, Q, WHP, FLP, BHP
    """
    records = []
    for i, u in enumerate(choke_sequence):
        Q, WHP, FLP, BHP = simulator.step(u)
        records.append(
            {"time_hr": i * dt_hours, "choke": u, "Q": Q, "WHP": WHP, "FLP": FLP, "BHP": BHP}
        )
    return pd.DataFrame(records)
