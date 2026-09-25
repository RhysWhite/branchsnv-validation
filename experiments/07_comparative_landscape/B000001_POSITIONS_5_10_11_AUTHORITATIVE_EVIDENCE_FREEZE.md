# Experiment 07 B000001 positions 5, 10 and 11 authoritative-evidence freeze

Status: `FROZEN_EVIDENCE_ONLY_PRE_ADJUDICATION`

Parent commit:

`cd742d84a0359f0e9771fb66788be3e4c8d7a3d0`

T000003 completion-freeze SHA-256:

`10bec5edfc74066398ca07eea12727d410314fd6bf90aa6719fc87decbb93200`

## Scope

This freeze covers only B000001 positions 5, 10 and 11.

It freezes evidence required for later human scientific adjudication.

It does not:

- alter a scientific disposition;
- create an event proposal;
- create live event authority;
- modify the production event ledger;
- establish Wave-1 eligibility.

## Position 5

The frozen PubMed source record establishes that the publication documents
explicit analytical protocols based on PAML programs.

PAML is already frozen as:

- Wave-0 anchor: `W0A07`;
- canonical DOI: `10.1093/molbev/msm088`;
- confirmed role: `near_direct`.

The evidence does not yet establish whether position 5 adds a distinct relevant
reusable capability beyond the existing PAML method identity.

Position 5 remains:

`retain_for_method_assessment`

## Positions 10 and 11

Frozen screening identities are:

- position 10:
  `publication_component:citation:publication:doi:10.1002/9780470015902.a0020859`
- position 11:
  `publication_component:citation:publication:doi:10.1002/9780470015902.a0020859.pub2`

Authoritative Wiley evidence establishes a previous/current publication-version
relationship between the base DOI and the `.pub2` DOI.

The current `.pub2` identity is independently corroborated by the University
of the Sunshine Coast institutional repository.

### Source-capture limitation

Raw Wiley publisher bytes are not archived in the Experiment-07 repository.

The publisher evidence is frozen as an
`authoritative_web_source_fact_transcription`, with the stable source URL and
the raw-byte limitation retained explicitly.

This is not represented as human verification by the operator.

No terminal disposition is made for either position at this gate.

## Frozen evidence identities

Source-review packet SHA-256:

`f3fb68cb08f03c255daf13ee0d72222b14528cf41920b31e0af57c6d3a005928`

Batch-membership SHA-256:

`858da5437197b78898c1703318d2c9c9be23a8f0eaade31df7b0f2de81726a91`

Evidence packet JSON SHA-256:

`0738af45d26f5c35875f465a4b80987dd6d1781771c34cd2ece8ecd7a5846513`

Evidence facts TSV SHA-256:

`41f064b9fbcb8a2e029366d8dd3e28ff6dd2183ebab280bebb8823c977bf4232`

Evidence packet Markdown SHA-256:

`9bb8ec8880958b11df6b25bbc5c41e6c7294760601a32d6f21d517838c8b1402`

Evidence checksum manifest SHA-256:

`e12bbe83e29f549cdffbc36d470bba44aa3bebfee718fbe76e1a2f4b8b31dcea`

Production ledger remains:

`a1303b93bd70c2106582f2a5a8749fcdfd649c18ff31fc6c3712cce8dc2f54fe`

with exactly 19 events.

## Decision boundary

Current states remain:

- position 5: `retain_for_method_assessment`;
- position 10: `awaiting_source_escalation`;
- position 11: `awaiting_source_escalation`.

No event proposal exists.

No additional production mutation authority exists.

## Next gate

`HUMAN_SCIENTIFIC_ADJUDICATION_POSITIONS_5_10_11`
