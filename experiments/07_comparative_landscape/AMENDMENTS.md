# Experiment 07 protocol amendments

## Amendment 01 — OpenAlex query syntax

**Timing:** before formal database retrieval or screening.

After freezing the initial search protocol, the current OpenAlex API
documentation was checked against the recorded query syntax. OpenAlex documents
`search` as a stemmed text search supporting Boolean operators and quoted
phrases, and `search.exact` as an unstemmed text search. Wildcard expansion
using `*` was not documented.

Accordingly, OpenAlex queries Q13-Q17 were amended before retrieval to replace
wildcard shorthand with explicit lexical variants and to use the documented
`search` parameter.

The PubMed and bio.tools query definitions were not changed.

No formal search results had been retrieved or screened before this amendment.
The original pre-retrieval protocol remains preserved in Git history at commit
`f3ff6a3bb216e170c2a62cdfd3931a80f0c3596b`.

This amendment changes query syntax only and does not change the prespecified
search concepts, eligibility criteria, analytical roles, or benchmark
eligibility criteria.

## Amendment 02 — Harmonisation of OpenAlex search field

**Timing:** after retrieval attempt 01 and before record screening,
eligibility assessment, capability classification, or tool selection.

Retrieval attempt 01 completed successfully for all 18 queries across PubMed,
OpenAlex, and bio.tools. All 54 source-query retrievals were complete and all
reported counts matched retrieved counts.

Inspection of aggregate retrieval counts, before screening any individual
records, identified a systematic database-scope mismatch. The prespecified
PubMed queries searched Title/Abstract fields, whereas the OpenAlex `search`
parameter searched title, abstract, and full text.

This produced 33,217 OpenAlex candidate rows compared with 718 PubMed and
498 bio.tools rows. OpenAlex Q16 alone returned 17,179 records and Q11
returned 6,573 records. The resulting corpus contained 34,433 candidate rows
and 31,349 deduplicated records.

To harmonise bibliographic search scope across PubMed and OpenAlex, the
OpenAlex implementation will therefore be amended to search title and abstract
only. The 18 prespecified concepts, PubMed queries, bio.tools queries,
eligibility criteria, and benchmark criteria remain unchanged.

No candidate records from retrieval attempt 01 were screened before this
decision. Retrieval-attempt metadata, query counts, corpus checksums, and the
console-log checksum are retained in the repository audit record.

### Implementation of Amendment 02

The amended OpenAlex searches use OpenAlex Query Language (OQL) at the API
root. Each bibliographic concept query is expressed as:

`works where title/abstract has (<prespecified Boolean concept expression>)`

This limits OpenAlex bibliographic retrieval to title and abstract text while
preserving the 18 previously defined search concepts. Quoted phrases remain
exact phrases and unquoted terms use OpenAlex's documented stemmed search
behaviour.

All 18 amended OQL expressions will be passed through the OpenAlex `/query`
translation/validation endpoint before retrieval. This endpoint validates the
query without executing it against the search index.

The OpenAlex retrieval implementation is also changed from the classic
`/works?search=` interface to the API-root `?oql=` interface with cursor
pagination. No PubMed or bio.tools search definition is changed.

## Amendment 03 — Generic high-recall search expansion

**Timing:** after completion of the frozen seed-recovery diagnostic and before
formal eligibility screening, capability classification, or benchmark
selection.

The pre-search seed registry contained 14 tools classified prospectively as
direct, near-direct, or diagnostic-panel comparator candidates. A deterministic
name-recovery diagnostic, whose implementation was committed before execution,
found candidate name matches for 4 of these 14 tools (28.6%).

Candidate name recovery is not equivalent to confirmed tool recovery, and the
diagnostic was not used to make inclusion or exclusion decisions. However, the
low recovery demonstrated that the original exact-phrase-oriented search had
insufficient sensitivity to serve as the sole discovery mechanism for the
comparative software landscape.

A single supplementary high-recall search expansion will therefore be
performed before formal screening.

The expansion will:

1. use generic analytical concepts rather than software or author names;
2. retain title/abstract restriction for bibliographic databases;
3. broaden vocabulary for clade/lineage markers, branch-event reconstruction,
   ancestral reconstruction, phylogenetic genotyping, and recurrent/homoplasic
   variation;
