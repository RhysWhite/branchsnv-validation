# Experiment 07 B000001 post-canary continuation design

Status: `FROZEN_PRE_IMPLEMENTATION`

## Purpose

This design defines the first controlled continuation after successful
completion and reconciliation of T000001.

Parent T000001 completion commit:

`5770934347af9d604c22c8c199cbb6e9c1db58ca`

The design does not itself authorize a live event, edit the human-review
packet, or mutate the production ledger.

## Current frozen state

T000001 produced exactly one accepted production event:

`E000000001`

Current production event count:

`1`

Current ledger SHA-256:

`33b49116d126f45cb54354b121eb69eb0abb212738794fef524a667ee0b2f2ba`

Current derived state:

- ready: 94,621
- complete: 1
- awaiting source escalation: 0
- blocked metadata: 484

Position 1 is complete.

Positions 2-500 remain undecided and unauthorized.

## Continuation strategy

The first post-canary continuation uses a bounded ten-record validation
tranche.

Transaction:

`T000002`

Target:

B000001 positions 2-11 inclusive.

Exactly ten events are required.

Partial execution is not permitted.

This tranche is intentionally bounded so that multi-event proposal generation,
human evidence review, deterministic ordering, append semantics, checkpoint
creation, replay protection and reconciliation can all be validated before any
larger tranche is considered.

Successful T000002 completion does not automatically authorize a larger
tranche.

## Exact T000002 target

Ordered target-ID SHA-256:

`ab135632dc02db9435ccec5ce5301ef9847770c1ee61a9d91de9103a9ca9ea65`

Canonical membership-row SHA-256:

`c35fb0b42daf9c7bec8ce70f7170452b6f19800d0bddcfd6e83ccdccb432ba09`

Canonical baseline-row SHA-256:

`c02e9eb5d12fd8433c363bc24dccf1f3d965fa9c4fd64edb48a74576b98bdbd7`

Canonical combined target-identity SHA-256:

`2f8188c05e3e804133604cbe9d2f1325657aa30f9aa87dcbe5c75572908eb671`

Target entities:

- position 2: `publication_component:citation:publication:doi:10.1001/jamanetworkopen.2018.7665`; row SHA `95063f377c539af86ca0a0d5b2b5d06f4e223bc02a4ae96aaa3c91a77ae21d42`; title `Risk Assessment After a Severe Hospital-Acquired Infection Associated With Carbapenemase-Producing Pseudomonas aeruginosa`
- position 3: `publication_component:citation:publication:doi:10.1001/jamanetworkopen.2020.24191`; row SHA `976cf5bbe47a5fe7f8d80ec10c8e93f8b0999f926b45a1324ad66ab145d40781`; title `Analysis of Genomic Characteristics and Transmission Routes of Patients With Confirmed SARS-CoV-2 in Southern California During the Early Stage of the US COVID-19 Pandemic`
- position 4: `publication_component:citation:publication:doi:10.1001/jamanetworkopen.2026.17898`; row SHA `18f92cc654af581b1bea5dff5dbe7c0580879707e0832e217242799f786f9d3b`; title `Hospital Environment–Associated Sources of Mycobacterium abscessus Infection in Transplant Recipients`
- position 5: `publication_component:citation:publication:doi:10.1002/0471142727.mb1901s101`; row SHA `e8ad05c3b5a50b298d65cd6de86217c4ba0836e10d7707d57ca8e1d01d42c837`; title `Detecting the Signatures of Adaptive Evolution in Protein‐Coding Genes`
- position 6: `publication_component:citation:publication:doi:10.1002/1873-3468.13356`; row SHA `ff97b6d665ffaf371fa83622d8ce3cf9409ac866a1d6e8fc403c4869c788fcf8`; title `Molecular evolution of proteins mediating mitochondrial fission–fusion dynamics`
- position 7: `publication_component:citation:publication:doi:10.1002/2211-5463.12843`; row SHA `83380ff654ecbd316bf71ada12ebafdd32e963f7c79da7c44f52d4f8aee2ead9`; title `Origin and adaptation of green‐sensitive (RH2) pigments in vertebrates`
- position 8: `publication_component:citation:publication:doi:10.1002/2211-5463.13555`; row SHA `c396dd435735bf5a5935c3ea4a053ea145b5e0ca451c657e30e8cf71635c0c76`; title `Potentially reduced fusogenicity of syncytin‐2 in New World monkeys`
- position 9: `publication_component:citation:publication:doi:10.1002/2211-5463.13728`; row SHA `0c2b6bc07cd3bd69ac2fb111bc5be0d5279f4be49a525ea66aea119c9cee4269`; title `Insights into the identification and evolutionary conservation of key genes in the transcriptional circuits of meiosis initiation and commitment in budding yeast`
- position 10: `publication_component:citation:publication:doi:10.1002/9780470015902.a0020859`; row SHA `af854acdd8f52ea2b34950e8ed56de90e87e5b78a34812cb8da98fdf8e49ec74`; title `Selection against Amino Acid Replacements in Human Proteins`
- position 11: `publication_component:citation:publication:doi:10.1002/9780470015902.a0020859.pub2`; row SHA `3bc43d2f7176233cfa1e88af0134ab4352ffc2dc3877ba50d3abd5c0a4269709`; title `Selection against Amino Acid Replacements in Human Proteins`

