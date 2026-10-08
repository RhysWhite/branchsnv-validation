# HomoplasyFinder parser amendment v1

The HomoplasyFinder report parser now preserves
`MinimumNumberChangesOnTree` in
`reported_recurrence_count_if_available` for retained inconsistent sites.

Integer-valued numeric counts are normalized to integer strings. If the
column is absent or the value is empty, the existing empty-string
representation is retained. Present non-numeric or non-integer counts fail.

Existing consistency-index filtering is unchanged.

No HomoplasyFinder executable, source revision, JAR, recipe, run contract,
output contract, input adapter, benchmark metric, truth definition, scenario
definition, other parser or other comparator changed.

The full benchmark remains unauthorized.

## Next gate

`CLOSE_HOMOPLASYFINDER_SMOKE_AND_PROCEED_TO_PAML`
