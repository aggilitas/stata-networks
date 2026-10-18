"""Figure 2 of the paper: the network of layers.

Nodes are the 18 TCLF chapters, the layers of the multiplex. A directed edge b -> a is drawn when the weight of
chapter b is significant at 5 per cent (MRQAP, results/mrqap.csv) in the model of chapter a's weight. Pairs
significant in both directions are drawn as one line without arrow heads, pairs significant in one direction only
as a thin arrow to the explained chapter. Negative associations are dashed. Nodes are coloured by stage: raw
materials (41, 43, 50-53, the chapters that contain the raw material with its yarns and fabrics), yarns and fabrics
(54, 56, 58-60) and finished goods. The seven finished-goods chapters (42, 57, 61-65) are on a
heptagon on the right, the eleven chapters of raw materials, yarns and fabrics on an arc on the left: these are the
two positions of the network (results/layer_positions.txt). The structurally equivalent pairs, read from
results/layer_pair_relations.csv (written by layer_positions.py, to be run first), are enclosed. The lines are drawn first, then the arrows; each edge is the least curved arc
that clears every other node, does not run along an edge already drawn (a crossing is allowed), and meets its end nodes at an angle
apart from the edges already there (arrows 15 degrees, lines 6). Each label is put at the first position, from
the side away from the centre of its group, where it covers no edge, node or other label. Writes
results/fig_layer_network.png (300 dpi) and results/fig_layer_network.pdf. Requires matplotlib and numpy."""
import csv, math, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, "results")
UP = ["41", "43", "50", "51", "52", "53", "54", "56", "58", "59", "60"]
FIN = ["42", "57", "61", "62", "63", "64", "65"]
NAME = {"41": "raw hides", "42": "leather goods", "43": "furskins", "50": "silk", "51": "wool", "52": "cotton",
        "53": "other veg. fibres", "54": "man-made filaments", "56": "wadding, nonwovens", "57": "carpets",
        "58": "special fabrics", "59": "coated fabrics", "60": "knitted fabrics", "61": "knitted apparel",
        "62": "non-knitted apparel", "63": "made-up textiles", "64": "footwear", "65": "headgear"}
BLUE, ORANGE, INK, GREY, VERM = "#0072B2", "#E69F00", "#222222", "#9A9A9A", "#D55E00"
SKY = "#56B4E9"
RAW = {"41", "43", "50", "51", "52", "53"}                  # chapters that contain the raw material

rows = list(csv.DictReader(open(os.path.join(RES, "mrqap.csv"), encoding="utf-8")))
sig = {(r["y_sector"], r["x_sector"]): float(r["b_x"]) for r in rows if float(r["p_mrqap"]) < 0.05}

# positions: upstream chapters on an arc on the left, the finished goods on a heptagon on the right; labels
# point away from the centre of their group
FIN_ORDER = ["42", "61", "63", "62", "64", "65", "57"]
pos, centre = {}, {}
for n, k in enumerate(UP):
    a = math.radians(105 + 150 * n / (len(UP) - 1)); pos[k] = (-0.35 + 1.15 * math.cos(a), 1.15 * math.sin(a)); centre[k] = (-0.35, 0.0)
for n, k in enumerate(FIN_ORDER):
    a = math.radians(90 - 360 * n / len(FIN_ORDER)); pos[k] = (1.0 + 0.78 * math.cos(a), 0.78 * math.sin(a)); centre[k] = (1.0, 0.0)

TWINS = [(r["x"], r["y"]) for r in csv.DictReader(open(os.path.join(RES, "layer_pair_relations.csv"), encoding="utf-8"))
         if r["before"] == "equal" and r["after"] == "equal"]
assert TWINS == [("61", "63")], TWINS
CLEAR = 0.15                                      # node disc radius (about 0.10) plus a margin, in data units


def arc(p, q, rad):
    """points of the arc3 path p -> q with curvature rad"""
    (x1, y1), (x2, y2) = p, q
    cx, cy = (x1 + x2) / 2 + rad * (y2 - y1), (y1 + y2) / 2 - rad * (x2 - x1)
    return [((1 - t) ** 2 * x1 + 2 * t * (1 - t) * cx + t ** 2 * x2, (1 - t) ** 2 * y1 + 2 * t * (1 - t) * cy + t ** 2 * y2)
            for t in (i / 200 for i in range(201))]


def clearance(p, q, rad, skip):
    """least distance from the arc3 path p -> q with curvature rad to the centre of any node not in skip"""
    return min(math.dist(pt, pos[k]) for k in pos if k not in skip for pt in arc(p, q, rad))


