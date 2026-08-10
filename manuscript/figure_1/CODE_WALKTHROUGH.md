# Figure 1 code walkthrough

This document explains `make_figure_1_exact.py` **line by line in plain English**. It assumes no prior Python or Matplotlib experience.

## The 60-second mental model

The script does not calculate BRANCHSNV results from data. It **draws a scientifically defined schematic**. Think of the page as a blank sheet of paper whose width and height are each described from 0 to 1. The code creates several invisible rectangular drawing areas (`axes`) and then places lines, circles, letters, and labels inside those areas at exact coordinates. Panels A, B, and C are therefore assembled from simple vector objects.

A few Python ideas used repeatedly:

- `x = ...` stores a value under a name.
- `[a, b, c]` is a list.
- `for ...:` repeats the indented lines below it.
- `if ...:` runs the indented line only when the condition is true.
- `ax.plot(...)` draws a line.
- `ax.text(...)` writes text.
- `Circle(...)` creates a circle.
- Coordinates inside each axes run from 0 (left/bottom) to 1 (right/top).
- `fontsize`, `color`, `ha` (horizontal alignment), and `va` (vertical alignment) control appearance.

## Line-by-line explanation

**Line 1**

```python
import matplotlib.pyplot as plt
```

Imports Matplotlib's plotting interface and gives it the short name `plt`. This is the main drawing library used by the script.

**Line 2**

```python
from matplotlib.patches import Circle
```

Imports the `Circle` shape used for the root, tip markers, and the A/G endpoint-state circles.

**Line 3**

```python
from matplotlib.lines import Line2D
```

Imports `Line2D`, which is used to draw the long horizontal rules separating major figure sections.

**Line 4**

```python
import matplotlib as mpl
```

Imports Matplotlib itself as `mpl` so global typography/export settings can be configured.

**Line 5**

```python
from pathlib import Path
```

Imports Python's `Path` object for constructing output-file paths safely.

**Line 6**

```python

```

Blank line used only to separate logical blocks and make the script easier to read.

**Line 7**

```python
# Cell Press production dimensions
```

Comment marking the start of the figure-size settings.

**Line 8**

```python
FIG_W, FIG_H = 6.50, 5.10  # 16.5 × 13.0 cm
```

Sets the artwork to 6.50 × 5.10 inches (16.5 × 13.0 cm), i.e. a Cell Press full-width figure that fits on one page.

**Line 9**

```python

```

Blank line used only to separate logical blocks and make the script easier to read.

**Line 10**

```python
mpl.rcParams.update({
```

Starts a dictionary of global Matplotlib settings.

**Line 11**

```python
    "font.family": "Arimo",  # Arial-compatible preview; SVG/PDF text remains editable
```

Uses Arimo for this locked render because Microsoft Arial was not available in the execution environment. Arimo is metrically compatible with Arial; the vector text remains editable.

**Line 12**

```python
    "font.size": 7.0,
```

Sets the default text size to 7 pt, inside Cell Press's recommended ~6–8 pt range at final print size.

**Line 13**

```python
    "svg.fonttype": "none",
```

Keeps SVG text as real editable text rather than turning every letter into a vector outline.

**Line 14**

```python
    "pdf.fonttype": 42,
```

Requests TrueType-style font embedding in PDF output so text remains high quality and portable.

**Line 15**

```python
    "ps.fonttype": 42,
```

Applies the same font-embedding choice to PostScript-based output.

**Line 16**

```python
})
```

Closes the global settings dictionary.

**Line 17**

```python

```

Blank line used only to separate logical blocks and make the script easier to read.

**Line 18**

```python
INK = "#222222"
```

Defines the near-black colour used for most text and tree lines.

**Line 19**

```python
GREY = "#666666"
```

Defines the medium grey used for secondary labels.

**Line 20**

```python
LIGHT = "#D9D9D9"
```

Defines the pale grey used for dividers and table rules.

**Line 21**

```python
BLUE = "#1F5AA6"
```

Defines blue as the colour for the observed/clade-exclusivity side of the figure.

**Line 22**

```python
ORANGE = "#D95F02"
```

Defines orange as the colour for inferred focal-edge substitution.

**Line 23**

```python
RED = "#B2182B"
```

Defines red for the focal edge and the recurrent outside G state.

**Line 24**

```python
PURPLE = "#7B3294"
```

Defines purple for the placement-ambiguity class.

**Line 25**

```python

```

Blank line used only to separate logical blocks and make the script easier to read.

**Line 26**

```python
fig = plt.figure(figsize=(FIG_W, FIG_H), facecolor="white")
```

