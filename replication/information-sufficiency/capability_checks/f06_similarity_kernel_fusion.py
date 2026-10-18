"""Capability checks for Supplementary Section S11.2 and S11 Table B.

Family F06: similarity-network and multiple-kernel fusion.

The script recomputes every number quoted in the explanation paragraphs that
follow S11 Table B. Each result line names the row of the table, the
capability column and the quantity shown. A value is printed at the precision
used in Section S11.2, followed by the same value to twelve significant digits
in square brackets.

Requirements: Python 3.12 or later and numpy. The script is deterministic and
reads or writes no files. Run it as

    python f06_similarity_kernel_fusion.py

Node sets
---------
The ambient system N has ten nodes, 0 to 9. Three represented sets are
compared: N itself (ten nodes), S_a = {0, ..., 7} (eight nodes) and
S_b = {0, ..., 5} (six nodes). The retained pair is nodes 0 and 1, which
belong to every represented set.

Capabilities
------------
C1 (static and dynamic networks). A step is applied to the cases of a
    represented set only, and the value it gives for the retained pair is
    compared across N, S_a and S_b. The data of nodes 0 and 1 never change;
    only the set of other represented nodes does.
C2 (fully and partially observed networks). Nodes outside the represented set
    are unobserved. A step computed from the observed cases alone gives the
    same values as in C1, and the value over N is the full-observation value.
    Where Section S11.2 states that an aggregate of the unobserved part would
    not restore that value, the script adds one REST column or one REST node,
    built from the totals of the represented nodes over N, and shows that the
    value still differs from the full-observation value.
C3 (common positive multiplicative shock). The step's own input over N is
    multiplied by lambda = 3 and the value of the retained pair is compared
    with the value without the shock.
C4 (Fs, Fa, I, A, J). The AIMNER templates are computed on the same data: the
    flow weight x_ij / F_i with the source total F_i over N, the interaction
    weight of equation (4) of the main text,
        Phi_ij = sum_X (N_iX / N_i) (N_jX / sum_{k != i} N_kX),
    and the attribute edge value ln(z_j / z_i). They are compared with the
    single value per pair that the F06 steps return.

Data
----
All random data come from numpy.random.default_rng(20261018), drawn in this
order:
    f    10 x 10 full-mesh flows with asymmetric edges, uniform on [1, 20],
         zero diagonal;
    d    10 x 10 full-mesh dyadic values with symmetric edges, (U + U^T) / 2
         with U uniform on [1, 9], zero diagonal;
    comp 10 x 3 node-by-subgroup counts, integers from 1 to 29;
    z    positive scalar node attribute, uniform on [1, 50];
    X    10 x 3 node attribute vectors, uniform on [0.5, 2].
The binary interaction graph used by the diffusion kernel joins nodes i and j
when d_ij is below the median of the off-diagonal values of d.

Counterexamples
---------------
Row 1, feature filter. Two features. Node 0 is at (0, 0), node 1 at (3, 4) and
    node k = 2, ..., 9 at (k, k), except that feature 2 is missing for nodes
    3, 8 and 9. A feature is dropped when it is missing in more than 20% of
    the represented cases. Over N, 3 of 10 cases miss feature 2 (30%), the
    feature is dropped and the distance of nodes 0 and 1 is 3. Over S_b, 1 of
    6 cases misses it (16.7%), the feature is kept and the distance is 5.
    Only the feature rule is applied, as row 1 of S11.2 describes it.
Rows 4, 8 and 9, interaction networks. The rest of the system is changed by
    multiplying the subgroup-0 counts of nodes 5 to 9 by 4. The compositions
    of nodes 0 and 1 stay the same, so a pair-local kernel of their shares
    stays the same, while the interaction weight changes. The pair-local
    kernel is exp(-||s_i - s_j||^2), with s_i the subgroup shares of node i.
Row 11, REST column. Each represented node's score vector over S is extended by
    one entry, its total over N minus its total over S.
Row 13, REST node. The induced graph on S is extended by one node joined to
    each represented node with the weight of that node's edges to the nodes
    outside S.

Step definitions follow the sources cited in S11 Table B. The scaled
exponential kernel is SNF eq. (1) with K = 3 and mu = 0.5. The SNFtool kernel
is affinityMatrix with K = 3 and sigma = 0.5, including its symmetrisation
(D + D^T) / 2 and its normal-density prefactor. The NEMO kernel uses K = 3.
KNN imputation fills feature 3 of node 0, treated as missing, with the mean
of that feature over the K = 3 other cases nearest in the remaining features.
The fixed-width Gaussian kernel is exp(-||x_i - x_j||^2 / D_m) with D_m the
number of features. The pairwiseMKL Gaussian kernel uses the median pairwise
distance s as width, exp(-||x_i - x_j||^2 / (2 s^2)). The diffusion kernel
uses beta = 0.3 and H = A - D with D the diagonal of row sums; its C1 and C2
checks use the binary graph, its C3 check the weighted input d / 10 and its
direction check the asymmetric input f / 10. The kernel of the scalar
attribute is exp(-(z_i - z_j)^2 / 100). The principal components of row 16
are computed by an exact singular value decomposition in place of the
randomized one, with the sign fixed so that the first loading is positive.
"""

