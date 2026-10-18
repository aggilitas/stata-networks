"""Synthetic study of section 5 and the numerical examples of section 4 (Propositions 4-6, Table 3, Figure 1).

Seed: numpy default_rng(7); the draws are made in the order of this file, so the order must be kept (the draw of
the node attribute below is used by no result but moves the stream of the later draws).
1. Concentration (Proposition 4): symbolic check with sympy of the quadratic term that makes the concentration of
   destination shares non-constant along a direction of the outside flows.
2. Non-representability (Proposition 5): two systems on the nodes i, j, k1, k2, k3 with the same flows inside
   S = {i, j} and the same outside flows of the sources, differing only by the edge k2 -> k3; outgoing closeness
   of i, betweenness of j and PageRank of i and j. Unit weights; closeness with the distance 1 per edge,
   normalised for outgoing reachability; networkx betweenness and PageRank (damping 0.85) with weight "w".
   Proposition 6: the first system with a further unit flow on k3 -> k1 against the second system; the block sum
   of the two outside pairs is the same.
3. Nested boundaries (Table 3, Figure 1): 120 nodes, positions uniform on the unit square, node size lognormal
   with log-mean 0 and log-standard deviation 0.8; flow W_ab = size_a size_b exp(-d_ab / 0.25), the 10 strongest
   out-links of every node kept; edge distance 1 / flow for closeness (on the reversed graph) and betweenness;
   PageRank with weight = flow. Node attribute lognormal(0, 1); subgroup composition Dirichlet(1, 1, 1) times
   size, G = 3. Twenty reference nodes, always inside S; S grows by nested steps of 20 nodes. Errors are mean
   absolute relative errors: the flow share and the interaction over the positive-flow reference edges,
   betweenness over the reference nodes with positive betweenness in the full system (both counts are printed
   under "error_sample").
4. Fixed regression subnet inside a changing construction set: the retained weights of the nodes present in every
   period are the same whether the nodes that enter and leave are represented individually or folded into REST.
Writes figure1_boundary.png (300 dpi), figure1_boundary.pdf and synthetic_results.json next to this file, and
prints the results. Requires numpy, networkx, sympy and matplotlib."""
import numpy as np, networkx as nx, sympy as sp, json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

rng = np.random.default_rng(7)
out = {}

# ---------- 1. Herfindahl lower bound: symbolic check of the two cases ----------
t, s = sp.symbols("t s", positive=True)
m = 3
v = sp.symbols("v1:%d" % (m + 1), positive=True)
h = sp.symbols("h1:%d" % (m + 1), real=True)
Cu = sp.symbols("C_u", positive=True)                      # observed constant: sum of squared S-edges
num = Cu + sum((v[k] + t * h[k]) ** 2 for k in range(m))
den = (s + sum(v) + t * sum(h)) ** 2
phi = num / den
# constancy would need num - c*den == 0 identically in t for c = phi(0)
c = phi.subs(t, 0)
poly = sp.Poly(sp.expand(num - c * den), t)
lead = sp.simplify(poly.coeff_monomial(t ** 2))
# leading coefficient: |h|^2 - c*(1'h)^2 ; zero only on a measure-zero set of v
target = sum(hk**2 for hk in h) - c*sum(h)**2
out["herfindahl_t2_coeff_matches_formula"] = bool(sp.simplify(lead - target) == 0)
out["herfindahl_t2_coeff_example"] = float(lead.subs({s:1, v[0]:1, v[1]:2, v[2]:3, h[0]:1, h[1]:-1, h[2]:0}))

# ---------- 2. Non-representability: same (u,v), different outside topology ----------
def build(extra):
    G = nx.DiGraph()
    for a,b in [("i","j"),("j","i"),("i","k1"),("k1","i"),("j","k2"),("k2","j"),("k3","i")]:
        G.add_edge(a,b,w=1.0)
    for a,b in extra: G.add_edge(a,b,w=1.0)
    return G
