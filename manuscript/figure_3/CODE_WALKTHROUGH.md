# Figure 3 code walkthrough — line by line

This document explains `make_figure_3.py` for a reader who does **not** need to know Python already. It follows the script in order and explains what each non-blank line contributes to the figure or its reproducibility package.

**Script covered:** `make_figure_3.py` (509 lines)  
**SHA-256 of the script documented here:** `86106a42adcbc2fca325da9be856bd8a674cf66c0bdfb441b6dde0cfaea1d920`

Blank-only lines are omitted below because they do not execute anything; they only make the Python source easier to read.

## Very small Python glossary

- **Indentation:** spaces at the start of a line define which lines belong inside a function, loop, condition, or other block.
- **`def`:** defines a reusable function.
- **`return`:** sends a result back from a function.
- **`if` / `elif` / `else`:** choose between alternative actions.
- **`for`:** repeats code for each item in a collection.
- **`with`:** opens a resource such as a file and guarantees cleanup afterwards.
- **List `[...]`:** an ordered collection of values.
- **Dictionary `{...}`:** a collection of key/value pairs.
- **Tuple `(...)`:** a small ordered group of values, often used here for coordinates or plot settings.
- **f-string:** a quoted string beginning with `f` that can insert values inside `{...}`.
- **`ax`:** shorthand used here for one Matplotlib axes, i.e. one drawing area/panel.
- **Axes coordinates:** values from 0 to 1 that describe a location as a fraction of a panel’s width or height.
- **Data coordinates:** coordinates in the actual plotted data system; for the phylogram, x values are branch-length distances and y values correspond to tip positions.

## The overall flow before the line-by-line detail

1. Read the committed empirical result tables and calculate the Panel A totals.
2. Read the real Clade A alignment at `AP009378.1_4301132`.
3. Read the real Clade A Newick tree and extract the minimal subtree containing the five observed `G` taxa.
4. Draw Panel A from the calculated empirical totals.
5. Draw Panel B as a real phylogram with supplied branch lengths retained.
6. Export PDF, SVG, PNG, TIFF, and RGB TIFF versions.
7. Calculate file checksums and update the lightweight package documentation.

## 1. Imports, colour palette, figure size, and global plotting settings

**Line 1** — `from __future__ import annotations`  
Enables postponed evaluation of type annotations. In practice, this makes Python treat many type hints more flexibly and avoids some forward-reference problems.

**Line 3** — `from dataclasses import dataclass`  
Imports `dataclass`, which is used to make a small structured object for carrying the numerical summary values used in Panel A.

**Line 4** — `from io import StringIO`  
Imports `StringIO`, which lets a normal text string behave like an open text file. Biopython can then read the Newick tree string from memory.

**Line 5** — `from pathlib import Path`  
Imports `Path`, Python’s object-oriented way to work with file and directory paths.

**Line 6** — `import hashlib`  
Imports the SHA-256 hashing library used later to calculate file checksums.

**Line 8** — `import matplotlib as mpl`  
Imports the main Matplotlib package under the short name `mpl`; this is used for global plotting settings.

**Line 9** — `import matplotlib.pyplot as plt`  
Imports Matplotlib’s plotting interface as `plt`; this creates the figure, axes, text, lines, and exported files.

**Line 10** — `from matplotlib.lines import Line2D`  
Imports `Line2D`, used for the thin vertical separator between Panels A and B.

**Line 11** — `from matplotlib.patches import FancyBboxPatch, Rectangle`  
Imports two patch shapes: rounded boxes and rectangles. Panel A uses both.

**Line 12** — `from PIL import Image`  
Imports Pillow’s `Image` class so the TIFF can be reopened and explicitly converted to RGB.

**Line 13** — `import pandas as pd`  
Imports pandas as `pd`; pandas reads the tab-separated result tables and performs the small summary calculations.

**Line 14** — `from Bio import Phylo`  
Imports the `Phylo` module from Biopython for reading and querying the real Newick phylogeny.

**Line 16** — `# Figure 1 palette / manuscript conventions`  
Comment marking the start of the colour definitions. These colours are reused consistently through the figure.

**Line 17** — `INK = "#222222"`  
Defines the near-black ink colour used for ordinary text, tree branches, and outlines.

**Line 18** — `GREY = "#666666"`  
Defines the medium grey used for secondary labels such as the site-state heading and scale text.

**Line 19** — `LIGHT_GREY = "#D9D9D9"`  
Defines the pale grey used for the divider between Panels A and B.

**Line 20** — `BLUE = "#1F5AA6"`  
Defines the blue used for the focal clade and the fixed-exclusive/unambiguous category.

**Line 21** — `ORANGE = "#D95F02"`  
Defines the orange used for the non-exclusive recurrent-state category and the outside `G` event.

**Line 22** — `PURPLE = "#7B3294"`  
Defines the purple used for placement ambiguity.

**Line 23** — `PALE_ORANGE = "#FBE8D8"`  
Defines a very pale orange used for the small 4.44% segment in Panel A.

**Line 25** — `# Final artwork is sized for a compact full-width landscape figure.`  
Comment explaining that the next two constants control the physical size of the complete figure.

**Line 26** — `FIG_W = 6.50`  
Sets the final figure width to 6.50 inches.

**Line 27** — `FIG_H = 4.40`  
Sets the final figure height to 4.40 inches.

**Line 29** — `mpl.rcParams.update({`  
Starts a dictionary of global Matplotlib settings. These settings apply to all text and vector exports that follow.

**Line 30** — `"font.family": "sans-serif",`  
Requests a generic sans-serif font family.

**Line 31** — `"font.sans-serif": ["Arial", "Arimo", "Liberation Sans", "DejaVu Sans"],`  
Defines the font preference order. Matplotlib tries the names from left to right and uses the first installed font it can find.

**Line 32** — `"font.size": 7.0,`  
Sets the default text size to 7 points unless an individual text object specifies another size.

**Line 33** — `"pdf.fonttype": 42,`  
Requests TrueType-style font embedding in PDF output so text stays clean and editable/vector-based where supported.

**Line 34** — `"ps.fonttype": 42,`  
Uses the same font-type setting for PostScript output.

**Line 35** — `"svg.fonttype": "none",`  
Keeps SVG text as text rather than converting every character into vector outlines.

**Line 36** — `})`  
Closes the global Matplotlib settings dictionary and applies it.

## 2. The `Summary` data container

**Line 39** — `@dataclass`  
The `@dataclass` decorator tells Python to automatically create an initializer and other useful methods for the class immediately below.

**Line 40** — `class Summary:`  
Begins the `Summary` class. One `Summary` object will hold every count and percentage needed by Panel A.

**Line 41** — `taxa: int`  
Continues the surrounding Python statement or supplies one of its arguments/settings.

**Line 42** — `variable_sites: int`  
Continues the surrounding Python statement or supplies one of its arguments/settings.

**Line 43** — `branches: int`  
Continues the surrounding Python statement or supplies one of its arguments/settings.

**Line 44** — `informative: int`  
Continues the surrounding Python statement or supplies one of its arguments/settings.

**Line 45** — `both: int`  
Continues the surrounding Python statement or supplies one of its arguments/settings.

**Line 46** — `both_pct: float`  
Continues the surrounding Python statement or supplies one of its arguments/settings.

**Line 47** — `unamb_not_fixed: int`  
Continues the surrounding Python statement or supplies one of its arguments/settings.

**Line 48** — `unamb_not_fixed_pct: float`  
Continues the surrounding Python statement or supplies one of its arguments/settings.

**Line 49** — `placement_ambiguous: int`  
Continues the surrounding Python statement or supplies one of its arguments/settings.

**Line 50** — `placement_ambiguous_pct: float`  
Continues the surrounding Python statement or supplies one of its arguments/settings.

