"""Capability checks for Supplementary Section S11.1, S11 Table A.

Family F05: multiview latent or coordinated representation. The script compares
the pre-construction steps documented in this family with the AIMNER flow,
interaction and attribute templates and REST, and recomputes every number quoted
in the paragraphs that follow S11 Table A.

Usage
-----
    python f05_multiview_representation.py

Requirements: Python 3.12 or later and numpy. The script reads no files, writes no
files and uses no network. All random draws come from numpy generators started
with the fixed seed 20261018, so every run prints the same output.

Output
------
Part 1 prints the design of the two numeric checks. Part 2 prints every number
quoted in the explanations of S11 Table A, in the order of the paragraphs, each on
a line that names the table row, the capability and what the number shows. Part 3
prints, row by row, the capability checks behind the cells of the table.
Nodes are numbered from 0, as in S11 (pair 0-1); periods and layers are printed
numbered from 1, so that [2] denotes the second period or the second layer.

The two numeric checks
----------------------
Both checks use an ambient system N of nine nodes, numbered 0 to 8, three layers
and a regression subnet R = {0, 1, 2, 3}. The retained values of a step are its
outputs on the directed edges among the nodes of R, in every period and layer.

Node sets. A construction set S_t is the set of nodes whose edges are represented
(observed) in period t. R is always inside it, and a step works on the mesh of
S_t, that is on all ordered pairs (i, j) of distinct nodes of S_t.
  * S_a = {0, 1, 2, 3, 4, 5} in every period: a static set under partial
    observation.
  * S_b is a dynamic set under partial observation. It equals S_a in the first
    period and its membership changes afterwards.
      first check:  {0,1,2,3,4,5}, {0,1,2,3,6,7}
      second check: {0,1,2,3,4,5}, {0,1,2,3,6,7}, {0,1,2,3,5,8}, {0,1,2,3,4,7}
  * Full observation is S_t = N = {0, 1, ..., 8} in every period.

Data. Each check draws full-mesh flows x[t, k, i, j] (period t, layer k, source i,
target j) from a lognormal distribution and sets about one fifth of the cells to
zero, as realised zero flows that the complete directed mesh keeps as zero-valued
edges. The diagonal (internal flows) is zero. A strictly positive copy of the
flows is drawn as the most favourable case for the logarithmic steps.
The first check, with two periods, also draws
  * a symmetric full-mesh variable: Euclidean distances between nine random points
    in the unit square, used as symmetric edges and as the covariate of row 13;
  * node-by-subgroup counts for three subgroups and a positive node attribute;
  * nine correlated node time series of 200 observations for row 20.
The second check, with four periods, also draws a copy of the positive flows with
nonzero internal flows (row 26), a second set of nine points (row 26) and a second
set of node time series (row 20).

Shock. A common positive multiplicative shock lambda_t multiplies every input of
period t. First check: lambda = (1, 3), so only the second period is shocked, by 3.
Second check: lambda = (1, 3, 0.5, 2).

Capabilities. For each step the script computes
  C1: the largest change of a retained value between S_a and S_b (same R, both
      under partial observation; S_b changes membership, S_a does not);
  C2: the largest difference of a retained value between S_a and full observation;
  C3: the largest change of a retained value under full observation when the shock
      is applied.
A capability holds (yes) when the largest difference is below 1e-10. When the
retained values contain nan or infinite cells, the step is undefined at the
realised zeros; it is then also checked on the strictly positive copy.

Counterexamples quoted in S11.1
-------------------------------
  * Row 20, C1 and C2: the partial correlation of nodes 0 and 1 conditions on every
    other represented node, so it changes with the represented set (first check,
    no ridge term).
  * Rows 9 and 11, C3: a logarithm followed by centring per period, and closure
    followed by a log-ratio without offset, are undefined at the realised zeros
    (first check, count of nan or infinite retained cells).
  * Row 15, C1 and C2: a proportional feature filter (a layer is kept when its
    share of all counts is at least 0.335) keeps different layers under S_a, S_b
    and full observation (second check, strictly positive flows).
  * Row 20, C3: with a ridge term rho * I (rho = 0.1) added to the raw covariance,
    a common shock of 3 on all node series changes the partial correlation of
    nodes 0 and 1 (second check).
  * Fs: on symmetric distances the z-score, log10 and Frobenius scaling keep every
    edge equal to its reverse, whereas the flow weights of the same edges are
    directed because the source totals differ (first check).
  * Fa: two sources 0 and 2 send x_01 = x_21 = 5 to node 1, with source totals 10
    and 50. Every documented step maps the two equal inputs to equal outputs; the
    flow template gives 5/10 = 0.5 and 5/50 = 0.1.
  * Row 20, Fs and Fa: an undirected connectome keeps N(N-1)/2 = 36 values against
    N(N-1) = 72 directed flow weights.
  * I: on node-by-subgroup counts the documented steps return a 9 by 3 node-level
    array, whereas the interaction template gives a 9 by 9 array of directed
    weights.
  * J: edge views have N(N-1) = 72 cases per period and node views have N = 9.
"""

import types
import warnings
from contextlib import contextmanager
from statistics import NormalDist

import numpy as np

SEED = 20261018
N_NODES = 9
N_LAYERS = 3
R = [0, 1, 2, 3]
S_FULL = list(range(N_NODES))
S_A = [0, 1, 2, 3, 4, 5]
TOLERANCE = 1e-10
TABLE = "S11 Table A"


