# Figure 4 code walkthrough

This document explains `make_figure_4.py` **line by line** in plain English. It assumes no prior knowledge of Python, Matplotlib, or statistical programming.

## The whole script in one sentence

The script reads the committed run-level benchmark measurements, checks that every manuscript configuration has exactly three measured runs, recalculates medians, observed ranges, and descriptive linear fits, draws panels A–F, and exports the publication artwork.

## A few Python ideas used repeatedly

- `name = value` stores a value under a useful name.
- `function(...)` runs a reusable piece of code; values inside the parentheses are its inputs.
- `for ...:` repeats the indented lines below it, while `if ...:` conditionally runs an indented block.
- `ax.plot(...)`, `ax.scatter(...)`, and `ax.text(...)` draw lines, points, and text in a Matplotlib axes.
- Indentation is part of Python syntax: lines shifted to the right belong to the block immediately above them.

The important scientific distinction is that fixed configuration lists define **which committed benchmark runs belong in the figure**; the measured wall-time and memory values themselves are read from `results/04_scalability/raw_runs.tsv`.

## Line-by-line explanation

### Line 1

```python
#!/usr/bin/env python3
```
Shebang line allowing the file to be run directly with the environment's Python 3 interpreter on Unix-like systems.

### Line 2

```python
"""Generate manuscript Figure 4 from committed BRANCHSNV scalability runs.
```
Starts or continues the script/function documentation string describing what this code is intended to do.

### Line 3

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 4

```python
The benchmark experiment itself lives in experiments/04_scalability/. This script
```
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 5

```python
only turns the committed run-level measurements in results/04_scalability/raw_runs.tsv
```
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 6

```python
into the publication figure. It deliberately does not regenerate benchmark inputs or
```
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 7

```python
rerun BRANCHSNV.
```
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 8

```python
"""
```
Closes the multi-line documentation string started above.

### Line 9

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 10

```python
from __future__ import annotations
```
Enables postponed evaluation of type annotations, making the type hints used later more flexible.

### Line 11

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 12

```python
import csv
```
Imports `csv` functionality needed later in the script.

### Line 13

```python
import math
```
Imports `math` functionality needed later in the script.

### Line 14

```python
import re
```
Imports `re` functionality needed later in the script.

### Line 15

```python
import statistics
```
Imports `statistics` functionality needed later in the script.

### Line 16

```python
from collections import defaultdict
```
Imports `collections` functionality needed later in the script.

### Line 17

```python
from pathlib import Path
```
Imports `pathlib` functionality needed later in the script.

### Line 18

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 19

```python
import matplotlib as mpl
```
Imports `matplotlib` functionality needed later in the script.

### Line 20

```python
import matplotlib.pyplot as plt
```
Imports `matplotlib.pyplot` functionality needed later in the script.

### Line 21

```python
from PIL import Image
```
Imports `PIL` functionality needed later in the script.

### Line 22

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 23

```python
# -----------------------------------------------------------------------------
```
Visual separator comment marking a new major section of the script.

### Line 24

```python
# Locked publication style
```
Comment for the reader; it documents the purpose of the code that follows and is not executed by Python.

### Line 25

```python
# -----------------------------------------------------------------------------
```
Visual separator comment marking a new major section of the script.

### Line 26

```python
FIG_W, FIG_H = 6.50, 7.10
```
Sets the physical width and height of the final manuscript artwork in inches.

### Line 27

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 28

```python
mpl.rcParams.update({
```
Starts or closes the global Matplotlib style settings used for the locked publication render.

### Line 29

```python
    "font.family": "Arimo",
```
Sets this specific global typography or vector-export option for the figure.

### Line 30

```python
    "font.size": 7.0,
```
Sets this specific global typography or vector-export option for the figure.

### Line 31

```python
    "axes.titlesize": 7.8,
```
Sets this specific global typography or vector-export option for the figure.

### Line 32

```python
    "axes.labelsize": 7.2,
```
Sets this specific global typography or vector-export option for the figure.

### Line 33

```python
    "xtick.labelsize": 6.5,
```
Sets this specific global typography or vector-export option for the figure.

### Line 34

```python
    "ytick.labelsize": 6.5,
```
Sets this specific global typography or vector-export option for the figure.

### Line 35

```python
    "svg.fonttype": "none",
```
Sets this specific global typography or vector-export option for the figure.

### Line 36

```python
    "pdf.fonttype": 42,
```
Sets this specific global typography or vector-export option for the figure.

### Line 37

```python
    "ps.fonttype": 42,
```
Sets this specific global typography or vector-export option for the figure.

### Line 38

```python
})
```
Starts or closes the global Matplotlib style settings used for the locked publication render.

### Line 39

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 40

```python
INK = "#222222"
```
Defines the near-black color used for ordinary text and labels.

### Line 41

```python
GREY = "#777777"
```
Defines the medium-grey color used for secondary plotting elements.

### Line 42

```python
LIGHT = "#E5E5E5"
```
Defines the light-grey color used for horizontal grid lines.

### Line 43

```python
FIT_GREY = "#9A9A9A"
```
Defines the grey used for the dashed descriptive linear-fit line.

### Line 44

```python
BLUE = "#0072B2"
```
Defines the blue used consistently for wall-time or exact-oracle visual elements.

### Line 45

```python
ORANGE = "#D55E00"
```
Defines the orange used consistently for memory/scalability visual elements.

### Line 46

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 47

```python
TAXA_LEVELS = [50, 100, 250, 500, 1000, 2000]
```
Lists the six taxon counts that must be present for the manuscript taxon-scaling panels.

### Line 48

```python
SITE_LEVELS = [1000, 5000, 10000, 25000, 50000, 100000]
```
Lists the six alignment lengths that must be present for the manuscript site-scaling panels.

### Line 49

