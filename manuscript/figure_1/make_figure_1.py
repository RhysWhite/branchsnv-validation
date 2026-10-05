#!/usr/bin/env python3
from pathlib import Path
import hashlib
from datetime import datetime, timezone
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, Polygon
from matplotlib import font_manager
from PIL import Image

HERE = Path(__file__).resolve().parent

# Nature-style production dimensions: 180 mm wide, double-column figure.
MM = 1 / 25.4
FIG_W_MM = 180.0
FIG_H_MM = 135.0

# Pin the font so the same generator does not silently change typography
# according to whichever system fonts happen to be installed.
# DejaVu Sans is distributed with Matplotlib and is therefore available
# in the declared rendering environment.
FONT = "DejaVu Sans"

mpl.rcParams.update({
    "font.family": FONT,
    "font.size": 7.2,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "svg.fonttype": "none",
    "svg.hashsalt": "branchsnv-figure1-nature-methods-v1",
    "axes.linewidth": 0.7,
    "lines.solid_capstyle": "round",
    "lines.solid_joinstyle": "round",
})

# Restrained semantic palette.
INK = "#1F2328"
MUTED = "#687078"
RULE = "#C9CDD2"
LIGHT = "#EEF3F7"
LIGHT_BLUE = "#F2F7FC"
LIGHT_ORANGE = "#FFF5EC"
BLUE = "#1565C0"
RED = "#D71920"
ORANGE = "#F05A00"
PURPLE = "#7B2CBF"
WHITE = "#FFFFFF"

PANEL_FS = 8.0
TITLE_FS = 9.7
SUBHEAD_FS = 7.4
BODY_FS = 7.0
SMALL_FS = 6.2
BIG_FS = 16.0

def T(ax, x, y, s, **kwargs):
    base = dict(transform=ax.transAxes, color=INK, ha="left", va="center")
    base.update(kwargs)
    return ax.text(x, y, s, **base)

def HLINE(ax, y):
    ax.plot([0.015, 0.985], [y, y], transform=ax.transAxes, color=RULE, lw=0.75, clip_on=False)

def panel_label(ax, letter, title, y):
    T(ax, 0.016, y, letter, fontsize=PANEL_FS, fontweight="bold", va="top")
    T(ax, 0.064, y, title, fontsize=TITLE_FS, fontweight="bold", va="top")

def rounded_box(ax, x, y, w, h, fc, ec="none", radius=0.012):
    p = FancyBboxPatch((x, y), w, h, transform=ax.transAxes,
                       boxstyle=f"round,pad=0.004,rounding_size={radius}",
                       facecolor=fc, edgecolor=ec, linewidth=0.6)
    ax.add_patch(p)
    return p

def draw_tag_icon(ax, x, y, s=0.018):
    pts = [(x-s, y), (x-0.2*s, y+s), (x+s, y+s), (x+s, y-0.2*s),
           (x-0.2*s, y-s)]
    ax.add_patch(Polygon(pts, closed=True, fill=False, ec=INK, lw=0.75, transform=ax.transAxes))
    ax.add_patch(Circle((x+0.55*s, y+0.55*s), 0.16*s, transform=ax.transAxes,
                        fill=False, ec=INK, lw=0.7))

def draw_stack_icon(ax, x, y, s=0.016):
    for dy in (0.010, 0.000, -0.010):
        pts = [(x-s, y+dy), (x, y+dy+s*0.7), (x+s, y+dy), (x, y+dy-s*0.7)]
        ax.add_patch(Polygon(pts, closed=True, fill=False, ec=INK, lw=0.72, transform=ax.transAxes))

def draw_doc_icon(ax, x, y, w=0.022, h=0.034):
    rounded_box(ax, x-w/2, y-h/2, w, h, WHITE, INK, 0.003)
    ax.plot([x+w*0.18, x+w*0.34], [y+h*0.50, y+h*0.28], transform=ax.transAxes, color=INK, lw=0.7)
    ax.plot([x-w*0.28, x+w*0.20], [y+0.005, y+0.005], transform=ax.transAxes, color=INK, lw=0.6)
    ax.plot([x-w*0.28, x+w*0.12], [y-0.003, y-0.003], transform=ax.transAxes, color=INK, lw=0.6)
    ax.plot([x-w*0.28, x+w*0.05], [y-0.011, y-0.011], transform=ax.transAxes, color=INK, lw=0.6)

