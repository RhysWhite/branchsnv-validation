# Experiment 07 OpenCitations multiplicity implementation

Status: `FROZEN_PRE_PRODUCTION_ADJUDICATION`

## Scope

This implementation realizes Amendment 36 without rewriting historical
provider evidence and without requiring a new provider request for the seven
eligible historical OpenCitations response-integrity failures.

## Classification rule

For exact OpenCitations Meta DOI/OMID lookups, a multi-record HTTP-200 JSON
response is accepted as a provider-identity observation only when:

1. every element is an object;
2. every record has a non-empty `id`;
3. the complete trimmed `id` bundle is identical across all records;
4. every `id` bundle contains the exact requested identifier token; and
5. canonical JSON becomes identical after excluding only `venue` and
   `pub_date`.

No first-row selection, majority rule, fuzzy matching or descriptive-field
selection is permitted.

## Historical failure adjudication

A previously materialised `response_integrity_failure` may be adjudicated only
when its final historical attempt recorded:

`OpenCitations exact lookup returned N records`

and the preserved HTTP-200 response independently satisfies the Amendment 36
classifier.

The historical:

- `failure.json`;
- request record;
- attempt record;
- response metadata; and
- response body

remain immutable.

A deterministic `adjudication.json` is added alongside `failure.json`.

It records:

- the Amendment 36 rule identity;
- the Amendment 36 freeze commit;
- historical and effective terminal states;
- common provider identifier;
- provider-record count;
- varying fields;
- source attempt number;
- source failure SHA-256;
- source attempt-record SHA-256;
- source response-metadata SHA-256; and
- source response-body SHA-256.

## Fail-closed verification

`adjudication.json` is not trusted merely because it exists.

Its complete contents are independently reconstructed from immutable archived
evidence during validation.

A forged adjudication therefore fails semantic validation even if an attacker
regenerates the outer archive checksum manifest.

An adjudication without its historical `failure.json` is invalid.

A lookup may not contain both:

- `terminal.json` and `failure.json`; or
- `terminal.json` and `adjudication.json`.

No synthetic successful attempt is created.

No historical failed attempt is rewritten.

No `terminal.json` is manufactured for an adjudicated historical failure.

## Effective state

A valid Amendment 36 adjudication contributes effective lookup state
`success`.

The historical attempts ledger continues to record the original
`response_integrity_failure`.

The effective `lookup_status.tsv` state is derived from the independently
validated adjudication.

Both remain reproducible from raw archive evidence.

## Network boundary

Eligible historical failures are adjudicated before any new provider request
can occur.

Synthetic tests demonstrate zero executor calls during both:

- initial historical-failure adjudication; and
- reuse of an existing adjudication.

Non-eligible historical failures retain their existing terminal-failure
semantics.

## Validation evidence

Before this implementation freeze:

- focused Amendment 36 transport/archive tests passed;
- the complete current Experiment 07 offline stack passed;
- historical Experiment 07 regression tests passed;
- re-checksummed forged adjudication evidence failed semantic validation;
- historical failure and attempt evidence remained byte-identical;
- the real production archive remained checksum-valid; and
- no production adjudication or provider request occurred.

## Production state at implementation freeze

The production archive remains `INCOMPLETE`:

- 1,691 `success`;
- 33 `not_found`;
- 7 historical `response_integrity_failure`;
- 0 `adjudication.json` records.

The frozen logical lookup count remains 1,731.

## Scientific boundary

This implementation does not:

- resolve conflicting venue values;
- resolve conflicting publication dates;
- select descriptive metadata;
- perform title reconciliation;
- merge publication components;
- consolidate software tools; or
- perform scientific screening.

## Next gate

Apply the frozen Amendment 36 implementation to the existing production
archive through the authorized archive runner.

The production run must then demonstrate:

- exactly seven adjudications;
- zero new provider attempts;
- all 1,731 logical lookups in accepted terminal state;
- a `COMPLETE` manifest;
- exact checksum coverage;
- semantic reconstruction of all derived ledgers;
- preservation of the historical failed attempts; and
- scientific screening remaining zero.
