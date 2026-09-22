# Figure 1 code walkthrough

This document explains `make_figure_1.py` line by line in plain English. It assumes no prior knowledge of Python or Matplotlib.

## The whole script in one sentence

The script creates a blank page, divides it into invisible drawing regions, draws Panels A–C from simple vector lines/circles/text, adds the safeguard strip, and exports the finished artwork in four formats.

## Five Python ideas used repeatedly

- `name = value` stores a value under a useful name.
- `[a, b, c]` creates a list.
- `for ...:` repeats the indented lines below it.
- `ax.plot(...)` draws a line and `ax.text(...)` writes text.
- Coordinates inside each drawing region run from 0 (left/bottom) to 1 (right/top).

## Line-by-line explanation

### Line 1

```python
import matplotlib.pyplot as plt
```
Imports Matplotlib's plotting interface. `plt` is the short name used to create and export the figure.

### Line 2

```python
from matplotlib.patches import Circle
```
Imports the `Circle` shape used for the root, tip markers, and the A/G endpoint circles.

### Line 3

```python
from matplotlib.lines import Line2D
```
Imports `Line2D`, used for the long horizontal separators between major figure sections.

### Line 4

```python
import matplotlib as mpl
```
Imports Matplotlib itself as `mpl` so global font and export settings can be configured.

### Line 5

```python
from pathlib import Path
```
Imports `Path`, which is used to construct output-file paths.

### Line 6

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 7

```python
# Final publication figure dimensions
```
Comment marking the final figure dimensions.

### Line 8

```python
FIG_W, FIG_H = 6.50, 5.10  # 16.5 × 13.0 cm
```
Sets the final page size to 6.50 × 5.10 inches, equivalent to 16.5 × 13.0 cm.

### Line 9

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 10

```python
mpl.rcParams.update({
```
Starts the global Matplotlib settings block.

### Line 11

```python
    "font.family": "Arimo",  # Arial-compatible preview; SVG/PDF text remains editable
```
Uses Arimo for the locked render. It is metrically compatible with Arial and preserves the figure layout.

### Line 12

```python
    "font.size": 7.0,
```
Sets the default text size to 7 pt.

### Line 13

```python
    "svg.fonttype": "none",
```
Keeps SVG text editable instead of converting letters into vector outlines.

### Line 14

```python
    "pdf.fonttype": 42,
```
Uses TrueType-style font embedding in PDF output.

### Line 15

```python
    "ps.fonttype": 42,
```
Applies the same font embedding choice to PostScript-based output.

### Line 16

```python
})
```
Closes the list, function call, or settings block opened on the preceding lines.

### Line 17

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 18

```python
INK = "#222222"
```
Defines the near-black colour used for most text and tree lines.

### Line 19

```python
GREY = "#666666"
```
Defines the secondary grey text colour.

### Line 20

```python
LIGHT = "#D9D9D9"
```
Defines the pale grey used for dividers and table rules.

### Line 21

```python
BLUE = "#1F5AA6"
```
Defines blue for the observed/clade-exclusivity side of the figure.

### Line 22

```python
ORANGE = "#D95F02"
```
Defines orange for the inferred focal-edge substitution side.

### Line 23

```python
RED = "#B2182B"
```
Defines red for the focal edge and the recurrent outside G.

### Line 24

```python
PURPLE = "#7B3294"
```
Defines purple for placement ambiguity.

### Line 25

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 26

```python
fig = plt.figure(figsize=(FIG_W, FIG_H), facecolor="white")
```
Creates the blank white figure canvas.

### Line 27

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 28

```python
# Main layout grid
```
Comment marking the start of the fixed layout grid.

### Line 29

```python
axA = fig.add_axes([0.055, 0.61, 0.89, 0.34])
```
Creates Panel A's drawing area. The four numbers are left position, bottom position, width, and height as fractions of the whole figure.

### Line 30

