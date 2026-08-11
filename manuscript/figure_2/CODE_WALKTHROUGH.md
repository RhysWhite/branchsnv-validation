# Figure 2 code walkthrough

This document explains `make_figure_2.py` **line by line** in plain English. It assumes no prior knowledge of Python or Matplotlib.

## The whole script in one sentence

The script reads the committed validation summaries for Experiments 01–05, extracts the exact headline counts used in Figure 2, draws the four validation-evidence boxes and their connectors, exports the publication artwork, and updates the figure README with the generated artwork checksums.

## A few Python ideas used repeatedly

- `name = value` stores a value under a useful name.
- `function(...)` runs a reusable block of code.
- Indented lines belong to the function, loop, condition, or context-manager line above them.
- `ax.text(...)`, `ax.plot(...)`, and Matplotlib patch objects place visible elements on the figure canvas.
- The plotting script reads numerical claims from committed result files; it does not recompute the validation experiments.

## Line-by-line explanation

### Line 1

````python
#!/usr/bin/env python3
````
Shebang line allowing the file to be run directly with the environment's Python 3 interpreter on Unix-like systems.

### Line 2

````python
"""Generate manuscript Figure 2 from committed BRANCHSNV validation summaries.
````
Starts or continues the script/function documentation string describing what this code is intended to do.

### Line 3

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 4

````python
The figure is a compact validation overview. All numerical claims are read from the
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 5

````python
committed machine-readable result snapshots rather than typed into the artwork code.
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 6

````python
"""
````
Closes the multi-line documentation string started above.

### Line 7

````python
from __future__ import annotations
````
Enables postponed evaluation of type annotations, making the type hints used later more flexible.

### Line 8

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 9

````python
import hashlib
````
Imports `hashlib` functionality needed later in the script.

### Line 10

````python
import json
````
Imports `json` functionality needed later in the script.

### Line 11

````python
from pathlib import Path
````
Imports `pathlib` functionality needed later in the script.

### Line 12

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 13

````python
import matplotlib as mpl
````
Imports `matplotlib` functionality needed later in the script.

### Line 14

````python
import matplotlib.pyplot as plt
````
Imports `matplotlib.pyplot` functionality needed later in the script.

### Line 15

````python
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
````
Imports `matplotlib.patches` functionality needed later in the script.

### Line 16

````python
from PIL import Image
````
Imports `PIL` functionality needed later in the script.

### Line 17

````python
from matplotlib import font_manager
````
Imports Matplotlib's font manager so the required Arimo font can be checked explicitly before any artwork is rendered.


### Line 18

````python
FIG_W, FIG_H = 6.50, 2.72
````
Sets the physical width and height of the final manuscript artwork in inches.

### Line 19

````python
font_manager.findfont(font_manager.FontProperties(family="Arimo", weight="normal"), fallback_to_default=False)
````
Requires the regular Arimo font and disables fallback, so the script stops instead of silently substituting a different font.


### Line 20

````python
mpl.rcParams.update({
````
Starts or closes the global Matplotlib style settings used for the locked publication render.

### Line 21

````python
    "font.family": "Arimo",
````
Sets this specific global typography or vector-export option for the figure.

### Line 22

````python
    "font.size": 7.0,
````
Sets this specific global typography or vector-export option for the figure.

### Line 23

````python
    "svg.fonttype": "none",
````
Sets this specific global typography or vector-export option for the figure.

### Line 24

````python
    "pdf.fonttype": 42,
````
Sets this specific global typography or vector-export option for the figure.

### Line 25

````python
    "ps.fonttype": 42,
````
Sets this specific global typography or vector-export option for the figure.

### Line 26

````python
})
````
Starts or closes the global Matplotlib style settings used for the locked publication render.

### Line 27

````python
font_manager.findfont(font_manager.FontProperties(family="Arimo", weight="bold"), fallback_to_default=False)
````
Requires the bold Arimo font and disables fallback, preventing silent substitution for bold figure text.


### Line 28

````python
INK = "#111111"
````
Defines the near-black color used for ordinary text and labels.

### Line 29

````python
BLUE = "#0000FF"
````
Defines the blue used consistently for wall-time or exact-oracle visual elements.

### Line 30

````python
RED = "#E00000"
````
Defines the red used for deliberate-fault validation evidence.

### Line 31

````python
GREEN = "#38A900"
````
Defines the green used for published-data validation evidence.

### Line 32

````python
ORANGE = "#F06A00"
````
Defines the orange used consistently for memory/scalability visual elements.

### Line 33

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 34

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 35

