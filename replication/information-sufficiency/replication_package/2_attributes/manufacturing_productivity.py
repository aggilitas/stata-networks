"""Annual manufacturing labour productivity from the quarterly accounts:
P(i,t) = sum of the four quarters of real GVA / sum of the four quarters of
hours worked (euro per hour), NACE C, 2015-2025, one source for every year.
Checks completeness and flags, and compares the growth of P with the annual
industry accounts (nama_10_a64 / nama_10_a64_e) where those exist.
Writes manufacturing_productivity.csv and manufacturing_productivity_check.txt."""
import json, itertools, os, math, csv
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here)
R20 = "BE BG DE DK EE EL ES FR HR HU IE IT LT LU LV PL PT RO SE SI".split()
YA = range(2015, 2026)
def load(fn, key_time="time"):
    j = json.load(open(os.path.join(root, "data", "eurostat", fn), encoding="utf-8"))
    ids = j["id"]; cats = [sorted(j["dimension"][d]["category"]["index"].items(), key=lambda kv: kv[1]) for d in ids]
    out = {}
    for flat, combo in enumerate(itertools.product(*cats)):
        k = dict(zip(ids, (c[0] for c in combo)))
        v = j.get("value", {}).get(str(flat)); st = j.get("status", {}).get(str(flat))
        out[(k["geo"], k.get("nace_r2", "C"), k["time"])] = (v, st)
    return out
GQ, HQ = load("namq_10_a10_C_r20.json"), load("namq_10_a10_e_C_r20.json")
GA, HA = load("nama_10_a64_eu27.json"), load("nama_10_a64_e_eu27.json")
lines, rows = [], []
for g in R20:
    miss, flags, P = [], set(), {}
    for t in YA:
        qs = [f"{t}-Q{q}" for q in range(1, 5)]
        gv = [GQ.get((g, "C", q), (None, None)) for q in qs]; hv = [HQ.get((g, "C", q), (None, None)) for q in qs]
        m = [q for q, a, b in zip(qs, gv, hv) if a[0] is None or b[0] is None]
        miss += m
        flags |= {s for s in [a[1] for a in gv] + [b[1] for b in hv] if s}
        if not m: P[t] = 1000 * sum(a[0] for a in gv) / sum(b[0] for b in hv)
    comp = []
    for t in range(2016, 2026):
        ga, ha, ga0, ha0 = (GA.get((g, "C", str(t)), (None,))[0], HA.get((g, "C", str(t)), (None,))[0],
                            GA.get((g, "C", str(t - 1)), (None,))[0], HA.get((g, "C", str(t - 1)), (None,))[0])
        if None in (ga, ha, ga0, ha0) or t not in P or t - 1 not in P: continue
        comp.append((math.log(P[t] / P[t - 1]), math.log((ga / ha) / (ga0 / ha0))))
    if comp:
        d = [abs(a - b) for a, b in comp]
        cmp_txt = f"growth vs annual accounts: {len(comp)} years, max |diff| {max(d):.4f}, mean {sum(d)/len(d):.4f}"
    else:
        cmp_txt = "no annual comparison"
    lines.append(f"{g}: missing quarters {miss or '-'} | flags {sorted(flags) or '-'} | {cmp_txt}")
    for t in YA:
        if t in P: rows.append([g, t, repr(P[t])])
with open(os.path.join(here, "manufacturing_productivity.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["country", "year", "prod_eur_per_hour"]); w.writerows(rows)
open(os.path.join(here, "manufacturing_productivity_check.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("\n".join(lines)); print(len(rows), "country-years written")
