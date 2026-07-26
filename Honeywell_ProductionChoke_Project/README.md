# Autonomous Production Choke Controller for a Single Naturally Flowing Oil Well
### Honeywell Hackathon Submission

## What this is
A simplified Model Predictive Control (MPC) system that sets the production
choke position each hour to hit a target oil rate (Q) while respecting hard
pressure constraints (WHP, FLP, BHP). See `design_log.md` for the full design
rationale and `presentation_content.md` for the write-up content.

## How to run

```bash
pip install -r requirements.txt

# 1. Identify the dynamic model from step-test data
python model_id.py

# 2. Run all three demonstration scenarios (A/B/C) end-to-end
python scenario_runner.py

# 3. Generate the required plots from the scenario results
python make_plots.py
```

Place `CSv_honeywell.csv` (the step-test dataset) in this same folder before
running — both `model_id.py` and `scenario_runner.py` look for it next to
the scripts first.

## File guide

| File | Purpose |
|---|---|
| `model_id.py` | Fits per-channel first-order ARX models from step-test data; validates 1-step and open-loop (multi-step) R² |
| `mpc_controller.py` | Brute-force constrained MPC: grid search over feasible choke moves, logs full rationale trail |
| `scenario_runner.py` | Wires model + controller together, runs Scenarios A/B/C, asserts zero constraint violations |
| `step_test.py` | Generic open-loop step-test harness (works with any simulator exposing `.step(choke)`) |
| `make_plots.py` | Generates the 6-panel required plot (Target Q, Actual Q, WHP, FLP, BHP, Choke) per scenario |
| `scenario_results.csv` | Logged output of all three scenario runs |
| `design_log.md` | Design decisions, alternatives considered, and why — including a real bug found and fixed during verification |
| `presentation_content.md` | Drop-in content for the required presentation template |

## Key results

| Scenario | Target | Outcome |
|---|---|---|
| A — Startup to Target | 120 bbl/hr | Reached within 2% by hour 8; held exactly |
| B — Target Tracking | 120 → 145 bbl/hr | Reached new target within 2% by hour 7 after the step |
| C — Infeasible Target | 220 bbl/hr | Correctly refused; settled at ~151 bbl/hr, the actual safe maximum |

Zero constraint violations across all three scenarios, verified
programmatically via assertions in `scenario_runner.py` (not just visually
from plots).