def draw_tree_icon(ax, x, y, descendants=False):
    lw = 0.72
    if descendants:
        ax.plot([x-0.020, x-0.008], [y, y], transform=ax.transAxes, color=INK, lw=lw)
        ax.plot([x-0.008, x-0.008], [y-0.014, y+0.014], transform=ax.transAxes, color=INK, lw=lw)
        for yy in (y-0.014, y, y+0.014):
            ax.plot([x-0.008, x+0.012], [yy, yy], transform=ax.transAxes, color=INK, lw=lw)
            ax.add_patch(Circle((x+0.014, yy), 0.004, transform=ax.transAxes, fill=False, ec=INK, lw=0.7))
    else:
        ax.add_patch(Circle((x-0.020, y-0.015), 0.0045, transform=ax.transAxes, fc=INK, ec=INK))
        ax.plot([x-0.016, x-0.016], [y-0.015, y+0.015], transform=ax.transAxes, color=INK, lw=lw)
        ax.plot([x-0.016, x+0.006], [y+0.006, y+0.006], transform=ax.transAxes, color=INK, lw=lw)
        ax.plot([x+0.006, x+0.006], [y-0.006, y+0.016], transform=ax.transAxes, color=INK, lw=lw)
        for yy in (y-0.006, y+0.016):
            ax.plot([x+0.006, x+0.022], [yy, yy], transform=ax.transAxes, color=INK, lw=lw)
            ax.add_patch(Circle((x+0.024, yy), 0.004, transform=ax.transAxes, fill=False, ec=INK, lw=0.7))

def draw_panel_a(ax):
    panel_label(ax, "a", "One branch, one site", 0.982)

    # Tree geometry
    x0 = 0.165
    x1 = 0.285
    x2 = 0.420
    xt = 0.535
    ys = [0.930, 0.898, 0.866, 0.800, 0.768, 0.736, 0.665, 0.633, 0.601]
    y_focal = ys[1]
    y_mid = ys[4]
    y_bot = ys[7]
    y_upper_split = (y_focal + y_mid) / 2
    y_root = (y_upper_split + y_bot) / 2

    lw = 0.90
    # Root / main tree
    ax.plot([x0, x0], [y_bot, y_upper_split], transform=ax.transAxes, color=INK, lw=lw)
    ax.plot([x0, x1], [y_upper_split, y_upper_split], transform=ax.transAxes, color=INK, lw=lw)
    ax.plot([x0, x2-0.115], [y_bot, y_bot], transform=ax.transAxes, color=INK, lw=lw)

    # Upper split
    ax.plot([x1, x1], [y_mid, y_focal], transform=ax.transAxes, color=INK, lw=lw)

    # focal edge
    ax.plot([x1, x2], [y_focal, y_focal], transform=ax.transAxes, color=RED, lw=1.65)
    T(ax, (x1+x2)/2, y_focal+0.028, "focal edge", fontsize=SMALL_FS, fontweight="bold",
      color=RED, ha="center")

    # Focal clade
    ax.plot([x2, x2], [ys[2], ys[0]], transform=ax.transAxes, color=INK, lw=lw)
    for y in ys[:3]:
        ax.plot([x2, xt], [y, y], transform=ax.transAxes, color=INK, lw=lw)

    # Middle clade
    ax.plot([x1, x2], [y_mid, y_mid], transform=ax.transAxes, color=INK, lw=lw)
    ax.plot([x2, x2], [ys[5], ys[3]], transform=ax.transAxes, color=INK, lw=lw)
    for y in ys[3:6]:
        ax.plot([x2, xt], [y, y], transform=ax.transAxes, color=INK, lw=lw)

    # Bottom clade
    xb = x2 - 0.115
    ax.plot([xb, xb], [ys[8], ys[6]], transform=ax.transAxes, color=INK, lw=lw)
    for y in ys[6:9]:
        ax.plot([xb, xt], [y, y], transform=ax.transAxes, color=INK, lw=lw)

    # tips
    for y in ys:
        ax.add_patch(Circle((xt, y), 0.0055, transform=ax.transAxes,
                            fc=WHITE, ec=INK, lw=0.75))

    # root
    ax.add_patch(Circle((x0, y_root), 0.006, transform=ax.transAxes, fc=INK, ec=INK))
    T(ax, x0-0.014, y_root-0.005, "root", fontsize=SMALL_FS, color=MUTED, ha="right")

    # focal descendants bracket
    bx = 0.562
    ax.plot([bx, bx], [ys[2]-0.008, ys[0]+0.008], transform=ax.transAxes, color=BLUE, lw=0.9)
    ax.plot([bx-0.010, bx], [ys[0]+0.008, ys[0]+0.008], transform=ax.transAxes, color=BLUE, lw=0.9)
    ax.plot([bx-0.010, bx], [ys[2]-0.008, ys[2]-0.008], transform=ax.transAxes, color=BLUE, lw=0.9)
    T(ax, bx+0.013, y_focal, "focal\ndescendants", fontsize=SMALL_FS, fontweight="bold",
      color=BLUE, ha="left", linespacing=0.95)

    # site-state column
    ax.plot([0.665, 0.665], [0.585, 0.947], transform=ax.transAxes, color=RULE, lw=0.7)
    T(ax, 0.720, 0.952, "one site", fontsize=SUBHEAD_FS, fontweight="bold", ha="center")

    states = ["G","G","G","A","A","A","A","A","G"]
    for i, (y, base) in enumerate(zip(ys, states)):
        color = BLUE if i < 3 else (RED if i == 8 else INK)
        T(ax, 0.720, y, base, fontsize=BODY_FS, fontweight="bold", color=color, ha="center")

    T(ax, 0.800, 0.875, "Focal clade:  G G G", fontsize=BODY_FS, fontweight="bold", color=BLUE)
    T(ax, 0.800, 0.815, "Outside includes G", fontsize=BODY_FS, fontweight="bold", color=RED)