4. be defined and committed before its retrieval results are observed; and
5. be merged with the previously frozen formal corpus without deleting
   provenance from either search stage.

The expansion will be performed once. Search terms will not subsequently be
retuned to maximise recovery of the seed registry. Any known relevant methods
not retrieved after this generic expansion will instead be handled through the
already-prespecified backward/forward citation-chaining stage and documented
accordingly.

No formal record screening, software-landscape inclusion/exclusion decisions,
capability classification, or benchmark selection had been performed before
this amendment.

## Amendment 04 — PubMed retrieval partitioning above 10,000 records

**Timing:** after failed high-recall retrieval Attempt 03 and before any
screening, eligibility assessment, capability classification, or benchmark
selection.

The frozen high-recall retrieval implementation failed closed on PubMed query
HR05 because PubMed reported 12,654 matching records. The implementation
allowed a maximum of 10,000 PubMed ESearch identifiers per query, consistent
with the PubMed ESearch retrieval ceiling.

This failure does not motivate any change to the scientific search expression.
The five high-recall concept queries therefore remain unchanged.

To permit complete retrieval of a PubMed query returning more than 10,000
records, the PubMed retrieval implementation will be amended to partition the
result set deterministically by PubMed Entry Date (EDAT).

The amended behaviour will be:

1. execute the original unmodified PubMed query and record its reported count;
2. if the reported count is <=10,000, retain the existing retrieval behaviour;
3. if the reported count is >10,000, retain the original query expression and
   recursively subdivide retrieval using `datetype=edat` with non-overlapping
   `mindate` and `maxdate` intervals;
4. bisect date intervals deterministically until every terminal interval
   reports <=10,000 records;
5. retrieve all PMIDs from every terminal interval;
6. require the sum of terminal interval counts to equal the count reported by
   the original unpartitioned query;
7. require the number of retrieved PMIDs and the number of unique PMIDs both
   to equal that original reported count;
8. fail closed if a single-day EDAT interval still exceeds 10,000 records, if
   interval counts do not reconcile, if duplicate PMIDs occur across
   non-overlapping intervals, or if any PubMed summary record is missing; and
9. retain the partition responses and partition metadata in the raw retrieval
   archive for audit.

EDAT is used only as a retrieval partition and is not an additional scientific
eligibility or search criterion. The original Title/Abstract query remains
unchanged.

A broad EDAT envelope will be used for partitioning. Before record retrieval,
the count within that envelope must equal the count from the original
unbounded query. If it does not, retrieval will stop rather than silently
exclude records.

The previously frozen OpenAlex and bio.tools retrieval implementations are
unchanged.

No records from failed Attempt 03 were screened or used for inclusion,
exclusion, capability classification, or benchmark selection.

## Amendment 05 — merged seed-recovery ordering validation

**Timing:** recorded after execution of the prespecified merged-universe
seed-recovery diagnostic and before any modification of validation code,
human confirmation, eligibility screening, capability classification, or
citation chaining.

The production diagnostic completed successfully, but an auxiliary
byte-for-byte comparison of its formal-stage candidate-match projection against
the earlier formal-search output failed.

A read-only differential audit demonstrated that the two outputs contain the
same 29-row multiset with zero missing and zero extra row occurrences. The
difference consists solely of the reversed order of two SNPPar OpenAlex Q11
records (`W3041660225` and `W4225492844`).

The original frozen checker sorts candidate matches by seed tool, source,
case-folded title, and query ID. Those two records are tied on every field in
that sort key, so Python's stable sort preserves their pre-existing input
order. The deterministic merged candidate universe supplies the tied records
in the opposite order.

Full-row deterministic canonicalization produces identical formal-stage
content (SHA-256
`7b00244753bbdc8b19637dfcc2bab96ba77633ea649a887a2b9203462fc20c14`).

Accordingly, the reproduction criterion for this ordering tie is clarified as
exact row-multiset equality plus byte-identical deterministic canonicalization,
rather than byte identity under an incomplete historical sort key.

This amendment does not change the seed registry, aliases, normalization,
phrase matching, uniqueness definition, recovery status, search expressions,
merged search universe, or generated production diagnostic. The production
diagnostic is retained unchanged.

