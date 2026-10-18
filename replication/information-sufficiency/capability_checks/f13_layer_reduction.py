"""Capability checks for multilayer-network layer reduction (F13).

Supplementary Section S11.4, S11 Table D.

This script recomputes every number quoted in the paragraphs that explain the
"no" cells of S11 Table D. Each printed line names the row of Table D, the
capability and the quantity shown. Values are printed at the precision used in
S11.

Requirements: Python 3.12 or later and numpy. The script is deterministic:
every random draw comes from a numpy Generator with a fixed seed, and the order
of the draws is fixed. It reads no files and writes only to standard output.

Notation
--------
x_ij     value of the directed edge from source i to target j; the diagonal
         is zero.
F_i      total of source i over the ambient system, F_i = sum_j x_ij over all
         nodes of the ambient system.
w_ij     AIMNER flow weight w_ij = x_ij / F_i. Under partial observation REST
         completes F_i, so the denominator is always the ambient total.
lambda   common positive multiplicative shock applied to every input value.
R        retained nodes {0, 1, 2}. In the C1 and C2 checks the retained
         values are the six ordered pairs among them. C3 does not depend on
         which nodes are retained, so the C3 checks of rows 1, 4 and 6 retain
         every edge of the layer (all 72 ordered pairs of the nine nodes) and
         report the largest change over them.
S_a      represented or observed nodes {0, 1, 2, 3, 4}.
S_b      S_a plus node 5, i.e. node 5 enters the represented set.
full     all nodes {0, ..., 8}, i.e. full observation.

Capabilities: C1 static and dynamic networks (retained values unchanged when
the represented nodes change), C2 fully and partially observed networks
(retained values exact under partial observation), C3 invariance to a common
positive multiplicative shock, Fs and Fa flow networks from full-mesh data
with symmetric and asymmetric edges, I interaction networks from
node-by-subgroup compositions, A attribute networks from node attributes.

Examples
--------
Example 1. Asymmetric flow mesh (random stream A, seed 13, first draw).
    An ambient system of N = 9 nodes. The first draw of stream A is a 9 by 9
    array of standard lognormal values with the diagonal set to zero. It is an
    asymmetric full mesh x, and its source totals F_i are taken over all nine
    nodes. Used for row 1 and rows 4 and 6 under C3 (the shock lambda = 3.7 is
    applied to every value), for rows 4 and 6 under Fa (the AIMNER flow layer
    w = x / F is passed through W + W^T, and x_01 and x_10 are swapped), and
    for row 3 under Fs and Fa (a flow weight in [0, 1] is divided by 10 and
    rounded).

Example 2. Symmetric distance meshes (stream A, second and third draws).
    Nine points are drawn uniformly in the unit square. Their Euclidean
    distances form a symmetric full mesh D with positive off-diagonal values.
    A 9 by 9 array of factors drawn uniformly from [0.5, 2] multiplies D, and
    the product is symmetrised, which gives a second, different symmetric mesh
    D2. Used for rows 1 to 15 under Fs (AIMNER flow weights from D are directed
    because the source totals differ), for row 2 under Fs (binarising D and D2
    gives the same complete graph) and for row 7 under Fs (the layer-total
    shares of D stay symmetric).

Example 3. Positive node attributes (stream A, fourth draw).
    Nine standard lognormal values z_i. The AIMNER attribute layer is
    a_ij = ln z_j - ln z_i, which is antisymmetric. Used for rows 4 and 6
    under A (W + W^T turns the layer into zeros).

Example 4. Trade values near the rounding threshold of row 3 (no randomness).
    A 3 by 3 layer with the off-diagonal values 8, 30, 6, 4, 12 and 7. Row 3
    divides each value by 10, rounds it to the nearest integer and links a
    pair when the result is positive. Used for row 3 under C3 with the common
    shock lambda = 0.5.

Example 5. Asset price series (random stream B, seed 7, first two draws).
    Five assets over 5000 days. Daily log-returns are r_it = l_i f_t + e_it,
    where f_t is a common standard normal factor (first draw of stream B),
    e_it are independent standard normal terms (second draw) and the loadings
    are l = (0.1, 0.1, 0.9, 0.9, 0.9), so assets 0 and 1 are almost
    uncorrelated with each other. Prices are
    P_it = 50 exp(0.01 * cumulative sum of r_it over days), and correlations
    are computed from the log-returns of P. The represented assets are
    {0, 1, 2, 3}, and then {0, 1, 2, 3, 4} when asset 4 enters. Under C2 the
    same two sets are read as partial observation ({0, 1, 2, 3}, asset 4
    unobserved) against full observation of the five assets. Used for
    row 10 under C1 and C2:
    - The influence d(i|j) is the mean, over the represented assets k other
      than i and j, of rho_ik - rho_ik|j, where rho_ik|j is the partial
      correlation of i and k given j. The influence d(2|3) changes when
      asset 4 enters.
    - The planar maximally filtered graph (PMFG) adds pairs in decreasing
      order of correlation as long as the graph stays planar, until it holds
      3(n - 2) links among n assets. For n = 4 the complete graph K4 is planar
      and has 3(4 - 2) = 6 links, so every pair is linked. For n = 5 the first
      nine pairs form K5 minus its weakest pair, which is planar, whereas K5
      is not, so the PMFG keeps every pair except the weakest. This makes the
      construction below exact for n <= 5 without a general planarity test.
      Here the weakest pair among the five assets is (0, 1), so the retained
      pair (0, 1) is linked among four assets and loses its link when the
      fifth asset is represented.

Example 6. One directed commodity layer (stream B, fifth draw).
    After the two draws of Example 5, stream B yields two blocks that S11 does
    not use: a 5000 by 1 normal block with standard deviation 0.05 and an 8 by
    8 lognormal block. They are drawn and discarded so that the next draw is
    exactly the layer behind the quoted numbers. That draw is a 9 by 9
    standard lognormal array with zero diagonal, read as the imports of one
    commodity among nine countries. Row 7 divides every value by the layer
    total over the represented countries. Used for row 7 under C1 (S_a to
    S_b), under C2 (S_a against full observation) and under Fa (row sums of
    the shares, and the share of edge 0 -> 1 against the flow weight
    x_01 / F_0).

Example 7. Percentile thresholds (200 independent layers, seeds 0 to 199).
    Each seed gives one 9 by 9 standard lognormal layer with zero diagonal.
    Row 8 links a pair when its weight exceeds the 90th percentile of the
    off-diagonal weights of its layer, which keeps the strongest 10 per cent.
    The check counts the layers in which the links of the six retained pairs
    differ between partial observation (S_a) and full observation.

Example 8. Co-authorship (no randomness).
    Five authors 0 to 4, two category layers 0 and 1, and five papers:
        paper 1: authors {0, 1, 2},    category 0
        paper 2: authors {0, 1},       categories 0 and 1
        paper 3: authors {1, 2, 3, 4}, category 0
        paper 4: authors {0, 3},       category 1
        paper 5: authors {0, 1, 4},    category 0
    Row 11 gives each co-author pair of a paper p the weight
    1 / (L_p (N_p - 1)) in each of its L_p category layers, where N_p is the
    number of authors of p. The AIMNER interaction weight of equation (4) of
    the main text is computed in layer 0, with the papers of category 0 as
    the subgroups X:
        I_ij = sum over X of (N_i^X / N_i) * (N_j^X / sum over k != i of N_k^X),
    where N_i^X is 1 when author i is on paper X and 0 otherwise, and N_i is
    the number of category-0 papers of author i. Used for row 11 under I.

Counterexamples
---------------
Each example is a counterexample to one capability of one row of Table D: a
retained value that changes when a node enters (C1), a retained value that
differs from its full-observation value (C2), a retained value that changes
under a common positive shock (C3), or an output that cannot carry the
directed flow weights, the directed interaction weights or the antisymmetric
attribute edge values of AIMNER (Fs, Fa, I, A). The AIMNER values are printed
beside them where S11 quotes them.
"""