**Line 51** — `derived_state_outside: int`  
Continues the surrounding Python statement or supplies one of its arguments/settings.

**Line 52** — `derived_state_outside_pct: float`  
Continues the surrounding Python statement or supplies one of its arguments/settings.

**Line 53** — `descendant_not_fixed: int`  
Continues the surrounding Python statement or supplies one of its arguments/settings.

**Line 54** — `descendant_not_fixed_pct: float`  
Continues the surrounding Python statement or supplies one of its arguments/settings.

## 3. Finding the repository and loading the empirical summary

**Line 57** — `def repo_root() -> Path:`  
Defines a function named `repo_root` and states that it returns a `Path` object.

**Line 58** — `return Path(__file__).resolve().parents[2]`  
Starts from the location of this script, resolves it to an absolute path, then goes up two parent directories to reach the repository root.

**Line 61** — `def load_summary(root: Path) -> Summary:`  
Defines `load_summary`, which reads the empirical result files and returns one populated `Summary` object.

**Line 62** — `ds = pd.read_csv(root / "results/06_empirical_cross_classification/dataset_summary.tsv", sep="\t")`  
Reads `dataset_summary.tsv` as a tab-separated table. This table contains one summary row per empirical dataset.

**Line 63** — `ev = pd.read_csv(root / "results/06_empirical_cross_classification/informative_events.tsv", sep="\t")`  
Reads `informative_events.tsv`, which contains the individual informative empirical events.

**Line 64** — `ev = ev[ev["root_adjacent"] == 0].copy()`  
Keeps only non-root-adjacent events. `.copy()` creates an independent DataFrame rather than a potentially ambiguous view.

**Line 66** — `informative = int(ds["informative"].sum())`  
Adds the `informative` counts across all datasets and converts the result to a normal Python integer.

**Line 67** — `both = int(ds["both"].sum())`  
Adds the counts classified as both fixed-exclusive and unambiguous focal-edge substitutions.

**Line 68** — `unamb_not_fixed = int(ds["unambiguous_not_fixed"].sum())`  
Adds the counts that are unambiguous focal-edge substitutions but are not fixed-exclusive.

**Line 69** — `placement = int(ds["placement_ambiguous"].sum())`  
Adds the placement-ambiguous counts.

**Line 70** — `outside = int((ev["nonexclusivity_mechanism"] == "derived_state_outside").sum())`  
Counts event rows whose non-exclusivity mechanism is `derived_state_outside`.

**Line 71** — `not_fixed = int((ev["nonexclusivity_mechanism"] == "descendant_not_fixed").sum())`  
Counts event rows whose non-exclusivity mechanism is `descendant_not_fixed`.

**Line 73** — `return Summary(`  
Starts construction of the `Summary` object that will be returned to the plotting code.

**Line 74** — `taxa=int(ds["taxa"].sum()),`  
Adds the number of taxa across the five empirical datasets.

**Line 75** — `variable_sites=int(ds["variable_sites"].sum()),`  
Adds the number of variable sites across the five empirical datasets.

**Line 76** — `branches=int(ds["eligible_non_root_adjacent_branches"].sum()),`  
Adds the number of eligible non-root-adjacent branches.

**Line 77** — `informative=informative,`  
Stores the previously calculated total number of informative comparisons.

**Line 78** — `both=both,`  
Stores the number in the fixed-exclusive plus unambiguous intersection.

**Line 79** — `both_pct=100 * both / informative,`  
Calculates that intersection as a percentage of all informative comparisons.

**Line 80** — `unamb_not_fixed=unamb_not_fixed,`  
Stores the number of unambiguous substitutions that were not fixed-exclusive.

**Line 81** — `unamb_not_fixed_pct=100 * unamb_not_fixed / informative,`  
Calculates that discordant category as a percentage of all informative comparisons.

**Line 82** — `placement_ambiguous=placement,`  
Stores the placement-ambiguous count.

**Line 83** — `placement_ambiguous_pct=100 * placement / informative,`  
Calculates the placement-ambiguous percentage.

**Line 84** — `derived_state_outside=outside,`  
Stores the number of discordant cases where the derived nucleotide also occurred outside the focal clade.

**Line 85** — `derived_state_outside_pct=100 * outside / unamb_not_fixed,`  
Calculates that mechanism as a percentage of the 675 discordant cases, not as a percentage of all 31,644 comparisons.

**Line 86** — `descendant_not_fixed=not_fixed,`  
Stores the number of discordant cases where the descendant clade itself was not fixed at the site.

**Line 87** — `descendant_not_fixed_pct=100 * not_fixed / unamb_not_fixed,`  
Calculates that second mechanism as a percentage of the 675 discordant cases.

**Line 88** — `)`  
Closes the `Summary(...)` call and returns the completed object.

## 4. Reading one site from the Clade A NEXUS alignment

**Line 91** — `def load_alignment_site(root: Path, site_id: str) -> dict[str, str]:`  
Defines a function that reads one requested site from the Clade A NEXUS alignment and returns a dictionary mapping each taxon name to its nucleotide state.

**Line 92** — `path = root / "inputs/empirical/clade_a_alignment.nex"`  
Builds the path to the committed Clade A alignment.

**Line 93** — `taxa: list[str] = []`  
Creates an empty list that will later hold taxon names from the NEXUS `taxlabels` line.

**Line 94** — `in_matrix = False`  
Creates a Boolean flag that records whether the parser has reached the NEXUS matrix block.

**Line 95** — `with path.open() as handle:`  
Opens the alignment file. The `with` statement ensures the file is closed automatically.

**Line 96** — `for raw in handle:`  
Loops through the file one raw line at a time.

**Line 97** — `line = raw.strip()`  
Removes leading/trailing whitespace and the newline character from the current line.

**Line 98** — `if line.startswith("taxlabels"):`  
Checks whether the current line begins the `taxlabels` declaration.

**Line 99** — `taxa = line.split("\t")[1:]`  
Splits that line at tab characters and stores every field after the first one as a taxon name.

**Line 100** — `elif line == "matrix":`  
Checks whether the parser has reached the line that starts the matrix.

**Line 101** — `in_matrix = True`  
Turns the `in_matrix` flag on so subsequent lines are interpreted as site rows.

**Line 102** — `elif in_matrix:`  
Handles lines only after the parser has entered the matrix block.

**Line 103** — `if line == ";":`  
Checks for the semicolon that terminates the NEXUS matrix.

**Line 104** — `break`  
Stops scanning the file if the matrix has ended.

**Line 105** — `if line.startswith(site_id + "\t"):`  
Checks whether the current matrix row starts with the requested site identifier followed by a tab.

**Line 106** — `values = line.split("\t")[1:]`  
Splits the matching row by tabs and removes the first field (the site identifier), leaving only nucleotide values.

**Line 107** — `return dict(zip(taxa, values))`  
Pairs taxon names with nucleotide values using `zip`, converts those pairs to a dictionary, and immediately returns the result.

**Line 108** — `raise ValueError(f"Site not found: {site_id}")`  
Raises a clear error if the requested site is not found instead of silently continuing with missing data.

## 5. Loading the real Clade A worked example

**Line 111** — `def load_clade_a_example(root: Path):`  
Defines the helper that loads every piece of information needed for the real Clade A worked example in Panel B.

**Line 112** — `site_id = "AP009378.1_4301132"`  
Hard-codes the exact site used in the manuscript example.

**Line 113** — `states = load_alignment_site(root, site_id)`  
Calls `load_alignment_site` to obtain the observed nucleotide state for every Clade A taxon at that site.

**Line 114** — `g_taxa = sorted(t for t, state in states.items() if state == "G")`  
Builds a sorted list containing only taxa whose observed state at the site is `G`.

