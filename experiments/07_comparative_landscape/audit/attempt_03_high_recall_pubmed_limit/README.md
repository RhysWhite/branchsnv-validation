# Retrieval attempt 03 — high-recall search failure

This was the first execution of the frozen generic high-recall expansion.

The retrieval was executed from repository commit
`080b581cbd93a5b4d4f1f12bb6bd03b2edb7e3c7`.

Retrieval completed through HR01–HR04 across the configured sources and then
failed closed when PubMed HR05 reported 12,654 records, exceeding the
retriever's prespecified 10,000-record PubMed ESearch ceiling.

No screening, eligibility decision, capability classification, or benchmark
selection was performed from this partial retrieval.

The complete partial raw corpus is intentionally not committed as the formal
screening corpus. This audit record retains:

- the failure manifest;
- the checksum manifest covering the partial corpus;
- the complete console log;
- the raw HR05 PubMed ESearch response establishing the reported count;
- a source/query partial-file inventory; and
- a structured failure summary.

The local partial corpus will be retained until the retrieval-limit handling
amendment is frozen and a replacement retrieval succeeds.
