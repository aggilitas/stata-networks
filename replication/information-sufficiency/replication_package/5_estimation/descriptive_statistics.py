"""Descriptive statistics reported in section 6 and Appendix A.

Reads data/comext_exports, 3_inputs/networks, 2_attributes/real_credit_cost.csv,
5_estimation/results/screen_models.csv (written by estimation.do) and
5_estimation/results/mrqap.csv (written by mrqap.py); run after both, or with the packaged results.
Writes descriptive_statistics_result.txt. Quantiles are inclusive
(statistics.quantiles, method='inclusive')."""
import csv, gzip, os, statistics as st
from collections import defaultdict
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here)
EU27 = "AT BE BG CY CZ DE DK EE ES FI FR GR HR HU IE IT LT LU LV MT NL PL PT RO SE SI SK".split()
R = "BE BG DE DK EE ES FR GR HR HU IT LT LV PL PT RO SE SI".split()
TCLF = ["41", "42", "43"] + [str(c) for c in range(50, 66)]
HS = [k for k in TCLF if k != "55"]
Y = range(2016, 2026)
out = []
say = out.append
dec = lambda v: st.quantiles(v, n=10, method="inclusive")

# trade: world totals, extra-EU27 totals, recorded cells on the subnet
world, ext, cell = defaultdict(float), defaultdict(float), {}
for i in EU27:
    for r in csv.DictReader(gzip.open(os.path.join(root, "data", "comext_exports", f"export_{i}.csv.gz"), "rt", encoding="utf-8")):
        k, t, p, v = r["product"], int(r["year"]), r["partner"], r["value_eur"]
        if k not in TCLF or t not in Y or v in ("", None): continue
        if p == "WORLD": world[(i, k)] += float(v)
        elif p == "EXT_EU27_2020": ext[(i, k)] += float(v)
        elif i in R and p in R and p != i and k in HS: cell[(i, p, k, t)] = float(v)
tot = sum(world.values()); by = {i: sum(v for (a, k), v in world.items() if a == i) for i in EU27}
say("Shares of EU27 exports to the world in the 19 TCLF chapters, 2016-2025 (section 6.1):")
for i in sorted(by, key=by.get, reverse=True)[:3]: say(f"  {i} {100 * by[i] / tot:.1f} per cent")
say(f"  the eighteen members of R {100 * sum(by[i] for i in R) / tot:.1f} per cent")
by18 = {i: sum(v for (a, k), v in world.items() if a == i and k in HS) for i in EU27}; tot18 = sum(by18.values())
say(f"  over the 18 chapters without 55: the eighteen members of R {100 * sum(by18[i] for i in R) / tot18:.1f} per cent; IT {100 * by18['IT'] / tot18:.1f} per cent")
sh = {i: 100 * sum(ext[(i, k)] for k in HS) / sum(world[(i, k)] for k in HS) for i in R}
lo, hi = min(sh, key=sh.get), max(sh, key=sh.get)
say(f"Share of exports outside the EU27, 18 chapters, 2016-2025 (section 6.5): lowest {lo} {sh[lo]:.1f}, highest {hi} {sh[hi]:.1f} per cent")
n_cells = len(R) * (len(R) - 1) * len(HS) * len(Y)
zero_rec = sum(1 for v in cell.values() if v == 0)
say(f"Cells of the mesh of R (section 6.5): {n_cells}; recorded {len(cell)}, of which {zero_rec} with value zero; absent {n_cells - len(cell)}")

# REST share, bias factor, switches, from the input networks
rho, series, sw, nser = {}, defaultdict(list), 0, 0
for k in HS:
    X, REST, w = defaultdict(float), {}, defaultdict(dict)
    for r in csv.DictReader(open(os.path.join(root, "3_inputs", "networks", f"export_{k}.csv"), encoding="utf-8")):
        i, j, t, v = r["source"], r["target"], int(r["year"]), float(r["source_value"])
        X[(i, t)] += v
        if j == "REST": REST[(i, t)] = v
        else: w[(i, j)][t] = v
    for (i, t), x in X.items(): rho[(i, k, t)] = REST[(i, t)] / x
    for s in w.values():
        nser += 1; z = [s[t] > 0 for t in Y]; sw += sum(a != b for a, b in zip(z, z[1:]))
v = list(rho.values()); d = dec(v)
say(f"REST share of the source's world exports, {len(v)} source-chapter-year cells (section 6.1): "
    f"min {min(v):.3f}; median {100 * st.median(v):.1f}, 10th {100 * d[0]:.1f}, 90th {100 * d[8]:.1f} per cent")
