"""Exact arithmetic for Supplementary Section S1.7, not a performance experiment."""
from fractions import Fraction as F
from pathlib import Path
import json

def interaction(B):
    n, g = len(B), len(B[0])
    r = list(map(sum, B))
    c = [sum(row[x] for row in B) for x in range(g)]
    return [[sum((F(B[i][x], r[i]) * F(B[j][x], c[x]-B[i][x])
                  for x in range(g) if r[i] and B[i][x] and c[x]>B[i][x]), F(0))
             if i != j else F(0) for j in range(n)] for i in range(n)]

def two_step(B):
    n, g = len(B), len(B[0])
    r = list(map(sum, B))
    c = [sum(row[x] for row in B) for x in range(g)]
    return [[sum((F(B[i][x], r[i])*F(B[j][x], c[x])
                  for x in range(g) if r[i] and B[i][x] and c[x]), F(0))
             for j in range(n)] for i in range(n)]

def newman(B):
    n, g = len(B), len(B[0])
    c = [sum(row[x] for row in B) for x in range(g)]
    return [[sum((F(B[i][x]*B[j][x], c[x]-1)
                  for x in range(g) if c[x]>1), F(0))
             if i != j else F(0) for j in range(n)] for i in range(n)]

def verify():
    B = [[8, 2], [4, 6], [8, 2]]
    P, Q = interaction(B), two_step(B)
    altered = [[8, 2], [4, 6], [18, 2]]
    assert P[0][1] == F(5, 12) and P[1][0] == F(1, 2)
    assert interaction(altered)[0][1] == F(13, 44)
    after = Q[0][1]/(1-Q[0][0])
    assert after == F(7, 16) and after != P[0][1]
    assert all(sum(row) == 1 for row in P)
    assert interaction([[7*x for x in row] for row in B]) == P

    binary = [[1, 1, 0], [1, 0, 1], [1, 1, 1], [0, 0, 1]]
    PB, W = interaction(binary), newman(binary)
    for i, row in enumerate(W):
        assert sum(row) == sum(binary[i])
        assert PB[i] == [w/sum(row) for w in row]

    B4 = [[8, 2], [4, 6], [3, 4], [5, 2]]
    redistributed = [[8, 2], [4, 6], [5, 1], [3, 5]]
    closed = B4[:2] + [[sum(row[x] for row in B4[2:]) for x in range(2)]]
    assert interaction(B4)[0][1] == interaction(redistributed)[0][1]
    assert interaction(B4)[0][1] == interaction(closed)[0][1]
    same_rest_size = B4[:2] + [[6, 8]]
    assert sum(closed[-1]) == sum(same_rest_size[-1])
    assert interaction(closed)[0][1] == F(11, 30)
    assert interaction(same_rest_size)[0][1] == F(71, 175)
    assert interaction(closed)[0][1] != interaction(same_rest_size)[0][1]

    same_composition = [[16, 4], [8, 2], [24, 6]]
    PC = interaction(same_composition)
    masses = list(map(sum, same_composition))
    for i in range(3):
        for j in range(3):
            if i != j: assert PC[i][j] == F(masses[j], sum(masses)-masses[i])

    zero_cases = [[1, 1], [1, 0], [0, 0]]
    PZ = interaction(zero_cases)
    assert sum(PZ[0]) == F(1, 2)
    assert sum(PZ[1]) == 1
    assert sum(PZ[2]) == 0
    assert all(0 <= sum(row) <= 1 for row in PZ)
    return dict(status='passed',
        scope='Exact rational arithmetic for structural identities, not empirical estimates',
        binary_newman_identity=True, positive_denominator_row_sums=True,
        common_positive_scale_invariance=True,
        outside_subgroup_redistribution_invariance=True, rest_closure=True,
        combined_rest_size_alone_insufficient=True,
        equal_composition_target_mass_identity=True, zero_denominator_convention=True,
        illustration=dict(P_ij=str(P[0][1]), P_ji=str(P[1][0]),
                          changed_third_node=str(interaction(altered)[0][1]),
                          diagonal_removed_after_mixture=str(after)))

if __name__ == '__main__':
    result = verify()
    Path(__file__).with_name('interaction_projection_checks.json').write_text(
        json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