```python
axB1 = fig.add_axes([0.075, 0.325, 0.34, 0.235])
```
Creates the observed half of Panel B.

### Line 31

```python
axBmid = fig.add_axes([0.455, 0.325, 0.08, 0.235])
```
Creates the narrow middle strip in Panel B containing the ≠ symbol.

### Line 32

```python
axB2 = fig.add_axes([0.575, 0.325, 0.35, 0.235])
```
Creates the inferred half of Panel B.

### Line 33

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 34

```python
# Panel C: dedicated header and body axes
```
Comment explaining that Panel C has a separate header and body so the table rule sits in the correct place.

### Line 35

```python
axChead = fig.add_axes([0.075, 0.230, 0.835, 0.045])
```
Creates the header strip for Panel C.

### Line 36

```python
axC1 = fig.add_axes([0.075, 0.135, 0.47, 0.095])
```
Creates the left body of Panel C, containing the pair-set table.

### Line 37

```python
axC2 = fig.add_axes([0.60, 0.135, 0.31, 0.095])
```
Creates the right body of Panel C, containing the tie-breaking explanation.

### Line 38

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 39

```python
axF = fig.add_axes([0.055, 0.025, 0.89, 0.085])
```
Creates the bottom Design Safeguards strip.

### Line 40

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 41

```python
for ax in (axA, axB1, axBmid, axB2, axChead, axC1, axC2, axF):
```
Starts a loop over every panel/axes object.

### Line 42

```python
    ax.set_xlim(0, 1)
```
Sets each panel's horizontal coordinate system to run from 0 to 1.

### Line 43

```python
    ax.set_ylim(0, 1)
```
Sets each panel's vertical coordinate system to run from 0 to 1.

### Line 44

```python
    ax.axis("off")
```
Hides ordinary chart axes, ticks, and borders because this is a schematic.

### Line 45

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 46

```python
# Major section separators
```
Human-readable comment: Major section separators.

### Line 47

```python
for y in [0.595, 0.305, 0.122]:
```
Loops over the three major section-divider heights.

### Line 48

```python
    fig.add_artist(Line2D([0.055, 0.945], [y, y], transform=fig.transFigure,
```
Draws a long horizontal separator across the figure.

### Line 49

```python
                          color=LIGHT, lw=0.7))
```
Sets that separator to pale grey with a thin line weight.

### Line 50

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 51

```python
# ======================================================
```
Human-readable comment: ======================================================.

### Line 52

```python
# Panel A
```
Human-readable comment: Panel A.

### Line 53

```python
# ======================================================
```
Human-readable comment: ======================================================.

### Line 54

```python
axA.text(-0.035, 1.02, "A", fontsize=10.5, fontweight="bold", va="top", color=INK)
```
Adds the capital panel label A.

### Line 55

```python
axA.text(0.005, 1.015, "One branch, one site", fontsize=8.6, fontweight="bold",
```
Starts the Panel A heading, `One branch, one site`.

### Line 56

```python
         va="top", color=INK)
```
Continues the appearance and alignment settings for the drawing command started on the preceding line.

### Line 57

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 58

```python
xR, xX, xF, xO, xY, xTip = 0.08, 0.22, 0.38, 0.38, 0.25, 0.51
```
Defines the horizontal coordinates of the root, internal nodes, focal node, sister node, lower node, and terminal tips.

### Line 59

```python
ys = [0.89, 0.80, 0.71, 0.54, 0.45, 0.36, 0.19, 0.10, 0.01]
```
Defines the nine tip heights from top to bottom.

### Line 60

```python
yF = sum(ys[:3]) / 3
```
Calculates the vertical centre of the three focal descendants.

### Line 61

```python
yO = sum(ys[3:6]) / 3
```
Calculates the vertical centre of their outside sister group.

### Line 62

```python
yY = sum(ys[6:]) / 3
```
Calculates the vertical centre of the lower outside group.

