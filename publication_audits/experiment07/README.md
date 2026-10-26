# Experiment 07: metric semantics and reader-facing aggregate table

This additive reporting audit does **not** alter the frozen independent scorer,
original aggregate scores, 1,350 scenario-level source rows, results archive,
or either publication figure. The source archive is governed by
`publication_evidence.sha256` and `verify_experiment07_publication.py`.

## Why a reporting transformation is necessary

The original scorer's `aggregate()` deliberately supplies a numerical convention
of `precision=recall=F1=1.0` for the empty-event case (TP=FP=FN=0). This occurs
in **five** aggregate rows with `regime=unique_only` and recurrent-site endpoints
(four full-site methods and POUTINE's separate biallelic-only endpoint).
Those values mean neither positive truth sites nor positive predictions occurred.
**They are not measured F1=100%**: precision, recall and F1 have zero
denominators and are marked `NA` in the reporting table.

Elsewhere, `F1_pct` is calculated directly from counts as
`100 × 2TP/(2TP+FP+FN)`. Precision and recall are `NA` whenever their respective
denominators vanish. All metrics are *percentages*, not proportions. `NA` means
mathematically undefined; it does not mean zero or a failed run. In reversal
scenarios each full-site method recovers 0 of 600 recurrent truth sites;
its F1 is correctly 0% (not undefined). POUTINE's observed-biallelic-only
endpoint has a restricted denominator and must never be compared to the
full-site endpoint without an explicit eligibility qualification.

The table is deterministically generated and verified against each source
aggregate and the 1,350 individual scenario scores:

```bash
python publication_audits/experiment07/verify_reporting_semantics.py
```

Do not substitute this table for the historically sealed original: cite both
`results/07_comparative_landscape/accuracy_benchmark_v1/aggregate_scores.tsv`
and this reporting transformation when presenting regime-level results.
Independent native comparator re-execution remains outside this reporting audit.