```python
MODE_LEVELS = ["fixed-exclusive", "parsimony", "both"]
```
Fixes the displayed order of the three BRANCHSNV analysis modes.

### Line 50

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 51

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 52

```python
# -----------------------------------------------------------------------------
```
Visual separator comment marking a new major section of the script.

### Line 53

```python
# Input parsing and validation
```
Comment for the reader; it documents the purpose of the code that follows and is not executed by Python.

### Line 54

```python
# -----------------------------------------------------------------------------
```
Visual separator comment marking a new major section of the script.

### Line 55

```python
def normalize_header(value: str) -> str:
```
Defines a helper that converts a table header into a consistent lower-case underscore form.

### Line 56

```python
    """Normalize a TSV column name so small naming differences are tolerated."""
```
Starts or continues the script/function documentation string describing what this code is intended to do.

### Line 57

```python
    value = value.strip().lower()
```
Removes surrounding whitespace from the header and converts it to lower case.

### Line 58

```python
    value = re.sub(r"[^a-z0-9]+", "_", value)
```
Replaces any run of non-alphanumeric header characters with a single underscore.

### Line 59

```python
    return value.strip("_")
```
Returns this calculated value to the code that called the current function.

### Line 60

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 61

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 62

```python
def first_present(row: dict[str, str], aliases: tuple[str, ...]) -> str | None:
```
Defines a helper that returns the first non-empty value found among several accepted column aliases.

### Line 63

```python
    """Return the first non-empty value present under any accepted column alias."""
```
Starts or continues the script/function documentation string describing what this code is intended to do.

### Line 64

```python
    for alias in aliases:
```
Starts a loop that repeats the following indented code once for each item in the specified collection.

### Line 65

```python
        if alias in row and str(row[alias]).strip() != "":
```
Tests this condition; the following indented block runs only when the condition is true.

### Line 66

```python
            return str(row[alias]).strip()
```
Returns this calculated value to the code that called the current function.

### Line 67

```python
    return None
```
Returns this calculated value to the code that called the current function.

### Line 68

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 69

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 70

```python
def as_int(value: str | None, label: str) -> int:
```
Defines a strict conversion helper for required integer-like values.

### Line 71

```python
    if value is None:
```
Tests this condition; the following indented block runs only when the condition is true.

### Line 72

```python
        raise ValueError(f"Missing required value: {label}")
```
Stops execution with an explicit error rather than allowing an invalid or incomplete input to be used silently.

### Line 73

```python
    return int(float(value))
```
Returns this calculated value to the code that called the current function.

### Line 74

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 75

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 76

```python
def as_float(value: str | None, label: str) -> float:
```
Defines a strict conversion helper for required floating-point values.

### Line 77

```python
    if value is None:
```
Tests this condition; the following indented block runs only when the condition is true.

### Line 78

```python
        raise ValueError(f"Missing required value: {label}")
```
Stops execution with an explicit error rather than allowing an invalid or incomplete input to be used silently.

### Line 79

```python
    return float(value)
```
Returns this calculated value to the code that called the current function.

### Line 80

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 81

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 82

```python
def read_raw_runs(path: Path) -> list[dict[str, object]]:
```
Defines the parser that reads the committed run-level benchmark TSV into standardized Python dictionaries.

### Line 83

```python
    """Read the committed run-level benchmark table using conservative aliases."""
```
Starts or continues the script/function documentation string describing what this code is intended to do.

### Line 84

```python
    with path.open("r", encoding="utf-8", newline="") as handle:
```
Opens this resource using a context manager so it is closed cleanly when the indented block finishes.

### Line 85

```python
        reader = csv.DictReader(handle, delimiter="\t")
```
Creates a tab-delimited dictionary reader so each benchmark row can be accessed by column name.

### Line 86

```python
        if reader.fieldnames is None:
```
Tests this condition; the following indented block runs only when the condition is true.

### Line 87

```python
            raise ValueError(f"No TSV header found in {path}")
```
Stops execution with an explicit error rather than allowing an invalid or incomplete input to be used silently.

### Line 88

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 89

```python
        normalized = [normalize_header(name) for name in reader.fieldnames]
```
Normalizes every input column name once so accepted aliases can be matched consistently.

### Line 90

```python
        rows: list[dict[str, object]] = []
```
Creates the list that will accumulate all successfully parsed benchmark measurements.

### Line 91

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 92

```python
        for original in reader:
```
Starts a loop that repeats the following indented code once for each item in the specified collection.

### Line 93

```python
            row = {
```
Starts rebuilding the current row with normalized column names.

### Line 94

```python
                normalized[i]: (original.get(reader.fieldnames[i]) or "")
```
Uses the normalized header at this column position as the new dictionary key.

### Line 95

```python
                for i in range(len(reader.fieldnames))
```
Starts a loop that repeats the following indented code once for each item in the specified collection.

### Line 96

```python
            }
```
Closes or continues the multi-line Python expression started on the preceding lines.

### Line 97

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 98

```python
            dataset = first_present(row, ("dataset_id", "dataset_identifier", "dataset"))
```
Looks up this required benchmark field using the explicit set of accepted column-name aliases.

### Line 99

```python
            taxa = first_present(row, ("taxa", "number_of_taxa", "ntax"))
```
Looks up this required benchmark field using the explicit set of accepted column-name aliases.

### Line 100

```python
            sites = first_present(row, ("sites", "number_of_sites", "nchar"))
```
Looks up this required benchmark field using the explicit set of accepted column-name aliases.

### Line 101

```python
            mode = first_present(row, ("mode", "analysis_mode"))
```
Looks up this required benchmark field using the explicit set of accepted column-name aliases.

### Line 102

```python
            replicate = first_present(row, ("replicate", "rep", "run"))
```
Looks up this required benchmark field using the explicit set of accepted column-name aliases.

