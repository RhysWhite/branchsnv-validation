# Triage pre-review text reconciliation v1 — implementation freeze

Status: `FROZEN_IMPLEMENTATION_PRE_OUTPUT`

This freeze binds the offline reconciliation implementation to the previously
frozen reconciliation design and Amendment 001.

## Repository position

- freeze parent: `53644804724a064acdc4a7b04870497091ed0c8f`
- original reconciliation-design commit: `1aa32f02387e4c5638b18b951bd5bc7a231c0b5f`
- Amendment 001 commit: `53644804724a064acdc4a7b04870497091ed0c8f`

## Frozen implementation

- `experiments/07_comparative_landscape/triage_pre_review_text_reconciliation_v1.py` — `2383ef19b895056d3b66c78019d1cbd62e830bffa034dffb70424c921244ddad`
- `experiments/07_comparative_landscape/test_triage_pre_review_text_reconciliation_v1.py` — `fb43dde98b8da8e9964ff672fca598141d70d366357f57755774175e97a95014`
- `experiments/07_comparative_landscape/test_triage_pre_review_text_reconciliation_hostile_v1.py` — `b7be01254ee62bf13e35c8805af690b2301567522558efae16a6885cf0d40bd1`

## Validation evidence

The candidate passed:

- 25 reconciliation-focused tests;
- 16 hostile reconciliation tests;
- 62 applicable lower-layer post-live regression tests;
- complete read-only reconstruction of all 4,499 development records;
- two independent complete temporary output builds;
- byte-identical comparison of all four generated files;
- structural and semantic validation of both temporary builds.

The obsolete pre-live Wave B assertion that authorization must not exist was
excluded because Wave B has subsequently completed its explicitly authorized
live execution. No frozen Wave B implementation or test was modified.

## Frozen reconciliation totals

- resolution rows: 4,499
- normalized-text rows: 4,190
- abstract absent: 309
- usable PubMed abstracts: 3,931
- usable OpenAlex abstracts: 259
- Wave B fallbacks: 25

## Expected canonical output hashes

- `reconciled_resolution.tsv` — `cb2a5d32d6eabcde6ba7aa5db52bfcc813fc52e45a897cac7ec13a632ce016d5`
- `reconciled_normalized_text.tsv` — `8c897444fe1a4d26226c8ecb798cd9d08bd3acc362aead972fdbee80d326785b`
- `reconciliation_summary.json` — `c43385e506a7d37c5290fdb3842c2991c0398efcf944f57be68ffadd51d5c802`
- `reconciliation_outputs.sha256` — `62aa1bed45d5bfc77b190247d94a1a9e4bb7be772d14fb55f2cbf03f3ab3f5cf`

Canonical output generation is not part of this freeze commit. The canonical
output directory must remain untouched until the next controlled gate.

## Boundaries

No network execution, scientific screening decision, scientific label,
model fitting, threshold selection, blind-validation-content use, production
mutation, raw-archive mutation, Wave A mutation or Wave B mutation is
authorized by this freeze.

Abstract absence remains absence of retrieval text and is not scientific
exclusion evidence.

## Next gate

`CONTROLLED_CANONICAL_RECONCILIATION_OUTPUT_GENERATION_WITH_EXACT_FROZEN_HASH_MATCH`