**Line 116** — `tree_text = (root / "inputs/empirical/clade_a_tree.nwk").read_text().strip()`  
Reads the committed Clade A Newick tree into a plain text string and strips surrounding whitespace.

**Line 117** — `tree = Phylo.read(StringIO(tree_text), "newick")`  
Parses that Newick text into a Biopython tree object.

**Line 119** — `focal_four = ["DRR092886", "SRR10420675", "SRR23133748", "SRR18207138"]`  
Defines the four taxa that form the focal four-descendant clade in the worked example.

**Line 120** — `outside_tip = "SRR8871728"`  
Defines the separate outside terminal lineage that also carries `G`.

**Line 121** — `subtree = tree.common_ancestor(g_taxa)  # 14-tip minimal clade containing all five G observations`  
Finds the most recent common ancestor of all five `G` taxa. This gives the minimal displayed subtree containing the focal four-tip group and the outside `G` lineage.

**Line 122** — `focal_clade = tree.common_ancestor(focal_four)`  
Finds the most recent common ancestor of just the four focal taxa. That internal clade is highlighted in blue later.

**Line 123** — `return site_id, states, subtree, focal_four, focal_clade, outside_tip`  
Returns all the pieces needed to draw Panel B.

## 6. Small reusable drawing helpers

**Line 126** — `def panel_letter(ax, letter: str) -> None:`  
Defines a reusable helper for drawing a capital panel letter.

**Line 127** — `# Keep panel letters fully inside the axes so no glyph is clipped at the`  
Comment explaining why the letter is kept inside the plotting area.

**Line 128** — `# top edge of the exported figure.`  
Second line of the same comment.

**Line 129** — `ax.text(-0.04, 0.995, letter, transform=ax.transAxes,`  
Places the panel letter in axes-relative coordinates. The x value is slightly left of the panel body and the y value is just inside the top edge.

**Line 130** — `ha="left", va="top", fontsize=12.0, fontweight="bold", color=INK)`  
Finishes the text call: left aligned, top anchored, 12-point bold, and drawn in the main ink colour.

**Line 133** — `def rounded_box(ax, xy, width, height, edge, text, text_color=INK, face="white",`  
Begins a reusable `rounded_box` helper. The arguments control location, size, border colour, displayed text, text colour, fill colour, font size, and font weight.

**Line 134** — `fontsize=7.0, weight="normal"):`  
Continues the function signature with optional defaults for font size and font weight.

**Line 135** — `x, y = xy`  
Unpacks the `(x, y)` coordinate pair into separate variables.

**Line 136** — `box = FancyBboxPatch(`  
Starts construction of a Matplotlib rounded rectangle patch.

**Line 137** — `(x, y), width, height,`  
Supplies the lower-left coordinate plus the box width and height.

**Line 138** — `boxstyle="round,pad=0.008,rounding_size=0.014",`  
Specifies a rounded box style, a small internal padding value, and the corner-rounding radius.

**Line 139** — `facecolor=face, edgecolor=edge, linewidth=0.85,`  
Sets the box fill colour, border colour, and line width.

**Line 140** — `)`  
Closes the rounded rectangle constructor.

**Line 141** — `ax.add_patch(box)`  
Adds the finished rounded rectangle to the axes.

**Line 142** — `ax.text(x + width / 2, y + height / 2, text,`  
Starts drawing the text inside the box at its geometric centre.

**Line 143** — `ha="center", va="center", fontsize=fontsize,`  
Centres the text horizontally and vertically and applies the requested font size.

**Line 144** — `color=text_color, fontweight=weight, linespacing=1.05)`  
Sets text colour, font weight, and line spacing, completing the box helper.

## 7. Drawing Panel A: empirical non-equivalence

**Line 147** — `def draw_panel_a(ax, s: Summary) -> None:`  
Defines the function that draws all of Panel A.

**Line 148** — `ax.set_xlim(0, 1)`  
Sets Panel A’s horizontal plotting coordinates to run from 0 to 1.

**Line 149** — `ax.set_ylim(0, 1)`  
Sets Panel A’s vertical plotting coordinates to run from 0 to 1.

**Line 150** — `ax.axis("off")`  
Hides the ordinary axes, ticks, and frame because this panel is a designed diagram rather than a conventional graph.

**Line 151** — `panel_letter(ax, "A")`  
Draws the capital `A` panel label.

**Line 153** — `ax.text(0.50, 1.005, "Empirical non-equivalence", transform=ax.transAxes,`  
Starts the Panel A heading at the horizontal centre of the panel.

**Line 154** — `ha="center", va="bottom", fontsize=9.0, fontweight="bold", color=INK)`  
Finishes the heading formatting: centred, bold, 9-point text in the main ink colour.

**Line 155** — `ax.text(0.50, 0.952,`  
Starts the small dataset-summary line below the heading.

**Line 156** — `f"{s.taxa:,} genomes · {s.variable_sites:,} variable sites · {s.branches:,} branches",`  
Uses an f-string to insert the actual totals for genomes, variable sites, and branches, including thousands separators.

**Line 157** — `transform=ax.transAxes, ha="center", va="top", fontsize=6.7, color=GREY)`  
Finishes the summary line formatting in smaller grey text.

**Line 159** — `rounded_box(ax, (0.09, 0.80), 0.82, 0.085, INK,`  
Calls the rounded-box helper to create the large top box in Panel A.

**Line 160** — `f"{s.informative:,} informative\nsite–edge comparisons",`  
Places the total informative-comparison count on two lines inside that box.

**Line 161** — `fontsize=7.2, weight="bold")`  
Uses 7.2-point bold text for the total.

**Line 163** — `# Three stacked categories: no narrow columns and no text collisions.`  
Comment explaining the decision to use vertically stacked categories instead of three narrow boxes.

**Line 164** — `rows = [`  
Starts a Python list named `rows`. Each tuple in this list describes one empirical category.

**Line 165** — `(0.635, BLUE, f"{s.both:,} ({s.both_pct:.2f}%)",`  
First tuple: vertical position, blue colour, and the count/percentage for comparisons that satisfy both criteria.

**Line 166** — `"Fixed-exclusive + unambiguous\nfocal-edge substitution"),`  
Adds the two-line descriptive label for that blue category.

**Line 167** — `(0.505, ORANGE, f"{s.unamb_not_fixed:,} ({s.unamb_not_fixed_pct:.2f}%)",`  
Second tuple: vertical position, orange colour, and count/percentage for unambiguous but non-exclusive substitutions.

**Line 168** — `"Unambiguous focal-edge substitution,\nnot fixed-exclusive"),`  
Adds the two-line descriptive label for that orange category.

**Line 169** — `(0.375, PURPLE, f"{s.placement_ambiguous:,} ({s.placement_ambiguous_pct:.2f}%)",`  
Third tuple: vertical position, purple colour, and count/percentage for placement ambiguity.

**Line 170** — `"Placement-ambiguous"),`  
Adds the label for the purple category.

**Line 171** — `]`  
Closes the `rows` list.

**Line 172** — `for y, color, count, label in rows:`  
Loops over the three tuples, unpacking each tuple into `y`, `color`, `count`, and `label`.

**Line 173** — `ax.add_patch(Rectangle((0.09, y), 0.018, 0.078, facecolor=color, edgecolor="none"))`  
Draws a narrow vertical colour bar beside the current category.

**Line 174** — `ax.text(0.125, y + 0.053, count, ha="left", va="center",`  
Starts the bold count/percentage label next to that colour bar.

**Line 175** — `fontsize=7.3, fontweight="bold", color=color)`  
Finishes the count label formatting using the category’s colour.

**Line 176** — `ax.text(0.125, y + 0.018, label, ha="left", va="center",`  
Starts the explanatory text underneath the count.

**Line 177** — `fontsize=6.55, color=INK, linespacing=1.04)`  
Finishes the explanatory text using smaller black type and controlled line spacing.

