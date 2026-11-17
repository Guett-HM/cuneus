"""Every physics/numerics check of cuneus.validation must pass (docs/VALIDATION.md)."""
import pytest

from cuneus import validation


@pytest.mark.parametrize("check", validation.CHECKS, ids=lambda c: c.__name__)
def test_check_passes(check):
    r = check()
    assert r["passed"], f"{r['name']}: {r['measured_text']} (limit {r['limit_text']})"
