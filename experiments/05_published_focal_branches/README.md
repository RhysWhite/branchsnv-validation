# Experiment 05 — Published focal branches

## Question

Does BRANCHSNV reproduce previously reported nucleotide substitutions on three independently published focal branches?

## Datasets and focal edges

| Dataset | Publication | Focal descendants | Published SNVs |
|---|---|---:|---:|
| MRSA AK3 | White et al., *Microbial Genomics* 2025; DOI 10.1099/mgen.0.001452 | 360 | 23 |
| MRSA ST97 | White et al., *Microbial Genomics* 2024; DOI 10.1099/mgen.0.001273 | 2 | 10 |
| *E. coli* ST131/OXA-48 | White et al., *Drug Resistance Updates* 2026; DOI 10.1016/j.drup.2025.101327 | 39 | 13 |

The exact descendant sets are committed under `inputs/empirical/focal_descendants/`. For AK3, the publication reports parent-to-child substitutions directly. For ST97 and ST131/OXA-48, published group-allele contrasts define the expected states on the corresponding focal edge. The experiment requires the same genomic position and expected parent-to-child contrast, and additionally requires every reproduced SNV to be both strictly fixed-exclusive and `unambiguous_change` under BRANCHSNV.

The ST97 working matrix/tree use `REF` for publication isolate 23MR1425. The OXA-48 matrix uses `REF` for reference isolate 18AR0845 while the tree uses `18AR0845`; `run.py` performs that single deterministic taxon-label normalization and records both input and transformed SHA-256 hashes.

## Run

```bash
python experiments/05_published_focal_branches/run.py \
  --branchsnv-root ../branchsnv \
  --input-dir inputs/empirical \
  --output-dir reproduced_results/05_published_focal_branches
```

## Pass criterion

All **46/46** published SNVs must match in position and expected focal-edge state contrast, with no additional focal-branch SNVs reported; all 46 must be fixed-exclusive and unambiguous focal-edge substitutions.

One published insertion/deletion event associated with each focal branch is recorded explicitly in `summary.json` but excluded from the 46-SNV pass criterion because the current BRANCHSNV release reconstructs nucleotide substitutions only.