Creates the blank white figure canvas at the dimensions defined on line 8.

**Line 27**

```python

```

Blank line used only to separate logical blocks and make the script easier to read.

**Line 28**

```python
# Main layout grid
```

Comment marking the start of the fixed layout grid.

**Line 29**

```python
axA = fig.add_axes([0.055, 0.61, 0.89, 0.34])
```

Creates the axes occupying Panel A. The four numbers are left position, bottom position, width, and height, each expressed as a fraction of the full figure.

**Line 30**

```python
axB1 = fig.add_axes([0.075, 0.325, 0.34, 0.235])
```

Creates the left half of Panel B, which contains the observed clade-exclusivity question.

**Line 31**

```python
axBmid = fig.add_axes([0.455, 0.325, 0.08, 0.235])
```

Creates the narrow middle part of Panel B containing the ≠ symbol and 'kept separate' label.

**Line 32**

```python
axB2 = fig.add_axes([0.575, 0.325, 0.35, 0.235])
```

Creates the right half of Panel B, which contains the inferred focal-edge substitution question.

**Line 33**

```python

```

Blank line used only to separate logical blocks and make the script easier to read.

**Line 34**

```python
# Panel C: dedicated header and body axes
```

Comment explaining that Panel C is deliberately split into a header axis and body axes to prevent the table rule from floating or overlapping text.

**Line 35**

```python
axChead = fig.add_axes([0.075, 0.230, 0.835, 0.045])
```

Creates the header strip for Panel C, holding the two column headers and their underline.

**Line 36**

```python
axC1 = fig.add_axes([0.075, 0.135, 0.47, 0.095])
```

Creates the left body of Panel C, containing the optimal state-pair sets and reported classes.

**Line 37**

```python
axC2 = fig.add_axes([0.60, 0.135, 0.31, 0.095])
```

Creates the right body of Panel C, containing the 'No arbitrary tie-breaking' explanation.

**Line 38**

```python

```

Blank line used only to separate logical blocks and make the script easier to read.

**Line 39**

```python
axF = fig.add_axes([0.055, 0.025, 0.89, 0.085])
```

Creates the bottom Design Safeguards strip.

**Line 40**

```python

```

Blank line used only to separate logical blocks and make the script easier to read.

**Line 41**

```python
for ax in (axA, axB1, axBmid, axB2, axChead, axC1, axC2, axF):
```

Loops over every axes object that was just created.

**Line 42**

```python
    ax.set_xlim(0, 1)
```

Makes the horizontal coordinate system of each axes run from 0 to 1. This lets the code place elements using simple relative coordinates.

**Line 43**

```python
    ax.set_ylim(0, 1)
```

Does the same for the vertical coordinate system.

**Line 44**

```python
    ax.axis("off")
```

Turns off normal chart axes, ticks, and borders because this is a schematic figure rather than a numerical plot.

**Line 45**

```python

```

Blank line used only to separate logical blocks and make the script easier to read.

**Line 46**

```python
# Major section separators
```

Comment marking the horizontal separators between the major sections.

**Line 47**

```python
for y in [0.595, 0.305, 0.122]:
```

Loops over the three vertical positions at which long divider rules are required.

**Line 48**

```python
    fig.add_artist(Line2D([0.055, 0.945], [y, y], transform=fig.transFigure,
```

Adds a full-figure horizontal line spanning the main content width at the current vertical position.

**Line 49**

```python
                          color=LIGHT, lw=0.7))
```

Sets that divider to pale grey and 0.7-pt width.

**Line 50**

```python

```

Blank line used only to separate logical blocks and make the script easier to read.

**Line 51**

```python
# ======================================================
```

Decorative comment line marking the beginning of Panel A.

**Line 52**

```python
# Panel A
```

Names the section being built next: Panel A.

**Line 53**

```python
# ======================================================
```

Decorative comment line marking the Panel A boundary.

**Line 54**

```python
axA.text(-0.035, 1.02, "A", fontsize=10.5, fontweight="bold", va="top", color=INK)
```

Places the capital panel label `A` at the upper-left of Panel A.

**Line 55**

```python
axA.text(0.005, 1.015, "One branch, one site", fontsize=8.6, fontweight="bold",
```

Begins the Panel A heading, `One branch, one site`.

**Line 56**

```python
         va="top", color=INK)
```

Finishes the Panel A heading settings, aligning it to the top and using the main text colour.

**Line 57**

```python

```

Blank line used only to separate logical blocks and make the script easier to read.

**Line 58**

