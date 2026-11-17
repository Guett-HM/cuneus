"""Phase 1 experiments of the high-density (coherent) tier.

lattice    square vs hexagonal lattice at equal density, for three conditions:
           ideal      decoder knows the exact response, dots exactly on their sites
           estimated  response estimated from training frames of known symbols
           realistic  estimated response and dot placement errors (go/no-go condition)
           and two decoders (linear MMSE; MMSE followed by interference cancellation).
placement  best density vs dot placement error (what the writer must achieve).
focus      density vs defocus, with a response fixed at best focus or re-estimated
           from training symbols read at the same focus.

Every configuration uses its own deterministic random stream, so results do not depend
on the order or the number of worker processes.
"""
import math
import os
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from .alphabet import apsk
from .channel import PeriodicChannel
from .equalizer import LinearMMSE, estimate_response, pic
from .lattice import Lattice
from .metrics import mutual_info, wilson
from .optics import Reader

KINDS = ("square", "hex")
CONDITIONS = ("ideal", "estimated", "realistic")

DEFAULTS = {
    "wavelength": 0.405, "na": 0.90, "n": 48, "q": 12, "photons": 64_000.0,
    "writing_variability": 0.10, "placement_error": 0.05, "training_frames": 2,
    "frames": 6, "pic_iterations": 16, "estimate_radius": 1.0, "seed": 2026,
}
QUICK = {"n": 24, "frames": 2, "pic_iterations": 8}


def _stream(params, *keys):
    return np.random.default_rng([params["seed"], *[int(round(k)) + 1_000_000 for k in keys]])


def _frame(channel, alphabet, rng, writing, placement):
    n = channel.n
    sym = rng.integers(0, len(alphabet), (n, n))
    g = 1 + writing / math.sqrt(2) * (rng.standard_normal((n, n)) + 1j * rng.standard_normal((n, n)))
    jitter = placement * rng.standard_normal((n, n, 2)) if placement else None
    return sym, channel.measure(g * alphabet[sym], rng, jitter)


def _decode_stats(sym, dec, m, area):
    t, e = np.concatenate(sym), np.concatenate(dec)
    k = int(np.sum(t != e))
    bits = mutual_info(t, e, m)
    lo, hi = wilson(k, t.size)
    return {"ser": k / t.size, "ser_ci95": [lo, hi], "bits_per_symbol": bits,
            "density_bits_um2": bits / area}


def simulate(kind, pitch, params, *, placement=0.0, estimate=True, train_defocus=None,
             defocus=0.0, key=()):
    """Decode `frames` random frames; return statistics for the linear and the iterative
    decoder. placement: rms dot placement error per axis (um). estimate: the decoder learns
    the response from training frames (read at train_defocus, default: the same focus)."""
    alphabet = apsk()
    lattice = Lattice.from_square_pitch(kind, pitch)
    reader = Reader(params["wavelength"], params["na"], defocus)
    ch = PeriodicChannel(lattice, reader, n=params["n"], q=params["q"], photons=params["photons"])
    rng = _stream(params, KINDS.index(kind), pitch * 1e4, placement * 1e5, estimate,
                  defocus * 1e4, -1 if train_defocus is None else train_defocus * 1e4, *key)
    w = params["writing_variability"]
    H = None
    if estimate:
        tdz = defocus if train_defocus is None else train_defocus
        tch = ch if tdz == defocus else PeriodicChannel(
            lattice, Reader(params["wavelength"], params["na"], tdz),
            n=params["n"], q=params["q"], photons=params["photons"])
        training = []
        for _ in range(params["training_frames"]):
            s, y = _frame(tch, alphabet, rng, w, placement)
            training.append((alphabet[s], y))
        radius = params["estimate_radius"] + 2.2 * abs(tdz)
        H = estimate_response(ch, training, radius=radius)
    eq = LinearMMSE(ch, alphabet, H=H)
    sym, lin, it = [], [], []
    for _ in range(params["frames"]):
        s, y = _frame(ch, alphabet, rng, w, placement)
        d = eq.decide(eq.soft(y))
        sym.append(s.ravel())
        lin.append(d.ravel())
        it.append(pic(ch, y, d, alphabet, H=H, iterations=params["pic_iterations"])[0].ravel())
    area = lattice.cell_area
    return {"lattice": kind, "pitch_nm": round(pitch * 1000, 1),
            "spacing_nm": round(lattice.spacing * 1000, 1), "cell_area_um2": area,
            "symbols": int(sum(x.size for x in sym)),
            "linear": _decode_stats(sym, lin, len(alphabet), area),
            "iterative": _decode_stats(sym, it, len(alphabet), area)}


def _pool_map(fn, jobs, workers):
    if workers <= 1:
        return [fn(j) for j in jobs]
    with ProcessPoolExecutor(workers) as ex:
        return list(ex.map(fn, jobs))


