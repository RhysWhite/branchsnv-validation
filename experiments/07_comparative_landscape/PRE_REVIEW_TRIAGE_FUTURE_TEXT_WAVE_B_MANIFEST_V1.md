# Pre-review triage future text Wave B manifest v1

Status: `FROZEN_PRE_IMPLEMENTATION`

## Purpose

This freeze defines the deterministic Future Wave B OpenAlex fallback
population derived from the completed and frozen Future Wave A retrieval.

It does not authorize network access.

It does not create a Wave B execution authorization.

It does not perform reconciliation, future scoring, model fitting, threshold
selection, blind-validation scientific inspection, or scientific screening.

## Frozen candidate population

Exactly 40 Future Wave A PubMed records require OpenAlex fallback:

- 38 because the verified PubMed record normalized as `abstract_absent`;
- 2 because the exact PubMed route ended `verified_not_found`.

The OpenAlex routes are:

- 31 `exact_work_id`;
- 8 `exact_doi`;
- 1 `exact_pmid`.

The route precedence is:

`exact_work_id -> exact_doi -> exact_pmid`

## Request 10083

Request 10083 is not a Wave B candidate.

Its explicitly authorized no-network recovery selected PMID 37878119 from
the already archived PubMed response. The selected focal record reproduces
`usable_abstract_pubmed`, so the retrieval cascade terminates at Future
Wave A.

The original request-10083 canonical fault evidence remains preserved.

## Frozen outputs

Request manifest:

`results/07_comparative_landscape/pre_review_triage_future_text_retrieval_v1/live_wave_b_request_manifest.tsv`

Rows: 40

SHA-256:

`e6b79c2fff3f31a8155dd7c37188d0ea2c4bd786c7e7de9950570288a2c62d11`

Derivation evidence:

`results/07_comparative_landscape/pre_review_triage_future_text_retrieval_v1/live_wave_b_derivation.tsv`

Rows: 40

SHA-256:

`7fc3bd6fee6c5a3539587223ef6459df1ecce41ad670de3929836eef7a6c4474`

No title text or abstract text is stored in either Wave B manifest artifact.

## Authority boundary

This freeze creates no network authority.

Future Wave B requires a separate explicit human authorization after the
execution guard, transport adapter, runner core and live entrypoint have been
implemented, hostile-tested and frozen.

The Future Wave A authorization cannot authorize Future Wave B.

## Implementation requirement

The future execution layer must support all three frozen exact OpenAlex
routes.

In particular, the manifest contains one `exact_pmid` request using
`work_by_pmid`. This route must be explicitly implemented and hostile-tested;
the historical development Wave B population did not exercise that route.

## Next gate

`IMPLEMENT_AND_HOSTILE_TEST_FUTURE_WAVE_B_EXECUTION_BEFORE_SEPARATE_HUMAN_AUTHORIZATION`
