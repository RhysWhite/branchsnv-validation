# Pre-review triage future text live retrieval v1 — Amendment 001

Status: `FROZEN_PRE_IMPLEMENTATION`

This amendment corrects the pre-Wave-A authority boundary frozen in
commit `54e1b0404bf6ed87315b55f320495360e7ce1524`.

The supported future input manifest remains unchanged at 12,162 rows.

The base freeze incorrectly promoted all 12,162 records directly into
live Wave A. Reapplication of the frozen development offline-cache
semantics gives the exact partition:

- 14 records resolved from cached usable OpenAlex abstracts
- 1 record terminal from cached sources with no usable abstract
- 12,147 records requiring live Wave A lookup

The original 12,162-row Wave A manifest is retained byte-identically
as historical evidence but is superseded for execution authority.

Corrected Wave A:

- PubMed exact PMID EFetch: 8,539
- OpenAlex exact Work ID: 3,574
- OpenAlex exact DOI: 34
- Total live requests: 12,147

Corrected request manifest:

`results/07_comparative_landscape/pre_review_triage_future_text_retrieval_v1/live_wave_a_request_manifest_amendment_001.tsv`

SHA256:

`9c5a1b7cda465f0f4a88fc06c612c979af3093f0cecabbe4d8b42576cac30e73`

The 15 terminal-offline records are pinned through
`offline_selected_cache_provenance.tsv`. Their 45 selected terminal,
response-metadata and response-body files were independently verified
against the frozen 8,666-entry historical metadata-resolution checksum
manifest using paths relative to that checksum-manifest root.

This amendment creates no network authority and no execution authority.
It authorizes no model fitting, future scoring, threshold selection,
scientific screening decision, blind-validation scientific-content use,
or production mutation.

The next gate is to regenerate and hostile-test the future Wave A guard,
runner core and live entrypoint against Amendment 001 with real network
access disabled. A separate explicit human authorization may be created
only after that corrected implementation is committed.