````python
def repo_root() -> Path:
````
Defines a helper that finds the root of the validation repository from the location of this figure script.

### Line 36

````python
    return Path(__file__).resolve().parents[2]
````
Returns this calculated value to the code that called the current function.

### Line 37

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 38

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 39

````python
def load_json(path: Path) -> dict:
````
Defines a helper that reads a JSON file and returns the decoded Python object.

### Line 40

````python
    return json.loads(path.read_text(encoding="utf-8"))
````
Returns this calculated value to the code that called the current function.

### Line 41

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 42

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 43

````python
def sha256(path: Path) -> str:
````
Defines a helper that calculates the SHA-256 checksum of a file in chunks.

### Line 44

````python
    digest = hashlib.sha256()
````
Creates a new SHA-256 digest object used to checksum an output file.

### Line 45

````python
    with path.open("rb") as handle:
````
Opens this resource using a context manager so it is closed cleanly when the indented block finishes.

### Line 46

````python
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
````
Starts a loop that repeats the following indented code once for each item in the specified collection.

### Line 47

````python
            digest.update(chunk)
````
Adds the current file chunk to the running SHA-256 calculation.

### Line 48

````python
    return digest.hexdigest()
````
Returns this calculated value to the code that called the current function.

### Line 49

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 50

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 51

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 52

````python
def normalize_svg_whitespace(path: Path) -> None:
````
Defines the reusable `normalize_svg_whitespace` function used later in the script.

### Line 53

````python
    """Remove renderer-added trailing spaces so the tracked SVG stays Git-clean."""
````
Starts or continues the script/function documentation string describing what this code is intended to do.

### Line 54

````python
    lines = path.read_text(encoding="utf-8").splitlines()
````
Reads this committed text file using UTF-8 encoding.

### Line 55

````python
    path.write_text("\n".join(line.rstrip() for line in lines) + "\n", encoding="utf-8")
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 56

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 57

````python
def claim_values(root: Path) -> dict[str, object]:
````
Defines the data-loading function that extracts the exact validation counts used in Figure 2 from committed result summaries.

### Line 58

````python
    s1 = load_json(root / "results" / "01_exact_oracle" / "summary.json")
````
Loads this experiment's committed machine-readable summary JSON; it is a source of truth for a displayed validation claim.

### Line 59

````python
    s2 = load_json(root / "results" / "02_deliberate_faults" / "summary.json")
````
Loads this experiment's committed machine-readable summary JSON; it is a source of truth for a displayed validation claim.

### Line 60

````python
    s3 = load_json(root / "results" / "03_published_datasets" / "summary.json")
````
Loads this experiment's committed machine-readable summary JSON; it is a source of truth for a displayed validation claim.

### Line 61

````python
    s4 = load_json(root / "results" / "04_scalability" / "summary.json")
````
Loads this experiment's committed machine-readable summary JSON; it is a source of truth for a displayed validation claim.

### Line 62

````python
    s5 = load_json(root / "results" / "05_published_focal_branches" / "summary.json")
````
Loads this experiment's committed machine-readable summary JSON; it is a source of truth for a displayed validation claim.

### Line 63

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 64

````python
    p3 = s3["public_comparison"]["totals"]
````
Selects the Experiment 03 totals dictionary so the SNPPar concordance counts can be accessed concisely.

### Line 65

````python
    p5 = s5["totals"]
````
Selects the Experiment 05 totals dictionary so the published focal-branch reproduction counts can be accessed concisely.

### Line 66

