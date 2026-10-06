# HomoplasyFinder CLI amendment authorization

## Trigger

The frozen source revision contains a runnable repository JAR.

Its help output requires the command-line options `--fasta` and `--tree`.
The frozen execution recipe instead used `-fasta` and `-tree`.

The JAR rejected the single-dash argument but returned exit status zero.
Therefore a successful smoke test must require the expected output report in
addition to process completion.

## Authorized amendment

Only `methods.HomoplasyFinder.run_contract` in
`environment_recipes.json` may change:

- `-fasta` becomes `--fasta`
- `-tree` becomes `--tree`

No source, JAR, dependency, build, input, parser, truth, metric, scenario or
other comparator recipe change is authorized.

The full benchmark remains unauthorized.

## Next gate

`IMPLEMENT_AND_FREEZE_HOMOPLASYFINDER_CLI_AMENDMENT_V1`