import numpy as np

SEED = 20261018
N_NODES = 10
N_SUBGROUPS = 3
LAMBDA = 3.0
BETA = 0.3
K_NEIGHBOURS = 3
GENEMANIA_LINKS = 50
FEATURE_DROP_SHARE = 0.20

NODES_N = np.arange(N_NODES)
NODES_SA = np.arange(8)
NODES_SB = np.arange(6)
REPRESENTED_SETS = (("N", NODES_N), ("S_a", NODES_SA), ("S_b", NODES_SB))
I_NODE, J_NODE = 0, 1

TABLE_B_STEPS = {
    1: "Complete-case and complete-feature filtering, view deletion and feature intersection",
    2: "KNN imputation",
    3: "Per-feature z-score",
    4: "Pair-local distance of case vectors",
    5: "SNF chi-squared distance for discrete variables",
    6: "Scaled exponential kernel with local scaling",
    7: "Partial-modality fills before integration",
    8: "Unit-diagonal linear (cosine) kernel of case vectors",
    9: "Gaussian kernels with fixed widths",
    10: "Kernel centring and trace-one normalisation",
    11: "Unit-diagonal empirical kernel map of a full-mesh score matrix",
    12: "K_LI from the centred interaction matrix",
    13: "Diffusion kernel exp(beta H)",
    14: "pairwiseMKL base kernels, Kronecker pairwise kernels and centring",
    15: "GeneMANIA network construction",
    16: "Randomized PCA of the z-scored view",
}


# ---------------------------------------------------------------- data
rng = np.random.default_rng(SEED)
flows = rng.uniform(1, 20, (N_NODES, N_NODES))
np.fill_diagonal(flows, 0)
dyadic = rng.uniform(1, 9, (N_NODES, N_NODES))
dyadic = (dyadic + dyadic.T) / 2
np.fill_diagonal(dyadic, 0)
counts = rng.integers(1, 30, (N_NODES, N_SUBGROUPS)).astype(float)
attribute = rng.uniform(1, 50, N_NODES)
features = rng.uniform(0.5, 2.0, (N_NODES, 3))

upper = np.triu_indices(N_NODES, 1)
binary_graph = (dyadic < np.median(dyadic[upper])).astype(float)
np.fill_diagonal(binary_graph, 0)


# ---------------------------------------------------------------- output
def fmt(value, spec):
    return format(value, spec)


def show(label, value, spec=".4f"):
    print(f"{label} = {fmt(value, spec)}   [{value:.12g}]")


def show_flag(label, flag):
    print(f"{label}: {bool(flag)}")


def header(text):
    print()
    print(text)