### Line 63

```python
yX = (yF + yO) / 2
```
Places internal node X halfway between the focal group and its sister group.

### Line 64

```python
yR = (yX + yY) / 2
```
Places the root halfway between the upper and lower major groups.

### Line 65

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 66

```python
lw_tree = 0.8
```
Stores the standard tree line width.

### Line 67

```python
axA.plot([xR, xR], [yY, yX], color=INK, lw=lw_tree)
```
Draws the vertical part of the root connection.

### Line 68

```python
axA.plot([xR, xX], [yX, yX], color=INK, lw=lw_tree)
```
Draws the upper root branch.

### Line 69

```python
axA.plot([xR, xY], [yY, yY], color=INK, lw=lw_tree)
```
Draws the lower root branch.

### Line 70

```python
axA.plot([xX, xX], [yO, yF], color=INK, lw=lw_tree)
```
Draws the vertical connector at the upper internal node.

### Line 71

```python
axA.plot([xX, xF], [yO, yO], color=INK, lw=lw_tree)
```
Draws the branch from the upper internal node to the outside sister group.

### Line 72

```python
axA.plot([xX, xF], [yF, yF], color=RED, lw=1.5)
```
Draws the focal edge in red and slightly thicker than the rest of the tree.

### Line 73

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 74

```python
axA.plot([xF, xF], [ys[2], ys[0]], color=INK, lw=lw_tree)
```
Draws the vertical connector joining the three focal descendants.

### Line 75

```python
for yy in ys[:3]:
```
Starts a loop over the three focal tip heights.

### Line 76

```python
    axA.plot([xF, xTip], [yy, yy], color=INK, lw=lw_tree)
```
Draws each focal terminal branch.

### Line 77

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 78

```python
axA.plot([xO, xO], [ys[5], ys[3]], color=INK, lw=lw_tree)
```
Draws the connector joining the three taxa in the outside sister group.

### Line 79

```python
for yy in ys[3:6]:
```
Starts a loop over those three tip heights.

### Line 80

```python
    axA.plot([xO, xTip], [yy, yy], color=INK, lw=lw_tree)
```
Draws each sister-group terminal branch.

### Line 81

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 82

```python
axA.plot([xY, xY], [ys[8], ys[6]], color=INK, lw=lw_tree)
```
Draws the connector joining the three lower outside taxa.

### Line 83

```python
for yy in ys[6:]:
```
Starts a loop over those three tip heights.

### Line 84

```python
    axA.plot([xY, xTip], [yy, yy], color=INK, lw=lw_tree)
```
Draws each lower terminal branch.

### Line 85

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 86

```python
axA.add_patch(Circle((xR, yR), 0.010, ec=INK, fc=INK, lw=0.7))
```
Draws the filled black root marker.

### Line 87

```python
axA.text(xR-0.02, yR-0.06, "root", fontsize=6.1, color=GREY, ha="right")
```
Places the small `root` label beside it.

### Line 88

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 89

```python
for i, yy in enumerate(ys):
```
Loops over all nine tip positions.

### Line 90

```python
    ec = BLUE if i < 3 else GREY
```
Uses blue outlines for focal tips and grey outlines for outside tips.

### Line 91

```python
    axA.add_patch(Circle((xTip, yy), 0.010, ec=ec, fc="white", lw=0.8))
```
Draws the open circle at each tip.

### Line 92

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 93

```python
axA.text((xX+xF)/2, yF+0.075, "focal edge", fontsize=6.3, fontweight="bold",
```
Begins the red `focal edge` label above the focal branch.

### Line 94

```python
         color=RED, ha="center")
```
Continues the appearance and alignment settings for the drawing command started on the preceding line.

### Line 95

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 96

```python
bx = 0.545
```
Stores the x-position of the blue bracket marking the focal descendants.

### Line 97

