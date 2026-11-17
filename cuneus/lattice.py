"""Square and hexagonal lattices, described by the area per symbol.

Both lattices are stored as rows: row j sits at y = j*h and its symbols at
x = i*a + (j odd) * shift. Square: a = h, shift = 0. Hexagonal: h = a*sqrt(3)/2,
shift = a/2, so that every symbol has six nearest neighbours at distance a.
Comparisons are always made at the same area per symbol (the same density).
"""
import math
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Lattice:
    kind: str            # "square" or "hex"
    cell_area: float     # um^2 per symbol

    def __post_init__(self):
        if self.kind not in ("square", "hex"):
            raise ValueError(f"unknown lattice {self.kind!r}")
        if self.cell_area <= 0:
            raise ValueError("cell_area must be positive")

    @classmethod
    def from_square_pitch(cls, kind, pitch):
        """Lattice of the given kind with the density of a square lattice of this pitch."""
        return cls(kind, pitch * pitch)

    @property
    def spacing(self):
        """Nearest-neighbour distance a (um)."""
        if self.kind == "square":
            return math.sqrt(self.cell_area)
        return math.sqrt(2 * self.cell_area / math.sqrt(3))

    @property
    def row_height(self):
        return self.spacing if self.kind == "square" else self.spacing * math.sqrt(3) / 2

    @property
    def row_shift(self):
        """Horizontal offset of odd rows (um)."""
        return 0.0 if self.kind == "square" else self.spacing / 2

    @property
    def neighbours(self):
        return 4 if self.kind == "square" else 6

    def positions(self, n):
        """Nominal (x, y) positions of an n x n patch (n rows of n symbols), shape (n, n, 2)."""
        j, i = np.meshgrid(np.arange(n), np.arange(n), indexing="ij")
        x = i * self.spacing + (j % 2) * self.row_shift
        y = j * self.row_height
        return np.stack([x, y], -1)

    def brillouin_zone(self):
        """Corners (cycles/um) of the first Brillouin zone: the frequency cell of the lattice.
        Square: a square of side 1/a. Hexagonal (rows along x): a hexagon with corners on the
        fx axis at 2/(3a). Its area is 1 / cell_area."""
        a = self.spacing
        if self.kind == "square":
            h = 1 / (2 * a)
            return np.array([[-h, -h], [h, -h], [h, h], [-h, h]])
        r = 2 / (3 * a)
        ang = np.deg2rad(np.arange(0, 360, 60))
        return np.stack([r * np.cos(ang), r * np.sin(ang)], 1)

    def zone_fraction_outside_pupil(self, cutoff, samples=1201):
        """Fraction of the Brillouin zone farther than `cutoff` from the origin.

        The zone holds exactly one frequency per symbol degree of freedom, and every point of
        it is closer to the origin than any of its aliases, so a zone frequency outside the
        pupil disc is never seen by the reader: that fraction of the written information
        cannot be recovered by a linear decoder."""
        from matplotlib.path import Path
        zone = self.brillouin_zone()
        r = float(np.max(np.hypot(*zone.T)))
        g = np.linspace(-r, r, samples)
        X, Y = np.meshgrid(g, g)
        inside = Path(zone).contains_points(np.c_[X.ravel(), Y.ravel()]).reshape(X.shape)
        outside = inside & (X ** 2 + Y ** 2 > cutoff ** 2)
        return float(np.sum(outside) / np.sum(inside))

    def label(self):
        return f"{self.kind} lattice, {self.cell_area:.4f} um^2 per symbol, spacing {self.spacing * 1000:.0f} nm"
