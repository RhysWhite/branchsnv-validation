# Citation Wave 0 production Attempt 01

Status: FAILED_PRE_REQUEST

The first production invocation of the frozen Wave 0 citation retriever exited
before creating the production output directory and before making any citation
API request.

## Failure

The invoking shell could read a populated `OPENALEX_API_KEY` shell variable,
but the Python child process reported:

`ERROR | OPENALEX_API_KEY is required`

A post-failure environment audit, performed without printing the credential,
confirmed that the variable was populated in the shell but absent from
`os.environ`.

The cause is therefore consistent with the variable having been assigned in
the interactive shell without being exported to child processes.

## Scientific impact

None.

The retriever validates `OPENALEX_API_KEY` before output-directory creation
and before citation retrieval. Therefore:

- zero citation API requests were made by the production retriever;
- zero citation records were observed;
- no partial citation corpus exists;
- no search, screening, anchor, or stopping-rule decision can have been
  influenced by citation results.

The frozen retriever itself is unchanged.

A subsequent production attempt may occur only after this failed attempt is
frozen and the credential is exported to the child-process environment.
