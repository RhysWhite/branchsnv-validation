# Experiment 07 scientific decision ledger

## Purpose

This ledger records methodological decisions that can affect discovery,
coverage, classification, or reproducibility in Experiment 07.

The purpose is not to retrospectively claim that every numerical choice was
uniquely optimal. Decisions are instead classified according to their actual
basis:

- **scientific scope** — determined by the analytical question;
- **rule-derived outcome** — a number produced by applying a previously frozen
  rule rather than selected in advance;
- **empirically validated design** — a design whose adequacy was tested using
  prespecified evidence before downstream screening;
- **source-structure constraint** — determined by documented properties of an
  external source or identifier system;
- **operational bound** — a pragmatic implementation limit that does not define
  biological eligibility or comparative conclusions.

Where a choice is operational rather than scientifically unique, that is
stated explicitly. The associated safeguards and residual limitations are
recorded rather than hidden.

This ledger is a methodological audit and clarification. It does not alter the
previously frozen search corpus, eligibility rules, comparator classifications,
citation edges, or citation-chaining saturation rule.

---

## Decision ledger

| Decision | Classification | Basis and justification | Empirical or structural safeguard | Residual limitation |
|---|---|---|---|---|
| Six analytical roles | scientific scope | The study objective is comparison of software relevant to interpretation of sequence variation in a phylogenetic context. The frozen protocol separates clade/lineage marker discovery, branch-change reconstruction, homoplasy/recurrent-state analysis, marker deployment/genotyping, general phylogenetic/parsimony infrastructure, and upstream variant/recombination/phylogeny workflows so that tools with different purposes are not collapsed into one comparison. | Eligibility and benchmark rules were frozen against these roles before formal screening. Direct benchmarking is restricted to shared endpoints. | The taxonomy is a study-scope framework, not a claim that these are the only possible categories of phylogenetic software. |
| 18 initial formal query families | operational decomposition with prospective freeze | The 18 query families were lexical representations of the prespecified analytical roles. The number 18 was not treated as an optimal or exhaustive query count. | Before formal eligibility screening, a frozen seed-recovery diagnostic found candidate-name matches for only 4 of 14 prospectively recorded direct, near-direct, or diagnostic-panel candidates, demonstrating that the initial exact-phrase-oriented search was insufficient as the sole discovery mechanism. | Individual relevant methods may use terminology absent from the initial query vocabulary. This limitation motivated the separate high-recall and citation-chaining stages rather than post hoc expansion of the original 18 queries. |
| PubMed, OpenAlex, and bio.tools as formal database sources | complementary reproducible source design | The sources represent different discovery channels: PubMed is a biomedical and life-sciences bibliographic resource; OpenAlex provides a broad scholarly-works corpus and citation graph; bio.tools is a dedicated registry of bioinformatics software and data resources. The number of databases is not asserted to guarantee completeness. The defining corpus uses sources that can be queried programmatically with retained provenance. | Records are merged across sources rather than requiring agreement between databases. Search completeness is evaluated after the high-recall and iterative citation-chain stages rather than inferred from use of three databases. | All bibliographic and software registries have coverage and metadata limitations. Relevant methods absent from all three databases may still require citation-chain or supplementary discovery. |
| Google Scholar supplementary-only role | reproducibility design | The frozen protocol permits Google Scholar as a supplementary discovery check but does not allow it to define the reproducible search corpus. The primary corpus is defined by the frozen programmatic retrieval procedures with recorded raw responses, counts, manifests, and checksums. | A Google Scholar observation cannot silently modify the frozen database-search corpus. Any method discovered outside the defining corpus must retain separate provenance and still satisfy the same evidence-supported eligibility criteria. | Supplementary discovery is not equivalent to an independently reproducible database corpus. |
| Title/abstract restriction for PubMed and OpenAlex bibliographic searches | harmonisation decision | The initial OpenAlex implementation searched a broader text scope than the PubMed Title/Abstract queries. Before screening any candidate records, aggregate retrieval counts exposed this scope mismatch. OpenAlex was therefore restricted to title and abstract so bibliographic sources addressed comparable searchable fields. | The amendment occurred before record screening, eligibility assessment, capability classification, or tool selection. The 18 concepts themselves were unchanged. | Title/abstract searching may miss methods described only in full text or poorly indexed records; complementary software-registry search and citation chaining address this limitation. |
| Prospectively recorded seed registry | development diagnostic, not reference standard | Seed tools came from author domain knowledge and exploratory searching before the formal search and informed vocabulary and possible analytical roles. They were explicitly prohibited from determining final inclusion. | Seed recovery was used only as a sensitivity diagnostic. Final inclusion requires formal discovery/citation chaining plus the frozen evidence-based eligibility rules. | Because seed knowledge informed vocabulary, seed recovery is not an unbiased estimate of absolute search recall. |
| Fourteen priority comparator candidates used in the recovery diagnostic | rule-derived subset | The 14 were the seed-registry entries prospectively assigned direct, near-direct, or diagnostic-panel comparator roles. They were not chosen after observing search results. | The diagnostic implementation and seed registry were frozen before execution. Recovery was not used to include or exclude tools. | The 14 are a development set, not a complete or statistically independent universe of relevant software. |
| Five generic high-recall concept blocks | operational grouping with prospective freeze | After inadequate initial seed recovery was demonstrated, one broader search stage was defined around comparator-focused analytical concepts: clade/lineage markers, branch mutation/substitution mapping, ancestral reconstruction, homoplasy/recurrent variation, and phylogenetic SNP lineage genotyping. Five is therefore the number of broad concept blocks used for this prespecified expansion, not a claimed optimum. | The expansion used generic analytical vocabulary rather than software or author names, was committed before retrieval, and was performed once. Query vocabulary could not be subsequently retuned to maximise recovery of known tools. | Alternative vocabularies or additional blocks might retrieve additional records. Residual misses are assessed through citation chaining and final search-completeness analysis rather than further query tuning. |
| Only one high-recall expansion | anti-overfitting stopping rule | Repeated query modification after seeing which known tools were missed would make the search increasingly outcome-driven. The protocol therefore allowed one generic expansion and prohibited further retuning. | Remaining missed methods can enter through independently prespecified citation chaining, with discovery provenance retained. | A single expansion may sacrifice some database-search sensitivity in exchange for protection against retrospective vocabulary optimisation. |
| Nine initial citation-anchor screening candidates | rule-derived outcome | Before citation retrieval, anchor screening was restricted to all seed tools that were prospectively direct/near-direct candidates and were recovered by candidate-name matching in the frozen merged search universe. Exactly nine tools satisfied that mechanical rule. | All nine were subjected to the same frozen identity, landscape-eligibility, analytical-role, evidence, and canonical-publication requirements before citation retrieval. | The initial candidate pool depends partly on the pre-search seed registry, which is why later iterative citation chaining is required rather than treating Wave 0 as complete. |
| Eight Wave-0 anchors | rule-derived outcome | Eight was not chosen as a target sample size. Eight of the nine mechanically eligible candidates satisfied the frozen anchor-screening requirements. IQ-TREE 2 was not promoted because the recovered name-match evidence did not establish the intended IQ-TREE 2 tool. | A `do_not_anchor` decision does not exclude a method from the final landscape; the method can still be discovered and assessed through later protocol-defined stages. | The initial graph traversal begins from evidence-confirmed direct/near-direct methods available at that stage; later waves are required to reduce dependence on the starting set. |
| Canonical primary publication per anchor | reproducibility and identity rule | Citation expansion must correspond to a reproducibly identifiable publication representing the relevant method, rather than an arbitrary review, application paper, or secondary mention. | Canonical identifiers and supporting primary/official evidence are frozen before citation expansion. | Some software has complex publication histories, so canonical-publication assignment requires documented judgment. |
| Backward and forward citation chaining | complementary graph traversal | Backward references identify antecedent methodological literature; forward citations identify later methods and applications that cite the anchor. Either direction alone can miss relevant methods. | Every anchor is expanded in both directions. A wave cannot complete without terminal status for both directions from each required citation source. | Citation links do not themselves establish methodological relevance; every discovered record still requires screening. |
| OpenAlex plus OpenCitations citation graphs | independent-source robustness | The protocol uses two citation graphs to reduce dependence on the omissions or identifier behaviour of any single provider. | The union is used for discovery and source provenance is retained. Provider disagreements are not silently collapsed; retrieval has explicit reconciliation and fail-closed checks. | The two citation graphs are not statistically independent and can share upstream metadata sources or omissions. |
| No citation-count, date, language, publication-type, software-name, title-keyword, or abstract-keyword prefilter before citation screening | high-recall discovery rule | Citation chaining is intended as an orthogonal discovery mechanism capable of recovering methods missed because of terminology. Applying lexical or popularity filters before screening would recreate the same discovery bias the chaining stage is intended to mitigate. | All available retrieved citation neighbours enter the screening universe before scientific relevance assessment. | This increases screening burden substantially. |
| Iterative citation chaining beyond Wave 0 | scientific discovery design | Citation chaining is a graph traversal, not a single-hop sensitivity check. Every newly discovered eligible direct/near-direct method with an established canonical primary publication becomes an anchor in the next wave. | New anchors are expanded only in the following wave, keeping wave provenance deterministic and preventing within-wave order effects. | The number of required waves is unknown in advance. |
| Citation-chain stopping rule | rule-derived saturation criterion | Chaining stops only when a complete wave yields zero new eligible direct/near-direct methods requiring expansion. No fixed wave number or fixed record count is used as the scientific stopping rule. | A wave cannot be called complete while retrieval, record screening, candidate-method assessment, or canonical-anchor determination remains unfinished. | Saturation is conditional on the coverage of the selected citation providers and the frozen eligibility definition. |
| PubMed >10,000-result partition threshold | source-structure constraint | The threshold follows the retrieval ceiling encountered by the PubMed ESearch workflow; it is not a scientific inclusion threshold. | Large result sets are partitioned deterministically by Entry Date while the original scientific query remains unchanged, and terminal partition counts must reconcile exactly to the original query count. | Failure of the deterministic partition to reconcile causes retrieval failure rather than partial acceptance. |
| Ten OpenCitations root OCI buckets | source-structure constraint | OCI variable components are numeric. Partitioning by terminal decimal digit therefore yields the ten structurally exhaustive and mutually exclusive root buckets 0–9. | Leaf membership, uniqueness, union cardinality and independent count reconciliation are all checked. | Further recursive partitioning can be required for transport reasons. |
| 64-digit recursive OCI suffix ceiling | operational safety bound | The ceiling prevents unbounded recursion and is not a scientific threshold. Before implementation, archived OCI component lengths were structurally inspected and verified to be below the bound. Reaching the bound fails closed. | No citation is excluded because of the ceiling: reaching it terminates retrieval as a failure. | The value 64 is deliberately conservative rather than uniquely optimal. |
| Three consecutive identical provider-reconciled OpenCitations snapshots | operational integrity criterion | Provider-side identifier state was observed to change between snapshots. Requiring three consecutive identical reconciled production identities establishes repeatability across two successive snapshot transitions rather than accepting a single pairwise coincidence. This criterion does not define citation relevance. | Stable bracketing counts, reconciled cardinality, complete-row and OCI-set hashes, and direct verification of every discrepant OCI are all additionally required. Failure yields no production result. | Three is a conservative operational repeatability threshold, not a biological parameter or uniquely optimal statistical estimator. |
| Maximum five fresh OpenCitations snapshot attempts | operational availability bound | The attempt ceiling limits repeated live-provider requests while permitting transient source instability to settle. Increasing the ceiling from three to five did not relax the acceptance requirement of three consecutive identical reconciliations. | The authoritative Wave-0 result stabilized and was accepted on attempts 1–3, so attempts 4–5 were not used to select or alter the accepted corpus. | Five is a pragmatic upper bound; persistent instability still causes fail-closed retrieval. |
| Raw Wave-0 API responses excluded from Git | repository engineering decision | The authoritative Wave-0 raw archive contains hundreds of reproducible provider-response files and is much larger than the compact production corpus. Git retention is therefore separated from scientific provenance retention. | Raw responses and failed-development runs are retained separately; production outputs retain manifests, status ledgers, checksums and exact implementation commit provenance. | Long-term release/archive storage must preserve the external raw archive if exact provider-response reconstruction is required. |

