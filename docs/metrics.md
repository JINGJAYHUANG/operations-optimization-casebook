# Decision-quality metrics

## Objective improvement

For maximization:

```text
optimized objective − baseline objective
```

For minimization:

```text
baseline objective − optimized objective
```

Positive values indicate improvement in the preferred direction.

## Decision stability ratio

```text
stress tests with unchanged decision / total stress tests
```

This is a structural stability indicator, not a probability of success.

## Worst objective degradation

The largest unfavorable objective movement across solved stress cases.

## Audit pass

Requires exact solver status, feasible recomputation, matching objective, and zero reference optimality gap, plus any supplied baseline policy gates.

## Portfolio status counts

The suite reports recommended, conditional, and hold counts separately. A single hold is not offset by multiple recommendations.
