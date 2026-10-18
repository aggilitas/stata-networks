"""Capability checks for Supplementary Section S11.3 (S11 Table C).

Family F07: dynamic state estimation and assimilation.

The script recomputes every number quoted in the paragraphs that explain
S11 Table C and prints each one on a labelled line that names the table row,
the capability and the quantity shown. Every example is constructed. Each one
is a counterexample showing that a documented pre-construction step lacks a
capability, or the AIMNER flow weight used as the reference.

Requirements: Python 3.12 or later and numpy. The script reads no files,
writes no files and uses no network. Run it as

    python f07_state_estimation.py

Capabilities
------------
C1  Work in static and dynamic networks: a retained value is unchanged when
    the represented nodes change.
C2  Work in fully and partially observed networks: a retained value under
    partial observation equals its value under full observation.
C3  Algebraic invariance to a common positive multiplicative shock: a
    retained value is unchanged when every input value of period t is
    multiplied by the same factor lambda_t > 0.
Fs  Flow networks from full-mesh network data with symmetric edges.

Network notation
----------------
The random examples use a network of 12 nodes, numbered 0 to 11, observed
over 12 periods, numbered 0 to 11. R = {0, 1, 2, 3, 4} is the regression
subnet. The retained values are those on the directed edges among the nodes
of R. x[t, i, j] is the value of the edge from source i to target j in
period t, and self-edges are 0.

Random draws
------------
Two generators, numpy.random.default_rng(7) and numpy.random.default_rng(11),
make all random draws. Each draws its arrays in the fixed order below. The
order matters because every draw advances the stream. Two draws of the second
generator feed none of the quoted examples. They are kept so that the draws
after them reproduce the published values.

Generator 1 (seed 7), in this order:
  1. flow panel X: 12 periods x 12 x 12, lognormal(0, 1), self-edges set to 0;
  2. construction sets S_t: for each period, R plus a random subset of the
     nodes 5 to 11, whose size is drawn uniformly from 0 to 7;
  3. period shocks lambda_t: uniform on [0.5, 3.0], one per period;
  4. multiplicative noise of a 60-month series: lognormal(0, 0.05);
  5. matrix D: 12 x 12, uniform on [1, 10], symmetrised as (D + D^T) / 2,
     diagonal set to 0.
Generator 2 (seed 11), in this order:
  1. flow panel X, drawn as in generator 1;
  2. period shocks lambda_t, drawn as in generator 1;
  3. construction sets (R plus a random subset of the nodes 5 to 11, size
     drawn from 0 to 6): not used by any quoted example;
  4. call counts C: 12 periods x 12 x 12, Poisson with mean 0.02, self-edges
     set to 0;
  5. four integer series of length 12 (visit and test counts): not used by
     any quoted example;
  6. 200 observations of a common factor z and of the series
     x0 = z + 0.3 e, x1 = z + 0.1 e, target y = z + 0.5 e and three unrelated
     standard normal series, each e a fresh standard normal draw;
  7. 300 observations of a node series g and of the node series
     a = g + 0.3 e and b = g + 0.3 e.

The examples
------------
Row A (AIMNER flow template with REST, reference). The flow weight of edge
(i, j) is w_ij = x_ij / F_i, where F_i is the total of source i over the
ambient system, given by the represented edges of i plus REST. The weights of
the retained edges are computed under full observation (all 12 nodes in every
period) and under the period-specific construction sets S_t of generator 1,
and under S_t once more after every period is multiplied by its shock
lambda_t. The retained weights do not change in either comparison.

Row 5 (seasonal adjustment, C3). A 60-month series
x_t = exp(0.01 t) (1 + 0.3 sin(2 pi t / 12)) u_t, with u_t the lognormal
noise of generator 1, is seasonally adjusted by the classical multiplicative
ratio-to-moving-average method: a centred 2 x 12 moving average gives the
trend, the mean ratio of the series to the trend for each calendar month
gives the seasonal index, the indices are scaled to mean 1, and the series is
divided by its index. Month 30 is then multiplied by a shock of 1.5 and the
adjustment is repeated. The adjusted value of month 30 keeps the shock.

Row 10 (one fixed node set present in every period, C1). Node 11 is absent
from the ambient system in periods 0 to 4 and enters in period 5. A rule that
keeps only the nodes present in every period keeps 11 of the 12 nodes and
removes node 11 from every period. The script counts the positive edge values
from the five nodes of R to node 11 in periods 5 to 11 that the rule removes
with the node.

Row 14 (Gaussian anamorphosis fitted to the histogram of the available data,
C1, C2 and C3). The normal score of a value v in a pool of n values is
Phi^-1(r / (n + 1)), where r is the number of pool values not above v and
Phi^-1 is the inverse standard normal distribution function. The retained
value is x[3, 0, 1] of generator 2. The pool holds the edge values of all
represented nodes over all 12 periods. Under full observation all 12 nodes
are represented. Under partial observation the five nodes 7 to 11 are not
represented, so the pool holds only the edges among the nodes 0 to 6. For C3
every period of the full pool, the retained value included, is multiplied by
its shock lambda_t of generator 2.

Row 15 (superobbing onto the model grid, C1 and C2). Three sites inside one
grid cell observe 1, 3 and 8. The cell value is their mean. When the site
that observes 8 is not represented, the mean of the remaining two is the
cell value.

Row 19 (nearest-neighbour data association, C1, C2 and C3). Two tracks,
named track 0 and track 2, have the predicted positions 0.0 and 2.0. A report
at 1.2 is assigned to the track with the nearest predicted position. When
track 2 is not represented, the report is assigned to track 0. With the track
predictions carried over from the previous period, a shock of 0.5 on the
current report moves it from 1.2 to 0.6, and it is assigned to track 0.

Row 21 (targeted predictors by soft thresholding, C1 and C2). Soft
thresholding is computed as a lasso fit: the series are standardised, the
target is centred, and the coefficients minimise
(1 / 2n) ||y - X b||^2 + 0.7 ||b||_1 by cyclic coordinate descent over 2000
sweeps. The optimality conditions of the lasso are checked at the result.
The lasso variant of least angle regression (LARS) traces this same solution
as the penalty varies. Pool A holds x0 and the three unrelated series, and x0
is selected (non-zero coefficient). Pool B adds x1, which follows the common
factor more closely, and x0 is no longer selected.

Row 22 (node pruning by mean incoming plus outgoing calls, C1, C2 and C3).
The calls of node 0 are those of generator 2 plus 0.11 calls per period to
each of the nodes 6 to 11. Node 0 is kept when the mean over the 12 periods
of its outgoing plus incoming calls is at least one per period (one call per
month in the source). The mean is computed over all 12 nodes as partners
(the ambient system) and over the represented partners 0 to 5 only. For C3
the calls of the first six periods, half of the 12, are multiplied by a
shock of 0.6 and the mean is again taken over all 12 nodes.

Row 28 (networks estimated from node series, C1 and C2). The link between
nodes a and b is their partial correlation given the other represented
nodes. When only a and b are represented it is the plain correlation of the
two series. When node g, which drives both, is also represented, the partial
correlation given g is the correlation of the residuals of a and b after a
least-squares regression on g with an intercept.

Fs check (rows 1 and 12 against the AIMNER flow weight). D is a symmetric
full-mesh matrix from generator 1. The script reports the largest difference
between the two directions of an edge, max |v_ij - v_ji|, for the log of the
edge values (row 1), for the share of the network-wide total (row 12) and for
the AIMNER flow weight d_ij / sum_k d_ik. The log and the network-wide share
stay symmetric, whereas the flow weights differ between the two directions
because the source totals differ.
"""

