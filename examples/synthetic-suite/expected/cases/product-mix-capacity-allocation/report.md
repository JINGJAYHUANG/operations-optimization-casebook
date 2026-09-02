# Product mix under three constrained resources

**Case ID:** `product-mix-capacity-allocation`  
**Model type:** `product_mix`  
**Decision status:** **RECOMMENDED**  
**Solver:** `exact-vertex-enumeration`  
**Objective:** `2,640`

> This result is produced from a small deterministic synthetic instance. It demonstrates decision logic and audit controls; it is not a production operating instruction.

## Decision context

Choose weekly production quantities that maximize contribution while respecting machine, skilled-labor, and material capacity.

## Recommended decision

```json
{
  "premium": 0.0,
  "service-kit": 2.9999999999999996,
  "standard": 39.0
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

- Baseline objective: `2,176`
- Improvement in the preferred direction: `464`

## Stress and sensitivity

- Stress tests: `3`
- All stress tests feasible: `True`
- Decision stability ratio: `33.3%`
- Worst objective degradation: `-0`

| Stress | Status | Objective | Decision changed |
|---|---|---:|---:|
| labor-capacity-minus-12 | solved | 2,640 | True |
| premium-margin-minus-15-percent | solved | 2,640 | False |
| material-capacity-plus-10 | solved | 2,840 | True |

## Implementation gate

- Owner: `Operations planning manager`
- Human approval required: `False`
- Rollback trigger: Re-solve when a resource capacity or unit contribution changes by more than 5%.
- Monitoring KPIs: contribution, capacity utilization, overtime hours
- Known model limitations: linear unit economics, no setup-time sequence

## Interpretation boundary

An exact reference solution proves optimality only for the stated small synthetic instance and model contract. It does not prove that the model includes every real constraint, that input data are current, or that the recommendation should be executed without operational ownership and approval.