def set_label(name, nodes):
    return f"represented set {name} ({len(nodes)} nodes)"


# ---------------------------------------------------------------- helpers
def position(nodes, node):
    return int(np.flatnonzero(nodes == node)[0])


def pair_value(matrix, nodes):
    return matrix[position(nodes, I_NODE), position(nodes, J_NODE)]


def zscore(matrix):
    return (matrix - matrix.mean(0)) / matrix.std(0, ddof=1)


def euclidean(matrix):
    return np.sqrt(((matrix[:, None, :] - matrix[None, :, :]) ** 2).sum(-1))


def unit_diagonal(kernel):
    scale = np.sqrt(np.diag(kernel))
    return kernel / np.outer(scale, scale)


def centre_kernel(kernel):
    m = len(kernel)
    h = np.eye(m) - np.ones((m, m)) / m
    return h @ kernel @ h


def nearest_mean(dist, k, power=1):
    """Mean of the k smallest off-diagonal entries of each row of dist**power."""
    m = len(dist)
    return np.array([np.sort(dist[r][np.arange(m) != r] ** power)[:k].mean() for r in range(m)])


def snf_kernel(dist, k=K_NEIGHBOURS, mu=0.5):
    """SNF eq. (1): W = exp(-rho^2 / (mu eps)), eps = (mean_i + mean_j + rho_ij) / 3."""
    means = nearest_mean(dist, k)
    eps = (means[:, None] + means[None, :] + dist) / 3
    return np.exp(-dist ** 2 / (mu * eps)), eps


def snftool_kernel(dist, k=K_NEIGHBOURS, sigma=0.5):
    """SNFtool affinityMatrix: symmetrise, then a normal density with local scale."""
    dist = (dist + dist.T) / 2
    means = nearest_mean(dist, k)
    local = (means[:, None] + means[None, :]) / 2 * 2 / 3 + dist / 3
    sd = sigma * local
    exponent = dist ** 2 / (2 * sd ** 2)
    prefactor = 1 / (np.sqrt(2 * np.pi) * sd)
    kernel = np.exp(-exponent) * prefactor
    return (kernel + kernel.T) / 2, exponent, prefactor


def nemo_kernel(dist, k=K_NEIGHBOURS):
    """NEMO eqs (1) and (2): normal density with a variance from squared neighbour distances."""
    means_sq = nearest_mean(dist, k, power=2)
    var = (means_sq[:, None] + means_sq[None, :] + dist ** 2) / 3
    return np.exp(-dist ** 2 / (2 * var)) / np.sqrt(2 * np.pi * var)


def knn_impute(matrix, row, col, k=K_NEIGHBOURS):
    """Fill matrix[row, col] with the mean of column col over the k nearest other rows."""
    others = [c for c in range(matrix.shape[1]) if c != col]
    dist = np.sqrt(((matrix[:, others] - matrix[row, others]) ** 2).sum(1))
    dist[row] = np.inf
    return matrix[np.argsort(dist)[:k], col].mean()


def chi2_distance(c, nodes, masses=None):
    """Chi-squared distance of row profiles; column masses over the represented rows unless given."""
    sub = c[nodes]
    profiles = sub / sub.sum(1, keepdims=True)
    if masses is None:
        masses = sub.sum(0) / sub.sum()
    diff = profiles[position(nodes, I_NODE)] - profiles[position(nodes, J_NODE)]
    return np.sqrt((diff ** 2 / masses).sum())


def expm_symmetric(matrix):
    w, v = np.linalg.eigh(matrix)
    return (v * np.exp(w)) @ v.T


def expm_general(matrix, squarings=10, terms=30):
    """Matrix exponential by scaling and squaring of a Taylor series."""
    a = matrix / 2 ** squarings
    result = np.eye(len(a))
    term = np.eye(len(a))
    for t in range(1, terms):
        term = term @ a / t
        result = result + term
    for _ in range(squarings):
        result = result @ result
    return result


