"""Country and chapter selection for the TCLF group under longer windows.

Same data and same observation rule as select_subnet.py; only the window changes.
Comext DS-045409, exporter-declared exports (data/comext_exports/export_XX.csv.gz,
1988-2025), the 19 TCLF chapters 41-43 and 50-65. Windows: s-2025 for every
start year s = 2006, ..., 2016 (2016-2025 is the window of select_subnet.py).

A country i is observed in chapter k over a window if, in every year of it:
  - its WORLD export total in k is published;
  - it reports nothing in k under QY or QX (partner not specified for
    commercial or military reasons);
  - its intra-EU exports recorded without a partner (QV) stay below 1 per cent
    of its WORLD total in k.
QV, QU, QR and QQ go to REST, as in select_subnet.py.

For each window the script reports
  (a) the countries observed in all 19 chapters;
  (b) the countries observed in the 18 chapters without 55;
  (c) the countries of the eighteen-country subnet that fail the rule, and in
      which of the 18 chapters;
  (d) the trade-off between chapters and countries, computed as in select_subnet.py
      (for every number n of chapters, the chapter subset whose fixed
      country set is largest; ties go to the first subset in the order of
      itertools.combinations, as in select_subnet.py);
  (e) the smallest REST_i = WORLD_i - sum_j x_ij over the set in (b).
It also lists, for the nine member states outside the subnet, the chapters
among the 18 in which they fail the rule in 2016-2025.
It does not run or modify select_subnet.py. Writes window_check_result.txt."""
import csv, gzip, os
from itertools import combinations

here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here)
longdir = os.path.join(root, "data", "comext_exports")
EU27 = "AT BE BG CY CZ DE DK EE ES FI FR GR HR HU IE IT LT LU LV MT NL PL PT RO SE SI SK".split()
TCLF = ["41", "42", "43"] + [str(c) for c in range(50, 66)]
T18 = [k for k in TCLF if k != "55"]
SUB18 = "BE BG DE DK EE ES FR GR HR HU IT LT LV PL PT RO SE SI".split()
OUT9 = [i for i in EU27 if i not in SUB18]
QV_MAX = 0.01
STARTS = range(2006, 2017)
END = 2025
HIDE = ("QY", "QX")
OTHER = ("QV", "QU", "QR", "QQ")
ACCESSION = {"AT": 1995, "FI": 1995, "SE": 1995, "CY": 2004, "CZ": 2004, "EE": 2004,
             "HU": 2004, "LT": 2004, "LV": 2004, "MT": 2004, "PL": 2004, "SI": 2004,
             "SK": 2004, "BG": 2007, "RO": 2007, "HR": 2013}

world, hidden, hidcode, hidv, other, cell, qv, neg = {}, {}, {}, {}, {}, {}, {}, 0
anyrow = set()
first_world = {}
for i in EU27:
    fw = {}
    for r in csv.DictReader(gzip.open(os.path.join(longdir, f"export_{i}.csv.gz"), "rt", encoding="utf-8")):
        k, t, p = r["product"], int(r["year"]), r["partner"]
        if k not in TCLF or r["value_eur"] in ("", None):
            continue
        v = float(r["value_eur"])
        if p == "WORLD":
            fw[k] = min(fw.get(k, t), t)
        if t < min(STARTS) or t > END:
            continue
        anyrow.add((i, k, t))
        if v < 0:
            neg += 1
        if p == "WORLD":
            world[(i, k, t)] = v
        elif p in HIDE:
            hidden[(i, k, t)] = hidden.get((i, k, t), 0) + v
            if v > 0:
                hidcode.setdefault((i, k, t), set()).add(p)
                hidv[(i, k, t, p)] = v
        elif p in OTHER:
            if p == "QV":
                qv[(i, k, t)] = qv.get((i, k, t), 0) + v
            if v > 0:
                other.setdefault((i, p), set()).add(t)
        elif p in EU27 and p != i:
            cell[(i, p, k, t)] = v
    first_world[i] = fw

out = []
say = lambda s="": out.append(s)


def observe(W):
    obs, why = {}, {}
    for i in EU27:
        for k in TCLF:
            miss = [t for t in W if (i, k, t) not in world]
            hid = [t for t in W if hidden.get((i, k, t), 0) > 0]
            qvy = [t for t in W if world.get((i, k, t), 0) > 0 and qv.get((i, k, t), 0) >= QV_MAX * world[(i, k, t)]]
            obs[(i, k)] = not miss and not hid and not qvy
            if not obs[(i, k)]:
                why[(i, k)] = (miss, hid, qvy)
    return obs, why