def draw_panel_b(ax):
    panel_label(ax, "b", "Two questions, different answers", 0.552)

    # left / right anchors
    lx, rx = 0.065, 0.640
    cx = 0.505

    T(ax, lx, 0.505, "OBSERVED", fontsize=SUBHEAD_FS, fontweight="bold", color=BLUE)
    T(ax, lx, 0.474, "Clade-exclusive?", fontsize=BODY_FS, fontweight="bold")

    # Left observation card
    rounded_box(ax, lx, 0.354, 0.345, 0.095, LIGHT_BLUE)
    T(ax, lx+0.018, 0.415, "focal", fontsize=SMALL_FS, color=MUTED)
    for x in (lx+0.098, lx+0.137, lx+0.176):
        T(ax, x, 0.415, "G", fontsize=BODY_FS, fontweight="bold", color=BLUE, ha="center")

    T(ax, lx+0.018, 0.375, "outside", fontsize=SMALL_FS, color=MUTED)
    bases = [("A",INK),("A",INK),("A",INK),("A",INK),("A",INK),("G",RED)]
    for i,(b,c) in enumerate(bases):
        T(ax, lx+0.098+i*0.039, 0.375, b, fontsize=BODY_FS, fontweight="bold", color=c, ha="center")

    T(ax, lx, 0.318, "NO", fontsize=BIG_FS, fontweight="bold", color=BLUE)
    T(ax, lx+0.093, 0.322, "not fixed-exclusive", fontsize=BODY_FS, fontweight="bold")
    T(ax, lx+0.093, 0.295, "G occurs outside the clade", fontsize=SMALL_FS, color=MUTED)

    # center separator
    ax.plot([cx, cx], [0.285, 0.495], transform=ax.transAxes, color=RULE, lw=0.7)
    T(ax, cx, 0.392, "≠", fontsize=21, fontweight="bold", ha="center")
    T(ax, cx, 0.337, "kept separate", fontsize=SMALL_FS, color=MUTED, ha="center")

    # right
    T(ax, rx, 0.505, "INFERRED", fontsize=SUBHEAD_FS, fontweight="bold", color=ORANGE)
    T(ax, rx, 0.474, "Substitution on the focal edge?", fontsize=BODY_FS, fontweight="bold")
    rounded_box(ax, rx, 0.354, 0.325, 0.095, LIGHT_ORANGE)

    T(ax, rx+0.162, 0.428, "all optimal reconstructions", fontsize=SMALL_FS, color=MUTED, ha="center")
    px, gx, y = rx+0.082, rx+0.255, 0.382
    T(ax, px, y+0.038, "parent", fontsize=SMALL_FS, color=MUTED, ha="center")
    T(ax, gx, y+0.038, "child", fontsize=SMALL_FS, color=MUTED, ha="center")
    ax.add_patch(Circle((px, y), 0.021, transform=ax.transAxes, fill=False, ec=ORANGE, lw=1.0))
    ax.add_patch(Circle((gx, y), 0.021, transform=ax.transAxes, fill=False, ec=BLUE, lw=1.0))
    T(ax, px, y, "A", fontsize=BODY_FS, fontweight="bold", ha="center")
    T(ax, gx, y, "G", fontsize=BODY_FS, fontweight="bold", color=BLUE, ha="center")
    ax.annotate("", xy=(gx-0.030,y), xytext=(px+0.030,y), xycoords=ax.transAxes,
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=0.9))

    T(ax, rx, 0.318, "YES", fontsize=BIG_FS, fontweight="bold", color=ORANGE)
    T(ax, rx+0.093, 0.322, "unambiguous A→G", fontsize=BODY_FS, fontweight="bold")
    T(ax, rx+0.093, 0.295, "Only optimal focal-edge pair: A→G", fontsize=SMALL_FS, color=MUTED)

