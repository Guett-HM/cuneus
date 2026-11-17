"""Unit tests of the physical model and the decoders."""
import math

import numpy as np
import pytest

from cuneus.alphabet import apsk, equal_discrimination_levels
from cuneus.channel import PeriodicChannel
from cuneus.equalizer import LinearMMSE, pic
from cuneus.lattice import Lattice
from cuneus.metrics import mutual_info, wilson
from cuneus.optics import Reader


def test_reader_quantities():
    r = Reader()
    assert r.cutoff == pytest.approx(0.9 / 0.405)
    assert r.depth_of_focus == pytest.approx(0.405 / 0.81)
    assert r.dof_density == pytest.approx(15.5, abs=0.1)        # one symbol per ~0.065 um^2


@pytest.mark.parametrize("kind", ["square", "hex"])
def test_lattice_area_is_preserved(kind):
    lat = Lattice.from_square_pitch(kind, 0.26)
    assert lat.spacing * lat.row_height == pytest.approx(0.26 ** 2)
    assert lat.neighbours == (4 if kind == "square" else 6)


def test_lattice_rejects_bad_input():
    with pytest.raises(ValueError):
        Lattice("triangle", 0.1)
    with pytest.raises(ValueError):
        Lattice("hex", -1)


def test_apsk_alphabet():
    cv = apsk()
    assert cv.size == 16
    assert np.allclose(np.sort(np.abs(cv + 1)), [0.5] * 8 + [1.0] * 8)
    assert np.mean(cv) == pytest.approx(-1)                     # centred on the background


def test_levels_constant_noise_are_even():
    lv = equal_discrimination_levels(5, 0.1, 0.9, lambda r: np.full_like(r, 0.01))
    assert np.allclose(lv, np.linspace(0.1, 0.9, 5))


@pytest.fixture(scope="module")
def hex_channel():
    return PeriodicChannel(Lattice.from_square_pitch("hex", 0.26), Reader(), n=24, q=12)


def test_channel_is_linear(hex_channel):
    rng = np.random.default_rng(0)
    a = rng.standard_normal((24, 24)) + 1j * rng.standard_normal((24, 24))
    b = rng.standard_normal((24, 24)) + 1j * rng.standard_normal((24, 24))
    ch = hex_channel
    assert np.allclose(ch.field(a + 2 * b), ch.field(a) + 2 * ch.field(b))


def test_channel_is_periodic(hex_channel):
    """Moving every symbol two rows down moves the image by two row heights."""
    ch = hex_channel
    rng = np.random.default_rng(1)
    x = rng.standard_normal((24, 24)) + 0j
    y1 = ch.field(np.roll(x, 2, axis=0))
    y0 = np.roll(ch.field(x), 2 * ch.q, axis=0)
    assert np.allclose(y0, y1)


def test_channel_rejects_odd_sizes():
    with pytest.raises(ValueError):
        PeriodicChannel(Lattice("hex", 0.07), Reader(), n=25)


def test_noise_level_matches_photons(hex_channel):
    ch = hex_channel
    rng = np.random.default_rng(2)
    zero = np.zeros((24, 24), complex)
    n = ch.measure(zero, rng) - ch.field(zero)
    assert np.var(n) == pytest.approx(ch.noise_var, rel=0.02)


def test_mmse_and_pic_decode_a_comfortable_lattice():
    ch = PeriodicChannel(Lattice.from_square_pitch("hex", 0.30), Reader(), n=24, q=12)
    cv = apsk()
    eq = LinearMMSE(ch, cv)
    rng = np.random.default_rng(3)
    s = rng.integers(0, 16, (24, 24))
    y = ch.measure(cv[s], rng)
    d = eq.decide(eq.soft(y))
    assert np.mean(d != s) < 0.01
    d2, z = pic(ch, y, d, cv, iterations=3)
    assert np.mean(d2 != s) < 0.01
    assert z.shape == (24, 24)


def test_pic_never_increases_the_residual():
    ch = PeriodicChannel(Lattice.from_square_pitch("square", 0.235), Reader(), n=24, q=12)
    cv = apsk()
    rng = np.random.default_rng(4)
    s = rng.integers(0, 16, (24, 24))
    y = ch.measure(cv[s], rng)
    d = LinearMMSE(ch, cv).decide(LinearMMSE(ch, cv).soft(y))
    d2, _ = pic(ch, y, d, cv, iterations=6)
    r0 = np.linalg.norm(y - ch.field(cv[d]))
    r1 = np.linalg.norm(y - ch.field(cv[d2]))
    assert r1 <= r0 + 1e-9


def test_mutual_info_and_wilson():
    t = np.arange(16).repeat(100)
    assert mutual_info(t, t, 16) == pytest.approx(4.0)
    lo, hi = wilson(5, 100)
    assert lo < 0.05 < hi
    assert wilson(0, 0) == (0.0, 1.0)
    assert math.isclose(sum(wilson(50, 100)), 1.0, rel_tol=1e-9)
