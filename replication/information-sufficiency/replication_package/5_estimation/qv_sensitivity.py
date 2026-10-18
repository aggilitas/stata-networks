"""Sensitivity of the screen to intra-EU exports recorded without a partner (QV), Supplementary Table S2.

QV is part of the source's world total and of no partner cell, so it is in REST. Its true partners are not
recorded; some may lie in R. Allocating a part q of a cell's QV to a partner j in R raises only the numerator of
that corridor's weight, by q / X_it, and leaves every other weight unchanged; the whole QV of a cell can raise
the weights of its source by at most QV / X_it in total. The selection rule keeps that share below 1 per cent
(1_selection/select_subnet.py). The script refits the 306 screen models of estimation.do under four allocations:
  proportional, all cells: every QV is split over the source's recorded EU27 partners in proportion to its
      recorded exports to them in that chapter and year (only the part that falls on R enters);
  proportional, ten cells: the same for the ten largest QV / X cells only;
  single partner, one cell at a time: the whole QV of one of the ten largest cells goes to one partner in R,
      every partner in turn (exhaustive);
  single partner, ten cells jointly: the whole QV of each of the ten cells goes to one partner in R drawn at
      random, 200 draws.
It reports the largest relative changes in the coefficients and the clustered standard errors of the models
significant under MRQAP, the largest change of a p value, and every change of significance at 5 per cent. The MRQAP
p values are recomputed, with the statistic and the 10,000 permutations of mrqap.py, for the proportional allocations
and for every single-partner allocation of each of the ten cells; the random joint draws are judged by the p values
from corridor-clustered standard errors. Reads data/comext_exports, ../3_inputs/networks/, results/unit_roots.csv (the specification of estimation.do) and
results/mrqap.csv (mrqap.py, run first), whose MRQAP p values the unperturbed computation must reproduce. Writes
results/qv_sensitivity.txt and results/qv_sensitivity_cells.csv. Requires numpy and scipy."""
import csv, gzip, math, os, random
import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
NET = os.path.join(ROOT, "3_inputs", "networks"); RES = os.path.join(HERE, "results")
R = "BE BG DE DK EE ES FR GR HR HU IT LT LV PL PT RO SE SI".split()
EU27 = "AT BE BG CY CZ DE DK EE ES FI FR GR HR HU IE IT LT LU LV MT NL PL PT RO SE SI SK".split()
HS = "41 42 43 50 51 52 53 54 56 57 58 59 60 61 62 63 64 65".split()
Y = list(range(2016, 2026)); T = len(Y); yidx = {t: n for n, t in enumerate(Y)}
ALPHA, NPERM, SEED, DRAWS = 0.05, 10000, 20260927, 200
E = [(i, j) for i in R for j in R if i != j]; G = len(E); N = G * T
eidx = {e: n for n, e in enumerate(E)}

X, W = {}, {}
for k in HS:
    tot, v = {}, {}
    for r in csv.DictReader(open(os.path.join(NET, f"export_{k}.csv"), encoding="utf-8")):
        t, i, j, a = int(r["year"]), r["source"], r["target"], float(r["source_value"])
        tot[(i, t)] = tot.get((i, t), 0.0) + a
        if j != "REST": v[(i, j, t)] = a
    X[k] = tot
    W[k] = np.array([[v[(i, j, t)] / tot[(i, t)] if tot[(i, t)] > 0 else 0.0 for t in Y] for i, j in E])
ur = {r["variable"]: float(r["p_fisher_pp"]) for r in csv.DictReader(open(os.path.join(RES, "unit_roots.csv"), encoding="utf-8"))}


def attribute(name, change):
    a = {}
    for r in csv.DictReader(open(os.path.join(NET, f"attr_{name}.csv"), encoding="utf-8")):
        a[(r["source"], r["target"], int(r["year"]))] = math.log(float(r["target_value"]) / float(r["source_value"]))
    return np.array([[a[(i, j, t)] - (a[(i, j, t - 1)] if change else 0.0) for t in Y] for i, j in E])


within = lambda M: (M - M.mean(axis=1, keepdims=True)).ravel()
C = np.column_stack([within(attribute(a, ur[f"attr_{a}"] >= ALPHA)) for a in ("prod", "fin", "elec")])
K = 1 + C.shape[1]; CF = (N - 1) / (N - K - 1) * G / (G - 1)


def fit(xv, Ymat):
    Xm = np.column_stack([xv, C]); XtXi = np.linalg.inv(Xm.T @ Xm)
    B = XtXi @ (Xm.T @ Ymat); U = Ymat - Xm @ B; z = Xm @ XtXi[0]
    S = (z[:, None] * U).reshape(G, T, -1).sum(axis=1)
    se = np.sqrt(CF * (S ** 2).sum(axis=0))
    return B[0], se, B[0] / se


