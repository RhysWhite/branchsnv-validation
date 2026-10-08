# Experiment 07 post-retrieval metadata reconciliation design

Status: `FROZEN_PRE_IMPLEMENTATION`

## Purpose

This stage defines how frozen metadata-retrieval evidence may be interpreted
after retrieval completion and before scientific screening.

It does not perform reconciliation, component merging, scientific screening,
or any additional provider request.

The raw retrieval archive remains immutable evidence.

## Frozen inputs

The design operates on the completed Experiment 07 metadata-retrieval state:

- 1,342 attention components;
- 1,847 lookup assignments;
- 1,731 unique logical lookups;
- 1,698 successful retrievals;
- 33 exact `not_found` outcomes.

The metadata-retrieval archive is `COMPLETE`.

## General principles

1. Retrieval evidence is immutable.
2. Reconciliation creates derived evidence only.
3. No provider is globally ranked as authoritative.
4. No majority vote may establish publication identity.
5. Title agreement cannot override identifier conflict.
6. `not_found` is route-specific negative evidence only.
7. `not_found` does not prove that a publication does not exist.
8. No component merge is permitted during this stage.
9. No scientific inclusion/exclusion decision is permitted.
10. Every derived decision must identify the exact lookup evidence supporting
   it.
11. Ambiguity must remain explicit rather than being guessed away.

## Identifier-conflict components

There are exactly 117 components assigned to
`adjudicate_identifier_conflict`.

Read-only audits found:

- zero successful-lookup self-confirmation failures;
- zero disconnected requested-identifier graphs;
- 68 components with focal-response same-namespace multiplicity;
- 48 components classified by cross-provider primary-identifier disagreement;
- one component classified by an external focal same-namespace identifier;
- 17 with residual title disagreement after transparent comparison
  normalisation; and
- zero clean connected candidates under the frozen diagnostic rules.

The 117 components therefore remain `identifier_conflict_hold`.

No automatic identifier winner is selected.

No DOI, PMID, OpenAlex identifier, or OMID is deleted.

No publication components are merged on the basis of these retrieval results.

Title agreement, including agreement after case/punctuation normalisation, does
not resolve an identifier conflict.

## Native-provider identity components

There are exactly 502 `native_provider_identity` components.

The retrieval outcomes are:

- 494 successful self-confirming native-provider lookups;
- 8 exact `not_found` outcomes;
- 262 with exactly one DOI and exactly one PMID anchor;
- 48 with exactly one DOI and no PMID anchor;
- 1 with exactly one PMID and no DOI anchor;
- 183 successful native-provider records with neither DOI nor PMID; and
- zero successful lookups with multiple competing DOI or PMID anchors.

### Unique publication anchors

The 311 components with exactly one DOI and/or one PMID may receive those
identifiers as derived exact publication anchors.

This does not merge the component with any other component.

A later, separately frozen component-consolidation stage would be required
before any cross-component union could occur.

### Confirmed but unanchored provider identities

The 183 successful records with no DOI or PMID remain
`provider_identity_confirmed_unanchored`.

Their native OpenAlex ID or OMID is retained.

No DOI or PMID is inferred from title similarity.

### Provider `not_found`

The eight exact `not_found` cases remain
`provider_identity_not_found`.

Their pre-existing component identity is retained unchanged.

No title, DOI or PMID is inferred.

## Title recovery

There are exactly 1,067 components assigned a `recover_title` purpose.

The retrieved evidence is:

- 575 components with exactly one exact retrieved title;
- 7 with multiple exact strings that are token-equivalent under the frozen
  diagnostic comparison;
- 1 with multiple exact strings that are compact-equivalent;
- 2 with substantive residual cross-identifier disagreement; and
- 482 with no retrieved title.

### Exact single-title evidence

For the 575 components with one exact retrieved title, that exact string may
be emitted as `resolved_title`.

The source lookup or lookups must be recorded.

### Normalisation-equivalent variants

For the eight components with multiple exact strings that differ only under
the frozen transparent diagnostic normalisation, the exact source strings are
all preserved.

Their status is `title_equivalent_variants`.

No exact source spelling is silently declared more authoritative than another
during reconciliation design.

`resolved_title` therefore remains empty for these eight components unless a
later separately frozen display-string rule is adopted.

The comparison normalisation is evidence classification only. It does not
rewrite raw titles.

### Residual title conflict

The two `recover_title` components with substantive cross-identifier title
disagreement remain `title_conflict_hold`.

No title is selected.

### No retrieved title

The 482 components with no retrieved title remain `title_unresolved`.

A successful identifier lookup without a title is not converted into a title
by inference.

## Amendment 36 records

The seven Amendment 36 OpenCitations adjudications are ordinary successful
retrieval evidence at this stage.

Their original historical failed attempts remain immutable.

Only metadata fields explicitly present in the preserved adjudicated response
may contribute evidence.

The Amendment 36 rule itself does not create title precedence or identifier
precedence.

## `not_found` semantics

An exact `not_found` records only that the frozen provider route did not return
a record for the exact requested identifier during the retrieval run.

It must not:

- delete an identifier;
- prove that a publication does not exist;
- cause component exclusion;
- override positive evidence from another exact route; or
- trigger fuzzy matching.

## Planned derived outputs

Implementation should create derived files rather than modify retrieval
inputs.

At minimum the reconciliation implementation should produce:

1. one component-level reconciliation row for each of the 1,342 attention
   components;
2. an evidence ledger linking every derived value/status to exact logical
   lookup IDs;
3. explicit title status;
4. explicit identifier status;
5. exact derived DOI/PMID anchors where permitted;
6. preserved conflict-hold states; and
7. a machine-readable baseline and checksum manifest.

The component-level output must retain all 1,342 components.

## Required component-level states

Identifier status must distinguish at least:

- `identifier_conflict_hold`;
- `provider_identity_anchored`;
- `provider_identity_confirmed_unanchored`;
- `provider_identity_not_found`;
- `not_applicable`.

Title status must distinguish at least:

- `title_resolved_exact`;
- `title_equivalent_variants`;
- `title_conflict_hold`;
- `title_unresolved`;
- `not_applicable`.

A component may independently have an identifier state and a title state.

## Prohibited implementation behaviour

The implementation must fail closed if it attempts to:

- modify raw retrieval files;
- make a network request;
- select a winner among the 117 identifier-conflict components;
- merge components;
- infer DOI or PMID from title similarity;
- treat title equivalence as proof of identifier equivalence;
- convert `not_found` into scientific exclusion;
- perform fuzzy matching;
- perform scientific screening; or
- rank candidate software/tools.

## Scientific boundary

This is still metadata preparation.

`scientific_screening_performed` must remain `false`.

`component_merge_performed` must remain `false`.

`screening_log.tsv` must remain empty.

## Superseded diagnostic

One exploratory identifier-linkage report used an over-broad PubMed XML
identifier parser that included nested reference/correction identifiers.

That report is explicitly superseded and excluded from this design.

The corrected focal-record audit, which restricts PubMed identifier evidence
to the primary record and its focal `ArticleIdList`, is the accepted audit.

## Next gate

The next gate is:

`IMPLEMENT_FROZEN_POST_RETRIEVAL_RECONCILIATION_WITHOUT_SCREENING`

Implementation must be tested against synthetic hostile cases before any
production reconciliation output is created.