from statistics import NormalDist

import numpy as np

N = 12                      # nodes 0 to 11
T = 12                      # periods 0 to 11
R = np.arange(5)            # regression subnet {0, 1, 2, 3, 4}
OUTSIDE_R = np.arange(5, N)  # nodes 5 to 11
RETAINED = [(i, j) for i in R for j in R if i != j]


def report(row, capability, text, value):
    """Print one labelled result line."""
    print(f"Table C row {row}, {capability}: {text} = {value}")


# ---------------------------------------------------------------------------
# Generator 1 (seed 7): draws in the fixed order of the docstring
# ---------------------------------------------------------------------------
rng1 = np.random.default_rng(7)
X1 = rng1.lognormal(0.0, 1.0, size=(T, N, N))
for t in range(T):
    np.fill_diagonal(X1[t], 0.0)
sets_dynamic = []
for t in range(T):
    size = rng1.integers(0, len(OUTSIDE_R) + 1)
    extra = rng1.choice(OUTSIDE_R, size=size, replace=False)
    sets_dynamic.append(np.sort(np.r_[R, extra]))
sets_full = [np.arange(N) for t in range(T)]
shock1 = rng1.uniform(0.5, 3.0, size=T)
MONTHS = 60
month_noise = rng1.lognormal(0.0, 0.05, MONTHS)
D = rng1.uniform(1.0, 10.0, size=(N, N))
D = (D + D.T) / 2.0
np.fill_diagonal(D, 0.0)