---

## Search-source rationale

The three defining database sources were selected for complementary discovery
roles rather than because three sources were assumed sufficient.

### PubMed

PubMed is maintained by NCBI/NLM for searching and retrieving biomedical and
life-sciences literature. Its role in Experiment 07 is domain-focused
bibliographic discovery.

Official source consulted:

- NCBI/NLM, **About PubMed**:
  `https://pubmed.ncbi.nlm.nih.gov/about/`

### OpenAlex

OpenAlex represents a broad scholarly-works corpus covering journal articles,
conference papers, books and chapters, preprints, dissertations, datasets and
other scholarly works, with explicit relationships between works including
citations. Its role in Experiment 07 is broad scholarly discovery and
citation-graph coverage outside a strictly biomedical index.

Official sources consulted:

- OpenAlex Help Center, **Works Overview**:
  `https://help.openalex.org/data/works/`
- OpenAlex Help Center, **Citations**:
  `https://help.openalex.org/data/works/citations/`

OpenAlex explicitly notes that citation links are reconstructed by matching
references to works already represented in OpenAlex. Its documented reference
set can therefore be shorter than a publication's printed reference list when,
for example, the cited work is absent from OpenAlex or bibliographic matching
fails. This is a source-coverage limitation and is one reason citation
discovery is not allowed to depend on OpenAlex alone.

