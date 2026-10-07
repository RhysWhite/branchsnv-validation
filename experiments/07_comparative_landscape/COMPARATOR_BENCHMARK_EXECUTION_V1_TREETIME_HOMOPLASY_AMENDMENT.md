# TreeTime homoplasy amendment v1

TreeTime recurrent-site scoring is now derived from normalized branch changes
produced by the frozen TreeTime ancestral reconstruction workflow.

A genomic position is reported as recurrent when at least two reconstructed
branch changes occur at that position. The number of reconstructed branch
changes is retained in `reported_recurrence_count_if_available`.

Recurrence is grouped by genomic position and does not require repeated
changes to have identical ancestral and derived states. This therefore
supports repeated same-state changes, convergent changes and reversals under
the frozen site-level benchmark endpoint.

The TreeTime `homoplasy` command and its top-N stdout are not used as the
scored recurrent-site call set.

The TreeTime executable, source pin and ancestral reconstruction parameters
are unchanged. No benchmark truth, scenario definition, metric definition,
comparator version or other comparator implementation changed.

Focused synthetic validation passes without executing any of the frozen
150 benchmark scenarios.

The full benchmark remains unauthorized.

## Next gate

`AUTHORIZE_COMPARATOR_BENCHMARK_RUNNER_IMPLEMENTATION_V1`
