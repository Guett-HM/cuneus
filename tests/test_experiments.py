"""Experiments run end to end, deterministically, and independently of the worker count."""
import json

import pytest

from cuneus import experiments as E
from cuneus.cli import main


def test_simulate_is_deterministic():
    p = dict(E.DEFAULTS, **E.QUICK, frames=1)
    a = E.simulate("hex", 0.26, p, placement=0.013, estimate=True)
    b = E.simulate("hex", 0.26, p, placement=0.013, estimate=True)
    assert a == b


def test_worker_count_does_not_change_results():
    p = dict(E.DEFAULTS, **E.QUICK, frames=1)
    one = E.run_lattice(p, [0.26], workers=1)
    two = E.run_lattice(p, [0.26], workers=2)
    assert one == two


def test_quick_lattice_structure():
    res = E.run("lattice", quick=True, workers=1)
    assert {r["condition"] for r in res["rows"]} == set(E.CONDITIONS)
    for cond in E.CONDITIONS:
        for dec in ("linear", "iterative"):
            s = res["summary"][cond][dec]
            assert s["hex"]["density_bits_um2"] > 0 and "hex_gain" in s


def test_unknown_experiment():
    with pytest.raises(ValueError):
        E.run("nonsense", quick=True)


def test_cli_quick_run_records_provenance(tmp_path, monkeypatch):
    import cuneus.cli as cli
    monkeypatch.setattr(cli, "RESULTS_QUICK", str(tmp_path))
    assert main(["run", "focus", "--quick", "--workers", "1"]) == 0
    manifest = json.loads((tmp_path / "MANIFEST.json").read_text())
    entry = manifest["files"]["focus.json"]
    assert entry["command"].startswith("python -m cuneus run focus --quick")
    assert entry["parameters"]["n"] == E.QUICK["n"]
