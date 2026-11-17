"""Information and statistics."""
import math

import numpy as np


def mutual_info(x, y, m):
    """Mutual information (bits) between transmitted and decided symbols, from counts."""
    C = np.zeros((m, m))
    np.add.at(C, (np.ravel(x), np.ravel(y)), 1)
    P = C / C.sum()
    px, py = P.sum(1, keepdims=True), P.sum(0, keepdims=True)
    nz = P > 0
    return float(np.sum(P[nz] * np.log2(P[nz] / (px @ py)[nz])))


def wilson(k, n, z=1.96):
    """95% Wilson interval for a proportion k/n."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))
