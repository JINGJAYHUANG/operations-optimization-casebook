# Operations Optimization Casebook

[![CI](https://github.com/JINGJAYHUANG/operations-optimization-casebook/actions/workflows/ci.yml/badge.svg)](https://github.com/JINGJAYHUANG/operations-optimization-casebook/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/JINGJAYHUANG/operations-optimization-casebook)](https://github.com/JINGJAYHUANG/operations-optimization-casebook/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%E2%80%933.13-blue.svg)](pyproject.toml)

An auditable operations-research casebook that separates **mathematical optimality**, **decision robustness**, and **implementation authorization**.

The public release contains ten deterministic synthetic cases, ten exact small-instance reference solvers, baseline comparisons, stress tests, implementation gates, hash-chained evidence, deep rebuild verification, and a 365-test quality gate.

**Status:** `v0.1.0` · public synthetic casebook validated · not a production execution system

[中文说明](docs/README.zh-CN.md) · [Architecture](docs/architecture.md) · [Model contract](docs/model-contract.md) · [Solver assurance](docs/solver-assurance.md) · [Implementation governance](docs/implementation-governance.md)

## The decision sequence

Optimization projects often begin with a solver and end with a number. This casebook uses a stricter order:

```text
Decision question
→ model contract
→ input validation
→ exact reference solution
→ independent feasibility and objective recomputation
→ baseline comparison
→ sensitivity and stress tests
→ operational conditions and ownership
→ recommendation, conditional approval, or hold
→ tamper-evident evidence bundle
```

A low objective value is not enough. The result must also answer:

- Is the decision feasible when recomputed independently?
- Is the objective internally consistent?
- Is optimality exact for the declared instance?
- Is the result better than the current baseline?
- Does the decision survive material input changes?
- Which assumptions are outside the model?
- Who owns implementation and monitoring?
- What change should trigger a re-solve or rollback?

## Reference models

| Case | Model family | Exact reference method | Decision lesson |
|---|---|---|---|
| Product mix | Small continuous linear program | Vertex enumeration | Binding capacity and contribution trade-offs |
| Transportation | Balanced min-cost flow | Successive shortest path | Lane cost, supply, demand, and forbidden arcs |
| Assignment | One-to-one matching | Permutation enumeration | Certification constraints and second-best margin |
| Facility location | Fixed-charge location-allocation | Facility and assignment enumeration | Fixed cost versus service distance and capacity |
| Workforce scheduling | Integer covering | Complete bounded enumeration | Coverage, overstaffing, and wage cost |
| Newsvendor | Single-period stochastic inventory | Discrete expectation enumeration | Expected profit, fill rate, and stockout risk |
| Project crashing | Precedence network with crash options | Complete option enumeration + CPM | Deadline penalty versus direct crash cost |
| Vehicle routing | Small capacitated routing | Allocation and route enumeration | Route cost, capacity, and operational caveats |
| Robust choice | Scenario decision analysis | Exact candidate enumeration | Expected cost, worst case, and minimax regret |
| Capital budgeting | Binary portfolio selection | Exact subset enumeration | Cash, risk, dependency, and exclusivity constraints |

The reference algorithms are deliberately transparent and dependency-free. They are suitable for small teaching, audit, and regression instances. Larger real models should use an industrial solver behind an adapter while preserving the same evidence contract.

## Quick start

```bash
python -m pip install -e .

opcase validate --kind suite examples/synthetic-suite/casebook.json

opcase run-suite \
  --manifest examples/synthetic-suite/casebook.json \
  --output run-reference \
  --fixed-time 2026-09-02T00:00:00Z

opcase verify --run-dir run-reference --deep
```

Expected portfolio result:

```text
PASS suite=public-synthetic-operations-optimization-suite
cases=10/10 recommended=5 conditional=5 hold=0
```

Inspect the decisions:

```bash
opcase inspect --run-dir run-reference
```

Compare a candidate model or policy version:

```bash
opcase compare \
  --baseline examples/synthetic-suite/expected \
  --candidate run-reference \
  --fail-on-regression
```

## Model contract

Every case is a versioned JSON document with:

```text
case identity
model family
objective sense
business decision context
data and constraints
baseline decision
stress tests
implementation policy
monitoring KPIs
rollback trigger
known limitations
```

A solver result is independently recomputed from its decision variables. The audit does not trust the solver's objective or feasibility claim without checking them.

## Decision states

### `recommended`

The exact solution, audit, baseline gate, stress policy, owner, and implementation rules pass without an outstanding approval condition.

### `conditional`

The mathematical result is valid, but implementation still requires human approval, shows material stress sensitivity, exceeds a preference threshold, or depends on an explicitly unresolved operating condition.

### `hold`

A hard gate fails—for example infeasibility, objective mismatch, missing owner, service threshold failure, unacceptable regret, failed stress feasibility, or a non-exact solver certificate.

Scoring or objective improvement cannot override a hold.

## Evidence bundle

Each case run produces:

```text
case-run/
├── inputs/case.json
├── solution.json
├── audit.json
├── sensitivity.json
├── decision.json
├── summary.json
├── report.md
├── report.html
├── events.jsonl
└── run-manifest.json
```

The suite adds:

```text
suite-run/
├── inputs/suite.json
├── cases/<case-id>/...
├── decision-portfolio.csv
├── summary.json
├── report.md
├── report.html
└── suite-manifest.json
```

`opcase verify --deep` checks stored hashes and event chains, then rebuilds every case from the input snapshots and compares the regenerated evidence byte for byte.

## Stress testing

Stress tests use explicit dotted-path patches, for example:

```json
{
  "name": "labor-capacity-minus-12",
  "patch": {
    "data.capacities.labor": 96
  }
}
```

The output records:

- whether the stressed model remains valid and feasible;
- the stressed objective;
- degradation from the base objective;
- whether the recommended decision changes;
- the decision-stability ratio;
- whether the case remains inside policy thresholds.

Stress testing does not assign probabilities unless the model explicitly contains them. It is a structured robustness probe, not a substitute for a complete uncertainty model.

## Public synthetic suite

The included data are fictional and do not describe a real factory, logistics network, workforce, customer, vehicle fleet, investment committee, or operating plan.

The reference portfolio contains:

```text
10 case families
30 named stress tests
10 feasible baseline decisions
5 recommended decisions
5 conditional decisions
0 holds in the positive suite
3 negative-control cases
106 committed reference artifacts
```

Negative controls demonstrate that the system rejects:

- unbalanced transportation supply and demand;
- cyclic project precedence;
- profitable inventory decisions that fail a service gate;
- missing implementation ownership;
- changed solver objectives;
- fake optimality gaps;
- invalid stress patches;
- non-optimal solver status.

## CLI

```text
opcase validate      Validate one case or a suite manifest
opcase solve         Solve, audit, stress, and report one case
opcase run-suite     Run the complete casebook portfolio
opcase verify        Verify hashes and optionally deep-rebuild
opcase inspect       Inspect a completed case or suite
opcase compare       Compare baseline and candidate runs
opcase list-types    List supported model families
opcase init          Preview or create a starter case
```

Starter creation is preview-first:

```bash
opcase init --target ./my-optimization-case
opcase init --target ./my-optimization-case --apply
```

## Repository map

```text
src/opcase/                    Solvers, validation, audit, stress, reports, CLI
schemas/                       Case, suite, solution, decision, event, manifest contracts
examples/synthetic-suite/      Ten public synthetic cases and committed reference outputs
examples/negative-controls/    Deliberate invalid, infeasible, and policy-hold examples
tests/                         Algorithm, audit, stress, tamper, CLI, and packaging tests
scripts/                       Release gate, public audit, link audit, schema and example checks
docs/                          Architecture, model governance, assurance, and case authoring
.github/workflows/             Pinned Python CI and immutable release workflow
```

## Maturity and limits

`v0.1.0` verifies the public synthetic model contracts, exact small-instance solvers, independent recomputation, policy gates, deterministic artifacts, and packaging. It does **not** prove that:

- a real operating problem has been modeled completely;
- input data are accurate, current, or unbiased;
- an industrial solver has returned a globally optimal answer;
- a route is executable under traffic, time windows, or legal constraints;
- a workforce plan respects every labor rule or skill requirement;
- a capital project value estimate is economically correct;
- a recommendation has been approved for execution.

Use [solver assurance](docs/solver-assurance.md), [sensitivity and robustness](docs/sensitivity-and-robustness.md), and [implementation governance](docs/implementation-governance.md) before adapting the framework to real decisions.
