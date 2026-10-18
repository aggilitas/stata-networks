"""Input files for the estimation do-file on the eighteen-country subnet, one file per network.

R = the eighteen member states observed in all 18 TCLF chapters (1_selection/select_subnet.py;
chapter 55 is out because Denmark and Italy withhold the partner; Ireland and Luxembourg record
intra-EU exports without a partner (QV) above 1 per cent of their world total) with complete
attributes: BE BG DE DK EE ES FR GR HR HU IT LT LV PL PT RO SE SI. 2016-2025.
Trade: Comext DS-045409, exporter-declared exports only; an absent partner cell is zero.
  networks/export_<hs>.csv  (i, j) exports of i to j; (i, REST) world exports of i
                            minus exports of i to R; read with direction(outflow);
                            one declaration, so the value is in both columns.
Attributes (R x R rows, 2015-2025, source_value = A_i, target_value = A_j):
  networks/attr_prod.csv  manufacturing (NACE C) real value added per hour worked, sum
                          of the four quarters (2_attributes/manufacturing_productivity.py)
  networks/attr_fin.csv   real cost of bank credit to non-financial corporations,
                          (1 + i/100) / (1 + pi/100) (2_attributes/real_credit_cost.py)
  networks/attr_elec.csv  electricity price, non-household, EUR/kWh excl. VAT,
                          band MWH2000-19999, (S1 + S2) / 2
Also writes check_weights.csv (weights by the direct formula, for the do-file check) and
input_notes.txt (zero cells and data flags)."""
import csv, gzip, itertools, json, os
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here)
eus = os.path.join(root, "data", "eurostat")
out = os.path.join(here, "networks"); os.makedirs(out, exist_ok=True)
R = "BE BG DE DK EE ES FR GR HR HU IT LT LV PL PT RO SE SI".split()
HS = "41 42 43 50 51 52 53 54 56 57 58 59 60 61 62 63 64 65".split()
Y = list(range(2016, 2026)); YA = list(range(2015, 2026))
BAND = "MWH2000-19999"; HIDE = ("QY", "QX"); QV_MAX = 0.01
x, world, hidden, qv = {}, {}, {}, {}
for rep in R:
    for r in csv.DictReader(gzip.open(os.path.join(root, "data", "comext_exports", f"export_{rep}.csv.gz"), "rt", encoding="utf-8")):
        t, k, p = int(r["year"]), r["product"], r["partner"]
        if t not in Y or k not in HS or r["value_eur"] in ("", None): continue
        v = float(r["value_eur"])
        if p == "WORLD": world[(rep, k, t)] = v
        elif p in HIDE: hidden[(rep, k, t)] = hidden.get((rep, k, t), 0) + v
        elif p == "QV": qv[(rep, k, t)] = qv.get((rep, k, t), 0) + v
        elif p in R and p != rep: x[(rep, p, k, t)] = v
def wcsv(path, header, data):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(header)
        for r in data: w.writerow([repr(v) if isinstance(v, float) else v for v in r])
HEAD = ["year", "source", "target", "source_value", "target_value"]
notes, chk = [], []
for k in HS:
    rows, zeros = [], 0
    for t in Y:
        for i in R:
            assert (i, k, t) in world and hidden.get((i, k, t), 0) == 0, (i, k, t)
            assert world[(i, k, t)] == 0 or qv.get((i, k, t), 0) < QV_MAX * world[(i, k, t)], (i, k, t)
            s = 0.0
            for j in R:
                if j == i: continue
                a = x.get((i, j, k, t), 0.0); assert a >= 0
                zeros += a == 0
                rows.append([t, i, j, a, a]); s += a
                chk.append([t, k, i, j, a / world[(i, k, t)] if world[(i, k, t)] > 0 else 0.0])
            rest = world[(i, k, t)] - s; assert rest >= 0, (i, k, t, rest)
            rows.append([t, i, "REST", rest, rest])
    wcsv(os.path.join(out, f"export_{k}.csv"), HEAD, rows)
    allz = sum(1 for i in R for j in R if i != j and all(x.get((i, j, k, t), 0) == 0 for t in Y))
    notes.append(f"export_{k}: {zeros} zero edge-years of {len(R) * (len(R) - 1) * 10}; {allz} edges zero in all years")
wcsv(os.path.join(here, "check_weights.csv"), ["year", "hs", "source", "target", "export_direct"], chk)
def js(ds):
    j = json.load(open(os.path.join(eus, ds + "_eu27.json"), encoding="utf-8"))
    ids = j["id"]; cats = [sorted(j["dimension"][d]["category"]["index"].items(), key=lambda kv: kv[1]) for d in ids]
    res = {}
    for flat, combo in enumerate(itertools.product(*cats)):
        v = j.get("value", {}).get(str(flat)); st = j.get("status", {}).get(str(flat))
        key = dict(zip(ids, (c[0] for c in combo)))
        if v is not None or st is not None: res[tuple(sorted(key.items()))] = (v, st)
    return res
def write_attr(series, name):
    data = [[t, i, j, series[(i, t)], series[(j, t)]] for t in YA for i in R for j in R if i != j]
    wcsv(os.path.join(out, name), HEAD, data)
def attr(ds, sel, fn, name, label):
    d = js(ds); vals = {}
    for key, (v, st) in d.items():
        k = dict(key)
        if any(k.get(a) != b for a, b in sel.items()): continue
        g = k["geo"].replace("EL", "GR")
        if g in R: vals.setdefault(g, {})[k["time"]] = (v, st)
    series = {}
    for g in R:
        for t in YA:
            v, flag = fn(vals[g], t)
            assert v is not None and v > 0, (label, g, t, v)
            series[(g, t)] = v
            if flag: notes.append(f"{label} {g} {t}: {flag}")
    write_attr(series, name)
def semi(vals, t):
    a, sa = vals.get(f"{t}-S1", (None, None)); b, sb = vals.get(f"{t}-S2", (None, None))
    fl = ", ".join(f"{s} {f}" for s, f in (("S1", sa), ("S2", sb)) if f)
    return (None if a is None or b is None else (a + b) / 2), (fl or None)
P = {}
for r in csv.DictReader(open(os.path.join(root, "2_attributes", "manufacturing_productivity.csv"), encoding="utf-8")):
    P[(r["country"].replace("EL", "GR"), int(r["year"]))] = float(r["prod_eur_per_hour"])
assert all((g, t) in P and P[(g, t)] > 0 for g in R for t in YA)
write_attr(P, "attr_prod.csv")
attr("nrg_pc_205", {"nrg_cons": BAND, "tax": "X_VAT", "currency": "EUR", "unit": "KWH"}, semi, "attr_elec.csv", f"electricity {BAND}")
fin = {}
for r in csv.DictReader(open(os.path.join(root, "2_attributes", "real_credit_cost.csv"), encoding="utf-8")):
    fin[(r["country"], int(r["year"]))] = float(r["real_gross"])
assert all((g, t) in fin and fin[(g, t)] > 0 for g in R for t in YA)
write_attr(fin, "attr_fin.csv")
notes += ["finance: " + l.strip() for l in open(os.path.join(root, "2_attributes", "real_credit_cost_flags.txt"), encoding="utf-8") if l.strip()]
open(os.path.join(here, "input_notes.txt"), "w", encoding="utf-8").write(
    "Zero cells in the trade inputs and flags in the attribute inputs, eighteen-country subnet\n" + "\n".join(notes) + "\n")
print("network files", len(HS), "| check rows", len(chk))
print("\n".join(n for n in notes if n.startswith("export_")))