### Line 103

```python
            wall = first_present(
```
Looks up this required benchmark field using the explicit set of accepted column-name aliases.

### Line 104

```python
                row,
```
Supplies another argument or value to the multi-line expression being constructed.

### Line 105

```python
                ("wall_time_s", "wall_seconds", "wall_time", "elapsed_seconds", "elapsed_s"),
```
Supplies another argument or value to the multi-line expression being constructed.

### Line 106

```python
            )
```
Closes or continues the multi-line Python expression started on the preceding lines.

### Line 107

```python
            rss_mib = first_present(
```
Looks up this required benchmark field using the explicit set of accepted column-name aliases.

### Line 108

```python
                row,
```
Supplies another argument or value to the multi-line expression being constructed.

### Line 109

```python
                ("peak_rss_mib", "peak_resident_memory_mib", "peak_resident_set_size_mib"),
```
Supplies another argument or value to the multi-line expression being constructed.

### Line 110

```python
            )
```
Closes or continues the multi-line Python expression started on the preceding lines.

### Line 111

```python
            rss_kib = first_present(
```
Looks up this required benchmark field using the explicit set of accepted column-name aliases.

### Line 112

```python
                row,
```
Supplies another argument or value to the multi-line expression being constructed.

### Line 113

```python
                ("peak_rss_kib", "peak_resident_memory_kib", "maximum_resident_set_size_kib"),
```
Supplies another argument or value to the multi-line expression being constructed.

### Line 114

```python
            )
```
Closes or continues the multi-line Python expression started on the preceding lines.

### Line 115

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 116

```python
            if not all((dataset, taxa, sites, mode, wall)):
```
Tests this condition; the following indented block runs only when the condition is true.

### Line 117

```python
                continue
```
Skips the remainder of this loop iteration and moves directly to the next input row.

### Line 118

```python
            if rss_mib is None and rss_kib is None:
```
Tests this condition; the following indented block runs only when the condition is true.

### Line 119

```python
                raise ValueError("Raw benchmark table lacks peak-RSS MiB or KiB values")
```
Stops execution with an explicit error rather than allowing an invalid or incomplete input to be used silently.

### Line 120

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 121

```python
            rows.append({
```
Starts appending one standardized benchmark measurement to the parsed row list.

### Line 122

```python
                "dataset_id": dataset,
```
Stores this standardized field in the parsed benchmark row used by all later calculations.

### Line 123

```python
                "taxa": as_int(taxa, "taxa"),
```
Stores this standardized field in the parsed benchmark row used by all later calculations.

### Line 124

```python
                "sites": as_int(sites, "sites"),
```
Stores this standardized field in the parsed benchmark row used by all later calculations.

### Line 125

```python
                "mode": mode,
```
Stores this standardized field in the parsed benchmark row used by all later calculations.

### Line 126

```python
                "replicate": as_int(replicate or "1", "replicate"),
```
Stores this standardized field in the parsed benchmark row used by all later calculations.

### Line 127

```python
                "wall_s": as_float(wall, "wall time"),
```
Stores this standardized field in the parsed benchmark row used by all later calculations.

### Line 128

```python
                "rss_mib": as_float(rss_mib, "peak RSS MiB")
```
Stores this standardized field in the parsed benchmark row used by all later calculations.

### Line 129

```python
                if rss_mib is not None
```
Tests this condition; the following indented block runs only when the condition is true.

### Line 130

```python
                else as_float(rss_kib, "peak RSS KiB") / 1024.0,
```
Begins the alternative branch used when the preceding condition is false.

### Line 131

```python
            })
```
Starts or closes the global Matplotlib style settings used for the locked publication render.

### Line 132

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 133

```python
    if not rows:
```
Tests this condition; the following indented block runs only when the condition is true.

### Line 134

```python
        raise ValueError(f"No benchmark rows could be parsed from {path}")
```
Stops execution with an explicit error rather than allowing an invalid or incomplete input to be used silently.

### Line 135

```python
    return rows
```
Returns this calculated value to the code that called the current function.

### Line 136

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 137

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 138

```python
def group_values(
```
Defines the selector that extracts exactly three measured replicates for each requested benchmark configuration.

### Line 139

```python
    rows: list[dict[str, object]],
```
Creates the list that will accumulate all successfully parsed benchmark measurements.

### Line 140

```python
    *,
```
Supplies another argument or value to the multi-line expression being constructed.

### Line 141

```python
    x_field: str,
```
Supplies another argument or value to the multi-line expression being constructed.

### Line 142

```python
    levels: list[object],
```
Supplies another argument or value to the multi-line expression being constructed.

### Line 143

```python
    metric: str,
```
Supplies another argument or value to the multi-line expression being constructed.

### Line 144

```python
    fixed: dict[str, object],
```
Supplies another argument or value to the multi-line expression being constructed.

### Line 145

```python
) -> list[list[float]]:
```
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 146

```python
    """Collect exactly three replicate measurements for every requested level."""
```
Starts or continues the script/function documentation string describing what this code is intended to do.

### Line 147

```python
    grouped: dict[object, list[tuple[int, float]]] = defaultdict(list)
```
Creates a dictionary-of-lists that will collect replicate values for each requested x-axis level.

### Line 148

```python
    for row in rows:
```
Starts a loop that repeats the following indented code once for each item in the specified collection.

### Line 149

```python
        if all(row[key] == value for key, value in fixed.items()):
```
Tests this condition; the following indented block runs only when the condition is true.

### Line 150

```python
            grouped[row[x_field]].append((int(row["replicate"]), float(row[metric])))
```
Adds the replicate number and selected metric value under the appropriate taxon/site/mode level.

### Line 151

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 152

```python
    result: list[list[float]] = []
```
Creates the ordered result list that will follow the explicitly requested level order.

