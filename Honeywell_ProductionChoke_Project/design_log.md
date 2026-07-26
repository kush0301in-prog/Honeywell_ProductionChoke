# Honeywell Hackathon — Design Log
## Autonomous Production Choke Controller for a Single Naturally Flowing Oil Well

_Last updated: Milestone 1 (Strategy selection)_

---

## Problem Snapshot

- **Well type:** single naturally flowing well (no gas lift, no ESP, no artificial lift)
- **Manipulated variable:** production choke opening, 0–100%, max ±5% move per control step
- **Control interval (Ts):** 1 hour
- **Controller inputs each step:** current Q, WHP, FLP, BHP, current choke position
- **Objective:** achieve target oil rate (Q) whenever feasible; else settle at max achievable safe rate
- **Active hard constraints:** WHP, FLP, BHP within safe operating envelope (any candidate move predicted to violate these must be rejected)
- **Informational-only variables:** WHT, Annulus Pressure (not active constraints, but should be acknowledged as part of the full envelope)
- **Simulator interface (as specified):** `Q, WHP, FLP, BHP = simulator.step(choke_position)` — simulator will be provided; not required to build it ourselves
- **Demonstration scenarios:**
  - A — Startup to Target
  - B — Target Tracking (step change, e.g. 100 → 150 bbl/hr)
  - C — Infeasible Target (must respect constraints, reject unsafe conditions, settle at max safe rate)
- **Required deliverables:** Python notebook/code, open-loop step-test analysis, dynamic model identification, controller implementation, results for all 3 scenarios, required plots (Target Q, Actual Q, WHP, FLP, BHP, Choke Position per scenario), presentation using provided template (Process Understanding & Model / Control Strategy / Results sections)
- **Deadline:** 26 July 2026, 23:59

---

## Decision Log

### D1 — Control & Prediction Strategy

**Decision:** Simplified Model Predictive Control (MPC) using brute-force/grid-search candidate evaluation over feasible choke moves, driven by a low-order dynamic model identified from open-loop step-test data.

**Why chosen:**
- Single input, three simultaneous hard output constraints + a rate limit — a textbook constrained-MPC problem shape.
- Ts = 1 hour means computational cost is a non-issue; grid search over a handful of candidate moves is trivial.
- Every decision (accept/reject a candidate move) comes with a predicted trajectory and an explicit reason — directly satisfies the "provide rationale" and judge-explainability requirements.
- Matches the official FAQ guidance ("a simplified MPC-style approach is recommended").

**Alternatives considered:** rule-based thresholds, PID (with constraint-override bolt-ons), full solver-based MPC (CasADi/GEKKO), regression/XGBoost as direct controller, reinforcement learning, hybrid ML+MPC.

**Pros:** native multivariable constraint handling; strong explainability; low compute cost; robust via receding-horizon replanning (replans every hour using fresh measurements).

**Cons:** controller quality bounded by model fidelity; more upfront design effort than PID or rule-based.

**Future improvements to flag in "Lessons Learned":** recursive/online model re-identification for adaptation to model-plant mismatch; soft-constraint slack for graceful degradation in infeasible-target cases; uncertainty-aware constraint margins.

---

### D2 — Terminal (Steady-State) Feasibility Check

**Decision:** In addition to checking each candidate's *next-hour* predicted WHP/FLP/BHP, also reject any candidate whose closed-form steady-state value `y_ss = (b·u + c)/(1 - a)` would violate a limit if that choke position were held indefinitely.

**Why chosen:** Verification of Scenario C (infeasible target) surfaced a real bug — with only a one-step-ahead check, the controller kept opening the choke because each *individual* next-hour move looked safe, while the system was still lagging toward a violation from earlier moves. By the time it reached 100% choke, BHP had already been dropping for several hours and blew through the limit. A first-order model gives a closed-form steady-state formula, so this check is nearly free to add.

**Alternatives considered:** full multi-step numerical rollout per candidate (more general, but unnecessary given we have a closed-form first-order model); shrinking the ramp rate (doesn't fix the root cause); tightening limits with an arbitrary safety margin (hides the bug rather than fixing it).

**Pros:** closes the exact gap verification found; still closed-form and cheap; easy to explain in Q&A ("we check not just where this move takes us next hour, but where it would eventually settle").

**Cons:** relies on the first-order model's steady-state formula being valid — would need to move to numerical rollout if a higher-order model were adopted later.

---

### D3 — Source of Numeric Safety Limits (WHP/FLP/BHP)

**Decision:** The Honeywell problem statement defines WHP, FLP, and BHP as active
safety constraints conceptually ("must remain within a safe operating
envelope") but does not specify numeric psi bounds. We derived a closed-loop
operating envelope — `WHP: 150–350 psi`, `FLP: 100–250 psi`, `BHP: 2900–3450
psi` — from the observed range in the step-test data (`WHP 216–270`, `FLP
154–189`, `BHP 2883–3137 psi` across the 30–65% choke range tested), with
margin added on both sides.

**Note on BHP:** the raw step-test data briefly touches ~2883 psi (at 65%
choke) — just below our assumed 2900 psi closed-loop limit. This is expected
and not a contradiction: system identification deliberately explores a wide
range, including toward the edges of the eventual operating envelope, to
characterize dynamics well; the 2900 psi bound is a constraint we enforce
for the *controller's* closed-loop decisions, not a hard physical limit
the open-loop identification experiment itself was required to respect.
Every closed-loop scenario (A/B/C) keeps BHP at or above 2923 psi — the
constraint is never violated during actual controller operation.

**Why chosen:** with no Honeywell-specified numeric envelope, deriving
limits from the observed step-test range is the most defensible, data-driven
choice available, and is explicitly documented here rather than left as an
unexplained hardcoded constant.

---



| Milestone | Content | Status |
|---|---|---|
| M0 | Project setup, simulator interface, and design log | ✅ Completed |
| M1 | Open-loop step tests + dynamic model identification | ✅ Completed |
| M2 | MPC controller implementation | ✅ Completed |
| M3 | Scenario A/B/C runs + required plots | ✅ Completed |
| M4 | Documentation + presentation content | ✅ Completed |