Search retuning remains prohibited. Candidate matches remain pending human
confirmation.

## Amendment 06 — citation-chain anchor screening

**Timing:** frozen after completion of merged-universe seed-name recovery and
before human confirmation of candidate matches, software-landscape screening
of candidate anchors, primary-anchor selection, or any backward/forward
citation retrieval.

The original protocol specifies backward and forward citation chaining from
**included direct and near-direct methods**. Candidate-name recovery alone does
not establish either inclusion or analytical role.

To operationalize that requirement without selecting tools ad hoc, initial
anchor screening is restricted to all prespecified seed tools that:

1. were assigned `direct_candidate` or `near_direct_candidate` before the
   formal search; and
2. were recovered by candidate-name matching in the frozen merged search
   universe.

Exactly nine seed tools meet this mechanical rule.

Each is evaluated using the already-frozen software-landscape eligibility
criteria and primary/official evidence. Tool identity, landscape inclusion,
direct/near-direct role, and canonical primary publication must all be
established before a tool may become a citation-chain anchor.

Candidate name matches may be rejected as false positives. A failure to become
a citation-chain anchor does not by itself exclude a tool from the software
landscape.

No citation retrieval occurs until the nine-row anchor-screening table has been
completed and frozen.

This operationalization does not modify the completed search strategies or
permit search retuning.

## Amendment 07 — citation-anchor TSV serialization correction

**Timing:** recorded immediately after freezing the citation-chain anchor
screening procedure and before any human confirmation, landscape screening,
primary-source assessment, anchor selection, or citation retrieval.

The initial nine-row pre-screening TSV placed the empty `notes` field as its
final column. Consequently, each unscreened data row ended with a literal tab,
which was reported as trailing whitespace by `git diff --check`.

This amendment changes only TSV serialization: the empty `notes` column is
moved immediately before the non-empty `citation_chain_anchor_decision`
column. All nine records and every parsed field value are unchanged.

No identity status, eligibility criterion, landscape decision, analytical
role, bibliographic anchor, screening note, or citation-chain decision was
modified. All nine candidates remain completely unscreened and all
citation-chain anchor decisions remain `pending`.

## Amendment 08 — direct and near-direct role rubric

**Timing:** frozen before any of the nine citation-anchor candidates received
a final human-confirmed identity, software-landscape eligibility decision,
evidence-supported analytical role, canonical publication anchor, or
citation-chain decision.

The original protocol distinguishes direct and near-direct methods but did not
operationally define the boundary between those labels.

The role distinction is therefore frozen against the analytical endpoints,
rather than against particular tool identities.

A method is `direct` when its documented first-class output includes either
(1) clade-exclusive/fixed sequence-state classification or (2) sequence-state
change/substitution assigned to a phylogenetic branch or edge.

A method is `near_direct` when it provides closely related ancestral-state,
ancestral-sequence, node-associated SNP, or phylogenetic-state output from
which such an endpoint could be derived, but does not itself document the
endpoint as a first-class output.

The complete rule is retained in `CITATION_ANCHOR_ROLE_RUBRIC.md`.

Seed-registry roles remain provenance only. They do not determine the final
evidence-supported role.

This clarification changes no search result, seed-recovery result, eligibility
criterion, capability result, benchmark decision, or citation-chain decision.

## Amendment 09 — search-parameter rationale and completeness validation

**Timing:** frozen after completion of the formal and generic high-recall
database searches and citation-anchor screening, but before any backward or
forward citation-chain retrieval.

The database search expressions are not asserted to be uniquely optimal.
Because the complete relevant software set is unknown a priori, such an
optimality claim cannot be established at query-design time.

The search instead follows a staged validation design:

1. analytical concepts were defined before formal screening;
2. the pre-search seed registry informed vocabulary but not final inclusion;
3. the original exact-phrase-oriented search was executed across PubMed,
   OpenAlex, and bio.tools;
4. a frozen pre-screening sensitivity diagnostic demonstrated inadequate
   recovery of prespecified priority candidates;
5. one generic high-recall expansion was defined and committed without software
   names or author names;