def draw_panel_c(ax):
    panel_label(ax, "c", "Retain all optimal focal-edge state pairs", 0.255)

    x0, x1, x2 = 0.065, 0.390, 0.665
    rounded_box(ax, x0, 0.198, x2-x0, 0.036, LIGHT)
    T(ax, x0+0.012, 0.216, "Optimal parent→child pair(s)", fontsize=SMALL_FS, fontweight="bold")
    T(ax, x1+0.012, 0.216, "BRANCHSNV reports", fontsize=SMALL_FS, fontweight="bold")
    ax.plot([x1, x1], [0.120, 0.235], transform=ax.transAxes, color=RULE, lw=0.55)

    rows = [
        ("A→G only", "Unambiguous change", BLUE),
        ("A→G or C→G", "State ambiguity", ORANGE),
        ("A→G or G→G", "Placement ambiguity", PURPLE),
        ("G→G only", "No change", MUTED),
    ]
    ys = [0.183,0.157,0.131,0.105]
    for i,(lhs,rhs,c) in enumerate(rows):
        T(ax, x0+0.012, ys[i], lhs, fontsize=BODY_FS)
        T(ax, x1+0.012, ys[i], rhs, fontsize=BODY_FS, fontweight="bold", color=c)
        if i < 3:
            ax.plot([x0, x2], [ys[i]-0.014, ys[i]-0.014], transform=ax.transAxes,
                    color="#E1E5E8", lw=0.5)

    ax.plot([0.685,0.685], [0.100,0.228], transform=ax.transAxes, color=RULE, lw=0.65)
    T(ax, 0.710, 0.176, "No arbitrary tie-breaking", fontsize=BODY_FS, fontweight="bold")
    T(ax, 0.710, 0.140, "All globally optimal focal-edge\nstate pairs are retained.",
      fontsize=SMALL_FS, color=MUTED, va="center", linespacing=1.1)

    # Safeguards
    HLINE(ax, 0.084)
    T(ax, 0.015, 0.066, "DESIGN SAFEGUARDS", fontsize=SMALL_FS, fontweight="bold", color=MUTED)

    # Five equal-width safeguard modules; text is deliberately compact so
    # nothing approaches the production crop boundary.
    bounds = [0.015, 0.209, 0.403, 0.597, 0.791, 0.985]
    modules = [
        ("Explicit root", "defines direction", "root"),
        ("Exact descendant set", "defines branch", "desc"),
        ("Exact taxon labels", "define correspondence", "tag"),
        ("Complete optimal set", "retains uncertainty", "stack"),
        ("Deterministic provenance", "supports auditability", "doc"),
    ]
    for i,(head,sub,kind) in enumerate(modules):
        left, right = bounds[i], bounds[i+1]
        if i > 0:
            ax.plot([left,left],[0.012,0.065],transform=ax.transAxes,color=RULE,lw=0.55)
        icon_x = left + 0.030
        text_x = left + 0.057
        icon_y = 0.036
        if kind=="root":
            draw_tree_icon(ax, icon_x, icon_y, False)
        elif kind=="desc":
            draw_tree_icon(ax, icon_x, icon_y, True)
        elif kind=="tag":
            draw_tag_icon(ax, icon_x, icon_y)
        elif kind=="stack":
            draw_stack_icon(ax, icon_x, icon_y)
        elif kind=="doc":
            draw_doc_icon(ax, icon_x, icon_y)
        T(ax, text_x, 0.043, head, fontsize=5.75, fontweight="bold")
        T(ax, text_x, 0.023, sub, fontsize=5.45, color=MUTED)