**Line 179** — `ax.text(0.09, 0.300,`  
Starts the blue statement beneath the three categories.

**Line 180** — `"No fixed-exclusive comparison lacked\nan unambiguous focal-edge substitution.",`  
Provides the exact two-line statement that no fixed-exclusive comparison lacked an unambiguous focal-edge substitution.

**Line 181** — `ha="left", va="center", fontsize=6.35, color=BLUE, fontweight="bold", linespacing=1.0)`  
Formats that statement in bold blue text.

**Line 183** — `ax.text(0.09, 0.225, f"Why were {s.unamb_not_fixed:,} unambiguous focal-edge substitutions\nnot fixed-exclusive?",`  
Starts the question introducing the breakdown of the 675 discordant cases.

**Line 184** — `ha="left", va="center", fontsize=6.35, color=INK, fontweight="bold", linespacing=1.0)`  
Finishes its placement and formatting.

**Line 186** — `x0, y0, w, h = 0.09, 0.098, 0.82, 0.078`  
Defines the lower-left position, width, and height of the proportional discordance bar.

**Line 187** — `frac = s.derived_state_outside / s.unamb_not_fixed`  
Calculates the fraction of discordant cases caused by the derived nucleotide also being observed outside the focal clade.

**Line 188** — `ax.add_patch(Rectangle((x0, y0), w * frac, h, facecolor=ORANGE, edgecolor="none"))`  
Draws the large orange portion of the proportional bar using that exact fraction.

**Line 189** — `ax.add_patch(Rectangle((x0 + w * frac, y0), w * (1 - frac), h, facecolor=PALE_ORANGE, edgecolor="none"))`  
Draws the remaining small pale-orange portion.

**Line 190** — `ax.add_patch(FancyBboxPatch((x0, y0), w, h,`  
Starts an outline around the complete proportional bar.

**Line 191** — `boxstyle="round,pad=0,rounding_size=0.01",`  
Uses rounded ends with no internal padding.

**Line 192** — `facecolor="none", edgecolor=ORANGE, linewidth=0.75))`  
Sets the outline to orange with a thin stroke.

**Line 193** — `ax.text(x0 + w * frac / 2, y0 + h / 2,`  
Starts the white text centred inside the large orange segment.

**Line 194** — `f"{s.derived_state_outside:,} ({s.derived_state_outside_pct:.2f}%)\nderived nucleotide also observed\noutside the focal clade",`  
Displays the count, percentage, and the scientifically precise explanation: the derived nucleotide was also observed outside the focal clade.

**Line 195** — `ha="center", va="center", fontsize=5.85, color="white", fontweight="bold", linespacing=0.93)`  
Finishes the orange-segment text formatting with compact line spacing.

**Line 197** — `# Small category is labelled below with a short leader, preserving the true 4.44% width.`  
Comment explaining why the 4.44% category is labelled externally rather than artificially widened.

**Line 198** — `tiny_mid = x0 + w * frac + w * (1 - frac) / 2`  
Calculates the horizontal midpoint of the true 4.44% segment.

**Line 199** — `ax.plot([tiny_mid, tiny_mid], [y0, 0.064], color=INK, lw=0.65)`  
Draws the short vertical part of the leader line down from that small segment.

**Line 200** — `ax.plot([tiny_mid, 0.865], [0.064, 0.064], color=INK, lw=0.65)`  
Draws the horizontal part of the leader line toward the external label.

**Line 201** — `ax.text(0.865, 0.055,`  
Starts the external label for the 30 cases.

**Line 202** — `f"{s.descendant_not_fixed} ({s.descendant_not_fixed_pct:.2f}%)\ndescendant clade not fixed",`  
Displays the count, percentage, and explanation that the descendant clade was not fixed.

**Line 203** — `ha="right", va="top", fontsize=5.75, color=INK, linespacing=0.96)`  
Right-aligns the external label and uses compact type so it stays clear of the panel divider.

## 8. Calculating phylogram x- and y-coordinates

**Line 206** — `def get_depths(clade, current=0.0, out=None):`  
Defines a recursive helper that calculates cumulative branch-length depth for every node in a tree.

**Line 207** — `if out is None:`  
Checks whether this is the first recursive call and no output dictionary has been supplied yet.

**Line 208** — `out = {}`  
Creates the output dictionary on that first call.

**Line 209** — `out[id(clade)] = current`  
Stores the current cumulative depth using the Python object identity of the clade as the dictionary key.

**Line 210** — `for child in clade.clades:`  
Loops through every immediate child of the current clade.

**Line 211** — `get_depths(child, current + (child.branch_length or 0.0), out)`  
Recursively visits each child, adding that child’s branch length to the cumulative depth. Missing/zero branch lengths are treated as zero.

**Line 212** — `return out`  
Returns the completed mapping from tree-node identities to cumulative depths.

**Line 215** — `def get_ycoords(clade, terminals, out=None):`  
Defines a second recursive helper that assigns vertical positions to tree nodes.

**Line 216** — `if out is None:`  
Checks whether an output dictionary has been supplied.

**Line 217** — `out = {}`  
Creates it if this is the first call.

**Line 218** — `if clade.is_terminal():`  
Checks whether the current clade is a terminal tip.

**Line 219** — `out[id(clade)] = terminals.index(clade)`  
For a tip, uses its position in the terminal list as its y-coordinate.

**Line 220** — `else:`  
Handles internal nodes instead.

**Line 221** — `for child in clade.clades:`  
Loops through every child of the internal node.

**Line 222** — `get_ycoords(child, terminals, out)`  
Recursively assigns y-coordinates to those children first.

**Line 223** — `out[id(clade)] = sum(out[id(child)] for child in clade.clades) / len(clade.clades)`  
Places the internal node at the mean y-position of its children, which centres branching points vertically.

**Line 224** — `return out`  
Returns the completed y-coordinate mapping.

## 9. Drawing Panel B: the real pruned phylogram

**Line 227** — `def draw_phylogram(ax, subtree, states, focal_clade, focal_four, outside_tip):`  
Defines the main phylogram-drawing function. It receives the axes, the real pruned subtree, the site-state dictionary, focal-clade information, and the outside terminal taxon.

**Line 228** — `terminals = list(subtree.get_terminals())`  
Gets the terminal tips from the subtree and converts the returned iterator/list-like object into a normal list.

**Line 229** — `depths = get_depths(subtree)`  
Calculates cumulative branch-length depths for all nodes.

**Line 230** — `ycoords = get_ycoords(subtree, terminals)`  
Calculates vertical coordinates for all nodes.

**Line 231** — `n = len(terminals)`  
Stores the number of terminal tips.

**Line 232** — `maxdepth = max(depths[id(t)] for t in terminals)`  
Finds the greatest tip depth; this is the rightmost branch-length coordinate in the displayed phylogram.

**Line 234** — `def yplot(clade):`  
Defines a small local function that converts the stored tip order into a top-to-bottom plotting order.

**Line 235** — `return n - 1 - ycoords[id(clade)]`  
Flips the y-coordinate so the first terminal appears at the top rather than the bottom.

**Line 237** — `# Base phylogram.`  
Comment marking the start of drawing the unhighlighted base phylogram.

**Line 238** — `def recurse(clade):`  
Defines a recursive tree-drawing function.

**Line 239** — `x = depths[id(clade)]`  
Looks up the current node’s x-coordinate from cumulative branch length.

**Line 240** — `if clade.clades:`  
Continues only if the current node has children.

**Line 241** — `ys = [yplot(c) for c in clade.clades]`  
Calculates the y-coordinate of each child.

**Line 242** — `ax.plot([x, x], [min(ys), max(ys)], color=INK, lw=0.72, zorder=1)`  
Draws the vertical connector joining those children at the current node’s x-coordinate.