6. no subsequent query retuning was permitted; and
7. final search performance will be measured against the completed
   evidence-supported direct/near-direct landscape after citation chaining.

Because seed knowledge contributed to search vocabulary, seed recovery is
explicitly treated as a development-set diagnostic rather than an unbiased
estimate of recall.

The final validation will report relative recall of the formal search,
high-recall search, their union, source-specific and query-family contribution,
coverage of methods absent from the original seed registry, and structured
analysis of any methods found only through citation chaining.

These endpoints are frozen in
`SEARCH_COMPLETENESS_VALIDATION_PLAN.md` before citation results are observed.

Results of this validation will not be used to modify the primary search
corpus.

## Amendment 10 — iterative dual-source citation chaining

**Timing:** frozen after source-backed initial citation-anchor screening and
search-parameter validation planning, but before retrieval of any backward or
forward citation neighbourhood.

Citation chaining is operationalized as iterative bidirectional graph
traversal rather than a single citation hop.

Every eligible direct/near-direct method discovered during a completed wave
becomes a next-wave anchor once its canonical primary publication has been
established. Newly discovered anchors are not expanded within the wave in which
they are found.

Chaining continues until a complete wave yields zero new eligible
direct/near-direct methods requiring expansion.

To reduce dependence on a single citation graph, citation edges are retrieved
from both OpenAlex Works and OpenCitations Index v2. Their union defines the
citation discovery set and source provenance is retained for every edge.

No citation-count, publication-date, language, publication-type, software-name,
title-keyword, or abstract-keyword filter is applied before record screening.

A wave cannot be declared complete while citation retrieval, record screening,
candidate-method assessment, or canonical-anchor determination remains
unfinished.

Citation chaining cannot alter the already-frozen formal or high-recall search
expressions. Search misses identified during chaining are retained for the
prespecified final completeness and miss analysis.

The complete operational rules are frozen in
`CITATION_CHAINING_PROTOCOL.md`.

## Amendment 11 — citation-wave retrieval implementation

**Timing:** frozen after the iterative dual-source citation-chaining protocol
and before the first production citation API request.

The Wave citation retriever is implemented for the two prespecified citation
sources.

OpenAlex anchors are resolved from DOI. Backward edges use the resolved Work's
`referenced_works` relation and forward edges use the Works `cites` filter with
cursor pagination.

OpenCitations Index v2 uses its `references` and `citations` operations for
backward and forward chaining respectively.

Retrieval is fail-closed. The implementation requires a terminal status for
each anchor × source × direction combination and requires available reported
counts to reconcile with retrieved counts.

Raw API responses are retained. Credentials are environment-only and are not
written to outputs.

Offline regression tests cover identifier normalization, OpenCitations PID
parsing, response-shape handling, OpenAlex backward retrieval, OpenAlex
forward cursor pagination, OpenCitations bidirectional retrieval, terminal
status completeness, and fail-closed count behaviour.

The regression suite makes no network requests.

No citation results had been retrieved when this implementation was frozen.

## Amendment 12 — independent OpenCitations count reconciliation

**Timing:** recorded after freezing the first citation-wave retrieval
implementation but before any production citation API request.

A pre-production implementation audit identified that OpenAlex retrieval had
an independent completeness check but the initial OpenCitations implementation
set `reported_count` equal to the number of rows returned by the citation-data
endpoint. That value could not independently detect an incomplete response.

OpenCitations Index v2 provides separate `reference-count` and
`citation-count` operations. The retriever is therefore hardened so that each
backward/forward OpenCitations retrieval first obtains the independently
reported count and then requires the corresponding `references` or
`citations` response to contain exactly that many citation rows.

A mismatch fails closed.

If the count endpoint returns HTTP 404 the anchor/direction is recorded as
`not_indexed`. If the count endpoint resolves the anchor but the corresponding
citation-data endpoint returns HTTP 404, retrieval fails rather than
interpreting the result as zero citations.

Offline regression tests now include valid count reconciliation and an
explicit count-mismatch failure case.

This change affects retrieval validation only. It changes no citation source,
anchor, search criterion, screening criterion, scientific filter, or
citation-chaining stopping rule.

No production citation result had been observed when this hardening was
specified.

