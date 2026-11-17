"""Symbol alphabets.

A coherent alphabet lists the complex field written by each symbol, relative to the
unwritten background: c = a * exp(i phi) - 1 inside the dot. An intensity alphabet lists
reflectance levels for bright-field readers.
"""
import numpy as np


def apsk(n_phase=8, amplitudes=(1.0, 0.5)):
    """APSK alphabet of 4D-VODS: n_phase phases (offset by pi/n_phase) on each amplitude ring.
    Symbol b -> ring b // n_phase, phase b % n_phase (Gray mapping is applied to the bits,
    not to the symbol index). Returns c = a e^{i phi} - 1 for every symbol."""
    b = np.arange(n_phase * len(amplitudes))
    a = np.asarray(amplitudes)[b // n_phase]
    phi = 2 * np.pi * (b % n_phase) / n_phase + np.pi / n_phase
    return a * np.exp(1j * phi) - 1.0


def equal_discrimination_levels(m, r_min, r_max, sigma, grid=4001):
    """Reflectance levels for a reader whose noise depends on the level.

    sigma(r) is the standard deviation of the measured value at reflectance r. The levels
    are placed so that the integral of dr / sigma(r) is the same between neighbours, which
    makes every pair of adjacent levels equally easy to tell apart. With constant noise this
    gives evenly spaced levels."""
    r = np.linspace(r_min, r_max, grid)
    inv = 1.0 / np.asarray(sigma(r), dtype=float)
    F = np.concatenate([[0.0], np.cumsum(0.5 * (inv[1:] + inv[:-1]) * np.diff(r))])
    return np.interp(np.linspace(0.0, F[-1], m), F, r)