### bio.tools

bio.tools is a community-driven registry dedicated to bioinformatics software,
databases, workflows and services, with structured tool metadata and a
programmatic API. Its role is direct software-resource discovery rather than
publication-only discovery.

Official sources consulted:

- bio.tools documentation, **What is bio.tools?**:
  `https://biotools.readthedocs.io/en/latest/what_is_biotools.html`
- bio.tools documentation, **API Reference**:
  `https://biotools.readthedocs.io/en/latest/api_reference.html`

### Interpretation

These sources are complementary but are not claimed to be exhaustive.

The completeness argument for Experiment 07 therefore does **not** take the
form:

> three databases were searched, therefore all relevant tools were found.

Instead, completeness is evaluated empirically through the staged design:

1. prospectively frozen formal database search;
2. pre-screening sensitivity diagnostic;
3. one frozen generic high-recall expansion;
4. merged-corpus assessment;
5. evidence-based initial anchor screening;
6. iterative bidirectional citation chaining using two citation graphs until
   the frozen saturation criterion is reached; and
7. the separately frozen final search-completeness and miss analysis.

Database count and query count are therefore inputs to the discovery strategy,
not evidence of completeness by themselves.

---

## Distinction between discovery and evaluation

Discovery-stage inclusion is intentionally broad.

