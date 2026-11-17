"""Scalar Fourier optics of the reader.

All lengths are in micrometres. A reader is described by its wavelength, numerical
aperture and, optionally, a defocus. Coherent readout (interferometric, high-density tier)
filters the written field with the pupil; incoherent bright-field readout (low-cost tier)
filters the written intensity with the optical transfer function, the normalised
autocorrelation of the pupil.
"""
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Reader:
    wavelength: float = 0.405     # um
    na: float = 0.90
    defocus: float = 0.0          # um, in the medium of index n
    n: float = 1.0                # refractive index on the object side

    @property
    def cutoff(self):
        """Coherent cut-off frequency NA / lambda (cycles per um)."""
        return self.na / self.wavelength

    @property
    def depth_of_focus(self):
        """lambda / NA^2 (um)."""
        return self.wavelength / self.na ** 2

    @property
    def dof_density(self):
        """Complex degrees of freedom per um^2 of a coherent image: pi (NA/lambda)^2."""
        return np.pi * self.cutoff ** 2

    def pupil(self, FX, FY):
        """Complex pupil on a grid of spatial frequencies (cycles/um).

        Defocus uses the exact (non-paraxial) phase  2 pi dz (n/lambda) (1 - cos theta),
        with sin theta = lambda f / n."""
        f2 = FX ** 2 + FY ** 2
        inside = f2 <= self.cutoff ** 2
        if self.defocus == 0.0:
            return inside.astype(complex)
        s2 = np.clip(f2 * (self.wavelength / self.n) ** 2, 0.0, 1.0)
        phase = 2 * np.pi * self.defocus * self.n / self.wavelength * (1 - np.sqrt(1 - s2))
        return inside * np.exp(1j * phase)

    def otf(self, FX, FY):
        """Incoherent OTF on the same (periodic) frequency grid, normalised to 1 at f = 0."""
        P = self.pupil(FX, FY)
        psf = np.abs(np.fft.ifft2(P)) ** 2
        O = np.fft.fft2(psf)
        return O / O.flat[0]


def frequency_grid(nx, ny, dx, dy):
    """FFT-ordered spatial-frequency grids (cycles/um) for an ny x nx array of pixels dx x dy."""
    fx, fy = np.fft.fftfreq(nx, d=dx), np.fft.fftfreq(ny, d=dy)
    return np.meshgrid(fx, fy)