import numpy as np

N_NODES = 9
RETAINED = [0, 1, 2]
S_A = [0, 1, 2, 3, 4]
S_B = [0, 1, 2, 3, 4, 5]
FULL = list(range(N_NODES))
N_DAYS = 5000
N_LAYERS_PERCENTILE = 200


# ---------------------------------------------------------------- helpers
def submesh(M, nodes):
    """Values among the given nodes, in the order of the list."""
    return M[np.ix_(nodes, nodes)]


def retained_values(M, nodes):
    """Off-diagonal values of the retained pairs in a layer built on `nodes`."""
    idx = [nodes.index(r) for r in RETAINED]
    block = M[np.ix_(idx, idx)]
    return block[~np.eye(len(RETAINED), dtype=bool)]


def largest_change(a, b):
    return float(np.max(np.abs(np.asarray(a) - np.asarray(b))))


def yes_no(flag):
    return "yes" if flag else "no"


# ------------------------------------------------- AIMNER reference values
def aimner_flow_weights(x, nodes, source_totals):
    """w_ij = x_ij / F_i with F_i over the ambient system (completed by REST)."""
    return submesh(x, nodes) / source_totals[nodes][:, None]


def aimner_interaction_weights(membership):
    """Equation (4) of the main text for a node-by-subgroup array N_i^X."""
    n, g = membership.shape
    node_totals = membership.sum(axis=1)
    weights = np.zeros((n, n))
    for i in range(n):
        if node_totals[i] == 0:
            continue
        for j in range(n):
            if i == j:
                continue
            for s in range(g):
                others = membership[:, s].sum() - membership[i, s]
                if others > 0:
                    weights[i, j] += (membership[i, s] / node_totals[i]) * (
                        membership[j, s] / others
                    )
    return weights