# ----------------------------------------------------------------------------
# Data of the two checks
# ----------------------------------------------------------------------------
def first_check_data():
    """Two periods, three subgroups, shock 3 in the second period."""
    rng = np.random.default_rng(SEED)
    n_periods, n_subgroups = 2, 3
    flows = rng.lognormal(0.0, 1.0, (n_periods, N_LAYERS, N_NODES, N_NODES))
    flows[rng.random((n_periods, N_LAYERS, N_NODES, N_NODES)) < 0.2] = 0.0
    positive = rng.lognormal(0.0, 1.0, (n_periods, N_LAYERS, N_NODES, N_NODES))
    for x in (flows, positive):
        for t in range(n_periods):
            for k in range(N_LAYERS):
                np.fill_diagonal(x[t, k], 0.0)
    points = rng.random((N_NODES, 2))
    distance = np.sqrt(((points[:, None, :] - points[None, :, :]) ** 2).sum(-1))
    counts = rng.integers(0, 50, (n_periods, N_NODES, n_subgroups)).astype(float)
    attribute = rng.lognormal(0.0, 0.5, (n_periods, N_NODES))
    sources = rng.standard_normal((200, N_NODES))
    mixing = rng.standard_normal((N_NODES, N_NODES))
    return types.SimpleNamespace(
        n_periods=n_periods,
        n_subgroups=n_subgroups,
        s_b={0: [0, 1, 2, 3, 4, 5], 1: [0, 1, 2, 3, 6, 7]},
        shock=np.array([1.0, 3.0]),
        flows=flows,
        positive=positive,
        distance=distance,
        counts=counts,
        attribute=attribute,
        series=sources @ mixing,
    )


def second_check_data():
    """Four periods, shocks 1, 3, 0.5 and 2, S_b changing in every later period."""
    rng = np.random.default_rng(SEED)
    n_periods = 4
    flows = rng.lognormal(0.0, 1.0, (n_periods, N_LAYERS, N_NODES, N_NODES))
    flows[rng.random((n_periods, N_LAYERS, N_NODES, N_NODES)) < 0.2] = 0.0
    positive = rng.lognormal(0.0, 1.0, (n_periods, N_LAYERS, N_NODES, N_NODES))
    for x in (flows, positive):
        for t in range(n_periods):
            for k in range(N_LAYERS):
                np.fill_diagonal(x[t, k], 0.0)
    with_internal = positive.copy()
    for t in range(n_periods):
        for k in range(N_LAYERS):
            with_internal[t, k][np.diag_indices(N_NODES)] = rng.lognormal(0.0, 1.0, N_NODES)
    points = rng.random((N_NODES, 2))
    distance = np.sqrt(((points[:, None] - points[None]) ** 2).sum(-1))
    sources = rng.standard_normal((200, N_NODES))
    mixing = rng.standard_normal((N_NODES, N_NODES))
    return types.SimpleNamespace(
        n_periods=n_periods,
        s_b={0: [0, 1, 2, 3, 4, 5], 1: [0, 1, 2, 3, 6, 7],
             2: [0, 1, 2, 3, 5, 8], 3: [0, 1, 2, 3, 4, 7]},
        shock=np.array([1.0, 3.0, 0.5, 2.0]),
        flows=flows,
        positive=positive,
        with_internal=with_internal,
        distance=distance,
        series=sources @ mixing,
    )


# ----------------------------------------------------------------------------
# Node sets, meshes, retained values and the three comparisons
# ----------------------------------------------------------------------------
def mesh(nodes):
    """All ordered pairs of distinct nodes."""
    return [(i, j) for i in nodes for j in nodes if i != j]


def period_set(node_set, t):
    """Node set of period t; a static set is a list, a dynamic set a dict by period."""
    return node_set[t] if isinstance(node_set, dict) else node_set


def apply_shock(x, shock):
    y = x.copy()
    for t in range(x.shape[0]):
        y[t] *= shock[t]
    return y


