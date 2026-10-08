# Experiment 07 T000002 authoritative-source retrieval and escalation-resolution design

Status: `FROZEN_PRE_IMPLEMENTATION`

## Purpose

This design defines how authoritative evidence will be acquired for the ten
T000002 records currently awaiting source escalation.

Parent T000002 completion commit:

`8cfefe12c6c300c2f9b2ad70683274f5d2976a72`

No network retrieval, terminal scientific decision or production-ledger
mutation is authorized by this design.

## Frozen parent state

Production events:

`11`

Production ledger SHA-256:

`fb90d762d4fe9e81410816fe9403c735de138fe1614c11cb83993b40f2c63dff`

Derived state:

- ready: 94,611
- awaiting source escalation: 10
- complete: 1
- blocked metadata: 484

The ten unresolved events are E000000002-E000000011.

## Exact target

Canonical target identity SHA-256:

`5970e1ec739b5b01c546e526c402d2f3a6e06e8f43aef0bfcd375e692bc2ab5e`

Targets:

- position 2 / E000000002: `publication_component:citation:publication:doi:10.1001/jamanetworkopen.2018.7665` — Risk Assessment After a Severe Hospital-Acquired Infection Associated With Carbapenemase-Producing Pseudomonas aeruginosa
- position 3 / E000000003: `publication_component:citation:publication:doi:10.1001/jamanetworkopen.2020.24191` — Analysis of Genomic Characteristics and Transmission Routes of Patients With Confirmed SARS-CoV-2 in Southern California During the Early Stage of the US COVID-19 Pandemic
- position 4 / E000000004: `publication_component:citation:publication:doi:10.1001/jamanetworkopen.2026.17898` — Hospital Environment–Associated Sources of Mycobacterium abscessus Infection in Transplant Recipients
- position 5 / E000000005: `publication_component:citation:publication:doi:10.1002/0471142727.mb1901s101` — Detecting the Signatures of Adaptive Evolution in Protein‐Coding Genes
- position 6 / E000000006: `publication_component:citation:publication:doi:10.1002/1873-3468.13356` — Molecular evolution of proteins mediating mitochondrial fission–fusion dynamics
- position 7 / E000000007: `publication_component:citation:publication:doi:10.1002/2211-5463.12843` — Origin and adaptation of green‐sensitive (RH2) pigments in vertebrates
- position 8 / E000000008: `publication_component:citation:publication:doi:10.1002/2211-5463.13555` — Potentially reduced fusogenicity of syncytin‐2 in New World monkeys
- position 9 / E000000009: `publication_component:citation:publication:doi:10.1002/2211-5463.13728` — Insights into the identification and evolutionary conservation of key genes in the transcriptional circuits of meiosis initiation and commitment in budding yeast
- position 10 / E000000010: `publication_component:citation:publication:doi:10.1002/9780470015902.a0020859` — Selection against Amino Acid Replacements in Human Proteins
- position 11 / E000000011: `publication_component:citation:publication:doi:10.1002/9780470015902.a0020859.pub2` — Selection against Amino Acid Replacements in Human Proteins

No record outside B000001 positions 2-11 belongs to this retrieval phase.

## Why retrieval is required

The existing local evidence established bibliographic identity and citation
provenance but was insufficient for terminal scientific screening.

The following are not independently sufficient for a terminal disposition:

- title alone;
- DOI alone;
- PMID alone;
- OpenAlex or Crossref bibliographic metadata;
- citation-list membership;
- search-result snippets;
- citation frequency;
- discovery route.

Failure to retrieve one source is not itself a scientific exclusion.

## Authoritative source classes

- `primary_publication_full_text` — terminal_capable: Official publisher full text or stable public full-text archive of the target publication.
- `primary_publication_abstract` — terminal_capable_if_substantive: PubMed or official publisher abstract when the abstract itself contains sufficient substantive evidence.
- `official_supplementary_material` — terminal_capable: Supplementary methods, software descriptions, data or other files supplied by the publication/publisher.
- `official_software_repository` — terminal_capable: Repository controlled by the method authors/project and linked from the publication or another stable authoritative source.
- `official_software_documentation` — terminal_capable: Stable project documentation controlled by the authors or project.
- `official_registry_record` — supporting_or_terminal_capable: Stable software/method registry record with substantive capability documentation and provenance.

A source is terminally useful only when its substantive content supports the
scientific claim being made.

## Retrieval priority

For each target, retrieval should proceed through stable authoritative routes
where available:

1. PMCID or stable public full-text archive;
2. PubMed authoritative record and abstract;
3. official publisher article;
4. official supplementary material;
5. publication-linked official software repository/documentation;
6. stable official software registry record.

Multiple sources may be retained for one record.

Every retrieval attempt, successful or unsuccessful, must be logged.

## Evidence questions

Every record must ultimately be assessed against:

1. Does an identifiable reusable analytical implementation exist or have
   existed?
2. Does it operate on sequence, SNP, genotype or phylogenetic data?
3. Does it perform at least one frozen Experiment 07 landscape role?
4. If another record describes the same method, is there a distinct reusable
   capability?
5. Is the proposed scientific disposition supported by primary or stable
   authoritative evidence?

Retrieval itself does not answer these questions automatically.

Human review remains required.

## Storage model

Untracked production evidence root:

`results/07_comparative_landscape/t000002_authoritative_source_retrieval`

Required artifacts after retrieval implementation:

- `retrieval_manifest.tsv`
- `evidence_assessment.tsv`
- `retrieval_summary.json`
- `checksums.sha256`
- `raw/`

Every obtained payload must have a SHA-256 and byte count.

Access/license restrictions must be recorded.

Restricted source content must not be committed into tracked repository
history.

## Terminal resolution

Retrieval does not itself create terminal events.

After retrieval has been completed and separately frozen, each record receives
human scientific review.

A terminal resolution requires a separately authorized
`superseding_record_decision` that supersedes the current source-escalation
event and records:

`evidence_escalation_status = resolved`

Allowed outcomes remain:

- `exclude`
- `retain_for_method_assessment`

The existing frozen exclusion reason vocabulary is unchanged.

## No forced resolution

If authoritative evidence remains insufficient after documented retrieval
attempts:

- no terminal decision is forced;
- the existing source-escalation event remains current;
- no superseding event is created merely to close the record;
- retrieval completion may still be frozen as complete evidence work.

## Positions 10 and 11

Positions 10 and 11 share a title but have different DOI identities.

This is not enough to assign
`duplicate_record_same_method_no_distinct_capability`.

A duplicate exclusion requires authoritative evidence establishing both:

1. the same underlying method/record relationship; and
2. absence of a distinct reusable capability.

No duplicate decision is preselected.

## Separation of publication and method

A publication that uses genomic or phylogenetic analysis is not automatically
a reusable analytical method.

Use of software does not establish that the publication introduces that
software.

Method relevance, implementation identity and landscape role must each be
source-backed.

## Execution boundary

This design authorizes none of the following:

- network retrieval;
- review-packet terminal edits;
- event-ledger mutation;
- superseding events;
- terminal scientific decisions.

A separate implementation freeze is required before any live source retrieval.

## Next gate

`IMPLEMENT_T000002_AUTHORITATIVE_SOURCE_RETRIEVAL_QUEUE_AND_RUNNER_WITHOUT_NETWORK_EXECUTION`
