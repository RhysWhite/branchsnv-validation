# Experiment 07 branch-history rewrite provenance

Status: `COMPLETE_LOCAL_HISTORY_REWRITE`

## Purpose

A publication-neutrality audit identified an excluded publication-venue label inside four provider-returned raw search snapshots. The exact excluded text is intentionally not reproduced here.

The affected blobs were reachable only from the local `experiment-07-comparators` branch. No other local branch, remote-tracking ref, or tag contained those blobs.

The branch history was therefore rewritten narrowly rather than deleting the raw retrieval evidence.

## Rewrite scope

- Rewrite base parent: `a8c8a65dc2e4d176c32d8dc1bdbfa13c194a86ef`
- First rewritten historical commit: `9b76a38f11e4aa6e8be4c10ae219838b1e997718`
- Rewritten equivalent: `c69c645ae452d53f68ad928942f7d8d1c8b31bf7`
- Pre-rewrite design HEAD: `5b85795e606f2048d954d5f5dbe07c6adec5a68d`
- Rewritten design HEAD: `cab2e61a0bdf7b64c0bfbf082da7df7a22c2720e`
- Rewritten commits: `52`
- Rewrite topology: linear

Commit authors, author dates, committers, committer dates, and commit messages were preserved exactly. The complete old-to-new mapping is in `commit_map.tsv`.

Historical commit identifiers embedded inside existing audit and provenance records were intentionally retained. They describe the repository state under which those historical operations actually ran; silently substituting rewritten identifiers would falsify that provenance.

## Content transformation

Only occurrences of the excluded venue label inside four raw provider snapshots were replaced with the literal marker `PUBLICATION_VENUE_REDACTED`.

Exactly seven paths differ between the pre-rewrite and rewritten design tips: four raw snapshots and three checksum manifests.

- `results/07_comparative_landscape/formal_search/raw/biotools/Q18_page_0002.json`
  - pre-rewrite SHA256: `44b6e6ff51564f6170c6c6c9d77a03430d57e760fe41597a2e80d6df624b1104`
  - rewritten SHA256: `bea2fc9119e36117bb79fa320fd57a5125132aee19743d8dbff740405ac25acc`
- `results/07_comparative_landscape/formal_search/raw/openalex/Q11_page_0001.json`
  - pre-rewrite SHA256: `a5a9c6a81a8383156a9082ee17554c9b6c160fe8ccd6b512c6c1fd63914735aa`
  - rewritten SHA256: `92f445a1b287f53973355fc40b9e4910d95f9175f9073b61d6d0201740d43ad3`
- `results/07_comparative_landscape/formal_search/raw/openalex/Q16_page_0009.json`
  - pre-rewrite SHA256: `e93a87f0e4cb38240fe15f43e404ac312d53a52edfb5641add7ae25b7b198237`
  - rewritten SHA256: `3accba7ead31b49199142b650c65122969bf75bb75e9e79d176d90c97cb67f1d`
- `results/07_comparative_landscape/formal_search/raw/pubmed/Q16_esummary_0003.json`
  - pre-rewrite SHA256: `8b695f9cf6104897760fb20c3b556981f89e5cc230279094b9f73283628f9730`
  - rewritten SHA256: `383dd43f480a64ba51ffe1659b185fa74dd06a5681f36a2c33b94bd52627fac3`

The three dependent checksum manifests were regenerated to match the rewritten raw bytes:

- `experiments/07_comparative_landscape/audit/attempt_01_fulltext_openalex/corpus_checksums.sha256`
- `experiments/07_comparative_landscape/audit/attempt_02_title_abstract_openalex/corpus_checksums.sha256`
- `results/07_comparative_landscape/formal_search/corpus_checksums.sha256`

## Validation

Before adoption into the working repository, the isolated rewritten candidate passed:

- frozen design and metadata-resolution queue checksum verification;
- the current offline screening-entity, citation-identity, cross-stage, and metadata-resolution queue regression suites;
- the complete historical Experiment 07 regression stack;
- zero scientific screening decisions;
- exact seven-path rewrite closure;
- checksum reconstruction from rewritten raw bytes;
- zero excluded venue-label matches across objects reachable from named refs;
- preservation of the 18 historical commit identifiers intentionally embedded as provenance strings.

After local adoption, the four uncommitted metadata-transport implementation/test files remained byte-identical and both transport synthetic suites passed. Live metadata execution remained disabled and no production metadata retrieval was performed.

## Recovery evidence

A complete pre-rewrite branch bundle was created outside the repository before history replacement.

- bundle SHA256: `138925009977068e3bcf53133ee334371b5b2055763b19c4ff1199295a8606c1`
- `commit_map.tsv` SHA256 before this note: `0e146e710310a95af8a87a54d2716bcd7d09dcb754ae910943c7da44b10922c0`

This provenance commit itself is subsequent to the 52-commit rewrite and therefore is not represented in `commit_map.tsv`.