@contextmanager
def quiet():
    """Silence floating-point warnings at zeros; the counts of nan cells report them."""
    with np.errstate(all="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        yield


def largest_abs(diff):
    values = np.abs(np.asarray(diff, dtype=float)).ravel()
    values = values[~np.isnan(values)]
    return float(values.max()) if values.size else float("nan")


def verdict(value):
    return "yes" if value < TOLERANCE else "no"


def compare(retain, x, s_b, shock):
    """retain(x, node_set) returns the retained values of a step."""
    with quiet():
        base = retain(x, S_FULL)
        under_a = retain(x, S_A)
        c1 = largest_abs(under_a - retain(x, s_b))
        c2 = largest_abs(under_a - base)
        c3 = largest_abs(retain(apply_shock(x, shock), S_FULL) - base)
    return c1, c2, c3, int((~np.isfinite(base)).sum()), base.size


def report(label, retain, x, s_b, shock, data_note):
    c1, c2, c3, nonfinite, size = compare(retain, x, s_b, shock)
    if nonfinite:
        print(f"{label}, C1 to C3 ({data_note}): undefined, "
              f"{nonfinite} of {size} retained cells are nan or infinite")
        return
    print(f"{label}, C1 ({data_note}): largest change of a retained value "
          f"between S_a and S_b = {c1:.6g} -> {verdict(c1)}")
    print(f"{label}, C2 ({data_note}): largest difference of a retained value "
          f"between S_a and full observation = {c2:.6g} -> {verdict(c2)}")
    print(f"{label}, C3 ({data_note}): largest change of a retained value "
          f"under the shock = {c3:.6g} -> {verdict(c3)}")


# Edge-period arrangement: cases are the directed edges of the mesh of S_t,
# stacked over periods; the columns are the layers.
def edge_period_block(x, node_set):
    rows, keys = [], []
    for t in range(x.shape[0]):
        for (i, j) in mesh(period_set(node_set, t)):
            rows.append(x[t, :, i, j])
            keys.append((t, i, j))
    return np.array(rows), keys


def retained_rows(values, keys, n_periods):
    lookup = {key: values[n] for n, key in enumerate(keys)}
    return np.array([lookup[(t, i, j)] for t in range(n_periods) for (i, j) in mesh(R)])


def edge_period_retain(step):
    def retain(x, node_set):
        block, keys = edge_period_block(x, node_set)
        return retained_rows(step(block, keys), keys, x.shape[0])
    return retain


# Period arrangement: cases are the periods; the features are (layer, directed
# edge) over the union of the meshes; a cell is missing (nan) when the edge lies
# outside the mesh of S_t in that period.
def period_case_table(x, node_set):
    n_periods = x.shape[0]
    features = sorted({(k, i, j) for t in range(n_periods)
                       for (i, j) in mesh(period_set(node_set, t)) for k in range(N_LAYERS)})
    table = np.full((n_periods, len(features)), np.nan)
    for c, (k, i, j) in enumerate(features):
        for t in range(n_periods):
            nodes = period_set(node_set, t)
            if i in nodes and j in nodes:
                table[t, c] = x[t, k, i, j]
    return table, features


def period_case_retain(step):
    def retain(x, node_set):
        table, features = period_case_table(x, node_set)
        out = step(table)
        index = {feature: c for c, feature in enumerate(features)}
        return np.array([out[t, index[(k, i, j)]] for t in range(x.shape[0])
                         for (i, j) in mesh(R) for k in range(N_LAYERS)])
    return retain


# ----------------------------------------------------------------------------
# Documented F05 pre-construction steps (cases by variables)
# ----------------------------------------------------------------------------
def period_labels(keys):
    return np.array([key[0] for key in keys])


def centre_cases(X, keys):
    """Row 1: centring over the pooled edge-period cases."""
    return X - X.mean(0)


def centre_per_period(X, keys):
    """Row 6: centring per group, with the periods as groups."""
    Y, p = X.copy(), period_labels(keys)
    for t in np.unique(p):
        Y[p == t] -= X[p == t].mean(0)
    return Y


def z_score(X, keys):
    """Row 4: z-score over the block's cases."""
    return (X - X.mean(0)) / X.std(0)


def frobenius_scaling(X, keys):
    """Row 5: centring, then division by the Frobenius norm of the block."""
    C = X - X.mean(0)
    return C / np.linalg.norm(C)


def inertia_scaling(X, keys):
    """Row 5: z-score, then division by the square root of the block inertia."""
    C = (X - X.mean(0)) / X.std(0)
    return C / (np.linalg.norm(C) / np.sqrt(C.shape[0]))


def largest_eigenvalue_scaling(X, keys):
    """Row 5: centring, then division by the root of the largest covariance eigenvalue."""
    C = X - X.mean(0)
    largest = np.linalg.eigvalsh(np.cov(C.T, bias=True)).max()
    return C / np.sqrt(largest)


def view_scaling(X, keys):
    """Row 5: centring, then division by one standard deviation of the whole view."""
    C = X - X.mean(0)
    return C / C.std()


def centre_scale_per_period(X, keys):
    """Row 7: centring and scaling per group, each group within one period."""
    Y, p = centre_per_period(X, keys), period_labels(keys)
    for t in np.unique(p):
        Y[p == t] /= Y[p == t].std()
    return Y


def centre_scale_nested_groups(X, keys):
    """Row 7: centring and scaling per group, two groups nested in each period."""
    Y = X.copy()
    group = np.array([2 * t + (i % 2) for (t, i, j) in keys])
    for g in np.unique(group):
        Y[group == g] -= Y[group == g].mean(0)
        Y[group == g] /= Y[group == g].std()
    return Y


def log10_elementwise(X, keys):
    """Row 8: elementwise base-10 logarithm."""
    return np.log10(X)


def log1p_elementwise(X, keys):
    """Row 8: elementwise logarithm with pseudocount 1."""
    return np.log1p(X)


def log_centre_per_period(X, keys):
    """Row 9: logarithm, then centring per period."""
    return centre_per_period(np.log(X), keys)


def size_factors(X):
    """Median-of-ratios size factor of each case."""
    geometric_mean = np.exp(np.log(X).mean(0))
    return np.median(X / geometric_mean, axis=1)


def size_factor_normalisation(X, keys):
    """Row 10: division of each case by its size factor."""
    return X / size_factors(X)[:, None]


def size_factor_log_centre(X, keys):
    """Row 10 variant: size factors, an exact logarithm, then pooled centring."""
    L = np.log(X / size_factors(X)[:, None])
    return L - L.mean(0)


def size_factor_log1p_centre(X, keys):
    """Row 10 variant: size factors, log(1 + x), then pooled centring."""
    L = np.log1p(X / size_factors(X)[:, None])
    return L - L.mean(0)


def closure_log_ratio(X, keys, offset=0.0):
    """Rows 11 and 12: closure of each case, then centred log-ratio."""
    P = (X + offset) / (X + offset).sum(1, keepdims=True)
    L = np.log(P)
    return L - L.mean(1, keepdims=True)


def closure_log_ratio_offset_one(X, keys):
    return closure_log_ratio(X, keys, offset=1.0)


def regress_out_covariate(covariate):
    """Row 13: least-squares residuals on an intercept and an edge covariate."""
    def step(X, keys):
        c = np.array([covariate[i, j] for (_, i, j) in keys])
        design = np.column_stack([np.ones_like(c), c])
        coefficients = np.linalg.lstsq(design, X, rcond=None)[0]
        return X - design @ coefficients
    return step


def layers_kept_by_share(x, node_set, threshold=0.335):
    """Row 15: a layer is kept when its share of all counts is at least the threshold."""
    block, _ = edge_period_block(x, node_set)
    share = block.sum(0) / block.sum()
    return [k + 1 for k in range(N_LAYERS) if share[k] >= threshold]


def case_total_filter(x, node_set, threshold=6.0):
    """Row 16: a case is kept when its own total over the layers reaches the threshold."""
    block, keys = edge_period_block(x, node_set)
    keep = block.sum(1) >= threshold
    lookup = {key: keep[n] for n, key in enumerate(keys)}
    return np.array([lookup[(t, i, j)] for t in range(x.shape[0]) for (i, j) in mesh(R)], float)


def clip_at_threshold(X, keys):
    """Row 17: clipping at the fixed threshold 1.1."""
    return np.minimum(X, 1.1)


def rank_inverse_normal(X, keys):
    """Row 18: rank-based inverse Gaussian transform of each column."""
    normal = NormalDist()
    ranks = X.argsort(0, kind="stable").argsort(0, kind="stable") + 1
    quantiles = (ranks - 0.5) / X.shape[0]
    return np.vectorize(normal.inv_cdf)(quantiles)


def partial_correlation(series, nodes, a=0, b=1):
    """Row 20: partial correlation of nodes a and b given the other nodes in `nodes`."""
    precision = np.linalg.inv(np.cov(series[:, nodes].T))
    ia, ib = nodes.index(a), nodes.index(b)
    return -precision[ia, ib] / np.sqrt(precision[ia, ia] * precision[ib, ib])


def ridge_partial_correlation(series, rho=0.1, normalise=False):
    """Row 20: partial correlation of nodes 0 and 1 from the inverse of Sigma + rho * I."""
    covariance = np.cov(series.T)
    if normalise:
        covariance = covariance / np.sqrt(np.mean(np.diag(covariance) ** 2))
    precision = -np.linalg.inv(covariance + rho * np.eye(series.shape[1]))
    scale = np.sqrt(np.abs(np.diag(precision)))
    return (precision / scale[:, None] / scale[None, :])[0, 1]


def centre_within_corridor(X, keys):
    """Row 21: within-subject decomposition, each corridor (i, j) a subject."""
    Y = X.copy()
    corridors = {}
    for n, (_, i, j) in enumerate(keys):
        corridors.setdefault((i, j), []).append(n)
    for rows in corridors.values():
        Y[rows] -= X[rows].mean(0)
    return Y


def mean_imputation_retain(x, node_set):
    """Row 22: cases are the full mesh of N; cells outside the mesh of S_t are
    missing and replaced by the feature-wise mean of the observed cells."""
    block, keys = edge_period_block(x, S_FULL)
    observed = np.array([(i in period_set(node_set, t)) and (j in period_set(node_set, t))
                         for (t, i, j) in keys])
    imputed = block.copy()
    imputed[~observed] = block[observed].mean(0)
    return retained_rows(imputed, keys, x.shape[0])


def identity(X, keys):
    """Row 23: masking and available-data computation leave observed cells unchanged."""
    return X.copy()


def union_alignment_retain(x, node_set):
    """Row 24: alignment on the union of case names; observed cells pass unchanged."""
    block, keys = edge_period_block(x, node_set)
    return retained_rows(block, keys, x.shape[0])


def divide_by_record_sum(x, node_set):
    """Row 25 read with the sum of the source's records in the graph as divisor."""
    out = []
    for t in range(x.shape[0]):
        nodes = period_set(node_set, t)
        for (i, j) in mesh(R):
            for k in range(N_LAYERS):
                out.append(x[t, k, i, j] / sum(x[t, k, i, m] for m in nodes if m != i))
    return np.array(out)


def transition_distribution(x, node_set):
    """Row 26: flow divided by the sum over the represented regions, own region included."""
    out = []
    for t in range(x.shape[0]):
        nodes = period_set(node_set, t)
        for (i, j) in mesh(R):
            for k in range(N_LAYERS):
                out.append(x[t, k, i, j] / sum(x[t, k, i, m] for m in nodes))
    return np.array(out)


def cosine_of_transition_distributions(x, node_set):
    """Row 26: cosine similarity of the regions' transition distributions (layer 1)."""
    out = []
    for t in range(x.shape[0]):
        nodes = period_set(node_set, t)
        dist = {i: np.array([x[t, 0, i, m] for m in nodes]) / sum(x[t, 0, i, m] for m in nodes)
                for i in nodes}
        for (i, j) in mesh(R):
            out.append(dist[i] @ dist[j] / np.linalg.norm(dist[i]) / np.linalg.norm(dist[j]))
    return np.array(out)


# ----------------------------------------------------------------------------
# AIMNER templates
# ----------------------------------------------------------------------------
def aimner_flow_weight(x, node_set):
    """Flow template: edge value divided by the ambient total of its source, which
    is the represented total plus REST."""
    out = []
    for t in range(x.shape[0]):
        nodes = period_set(node_set, t)
        for (i, j) in mesh(R):
            for k in range(N_LAYERS):
                represented = sum(x[t, k, i, m] for m in nodes if m != i)
                ambient = x[t, k, i, :].sum() - x[t, k, i, i]
                rest = ambient - represented
                total = represented + rest
                out.append(x[t, k, i, j] / total if total > 0 else 0.0)
    return np.array(out)


def interaction_weights(counts):
    """Interaction template, equation (4) of the main text, from node-by-subgroup counts."""
    n = counts.shape[0]
    weights = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            total = 0.0
            for g in range(counts.shape[1]):
                source = counts[i, g] / counts[i].sum() if counts[i].sum() > 0 else 0.0
                others = counts[:, g].sum() - counts[i, g]
                total += source * (counts[j, g] / others if others > 0 else 0.0)
            weights[i, j] = total
    return weights


def attribute_edge_values(z):
    """Attribute template: ln(z_j / z_i) for every ordered pair (i, j)."""
    return np.log(z[None, :] / z[:, None])


def largest_reverse_difference(matrix_by_edge, nodes):
    return max(abs(matrix_by_edge[(i, j)] - matrix_by_edge[(j, i)]) for (i, j) in mesh(nodes))


# ----------------------------------------------------------------------------
# Part 1: design
# ----------------------------------------------------------------------------
def changing_periods(s_b, n_periods):
    return [t + 1 for t in range(1, n_periods) if sorted(s_b[t]) != sorted(s_b[t - 1])]


def print_design(first, second):
    print("PART 1. Design of the two numeric checks")
    print(f"{TABLE}, design: ambient nodes = {N_NODES}")
    print(f"{TABLE}, design: layers = {N_LAYERS}")
    print(f"{TABLE}, design: nodes of the regression subnet R = {len(R)}")
    print(f"{TABLE}, design: nodes of the static construction set S_a = {len(S_A)}")
    print(f"{TABLE}, design, first check: subgroups = {first.n_subgroups}")
    print(f"{TABLE}, design, first check: periods = {first.n_periods}")
    print(f"{TABLE}, design, first check: periods in which S_b changes membership "
          f"(periods numbered from 1) = {changing_periods(first.s_b, first.n_periods)}")
    print(f"{TABLE}, design, first check: shock of the second period lambda_t = "
          f"{first.shock[1]:g}")
    print(f"{TABLE}, design, second check: periods = {second.n_periods}")
    print(f"{TABLE}, design, second check: shocks by period = "
          f"{', '.join(f'{v:g}' for v in second.shock)}")
    print(f"{TABLE}, design, second check: periods in which S_b changes membership "
          f"(periods numbered from 1) = {changing_periods(second.s_b, second.n_periods)}")
    print()


# ----------------------------------------------------------------------------
# Part 2: numbers quoted in the explanations of S11 Table A
# ----------------------------------------------------------------------------
def print_quoted_numbers(first, second):
    print("PART 2. Numbers quoted in the explanations of S11 Table A")

    # Row 15, second check: layers kept by the proportional feature filter.
    kept_a = layers_kept_by_share(second.positive, S_A)
    kept_b = layers_kept_by_share(second.positive, second.s_b)
    kept_full = layers_kept_by_share(second.positive, S_FULL)
    print(f"{TABLE} row 15, C1 and C2 (second check): layers kept by the share filter "
          f"under S_a (layers numbered from 1) = {kept_a}")
    print(f"{TABLE} row 15, C1 and C2 (second check): layers kept by the share filter "
          f"under S_b (layers numbered from 1) = {kept_b}")
    print(f"{TABLE} row 15, C1 and C2 (second check): layers kept by the share filter "
          f"under full observation (layers numbered from 1) = {kept_full}")

    # Row 20, first check: partial correlation of pair 0-1 without ridge term.
    r_a = partial_correlation(first.series, S_A)
    r_b = partial_correlation(first.series, first.s_b[1])
    r_full = partial_correlation(first.series, S_FULL)
    print(f"{TABLE} row 20, C1 and C2 (first check, no ridge term): partial correlation "
          f"of pair 0-1 under S_a = {r_a:.3f} (unrounded {r_a:.6f})")
    print(f"{TABLE} row 20, C1 and C2 (first check, no ridge term): partial correlation "
          f"of pair 0-1 under the second-period set of S_b {first.s_b[1]} = {r_b:.3f} "
          f"(unrounded {r_b:.6f})")
    print(f"{TABLE} row 20, C1 and C2 (first check, no ridge term): partial correlation "
          f"of pair 0-1 under full observation = {r_full:.3f} (unrounded {r_full:.6f})")

    # Rows 9 and 11, first check: retained cells undefined at realised zeros.
    for row, name, step in [(9, "logarithm, then centring per period", log_centre_per_period),
                            (11, "closure and log-ratio, offset 0", closure_log_ratio)]:
        with quiet():
            values = edge_period_retain(step)(first.flows, S_FULL)
        print(f"{TABLE} row {row}, C3 (first check): retained cells that are nan or infinite "
              f"after {name} = {int((~np.isfinite(values)).sum())} of {values.size}")

    # Row 20, second check: ridge partial correlation under a common shock.
    rho, lam = 0.1, 3.0
    before = ridge_partial_correlation(second.series, rho)
    after = ridge_partial_correlation(lam * second.series, rho)
    print(f"{TABLE} row 20, C3 (second check, rho = {rho:g}, lambda = {lam:g}): regularised "
          f"partial correlation of pair 0-1 before the shock = {before:.3f} "
          f"(unrounded {before:.6f})")
    print(f"{TABLE} row 20, C3 (second check, rho = {rho:g}, lambda = {lam:g}): regularised "
          f"partial correlation of pair 0-1 after the shock = {after:.3f} "
          f"(unrounded {after:.6f})")

    # Fs, first check: symmetric distances stay symmetric; flow weights are directed.
    edges = mesh(S_FULL)
    cases = np.array([[first.distance[i, j]] for (i, j) in edges])
    keys = [(0, i, j) for (i, j) in edges]
    for row, name, step in [(4, "the z-score", z_score), (8, "log10", log10_elementwise),
                            (5, "Frobenius scaling", frobenius_scaling)]:
        out = step(cases, keys)[:, 0]
        by_edge = {(i, j): out[n] for n, (i, j) in enumerate(edges)}
        print(f"{TABLE} row {row}, Fs (first check, symmetric distances): largest "
              f"|g_ij - g_ji| after {name} = {largest_reverse_difference(by_edge, S_FULL):g}")
    flow_on_distance = first.distance / first.distance.sum(1, keepdims=True)
    asym = float(np.abs(flow_on_distance - flow_on_distance.T).max())
    print(f"{TABLE} row A, Fs (first check, symmetric distances): largest |w_ij - w_ji| of "
          f"the flow weights of the same edges = {asym:.4f} (unrounded {asym:.6f})")

    # Fa: equal edges, different source totals.
    x = np.zeros((N_NODES, N_NODES))
    x[0, 1] = x[2, 1] = 5.0
    x[0, 3] = 5.0
    x[2, 3] = 45.0
    print(f"{TABLE} rows 1 to 24 and row A, Fa: source totals of nodes 0 and 2 = "
          f"{x[0].sum():g} and {x[2].sum():g}, with x_01 = x_21 = {x[0, 1]:g}")
    print(f"{TABLE} row A, Fa: flow template weight w_01 = {x[0, 1] / x[0].sum():g}")
    print(f"{TABLE} row A, Fa: flow template weight w_21 = {x[2, 1] / x[2].sum():g}")

    # Row 20, Fs and Fa: undirected values against directed flow weights.
    print(f"{TABLE} row 20, Fs and Fa (first check): undirected values kept per node pair "
          f"= {N_NODES * (N_NODES - 1) // 2}")
    print(f"{TABLE} row 20, Fs and Fa (first check): directed flow weights = "
          f"{len(mesh(S_FULL))}")

    # I, first check: node-level outputs against interaction weights.
    counts = first.counts[0]
    keys = [(0, i, -1) for i in range(N_NODES)]
    with quiet():
        shapes = {step(counts, keys).shape for step in
                  (centre_cases, z_score, log1p_elementwise, frobenius_scaling,
                   closure_log_ratio_offset_one)}
    node_shape = shapes.pop() if len(shapes) == 1 else None
    print(f"{TABLE} rows 1 to 26, I (first check): shape of the outputs of centring, z-score, "
          f"log(1 + x), Frobenius scaling and closure with log-ratio, offset 1, on "
          f"node-by-subgroup counts = {node_shape[0]} by {node_shape[1]}")
    weights = interaction_weights(counts)
    print(f"{TABLE} rows 1 to 26, I (first check): shape of the interaction template "
          f"weights = {weights.shape[0]} by {weights.shape[1]}")

    # J, first check: cases of edge views and node views.
    print(f"{TABLE} rows 1 to 26, J (first check): edge-view cases per period N(N-1) = "
          f"{len(mesh(S_FULL))}")
    print(f"{TABLE} rows 1 to 26, J (first check): node-view cases N = "
          f"{first.attribute[0].shape[0]}")
    print()


# ----------------------------------------------------------------------------
# Part 3: capability checks behind the rows of S11 Table A
# ----------------------------------------------------------------------------
def print_row_checks(first, second):
    print("PART 3. Capability checks behind the rows of S11 Table A")
    f1 = (first.s_b, first.shock)
    f2 = (second.s_b, second.shock)
    zeros1 = "first check, flows with realised zeros"
    positive1 = "first check, strictly positive copy"
    zeros2 = "second check, flows with realised zeros"
    positive2 = "second check, strictly positive copy"

    report(f"{TABLE} row 1", edge_period_retain(centre_cases), first.flows, *f1, zeros1)
    report(f"{TABLE} row 2", period_case_retain(lambda W: W - np.nanmean(W, axis=0)),
           second.flows, *f2, "second check, periods as cases")

    def log10_centre_over_periods(W):
        L = np.log10(W)
        return L - np.nanmean(L, axis=0)
    report(f"{TABLE} row 3", period_case_retain(log10_centre_over_periods),
           second.positive, *f2, "second check, periods as cases, strictly positive copy")
    report(f"{TABLE} row 3", period_case_retain(log10_centre_over_periods),
           second.flows, *f2, "second check, periods as cases, realised zeros")

    report(f"{TABLE} row 4", edge_period_retain(z_score), first.flows, *f1, zeros1)
    for name, step in [("Frobenius norm", frobenius_scaling),
                       ("square root of the block inertia", inertia_scaling),
                       ("square root of the largest covariance eigenvalue",
                        largest_eigenvalue_scaling),
                       ("one standard deviation of the whole view", view_scaling)]:
        report(f"{TABLE} row 5", edge_period_retain(step), first.flows, *f1,
               f"{zeros1}, divisor {name}")
    report(f"{TABLE} row 6", edge_period_retain(centre_per_period), first.flows, *f1, zeros1)
    report(f"{TABLE} row 7", edge_period_retain(centre_scale_per_period), first.flows, *f1,
           f"{zeros1}, one group per period")
    report(f"{TABLE} row 7", edge_period_retain(centre_scale_nested_groups), second.flows, *f2,
           f"{zeros2}, two groups nested in each period")

    report(f"{TABLE} row 8", edge_period_retain(log10_elementwise), first.flows, *f1,
           f"{zeros1}, log10")
    report(f"{TABLE} row 8", edge_period_retain(log10_elementwise), first.positive, *f1,
           f"{positive1}, log10")
    report(f"{TABLE} row 8", edge_period_retain(log1p_elementwise), first.flows, *f1,
           f"{zeros1}, log(1 + x)")

    report(f"{TABLE} row 9", edge_period_retain(log_centre_per_period), first.flows, *f1, zeros1)
    report(f"{TABLE} row 9", edge_period_retain(log_centre_per_period), first.positive, *f1,
           positive1)

    report(f"{TABLE} row 10", edge_period_retain(size_factor_normalisation), first.flows, *f1,
           zeros1)
    report(f"{TABLE} row 10", edge_period_retain(size_factor_normalisation), first.positive,
           *f1, positive1)
    block0, keys = edge_period_block(second.positive, S_FULL)
    block1, _ = edge_period_block(apply_shock(second.positive, second.shock), S_FULL)
    lam_case = second.shock[period_labels(keys)]
    ratio = size_factors(block1) / size_factors(block0)
    geometric = np.exp(np.mean(np.log(lam_case)))
    print(f"{TABLE} row 10, C3 ({positive2}): largest |s_e(lambda x) / s_e(x) - "
          f"lambda_t(e) / G(lambda)| = {largest_abs(ratio - lam_case / geometric):.6g}")
    print(f"{TABLE} row 10, C3 ({positive2}): largest |s_e(lambda x) / s_e(x) - 1| = "
          f"{largest_abs(ratio - 1.0):.6g}")
    report(f"{TABLE} row 10", edge_period_retain(size_factor_log_centre), second.positive, *f2,
           f"{positive2}, exact logarithm and pooled centring after the size factors")
    report(f"{TABLE} row 10", edge_period_retain(size_factor_log1p_centre), second.positive,
           *f2, f"{positive2}, log(1 + x) and pooled centring after the size factors")

    report(f"{TABLE} row 11", edge_period_retain(closure_log_ratio), first.flows, *f1, zeros1)
    report(f"{TABLE} row 11", edge_period_retain(closure_log_ratio), first.positive, *f1,
           positive1)
    report(f"{TABLE} row 12", edge_period_retain(closure_log_ratio_offset_one), first.flows,
           *f1, f"{zeros1}, offset 1")
    report(f"{TABLE} row 13", edge_period_retain(regress_out_covariate(first.distance)),
           first.flows, *f1, f"{zeros1}, covariate = distance")

    print(f"{TABLE} row 15, C1 and C2 (second check, strictly positive copy): layers kept "
          f"under S_a, S_b and full observation (layers numbered from 1) = "
          f"{layers_kept_by_share(second.positive, S_A)}, "
          f"{layers_kept_by_share(second.positive, second.s_b)}, "
          f"{layers_kept_by_share(second.positive, S_FULL)}")
    report(f"{TABLE} row 16", case_total_filter, second.positive, *f2,
           f"{positive2}, keep indicator")
    report(f"{TABLE} row 17", edge_period_retain(clip_at_threshold), second.flows, *f2, zeros2)
    report(f"{TABLE} row 18", edge_period_retain(rank_inverse_normal), first.flows, *f1, zeros1)

    r_a = partial_correlation(first.series, S_A)
    r_b = partial_correlation(first.series, first.s_b[1])
    r_full = partial_correlation(first.series, S_FULL)
    r_shock = partial_correlation(3.0 * first.series, S_FULL)
    print(f"{TABLE} row 20, C1 (first check, no ridge term): change of the partial "
          f"correlation of pair 0-1 between S_a and S_b = {abs(r_a - r_b):.6g} -> "
          f"{verdict(abs(r_a - r_b))}")
    print(f"{TABLE} row 20, C2 (first check, no ridge term): difference of the partial "
          f"correlation of pair 0-1 between S_a and full observation = "
          f"{abs(r_a - r_full):.6g} -> {verdict(abs(r_a - r_full))}")
    print(f"{TABLE} row 20, C3 (first check, no ridge term): change of the partial "
          f"correlation of pair 0-1 under a common shock of 3 = {abs(r_shock - r_full):.6g} "
          f"-> {verdict(abs(r_shock - r_full))}")
    raw = abs(ridge_partial_correlation(3.0 * second.series)
              - ridge_partial_correlation(second.series))
    normalised = abs(ridge_partial_correlation(3.0 * second.series, normalise=True)
                     - ridge_partial_correlation(second.series, normalise=True))
    print(f"{TABLE} row 20, C3 (second check, ridge rho = 0.1 on the raw covariance): change "
          f"of the partial correlation of pair 0-1 under a common shock of 3 = {raw:.6g} -> "
          f"{verdict(raw)}")
    print(f"{TABLE} row 20, C3 (second check, ridge rho = 0.1 after normalising the "
          f"covariance): change under a common shock of 3 = {normalised:.6g} -> "
          f"{verdict(normalised)}")

    report(f"{TABLE} row 21", edge_period_retain(centre_within_corridor), second.flows, *f2,
           f"{zeros2}, corridors as subjects")
    report(f"{TABLE} row 22", mean_imputation_retain, second.flows, *f2,
           f"{zeros2}, retained cells after mean imputation")
    report(f"{TABLE} row 23", edge_period_retain(identity), first.flows, *f1, zeros1)
    report(f"{TABLE} row 24", union_alignment_retain, second.flows, *f2, zeros2)

    report(f"{TABLE} row 25", aimner_flow_weight, second.flows, *f2,
           f"{zeros2}, divisor = published total of the source")
    report(f"{TABLE} row 25", divide_by_record_sum, second.flows, *f2,
           f"{zeros2}, divisor = sum of the source's records in the graph")

    report(f"{TABLE} row 26", transition_distribution, second.with_internal, *f2,
           f"{positive2} with internal flows, transition distribution")
    report(f"{TABLE} row 26", cosine_of_transition_distributions, second.with_internal, *f2,
           f"{positive2} with internal flows, cosine graph")
    with_self = largest_abs(transition_distribution(second.with_internal, S_FULL)
                            - aimner_flow_weight(second.with_internal, S_FULL))
    without_self = largest_abs(transition_distribution(second.positive, S_FULL)
                               - aimner_flow_weight(second.positive, S_FULL))
    print(f"{TABLE} row 26 (second check, full observation): largest difference between the "
          f"transition distribution and the flow weight, internal flows nonzero = "
          f"{with_self:.6g}")
    print(f"{TABLE} row 26 (second check, full observation): largest difference between the "
          f"transition distribution and the flow weight, internal flows zero = "
          f"{without_self:.6g}")
    rows = second.distance / second.distance.sum(1, keepdims=True)
    unit = rows / np.linalg.norm(rows, axis=1, keepdims=True)
    cosine = unit @ unit.T
    print(f"{TABLE} row 26, Fs (second check, symmetric distances): largest |c_ij - c_ji| "
          f"of the cosine-similarity graph = {float(np.abs(cosine - cosine.T).max()):g}")

    report(f"{TABLE} row A", aimner_flow_weight, first.flows, *f1,
           f"{zeros1}, flow template with REST")

    # Fa: column-wise steps map the equal edges 0->1 and 2->1 to equal outputs.
    x = np.zeros((N_NODES, N_NODES))
    x[0, 1] = x[2, 1] = 5.0
    x[0, 3] = 5.0
    x[2, 3] = 45.0
    edges = mesh(S_FULL)
    cases = np.array([[x[i, j]] for (i, j) in edges])
    keys = [(0, i, j) for (i, j) in edges]
    position = {edge: n for n, edge in enumerate(edges)}
    gap = 0.0
    for step in (centre_cases, z_score, frobenius_scaling, log1p_elementwise):
        out = step(cases, keys)[:, 0]
        gap = max(gap, abs(out[position[(0, 1)]] - out[position[(2, 1)]]))
    print(f"{TABLE} rows 1 to 24, Fa: largest difference between the outputs for edges "
          f"0->1 and 2->1 after centring, z-score, Frobenius scaling and log(1 + x) = {gap:g}")

    # I: zero subgroup counts make closure and log-ratio without offset undefined.
    print(f"{TABLE} rows 11 and 12, I (first check): zero node-by-subgroup counts in the "
          f"first period = {int((first.counts[0] == 0).sum())}")

    # A: the attribute template is antisymmetric; a two-part closure would give half of it.
    z = first.attribute[0]
    values = attribute_edge_values(z)
    print(f"{TABLE} rows 1 to 26, A (first check): attribute template values form a "
          f"{values.shape[0]} by {values.shape[1]} array, largest |a_ij + a_ji| = "
          f"{float(np.abs(values + values.T).max()):g}")
    i, j = 1, 4
    pair = closure_log_ratio(np.array([[z[i], z[j]]]), None)[0]
    print(f"{TABLE} row 11, A (first check, nodes {i} and {j} closed as a two-part "
          f"composition, an arrangement no source documents): target component of the "
          f"log-ratio = {pair[1]:.6f}, half of ln(z_j / z_i) = {values[i, j] / 2:.6f}")

    # J: edge-period keys and node keys are disjoint.
    edge_keys = {f"{i}-{j}" for (i, j) in mesh(S_FULL)}
    node_keys = {f"{i}" for i in range(N_NODES)}
    print(f"{TABLE} row 24, J (first check): case names shared by an edge view and a node "
          f"view = {len(edge_keys & node_keys)}, rows of their union = "
          f"{len(edge_keys | node_keys)}")


def main():
    first = first_check_data()
    second = second_check_data()
    print_design(first, second)
    print_quoted_numbers(first, second)
    print_row_checks(first, second)


if __name__ == "__main__":
    main()