def ends(p, q, rad):
    """directions, in degrees, in which the arc3 path p -> q leaves p and reaches q (from the node outwards)"""
    (x1, y1), (x2, y2) = p, q
    cx, cy = (x1 + x2) / 2 + rad * (y2 - y1), (y1 + y2) / 2 - rad * (x2 - x1)
    return math.degrees(math.atan2(cy - y1, cx - x1)), math.degrees(math.atan2(cy - y2, cx - x2))


gap = lambda u, v: abs((u - v + 180) % 360 - 180)
drawn, at = np.zeros((0, 2)), {k: [] for k in pos}      # points of the edges drawn; directions of the edges at each node


def score(b, a, r, apart):
    """None if the arc passes over a node; else (longest stretch within 0.025 of an edge already drawn, away from
    the end nodes, and the worst angle shortfall at the two nodes)"""
    if clearance(pos[b], pos[a], r, {a, b}) < CLEAR: return None
    pts = np.array(arc(pos[b], pos[a], r))
    away = np.min(np.stack([np.hypot(*(pts - np.array(pos[e])).T) for e in (a, b)]), axis=0) > 0.2
    along = 0.0
    if len(drawn):
        near = np.zeros(len(pts), bool)
        near[away] = np.sqrt(((pts[away, None, :] - drawn[None, :, :]) ** 2).sum(axis=2)).min(axis=1) < 0.025
        step = np.hypot(*np.diff(pts, axis=0).T).mean(); run = 0
        for v in near:
            run = run + 1 if v else 0; along = max(along, run * step)
    db, da = ends(pos[b], pos[a], r)
    short = max([max(0.0, apart - gap(db, u)) for u in at[b]] + [max(0.0, apart - gap(da, u)) for u in at[a]] + [0.0])
    return along, short


def place(b, a, first, apart):
    """the least curved arc from b to a, starting with first, that clears the nodes, runs along no drawn edge
    (no stretch longer than 0.15 within 0.025 of one; a crossing is shorter) and meets both nodes apart from the
    edges there; failing that, the node-clearing arc with the shortest such stretch and then the smallest shortfall"""
    global drawn
    cands = [first, -first] + [s_ * x / 20 for x in range(2, 17) for s_ in (1, -1)]
    scored = [(r, score(b, a, r, apart)) for r in cands]
    scored = [(r, sc) for r, sc in scored if sc is not None]
    good = [r for r, sc in scored if sc[0] <= 0.15 and sc[1] == 0]
    r = good[0] if good else min(scored, key=lambda x: (x[1][0], x[1][1]))[0]
    if not good: print(f"edge {b} -> {a}: no arc meets every condition; curvature {r}, along {dict(scored)[r][0]:.2f}, shortfall {dict(scored)[r][1]:.1f}")
    drawn = np.vstack([drawn, np.array(arc(pos[b], pos[a], r))])
    db, da = ends(pos[b], pos[a], r); at[b].append(db); at[a].append(da)
    return r


fig, ax = plt.subplots(figsize=(7.2, 6.0))
ax.set_aspect("equal"); ax.axis("off")
recip = sorted({tuple(sorted(m)) for m in sig if (m[1], m[0]) in sig})
single = sorted(m for m in sig if (m[1], m[0]) not in sig)
for (a, b) in recip:
    style = "--" if sig[(a, b)] < 0 or sig[(b, a)] < 0 else "-"
    r = place(b, a, 0.0, 6)
    ax.add_patch(FancyArrowPatch(pos[b], pos[a], arrowstyle="-", linestyle=style, color=VERM if style == "--" else INK,
                                 lw=1.4, shrinkA=11, shrinkB=11,
                                 connectionstyle=f"arc3,rad={r}", zorder=2))
for (a, b) in single:
    style = "--" if sig[(a, b)] < 0 else "-"
    r = place(b, a, 0.12, 15)
    ax.add_patch(FancyArrowPatch(pos[b], pos[a], arrowstyle="-|>", mutation_scale=9, linestyle=style,
                                 color=VERM if style == "--" else GREY, lw=0.8, shrinkA=11, shrinkB=11,
                                 connectionstyle=f"arc3,rad={r}", zorder=1))
drawn = [tuple(pt) for pt in drawn]
for u, v in TWINS:                                  # a capsule behind the two nodes of a structurally equivalent pair
    (x1, y1), (x2, y2) = pos[u], pos[v]
    ax.plot([x1, x2], [y1, y2], color="#F2D6A2", lw=26, solid_capstyle="round", zorder=0.5)
