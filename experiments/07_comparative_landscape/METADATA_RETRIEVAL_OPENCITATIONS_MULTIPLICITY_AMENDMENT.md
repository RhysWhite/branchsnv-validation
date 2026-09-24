# Experiment 07 OpenCitations exact-response multiplicity amendment

Status: `FROZEN_PRE_IMPLEMENTATION_RESPONSE_MULTIPLICITY_CORRECTION`

## Purpose

The first production metadata-resolution run executed the frozen 1,731-lookup
queue through the frozen archive runner.

The run terminated `INCOMPLETE` with:

- 1,691 successful lookups;
- 33 exact not-found results; and
- 7 response-integrity failures.

All seven response-integrity failures arose from OpenCitations Meta exact
lookups returning more than one HTTP-200 JSON record.

No other provider produced a response-integrity failure.

This amendment defines how that empirically observed provider response shape is
to be classified.

## Empirical observation

The seven affected exact OpenCitations lookups returned 15 provider rows in
total.

Within each affected lookup:

- every returned row was a JSON object;
- every row had the same complete `id` bundle;
- every row contained the exact requested DOI or OMID token;
- title was invariant;
- author was invariant;
- type was invariant; and
- after excluding `venue` and `pub_date`, every record was canonically
  identical.

Six lookups differed only in `venue`.

One lookup differed only in `pub_date`.

The returned rows were therefore not byte-identical duplicates. The provider
supplied multiple descriptive representations of one identity-concordant
bibliographic resource.

## Existing transport output boundary

The frozen metadata-resolution transport does not promote OpenCitations title,
venue, publication date, author, or type into terminal evidence.

Its accepted terminal representation contains the provider identifier bundle
plus transport/archive provenance.

The complete provider response remains preserved as immutable raw evidence.

## Amendment rule

For `opencitations_meta` exact metadata lookup routes only, a JSON list
containing more than one record may be classified as a successful provider
identity observation only when all of the following are true:

1. every returned element is a JSON object;
2. every record contains a non-empty `id` field;
3. after surrounding whitespace is removed, the complete `id` field is
   exactly identical across all returned records;
4. every returned `id` bundle contains the exact requested identifier token,
   expressed as `<identifier_namespace>:<identifier>`;
5. after removing only the fields `venue` and `pub_date`, deterministic
   canonical JSON for every record is exactly identical.

Consequently, title, author, type and every other non-excluded field must be
identical across the provider rows.

## Permitted descriptive multiplicity

Only `venue` and `pub_date` are permitted to differ under this rule.

Neither field is selected, ranked, merged, normalized, reconciled or promoted
into terminal evidence.

Their conflicting provider values remain preserved verbatim in the immutable
raw response.

## Fail-closed conditions

A multi-record OpenCitations exact response remains a
`response_integrity_failure` if any of the following occurs:

- a returned element is not an object;
- an `id` field is absent or empty;
- identifier bundles differ;
- any row does not contain the exact requested identifier;
- any field other than `venue` or `pub_date` differs;
- canonical equivalence after excluding `venue` and `pub_date` fails; or
- the response is otherwise structurally invalid.

No first-row preference is permitted.

No majority rule is permitted.

No field-value selection is permitted.

No fuzzy matching is permitted.

## Singleton and empty responses

Existing behavior is unchanged:

- an empty exact OpenCitations response remains `not_found`;
- a singleton exact OpenCitations response follows the existing singleton
  classification path.

## Raw evidence and provenance

The original seven failed attempts remain immutable production evidence.

This amendment does not authorize rewriting, deleting or reclassifying those
attempt records in place.

After implementation and testing are separately frozen, the production archive
may be resumed through the existing archive/resume mechanism.

Any new provider exchange becomes a new attempt.

## Downstream boundary

This amendment establishes only provider identity for the transport terminal
state.

It does not resolve conflicting venue or publication-date metadata.

It does not implement title reconciliation.

It does not merge publication components.

It does not consolidate software tools.

It does not perform scientific screening.

Any later consumer of descriptive metadata must operate from preserved raw
evidence under its own explicit reconciliation rules.

## Unchanged scientific state

This amendment does not alter:

- the 1,731 frozen logical lookup keys;
- the 1,342 attention components;
- the 1,847 evidence assignments;
- provider assignment;
- identifier namespace or identifier value;
- lookup routes;
- retry limits;
- redirect limits;
- pacing;
- raw-response preservation;
- archive/resume semantics;
- publication identity rules;
- tool-consolidation rules; or
- screening rules.

Scientific screening remains zero.

## Next gate

Implement and test this response-multiplicity rule offline.

Live retrieval must not be resumed until that implementation is independently
frozen.
