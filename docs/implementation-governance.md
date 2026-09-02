# Implementation governance

Optimization creates a proposed decision, not an authorization.

## Minimum implementation package

- named owner;
- decision scope and effective period;
- data cut-off;
- approval requirement;
- operational dependencies;
- monitoring KPIs;
- rollback or re-solve trigger;
- exception process;
- record of actual implementation;
- post-implementation comparison.

## Hard gates

A case enters `hold` when a hard requirement fails. Objective improvement cannot override the gate.

## Conditional decisions

A conditional result should state exactly what remains open. Examples include human approval, stress fragility, service preference, missing external constraint, or model scope limitation.

## Closed-loop learning

After implementation, compare:

```text
predicted objective
realized objective
predicted constraint usage
realized usage
planned service
realized service
modeled assumptions
observed assumptions
```

Use the variance to update data, model structure, stress tests, and governance thresholds.