````python
    return {
````
Returns this calculated value to the code that called the current function.

### Line 67

````python
        "oracle_total": int(s1["total_comparisons"]),
````
Adds this named, explicitly converted validation value to the dictionary returned to the drawing routine.

### Line 68

````python
        "oracle_mismatches": int(s1["total_mismatches"]),
````
Adds this named, explicitly converted validation value to the dictionary returned to the drawing routine.

### Line 69

````python
        "oracle_settings": int(s1["topology_cases"]),
````
Adds this named, explicitly converted validation value to the dictionary returned to the drawing routine.

### Line 70

````python
        "fault_detected": int(s2["faults_detected"]),
````
Adds this named, explicitly converted validation value to the dictionary returned to the drawing routine.

### Line 71

````python
        "fault_total": int(s2["faults_evaluated"]),
````
Adds this named, explicitly converted validation value to the dictionary returned to the drawing routine.

### Line 72

````python
        "fault_challenges": int(s2["total_challenges"]),
````
Adds this named, explicitly converted validation value to the dictionary returned to the drawing routine.

### Line 73

````python
        "fault_differentiating": int(s2["total_differentiating_challenges"]),
````
Adds this named, explicitly converted validation value to the dictionary returned to the drawing routine.

### Line 74

````python
        "snppar_exact": int(p3["exact_unambiguous_matches"]),
````
Adds this named, explicitly converted validation value to the dictionary returned to the drawing routine.

### Line 75

````python
        "snppar_unambiguous": int(p3["branchsnv_unambiguous_events"]),
````
Adds this named, explicitly converted validation value to the dictionary returned to the drawing routine.

### Line 76

````python
        "snppar_ambiguous": int(p3["snppar_only_supported_as_branchsnv_placement_ambiguous"]),
````
Adds this named, explicitly converted validation value to the dictionary returned to the drawing routine.

### Line 77

````python
        "published_exact": int(p5["exact_position_direction"]),
````
Adds this named, explicitly converted validation value to the dictionary returned to the drawing routine.

### Line 78

````python
        "published_total": int(p5["published_snvs"]),
````
Adds this named, explicitly converted validation value to the dictionary returned to the drawing routine.

### Line 79

````python
        "published_analyses": len(s5["datasets"]),
````
Adds this named, explicitly converted validation value to the dictionary returned to the drawing routine.

### Line 80

````python
        "benchmark_runs": int(s4["measured_runs"]),
````
Adds this named, explicitly converted validation value to the dictionary returned to the drawing routine.

### Line 81

````python
        "largest_taxa": int(s4["largest_taxon_configuration"]["ntax"]),
````
Adds this named, explicitly converted validation value to the dictionary returned to the drawing routine.

### Line 82

````python
        "largest_taxa_sites": int(s4["largest_taxon_configuration"]["nchar"]),
````
Adds this named, explicitly converted validation value to the dictionary returned to the drawing routine.

### Line 83

````python
        "largest_sites_taxa": int(s4["largest_site_configuration"]["ntax"]),
````
Adds this named, explicitly converted validation value to the dictionary returned to the drawing routine.

### Line 84

````python
        "largest_sites": int(s4["largest_site_configuration"]["nchar"]),
````
Adds this named, explicitly converted validation value to the dictionary returned to the drawing routine.

### Line 85

````python
    }
````
Closes or continues the multi-line Python expression started on the preceding lines.

### Line 86

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 87

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 88

````python
def rounded_box(ax: plt.Axes, x: float, y: float, w: float, h: float, color: str) -> None:
````
Defines a reusable drawing helper for one rounded validation-evidence box.

### Line 89

````python
    patch = FancyBboxPatch(
````
Creates the rounded rectangular outline used for one evidence box.

### Line 90

````python
        (x, y), w, h,
````
Supplies another argument or value to the multi-line expression being constructed.

### Line 91

````python
        boxstyle="round,pad=0.010,rounding_size=0.018",
````
Chooses rounded corners and a small internal padding for the evidence box.

### Line 92

````python
        linewidth=0.85,
````
Sets the stroke width for this drawn shape.

### Line 93

````python
        edgecolor=color,
````
Uses the category color for the outline of the box.

### Line 94

````python
        facecolor="white",
````
Keeps the inside of the evidence box white.

### Line 95

````python
        transform=ax.transAxes,
````
Interprets the coordinates in axes-relative units, where 0 to 1 spans the full drawing area.

### Line 96

````python
        clip_on=False,
````
Allows the object to extend slightly outside the nominal axes boundary if needed.

### Line 97

````python
    )
````
Closes or continues the multi-line Python expression started on the preceding lines.

### Line 98

````python
    ax.add_patch(patch)
````
Adds the constructed patch/arrow object to the Matplotlib axes so it appears in the figure.

### Line 99

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 100

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 101

````python
def bullet(ax: plt.Axes, x: float, y: float, text: str, color: str, size: float = 7.0) -> None:
````
Defines a helper that draws one colored bullet and its associated text inside a validation box.

### Line 102

````python
    ax.text(x, y, "•", transform=ax.transAxes, color=color, fontsize=10.5,
````
Interprets the coordinates in axes-relative units, where 0 to 1 spans the full drawing area.

### Line 103

````python
            ha="left", va="center")
````
Stores the value calculated on this line in `ha` for use by later code.

### Line 104

````python
    ax.text(x + 0.020, y, text, transform=ax.transAxes, color=INK, fontsize=size,
````
Interprets the coordinates in axes-relative units, where 0 to 1 spans the full drawing area.

### Line 105

````python
            ha="left", va="center", linespacing=0.95)
````
Stores the value calculated on this line in `ha` for use by later code.

### Line 106

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 107

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 108

