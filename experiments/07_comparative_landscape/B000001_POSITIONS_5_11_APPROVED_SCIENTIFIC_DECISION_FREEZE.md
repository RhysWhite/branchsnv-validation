# Experiment 07 B000001 positions 5 and 11 approved scientific-decision freeze

Status: `HUMAN_APPROVED_PRE_LIVE_FREEZE`

Parent authoritative-evidence commit:

`744fac515fd9f193f5ad960644d9ca2b3f5cdc84`

Authoritative-evidence freeze SHA-256:

`11bf8db6a93d47a84b965d322939cfbe1d9a7c1e07eec5d80ddc2b6a31923438`

## Human approval

The immediately preceding scientific adjudication proposed exactly:

- position 5:
  - `exclude`
  - `duplicate_record_same_method_no_distinct_capability`
- position 11:
  - `exclude`
  - `application_only_no_reusable_method`
- position 10:
  - remain unresolved and untouched

The human operator responded:

`okay do it`

This freeze records that response as approval of exactly those two proposed
terminal decisions and **not** as approval of a position-10 decision.

## Position 5

Current event before this freeze:

`E000000015`

Approved future superseding decision:

- `exclude`
- exclusion reason:
  `duplicate_record_same_method_no_distinct_capability`
- candidate-method flag:
  `false`

The adjudication is an explicit human scientific inference from the frozen
evidence: the record documents analytical protocols based on PAML, while PAML
is already the frozen W0A07 method, and the reviewed record is treated as not
adding a distinct relevant reusable capability.

## Position 11

Current event before this freeze:

`E000000011`

Approved future superseding decision:

- `exclude`
- exclusion reason:
  `application_only_no_reusable_method`
- candidate-method flag:
  `false`

The adjudication is an explicit human scientific inference from the frozen
publisher and institutional evidence describing the article's biological
selection/evolution scope without establishing a distinct reusable analytical
software or method.

## Position 10

Current event:

`E000000010`

Position 10 remains:

`awaiting_source_escalation`

No terminal decision is approved for position 10.

## Authority boundary

This freeze:

- records approved scientific decisions;
- creates a deterministic future proposal;
- does **not** append events;
- does **not** authorize live production mutation;
- does **not** modify the event ledger.

Production ledger SHA-256 remains:

`a1303b93bd70c2106582f2a5a8749fcdfd649c18ff31fc6c3712cce8dc2f54fe`

Production event count remains:

`19`

## Decision-packet identities

Proposal SHA-256:

`eb56ba69839d9e5507f05dec8898e382b1ae1d2059ff55607f865b8da231c068`

Decision-summary SHA-256:

`0cc225a482b2a04bba3bef58efb9e4ef898d1de9eaf2b34f64242b1741b3fb29`

Decision-packet checksum SHA-256:

`59ed33e76180eaa7f47d16756ff7dff9f4adcf8cbfe925e35997e21a6c3e1a67`

## Next gate

`CONTROLLED_LIVE_APPEND_POSITIONS_5_11`