```python
xR, xX, xF, xO, xY, xTip = 0.08, 0.22, 0.38, 0.38, 0.25, 0.51
```

Defines the horizontal coordinates of the key internal tree nodes and of the common tip endpoint. The names are shorthand for root (`R`), upper internal node (`X`), focal node (`F`), outside sister node (`O`), lower internal node (`Y`), and tips.

**Line 59**

```python
ys = [0.89, 0.80, 0.71, 0.54, 0.45, 0.36, 0.19, 0.10, 0.01]
```

Defines the vertical positions of the nine terminal taxa, from top to bottom.

**Line 60**

```python
yF = sum(ys[:3]) / 3
```

Calculates the vertical centre of the three focal descendants.

**Line 61**

```python
yO = sum(ys[3:6]) / 3
```

Calculates the vertical centre of the three taxa in the focal clade's outside sister group.

**Line 62**

```python
yY = sum(ys[6:]) / 3
```

Calculates the vertical centre of the three lower outside taxa.

**Line 63**

```python
yX = (yF + yO) / 2
```

Places internal node X halfway between the focal group and its sister group.

**Line 64**

```python
yR = (yX + yY) / 2
```

Places the root halfway between the upper and lower parts of the tree.

**Line 65**

```python

```

Blank line used only to separate logical blocks and make the script easier to read.

**Line 66**

```python
lw_tree = 0.8
```

Stores the standard phylogeny line width (0.8 pt), comfortably inside the Cell Press 0.5–1.5 pt guidance.

**Line 67**

```python
axA.plot([xR, xR], [yY, yX], color=INK, lw=lw_tree)
```

Draws the vertical part of the root connecting the upper and lower major branches.

**Line 68**

```python
axA.plot([xR, xX], [yX, yX], color=INK, lw=lw_tree)
```

Draws the root's horizontal branch to the upper internal node X.

**Line 69**

```python
axA.plot([xR, xY], [yY, yY], color=INK, lw=lw_tree)
```

Draws the root's horizontal branch to the lower internal node Y.

**Line 70**

```python
axA.plot([xX, xX], [yO, yF], color=INK, lw=lw_tree)
```

Draws the vertical connector at X between the focal node and its outside sister node.

**Line 71**

```python
axA.plot([xX, xF], [yO, yO], color=INK, lw=lw_tree)
```

Draws the branch from X to the outside sister node in standard black.

**Line 72**

```python
axA.plot([xX, xF], [yF, yF], color=RED, lw=1.5)
```

Draws the focal edge from X to F in red and at 1.5 pt, making the branch being interrogated visually explicit.

**Line 73**

```python

```

Blank line used only to separate logical blocks and make the script easier to read.

**Line 74**

```python
axA.plot([xF, xF], [ys[2], ys[0]], color=INK, lw=lw_tree)
```

Draws the vertical connector joining the three focal descendant tips.

**Line 75**

```python
for yy in ys[:3]:
```

Starts a loop over the first three tip heights: these are the focal descendants.

**Line 76**

```python
    axA.plot([xF, xTip], [yy, yy], color=INK, lw=lw_tree)
```

For each focal descendant, draws the horizontal terminal branch from the focal internal node to the tip.

**Line 77**

```python

```

Blank line used only to separate logical blocks and make the script easier to read.

**Line 78**

```python
axA.plot([xO, xO], [ys[5], ys[3]], color=INK, lw=lw_tree)
```

Draws the vertical connector joining the three taxa in the focal clade's outside sister group.

**Line 79**

```python
for yy in ys[3:6]:
```

Starts a loop over those three outside sister-group taxa.

**Line 80**

```python
    axA.plot([xO, xTip], [yy, yy], color=INK, lw=lw_tree)
```

Draws each sister-group terminal branch.

**Line 81**

```python

```

Blank line used only to separate logical blocks and make the script easier to read.

**Line 82**

```python
axA.plot([xY, xY], [ys[8], ys[6]], color=INK, lw=lw_tree)
```

Draws the vertical connector joining the three lower outside taxa.

**Line 83**

```python
for yy in ys[6:]:
```

Starts a loop over those three lower taxa.

**Line 84**

```python
    axA.plot([xY, xTip], [yy, yy], color=INK, lw=lw_tree)
```

Draws each lower terminal branch.

**Line 85**

```python

```

Blank line used only to separate logical blocks and make the script easier to read.

**Line 86**

```python
axA.add_patch(Circle((xR, yR), 0.010, ec=INK, fc=INK, lw=0.7))
```

Draws a filled black circle at the computed root position.

**Line 87**

```python
axA.text(xR-0.02, yR-0.06, "root", fontsize=6.1, color=GREY, ha="right")
```

