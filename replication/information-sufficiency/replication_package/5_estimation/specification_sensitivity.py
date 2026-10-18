"""Sensitivity of the 306 flow-weight tests to the specification (Supplementary Section S8.1).

The models and the MRQAP test of mrqap.py (the same data, the same 10,000 node permutations from seed 20260927) are
refitted under four changes of the specification: year effects absorbed together with the corridor effect, all three
attribute edge values in levels, all three as yearly changes, and the level/change choice of the unit-root step
reversed. For each specification the script reports the number of flow-weight coefficients significant at 5 per
cent under MRQAP, the ties lost and gained against the published specification, the split of the ties between the
finished goods and the other chapters, the structurally equivalent pairs and the partition into two positions, as in
layer_positions.py. Only the flow-weight tests are rerun.

Reads ../3_inputs/networks/ and results/unit_roots.csv, and checks that the published specification reproduces the
MRQAP p values of results/mrqap.csv. Writes results/specification_sensitivity.txt. Requires numpy and scipy.
About ten minutes."""
import csv, itertools, math, os
import numpy as np
from scipy import stats
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
NET = os.path.join(ROOT, "3_inputs", "networks"); RES = os.path.join(HERE, "results")
R = "BE BG DE DK EE ES FR GR HR HU IT LT LV PL PT RO SE SI".split()
HS = "41 42 43 50 51 52 53 54 56 57 58 59 60 61 62 63 64 65".split()
FIN = {"42", "57", "61", "62", "63", "64", "65"}
Y = list(range(2016, 2026)); T = len(Y)
NPERM, SEED, ALPHA = 10000, 20260927, 0.05
E = [(i, j) for i in R for j in R if i != j]; G = len(E); N = G * T
eidx = {e: n for n, e in enumerate(E)}


def weights(k):
    tot, v = {}, {}
    for r in csv.DictReader(open(os.path.join(NET, f"export_{k}.csv"), encoding="utf-8")):
        t, i, j, a = int(r["year"]), r["source"], r["target"], float(r["source_value"])
        tot[(i, t)] = tot.get((i, t), 0.0) + a
        if j != "REST":
            v[(i, j, t)] = a
    return np.array([[v[(i, j, t)] / tot[(i, t)] if tot[(i, t)] > 0 else 0.0 for t in Y] for i, j in E])


ATTR = {}
for name in ("prod", "fin", "elec"):
    a = {}
    for r in csv.DictReader(open(os.path.join(NET, f"attr_{name}.csv"), encoding="utf-8")):
        a[(r["source"], r["target"], int(r["year"]))] = math.log(float(r["target_value"]) / float(r["source_value"]))
    ATTR[name] = a


def attribute(name, change):
    a = ATTR[name]
    if change:
        return np.array([[a[(i, j, t)] - a[(i, j, t - 1)] for t in Y] for i, j in E])
    return np.array([[a[(i, j, t)] for t in Y] for i, j in E])


def within(M, year):
    M = M - M.mean(axis=1, keepdims=True)
    if year:
        M = M - M.mean(axis=0, keepdims=True)
    return M.ravel()


W = {k: weights(k) for k in HS}
ur = {r["variable"]: float(r["p_fisher_pp"]) for r in csv.DictReader(open(os.path.join(RES, "unit_roots.csv"), encoding="utf-8"))}
BASE = {a: ur[f"attr_{a}"] >= ALPHA for a in ("prod", "fin", "elec")}   # True = yearly change
rng = np.random.default_rng(SEED); pos = {c: n for n, c in enumerate(R)}
perm = [rng.permutation(len(R)) for _ in range(NPERM)]
pidx = [np.array([eidx[(R[p[pos[i]]], R[p[pos[j]]])] for i, j in E]) for p in perm]


def run(spec, year):
    C = np.column_stack([within(attribute(a, spec[a]), year) for a in ("prod", "fin", "elec")])
    Wi = {k: within(W[k], year) for k in HS}
    K = 1 + C.shape[1] + ((T - 1) if year else 0)
    CF = (N - 1) / (N - K - 1) * G / (G - 1)

    def fit(xv, Ymat):
        X = np.column_stack([xv, C]); XtXi = np.linalg.inv(X.T @ X)
        B = XtXi @ (X.T @ Ymat); U = Ymat - X @ B; z = X @ XtXi[0]
        S = (z[:, None] * U).reshape(G, T, -1).sum(axis=1)
        se = np.sqrt(CF * (S ** 2).sum(axis=0))
        return B[0], se, B[0] / se

    obs = {}
    for b in HS:
        ys = [a for a in HS if a != b]
        beta, se, t = fit(Wi[b], np.column_stack([Wi[a] for a in ys]))
        for n, a in enumerate(ys):
            obs[(a, b)] = (float(beta[n]), float(t[n]), float(2 * stats.t.sf(abs(t[n]), G - 1)))
    Pc = C @ np.linalg.solve(C.T @ C, C.T)
    count = {m: 0 for m in obs}
    for b in HS:
        ys = [a for a in HS if a != b]; Ymat = np.column_stack([Wi[a] for a in ys])
        ex = (Wi[b] - Pc @ Wi[b]).reshape(G, T)
        tobs = np.abs(np.array([obs[(a, b)][1] for a in ys]))
        for q in pidx:
            _, _, tp = fit(ex[q].ravel(), Ymat)
            for n in np.nonzero(np.abs(tp) >= tobs)[0]:
                count[(ys[n], b)] += 1
    pq = {m: (1 + count[m]) / (1 + NPERM) for m in obs}
    return obs, pq


