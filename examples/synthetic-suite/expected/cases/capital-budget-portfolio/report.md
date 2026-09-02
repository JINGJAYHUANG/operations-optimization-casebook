# Capital project portfolio with dependencies and risk budget

**Case ID:** `capital-budget-portfolio`  
**Model type:** `capital_budgeting`  
**Decision status:** **CONDITIONAL**  
**Solver:** `exact-binary-portfolio-enumeration`  
**Objective:** `161`

> This result is produced from a small deterministic synthetic instance. It demonstrates decision logic and audit controls; it is not a production operating instruction.

## Decision context

Select a portfolio of operating investments that maximizes modeled value within cash, risk, dependency, and mutual-exclusion constraints.

## Recommended decision

```json
{
  "selected_projects": [
    "automation",
    "energy-upgrade",
    "quality-lab",
    "route-system"
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

- Baseline objective: `108`
- Improvement in the preferred direction: `53`

## Stress and sensitivity

- Stress tests: `3`
- All stress tests feasible: `True`
- Decision stability ratio: `33.3%`
- Worst objective degradation: `13`

| Stress | Status | Objective | Decision changed |
|---|---|---:|---:|
| budget-minus-15 | solved | 148 | True |
| automation-value-minus-20 | solved | 148 | True |
| risk-budget-minus-3 | solved | 161 | False |

## Implementation gate

- Owner: `Capital allocation committee`
- Human approval required: `True`
- Conditions: `human_approval_required`
- Rollback trigger: Re-rank when project cost, value, dependency, or risk estimates change materially.
- Monitoring KPIs: realized NPV, cash draw, risk consumption
- Known model limitations: additive value model, no inter-project synergies except explicit dependencies

## Interpretation boundary

An exact reference solution proves optimality only for the stated small synthetic instance and model contract. It does not prove that the model includes every real constraint, that input data are current, or that the recommendation should be executed without operational ownership and approval.
