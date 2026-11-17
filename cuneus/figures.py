"""Figures of the Phase 1 report, rebuilt from results/ (python -m cuneus figures).

One visual style: the square lattice is always categorical slot 1 (blue) and the hexagonal
lattice slot 2 (orange); the linear decoder is dashed with open markers, the iterative
decoder solid with filled markers, so colour is never the only cue. Every figure is saved
as PNG (web), PDF (print) and a CSV of the plotted values in figures/data/.
"""
import csv
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, Polygon  # noqa: E402

from . import RESULTS, ROOT  # noqa: E402
from .lattice import Lattice  # noqa: E402
from .optics import Reader  # noqa: E402

FIG = os.path.join(ROOT, "figures")
DATA = os.path.join(FIG, "data")
COL = {"square": "#2a78d6", "hex": "#eb6834"}
NAME = {"square": "square lattice", "hex": "hexagonal lattice"}
INK, INK2, GRID, SURF = "#1d1d1b", "#52514e", "#e4e3df", "#fcfcfb"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": INK2,
    "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.8, "figure.facecolor": SURF,
    "axes.facecolor": SURF, "savefig.facecolor": SURF, "legend.frameon": False,
    "text.color": INK, "pdf.fonttype": 42, "lines.linewidth": 2, "lines.markersize": 5,
})
PDF_META = {"Creator": "CUNEUS cuneus/figures.py", "Author": "Hakim Guettal", "CreationDate": None}
STYLE = {"linear": dict(ls="--", mfc=SURF), "iterative": dict(ls="-")}
DEC = {"linear": "linear MMSE", "iterative": "MMSE + interference cancellation"}
LEARNT = {"re-estimated": "response learnt at the same focus", "fixed": "response fixed at best focus"}


def _load(name):
    with open(os.path.join(RESULTS, f"{name}.json")) as f:
        return json.load(f)


def _title(ax, text):
    ax.set_title(text, loc="left", fontsize=10.5, color=INK)


def _save(fig, name, header, rows):
    os.makedirs(DATA, exist_ok=True)
    paths = [os.path.join(FIG, f"{name}.png"), os.path.join(FIG, f"{name}.pdf")]
    fig.savefig(paths[0], dpi=200, bbox_inches="tight")
    fig.savefig(paths[1], metadata=PDF_META, bbox_inches="tight")
    plt.close(fig)
    with open(os.path.join(DATA, f"{name}.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow([f"{v:.6g}" if isinstance(v, float) else v for v in r])
    return paths


def lattice_density():
    res = _load("lattice")
    titles = {"ideal": "Ideal: exact response, exact placement",
              "estimated": "Response learnt from known symbols",
              "realistic": "Learnt response + placement error 5% of pitch"}
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 3.9), sharey=True)
    rows = []
    for ax, cond in zip(axes, ("ideal", "estimated", "realistic")):
        for kind in ("square", "hex"):
            sel = sorted((r for r in res["rows"] if r["condition"] == cond and r["lattice"] == kind),
                         key=lambda r: r["pitch_nm"])
            x = [r["pitch_nm"] for r in sel]
            for dec in ("linear", "iterative"):
                y = [r[dec]["density_bits_um2"] for r in sel]
                ax.plot(x, y, color=COL[kind], marker="o" if kind == "square" else "s",
                        label=f"{NAME[kind]}, {DEC[dec]}", **STYLE[dec])
                rows += [(cond, kind, dec, xi, yi, r[dec]["ser"]) for xi, yi, r in zip(x, y, sel)]
        best = res["summary"][cond]["iterative"]
        ax.annotate(f"hexagonal +{100 * best['hex_gain']:.0f}%\n(best vs best, iterative)",
                    xy=(best["hex"]["pitch_nm"], best["hex"]["density_bits_um2"]),
                    xytext=(0.98, 0.04), textcoords="axes fraction", ha="right", fontsize=8.5, color=INK2)
        _title(ax, titles[cond])
        ax.set_xlabel("square-equivalent pitch (nm)")
    axes[0].set_ylabel("information density before error correction\n(bits per µm²)")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2, fontsize=8.5, bbox_to_anchor=(0.5, -0.12))
    return _save(fig, "lattice_density", ["condition", "lattice", "decoder", "pitch_nm", "bits_per_um2", "ser"], rows)


