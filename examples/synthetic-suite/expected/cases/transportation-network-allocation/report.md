# Minimum-cost plant-to-hub transportation plan

**Case ID:** `transportation-network-allocation`  
**Model type:** `transportation`  
**Decision status:** **RECOMMENDED**  
**Solver:** `successive-shortest-path-min-cost-flow`  
**Objective:** `350`

> This result is produced from a small deterministic synthetic instance. It demonstrates decision logic and audit controls; it is not a production operating instruction.

## Decision context

Allocate one planning period of supply across distribution hubs while honoring a forbidden lane and exact demand balance.

## Recommended decision

```json
{
  "shipments": {
    "east": {
      "hub-d": 25.0
    },
    "north": {
      "hub-a": 30.0,
      "hub-b": 10.0
    },
    "south": {
      "hub-b": 15.0,
      "hub-c": 20.0
    }
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

- Baseline objective: `350`
- Improvement in the preferred direction: `0`

## Stress and sensitivity

- Stress tests: `3`
- All stress tests feasible: `True`
- Decision stability ratio: `0.0%`
- Worst objective degradation: `80`

| Stress | Status | Objective | Decision changed |
|---|---|---:|---:|
| south-to-hub-c-cost-spike | solved | 430 | True |
| hub-d-demand-shift | solved | 375 | True |
| north-supply-reduced | solved | 350 | True |

## Implementation gate

- Owner: `Network planning lead`
- Human approval required: `False`
- Rollback trigger: Re-solve after a lane closure, demand shift above 5 units, or carrier rate change above 8%.
- Monitoring KPIs: landed transport cost, lane utilization, service fill
- Known model limitations: single-period deterministic demand

## Interpretation boundary

An exact reference solution proves optimality only for the stated small synthetic instance and model contract. It does not prove that the model includes every real constraint, that input data are current, or that the recommendation should be executed without operational ownership and approval.
