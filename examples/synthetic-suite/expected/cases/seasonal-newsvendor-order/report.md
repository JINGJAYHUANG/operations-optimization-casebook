# Single-period order quantity under uncertain demand

**Case ID:** `seasonal-newsvendor-order`  
**Model type:** `newsvendor`  
**Decision status:** **CONDITIONAL**  
**Solver:** `exact-discrete-expectation-enumeration`  
**Objective:** `372.5`

> This result is produced from a small deterministic synthetic instance. It demonstrates decision logic and audit controls; it is not a production operating instruction.

## Decision context

Choose a discrete order quantity that maximizes expected contribution while monitoring fill rate and stockout risk.

## Recommended decision

```json
{
  "order_quantity": 70
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

- Baseline objective: `316`
- Improvement in the preferred direction: `56.5`

## Stress and sensitivity

- Stress tests: `3`
- All stress tests feasible: `True`
- Decision stability ratio: `66.7%`
- Worst objective degradation: `13.5`

| Stress | Status | Objective | Decision changed |
|---|---|---:|---:|
| high-demand-shift | solved | 403.5 | False |
| salvage-value-drop | solved | 359 | True |
| shortage-penalty-rise | solved | 369.5 | False |

## Implementation gate

- Owner: `Inventory and merchandising lead`
- Human approval required: `True`
- Conditions: `human_approval_required`
- Rollback trigger: Re-estimate the demand distribution after a material forecast or salvage-value change.
- Monitoring KPIs: fill rate, markdown loss, lost sales
- Known model limitations: single-period demand, estimated probability distribution

## Interpretation boundary

An exact reference solution proves optimality only for the stated small synthetic instance and model contract. It does not prove that the model includes every real constraint, that input data are current, or that the recommendation should be executed without operational ownership and approval.
