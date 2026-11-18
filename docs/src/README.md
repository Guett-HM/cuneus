# Document sources

Markdown version of the concept note, exported together with the PDF in `docs/`. It exists so
that anyone can read the text in a diff, quote a line in an issue, or propose a correction in a
pull request.

| File | PDF |
| --- | --- |
| `concept-note.md` | `docs/CUNEUS_Concept_Note_v0.2.pdf` |

The editable master is kept by the author; accepted corrections are applied there and both the
PDF and the Markdown are re-exported. Charts appear here as the images in `figures/`; their
values are in `figures/data/*.csv` and `results/`.

The main Phase 1 numbers quoted in the concept note are registered in `results/claims.json` and
checked against the results by `python -m cuneus check` and the test suite.
