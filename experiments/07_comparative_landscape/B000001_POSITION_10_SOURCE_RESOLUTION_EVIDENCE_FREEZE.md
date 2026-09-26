# Experiment 07 B000001 position 10 source-resolution evidence freeze

Status: `FROZEN_POSITION_10_SOURCE_EVIDENCE_PRE_DECISION_FREEZE`

Parent commit:

`dd0c5036f5ae28890ba85d1758e6a070aaeeaeef`

## Scope

This freeze covers only B000001 position 10:

`publication_component:citation:publication:doi:10.1002/9780470015902.a0020859`

Current event:

`E000000010`

Current state:

`awaiting_source_escalation`

## Newly frozen evidence

The exact DOI was resolved independently through:

- Crossref REST exact-DOI metadata;
- DOI CSL content negotiation;
- normal DOI resolution to the Wiley Online Library publisher target.

Crossref and DOI CSL both identify the record as:

`Selection against Amino Acid Replacements in Human Proteins`

in the `Encyclopedia of Life Sciences`, published by Wiley.

The Crossref record contains a substantive abstract. Raw source bytes and
network status have been retained in the frozen evidence directory.

Evidence packet SHA-256:

`59d70f1a8dfea1042be3f48f03e09648ca173fe482841fd571e181ae56b928a5`

Evidence facts SHA-256:

`b11022571fb37b5f707561eb2dbf10753f05a735299a726f4080c3b6d0b6e12c`

Evidence packet Markdown SHA-256:

`012be3ba5e67226ee02f56c133bb38c205958f91f4622d08d0754be16b4619d6`

Evidence checksum-manifest SHA-256:

`4b5ef95e11ab1d6a67e84094ffd236a44cfa7cb565bdf3ee3f3c7aee1d348261`

## Production boundary

Production ledger SHA-256 remains:

`3433a183d6a5bb4434a4b26e72bf6e380d546d6e53688a506328bf7f4bda5793`

with exactly 21 events.

This evidence freeze does not:

- append or supersede an event;
- create production mutation authority;
- itself freeze a scientific disposition;
- change Position 10 from `awaiting_source_escalation`.

## Next gate

`FREEZE_HUMAN_APPROVED_B000001_POSITION_10_SCIENTIFIC_DECISION`
