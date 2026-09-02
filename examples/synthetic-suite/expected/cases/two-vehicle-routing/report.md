# Capacitated two-vehicle routing plan

**Case ID:** `two-vehicle-routing`  
**Model type:** `vehicle_routing`  
**Decision status:** **CONDITIONAL**  
**Solver:** `exact-allocation-and-route-enumeration`  
**Objective:** `344.285801`

> This result is produced from a small deterministic synthetic instance. It demonstrates decision logic and audit controls; it is not a production operating instruction.

## Decision context

Partition six customer stops across two vehicles and optimize visit order subject to vehicle capacity.

## Recommended decision

```json
{
  "routes": [
    [
      "c1",
      "c3",
      "c2"
    ],
    [
      "c4",
      "c5",
      "c6"
    ]
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

- Baseline objective: `348.137449`
- Improvement in the preferred direction: `3.851648`

## Stress and sensitivity

- Stress tests: `3`
- All stress tests feasible: `True`
- Decision stability ratio: `100.0%`
- Worst objective degradation: `60`

| Stress | Status | Objective | Decision changed |
|---|---|---:|---:|
| vehicle-capacity-minus-one | solved | 344.285801 | False |
| customer-c3-demand-plus-one | solved | 344.285801 | False |
| vehicle-fixed-cost-plus-30 | solved | 404.285801 | False |

## Implementation gate

- Owner: `Dispatch supervisor`
- Human approval required: `True`
- Conditions: `human_approval_required`
- Rollback trigger: Re-route when a stop, demand quantity, travel restriction, or vehicle availability changes.
- Monitoring KPIs: route distance, on-time delivery, vehicle utilization
- Known model limitations: Euclidean distance proxy, no time windows, no traffic

## Interpretation boundary

An exact reference solution proves optimality only for the stated small synthetic instance and model contract. It does not prove that the model includes every real constraint, that input data are current, or that the recommendation should be executed without operational ownership and approval.