# --------------------------------------- documented F13 steps (Table D rows)
def place_on_common_node_set(layer):
    """Row 1: place each supplied value unchanged on the integer node set
    0, ..., max id, padding absent nodes with empty rows and columns."""
    edges = [(i, j, layer[i, j]) for i in range(layer.shape[0])
             for j in range(layer.shape[1]) if layer[i, j] != 0]
    size = max(max(i, j) for i, j, _ in edges) + 1
    out = np.zeros((size, size))
    for i, j, value in edges:
        out[i, j] = value
    return out


def binarise_at_zero(layer):
    """Row 2: a_ij = 1 when the edge value is positive."""
    return (layer > 0).astype(float)


def divide_round_binarise(layer):
    """Row 3: divide by 10, round to the nearest integer, link when positive."""
    return (np.rint(layer / 10.0) > 0).astype(float)


def symmetrise(layer):
    """Rows 4 and 6: A = W + W^T."""
    return layer + layer.T


def layer_total_shares(layer):
    """Row 7: each value divided by the total of the layer."""
    return layer / layer.sum()


def percentile_links(layer, q=90.0):
    """Row 8: link when the weight exceeds the q-th percentile of the layer."""
    off_diagonal = layer[~np.eye(layer.shape[0], dtype=bool)]
    return (layer > np.percentile(off_diagonal, q)).astype(float)


def correlation(returns):
    return np.corrcoef(returns.T)


def log_returns(prices):
    return np.diff(np.log(prices), axis=0)


def partial_correlation(C, i, k, j):
    """rho_ik|j from the correlation matrix C."""
    return (C[i, k] - C[i, j] * C[k, j]) / np.sqrt(
        (1.0 - C[i, j] ** 2) * (1.0 - C[k, j] ** 2)
    )


