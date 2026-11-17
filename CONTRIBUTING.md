# Contributing to CUNEUS

CUNEUS is a concept study by a non-specialist, built with the help of AI tools. The most
valuable contributions are **corrections**: an assumption that is wrong, a formula that is
too optimistic, a reference that was missed. You do not need to send code for that; a short
issue is enough.

## Ways to help

| You are… | Most useful contribution |
| --- | --- |
| An optics or laser-writing specialist | A [physics correction](https://github.com/GuettHM/cuneus/issues/new?template=physics_correction.yml): what the model gets wrong and how much it matters. Real placement accuracy and writing variability of a writer are especially welcome |
| A signal-processing or coding-theory specialist | Review of the decoders (`cuneus/equalizer.py`) and of the error-correction plan for Phase 3 |
| A developer | Bug reports, tests, faster code |
| Anyone | Questions about anything that is unclear: unclear text is a bug too |

## Ground rules for code changes

1. **Every number must stay reproducible.** Results are produced only by
   `python -m cuneus run …`, which records the command, commit and software versions in
   `results/MANIFEST.json`. Never edit a file in `results/` by hand.
2. **Published numbers are registered.** If a change moves a number quoted in the README,
   the report or the project page, update `results/claims.json` and the text, run
   `python -m cuneus site` and `python -m cuneus check`.
3. **Physics changes need a validation check or a test.** If you change the optics, add a
   comparison with an independent reference in `cuneus/validation.py` when one exists.
4. **Fixed seeds stay fixed.** Every configuration uses its own deterministic random stream;
   if a change alters results on purpose, explain why in `CHANGELOG.md`.
5. Before opening a pull request: `pytest -q` and `ruff check .` must pass.

## Set-up

```bash
git clone https://github.com/GuettHM/cuneus && cd cuneus
pip install -e ".[dev]"          # or: pip install -r requirements-lock.txt
pytest -q                        # about 20 seconds
python -m cuneus validate        # physics validation checks
python -m cuneus check           # published numbers vs results
```

## Licence

By contributing you agree that your contribution is released under the MIT License, like the
rest of the project. Contributors are credited in `CHANGELOG.md` and, for substantial
contributions, in `CITATION.cff`.

Please follow the [code of conduct](CODE_OF_CONDUCT.md).