G1 = build([]); G2 = build([("k2","k3")])          # only an outside-outside edge differs
# u (S-internal flows) and v_i=(f_ik1,f_ik2,f_ik3)=(1,0,0), v_j=(0,1,0) are identical in G1 and G2
def out_closeness(G,node):
    L = nx.single_source_dijkstra_path_length(G,node,weight="w"); L.pop(node)
    n=G.number_of_nodes(); r=len(L)
    return 0.0 if r==0 else (r/(n-1))*(r/sum(L.values()))
out["nonrep_closeness_i"] = [out_closeness(G1,"i"), out_closeness(G2,"i")]
out["nonrep_betweenness_j"] = [nx.betweenness_centrality(G1,weight="w")["j"], nx.betweenness_centrality(G2,weight="w")["j"]]
out["nonrep_pagerank_i"] = [nx.pagerank(G1,weight="w")["i"], nx.pagerank(G2,weight="w")["i"]]
out["nonrep_pagerank_j"] = [nx.pagerank(G1,weight="w")["j"], nx.pagerank(G2,weight="w")["j"]]
# Proposition 6: A sums the flows on (k2, k3) and (k3, k1) and keeps every other coordinate; v-bar = the first
# system with a unit flow on (k3, k1), v-bar' = the second system; the flows within S and the block sum agree
G3 = build([("k3", "k1")])
out["prop6_closeness_i"] = [out_closeness(G3, "i"), out_closeness(G2, "i")]
out["prop6_betweenness_j"] = [nx.betweenness_centrality(G3, weight="w")["j"], nx.betweenness_centrality(G2, weight="w")["j"]]
out["prop6_nodes"] = [G3.number_of_nodes(), G2.number_of_nodes()]

# ---------- 3. Nested-boundary consequence experiment ----------
n = 120
pos = rng.uniform(0, 1, (n, 2))
size = rng.lognormal(0, 0.8, n)
d = np.linalg.norm(pos[:, None, :] - pos[None, :, :], axis=2)
W = size[:, None] * size[None, :] * np.exp(-d / 0.25)
np.fill_diagonal(W, 0)
# sparsify: keep the 10 strongest out-links per node so path measures are informative
F = np.zeros_like(W)
for k in range(n):
    keep = np.argsort(W[k])[-10:]
    F[k, keep] = W[k, keep]
G_full = nx.DiGraph()
for a in range(n):
    for b in range(n):
        if F[a, b] > 0: G_full.add_edge(a, b, w=F[a, b], dist=1.0 / F[a, b])
attr = rng.lognormal(0, 1, n)                     # node attribute for the log-ratio channel
comp = rng.dirichlet(np.ones(3), n) * size[:, None]  # subgroup composition N_kX, G=3

order = rng.permutation(n)
ref = order[:20]                                   # reference nodes, always inside S
edges_ref = [(a, b) for a in ref for b in ref if a != b and F[a, b] > 0]
def full_measures():
    tot = F.sum(1)
    share = {(a, b): F[a, b] / tot[a] for (a, b) in edges_ref}
    herf = {a: float(((F[a] / tot[a]) ** 2).sum()) for a in ref}
    inter = {}
    for (a, b) in edges_ref:
        val = 0.0
        for X in range(3):
            denom = comp[:, X].sum() - comp[a, X]
            val += (comp[a, X] / comp[a].sum()) * (comp[b, X] / denom)
        inter[(a, b)] = val
    clo = nx.closeness_centrality(G_full.reverse(), distance="dist")
    bet = nx.betweenness_centrality(G_full, weight="dist")
    pr = nx.pagerank(G_full, weight="w")
    return share, herf, inter, {a: clo[a] for a in ref}, {a: bet[a] for a in ref}, {a: pr[a] for a in ref}
share_f, herf_f, inter_f, clo_f, bet_f, pr_f = full_measures()
out["error_sample"] = {"reference_nodes": len(ref), "positive_flow_reference_edges": len(edges_ref),
                       "reference_nodes_with_positive_betweenness": sum(1 for a in ref if bet_f[a] != 0)}

def mare(est, tru):
    vals = [abs(est[k] - tru[k]) / abs(tru[k]) for k in tru if tru[k] != 0 and np.isfinite(est[k])]
    return float(np.mean(vals))