````python
def connector(
````
Defines a helper that draws the colored dot and arrow linking one evidence box to the central conclusion.

### Line 109

````python
    ax: plt.Axes,
````
Supplies another argument or value to the multi-line expression being constructed.

### Line 110

````python
    start: tuple[float, float],
````
Supplies another argument or value to the multi-line expression being constructed.

### Line 111

````python
    end: tuple[float, float],
````
Supplies another argument or value to the multi-line expression being constructed.

### Line 112

````python
    color: str,
````
Supplies another argument or value to the multi-line expression being constructed.

### Line 113

````python
) -> None:
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 114

````python
    ax.plot(start[0], start[1], marker="o", markersize=4.0, color=color,
````
Draws the colored circular anchor point where a connector leaves an evidence box.

### Line 115

````python
            transform=ax.transAxes, clip_on=False, zorder=4)
````
Interprets the coordinates in axes-relative units, where 0 to 1 spans the full drawing area.

### Line 116

````python
    arrow = FancyArrowPatch(
````
Creates the arrow linking this evidence box to the central convergent-evidence statement.

### Line 117

````python
        start,
````
Supplies another argument or value to the multi-line expression being constructed.

### Line 118

````python
        end,
````
Supplies another argument or value to the multi-line expression being constructed.

### Line 119

````python
        arrowstyle="-|>",
````
Chooses a filled triangular arrowhead pointing toward the centre.

### Line 120

````python
        mutation_scale=10,
````
Sets the visual size of the connector arrowhead.

### Line 121

````python
        linewidth=0.95,
````
Sets the stroke width for this drawn shape.

### Line 122

````python
        color=color,
````
Supplies another argument or value to the multi-line expression being constructed.

### Line 123

````python
        transform=ax.transAxes,
````
Interprets the coordinates in axes-relative units, where 0 to 1 spans the full drawing area.

### Line 124

````python
        connectionstyle="arc3,rad=0",
````
Requests a straight connector rather than a curved arrow.

### Line 125

````python
        shrinkA=1,
````
Supplies another argument or value to the multi-line expression being constructed.

### Line 126

````python
        shrinkB=1,
````
Supplies another argument or value to the multi-line expression being constructed.

### Line 127

````python
    )
````
Closes or continues the multi-line Python expression started on the preceding lines.

### Line 128

````python
    ax.add_patch(arrow)
````
Adds the constructed patch/arrow object to the Matplotlib axes so it appears in the figure.

### Line 129

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 130

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 131

````python
def draw(ax: plt.Axes, values: dict[str, object]) -> None:
````
Defines the main Figure 2 drawing routine.

### Line 132

````python
    ax.set_xlim(0, 1)
````
Fixes the axes coordinate range to 0–1 so all layout positions are expressed as proportions of the full canvas.

### Line 133

````python
    ax.set_ylim(0, 1)
````
Fixes the axes coordinate range to 0–1 so all layout positions are expressed as proportions of the full canvas.

### Line 134

````python
    ax.axis("off")
````
Hides normal plot axes because Figure 2 is a schematic layout rather than a numeric graph.

### Line 135

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 136

````python
    left_x, right_x = 0.010, 0.650
````
Defines the common horizontal positions for the left and right evidence boxes.

### Line 137

````python
    box_w, box_h = 0.340, 0.445
````
Defines the common width and height used by all four evidence boxes.

### Line 138

````python
    top_y, bottom_y = 0.535, 0.020
````
Defines the vertical positions of the top and bottom evidence-box rows.

### Line 139

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 140

````python
    rounded_box(ax, left_x, top_y, box_w, box_h, BLUE)
````
Defines the common width and height used by all four evidence boxes.

### Line 141

````python
    rounded_box(ax, right_x, top_y, box_w, box_h, RED)
````
Defines the common width and height used by all four evidence boxes.

### Line 142

````python
    rounded_box(ax, left_x, bottom_y, box_w, box_h, GREEN)
````
Defines the common width and height used by all four evidence boxes.

### Line 143

````python
    rounded_box(ax, right_x, bottom_y, box_w, box_h, ORANGE)
````
Defines the common width and height used by all four evidence boxes.

### Line 144

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 145

````python
    title_y = top_y + box_h - 0.055
````
Calculates the shared vertical position of the two top-box headings.

### Line 146

````python
    ax.text(left_x + 0.018, title_y, "Exact oracle", transform=ax.transAxes,
````
Interprets the coordinates in axes-relative units, where 0 to 1 spans the full drawing area.

### Line 147

````python
            color=BLUE, fontsize=14.5, ha="left", va="center")
