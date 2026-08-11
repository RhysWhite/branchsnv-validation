# Figure 4 code walkthrough

This document explains `make_figure_4.py` in plain English. Unlike Figure 1, which draws a conceptual schematic, Figure 4 is a **data-driven figure**: the plotting script reads the committed run-level benchmark measurements and recalculates every summary displayed in the artwork.

## The 60-second mental model

The script performs five steps:

1. locate `results/04_scalability/raw_runs.tsv` relative to the repository root;
2. read and normalize the run-level benchmark columns;
3. require exactly three measurements for every plotted configuration;
4. calculate medians, observed minima/maxima, and descriptive ordinary least-squares fits;
5. draw panels A-F and export PDF, SVG, PNG, TIFF, and RGB TIFF files.

No benchmark result is hard-coded into the plotting script. The fixed lists of taxa, sites, and analysis modes define **which committed configurations belong in the manuscript figure**, not their measured values.

## 1. Imports and locked plotting style

The opening imports use only Python's standard library plus Matplotlib and Pillow. `csv` reads the tab-separated measurements, `statistics` calculates medians and means, and `Path` constructs repository-relative paths. Matplotlib draws the figure; Pillow explicitly creates the RGB TIFF production copy.

```python
FIG_W, FIG_H = 6.50, 7.10
```

sets the final figure canvas. The subsequent `mpl.rcParams.update(...)` block locks typography and keeps text editable in SVG/PDF output.

The color constants have one scientific visual role throughout the figure:

```python
BLUE = "#0072B2"
ORANGE = "#D55E00"
```

Blue always represents wall time and orange always represents peak resident memory. Grey is reserved for axes, grid lines, and the descriptive fit.

The three level lists define the benchmark configurations expected in the committed results:

```python
TAXA_LEVELS = [50, 100, 250, 500, 1000, 2000]
SITE_LEVELS = [1000, 5000, 10000, 25000, 50000, 100000]
MODE_LEVELS = ["fixed-exclusive", "parsimony", "both"]
```

## 2. Reading the committed raw measurements

`normalize_header()` converts column labels to a lower-case underscore form. This makes the figure script tolerant of harmless naming differences such as `Wall time (s)` versus `wall_time_s` without changing any numeric values.

`first_present()` searches a small, explicit set of accepted aliases for each required field. The script requires:

- dataset identifier;
- taxon count;
- site count;
- analysis mode;
- replicate number;
- wall time;
- peak resident memory.

`read_raw_runs()` then reads every row from `raw_runs.tsv`. Peak resident memory may be supplied directly in MiB or in KiB; KiB is converted to MiB by division by 1024. Rows that do not contain the core benchmark fields are ignored, while a missing memory field raises an error.

The result is a simple list of dictionaries with standardized keys:

```text
dataset_id
taxa
sites
mode
replicate
wall_s
rss_mib
```

## 3. Selecting the exact manuscript configurations

`group_values()` filters the run-level table for one panel at a time. For example, panel A requests:

```python
x_field="taxa"
levels=TAXA_LEVELS
metric="wall_s"
fixed={"sites": 10000, "mode": "both"}
```

This means: collect wall time for the six prespecified taxon counts, but only from 10,000-site runs in `both` mode.

The function sorts values by replicate number and then applies a deliberately strict check:

```python
if len(reps) != 3:
    raise ValueError(...)
```

The figure is therefore not generated from an incomplete or accidentally duplicated benchmark configuration.

The same logic selects:

- panel B: taxon scaling, peak RSS;
- panel C: site scaling, wall time;
- panel D: site scaling, peak RSS;
- panel E: analysis-mode comparison, wall time;
- panel F: analysis-mode comparison, peak RSS.

## 4. Recalculating summary statistics

`summaries()` calculates three quantities directly from each group of three measured runs:

```python
median
minimum
maximum
```

These become the large filled point and the vertical observed-range line in each configuration.

`linear_fit()` implements ordinary least-squares regression for panels A-D using the configuration **medians**. The fitted form is:

```text
y = slope * x + intercept
```

where the first `x` means multiplication. The function then computes R-squared as:

```text
1 - residual sum of squares / total sum of squares
```

