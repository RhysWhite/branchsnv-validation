# Experiment 07 — completed comparator accuracy publication record

This **additive**, explicitly labelled exploratory extension records the 150-scenario
benchmark completed on 26 October 2026. It is separate from the original literature
landscape study and from the historical Experiments 01–06 canonical snapshot.

- Seven methods are scored on exact latent branch events (BRANCHSNV plus six external tools).
- Four external methods are scored on recurrent sites using a *different* endpoint.
- Eight external workflows were executed on 150 frozen scenarios each: 1,200 jobs.
  The original 300 FastML/TreeTime jobs were retained; six others contributed 900 new jobs.
- BRANCHSNV was separately independently scored on the same 150 scenarios.
- The six-method extension was finalized after successful native software normalization;
  the surviving independent scorer is `exp07_score_archived.py`, whose SHA-256 equals
  the checksum recorded in `results/.../accuracy_benchmark_v1/provenance.json`.

## Start here

```bash
python verify_experiment07_publication.py
```

This lightweight, standard-library-only validator verifies SHA-256 seals, the 150-scenario
coverage, exact TP/FP/FN arithmetic, aggregation, historical Experiment 06 figures,
method eligibility, and figure-data hashes. The plotting source is at
`manuscript/comparator_accuracy/plot_final_figures.py`.

## Traceability and limitations

`publication_claims.json` is the machine-readable claim register. The original source
manifest and source pins are preserved in this directory. The first benchmark uses
branch lengths derived from realised mutation events. Accordingly the analysis
measures **latent-history recovery conditional on event-derived branch lengths**, not
accuracy for branch lengths independently generated from event histories.

**Publication completeness boundary:** this overlay makes the *scored results and
figures* auditable. An independent **fresh native execution** still requires public
archiving of the final post-hotfix Jynx executor, full canonical observed inputs,
execution environment/container locks, and the truth-separated scoring truth archive.
Do not claim complete third-party end-to-end reproduction until those deposits pass
an independent rerun. Existing canonical input and results must not be overwritten.