def laplacian_like(adjacency):
    """H = A - D with D the diagonal of row sums."""
    return adjacency - np.diag(adjacency.sum(1))


def flow_weight(x, src, dst):
    """AIMNER flow template: edge value divided by the source total over the ambient system."""
    return x[src, dst] / x[src].sum()


def interaction_weight(c, src, dst):
    """AIMNER interaction template, equation (4) of the main text."""
    totals = c.sum(0)
    share = c[src] / c[src].sum()
    return float(sum(share[g] * c[dst, g] / (totals[g] - c[src, g]) for g in range(c.shape[1])))


def top_links_per_row(matrix, k):
    """Keep the k largest off-diagonal links of each row."""
    kept = np.zeros_like(matrix)
    for r in range(len(matrix)):
        cols = [c for c in np.argsort(-matrix[r]) if c != r][:k]
        kept[r, cols] = matrix[r, cols]
    return kept


def genemania_normalise(matrix):
    return matrix / np.sqrt(np.outer(matrix.sum(1), matrix.sum(0)))


def first_pc_score_gap(matrix, nodes, standardise):
    a = matrix[nodes] - matrix[nodes].mean(0)
    if standardise:
        a = a / matrix[nodes].std(0, ddof=1)
    _, _, vt = np.linalg.svd(a, full_matrices=False)
    loading = vt[0] * np.sign(vt[0, 0])
    scores = a @ loading
    return scores[position(nodes, I_NODE)] - scores[position(nodes, J_NODE)]


# ---------------------------------------------------------------- setup
print("S11 Table B (F06, similarity-network and multiple-kernel fusion): capability checks")
print(f"Random seed = {SEED}")
header("Setup quoted in Section S11.2")
print(f"Setup: number of nodes in the ambient system N = {N_NODES}")
print("Setup: number of nodes in the represented sets N, S_a, S_b = "
      + ", ".join(str(len(nodes)) for _, nodes in REPRESENTED_SETS))
print(f"Setup: retained pair = nodes {I_NODE} and {J_NODE}")
print(f"Setup: common shock lambda = {LAMBDA:g}")
print(f"Table B: number of F06 pre-construction rows = {len(TABLE_B_STEPS)}")


# ---------------------------------------------------------------- row 1
header(f"Row 1: {TABLE_B_STEPS[1]}")
filter_data = np.array([[0.0, 0.0], [3.0, 4.0]] + [[float(k), float(k)] for k in range(2, N_NODES)])
filter_data[[3, 8, 9], 1] = np.nan
print(f"Table B row 1: a feature is dropped when it is missing in more than "
      f"{FEATURE_DROP_SHARE:.0%} of the represented cases")


def feature_filter(matrix, nodes):
    sub = matrix[nodes]
    keep = np.isnan(sub).mean(0) <= FEATURE_DROP_SHARE
    return sub[:, keep], np.isnan(sub).mean(0)


for name, nodes in (("N", NODES_N), ("S_b", NODES_SB)):
    kept, shares = feature_filter(filter_data, nodes)
    dist = np.sqrt(((kept[position(nodes, I_NODE)] - kept[position(nodes, J_NODE)]) ** 2).sum())
    print(f"Table B row 1, C1 and C2: {set_label(name, nodes)}: share of cases missing feature 2 = "
          f"{shares[1]:.3f}, features kept = {kept.shape[1]}")
    show(f"Table B row 1, C1 and C2: distance of nodes 0 and 1 after the feature filter, "
         f"{set_label(name, nodes)}", dist, "g")

kept_x, _ = feature_filter(filter_data, NODES_N)
kept_lx, _ = feature_filter(LAMBDA * filter_data, NODES_N)
show_flag("Table B row 1, C3: filtered output of lambda*X equals lambda times the filtered output of X",
          np.allclose(kept_lx, LAMBDA * kept_x, equal_nan=True))
show_flag("Table B row 1, C3: filtered output of lambda*X equals the filtered output of X",
          np.allclose(kept_lx, kept_x, equal_nan=True))