## Amendment 13 — OpenAlex credential handling

**Timing:** recorded after freezing and independently hardening the
citation-wave retrieval implementation, but before any production citation
API request.

A pre-production credential-safety review identified that the initial
citation retriever supplied `OPENALEX_API_KEY` as an OpenAlex URL query
parameter. Although successful response files did not serialize request URLs,
a terminal request exception could include the URL in console output and
therefore risk exposing the credential.

The OpenAlex API key is therefore moved from the request URL to the HTTP
`Authorization: Bearer` header, matching the credential-handling pattern
already used by the frozen Experiment 07 OpenAlex database-search retrievers.

Offline tests require that the credential is absent from generated URLs and
present in the request header.

This change affects authentication transport only. It changes no API source,
query, citation edge, anchor, count reconciliation, scientific filter,
screening criterion, or stopping rule.

No production citation API request had occurred when this correction was
specified.

## Amendment 14 — resolution of OpenAlex credential static-check false positive

**Timing:** recorded after credential hardening and its subsequent read-only
audit, but before any production citation API request.

An auxiliary static check intended to verify removal of the OpenAlex API key
from request URLs searched the complete Python source for the literal substring
`api_key=`. It reported a failure because normal Python keyword-argument syntax
in the internal call `api_key=api_key` contains the same substring.

A read-only AST and runtime audit demonstrated that this was a false positive:

1. neither OpenAlex URL-construction function accepts an API-key argument;
2. no `build_url()` parameter dictionary contains an `api_key` key;
3. the key is supplied to OpenAlex requests through HTTP `Authorization`
   headers;
4. runtime-generated OpenAlex URLs contain no API-key parameter; and
5. the frozen offline retrieval regression suite remains fully passing.

The credential-handling implementation itself therefore required no further
change.

The audit is retained under
`audit/openalex_credential_static_check/`.

No production citation retrieval had occurred when this resolution was
recorded.

## Amendment 15 — Wave 0 Attempt 01 pre-request environment failure

**Timing:** recorded immediately after the first production invocation of the
Wave 0 citation retriever and before any successful production citation
retrieval.

Attempt 01 terminated with:

`ERROR | OPENALEX_API_KEY is required`

The invoking shell contained a populated `OPENALEX_API_KEY` shell variable,
but a post-failure audit confirmed that the variable was absent from the child
process environment (`os.environ`). The failure is therefore consistent with
the variable not having been exported.

The retriever checks this requirement before creating the output directory and
before performing any citation API request. No Wave 0 result directory was
created and no citation result was observed.

The failed execution is retained under
`audit/citation_wave_0_attempt_01_env/`.

The retriever, citation protocol, anchors, search corpus, and scientific
criteria are unchanged. A subsequent production attempt is permitted after
exporting the existing shell variable to the child-process environment.

## Amendment 16 — Wave 0 Attempt 02 malformed credential failure

**Timing:** recorded immediately after production Wave 0 Attempt 02 and before
any subsequent citation retrieval.

After Attempt 01 established that `OPENALEX_API_KEY` had not been exported,
the existing non-empty shell variable was exported and Attempt 02 was started.

Attempt 02 failed during construction of the OpenAlex HTTP Authorization
header with `ValueError: Invalid header value`.

The contemporaneously preserved traceback records that the rejected header
value began with `Bearer echo` and contained carriage-return-delimited shell
command text including `export OPENALEX_API_KEY`. This establishes that the
exported value was malformed rather than a valid single-line API credential.

A later audit found that `OPENALEX_API_KEY` was no longer populated. That later
environment state is not used to reconstruct the historical value; the failure
classification relies on the contemporaneous execution log.

The exception occurred in `http.client.putheader()` before HTTP transmission.
The audited production output contains zero result files and no usable citation
response or citation record was observed.

The failed execution and partial-output inventory are retained under
`audit/citation_wave_0_attempt_02_invalid_credential/`.

No retrieval implementation, citation source, anchor, scientific criterion,
search expression, or stopping rule was changed.

A subsequent production attempt is permitted only after supplying the actual
OpenAlex API key as a valid single-line environment credential.

## Amendment 17 — Wave 0 Attempt 03 incomplete HTTP response

