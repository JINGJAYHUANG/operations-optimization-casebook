# Integer workforce coverage across six periods

**Case ID:** `weekly-workforce-coverage`  
**Model type:** `workforce_schedule`  
**Decision status:** **RECOMMENDED**  
**Solver:** `exact-integer-enumeration`  
**Objective:** `906`

> This result is produced from a small deterministic synthetic instance. It demonstrates decision logic and audit controls; it is not a production operating instruction.

## Decision context

Select integer staffing by overlapping shifts to meet every period demand at minimum wage cost.

## Recommended decision

```json
{
  "workers_by_shift": {
    "early": 0,
    "late": 0,
    "mid": 2,
    "split": 4,
    "swing": 3
  }
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

- Baseline objective: `1,277`
- Improvement in the preferred direction: `371`

## Stress and sensitivity

- Stress tests: `3`
- All stress tests feasible: `True`
- Decision stability ratio: `33.3%`
- Worst objective degradation: `151`

| Stress | Status | Objective | Decision changed |
|---|---|---:|---:|
| period-4-demand-plus-2 | solved | 1,057 | True |
| late-shift-cost-plus-20 | solved | 906 | False |
| split-shift-limit-minus-2 | solved | 956 | True |

## Implementation gate

- Owner: `Workforce planning manager`
- Human approval required: `False`
- Rollback trigger: Re-solve when a binding input, cost, capacity, demand, or policy assumption changes.
- Monitoring KPIs: coverage shortfall, overtime, schedule acceptance
- Known model limitations: aggregate skills, no individual preferences

## Interpretation boundary

An exact reference solution proves optimality only for the stated small synthetic instance and model contract. It does not prove that the model includes every real constraint, that input data are current, or that the recommendation should be executed without operational ownership and approval.
