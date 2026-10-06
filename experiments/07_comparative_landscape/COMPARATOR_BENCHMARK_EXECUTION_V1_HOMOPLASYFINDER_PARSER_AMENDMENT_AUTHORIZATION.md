# HomoplasyFinder parser amendment authorization

## Trigger

The successful HomoplasyFinder smoke report contains
`MinimumNumberChangesOnTree`.

For the recurrent toy site, the report gives a value of `2`, but the current
parser discards this value and emits an empty
`reported_recurrence_count_if_available` field.

The frozen benchmark includes recurrence-count absolute error as a secondary
homoplasy endpoint.

## Authorized amendment

Only the HomoplasyFinder report parser and its focused toy-validation coverage
may change.

For retained inconsistent sites, the parser must preserve an available numeric
`MinimumNumberChangesOnTree` value in
`reported_recurrence_count_if_available`.

If the column is absent or its value is empty, the existing empty-string
representation is retained.

A present, non-empty, non-numeric count must fail rather than being silently
discarded.

Existing consistency-index filtering must remain unchanged.

No executable, source revision, JAR, recipe, run contract, output contract,
input adapter, metric, truth definition, scenario definition, other parser or
other comparator change is authorized.

The full benchmark remains unauthorized.

## Next gate

`IMPLEMENT_AND_FREEZE_HOMOPLASYFINDER_PARSER_AMENDMENT_V1`