**Line 243** — `for child in clade.clades:`  
Loops through each child branch.

**Line 244** — `xc = depths[id(child)]`  
Gets the child’s x-coordinate.

**Line 245** — `yc = yplot(child)`  
Gets the child’s y-coordinate.

**Line 246** — `ax.plot([x, xc], [yc, yc], color=INK, lw=0.72, zorder=1)`  
Draws the horizontal branch from the current node to that child.

**Line 247** — `recurse(child)`  
Recursively repeats the same drawing procedure below that child.

**Line 248** — `recurse(subtree)`  
Starts the recursive drawing from the root of the pruned subtree.

**Line 250** — `# Focal branch and focal clade descendants in Figure-1 blue.`  
Comment marking the focal-clade highlighting stage.

**Line 251** — `focal_path = subtree.get_path(focal_clade)`  
Gets the path from the displayed subtree root to the focal clade.

**Line 252** — `focal_parent = subtree if len(focal_path) == 1 else focal_path[-2]`  
Determines the node immediately ancestral to the focal clade; a conditional expression handles the edge case where the focal clade is directly below the displayed root.

**Line 253** — `ax.plot([depths[id(focal_parent)], depths[id(focal_clade)]],`  
Starts drawing the single edge entering the focal clade in blue.

**Line 254** — `[yplot(focal_clade), yplot(focal_clade)], color=BLUE, lw=1.25, zorder=3)`  
Finishes that focal-edge line using a thicker stroke and higher drawing order.

**Line 256** — `def recolor_focal(clade):`  
Defines a recursive helper that recolours all branches inside the focal clade blue.

**Line 257** — `x = depths[id(clade)]`  
Gets the current focal-subtree node’s x-coordinate.

**Line 258** — `if clade.clades:`  
Continues only if that node has children.

**Line 259** — `ys = [yplot(c) for c in clade.clades]`  
Gets all child y-coordinates.

**Line 260** — `ax.plot([x, x], [min(ys), max(ys)], color=BLUE, lw=1.05, zorder=2)`  
Draws the blue vertical connector at the current internal node.

**Line 261** — `for child in clade.clades:`  
Loops through each child within the focal clade.

**Line 262** — `xc = depths[id(child)]`  
Gets the child x-coordinate.

**Line 263** — `yc = yplot(child)`  
Gets the child y-coordinate.

**Line 264** — `ax.plot([x, xc], [yc, yc], color=BLUE, lw=1.05, zorder=2)`  
Draws that child branch in blue.

**Line 265** — `recolor_focal(child)`  
Recursively continues through the rest of the focal clade.

**Line 266** — `recolor_focal(focal_clade)`  
Starts the blue recolouring at the focal clade root.

**Line 268** — `outside_term = next(t for t in terminals if t.name == outside_tip)`  
Finds the terminal object whose name matches the separately occurring outside `G` lineage.

**Line 269** — `outside_path = subtree.get_path(outside_term)`  
Gets the path from the displayed subtree root to that outside terminal.

**Line 270** — `outside_parent = subtree if len(outside_path) == 1 else outside_path[-2]`  
Identifies the immediate parent of that terminal branch.

**Line 271** — `# Only the terminal edge carrying the separate reconstructed event is orange.`  
Comment clarifying that only the actual terminal edge carrying the independent event is highlighted orange.

**Line 272** — `ax.plot([depths[id(outside_parent)], depths[id(outside_term)]],`  
Starts drawing that terminal edge in orange.

**Line 273** — `[yplot(outside_term), yplot(outside_term)], color=ORANGE, lw=1.25, zorder=3)`  
Finishes the orange terminal-edge line with the same emphasis thickness used for the focal edge.

**Line 275** — `# Tip markers, taxon labels, and site-state column.`  
Comment marking the tip markers, accession labels, and nucleotide-state column.

**Line 276** — `# IMPORTANT: label columns use axes-fraction x coordinates with data y coordinates.`  
Comment explaining that horizontal label positions use axes fractions while vertical positions remain tied to tree-tip y-coordinates.

**Line 277** — `# This decouples text placement from phylogram branch-length units and prevents`  
Continues the explanation: separating coordinate systems prevents label placement from depending on branch-length scale.

**Line 278** — `# overlaps when font metrics or rendering backends change.`  
Finishes the explanation: this is specifically to reduce overlap when fonts or rendering change.

**Line 279** — `label_transform = ax.get_yaxis_transform()`  
Creates a blended transform: x is interpreted as a fraction of axes width, while y remains in the tree’s data coordinates.

**Line 280** — `x_name_ax = 0.605`  
Sets the dedicated horizontal column for taxon names.

**Line 281** — `x_state_ax = 0.810`  
Sets the dedicated horizontal column for the `T`/`G` site-state letters.

**Line 282** — `x_bracket_ax = 0.845`  
Sets the dedicated horizontal column for the focal-clade bracket.

**Line 283** — `x_bracket_label_ax = 0.868`  
Sets the dedicated horizontal column for the text label to the right of that bracket.

**Line 285** — `for term in terminals:`  
Loops over every displayed terminal taxon.

**Line 286** — `y = yplot(term)`  
Calculates the terminal’s vertical plotting position.

**Line 287** — `x = depths[id(term)]`  
Looks up the terminal’s real branch-length x-coordinate.

**Line 288** — `state = states[term.name]`  
Looks up the observed nucleotide state for this terminal at the example site.

**Line 289** — `if term.name in focal_four:`  
Checks whether this terminal is one of the four focal descendants.

**Line 290** — `face = edge = text_color = BLUE`  
Makes focal-tip marker fill, outline, and taxon-name text blue.

**Line 291** — `state_color = BLUE`  
Makes the site-state letter blue as well.

**Line 292** — `weight = "bold"`  
Uses bold text for the focal taxa.

**Line 293** — `elif term.name == outside_tip:`  
Checks whether this is the separate outside terminal `G` lineage.

**Line 294** — `face = edge = text_color = ORANGE`  
Makes its marker and taxon-name text orange.

**Line 295** — `state_color = ORANGE`  
Makes its site-state letter orange.

**Line 296** — `weight = "bold"`  
Uses bold text for that outside `G` taxon.

**Line 297** — `else:`  
Handles every other displayed terminal.

**Line 298** — `face, edge, text_color, weight = "white", INK, INK, "normal"`  
Uses an open white circle with black outline and ordinary black taxon text for the remaining tips.

**Line 299** — `state_color = GREY`  
Uses grey for their site-state letters.

**Line 300** — `ax.scatter([x], [y], s=30, facecolor=face, edgecolor=edge, linewidth=0.75, zorder=4)`  
Draws the terminal marker at its real phylogram coordinate.

**Line 301** — `ax.text(x_name_ax, y, term.name, transform=label_transform,`  
Starts drawing the taxon name in the dedicated axes-relative text column while keeping the correct data y-coordinate.

**Line 302** — `ha="left", va="center", fontsize=5.80,`  
Sets left alignment, vertical centring, and a compact 5.8-point font.

**Line 303** — `color=text_color, fontweight=weight, clip_on=False)`  
Applies the chosen colour/weight and allows the label to extend beyond the raw data rectangle if necessary.

**Line 304** — `ax.text(x_state_ax, y, state, transform=label_transform,`  
Starts drawing the nucleotide state in the separate state column.

**Line 305** — `ha="center", va="center", fontsize=6.35,`  
Centres the state letter within its column and vertically on the corresponding tip.

**Line 306** — `color=state_color, fontweight=weight, clip_on=False)`  
Applies the appropriate blue/orange/grey colour and font weight.

**Line 308** — `ax.text(x_state_ax, 0.895, "site state", transform=ax.transAxes,`  
Starts the `site state` column heading.

