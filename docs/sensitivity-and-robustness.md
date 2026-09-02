# Sensitivity and robustness

An optimum can be fragile even when it is mathematically correct.

## Questions to ask

- Does a small input change alter the decision or only the objective?
- Which constraints bind?
- How much does the objective degrade under plausible stress?
- Does the model become infeasible?
- Are several near-optimal decisions operationally interchangeable?
- Is uncertainty represented by scenarios, distributions, or only point estimates?

## Casebook outputs

For each stress:

```text
validation status
feasibility
stressed objective
objective change
preferred-direction degradation
decision changed
audit status
```

The aggregate reports:

```text
decision stability ratio
worst objective degradation
all-stress feasibility
```

## Interpretation

A changed decision is not automatically bad. It may show that the model is responding correctly. The governance question is whether the organization can monitor the triggering input and re-optimize before execution quality deteriorates.

Stress tests are not probability statements unless probabilities are explicitly part of the model.
