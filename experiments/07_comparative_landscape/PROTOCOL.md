# Experiment 07 — Comparative software landscape and cross-method evaluation

## Status

Protocol frozen before formal tool screening and capability classification.

The `seed_tool_registry.tsv` file records tools identified from author
domain knowledge and exploratory searching before the formal search. It was
used to develop search vocabulary and define potentially relevant analytical
roles. It is not the final comparative landscape, and presence or absence in
the seed registry will not determine inclusion. Final inclusion will be based
only on the formal search, citation chaining, eligibility criteria, and
source-backed screening defined below.

## Objective

Identify software relevant to interpretation of sequence variation in a
phylogenetic context, determine which analytical questions each tool addresses,
and perform direct benchmarking only where outputs are scientifically
comparable.

The comparison is designed to distinguish six analytical roles:

1. clade/lineage marker discovery;
2. branch-change reconstruction;
3. homoplasy/recurrent-state analysis;
4. marker deployment/genotyping;
5. general phylogenetic/parsimony infrastructure; and
6. upstream variant-calling, recombination, and phylogeny workflows.

## Search sources

Formal searches will use:

1. PubMed;
2. bio.tools;
3. OpenAlex;
4. backward citation chaining from included direct and near-direct methods; and
5. forward citation chaining from included direct and near-direct methods.

Primary software repositories and official documentation will subsequently be
used to verify capabilities, software availability, versions, and execution
requirements.

Google Scholar may be used only as a supplementary discovery check and will
not define the reproducible search corpus.

## Search date

The formal search date and retrieval timestamps will be recorded in the search
outputs.

## Eligibility for the software landscape

A software tool is eligible when all of the following apply:

1. a publication or stable public documentation describing the method exists;
2. an identifiable software implementation exists or existed;
3. the tool operates on sequence, SNP, genotype, or phylogenetic data; and
4. the tool addresses at least one of the six analytical roles defined above.

Tools are not excluded solely because they are organism-specific, historical,
unmaintained, web-only, or not executable in the current environment. These
properties are recorded separately.

## Exclusion from the software landscape

Records are excluded when they:

1. describe only a biological application with no identifiable analytical
   software or reusable method;
2. concern unrelated variant classes or data types without a relevant
   sequence/phylogenetic capability;
3. duplicate another publication or software record for the same method
   without adding a distinct relevant capability; or
4. cannot be supported by a primary publication or stable authoritative
   documentation.

Every screened exclusion will be recorded with a reason.

## Benchmark eligibility

Inclusion in the landscape does not imply eligibility for direct benchmarking.

A tool is eligible for executable head-to-head comparison only when:

1. its documented purpose overlaps a BRANCHSNV analytical question;
2. sufficiently equivalent biological inputs can be supplied;
3. its outputs can be mapped to a prespecified truth or comparison endpoint
   without redefining the tool's intended output; and
4. the software can be executed reproducibly or authoritative published output
   is available for the exact benchmark data.

Tools failing one or more criteria remain in the landscape and are classified
as contextual, near-direct, or non-executable comparators.

## Capability evidence

Capabilities will not be inferred from tool names or secondary descriptions.

Each substantive capability classification must be supported by one or more of:

1. the primary method publication;
2. official software documentation;
3. the official source repository; or
4. direct execution of a version-recorded release.

Capability values will be:

- yes
- no
- partial
- not_applicable
- not_established

The evidence source and explanatory note will be retained for every
non-trivial classification.

## Fair-comparison principle

No method will be scored negatively for failing to perform a task outside its
documented purpose.

Direct quantitative comparisons will be restricted to shared analytical
endpoints. Differences in purpose, inputs, reconstruction model, treatment of
uncertainty, or output semantics will be reported rather than collapsed into
an overall ranking.

## Reproducibility

The publication-validation repository will retain:

- exact search queries;
- retrieval dates;
- raw search results where licensing permits;
- deduplication and screening decisions;
- inclusion/exclusion reasons;
- primary capability evidence;
- software versions and installation records;
- benchmark eligibility decisions;
- exact benchmark inputs and outputs; and
- checksums for publication outputs.