## Event identity

Current production event count:

`1`

Expected T000002 event IDs:

`E000000002` through `E000000011`

Expected post-transaction event count if successful:

`11`

All ten are initial events for previously event-free entities.

Superseding events are prohibited in T000002.

## Review-packet boundary

Working packet:

`results/07_comparative_landscape/baseline_scientific_screening_review_work/B000001/review_packet.tsv`

Pre-T000002 SHA-256:

`bbaa8eeed4b60fa310434819dcf67ecf540d25112634818690bdb37cf5e0e286`

Pre-T000002 bytes:

`306073`

Position 1 must remain locked to the T000001-reviewed state.

After a separate tracked T000002 authorization is frozen, only positions 2-11
may receive human-entered `proposed_` values.

Positions 12-500 must remain blank.

No software or model preclassification is permitted.

## Scientific review contract

Every one of positions 2-11 requires explicit human review.

Permitted initial outcomes are:

1. terminal `record_decision`;
2. `source_escalation`.

Terminal decisions are either:

- `exclude`; or
- `retain_for_method_assessment`.

For `exclude`:

- `candidate_method_flag = false`;
- exactly one frozen exclusion reason is required.

For `retain_for_method_assessment`:

- `candidate_method_flag = true`;
- exclusion reason must be blank.

Frozen exclusion reasons remain exactly:

- `application_only_no_reusable_method`
- `unrelated_variant_or_data_type`
- `duplicate_record_same_method_no_distinct_capability`
- `unsupported_by_primary_or_stable_authoritative_source`

A terminal decision requires a non-empty evidence basis and source locator.

If available metadata is insufficient to support a terminal decision,
uncertainty is retained and the record enters `source_escalation` with
`awaiting_source_escalation`.

Title-only or model-only preclassification is prohibited.

## Human provenance

A separate authorization must freeze:

- explicit non-empty `operator_id`;
- `operator_type` of either `human` or `human_with_assistance`.

Operator identity must not be inferred from OS, Git, environment variables or
account metadata.

The human remains responsible for every scientific disposition.

## Authorization boundary

This design creates no authorization.

A future tracked one-use T000002 authorization must pin:

- this frozen continuation design;
- exact positions 2-11;
- exact ten-record target identity;
- current post-T000001 ledger SHA;
- expected pre-event count of 1;
- exactly ten permitted live events;
- expected event IDs E000000002-E000000011;
- explicit human operator provenance;
- positions 12-500 unauthorized;
- no preselected scientific outcomes;
- the T000002 checkpoint contract.

No intervening tracked commit may occur between the future authorization commit
and T000002 execution.

## T000002 checkpoint

Final checkpoint directory:

`results/07_comparative_landscape/baseline_scientific_screening_event_receipts/T000002`

Exact final files:

1. `authorization.json`
2. `proposal.tsv`
3. `receipt.json`

If the ledger append succeeds but checkpoint finalization fails:

- do not roll back the ledger;
- do not retry the transaction;
- preserve staging evidence;
- enter recovery-required state;
- reconcile before any further event authorization.

## Mandatory post-T000002 gate

After successful T000002 execution, no further authorization may be issued
until a separate completion/reconciliation freeze verifies:

- all ten ledger events;
- exact proposal-to-ledger correspondence;
- exact receipt transition;
- exact checkpoint;
- replay rejection;
- review-packet correspondence;
- positions 12-500 unchanged.

## Scientific boundary at this design freeze

- production events: 1
- completed B000001 positions: 1
- positions 2-500 decided: no
- positions 2-500 authorized: no
- retained candidate-method decisions: 0
- source-escalation events: 0
- method assessments: 0
- role assignments: 0
- canonical-publication decisions: 0
- Wave 1 promotions: 0

Scientific screening has begun, but only the T000001 canary is complete.

## Next gate

`IMPLEMENT_CONTROLLED_B000001_T000002_CONTINUATION_GUARD_WITHOUT_EVENTS`