````
Stores the value calculated on this line in `color` for use by later code.

### Line 148

````python
    ax.text(right_x + 0.018, title_y, "Deliberate faults", transform=ax.transAxes,
````
Interprets the coordinates in axes-relative units, where 0 to 1 spans the full drawing area.

### Line 149

````python
            color=RED, fontsize=14.5, ha="left", va="center")
````
Stores the value calculated on this line in `color` for use by later code.

### Line 150

````python
    ax.text(left_x + 0.018, bottom_y + box_h - 0.055, "Published data",
````
Starts a Matplotlib text object at the specified figure position.

### Line 151

````python
            transform=ax.transAxes, color=GREEN, fontsize=14.5, ha="left", va="center")
````
Interprets the coordinates in axes-relative units, where 0 to 1 spans the full drawing area.

### Line 152

````python
    ax.text(right_x + 0.018, bottom_y + box_h - 0.055, "Scalability",
````
Starts a Matplotlib text object at the specified figure position.

### Line 153

````python
            transform=ax.transAxes, color=ORANGE, fontsize=14.5, ha="left", va="center")
````
Interprets the coordinates in axes-relative units, where 0 to 1 spans the full drawing area.

### Line 154

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 155

````python
    bullet(ax, left_x + 0.010, top_y + 0.260,
````
Draws one evidence bullet using a count obtained from the committed result summaries.

### Line 156

````python
           f"{values['oracle_total']:,} comparisons", BLUE)
````
Builds formatted text by inserting the current calculated value into the displayed string.

### Line 157

````python
    bullet(ax, left_x + 0.010, top_y + 0.165,
````
Draws one evidence bullet using a count obtained from the committed result summaries.

### Line 158

````python
           f"{values['oracle_settings']} topology-edge settings", BLUE)
````
Builds formatted text by inserting the current calculated value into the displayed string.

### Line 159

````python
    bullet(ax, left_x + 0.010, top_y + 0.070,
````
Draws one evidence bullet using a count obtained from the committed result summaries.

### Line 160

````python
           f"{values['oracle_mismatches']} discrepancies", BLUE)
````
Builds formatted text by inserting the current calculated value into the displayed string.

### Line 161

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 162

````python
    bullet(ax, right_x + 0.010, top_y + 0.260,
````
Draws one evidence bullet using a count obtained from the committed result summaries.

### Line 163

````python
           f"{values['fault_detected']}/{values['fault_total']} fault classes detected", RED)
````
Builds formatted text by inserting the current calculated value into the displayed string.

### Line 164

````python
    bullet(ax, right_x + 0.010, top_y + 0.165,
````
Draws one evidence bullet using a count obtained from the committed result summaries.

### Line 165

````python
           f"{values['fault_challenges']:,} fault-challenge comparisons", RED)
````
Builds formatted text by inserting the current calculated value into the displayed string.

### Line 166

````python
    bullet(ax, right_x + 0.010, top_y + 0.070,
````
Draws one evidence bullet using a count obtained from the committed result summaries.

### Line 167

````python
           f"{values['fault_differentiating']:,} differentiating comparisons", RED)
````
Builds formatted text by inserting the current calculated value into the displayed string.

### Line 168

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 169

````python
    bullet(ax, left_x + 0.010, bottom_y + 0.285,
````
Draws one evidence bullet using a count obtained from the committed result summaries.

### Line 170

````python
           f"{values['snppar_exact']}/{values['snppar_unambiguous']} BRANCHSNV unambiguous\n   calls matched SNPPar", GREEN, 6.6)
````
Builds formatted text by inserting the current calculated value into the displayed string.

### Line 171

````python
    bullet(ax, left_x + 0.010, bottom_y + 0.175,
````
Draws one evidence bullet using a count obtained from the committed result summaries.

### Line 172

````python
           f"{values['published_exact']}/{values['published_total']} published focal-branch SNVs\n   reproduced across {values['published_analyses']} analyses", GREEN, 6.6)
````
Builds formatted text by inserting the current calculated value into the displayed string.

### Line 173

````python
    bullet(ax, left_x + 0.010, bottom_y + 0.065,
````
Draws one evidence bullet using a count obtained from the committed result summaries.

### Line 174

````python
           f"{values['snppar_ambiguous']} additional SNPPar events retained as\n   placement-ambiguous", GREEN, 6.6)
````
Builds formatted text by inserting the current calculated value into the displayed string.

### Line 175

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 176

````python
    bullet(ax, right_x + 0.010, bottom_y + 0.235,
````
Draws one evidence bullet using a count obtained from the committed result summaries.

### Line 177

````python
           f"{values['benchmark_runs']}/{values['benchmark_runs']} CLI runs completed", ORANGE)
