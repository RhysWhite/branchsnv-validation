# Canonical validation results

These files are the publication-validation snapshot generated for BRANCHSNV
v0.1.0a1. Local reruns should be written to `reproduced_results/` and compared with
these files rather than overwriting them.

The scalability timings describe the recorded benchmark environment and are not
expected to reproduce byte-for-byte on different hardware. Deterministic analytical
outputs and pass criteria should reproduce; runtime and peak memory should be
interpreted as environment-specific measurements.

From the repository root, verify file integrity with:

```bash
sha256sum -c results/checksums.sha256
```
