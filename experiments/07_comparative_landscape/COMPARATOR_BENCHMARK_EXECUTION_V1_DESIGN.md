# Comparator benchmark execution design v1

## Purpose

This freeze defines the quantitative comparison that may later be implemented for the eight method families that passed the frozen feasibility gate.

It does **not** authorize software installation, environment construction, canonical dataset generation, comparator execution or benchmark execution.

## Frozen executable comparator universe

Eight workflows are eligible: ARPIP, FastML, HomoplasyFinder, PAML, PastML, POUTINE, SNPPar and TreeTime.

SNPPar and TreeTime are the two full quantitative candidates. The other six are endpoint-specific. The 21 contextual comparators are not executed, and their scientific role in the comparative landscape is unchanged.

## Benchmark arms

### Branch-change reconstruction

BRANCHSNV is compared against ARPIP, FastML, PAML, PastML, SNPPar and TreeTime.

The primary scoring unit is an exact nucleotide state change at a genomic position on a canonical rooted-tree edge. Comparator-specific ancestral-node labels are mapped to edges only through the descendant-tip set of the edge.

Primary metrics are precision, recall and F1. False-positive and false-negative event counts are retained explicitly.

### Homoplasy/recurrent-state analysis

BRANCHSNV is compared against HomoplasyFinder, POUTINE, SNPPar and TreeTime.

The primary scoring unit is whether a genomic site is truly recurrent. A recurrent site has two or more independently generated mutation events in the frozen truth ledger. Parallel, convergent and reversal subclasses are retained for secondary analysis.

### Endpoints without fair executable comparators

No quantitative benchmark is forced for strict clade/lineage marker discovery or marker-deployment genotyping because no feasibility-qualified external method exposes a sufficiently equivalent nucleotide endpoint.

## Benchmark truth

The benchmark uses independently generated rooted, strictly bifurcating trees and 10,000-bp DNA sequences. Tree inference is not benchmarked.

Truth is an explicit branch-event ledger generated independently of BRANCHSNV and all comparator implementations. Tip alignments are derived from that event ledger. There is no recombination and no indel process.

Three tree sizes are frozen: 32, 128 and 512 tips.

Five event regimes are frozen: unique-only, parallel, convergent, reversal and mixed recurrence.

Two observation conditions are frozen: complete calls and exactly 5% missing/ambiguous tip observations.

Each size × regime × observation cell has five deterministic replicates, giving **150 canonical benchmark datasets**.

## Fair adapters

Every method receives information derived from the same canonical tip alignment and rooted tree. Tools accepting alignments receive the nucleotide alignment directly. SNP/VCF inputs are deterministic projections from that alignment. PastML receives one categorical column per variable nucleotide position; A/C/G/T are states and missing observations remain missing.

Truth ancestral sequences and the truth event ledger are never supplied to a comparator.

## Dependency structure

TreeTime, SNPPar and POUTINE are a dependency-linked family because SNPPar uses TreeTime by default for ASR and POUTINE also incorporates TreeTime.

Workflow-level results are reported separately, but they cannot be presented as three algorithmically independent confirmations.

## Reproducibility

Each comparator must have an isolated environment with an exact version/commit and dependency lock. Canonical benchmark execution must be network-disabled. Commands, environment identifiers, release/source hashes or permitted container digests, stdout/stderr, wall time and peak memory are recorded.

Restricted third-party source or binaries are not vendored into this repository.

## Failure handling

A timeout or non-zero exit is a completion failure, not a zero-accuracy result. Unsupported inputs are reported as `UNSUPPORTED_BY_METHOD_CONTRACT`; no scientifically invalid adapter is created merely to keep a method in the table.

Canonical data are never used for tuning or debugging. Later implementation validation may use separate toy data only.

## Next gate

`FREEZE_COMPARATOR_BENCHMARK_EXECUTION_IMPLEMENTATION_BEFORE_EXECUTION`
