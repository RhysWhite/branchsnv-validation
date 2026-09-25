# Experiment 07 controlled B000001 live event-entry authorization design

Status: `FROZEN_PRE_IMPLEMENTATION`

## Purpose

This design defines the safety and provenance contract for the first possible
live scientific-screening event in Experiment 07.

It does not itself authorise live event entry.

It does not contain a scientific screening decision.

It does not append an event.

Parent frozen event-appender implementation commit:

`552a0bc2620953c12683be9be6cd8cde61611864`

## Immutable batch scope

The only batch eligible for the first live authorization workflow is:

`B000001`

Frozen entity count:

`500`

First immutable entity:

`publication_component:citation:publication:doi:10.1001/archdermatol.2012.1817`

Last immutable entity:

`publication_component:citation:publication:doi:10.1007/s00239-016-9761-9`

Frozen first-entity baseline-row SHA-256:

`bb8ef2c1e0fd980a70884709d3085b8e44b5b425500d390ae943f638f1d08048`

Frozen batch-manifest ordered-ID SHA-256:

`8a98c513759bc8a8d00a53cad104411a860aebe2ccdb20a825aa636ccfb06ceb`

Independent canonical ordered-ID SHA-256:

`8a98c513759bc8a8d00a53cad104411a860aebe2ccdb20a825aa636ccfb06ceb`

Canonical full B000001 membership-row SHA-256:

`dbf86779c8d82b0185cc1c5c03194d00694b1322a2ef7235068c6d8082f3160b`

Canonical ordered B000001 baseline-row SHA-256:

`f9f1938f1fd296eb7ecc2ea9f0c87aae54a103e39d3374cd351293677698e12c`

The complete baseline queue remains frozen at:

`97575b71c4607c3dcad893d90210f9132a83d0ae2e299ac2f1aef7e94f527d58`

## Canary-first policy

The first live production mutation is intentionally restricted to a single
event.

The canary target is deterministically:

- batch: `B000001`;
- position in batch: `1`;
- screening entity: `publication_component:citation:publication:doi:10.1001/archdermatol.2012.1817`;
- baseline-row SHA-256: `bb8ef2c1e0fd980a70884709d3085b8e44b5b425500d390ae943f638f1d08048`.

The first live transaction may contain exactly one proposed event.

It may not contain a second B000001 entity.

It may not target any later batch.

This is an operational blast-radius restriction, not a scientific
classification.

The scientific outcome for the canary entity is not preselected.

After human review, the canary may validly become either:

- `record_decision`; or
- `source_escalation`.

Because the production ledger is currently at genesis, a
`superseding_record_decision` is not valid for the canary transaction.

## Canary completion gate

Successful entry of the first event does NOT automatically authorize positions
2-500.

After the canary append, work must stop and a separate completion/reconciliation
freeze must verify:

- ledger prefix preservation;
- assigned event ID;
- event contents;
- operator provenance;
- proposal provenance;
- persistent transaction checkpoint;
- post-ledger SHA;
- derived screening state;
- immutable package integrity;
- repository integrity.

Only a subsequent explicit authorization may permit additional B000001
transactions.

## Human review packet

Before live screening, a deterministic B000001 review packet must be generated
from frozen inputs.

The packet is a derived working artifact, not authoritative scientific history.

It must contain exactly 500 rows in immutable `position_in_batch` order.

Every row must contain:

- `batch_id`;
- `position_in_batch`;
- `global_active_index`;
- `baseline_row_sha256`;
- every frozen baseline queue field, in frozen queue-field order;
- blank human-entry fields:
  - `proposed_event_type`;
  - `proposed_record_decision`;
  - `proposed_exclusion_reason_code`;
  - `proposed_candidate_method_flag`;
  - `evidence_basis`;
  - `evidence_source_locator`;
  - `evidence_escalation_status`;
  - `notes`.

The frozen queue-field sequence at this design gate is:

`screening_entity_id,screening_entity_class,publication_reconciliation_key,database_dedup_keys,biotools_id,citation_provenance_ids,discovery_stages,citation_wave_provenance,title_or_software_name,title_variants,year,doi,pmid,openalex_id,omid,identity_attention_status,metadata_screenability,screening_state,record_decision,exclusion_reason_code,candidate_method_flag,evidence_escalation_status,operator,decision_batch,notes`

