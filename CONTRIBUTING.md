# Contributing

Contributions are welcome when they improve model clarity, auditability, solver assurance, or implementation governance.

## New case checklist

1. Define the operational decision before choosing an algorithm.
2. Supply a feasible baseline decision.
3. Add at least two coherent stress tests.
4. Name an implementation owner, monitoring KPIs, and rollback trigger.
5. Add a positive case and a negative control.
6. Independently recompute feasibility and objective.
7. Document model limitations.
8. Run the complete release gate.

## Public boundary

Use synthetic data. Do not commit credentials, private company data, employee schedules, customer locations, commercial rates, real investment values, or production operating instructions.
