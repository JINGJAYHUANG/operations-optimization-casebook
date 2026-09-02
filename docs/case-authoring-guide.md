# Case authoring guide

## Start with the decision

State who decides, when, and what action changes. Avoid beginning with an algorithm name.

## Define the baseline

Supply a feasible current decision that the evaluator can recompute. Do not compare against an undocumented spreadsheet total.

## Bound the public reference instance

Keep instances small enough for transparent exact solving. For larger teaching data, include an industrial-solver adapter and a reduced exact verification case.

## Add negative evidence

Every new model family should include:

- one feasible positive case;
- one invalid input;
- one infeasible case;
- one objective-tamper test;
- one policy hold;
- at least two stress tests.

## Separate limitations from failures

A simplification should be disclosed. A violated constraint, missing owner, or false objective is a failure.
