"""MRQAP inference for the 306 screen models of estimation.do (section 6.3 of the paper).

Each model regresses the layer-a weight on the layer-b weight of the same corridor, with the three attribute
edges as controls and the corridor effect absorbed (within transformation), as reghdfe does in estimation.do.
The permutation test is multiple regression QAP with double semi-partialling (Dekker, Krackhardt and Snijders,
2007): the within-transformed layer-b weight is residualised on the within-transformed controls, the node
labels of that residual are permuted jointly in rows and columns, with the same permutation in every year, and
the model is refitted. The statistic is the t statistic of the layer-b weight with standard errors clustered
on the corridor, computed as reghdfe computes them (small-sample factor (N-1)/(N-K) x G/(G-1), with K the
regressors and the absorbed constant). The p value is (1 + the number of permutations with |t| at least the
observed |t|) / (1 + the number of permutations). The node permutations are drawn once and used for every
model.

Reads ../3_inputs/networks/ (export_<hs>.csv, attr_prod.csv, attr_fin.csv, attr_elec.csv) and
results/unit_roots.csv, written by estimation.do: an attribute whose Fisher-type Phillips-Perron p value in
levels is at least 0.05 enters as its yearly change, as in the do-file. If results/screen_models.csv is present,
the coefficients and clustered standard errors are checked against it.
The same test is applied to each attribute edge of every model, the attribute being residualised on the network weight and
the other two attributes. Writes results/mrqap.csv (one row per model), results/mrqap_summary.txt and
results/mrqap_permutations.csv (the node permutations, one per row).
Requires numpy and scipy."""
import csv, math, os, sys
import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
NET = os.path.join(ROOT, "3_inputs", "networks"); RES = os.path.join(HERE, "results")
R = "BE BG DE DK EE ES FR GR HR HU IT LT LV PL PT RO SE SI".split()
HS = "41 42 43 50 51 52 53 54 56 57 58 59 60 61 62 63 64 65".split()
FIN = {"42", "57", "61", "62", "63", "64", "65"}           # finished goods
Y = list(range(2016, 2026)); T = len(Y)
NPERM, SEED, ALPHA = 10000, 20260927, 0.05
E = [(i, j) for i in R for j in R if i != j]; G = len(E); N = G * T
eidx = {e: n for n, e in enumerate(E)}


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
    if change:
        return np.array([[a[(i, j, t)] - a[(i, j, t - 1)] for t in Y] for i, j in E])
    return np.array([[a[(i, j, t)] for t in Y] for i, j in E])


def within(M):
    return (M - M.mean(axis=1, keepdims=True)).ravel()


# specification as decided by the unit-root step of estimation.do
ur = {r["variable"]: float(r["p_fisher_pp"]) for r in csv.DictReader(open(os.path.join(RES, "unit_roots.csv"), encoding="utf-8"))}
spec = {a: ur[f"attr_{a}"] >= ALPHA for a in ("prod", "fin", "elec")}
C = np.column_stack([within(attribute(a, spec[a])) for a in ("prod", "fin", "elec")])
Wi = {k: within(weights(k)) for k in HS}
K = 1 + C.shape[1]
CF = (N - 1) / (N - K - 1) * G / (G - 1)


def fit_col(X, Ymat, j):
    """coefficients, clustered standard errors and t of column j of X in the regressions of every column of Ymat on X"""
    XtXi = np.linalg.inv(X.T @ X)
    B = XtXi @ (X.T @ Ymat); U = Ymat - X @ B; z = X @ XtXi[j]
    S = (z[:, None] * U).reshape(G, T, -1).sum(axis=1)
    se = np.sqrt(CF * (S ** 2).sum(axis=0))
    return B[j], se, B[j] / se


def fit(xv, Ymat):
    """coefficients, clustered standard errors and t of x in the regressions of every column of Ymat on [x, C]"""
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
        obs[(a, b)] = (beta[n], se[n], t[n], 2 * stats.t.sf(abs(t[n]), G - 1))