def network(sig):
    edge = {(x, a) for (a, x) in sig}
    ix = {c: i for i, c in enumerate(HS)}; n = len(HS)
    A = np.zeros((n, n), int)
    for (x, a) in edge:
        A[ix[x], ix[a]] = 1
    D = np.zeros((n, n))
    for i, j in itertools.combinations(range(n), 2):
        ks = [k for k in range(n) if k not in (i, j)]
        D[i, j] = D[j, i] = sum(abs(A[i, k] - A[j, k]) + abs(A[k, i] - A[k, j]) for k in ks)
    before = {c: {x for (x, a) in edge if a == c} for c in HS}; after = {c: {a for (x, a) in edge if x == c} for c in HS}
    se = [f"{x}-{y}" for x, y in itertools.combinations(HS, 2) if before[x] - {y} == before[y] - {x} and after[x] - {y} == after[y] - {x}
          and (before[x] or after[x])]
    parts = {}
    for method in ("average", "complete"):
        lab = fcluster(linkage(squareform(D), method=method), 2, criterion="maxclust"); g = {}
        for c, l in zip(HS, lab):
            g.setdefault(int(l), []).append(c)
        parts[method] = sorted(g.values(), key=lambda v: int(v[0]))
    fin = sum(1 for (x, a) in edge if x in FIN and a in FIN); oth = sum(1 for (x, a) in edge if x not in FIN and a not in FIN)
    stage = {frozenset(FIN), frozenset(set(HS) - FIN)}
    return {"edges": len(edge), "within_finished": fin, "within_other": oth, "between": len(edge) - fin - oth,
            "structurally_equivalent": se, "d_61_63": int(D[ix["61"], ix["63"]]),
            "partition_average": parts["average"], "partition_complete": parts["complete"],
            "partition_equals_stages": all({frozenset(v) for v in parts[m]} == stage for m in parts)}


VARIANTS = [
    ("base (as published)", BASE, False),
    ("year effects added", BASE, True),
    ("all attributes in levels", {a: False for a in BASE}, False),
    ("all attributes as yearly changes", {a: True for a in BASE}, False),
    ("level/change choice reversed", {a: not BASE[a] for a in BASE}, False),
]
pub = {(r["y_sector"], r["x_sector"]): float(r["p_mrqap"]) for r in csv.DictReader(open(os.path.join(RES, "mrqap.csv"), encoding="utf-8"))}
res = {}
lines = ["Specification sensitivity of the 306 flow-weight tests (MRQAP, 10,000 node permutations, seed 20260927)", ""]
base_sig = None; base_obs = None
for name, spec, year in VARIANTS:
    obs, pq = run(spec, year)
    if name.startswith("base"):
        d = max(abs(pq[m] - pub[m]) for m in pq)
        assert d < 1e-12, ("base run does not reproduce mrqap.csv", d)
    sig = {m for m in pq if pq[m] < ALPHA}
    sigc = {m for m in obs if obs[m][2] < ALPHA}
    if base_sig is None:
        base_sig, base_obs = sig, obs
    rec = {"spec": {a: ("change" if spec[a] else "levels") for a in spec}, "year_effects": year,
           "mrqap_significant": len(sig), "clustered_significant": len(sigc),
           "lost_vs_base": sorted(f"{a}<-{b}" for a, b in base_sig - sig), "gained_vs_base": sorted(f"{a}<-{b}" for a, b in sig - base_sig),
           "sign_changes_among_base_significant": sum(1 for m in base_sig if np.sign(obs[m][0]) != np.sign(base_obs[m][0])),
           "corr_coefficients_with_base": float(np.corrcoef([obs[m][0] for m in sorted(obs)], [base_obs[m][0] for m in sorted(obs)])[0, 1])}
    rec.update(network(sig))
    res[name] = rec
    lines.append(f"{name}: attributes " + ", ".join(f"{a} {rec['spec'][a]}" for a in ("prod", "fin", "elec"))
                 + f"; year effects {'yes' if year else 'no'}")
    lines.append(f"  {len(sig)} of 306 significant under MRQAP ({rec['clustered_significant']} with corridor-clustered standard errors); "
                 f"lost against the published specification: {' '.join(rec['lost_vs_base']) or 'none'}; gained: {' '.join(rec['gained_vs_base']) or 'none'}")
    lines.append(f"  sign changes among the 70 published ties: {rec['sign_changes_among_base_significant']}; correlation of the 306 coefficients "
                 f"with the published ones {rec['corr_coefficients_with_base']:.3f}")
    lines.append(f"  ties among the finished goods {rec['within_finished']}, among the other chapters {rec['within_other']}, between the groups {rec['between']}; "
                 f"structurally equivalent pairs {', '.join(rec['structurally_equivalent']) or 'none'}; distance 61-63 {rec['d_61_63']}")
    lines.append(f"  two positions equal to finished goods / other chapters under average and complete linkage: {'yes' if rec['partition_equals_stages'] else 'no'}")
    lines.append("")
open(os.path.join(RES, "specification_sensitivity.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("\n".join(lines))
