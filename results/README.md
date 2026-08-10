# Canonical validation results

This directory is the manuscript-associated result snapshot for BRANCHSNV v0.1.0a1.
Local reruns should normally be written to `reproduced_results/` and compared with
these files rather than overwriting them.

Key machine-readable summaries are:

- `01_exact_oracle/summary.json`
- `02_deliberate_faults/summary.json`
- `03_published_datasets/summary.json`
- `04_scalability/summary.json`
- `05_published_focal_branches/summary.json`
- `06_empirical_cross_classification/summary.json`

Experiment 04 timings and peak-memory values are environment-specific. The other
experiments use exact pass criteria and committed/checksum-gated inputs.

Verify the full committed snapshot and headline values from the repository root:

```bash
python verify_publication_snapshot.py
```

For checksum-only verification, run `sha256sum -c results/checksums.sha256`.