```python
axA.plot([bx, bx], [ys[2]-0.022, ys[0]+0.022], color=BLUE, lw=0.8)
```
Draws the vertical part of the bracket.

### Line 98

```python
axA.plot([bx-0.012, bx], [ys[0]+0.022, ys[0]+0.022], color=BLUE, lw=0.8)
```
Draws the upper bracket cap.

### Line 99

```python
axA.plot([bx-0.012, bx], [ys[2]-0.022, ys[2]-0.022], color=BLUE, lw=0.8)
```
Draws the lower bracket cap.

### Line 100

```python
axA.text(bx+0.02, yF, "focal\ndescendants", fontsize=6.2, fontweight="bold",
```
Begins the two-line `focal descendants` label.

### Line 101

```python
         color=BLUE, va="center", linespacing=1.0)
```
Continues the appearance and alignment settings for the drawing command started on the preceding line.

### Line 102

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 103

```python
state_x = 0.69
```
Stores the x-position of the nucleotide-state column.

### Line 104

```python
axA.text(state_x, 0.99, "one site", fontsize=6.4, fontweight="bold",
```
Begins the `one site` heading above that column.

### Line 105

```python
         ha="center", va="top")
```
Continues the appearance and alignment settings for the drawing command started on the preceding line.

### Line 106

```python
states = ["G","G","G","A","A","A","A","A","G"]
```
Defines the nine observed nucleotide states shown next to the tips: G/G/G in the focal clade and A/A/A/A/A/G outside.

### Line 107

```python
for i, (yy, s) in enumerate(zip(ys, states)):
```
Loops through the tip heights and states together.

### Line 108

```python
    c = BLUE if i < 3 else (RED if i == 8 else INK)
```
Colours focal G states blue, the recurrent outside G red, and the outside A states black.

### Line 109

```python
    axA.text(state_x, yy, s, fontsize=7.0, fontweight="bold", color=c,
```
Begins drawing each nucleotide letter at the matching tip height.

### Line 110

```python
             ha="center", va="center")
```
Continues the appearance and alignment settings for the drawing command started on the preceding line.

### Line 111

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 112

```python
axA.text(0.80, 0.73, "Focal clade: G G G", fontsize=6.6, fontweight="bold",
```
Adds the concise blue summary `Focal clade: G G G`.

### Line 113

```python
         color=BLUE, ha="left")
```
Continues the appearance and alignment settings for the drawing command started on the preceding line.

### Line 114

```python
axA.text(0.80, 0.53, "Outside includes G", fontsize=6.6, fontweight="bold",
```
Adds the concise red summary `Outside includes G`.

### Line 115

```python
         color=RED, ha="left")
```
Continues the appearance and alignment settings for the drawing command started on the preceding line.

### Line 116

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 117

```python
# ======================================================
```
Human-readable comment: ======================================================.

### Line 118

```python
# Panel B
```
Human-readable comment: Panel B.

### Line 119

```python
# ======================================================
```
Human-readable comment: ======================================================.

### Line 120

```python
fig.text(0.055, 0.575, "B", fontsize=10.5, fontweight="bold", color=INK, va="top")
```
Adds the capital panel label B.

### Line 121

```python
fig.text(0.095, 0.575, "Two questions, different answers",
```
Begins the Panel B heading `Two questions, different answers`.

### Line 122

```python
         fontsize=8.6, fontweight="bold", color=INK, va="top")
```
Continues the appearance and alignment settings for the drawing command started on the preceding line.

### Line 123

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 124

```python
axB1.text(0.00, 0.90, "OBSERVED", fontsize=6.3, fontweight="bold",
```
Adds the blue category label `OBSERVED`.

### Line 125

```python
          color=BLUE, va="top")
```
Continues the appearance and alignment settings for the drawing command started on the preceding line.

### Line 126

```python
axB1.text(0.00, 0.74, "Clade-exclusive?", fontsize=8.2, fontweight="bold",
```
Adds the observed question `Clade-exclusive?`.

