"""Coherent readout of a periodic lattice of written dots (high-density tier).

The written field is  1 + sum_k x_k * dot(r - r_k), with x_k = a e^{i phi} - 1 the symbol
value (alphabet.apsk). Imaging is linear in the field, so the measured image is
y = h * comb + noise, where comb holds the symbol values at the dot positions and h is the
image of one dot (dot shape filtered by the pupil). The lattice is periodic (a torus of
n x n symbols), so there are no edges: every symbol has a full neighbourhood.

The dot is a square of side s; its spectrum is taken analytically, so dots on different
lattices have exactly the same area and the same strength. Positions are placed on a fine
grid of q pixels per lattice spacing (placement errors are rounded to that grid).
Noise: complex Gaussian, the same number of photons per symbol for every lattice."""
import math

import numpy as np

from .optics import frequency_grid


class PeriodicChannel:
    def __init__(self, lattice, reader, n=48, q=24, dot_side=None, photons=64_000.0):
        if n % 2 or q % 2:
            raise ValueError("n and q must be even")
        self.lattice, self.reader, self.n, self.q = lattice, reader, n, q
        self.photons = photons
        a, h = lattice.spacing, lattice.row_height
        self.dx, self.dy = a / q, h / q
        self.Mx = self.My = n * q
        self.shift_px = int(round(lattice.row_shift / self.dx))
        self.FX, self.FY = frequency_grid(self.Mx, self.My, self.dx, self.dy)
        self.dot_side = dot_side if dot_side is not None else 0.6 * math.sqrt(lattice.cell_area)
        s = self.dot_side
        dot = s * s * np.sinc(s * self.FX) * np.sinc(s * self.FY) / (self.dx * self.dy)
        self.P = reader.pupil(self.FX, self.FY)
        self.H = dot * self.P                                  # comb -> field
        self.noise_var = q * q / photons                       # per fine pixel (complex)
        j, i = np.meshgrid(np.arange(n), np.arange(n), indexing="ij")
        self.iy = j * q
        self.ix = (i * q + (j % 2) * self.shift_px) % self.Mx

    # ---- forward model ----------------------------------------------------
    def comb(self, values, jitter=None):
        """Symbol values placed on the fine grid. jitter (n, n, 2) in um moves each dot off its
        nominal site; sub-pixel offsets are split bilinearly over the four nearest pixels, which
        is exact to well below 0.1% inside the pupil because the grid is ~10x finer than the
        optical cutoff."""
        c = np.zeros((self.My, self.Mx), complex)
        if jitter is None:
            np.add.at(c, (self.iy, self.ix), values)
            return c
        fx = self.ix + jitter[..., 0] / self.dx
        fy = self.iy + jitter[..., 1] / self.dy
        x0, y0 = np.floor(fx).astype(int), np.floor(fy).astype(int)
        tx, ty = fx - x0, fy - y0
        for oy, wy in ((0, 1 - ty), (1, ty)):
            for ox, wx in ((0, 1 - tx), (1, tx)):
                np.add.at(c, ((y0 + oy) % self.My, (x0 + ox) % self.Mx), values * wx * wy)
        return c

    def field(self, values, jitter=None, H=None):
        H = self.H if H is None else H
        return np.fft.ifft2(np.fft.fft2(self.comb(values, jitter)) * H)

    def measure(self, values, rng, jitter=None):
        y = self.field(values, jitter)
        s = math.sqrt(self.noise_var / 2)
        return y + s * (rng.standard_normal(y.shape) + 1j * rng.standard_normal(y.shape))

    # ---- helpers ------------------------------------------------------------
    def unit_energy(self, H=None):
        """Energy sum |u|^2 of the image u of one unit dot (Parseval)."""
        H = self.H if H is None else H
        return float(np.sum(np.abs(H) ** 2)) / (self.Mx * self.My)

    def sample(self, img):
        """Values of an image at the nominal symbol positions, shape (n, n)."""
        return img[self.iy, self.ix]