Adds the small grey word `root` beside that circle.

**Line 88**

```python

```

Blank line used only to separate logical blocks and make the script easier to read.

**Line 89**

```python
for i, yy in enumerate(ys):
```

Loops over all nine tip positions while keeping both the tip number (`i`) and vertical position (`yy`).

**Line 90**

```python
    ec = BLUE if i < 3 else GREY
```

Chooses blue outlines for the first three focal tips and grey outlines for all other tips.

**Line 91**

```python
    axA.add_patch(Circle((xTip, yy), 0.010, ec=ec, fc="white", lw=0.8))
```

Draws the open circular marker at each tip using the chosen outline colour.

**Line 92**

```python

```

Blank line used only to separate logical blocks and make the script easier to read.

**Line 93**

```python
axA.text((xX+xF)/2, yF+0.075, "focal edge", fontsize=6.3, fontweight="bold",
```

Begins the `focal edge` text label, centring it above the red branch.

**Line 94**

```python
         color=RED, ha="center")
```

Finishes the label styling in red.

**Line 95**

```python

```

Blank line used only to separate logical blocks and make the script easier to read.

**Line 96**

```python
bx = 0.545
```

Stores the x-coordinate used for the bracket around the three focal descendants.

**Line 97**

```python
axA.plot([bx, bx], [ys[2]-0.022, ys[0]+0.022], color=BLUE, lw=0.8)
```

Draws the long vertical part of that blue bracket.

**Line 98**

```python
axA.plot([bx-0.012, bx], [ys[0]+0.022, ys[0]+0.022], color=BLUE, lw=0.8)
```

Draws the small upper horizontal cap of the bracket.

**Line 99**

```python
axA.plot([bx-0.012, bx], [ys[2]-0.022, ys[2]-0.022], color=BLUE, lw=0.8)
```

Draws the small lower horizontal cap.

**Line 100**

```python
axA.text(bx+0.02, yF, "focal\ndescendants", fontsize=6.2, fontweight="bold",
```

Begins the two-line label `focal descendants` to the right of the bracket.

**Line 101**

```python
         color=BLUE, va="center", linespacing=1.0)
```

Sets its colour, vertical alignment, and compact line spacing.

**Line 102**

```python

```

Blank line used only to separate logical blocks and make the script easier to read.

**Line 103**

```python
state_x = 0.69
```

Stores the horizontal position used for the nucleotide-state column.

**Line 104**

```python
axA.text(state_x, 0.99, "one site", fontsize=6.4, fontweight="bold",
```

Begins the `one site` heading above that nucleotide column.

**Line 105**

```python
         ha="center", va="top")
```

Centres the heading horizontally and anchors it from its top.

**Line 106**

```python
states = ["G","G","G","A","A","A","A","A","G"]
```

Defines the nine observed nucleotide states shown beside the nine taxa: focal G/G/G; outside A/A/A/A/A/G.

**Line 107**

```python
for i, (yy, s) in enumerate(zip(ys, states)):
```

Loops through the tree-tip heights and nucleotide states together.

**Line 108**

```python
    c = BLUE if i < 3 else (RED if i == 8 else INK)
```

Assigns blue to the focal G states, red to the outside recurrent G, and black to the remaining outside A states.

**Line 109**

```python
    axA.text(state_x, yy, s, fontsize=7.0, fontweight="bold", color=c,
```

Begins drawing the nucleotide letter at the matching tip height.

**Line 110**

```python
             ha="center", va="center")
```

Centres each nucleotide letter precisely on its row.

**Line 111**

```python

```

Blank line used only to separate logical blocks and make the script easier to read.

**Line 112**

```python
axA.text(0.80, 0.73, "Focal clade: G G G", fontsize=6.6, fontweight="bold",
```

Begins a concise blue callout stating the focal clade state pattern.

**Line 113**

```python
         color=BLUE, ha="left")
```

Finishes the callout styling and left alignment.

**Line 114**

```python
axA.text(0.80, 0.53, "Outside includes G", fontsize=6.6, fontweight="bold",
```

Begins the red callout noting that G also occurs outside the focal clade.

**Line 115**

```python
         color=RED, ha="left")
```

Finishes the callout styling.

**Line 116**

```python

```

Blank line used only to separate logical blocks and make the script easier to read.

**Line 117**

```python
# ======================================================
```

Decorative comment line marking the end of Panel A/start of Panel B.

**Line 118**

```python
# Panel B
```

Names the next section: Panel B.

**Line 119**

```python
# ======================================================
```