**Timing:** recorded immediately after Wave 0 production Attempt 03 and before
any retry, reconciliation, citation screening, or scientific use of its
partial output.

Attempt 03 successfully reached OpenAlex and OpenCitations and retrieved
multiple raw citation responses. It later failed while reading the
OpenCitations forward-citation response for Wave 0 anchor W0A07 (PAML).

Python raised `http.client.IncompleteRead`: 139,129 bytes had been received and
4,673,415 additional bytes were expected from the response body.

The corresponding OpenCitations forward-count request had completed, but the
forward citation-data response was not written because `response.read()` did
not complete. Wave 0 anchor W0A08 had not yet started.

All successfully written raw responses were validated and preserved
byte-for-byte in the Attempt 03 audit. The partial retrieval is explicitly
excluded from screening and scientific analysis.

This failure exposes a transport-robustness gap in the retriever:
`http.client.IncompleteRead` was not among its retryable exceptions.

Any subsequent implementation change may add retry handling for this transport
exception but may not alter citation sources, anchors, filters, search
expressions, screening criteria, or the saturation stopping rule.

## Amendment 18 — retry incomplete HTTP response bodies

**Timing:** specified after Wave 0 Attempt 03 was frozen as a failed production
retrieval and before any subsequent Wave 0 production attempt.

Attempt 03 failed because an OpenCitations response terminated before its
declared HTTP body was complete. Python raised
`http.client.IncompleteRead`.

The common JSON fetcher already applied a bounded retry policy to transient URL
errors, timeouts, and JSON decoding failures, but did not include
`http.client.IncompleteRead`.

The implementation is therefore hardened by adding only
`http.client.IncompleteRead` to that existing retryable exception set.

When this exception occurs:

1. the incomplete response body is discarded;
2. no raw response file is written from that incomplete body;
3. the same request is retried from the beginning under the existing retry
   count and backoff policy; and
4. persistent failure remains fail-closed.

Offline regression tests simulate an incomplete first response followed by a
complete second response and verify that exactly the complete response is
written. A second test verifies that repeated incomplete responses exhaust the
bounded retry policy, fail the retrieval, and leave no raw response file.

This patch changes transport robustness only. It does not change citation
sources, citation operations, anchors, count reconciliation, discovery scope,
filters, screening criteria, search expressions, or the saturation rule.

## Amendment 19 — persistent large OpenCitations response failure

**Timing:** recorded immediately after Wave 0 production Attempt 04 and before
any subsequent retry, partitioned retrieval, reconciliation, or citation
screening.

Attempt 04 used the hardened retriever that treats
`http.client.IncompleteRead` as a retryable transient transport error.

The same OpenCitations forward-citation operation for W0A07 (PAML) nevertheless
failed after all five bounded whole-response attempts.

The final attempt received 859,003 bytes before the connection terminated,
with 3,953,541 additional bytes expected.

This demonstrates that bounded repetition of the same large unpartitioned
response is insufficient. Increasing the retry count alone is therefore not
adopted.

The partial response tree is preserved in the Attempt 04 audit and is excluded
from screening and scientific analysis.

A subsequent implementation may partition the same OpenCitations citation
result into deterministic smaller requests, provided that the partition union
is reconciled against the independent citation count, duplicate citation
identities are prohibited, and incomplete coverage fails closed.

No citation source, anchor, scientific filter, search expression, screening
criterion, or saturation rule is changed by this finding.

## Amendment 20 — deterministic OCI partitioning for OpenCitations

**Timing:** frozen after Wave 0 Attempt 04 demonstrated persistent
whole-response failure despite five bounded retries, and before implementation
or production use of any partitioned OpenCitations retrieval.

OpenCitations Index v2 documents result filtering by regular expression and
defines each citation using an Open Citation Identifier (OCI) with numeric
citing and cited components.

Positive-count OpenCitations operations will therefore be retrieved as a
deterministic partition of the OCI identifier space rather than as one
unpartitioned citation-data response.

The root partition is based on the terminal decimal digit of the variable OCI
component:

- citing component for forward citations;
- cited component for backward references.

The ten decimal buckets are mutually exclusive and exhaustive for the
documented OCI lexical form.

