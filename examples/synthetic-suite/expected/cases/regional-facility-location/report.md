# Regional facility opening and customer allocation

**Case ID:** `regional-facility-location`  
**Model type:** `facility_location`  
**Decision status:** **CONDITIONAL**  
**Solver:** `exact-facility-and-assignment-enumeration`  
**Objective:** `469`

> This result is produced from a small deterministic synthetic instance. It demonstrates decision logic and audit controls; it is not a production operating instruction.

## Decision context

Select facilities and allocate five customer zones to minimize fixed and shipping cost while meeting facility capacities.

## Recommended decision

```json
{
  "assignments": {
    "zone-1": "alpha",
    "zone-2": "alpha",
    "zone-3": "alpha",
    "zone-4": "delta",
    "zone-5": "delta"
  },
  "open_facilities": [
    "alpha",
    "delta"
  ]
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

- Baseline objective: `745`
- Improvement in the preferred direction: `276`

## Stress and sensitivity

- Stress tests: `3`
- All stress tests feasible: `True`
- Decision stability ratio: `0.0%`
- Worst objective degradation: `52`

| Stress | Status | Objective | Decision changed |
|---|---|---:|---:|
| zone-4-demand-plus-4 | solved | 521 | True |
| delta-fixed-cost-plus-60 | solved | 509 | True |
| alpha-capacity-minus-8 | solved | 500 | True |

## Implementation gate

- Owner: `Supply-chain design director`
- Human approval required: `True`
- Conditions: `decision_changes_under_material_stress`, `human_approval_required`
- Rollback trigger: Re-open the network design when demand, fixed cost, or usable capacity changes materially.
- Monitoring KPIs: total landed cost, facility utilization, service distance
- Known model limitations: single-source customer assignment, no disruption probability

## Interpretation boundary

An exact reference solution proves optimality only for the stated small synthetic instance and model contract. It does not prove that the model includes every real constraint, that input data are current, or that the recommendation should be executed without operational ownership and approval.