### Line 127

```python
          color=INK, va="top")
```
Continues the appearance and alignment settings for the drawing command started on the preceding line.

### Line 128

```python
axB1.text(0.00, 0.48, "focal", fontsize=6.0, color=GREY, va="center")
```
Adds the small grey `focal` label.

### Line 129

```python
for j in range(3):
```
Starts a three-iteration loop for the three focal G states.

### Line 130

```python
    axB1.text(0.16+0.11*j, 0.48, "G", fontsize=7.5, fontweight="bold",
```
Places those three G letters across the row.

### Line 131

```python
              color=BLUE, ha="center", va="center")
```
Continues the appearance and alignment settings for the drawing command started on the preceding line.

### Line 132

```python
axB1.text(0.00, 0.31, "outside", fontsize=6.0, color=GREY, va="center")
```
Adds the small grey `outside` label.

### Line 133

```python
for j, s in enumerate(["A","A","A","A","A","G"]):
```
Loops across the six outside states.

### Line 134

```python
    axB1.text(0.16+0.09*j, 0.31, s, fontsize=7.1, fontweight="bold",
```
Places each outside nucleotide.

### Line 135

```python
              color=(RED if s == "G" else INK), ha="center", va="center")
```
Colours only the outside G red.

### Line 136

```python
axB1.text(0.00, 0.06, "NO", fontsize=13.0, fontweight="bold",
```
Begins the large blue result `NO`.

### Line 137

```python
          color=BLUE, va="bottom")
```
Continues the appearance and alignment settings for the drawing command started on the preceding line.

### Line 138

```python
axB1.text(0.23, 0.085, "not fixed-exclusive", fontsize=6.9, fontweight="bold",
```
Begins the bold explanation `not fixed-exclusive`.

### Line 139

```python
          color=INK, va="bottom")
```
Continues the appearance and alignment settings for the drawing command started on the preceding line.

### Line 140

```python
axB1.text(0.00, 0.005, "G occurs outside the clade", fontsize=6.0,
```
Begins the grey reason `G occurs outside the clade`.

### Line 141

```python
          color=GREY, va="bottom")
```
Continues the appearance and alignment settings for the drawing command started on the preceding line.

### Line 142

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 143

```python
axBmid.text(0.50, 0.54, "≠", fontsize=28, ha="center", va="center", color=INK)
```
Places the large ≠ symbol between observed and inferred analyses.

### Line 144

```python
axBmid.text(0.50, 0.24, "kept separate", fontsize=5.9, ha="center",
```
Adds the phrase `kept separate` below it.

### Line 145

```python
            va="center", color=GREY)
```
Continues the appearance and alignment settings for the drawing command started on the preceding line.

### Line 146

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 147

```python
axB2.text(0.00, 0.90, "INFERRED", fontsize=6.3, fontweight="bold",
```
Adds the orange category label `INFERRED`.

### Line 148

```python
          color=ORANGE, va="top")
```
Continues the appearance and alignment settings for the drawing command started on the preceding line.

### Line 149

```python
axB2.text(0.00, 0.74, "Substitution on the focal edge?", fontsize=8.2,
```
Begins the inferred question `Substitution on the focal edge?`.

### Line 150

```python
          fontweight="bold", color=INK, va="top")
```
Continues the appearance and alignment settings for the drawing command started on the preceding line.

### Line 151

```python
axB2.text(0.26, 0.46, "parent", fontsize=5.9, color=GREY, ha="center")
```
Labels the left endpoint as the parent state.

### Line 152

```python
axB2.text(0.74, 0.46, "child", fontsize=5.9, color=GREY, ha="center")
```
Labels the right endpoint as the child state.

### Line 153

```python
axB2.text(0.50, 0.55, "all optimal reconstructions", fontsize=5.9, color=GREY, ha="center")
```
Adds `all optimal reconstructions` above the endpoint relationship.

