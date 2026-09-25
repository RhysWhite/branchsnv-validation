# ASR000001 production completion and continuation design

Status: `ASR000001_COMPLETE_CONTINUATION_REQUIRED`

## Completed run

ASR000001 executed all 26 frozen seed tasks and finalized atomically.

Transport attempts: `58`

Final outcomes:

- 16 transient transport failures;
- 9 HTTP errors;
- 1 policy failure;
- 0 successful authoritative-source retrievals.

All retrieval evidence verifies against the ASR000001 checksum manifest.

## NCBI transport failure

All 16 NCBI tasks failed after three attempts each.

All 48 attempts recorded exactly:

`Transient HTTPS transport error: [Errno 101] Network is unreachable`

These are transport failures, not scientific evidence and not scientific
exclusion criteria.

## DOI outcomes

Nine DOI tasks reached publisher destinations and returned HTTP 403.

Those are retained as genuine transport/access outcomes and are not silently
reissued.

RQ000003 ended in the frozen HTTPS-policy failure and is likewise not included
in the transport-failure continuation.

## Continuation

A future continuation run is assigned:

`ASR000002`

It contains exactly the 16 NCBI tasks whose ASR000001 final state was
`transient_transport_error`.

Continuation queue SHA-256:

`d0a50b1610f0dcc5f61412cb2285b23391c38dd527890e1542c1b25ade7b3ca2`

Permitted routes:

- `pubmed_record`
- `pubmed_pmc_link_discovery`

The continuation does not include any DOI seed task.

It does not yet have live execution authority.

## Required transport amendment

Before ASR000002 may execute, the transport must support failover across the
already validated public DNS addresses.

One validated address may be used per retry attempt.

The actual attempted resolved address must be retained in transport evidence.

The amendment must not weaken:

- public-address validation;
- SSRF protection;
- HTTPS-only policy;
- redirect policy;
- connect/read/wall-time limits.

## Scientific boundary

No scientific decision was made by ASR000001.

The production event ledger and review packet remain unchanged.

All ten target records remain `awaiting_source_escalation`.

Scientific review must not begin on the basis of failed retrieval alone.

## Next gate

`IMPLEMENT_VALIDATED_ADDRESS_FAILOVER_AND_ASR000002_CONTINUATION_GUARD`