# ---------------------------------------------------------------------------
# Generator 2 (seed 11): draws in the fixed order of the docstring
# ---------------------------------------------------------------------------
rng2 = np.random.default_rng(11)
X2 = rng2.lognormal(0.0, 1.0, size=(T, N, N))
for t in range(T):
    np.fill_diagonal(X2[t], 0.0)
shock2 = rng2.uniform(0.5, 3.0, size=T)
for t in range(T):          # draw 3: not used by any quoted example
    size = rng2.integers(0, 7)
    rng2.choice(OUTSIDE_R, size=size, replace=False)
calls = rng2.poisson(0.02, size=(T, N, N)).astype(float)
for t in range(T):
    np.fill_diagonal(calls[t], 0.0)
calls[:, 0, 6:] += 0.11     # node 0 calls each of the nodes 6 to 11 a little
rng2.integers(50, 500, T)   # draw 5: not used by any quoted example
rng2.integers(5000, 9000, T)
rng2.integers(5, 60, T)
rng2.integers(100, 300, T)
OBS = 200
factor_z = rng2.normal(size=OBS)
series_x0 = factor_z + 0.3 * rng2.normal(size=OBS)
series_x1 = factor_z + 0.1 * rng2.normal(size=OBS)
target_y = factor_z + 0.5 * rng2.normal(size=OBS)
unrelated = rng2.normal(size=(OBS, 3))
OBS_NODE = 300
node_g = rng2.normal(size=(OBS_NODE, 1))
node_a = node_g[:, 0] + 0.3 * rng2.normal(size=OBS_NODE)
node_b = node_g[:, 0] + 0.3 * rng2.normal(size=OBS_NODE)

print("Supplementary Section S11.3, S11 Table C (family F07): recomputed values")
print()

# ---------------------------------------------------------------------------
# Row A: AIMNER flow weight with REST (reference)
# ---------------------------------------------------------------------------
def aimner_flow_weights(X, sets):
    """Flow weights x_ij / F_i on the mesh of each construction set.

    F_i is the total of source i over the ambient system, that is the
    represented edges of i plus REST.
    """
    W = np.full_like(X, np.nan)
    for t in range(X.shape[0]):
        source_total = X[t].sum(axis=1)
        for i in sets[t]:
            for j in sets[t]:
                if i != j:
                    W[t, i, j] = X[t, i, j] / source_total[i]
    return W


W_full = aimner_flow_weights(X1, sets_full)
W_dynamic = aimner_flow_weights(X1, sets_dynamic)
W_shocked = aimner_flow_weights(X1 * shock1[:, None, None], sets_dynamic)
diff_sets = max(np.max(np.abs(W_full[:, i, j] - W_dynamic[:, i, j])) for i, j in RETAINED)
diff_shock = max(np.max(np.abs(W_dynamic[:, i, j] - W_shocked[:, i, j])) for i, j in RETAINED)
report("A", "C1 and C2",
       "largest change of a retained AIMNER flow weight between full observation "
       "and the period-specific construction sets S_t (reference)", f"{diff_sets:g}")