def screen(Wd, only=None):
    """all 306 models, or only those with a chapter in `only`; (b, se, t, p)"""
    Wi = {k: within(Wd[k]) for k in HS}; res = {}
    for b in HS:
        ys = [a for a in HS if a != b and (only is None or a in only or b in only)]
        if not ys: continue
        beta, se, t = fit(Wi[b], np.column_stack([Wi[a] for a in ys]))
        for n, a in enumerate(ys):
            res[(a, b)] = (beta[n], se[n], t[n], 2 * stats.t.sf(abs(t[n]), G - 1))
    return res


# MRQAP with the permutations of mrqap.py (drawn in the same order from the same seed). The refit of a permutation
# uses the regressor partialled on the attributes (Frisch-Waugh-Lovell), which gives the coefficient, the clustered
# standard error and the t of the full regression; it is done for a block of permutations at once.
rng = np.random.default_rng(SEED); pos = {c: n for n, c in enumerate(R)}
PIDX = np.array([[eidx[(R[p[pos[i]]], R[p[pos[j]]])] for i, j in E] for p in (rng.permutation(len(R)) for _ in range(NPERM))])
CtC = np.linalg.solve(C.T @ C, C.T)
mc = lambda V: V - (V @ CtC.T) @ C.T                      # attributes partialled out of each row of V
BLOCK = 1000
MODELS = [(a, b) for b in HS for a in HS if a != b]


def mrqap(Wd, models=MODELS):
    """MRQAP p values of `models`"""
    Wi = {c: within(Wd[c]) for c in HS}; res = screen(Wd, only={c for m in models for c in m}); cnt = dict.fromkeys(models, 0)
    for b in HS:
        ys = [a for a, c in models if c == b]
        if not ys: continue
        ex = mc(Wi[b][None, :])[0].reshape(G, T)
        Yt = {a: mc(Wi[a][None, :])[0].reshape(G, T) for a in ys}
        for c0 in range(0, NPERM, BLOCK):
            X3 = mc(ex[PIDX[c0:c0 + BLOCK]].reshape(-1, N)).reshape(-1, G, T)
            Bg = (X3 ** 2).sum(axis=2); ssx = Bg.sum(axis=1)
            for a in ys:
                Ag = np.einsum("qgt,gt->qg", X3, Yt[a]); beta = Ag.sum(axis=1) / ssx
                S = (Ag - beta[:, None] * Bg) / ssx[:, None]
                cnt[(a, b)] += int((np.abs(beta / np.sqrt(CF * (S ** 2).sum(axis=1))) >= abs(res[(a, b)][2])).sum())
    return {m: (1 + cnt[m]) / (1 + NPERM) for m in models}


# QV and the recorded EU27 partner cells of the sources in R
QV, cells = {}, {}
for i in R:
    for r in csv.DictReader(gzip.open(os.path.join(ROOT, "data", "comext_exports", f"export_{i}.csv.gz"), "rt", encoding="utf-8")):
        k, t, p, v = r["product"], int(r["year"]), r["partner"], r["value_eur"]
        if k not in HS or t not in Y or v in ("", None): continue
        v = float(v)
        if p == "QV": QV[(i, k, t)] = QV.get((i, k, t), 0.0) + v
        elif p in EU27 and p != i: cells[(i, p, k, t)] = v
share = sorted(((q / X[k][(i, t)], (i, k, t)) for (i, k, t), q in QV.items() if q > 0 and X[k][(i, t)] > 0), reverse=True)
top10 = [c for _, c in share[:10]]


def perturb(sel, mode, partner=None, rng=None):
    Wd = {k: W[k].copy() for k in HS}
    for (i, k, t) in sel:
        q, Xt = QV[(i, k, t)], X[k][(i, t)]
        if mode == "prop":
            eu = {j: cells.get((i, j, k, t), 0.0) for j in EU27 if j != i}; s = sum(eu.values())
            if s <= 0: continue
            for j in R:
                if j != i and eu[j] > 0: Wd[k][eidx[(i, j)], yidx[t]] += q * eu[j] / s / Xt
        else:
            j = partner if partner is not None else rng.choice([j for j in R if j != i])
            Wd[k][eidx[(i, j)], yidx[t]] += q / Xt
    return Wd


base = screen(W); sigc0 = {m for m in base if base[m][3] < ALPHA}
pq0 = mrqap(W); sigq0 = {m for m in pq0 if pq0[m] < ALPHA}
ref = {(r["y_sector"], r["x_sector"]): float(r["p_mrqap"]) for r in csv.DictReader(open(os.path.join(RES, "mrqap.csv"), encoding="utf-8"))}
dref = max(abs(pq0[m] - ref[m]) for m in MODELS)
assert dref < 0.5 / (1 + NPERM), ("the MRQAP p values differ from results/mrqap.csv", dref)
assert sigc0 <= sigq0