### Line 153

```python
    for level in levels:
```
Starts a loop that repeats the following indented code once for each item in the specified collection.

### Line 154

```python
        reps = sorted(grouped.get(level, []), key=lambda item: item[0])
```
Sorts the measurements for this level by replicate number so their display order is deterministic.

### Line 155

```python
        if len(reps) != 3:
```
Tests this condition; the following indented block runs only when the condition is true.

### Line 156

```python
            raise ValueError(
```
Stops execution with an explicit error rather than allowing an invalid or incomplete input to be used silently.

### Line 157

```python
                f"Expected 3 measured runs for {x_field}={level} with {fixed}; found {len(reps)}"
```
Builds formatted text by inserting the current calculated value into the displayed string.

### Line 158

```python
            )
```
Closes or continues the multi-line Python expression started on the preceding lines.

### Line 159

```python
        result.append([value for _, value in reps])
```
Adds only the three metric values, now in replicate order, to the panel data.

### Line 160

```python
    return result
```
Returns this calculated value to the code that called the current function.

### Line 161

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 162

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 163

```python
# -----------------------------------------------------------------------------
```
Visual separator comment marking a new major section of the script.

### Line 164

```python
# Descriptive summaries and fits
```
Comment for the reader; it documents the purpose of the code that follows and is not executed by Python.

### Line 165

```python
# -----------------------------------------------------------------------------
```
Visual separator comment marking a new major section of the script.

### Line 166

```python
def summaries(replicates: list[list[float]]) -> tuple[list[float], list[float], list[float]]:
```
Defines the helper that calculates median, minimum, and maximum across each three-run replicate group.

### Line 167

```python
    medians = [statistics.median(values) for values in replicates]
```
Calculates the median of each three-run replicate group.

### Line 168

```python
    minima = [min(values) for values in replicates]
```
Calculates the smallest observed value in each three-run replicate group.

### Line 169

```python
    maxima = [max(values) for values in replicates]
```
Calculates the largest observed value in each three-run replicate group.

### Line 170

```python
    return medians, minima, maxima
```
Returns this calculated value to the code that called the current function.

### Line 171

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 172

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 173

```python
def linear_fit(xs: list[float], ys: list[float]) -> tuple[float, float, float]:
```
Defines the ordinary least-squares helper used for the descriptive scaling fits in panels A-D.

### Line 174

```python
    """Ordinary least-squares y = slope*x + intercept, plus R-squared."""
```
Starts or continues the script/function documentation string describing what this code is intended to do.

### Line 175

```python
    xbar = statistics.mean(xs)
```
Calculates the arithmetic mean of the x values for the least-squares fit.

### Line 176

```python
    ybar = statistics.mean(ys)
```
Calculates the arithmetic mean of the median y values for the least-squares fit.

### Line 177

```python
    ssx = sum((x - xbar) ** 2 for x in xs)
```
Calculates the total squared spread of the x values around their mean.

### Line 178

```python
    if ssx == 0:
```
Tests this condition; the following indented block runs only when the condition is true.

### Line 179

```python
        raise ValueError("Cannot fit a line when all x values are identical")
```
Stops execution with an explicit error rather than allowing an invalid or incomplete input to be used silently.

### Line 180

```python
    slope = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys)) / ssx
```
Calculates the ordinary least-squares slope from the covariance numerator divided by the x sum of squares.

### Line 181

```python
    intercept = ybar - slope * xbar
```
Calculates the fitted y-intercept from the two means and the fitted slope.

### Line 182

```python
    fitted = [slope * x + intercept for x in xs]
```
Calculates the fitted y value at every observed x coordinate.

### Line 183

```python
    sst = sum((y - ybar) ** 2 for y in ys)
```
Calculates total y variation around the mean for the R-squared denominator.

### Line 184

```python
    sse = sum((y - fit) ** 2 for y, fit in zip(ys, fitted))
```
Calculates the residual squared error between observed medians and fitted values.

### Line 185

```python
    r2 = 1.0 - sse / sst if sst else 1.0
```
Calculates R-squared, using 1.0 for the degenerate zero-variance case.

### Line 186

```python
    return slope, intercept, r2
```
Returns this calculated value to the code that called the current function.

### Line 187

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 188

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 189

```python
def format_r2(r2: float) -> str:
```
Defines a formatting helper that chooses the displayed precision for R-squared.

### Line 190

```python
    if r2 >= 0.9999:
```
Tests this condition; the following indented block runs only when the condition is true.

### Line 191

```python
        return f"{r2:.5f}"
```
Returns this calculated value to the code that called the current function.

### Line 192

```python
    return f"{r2:.4f}"
```
Returns this calculated value to the code that called the current function.

### Line 193

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 194

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 195

```python
# -----------------------------------------------------------------------------
```
Visual separator comment marking a new major section of the script.

### Line 196

```python
# Plotting helpers
```
Comment for the reader; it documents the purpose of the code that follows and is not executed by Python.

### Line 197

```python
# -----------------------------------------------------------------------------
```
Visual separator comment marking a new major section of the script.

### Line 198

```python
def style_axis(ax: plt.Axes) -> None:
```
Defines the common axis styling shared by all six Figure 4 panels.

### Line 199

```python
    ax.set_axisbelow(True)
```
Places grid lines behind the plotted data rather than on top of the points.

### Line 200

```python
    ax.grid(axis="y", color=LIGHT, linewidth=0.6)
```
Draws light horizontal reference grid lines only.

### Line 201

```python
    ax.spines["top"].set_visible(False)
```
Hides this unnecessary outer axis spine to keep the panel visually light.

### Line 202

```python
    ax.spines["right"].set_visible(False)
```
Hides this unnecessary outer axis spine to keep the panel visually light.

### Line 203

