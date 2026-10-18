"""Sensitivity of the second network to corrections for multiple testing (Supplementary Section S8.1).

The 306 flow-weight tests of results/mrqap.csv are taken as one family. The p value of each test is the one the
paper reports, from 100,000 permutations where results/mrqap_precision.csv gives one, otherwise from 10,000.
The network of layers is rebuilt from the tests significant at 5 per cent without a correction, under the
Benjamini-Hochberg and Benjamini-Yekutieli false discovery rate procedures and under the Holm procedure. For each
network the script reports the number of ties, their split between the finished goods and the other chapters,
the structurally equivalent pairs, the distance between chapters 61 and 63, the ties between 61 and 63, and the
partition into two positions by hierarchical clustering under average and complete linkage, as in
layer_positions.py. The regressions and the permutations are not rerun.

Reads results/mrqap.csv and results/mrqap_precision.csv (mrqap.py and mrqap_precision.py, run first, or the
packaged results). Writes results/multiple_testing.txt. Requires numpy and scipy."""
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
keys = sorted(p, key=lambda k: (p[k], k)); m = len(keys)
assert m == 306


def step_up(level):
    """largest i with p_(i) <= level(i); the i smallest p values are rejected"""
    kmax = 0
    for i, k in enumerate(keys, 1):
        if p[k] <= level(i):
            kmax = i
    return set(keys[:kmax])


cm = sum(1 / i for i in range(1, m + 1))
holm = set()
for i, k in enumerate(keys):
    if p[k] <= ALPHA / (m - i):
        holm.add(k)
    else:
        break
RULES = [("no correction", {k for k in keys if p[k] < ALPHA}),
         ("Benjamini-Hochberg", step_up(lambda i: ALPHA * i / m)),
         ("Benjamini-Yekutieli", step_up(lambda i: ALPHA * i / (m * cm))),
         ("Holm", holm)]
out = ["Second network under corrections for multiple testing: the 306 flow-weight tests as one family, level 5 per cent;",
       "p values as reported (100,000 permutations where computed, otherwise 10,000).", ""]
for name, sig in RULES:
    edge = {(x, a) for (a, x) in sig}                       # (b, a): the weight of b is significant in the model of a
    ix = {c: i for i, c in enumerate(HS)}; n = len(HS)
    A = np.zeros((n, n), int)
    for (x, a) in edge:
        A[ix[x], ix[a]] = 1
    D = np.zeros((n, n))
    for i, j in itertools.combinations(range(n), 2):
        ks = [k for k in range(n) if k not in (i, j)]
        D[i, j] = D[j, i] = sum(abs(A[i, k] - A[j, k]) + abs(A[k, i] - A[k, j]) for k in ks)
    before = {c: {x for (x, a) in edge if a == c} for c in HS}
    after = {c: {a for (x, a) in edge if x == c} for c in HS}
    tied = [c for c in HS if before[c] or after[c]]
    se = [f"{x}-{y}" for x, y in itertools.combinations(tied, 2) if before[x] - {y} == before[y] - {x} and after[x] - {y} == after[y] - {x}]
    fin = sum(1 for (x, a) in edge if x in FIN and a in FIN); oth = sum(1 for (x, a) in edge if x not in FIN and a not in FIN)
    t6163 = [s for s, e in (("61->63", ("61", "63")), ("63->61", ("63", "61"))) if e in edge]
    out.append(f"{name}: {len(edge)} ties, {fin} among the finished goods, {oth} among the other chapters, {len(edge) - fin - oth} between the two groups")
    out.append(f"  structurally equivalent pairs (chapters with ties): {', '.join(se) or 'none'}; distance 61-63 {int(D[ix['61'], ix['63']])}; "
               f"ties between 61 and 63: {', '.join(t6163) or 'none'}")
    out.append(f"  chapters without ties: {' '.join(c for c in HS if c not in tied) or 'none'}")
    for method in ("average", "complete"):
        lab = fcluster(linkage(squareform(D), method=method), 2, criterion="maxclust"); g = {}
        for c, l in zip(HS, lab):
            g.setdefault(l, []).append(c)
        groups = sorted(g.values(), key=lambda v: int(v[0]))
        same = {frozenset(v) for v in groups} == {frozenset(FIN), frozenset(set(HS) - FIN)}
        out.append(f"  two positions, {method} linkage: " + "; ".join("{" + ", ".join(v) + "}" for v in groups)
                   + f" (equal to finished goods / other chapters: {'yes' if same else 'no'})")
    out.append("")
open(os.path.join(RES, "multiple_testing.txt"), "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