````
Builds formatted text by inserting the current calculated value into the displayed string.

### Line 178

````python
    bullet(ax, right_x + 0.010, bottom_y + 0.140,
````
Draws one evidence bullet using a count obtained from the committed result summaries.

### Line 179

````python
           f"{values['largest_taxa']:,} taxa × {values['largest_taxa_sites']:,} sites", ORANGE)
````
Builds formatted text by inserting the current calculated value into the displayed string.

### Line 180

````python
    bullet(ax, right_x + 0.010, bottom_y + 0.045,
````
Draws one evidence bullet using a count obtained from the committed result summaries.

### Line 181

````python
           f"{values['largest_sites_taxa']:,} taxa × {values['largest_sites']:,} sites", ORANGE)
````
Builds formatted text by inserting the current calculated value into the displayed string.

### Line 182

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 183

````python
    connector(ax, (left_x + box_w + 0.010, top_y + 0.220), (0.425, 0.575), BLUE)
````
Draws one colored connector from an evidence box toward the central conclusion.

### Line 184

````python
    connector(ax, (right_x - 0.010, top_y + 0.220), (0.575, 0.575), RED)
````
Draws one colored connector from an evidence box toward the central conclusion.

### Line 185

````python
    connector(ax, (left_x + box_w + 0.010, bottom_y + 0.220), (0.425, 0.425), GREEN)
````
Draws one colored connector from an evidence box toward the central conclusion.

### Line 186

````python
    connector(ax, (right_x - 0.010, bottom_y + 0.220), (0.575, 0.425), ORANGE)
````
Draws one colored connector from an evidence box toward the central conclusion.

### Line 187

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 188

````python
    ax.text(0.500, 0.525, "Convergent\nevidence", transform=ax.transAxes,
````
Interprets the coordinates in axes-relative units, where 0 to 1 spans the full drawing area.

### Line 189

````python
            color=INK, fontsize=13.8, ha="center", va="center", linespacing=0.90)
````
Stores the value calculated on this line in `color` for use by later code.

### Line 190

````python
    ax.text(0.500, 0.335,
````
Starts a Matplotlib text object at the specified figure position.

### Line 191

````python
            "Exactness\nFault sensitivity\nPracticality\nEmpirical concordance",
````
Supplies another argument or value to the multi-line expression being constructed.

### Line 192

````python
            transform=ax.transAxes, color=INK, fontsize=7.4,
````
Interprets the coordinates in axes-relative units, where 0 to 1 spans the full drawing area.

### Line 193

````python
            ha="center", va="center", linespacing=0.90)
````
Stores the value calculated on this line in `ha` for use by later code.

### Line 194

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 195

````python
    ax.text(0.500, 0.690,
````
Starts a Matplotlib text object at the specified figure position.

### Line 196

````python
            f"{values['oracle_total']:,}/{values['oracle_total']:,}\nexact matches",
````
Supplies another argument or value to the multi-line expression being constructed.

### Line 197

````python
            transform=ax.transAxes, color=BLUE, fontsize=7.5,
````
Interprets the coordinates in axes-relative units, where 0 to 1 spans the full drawing area.

### Line 198

````python
            ha="center", va="center", linespacing=0.92)
````
Stores the value calculated on this line in `ha` for use by later code.

### Line 199

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 200

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 201

````python
def write_support_files(outdir: Path, checksums: dict[str, str]) -> None:
````
Defines a helper that writes the Figure 2 README, directory tree, and locked figure requirements after rendering.

### Line 202

