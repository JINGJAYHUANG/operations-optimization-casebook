# Solver assurance

## What `exact` means here

The public solvers exhaustively enumerate bounded decisions or use an exact graph algorithm for the supplied small instance. They report zero optimality gap only when the search space or network problem has been completely solved.

## Reference methods

- Linear product mix: enumerate feasible vertices.
- Transportation: min-cost flow through successive shortest paths.
- Assignment: enumerate complete permutations.
- Facility location: enumerate facility subsets and feasible assignments.
- Workforce scheduling: enumerate bounded integer shift counts.
- Newsvendor: enumerate every feasible integer quantity.
- Project crashing: enumerate every activity option combination and recompute CPM.
- Vehicle routing: enumerate vehicle allocations and route orders.
- Robust choice: enumerate alternatives and scenario criteria.
- Capital budgeting: enumerate all binary portfolios.

## Independent checks

Every returned decision is evaluated by a separate function that checks constraints and recomputes the objective. A changed objective, infeasible decision, or nonzero gap fails the audit.

## Production adapters

For large models, retain:

- solver name and version;
- model and data hashes;
- termination status;
- primal feasibility;
- objective recomputation;
- optimality gap or bound;
- time limit and node count;
- warm-start provenance;
- deterministic settings where possible;
- independent spot checks or reference subproblems.

Do not label `time_limit`, `feasible`, or `heuristic` as `optimal`.