fac = [1 / (1 - x) for x in v if x < 1]; d = dec(fac)
say(f"Factor 1/(1-rho) without REST, {len(fac)} cells with rho < 1 (section 6.2): median {st.median(fac):.2f}, 10th {d[0]:.2f}, 90th {d[8]:.2f}")
for (i, k, t), x in sorted(rho.items()):
    if x < 1: series[(i, k)].append(1 / (1 - x))
ratio = [max(s) / min(s) for s in series.values()]
say(f"  largest over smallest factor within a source-chapter series, {len(ratio)} series: median {st.median(ratio):.2f}; "
    f"above 3 in {sum(x > 3 for x in ratio)} ({100 * sum(x > 3 for x in ratio) / len(ratio):.1f} per cent)")
say(f"Year-to-year switches between zero and a positive value on the corridors of R (section 6.1): {sw} over {nser} corridor series")

# producer prices in 2022
pi = [float(r["ppi_change"]) for r in csv.DictReader(open(os.path.join(root, "2_attributes", "real_credit_cost.csv"), encoding="utf-8")) if r["year"] == "2022" and r["country"] in R]
say(f"Manufacturing producer price change in 2022 across the eighteen members (section 6.2): {min(pi):.1f} to {max(pi):.1f} per cent")

# screen
S = {(r["y_sector"], r["x_sector"]): r for r in csv.DictReader(open(os.path.join(here, "results", "screen_models.csv"), encoding="utf-8"))}
b = {key: float(r["b_x"]) for key, r in S.items()}; p = {key: float(r["p_x"]) for key, r in S.items()}
tt = {key: float(r["b_x"]) / float(r["se_x"]) for key, r in S.items()}
pairs = [(a, c) for a in HS for c in HS if a < c]
ta, tb = [tt[(a, c)] for a, c in pairs], [tt[(c, a)] for a, c in pairs]
one = sum((p[(a, c)] < .05) != (p[(c, a)] < .05) for a, c in pairs); both = sum(p[(a, c)] < .05 and p[(c, a)] < .05 for a, c in pairs)
say(f"Screen, corridor-clustered standard errors (section 6.3): correlation of the t statistics of the two directions over {len(pairs)} unordered pairs {st.correlation(ta, tb):.2f}; "
    f"pairs significant in at least one direction {one + both}, in both {both}, in one only {one}")
FG = {"42", "57", "61", "62", "63", "64", "65"}
blocks = [("finished goods, within", lambda y, x: y in FG and x in FG), ("other group, within", lambda y, x: y not in FG and x not in FG),
          ("finished goods on the other group", lambda y, x: y in FG and x not in FG), ("other group on finished goods", lambda y, x: y not in FG and x in FG),
          ("all", lambda y, x: True)]
say("Table 4 with corridor-clustered standard errors, significant at 5 per cent by block (ordered pairs, positive, negative, density):")
for name, f in blocks:
    ks = [key for key in S if f(*key)]; pos = sum(p[key] < .05 and b[key] > 0 for key in ks); neg = sum(p[key] < .05 and b[key] < 0 for key in ks)
    say(f"  {name}: {len(ks)}, {pos}, {neg}, {(pos + neg) / len(ks):.2f}")
Q = {(r["y_sector"], r["x_sector"]): float(r["p_mrqap"]) for r in csv.DictReader(open(os.path.join(here, "results", "mrqap.csv"), encoding="utf-8"))}
say("Table 4 with MRQAP, significant at 5 per cent by block (ordered pairs, positive, negative, density):")
for name, f in blocks:
    ks = [key for key in S if f(*key)]; pos = sum(Q[key] < .05 and b[key] > 0 for key in ks); neg = sum(Q[key] < .05 and b[key] < 0 for key in ks)
    say(f"  {name}: {len(ks)}, {pos}, {neg}, {(pos + neg) / len(ks):.2f}")
oneq = sum((Q[(a, c)] < .05) != (Q[(c, a)] < .05) for a, c in pairs); bothq = sum(Q[(a, c)] < .05 and Q[(c, a)] < .05 for a, c in pairs)
say(f"Screen, MRQAP (section 6.3): pairs significant in at least one direction {oneq + bothq}, in both {bothq}, in one only {oneq}")
open(os.path.join(here, "descriptive_statistics_result.txt"), "w", encoding="utf-8").write("\n".join(out) + "\n")
print("\n".join(out))
