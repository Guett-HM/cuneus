"""Decoders for the periodic coherent channel.

* ``estimate_response``: the image of one dot, estimated from frames of known symbols
  (training frames), so the decoder does not need to know the optics in advance.
* ``LinearMMSE``: exact linear minimum-mean-square-error equaliser for a periodic lattice
  (symbols with a known mean; the zero-mean part is equalised).
  The lattice is split into two rectangular sublattices (even rows A, odd rows B); in the
  Fourier domain every frequency of the sublattices couples to a group of aliases, and the
  equaliser solves a 2 x 2 system per frequency. The output is unbiased.
* ``pic``: parallel interference cancellation (decision feedback): subtract the image of all
  decided neighbours and re-estimate every symbol with a matched filter.
"""
import numpy as np


def estimate_response(channel, training, radius=1.0, iterations=80, tol=1e-4):
    """Least-squares estimate of the comb -> image transfer from (values, y) training pairs.

    Model: H(f) = pupil disc(f) x G(f). The disc (|f| <= NA/lambda) is known from the
    reader's NA; G is everything else (dot shape, defocus, aberrations), a smooth function
    of frequency, i.e. the transform of a kernel confined to a disc of the given radius (um).
    With 1 um this leaves ~100-200 complex unknowns instead of one per frequency, so a few
    thousand known symbols give a precise estimate. Solved by conjugate gradients on the
    normal equations. Returns H on the channel's frequency grid."""
    ch = channel
    num = np.zeros((ch.My, ch.Mx), complex)
    den = np.zeros((ch.My, ch.Mx))
    # The mean of the symbols only shows at the reciprocal-lattice frequencies (inside the
    # pupil: f = 0). Fitting the zero-mean part and skipping those few frequencies keeps the
    # normal equations well conditioned; G is smooth, so nothing is lost.
    lattice_lines = np.abs(np.fft.fft2(ch.comb(np.ones((ch.n, ch.n))))) > 1e-6 * ch.n ** 2
    for values, y in training:
        C = np.fft.fft2(ch.comb(values - values.mean()))
        C[lattice_lines] = 0.0
        num += np.conj(C) * np.fft.fft2(y)
        den += np.abs(C) ** 2
    B = (ch.FX ** 2 + ch.FY ** 2 <= ch.reader.cutoff ** 2).astype(float)
    yy, xx = np.meshgrid(np.fft.fftfreq(ch.My, 1 / ch.My) * ch.dy,
                         np.fft.fftfreq(ch.Mx, 1 / ch.Mx) * ch.dx, indexing="ij")
    M = (xx ** 2 + yy ** 2 <= radius ** 2).astype(float)
    scale = 1.0 / den.max()

    def normal(g):
        return M * np.fft.ifft2(B * den * scale * np.fft.fft2(M * g))

    b = M * np.fft.ifft2(B * num * scale)
    h = np.zeros_like(b)
    r = b.copy()
    p = r.copy()
    rs = np.vdot(r, r).real
    rs0 = rs
    for it in range(iterations):
        Ap = normal(p)
        alpha = rs / np.vdot(p, Ap).real
        h += alpha * p
        r -= alpha * Ap
        rs_new = np.vdot(r, r).real
        if rs_new < tol * tol * rs0:
            break
        p = r + (rs_new / rs) * p
        rs = rs_new
    estimate_response.iterations_used = it + 1
    return B * np.fft.fft2(M * h)


class LinearMMSE:
    def __init__(self, channel, alphabet, H=None):
        ch = self.ch = channel
        self.alphabet = np.asarray(alphabet)
        H = ch.H if H is None else H
        n, q = ch.n, ch.q
        self.nh = n // 2
        iy, ix = np.meshgrid(np.arange(ch.My), np.arange(ch.Mx), indexing="ij")
        phB = np.exp(-2j * np.pi * (ix * ch.shift_px / ch.Mx + iy * q / ch.My))
        self.hA, self.hB = self._group(H), self._group(H * phB)
        # symbols have a known mean (APSK minus the background is centred on -1); the
        # equaliser works on the zero-mean part and adds the mean back
        self.mean = complex(np.mean(self.alphabet))
        self.mean_field = channel.field(np.full((n, n), self.mean), H=H)
        prior = float(np.mean(np.abs(self.alphabet - self.mean) ** 2))
        lam = ch.noise_var * ch.Mx * ch.My / (prior * n * self.nh)
        s11 = np.sum(np.abs(self.hA) ** 2, -1)
        s22 = np.sum(np.abs(self.hB) ** 2, -1)
        s12 = np.sum(np.conj(self.hA) * self.hB, -1)
        self.g11, self.g22, self.g12 = s11 + lam, s22 + lam, s12
        self.det = self.g11 * self.g22 - np.abs(s12) ** 2
        # bias of the MMSE estimate (mean diagonal of (G^H G + lam I)^-1 G^H G), removed below
        self.biasA = float(np.mean(((s22 + lam) * s11 - np.abs(s12) ** 2) / self.det).real)
        self.biasB = float(np.mean(((s11 + lam) * s22 - np.abs(s12) ** 2) / self.det).real)

    def _group(self, Z):
        """(My, Mx) -> (n/2, n, aliases): Fy = my + (n/2) ay, Fx = mx + n ax."""
        q, n, nh = self.ch.q, self.ch.n, self.nh
        return Z.reshape(2 * q, nh, q, n).transpose(1, 3, 0, 2).reshape(nh, n, 2 * q * q)

    def soft(self, y):
        """Unbiased linear estimates of the symbol values, shape (n, n)."""
        Y = self._group(np.fft.fft2(y - self.mean_field))
        bA = np.sum(np.conj(self.hA) * Y, -1)
        bB = np.sum(np.conj(self.hB) * Y, -1)
        XA = (self.g22 * bA - self.g12 * bB) / self.det
        XB = (self.g11 * bB - np.conj(self.g12) * bA) / self.det
        x = np.empty((self.ch.n, self.ch.n), complex)
        x[0::2] = np.fft.ifft2(XA) / self.biasA
        x[1::2] = np.fft.ifft2(XB) / self.biasB
        return x + self.mean

    def decide(self, x):
        return np.argmin(np.abs(x[..., None] - self.alphabet), -1)


def pic(channel, y, decisions, alphabet, H=None, iterations=2):
    """Parallel interference cancellation with a matched filter.

    Each pass subtracts the image of every decided symbol except the one being estimated
    and re-decides it. The receiver keeps the decisions that best explain the measured
    image (smallest residual energy), so a pass that propagates errors cannot make the
    result worse. Returns (decisions, soft values)."""
    H = channel.H if H is None else H
    alphabet = np.asarray(alphabet)
    E = channel.unit_energy(H)
    d = decisions.copy()
    residual = y - channel.field(alphabet[d], H=H)
    best = (float(np.vdot(residual, residual).real), d, alphabet[d])
    for _ in range(iterations):
        mf = np.fft.ifft2(np.conj(H) * np.fft.fft2(residual))
        z = alphabet[d] + channel.sample(mf) / E
        d = np.argmin(np.abs(z[..., None] - alphabet), -1)
        residual = y - channel.field(alphabet[d], H=H)
        err = float(np.vdot(residual, residual).real)
        if err < best[0]:
            best = (err, d, z)
    return best[1], best[2]