Decorative comment line marking the Panel B boundary.

**Line 120**

```python
fig.text(0.055, 0.575, "B", fontsize=10.5, fontweight="bold", color=INK, va="top")
```

Places the capital panel label `B` at the full-figure level.

**Line 121**

```python
fig.text(0.095, 0.575, "Two questions, different answers",
```

Begins the Panel B heading `Two questions, different answers`.

**Line 122**

```python
         fontsize=8.6, fontweight="bold", color=INK, va="top")
```

Finishes that heading's font and alignment settings.

**Line 123**

```python

```

Blank line used only to separate logical blocks and make the script easier to read.

**Line 124**

```python
axB1.text(0.00, 0.90, "OBSERVED", fontsize=6.3, fontweight="bold",
```

Adds the blue category label `OBSERVED` above the left-hand analysis.

**Line 125**

```python
          color=BLUE, va="top")
```

Finishes the observed label formatting.

**Line 126**

```python
axB1.text(0.00, 0.74, "Clade-exclusive?", fontsize=8.2, fontweight="bold",
```

Adds the question `Clade-exclusive?`.

**Line 127**

```python
          color=INK, va="top")
```

Finishes the question formatting.

**Line 128**

```python
axB1.text(0.00, 0.48, "focal", fontsize=6.0, color=GREY, va="center")
```

Adds the small grey label `focal` before the focal nucleotide states.

**Line 129**

```python
for j in range(3):
```

Starts a three-iteration loop, one for each focal descendant.

**Line 130**

```python
    axB1.text(0.16+0.11*j, 0.48, "G", fontsize=7.5, fontweight="bold",
```

Places a blue G for each focal descendant, evenly spaced horizontally.

**Line 131**

```python
              color=BLUE, ha="center", va="center")
```

Finishes the position/alignment settings for those G letters.

**Line 132**

```python
axB1.text(0.00, 0.31, "outside", fontsize=6.0, color=GREY, va="center")
```

Adds the small grey label `outside` before the outside nucleotide states.

**Line 133**

```python
for j, s in enumerate(["A","A","A","A","A","G"]):
```

Loops over the six outside states A/A/A/A/A/G.

**Line 134**

```python
    axB1.text(0.16+0.09*j, 0.31, s, fontsize=7.1, fontweight="bold",
```

Places each outside nucleotide at an evenly spaced horizontal position.

**Line 135**

```python
              color=(RED if s == "G" else INK), ha="center", va="center")
```

Colours the recurrent outside G red and all outside A states black.

**Line 136**

```python
axB1.text(0.00, 0.06, "NO", fontsize=13.0, fontweight="bold",
```

Begins the large blue result word `NO`.

**Line 137**

```python
          color=BLUE, va="bottom")
```

Finishes the placement of `NO`.

**Line 138**

```python
axB1.text(0.23, 0.085, "not fixed-exclusive", fontsize=6.9, fontweight="bold",
```

Begins the bold explanation `not fixed-exclusive` beside `NO`.

**Line 139**

```python
          color=INK, va="bottom")
```

Finishes that explanation's position and colour.

**Line 140**

```python
axB1.text(0.00, 0.005, "G occurs outside the clade", fontsize=6.0,
```

Begins the small grey reason, `G occurs outside the clade`.

**Line 141**

```python
          color=GREY, va="bottom")
```

Finishes the reason's placement.

**Line 142**

```python

```

Blank line used only to separate logical blocks and make the script easier to read.

**Line 143**

```python
axBmid.text(0.50, 0.54, "≠", fontsize=28, ha="center", va="center", color=INK)
```

Places the large ≠ symbol in the centre strip, visually stating that the observed and inferred questions are not equivalent.

**Line 144**

```python
axBmid.text(0.50, 0.24, "kept separate", fontsize=5.9, ha="center",
```

Adds the small phrase `kept separate` beneath the ≠ symbol.

**Line 145**

```python
            va="center", color=GREY)
```

Finishes its alignment and colour.

**Line 146**

```python

```

Blank line used only to separate logical blocks and make the script easier to read.

**Line 147**

```python
axB2.text(0.00, 0.90, "INFERRED", fontsize=6.3, fontweight="bold",
```

Adds the orange category label `INFERRED` above the right-hand analysis.

**Line 148**

```python
          color=ORANGE, va="top")
```

Finishes that label formatting.

**Line 149**

```python
axB2.text(0.00, 0.74, "Substitution on the focal edge?", fontsize=8.2,
```

Begins the question `Substitution on the focal edge?`.

**Line 150**

```python
          fontweight="bold", color=INK, va="top")
```

