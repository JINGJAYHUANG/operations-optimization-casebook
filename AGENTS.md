# Repository instructions

## Purpose

Maintain an auditable public operations-optimization casebook that separates exact small-instance solving from implementation authorization.

## Non-negotiable rules

- Do not label a heuristic or time-limited result as optimal.
- Preserve independent feasibility and objective recomputation.
- Do not let objective improvement override a hard gate.
- New model families require a positive case, invalid input, infeasible or policy-hold negative control, stress tests, and tamper tests.
- Keep public examples synthetic and free of real company, employee, customer, route, cost, or investment data.
- Do not reduce the test floor to make CI pass.
- Keep fixed-time reference builds deterministic.
- Do not add industrial solver claims without recording solver identity, version, termination status, and gap evidence.

## Required checks

```bash
make release-gate
```