# ---------------------------------------------------------------- row 2
header(f"Row 2: {TABLE_B_STEPS[2]}")
fill = knn_impute(features, 0, 2)
fill_shock = knn_impute(LAMBDA * features, 0, 2)
show("Table B row 2, C3: KNN fill of feature 3 of node 0 (treated as missing), no shock", fill)
show("Table B row 2, C3: KNN fill of feature 3 of node 0 (treated as missing), lambda = 3", fill_shock)
show("Table B row 2, C3: ratio of the two fills", fill_shock / fill)


# ---------------------------------------------------------------- row 3
header(f"Row 3: {TABLE_B_STEPS[3]}")
for name, nodes in REPRESENTED_SETS:
    show(f"Table B row 3, C1 and C2: distance of nodes 0 and 1 after the per-feature z-score, "
         f"{set_label(name, nodes)}", pair_value(euclidean(zscore(features[nodes])), nodes))
mean_n, sd_n = features.mean(0), features.std(0, ddof=1)
ambient_values = [pair_value(euclidean((features[nodes] - mean_n) / sd_n), nodes)
                  for _, nodes in REPRESENTED_SETS]
show_flag("Table B row 3, C2: with feature moments over N (not documented) the distance is the same "
          "for N, S_a and S_b", np.allclose(ambient_values, ambient_values[0]))


# ---------------------------------------------------------------- row 4
header(f"Row 4: {TABLE_B_STEPS[4]}")
raw = pair_value(euclidean(features), NODES_N)
raw_shock = pair_value(euclidean(LAMBDA * features), NODES_N)
show("Table B row 4, C3: Euclidean distance of nodes 0 and 1, no shock", raw)
show("Table B row 4, C3: Euclidean distance of nodes 0 and 1, lambda = 3", raw_shock)
show("Table B row 4, C3: ratio of the two distances", raw_shock / raw)
show_flag("Table B row 4, C3: symmetrisation (D + D^T)/2 of lambda*f equals lambda times that of f",
          np.allclose((LAMBDA * flows + LAMBDA * flows.T) / 2, LAMBDA * (flows + flows.T) / 2))


# ---------------------------------------------------------------- row 5
header(f"Row 5: {TABLE_B_STEPS[5]}")
masses_n = counts.sum(0) / counts.sum()
for name, nodes in REPRESENTED_SETS:
    show(f"Table B row 5, C1 and C2: chi-squared distance of nodes 0 and 1, column masses over the "
         f"represented cases (documented), {set_label(name, nodes)}", chi2_distance(counts, nodes))
for name, nodes in REPRESENTED_SETS:
    show(f"Table B row 5, C1 and C2: chi-squared distance of nodes 0 and 1, column masses over N "
         f"(not documented), {set_label(name, nodes)}", chi2_distance(counts, nodes, masses_n))
show_flag("Table B row 5, I: chi-squared distance is equal in both directions",
          np.isclose(chi2_distance(counts, NODES_N),
                     chi2_distance(counts[[1, 0] + list(range(2, N_NODES))], NODES_N)))


# ---------------------------------------------------------------- row 6
header(f"Row 6: {TABLE_B_STEPS[6]}")
for name, nodes in REPRESENTED_SETS:
    kernel, _ = snf_kernel(euclidean(features[nodes]))
    show(f"Table B row 6, C1 and C2: SNF eq. (1) kernel of nodes 0 and 1, {set_label(name, nodes)}",
         pair_value(kernel, nodes))
k_plain, eps_plain = snf_kernel(euclidean(features))
k_shock, eps_shock = snf_kernel(euclidean(LAMBDA * features))
show("Table B row 6, C3: SNF eq. (1) kernel of nodes 0 and 1, no shock", pair_value(k_plain, NODES_N))
show("Table B row 6, C3: SNF eq. (1) kernel of nodes 0 and 1, lambda = 3", pair_value(k_shock, NODES_N))
show("Table B row 6, C3: ratio of the squared distance under the shock", raw_shock ** 2 / raw ** 2)
show("Table B row 6, C3: ratio of the local scale eps under the shock",
     pair_value(eps_shock, NODES_N) / pair_value(eps_plain, NODES_N))