A bucket that still exhausts the existing bounded transport retry policy may be
recursively subdivided by the next terminal digit. Subdivision retains an
exact-number child so numeric components shorter than the new suffix depth
cannot be lost.

No biological, bibliographic, temporal, lexical, software-name, or relevance
field participates in partition assignment.

A reconstructed operation is accepted only when every leaf is complete, every
row has a valid OCI belonging to its leaf, no OCI is duplicated across leaves,
and the unique OCI union exactly equals the independently retrieved
citation/reference count.

Failed Attempts 03 and 04 remain audit artefacts only and cannot contribute
citation rows to a later successful Wave 0 result.

The complete design is frozen in `OPENCITATIONS_PARTITIONING_SPEC.md`.

## Amendment 21 — implement deterministic OpenCitations OCI partitioning

**Timing:** implemented after Amendment 20 froze the partition design and
before any further production citation retrieval.

The frozen deterministic OCI-partition design is now implemented.

For every positive OpenCitations independent count, citation data are requested
through ten disjoint terminal-digit OCI root filters. Every successful leaf
validates complete OCI syntax and leaf membership.

A non-exact leaf that exhausts the existing bounded retry policy specifically
because of `http.client.IncompleteRead` is recursively replaced by the frozen
exact-number child and ten next-terminal-digit children.

The implementation uses a 64-digit variable-OCI-component suffix ceiling.
The ceiling is a transport-safety bound only. Reaching it fails closed.

Before implementation, OCI component lengths were inspected structurally in
the frozen Attempt 04 raw-response archive and verified not to exceed this
ceiling. No citation relevance or software content was inspected or used for
partition assignment.

The final reconstructed operation prohibits duplicate OCIs and requires the
number of unique OCI identities to equal the existing independent
citation/reference count exactly.

Zero independent counts terminate without citation-data requests.

Every completed partition leaf is preserved separately and recorded in
`opencitations_partition_leaves.tsv`; each citation edge retains the exact leaf
raw-response path from which it originated.

Offline tests cover:

- root partition exclusivity and exhaustiveness;
- exact-plus-ten recursive child coverage;
- forward versus backward variable OCI components;
- filtered URL construction;
- missing, malformed and out-of-leaf OCI failure;
- duplicate OCI failure;
- independent-count mismatch failure;
- order-independent union reconciliation;
- deterministic leaf execution order;
- retry-exhaustion subdivision;
- recursion-ceiling failure;
- non-IncompleteRead failure without subdivision;
- zero-count short-circuiting; and
- preservation of the pre-existing incomplete-body write protections.

No citation source, anchor, scientific filter, search expression, screening
criterion, comparator role, or saturation rule changed.

## Amendment 22 — Wave 0 Attempt 05 independent-count mismatch

**Timing:** recorded immediately after Wave 0 production Attempt 05 and before
any retry, API diagnostic request, partition modification, reconciliation, or
citation screening.

Attempt 05 was the first production execution using the frozen deterministic
OCI partition implementation.

For W0A07 (PAML) forward citations, all ten root terminal-digit partitions
completed without recursive subdivision.

Every returned OCI was syntactically valid, matched its recorded root
partition, and was unique across the partition union.

The independently retrieved OpenCitations citation-count endpoint reported
12,846 citation relationships, whereas the complete ten-partition union
contained 12,845 unique OCI rows.

The implementation therefore failed closed at the independent count
reconciliation gate.

The cause of the one-record discrepancy is not inferred from the failed
production run. Potential source-state drift, endpoint-semantic differences,
and a countable relationship outside the assumed valid-OCI partition universe
remain separate hypotheses requiring explicit diagnosis.

All Attempt 05 raw responses are preserved for audit and excluded from
scientific screening or method classification.

No citation source, partition rule, search expression, anchor, relevance
criterion, comparator classification, or saturation rule is changed by this
observation.

## Amendment 23 — freeze diagnostic for OpenCitations count mismatch

**Timing:** frozen after Attempt 05 and before any new OpenCitations diagnostic
request or further Wave 0 production attempt.

Attempts 03, 04 and 05 each returned an independent W0A07/PAML forward
citation count of 12,846.