**Line 309** — `ha="center", va="bottom", fontsize=5.95, color=GREY)`  
Centres that heading above the nucleotide letters in smaller grey type.

**Line 311** — `# Focal-clade bracket, kept in its own column to the right of site states.`  
Comment marking the focal-clade bracket and noting that it has its own column.

**Line 312** — `focal_terms = [t for t in terminals if t.name in focal_four]`  
Collects the four displayed focal terminal objects.

**Line 313** — `top = max(yplot(t) for t in focal_terms)`  
Finds the uppermost y-coordinate among those four tips.

**Line 314** — `bottom = min(yplot(t) for t in focal_terms)`  
Finds the lowermost y-coordinate among those four tips.

**Line 315** — `ax.plot([x_bracket_ax, x_bracket_ax], [bottom, top], transform=label_transform,`  
Starts the vertical blue bracket line in the bracket’s dedicated axes-relative x column.

**Line 316** — `color=BLUE, lw=0.75, clip_on=False)`  
Finishes the vertical bracket styling.

**Line 317** — `ax.plot([x_bracket_ax - 0.018, x_bracket_ax], [top, top], transform=label_transform,`  
Draws the short top horizontal tick of the bracket.

**Line 318** — `color=BLUE, lw=0.75, clip_on=False)`  
Finishes the top tick styling.

**Line 319** — `ax.plot([x_bracket_ax - 0.018, x_bracket_ax], [bottom, bottom], transform=label_transform,`  
Draws the short bottom horizontal tick of the bracket.

**Line 320** — `color=BLUE, lw=0.75, clip_on=False)`  
Finishes the bottom tick styling.

**Line 321** — `ax.text(x_bracket_label_ax, (top + bottom) / 2, "focal clade\n(4 descendants)",`  
Starts the two-line `focal clade (4 descendants)` label in its own column to the right of the bracket.

**Line 322** — `transform=label_transform, ha="left", va="center", fontsize=5.00,`  
Uses the blended coordinate transform, left alignment, vertical centring, and compact 5-point type.

**Line 323** — `color=BLUE, fontweight="bold", linespacing=1.0, clip_on=False)`  
Applies blue bold styling and permits the label to extend outside the raw data rectangle.

**Line 325** — `# Compact substitution annotations.`  
Comment marking the substitution-arrow annotations.

**Line 326** — `fx = (depths[id(focal_parent)] + depths[id(focal_clade)]) / 2`  
Calculates the midpoint x-coordinate of the focal edge.

**Line 327** — `fy = yplot(focal_clade)`  
Gets the y-coordinate of the focal-clade root.

**Line 328** — `ax.annotate("focal T→G", xy=(fx, fy), xytext=(maxdepth * 0.28, n + 0.42),`  
Starts an annotation reading `focal T→G`, pointing at the focal edge.

**Line 329** — `ha="center", va="bottom", fontsize=6.6, color=BLUE, fontweight="bold",`  
Positions the text above the tree in blue bold type.

**Line 330** — `arrowprops=dict(arrowstyle="-|>", color=BLUE, lw=0.7, shrinkA=2, shrinkB=2))`  
Defines the blue arrow shape, line width, and small gaps at the text/target ends.

**Line 332** — `ox = (depths[id(outside_parent)] + depths[id(outside_term)]) / 2`  
Calculates the midpoint x-coordinate of the separate outside terminal edge.

**Line 333** — `oy = yplot(outside_term)`  
Gets the y-coordinate of the outside terminal.

**Line 334** — `ax.annotate("terminal T→G", xy=(ox, oy), xytext=(maxdepth * 0.80, n + 1.12),`  
Starts an annotation reading `terminal T→G`, pointing at that orange terminal edge.

**Line 335** — `ha="left", va="bottom", fontsize=6.6, color=ORANGE, fontweight="bold",`  
Positions the annotation in orange bold type.

**Line 336** — `arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=0.7, shrinkA=2, shrinkB=2))`  
Defines the orange arrow appearance.

**Line 338** — `# Scale and compact legend on separate baselines.`  
Comment marking the phylogram scale bar and bottom legend.

**Line 339** — `scale = 0.01`  
Defines the scale-bar length as 0.01 substitutions per site in the tree’s branch-length units.

**Line 340** — `sx0, sy0 = 0.0, -0.55`  
Sets the scale bar’s starting x-coordinate and vertical position.

**Line 341** — `ax.plot([sx0, sx0 + scale], [sy0, sy0], color=INK, lw=0.7)`  
Draws the horizontal scale-bar segment.

**Line 342** — `ax.plot([sx0, sx0], [sy0 - 0.08, sy0 + 0.08], color=INK, lw=0.7)`  
Draws the left scale-bar end tick.

**Line 343** — `ax.plot([sx0 + scale, sx0 + scale], [sy0 - 0.08, sy0 + 0.08], color=INK, lw=0.7)`  
Draws the right scale-bar end tick.

**Line 344** — `ax.text(sx0 + scale / 2, sy0 - 0.22, "0.01 substitutions/site",`  
Starts the text explaining the scale-bar value.

**Line 345** — `ha="center", va="top", fontsize=5.9, color=GREY)`  
Centres that label below the scale bar in small grey type.

**Line 347** — `# Legend uses axes coordinates so text widths cannot collide as branch-length`  
Comment explaining why the bottom legend uses axes coordinates rather than branch-length coordinates.

**Line 348** — `# scaling changes. Each item has its own fixed horizontal slot.`  
Completes the comment: each legend item receives its own fixed horizontal slot.

**Line 349** — `legend_y = 0.018`  
Sets the shared vertical position of all bottom-legend items as a fraction of the axes height.

**Line 350** — `legend_items = [`  
Starts the list of legend-item definitions.

**Line 351** — `(0.035, "white", INK, "T", INK),`  
Defines the open black/white marker representing ancestral `T`.

**Line 352** — `(0.335, BLUE, BLUE, "focal-clade G", BLUE),`  
Defines the blue marker and label representing `G` in the focal clade.

**Line 353** — `(0.720, ORANGE, ORANGE, "outside G", ORANGE),`  
Defines the orange marker and label representing the outside `G` occurrence.

**Line 354** — `]`  
Closes the legend-item list.

**Line 355** — `for xdot, face, edge, label, color in legend_items:`  
Loops through the legend definitions and unpacks each item’s position, colours, label, and text colour.

**Line 356** — `ax.scatter([xdot], [legend_y], transform=ax.transAxes, s=24,`  
Starts drawing the legend marker at the specified axes-relative position.

**Line 357** — `facecolor=face, edgecolor=edge, linewidth=0.7,`  
Applies its fill, outline, and stroke width.

**Line 358** — `zorder=4, clip_on=False)`  
Keeps it above lower-zorder graphics and permits drawing right up to the edge of the axes.

**Line 359** — `ax.text(xdot + 0.025, legend_y, label, transform=ax.transAxes,`  
Starts the legend text immediately to the right of its marker.

**Line 360** — `ha="left", va="center", fontsize=5.9, color=color, clip_on=False)`  
Finishes the text alignment and colour.

**Line 362** — `ax.set_xlim(-0.001, maxdepth + 0.022)`  
Sets the tree’s x-axis data limits. This controls the branch-length drawing area; text columns are positioned separately with axes fractions.

**Line 363** — `ax.set_ylim(-1.9, n + 1.55)`  
Sets enough vertical room for all tips plus the top annotations and bottom scale/legend.

**Line 364** — `ax.axis("off")`  
Hides conventional axes, ticks, and borders for the phylogram panel.

## 10. Creating the Panel B container

**Line 367** — `def draw_panel_b(ax, root: Path) -> None:`  
Defines the outer Panel B drawing function.

**Line 368** — `ax.axis("off")`  
Hides the ordinary axes for the outer Panel B container.

