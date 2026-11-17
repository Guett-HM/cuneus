"""Validation of the model against references that do not come from the model.

Each check compares the code with a closed-form result of diffraction theory, a direct
numerical integral, an exact identity, or a property the decoder must have by construction.
``python -m cuneus validate`` writes docs/VALIDATION.md; tests/test_validation.py runs the
same checks on every push.
"""
import datetime as _dt
import math

import numpy as np
from scipy.special import j1

from . import __version__, provenance
from .alphabet import apsk, equal_discrimination_levels
from .channel import PeriodicChannel
from .equalizer import LinearMMSE, estimate_response
from .lattice import Lattice
from .metrics import mutual_info
from .optics import Reader, frequency_grid


def _result(name, title, reference, measured, limit, passed, measured_text, limit_text):
    return {"name": name, "title": title, "reference": reference, "measured": float(measured),
            "limit": float(limit), "passed": bool(passed), "measured_text": measured_text,
            "limit_text": limit_text}


def coherent_psf_is_airy():
    """Amplitude image of a point through the pupil = 2 J1(v)/v, v = 2 pi NA r / lambda."""
    r_ = Reader()
    m, dx = 1024, 0.02
    FX, FY = frequency_grid(m, m, dx, dx)
    E = np.fft.ifft2(r_.pupil(FX, FY))
    prof = np.real(E[0, :m // 2]) / np.real(E[0, 0])
    r = np.arange(prof.size) * dx
    v = 2 * np.pi * r_.na * r / r_.wavelength
    airy = np.ones_like(v)
    airy[1:] = 2 * j1(v[1:]) / v[1:]
    sel = r < 3 * r_.wavelength / r_.na
    err = float(np.max(np.abs(prof[sel] - airy[sel])))
    return _result("coherent_psf_is_airy", "Coherent image of a point is the Airy amplitude",
                   "2 J1(v)/v (closed form)", err, 0.01, err < 0.01,
                   f"max deviation {err:.4f}", "< 0.01")


def incoherent_mtf_is_analytic():
    """OTF of an aberration-free circular pupil = (2/pi)(acos u - u sqrt(1-u^2)), u = f / (2NA/lambda)."""
    r_ = Reader()
    m, dx = 1024, 0.02
    FX, FY = frequency_grid(m, m, dx, dx)
    O = np.real(r_.otf(FX, FY))[0, :m // 2]
    f = FX[0, :m // 2]
    u = np.clip(f / (2 * r_.cutoff), 0, 1)
    ref = 2 / np.pi * (np.arccos(u) - u * np.sqrt(1 - u * u))
    err = float(np.max(np.abs(O - ref)))
    return _result("incoherent_mtf_is_analytic", "Incoherent transfer function of the pupil",
                   "(2/π)(acos u − u√(1−u²)) (closed form)", err, 0.01, err < 0.01,
                   f"max deviation {err:.4f}", "< 0.01")


def dot_image_matches_direct_integral():
    """Field of one written dot = integral of the Airy amplitude PSF over the dot (direct quadrature)."""
    lat = Lattice.from_square_pitch("hex", 0.26)
    ch = PeriodicChannel(lat, Reader(), n=48, q=12)
    one = np.zeros((ch.n, ch.n), complex)
    one[ch.n // 2, ch.n // 2] = 1.0
    u = ch.field(one)
    iy0, ix0 = ch.iy[ch.n // 2, ch.n // 2], ch.ix[ch.n // 2, ch.n // 2]
    fc, s = ch.reader.cutoff, ch.dot_side
    g = np.linspace(-s / 2, s / 2, 161)
    w = np.full(g.size, g[1] - g[0])
    w[[0, -1]] *= 0.5
    worst = 0.0
    for k in range(0, 5):                          # points along x: 0, a/2, a, 3a/2, 2a
        x = k * lat.spacing / 2
        X, Y = np.meshgrid(x - g, -g)
        rr = np.hypot(X, Y)
        rs = np.maximum(rr, 1e-12)
        h = np.where(rr > 1e-12, fc * j1(2 * np.pi * fc * rs) / rs, np.pi * fc * fc)
        direct = float(w @ h @ w)
        code = u[iy0, (ix0 + int(round(x / ch.dx))) % ch.Mx].real
        worst = max(worst, abs(code - direct))
    peak = float(np.abs(u).max())
    rel = worst / peak
    return _result("dot_image_matches_direct_integral", "Image of one dot vs direct integral",
                   "∫ Airy amplitude over the dot (quadrature)", rel, 0.01, rel < 0.01,
                   f"max deviation {rel:.4f} of the peak", "< 0.01")


def subpixel_placement_is_a_shift():
    """A dot moved by a fraction of a pixel equals the Fourier-shifted dot inside the pupil."""
    lat = Lattice.from_square_pitch("hex", 0.26)
    ch = PeriodicChannel(lat, Reader(), n=24, q=12)
    vals = np.zeros((ch.n, ch.n), complex)
    vals[5, 7] = 1.0
    jit = np.zeros((ch.n, ch.n, 2))
    dx, dy = 0.37 * ch.dx, -0.61 * ch.dy
    jit[5, 7] = (dx, dy)
    a = ch.field(vals, jit)
    b = np.fft.ifft2(np.fft.fft2(ch.comb(vals)) * ch.H * np.exp(-2j * np.pi * (ch.FX * dx + ch.FY * dy)))
    rel = float(np.linalg.norm(a - b) / np.linalg.norm(b))
    return _result("subpixel_placement_is_a_shift", "Sub-pixel dot placement",
                   "exact Fourier shift theorem", rel, 0.005, rel < 0.005,
                   f"relative error {rel:.5f}", "< 0.005")


def parseval_unit_energy():
    """Energy of the image of one dot: Parseval sum over frequencies = sum over pixels."""
    lat = Lattice.from_square_pitch("square", 0.27)
    ch = PeriodicChannel(lat, Reader(), n=24, q=12)
    one = np.zeros((ch.n, ch.n), complex)
    one[0, 0] = 1.0
    u = ch.field(one)
    rel = abs(float(np.sum(np.abs(u) ** 2)) - ch.unit_energy()) / ch.unit_energy()
    return _result("parseval_unit_energy", "Energy of one dot's image (Parseval)",
                   "Σ|u|² over pixels = Σ|H|²/N over frequencies", rel, 1e-9, rel < 1e-9,
                   f"relative difference {rel:.1e}", "< 1e-9")


def mmse_exact_without_noise():
    """With negligible noise and an invertible channel the linear equaliser returns the symbols."""
    worst = 0.0
    for kind in ("square", "hex"):
        lat = Lattice.from_square_pitch(kind, 0.32)
        ch = PeriodicChannel(lat, Reader(), n=24, q=12, photons=1e14)
        cv = apsk()
        eq = LinearMMSE(ch, cv)
        rng = np.random.default_rng(1)
        x = cv[rng.integers(0, 16, (ch.n, ch.n))]
        worst = max(worst, float(np.max(np.abs(eq.soft(ch.field(x)) - x))))
    return _result("mmse_exact_without_noise", "Equaliser inverts the channel without noise",
                   "exact recovery (identity)", worst, 1e-3, worst < 1e-3,
                   f"max symbol error {worst:.1e}", "< 1e-3")


def mmse_is_unbiased():
    """The equaliser output is unbiased: its projection on the true symbols has gain 1."""
    lat = Lattice.from_square_pitch("square", 0.255)          # strong interference, bias matters
    ch = PeriodicChannel(lat, Reader(), n=48, q=12)
    cv = apsk()
    eq = LinearMMSE(ch, cv)
    rng = np.random.default_rng(2)
    num = den = 0.0
    for _ in range(4):
        x = cv[rng.integers(0, 16, (ch.n, ch.n))]
        xh = eq.soft(ch.measure(x, rng))
        num += np.vdot(x - eq.mean, xh - eq.mean)
        den += np.vdot(x - eq.mean, x - eq.mean).real
    gain = abs(num / den - 1)
    return _result("mmse_is_unbiased", "Equaliser output is unbiased",
                   "gain 1 on the true symbols (MMSE theory)", gain, 0.01, gain < 0.01,
                   f"|gain − 1| = {gain:.4f}", "< 0.01")


def response_estimate_converges():
    """Response learnt from known symbols (no noise) equals the true response inside the pupil."""
    lat = Lattice.from_square_pitch("hex", 0.25)
    ch = PeriodicChannel(lat, Reader(), n=48, q=12, photons=1e14)
    cv = apsk()
    rng = np.random.default_rng(3)
    train = []
    for _ in range(2):
        x = cv[rng.integers(0, 16, (ch.n, ch.n))]
        train.append((x, ch.field(x)))
    H = estimate_response(ch, train, iterations=200, tol=1e-8)
    inside = ch.FX ** 2 + ch.FY ** 2 <= ch.reader.cutoff ** 2
    rel = float(np.linalg.norm((H - ch.H)[inside]) / np.linalg.norm(ch.H[inside]))
    return _result("response_estimate_converges", "Response estimated from known symbols",
                   "true response (noise-free training)", rel, 0.01, rel < 0.01,
                   f"relative error {rel:.4f}", "< 0.01")


def defocus_is_phase_only_and_paraxial():
    """Defocus changes only the phase of the pupil; for small angles it equals pi lambda dz f^2."""
    r_ = Reader(defocus=0.3)
    FX, FY = frequency_grid(256, 256, 0.05, 0.05)
    P = r_.pupil(FX, FY)
    inside = FX ** 2 + FY ** 2 <= r_.cutoff ** 2
    amp = float(np.max(np.abs(np.abs(P[inside]) - 1)))
    small = inside & (FX ** 2 + FY ** 2 <= (0.15 * r_.cutoff) ** 2)
    ph = np.angle(P[small])
    par = np.pi * r_.wavelength * r_.defocus * (FX[small] ** 2 + FY[small] ** 2)
    rel = float(np.max(np.abs(ph - par)) / np.max(par))
    worst = max(amp, rel)
    return _result("defocus_is_phase_only_and_paraxial", "Defocus model",
                   "|pupil| = 1; phase → π λ dz f² at small angles", worst, 0.01, worst < 0.01,
                   f"amplitude change {amp:.1e}; paraxial deviation {rel:.4f}", "< 0.01")


def mutual_information_limits():
    """Mutual information: 4 bits for a perfect 16-symbol channel, ~0 for independent symbols."""
    rng = np.random.default_rng(4)
    t = rng.integers(0, 16, 200_000)
    perfect = mutual_info(t, t, 16)
    indep = mutual_info(t, rng.integers(0, 16, t.size), 16)
    err = max(abs(perfect - 4.0), indep)
    return _result("mutual_information_limits", "Mutual information estimator",
                   "log2 16 = 4 bits; 0 for independent symbols", err, 0.01, err < 0.01,
                   f"perfect {perfect:.4f} bits; independent {indep:.4f} bits", "± 0.01")


def lattice_geometry():
    """Hexagonal lattice: six neighbours at distance a and the requested area per symbol."""
    lat = Lattice("hex", 0.0625)
    pos = lat.positions(8).reshape(-1, 2)
    c = pos[3 * 8 + 3]
    d = np.sort(np.hypot(*(pos - c).T))[1:8]
    six = np.allclose(d[:6], lat.spacing) and d[6] > lat.spacing * 1.5
    area = lat.spacing * lat.row_height
    err = abs(area - 0.0625) / 0.0625
    ok = six and err < 1e-12
    return _result("lattice_geometry", "Hexagonal lattice geometry",
                   "6 neighbours at distance a; a·(a√3/2) = area", err, 1e-12, ok,
                   f"{'6' if six else 'wrong'} neighbours; area error {err:.1e}", "exact")


def equal_discrimination_spacing():
    """Levels for noise sigma ∝ sqrt(r) are evenly spaced in sqrt(r) (closed form)."""
    lv = equal_discrimination_levels(8, 0.04, 1.0, lambda r: 0.02 * np.sqrt(r), grid=20001)
    ref = np.linspace(math.sqrt(0.04), 1.0, 8) ** 2
    err = float(np.max(np.abs(lv - ref)))
    return _result("equal_discrimination_spacing", "Level spacing for level-dependent noise",
                   "even in √r when σ ∝ √r (closed form)", err, 1e-4, err < 1e-4,
                   f"max deviation {err:.1e}", "< 1e-4")


CHECKS = (coherent_psf_is_airy, incoherent_mtf_is_analytic, dot_image_matches_direct_integral,
          subpixel_placement_is_a_shift, parseval_unit_energy, mmse_exact_without_noise,
          mmse_is_unbiased, response_estimate_converges, defocus_is_phase_only_and_paraxial,
          mutual_information_limits, lattice_geometry, equal_discrimination_spacing)


def run_all():
    return [c() for c in CHECKS]


def write_report(results, path):
    env = provenance.environment()
    git = provenance.git_state()
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d")
    n_ok = sum(r["passed"] for r in results)
    lines = [
        "# Validation report",
        "",
        f"CUNEUS {__version__}, generated {now} by `python -m cuneus validate`, commit {git['commit']}, "
        f"Python {env['python']}, NumPy {env['numpy']}, SciPy {env['scipy']}.",
        "",
        f"**{n_ok} of {len(results)} checks pass.** Each check compares the code with a reference that "
        "does not come from the code: a closed-form result of diffraction theory, a direct numerical "
        "integral, an exact identity, or a property the decoder has by construction. The same checks "
        "run as tests on every push (`tests/test_validation.py`).",
        "",
        "| Check | Reference | Measured | Limit | Result |",
        "| --- | --- | --- | --- | --- |",
    ]
    for r in results:
        lines.append(f"| {r['title']} | {r['reference']} | {r['measured_text']} | {r['limit_text']} | "
                     f"{'pass' if r['passed'] else '**fail**'} |")
    lines += [
        "",
        "## What these checks do not cover",
        "",
        "They confirm that the code implements its stated model correctly. They do not test the model "
        "against reality: scalar optics, thin two-dimensional dots, a Gaussian model of writing and "
        "placement errors and shot-noise-limited detection remain assumptions until written glass is "
        "measured (Phase 3 of the plan).",
        "",
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
