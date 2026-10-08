# Pre-review triage future text Wave B implementation v1

Status: `FROZEN_PRE_AUTHORIZATION`

## Executable implementation

The Future Wave B executable layer is frozen from implementation commit:

`c410749fec34c726a5a6ce8a76d0ad84df18f2db`

The frozen implementation contains:

- Future Wave B authorization guard;
- Future Wave B transport-evidence adapter;
- Future Wave B runner core;
- Future Wave B live entrypoint;
- focused execution tests;
- live hostile tests.

## Frozen request population

Exactly 40 OpenAlex requests are permitted:

- 31 `exact_work_id -> work_by_openalex_id`;
- 8 `exact_doi -> work_by_doi`;
- 1 `exact_pmid -> work_by_pmid`.

No search/list endpoint, Crossref route, PubMed provider route, or ad-hoc probe
is permitted.

## Test boundary

The committed clean implementation passes 43 Future Wave B tests:

- 13 focused implementation tests;
- 30 live hostile tests.

The suite covers exact-PMID success identity, missing/wrong PMID fail-closed
behaviour, exact-PMID verified-not-found checkpointing, partial-archive replay
prevention, durable same-execution-ID recovery without reissue, different-ID
rejection, runtime invariant rechecks, and cross-process execution locking.

The real default network executor is blocked during hostile testing.

## Authorization boundary

This implementation freeze does not create authorization.

It does not authorize network access.

The earlier Future Wave A authorization cannot be reused.

A new explicit one-use human Future Wave B authorization is required and must
bind the exact clean git HEAD containing this freeze artifact.

The authorization must remain untracked.

## Preservation boundary

The low-level transport, transport-policy implementation, normalizer,
historical development Wave B implementation, Future Wave A implementation and
Future Wave A archives remain unchanged.

No reconciliation, future scoring, model fitting, threshold selection,
scientific screening, or blind-validation scientific inspection is performed
by this freeze.

## Next gate

`OBTAIN_SEPARATE_EXPLICIT_ONE_USE_HUMAN_FUTURE_WAVE_B_NETWORK_AUTHORIZATION_BOUND_TO_THE_RESULTING_IMPLEMENTATION_FREEZE_HEAD`