for k, (x, y) in pos.items():
    col = ORANGE if k in FIN else SKY if k in RAW else BLUE
    ax.scatter([x], [y], s=380, color=col, edgecolor="white", linewidth=1.5, zorder=3)
    ax.text(x, y, k, ha="center", va="center", fontsize=8, color="white" if col == BLUE else INK, fontweight="bold", zorder=4)
handles = [Line2D([0], [0], marker="o", color="w", markerfacecolor=SKY, markersize=10, label="raw materials"),
           Line2D([0], [0], marker="o", color="w", markerfacecolor=BLUE, markersize=10, label="yarns and fabrics"),
           Line2D([0], [0], marker="o", color="w", markerfacecolor=ORANGE, markersize=10, label="finished goods"),
           Line2D([0], [0], color=INK, lw=1.4, label="significant in each direction"),
           Line2D([0], [0], color="#F2D6A2", lw=9, solid_capstyle="round", label="structurally equivalent pair (61, 63)"),
           Line2D([0], [0], color=GREY, lw=0.8, marker=">", markersize=5, label="one direction only (arrow to the explained chapter)"),
           Line2D([0], [0], color=VERM, lw=1.2, linestyle="--", label="negative")]
ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.01), ncol=3, frameon=False, fontsize=7.5)
ax.set_xlim(-1.95, 2.35); ax.set_ylim(-1.42, 1.3)
fig.tight_layout()
# labels: the first position, turning away from the outward direction and then moving further out, whose box
# covers no visible part of an edge, no node and no label already placed
visible = [pt for pt in drawn if min(math.dist(pt, c) for c in pos.values()) > 0.11]
renderer = fig.canvas.get_renderer(); inv = ax.transData.inverted(); boxes = []
for k, (x, y) in pos.items():
    cx, cy = centre[k]; out = math.atan2(y - cy, x - cx)
    best = None                                   # failing a clean position, the one covering the fewest edge points
    for dist in (0.16, 0.24, 0.32):
        for off in (0, 20, -20, 40, -40, 60, -60, 80, -80, 100, -100, 120, -120, 150, -150, 180):
            ang = out + math.radians(off)
            lx, ly = x + dist * math.cos(ang), y + dist * math.sin(ang)
            ha = "left" if math.cos(ang) > 0.3 else "right" if math.cos(ang) < -0.3 else "center"
            va = "bottom" if math.sin(ang) > 0.7 else "top" if math.sin(ang) < -0.7 else "center"
            t = ax.text(lx, ly, NAME[k], ha=ha, va=va, fontsize=7.5, color=INK, zorder=4,
                        bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.9))
            bb = t.get_window_extent(renderer).transformed(inv)
            x0, y0, x1, y1 = bb.x0 - 0.02, bb.y0 - 0.02, bb.x1 + 0.02, bb.y1 + 0.02
            blocked = (any(math.dist((qx, qy), (max(x0, min(qx, x1)), max(y0, min(qy, y1)))) < 0.1 for qx, qy in pos.values())
                       or any(x0 < b1 and b0 < x1 and y0 < c1 and c0 < y1 for b0, c0, b1, c1 in boxes))
            covered = sum(x0 <= px <= x1 and y0 <= py <= y1 for px, py in visible)
            t.remove()
            if blocked: continue
            if best is None or covered < best[0]: best = (covered, lx, ly, ha, va, (x0, y0, x1, y1))
            if covered == 0: break
        if best and best[0] == 0: break
    assert best, k
    if best[0]: print(f"label of {k}: every position covers some edge; the one chosen covers {best[0]} points")
    ax.text(best[1], best[2], NAME[k], ha=best[3], va=best[4], fontsize=7.5, color=INK, zorder=4,
            bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.9))
    placed = best[5]
    boxes.append(placed)
fig.savefig(os.path.join(RES, "fig_layer_network.png"), dpi=300, bbox_inches="tight")
fig.savefig(os.path.join(RES, "fig_layer_network.pdf"), bbox_inches="tight", metadata={"CreationDate": None})
n2 = len({tuple(sorted(m)) for m in sig if (m[1], m[0]) in sig}); n1 = len([m for m in sig if (m[1], m[0]) not in sig])
print(f"layer network: {len(sig)} significant directed associations, {n2} pairs in both directions, {n1} in one direction only")
