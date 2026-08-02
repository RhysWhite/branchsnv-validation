# Experiment 03 — Published bacterial datasets

## Question

Does BRANCHSNV recover branch-level substitutions reported independently from
published bacterial genomic datasets, and does it make any methodological
differences explicit?

## Design

The experiment contains two complementary analyses.

### A. All-edge comparison with SNPPar

Four public SNP matrices distributed through the SNPPar testing repository
were analysed:

| Dataset | Taxa | Variable sites | Non-root edges compared |
|---|---:|---:|---:|
| *Elizabethkingia anophelis*, CP014805 | 70 | 374 | 138 |
| *Burkholderia dolosa*, chromosome 1 | 114 | 299 | 226 |
| *B. dolosa*, chromosome 2 | 114 | 153 | 226 |
| *B. dolosa*, chromosome 3 | 114 | 59 | 226 |

For each matrix, the original SNP table was converted deterministically to the
transposed NEXUS subset accepted by BRANCHSNV. The published tree and SNPPar
node-labelled tree were parsed independently. Every non-root edge was mapped
between programs by its complete sorted descendant-tip set; internal node names
were not assumed to be equivalent.

BRANCHSNV was run in parsimony mode on every mapped edge. Its
`unambiguous_change` events were compared with SNPPar's
`all_mutation_events.tsv` output using:

- exact descendant-defined edge;
- genomic position; and
- parent-to-child nucleotide direction.

SNPPar events absent from BRANCHSNV's unambiguous set were then tested against
BRANCHSNV's complete set of equal-cost optimal state pairs for that edge and
site.

### B. Published AK3 branch tables

The committed checksum-gated BRANCHSNV outputs from the AK3 working dataset
were compared with Tables 2 and 3 of:

> White RT et al. 20 years later: unravelling the genomic success of New
> Zealand's home-grown AK3 community-associated methicillin-resistant
> *Staphylococcus aureus*. *Microbial Genomics*. 2025;11:001452.
> DOI: 10.1099/mgen.0.001452.

The exact AK3 alignment and tree are not redistributed in this repository snapshot. When supplied via
`--ak3-input-dir`, the experiment verifies their recorded SHA-256 hashes and
reruns the repository's byte-for-byte validation before comparing the output
with the publication.

## Public input retrieval

Download the public SNPPar inputs and verify every SHA-256 checksum:

```bash
python experiments/03_published_datasets/download_public_inputs.py \
  --output-dir public_inputs/03_published_datasets
```

The download manifest, source URLs and expected hashes are embedded in
`run.py`. The checksum-gated downloader was developed for this BRANCHSNV validation;
it is not part of SNPPar. The SNPPar test repository describes these as self-contained
published datasets containing the reference, tree, and SNP tables required to
run SNPPar:

- https://github.com/d-j-e/SNPPar_test
- https://doi.org/10.1099/mgen.0.000694

## Run

```bash
python experiments/03_published_datasets/run.py \
  --branchsnv-root ../branchsnv \
  --public-input-dir public_inputs/03_published_datasets \
  --output-dir results/03_published_datasets
```

To repeat the checksum-gated AK3 raw-input analysis as part of the same run:

```bash
python experiments/03_published_datasets/run.py \
  --branchsnv-root ../branchsnv \
  --public-input-dir public_inputs/03_published_datasets \
  --ak3-input-dir /path/to/exact/ak3/files \
  --output-dir results/03_published_datasets
```

The AK3 directory must contain:

| File | Required SHA-256 |
|---|---|
| `396_MRSA_AK3(1).nex` | `40c49b026c52e04530ecbbee7044567ac3355eccf7adda42a7d96bf977df9014` |
| `Cluster_1_396genomes_refsa230905_barcode06_ML_Flitered_BS.nwk` | `18322b2808baf621d09dd5292027205e68a0f207d7be44f043bd044d0d314bd0` |

## Results

### Public all-edge comparison

Across **816 branch–matrix comparisons**, BRANCHSNV identified **877
unambiguous branch substitutions**. Every event matched a SNPPar event on the
same descendant-defined edge, at the same genomic position, and in the same
parent-to-child nucleotide direction.

| Measure | Result |
|---|---:|
| BRANCHSNV unambiguous events | 877 |
| Exact SNPPar matches | 877 |
| BRANCHSNV-only unambiguous events | 0 |
| Direction differences | 0 |
| Total SNPPar events | 943 |
| SNPPar-only events | 66 |

All 66 SNPPar-only events were among BRANCHSNV's possible state pairs but were
classified as `placement_ambiguous`: at least one globally optimal
reconstruction changed on the edge and at least one did not. Thus, there was
no unexplained event or nucleotide-direction disagreement. The difference
reflects BRANCHSNV's deliberate requirement that an unambiguous branch call be
supported across **all** globally optimal equal-cost reconstructions.

### AK3 comparison

For the 360-descendant MRSA AK3 branch, the committed output reproduced all
**23 published SNV positions and directions exactly**. The one published
deletion is outside the nucleotide-substitution scope of BRANCHSNV.

For the 385-descendant SaPITokyo12571-like branch, all 14 published SNV
positions were present, but the working inputs produced the reverse nucleotide
direction at every shared position and one additional position (1,891,191).
The published insertion is outside scope. This is retained as an unresolved
working-input/publication-version difference and is excluded from the primary
reproduction claim.

## Outputs

| File | Contents |
|---|---|
| `summary.json` | Machine-readable primary results and pass criteria |
| `dataset_summary.tsv` | Results for each public matrix |
| `branch_summary.tsv` | All 816 mapped edge comparisons |
| `event_comparison.tsv` | All 943 compared mutation events |
| `placement_ambiguous_snppar_events.tsv` | The 66 method-sensitive events and all BRANCHSNV optimal pairs |
| `ak3_table_comparison.tsv` | Position- and direction-level AK3 comparison |
| `public_input_checksums.tsv` | Exact public input sources and hashes |
| `run_metadata.json` | Environment and execution metadata |

## Interpretation

This is a concordance and method-sensitivity experiment, not a claim that
BRANCHSNV and SNPPar are interchangeable. SNPPar is designed primarily to
detect and annotate homoplasic events efficiently, whereas BRANCHSNV
interrogates a selected branch and retains every equally optimal focal-edge
state pair. Agreement for all BRANCHSNV-unambiguous events provides an
independent real-data check; the 66 ambiguity differences demonstrate a
specific, expected consequence of the all-optima reporting rule.