````python
    readme = f"""# Figure 2 - convergent validation evidence for BRANCHSNV
````
Starts the generated Figure 2 README text; the f-string allows artwork checksums to be inserted automatically.

### Line 203

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 204

````python
This directory contains the manuscript Figure 2 artwork and the exact Python/Matplotlib code used to render it from the committed validation summaries.
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 205

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 206

````python
## Final figure
````
Comment for the reader; it documents the purpose of the code that follows and is not executed by Python.

### Line 207

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 208

````python
![Figure 2 preview](Figure_2_preview_600dpi.png)
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 209

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 210

````python
## Data provenance
````
Comment for the reader; it documents the purpose of the code that follows and is not executed by Python.

### Line 211

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 212

````python
The numerical claims are read directly from:
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 213

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 214

````python
- `results/01_exact_oracle/summary.json`
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 215

````python
- `results/02_deliberate_faults/summary.json`
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 216

````python
- `results/03_published_datasets/summary.json`
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 217

````python
- `results/04_scalability/summary.json`
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 218

````python
- `results/05_published_focal_branches/summary.json`
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 219

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 220

````python
The figure therefore reflects the same machine-readable results checked by `verify_publication_snapshot.py`. No validation count is manually entered into the plotting code.
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 221

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 222

````python
## Figure files
````
Comment for the reader; it documents the purpose of the code that follows and is not executed by Python.

### Line 223

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 224

````python
| File | Purpose | SHA-256 |
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 225

````python
|---|---|---|
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 226

````python
| `Figure_2.pdf` | Vector production/submission figure. | `{checksums['Figure_2.pdf']}` |
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 227

````python
| `Figure_2_editable.svg` | Editable vector source. | `{checksums['Figure_2_editable.svg']}` |
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 228

````python
| `Figure_2_preview_600dpi.png` | README/inspection preview. | `{checksums['Figure_2_preview_600dpi.png']}` |
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 229

````python
| `Figure_2_1000dpi.tiff` | 1000-dpi LZW TIFF. | `{checksums['Figure_2_1000dpi.tiff']}` |
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 230

````python
| `Figure_2_1000dpi_RGB.tiff` | Explicit RGB 1000-dpi LZW TIFF. | `{checksums['Figure_2_1000dpi_RGB.tiff']}` |
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 231

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 232

````python
## Reproducing the figure
````
Comment for the reader; it documents the purpose of the code that follows and is not executed by Python.

### Line 233

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 234

````python
The locked render used Python 3.13, Matplotlib 3.10.8, Pillow 12.3.0, and Arimo regular/bold.
````
Writes the locked Python-package and font requirements into the generated figure README.


### Line 235

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 236

````python
From the repository root:
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 237

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 238

````python
```bash
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 239

````python
python manuscript/figure_2/make_figure_2.py
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 240

````python
```
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 241

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 242

````python
The script writes all five artwork files beside itself and updates this README's artwork checksums. `CODE_WALKTHROUGH.md` is maintained separately and is deliberately not overwritten during rerendering.
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 243

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 244

````python
## Interpretation
````
Comment for the reader; it documents the purpose of the code that follows and is not executed by Python.

### Line 245

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 246

````python
The four boxes represent complementary validation evidence rather than four estimates of the same property. The oracle tests exact implementation of the defined reconstruction problem; deliberate faults test sensitivity to specified implementation errors; published-data analyses test concordance and reproduction on independent empirical examples; and scalability tests establish practical end-to-end behavior over the measured input ranges.
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 247

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 248

````python
### Font note
````
Comment for the reader; it documents the purpose of the code that follows and is not executed by Python.

### Line 249

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 250

````python
The locked render uses **Arimo**, an Arial-compatible metric substitute. The script fails if Arimo regular or bold is unavailable rather than silently substituting another font. Exact output-file bytes can still vary across platforms with the font/FreeType rendering stack; the committed artwork hashes identify the publication render. The SVG retains editable text.
````
Explains the font requirement, the explicit no-fallback safeguard, and why committed artwork hashes identify the publication render without promising byte-identical cross-platform rasterization.


### Line 251

````python
"""
````
Closes the multi-line documentation string started above.

### Line 252

````python
    (outdir / "README.md").write_text(readme, encoding="utf-8")
````
Writes the generated README beside the figure artwork using UTF-8 encoding.

### Line 253

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 254

````python
    (outdir / "DIRECTORY_TREE.txt").write_text("""BRANCHSNV validation repository
````
Writes a small directory map showing the relationship between Figure 2 and its result inputs.

### Line 255

````python
|
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 256

````python
|-- results/
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 257

````python
|   |-- 01_exact_oracle/summary.json
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 258

````python
|   |-- 02_deliberate_faults/summary.json
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 259

````python
|   |-- 03_published_datasets/summary.json
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 260

````python
|   |-- 04_scalability/summary.json
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 261

````python
|   `-- 05_published_focal_branches/summary.json
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 262

````python
|
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 263

````python
`-- manuscript/
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 264

````python
    `-- figure_2/
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 265

````python
        |-- CODE_WALKTHROUGH.md
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 266

````python
        |-- DIRECTORY_TREE.txt
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 267

````python
        |-- Figure_2.pdf
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 268

````python
        |-- Figure_2_1000dpi.tiff
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 269

````python
        |-- Figure_2_1000dpi_RGB.tiff
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 270

````python
        |-- Figure_2_editable.svg
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 271

````python
        |-- Figure_2_preview_600dpi.png
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 272

````python
        |-- README.md
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 273

````python
        |-- make_figure_2.py
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 274

````python
        `-- requirements.txt
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 275

````python
""", encoding="utf-8")
````
Starts or continues the script/function documentation string describing what this code is intended to do.