t_plain, e_plain, p_plain = snftool_kernel(euclidean(features))
t_shock, e_shock, p_shock = snftool_kernel(euclidean(LAMBDA * features))
show("Table B row 6, C3: SNFtool affinityMatrix value of nodes 0 and 1, no shock", pair_value(t_plain, NODES_N))
show("Table B row 6, C3: SNFtool affinityMatrix value of nodes 0 and 1, lambda = 3", pair_value(t_shock, NODES_N))
show("Table B row 6, C3: ratio of the SNFtool exponent under the shock",
     pair_value(e_shock, NODES_N) / pair_value(e_plain, NODES_N))
show("Table B row 6, C3: ratio of the SNFtool prefactor without and with the shock",
     pair_value(p_plain, NODES_N) / pair_value(p_shock, NODES_N))
n_plain = pair_value(nemo_kernel(euclidean(features)), NODES_N)
n_shock = pair_value(nemo_kernel(euclidean(LAMBDA * features)), NODES_N)
show("Table B row 6, C3: NEMO kernel of nodes 0 and 1, no shock", n_plain)
show("Table B row 6, C3: NEMO kernel of nodes 0 and 1, lambda = 3", n_shock)
show_flag("Table B rows 4 and 6, Fa: SNFtool affinityMatrix of f equals that of f^T",
          np.allclose(snftool_kernel(flows)[0], snftool_kernel(flows.T)[0]))


# ---------------------------------------------------------------- row 8
header(f"Row 8: {TABLE_B_STEPS[8]}")
cosine_z = unit_diagonal(np.outer(attribute, attribute))
off = ~np.eye(N_NODES, dtype=bool)
show("Table B row 8, A: smallest unit-diagonal linear kernel value over all pairs on the scalar attribute z",
     cosine_z[off].min(), "g")
show("Table B row 8, A: largest unit-diagonal linear kernel value over all pairs on the scalar attribute z",
     cosine_z[off].max(), "g")


# ---------------------------------------------------------------- row 9
header(f"Row 9: {TABLE_B_STEPS[9]}")
dim = features.shape[1]
g_plain = pair_value(np.exp(-euclidean(features) ** 2 / dim), NODES_N)
g_shock = pair_value(np.exp(-euclidean(LAMBDA * features) ** 2 / dim), NODES_N)
show("Table B row 9, C3: Gaussian kernel with width sqrt(D_m) of nodes 0 and 1, no shock", g_plain)
show("Table B row 9, C3: Gaussian kernel with width sqrt(D_m) of nodes 0 and 1, lambda = 3", g_shock)


# ---------------------------------------------------------------- row 10
header(f"Row 10: {TABLE_B_STEPS[10]}")
for name, nodes in REPRESENTED_SETS:
    kc = centre_kernel(features[nodes] @ features[nodes].T)
    show(f"Table B row 10, C1 and C2: centred, trace-one linear kernel of nodes 0 and 1, "
         f"{set_label(name, nodes)}", pair_value(kc / np.trace(kc), nodes), ".3g")


# ---------------------------------------------------------------- row 11
header(f"Row 11: {TABLE_B_STEPS[11]}")
for name, nodes in REPRESENTED_SETS:
    scores = flows[np.ix_(nodes, nodes)]
    show(f"Table B row 11, C1 and C2: unit-diagonal empirical kernel map of nodes 0 and 1, "
         f"{set_label(name, nodes)}", pair_value(unit_diagonal(scores @ scores.T), nodes))