```python
    ax.spines["left"].set_color("#999999")
```
Sets this remaining axis spine to a neutral grey.

### Line 204

```python
    ax.spines["bottom"].set_color("#999999")
```
Sets this remaining axis spine to a neutral grey.

### Line 205

```python
    ax.spines["left"].set_linewidth(0.65)
```
Sets a thin line width for this remaining axis spine.

### Line 206

```python
    ax.spines["bottom"].set_linewidth(0.65)
```
Sets a thin line width for this remaining axis spine.

### Line 207

```python
    ax.tick_params(axis="both", colors=INK, width=0.55, length=2.8, pad=2)
```
Applies consistent tick color, width, length, and padding to both axes.

### Line 208

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 209

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 210

```python
def panel_label(ax: plt.Axes, label: str) -> None:
```
Defines the helper that places the bold capital panel label just above the plotting area.

### Line 211

```python
    ax.text(-0.14, 1.105, label, transform=ax.transAxes, fontsize=9.3,
```
Interprets the coordinates in axes-relative units, where 0 to 1 spans the full drawing area.

### Line 212

```python
            fontweight="bold", color=INK, ha="left", va="top")
```
Stores the value calculated on this line in `fontweight` for use by later code.

### Line 213

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 214

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 215

```python
def jitter_for(levels: list[float]) -> list[float]:
```
Defines the helper that calculates small deterministic horizontal offsets for the three replicate points.

### Line 216

```python
    diffs = [b - a for a, b in zip(levels[:-1], levels[1:]) if b > a]
```
Calculates positive gaps between adjacent numeric x-axis levels.

### Line 217

```python
    spacing = min(diffs) if diffs else 1.0
```
Uses the smallest x-axis gap as the scale for replicate-point jitter.

### Line 218

```python
    return [-0.07 * spacing, 0.0, 0.07 * spacing]
```
Returns this calculated value to the code that called the current function.

### Line 219

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 220

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 221

```python
def draw_scaling_panel(
```
Defines the shared plotting routine for the four continuous scaling panels A-D.

### Line 222

```python
    ax: plt.Axes,
```
Supplies another argument or value to the multi-line expression being constructed.

### Line 223

```python
    xs: list[float],
```
Supplies another argument or value to the multi-line expression being constructed.

### Line 224

```python
    reps: list[list[float]],
```
Supplies another argument or value to the multi-line expression being constructed.

### Line 225

```python
    *,
```
Supplies another argument or value to the multi-line expression being constructed.

### Line 226

```python
    color: str,
```
Supplies another argument or value to the multi-line expression being constructed.

### Line 227

```python
    title: str,
```
Supplies another argument or value to the multi-line expression being constructed.

### Line 228

```python
    xlabel: str,
```
Supplies another argument or value to the multi-line expression being constructed.

### Line 229

```python
    ylabel: str,
```
Supplies another argument or value to the multi-line expression being constructed.

### Line 230

```python
    label: str,
```
Supplies another argument or value to the multi-line expression being constructed.

### Line 231

```python
) -> tuple[float, float, float]:
```
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 232

```python
    style_axis(ax)
```
Applies the common Figure 4 axis styling to this panel.

### Line 233

```python
    panel_label(ax, label)
```
Adds the supplied capital panel label.

### Line 234

```python
    ax.set_title(title, pad=5, color=INK)
```
Sets the short panel heading above the axes.

### Line 235

```python
    ax.set_xlabel(xlabel, color=INK, labelpad=3)
```
Sets the x-axis label and its spacing.

### Line 236

```python
    ax.set_ylabel(ylabel, color=INK, labelpad=3)
```
Sets the y-axis label and its spacing.

### Line 237

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 238

```python
    medians, minima, maxima = summaries(reps)
```
Calculates the median and observed range for every three-run configuration.

### Line 239

```python
    jitter = jitter_for(xs)
```
Calculates deterministic horizontal offsets for the three individual replicate points.

### Line 240

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 241

```python
    for x, values, lo, hi, med in zip(xs, reps, minima, maxima, medians):
```
Starts a loop that repeats the following indented code once for each item in the specified collection.

### Line 242

```python
        ax.vlines(x, lo, hi, color=color, linewidth=0.75, alpha=0.70, zorder=2)
```
Draws the thin vertical line spanning the observed minimum to maximum for this configuration.

### Line 243

```python
        for offset, value in zip(jitter, values):
```
Starts a loop that repeats the following indented code once for each item in the specified collection.

### Line 244

```python
            ax.scatter(x + offset, value, s=16, facecolor=color, edgecolor=color,
```
Uses the category color for the outline of the box.

### Line 245

```python
                       linewidth=0.55, alpha=0.28, zorder=3)
```
Stores the value calculated on this line in `linewidth` for use by later code.

### Line 246

```python
        ax.scatter(x, med, s=24, facecolor=color, edgecolor="white",
```
Uses the category color for the outline of the box.

### Line 247

```python
                   linewidth=0.55, zorder=4)
```
Stores the value calculated on this line in `linewidth` for use by later code.

### Line 248

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 249

```python
    ax.plot(xs, medians, color=color, linewidth=1.25, zorder=3)
```
Connects the configuration medians with the category-colored solid line.

### Line 250

```python
    slope, intercept, r2 = linear_fit(xs, medians)
```
Fits the descriptive ordinary least-squares line to the configuration medians.

### Line 251

```python
    fit_x = [min(xs), max(xs)]
```
Uses the smallest and largest observed x values as the endpoints of the displayed fit line.

### Line 252

```python
    fit_y = [slope * x + intercept for x in fit_x]
```
Calculates the fitted y values at those two displayed endpoints.

### Line 253

```python
    ax.plot(fit_x, fit_y, color=FIT_GREY, linewidth=0.85,
```
Starts drawing the descriptive fit as a grey dashed line behind the measured data.