def reason(why, i, k, only=None, values=False):
    """only: restrict to these years; values: give the hidden value and its share of WORLD."""
    miss, hid, qvy = why[(i, k)]
    if only is not None:
        miss = [t for t in miss if t in only]
        hid = [t for t in hid if t in only]
        qvy = [t for t in qvy if t in only]
    s = []
    if miss:
        s.append("WORLD missing " + ",".join(str(t) for t in miss))
    if qvy:
        s.append("QV >= 1% " + ", ".join(f"{t}: {100 * qv[(i, k, t)] / world[(i, k, t)]:.2g}% of WORLD" for t in qvy))
    for code in HIDE:
        ys = [t for t in hid if code in hidcode.get((i, k, t), ())]
        if not ys:
            continue
        if values:
            s.append(code + " " + ", ".join(
                f"{t}: {hidv[(i, k, t, code)]:,.0f} EUR = {100 * hidv[(i, k, t, code)] / world[(i, k, t)]:.2g}% of WORLD"
                for t in ys))
        else:
            s.append(code + " " + ",".join(str(t) for t in ys))
    return "; ".join(s)


def fixed_set(obs, C):
    return [i for i in EU27 if all(obs[(i, k)] for k in C)]


def frontier(obs):
    """select_subnet.py's search, on bit masks: same order, same strict improvement."""
    bit = {i: 1 << n for n, i in enumerate(EU27)}
    mask = {k: sum(bit[i] for i in EU27 if obs[(i, k)]) for k in TCLF}
    full = (1 << len(EU27)) - 1
    pc = lambda x: bin(x).count("1")
    best = {}
    for n in range(1, len(TCLF) + 1):
        top = (0, None, 0)
        for C in combinations(TCLF, n):
            S = full
            for k in C:
                S &= mask[k]
                if pc(S) <= top[0]:
                    break
            c = pc(S)
            if c > top[0]:
                top = (c, C, S)
        best[n] = (top[0], top[1], [i for i in EU27 if top[2] & bit[i]])
    return best


def min_rest(S, C, W):
    worst = None
    for k in C:
        for i in S:
            for t in W:
                r = world[(i, k, t)] - sum(cell.get((i, j, k, t), 0) for j in S if j != i)
                if worst is None or r < worst[0]:
                    worst = (r, i, k, t)
    return worst


say("Country and chapter selection for TCLF under windows s-2025, s = 2006..2016")
say("Rule as in select_subnet.py: i observed in k if in every year WORLD is published, QY/QX are nil and QV < 1% of WORLD.")
say(f"negative values in the TCLF chapters, 2006-2025: {neg}")
say("")
say("Reporting coverage (first year with a WORLD export total, over the 19 chapters):")
for i in EU27:
    fy = sorted(set(first_world[i].values()))
    acc = ACCESSION.get(i, "founding or pre-1995")
    say(f"  {i}: WORLD from {fy[0] if len(fy) == 1 else fy}   EU accession {acc}")
say("All 27 reporters publish WORLD totals for the TCLF chapters from 2001 or earlier, so no")
say("window from 2006 on starts before a reporter's first year. Years before a country's")
say("accession are treated as the data show: the same two tests are applied to them, and")
say("their partner cells with the members are used as published.")
pre = sum(1 for (i, j, k, t), v in cell.items() if "HR" in (i, j) and i in SUB18 and j in SUB18
          and k in T18 and t <= 2012 and v > 0)
post = sum(1 for (i, j, k, t), v in cell.items() if "HR" in (i, j) and i in SUB18 and j in SUB18
           and k in T18 and t >= 2013 and v > 0)
say(f"  subnet cells with HR (either direction, 18 chapters) that are positive: 2006-2012 {pre} of"
    f" {7 * 34 * 18} ({100 * pre / (7 * 34 * 18):.0f}%), 2013-2025 {post} of {13 * 34 * 18}"
    f" ({100 * post / (13 * 34 * 18):.0f}%)")
say("Caveat: in pre-accession years, trade between the acceding country and the members was")
say("trade with third countries, whose confidential partner code is QZ; QZ is not in the")
say("local download (partners: EU27, WORLD, INT/EXT_EU27_2020, QY QV QX QU QR QQ), so it is")
say("not checked. This concerns HR in 2006-2013 and BG, RO in 2006 (and members' exports to")
say("them in those years). QX, the code without the intra/extra split, carries no TCLF value")
say("after 1992; every hidden-partner failure below is a QY entry.")
say("Years 2006-2025 in which a TCLF chapter carries a positive value under a code that goes to REST:")
for (i, p), ys in sorted(other.items()):
    say(f"  {i} {p}: {' '.join(str(t) for t in sorted(ys))}")
say("")

