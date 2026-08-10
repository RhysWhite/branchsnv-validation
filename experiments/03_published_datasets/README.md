# Experiment 03 — Published SNPPar datasets

## Question

When the focal-edge substitution is unambiguous under BRANCHSNV, does it agree with
independently generated SNPPar mutation-event output on the same descendant-defined
edge, position and nucleotide direction?

## Design

Four public variable-site matrices distributed with the SNPPar test repository are used:

| Dataset | Taxa | Variable sites | Non-root edges |
|---|---:|---:|---:|
| *Elizabethkingia anophelis* | 70 | 374 | 138 |
| *Burkholderia dolosa*, chromosome 1 | 114 | 299 | 226 |
| *B. dolosa*, chromosome 2 | 114 | 153 | 226 |
| *B. dolosa*, chromosome 3 | 114 | 59 | 226 |

Each SNP table is converted deterministically to transposed NEXUS. Edges are mapped
between trees by exact equality of complete descendant-tip sets, not internal node
labels. Concordance requires the same descendant-defined edge, genomic position and
parent-to-child nucleotide direction.

SNPPar events not classified as unambiguous by BRANCHSNV are tested against the full
BRANCHSNV optimal focal-edge state-pair set.

## Retrieve checksum-gated public inputs

```bash
python experiments/03_published_datasets/download_public_inputs.py \
  --output-dir public_inputs/03_published_datasets
```

Source URLs and required SHA-256 values are embedded in the experiment code.

## Run

```bash
python experiments/03_published_datasets/run.py \
  --branchsnv-root ../branchsnv \
  --public-input-dir public_inputs/03_published_datasets \
  --output-dir reproduced_results/03_published_datasets
```

## Result

Across 816 branch–matrix comparisons, BRANCHSNV reported 877 unambiguous focal-edge
substitutions and all 877 matched SNPPar exactly. SNPPar reported 943 events in total.
The remaining 66 events occurred across 33 branch–matrix comparisons; every one was
contained in BRANCHSNV's complete optimal state-pair set but was classified as
`placement_ambiguous` because equally optimal reconstructions included both a change
and no change on the focal edge. There were no BRANCHSNV-only unambiguous events and
no direction disagreements.

Published focal-branch reproduction is intentionally separated into Experiment 05.
