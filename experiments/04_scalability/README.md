# Experiment 04 — End-to-end scalability

## Question

How do BRANCHSNV wall time and peak resident memory change as taxon and site counts
increase?

## Design

Each measurement is a fresh command-line invocation and includes NEXUS and Newick
parsing, taxon validation, branch selection, analysis, TSV output, member output and
JSON provenance.

- Taxon scaling: 50, 100, 250, 500, 1,000 and 2,000 taxa at 10,000 sites.
- Site scaling: 1,000, 5,000, 10,000, 25,000, 50,000 and 100,000 sites at 250 taxa.
- Mode comparison: `fixed-exclusive`, `parsimony` and `both` at 500 taxa × 10,000 sites.
- Three repetitions per configuration in deterministic shuffled order after one
  unmeasured warm-up run.
- The focal branch contains approximately one quarter of taxa.
- Synthetic states follow a deterministic 20-site cycle covering focal, recurrent,
  mixed, ambiguous, missing and gap-containing patterns.

The scaling grid uses `--mode both`. BRANCHSNV v0.1.0a1 reconstructs ancestral states
for every site in all modes; the mode comparison therefore measures the practical
impact of output filtering rather than a different reconstruction algorithm.

## Inputs

The generated matrices total approximately 84 MB and are intentionally not tracked in
Git. Generate them with:

```bash
python experiments/04_scalability/generate_inputs.py \
  --output-root experiments/04_scalability/inputs
```

The generated manifest should match the committed publication manifest exactly:

```bash
cmp experiments/04_scalability/inputs/manifest.json \
  results/04_scalability/input_manifest.json
```

## Run

```bash
python experiments/04_scalability/run.py \
  --validation-root . \
  --branchsnv-source /path/to/branchsnv \
  --repetitions 3 \
  --results-dir reproduced_results/04_scalability

python experiments/04_scalability/summarize_models.py \
  --summary reproduced_results/04_scalability/benchmark_summary.tsv \
  --output reproduced_results/04_scalability/scaling_models.tsv

python experiments/04_scalability/plot_results.py \
  --summary reproduced_results/04_scalability/benchmark_summary.tsv \
  --output-dir reproduced_results/04_scalability/figures
```

GNU `time` is required for peak resident-memory measurement. Plot generation requires
Matplotlib; input generation, benchmarking and tabular summaries otherwise use the
Python standard library and BRANCHSNV.

## Outputs

- `raw_runs.tsv`: every replicate in actual execution order;
- `benchmark_summary.tsv`: median and observed range by configuration;
- `scaling_models.tsv`: descriptive linear-model coefficients and R² values;
- `summary.json`: headline configurations and mode comparison;
- `run_metadata.json`: software hashes and execution environment;
- `figures/`: runtime and memory plots in PNG and SVG formats;
- `input_manifest.json`: exact hashes of every deterministic benchmark input.

The committed timings describe the recorded virtualised environment. They should be
repeated against the frozen publication release if its production source differs from
the evaluated v0.1.0a1 snapshot.
