"""Monte Carlo precision of the MRQAP p values near the 5 per cent level (Supplementary Table S1).

A permutation p value from 10,000 draws is itself an estimate; near 0.05 its Monte Carlo standard error is
about 0.002. For every test of results/mrqap.csv (the network weight and each attribute edge of the 306 models)
the script computes the exact (Clopper-Pearson) 95 per cent interval of the permutation p from its 10,000 draws.
Each test whose interval contains 0.05 is computed again with the permutation sequence of mrqap.py extended to
100,000 draws: the same generator and seed, so that the first 10,000 permutations are those of mrqap.py, and the
same statistic (the corridor-clustered t of the tested regressor after double semi-partialling). The script
checks that the first 10,000 draws reproduce the p value of results/mrqap.csv exactly.

Reads ../3_inputs/networks/, results/unit_roots.csv and results/mrqap.csv (mrqap.py, run first). Writes
results/mrqap_precision.csv (every test: the hits among the 10,000 draws and the interval; for the tests
near 0.05 also the hits among 100,000 draws, the p value and its interval) and results/mrqap_precision.txt.
Requires numpy and scipy."""
import csv, math, os
import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
NET = os.path.join(ROOT, "3_inputs", "networks"); RES = os.path.join(HERE, "results")
R = "BE BG DE DK EE ES FR GR HR HU IT LT LV PL PT RO SE SI".split()
HS = "41 42 43 50 51 52 53 54 56 57 58 59 60 61 62 63 64 65".split()
Y = list(range(2016, 2026)); T = len(Y)
NPERM, NLONG, SEED, ALPHA, BLOCK = 10000, 100000, 20260927, 0.05, 1000
E = [(i, j) for i in R for j in R if i != j]; G = len(E); N = G * T
eidx = {e: n for n, e in enumerate(E)}; pos = {c: n for n, c in enumerate(R)}
TESTS = ("x", "prod", "fin", "elec")                      # the network weight and the three attribute edges


def weights(k):
    tot, v = {}, {}
    for r in csv.DictReader(open(os.path.join(NET, f"export_{k}.csv"), encoding="utf-8")):
        t, i, j, a = int(r["year"]), r["source"], r["target"], float(r["source_value"])
        tot[(i, t)] = tot.get((i, t), 0.0) + a
        if j != "REST": v[(i, j, t)] = a
    return np.array([[v[(i, j, t)] / tot[(i, t)] if tot[(i, t)] > 0 else 0.0 for t in Y] for i, j in E])


def attribute(name, change):
    a = {}
    for r in csv.DictReader(open(os.path.join(NET, f"attr_{name}.csv"), encoding="utf-8")):
        a[(r["source"], r["target"], int(r["year"]))] = math.log(float(r["target_value"]) / float(r["source_value"]))
    return np.array([[a[(i, j, t)] - (a[(i, j, t - 1)] if change else 0.0) for t in Y] for i, j in E])


within = lambda M: (M - M.mean(axis=1, keepdims=True)).ravel()
ur = {r["variable"]: float(r["p_fisher_pp"]) for r in csv.DictReader(open(os.path.join(RES, "unit_roots.csv"), encoding="utf-8"))}
C = np.column_stack([within(attribute(a, ur[f"attr_{a}"] >= ALPHA)) for a in ("prod", "fin", "elec")])
W = {k: within(weights(k)) for k in HS}
K = 1 + C.shape[1]; CF = (N - 1) / (N - K - 1) * G / (G - 1)


def partial(v, Z, Zp):
    """v (one row per draw, or a vector) with the columns of Z partialled out"""
    return v - (v @ Zp.T) @ Z.T


def tstat(X, y):
    """corridor-clustered t of x in the regression of y on x, for each row x of X (both already partialled)"""
    X3 = X.reshape(-1, G, T); Bg = (X3 ** 2).sum(axis=2); ssx = Bg.sum(axis=1)
    Ag = (X3 * y.reshape(G, T)).sum(axis=2); beta = Ag.sum(axis=1) / ssx
    S = (Ag - beta[:, None] * Bg) / ssx[:, None]
    return beta / np.sqrt(CF * (S ** 2).sum(axis=1))


def interval(k, m):
    """exact 95 per cent interval of a binomial proportion, k successes in m draws"""
    return (float(stats.beta.ppf(0.025, k, m - k + 1)) if k > 0 else 0.0, float(stats.beta.ppf(0.975, k + 1, m - k)) if k < m else 1.0)