def placement():
    res = _load("placement")
    fig, ax = plt.subplots(figsize=(6.2, 3.9))
    rows = []
    for kind in ("square", "hex"):
        for dec in ("linear", "iterative"):
            x = [100 * e["placement_fraction"] for e in res["summary"]]
            y = [e[kind][dec]["density_bits_um2"] for e in res["summary"]]
            ax.plot(x, y, color=COL[kind], marker="o" if kind == "square" else "s",
                    label=f"{NAME[kind]}, {DEC[dec]}", **STYLE[dec])
            rows += [(kind, dec, xi, yi, e[kind][dec]["pitch_nm"]) for xi, yi, e in zip(x, y, res["summary"])]
    _title(ax, "Best density vs dot placement error (learnt response)")
    ax.set_xlabel("rms placement error per axis (% of square-equivalent pitch)")
    ax.set_ylabel("best density (bits per µm²)")
    ax.legend(fontsize=7.8)
    header = ["lattice", "decoder", "placement_percent", "best_bits_per_um2", "best_pitch_nm"]
    return _save(fig, "placement", header, rows)


def focus():
    res = _load("focus")
    fig, ax = plt.subplots(figsize=(6.2, 3.9))
    rows = []
    for kind in ("square", "hex"):
        for mode, ls in (("re-estimated", "-"), ("fixed", ":")):
            sel = sorted((r for r in res["rows"] if r["lattice"] == kind and r["response"] == mode),
                         key=lambda r: r["defocus_dof"])
            x = [r["defocus_dof"] for r in sel]
            y = [max(r["linear"]["density_bits_um2"], r["iterative"]["density_bits_um2"]) for r in sel]
            ax.plot(x, y, color=COL[kind], ls=ls, marker="o" if kind == "square" else "s",
                    mfc=SURF if mode == "fixed" else COL[kind],
                    label=f"{NAME[kind]} ({res['pitch_nm'][kind]:.0f} nm), {LEARNT[mode]}")
            rows += [(kind, mode, xi, xi * res["depth_of_focus_um"], yi) for xi, yi in zip(x, y)]
    _title(ax, "Focus tolerance (best of the two decoders)")
    ax.set_xlabel(f"defocus (depths of focus, λ/NA² = {1000 * res['depth_of_focus_um']:.0f} nm)")
    ax.set_ylabel("density (bits per µm²)")
    ax.set_ylim(bottom=0)
    ax.legend(fontsize=7.5, loc="lower left")
    return _save(fig, "focus", ["lattice", "response", "defocus_dof", "defocus_um", "bits_per_um2"], rows)


def frequency_picture(pitch=0.265):
    """Pupil disc vs the Brillouin zone of each lattice at the same density. The zone holds one
    frequency per symbol; the part of it outside the pupil is information the reader never sees."""
    reader = Reader()
    fc = reader.cutoff
    fig, axes = plt.subplots(1, 2, figsize=(8.6, 4.2))
    rows = []
    for ax, kind in zip(axes, ("square", "hex")):
        lat = Lattice.from_square_pitch(kind, pitch)
        poly = lat.brillouin_zone()
        frac = lat.zone_fraction_outside_pupil(fc)
        rows.append((kind, pitch * 1000, lat.spacing * 1000, frac))
        ax.add_patch(Polygon(poly, closed=True, fc=matplotlib.colors.to_rgba(COL[kind], 0.18), ec=COL[kind], lw=2))
        ax.add_patch(Circle((0, 0), fc, fill=False, ec=INK, lw=1.6, ls="--"))
        lim = 2.6
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_aspect("equal")
        ax.set_xlabel("fx (cycles per µm)")
        _title(ax, f"{NAME[kind].capitalize()}: {100 * frac:.1f}% of the zone\noutside the pupil (never seen)")
        ax.text(0, -lim + 0.15, "dashed: pupil NA/λ; shaded: frequency cell of the lattice",
                ha="center", fontsize=8, color=INK2)
    axes[0].set_ylabel("fy (cycles per µm)")
    fig.suptitle(f"Same density ({pitch * 1000:.0f} nm square-equivalent pitch), 405 nm, NA 0.90",
                 x=0.06, ha="left", fontsize=9, color=INK2, y=0.02)
    return _save(fig, "frequency_picture", ["lattice", "pitch_nm", "spacing_nm", "zone_fraction_outside_pupil"], rows)


def make_all():
    os.makedirs(FIG, exist_ok=True)
    paths = []
    paths += frequency_picture()
    for name, fn in (("lattice", lattice_density), ("placement", placement), ("focus", focus)):
        if os.path.exists(os.path.join(RESULTS, f"{name}.json")):
            paths += fn()
    return paths