### Line 254

```python
            linestyle=(0, (3, 3)), zorder=1)
```
Uses an even dash-gap pattern for the grey descriptive fit line.

### Line 255

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 256

```python
    ax.set_xticks(xs)
```
Places x-axis ticks exactly at the measured taxon or site counts.

### Line 257

```python
    ax.set_xticklabels([f"{int(x):,}" for x in xs], rotation=45, ha="right")
```
Formats the numeric x-axis labels with thousands separators and rotates them to avoid collisions.

### Line 258

```python
    ax.tick_params(axis="x", labelsize=5.8)
```
Applies consistent tick color, width, length, and padding to both axes.

### Line 259

```python
    ax.margins(x=0.05, y=0.08)
```
Adds a small amount of plotting-space padding so points and range lines are not clipped by the axes.

### Line 260

```python
    ax.text(0.98, 0.035, rf"$R^2$ = {format_r2(r2)}", transform=ax.transAxes,
```
Interprets the coordinates in axes-relative units, where 0 to 1 spans the full drawing area.

### Line 261

```python
            ha="right", va="bottom", fontsize=6.6, color=INK)
```
Stores the value calculated on this line in `ha` for use by later code.

### Line 262

```python
    return slope, intercept, r2
```
Returns this calculated value to the code that called the current function.

### Line 263

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 264

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 265

```python
def draw_mode_panel(
```
Defines the plotting routine for the two categorical analysis-mode panels E-F.

### Line 266

```python
    ax: plt.Axes,
```
Supplies another argument or value to the multi-line expression being constructed.

### Line 267

```python
    reps: list[list[float]],
```
Supplies another argument or value to the multi-line expression being constructed.

### Line 268

```python
    *,
```
Supplies another argument or value to the multi-line expression being constructed.

### Line 269

```python
    color: str,
```
Supplies another argument or value to the multi-line expression being constructed.

### Line 270

```python
    ylabel: str,
```
Supplies another argument or value to the multi-line expression being constructed.

### Line 271

```python
    label: str,
```
Supplies another argument or value to the multi-line expression being constructed.

### Line 272

```python
) -> None:
```
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 273

```python
    style_axis(ax)
```
Applies the common Figure 4 axis styling to this panel.

### Line 274

```python
    panel_label(ax, label)
```
Adds the supplied capital panel label.

### Line 275

```python
    ax.set_title("Analysis mode", pad=5, color=INK)
```
Sets the short panel heading above the axes.

### Line 276

```python
    ax.set_xlabel("Analysis mode", color=INK, labelpad=3)
```
Sets the x-axis label and its spacing.

### Line 277

```python
    ax.set_ylabel(ylabel, color=INK, labelpad=3)
```
Sets the y-axis label and its spacing.

### Line 278

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 279

```python
    medians, minima, maxima = summaries(reps)
```
Calculates the median and observed range for every three-run configuration.

### Line 280

```python
    xpos = list(range(len(MODE_LEVELS)))
```
Creates numeric x positions 0, 1, and 2 for the three categorical analysis modes.

### Line 281

```python
    jitter = [-0.075, 0.0, 0.075]
```
Uses fixed symmetric horizontal offsets for the three replicate points in categorical mode panels.

### Line 282

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 283

```python
    for x, values, lo, hi, med in zip(xpos, reps, minima, maxima, medians):
```
Starts a loop that repeats the following indented code once for each item in the specified collection.

### Line 284

```python
        ax.vlines(x, lo, hi, color=color, linewidth=0.75, alpha=0.75, zorder=2)
```
Draws the thin vertical line spanning the observed minimum to maximum for this configuration.

### Line 285

```python
        for offset, value in zip(jitter, values):
```
Starts a loop that repeats the following indented code once for each item in the specified collection.

### Line 286

```python
            ax.scatter(x + offset, value, s=16, facecolor=color, edgecolor=color,
```
Uses the category color for the outline of the box.

### Line 287

```python
                       linewidth=0.55, alpha=0.28, zorder=3)
```
Stores the value calculated on this line in `linewidth` for use by later code.

### Line 288

```python
        ax.scatter(x, med, s=24, facecolor=color, edgecolor="white",
```
Uses the category color for the outline of the box.

### Line 289

```python
                   linewidth=0.55, zorder=4)
```
Stores the value calculated on this line in `linewidth` for use by later code.

### Line 290

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 291

```python
    ax.set_xticks(xpos)
```
Places categorical x-axis ticks at the three mode positions.

### Line 292

```python
    ax.set_xticklabels(MODE_LEVELS)
```
Formats the numeric x-axis labels with thousands separators and rotates them to avoid collisions.

### Line 293

```python
    ax.margins(x=0.10, y=0.12)
```
Adds a small amount of plotting-space padding so points and range lines are not clipped by the axes.

### Line 294

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 295

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 296

```python
# -----------------------------------------------------------------------------
```
Visual separator comment marking a new major section of the script.

### Line 297

```python
# Main figure assembly and export
```
Comment for the reader; it documents the purpose of the code that follows and is not executed by Python.

### Line 298

```python
# -----------------------------------------------------------------------------
```
Visual separator comment marking a new major section of the script.

### Line 299

```python
def main() -> None:
```
Defines the main entry point that loads the data, draws the figure, exports all artwork formats, and writes support files.

### Line 300

```python
    figure_dir = Path(__file__).resolve().parent
```
Locates the directory containing `make_figure_4.py`; all artwork is written beside the script.

### Line 301

```python
    repo_root = figure_dir.parents[1]
```
Moves two directory levels upward to locate the validation repository root.

### Line 302

```python
    raw_runs = repo_root / "results" / "04_scalability" / "raw_runs.tsv"
```
Constructs the repository-relative path to the committed run-level benchmark measurements.

