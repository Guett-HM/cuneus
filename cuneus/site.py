"""The project page (index.html) takes every number it shows from results/.

``python -m cuneus site`` rewrites two things in index.html and nothing else:

* the JSON block ``<script id="cuneus-data" type="application/json">`` that feeds the
  interactive charts, built from the result files;
* the text of every ``<span data-claim="ID">`` with the printed value of that claim from
  results/claims.json.

tests/test_site.py fails when index.html is not what this module would write, so a rerun that
moves a number cannot leave the page behind.
"""
import json
import os
import re

from . import RESULTS, ROOT, claims

PAGE = os.path.join(ROOT, "index.html")
DATA_RE = re.compile(r'(<script id="cuneus-data" type="application/json">)(.*?)(</script>)', re.S)
CLAIM_RE = re.compile(r'(<span data-claim="([a-z0-9_]+)">)(.*?)(</span>)')


def _load(name):
    with open(os.path.join(RESULTS, f"{name}.json")) as f:
        return json.load(f)


def _r(x, nd=2):
    return round(float(x), nd)


def data():
    """Everything the charts need, rounded for the page."""
    lat = _load("lattice")
    pitches = sorted({r["pitch_nm"] for r in lat["rows"]})
    series = {}
    for cond in ("ideal", "estimated", "realistic"):
        series[cond] = {}
        for kind in ("square", "hex"):
            rows = {r["pitch_nm"]: r for r in lat["rows"] if r["condition"] == cond and r["lattice"] == kind}
            series[cond][kind] = {dec: [_r(rows[p][dec]["density_bits_um2"]) for p in pitches]
                                  for dec in ("linear", "iterative")}
            series[cond][kind]["ser_iterative"] = [_r(rows[p]["iterative"]["ser"], 4) for p in pitches]
    pla = _load("placement")
    placement = [{"percent": _r(100 * e["placement_fraction"], 1),
                  **{k: {d: _r(e[k][d]["density_bits_um2"]) for d in ("linear", "iterative")}
                     for k in ("square", "hex")}} for e in pla["summary"]]
    foc = _load("focus")
    focus = {"depth_of_focus_um": foc["depth_of_focus_um"], "pitch_nm": foc["pitch_nm"],
             "rows": sorted(({"lattice": r["lattice"], "response": r["response"], "dof": r["defocus_dof"],
                              "best": _r(max(r["linear"]["density_bits_um2"], r["iterative"]["density_bits_um2"]))}
                             for r in foc["rows"]), key=lambda r: (r["lattice"], r["response"], r["dof"]))}
    pup = _load("pupil")
    ppitch = sorted({r["pitch_nm"] for r in pup["rows"]})
    pupil = {"pitches": ppitch,
             **{k: [_r(100 * next(r["zone_fraction_outside_pupil"] for r in pup["rows"]
                                  if r["lattice"] == k and r["pitch_nm"] == p), 2) for p in ppitch]
                for k in ("square", "hex")}}
    reg = claims.load()
    vals = claims.values(reg)
    printed = {c["id"]: claims.printed(c, vals[c["id"]]) for c in reg["claims"]}
    return {"source": "results/ of the CUNEUS repository, written by python -m cuneus site",
            "lattice": {"pitches": pitches, "series": series}, "placement": placement,
            "focus": focus, "pupil": pupil, "claims": printed}


def render(html):
    """Return html with the data block and every claim span brought up to date."""
    d = data()
    payload = json.dumps(d, separators=(",", ":"), ensure_ascii=False)
    if not DATA_RE.search(html):
        raise ValueError("index.html has no cuneus-data block")
    html = DATA_RE.sub(lambda m: m.group(1) + payload + m.group(3), html)

    def claim(m):
        cid = m.group(2)
        if cid not in d["claims"]:
            raise KeyError(f"index.html quotes unknown claim {cid!r}")
        return m.group(1) + d["claims"][cid] + m.group(4)

    return CLAIM_RE.sub(claim, html)


def build():
    with open(PAGE, encoding="utf-8") as f:
        html = f.read()
    new = render(html)
    with open(PAGE, "w", encoding="utf-8") as f:
        f.write(new)
    return len(CLAIM_RE.findall(new))


def is_current():
    with open(PAGE, encoding="utf-8") as f:
        html = f.read()
    return render(html) == html