A record or method entering the discovery universe does not imply:

- eligibility for the final software landscape;
- direct comparability with BRANCHSNV;
- eligibility for executable benchmarking; or
- evidence of equivalent performance.

Those questions are decided only by the separately frozen eligibility,
capability-evidence, fair-comparison and benchmark criteria.

---

## Interpretation of numerical thresholds

Numerical values in Experiment 07 must not be described uniformly as scientific
parameters.

The following are scientific or rule-derived:

- six analytical roles define the prespecified comparison scope;
- nine initial anchor-screen candidates result from the frozen mechanical
  candidate rule;
- eight Wave-0 anchors result from applying the frozen evidence-based anchor
  criteria;
- the number of citation waves is determined by saturation rather than fixed in
  advance.

The following are operational bounds or decompositions:

- 18 initial query families;
- five high-recall concept blocks;
- 64 OCI suffix digits;
- three consecutive stable reconciliation snapshots;
- five maximum snapshot attempts.

Operational numbers must therefore be reported together with their function,
fail-closed safeguard, and the explicit statement that they are not asserted
to be uniquely optimal biological or statistical thresholds.

---

## Final completeness assessment

The final claim must be evidence based.

The completed comparative landscape should report, at minimum:

- recovery of evidence-supported direct/near-direct methods by the initial
  formal search;
- incremental recovery from the generic high-recall search;
- recovery from the union of both database-search stages;
- contribution from each database and query family;
- methods absent from the original seed registry;
- methods discovered only through citation chaining;
- number of anchors and records screened in each citation wave;
- number of newly eligible direct/near-direct methods promoted after each wave;
- the wave at which the frozen zero-new-anchor saturation criterion was met;
- citation-source-specific contributions and disagreements; and
- structured analysis of methods missed by the frozen database-search corpus.

The final manuscript should therefore report observed discovery performance and
residual limitations rather than claiming perfect or mathematically proven
search completeness.
