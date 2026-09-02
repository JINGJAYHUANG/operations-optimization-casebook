# Model contract

A useful optimization case is more than coefficients and a solver call.

## Required fields

```json
{
  "schema_version": "1.0",
  "case_id": "example-case",
  "case_type": "product_mix",
  "title": "Example decision",
  "decision_context": "What must be decided and why",
  "objective_sense": "max",
  "data": {},
  "baseline_decision": {},
  "stress_tests": [],
  "policy": {}
}
```

## Baseline

The baseline must be a feasible current or proposed operating decision, not an arbitrary objective number. It is independently evaluated under the same model.

## Stress tests

Each stress test names one coherent change and provides explicit dotted-path replacements. Patches must preserve the case schema before solving.

## Policy

Recommended fields include:

- `min_improvement`;
- `min_decision_stability_ratio`;
- `max_objective_degradation`;
- service or regret thresholds when relevant;
- `implementation_owner`;
- `require_human_approval`;
- `monitoring_kpis`;
- `rollback_trigger`.

## Known limitations

Limitations are disclosed separately from hard gates. A known simplification is not automatically fatal, but it must not be hidden or converted into a claim that the real system is fully represented.
