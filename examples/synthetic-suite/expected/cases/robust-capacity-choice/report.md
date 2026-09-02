# Capacity alternative under uncertain demand regimes

**Case ID:** `robust-capacity-choice`  
**Model type:** `robust_choice`  
**Decision status:** **CONDITIONAL**  
**Solver:** `exact-robust-choice-enumeration`  
**Objective:** `252.375`

> This result is produced from a small deterministic synthetic instance. It demonstrates decision logic and audit controls; it is not a production operating instruction.

## Decision context

Choose among four capacity alternatives using a weighted combination of expected cost, worst-case cost, and maximum regret.

## Recommended decision

```json
{
  "selected": "outsourced"
}
```

## Audit gates

| Gate | Result |
|---|---:|
| `solution_status_optimal` | PASS |
| `decision_feasible` | PASS |
| `objective_recomputed` | PASS |
| `optimality_certificate_exact` | PASS |
| `baseline_feasible` | PASS |
| `baseline_not_better` | PASS |
| `minimum_improvement_met` | PASS |

## Baseline comparison

- Baseline objective: `367.4`
- Improvement in the preferred direction: `115.025`

## Stress and sensitivity

- Stress tests: `3`
- All stress tests feasible: `True`
- Decision stability ratio: `33.3%`
- Worst objective degradation: `82.625`

| Stress | Status | Objective | Decision changed |
|---|---|---:|---:|
| minimax-regret-policy | solved | 65 | False |
| shock-probability-doubles | solved | 255.8125 | True |
| worst-case-policy | solved | 335 | True |

## Implementation gate

- Owner: `S&OP director`
- Human approval required: `False`
- Conditions: `decision_changes_under_material_stress`
- Rollback trigger: Revisit scenario probabilities and costs at each S&OP cycle.
- Monitoring KPIs: capacity utilization, expedite cost, unserved demand
- Known model limitations: scenario costs are modeled estimates

## Interpretation boundary

An exact reference solution proves optimality only for the stated small synthetic instance and model contract. It does not prove that the model includes every real constraint, that input data are current, or that the recommendation should be executed without operational ownership and approval.