**Line 369** — `panel_letter(ax, "B")`  
Draws the capital `B` panel label.

**Line 370** — `ax.text(0.50, 1.005, "Clade A recurrent-state example", transform=ax.transAxes,`  
Starts the Panel B heading.

**Line 371** — `ha="center", va="bottom", fontsize=9.0, fontweight="bold", color=INK)`  
Centres and formats the heading.

**Line 372** — `ax.text(0.50, 0.955, "AP009378.1_4301132", transform=ax.transAxes,`  
Starts the site identifier directly below the heading.

**Line 373** — `ha="center", va="top", fontsize=6.8, color=GREY)`  
Formats the site identifier in smaller grey text.

**Line 375** — `_, states, subtree, focal_four, focal_clade, outside_tip = load_clade_a_example(root)`  
Loads the real site states, real pruned subtree, four focal taxa, focal clade object, and outside terminal lineage.

**Line 376** — `tree_ax = ax.inset_axes([0.02, 0.03, 0.96, 0.88])`  
Creates an inset axes inside Panel B. This gives the phylogram its own coordinate system while the outer axes handles the heading and panel label.

**Line 377** — `draw_phylogram(tree_ax, subtree, states, focal_clade, focal_four, outside_tip)`  
Calls `draw_phylogram` to render the actual tree and all its annotations.

## 11. Checksums and RGB TIFF conversion

**Line 380** — `def sha256(path: Path) -> str:`  
Defines a utility function that returns the SHA-256 checksum of any supplied file path.

**Line 381** — `digest = hashlib.sha256()`  
Creates a new empty SHA-256 digest object.

**Line 382** — `with path.open("rb") as handle:`  
Opens the target file in binary mode.

**Line 383** — `for chunk in iter(lambda: handle.read(1024 * 1024), b""):`  
Reads the file in 1-megabyte chunks until an empty byte string signals end-of-file.

**Line 384** — `digest.update(chunk)`  
Feeds each chunk into the running SHA-256 calculation.

**Line 385** — `return digest.hexdigest()`  
Returns the final checksum as a hexadecimal text string.

**Line 388** — `def save_rgb_tiff(src: Path, dst: Path) -> None:`  
Defines a utility that creates an explicit RGB TIFF copy from an existing TIFF.

**Line 389** — `with Image.open(src) as image:`  
Opens the source TIFF with Pillow and guarantees that the file is closed afterwards.

**Line 390** — `if image.mode != "RGB":`  
Checks whether the image is already RGB.

**Line 391** — `image = image.convert("RGB")`  
Converts it to RGB if necessary.

**Line 392** — `image.save(dst, compression="tiff_lzw", dpi=image.info.get("dpi", (1000, 1000)))`  
Writes the destination TIFF using LZW compression and preserves the stored DPI when available.

## 12. Writing the accompanying repository files

**Line 395** — `def write_docs(outdir: Path, checksums: dict[str, str]) -> None:`  
Defines the documentation-writing helper. It receives the figure output directory and the checksums already calculated for the artwork files.

**Line 396** — `readme = f"""# Figure 3 - clade exclusivity and focal-edge substitution were not equivalent in empirical phylogenies`  
Starts a multi-line f-string containing the README content.

**Line 398** — `This directory contains the final Figure 3 artwork and the exact Python/Matplotlib code used to render it.`  
States what the directory contains: the finished artwork and the exact rendering script.

**Line 400** — `## Final figure`  
Adds the README section heading for the final figure.

**Line 402** — `![Figure 3 preview](Figure_3_preview_600dpi.png)`  
Embeds the 600-dpi preview image when the README is displayed by a Markdown renderer.

**Line 404** — `## Data provenance`  
Adds the data-provenance section heading.

**Line 406** — `Panel A is generated directly from:`  
Introduces the source files used to generate Panel A.

**Line 408** — `- &#96;results/06_empirical_cross_classification/dataset_summary.tsv&#96;`  
Lists the dataset-level empirical summary table used by Panel A.

**Line 409** — `- &#96;results/06_empirical_cross_classification/informative_events.tsv&#96;`  
Lists the informative-event table used to calculate the discordance mechanisms.

**Line 411** — `Panel B is generated directly from:`  
Introduces the source files used to generate Panel B.

**Line 413** — `- &#96;inputs/empirical/clade_a_tree.nwk&#96;`  
Lists the real Clade A Newick tree.

**Line 414** — `- &#96;inputs/empirical/clade_a_alignment.nex&#96;`  
Lists the real Clade A NEXUS alignment.

**Line 416** — `The displayed tree is a pruned **phylogram** from the supplied Clade A tree. Horizontal branch lengths are retained from the Newick input. No schematic or invented topology is used.`  
Explicitly documents that the displayed topology is a pruned phylogram from the supplied tree and that horizontal branch lengths are retained.

**Line 418** — `## Figure files`  
Adds the README heading for the figure-file inventory.

**Line 420** — `| File | Purpose | SHA-256 |`  
Starts the Markdown table describing each output file and its checksum.

**Line 421** — `|---|---|---|`  
Adds the Markdown table separator row.

**Line 422** — `| &#96;Figure_3.pdf&#96; | Vector production/submission figure. | &#96;{checksums['Figure_3.pdf']}&#96; |`  
Documents the PDF and inserts its calculated SHA-256 checksum.

**Line 423** — `| &#96;Figure_3_editable.svg&#96; | Editable vector source. | &#96;{checksums['Figure_3_editable.svg']}&#96; |`  
Documents the editable SVG and its checksum.

**Line 424** — `| &#96;Figure_3_preview_600dpi.png&#96; | README/inspection preview. | &#96;{checksums['Figure_3_preview_600dpi.png']}&#96; |`  
Documents the 600-dpi PNG preview and its checksum.

**Line 425** — `| &#96;Figure_3_1000dpi.tiff&#96; | 1000-dpi LZW line-art TIFF. | &#96;{checksums['Figure_3_1000dpi.tiff']}&#96; |`  
Documents the 1000-dpi LZW TIFF and its checksum.

**Line 426** — `| &#96;Figure_3_1000dpi_RGB.tiff&#96; | Explicit RGB 1000-dpi LZW TIFF. | &#96;{checksums['Figure_3_1000dpi_RGB.tiff']}&#96; |`  
Documents the explicit RGB TIFF and its checksum.

**Line 428** — `## Artwork preparation choices`  
Adds the README section describing artwork-preparation choices.

**Line 430** — `- final artwork size: **6.5 × 4.4 in**;`  
Documents the physical artwork size.

**Line 431** — `- figure title and legend are not embedded in the artwork;`  
Documents that the manuscript-level figure title and legend are kept outside the artwork file itself.

**Line 432** — `- capital panel labels A and B;`  
Documents that panel labels use capital letters.

**Line 433** — `- text is approximately 6–8 pt at final print size;`  
Documents the approximate final text-size range.

**Line 434** — `- line weights are approximately 0.5–1.25 pt;`  
Documents the approximate stroke-width range.

**Line 435** — `- vector PDF and editable SVG supplied;`  
Documents the vector PDF and editable SVG outputs.

**Line 436** — `- 1000-dpi LZW TIFF supplied for line-art production;`  
Documents the high-resolution LZW TIFF output.

**Line 437** — `- RGB raster export supplied;`  
Documents the RGB raster output.

**Line 438** — `- Figure 1 color semantics retained: blue, orange, purple, and neutral grayscale.`  
Documents the colour semantics carried across from Figure 1.

**Line 440** — `### Font note`  
Adds the font-note subheading.

**Line 442** — `Arial is requested first in the Matplotlib font stack. Arial is not installed in the automated rendering environment, so the locked render uses **Arimo**, an Arial-compatible metric substitute. The SVG keeps text editable so the font can be substituted later if required.`  
Documents the requested font stack, the actual fallback used in this rendering environment, and the fact that SVG text remains editable.