### Line 303

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 304

```python
    if not raw_runs.exists():
```
Tests this condition; the following indented block runs only when the condition is true.

### Line 305

```python
        raise FileNotFoundError(
```
Stops execution with an explicit error rather than allowing an invalid or incomplete input to be used silently.

### Line 306

```python
            f"Expected committed benchmark measurements at {raw_runs}. "
```
Builds formatted text by inserting the current calculated value into the displayed string.

### Line 307

```python
            "Run this script from its manuscript/figure_4 location inside the validation repository."
```
Provides this literal text value to the surrounding data structure or drawing call.

### Line 308

```python
        )
```
Closes or continues the multi-line Python expression started on the preceding lines.

### Line 309

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 310

```python
    rows = read_raw_runs(raw_runs)
```
Parses and standardizes all committed benchmark measurements.

### Line 311

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 312

```python
    taxon_wall = group_values(
```
Starts selecting the exact three-run measurements required for this manuscript panel.

### Line 313

```python
        rows, x_field="taxa", levels=TAXA_LEVELS, metric="wall_s",
```
Specifies the x-axis variable, level order, and measured metric for this panel selection.

### Line 314

```python
        fixed={"sites": 10000, "mode": "both"},
```
Specifies the benchmark dimensions that must stay fixed while the panel's x variable changes.

### Line 315

```python
    )
```
Closes or continues the multi-line Python expression started on the preceding lines.

### Line 316

```python
    taxon_mem = group_values(
```
Starts selecting the exact three-run measurements required for this manuscript panel.

### Line 317

```python
        rows, x_field="taxa", levels=TAXA_LEVELS, metric="rss_mib",
```
Specifies the x-axis variable, level order, and measured metric for this panel selection.

### Line 318

```python
        fixed={"sites": 10000, "mode": "both"},
```
Specifies the benchmark dimensions that must stay fixed while the panel's x variable changes.

### Line 319

```python
    )
```
Closes or continues the multi-line Python expression started on the preceding lines.

### Line 320

```python
    site_wall = group_values(
```
Starts selecting the exact three-run measurements required for this manuscript panel.

### Line 321

```python
        rows, x_field="sites", levels=SITE_LEVELS, metric="wall_s",
```
Specifies the x-axis variable, level order, and measured metric for this panel selection.

### Line 322

```python
        fixed={"taxa": 250, "mode": "both"},
```
Specifies the benchmark dimensions that must stay fixed while the panel's x variable changes.

### Line 323

```python
    )
```
Closes or continues the multi-line Python expression started on the preceding lines.

### Line 324

```python
    site_mem = group_values(
```
Starts selecting the exact three-run measurements required for this manuscript panel.

### Line 325

```python
        rows, x_field="sites", levels=SITE_LEVELS, metric="rss_mib",
```
Specifies the x-axis variable, level order, and measured metric for this panel selection.

### Line 326

```python
        fixed={"taxa": 250, "mode": "both"},
```
Specifies the benchmark dimensions that must stay fixed while the panel's x variable changes.

### Line 327

```python
    )
```
Closes or continues the multi-line Python expression started on the preceding lines.

### Line 328

```python
    mode_wall = group_values(
```
Starts selecting the exact three-run measurements required for this manuscript panel.

### Line 329

```python
        rows, x_field="mode", levels=MODE_LEVELS, metric="wall_s",
```
Specifies the x-axis variable, level order, and measured metric for this panel selection.

### Line 330

```python
        fixed={"taxa": 500, "sites": 10000},
```
Specifies the benchmark dimensions that must stay fixed while the panel's x variable changes.

### Line 331

```python
    )
```
Closes or continues the multi-line Python expression started on the preceding lines.

### Line 332

```python
    mode_mem = group_values(
```
Starts selecting the exact three-run measurements required for this manuscript panel.

### Line 333

```python
        rows, x_field="mode", levels=MODE_LEVELS, metric="rss_mib",
```
Specifies the x-axis variable, level order, and measured metric for this panel selection.

### Line 334

```python
        fixed={"taxa": 500, "sites": 10000},
```
Specifies the benchmark dimensions that must stay fixed while the panel's x variable changes.

### Line 335

```python
    )
```
Closes or continues the multi-line Python expression started on the preceding lines.

### Line 336

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 337

```python
    fig, axes = plt.subplots(3, 2, figsize=(FIG_W, FIG_H))
```
Creates the 3-by-2 grid of six Matplotlib axes used for panels A-F.

### Line 338

```python
    fig.subplots_adjust(left=0.105, right=0.985, bottom=0.065, top=0.975,
```
Minimizes outer whitespace around the schematic while leaving a small safety margin.

### Line 339

```python
                        wspace=0.30, hspace=0.43)
```
Sets horizontal and vertical separation between panels so labels do not collide.

### Line 340

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 341

```python
    fits = []
```
Creates a list that will store the four scaling-panel fit results for console verification.

### Line 342

```python
    fits.append(draw_scaling_panel(
```
Draws one scaling panel and stores its slope, intercept, and R-squared result.

### Line 343

```python
        axes[0, 0], TAXA_LEVELS, taxon_wall, color=BLUE,
```
Supplies the target subplot, data series, scientific color, labels, and panel letter to the plotting helper.

### Line 344

```python
        title="Taxon scaling", xlabel="Number of taxa", ylabel="Wall time (s)", label="A",
```
Provides the remaining title/axis-label arguments for this panel call.

### Line 345

```python
    ))
```
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 346

```python
    fits.append(draw_scaling_panel(
```
Draws one scaling panel and stores its slope, intercept, and R-squared result.

### Line 347

```python
        axes[0, 1], TAXA_LEVELS, taxon_mem, color=ORANGE,
```
Supplies the target subplot, data series, scientific color, labels, and panel letter to the plotting helper.

