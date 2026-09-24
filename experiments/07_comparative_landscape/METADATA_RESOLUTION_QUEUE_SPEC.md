# Experiment 07 metadata-resolution logical evidence queue

Status: FROZEN_PRE_RETRIEVAL_QUEUE_CANDIDATE

## 1. Purpose

This specification defines the exact first-pass metadata evidence required
before scientific screening of the Experiment 07 comparator landscape.

The queue is derived only from already-frozen discovery, identity, and
cross-stage component artifacts.

No live metadata response was used to choose the queue.

## 2. Frozen upstream state

The queue is derived from the offline cross-stage implementation frozen at:

`78836f58fb1fdc31b3144cf7038f571b3f1f7947`

That layer derives:

- 94,898 provisional publication components;
- 215 software-registry components;
- 95,113 provisional screening components total;
- 619 publication components requiring identity attention;
- 1,067 publication components lacking a title; and
- 1,342 unique publication components requiring identity and/or title
  attention.

The 215 software-registry components require no metadata attention at this
stage.

## 3. Separation of layers

The following are distinct objects:

1. frozen discovery records;
2. frozen within-stage identities;
3. frozen cross-stage provisional components;
4. evidence questions;
5. component-evidence assignments;
6. logical exact lookups;
7. HTTP transport operations;
8. provider responses;
9. reconciliation decisions; and
10. scientific screening decisions.

No downstream layer may silently redefine an upstream layer.

## 4. Evidence questions

Three evidence questions are represented:

### 4.1 Provider-specific identity resolution

Determine what bibliographic entity a provider-local provisional identity
represents.

### 4.2 Identifier-conflict adjudication

Collect independent exact metadata relevant to inconsistent DOI, PMID,
OpenAlex, OMID, or cross-stage identifier evidence.

### 4.3 Title recovery

Obtain a usable publication title for a provisional publication component that
remains titleless after safe offline cross-stage aggregation.

## 5. First-pass policy

### 5.1 Provider-specific unresolved identity

Use the native exact provider identifier only.

OpenAlex-only provisional identity:

- provider: `openalex`
- route: `work_by_openalex_id`
- namespace: `openalex`

OpenCitations-only provisional identity:

- provider: `opencitations_meta`
- route: `metadata_by_omid`
- namespace: `omid`

### 5.2 Identifier conflict

Collect all applicable exact evidence from identifiers already present in the
frozen component.

Allowed routes:

| Identifier | Provider | Logical route |
|---|---|---|
| OpenAlex Work ID | OpenAlex | `work_by_openalex_id` |
| DOI | OpenAlex | `work_by_doi` |
| PMID | OpenAlex | `work_by_pmid` |
| DOI | OpenCitations Meta | `metadata_by_doi` |
| OMID | OpenCitations Meta | `metadata_by_omid` |
| PMID | PubMed | `record_by_pmid` |

There is no first-pass provider precedence and no early stopping.

### 5.3 Title-only

Use all exact native-provider identifiers represented by frozen source
provenance.

Native routes:

| Frozen source | Native identifier | Logical route |
|---|---|---|
| OpenAlex | OpenAlex Work ID | `work_by_openalex_id` |
| PubMed | PMID | `record_by_pmid` |
| OpenCitations | OMID | `metadata_by_omid` |

A non-native identifier merely present in metadata does not switch the
first-pass title request to another provider.

If more than one native source exists, all native exact routes are retained.

## 6. Exact-only boundary

The queue forbids:

- fuzzy title matching;
- title search;
- author search;
- approximate metadata matching;
- free-text search;
- software-name search;
- new literature discovery queries; and
- retrospective search-query tuning.

A later exact-identifier escalation requires a separately frozen escalation
plan based on retained first-pass outcomes.

## 7. Logical lookup identity

A logical lookup key is the ordered tuple:

`provider | route | identifier_namespace | normalized_identifier`

Its stable ID is the SHA-256 of the canonical JSON encoding of that tuple.

The same logical lookup may support multiple provisional components and
multiple purposes.

Logical-lookup reuse does not imply component identity.

## 8. Component-evidence assignment

Each assignment records:

- provisional screening-component ID;
- logical lookup ID;
- provider;
- logical route;
- identifier namespace;
- normalized identifier;
- queue-policy class; and
- evidence purpose or purposes.

Assignment identity is deterministically SHA-256 derived from those values.

## 9. Transport independence

The logical evidence queue does not prescribe one HTTP request per logical
lookup.

Transport code may batch provider-compatible lookups when supported.

Transport code may retry failed network operations.

Transport code may follow redirects while retaining redirect provenance.

Transport behavior must not change the logical lookup set.

## 10. Provider-response handling

Provider responses are evidence only.

Later retrieval code must retain raw responses or byte-equivalent evidence,
request provenance, checksums, status information, and redirect information.

No provider response automatically merges provisional components.

## 11. OpenAlex merged IDs

If an exact OpenAlex lookup redirects because an entity has been merged, the
requested identifier and returned/final identifier must both be retained.

The redirect is not itself an authorization to rewrite the frozen queue or
merge screening components.

## 12. OpenCitations route restriction

The first-pass Experiment 07 queue uses OpenCitations Meta only for:

- exact DOI lookup; and
- exact OMID lookup.

Broader identifier support is not required by this frozen queue.

## 13. PubMed route restriction

The first-pass Experiment 07 queue uses PubMed only for exact PMID metadata
retrieval.

Search endpoints are not part of the queue.

Transport implementation may batch exact PMIDs without changing their logical
lookup identities.

## 14. Frozen queue counts

Attention components:

- 1,342.

Component-evidence assignments:

- 1,847 total;
- 621 `conflict_all_exact_evidence`;
- 502 `native_provider_identity`;
- 724 `native_title_evidence`.

Unique logical lookup keys:

- 1,731 total.

By provider:

- OpenAlex: 1,169;
- OpenCitations Meta: 495;
- PubMed: 67.

By route:

- OpenAlex `work_by_doi`: 115;
- OpenAlex `work_by_openalex_id`: 987;
- OpenAlex `work_by_pmid`: 67;
- OpenCitations Meta `metadata_by_doi`: 115;
- OpenCitations Meta `metadata_by_omid`: 380;
- PubMed `record_by_pmid`: 67.

Title-only native evidence:

- 723 components;
- 724 assignments;
- 722 components with one native route;
- 1 component with two native routes;
- 394 OpenAlex native-title assignments;
- 330 OpenCitations native-title assignments;
- 0 PubMed native-title assignments in the frozen corpus.

Shared logical lookups:

- 116 logical lookup keys serve more than one component;
- 115 are shared within conflict evidence;
- 1 is shared across conflict evidence and native-provider identity resolution.

## 15. Interpretation

The 1,731 logical lookups are not 1,731 scientific observations and are not
necessarily 1,731 HTTP requests.

They are the frozen set of exact provider/route/identifier evidence objects
requested by the first-pass metadata-resolution design.

No identity resolution, component merge, or scientific screening decision is
encoded in the lookup manifest.
