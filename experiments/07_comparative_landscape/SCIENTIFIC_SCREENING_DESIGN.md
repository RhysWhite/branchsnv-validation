# Experiment 07 scientific screening design

Status: `FROZEN_PRE_IMPLEMENTATION`

## 1. Purpose

This stage operationalizes the already-frozen Experiment 07 scientific
screening rules after completion of publication-identity and metadata
reconciliation.

It does not change:

- the scientific scope;
- Q01-Q18;
- HR01-HR05;
- the database-search corpus;
- the Wave 0 citation corpus;
- software-landscape eligibility;
- analytical-role definitions;
- direct/near-direct definitions;
- benchmark eligibility criteria; or
- the citation-chain saturation rule.

No scientific screening decision has been made at this design freeze.

## 2. Screening universe

The baseline scientific-screening universe contains exactly 95,113 stable
screening entities:

- 94,898 `publication` entities; and
- 215 `software_registry` entities.

The 1,342 post-retrieval reconciliation components are a metadata/identity
attention overlay on this universe.

They are not a replacement screening universe.

Every one of the 95,113 screening entities must retain stable identity and
discovery provenance throughout screening.

## 3. Screening unit

The screening unit is the frozen stable screening entity.

For publication entities, the unit is the conservatively reconciled
publication/version identity.

For software-registry entities, the unit is the frozen registry identity.

A screening unit is not:

- a citation edge;
- a citation-provenance row;
- a source-query hit;
- a software-name match;
- a seed-registry entry; or
- necessarily one frozen merged-search deduplication key.

Publication and software-registry entities are not automatically merged.

Multiple screening entities may later support the same source-backed
software/method identity.

## 4. Six analytical roles

The software landscape retains the six protocol-defined analytical roles:

1. `clade_lineage_marker_discovery`
2. `branch_change_reconstruction`
3. `homoplasy_recurrent_state_analysis`
4. `marker_deployment_genotyping`
5. `general_phylogenetic_parsimony_infrastructure`
6. `upstream_variant_recombination_phylogeny_workflows`

These correspond exactly to:

1. clade/lineage marker discovery;
2. branch-change reconstruction;
3. homoplasy/recurrent-state analysis;
4. marker deployment/genotyping;
5. general phylogenetic/parsimony infrastructure; and
6. upstream variant-calling, recombination, and phylogeny workflows.

The six-role scope is not altered during screening.

## 5. Record-level screening rule

A screening entity advances to source-backed software/method assessment when
its available title, name, abstract, description, metadata or accessible
source material could plausibly describe, introduce, substantially extend or
document reusable analytical software/method relevant to one or more of the
six analytical roles.

Uncertainty is resolved toward retention for source checking.

No entity may be excluded because of:

- discovery route;
- citation frequency;
- number of anchors;
- provider count;
- seed status;
- unfamiliar software name;
- organism specificity alone;
- historical status alone;
- lack of current maintenance alone;
- web-only availability alone; or
- inability to execute in the current environment alone.

No keyword, software-name, citation-count or machine-learning prefilter may
silently remove entities from the screening universe.

All 95,113 entities must receive an explicit screening-process state.

## 6. Record-level process states

The production screening table must distinguish process state from scientific
decision.

Permitted `screening_state` values are:

- `blocked_metadata`
- `ready`
- `awaiting_source_escalation`
- `complete`

`blocked_metadata` and `awaiting_source_escalation` are not scientific
exclusions.

A row with either state is not counted as scientifically screened.

## 7. Completed record-level decisions

A completed screening entity has exactly one `record_decision`:

- `retain_for_method_assessment`
- `exclude`

No third completed scientific decision is introduced.

When evidence remains uncertain after the permitted record-level assessment,
the frozen high-recall rule applies: uncertainty is resolved toward
`retain_for_method_assessment`, not exclusion.

A retained entity is a candidate method/software record.

Retention at record level does not itself:

- confirm a software/method identity;
- establish software-landscape eligibility;
- assign a direct/near-direct role;
- establish benchmark eligibility; or
- make the record a citation anchor.

## 8. Frozen exclusion criteria

A record-level `exclude` decision must be supported by at least one explicit
frozen exclusion criterion.

The production reason codes are:

- `application_only_no_reusable_method`
- `unrelated_variant_or_data_type`
- `duplicate_record_same_method_no_distinct_capability`
- `unsupported_by_primary_or_stable_authoritative_source`

They correspond exactly to the protocol-defined exclusions:

1. biological application only, with no identifiable analytical software or
   reusable method;
2. unrelated variant classes or data types without a relevant
   sequence/phylogenetic capability;
3. duplicate publication or software record for the same method without a
   distinct relevant capability; or
4. inability to support the method by a primary publication or stable
   authoritative documentation.

The duplicate-record reason requires source-backed method identity evidence.
It must not be inferred merely from title similarity, identifier conflict,
discovery duplication, or name matching.

The unsupported-source reason requires an evidence attempt sufficient to
establish that support is unavailable; missing metadata alone cannot satisfy
that exclusion criterion.