rows = list(csv.DictReader(open(os.path.join(RES, "mrqap.csv"), encoding="utf-8")))
col = {"x": "p_mrqap", "prod": "p_mrqap_prod", "fin": "p_mrqap_fin", "elec": "p_mrqap_elec"}
out, near = [], []
for r in rows:
    for test in TESTS:
        p = float(r[col[test]]); hits = round(p * (NPERM + 1)) - 1
        assert abs((hits + 1) / (NPERM + 1) - p) < 1e-12
        lo, hi = interval(hits, NPERM)
        out.append({"y_sector": r["y_sector"], "x_sector": r["x_sector"], "test": test, "hits_10000": hits, "p_10000": p,
                    "mc95_low_10000": lo, "mc95_high_10000": hi})
        if lo <= ALPHA <= hi: near.append(out[-1])

# the permutation sequence of mrqap.py, extended: the first NPERM draws are those of mrqap.py
rng = np.random.default_rng(SEED)
perm = np.array([rng.permutation(len(R)) for _ in range(NLONG)])
src = np.array([pos[i] for i, _ in E]); dst = np.array([pos[j] for _, j in E])
lookup = np.full((len(R), len(R)), -1, dtype=np.int32); lookup[src, dst] = np.arange(G)
maps = lookup[perm[:, src], perm[:, dst]]                   # draw q: corridor g takes the residual of corridor maps[q, g]
assert (np.sort(maps, axis=1) == np.arange(G)).all()
for rec in near:
    a, b, test = rec["y_sector"], rec["x_sector"], rec["test"]
    if test == "x":
        Z = C; x = W[b]
    else:
        c = ("prod", "fin", "elec").index(test)
        Z = np.column_stack([W[b]] + [C[:, cc] for cc in range(3) if cc != c]); x = C[:, c]
    Zp = np.linalg.pinv(Z); xt = partial(x, Z, Zp); yt = partial(W[a], Z, Zp)
    tobs = abs(tstat(xt[None, :], yt)[0]); EX = xt.reshape(G, T); hits = 0
    for c0 in range(0, NLONG, BLOCK):
        Xq = partial(EX[maps[c0:c0 + BLOCK]].reshape(-1, N), Z, Zp)
        hits += int((np.abs(tstat(Xq, yt)) >= tobs).sum())
        if c0 + BLOCK == NPERM:
            assert hits == rec["hits_10000"], (a, b, test, hits, rec["hits_10000"])   # the draws of mrqap.py reproduced
    lo, hi = interval(hits, NLONG)
    rec.update({"hits_100000": hits, "p_100000": (hits + 1) / (NLONG + 1), "mc95_low_100000": lo, "mc95_high_100000": hi})

fields = ["y_sector", "x_sector", "test", "hits_10000", "p_10000", "mc95_low_10000", "mc95_high_10000",
          "hits_100000", "p_100000", "mc95_low_100000", "mc95_high_100000"]
with open(os.path.join(RES, "mrqap_precision.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(fields)
    for rec in out: w.writerow([repr(rec[k]) if isinstance(rec.get(k), float) else rec.get(k, "") for k in fields])
name = {"x": "network weight", "prod": "productivity", "fin": "real cost of credit", "elec": "electricity price"}
lines = [f"MRQAP Monte Carlo precision: {len(out)} tests ({len(rows)} models x {len(TESTS)}); {len(near)} have an exact 95 per cent "
         f"interval, from {NPERM} draws, that contains {ALPHA}; these are recomputed with {NLONG} draws (seed {SEED}, the first "
         f"{NPERM} draws those of mrqap.py, whose p values they reproduce)"]
for rec in near:
    s0, s1 = rec["p_10000"] < ALPHA, rec["p_100000"] < ALPHA
    lines.append(f"  {rec['y_sector']}<-{rec['x_sector']} {name[rec['test']]}: p {rec['p_10000']:.4f} with {NPERM} draws, "
                 f"{rec['p_100000']:.4f} with {NLONG} (95 per cent interval {rec['mc95_low_100000']:.4f}-{rec['mc95_high_100000']:.4f}); "
                 + ("significance unchanged" if s0 == s1 else "SIGNIFICANCE CHANGES"))
lines.append(f"changes of significance at {ALPHA}: {sum((r_['p_10000'] < ALPHA) != (r_['p_100000'] < ALPHA) for r_ in near)}")
open(os.path.join(RES, "mrqap_precision.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("\n".join(lines))
