# Changelog

## 0.1.0 (2026-11-17): Phase 1, simulator core

First version of CUNEUS, the successor of 4D-VODS v1.1.

- Periodic coherent channel for square and hexagonal lattices of APSK-16 dots, with writing
  variability, sub-pixel placement errors and non-paraxial defocus.
- Decoders: response learnt from known symbols (pupil edge + compact kernel), exact linear
  MMSE equaliser per frequency, parallel interference cancellation that keeps its best pass.
- Experiments `lattice`, `placement`, `focus`, `seeds`, `pupil`; results with provenance
  (`results/MANIFEST.json`) and every published number checked (`results/claims.json`).
- 12 validation checks against closed-form optics and exact identities (docs/VALIDATION.md).
- Project page (index.html): live coherent-imaging simulation of the reader in the browser,
  interactive frequency-cell explorer and Phase 1 charts; its numbers and chart data are
  rebuilt from results/ by `python -m cuneus site` and checked by tests/test_site.py.
- Phase 1 report (docs/PHASE1.md): hexagonal gain +10 to +20% depending on the decoder,
  replacing the +22% of the concept note; go/no-go: conditional go.
