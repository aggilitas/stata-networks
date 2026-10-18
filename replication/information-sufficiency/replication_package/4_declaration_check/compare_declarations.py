"""Exporter- versus importer-declared weights on a ten-country subnet D, TCLF chapters, 2016-2025.

w_exp(i,j,t) = x_ij / WORLD_i        x_ij = i's declared exports to j
w_imp(i,j,t) = m_ji / WORLD_i        m_ji = j's declared imports from i
The denominator is i's declared world exports in both, so REST_i is always taken
from the exporter: REST_imp = WORLD_i - sum_j m_ji (its minimum is reported; it can be negative).
A chapter is complete on both sides when, on D and in every year, neither side
reports under QY or QX and every cell of either side is present and positive.
Compared: level ratio m_ji / x_ij; its stability over the years on each edge
(sd of ln ratio); corridor-demeaned correlation of the two weights and the share
of within variance of w_exp that w_imp reproduces. Writes compare_declarations_result.txt."""
import csv, gzip, math, os
from statistics import median
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here)
D = "BE BG DE ES FR GR HU IT PL RO".split()
TCLF = ["41", "42", "43"] + [str(c) for c in range(50, 66)]
W = range(2016, 2026); HIDE = ("QY", "QX")
def load(path, flow):
    cell, world, hid = {}, {}, {}
    for r in csv.DictReader(gzip.open(path, "rt", encoding="utf-8")):
        k, t, p = r["product"], int(r["year"]), r["partner"]
        if k not in TCLF or t not in W or r["value_eur"] in ("", None): continue
        v = float(r["value_eur"]); rep = r["reporter"]
        if p == "WORLD": world[(rep, k, t)] = v
        elif p in HIDE: hid[(rep, k, t)] = hid.get((rep, k, t), 0) + v
        elif p in D and p != rep: cell[(rep, p, k, t)] = v
    return cell, world, hid
X, WX, HX, M, WM, HM = {}, {}, {}, {}, {}, {}
for c in D:
    a = load(os.path.join(root, "data", "comext_exports", f"export_{c}.csv.gz"), 2); X.update(a[0]); WX.update(a[1]); HX.update(a[2])
    b = load(os.path.join(root, "data", "comext_imports", f"import_{c}.csv.gz"), 1); M.update(b[0]); WM.update(b[1]); HM.update(b[2])
E = [(i, j) for i in D for j in D if i != j]
out = []
say = out.append
say("chapter | exp QY yrs | imp QY (importer:years) | exp zero | imp zero | both complete")
full = []
for k in TCLF:
    hx = sum(1 for i in D for t in W if HX.get((i, k, t), 0) > 0)
    hm = {j: [t for t in W if HM.get((j, k, t), 0) > 0] for j in D}
    hm = {j: v for j, v in hm.items() if v}
    zx = sum(1 for i, j in E for t in W if not X.get((i, j, k, t), 0) > 0)
    zm = sum(1 for i, j in E for t in W if not M.get((j, i, k, t), 0) > 0)
    ok = hx == 0 and not hm and zx == 0 and zm == 0
    if ok: full.append(k)
    say(f"{k} | {hx} | {hm or '-'} | {zx} | {zm} | {'yes' if ok else 'no'}")
def compare(k, edges_years):
    rows = []
    for (i, j) in E:
        for t in W:
            if (i, j, t) not in edges_years: continue
            x = X.get((i, j, k, t), 0.0); m = M.get((j, i, k, t), 0.0); w = WX[(i, k, t)]
            rows.append((i, j, t, x / w, m / w, x, m))
    rest = min(WX[(i, k, t)] - sum(M.get((j, i, k, t), 0.0) for j in D if j != i) for i in D for t in W)
    ratio = [m / x for *_, x, m in rows if x > 0 and m > 0]
    sd = []
    for (i, j) in E:
        lr = [math.log(m / x) for a, b, t, _, _, x, m in rows if (a, b) == (i, j) and x > 0 and m > 0]
        if len(lr) > 2:
            mu = sum(lr) / len(lr); sd.append(math.sqrt(sum((v - mu) ** 2 for v in lr) / (len(lr) - 1)))
    de, dm = [], []
    for (i, j) in E:
        r_ = [(we, wm) for a, b, t, we, wm, _, _ in rows if (a, b) == (i, j)]
        if len(r_) < 2: continue
        me = sum(v for v, _ in r_) / len(r_); mm = sum(v for _, v in r_) / len(r_)
        de += [v - me for v, _ in r_]; dm += [v - mm for _, v in r_]
    sxy = sum(a * b for a, b in zip(de, dm)); sxx = sum(a * a for a in de); syy = sum(b * b for b in dm)
    corr = sxy / math.sqrt(sxx * syy)
    r2 = 1 - sum((a - (sxy / syy) * b) ** 2 for a, b in zip(de, dm)) / sxx
    return rest, median(ratio), median(sd), corr, r2, len(rows)
say("\nboth sides complete: " + " ".join(full))
say("\nchapter | min REST_imp | median m/x | median sd of ln(m/x) over years | within corr | within R2 | edge-years")
for k in full:
    ey = {(i, j, t) for i, j in E for t in W}
    rest, rt, sd, corr, r2, n = compare(k, ey)
    say(f"{k} | {rest:,.0f} | {rt:.3f} | {sd:.3f} | {corr:.3f} | {r2:.3f} | {n}")
say("\n55 (exporter side hides the partner for IT in some years): comparison on the years and edges the exporter side does show")
k = "55"
ey = {(i, j, t) for i, j in E for t in W if HX.get((i, k, t), 0) == 0}
rest, rt, sd, corr, r2, n = compare(k, ey)
say(f"55 | {rest:,.0f} | {rt:.3f} | {sd:.3f} | {corr:.3f} | {r2:.3f} | {n}")
open(os.path.join(here, "compare_declarations_result.txt"), "w", encoding="utf-8").write("\n".join(out) + "\n")
print("\n".join(out))
