# Operations Optimization Casebook — Reference Suite

**Overall result:** PASS  
**Cases:** `10`  
**Recommended / Conditional / Hold:** `5 / 5 / 0`

> All examples are deterministic and synthetic. The suite validates algorithms, audit gates, reports, and evidence integrity; it does not authorize real operational changes.

| Case | Type | Objective | Status | Improvement | Stability |
|---|---|---:|---|---:|---:|
| `product-mix-capacity-allocation` | `product_mix` | 2,640 | recommended | 464 | 33.3% |
| `transportation-network-allocation` | `transportation` | 350 | recommended | 0 | 0.0% |
| `technician-task-assignment` | `assignment` | 23 | recommended | 0 | 33.3% |
| `regional-facility-location` | `facility_location` | 469 | conditional | 276 | 0.0% |
| `weekly-workforce-coverage` | `workforce_schedule` | 906 | recommended | 371 | 33.3% |
| `seasonal-newsvendor-order` | `newsvendor` | 372.5 | conditional | 56.5 | 66.7% |
| `project-crashing-deadline` | `project_crashing` | 130 | recommended | 230 | 66.7% |
| `two-vehicle-routing` | `vehicle_routing` | 344.285801 | conditional | 3.851648 | 100.0% |
| `robust-capacity-choice` | `robust_choice` | 252.375 | conditional | 115.025 | 33.3% |
| `capital-budget-portfolio` | `capital_budgeting` | 161 | conditional | 53 | 33.3% |

## Portfolio interpretation

A mathematically optimal solution can still be conditional or held when evidence, stress performance, service thresholds, ownership, or approval requirements are incomplete. The casebook intentionally keeps optimization quality separate from implementation authorization.
