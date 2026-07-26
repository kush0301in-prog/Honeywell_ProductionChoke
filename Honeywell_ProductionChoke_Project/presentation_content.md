# Presentation / Report Content
## Autonomous Production Choke Controller for a Single Naturally Flowing Oil Well

Content below is written to fit directly into the required presentation template sections (Process Understanding & Model, Control Strategy, and Results).

---

## Section 1: Process Understanding & Model

**Step-test results**
The provided step-test dataset holds the choke at five levels (30% → 40% →
55% → 45% → 65%) over 120 hours. All four measured variables (Oil Rate,
WHP, FLP, BHP) show clean, monotonic, non-oscillatory first-order-style
responses to each step — Oil Rate increases with choke opening; WHP, FLP,
and BHP all decrease with choke opening (consistent with expected choke
physics: opening the choke trades pressure for flow).

**Model assumptions**
- Each output channel can be modeled independently as a discrete-time
  first-order system driven by choke position: `y[k+1] = a·y[k] + b·u[k] + c`
- No cross-coupling terms between channels were needed — the data didn't
  justify the added complexity of a full multivariable state-space model
- Model assumed valid over the observed operating range (choke 20–65%);
  extrapolation beyond that carries more uncertainty
- **Safety limits** (WHP 150–350, FLP 100–250, BHP 2900–3450 psi): not
  specified numerically in the problem brief, so derived from the observed
  step-test range with added margin. See `design_log.md` (D3) for the full
  rationale, including why the identification data briefly (and
  acceptably) touches the edge of the BHP bound.

**Dynamic model developed**
Fit by ordinary least squares on the full step-test dataset, one model per
channel:

| Channel | a | b | c | R² (one-step) | R² (open-loop, multi-step) |
|---|---|---|---|---|---|
| Q (bbl/hr) | 0.824 | 0.320 | 6.93 | 0.999 | 0.998 |
| WHP (psi) | 0.889 | -0.176 | 35.4 | 0.998 | 0.996 |
| FLP (psi) | 0.863 | -0.136 | 30.1 | 0.998 | 0.994 |
| BHP (psi) | 0.926 | -0.623 | 253.8 | 0.998 | 0.995 |

The open-loop (multi-step, self-fed) R² values matter more than the
one-step values — that's the realistic test of whether this model is good
enough to forecast several hours ahead inside the controller, which is
exactly what MPC needs. All four are above 0.99.

---

## Section 2: Control Strategy

**Prediction methodology**
Simplified MPC: at each 1-hour control interval, candidate choke moves
within the allowed ±5% ramp are evaluated using the identified first-order
model. Each candidate's predicted next-hour Q, WHP, FLP, BHP is computed
in closed form.

**Choke move selection logic**
Grid search over feasible candidates (0.5% resolution); the candidate
minimizing `|predicted Q − target Q|` among *feasible* candidates is
selected. If no candidate is feasible, the controller holds position
(safest fallback) rather than guessing.

**Constraint handling approach**
Two layers of constraint checking per candidate:
1. **Next-hour check** — predicted WHP/FLP/BHP must be within limits
2. **Terminal (steady-state) check** — the closed-form steady-state value
   the system would settle to if that choke position were held
   indefinitely must *also* be within limits

The second layer was added after verification surfaced a real failure
mode: a one-step-ahead-only check let the controller walk the choke open
in small "locally safe" increments that were still headed toward a future
violation, because the system hadn't finished responding to earlier moves
yet. This is a lagged-dynamics problem, and the fix — checking the
eventual settling point, not just next hour — is only cheap because we
have a closed-form first-order model.

Every accepted/rejected candidate is logged with its predicted values and
a plain-English reason (e.g. `"BHP steady-state 2897.6 outside
[2900,3450]"`) — this is the rationale trail for judges/auditors.

**Note on scope:** this is a single-step-cost MPC (each replan minimizes
next-hour error, not a multi-step horizon), which is why Scenario A shows
a small overshoot-then-correct pattern before settling — the controller
doesn't anticipate its own lag, only reacts to it each hour. The terminal
steady-state check keeps this safe despite the myopic cost. A full
multi-step horizon is the natural next iteration, noted below.

---

## Section 3: Results

**Scenario outcomes**

| Scenario | Target | Result |
|---|---|---|
| A — Startup to Target | 120 bbl/hr | Reached within 2% in 8 hours; settled exactly at target |
| B — Target Tracking | 120 → 145 bbl/hr | Reached new target within 2% in 7 hours after the step; tracked exactly |
| C — Infeasible Target | 220 bbl/hr | Correctly refused; settled at ~151 bbl/hr, the actual maximum safe rate |

**Tracking performance:** target reached and held exactly in both feasible
scenarios (A, B), with settling times of 8 and 7 hours respectively —
governed by the ±5%/hour ramp limit, not the controller's decision logic.

**Safety performance:** zero constraint violations across all three
scenarios and all three pressure variables (verified programmatically,
not just visually) — including Scenario C, where the controller
deliberately trades production for safety once BHP approaches its limit.

**Lessons learned**
- A simple, well-validated model beats a complex, unvalidated one — the
  first-order assumption held up (R² > 0.99) and kept the whole system
  explainable
- One-step-ahead constraint checking is insufficient for lagged dynamics;
  verifying against realistic scenarios (not just unit tests) is what
  surfaced this
- Future improvement: online/recursive re-identification so the model
  adapts if real plant behavior drifts from the identified one (relevant
  if this were deployed against the live simulator rather than the
  reference dataset)
