# Merged-universe PMID conflict integrity audit

The frozen production merged universe contains 14 deduplication-key groups
with more than one non-empty PMID value.

All 14 groups are keyed by DOI under the pre-existing frozen identity
hierarchy, in which normalized DOI takes precedence over PMID.

Twelve groups reflect disagreement between PubMed and OpenAlex PMID metadata.
Two groups contain more than one PubMed source record carrying the same DOI.

For every PubMed candidate row in these groups, the PubMed source-record
identifier agrees with the stored PMID. The PMID values recorded by
`metadata_conflicts.tsv` also exactly reproduce the underlying candidate
metadata.

No identity rule, candidate record, deduplication key, representative metadata,
eligibility decision, or screening decision was modified as a consequence of
this audit.

The audit therefore records source-metadata heterogeneity rather than silently
resolving it.
