"""CUNEUS: optics-aware alphabets for archival data storage in glass.

The format of a storage medium (lattice, symbol alphabet, decoder) is computed from the
optics of the reader instead of being drawn by hand. This package holds the physical model
(``optics``, ``lattice``, ``alphabet``, ``channel``), the decoders (``equalizer``) and the
experiments that test the design rules.
"""
import os

__version__ = "0.1.0"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
RESULTS_QUICK = os.path.join(ROOT, "results_quick")
