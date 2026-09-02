# Technician-to-maintenance-task assignment

**Case ID:** `technician-task-assignment`  
**Model type:** `assignment`  
**Decision status:** **RECOMMENDED**  
**Solver:** `exact-permutation-enumeration`  
**Objective:** `23`

> This result is produced from a small deterministic synthetic instance. It demonstrates decision logic and audit controls; it is not a production operating instruction.

## Decision context

Assign five technicians to five maintenance jobs exactly once while respecting one prohibited certification mismatch.

## Recommended decision

```json
{
  "assignments": {
    "tech-a": "inspection",
    "tech-b": "calibration",
    "tech-c": "repair",
    "tech-d": "audit",
    "tech-e": "training"
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

- Baseline objective: `23`
- Improvement in the preferred direction: `0`

## Stress and sensitivity

- Stress tests: `3`
- All stress tests feasible: `True`
- Decision stability ratio: `33.3%`
- Worst objective degradation: `3`

| Stress | Status | Objective | Decision changed |
|---|---|---:|---:|
| tech-e-training-delay | solved | 25 | True |
| repair-complexity-increase | solved | 26 | False |
| audit-duration-reduction | solved | 22 | True |

## Implementation gate

- Owner: `Maintenance coordinator`
- Human approval required: `False`
- Rollback trigger: Re-solve when a binding input, cost, capacity, demand, or policy assumption changes.
- Monitoring KPIs: completion time, rework rate, certification compliance
- Known model limitations: one task per person, no travel-time sequencing

## Interpretation boundary

An exact reference solution proves optimality only for the stated small synthetic instance and model contract. It does not prove that the model includes every real constraint, that input data are current, or that the recommendation should be executed without operational ownership and approval.