Finishes the question styling.

**Line 151**

```python
axB2.text(0.26, 0.46, "parent", fontsize=5.9, color=GREY, ha="center")
```

Labels the left endpoint of the schematic as the reconstructed parent state.

**Line 152**

```python
axB2.text(0.74, 0.46, "child", fontsize=5.9, color=GREY, ha="center")
```

Labels the right endpoint as the child state.

**Line 153**

```python
axB2.text(0.50, 0.55, "all global optima", fontsize=5.9, color=GREY, ha="center")
```

Adds `all global optima` above the endpoint relationship, indicating that the result summarizes every globally minimum-change reconstruction.

**Line 154**

```python
for x, state, edge in [(0.26, "A", ORANGE), (0.74, "G", BLUE)]:
```

Loops over the two endpoint circles: parent A in orange and child G in blue.

**Line 155**

```python
    axB2.add_patch(Circle((x, 0.31), 0.055, ec=edge, fc="white", lw=1.0))
```

Draws the current endpoint circle.

**Line 156**

```python
    axB2.text(x, 0.31, state, fontsize=7.2, fontweight="bold",
```

Begins placing its nucleotide letter inside the circle.

**Line 157**

```python
              ha="center", va="center", color=INK)
```

Centres and styles that nucleotide letter.

**Line 158**

```python
axB2.annotate("", xy=(0.66,0.31), xytext=(0.34,0.31),
```

Begins drawing the arrow from the parent A state to the child G state.

**Line 159**

```python
              arrowprops=dict(arrowstyle="-|>", lw=0.9, color=INK,
```

Defines the arrow style, width, and colour.

**Line 160**

```python
                              mutation_scale=8.5))
```

Sets the arrowhead size.

**Line 161**

```python
axB2.text(0.00, 0.06, "YES", fontsize=13.0, fontweight="bold",
```

Begins the large orange result word `YES`.

**Line 162**

```python
          color=ORANGE, va="bottom")
```

Finishes its position.

**Line 163**

```python
axB2.text(0.23, 0.085, "unambiguous A→G", fontsize=6.9, fontweight="bold",
```

Begins the bold interpretation `unambiguous A→G`.

**Line 164**

```python
          color=INK, va="bottom")
```

Finishes the interpretation's placement.

**Line 165**

```python
axB2.text(0.00, 0.005, r"$P^\ast=\{A\rightarrow G\}$", fontsize=6.2,
```

Begins the mathematical notation for the complete optimal focal-edge pair set, P* = {A→G}.

**Line 166**

```python
          color=GREY, va="bottom")
```

Finishes the equation styling.

**Line 167**

```python

```

Blank line used only to separate logical blocks and make the script easier to read.

**Line 168**

```python
# ======================================================
```

Decorative comment line marking the start of Panel C.

**Line 169**

```python
# Panel C — corrected table hierarchy
```

Names Panel C and notes that its table hierarchy was deliberately corrected.

**Line 170**

```python
# ======================================================
```

Decorative comment line marking the Panel C boundary.

**Line 171**

```python
fig.text(0.055, 0.292, "C", fontsize=10.5, fontweight="bold", color=INK, va="top")
```

Places the capital panel label `C`.

**Line 172**

```python
fig.text(0.095, 0.292, "Retain all optimal focal-edge solutions",
```

Begins the Panel C heading `Retain all optimal focal-edge solutions`.

**Line 173**

```python
         fontsize=8.6, fontweight="bold", color=INK, va="top")
```

Finishes that heading.

**Line 174**

```python

```

Blank line used only to separate logical blocks and make the script easier to read.

**Line 175**

```python
# Column headers — no floating divider above them
```

Comment explaining that the next lines are column headers and that there is deliberately no stray divider above them.

**Line 176**

```python
axChead.text(0.00, 0.72, "Optimal pair set", fontsize=5.9, color=GREY,
```

Adds the left table header `Optimal pair set`.

**Line 177**

```python
             va="center", ha="left")
```

Finishes its alignment.

**Line 178**

```python
axChead.text(0.49, 0.72, "BRANCHSNV reports", fontsize=5.9, color=GREY,
```

Adds the right table header `BRANCHSNV reports`.

**Line 179**

```python
             va="center", ha="left")
```

Finishes its alignment.

**Line 180**

```python

```

Blank line used only to separate logical blocks and make the script easier to read.

**Line 181**

```python
# Proper table rule: immediately UNDER the column headers.
```

Comment explaining the table rule's intended position.

**Line 182**

```python
axChead.plot([0.00, 0.84], [0.28, 0.28], color=LIGHT, lw=0.6)
```

