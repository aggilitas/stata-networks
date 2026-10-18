"""Annual real cost of bank credit to non-financial corporations, per country.

i : ECB MIR, revolving loans and overdrafts, new business, NFCs, annualised agreed
    rate, in the national currency of the year (euro members EUR; BG BGN until
    2025; HR HRK until 2022, EUR from 2023), annual mean of the twelve months.
pi: Eurostat sts_inpp_a, producer prices, manufacturing (NACE C), unadjusted,
    percentage change on the previous year.
A = (1 + i/100) / (1 + pi/100), the gross real factor; the attribute edge value
is ln(A_j / A_i). Writes real_credit_cost.csv and real_credit_cost_flags.txt."""
import csv, io, json, itertools, os
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here)
C = "BE BG DE DK EE ES FR GR HR HU IE IT LT LU LV PL PT RO SE SI".split()
YA = range(2015, 2026)
NAT = {"BG": "BGN", "DK": "DKK", "HU": "HUF", "PL": "PLN", "RO": "RON", "SE": "SEK"}
def cur(c, t):
    if c == "HR": return "HRK" if t <= 2022 else "EUR"
    if c == "BG": return "BGN" if t <= 2025 else "EUR"
    return NAT.get(c, "EUR")
j = json.load(open(os.path.join(root, "data", "eurostat", "sts_inpp_a_C_eu27.json"), encoding="utf-8"))
ids = j["id"]; cats = [sorted(j["dimension"][d]["category"]["index"].items(), key=lambda kv: kv[1]) for d in ids]
ppi = {}
for flat, combo in enumerate(itertools.product(*cats)):
    k = dict(zip(ids, (c[0] for c in combo)))
    if k["unit"] != "PCH_SM": continue
    v = j.get("value", {}).get(str(flat)); st = j.get("status", {}).get(str(flat))
    ppi[(k["geo"].replace("EL", "GR"), int(k["time"]))] = (v, st)
rows, notes = [], []
for c in C:
    m = {}
    for r in csv.DictReader(io.StringIO(open(os.path.join(root, "data", "ecb_mir", f"MIR_A2Z_{c}.csv"), encoding="utf-8").read())):
        key = r["KEY"].split(".")
        if r["OBS_VALUE"] in ("", "NaN"): continue
        m[(key[9], r["TIME_PERIOD"])] = (float(r["OBS_VALUE"]), r.get("OBS_STATUS", ""))
    for t in YA:
        cu = cur(c, t)
        vals = [m.get((cu, f"{t}-{mm:02d}")) for mm in range(1, 13)]
        assert all(v is not None for v in vals), (c, t, cu, [mm for mm, v in zip(range(1, 13), vals) if v is None])
        i = sum(v[0] for v in vals) / 12
        st = sorted({v[1] for v in vals if v[1] not in ("", "A")})
        p, pst = ppi[(c, t)]
        assert p is not None, (c, t)
        A = (1 + i / 100) / (1 + p / 100)
        assert A > 0
        rows.append([c, t, cu, round(i, 6), p, A])
        if st or pst: notes.append(f"{c} {t}: MIR status {st or '-'}, PPI flag {pst or '-'}")
with open(os.path.join(here, "real_credit_cost.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["country", "year", "currency", "loan_rate", "ppi_change", "real_gross"])
    for r in rows: w.writerow(r[:5] + [repr(r[5])])
open(os.path.join(here, "real_credit_cost_flags.txt"), "w", encoding="utf-8").write("\n".join(notes) + "\n")
print(len(rows), "rows;", len(notes), "flag notes")
for c in ("DE", "HU", "EE", "BG", "HR"):
    print(c, " ".join(f"{t}:{i:.2f}/{p:+.1f}->{A:.3f}" for cc, t, cu, i, p, A in rows if cc == c and t in (2016, 2019, 2022, 2025)))
print("min A", min(r[5] for r in rows), "max A", max(r[5] for r in rows))