### Line 154

```python
for x, state, edge in [(0.26, "A", ORANGE), (0.74, "G", BLUE)]:
```
Loops over the parent A and child G endpoint states.

### Line 155

```python
    axB2.add_patch(Circle((x, 0.31), 0.055, ec=edge, fc="white", lw=1.0))
```
Draws the current endpoint circle.

### Line 156

```python
    axB2.text(x, 0.31, state, fontsize=7.2, fontweight="bold",
```
Begins placing the nucleotide letter inside that circle.

### Line 157

```python
              ha="center", va="center", color=INK)
```
Continues the appearance and alignment settings for the drawing command started on the preceding line.

### Line 158

```python
axB2.annotate("", xy=(0.66,0.31), xytext=(0.34,0.31),
```
Begins drawing the A→G arrow.

### Line 159

```python
              arrowprops=dict(arrowstyle="-|>", lw=0.9, color=INK,
```
Continues the appearance and alignment settings for the drawing command started on the preceding line.

### Line 160

```python
                              mutation_scale=8.5))
```
Part of the current drawing command or data definition; it supplies values used by the surrounding lines.

### Line 161

```python
axB2.text(0.00, 0.06, "YES", fontsize=13.0, fontweight="bold",
```
Begins the large orange result `YES`.

### Line 162

```python
          color=ORANGE, va="bottom")
```
Continues the appearance and alignment settings for the drawing command started on the preceding line.

### Line 163

```python
axB2.text(0.23, 0.085, "unambiguous A→G", fontsize=6.9, fontweight="bold",
```
Begins the bold interpretation `unambiguous A→G`.

### Line 164

```python
          color=INK, va="bottom")
```
Continues the appearance and alignment settings for the drawing command started on the preceding line.

### Line 165

```python
axB2.text(0.00, 0.005, "Only optimal focal-edge pair: A→G", fontsize=6.2,
```
Adds the plain-language statement `Only optimal focal-edge pair: A→G`.

### Line 166

```python
          color=GREY, va="bottom")
```
Continues the appearance and alignment settings for the drawing command started on the preceding line.

### Line 167

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 168

```python
# ======================================================
```
Human-readable comment: ======================================================.

### Line 169

```python
# Panel C — corrected table hierarchy
```
Human-readable comment: Panel C — corrected table hierarchy.

### Line 170

```python
# ======================================================
```
Human-readable comment: ======================================================.

### Line 171

```python
fig.text(0.055, 0.292, "C", fontsize=10.5, fontweight="bold", color=INK, va="top")
```
Adds the capital panel label C.

### Line 172

```python
fig.text(0.095, 0.292, "Retain all optimal focal-edge solutions",
```
Begins the heading `Retain all optimal focal-edge solutions`.

### Line 173

```python
         fontsize=8.6, fontweight="bold", color=INK, va="top")
```
Continues the appearance and alignment settings for the drawing command started on the preceding line.

### Line 174

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 175

```python
# Column headers — no floating divider above them
```
Human-readable comment: Column headers — no floating divider above them.

### Line 176

```python
axChead.text(0.00, 0.72, "Optimal parent→child pair(s)", fontsize=5.9, color=GREY,
```
Adds the left table header `Optimal parent→child pair(s)`.

### Line 177

```python
             va="center", ha="left")
```
Continues the appearance and alignment settings for the drawing command started on the preceding line.

### Line 178

```python
axChead.text(0.49, 0.72, "BRANCHSNV reports", fontsize=5.9, color=GREY,
```
Adds the right table header `BRANCHSNV reports`.

### Line 179

```python
             va="center", ha="left")
```
Continues the appearance and alignment settings for the drawing command started on the preceding line.

### Line 180

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 181

```python
# Proper table rule: immediately UNDER the column headers.
```
Human-readable comment: Proper table rule: immediately UNDER the column headers..

### Line 182

