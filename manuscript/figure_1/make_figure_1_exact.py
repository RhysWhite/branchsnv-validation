import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.lines import Line2D
import matplotlib as mpl
from pathlib import Path

# Cell Press production dimensions
FIG_W, FIG_H = 6.50, 5.10  # 16.5 × 13.0 cm

mpl.rcParams.update({
    "font.family": "Arimo",  # Arial-compatible preview; SVG/PDF text remains editable
    "font.size": 7.0,
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

INK = "#222222"
GREY = "#666666"
LIGHT = "#D9D9D9"
BLUE = "#1F5AA6"
ORANGE = "#D95F02"
RED = "#B2182B"
PURPLE = "#7B3294"

fig = plt.figure(figsize=(FIG_W, FIG_H), facecolor="white")

# Main layout grid
axA = fig.add_axes([0.055, 0.61, 0.89, 0.34])
axB1 = fig.add_axes([0.075, 0.325, 0.34, 0.235])
axBmid = fig.add_axes([0.455, 0.325, 0.08, 0.235])
axB2 = fig.add_axes([0.575, 0.325, 0.35, 0.235])

# Panel C: dedicated header and body axes
axChead = fig.add_axes([0.075, 0.230, 0.835, 0.045])
axC1 = fig.add_axes([0.075, 0.135, 0.47, 0.095])
axC2 = fig.add_axes([0.60, 0.135, 0.31, 0.095])

axF = fig.add_axes([0.055, 0.025, 0.89, 0.085])

for ax in (axA, axB1, axBmid, axB2, axChead, axC1, axC2, axF):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

# Major section separators
for y in [0.595, 0.305, 0.122]:
    fig.add_artist(Line2D([0.055, 0.945], [y, y], transform=fig.transFigure,
                          color=LIGHT, lw=0.7))

# ======================================================
# Panel A
# ======================================================
axA.text(-0.035, 1.02, "A", fontsize=10.5, fontweight="bold", va="top", color=INK)
axA.text(0.005, 1.015, "One branch, one site", fontsize=8.6, fontweight="bold",
         va="top", color=INK)

xR, xX, xF, xO, xY, xTip = 0.08, 0.22, 0.38, 0.38, 0.25, 0.51
ys = [0.89, 0.80, 0.71, 0.54, 0.45, 0.36, 0.19, 0.10, 0.01]
yF = sum(ys[:3]) / 3
yO = sum(ys[3:6]) / 3
yY = sum(ys[6:]) / 3
yX = (yF + yO) / 2
yR = (yX + yY) / 2

lw_tree = 0.8
axA.plot([xR, xR], [yY, yX], color=INK, lw=lw_tree)
axA.plot([xR, xX], [yX, yX], color=INK, lw=lw_tree)
axA.plot([xR, xY], [yY, yY], color=INK, lw=lw_tree)
axA.plot([xX, xX], [yO, yF], color=INK, lw=lw_tree)
axA.plot([xX, xF], [yO, yO], color=INK, lw=lw_tree)
axA.plot([xX, xF], [yF, yF], color=RED, lw=1.5)

axA.plot([xF, xF], [ys[2], ys[0]], color=INK, lw=lw_tree)
for yy in ys[:3]:
    axA.plot([xF, xTip], [yy, yy], color=INK, lw=lw_tree)

axA.plot([xO, xO], [ys[5], ys[3]], color=INK, lw=lw_tree)
for yy in ys[3:6]:
    axA.plot([xO, xTip], [yy, yy], color=INK, lw=lw_tree)

axA.plot([xY, xY], [ys[8], ys[6]], color=INK, lw=lw_tree)
for yy in ys[6:]:
    axA.plot([xY, xTip], [yy, yy], color=INK, lw=lw_tree)

axA.add_patch(Circle((xR, yR), 0.010, ec=INK, fc=INK, lw=0.7))
axA.text(xR-0.02, yR-0.06, "root", fontsize=6.1, color=GREY, ha="right")

for i, yy in enumerate(ys):
    ec = BLUE if i < 3 else GREY
    axA.add_patch(Circle((xTip, yy), 0.010, ec=ec, fc="white", lw=0.8))

axA.text((xX+xF)/2, yF+0.075, "focal edge", fontsize=6.3, fontweight="bold",
         color=RED, ha="center")

bx = 0.545
axA.plot([bx, bx], [ys[2]-0.022, ys[0]+0.022], color=BLUE, lw=0.8)
axA.plot([bx-0.012, bx], [ys[0]+0.022, ys[0]+0.022], color=BLUE, lw=0.8)
axA.plot([bx-0.012, bx], [ys[2]-0.022, ys[2]-0.022], color=BLUE, lw=0.8)
axA.text(bx+0.02, yF, "focal\ndescendants", fontsize=6.2, fontweight="bold",
         color=BLUE, va="center", linespacing=1.0)

state_x = 0.69
axA.text(state_x, 0.99, "one site", fontsize=6.4, fontweight="bold",
         ha="center", va="top")
states = ["G","G","G","A","A","A","A","A","G"]
for i, (yy, s) in enumerate(zip(ys, states)):
    c = BLUE if i < 3 else (RED if i == 8 else INK)
    axA.text(state_x, yy, s, fontsize=7.0, fontweight="bold", color=c,
             ha="center", va="center")

axA.text(0.80, 0.73, "Focal clade: G G G", fontsize=6.6, fontweight="bold",
         color=BLUE, ha="left")
axA.text(0.80, 0.53, "Outside includes G", fontsize=6.6, fontweight="bold",
         color=RED, ha="left")

# ======================================================
# Panel B
# ======================================================
fig.text(0.055, 0.575, "B", fontsize=10.5, fontweight="bold", color=INK, va="top")
fig.text(0.095, 0.575, "Two questions, different answers",
         fontsize=8.6, fontweight="bold", color=INK, va="top")

axB1.text(0.00, 0.90, "OBSERVED", fontsize=6.3, fontweight="bold",
          color=BLUE, va="top")
axB1.text(0.00, 0.74, "Clade-exclusive?", fontsize=8.2, fontweight="bold",
          color=INK, va="top")
axB1.text(0.00, 0.48, "focal", fontsize=6.0, color=GREY, va="center")
for j in range(3):
    axB1.text(0.16+0.11*j, 0.48, "G", fontsize=7.5, fontweight="bold",
              color=BLUE, ha="center", va="center")
axB1.text(0.00, 0.31, "outside", fontsize=6.0, color=GREY, va="center")
for j, s in enumerate(["A","A","A","A","A","G"]):
    axB1.text(0.16+0.09*j, 0.31, s, fontsize=7.1, fontweight="bold",
              color=(RED if s == "G" else INK), ha="center", va="center")
axB1.text(0.00, 0.06, "NO", fontsize=13.0, fontweight="bold",
          color=BLUE, va="bottom")
axB1.text(0.23, 0.085, "not fixed-exclusive", fontsize=6.9, fontweight="bold",
          color=INK, va="bottom")
axB1.text(0.00, 0.005, "G occurs outside the clade", fontsize=6.0,
          color=GREY, va="bottom")

axBmid.text(0.50, 0.54, "≠", fontsize=28, ha="center", va="center", color=INK)
axBmid.text(0.50, 0.24, "kept separate", fontsize=5.9, ha="center",
            va="center", color=GREY)

axB2.text(0.00, 0.90, "INFERRED", fontsize=6.3, fontweight="bold",
          color=ORANGE, va="top")
axB2.text(0.00, 0.74, "Substitution on the focal edge?", fontsize=8.2,
          fontweight="bold", color=INK, va="top")
axB2.text(0.26, 0.46, "parent", fontsize=5.9, color=GREY, ha="center")
axB2.text(0.74, 0.46, "child", fontsize=5.9, color=GREY, ha="center")
axB2.text(0.50, 0.55, "all global optima", fontsize=5.9, color=GREY, ha="center")
for x, state, edge in [(0.26, "A", ORANGE), (0.74, "G", BLUE)]:
    axB2.add_patch(Circle((x, 0.31), 0.055, ec=edge, fc="white", lw=1.0))
    axB2.text(x, 0.31, state, fontsize=7.2, fontweight="bold",
              ha="center", va="center", color=INK)
axB2.annotate("", xy=(0.66,0.31), xytext=(0.34,0.31),
              arrowprops=dict(arrowstyle="-|>", lw=0.9, color=INK,
                              mutation_scale=8.5))
axB2.text(0.00, 0.06, "YES", fontsize=13.0, fontweight="bold",
          color=ORANGE, va="bottom")
axB2.text(0.23, 0.085, "unambiguous A→G", fontsize=6.9, fontweight="bold",
          color=INK, va="bottom")
axB2.text(0.00, 0.005, r"$P^\ast=\{A\rightarrow G\}$", fontsize=6.2,
          color=GREY, va="bottom")

# ======================================================
# Panel C — corrected table hierarchy
# ======================================================
fig.text(0.055, 0.292, "C", fontsize=10.5, fontweight="bold", color=INK, va="top")
fig.text(0.095, 0.292, "Retain all optimal focal-edge solutions",
         fontsize=8.6, fontweight="bold", color=INK, va="top")

# Column headers — no floating divider above them
axChead.text(0.00, 0.72, "Optimal pair set", fontsize=5.9, color=GREY,
             va="center", ha="left")
axChead.text(0.49, 0.72, "BRANCHSNV reports", fontsize=5.9, color=GREY,
             va="center", ha="left")

# Proper table rule: immediately UNDER the column headers.
axChead.plot([0.00, 0.84], [0.28, 0.28], color=LIGHT, lw=0.6)

# Table rows
rows = [
    (r"$P^\ast=\{A\rightarrow G\}$", "Unambiguous change", BLUE),
    (r"$P^\ast=\{A\rightarrow G,\ C\rightarrow G\}$", "State ambiguity", ORANGE),
    (r"$P^\ast=\{A\rightarrow G,\ G\rightarrow G\}$", "Placement ambiguity", PURPLE),
    (r"$P^\ast=\{G\rightarrow G\}$", "No change", GREY),
]
ysC = [0.87, 0.61, 0.35, 0.09]
for i, (lhs, rhs, c) in enumerate(rows):
    if i > 0:
        axC1.plot([0, 1], [ysC[i]+0.13, ysC[i]+0.13], color="#EEEEEE", lw=0.5)
    axC1.text(0.00, ysC[i], lhs, fontsize=6.3, color=INK, va="center")
    axC1.text(0.58, ysC[i], rhs, fontsize=6.3, fontweight="bold",
              color=c, va="center")

axC2.text(0.00, 0.64, "No arbitrary tie-breaking",
          fontsize=7.2, fontweight="bold", color=INK, va="center")
axC2.text(0.00, 0.32,
          "All globally optimal focal-edge\nstate pairs are retained.",
          fontsize=6.1, color=GREY, va="center", linespacing=1.25)

# ======================================================
# Design safeguards
# ======================================================
axF.text(0.00, 0.96, "DESIGN SAFEGUARDS", fontsize=6.2, fontweight="bold",
         color=GREY, va="top")

safeguards = [
    ("Explicit root", "defines direction"),
    ("Exact descendants", "defines branch"),
    ("Exact taxon labels", "defines correspondence"),
    ("Complete optimal set", "retains uncertainty"),
    ("Deterministic provenance", "supports auditability"),
]
centres = [0.10, 0.30, 0.50, 0.70, 0.90]
for i, (x, (title, subtitle)) in enumerate(zip(centres, safeguards)):
    axF.text(x, 0.49, title, fontsize=6.1, fontweight="bold",
             ha="center", va="center", color=INK)
    axF.text(x, 0.16, subtitle, fontsize=5.9,
             ha="center", va="center", color=GREY)
    if i < 4:
        sep = (centres[i]+centres[i+1])/2
        axF.plot([sep, sep], [0.12, 0.65], color=LIGHT, lw=0.6)

# ---------- Export ----------
outdir = Path("/mnt/data")
pdf = outdir / "Figure_1_CellPress_final.pdf"
svg = outdir / "Figure_1_CellPress_final_editable.svg"
png = outdir / "Figure_1_CellPress_final_preview_600dpi.png"
tif = outdir / "Figure_1_CellPress_final_1000dpi.tiff"

fig.savefig(pdf, bbox_inches="tight", pad_inches=0.02)
fig.savefig(svg, bbox_inches="tight", pad_inches=0.02)
fig.savefig(png, dpi=600, bbox_inches="tight", pad_inches=0.02)
fig.savefig(tif, dpi=1000, bbox_inches="tight", pad_inches=0.02,
            pil_kwargs={"compression":"tiff_lzw"})

plt.show()
print("Final figure exported.")