def _best(rows, decoder):
    r = max(rows, key=lambda r: r[decoder]["density_bits_um2"])
    return {"density_bits_um2": r[decoder]["density_bits_um2"], "pitch_nm": r["pitch_nm"],
            "spacing_nm": r["spacing_nm"], "ser": r[decoder]["ser"]}


# ---- lattice ---------------------------------------------------------------------------
def _lattice_job(job):
    kind, pitch, cond, params = job
    placement = params["placement_error"] * pitch if cond == "realistic" else 0.0
    r = simulate(kind, pitch, params, placement=placement, estimate=cond != "ideal",
                 key=(CONDITIONS.index(cond),))
    r["condition"] = cond
    return r


def run_lattice(params, pitches, workers=2):
    jobs = [(k, p, c, params) for c in CONDITIONS for k in KINDS for p in pitches]
    rows = _pool_map(_lattice_job, jobs, workers)
    summary = {}
    for c in CONDITIONS:
        summary[c] = {}
        for dec in ("linear", "iterative"):
            best = {k: _best([r for r in rows if r["condition"] == c and r["lattice"] == k], dec)
                    for k in KINDS}
            gain = best["hex"]["density_bits_um2"] / best["square"]["density_bits_um2"] - 1
            summary[c][dec] = {**best, "hex_gain": gain}
    return {"experiment": "lattice", "parameters": params, "pitches_nm": [round(p * 1000, 1) for p in pitches],
            "rows": rows, "summary": summary}


# ---- placement -------------------------------------------------------------------------
def _placement_job(job):
    kind, pitch, frac, params = job
    r = simulate(kind, pitch, params, placement=frac * pitch, estimate=True, key=(7,))
    r["placement_fraction"] = frac
    return r


def run_placement(params, pitches, fractions, workers=2):
    jobs = [(k, p, f, params) for f in fractions for k in KINDS for p in pitches]
    rows = _pool_map(_placement_job, jobs, workers)
    summary = []
    for f in fractions:
        entry = {"placement_fraction": f}
        for k in KINDS:
            sel = [r for r in rows if r["placement_fraction"] == f and r["lattice"] == k]
            entry[k] = {dec: _best(sel, dec) for dec in ("linear", "iterative")}
        summary.append(entry)
    return {"experiment": "placement", "parameters": params, "rows": rows, "summary": summary}


# ---- focus -----------------------------------------------------------------------------
def _focus_job(job):
    kind, pitch, dz_units, mode, params = job
    dof = params["wavelength"] / params["na"] ** 2
    dz = dz_units * dof
    r = simulate(kind, pitch, params, placement=params["placement_error"] * pitch,
                 estimate=True, defocus=dz, train_defocus=0.0 if mode == "fixed" else None,
                 key=(11, int(mode == "fixed")))
    r.update(defocus_dof=dz_units, defocus_um=dz, response=mode)
    return r


def run_focus(params, pitch_by_kind, defocus_units, workers=2):
    jobs = [(k, pitch_by_kind[k], d, m, params) for m in ("fixed", "re-estimated")
            for k in KINDS for d in defocus_units]
    rows = _pool_map(_focus_job, jobs, workers)
    return {"experiment": "focus", "parameters": params,
            "depth_of_focus_um": params["wavelength"] / params["na"] ** 2,
            "pitch_nm": {k: round(v * 1000, 1) for k, v in pitch_by_kind.items()}, "rows": rows}


def grid(start, stop, step):
    k = int(round((stop - start) / step))
    return [round(start + i * step, 4) for i in range(k + 1)]


def run(name, quick=False, workers=None, out=None, **overrides):
    """Run one experiment and write <out>/<name>.json. Returns the result dict."""
    import json
    params = {**DEFAULTS, **overrides, **(QUICK if quick else {})}   # --quick sizes always win
    workers = workers or min(2, os.cpu_count() or 1)
    if name == "lattice":
        pitches = grid(0.24, 0.28, 0.02) if quick else grid(0.225, 0.30, 0.005)
        res = run_lattice(params, pitches, workers)
    elif name == "placement":
        pitches = grid(0.24, 0.28, 0.02) if quick else grid(0.235, 0.30, 0.005)
        fractions = (0.0, 0.05) if quick else (0.0, 0.025, 0.05, 0.075, 0.10)
        res = run_placement(params, pitches, fractions, workers)
    elif name == "focus":
        pitch = {"square": 0.26, "hex": 0.245}
        units = (0.0, 0.5) if quick else (0.0, 0.25, 0.5, 1.0, 1.5, 2.0)
        res = run_focus(params, pitch, units, workers)
    else:
        raise ValueError(f"unknown experiment {name!r}")
    res["quick"] = quick
    if out:
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, f"{name}.json"), "w") as f:
            json.dump(res, f, indent=1)
            f.write("\n")
    return res
