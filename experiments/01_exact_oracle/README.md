# Experiment 1: exact parsimony validation

This experiment tests the central BRANCHSNV ancestral-reconstruction claim:
for a selected rooted edge, the software must return the global minimum
unordered-state parsimony score and **every** parent–child nucleotide pair that
can occur on that edge among equally optimal reconstructions.

## Independent oracle

The validation oracle does not import or reuse BRANCHSNV's Sankoff algorithm.
Each test topology and focal edge is represented independently as an explicit
parent map. The oracle enumerates every A/C/G/T assignment to internal nodes,
calculates the complete-tree score, and retains all focal-edge state pairs from
globally optimal assignments.

BRANCHSNV is then run on an equivalent Newick topology. The following outputs
must agree exactly for every pattern:

1. global parsimony score;
2. complete set of possible focal-edge state pairs; and
3. classification as `no_change`, `unambiguous_change`,
   `change_state_ambiguous`, or `placement_ambiguous`.

## Coverage

The committed run evaluates:

- six five- or six-tip bifurcating and multifurcating cases, including internal,
  terminal, and root-adjacent focal branches;
- every unambiguous A/C/G/T tip pattern on each of those cases;
- every pattern formed from all 17 supported symbols (`ACGTRYSWKMBDHVN?-`)
  on a four-tip topology; and
- 5,000 additional deterministic full-alphabet patterns for each larger case.

This experiment validates the parsimony core. Parser behaviour, CLI behaviour,
fixed-exclusive classification, adversarial fault detection, real-data
reproduction, and scalability are evaluated separately.

## Run

From this validation repository, with the BRANCHSNV source repository alongside
it:

```bash
python experiments/01_exact_oracle/run.py \
  --branchsnv-root ../branchsnv \
  --output-dir results/01_exact_oracle
```

The script has no third-party runtime dependencies. A non-zero exit status is
returned if any discrepancy is found.

## Outputs

- `summary.json`: deterministic primary result and source hashes;
- `topology_summary.tsv`: coverage and outcome counts by topology;
- `status_summary.tsv`: aggregate reconstruction classifications;
- `mismatches.tsv`: discrepancies, with a header-only file indicating none;
- `run_metadata.json`: environment and elapsed-time provenance for the run.