Every exclusion must retain operator/batch provenance and a human-readable
note or evidence reference sufficient to audit the decision.

## 9. Metadata screenability

### 9.1 Publication entities

A publication entity is presently screenable when:

1. it has a stable screening-entity identifier or explicit conflict-hold
   identifier; and
2. it has usable non-empty bibliographic title evidence.

After completed metadata reconciliation:

- 94,414 publication entities satisfy the present title-evidence gate;
- 482 remain `title_unresolved`; and
- 2 remain `title_conflict_hold`.

The 484 unresolved/conflicted-title entities begin screening implementation as
`blocked_metadata`.

They are not excluded.

### 9.2 Equivalent title variants

The eight `title_equivalent_variants` components are screenable.

All exact title variants remain preserved.

No preferred display spelling is inferred merely for screening.

### 9.3 Identifier conflicts

The 117 `identifier_conflict_hold` components remain conflict-held.

Identifier conflict is not itself an exclusion criterion.

Where sufficient stable entity identity and title evidence exist, record-level
screening may proceed.

However, an identity conflict that can affect:

- the scientific disposition;
- duplicate-record interpretation;
- method identity;
- canonical-publication assignment; or
- anchor determination

remains a baseline-completion blocker until explicitly resolved or adjudicated
as non-blocking.

No identifier winner may be invented during screening.

### 9.4 Software-registry entities

All 215 software-registry screening entities remain independent screening
units.

They may be assessed using:

- registry name;
- registry description;
- documented functions;
- linked documentation; and
- accessible primary/official sources.

Absence of a bibliographic publication title is not a screening blocker for a
software-registry entity.

## 10. Metadata/source escalation

If frozen title/metadata are insufficient for a defensible scientific
disposition, the entity enters `awaiting_source_escalation`.

Permitted escalation evidence follows the frozen protocol and may include:

- abstract;
- primary method publication;
- accessible publication source;
- stable authoritative software documentation;
- official software documentation; or
- official source repository.

Escalation is part of screening and must be logged separately from the
metadata-reconciliation archive.

Raw retrieval evidence is not edited.

Source escalation must retain at minimum:

- screening-entity identifier;
- escalation reason;
- source class;
- source locator or stable identifier;
- evidence accessed;
- operator or batch provenance; and
- resulting screening state/decision.

Missing metadata never becomes an exclusion reason merely because escalation
was required.

## 11. Historical screening log

The existing historical `screening_log.tsv` remains unchanged and empty.

It is not silently repurposed.

The production implementation must create a new screening table.

## 12. Minimum baseline-screening table

The new baseline screening table must retain at minimum:

- `screening_entity_id`
- `screening_entity_class`
- `publication_reconciliation_key`
- `database_dedup_keys`
- `biotools_id`
- `citation_provenance_ids`
- `discovery_stages`
- `citation_wave_provenance`
- `title_or_software_name`
- `title_variants`
- `year`
- `doi`
- `pmid`
- `openalex_id`
- `omid`
- `identity_attention_status`
- `metadata_screenability`
- `screening_state`
- `record_decision`
- `exclusion_reason_code`
- `candidate_method_flag`
- `evidence_escalation_status`
- `operator`
- `decision_batch`
- `notes`

The implementation may add provenance fields, but it may not remove these
minimum scientific/audit fields.

## 13. Initial screening-state derivation

Before any scientific decision:

- 94,629 baseline entities are presently screenable from frozen metadata;
- 484 publication entities begin as `blocked_metadata`.

The 94,629 presently screenable entities comprise:

- 94,414 publication entities; and
- 215 software-registry entities.

The 484 metadata-blocked entities comprise:

- 482 `title_unresolved` publication entities; and
- 2 `title_conflict_hold` publication entities.

These are operational queue states, not inclusion/exclusion results.

## 14. Source-backed software/method assessment

Source-backed method assessment is a separate table/stage from record-level
screening.

Only entities with record decision `retain_for_method_assessment` advance.

Multiple retained screening entities may support one software/method identity.

All supporting screening-entity provenance must remain attached to the
resulting method assessment.

## 15. Method identity

Permitted `method_identity_status` values are:

- `confirmed`
- `false_positive_only`
- `not_established`

These values retain the previously frozen citation-anchor identity semantics.

Software-name equality alone cannot establish method identity.

## 16. Landscape eligibility

For each source-backed candidate method, four criteria are evaluated
independently:

1. publication or stable public documentation describing the method exists;
2. identifiable software implementation exists or existed;
3. the tool operates on sequence, SNP, genotype or phylogenetic data; and
4. the tool addresses at least one of the six frozen analytical roles.

Each criterion has exactly one value:

- `yes`
- `no`
- `not_established`

The `landscape_decision` is:

- `include` only when all four criteria are `yes`;
- `exclude` when at least one criterion is demonstrably `no`; or
- `pending` when necessary evidence remains `not_established`.

An exclusion reason must be explicit.

## 17. Analytical-role evidence

For landscape-included methods, role membership among the six protocol roles
must be supported by primary or official evidence.

