# Experiment 07 B000001 live-event authorization guard implementation

Status: `FROZEN_PRE_LIVE_AUTHORIZATION`

## Purpose

This freeze records implementation and hostile validation of the controlled
B000001 live-event authorization guard under authorization-design Amendment 01.

Parent Amendment 01 commit:

`2069f90c77a1ceba3bb5f1e89af38efa8cacc109`

The guard capability now exists, but no live authorization artifact exists and
no production scientific event has been accepted.

## Frozen implementation

Guard:

`b000001_live_event_entry_authorization_guard.py`

SHA-256:

`7de73aa421d1930fc7da9a87c568e36f289c3da1e0eb0c7ad1f6c01c73fa94c5`

Hostile tests:

`test_b000001_live_event_entry_authorization_guard.py`

SHA-256:

`f2bd0642bd66ee7828bd673f7d96b1dd54cbeabf0fddb0b63a6ae156cf1c55ce`

## Amendment 01

The guard treats:

`B000001_AUTHORIZATION_DESIGN_AMENDMENT_01`

as a mandatory normative dependency.

The amended review packet keeps all frozen baseline fields unchanged and places
all human-editable fields in the `proposed_` namespace.

The exact editable fields are:

- `proposed_event_type`
- `proposed_record_decision`
- `proposed_exclusion_reason_code`
- `proposed_candidate_method_flag`
- `proposed_evidence_basis`
- `proposed_evidence_source_locator`
- `proposed_evidence_escalation_status`
- `proposed_notes`

This resolves the parent-design naming collision without changing the
scientific contract.

## Deterministic review packet

The implementation deterministically generates the complete blank B000001
working review packet.

Rows:

`500`

Bytes:

`305410`

SHA-256:

`3e2187630de5555f7f00fba6034342d22a2a3b16ced345b20f5cff1c0f712e96`

The review packet itself is not persisted by this implementation freeze.

Its identity is pinned here and in the machine-readable implementation freeze.

All eight human-editable fields are blank at generation.

No software or model preclassification occurs.

## Canary identity

Batch:

`B000001`

Authorized future canary position:

`1`

Screening entity:

`publication_component:citation:publication:doi:10.1001/archdermatol.2012.1817`

Baseline-row SHA-256:

`bb8ef2c1e0fd980a70884709d3085b8e44b5b425500d390ae943f638f1d08048`

The guard does not itself authorize this entity for live mutation.

## Implemented controls

The frozen guard implements:

- mandatory validation of Amendment 01;
- reconstruction of exact frozen B000001 membership;
- deterministic review-packet generation;
- unique review-packet schema validation;
- immutable baseline-field validation;
- prohibition on human input in positions 2-500;
- exact mapping from amended `proposed_` fields to the frozen appender
  proposal schema;
- explicit operator-ID validation;
- exact one-use authorization validation;
- exact genesis-ledger requirement;
- dry-run canary preparation;
- exact one-event limit;
- expected first event ID `E000000001`;
- T000001 checkpoint staging;
- atomic invocation through the already-frozen appender;
- exact three-file checkpoint validation;
- receipt recording of Amendment 01;
- one-use replay rejection;
- recovery-state detection;
- preservation of staged checkpoint evidence after post-append failure;
- prohibition on retry after a ledger-success/checkpoint-failure state.

## Live-production authorization boundary

The guard does not create an authorization artifact.

For real production execution it requires a separately committed, tracked
authorization artifact satisfying the frozen authorization contract.

An untracked authorization cannot mutate the production ledger.

The guard therefore provides execution capability but not authorization.

## Hostile validation

Tests demonstrated:

- Amendment 01 is mandatory;
- exact B000001 identity reconstructs;
- review packet has no duplicate columns;
- frozen and proposed escalation fields are distinct;
- frozen and proposed notes fields are distinct;
- 500-row packet generation is deterministic;
- generated packet contains no preclassification;
- proposed values can be entered without changing frozen baseline fields;
- proposed values map into the exact frozen appender proposal;
- canary dry run succeeds against real genesis without mutation;
- position 2 scientific input fails closed;
- frozen baseline-note tampering fails closed;
- frozen baseline-escalation tampering fails closed;
- authorization cannot permit more than one event;
- authorization cannot enable positions 2-500;
- explicit operator identity is mandatory;
- untracked authorization cannot mutate production;
- complete T000001 execution succeeds against temporary copies;
- temporary checkpoint contains exactly three files;
- receipt records Amendment 01;
- replay fails closed;
- ledger-success/checkpoint-failure enters recovery-required state;
- staged recovery evidence is preserved;
- recovery state blocks duplicate append.

## Production state at freeze

Production ledger rows:

`0`

Production ledger SHA-256:

`d3ff9be1efe2b1237f616f25e702275ccc608577fa0ff8b301401a72900eb55f`

Active states:

- ready: 94,622;
- awaiting source escalation: 0;
- complete: 0;
- blocked metadata: 484.

Real receipt root:

absent.

Live authorization artifact:

absent.

Scientific screening:

not started.

## Checksum treatment

The future-mutable production `event_ledger.tsv` is deliberately omitted
from this historical implementation checksum manifest.

Its exact genesis SHA is nevertheless pinned in this document and in the
machine-readable freeze.

The derived review packet is also not included as a persisted file because it
can be reproduced byte-identically from frozen inputs. Its exact SHA and byte
count are frozen instead.

## Scientific boundary

At this freeze:

- production events = 0;
- B000001 accepted decisions = 0;
- B000001 source-escalation events = 0;
- authoritatively reviewed B000001 positions = 0;
- method assessments = 0;
- role assignments = 0;
- canonical-publication decisions = 0;
- Wave 1 promotions = 0;
- no live authorization exists;
- no production checkpoint exists;
- scientific screening has not begun.

## Next gate

`CREATE_CONTROLLED_B000001_POSITION_1_ONE_USE_LIVE_AUTHORIZATION`

That gate may create and freeze the tracked one-use authorization artifact,
including the explicit human operator identity.

It must not itself preselect a scientific decision or append the production
event.