rows = []
for r in [20, 40, 60, 80, 100, 120]:
    Sset = set(order[:r].tolist())
    Sidx = np.array(sorted(Sset))
    tot_world = F.sum(1)                          # aggregate over N: available in the admissible regime
    tot_S = F[:, Sidx].sum(1)                     # aggregate over S only: inadmissible regime
    # class E computed from S edges + world totals
    share_adm = {(a, b): F[a, b] / tot_world[a] for (a, b) in edges_ref}
    inter_adm = {}
    for (a, b) in edges_ref:
        val = 0.0
        for X in range(3):
            denom = comp[Sidx, X].sum() - comp[a, X] + (comp[:, X].sum() - comp[Sidx, X].sum())  # S part + outside total
            val += (comp[a, X] / comp[a].sum()) * (comp[b, X] / denom)
        inter_adm[(a, b)] = val
    # inadmissible regime for the share (aggregate over S)
    share_inadm = {(a, b): F[a, b] / tot_S[a] for (a, b) in edges_ref}
    # Proposition 4 object: concentration of all destination shares with the WORLD denominator (known).
    # From S edges + world total the analyst knows the S shares exactly and the outside mass 1-s, not its allocation:
    # H lies in [sum_S w^2 + (1-s)^2/m, sum_S w^2 + (1-s)^2]; report the uniform-spread point (lower bound) and the interval width.
    m_out = n - len(Sidx)
    herf_part, herf_width = {}, {}
    for a in ref:
        w_S = F[a, Sidx] / tot_world[a]; s_S = w_S.sum(); base = float((w_S ** 2).sum()); rest = 1.0 - s_S
        lo = base + (rest ** 2 / m_out if m_out > 0 else 0.0); hi = base + rest ** 2
        herf_part[a] = lo; herf_width[a] = (hi - lo) / herf_f[a]
    # path / spectral measures on the S-induced subgraph
    Gs = G_full.subgraph(Sset).copy()
    clo = nx.closeness_centrality(Gs.reverse(), distance="dist")
    bet = nx.betweenness_centrality(Gs, weight="dist")
    pr = nx.pagerank(Gs, weight="w")
    rows.append({
        "coverage": r / n,
        "share_admissible": mare(share_adm, share_f),
        "interaction_admissible": mare(inter_adm, inter_f),
        "share_inadmissible": mare(share_inadm, share_f),
        "herfindahl_partial": mare(herf_part, herf_f),
        "herfindahl_interval_width": float(np.mean(list(herf_width.values()))),
        "closeness_subgraph": mare({a: clo[a] for a in ref}, clo_f),
        "betweenness_subgraph": mare({a: bet[a] for a in ref}, bet_f),
        "pagerank_subgraph": mare({a: pr[a] for a in ref}, pr_f),
    })
out["boundary_rows"] = rows

# ---------- Figure 1: nested-boundary errors (redrawn) ----------
# Okabe-Ito colours, a distinct marker and line style per series, legend below the axes.
import os
HERE = os.path.dirname(os.path.abspath(__file__))
plt.rcParams.update({
    "font.size": 9, "axes.labelsize": 9.5, "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
    "legend.fontsize": 8, "pdf.fonttype": 42, "ps.fonttype": 42,
})
OKABE_ITO = {"black": "#000000", "orange": "#E69F00", "sky_blue": "#56B4E9", "bluish_green": "#009E73",
             "blue": "#0072B2", "vermillion": "#D55E00"}
