"""
Builds the example datasets for netcalc.

Layout, multi-subnet:

    year feature source target source_size source_value
                               target_size target_value

    size   the weight of the subnet at that node, a count
    value  the quantity being measured on that edge or node

Layout, single-subnet:

    year source target source_value target_value

The flow files are consistent with each other: the single-subnet flow
between two nodes is the sum of the subnet flows between them, so the
same network can be read at either resolution. The attribute files are
consistent in the same sense: the node level is the size-weighted mean
of its subnet levels.
"""

import csv
import random

NODES = ["van", "kars", "bolu", "rize", "ordu"]
BIRTHPLACES = ["van", "kars", "bolu", "rize", "ordu"]
YEARS = [2018, 2019, 2020]

random.seed(20260912)

# population of each birthplace group in each node and year
size = {}
for y in YEARS:
    for b in BIRTHPLACES:
        for n in NODES:
            base = 40000 if b == n else random.randint(1500, 45000)
            size[(y, b, n)] = base + (y - 2018) * random.randint(50, 900)

# years of schooling of each birthplace group in each node and year
schooling = {}
for y in YEARS:
    for b in BIRTHPLACES:
        for n in NODES:
            schooling[(y, b, n)] = round(random.uniform(5.0, 13.0), 2)

# migrants of each birthplace group along each edge and year
flow = {}
for y in YEARS:
    for b in BIRTHPLACES:
        for i in NODES:
            for j in NODES:
                if i != j:
                    flow[(y, b, i, j)] = random.randint(20, 3000)

MULTI = ["year", "feature", "source", "target",
         "source_size", "source_value", "target_size", "target_value"]
SINGLE = ["year", "source", "target", "source_value", "target_value"]


def write(name, header, rows):
    with open(name, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    print("%-32s %d rows" % (name, len(rows)))


# --- interaction: the measured quantity is the group itself ---------
rows = []
for y in YEARS:
    for b in BIRTHPLACES:
        for i in NODES:
            for j in NODES:
                if i == j:
                    continue
                s, t = size[(y, b, i)], size[(y, b, j)]
                rows.append([y, b, i, j, s, s, t, t])
write("test_interaction_multi.csv", MULTI, rows)

# --- flow: the measured quantity travels along the edge -------------
rows = []
for y in YEARS:
    for b in BIRTHPLACES:
        for i in NODES:
            for j in NODES:
                if i == j:
                    continue
                rows.append([y, b, i, j,
                             size[(y, b, i)], flow[(y, b, i, j)],
                             size[(y, b, j)], flow[(y, b, j, i)]])
write("test_flow_multi.csv", MULTI, rows)

rows = []
for y in YEARS:
    for i in NODES:
        for j in NODES:
            if i == j:
                continue
            out = sum(flow[(y, b, i, j)] for b in BIRTHPLACES)
            back = sum(flow[(y, b, j, i)] for b in BIRTHPLACES)
            rows.append([y, i, j, out, back])
write("test_flow_single.csv", SINGLE, rows)

# --- attribute: the measured quantity describes the node ------------
rows = []
for y in YEARS:
    for b in BIRTHPLACES:
        for i in NODES:
            for j in NODES:
                if i == j:
                    continue
                rows.append([y, b, i, j,
                             size[(y, b, i)], schooling[(y, b, i)],
                             size[(y, b, j)], schooling[(y, b, j)]])
write("test_attribute_multi.csv", MULTI, rows)


def node_level(y, n):
    num = sum(size[(y, b, n)] * schooling[(y, b, n)] for b in BIRTHPLACES)
    den = sum(size[(y, b, n)] for b in BIRTHPLACES)
    return round(num / den, 4)


rows = []
for y in YEARS:
    for i in NODES:
        for j in NODES:
            if i == j:
                continue
            rows.append([y, i, j, node_level(y, i), node_level(y, j)])
write("test_attribute_single.csv", SINGLE, rows)