Capabilities and roles must not be inferred from:

- tool name;
- seed-registry classification;
- search-query match;
- citation count;
- reviewer familiarity; or
- anticipated benchmark performance.

## 18. Direct / near-direct classification

The frozen directness values are:

- `direct`
- `near_direct`
- `other_landscape_role`
- `not_established`

`direct` requires documented first-class D1 and/or D2 output.

`near_direct` requires documented operation in the same analytical
neighbourhood without D1/D2 as first-class output.

The possibility of deriving D1/D2 through user post-processing does not by
itself make a method `direct`.

Directness is separate from landscape eligibility and benchmark eligibility.

## 19. Benchmark eligibility

Executable benchmark eligibility is not decided during baseline record-level
screening.

Landscape inclusion does not imply benchmark inclusion.

A later frozen stage must apply the already-existing benchmark criteria.

No method receives a positive or negative benchmark score during this
screening stage.

## 20. Canonical publication decisions

For every included `direct` or `near_direct` method, canonical-publication
status must be one of:

- `established`
- `no_distinct_primary_publication`
- `unresolved`

Canonical publication selection is based on method identity and primary-method
relevance, not citation count or convenience.

A software-registry entity is never itself a bibliographic citation anchor.

An included direct/near-direct method with
`no_distinct_primary_publication` remains in the software landscape but cannot
generate citation expansion.

`unresolved` blocks the relevant screening/wave completion gate.

## 21. Previously adjudicated Wave 0 anchors

The eight previously frozen Wave 0 anchor methods retain their prior
source-backed adjudications.

Their established canonical publications do not receive duplicate scientific
decisions merely because they are rediscovered in the baseline universe.

All rediscovery provenance is still retained.

Additional screening entities potentially supporting one of those methods must
be linked by source-backed evidence, not name matching alone.

## 22. Wave 1 promotion

No Wave 1 citation retrieval occurs until baseline screening is complete.

A canonical publication is eligible for Wave 1 only when all five frozen
conditions hold:

1. software/method identity is confirmed;
2. landscape decision is `include`;
3. evidence-supported directness role is `direct` or `near_direct`;
4. canonical primary publication is established; and
5. that canonical publication has not previously been citation-expanded.

Promotion is a deterministic consequence of frozen screening/method evidence.

It is not a separate popularity or priority judgment.

## 23. Baseline completion gate

Baseline screening is incomplete while any baseline entity is:

- unreconciled where reconciliation is required;
- in an identity conflict that can affect screening or anchor determination;
- missing required screenable metadata;
- unscreened;
- awaiting required source escalation;
- awaiting required candidate-method assessment; or
- associated with an unresolved direct/near-direct canonical-publication
  decision.

None of these states may be interpreted as citation saturation.

## 24. Saturation

The frozen stopping rule remains:

`0 new eligible direct/near-direct methods requiring citation expansion`

No fixed number of records, methods or citation waves is introduced.

## 25. Order and discovery-route independence

Screening eligibility and scientific decisions must not depend on:

- database-record order;
- citation-row order;
- source order;
- anchor order;
- citation direction;
- discovery route; or
- seed membership.

The screening implementation must preserve stable screening-entity IDs and
complete discovery provenance.

## 26. Required production separation

At minimum, scientific screening implementation must maintain separate
derived artifacts for:

1. baseline screening queue/decisions;
2. source-escalation evidence;
3. source-backed software/method assessments;
4. method-level evidence;
5. canonical-publication decisions; and
6. Wave 1 promotion candidates.

A manifest and checksum ledger are also required.

Record-level and method-level decisions must not be collapsed into one
ambiguous status field.

## 27. Prohibited behaviour

The implementation must fail closed rather than:

- alter the frozen discovery corpus;
- alter Q01-Q18 or HR01-HR05;
- modify retrieval or reconciliation evidence;
- silently drop screening entities;
- treat metadata absence as scientific exclusion;
- treat provider `not_found` as scientific exclusion;
- treat identifier conflict as scientific exclusion;
- infer publication identity from title similarity;
- infer software identity from name matching alone;
- use citation count as an eligibility criterion;
- use seed status as an eligibility criterion;
- auto-promote a candidate before method assessment is complete;
- construct Wave 1 before the baseline completion gate passes;
- treat unfinished screening as citation saturation; or
- rank tools by preference or anticipated performance.

## 28. Scientific boundary at design freeze

At this freeze:

- baseline screening universe = 95,113;
- scientific screening decisions = 0;
- method-level assessments = 0;
- new role assignments = 0;
- Wave 1 promotions = 0;
- component merge remains unchanged from reconciliation;
- `screening_log.tsv` remains empty.

## 29. Next gate

The next gate is:

`IMPLEMENT_FROZEN_SCIENTIFIC_SCREENING_INFRASTRUCTURE_WITHOUT_MAKING_DECISIONS`

The implementation stage must first construct and validate the full
95,113-row screening queue, evidence schemas and fail-closed state machinery.

It must not make include/exclude decisions during implementation validation.