No scientific decision column may be pre-populated by software, a language
model, query provenance, tool name, discovery route, citation frequency,
registry presence, or prior familiarity.

The packet may organise frozen metadata for human inspection, but it must not
preclassify records.

## Canary review

For the first authorization cycle, only row 1 of the review packet may be
converted into a live proposal.

The remaining 499 rows remain scientifically undecided.

The human operator must inspect the available evidence and choose the event
fields.

### Terminal decision

For `record_decision`, the human must explicitly select:

- `retain_for_method_assessment`; or
- `exclude`.

A terminal event requires a non-empty authoritative
`evidence_source_locator`.

If excluding, exactly one frozen exclusion reason must be selected.

### Source escalation

If the evidence is insufficient for a terminal decision, the human must use:

- `event_type = source_escalation`;
- `evidence_escalation_status = awaiting_source_escalation`;
- blank terminal-decision fields.

The evidence basis must explain why the available evidence is insufficient.

## Operator identity

No operator identity is inferred automatically.

A later live-authorization artifact must explicitly freeze:

- non-empty `operator_id`;
- `operator_type` equal to either:
  - `human`; or
  - `human_with_assistance`.

Git username, operating-system username, email address, account name and other
ambient metadata must not silently become the scientific operator identity.

The operator identity must be deliberately supplied and frozen.

## Human responsibility

The human operator remains responsible for:

- inspecting the record;
- inspecting the cited evidence;
- selecting event type;
- selecting any terminal decision;
- selecting any exclusion reason;
- determining whether source escalation is required;
- checking the final one-row proposal before live append.

Computational or language-model assistance may organise or summarise evidence
only when recorded through the already-frozen
`human_with_assistance` provenance.

No automated model output may authorize or append the live event.

## Future live-authorization artifact

A separate tracked authorization artifact must exist before any production
append.

That authorization artifact must pin at least:

- authorization status;
- parent commit;
- exact frozen appender implementation SHA;
- exact event-entry-design freeze;
- exact B000001 membership hashes from this design;
- batch ID `B000001`;
- authorized position `1`;
- authorized screening entity `publication_component:citation:publication:doi:10.1001/archdermatol.2012.1817`;
- authorized baseline-row SHA `bb8ef2c1e0fd980a70884709d3085b8e44b5b425500d390ae943f638f1d08048`;
- expected production pre-ledger SHA
  `d3ff9be1efe2b1237f616f25e702275ccc608577fa0ff8b301401a72900eb55f`;
- maximum live event count `1`;
- explicit operator ID;
- explicit operator type;
- permitted initial event types;
- receipt/checkpoint contract;
- statement that positions 2-500 remain unauthorised.

The authorization artifact does not preselect the scientific decision.

## Expected pre-ledger state

The first live transaction is authorized only from the exact genesis ledger:

`d3ff9be1efe2b1237f616f25e702275ccc608577fa0ff8b301401a72900eb55f`

The frozen appender's compare-and-swap check remains mandatory.

If the production ledger SHA differs for any reason, the authorization is
stale and the transaction must fail closed.

The authorization cannot be reused after a successful canary append.

## Proposal scope

The accepted canary proposal must contain exactly one row.

It must target exactly:

- `batch_id = B000001`;
- `screening_entity_id = publication_component:citation:publication:doi:10.1001/archdermatol.2012.1817`.

Its baseline-row SHA is supplied and checked by the frozen appender.

The proposal may contain only a valid initial:

- `record_decision`; or
- `source_escalation`.

The proposal must satisfy the full frozen event-entry contract.

## Proposal dry run

Before live mutation, the exact one-row proposal must pass a read-only dry run
through the frozen appender machinery against the exact current production
ledger.

The dry run must confirm:

- expected pre-ledger SHA exact;
- one proposal row;
- B000001 exact;
- position 1 exact;
- valid event semantics;
- valid evidence provenance;
- valid operator provenance;
- expected first event ID `E000000001`;
- strict prefix-extension candidate;
- review/adjudication fields blank;
- zero mutation during dry run.

The dry-run proposal SHA-256 must be reported and preserved in the eventual
transaction receipt.

The future authorization artifact does not need to precompute the post-ledger
SHA because the appender-generated UTC transaction timestamp is part of the
accepted event bytes.

## Production invocation boundary

The already-frozen appender remains unchanged.

