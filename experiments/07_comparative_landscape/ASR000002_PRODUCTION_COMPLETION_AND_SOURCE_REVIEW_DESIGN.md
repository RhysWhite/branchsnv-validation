# Experiment 07 ASR000002 production completion and source-review design

Status: `FROZEN_PRE_HUMAN_SOURCE_REVIEW`

## ASR000002 production completion

Authorization commit:

`369f117c4b65e8d35f95824a3500e6ddfda8d069`

Authorization SHA-256:

`59fb42fe7f915ef95c8e1470fcdc1ab1e05c79006e9f8163007d0f5f24120eb9`

Continuation queue SHA-256:

`d0a50b1610f0dcc5f61412cb2285b23391c38dd527890e1542c1b25ade7b3ca2`

ASR000002 completed all 16 authorized NCBI continuation tasks.

All 16 tasks ended in `retrieved`.

Total transport attempts: 32.

The validated-address failover was exercised in production.

Ninety child-route candidates were discovered but none was executed.

ASR000002 finalized atomically with no staging directory remaining.

## Derived source-review packet recovery

The initial read-only source-review builder completed the TSV and JSON outputs
but stopped before Markdown rendering because the renderer referenced the
non-existent key `abstract` rather than the actual record field
`pubmed_abstract`.

No production retrieval evidence or scientific state was affected.

Before recovery:

- the derived review directory contained exactly the completed TSV and JSON;
- both files were structurally validated;
- the TSV and JSON agreed for all ten records;
- all scientific-decision fields were blank;
- no Markdown or checksum artifact existed.

The Markdown packet was then rendered from the validated JSON using the
correct `pubmed_abstract` field and the four-file derived packet was frozen.

## Scientific boundary

ASR000002 made no scientific decision.

It did not mutate:

- the production screening event ledger;
- the B000001 review packet.

All ten target records remain `awaiting_source_escalation`.

Retrieval success itself is not a scientific disposition.

## Human source-review packet

A derived read-only packet is frozen at:

`results/07_comparative_landscape/baseline_scientific_screening_review_work/B000001/ASR000002_source_review`

It contains positions 2–11.

For positions 2–9 it incorporates the frozen PubMed primary-record and
link-discovery evidence recovered by ASR000002.

Positions 10–11 are retained explicitly without invented PubMed evidence.

The packet also retains the frozen DOI transport/access outcome from
ASR000001.

All scientific-decision fields remain blank.

## Source hierarchy

Human review must apply the previously frozen evidence rules.

A substantive primary-publication abstract may support a terminal scientific
decision where it establishes the required facts.

Absence of full text, HTTP 403, source unavailability or failed retrieval is
not itself a scientific exclusion.

Discovered child routes remain unexecuted unless separately authorized.

## Next gate

`HUMAN_SCIENTIFIC_REVIEW_B000001_POSITIONS_2_TO_11`
