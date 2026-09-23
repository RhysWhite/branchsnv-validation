# OpenCitations dual-axis snapshot reconciliation implementation

Status: FROZEN_PRE_PRODUCTION_EXECUTION

This implementation realizes the production design frozen in
`OPENCITATIONS_SNAPSHOT_RECONCILIATION_SPEC.md`.

## Production behavior

For every OpenCitations source-direction operation, the production path now
uses snapshot reconciliation.

For a positive pre-count, one snapshot attempt performs:

1. independent pre-count;
2. complete OCI-partition retrieval;
3. independent raw-string `creation`-partition retrieval;
4. independent post-count;
5. within-axis integrity validation;
6. exact cross-axis reconciliation.

Acceptance requires:

- identical pre- and post-counts;
- OCI-axis row count equal to that stable count;
- creation-axis row count equal to that stable count;
- unique complete rows within each axis;
- exact equality of canonical complete-row sets;
- exact equality of independently reconstructed OCI sets; and
- all transport and partition-integrity checks passing.

The OCI-axis rows remain the sole canonical production records.

The creation axis is retained only as an independent completeness witness.

## Zero-count behavior

A zero pre-count performs no partition-data requests.

A second independent count is still required.

Only a stable `0 -> 0` bracket is accepted.

## Snapshot retries

Up to three fresh whole-snapshot attempts are allowed for retryable transport
or source-reconciliation failures.

No successful leaf, row or count response from a failed snapshot attempt is
reused in a later attempt.

Failed attempts remain preserved under their own raw snapshot-attempt
directory and in the snapshot-attempt ledger.

## Non-retryable failures

Malformed rows, malformed OCIs, duplicate complete rows, duplicate OCIs,
partition-membership violations, missing/non-string creation values and
integrity/invariant failures fail closed.

## Production outputs

The existing canonical OCI leaf ledger is retained:

`opencitations_partition_leaves.tsv`

Two new production audit ledgers are emitted:

`opencitations_creation_partition_leaves.tsv`

`opencitations_snapshot_attempts.tsv`

The retrieval manifest is schema version 2 and explicitly records:

- dual-axis reconciliation;
- OCI as the canonical production axis;
- OCI and creation partition leaf counts;
- snapshot-attempt count;
- both recursion ceilings; and
- the maximum whole-snapshot attempt count.

All three ledgers are included in the output checksum manifest.

## Backward compatibility

The previously tested single-axis `retrieve_opencitations()` helper is retained
for regression testing.

The executable production `main()` path uses
`retrieve_opencitations_dual_axis()`.

## Offline validation

The pre-existing retrieval and OCI-partition test suites continue to pass
unchanged.

A dedicated snapshot-reconciliation suite additionally verifies:

- stable positive dual-axis acceptance;
- count bracketing;
- exact complete-row equality independent of result order;
- exact OCI-set equality;
- OCI-axis production provenance;
- preservation of empty creation values;
- rejection when OCI sets match but complete rows differ;
- three-attempt whole-snapshot exhaustion;
- recovery from stable count/data mismatch;
- isolation of failed snapshot rows from accepted output;
- recovery from pre/post source-count drift;
- recovery from retryable transport failure;
- stable zero-count bracketing with no data requests;
- non-retryable handling of missing creation;
- deterministic creation-partition `IncompleteRead` subdivision;
- absence of failed parent response bodies;
- creation-partition ledger output;
- snapshot-attempt ledger output;
- manifest schema version 2;
- checksum coverage of the new ledgers;
- credential non-disclosure; and
- zero network access during testing.

No scientific search, screening, role-classification, Wave-promotion or
citation-saturation rule is changed.
