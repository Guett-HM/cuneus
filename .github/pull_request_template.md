## What this changes

## Checklist

- [ ] `pytest -q` passes and `ruff check .` is clean
- [ ] If results changed: rerun with `python -m cuneus run ...` (provenance is recorded automatically) and explain why in `CHANGELOG.md`
- [ ] If a published number changed: update `results/claims.json` and the documents, then `python -m cuneus check`
- [ ] If the project page quotes a changed number: `python -m cuneus site` (tests/test_site.py checks it)