```python
axChead.plot([0.00, 0.84], [0.28, 0.28], color=LIGHT, lw=0.6)
```
Draws the single subtle rule immediately beneath the two Panel C column headers.

### Line 183

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 184

```python
# Table rows
```
Human-readable comment: Table rows.

### Line 185

```python
rows = [
```
Starts the list of four illustrative reconstruction classes.

### Line 186

```python
    ("A→G only", "Unambiguous change", BLUE),
```
Defines the unambiguous-change example: only A→G is optimal.

### Line 187

```python
    ("A→G or C→G", "State ambiguity", ORANGE),
```
Defines the state-ambiguity example: A→G and C→G are both optimal and both imply a change.

### Line 188

```python
    ("A→G or G→G", "Placement ambiguity", PURPLE),
```
Defines the placement-ambiguity example: A→G and G→G are both optimal, so the change may or may not lie on the focal edge.

### Line 189

```python
    ("G→G only", "No change", GREY),
```
Defines the no-change example: only G→G is optimal.

### Line 190

```python
]
```
Closes the list, function call, or settings block opened on the preceding lines.

### Line 191

```python
ysC = [0.87, 0.61, 0.35, 0.09]
```
Defines the four row heights.

### Line 192

```python
for i, (lhs, rhs, c) in enumerate(rows):
```
Loops through the four Panel C rows.

### Line 193

```python
    if i > 0:
```
Checks whether the current row is not the first.

### Line 194

```python
        axC1.plot([0, 1], [ysC[i]+0.13, ysC[i]+0.13], color="#EEEEEE", lw=0.5)
```
Adds a very faint separator above rows 2–4.

### Line 195

```python
    axC1.text(0.00, ysC[i], lhs, fontsize=6.3, color=INK, va="center")
```
Places the optimal pair-set expression in the left column.

### Line 196

```python
    axC1.text(0.58, ysC[i], rhs, fontsize=6.3, fontweight="bold",
```
Begins placing the BRANCHSNV classification in the right column.

### Line 197

```python
              color=c, va="center")
```
Continues the appearance and alignment settings for the drawing command started on the preceding line.

### Line 198

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 199

```python
axC2.text(0.00, 0.64, "No arbitrary tie-breaking",
```
Begins the bold statement `No arbitrary tie-breaking`.

### Line 200

```python
          fontsize=7.2, fontweight="bold", color=INK, va="center")
```
Continues the appearance and alignment settings for the drawing command started on the preceding line.

### Line 201

```python
axC2.text(0.00, 0.32,
```
Starts the explanatory text under that statement.

### Line 202

```python
          "All globally optimal focal-edge\nstate pairs are retained.",
```
Part of the current drawing command or data definition; it supplies values used by the surrounding lines.

### Line 203

```python
          fontsize=6.1, color=GREY, va="center", linespacing=1.25)
```
Continues the appearance and alignment settings for the drawing command started on the preceding line.

### Line 204

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 205

```python
# ======================================================
```
Human-readable comment: ======================================================.

### Line 206

```python
# Design safeguards
```
Human-readable comment: Design safeguards.

### Line 207

```python
# ======================================================
```
Human-readable comment: ======================================================.

### Line 208

```python
axF.text(0.00, 0.96, "DESIGN SAFEGUARDS", fontsize=6.2, fontweight="bold",
```
Begins the `DESIGN SAFEGUARDS` heading.

### Line 209

```python
         color=GREY, va="top")
```
Continues the appearance and alignment settings for the drawing command started on the preceding line.

### Line 210

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 211

```python
safeguards = [
```
Starts the list of the five safeguards.

### Line 212

```python
    ("Explicit root", "defines direction"),
```
Defines `Explicit root — defines direction`.

### Line 213

```python
    ("Exact descendants", "defines branch"),
```
Defines `Exact descendants — defines branch`.

### Line 214

