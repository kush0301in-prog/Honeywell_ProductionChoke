# Autonomous Production Choke Controller using Model Predictive Control (MPC)

> Honeywell Hackathon 2026 Project

A simplified **Model Predictive Control (MPC)** system that autonomously determines the optimal production choke position for a **single naturally flowing oil well**.

The controller maximizes oil production while maintaining safe operating conditions by respecting pressure constraints on:

- Well Head Pressure (WHP)
- Flow Line Pressure (FLP)
- Bottom Hole Pressure (BHP)

The project identifies system dynamics from historical step-test data, predicts future well behavior using **ARX models**, and selects the best choke position through constrained optimization.

---

# Project Overview

Oil wells operate under strict safety and operational limits. Opening the choke increases production but may reduce critical pressures beyond safe limits.

This project implements a simplified industrial MPC controller capable of

- Predicting future production
- Optimizing choke position every hour
- Respecting operational constraints
- Rejecting unsafe production requests automatically

The controller continuously balances **maximum production** and **safe operation**.

---

# Features

✔ First-order ARX model identification from step-test data

✔ Simplified constrained Model Predictive Control

✔ Automatic optimization of choke settings

✔ Hard safety constraints on WHP, FLP and BHP

✔ Multi-scenario simulation framework

✔ Automatic verification of constraint satisfaction

✔ Automated performance visualization

---

# Project Workflow

```
                    Step-Test Dataset
                           │
                           ▼
                 System Identification
                  (First-Order ARX Model)
                           │
                           ▼
               Model Predictive Controller
                           │
                           ▼
             Optimal Choke Position Selection
                           │
                           ▼
              Well Simulation & Validation
                           │
                           ▼
                Performance Visualization
```

---

# Repository Structure

| File | Description |
|------|-------------|
| `model_id.py` | Identifies first-order ARX models from step-test data |
| `mpc_controller.py` | Implements the constrained MPC controller |
| `scenario_runner.py` | Executes all demonstration scenarios |
| `step_test.py` | Generic step-test simulation framework |
| `make_plots.py` | Generates performance plots |
| `scenario_results.csv` | Logged outputs of all scenarios |
| `design_log.md` | Engineering decisions, assumptions and debugging process |
| `presentation_content.md` | Presentation material prepared for the hackathon |

---

# Installation

Clone the repository

```bash
git clone <repository-url>
cd <repository>
```

Install dependencies

```bash
pip install -r requirements.txt
```

Place

```
CSV_honeywell.csv
```

inside the project directory.

---

# Running the Project

## 1. Identify the Dynamic Model

```bash
python model_id.py
```

Fits first-order ARX models from the supplied step-test dataset.

---

## 2. Run All Scenarios

```bash
python scenario_runner.py
```

Runs every demonstration scenario and verifies all safety constraints.

---

## 3. Generate Performance Plots

```bash
python make_plots.py
```

Produces plots showing

- Target Oil Rate
- Actual Oil Rate
- WHP
- FLP
- BHP
- Choke Position

for every scenario.

---

# Demonstration Scenarios

## Scenario A — Startup to Target

**Target:** 120 bbl/hr

- Starts from initial operating conditions
- Reaches target production within approximately **2%**
- Maintains stable operation

---

## Scenario B — Target Tracking

**Target Change**

120 → 145 bbl/hr

The controller adapts to the new production target while maintaining all pressure constraints.

---

## Scenario C — Infeasible Target

**Requested Production**

220 bbl/hr

The requested production exceeds safe operating limits.

Instead of violating constraints, the controller safely settles near the maximum feasible production (~151 bbl/hr).

---

# Results

| Scenario | Result |
|-----------|--------|
| Startup to Target | Target achieved within 2% |
| Target Tracking | Successfully tracked changing production demand |
| Infeasible Target | Safely rejected unsafe production request |
| Constraint Violations | **Zero** |

All scenarios were verified programmatically using assertions in `scenario_runner.py`.

---

# Engineering Highlights

- System Identification using first-order ARX models
- Constrained optimization through brute-force MPC
- Automatic feasibility checking
- Industrial-style safety constraint enforcement
- Scenario-based validation
- Fully reproducible workflow

---

# Sample Output

> *(Insert generated plots here)*

Example:

```
plots_A_startup_to_target.png

plots_B_target_tracking.png

plots_C_infeasible_target.png
```

---

# Technologies Used

- Python
- NumPy
- Pandas
- Matplotlib
- ARX System Identification
- Model Predictive Control (MPC)

---

# Future Improvements

- Multi-variable MPC
- Longer prediction horizons
- Nonlinear well models
- Real-time optimization
- State estimation using Kalman Filters

---

# Disclaimer

This repository was developed as part of the **Honeywell Hackathon 2026**. It is intended for educational and demonstration purposes and is **not an official Honeywell product or production control system**.

---

# Author

**Kush**

Engineering Student

Model Predictive Control • Python • Control Systems • Data Analytics