summary = []
detail = []
base = None
for s in STARTS:
    W = range(s, END + 1)
    obs, why = observe(W)
    S19 = fixed_set(obs, TCLF)
    S18 = fixed_set(obs, T18)
    sub_ok18 = [k for k in T18 if all(obs[(i, k)] for i in SUB18)]
    sub_ok19 = [k for k in TCLF if all(obs[(i, k)] for i in SUB18)]
    best = frontier(obs)
    n20 = max([n for n in best if best[n][0] >= 18] or [0])
    rmin = min_rest(S18, T18, W)
    if s == 2016:
        base = (S18, S19)
    summary.append((s, len(W), S19, S18, sub_ok18, sub_ok19, n20, best, rmin, obs, why))
    d = []
    d.append(f"=== window {s}-{END} ({len(W)} years) ===")
    d.append(f"observed in all 19 chapters: {len(S19)}  {' '.join(S19)}")
    d.append(f"observed in the 18 chapters without 55: {len(S18)}  {' '.join(S18)}")
    d.append(f"subnet of 18: all observed in {len(sub_ok18)} of the 18 chapters"
             + (f"; chapters lost: {' '.join(k for k in T18 if k not in sub_ok18)}; failing members:" if len(sub_ok18) < 18 else ""))
    for i in SUB18:
        bad = [k for k in T18 if not obs[(i, k)]]
        if bad:
            d.append(f"   {i}: " + " | ".join(f"{k} ({reason(why, i, k)})" for k in bad))
    d.append(f"chapter 55: " + ", ".join(f"{i} ({reason(why, i, '55')})" for i in EU27 if not obs[(i, '55')]))
    d.append(f"largest number of chapters with a fixed set of >= 18 countries: {n20}")
    d.append(f"smallest REST over the 18-chapter set: {rmin[0]:,.0f} ({rmin[1]}, chapter {rmin[2]}, {rmin[3]})")
    d.append("trade-off (as select_subnet.py): chapters -> largest fixed country set")
    for n in range(len(TCLF), 0, -1):
        c, C, S = best[n]
        left = [k for k in TCLF if k not in C] if C else TCLF
        d.append(f"  {n:2d} chapters: {c:2d} countries | left out: {' '.join(left) or '-'} | countries: {' '.join(S)}")
    d.append("")
    detail.append(d)

say("Summary (subnet = BE BG DE DK EE ES FR GR HR HU IT LT LV PL PT RO SE SI)")
say("A = countries observed in all 19 chapters; B = countries observed in the 18 chapters without 55;")
say("C = chapters of 18 (of 19) in which all 18 subnet countries are observed;")
say("D = largest number of chapters (of 19) with a fixed set of at least 18 countries.")
say("start  years   A    B    C (of 19)   D")
for s, ny, S19, S18, k18, k19, n20, *_ in summary:
    say(f" {s}   {ny:2d}   {len(S19):2d}   {len(S18):2d}   {len(k18):2d} ({len(k19):2d})     {n20:2d}")
say("")
say("Trade-off frontier (as select_subnet.py): largest fixed country set for n chapters, by window start")
say("  n   " + " ".join(f"{s}" for s in STARTS))
for n in range(len(TCLF), 0, -1):
    say(f" {n:2d}   " + " ".join(f"{summary[m][7][n][0]:4d}" for m in range(len(summary))))
say("")
say("Change against 2016-2025 in the 18-chapter set (who drops, where, why; only the added years can")
say("cause a drop, and each is listed with the value under QY or QV and its share of the WORLD total):")
S18b, S19b = base
for s, ny, S19, S18, k18, k19, n20, best, rmin, obs, why in summary:
    if s == 2016:
        continue
    drop = [i for i in S18b if i not in S18]
    gain = [i for i in S18 if i not in S18b]
    parts = []
    for i in drop:
        bad = [k for k in T18 if not obs[(i, k)]]
        parts.append(f"{i} [" + " | ".join(f"{k}: {reason(why, i, k, only=range(s, 2016), values=True)}" for k in bad) + "]")
    say(f"  {s}-{END}: {len(S18)} countries; drops {len(drop)}: " + ("; ".join(parts) or "-")
        + (f"; enters: {' '.join(gain)}" if gain else ""))
say("")
say("Member states outside the subnet, 2016-2025: chapters among the 18 (55 excluded) that fail the rule")
obs, why = observe(range(2016, END + 1))
for i in OUT9:
    bad = [k for k in T18 if not obs[(i, k)]]
    say(f"  {i}: {len(bad)} chapter{'s' if len(bad) != 1 else ''}: " + " | ".join(f"{k} ({reason(why, i, k)})" for k in bad)
        + (f"   [also 55: {reason(why, i, '55')}]" if not obs[(i, '55')] else ""))
    nodata = [(k, t) for k in T18 for t in why.get((i, k), ([], []))[0] if (i, k, t) not in anyrow]
    if nodata:
        say(f"      chapter-years with WORLD missing in which no value at all (no partner, no aggregate) is published: "
            + " ".join(f"{k}/{t}" for k, t in nodata))
say("")
for d in detail:
    out.extend(d)
open(os.path.join(here, "window_check_result.txt"), "w", encoding="utf-8").write("\n".join(out) + "\n")
print("\n".join(out))
