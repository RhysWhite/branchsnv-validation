# Citation Wave 0 production Attempt 05

Status: FAILED_DURING_SOURCE_RECONCILIATION

Attempt 05 was the first production execution using the frozen deterministic
OpenCitations OCI-partition implementation.

The partition transport itself completed for W0A07 (PAML) forward citations.

All ten root terminal-digit OCI partitions were retrieved successfully.

Every returned OCI was syntactically valid, belonged to its recorded root
partition, and was unique across the ten leaves.

No recursive partition subdivision was required.

## Failure

The independently retrieved OpenCitations citation count was:

12,846

The complete ten-leaf partition union contained:

12,845 unique OCI rows

Difference:

1 citation relationship

The retriever therefore failed closed before accepting the operation.

## Current interpretation

The cause is deliberately unresolved at this stage.

The observed mismatch could potentially reflect, among other possibilities:

- source-state change between the independent count request and the sequence
  of filtered partition requests;
- a difference between count-endpoint and filtered-data semantics; or
- a citation relationship included in the count whose OCI representation does
  not belong to the assumed numeric OCI partition universe.

These possibilities are hypotheses only and have not yet been adjudicated.

No partition rule or scientific search rule is changed on the basis of this
failure.

## Preservation

All raw responses successfully written during Attempt 05 are preserved
byte-for-byte in a deterministic archive.

The ten W0A07 forward root leaves have a separate forensic inventory.

The W0A07 forward independent count response is also compared, without network
access, against the preserved count responses from Attempts 03 and 04.

No citation record from Attempt 05 has been screened, classified, reconciled
into the literature-search universe, or promoted as a later-wave anchor.