check = "results/screen_models.csv not found; no check against the do-file"
sp = os.path.join(RES, "screen_models.csv")
if os.path.exists(sp):
    S = {(r["y_sector"], r["x_sector"]): r for r in csv.DictReader(open(sp, encoding="utf-8"))}
    db = max(abs(obs[m][0] - float(S[m]["b_x"])) for m in obs)
    ds = max(abs(obs[m][1] - float(S[m]["se_x"])) / float(S[m]["se_x"]) for m in obs)
    dp = max(abs(obs[m][3] - float(S[m]["p_x"])) for m in obs)
    assert db < 1e-8 and ds < 1e-6 and dp < 1e-6, (db, ds, dp)
    check = f"coefficients, clustered standard errors and p values equal those of results/screen_models.csv (largest differences {db:.1e} absolute, {ds:.1e} relative; p {dp:.1e} absolute)"

# permutations: node labels, the same permutation in every year
rng = np.random.default_rng(SEED)
pos = {c: n for n, c in enumerate(R)}
perm = [rng.permutation(len(R)) for _ in range(NPERM)]
with open(os.path.join(RES, "mrqap_permutations.csv"), "w", newline="", encoding="utf-8") as f:
    # row q holds p_q, positions in R counted from 0: in permutation q, corridor (i, j) takes the residual of
    # corridor (R[p_q(i)], R[p_q(j)])
    w = csv.writer(f); w.writerow([f"p{c}" for c in range(len(R))])
    for p in perm: w.writerow([int(v) for v in p])
pidx = [np.array([eidx[(R[p[pos[i]]], R[p[pos[j]]])] for i, j in E]) for p in perm]
Pc = C @ np.linalg.solve(C.T @ C, C.T)
count = {m: 0 for m in obs}
for b in HS:
    ys = [a for a in HS if a != b]; Ymat = np.column_stack([Wi[a] for a in ys])
    ex = (Wi[b] - Pc @ Wi[b]).reshape(G, T)
    tobs = np.abs(np.array([obs[(a, b)][2] for a in ys]))
    for q in pidx:
        _, _, tp = fit(ex[q].ravel(), Ymat)
        for n in np.nonzero(np.abs(tp) >= tobs)[0]:
            count[(ys[n], b)] += 1
pq = {m: (1 + count[m]) / (1 + NPERM) for m in obs}

# the attribute edges: the same test for each attribute, residualised on the network weight and the other two attributes
ANAMES = ("prod", "fin", "elec")
acount = {(m, c): 0 for m in obs for c in range(3)}; aobs = {}
for b in HS:
    ys = [a for a in HS if a != b]; Ymat = np.column_stack([Wi[a] for a in ys])
    Xf = np.column_stack([Wi[b], C])
    for c in range(3):
        _, _, tfull = fit_col(Xf, Ymat, 1 + c)
        for n, a in enumerate(ys): aobs[((a, b), c)] = tfull[n]
        others = np.delete(Xf, 1 + c, axis=1)
        ec = (Xf[:, 1 + c] - others @ np.linalg.lstsq(others, Xf[:, 1 + c], rcond=None)[0]).reshape(G, T)
        tob = np.abs(tfull)
        for q in pidx:
            _, _, tp = fit_col(np.column_stack([others, ec[q].ravel()]), Ymat, others.shape[1])
            for n in np.nonzero(np.abs(tp) >= tob)[0]:
                acount[((ys[n], b), c)] += 1
pqa = {k: (1 + v) / (1 + NPERM) for k, v in acount.items()}

