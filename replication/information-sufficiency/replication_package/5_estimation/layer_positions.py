"""Positional analysis of the network of layers (section 6.4 and Table 5 of the paper).

The network of layers has the 18 TCLF chapters as nodes and a directed edge b -> a when the weight of chapter b is
significant at 5 per cent under MRQAP in the model of chapter a's weight (results/mrqap.csv; the p value is the one
the paper reports, from 100,000 permutations where results/mrqap_precision.csv gives one, otherwise from 10,000).
For a pair of chapters x, y the before set of x is the set of chapters whose weight is significant in the model of x,
and the after set of x the set of chapters in whose models the weight of x is significant; the pair's own two
models are left out, so the before set of x is compared with that of y without y and x. Two sets stand in one of
five relations: equal, the first containing the second, the second containing the first, partial overlap, or
disjoint. A set that is empty once the other chapter is removed is contained in the other set; such pairs are
counted with containment and reported separately. Equality of both the before and the after sets is structural
equivalence (Lorrain and White, 1971).

Positions: the distance between two chapters is the number of ties to and from third chapters that one of them has and
the other lacks, the before and the after sets both counted (Wasserman and Faust, 1994, ch. 9). The chapters are grouped by
hierarchical clustering of this distance, under average and under complete linkage, and the partitions into two to
six positions are reported, with the density of edges between and within the positions of the partition into two.

Writes results/layer_positions.txt and results/layer_pair_relations.csv (one row per pair, with the distance of the pair).
Requires numpy and scipy."""
import csv, itertools, os
import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform

HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, "results")
HS = "41 42 43 50 51 52 53 54 56 57 58 59 60 61 62 63 64 65".split()
FIN = {"42", "57", "61", "62", "63", "64", "65"}           # finished goods
ALPHA = 0.05

MQ = {(r["y_sector"], r["x_sector"]): r for r in csv.DictReader(open(os.path.join(RES, "mrqap.csv"), encoding="utf-8"))}
PR = {(r["y_sector"], r["x_sector"]): r for r in csv.DictReader(open(os.path.join(RES, "mrqap_precision.csv"), encoding="utf-8"))
      if r["test"] == "x"}
p = {k: float(PR[k]["p_100000"]) if k in PR and PR[k]["p_100000"] else float(MQ[k]["p_mrqap"]) for k in MQ}
b = {k: float(MQ[k]["b_x"]) for k in MQ}
edge = {(x, a) for (a, x) in MQ if p[(a, x)] < ALPHA}      # (b, a): b explains a
assert len(edge) == 70 and sum(b[(a, x)] < 0 for (x, a) in edge) == 1
before = {c: {x for (x, a) in edge if a == c} for c in HS}
after = {c: {a for (x, a) in edge if x == c} for c in HS}

n = len(HS); ix = {c: i for i, c in enumerate(HS)}
A = np.zeros((n, n), int)
for (x, a) in edge: A[ix[x], ix[a]] = 1
D = np.zeros((n, n))
for i, j in itertools.combinations(range(n), 2):
    ks = [k for k in range(n) if k not in (i, j)]
    D[i, j] = D[j, i] = sum(abs(A[i, k] - A[j, k]) + abs(A[k, i] - A[k, j]) for k in ks)


def relation(s, t):
    if s == t: return "equal"
    if s <= t: return "second contains first"
    if t <= s: return "first contains second"
    if s & t: return "partial overlap"
    return "disjoint"


rows = []
for x, y in itertools.combinations(HS, 2):
    bx, by, ax, ay = before[x] - {y}, before[y] - {x}, after[x] - {y}, after[y] - {x}
    tie = "both" if (x, y) in edge and (y, x) in edge else f"{x}->{y}" if (x, y) in edge else f"{y}->{x}" if (y, x) in edge else "none"
    rows.append({"x": x, "y": y, "tie": tie, "before": relation(bx, by), "after": relation(ax, ay),
                 "before_empty": int(not bx or not by) if bx != by else 0, "after_empty": int(not ax or not ay) if ax != ay else 0,
                 "before_x_only": " ".join(sorted(bx - by, key=int)), "before_y_only": " ".join(sorted(by - bx, key=int)),
                 "before_common": " ".join(sorted(bx & by, key=int)), "after_x_only": " ".join(sorted(ax - ay, key=int)),
                 "after_y_only": " ".join(sorted(ay - ax, key=int)), "after_common": " ".join(sorted(ax & ay, key=int)),
                 "distance": int(D[ix[x], ix[y]])})
