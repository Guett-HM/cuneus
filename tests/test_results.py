"""Published results: provenance hashes match and every quoted number matches results/."""
import os

import pytest

from cuneus import RESULTS, claims, provenance

pytestmark = pytest.mark.skipif(not os.path.exists(os.path.join(RESULTS, "MANIFEST.json")),
                                reason="no published results yet")


def test_manifest_matches_files():
    assert provenance.verify(RESULTS) == []


def test_every_published_number_is_current():
    problems, n = claims.check()
    assert n > 0
    assert problems == []
