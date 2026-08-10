# Experiment 06 — Empirical cross-classification across complete phylogenies

## Question

Across real bacterial SNV phylogenies, how often does strict clade exclusivity coincide
with an unambiguous equal-cost substitution reconstructed on the focal edge?

## Datasets

| Dataset | Taxa | Variable sites | Rooting |
|---|---:|---:|---|
| MRSA AK3 | 396 | 10,481 | outgroup `SRR13968194` |
| MRSA ST97 | 103 | 4,651 | outgroup `ERR4911723` |
| *E. coli* ST131/OXA-48 | 47 | 266 | four-taxon outgroup recorded in `run.py` |
| *E. coli* ST131 Clade A | 120 | 3,911 | supplied NEWICK root |
| *E. coli* ST131 Clade B | 246 | 12,148 | supplied NEWICK root |

The all-edge implementation is maintained in this validation repository and does not
import production BRANCHSNV reconstruction logic. NumPy/Numba implement the four-state
dynamic program and pandas performs table-level aggregation. Fixed exclusivity is
calculated independently from observed tip states.

The two branches directly incident to each degree-two root are excluded from the
primary denominator and retained in `root_adjacent.tsv`. The OXA-48 `REF` → `18AR0845`
label normalization is applied in memory only.

## Run

The accelerated analysis and production-QC check are deliberately run in separate
fresh Python processes so the independent implementation and production check remain
operationally separated:

```bash
python experiments/06_empirical_cross_classification/run.py \
  --branchsnv-root ../branchsnv \
  --input-dir inputs/empirical \
  --output-dir reproduced_results/06_empirical_cross_classification

python experiments/06_empirical_cross_classification/production_qc.py \
  --branchsnv-root ../branchsnv \
  --input-dir inputs/empirical \
  --analysis-results-dir reproduced_results/06_empirical_cross_classification

python experiments/06_empirical_cross_classification/verify.py \
  --results-dir reproduced_results/06_empirical_cross_classification
```

## Expected primary result

Across 1,804 non-root-adjacent branches and 16,073,690 branch–site comparisons,
31,644 comparisons are informative: 30,817 satisfy both criteria, 675 are unambiguous
substitutions that are not fixed-exclusive, and 152 are placement-ambiguous. There are
no fixed-exclusive comparisons lacking an unambiguous substitution and no
`change_state_ambiguous` comparisons in the primary analysis.

Among the 675 unambiguous but non-exclusive substitutions, 645 have the derived
nucleotide elsewhere outside the focal clade and 30 occur where the descendant clade
is not fixed at the observed site.

## Production check

Eight prespecified Clade A/B branches cover 64,236 branch–site analyses and 1,617
informative records. Unmodified production BRANCHSNV must agree 1,617/1,617 in whole-
tree parsimony score, complete optimal focal-edge pair set, reconstruction class and
fixed-exclusive status. The canonical snapshot contains zero discrepancies.