scores_sa = flows[np.ix_(NODES_SA, NODES_SA)]
rest_column = flows[NODES_SA].sum(1) - scores_sa.sum(1)
with_rest = np.column_stack([scores_sa, rest_column])
show("Table B row 11, C2: unit-diagonal empirical kernel map of nodes 0 and 1 with a REST column, "
     "represented set S_a (8 nodes)", pair_value(unit_diagonal(with_rest @ with_rest.T), NODES_SA))
ekm_n = flows @ flows.T
show_flag("Table B row 11, Fa: empirical kernel map gives K_01 = K_10", np.isclose(ekm_n[0, 1], ekm_n[1, 0]))
show("Table B row 11, Fa: AIMNER flow weight from node 0 to node 1 on asymmetric f", flow_weight(flows, 0, 1))
show("Table B row 11, Fa: AIMNER flow weight from node 1 to node 0 on asymmetric f", flow_weight(flows, 1, 0))


# ---------------------------------------------------------------- row 12
header(f"Row 12: {TABLE_B_STEPS[12]}")
for name, nodes in REPRESENTED_SETS:
    m = dyadic[np.ix_(nodes, nodes)]
    mc = m - m.mean(0)
    show(f"Table B row 12, C1 and C2: K_LI of nodes 0 and 1 on weighted symmetric d, "
         f"{set_label(name, nodes)}", pair_value(unit_diagonal(mc @ mc.T), nodes))


# ---------------------------------------------------------------- row 13
header(f"Row 13: {TABLE_B_STEPS[13]}")
for name, nodes in REPRESENTED_SETS:
    a = binary_graph[np.ix_(nodes, nodes)]
    show(f"Table B row 13, C1 and C2: diffusion kernel of nodes 0 and 1 on the binary graph induced on the "
         f"represented set, {set_label(name, nodes)}", pair_value(expm_symmetric(BETA * laplacian_like(a)), nodes))
a_sa = binary_graph[np.ix_(NODES_SA, NODES_SA)]
to_outside = binary_graph[NODES_SA].sum(1) - a_sa.sum(1)
size = len(NODES_SA) + 1
a_rest = np.zeros((size, size))
a_rest[:-1, :-1] = a_sa
a_rest[:-1, -1] = to_outside
a_rest[-1, :-1] = to_outside
show("Table B row 13, C2: diffusion kernel of nodes 0 and 1 with a REST node, represented set S_a (8 nodes)",
     pair_value(expm_symmetric(BETA * laplacian_like(a_rest)), NODES_SA))
w_plain = pair_value(expm_symmetric(BETA * laplacian_like(dyadic / 10)), NODES_N)
w_shock = pair_value(expm_symmetric(BETA * laplacian_like(LAMBDA * dyadic / 10)), NODES_N)
show("Table B row 13, C3: diffusion kernel of nodes 0 and 1 on weighted input d/10, no shock", w_plain)
show("Table B row 13, C3: diffusion kernel of nodes 0 and 1 on weighted input d/10, lambda = 3", w_shock)
k_asym = expm_general(BETA * laplacian_like(flows / 10))
show_flag("Table B row 13, Fa: exp(beta H) on asymmetric f is symmetric", np.allclose(k_asym, k_asym.T))
show("Table B row 13, Fa: largest |K_ij - K_ji| of exp(beta H) on asymmetric f", np.abs(k_asym - k_asym.T).max(), ".4g")


# ---------------------------------------------------------------- row 14
header(f"Row 14: {TABLE_B_STEPS[14]}")
for name, nodes in REPRESENTED_SETS:
    dist = euclidean(features[nodes])
    width = np.quantile(dist[np.triu_indices(len(nodes), 1)], 0.5)
    show(f"Table B row 14, C1 and C2: Gaussian kernel of nodes 0 and 1 with the width at the median "
         f"distance, {set_label(name, nodes)}", pair_value(np.exp(-dist ** 2 / (2 * width ** 2)), nodes))


# ---------------------------------------------------------------- row 15
header(f"Row 15: {TABLE_B_STEPS[15]}")
print(f"Table B row 15: links kept per gene = {GENEMANIA_LINKS}; each node has at most "
      f"{N_NODES - 1} links, so every link is kept")