For the committed benchmark values used in the locked render, the recalculated fits are:

```text
Wall time vs taxa:      R2 = 0.997859688
Peak RSS vs taxa:       R2 = 0.999766298
Wall time vs sites:     R2 = 0.999966429
Peak RSS vs sites:      R2 = 0.999967871
```

These are descriptive summaries across the tested ranges, not extrapolative performance models.

## 5. Drawing a scaling panel

`draw_scaling_panel()` is shared by panels A-D. It first applies the common axis formatting, title, labels, and capital panel letter.

For every configuration it draws:

1. a thin vertical line from the smallest to largest measured value;
2. the three measured runs as small semi-transparent points;
3. the median as a larger filled point with a white edge.

The three replicate points receive a very small deterministic **horizontal display offset** so that repeated or nearly repeated measurements can be seen. Their y-values are never changed.

The function then connects the medians with a colored solid line and draws the ordinary least-squares fit as a grey dashed line. The recalculated R-squared is printed in the lower-right corner.

## 6. Drawing the analysis-mode panels

`draw_mode_panel()` uses the same three-run, median, and observed-range representation but does not fit a line across the three analysis modes. The x-axis is categorical and ordered explicitly as:

```text
fixed-exclusive
parsimony
both
```

This makes panels E and F direct comparisons of the same 500-taxon x 10,000-site input matrix.

## 7. Locating repository data

Inside `main()`:

```python
figure_dir = Path(__file__).resolve().parent
repo_root = figure_dir.parents[1]
raw_runs = repo_root / "results" / "04_scalability" / "raw_runs.tsv"
```

finds the source table from the expected repository layout:

```text
repository-root/
    results/04_scalability/raw_runs.tsv
    manuscript/figure_4/make_figure_4.py
```

This keeps machine-specific absolute paths out of the script.

If the committed raw measurements are absent, the script stops with a clear `FileNotFoundError` instead of silently using substitute values.

## 8. Building panels A-F

`plt.subplots(3, 2, ...)` creates the six axes. The next six plotting calls map the benchmark dimensions to the manuscript panels:

```text
A  taxon count -> wall time
B  taxon count -> peak RSS
C  site count  -> wall time
D  site count  -> peak RSS
E  mode        -> wall time
F  mode        -> peak RSS
```

The figure intentionally contains no manuscript title or legend inside the artwork. Those belong in the manuscript and in this directory's README.

## 9. Exporting publication files

The final filenames are declared beside the script:

```text
Figure_4.pdf
Figure_4_editable.svg
Figure_4_preview_600dpi.png
Figure_4_1000dpi.tiff
Figure_4_1000dpi_RGB.tiff
```

PDF and SVG preserve vector geometry. The PNG is written at 600 dpi for the GitHub preview. The TIFF is written at 1000 dpi with lossless LZW compression.

Pillow then reopens the TIFF and explicitly converts it to RGB before writing `Figure_4_1000dpi_RGB.tiff`. This gives a separate production file for workflows that require RGB raster artwork.

## 10. Console verification

After export, the script prints the source data path and the four recalculated fit coefficients/R-squared values. This is a quick check that a re-render used the expected committed measurements.

For the locked package the expected printed values are:

```text
runtime_taxa: slope=0.0146865591398; intercept=0.0954032258065; R2=0.997859688
memory_taxa: slope=0.101840752688; intercept=109.545010753; R2=0.999766298
runtime_sites: slope=0.000313823358512; intercept=0.524956420686; R2=0.999966429
memory_sites: slope=0.00259145824521; intercept=108.396412528; R2=0.999967871
```

## What can be changed safely

Typography, spacing, line weights, colors, and output filenames can be changed without changing the benchmark calculations, provided the plotted source values and panel definitions remain the same.

## What requires scientific re-checking

Re-check the figure and README if any of the following changes:

- benchmark configuration grids;
- number of measured repetitions;
- definition of wall time or peak resident memory;
- benchmark source table;
- summary statistic used for the large point;
- fitted model;
- BRANCHSNV version or benchmark environment.

If the underlying benchmark is rerun against a different software release, regenerate Figure 4 from the new committed `raw_runs.tsv` rather than retaining the old artwork.