**Line 443** — `"""`  
Closes the multi-line README string.

**Line 444** — `(outdir / "README.md").write_text(readme)`  
Writes the completed README string to `README.md` in the figure directory.

**Line 446** — `# CODE_WALKTHROUGH.md is maintained as a separate, human-readable`  
Comment explaining that the detailed walkthrough is maintained as a separate document rather than generated by the plotting script.

**Line 447** — `# line-by-line companion to this script. It is deliberately not rewritten`  
Continues that comment and specifies that the walkthrough is line-by-line.

**Line 448** — `# here so a rerender cannot replace the detailed explanatory document.`  
Explains why: re-rendering the figure should not overwrite the detailed explanatory document.

**Line 450** — `(outdir / "DIRECTORY_TREE.txt").write_text("""BRANCHSNV validation repository`  
Starts writing `DIRECTORY_TREE.txt` as a multi-line string.

**Line 451** — `|`  
First line of the directory-tree illustration.

**Line 452** — `&#96;-- manuscript/`  
Shows the `manuscript/` directory beneath the repository root.

**Line 453** — `&#96;-- figure_3/`  
Shows the `figure_3/` directory beneath `manuscript/`.

**Line 454** — `|-- CODE_WALKTHROUGH.md`  
Lists `CODE_WALKTHROUGH.md` as a file in the figure package.

**Line 455** — `|-- DIRECTORY_TREE.txt`  
Lists `DIRECTORY_TREE.txt`.

**Line 456** — `|-- Figure_3.pdf`  
Lists the PDF artwork file.

**Line 457** — `|-- Figure_3_1000dpi.tiff`  
Lists the 1000-dpi TIFF.

**Line 458** — `|-- Figure_3_1000dpi_RGB.tiff`  
Lists the explicit RGB TIFF.

**Line 459** — `|-- Figure_3_editable.svg`  
Lists the editable SVG.

**Line 460** — `|-- Figure_3_preview_600dpi.png`  
Lists the 600-dpi PNG preview.

**Line 461** — `|-- README.md`  
Lists the README.

**Line 462** — `|-- make_figure_3.py`  
Lists the exact Python rendering script.

**Line 463** — `&#96;-- requirements.txt`  
Lists the requirements file as the final item in the directory tree.

**Line 464** — `""")`  
Closes the multi-line directory-tree string and writes the file.

**Line 466** — `(outdir / "requirements.txt").write_text("""matplotlib==3.10.8`  
Starts writing `requirements.txt` as a multi-line string.

**Line 467** — `pandas==2.2.3`  
Pins the pandas version used by the locked environment.

**Line 468** — `Pillow==12.3.0`  
Pins the Pillow version used by the locked environment.

**Line 469** — `biopython==1.86`  
Pins the Biopython version used by the locked environment.

**Line 470** — `""")`  
Closes and writes the requirements string. The first line of this string, on line 466, also pins Matplotlib.

## 13. Building and exporting the complete figure

**Line 473** — `def build(outdir: Path) -> None:`  
Defines the main `build` function that assembles and exports the entire figure package.

**Line 474** — `root = repo_root()`  
Determines the repository root from the script location.

**Line 475** — `s = load_summary(root)`  
Loads and calculates all Panel A summary values.

**Line 477** — `fig = plt.figure(figsize=(FIG_W, FIG_H))`  
Creates the complete Matplotlib figure using the physical width and height defined near the top of the script.

**Line 478** — `grid = fig.add_gridspec(`  
Starts a two-column grid specification inside that figure.

**Line 479** — `1, 2, width_ratios=[0.95, 1.25],`  
Creates one row and two columns; Panel B is allocated slightly more width than Panel A.

**Line 480** — `left=0.055, right=0.985, top=0.955, bottom=0.065, wspace=0.10,`  
Sets the outer margins and the horizontal space between panels.

**Line 481** — `)`  
Closes the grid specification.

**Line 482** — `ax_a = fig.add_subplot(grid[0, 0])`  
Creates the axes occupying the left grid cell for Panel A.

**Line 483** — `ax_b = fig.add_subplot(grid[0, 1])`  
Creates the axes occupying the right grid cell for Panel B.

**Line 484** — `draw_panel_a(ax_a, s)`  
Draws Panel A using the calculated summary object.

**Line 485** — `draw_panel_b(ax_b, root)`  
Draws Panel B using data located relative to the repository root.

**Line 487** — `# restrained separator only; no boxed panel frames`  
Comment explaining that the panels are separated only by a restrained line rather than boxes around each panel.

**Line 488** — `fig.lines.append(Line2D([0.435, 0.435], [0.075, 0.945], transform=fig.transFigure,`  
Starts construction of the vertical separator line in figure-relative coordinates.

**Line 489** — `color=LIGHT_GREY, lw=0.65))`  
Sets that separator to pale grey with a thin line width.

**Line 491** — `pdf = outdir / "Figure_3.pdf"`  
Defines the output path for the vector PDF.

**Line 492** — `svg = outdir / "Figure_3_editable.svg"`  
Defines the output path for the editable SVG.

**Line 493** — `png = outdir / "Figure_3_preview_600dpi.png"`  
Defines the output path for the 600-dpi PNG preview.

**Line 494** — `tiff = outdir / "Figure_3_1000dpi.tiff"`  
Defines the output path for the 1000-dpi TIFF.

**Line 495** — `rgb_tiff = outdir / "Figure_3_1000dpi_RGB.tiff"`  
Defines the output path for the explicit RGB TIFF.

**Line 497** — `fig.savefig(pdf, dpi=600)`  
Saves the figure as a PDF. Because the artwork is mainly Matplotlib vector objects, lines and text remain vector content.

**Line 498** — `fig.savefig(svg, dpi=600)`  
Saves an editable SVG copy.

**Line 499** — `fig.savefig(png, dpi=600)`  
Saves the PNG preview at 600 dpi.

**Line 500** — `fig.savefig(tiff, dpi=1000, pil_kwargs={"compression": "tiff_lzw"})`  
Saves the TIFF at 1000 dpi using LZW compression.

**Line 501** — `plt.close(fig)`  
Closes the Matplotlib figure to release memory and file resources.

**Line 502** — `save_rgb_tiff(tiff, rgb_tiff)`  
Reopens the TIFF through Pillow and writes an explicit RGB TIFF copy.

**Line 504** — `checksums = {p.name: sha256(p) for p in (pdf, svg, png, tiff, rgb_tiff)}`  
Calculates SHA-256 checksums for all five artwork files and stores them in a dictionary keyed by filename.

**Line 505** — `write_docs(outdir, checksums)`  
Writes the README, directory tree, and requirements files using the calculated checksums.

**Line 508** — `if __name__ == "__main__":`  
This standard Python guard is true only when the script is run directly, not when it is imported as a module.

**Line 509** — `build(Path(__file__).resolve().parent)`  
When run directly, calls `build` and tells it to write files beside the script itself.

## What to check if this script is modified later

- Re-run the script and confirm the empirical totals still come from the committed result tables rather than being typed manually into the artwork.
- Confirm the Panel B topology still comes from `clade_a_tree.nwk` and the nucleotide states still come from `clade_a_alignment.nex`.
- Confirm `AP009378.1_4301132` still has the five displayed `G` observations expected by the worked example.
- Inspect the 600-dpi preview for text/line collisions, especially the taxon-name column, the site-state column, the focal-clade bracket, and the bottom legend.
- Confirm the proportional 95.56%/4.44% bar has not been visually widened for the small category.
- Recalculate the SHA-256 shown at the top of this walkthrough if `make_figure_3.py` changes, so readers can tell which exact script version is being documented.
