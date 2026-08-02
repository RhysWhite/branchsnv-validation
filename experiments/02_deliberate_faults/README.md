# Experiment 2: deliberate-fault validation

This experiment asks whether the BRANCHSNV publication-validation framework is
capable of detecting plausible analytical errors, rather than merely agreeing
with the correct implementation.

Ten controlled fault variants were implemented in this validation repository.
They alter ancestral reconstruction, state handling, rooting, branch selection,
taxon mapping, or fixed-exclusive classification. BRANCHSNV production source
is imported read-only and is not modified.

## Deliberate faults

| Fault | Incorrect behaviour | Required safeguard |
|---|---|---|
| Reverse parent/child | Report the selected edge in child-to-parent orientation | Rooted edges must be reported parent to child |
| Majority instead of parsimony | Infer states from the majority on either side of an edge | Use complete-tree global parsimony |
| Gap as a fifth state | Treat `-` as an observed evolutionary state | Treat configured gap and missing symbols as unknown nucleotide states |
| Retain one optimum | Keep only the first equally optimal focal-edge state pair | Retain every pair attainable among global optima |
| Opposite branch side | Analyse a sibling clade rather than the requested descendants | Resolve the edge from the exact requested descendant set |
| Ignore outgroup rooting | Use the Newick's existing root | Apply the requested root before branch selection and direction assignment |
| Accept MRCA superset | Replace an invalid exact descendant request with its MRCA | Reject exact requests whose MRCA contains additional tips |
| Match taxa by order | Join tree tips to alignment columns by position | Join taxa by exact labels independently of column order |
| Permit missing outside taxa | Call a site exclusive despite missing outside states | Require all descendant and outside taxa to be callable |
| Equate change with exclusivity | Call every unambiguous branch substitution a fixed-exclusive marker | Keep reconstructed-change and fixed-exclusive definitions separate |

## Challenge design

The four ancestral-reconstruction faults were evaluated against exhaustive or
deterministically generated pattern sets derived from Experiment 1. Additional
exhaustive challenges tested the wrong branch side, permuted alignment columns,
missing-data handling, and definition conflation. Rooting and exact-descendant
faults were tested with permanent tree configurations selected to require the
corresponding validation rule.

In total, the committed run comprises **280,216 fault–challenge comparisons**.
This is a sum across fault variants; it is not a count of unique input patterns.
A fault is considered detected if at least one challenge distinguishes the
faulted result from the correct result. The script returns a non-zero exit
status if any fault survives all assigned challenges.

## Run

From this validation repository, with the BRANCHSNV source repository alongside
it:

```bash
python experiments/02_deliberate_faults/run.py \
  --branchsnv-root ../branchsnv \
  --output-dir results/02_deliberate_faults
```

The script requires only Python 3.10 or later and the local BRANCHSNV source
checkout.

## Outputs

- `summary.json`: deterministic primary result, fault definitions, witnesses,
  source hashes, and aggregate counts;
- `fault_summary.tsv`: one summary row per deliberate fault;
- `witnesses.tsv`: the first permanent differentiating case retained for each
  fault;
- `run_metadata.json`: environment and elapsed-time provenance.

## Interpretation

Detection of every deliberate fault demonstrates that the validation design is
sensitive to the tested classes of incorrect behaviour. It does not establish
that every conceivable defect would be detected, nor does the fraction of
patterns differentiating a fault estimate a real-world error probability.