for name, nodes in REPRESENTED_SETS:
    sub = dyadic[np.ix_(nodes, nodes)]
    sparse = top_links_per_row(sub, GENEMANIA_LINKS)
    assert np.array_equal(sparse, sub)
    show(f"Table B row 15, C1 and C2: GeneMANIA normalisation x_ij/sqrt(r_i c_j) of nodes 0 and 1 on "
         f"symmetric d, {set_label(name, nodes)}", pair_value(genemania_normalise(sparse), nodes))


# ---------------------------------------------------------------- row 16
header(f"Row 16: {TABLE_B_STEPS[16]}")
for name, nodes in REPRESENTED_SETS:
    show(f"Table B row 16, C1 and C2: difference of the first principal-component scores of nodes 0 and 1 "
         f"after the z-score, {set_label(name, nodes)}", first_pc_score_gap(features, nodes, True))


# ---------------------------------------------------------------- C4 flow
header("Rows 4 to 6, 8 to 13 and 15 against row A, Fs: flow template on symmetric full-mesh data d")
w01 = flow_weight(dyadic, 0, 1)
w10 = flow_weight(dyadic, 1, 0)
show("Table B row A, Fs: AIMNER flow weight from node 0 to node 1 on symmetric d", w01)
show("Table B row A, Fs: AIMNER flow weight from node 1 to node 0 on symmetric d", w10)
show("Table B row 15, Fs: GeneMANIA value x_01/sqrt(r_0 c_1) over N", pair_value(genemania_normalise(dyadic), NODES_N))
show("Table B row 15, Fs: geometric mean of the two AIMNER flow weights", np.sqrt(w01 * w10))


# ---------------------------------------------------------------- C4 interaction
header("Rows 4 to 6 and 8 to 15 against row A, I: interaction template on node-by-subgroup counts")
phi01 = interaction_weight(counts, 0, 1)
phi10 = interaction_weight(counts, 1, 0)
show("Table B row A, I: AIMNER interaction weight from node 0 to node 1", phi01)
show("Table B row A, I: AIMNER interaction weight from node 1 to node 0", phi10)
shares = counts / counts.sum(1, keepdims=True)
kern_shares = np.exp(-euclidean(shares) ** 2)
show("Table B rows 4, 8 and 9, I: Gaussian kernel of the composition shares of nodes 0 and 1", kern_shares[0, 1])
show_flag("Table B rows 4, 8 and 9, I: the kernel is equal in both directions",
          np.isclose(kern_shares[0, 1], kern_shares[1, 0]))
changed = counts.copy()
changed[5:, 0] *= 4
shares_changed = changed / changed.sum(1, keepdims=True)
show("Table B rows 4, 8 and 9, I: Gaussian kernel of the composition shares of nodes 0 and 1 after the "
     "rest of the system changes", np.exp(-euclidean(shares_changed) ** 2)[0, 1])
show("Table B row A, I: AIMNER interaction weight from node 0 to node 1 after the rest of the system changes",
     interaction_weight(changed, 0, 1))


# ---------------------------------------------------------------- C4 attribute
header("Rows 4 to 6 and 8 to 15 against row A, A: attribute template on the scalar attribute z")
edge_values = np.log(attribute[None, :] / attribute[:, None])
kernel_z = np.exp(-(attribute[:, None] - attribute[None, :]) ** 2 / 100.0)
show_flag("Table B row A, A: AIMNER attribute edge value ln(z_j/z_i) is antisymmetric",
          np.allclose(edge_values, -edge_values.T))
show_flag("Table B rows 4, 5, 6 and 9, A: a kernel of |z_i - z_j| is symmetric", np.allclose(kernel_z, kernel_z.T))
show("Table B row A, A: AIMNER attribute edge value from node 0 to node 1", edge_values[0, 1])
show("Table B row A, A: AIMNER attribute edge value from node 1 to node 0", edge_values[1, 0])