with open(os.path.join(RES, "layer_pair_relations.csv"), "w", newline="", encoding="utf-8") as f:
    wr = csv.DictWriter(f, fieldnames=list(rows[0])); wr.writeheader(); wr.writerows(rows)

out = []
say = lambda s="": out.append(s)
say("Positional analysis of the network of layers: 18 chapters, 70 edges significant at 5 per cent under MRQAP")
say("(p values as reported: 100,000 permutations where computed), one negative (59 -> 62).")
say()
say("Relations between the sets of the 153 pairs of chapters, the pair's own models left out:")
say(f"  {'relation':<24}{'before':>8}{'after':>8}")
REL = ["equal", "contains", "partial overlap", "disjoint"]
cnt = {s: {r_: 0 for r_ in REL} for s in ("before", "after")}
emp = {"before": 0, "after": 0}
for r in rows:
    for s in ("before", "after"):
        rel = r[s]; cnt[s]["contains" if "contains" in rel else rel] += 1; emp[s] += r[f"{s}_empty"]
for r_ in REL:
    say(f"  {('one contains the other' if r_ == 'contains' else r_):<24}{cnt['before'][r_]:>8}{cnt['after'][r_]:>8}")
say(f"  {'pairs':<24}{sum(cnt['before'].values()):>8}{sum(cnt['after'].values()):>8}")
say(f"  of the containments, one set empty once the other chapter is removed: before {emp['before']}, after {emp['after']}")
assert sum(cnt["before"].values()) == sum(cnt["after"].values()) == 153
se = [(r["x"], r["y"]) for r in rows if r["before"] == "equal" and r["after"] == "equal"]
say()
say("Structurally equivalent pairs (before and after sets both equal): " + ", ".join(f"{x}-{y}" for x, y in se))
for x, y in se:
    say(f"  {x}-{y}: before {sorted(before[x] - {y}, key=int)}, after {sorted(after[x] - {y}, key=int)}, "
        f"tie between them: {next(r['tie'] for r in rows if (r['x'], r['y']) == (x, y))}")
one = [(r["x"], r["y"], r["before"], r["after"]) for r in rows if (r["before"] == "equal") != (r["after"] == "equal")]
say("Pairs equal on one side only: " + "; ".join(f"{x}-{y} (before {bf}, after {af})" for x, y, bf, af in one))

say()
say("Distance between two chapters: the number of ties to and from third chapters that one of them has and the other lacks.")
say("Smallest distances: " + ", ".join(f"{HS[i]}-{HS[j]} {int(D[i, j])}" for d_, i, j in
                                         sorted((D[i, j], i, j) for i, j in itertools.combinations(range(n), 2))[:6]))
part2 = {}
for method in ("average", "complete"):
    Z = linkage(squareform(D), method=method)
    say()
    say(f"Hierarchical clustering, {method} linkage:")
    for k in range(2, 7):
        lab = fcluster(Z, k, criterion="maxclust"); g = {}
        for c, l in zip(HS, lab): g.setdefault(l, []).append(c)
        groups = sorted(g.values(), key=lambda v: int(v[0]))
        label = f"{k} positions" if len(groups) == k else f"{k} positions requested, {len(groups)} obtained"
        say(f"  {label}: " + "; ".join("{" + ", ".join(v) + "}" for v in groups))
        if k == 2: part2[method] = {frozenset(v) for v in groups}
stage = {frozenset(FIN), frozenset(set(HS) - FIN)}
same = all(v == stage for v in part2.values())
say()
say(f"The partition into two positions equals the stage classification of Table 4 (finished goods / raw materials, "
    f"yarns and fabrics) under both linkages: {same}")
assert same
say("Density of edges from the row position to the column position, partition into two (own pairs excluded):")
grp = [sorted(FIN, key=int), sorted(set(HS) - FIN, key=int)]
for g in grp:
    say("  " + "{" + ", ".join(g) + "}: " + "  ".join(f"{np.mean([A[ix[u], ix[v]] for u in g for v in h if u != v]):.2f}" for h in grp))
open(os.path.join(RES, "layer_positions.txt"), "w", encoding="utf-8").write("\n".join(out) + "\n")
print("\n".join(out))
