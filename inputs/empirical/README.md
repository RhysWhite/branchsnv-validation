# Empirical publication inputs

This directory contains the exact working transposed-NEXUS alignments and rooted
NEWICK trees used for the focal-branch and complete-phylogeny analyses in Experiments
05 and 06. `checksums.sha256` is the integrity manifest for every committed input and
focal-descendant list.

| Prefix | Dataset | Taxa | Variable sites | Rooting used in validation |
|---|---|---:|---:|---|
| `ak3_` | MRSA AK3 | 396 | 10,481 | outgroup `SRR13968194` |
| `st97_` | MRSA ST97 | 103 | 4,651 | outgroup `ERR4911723` |
| `oxa48_` | *E. coli* ST131/OXA-48 | 47 | 266 | `ERR1852604 ERR1791001 ERR1791000 ERR1791004` |
| `clade_a_` | *E. coli* ST131 Clade A | 120 | 3,911 | supplied NEWICK root |
| `clade_b_` | *E. coli* ST131 Clade B | 246 | 12,148 | supplied NEWICK root |

The OXA-48 alignment uses `REF` for the reference isolate represented as `18AR0845` in
the tree. The committed source file is retained unchanged; Experiments 05 and 06 apply
and record the single deterministic `REF` → `18AR0845` taxon-label normalization before
analysis.

`focal_descendants/` contains the exact complete descendant sets used for the three
published focal-branch comparisons. The SHA-256 digest of each sorted newline-delimited
list is also the full descendant-derived BRANCHSNV branch digest.

Public sequence-data provenance is reported in the associated manuscript. The Clade A
and Clade B working matrices draw on genomes from BioProjects PRJNA637928,
PRJNA531554 and PRJNA1077717.
