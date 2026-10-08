# Experiment 07 metadata-retrieval source-contract amendment implementation

Status: `FROZEN_PRE_LIVE_EXECUTION_AMENDMENT_34_IMPLEMENTATION`

## Scope

This freeze records implementation of Amendment 34, the post-freeze
metadata-retrieval provider source-contract correction.

It is layered on top of the original frozen transport implementation rather
than replacing or rewriting that historical freeze.

The original implementation freeze remains preserved at commit
`f6c0edb96d95b5e83fa74bf47db00386e5b1c136`.

The source-contract amendment preceding this implementation freeze is preserved
at commit `1f8bd90bd98de81e519f9c3c343f48a263f849f4`.

## Implemented corrections

OpenAlex authentication now uses the optional `api_key` query parameter read
from `OPENALEX_API_KEY`. The previous Bearer-header mechanism is no longer
used.

Credential-bearing OpenAlex URLs are sanitized before persistence. Allowed
same-provider redirects preserve an existing key when the provider omits it
from `Location`. A redirect that substitutes or unexpectedly introduces a
different credential fails closed.

Persisted `Location` header values are URL-sanitized so credentials cannot
enter redirect evidence through response headers.

PubMed exact PMID retrieval now includes the fixed tool identifier:

`branchsnv_validation_experiment_07`

An optional `NCBI_EMAIL` is included during offline request construction when
supplied and is redacted from persisted URLs. Before any later live execution,
a non-empty syntactically acceptable `NCBI_EMAIL` is mandatory.

No NCBI API key is introduced.

OpenCitations transport behavior is unchanged.

## Archive validation

Raw-evidence validation continues to reconstruct request identity
independently rather than trusting archived URLs.

For provider-authorized redacted operational query parameters, the validator
uses synthetic sentinel values to rebuild the request through the production
request builder, sanitizes that reconstruction, and requires exact equality
with the archived URL.

This permits only:

- `api_key=<REDACTED>` for OpenAlex; and
- `email=<REDACTED>` for PubMed.

Provider-incompatible sensitive parameters, duplicate sensitive parameters,
unredacted values, forged non-sensitive parameters, route changes, identifier
changes, host/path changes, and altered redirect request identities remain
fail-closed conditions.

PubMed `tool`, `db`, `id`, and `retmode` remain exact non-sensitive request
identity.

OpenAlex redirect-chain validation reconstructs the inherited redacted
`api_key` across allowed redirects and rejects its removal or substitution.

## Unchanged contract

The amendment implementation does not change the frozen 1,731 logical lookup
keys, provider assignments, exact identifiers, no-batching rule, retry and
redirect limits, pacing, response validation, immutable evidence, resume
semantics, completion semantics, publication identity, tool consolidation, or
scientific screening rules.

## Validation

Before this freeze, the complete current offline stack and complete historical
Experiment 07 regression stack passed.

All Amendment 34 transport and archive hostile regressions passed, including
credential persistence, redirect inheritance/substitution, PubMed contact
redaction, live-preflight ordering, independent archived-request
reconstruction, provider-incompatible query rejection, forged PubMed tool
rejection, and redirect-chain tamper rejection.

Static hostile-test coverage was additionally verified semantically from the
Python AST so adjacent source string literals could not create a false-negative
coverage audit.

The original implementation freeze remained independently auditable from its
historical commit. The frozen evidence queue remained unchanged. Scientific
screening remained empty. No production retrieval occurred.

## Live boundary

`LIVE_EXECUTION_ENABLED` remains `False`.

This implementation freeze does not authorize network execution.

Any later live-enablement change must be separate, minimal, explicitly
reviewed, and retain the Amendment 34 preflight requirements.
