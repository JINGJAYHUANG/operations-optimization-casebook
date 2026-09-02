# Project crashing with deadline penalty

**Case ID:** `project-crashing-deadline`  
**Model type:** `project_crashing`  
**Decision status:** **RECOMMENDED**  
**Solver:** `exact-crash-option-enumeration`  
**Objective:** `130`

> This result is produced from a small deterministic synthetic instance. It demonstrates decision logic and audit controls; it is not a production operating instruction.

## Decision context

Choose activity duration-cost options to minimize direct cost plus tardiness penalty while preserving precedence logic.

## Recommended decision

```json
{
  "duration_by_activity": {
    "A": 4.0,
    "B": 4.0,
    "C": 6.0,
    "D": 2.0,
    "E": 4.0,
    "F": 2.0
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

- Baseline objective: `360`
- Improvement in the preferred direction: `230`

## Stress and sensitivity

- Stress tests: `3`
- All stress tests feasible: `True`
- Decision stability ratio: `66.7%`
- Worst objective degradation: `65`

| Stress | Status | Objective | Decision changed |
|---|---|---:|---:|
| deadline-tightened-by-one | solved | 195 | True |
| tardiness-penalty-halved | solved | 130 | False |
| activity-c-crash-cost-plus-30 | solved | 130 | False |

## Implementation gate

- Owner: `Program manager`
- Human approval required: `False`
- Rollback trigger: Recompute after a critical-path duration estimate or deadline changes.
- Monitoring KPIs: project completion date, crash spend, critical-path variance
- Known model limitations: deterministic activity durations, no resource leveling

## Interpretation boundary

An exact reference solution proves optimality only for the stated small synthetic instance and model contract. It does not prove that the model includes every real constraint, that input data are current, or that the recommendation should be executed without operational ownership and approval.