def build():
    fig = plt.figure(figsize=(FIG_W_MM*MM, FIG_H_MM*MM), facecolor=WHITE)
    ax = fig.add_axes([0,0,1,1])
    ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis("off")

    draw_panel_a(ax)
    HLINE(ax, 0.570)
    draw_panel_b(ax)
    HLINE(ax, 0.270)
    draw_panel_c(ax)

    fixed_dt = datetime(2026, 10, 5, 0, 0, 0, tzinfo=timezone.utc)
    fixed_date = "2026-10-05T00:00:00Z"
    creator = "BRANCHSNV Figure 1 reproducible generator"

    fig.savefig(
        HERE/"Figure_1.pdf",
        facecolor=WHITE,
        metadata={
            "Title": "BRANCHSNV Figure 1",
            "Author": "Rhys T. White et al.",
            "Subject": "Analytical design of BRANCHSNV",
            "Creator": creator,
            "CreationDate": fixed_dt,
            "ModDate": fixed_dt,
        },
    )

    fig.savefig(
        HERE/"Figure_1_editable.svg",
        facecolor=WHITE,
        metadata={
            "Title": "BRANCHSNV Figure 1",
            "Creator": creator,
            "Date": fixed_date,
        },
    )

    fig.savefig(
        HERE/"Figure_1_preview_600dpi.png",
        dpi=600,
        facecolor=WHITE,
        metadata={
            "Title": "BRANCHSNV Figure 1",
            "Author": "Rhys T. White et al.",
            "Software": creator,
        },
    )

    fig.savefig(
        HERE/"Figure_1_1000dpi.tiff",
        dpi=1000,
        facecolor=WHITE,
        pil_kwargs={"compression":"tiff_lzw"},
    )

    plt.close(fig)

    # Normalize Matplotlib SVG whitespace so the generated source is
    # byte-stable and passes git diff --check.
    svg_path = HERE/"Figure_1_editable.svg"
    svg_text = svg_path.read_text(encoding="utf-8")
    svg_text = "\n".join(line.rstrip() for line in svg_text.splitlines()) + "\n"
    svg_path.write_text(svg_text, encoding="utf-8")

    with Image.open(HERE/"Figure_1_1000dpi.tiff") as im:
        im.convert("RGB").save(HERE/"Figure_1_1000dpi_RGB.tiff",
                               compression="tiff_lzw", dpi=(1000,1000))

    print(f"Font: {FONT}")
    print(f"Figure size: {FIG_W_MM:.1f} × {FIG_H_MM:.1f} mm")
    for name in ["Figure_1.pdf","Figure_1_editable.svg","Figure_1_preview_600dpi.png",
                 "Figure_1_1000dpi.tiff","Figure_1_1000dpi_RGB.tiff"]:
        p=HERE/name
        print(f"{name}\t{hashlib.sha256(p.read_bytes()).hexdigest()}")

if __name__ == "__main__":
    build()
