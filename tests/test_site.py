"""The project page shows the current results: data block and quoted numbers are up to date."""
import json
import re

from cuneus import site


def test_index_html_is_current():
    assert site.is_current(), "index.html is out of date: run python -m cuneus site"


def test_every_quoted_claim_exists_and_data_parses():
    with open(site.PAGE, encoding="utf-8") as f:
        html = f.read()
    data = json.loads(site.DATA_RE.search(html).group(2))
    quoted = re.findall(r'data-claim="([a-z0-9_]+)"', html)
    assert quoted and all(q in data["claims"] for q in quoted)
    assert data["lattice"]["pitches"][0] == 225.0