fig, ax = plt.subplots(figsize=(6.5, 4.7), layout="constrained")
cov = [row["coverage"] for row in rows]
# key: (legend label, colour, line style, marker, marker size, filled marker, drawing order)
styles = {
    "share_admissible": ("Flow weight, aggregate over $N$ (exact class)",
                         OKABE_ITO["black"], "-", "s", 4.5, True, 6),
    "interaction_admissible": ("Interaction weight, subgroup totals over $N$ (exact class)",
                               OKABE_ITO["black"], (0, (4, 2)), "o", 9.0, False, 7),
    "share_inadmissible": ("Flow weight, aggregate over $S_r$ (inadmissible regime)",
                           OKABE_ITO["vermillion"], "-", "^", 5.5, True, 4),
    "herfindahl_partial": ("Concentration of target shares,\nequal-allocation point ($q^*=m$)",
                           OKABE_ITO["orange"], (0, (6, 1.5, 1.5, 1.5)), "v", 6.5, False, 3.5),
    "closeness_subgraph": ("Closeness on $S_r$-subgraph ($q^*=\\infty$)",
                           OKABE_ITO["blue"], (0, (5, 1.5, 1, 1.5, 1, 1.5)), "D", 4.5, True, 2.5),
    "betweenness_subgraph": ("Betweenness on $S_r$-subgraph ($q^*=\\infty$)",
                             OKABE_ITO["sky_blue"], (0, (4, 2)), "X", 7.0, True, 3.2),
    "pagerank_subgraph": ("PageRank on $S_r$-subgraph ($q^*=\\infty$)",
                          OKABE_ITO["bluish_green"], (0, (1, 1.3)), "P", 7.5, True, 3),
}
handles = []
for key, (lab, col, ls, mk, ms, filled, z) in styles.items():
    (line,) = ax.plot(cov, [row[key] for row in rows], color=col, linestyle=ls, linewidth=1.5,
                      marker=mk, markersize=ms, markerfacecolor=col if filled else "none",
                      markeredgecolor=col, markeredgewidth=1.2 if filled else 1.4, label=lab, zorder=z)
    handles.append(line)
ax.set_xlabel("Observed share of nodes in the ambient system, $|S_r|/|N|$")
ax.set_ylabel("Mean absolute relative error\n(reference nodes/edges)")
ax.set_yscale("symlog", linthresh=1e-3)
fig.legend(handles=handles, loc="outside lower center", ncol=2, frameon=False,
           handlelength=3.4, columnspacing=1.6, labelspacing=0.55)
fig.savefig(os.path.join(HERE, "figure1_boundary.png"), dpi=300)
fig.savefig(os.path.join(HERE, "figure1_boundary.pdf"), metadata={"CreationDate": None})

# ---------- 4. Fixed regression subnet inside a changing construction set ----------
# R = the 37 nodes present in every period (fixed regression subnet, complete mesh, balanced);
# C_t = 60 nodes with four entries and four exits per period (individually represented in construction);
# N = the whole 120-node system, known only through source totals. Retained R x R weights must be
# identical whether the C_t \ R nodes are represented individually or folded into the outside aggregate.
T = 10
present = {t: set(order[:60].tolist()) for t in range(T)}
pool = order[60:].tolist()
for t in range(1, T):
    present[t] = set(present[t - 1])
    leave = rng.choice(sorted(present[t] - set(ref.tolist())), 4, replace=False)
    enter = rng.choice([k for k in pool if k not in present[t]], 4, replace=False)
    present[t] -= set(leave.tolist()); present[t] |= set(enter.tolist())
Rset = sorted(set.intersection(*present.values()))
tot = F.sum(1)
maxdiff = 0.0
for t in range(T):
    Ct = sorted(present[t])
    for i in Rset:
        den_node = F[i, [k for k in Ct if k != i]].sum() + (tot[i] - F[i, [k for k in Ct if k != i]].sum())   # C_t edges + REST
        den_fold = F[i, [k for k in Rset if k != i]].sum() + (tot[i] - F[i, [k for k in Rset if k != i]].sum()) # R edges + REST
        for j in Rset:
            if j == i: continue
            maxdiff = max(maxdiff, abs(F[i, j] / den_node - F[i, j] / den_fold))
assert maxdiff < 1e-12
out["fixed_subnet"] = {"R_nodes": len(Rset), "R_edges_per_period": len(Rset) * (len(Rset) - 1),
                       "C_t_nodes": 60, "C_t_edges_per_period": 60 * 59, "periods": T,
                       "entries_exits_per_period": 4, "max_abs_diff_node_vs_folded": maxdiff}
json.dump(out, open(os.path.join(HERE, "synthetic_results.json"), "w", encoding="utf-8"), indent=1)
print(json.dumps({k: out[k] for k in out if k != "boundary_rows"}, indent=1))
for row in rows:
    print({k: (round(val, 4) if isinstance(val, float) else val) for k, val in row.items()})