def influence(C, i, j, nodes):
    """Row 10: d(i|j) = mean over represented k of rho_ik - rho_ik|j."""
    ks = [k for k in nodes if k not in (i, j)]
    return float(np.mean([C[i, k] - partial_correlation(C, i, k, j) for k in ks]))


def all_pairs(nodes):
    return [(a, b) for pos, a in enumerate(nodes) for b in nodes[pos + 1:]]


def weakest_pair(C, nodes):
    return min(all_pairs(nodes), key=lambda e: C[e[0], e[1]])


def pmfg_links_small(C, nodes):
    """Row 10: exact PMFG for at most five nodes (see Example 5)."""
    n = len(nodes)
    if n > 5:
        raise ValueError("the exact construction here covers at most five nodes")
    links = set(all_pairs(nodes))
    if n == 5:
        links.discard(weakest_pair(C, nodes))
    return links


def coauthorship_projection(papers, n_authors, n_categories):
    """Row 11: weight 1 / (L_p (N_p - 1)) per co-author pair and category."""
    W = np.zeros((n_categories, n_authors, n_authors))
    for authors, categories in papers:
        n_p, l_p = len(authors), len(categories)
        for c in categories:
            for a in authors:
                for b in authors:
                    if a != b:
                        W[c, a, b] += 1.0 / (l_p * (n_p - 1))
    return W


