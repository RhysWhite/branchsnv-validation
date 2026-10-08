# TreeTime homoplasy amendment authorization v1

A narrowly scoped amendment is authorized for the frozen TreeTime benchmark implementation.

TreeTime v0.12.1 `homoplasy` output is unsuitable as the scored recurrent-site call set because the command reports only the first `n` repeated mutation types, with a default of 10, while frozen benchmark scenarios contain up to 30 recurrent genomic sites.

The frozen TreeTime ancestral workflow uses the same joint maximum-likelihood ancestral reconstruction implementation under the frozen non-marginal settings and provides the complete reconstructed branch-change set.

The amendment may therefore:

- retain the existing frozen TreeTime ancestral command and parameters;
- derive TreeTime recurrent-site calls from normalized TreeTime ancestral branch events;
- call a position recurrent when at least two reconstructed branch changes occur at that position;
- record the number of reconstructed branch changes as the available recurrence count;
- count recurrence by genomic position regardless of the state-transition identities;
- update the TreeTime environment/output contract accordingly; and
- add focused synthetic validation for non-recurrent, parallel-like, convergent-like and reversal-like cases.

Only `environment_recipes.json`, `adapters.py` and `toy_validation.py` may change.

Benchmark execution, benchmark-dataset mutation, benchmark-truth access for implementation, metric or scenario changes, source/version changes, changes to other comparators, and production bridging remain unauthorized.

The frozen 150-scenario dataset must not be executed during implementation or validation of this amendment.

This is a one-use amendment authorization. Rerun is not authorized.

## Next gate

`IMPLEMENT_AND_FREEZE_TREETIME_HOMOPLASY_AMENDMENT_V1`