def compare(res, pq=None):
    """changes against the unperturbed screen: coefficients and clustered SE of the models significant under MRQAP,
    clustered p values of all models in res, MRQAP p values of the models in pq"""
    keys = [m for m in res]; sg = [m for m in keys if m in sigq0]
    d = {"db": max(abs(res[m][0] / base[m][0] - 1) for m in sg), "dse": max(abs(res[m][1] / base[m][1] - 1) for m in sg),
         "dp": max(abs(res[m][3] - base[m][3]) for m in keys), "flips": sorted(m for m in keys if (res[m][3] < ALPHA) != (m in sigc0))}
    if pq is not None:
        d["dq"] = max(abs(pq[m] - pq0[m]) for m in pq); d["qflips"] = sorted(m for m in pq if (pq[m] < ALPHA) != (m in sigq0))
    return d


def merge(ds):
    out = {k: max(d[k] for d in ds) for k in ("db", "dse", "dp", "dq") if all(k in d for d in ds)}
    for k in ("flips", "qflips"):
        if all(k in d for d in ds): out[k] = sorted({m for d in ds for m in d[k]})
    return out


fl = lambda ms: " ".join(a + "<-" + b for a, b in ms) or "none"
fmt = lambda d: (f"largest relative change among the {len(sigq0)} models significant under MRQAP: coefficient {100 * d['db']:.3f} per cent, "
                 f"clustered standard error {100 * d['dse']:.3f} per cent; largest change of a clustered p value {d['dp']:.4f}; changes of "
                 f"significance, corridor-clustered standard errors: {fl(d['flips'])}" + (f"; largest change of an MRQAP p value {d['dq']:.4f}; changes of "
                 f"significance, MRQAP: {fl(d['qflips'])}" if "dq" in d else ""))
out = [f"QV sensitivity on the eighteen-country subnet; {len(share)} source-chapter-year cells with positive QV; "
       f"QV / X at most {100 * share[0][0]:.4f} per cent, median {100 * share[len(share) // 2][0]:.4f} per cent",
       f"screen: {len(sigq0)} of 306 models significant at 5 per cent under MRQAP ({NPERM} permutations, seed {SEED}; the p values of "
       f"results/mrqap.csv reproduced), {len(sigc0)} with corridor-clustered standard errors", "",
       "ten largest QV / X cells: " + "; ".join(f"{i} {k} {t} {100 * s:.4f}%" for s, (i, k, t) in share[:10]), ""]
Wp = perturb([c for _, c in share], "prop")
out.append("proportional allocation, all cells: " + fmt(compare(screen(Wp), mrqap(Wp))))
Wp = perturb(top10, "prop")
out.append("proportional allocation, ten cells: " + fmt(compare(screen(Wp), mrqap(Wp))))
rows, cellw = [], []
for (i, k, t) in top10:
    ds = []
    for j in R:
        if j == i: continue
        Wp = perturb([(i, k, t)], "single", partner=j); mk = [m for m in MODELS if k in m]
        d = compare(screen(Wp, only={k}), mrqap(Wp, mk)); ds.append(d)
        rows.append([i, k, t, j, 100 * QV[(i, k, t)] / X[k][(i, t)], d["db"], d["dse"], d["dp"], d["dq"], fl(d["flips"]), fl(d["qflips"])])
    cellw.append(merge(ds))
    out.append(f"single partner, cell {i} {k} {t} ({100 * QV[(i, k, t)] / X[k][(i, t)]:.4f}%), every partner of R, worst case: " + fmt(cellw[-1]))
out.append("single partner, the ten cells one at a time, every partner, worst case over the cells: " + fmt(merge(cellw)))
rng = random.Random(SEED); draws = [compare(screen(perturb(top10, "single", rng=rng))) for _ in range(DRAWS)]
out.append(f"single partner, ten cells jointly, {DRAWS} random draws, largest over the draws (corridor-clustered standard errors): " + fmt(merge(draws))
           + f"; draws with a change of significance: {sum(bool(d['flips']) for d in draws)}")
with open(os.path.join(RES, "qv_sensitivity_cells.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["source", "hs", "year", "partner", "qv_share_pct", "max_rel_change_b_sig", "max_rel_change_se_sig",
                                   "max_change_p_cluster", "max_change_p_mrqap", "changes_of_significance_cluster", "changes_of_significance_mrqap"])
    for r in rows: w.writerow([r[0], r[1], r[2], r[3]] + [repr(float(x)) for x in r[4:9]] + r[9:])
open(os.path.join(RES, "qv_sensitivity.txt"), "w", encoding="utf-8").write("\n".join(out) + "\n")
print("\n".join(out))
