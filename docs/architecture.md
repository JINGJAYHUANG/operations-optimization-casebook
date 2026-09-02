# Architecture

## Separation of concerns

The project separates five layers that are often collapsed into one solver script.

### 1. Decision contract

Defines the decision, objective sense, data, constraints, baseline, stress cases, implementation owner, monitoring, and rollback rule.

### 2. Reference solver

Computes an exact solution for a deliberately bounded synthetic instance. The solver is transparent and deterministic.

### 3. Independent audit

Recomputes feasibility and objective value from the returned decision. Solver self-reporting is not sufficient.

### 4. Decision governance

Evaluates baseline improvement, service or regret thresholds, stress feasibility, decision stability, ownership, approval, and limitations.

### 5. Evidence and verification

Writes canonical JSON, reports, hash-chained events, file digests, and deep rebuild receipts.

## Data flow

```text
case.json
  │
  ├── validate_case
  │
  ├── solve_case
  │
  ├── evaluate_decision
  │
  ├── audit_solution
  │
  ├── run_sensitivity
  │
  ├── build_decision
  │
  ├── render reports
  │
  └── write manifest and event chain
```

## Determinism

With the same case, package version, and fixed evaluation timestamp, the output is byte-identical. Run identity is derived from canonical case content, timestamp, and package version.

## Extension path

A production solver adapter should return the same minimum contract:

```text
status
solver identity and version
objective
structured decision
optimality or gap evidence
runtime metadata
```

The existing independent evaluator should remain authoritative for feasibility and objective recomputation.
