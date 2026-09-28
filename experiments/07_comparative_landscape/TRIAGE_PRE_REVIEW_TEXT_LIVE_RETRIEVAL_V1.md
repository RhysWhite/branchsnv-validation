# Triage pre-review text live retrieval v1

## Status

`FROZEN_PRE_AUTHORIZATION`

This freeze creates no live-network authority.

It defines the authority boundary that must be satisfied before any
development-text retrieval request is sent.

## Wave A

Wave A contains exactly 4,490 first-hop exact requests:

- 3,956 PubMed exact PMID EFetch requests;
- 526 OpenAlex exact Work-ID requests;
- 8 OpenAlex exact DOI requests.

Frozen request manifest:

`results/07_comparative_landscape/triage_pre_review_text_retrieval_v1/live_wave_a_request_manifest.tsv`

SHA-256:

`91a87f2d8a2bfc00ead9a5f1b6e6fcaf850666573583bb07317a1416d446211d`

Only exact singleton retrieval is permitted. Search/list endpoints,
Crossref fallback, and ad hoc connectivity probes are outside Wave A.

## Transport

The existing exact-identifier transport is reused unchanged.

Frozen transport mappings are:

- PubMed `exact_pmid_efetch` -> `record_by_pmid`;
- OpenAlex `exact_work_id` -> `work_by_openalex_id`;
- OpenAlex `exact_doi` -> `work_by_doi`.

Maximum initiation rate remains two requests per second for each
provider. Execution is serial in frozen request order.

PubMed live execution requires the configured NCBI contact email.
The contact value and provider credentials must never enter archived
evidence.

## Authorization

This freeze is not an authorization.

A later authorization must bind the exact design, Wave A request
manifest, source hashes, output root, parent commit, and maximum request
count.

Authorization is one-use. The first execution binds an execution ID.
A failed/interrupted run may resume only under that same execution ID
from a verified checkpoint. A second execution ID or replay after
completion fails closed.

## Wave B

Wave A does not authorize OpenAlex fallback requests for PubMed records.

After Wave A is complete, a second deterministic manifest may be
derived only for PubMed records whose verified result establishes no
usable PubMed abstract under the frozen rules.

Transient transport failure, parser failure, identity mismatch, or
unverified evidence cannot trigger fallback.

Wave B requires a separate human authorization.

## Scientific boundary

Neither Wave A nor this design creates a scientific decision, model
score, threshold, automated exclusion rule, production-screening
authority, future-universe scoring authority, or blind-validation
authority.

## Next gate

Implement and hostile-test the Wave A authorization guard and live
execution runner with mocked transport only. No real network request is
permitted at that gate.