### Line 348

```python
        title="Taxon scaling", xlabel="Number of taxa",
```
Provides the remaining title/axis-label arguments for this panel call.

### Line 349

```python
        ylabel="Peak resident memory (MiB)", label="B",
```
Provides the remaining title/axis-label arguments for this panel call.

### Line 350

```python
    ))
```
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 351

```python
    fits.append(draw_scaling_panel(
```
Draws one scaling panel and stores its slope, intercept, and R-squared result.

### Line 352

```python
        axes[1, 0], SITE_LEVELS, site_wall, color=BLUE,
```
Supplies the target subplot, data series, scientific color, labels, and panel letter to the plotting helper.

### Line 353

```python
        title="Site scaling", xlabel="Number of sites", ylabel="Wall time (s)", label="C",
```
Provides the remaining title/axis-label arguments for this panel call.

### Line 354

```python
    ))
```
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 355

```python
    fits.append(draw_scaling_panel(
```
Draws one scaling panel and stores its slope, intercept, and R-squared result.

### Line 356

```python
        axes[1, 1], SITE_LEVELS, site_mem, color=ORANGE,
```
Supplies the target subplot, data series, scientific color, labels, and panel letter to the plotting helper.

### Line 357

```python
        title="Site scaling", xlabel="Number of sites",
```
Provides the remaining title/axis-label arguments for this panel call.

### Line 358

```python
        ylabel="Peak resident memory (MiB)", label="D",
```
Provides the remaining title/axis-label arguments for this panel call.

### Line 359

```python
    ))
```
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 360

```python
    draw_mode_panel(
```
Starts drawing one categorical analysis-mode comparison panel without a fitted line.

### Line 361

```python
        axes[2, 0], mode_wall, color=BLUE, ylabel="Wall time (s)", label="E",
```
Supplies the target subplot, data series, scientific color, labels, and panel letter to the plotting helper.

### Line 362

```python
    )
```
Closes or continues the multi-line Python expression started on the preceding lines.

### Line 363

```python
    draw_mode_panel(
```
Starts drawing one categorical analysis-mode comparison panel without a fitted line.

### Line 364

```python
        axes[2, 1], mode_mem, color=ORANGE,
```
Supplies the target subplot, data series, scientific color, labels, and panel letter to the plotting helper.

### Line 365

```python
        ylabel="Peak resident memory (MiB)", label="F",
```
Provides the remaining title/axis-label arguments for this panel call.

### Line 366

```python
    )
```
Closes or continues the multi-line Python expression started on the preceding lines.

### Line 367

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 368

```python
    pdf = figure_dir / "Figure_4.pdf"
```
Defines the path for one of the publication artwork output formats.

### Line 369

```python
    svg = figure_dir / "Figure_4_editable.svg"
```
Defines the path for one of the publication artwork output formats.

### Line 370

```python
    png = figure_dir / "Figure_4_preview_600dpi.png"
```
Defines the path for one of the publication artwork output formats.

### Line 371

```python
    tif = figure_dir / "Figure_4_1000dpi.tiff"
```
Defines the path for one of the publication artwork output formats.

### Line 372

```python
    rgb_tif = figure_dir / "Figure_4_1000dpi_RGB.tiff"
```
Defines the path for one of the publication artwork output formats.

### Line 373

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 374

```python
    fig.savefig(pdf)
```
Exports the figure as a vector PDF.

### Line 375

```python
    fig.savefig(svg)
```
Exports the figure as an editable vector SVG.

### Line 376

```python
    fig.savefig(png, dpi=600)
```
Exports the figure as a 600-dpi PNG preview for inspection and GitHub display.

### Line 377

```python
    fig.savefig(tif, dpi=1000, pil_kwargs={"compression": "tiff_lzw"})
```
Exports the figure as a 1000-dpi LZW-compressed TIFF for high-resolution production use.

### Line 378

```python
    plt.close(fig)
```
Closes the Matplotlib figure after export to release memory and resources.

### Line 379

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 380

```python
    with Image.open(tif) as image:
```
Opens this resource using a context manager so it is closed cleanly when the indented block finishes.

### Line 381

```python
        image.convert("RGB").save(
```
Converts the TIFF pixels explicitly to RGB and starts writing the RGB production copy.

### Line 382

```python
            rgb_tif,
```
Supplies another argument or value to the multi-line expression being constructed.

### Line 383

```python
            format="TIFF",
```
Specifies TIFF as the output file format for the RGB copy.

### Line 384

```python
            compression="tiff_lzw",
```
Uses lossless LZW compression for the TIFF output.

### Line 385

```python
            dpi=(1000, 1000),
```
Records 1000 dpi in both dimensions for the RGB TIFF metadata.

### Line 386

```python
        )
```
Closes or continues the multi-line Python expression started on the preceding lines.

### Line 387

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 388

```python
    print(f"Figure 4 generated from: {raw_runs}")
```
Prints the exact committed source-data path used to generate the figure.

### Line 389

```python
    for name, (slope, intercept, r2) in zip(
```
Starts a loop that repeats the following indented code once for each item in the specified collection.

### Line 390

```python
        ["runtime_taxa", "memory_taxa", "runtime_sites", "memory_sites"], fits
```
Supplies the four console labels in the same order as the stored fit results.

### Line 391

```python
    ):
```
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 392

```python
        print(f"{name}: slope={slope:.12g}; intercept={intercept:.12g}; R2={r2:.9f}")
```
Prints slope, intercept, and R-squared at high precision as a quick rerender verification check.

### Line 393

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 394

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 395

```python
if __name__ == "__main__":
```
Standard Python guard: the indented line below runs only when this file is executed directly, not when imported.

### Line 396

```python
    main()
```
Calls the main figure-building function when the script is run directly.