```python
    ("Exact taxon labels", "defines correspondence"),
```
Defines `Exact taxon labels — defines correspondence`.

### Line 215

```python
    ("Complete optimal set", "retains uncertainty"),
```
Defines `Complete optimal set — retains uncertainty`.

### Line 216

```python
    ("Deterministic provenance", "supports auditability"),
```
Defines `Deterministic provenance — supports auditability`.

### Line 217

```python
]
```
Closes the list, function call, or settings block opened on the preceding lines.

### Line 218

```python
centres = [0.10, 0.30, 0.50, 0.70, 0.90]
```
Defines five evenly spaced column centres for the safeguards.

### Line 219

```python
for i, (x, (title, subtitle)) in enumerate(zip(centres, safeguards)):
```
Loops through the five safeguards and their positions.

### Line 220

```python
    axF.text(x, 0.49, title, fontsize=6.1, fontweight="bold",
```
Begins drawing each bold safeguard title.

### Line 221

```python
             ha="center", va="center", color=INK)
```
Continues the appearance and alignment settings for the drawing command started on the preceding line.

### Line 222

```python
    axF.text(x, 0.16, subtitle, fontsize=5.9,
```
Begins drawing the smaller explanatory subtitle.

### Line 223

```python
             ha="center", va="center", color=GREY)
```
Continues the appearance and alignment settings for the drawing command started on the preceding line.

### Line 224

```python
    if i < 4:
```
Checks whether a vertical separator is needed after the current safeguard.

### Line 225

```python
        sep = (centres[i]+centres[i+1])/2
```
Calculates the midpoint between this safeguard and the next one.

### Line 226

```python
        axF.plot([sep, sep], [0.12, 0.65], color=LIGHT, lw=0.6)
```
Draws the pale vertical separator.

### Line 227

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 228

```python
# ---------- Export ----------
```
Human-readable comment: ---------- Export ----------.

### Line 229

```python
outdir = Path(__file__).resolve().parent
```
Sets the output directory to the directory containing this script.

### Line 230

```python
pdf = outdir / "Figure_1.pdf"
```
Creates the output filename `Figure_1.pdf`.

### Line 231

```python
svg = outdir / "Figure_1_editable.svg"
```
Creates the editable SVG filename.

### Line 232

```python
png = outdir / "Figure_1_preview_600dpi.png"
```
Creates the 600-dpi PNG preview filename.

### Line 233

```python
tif = outdir / "Figure_1_1000dpi.tiff"
```
Creates the 1000-dpi TIFF filename.

### Line 234

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 235

```python
fig.savefig(pdf, bbox_inches="tight", pad_inches=0.02)
```
Exports the vector PDF.

### Line 236

```python
fig.savefig(svg, bbox_inches="tight", pad_inches=0.02)
```
Exports the editable SVG.

### Line 237

```python
fig.savefig(png, dpi=600, bbox_inches="tight", pad_inches=0.02)
```
Exports the PNG preview at 600 dpi.

### Line 238

```python
fig.savefig(tif, dpi=1000, bbox_inches="tight", pad_inches=0.02,
```
Begins exporting the TIFF at 1000 dpi.

### Line 239

```python
            pil_kwargs={"compression":"tiff_lzw"})
```
Uses lossless LZW compression for the TIFF.

### Line 240

```python

```
Blank line used only to separate logical blocks and make the script easier to read.

### Line 241

```python
plt.show()
```
Displays the figure when the script is run interactively.

### Line 242

```python
print("Figure 1 exported.")
```
Prints a confirmation message after export.

## What can be changed safely

Text wording, output filenames, and colours can be changed without changing the scientific topology. Layout coordinates can also be adjusted, but every change should be checked visually at final print size.

## What must be re-checked if changed

The topology coordinates and the nine nucleotide states in Panel A jointly define the scientific example. If the tree topology or any of the states are changed, independently re-check that the only optimal focal-edge pair is still `A→G` before using the revised figure.
