# Validation report

CUNEUS 0.1.0, generated 2026-11-17 by `python -m cuneus validate`, commit aedabcf, Python 3.13.18, NumPy 2.5.3, SciPy 1.18.1.

**12 of 12 checks pass.** Each check compares the code with a reference that does not come from the code: a closed-form result of diffraction theory, a direct numerical integral, an exact identity, or a property the decoder has by construction. The same checks run as tests on every push (`tests/test_validation.py`).

| Check | Reference | Measured | Limit | Result |
| --- | --- | --- | --- | --- |
| Coherent image of a point is the Airy amplitude | 2 J1(v)/v (closed form) | max deviation 0.0017 | < 0.01 | pass |
| Incoherent transfer function of the pupil | (2/π)(acos u − u√(1−u²)) (closed form) | max deviation 0.0007 | < 0.01 | pass |
| Image of one dot vs direct integral | ∫ Airy amplitude over the dot (quadrature) | max deviation 0.0028 of the peak | < 0.01 | pass |
| Sub-pixel dot placement | exact Fourier shift theorem | relative error 0.00012 | < 0.005 | pass |
| Energy of one dot's image (Parseval) | Σ|u|² over pixels = Σ|H|²/N over frequencies | relative difference 4.1e-16 | < 1e-9 | pass |
| Equaliser inverts the channel without noise | exact recovery (identity) | max symbol error 5.1e-14 | < 1e-3 | pass |
| Equaliser output is unbiased | gain 1 on the true symbols (MMSE theory) | |gain − 1| = 0.0007 | < 0.01 | pass |
| Response estimated from known symbols | true response (noise-free training) | relative error 0.0004 | < 0.01 | pass |
| Defocus model | |pupil| = 1; phase → π λ dz f² at small angles | amplitude change 2.2e-16; paraxial deviation 0.0045 | < 0.01 | pass |
| Mutual information estimator | log2 16 = 4 bits; 0 for independent symbols | perfect 3.9999 bits; independent 0.0007 bits | ± 0.01 | pass |
| Hexagonal lattice geometry | 6 neighbours at distance a; a·(a√3/2) = area | 6 neighbours; area error 0.0e+00 | exact | pass |
| Level spacing for level-dependent noise | even in √r when σ ∝ √r (closed form) | max deviation 3.2e-09 | < 1e-4 | pass |

## What these checks do not cover

They confirm that the code implements its stated model correctly. They do not test the model against reality: scalar optics, thin two-dimensional dots, a Gaussian model of writing and placement errors and shot-noise-limited detection remain assumptions until written glass is measured (Phase 3 of the plan).
