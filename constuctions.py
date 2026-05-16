from scipy.optimize import linprog
from fractions import Fraction
from math import comb
import numpy as np
import itertools
import math

# ======================================================================================================================================================== #
# Auxiliary function returning the length of the vector storing
# the coefficients of the linear programming variables, where:
# n - total number of shares in the cryptographic scheme
def compute_coefficient_vector_length(n):
    return 2 * (n + 1)  # two sets of variables (x_j and y_j), indexed from 0
# ======================================================================================================================================================== #


# ======================================================================================================================================================== #
# Function returning the vector "z" filled with coefficients of the objective
# function variables x_j (at indices [0, ..., n]) and coefficients of
# variables y_j (at indices [n+1, ..., 2n + 1]), where:
# k - minimum number of shares required to decrypt the message
# n - total number of shares in the cryptographic scheme
def create_objective_function_coefficients(k, n):
    vector_length = compute_coefficient_vector_length(n)
    z = np.zeros(vector_length)  # create and initialize with zeros a vector capable of storing all LP variables

    for j in range(n - k + 1):
        coefficient = math.comb(n - k, j) / math.comb(n, j)  # coefficient computed as the ratio of corresponding binomial coefficients
        z[j] = -coefficient        # linprog performs minimization, therefore the coefficient is negated
        z[n + 1 + j] = coefficient # coefficient stored in the vector for y_j variables

    return z
# ======================================================================================================================================================== #


# ======================================================================================================================================================== #
# Function returning the bounds for the linear programming variables, where:
# n - total number of shares in the cryptographic scheme
def create_variable_bounds(n):
    bounds = [(0, None)] * compute_coefficient_vector_length(n)  # each variable must be non-negative

    return bounds
# ======================================================================================================================================================== #


# ======================================================================================================================================================== #
# Function returning coefficient matrix "a" and constraint values "b" for a linear programming problem, where:
# k - minimum number of shares required to decrypt the message
# n - total number of shares in the cryptographic scheme
def create_constraints_coefficients_and_values(k, n):
    num_variables = compute_coefficient_vector_length(n)
    num_equations = k + 2  # k security equations + 2 normalization equations

    a = np.zeros((num_equations, num_variables), dtype=float)  # initialize coefficient matrix
    b = np.zeros(num_equations, dtype=float)  # initialize constraint values vector

    for l in range(k):  # security constraints for l = 0..k-1
        coefficient_vector = np.zeros(num_variables, dtype=float)
        j_min = l
        j_max = n - k + l + 1

        for j in range(j_min, j_max + 1):
            numerator = math.comb(n - k + 1, j - l)
            denominator = math.comb(n, j)
            coefficient = numerator / denominator

            coefficient_vector[j] = coefficient
            coefficient_vector[n + 1 + j] = -coefficient

        a[l, :] = coefficient_vector
        b[l] = 0.0

    sum_x = np.zeros(num_variables, dtype=float)
    sum_x[0: n + 1] = 1.0
    a[k, :] = sum_x
    b[k] = 1.0

    sum_y = np.zeros(num_variables, dtype=float)
    sum_y[n + 1: 2 * (n + 1)] = 1.0
    a[k + 1, :] = sum_y
    b[k + 1] = 1.0

    return a, b
# ======================================================================================================================================================== #


# ======================================================================================================================================================== #
# Function solving the linear programming problem and returning the optimal value
# for the gamma optimization problem, where:
# k - minimum number of shares required to decrypt the message
# n - total number of shares in the cryptographic scheme
def solve_L(k, n):
    c = create_objective_function_coefficients(k, n)
    A, b = create_constraints_coefficients_and_values(k, n)
    bounds = create_variable_bounds(n)

    result = linprog(c, A_eq=A, b_eq=b, bounds=bounds, method="highs")

    L_opt = -result.fun

    return L_opt, result.x
# ======================================================================================================================================================== #


# ======================================================================================================================================================== #
# Function returning a fraction based on a floating-point number and tolerance, where:
# x - floating-point number
# tol - tolerance
def convert_to_fraction(x, tol=1e-8):
    if abs(x) < tol:
        return Fraction(0)
    return Fraction(str(float(x))).limit_denominator(1000000)
# ======================================================================================================================================================== #


# ======================================================================================================================================================== #
# Function returning the minimal value of m for the given linear programming coefficients, where:
# n - total number of shares in the cryptographic scheme
# w - vector of values computed using linear programming
def compute_minimal_m(n, w):
    w_fraction = [convert_to_fraction(a) for a in w]  # convert floating-point numbers to fractions
    m_candidates = []

    for j, wj in enumerate(w_fraction):
        if wj == 0:
            continue

        p, q = wj.numerator, wj.denominator
        C = comb(n, j)
        g = math.gcd(p, C)
        m_j = q * (C // g)
        m_candidates.append(m_j)

    if not m_candidates:
        return 1

    m = m_candidates[0]
    for value in m_candidates[1:]:
        m = (m * value) // math.gcd(m, value)

    return m
# ======================================================================================================================================================== #


# ======================================================================================================================================================== #
# Function returning the basis matrix of the scheme based on the linear programming solution and a given m, where:
# n - total number of shares in the cryptographic scheme
# w - vector of values computed using linear programming
# m - width of the matrix
def create_basis_matrix(n, w, m):
    w_fraction = [convert_to_fraction(wj) for wj in w]
    columns = []
    total_columns = 0

    for j, wj_fraction in enumerate(w_fraction):
        if wj_fraction == 0:
            continue

        total = int(wj_fraction * m)
        C = comb(n, j)

        if total % C != 0:
            raise ValueError(f"total={total} not divisible by C={C} for j={j}")

        per_vector = total // C

        for indices in itertools.combinations(range(n), j):
            v = np.zeros(n, dtype=int)
            v[list(indices)] = 1
            columns.extend([v] * per_vector)

        total_columns += total

    if total_columns != m:
        raise ValueError(f"Total number of columns {total_columns} ≠ m={m}")

    return np.array(columns).T
# ======================================================================================================================================================== #


# ======================================================================================================================================================== #
# Function returning the basis matrices B0 and B1 of the scheme based on both sets of
# linear programming solutions for a small m, where:
# n - total number of shares in the cryptographic scheme
# x_values - values computed using linear programming for matrix B0
# y_values - values computed using linear programming for matrix B1
def create_matrix_set(n, x_values, y_values):
    m_x = compute_minimal_m(n, x_values)
    m_y = compute_minimal_m(n, y_values)
    m = (m_x * m_y) // math.gcd(m_x, m_y)

    G0 = create_basis_matrix(n, x_values, m)
    G1 = create_basis_matrix(n, y_values, m)

    return G0, G1, m
# ======================================================================================================================================================== #


# ======================================================================================================================================================== #
# Function returning the basis matrices of an optimal (k, n) scheme with optimal contrast, where:
# k - minimum number of shares required to decrypt the message
# n - total number of shares in the cryptographic scheme
def create_optimal_scheme(k, n):
    result = solve_L(k, n)[1]

    x_j = result[0 : n + 1]
    y_j = result[n + 1 : 2 * (n + 1)]

    m_x = compute_minimal_m(n, x_j)
    m_y = compute_minimal_m(n, y_j)
    m = (m_x * m_y) // math.gcd(m_x, m_y)

    B0 = create_basis_matrix(n, x_j, m)
    B1 = create_basis_matrix(n, y_j, m)

    return B0, B1
# ======================================================================================================================================================== #