report("A", "C3",
       "largest change of a retained AIMNER flow weight under the period shocks "
       "lambda_t (reference, rounding only)", f"{diff_shock:.1e}")
print()

# ---------------------------------------------------------------------------
# Row 5: seasonal adjustment, C3
# ---------------------------------------------------------------------------
def seasonal_adjust(x, p=12):
    """Classical multiplicative ratio-to-moving-average seasonal adjustment."""
    n = len(x)
    trend = np.full(n, np.nan)
    weights = np.r_[0.5, np.ones(p - 1), 0.5] / p      # centred 2 x 12 average
    for k in range(p // 2, n - p // 2):
        trend[k] = weights @ x[k - p // 2:k + p // 2 + 1]
    ratio = x / trend
    index = np.array([np.nanmean(ratio[m::p]) for m in range(p)])
    index = index / index.mean()
    return x / np.tile(index, n // p + 1)[:n]


months = np.arange(MONTHS)
monthly = np.exp(0.01 * months) * (1.0 + 0.3 * np.sin(2.0 * np.pi * months / 12.0)) * month_noise
SHOCK_MONTH = 30
month_shock = np.ones(MONTHS)
month_shock[SHOCK_MONTH] = 1.5
adjusted = seasonal_adjust(monthly)
adjusted_shocked = seasonal_adjust(monthly * month_shock)
report(5, "C3", "seasonally adjusted value at month 30 without the shock",
       f"{adjusted[SHOCK_MONTH]:.4f}")
report(5, "C3", "seasonally adjusted value at month 30 with a shock of 1.5 at that month",
       f"{adjusted_shocked[SHOCK_MONTH]:.4f}")
print()

# ---------------------------------------------------------------------------
# Row 10: one fixed node set present in every period, C1
# ---------------------------------------------------------------------------
ENTERING_NODE = 11
ENTRY_PERIOD = 5
present = np.ones((T, N), dtype=bool)
present[:ENTRY_PERIOD, ENTERING_NODE] = False
fixed_set = [n for n in range(N) if present[:, n].all()]
removed = int(sum(X1[t, i, ENTERING_NODE] > 0
                  for t in range(ENTRY_PERIOD, T) for i in R))
report(10, "C1", "period in which node 11 enters the ambient system", ENTRY_PERIOD)
report(10, "C1", "nodes kept by the fixed node-set rule, of 12", len(fixed_set))
report(10, "C1", "positive edge values from the five nodes of R to the entering node 11 "
       "in periods 5 to 11, removed with the node", removed)
print()

# ---------------------------------------------------------------------------
# Row 14: Gaussian anamorphosis fitted to the available data, C1, C2 and C3
# ---------------------------------------------------------------------------
STANDARD_NORMAL = NormalDist()


def normal_score(value, pool):
    """Normal score Phi^-1(r / (n + 1)), r = number of pool values not above value."""
    pool = np.sort(pool)
    rank = np.searchsorted(pool, value, side="right")
    return STANDARD_NORMAL.inv_cdf(rank / (len(pool) + 1))


def pooled_edge_values(X, nodes, periods):
    return np.array([X[t, i, j] for t in periods for i in nodes for j in nodes if i != j])


nodes_full = list(range(N))
nodes_partial = list(range(7))           # nodes 7 to 11 not represented
retained_value = X2[3, 0, 1]
X2_shocked = X2 * shock2[:, None, None]
score_full = normal_score(retained_value, pooled_edge_values(X2, nodes_full, range(T)))
score_partial = normal_score(retained_value, pooled_edge_values(X2, nodes_partial, range(T)))
score_shocked = normal_score(X2_shocked[3, 0, 1],
                             pooled_edge_values(X2_shocked, nodes_full, range(T)))
report(14, "C1 and C2", "nodes not represented under partial observation",
       N - len(nodes_partial))
report(14, "C1 and C2", "normal score of the retained value x[3, 0, 1], all 12 nodes represented",
       f"{score_full:.4f}")
report(14, "C1 and C2", "normal score of the same retained value, nodes 7 to 11 not represented",
       f"{score_partial:.4f}")
report(14, "C3", "normal score of the retained value after the period shocks lambda_t, "
       "pooled over all periods", f"{score_shocked:.4f}")
print()

# ---------------------------------------------------------------------------
# Row 15: superobbing onto the model grid, C1 and C2
# ---------------------------------------------------------------------------
site_values = np.array([1.0, 3.0, 8.0])
report(15, "C1 and C2", "number of sites in the grid cell", len(site_values))
report(15, "C1 and C2", "cell value, all three sites represented", f"{site_values.mean():.1f}")
report(15, "C1 and C2", "cell value, the site observing 8 not represented",
       f"{site_values[:2].mean():.1f}")
print()

# ---------------------------------------------------------------------------
# Row 19: nearest-neighbour data association, C1, C2 and C3
# ---------------------------------------------------------------------------
tracks = {"track 0": 0.0, "track 2": 2.0}
REPORT_POSITION = 1.2
REPORT_SHOCK = 0.5


def nearest_track(position, track_set):
    return min(track_set, key=lambda name: abs(position - track_set[name]))


report(19, "C1 and C2", f"report at {REPORT_POSITION:.1f}, both tracks represented, assigned to",
       nearest_track(REPORT_POSITION, tracks))
report(19, "C1 and C2", f"report at {REPORT_POSITION:.1f}, track 2 not represented, assigned to",
       nearest_track(REPORT_POSITION, {"track 0": tracks["track 0"]}))
shocked_position = REPORT_SHOCK * REPORT_POSITION
report(19, "C3", f"report position after a shock of {REPORT_SHOCK:.1f}", f"{shocked_position:.1f}")
report(19, "C3", "shocked report, both tracks represented, assigned to",
       nearest_track(shocked_position, tracks))
print()

# ---------------------------------------------------------------------------
# Row 21: targeted predictors by soft thresholding, C1 and C2
# ---------------------------------------------------------------------------
PENALTY = 0.7


def standardise(Xm):
    return (Xm - Xm.mean(axis=0)) / Xm.std(axis=0)


def lasso_coordinate_descent(Xm, yv, penalty, sweeps=2000):
    """Lasso on standardised columns by cyclic coordinate descent."""
    Xs = standardise(Xm)
    yc = yv - yv.mean()
    n = len(yc)
    b = np.zeros(Xs.shape[1])
    for _ in range(sweeps):
        for k in range(Xs.shape[1]):
            partial_residual = yc - Xs @ b + Xs[:, k] * b[k]
            rho = Xs[:, k] @ partial_residual / n
            b[k] = np.sign(rho) * max(abs(rho) - penalty, 0.0)
    return b


def lasso_optimal(Xm, yv, b, penalty, tol=1e-8):
    """Check the lasso optimality (subgradient) conditions at b."""
    Xs = standardise(Xm)
    yc = yv - yv.mean()
    gradient = Xs.T @ (yc - Xs @ b) / len(yc)
    active = b != 0
    ok_active = np.all(np.abs(gradient[active] - penalty * np.sign(b[active])) < tol)
    ok_zero = np.all(np.abs(gradient[~active]) <= penalty + tol)
    return bool(ok_active and ok_zero)


pool_a = np.c_[series_x0, unrelated]
pool_b = np.c_[series_x0, series_x1, unrelated]
coef_a = lasso_coordinate_descent(pool_a, target_y, PENALTY)
coef_b = lasso_coordinate_descent(pool_b, target_y, PENALTY)
report(21, "C1 and C2", "lasso optimality conditions hold in both pools",
       lasso_optimal(pool_a, target_y, coef_a, PENALTY)
       and lasso_optimal(pool_b, target_y, coef_b, PENALTY))
report(21, "C1 and C2", "series x0 selected from pool A (x0 and three unrelated series)",
       bool(coef_a[0] != 0))
report(21, "C1 and C2", "series x0 selected once x1 enters the pool (pool B)",
       bool(coef_b[0] != 0))
report(21, "C1 and C2", "coefficient of x0 in pool A", f"{coef_a[0]:.4f}")
report(21, "C1 and C2", "coefficient of x0 in pool B", f"{coef_b[0]:.4f}")
print()

# ---------------------------------------------------------------------------
# Row 22: node pruning by mean incoming plus outgoing calls, C1, C2 and C3
# ---------------------------------------------------------------------------
CALL_THRESHOLD = 1.0     # one call per period (per month in the source)
CALL_SHOCK = 0.6


def mean_calls(C, partners, node=0):
    """Mean over periods of the node's outgoing plus incoming calls with the partners."""
    partners = list(partners)
    return float(np.mean([C[t][node, partners].sum() + C[t][partners, node].sum()
                          for t in range(C.shape[0])]))


call_shock = np.where(np.arange(T) < T // 2, CALL_SHOCK, 1.0)
mean_full = mean_calls(calls, range(N))
mean_partial = mean_calls(calls, range(6))
mean_shocked = mean_calls(calls * call_shock[:, None, None], range(N))
report(22, "C1 and C2", "mean calls of node 0 per period, all 12 nodes as partners",
       f"{mean_full:.3f}")
report(22, "C1 and C2", "node 0 kept (mean at least 1), all 12 nodes as partners",
       mean_full >= CALL_THRESHOLD)
report(22, "C1 and C2", "mean calls of node 0 per period, represented partners 0 to 5 only",
       f"{mean_partial:.3f}")
report(22, "C1 and C2", "node 0 kept, represented partners 0 to 5 only",
       mean_partial >= CALL_THRESHOLD)
report(22, "C3", "shocked periods (periods 0 to 5), of 12", int(np.sum(call_shock != 1.0)))
report(22, "C3", f"mean calls of node 0 per period after a shock of {CALL_SHOCK:.1f} "
       "in the shocked periods", f"{mean_shocked:.3f}")
report(22, "C3", "node 0 kept after the shock", mean_shocked >= CALL_THRESHOLD)
print()

# ---------------------------------------------------------------------------
# Row 28: networks estimated from node series, C1 and C2
# ---------------------------------------------------------------------------
def partial_correlation(u, w, Z=None):
    """Correlation of u and w, or of their residuals after regression on Z."""
    if Z is None:
        return float(np.corrcoef(u, w)[0, 1])
    design = np.c_[np.ones(len(u)), Z]
    res_u = u - design @ np.linalg.lstsq(design, u, rcond=None)[0]
    res_w = w - design @ np.linalg.lstsq(design, w, rcond=None)[0]
    return float(np.corrcoef(res_u, res_w)[0, 1])


report(28, "C1 and C2", "partial correlation of nodes a and b, only a and b represented",
       f"{partial_correlation(node_a, node_b):.3f}")
report(28, "C1 and C2", "partial correlation of nodes a and b, node g also represented",
       f"{partial_correlation(node_a, node_b, node_g):.3f}")
print()

# ---------------------------------------------------------------------------
# Fs: symmetric full-mesh input, rows 1 and 12 against the AIMNER flow weight
# ---------------------------------------------------------------------------
off_diagonal = ~np.eye(N, dtype=bool)
log_values = np.zeros_like(D)
log_values[off_diagonal] = np.log(D[off_diagonal])
network_share = D / D.sum()
flow_weight = D / D.sum(axis=1, keepdims=True)
report(1, "Fs", "largest |v_ij - v_ji| after the log of a symmetric full-mesh input",
       f"{np.max(np.abs(log_values - log_values.T)):g}")
report(12, "Fs", "largest |v_ij - v_ji| after division by the network-wide total",
       f"{np.max(np.abs(network_share - network_share.T)):g}")
report("A", "Fs", "largest |w_ij - w_ji| of the AIMNER flow weight on the same input",
       f"{np.max(np.abs(flow_weight - flow_weight.T)):.4f}")