with open(os.path.join(RES, "mrqap.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["y_sector", "x_sector", "b_x", "se_x", "t_x", "p_cluster", "p_mrqap", "p_mrqap_prod", "p_mrqap_fin", "p_mrqap_elec"])
    for (a, b) in sorted(obs):
        w.writerow([a, b] + [repr(float(v)) for v in obs[(a, b)]] + [repr(pq[(a, b)])] + [repr(pqa[((a, b), c)]) for c in range(3)])


def summary(p, label):
    sig = {m for m in obs if p[m] < ALPHA}
    rec = sorted({tuple(sorted(m)) for m in sig if (m[1], m[0]) in sig})
    L = [f"{label}: {len(sig)} of 306 significant at 5 per cent ({sum(obs[m][0] > 0 for m in sig)} positive, "
         f"{sum(obs[m][0] < 0 for m in sig)} negative); {len(rec)} pairs significant in both directions"]
    for name, f in (("finished goods, within", lambda y, x: y in FIN and x in FIN),
                    ("other group, within", lambda y, x: y not in FIN and x not in FIN),
                    ("finished goods on the other group", lambda y, x: y in FIN and x not in FIN),
                    ("other group on finished goods", lambda y, x: y not in FIN and x in FIN)):
        ks = [m for m in obs if f(*m)]; s = [m for m in ks if m in sig]
        L.append(f"  {name}: {len(ks)} ordered pairs, {sum(obs[m][0] > 0 for m in s)} positive, "
                 f"{sum(obs[m][0] < 0 for m in s)} negative, density {len(s) / len(ks):.2f}")
    L.append("  reciprocal pairs: " + " ".join(f"{a}-{b}" for a, b in rec))
    pairs = [(a, b) for a in HS for b in HS if a < b]
    one = sum((p[(a, b)] < ALPHA) != (p[(b, a)] < ALPHA) for a, b in pairs)
    L.append(f"  unordered pairs significant in at least one direction {one + len(rec)}, in one only {one}")
    return L, sig


out = [f"MRQAP, double semi-partialling, {NPERM} node permutations (seed {SEED}), the same in every year;",
       "specification from results/unit_roots.csv: " + ", ".join(f"{a} {'yearly change' if spec[a] else 'levels'}" for a in spec),
       check, ""]
Lq, sq = summary(pq, "MRQAP"); Lc, sc = summary({m: obs[m][3] for m in obs}, "p values from corridor-clustered standard errors, G-1 df")
out += Lq + [""] + Lc + [""]
out.append(f"significant with corridor-clustered standard errors but not under MRQAP: {' '.join(a + '<-' + b for a, b in sorted(sc - sq)) or 'none'}")
out.append(f"significant under MRQAP but not with corridor-clustered standard errors: {' '.join(a + '<-' + b for a, b in sorted(sq - sc)) or 'none'}")
pc = np.array([obs[m][3] for m in sorted(obs)]); pm = np.array([pq[m] for m in sorted(obs)])
out.append(f"Spearman correlation of the two p values over the 306 models: {stats.spearmanr(pc, pm).correlation:.3f}")
tt = [(obs[(a, b)][2], obs[(b, a)][2]) for a in HS for b in HS if a < b]
out.append(f"correlation of the t statistics of the two directions over 153 unordered pairs: {np.corrcoef(np.array(tt).T)[0, 1]:.2f}")
out.append("")
out.append("attribute edges significant at 5 per cent, by dependent chapter (of its 17 models): MRQAP | corridor-clustered standard errors")
for a in HS:
    row = []
    for c, nm in enumerate(ANAMES):
        mq = [m for m in obs if m[0] == a and pqa[(m, c)] < ALPHA]
        mc = [m for m in obs if m[0] == a and 2 * stats.t.sf(abs(aobs[(m, c)]), G - 1) < ALPHA]
        sgn = lambda L: ("+" if all(aobs[(m, c)] > 0 for m in L) else "-" if all(aobs[(m, c)] < 0 for m in L) else "+/-") if L else ""
        if mq or mc: row.append(f"{nm} {len(mq)}{sgn(mq)} | {len(mc)}{sgn(mc)}")
    if row: out.append(f"  {a}: " + "; ".join(row))
open(os.path.join(RES, "mrqap_summary.txt"), "w", encoding="utf-8").write("\n".join(out) + "\n")
print("\n".join(out))