### Line 276

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 277

````python
    (outdir / "requirements.txt").write_text(
````
Writes the locked Python package versions needed to regenerate Figure 2.

### Line 278

````python
        "matplotlib==3.10.8\nPillow==12.3.0\n",
````
Supplies another argument or value to the multi-line expression being constructed.

### Line 279

````python
        encoding="utf-8",
````
Supplies another argument or value to the multi-line expression being constructed.

### Line 280

````python
    )
````
Closes or continues the multi-line Python expression started on the preceding lines.

### Line 281

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 282

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 283

````python
def main() -> None:
````
Defines the main entry point that loads the data, draws the figure, exports all artwork formats, and writes support files.

### Line 284

````python
    outdir = Path(__file__).resolve().parent
````
Sets the output directory to the directory containing this plotting script.

### Line 285

````python
    values = claim_values(repo_root())
````
Loads all validation claims from the committed result summaries before anything is drawn.

### Line 286

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 287

````python
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
````
Creates the Matplotlib figure and the single axes used as a free-positioned schematic canvas.

### Line 288

````python
    fig.subplots_adjust(left=0.005, right=0.995, top=0.990, bottom=0.010)
````
Minimizes outer whitespace around the schematic while leaving a small safety margin.

### Line 289

````python
    draw(ax, values)
````
Calls the main drawing routine using the verified values loaded from the committed results.

### Line 290

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 291

````python
    pdf = outdir / "Figure_2.pdf"
````
Defines the path for one of the publication artwork output formats.

### Line 292

````python
    svg = outdir / "Figure_2_editable.svg"
````
Defines the path for one of the publication artwork output formats.

### Line 293

````python
    png = outdir / "Figure_2_preview_600dpi.png"
````
Defines the path for one of the publication artwork output formats.

### Line 294

````python
    tiff = outdir / "Figure_2_1000dpi.tiff"
````
Defines the path for one of the publication artwork output formats.

### Line 295

````python
    rgb_tiff = outdir / "Figure_2_1000dpi_RGB.tiff"
````
Defines the path for one of the publication artwork output formats.

### Line 296

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 297

````python
    fig.savefig(pdf)
````
Exports the figure as a vector PDF.

### Line 298

````python
    fig.savefig(svg)
````
Exports the figure as an editable vector SVG.

### Line 299

````python
    normalize_svg_whitespace(svg)
````
Continues the current Python statement or supplies a parameter/value used by the surrounding operation.

### Line 300

````python
    fig.savefig(png, dpi=600)
````
Exports the figure as a 600-dpi PNG preview for inspection and GitHub display.

### Line 301

````python
    fig.savefig(tiff, dpi=1000, pil_kwargs={"compression": "tiff_lzw"})
````
Exports the figure as a 1000-dpi LZW-compressed TIFF for high-resolution production use.

### Line 302

````python
    plt.close(fig)
````
Closes the Matplotlib figure after export to release memory and resources.

### Line 303

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 304

````python
    with Image.open(tiff) as image:
````
Opens this resource using a context manager so it is closed cleanly when the indented block finishes.

### Line 305

````python
        image.convert("RGB").save(
````
Converts the TIFF pixels explicitly to RGB and starts writing the RGB production copy.

### Line 306

````python
            rgb_tiff,
````
Supplies another argument or value to the multi-line expression being constructed.

### Line 307

````python
            format="TIFF",
````
Specifies TIFF as the output file format for the RGB copy.

### Line 308

````python
            compression="tiff_lzw",
````
Uses lossless LZW compression for the TIFF output.

### Line 309

````python
            dpi=(1000, 1000),
````
Records 1000 dpi in both dimensions for the RGB TIFF metadata.

### Line 310

````python
        )
````
Closes or continues the multi-line Python expression started on the preceding lines.

### Line 311

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 312

````python
    checksums = {path.name: sha256(path) for path in (pdf, svg, png, tiff, rgb_tiff)}
````
Calculates SHA-256 checksums for all rendered Figure 2 artwork files.

### Line 313

````python
    write_support_files(outdir, checksums)
````
Updates the support files using the checksums from the newly rendered artwork.

### Line 314

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 315

````python

````
Blank line used only to separate logical blocks and make the script easier to read.

### Line 316

````python
if __name__ == "__main__":
````
Standard Python guard: the indented line below runs only when this file is executed directly, not when imported.

### Line 317

````python
    main()
````
Calls the main figure-building function when the script is run directly.