Draws one subtle grey horizontal rule immediately below the two column headers.

**Line 183**

```python

```

Blank line used only to separate logical blocks and make the script easier to read.

**Line 184**

```python
# Table rows
```

Comment marking the start of the four table rows.

**Line 185**

```python
rows = [
```

Starts a Python list containing the four possible example classifications shown in Panel C.

**Line 186**

```python
    (r"$P^\ast=\{A\rightarrow G\}$", "Unambiguous change", BLUE),
```

Defines the unambiguous-change example: one changing optimal pair, A→G, shown in blue.

**Line 187**

```python
    (r"$P^\ast=\{A\rightarrow G,\ C\rightarrow G\}$", "State ambiguity", ORANGE),
```

Defines the state-ambiguity example: two changing optimal pairs, A→G and C→G, shown in orange.

**Line 188**

```python
    (r"$P^\ast=\{A\rightarrow G,\ G\rightarrow G\}$", "Placement ambiguity", PURPLE),
```

Defines the placement-ambiguity example: a changing pair A→G and a non-changing pair G→G, shown in purple.

**Line 189**

```python
    (r"$P^\ast=\{G\rightarrow G\}$", "No change", GREY),
```

Defines the no-change example: only G→G, shown in grey.

**Line 190**

```python
]
```

Closes the list of table rows.

**Line 191**

```python
ysC = [0.87, 0.61, 0.35, 0.09]
```

Defines the four vertical positions used for those rows.

**Line 192**

```python
for i, (lhs, rhs, c) in enumerate(rows):
```

Loops through each table row, giving access to the row number, pair-set text, reported class, and display colour.

**Line 193**

```python
    if i > 0:
```

Checks whether the row is not the first row.

**Line 194**

```python
        axC1.plot([0, 1], [ysC[i]+0.13, ysC[i]+0.13], color="#EEEEEE", lw=0.5)
```

For rows 2–4, draws a very faint separator above the row to improve readability.

**Line 195**

```python
    axC1.text(0.00, ysC[i], lhs, fontsize=6.3, color=INK, va="center")
```

Places the optimal pair-set expression in the left column.

**Line 196**

```python
    axC1.text(0.58, ysC[i], rhs, fontsize=6.3, fontweight="bold",
```

Begins placing the BRANCHSNV classification in the right column.

**Line 197**

```python
              color=c, va="center")
```

Colours and vertically centres the classification.

**Line 198**

```python

```

Blank line used only to separate logical blocks and make the script easier to read.

**Line 199**

```python
axC2.text(0.00, 0.64, "No arbitrary tie-breaking",
```

Begins the bold statement `No arbitrary tie-breaking` in the right-hand Panel C note.

**Line 200**

```python
          fontsize=7.2, fontweight="bold", color=INK, va="center")
```

Finishes its styling.

**Line 201**

```python
axC2.text(0.00, 0.32,
```

Starts the two-line explanation underneath.

**Line 202**

```python
          "All globally optimal focal-edge\nstate pairs are retained.",
```

Provides the actual explanation: every globally optimal focal-edge state pair is retained.

**Line 203**

```python
          fontsize=6.1, color=GREY, va="center", linespacing=1.25)
```

Sets the explanatory text size, grey colour, centring, and line spacing.

**Line 204**

```python

```

Blank line used only to separate logical blocks and make the script easier to read.

**Line 205**

```python
# ======================================================
```

Decorative comment line marking the start of the Design Safeguards strip.

**Line 206**

```python
# Design safeguards
```

Names the section `Design safeguards`.

**Line 207**

```python
# ======================================================
```

Decorative comment line marking its boundary.

**Line 208**

```python
axF.text(0.00, 0.96, "DESIGN SAFEGUARDS", fontsize=6.2, fontweight="bold",
```

Begins the `DESIGN SAFEGUARDS` heading at the left of the bottom strip.

**Line 209**

```python
         color=GREY, va="top")
```

Finishes the heading's colour and alignment.

**Line 210**

```python

```

Blank line used only to separate logical blocks and make the script easier to read.

**Line 211**

```python
safeguards = [
```

Starts a list of the five safeguards shown along the bottom.

**Line 212**

```python
    ("Explicit root", "defines direction"),
```

Defines safeguard 1: an explicit root defines branch direction.

**Line 213**

```python
    ("Exact descendants", "defines branch"),
```

Defines safeguard 2: exact descendants define branch identity.

**Line 214**

```python
    ("Exact taxon labels", "defines correspondence"),
```

