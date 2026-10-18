"""Country and sector selection for the TCLF group, absent cell = zero.

Comext DS-045409, exporter-declared exports (data/comext_exports/export_XX.csv.gz),
2016-2025, the 19 TCLF chapters: 41-43 (leather), 50-63 (textiles),
64-65 (footwear, headgear).

A country i is observed in chapter k if, in every year of the window:
  - its WORLD export total in k is published;
  - it reports nothing in k under QY or QX (partner not specified for
    commercial or military reasons: the flow exists but its partner is hidden);
  - its intra-EU exports recorded without a partner (QV) stay below 1 per cent of
    its WORLD total in k. Such exports are in the world total and in no partner
    cell, so they can raise a weight at most by their share of the total; the
    condition bounds that share by one percentage point. The gap in which the
    threshold falls is reported below: any threshold within it gives the same set.
An absent partner cell is zero: member states estimate below-threshold trade and
allocate it by partner and chapter, so a cell with trade is never left empty.
QV and QR (stores and provisions) go to REST.

For a set S of countries fixed across the chosen chapters, every i in S must be
observed in every chosen chapter; REST_i = WORLD_i - sum_{j in S} x_ij >= 0.
Writes selection_result.txt (the trade-off between countries and chapters, reasons)."""
import csv, gzip, os
from itertools import combinations
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here)
longdir = os.path.join(root, "data", "comext_exports")
EU27 = "AT BE BG CY CZ DE DK EE ES FI FR GR HR HU IE IT LT LU LV MT NL PL PT RO SE SI SK".split()
TCLF = ["41", "42", "43"] + [str(c) for c in range(50, 66)]
W = range(2016, 2026)
HIDE = ("QY", "QX")
QV_MAX = 0.01
world, hidden, qv, cell, neg = {}, {}, {}, {}, []
for i in EU27:
    for r in csv.DictReader(gzip.open(os.path.join(longdir, f"export_{i}.csv.gz"), "rt", encoding="utf-8")):
        k, t, p = r["product"], int(r["year"]), r["partner"]
        if k not in TCLF or t not in W or r["value_eur"] in ("", None): continue
        v = float(r["value_eur"])
        if v < 0: neg.append((i, p, k, t, v))
        if p == "WORLD": world[(i, k, t)] = v
        elif p in HIDE: hidden[(i, k, t)] = hidden.get((i, k, t), 0) + v
        elif p == "QV": qv[(i, k, t)] = qv.get((i, k, t), 0) + v
        elif p in EU27 and p != i: cell[(i, p, k, t)] = v
out = []
say = lambda s="": out.append(s)
say(f"negative values: {len(neg)}")
obs, why = {}, {}
for i in EU27:
    for k in TCLF:
        miss = [t for t in W if (i, k, t) not in world]
        hid = [t for t in W if hidden.get((i, k, t), 0) > 0]
        qvy = [t for t in W if (i, k, t) in world and world[(i, k, t)] > 0 and qv.get((i, k, t), 0) >= QV_MAX * world[(i, k, t)]]
        obs[(i, k)] = not miss and not hid and not qvy
        if not obs[(i, k)]: why[(i, k)] = (miss, hid, qvy)
say("\nobserved countries per chapter (of 27):")
for k in TCLF:
    bad = {i: why[(i, k)] for i in EU27 if not obs[(i, k)]}
    say(f"  {k}: {27 - len(bad)}  not observed: " + ", ".join(
        f"{i}({' '.join(x for x in ('WORLD missing ' + str(m) if m else '', 'QY ' + str(len(h)) + 'y' if h else '', 'QV>=1% ' + str(len(q)) + 'y' if q else '') if x)})"
        for i, (m, h, q) in bad.items()))
say("\nobserved chapters per country (of 19):")
for i in EU27:
    say(f"  {i}: {sum(obs[(i, k)] for k in TCLF)}  missing: {' '.join(k for k in TCLF if not obs[(i, k)])}")
# trade-off: for every chapter subset, the countries observed in all of them
mask = {k: frozenset(i for i in EU27 if obs[(i, k)]) for k in TCLF}
best = {}
for n in range(1, len(TCLF) + 1):
    top = (0, None, None)
    for C in combinations(TCLF, n):
        S = frozenset(EU27)
        for k in C:
            S &= mask[k]
            if len(S) <= top[0]: break
        if len(S) > top[0]: top = (len(S), C, S)
    best[n] = top
say("\nchapters -> largest fixed country set observed in all of them:")
for n in range(len(TCLF), 0, -1):
    c, C, S = best[n]
    out_ch = [k for k in TCLF if k not in C]
    say(f"  {n:2d} chapters: {c:2d} countries | left out: {' '.join(out_ch) or '-'} | countries: {' '.join(sorted(S))}")
def zeros(S, C):
    res = []
    for k in C:
        z = sum(1 for i in S for j in S if i != j for t in W if not cell.get((i, j, k, t), 0) > 0)
        allz = sum(1 for i in S for j in S if i != j and all(not cell.get((i, j, k, t), 0) > 0 for t in W))
        rmin = min(world[(i, k, t)] - sum(cell.get((i, j, k, t), 0) for j in S if j != i) for i in S for t in W)
        res.append((k, z, allz, rmin))
    return res
say("\nzero cells for the full set of 19 chapters and for each Pareto set with >= 10 countries:")
for n in range(len(TCLF), 0, -1):
    c, C, S = best[n]
    if c < 10: continue
    E = c * (c - 1)
    say(f"  {n} chapters, {c} countries ({E} edges x 10 years):")
    for k, z, allz, rmin in zeros(S, C):
        say(f"     {k}: zero edge-years {z} ({100 * z / (E * 10):.1f}%), edges zero in all years {allz}, min REST {rmin:,.0f}")
# QV: the largest share of the WORLD total per member state over the 18 chapters without 55 (chapter-years with a
# published WORLD total and no hidden partner), and the gap in which the 1 per cent threshold falls
T18 = [k for k in TCLF if k != "55"]
say("\nlargest QV share of the WORLD total, 2016-2025, 18 chapters without 55 (chapter-years with WORLD published and no QY/QX):")
mx = {}
for (i, k, t), q in qv.items():
    if k in T18 and t in W and world.get((i, k, t), 0) > 0 and not hidden.get((i, k, t), 0) > 0:
        sh = q / world[(i, k, t)]
        if sh > mx.get(i, (0,))[0]: mx[i] = (sh, k, t)
for i in sorted(mx, key=lambda i: -mx[i][0]):
    say(f"  {i}: {100 * mx[i][0]:.4f} per cent (chapter {mx[i][1]}, {mx[i][2]})")
S18 = best[18][2]
inside = [100 * mx[i][0] for i in S18 if i in mx]
# member states that meet the WORLD and QY/QX conditions in all 18 chapters and fail on QV alone
S0 = [i for i in EU27 if all(all((i, k, t) in world for t in W) and not any(hidden.get((i, k, t), 0) > 0 for t in W) for k in T18)]
fail = {i: 100 * mx[i][0] for i in S0 if i not in S18}
say(f"  in the 18-chapter set ({len(S18)} states) the largest share is {max(inside):.4f} per cent; the member states that fail only on QV: "
    + ", ".join(f"{i} {v:.4f}" for i, v in sorted(fail.items(), key=lambda kv: -kv[1])))
say(f"  any threshold between {max(inside):.4f} and {min(fail.values()):.4f} per cent gives the same 18-chapter set")
open(os.path.join(here, "selection_result.txt"), "w", encoding="utf-8").write("\n".join(out) + "\n")
print("\n".join(out))