Its public CLI continues to refuse real production mutation.

A future separately implemented authorization guard may call the frozen library
routine with:

`allow_production=True`

only after it independently verifies all conditions in this design and the
later tracked live-authorization artifact.

The existence of the library parameter alone is not authorization.

## Persistent transaction checkpoint

Live transaction checkpoints must be stored outside the immutable eight-file
execution package.

Reserved checkpoint root:

`results/07_comparative_landscape/baseline_scientific_screening_event_receipts`

The first transaction checkpoint is reserved as:

`T000001`

The final checkpoint path is therefore:

`results/07_comparative_landscape/baseline_scientific_screening_event_receipts/T000001`

The final T000001 checkpoint must be an immutable directory containing exactly:

1. `authorization.json`
2. `proposal.tsv`
3. `receipt.json`

### authorization.json

This is an exact snapshot of the tracked live-authorization JSON used for the
transaction.

### proposal.tsv

This is the exact one-row proposal byte stream used for the accepted append.

### receipt.json

This contains the frozen appender transaction receipt plus:

- authorization commit;
- authorization JSON SHA-256;
- appender implementation SHA-256;
- proposal SHA-256;
- transaction checkpoint ID;
- checkpoint status.

## Crash-safe checkpoint sequence

The future authorization guard must use this sequence:

1. validate immutable production inputs;
2. validate tracked live authorization;
3. verify genesis pre-ledger SHA;
4. validate the exact one-row proposal;
5. perform a dry-run transaction preparation;
6. create a temporary T000001 checkpoint directory;
7. copy the exact authorization JSON into that temporary directory;
8. copy the exact proposal TSV into that temporary directory;
9. fsync staged checkpoint files;
10. recheck the production ledger SHA;
11. invoke the frozen atomic appender with
    `allow_production=True`;
12. capture the returned transaction receipt;
13. write and fsync `receipt.json` in the temporary checkpoint;
14. atomically rename the complete temporary checkpoint directory to
    `T000001`;
15. re-read and validate both the production ledger and checkpoint;
16. stop.

If the append fails before production mutation, the temporary checkpoint may be
removed.

If the production ledger append succeeds but checkpoint finalization fails:

- the accepted ledger must NOT be rolled back;
- the append must NOT be retried;
- stale-SHA protection will prevent duplicate replay;
- the temporary checkpoint must be preserved;
- the workflow must stop in a recovery-required state;
- a dedicated reconciliation gate must recover/freeze the accepted event before
  any further live event.

## Receipt contract

The T000001 receipt must preserve at least:

- `transaction_id = T000001`;
- batch ID;
- screening entity ID;
- proposal SHA-256;
- authorization commit;
- authorization JSON SHA-256;
- pre-append ledger SHA-256;
- post-append ledger SHA-256;
- pre-append event count;
- post-append event count;
- first assigned event ID;
- last assigned event ID;
- transaction timestamp UTC;
- event-type counts;
- terminal-decision counts;
- derived-state counts after append;
- strict-prefix-extension status;
- published status;
- post-publication validation status.

For the canary transaction:

- pre-event count must be 0;
- post-event count must be 1;
- first event ID must be `E000000001`;
- last event ID must be `E000000001`.

## No mutation by this design

This design does not:

- create the review packet;
- create the checkpoint root;
- create a live authorization artifact;
- create a proposal;
- call `allow_production=True`;
- append an event;
- create T000001;
- start scientific screening.

## Scientific boundary

At this design freeze:

- production event rows = 0;
- B000001 accepted decisions = 0;
- B000001 source-escalation events = 0;
- B000001 positions reviewed authoritatively = 0;
- method assessments = 0;
- role assignments = 0;
- canonical-publication decisions = 0;
- Wave 1 promotions = 0;
- B000001 live event entry remains unauthorised;
- scientific screening has not begun.

## Next gate

`IMPLEMENT_CONTROLLED_B000001_LIVE_AUTHORIZATION_GUARD_WITHOUT_EVENTS`

The next gate may implement:

- deterministic B000001 review-packet generation;
- exact canary-position validation;
- live-authorization validation;
- one-row proposal extraction/validation;
- dry-run preparation;
- checkpoint staging;
- production-authorization guard logic;
- recovery-state detection;
- hostile tests using temporary ledgers.

It must not create a live authorization artifact and must not append an event to
the real production ledger.
