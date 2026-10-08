# HomoplasyFinder CLI amendment v1

The HomoplasyFinder execution recipe now uses the command-line flags accepted
by the repository JAR:

- `--fasta`
- `--tree`

No source revision, JAR, build procedure, dependency, input adapter, output
contract, parser, truth definition, metric, scenario definition or other
comparator recipe changed.

A subsequent smoke rerun must both execute and produce at least one
`consistencyIndexReport_*.txt` file. Exit status alone is insufficient because
the JAR returned zero when the earlier command-line flags were rejected.

The full benchmark remains unauthorized.

## Next gate

`RERUN_HOMOPLASYFINDER_AUTHORIZED_TOY_SMOKE_WITH_CORRECTED_CLI_V1`
