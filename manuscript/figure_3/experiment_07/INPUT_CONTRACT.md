# Figure 3 / Experiment 07 – input contract

This is an **adapter target**, not a claim that Experiment 07 already emits this schema.
Create the normalised long table from the *real and scientifically adjudicated* comparator runs. Do not infer branch-event F1 for methods that do not support that target.

One row per (`scenario_id`, `method`, `endpoint`). The row fields:

| Column | Semantics |
|---|---|
| `scenario_id` | Unique benchmark scenario/run ID, shared across methods, including missingness status and replicate |
| `pair_id` | Same scenario family across complete and masked_5pct; includes replicate (excludes masking) |
| `method` | BRANCHSNV, SNPPar, TreeTime, FastML, PAML, PastML, ARPIP, HomoplasyFinder, POUTINE |
| `tips` | Tree tip count |
| `regime` | Frozen evolutionary regime label |
| `masking` | `complete` or `masked_5pct` |
| `endpoint` | Harmonised truth-referenced endpoint, e.g. `branch_event_f1` ONLY if directly comparable |
| `value` | Observed endpoint score for eligible method/scenario; NA permitted for ineligible |
| `runtime_seconds` | Observed positive walltime, NA for unsuccessful runs |
| `eligible` | Explicit TRUE/FALSE scientific endpoint eligibility; not automatically guessed from file presence |
| `reason` | Written reason why ineligible; required as a scientific evidence principle |

The code fails closed for duplicate scenario+method entries and for missing eligible numeric scores. It writes an excluded-rows audit, paired comparisons, masking pairs and input SHA256.

**No actual Experiment 07 table has been used in creating this package.** The single provided fixture is synthetic and MUST NOT be committed or cited as a study result.

## Generate *preliminary* artwork, once your science-screened normalised CSV exists

```bash
python manuscript/figure_3/make_figure_3.py \
  --input /path/to/approved-format-exp07-long-table.tsv \
  --outdir manuscript/figure_3/_generated \
  --endpoint branch_event_f1 \
  --direction higher \
  --preliminary
```

`branch_event_f1` is an **example endpoint name only**. Use the actual supported endpoint; do not try to coerce every comparator into it. The `--preliminary` flag is compulsory and applies a watermark: scientific sign-off remains separate.

## Comparator coverage and interpretability

This figure is **not** evidence that all eight external methods infer the same target. When some methods lack comparable endpoints, they must be marked `eligible=FALSE` with a reason. Panel B requires matched scenario IDs across BRANCHSNV and each eligible comparator. Panel C requires complete and 5%-masked pairs with identical pair IDs. Runtime comparability requires documented hardware and run conditions; the script cannot independently check that.
