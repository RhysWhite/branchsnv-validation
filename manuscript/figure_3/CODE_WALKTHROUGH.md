# Figure 3 code walkthrough

`make_figure_3.py` reads the committed experiment 06 tables and the committed Clade A tree/alignment, then renders both figure panels with Matplotlib.

Panel A uses a vertical summary layout to avoid narrow-box text wrapping at final print size. The 95.56%/4.44% discordance bar is proportional; the small 4.44% category is labelled externally rather than visually enlarged.

Panel B uses the actual 14-tip pruned Clade A phylogram containing the five observed G states at `AP009378.1_4301132`. Horizontal distances are cumulative branch lengths from the supplied Newick tree. The four-descendant focal clade is blue, the independent outside terminal G occurrence is orange, and ancestral T tips remain open black circles.