Attempt 05 successfully retrieved all ten frozen terminal-digit OCI root
partitions, yielding 12,845 unique valid OCIs with no duplicates.

The cause of the one-record discrepancy remains unresolved.

A source-forensic diagnostic is therefore frozen before execution. It will
bracket one unfiltered OpenCitations `/citations` request with independent
citation-count requests immediately before and after it.

The citation-data operation will request `text/csv`, a serialization documented
by OpenCitations for its REST API. No filter, relevance criterion, date rule,
software term or other scientific selection will be applied.

The resulting CSV rows will be compared against the exact Attempt-05 OCI union
reconstructed from the committed failed-attempt archive. Empty, malformed or
otherwise nonconforming OCI values will be retained and reported rather than
discarded.

The diagnostic cannot itself be used as the Wave 0 production corpus and does
not alter the exact production completeness gate.

## Amendment 24 — implement frozen OpenCitations count-mismatch diagnostic

**Timing:** implemented after Amendment 23 froze the diagnostic design and
before any diagnostic network request or subsequent Wave 0 production attempt.

A standalone source-forensic retriever now implements exactly the frozen
W0A07/PAML sequence:

1. citation-count JSON;
2. unfiltered citations CSV;
3. citation-count JSON.

The production Wave 0 retriever is unchanged.

Successful response bodies are preserved byte-for-byte only after complete HTTP
transfer. Incomplete bodies are discarded. Transient transport failures use a
bounded five-attempt policy.

The exact Attempt-05 comparator is reconstructed from the committed failed-run
archive and independently required to contain all ten root partitions and
12,845 unique valid OCIs with no duplicates.

CSV analysis retains empty and nonconforming OCI rows, explicitly reports valid
OCI duplicates and both set differences, and never treats the diagnostic as a
production corpus.

Offline end-to-end validation used the real frozen 12,845-OCI Attempt-05 union
plus one synthetic additional OCI. The diagnostic correctly recovered 12,846
unique CSV OCIs and isolated exactly the one synthetic CSV-only relationship.

All offline tests prohibit network access.

No production retrieval, citation search, relevance screening, comparator
classification or saturation rule was changed.

## Amendment 25 — unfiltered CSV diagnostic fails bounded transport

**Timing:** recorded immediately after the first execution of the frozen
OpenCitations count-mismatch diagnostic and before any retry, diagnostic
redesign, or subsequent Wave 0 production attempt.

The pre-diagnostic W0A07/PAML citation-count request completed successfully.

The next frozen operation requested the same unfiltered OpenCitations
`/citations` result as CSV rather than JSON.

That CSV response still failed with `http.client.IncompleteRead` after all five
bounded whole-response attempts.

The incomplete body was never written as a successful response.

The frozen post-count operation was consequently not attempted, and no
diagnostic interpretation was produced.

This establishes that changing serialization from JSON to CSV is insufficient
to solve the large unfiltered-response transport problem for this target.

The result does not resolve the one-record count discrepancy and does not alter
the production completeness gate, citation partition design, literature search,
screening criteria, comparator classifications, or citation-chaining saturation
rule.

## Amendment 26 — freeze OCI-independent creation-string diagnostic

**Timing:** frozen after the unfiltered CSV diagnostic failed bounded transport
and before any second diagnostic network request.

Offline inspection of the frozen Attempt-05 W0A07 forward corpus showed that
`creation` cannot safely be treated as a strict complete calendar date.
The archived data include complete dates, reduced-precision year-month values,
reduced-precision year values, and empty values.

The second diagnostic therefore treats `creation` only as an opaque raw string.

Its root consists of explicit empty and non-digit buckets plus ten digit-prefix
regular-expression buckets. A large digit/hyphen prefix bucket may be
recursively subdivided into an exact-prefix child, ten decimal continuations,
a hyphen continuation and an unexpected-character continuation.

This partition is independent of OCI and preserves reduced-precision and
unexpected creation strings.

The independent citation count is retrieved immediately before and after the
partition sequence. Returned row counts, complete row duplicates, OCI syntax,
OCI duplicates and exact set differences relative to Attempt 05 are all
reported separately.

No source result from this diagnostic is itself a production Wave 0 corpus,
and no literature-search or screening rule is changed.