# ---------------------------------------------------------------- examples
def main():
    lines = []
    out = lines.append

    # Stream A (seed 13): Examples 1 to 3, drawn in this order.
    stream_a = np.random.default_rng(13)
    x = stream_a.lognormal(0.0, 1.0, (N_NODES, N_NODES))
    np.fill_diagonal(x, 0.0)
    source_totals = x.sum(axis=1)
    points = stream_a.random((N_NODES, 2))
    D = np.sqrt(((points[:, None] - points[None]) ** 2).sum(-1))
    np.fill_diagonal(D, 0.0)
    D2 = D * stream_a.uniform(0.5, 2.0, (N_NODES, N_NODES))
    D2 = (D2 + D2.T) / 2.0
    np.fill_diagonal(D2, 0.0)
    z = stream_a.lognormal(0.0, 1.0, N_NODES)

    # Stream B (seed 7): Examples 5 and 6, drawn in this order.
    stream_b = np.random.default_rng(7)
    common_factor = stream_b.normal(size=(N_DAYS, 1))
    idiosyncratic = stream_b.normal(size=(N_DAYS, 5))
    _ = stream_b.normal(0.0, 0.05, (N_DAYS, 1))      # not used in S11
    _ = stream_b.lognormal(0.0, 1.0, (8, 8))         # not used in S11
    trade = stream_b.lognormal(0.0, 1.0, (N_NODES, N_NODES))
    np.fill_diagonal(trade, 0.0)

    loadings = np.array([0.1, 0.1, 0.9, 0.9, 0.9])
    returns = common_factor * loadings + idiosyncratic
    prices = 50.0 * np.exp(np.cumsum(0.01 * returns, axis=0))
    C = correlation(log_returns(prices))

    out("F13 multilayer-network layer reduction: Supplementary Section S11.4, S11 Table D")
    out("Retained nodes R = {0, 1, 2}; S_a = {0, ..., 4}; S_b = S_a plus node 5; "
        "full observation = {0, ..., 8}")
    out("")

    # ---------------- C1 and C2: rows 7, 8 and 10 (paragraph after Table D on C1 and C2)
    share_a = retained_values(layer_total_shares(submesh(trade, S_A)), S_A)
    share_b = retained_values(layer_total_shares(submesh(trade, S_B)), S_B)
    share_full = retained_values(layer_total_shares(submesh(trade, FULL)), FULL)
    out("Table D row 7, C1: largest change of a retained layer-total share between "
        "S_a and S_b (node 5 enters) = %.4f" % largest_change(share_a, share_b))
    out("Table D row 7, C2: largest difference of a retained layer-total share between "
        "S_a and full observation = %.3f" % largest_change(share_a, share_full))

    differing = 0
    for seed in range(N_LAYERS_PERCENTILE):
        layer = np.random.default_rng(seed).lognormal(0.0, 1.0, (N_NODES, N_NODES))
        np.fill_diagonal(layer, 0.0)
        links_partial = retained_values(percentile_links(submesh(layer, S_A)), S_A)
        links_full = retained_values(percentile_links(submesh(layer, FULL)), FULL)
        if not np.array_equal(links_partial, links_full):
            differing += 1
    out("Table D row 8, C2: random layers in which the retained 90th-percentile links "
        "differ between S_a and full observation = %d of %d" % (differing, N_LAYERS_PERCENTILE))

    four, five = [0, 1, 2, 3], [0, 1, 2, 3, 4]
    d_four = influence(C, 2, 3, four)
    d_five = influence(C, 2, 3, five)
    out("Table D row 10, C1 and C2: influence d(2|3) over the assets {0, 1, 2, 3} = %.4f" % d_four)
    out("Table D row 10, C1 and C2: influence d(2|3) over the assets {0, 1, 2, 3, 4} = %.4f" % d_five)
    out("Table D row 10, C1 and C2: change of d(2|3) when asset 4 enters or is unobserved = %.4f"
        % abs(d_five - d_four))

    links_four = pmfg_links_small(C, four)
    links_five = pmfg_links_small(C, five)
    out("Table D row 10, C1 and C2: correlation of the retained pair (0, 1) = %.3f; "
        "weakest pair among the five assets = %s" % (C[0, 1], weakest_pair(C, five)))
    out("Table D row 10, C1 and C2: PMFG links among four assets = %d, 3(n - 2) = %d; "
        "pair (0, 1) linked = %s" % (len(links_four), 3 * (4 - 2), yes_no((0, 1) in links_four)))
    out("Table D row 10, C1 and C2: PMFG links among five assets = %d, 3(n - 2) = %d; "
        "pair (0, 1) linked = %s" % (len(links_five), 3 * (5 - 2), yes_no((0, 1) in links_five)))
    out("")

    # ---------------- C3: rows 1, 4, 6 and 3
    lam = 3.7
    padded = place_on_common_node_set(x)
    padded_shocked = place_on_common_node_set(lam * x)
    out("Table D row 1, C3: largest change of a retained value (all 72 edges retained) "
        "under the common shock lambda = %.1f = %.2f"
        % (lam, largest_change(padded_shocked, padded)))
    out("Table D rows 4 and 6, C3: largest change of a retained value of W + W^T (all 72 "
        "edges retained) under the common shock lambda = %.1f = %.2f"
        % (lam, largest_change(symmetrise(padded_shocked), symmetrise(padded))))

    near_threshold = np.array([[0.0, 8.0, 30.0],
                               [6.0, 0.0, 4.0],
                               [12.0, 7.0, 0.0]])
    out("Table D row 3, C3: links of the values 8, 30, 6, 4, 12 and 7 = %d"
        % int(divide_round_binarise(near_threshold).sum()))
    out("Table D row 3, C3: links after the common shock lambda = 0.5 = %d"
        % int(divide_round_binarise(0.5 * near_threshold).sum()))
    out("")

    # ---------------- Fs and Fa: rows 1 to 15, 2, 3, 4, 6 and 7
    w_sym = aimner_flow_weights(D, FULL, D.sum(axis=1))
    out("Table D rows 1 to 15, Fs: AIMNER flow weight w_01 from the symmetric mesh D = %.4f"
        % w_sym[0, 1])
    out("Table D rows 1 to 15, Fs: AIMNER flow weight w_10 from the symmetric mesh D = %.4f"
        % w_sym[1, 0])

    bin_D, bin_D2 = binarise_at_zero(D), binarise_at_zero(D2)
    out("Table D row 2, Fs: links after binarising the symmetric mesh D = %d of %d "
        "(complete graph); D and D2 differ = %s; their binary layers are equal = %s"
        % (int(bin_D.sum()), N_NODES * (N_NODES - 1), yes_no(not np.array_equal(D, D2)),
           yes_no(np.array_equal(bin_D, bin_D2))))

    w = aimner_flow_weights(x, FULL, source_totals)
    out("Table D row 3, Fs and Fa: largest AIMNER flow weight = %.4f; links after "
        "dividing the flow layer by 10 and rounding = %d of %d"
        % (w.max(), int(divide_round_binarise(w).sum()), N_NODES * (N_NODES - 1)))

    x_swapped = x.copy()
    x_swapped[0, 1], x_swapped[1, 0] = x[1, 0], x[0, 1]
    out("Table D rows 4 and 6, Fa: W + W^T unchanged when x_01 and x_10 are swapped = %s"
        % yes_no(np.array_equal(symmetrise(x), symmetrise(x_swapped))))
    w_through_sym = symmetrise(w)
    out("Table D rows 4 and 6, Fa: AIMNER flow weight w_01 = %.4f" % w[0, 1])
    out("Table D rows 4 and 6, Fa: AIMNER flow weight w_10 = %.4f" % w[1, 0])
    out("Table D rows 4 and 6, Fa: value of W + W^T for this flow layer, 0 -> 1 = %.4f, "
        "1 -> 0 = %.4f" % (w_through_sym[0, 1], w_through_sym[1, 0]))

    shares_D = layer_total_shares(D)
    out("Table D row 7, Fs: largest |s_ij - s_ji| of the layer-total shares of the "
        "symmetric mesh D = %.1f" % largest_change(shares_D, shares_D.T))
    shares_trade = layer_total_shares(trade)
    row_sums = shares_trade.sum(axis=1)
    out("Table D row 7, Fa: smallest row sum of the layer-total shares = %.3f" % row_sums.min())
    out("Table D row 7, Fa: largest row sum of the layer-total shares = %.3f" % row_sums.max())
    out("Table D row 7, Fa: layer-total share w_01 = %.4f" % shares_trade[0, 1])
    out("Table D row 7, Fa: AIMNER flow weight x_01 / F_0 = %.4f"
        % (trade[0, 1] / trade[0].sum()))
    out("")

    # ---------------- I: row 11
    papers = [([0, 1, 2], [0]),
              ([0, 1], [0, 1]),
              ([1, 2, 3, 4], [0]),
              ([0, 3], [1]),
              ([0, 1, 4], [0])]
    n_authors, n_categories = 5, 2
    projection = coauthorship_projection(papers, n_authors, n_categories)
    category0 = [authors for authors, categories in papers if 0 in categories]
    membership = np.zeros((n_authors, len(category0)))
    for s, authors in enumerate(category0):
        membership[authors, s] = 1.0
    interaction = aimner_interaction_weights(membership)
    out("Table D row 11, I: AIMNER interaction weight I_01 (papers as subgroups) = %.3f"
        % interaction[0, 1])
    out("Table D row 11, I: AIMNER interaction weight I_10 (papers as subgroups) = %.3f"
        % interaction[1, 0])
    out("Table D row 11, I: co-authorship projection weight w_01 in layer 0 = %.1f"
        % projection[0, 0, 1])
    out("Table D row 11, I: co-authorship projection weight w_10 in layer 0 = %.1f"
        % projection[0, 1, 0])
    out("")

    # ---------------- A: rows 4 and 6
    log_z = np.log(z)
    attribute_layer = log_z[None, :] - log_z[:, None]
    out("Table D rows 4 and 6, A: largest |entry| of W + W^T for the AIMNER attribute "
        "layer ln(z_j / z_i) = %.1f" % np.max(np.abs(symmetrise(attribute_layer))))

    print("\n".join(lines))


if __name__ == "__main__":
    main()