Defines safeguard 3: exact taxon labels define tree/matrix correspondence.

**Line 215**

```python
    ("Complete optimal set", "retains uncertainty"),
```

Defines safeguard 4: the complete optimal set retains uncertainty.

**Line 216**

```python
    ("Deterministic provenance", "supports auditability"),
```

Defines safeguard 5: deterministic provenance supports auditability.

**Line 217**

```python
]
```

Closes the safeguards list.

**Line 218**

```python
centres = [0.10, 0.30, 0.50, 0.70, 0.90]
```

Defines the five evenly spaced horizontal centres used for the safeguard columns.

**Line 219**

```python
for i, (x, (title, subtitle)) in enumerate(zip(centres, safeguards)):
```

Loops over the positions and safeguards together, unpacking each title and subtitle.

**Line 220**

```python
    axF.text(x, 0.49, title, fontsize=6.1, fontweight="bold",
```

Begins drawing the bold safeguard title.

**Line 221**

```python
             ha="center", va="center", color=INK)
```

Centres the title within its column.

**Line 222**

```python
    axF.text(x, 0.16, subtitle, fontsize=5.9,
```

Begins drawing the smaller explanatory subtitle.

**Line 223**

```python
             ha="center", va="center", color=GREY)
```

Centres the subtitle in grey.

**Line 224**

```python
    if i < 4:
```

Checks whether the current safeguard is one of the first four.

**Line 225**

```python
        sep = (centres[i]+centres[i+1])/2
```

Calculates the midpoint between the current column and the next one.

**Line 226**

```python
        axF.plot([sep, sep], [0.12, 0.65], color=LIGHT, lw=0.6)
```

Draws a pale vertical separator at that midpoint. No separator is drawn after the fifth item.

**Line 227**

```python

```

Blank line used only to separate logical blocks and make the script easier to read.

**Line 228**

```python
# ---------- Export ----------
```

Comment marking the export section.

**Line 229**

```python
outdir = Path("/mnt/data")
```

Sets `/mnt/data` as the output directory used in the original execution environment.

**Line 230**

```python
pdf = outdir / "Figure_1_CellPress_final.pdf"
```

Constructs the output path for the vector PDF.

**Line 231**

```python
svg = outdir / "Figure_1_CellPress_final_editable.svg"
```

Constructs the output path for the editable SVG.

**Line 232**

```python
png = outdir / "Figure_1_CellPress_final_preview_600dpi.png"
```

Constructs the output path for the 600-dpi PNG preview.

**Line 233**

```python
tif = outdir / "Figure_1_CellPress_final_1000dpi.tiff"
```

Constructs the output path for the 1000-dpi TIFF.

**Line 234**

```python

```

Blank line used only to separate logical blocks and make the script easier to read.

**Line 235**

```python
fig.savefig(pdf, bbox_inches="tight", pad_inches=0.02)
```

Saves the figure as a tightly cropped vector PDF with a small amount of outer padding.

**Line 236**

```python
fig.savefig(svg, bbox_inches="tight", pad_inches=0.02)
```

Saves the same artwork as editable SVG.

**Line 237**

```python
fig.savefig(png, dpi=600, bbox_inches="tight", pad_inches=0.02)
```

Saves a 600-dpi PNG preview for convenient viewing and GitHub display.

**Line 238**

```python
fig.savefig(tif, dpi=1000, bbox_inches="tight", pad_inches=0.02,
```

Begins saving the line-art TIFF at 1000 dpi.

**Line 239**

```python
            pil_kwargs={"compression":"tiff_lzw"})
```

Uses LZW compression for the TIFF, matching the Cell Press recommendation for compact lossless TIFF files.

**Line 240**

```python

```

Blank line used only to separate logical blocks and make the script easier to read.

**Line 241**

```python
plt.show()
```

Displays the figure when the script is run interactively.

**Line 242**

```python
print("Final figure exported.")
```

Prints a short confirmation message after export.

## What to change safely

For ordinary repository use, use `make_figure_1.py`, which changes only the output directory so the files are written beside the script. The geometry and plotting logic are unchanged.

For final Cell Press production, the one deliberate visual-production change still required is replacing `Arimo` with `Arial` on a system where Arial is installed, then checking that no text shifts or overlaps before exporting the final PDF/TIFF.

## What not to change without re-checking the science

The topology, the nine nucleotide states, and the focal-edge relationship in Panel A are linked to the conceptual example. Altering lines 58–64, 67–84, or 106–110 can change the topology or state pattern. If those are changed, the stated optimal focal-edge pair set `P* = {A→G}` should be independently re-verified before the figure is used.
