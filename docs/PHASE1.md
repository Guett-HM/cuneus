# CUNEUS Phase 1 report: simulator core and lattice test

Hakim Guettal, 17 November 2026. Version 0.1.0 of the repository.

*I am not a professional physicist. CUNEUS grew out of my earlier study 4D-VODS, which started
as a geometric intuition (storing data in the shape of engraved symbols); like it, this
simulator and its documents were built with the help of AI tools on standard diffraction
optics. Corrections from specialists are very welcome.*

Phase 1 of the [concept note](CUNEUS_Concept_Note_v0.2.pdf) had one job: build a simulator of the dense tier that has none of
the weaknesses found in 4D-VODS v1.1 (finite patches, decoders that know the optics exactly,
no placement errors, no defocus) and use it to test the claim that a hexagonal lattice stores
more than a square one. This report gives the method, the results and the go/no-go decision.
Every number in it is computed from `results/` and checked by `python -m cuneus check`.

## 1. Model

**Medium and reader.** Dots of side 0.6 × the square-equivalent pitch are written in a
reflective layer. Each dot changes the reflected field from 1 to a·e^{iφ}, with 8 phases and
2 amplitudes (APSK-16, 4 bits per dot), as in 4D-VODS. A coherent microscope at 405 nm and
NA 0.90 records the complex field (interferometric readout). Imaging is linear in the field,
so the image is the sum of the images of the individual dots plus noise.

**Lattice.** Square or hexagonal, compared at the same area per symbol. The patch is periodic
(48 × 48 symbols on a torus), so every symbol has a full neighbourhood and no result depends on
edges, the artefact that flattered the v1.1 decoders on small patches.

**Errors.** Each written dot has a complex error of 10% rms (writing variability) and may be
displaced by a Gaussian placement error; sub-pixel displacements use cubic weights, accurate
to 0.012% inside the pupil. Detection noise is complex Gaussian with 64,000 photons per
symbol. Defocus is the exact non-paraxial phase of the pupil.

**Decoders.**

* *Learnt response.* The decoder does not know the optics. It learns the image of one dot
  from two frames of known symbols, as the product of the pupil disc (the NA is known) and a
  smooth function of frequency: a kernel confined to 1 µm, or more when defocus spreads it.
  Conjugate gradients solve the least-squares problem in about 80 iterations.
* *Linear MMSE.* On a periodic lattice the exact linear minimum-mean-square-error equaliser is
  diagonal in frequency once the lattice is split into two rectangular sublattices; it solves a
  2 × 2 system per frequency and its output is unbiased by construction.
* *Interference cancellation.* Starting from the MMSE decisions, each pass subtracts the image
  of every neighbour and re-decides each symbol with a matched filter. The decoder keeps the
  pass whose decisions best explain the image (smallest residual), so a pass that propagates
  errors cannot make the result worse.

**Measure.** Information density = mutual information between written and decided symbols,
per µm², before error correction, as in 4D-VODS v1.1; 13,824 symbols per point.

The model is checked against closed-form optics and exact identities in
[VALIDATION.md](VALIDATION.md): 12 of 12 checks pass.

## 2. Results

### 2.1 Square against hexagonal lattice

Best density over square-equivalent pitches from 225 to 300 nm, bits per µm²
(`results/lattice.json`, figure `figures/lattice_density.png`):

| Condition | Square, linear | Square, iterative | Hexagonal, linear | Hexagonal, iterative | Hexagonal gain, linear | Hexagonal gain, iterative |
| --- | --- | --- | --- | --- | --- | --- |
| Ideal | 44.1 | 59.5 | 52.9 | 65.8 | +20% | +11% |
| Learnt response | 43.7 | 57.7 | 52.7 | 66.1 | +21% | +15% |
| Learnt response, placement error 5% of pitch | 39.0 | 47.1 | 46.0 | 51.9 | +18% | +10% |

Repeating the realistic case with four further random seeds (`results/seeds.json`) gives a
hexagonal gain of +10% on average (range 9 to 12%) with interference cancellation and
+19% (range 18 to 20%) with the linear equaliser. The ranking never changes. The densities
themselves move by up to about 1 bit/µm² between draws
(hexagonal, iterative: 51.9 to 52.7 bits/µm²), so smaller differences between rows, such as
66.1 against 65.8, are sampling noise: a decoder that learns the response cannot do better on
average than one that knows it.

Why the hexagonal lattice wins: the frequency cell of a lattice (its Brillouin zone) holds
exactly one value per symbol, and the reader only sees the part of it inside the pupil disc
(`results/pupil.json`, `figures/frequency_picture.png`). At 265 nm, 6.1% of the square cell
lies outside the pupil against 1.1% of the hexagonal cell, because a hexagon is closer to a
disc. Why the gain shrinks with interference cancellation: a linear decoder cannot recover
what the reader never sees, while a decoder that uses the finite alphabet (only 16 possible
values per dot) can rebuild part of it, so the lattice that loses more also has more to win
back.

Interference cancellation is the larger effect: under ideal conditions it lifts the hexagonal
lattice by +24% over the linear equaliser, against +11% for the hexagonal lattice over the
square one with the same decoder.

### 2.2 Learning the response

The learnt response costs nothing measurable: the "learnt response" row matches the "ideal" row
within the sampling spread. With noise-free training, the learnt response matches the true one
to 0.04% inside the pupil (validation check). The key is the model: an unconstrained estimate
with one unknown per frequency had errors of 16–26% and made interference cancellation diverge;
using the known pupil edge and a compact kernel cut the unknowns to about 50 effective ones.

### 2.3 Dot placement

Best density with a learnt response against rms placement error per axis
(`results/placement.json`, `figures/placement.png`):

| Placement error (% of pitch) | Square, iterative | Hexagonal, iterative |
| --- | --- | --- |
| 0 | 58.6 | 65.8 |
| 2.5 | 55.5 | 61.5 |
| 5 | 46.5 | 52.5 |
| 7.5 | 39.4 | 42.6 |
| 10 | 32.6 | 35.0 |

The 5% row (52.5) and the realistic row of section 2.1 (51.9) are the same setting with
different random draws. At the best hexagonal pitch (245 nm) 5% is about 12 nm per axis.
Placement is the largest
loss in the realistic case and therefore the first specification of a writer: about 6 nm
(2.5%) keeps more than 90% of the ideal density.

### 2.4 Focus

Density at the best realistic pitches (square 255 nm, hexagonal 245 nm, 5% placement error)
against defocus, best of the two decoders (`results/focus.json`, `figures/focus.png`). The
depth of focus λ/NA² is 0.5 µm.

| Defocus (depths of focus) | Hexagonal, response fixed at best focus | Hexagonal, response learnt at the same focus |
| --- | --- | --- |
| 0.5 | 18.3 | 51.0 |
| 1.0 | 3.6 | 49.7 |
| 2.0 | 1.1 | 40.0 |

Coherent defocus is a pure phase in the pupil, which a learnt response absorbs. A decoder with
a fixed response loses two thirds of the density at half a depth of focus; one that learns the
response from known symbols at the same focus keeps 49.7 bits/µm² at one depth of focus. At
two depths of focus the square lattice (42.2) overtakes the hexagonal one, only because each
is tested at its own optimum pitch: the learnt kernel then has to cover a wide blur and the
denser hexagonal pitch (245 against 255 nm) suffers first. In practice the
known symbols must be spread over the plate as pilots, close enough that focus does not change
between them; Phase 3 will size that overhead.

## 3. Go/no-go

The criterion set in the concept note was a hexagonal gain of at least 15% with a learnt
response and 5% placement errors. It is met with the linear equaliser (+18%) and missed with
interference cancellation (+10%). Decision: **conditional go.**

* The hexagonal lattice stays the default: it wins in every condition, with both decoders and
  in every seed.
* The +22% quoted in the concept note is withdrawn and replaced by "+10 to +20% depending on the
  decoder".
* CUNEUS's case rests on the combination: interference cancellation, a learnt response and the
  focus tolerance it brings. Under the idealised assumptions of 4D-VODS v1.1 (42.6 bits/µm²
  at 300 nm) the combination gives 65.8 bits/µm² (+54%). With a learnt response and 5%
  placement errors, which v1.1 did not model, it gives 51.9 bits/µm²:
  about 43 bits/µm² of user data with the v1.1 overhead, about 1.41× a BDXL layer.

## 4. Prior art

The three ideas behind these results are known; Phase 1 measures them for this reader, it does
not invent them.

* **Hexagonal lattice and two-dimensional equalisation.** Philips' two-dimensional optical
  storage (TwoDOS) wrote bits on a hexagonal lattice and read them with two-dimensional
  equalisation and detection: A. H. J. Immink et al., "Signal processing and coding for
  two-dimensional optical storage", *IEEE GLOBECOM* 2003; T. Conway, "A partial response read
  channel for two dimensional optical data storage", *IEEE Trans. Consumer Electronics* 50(4),
  1107–1112 (2004); L. Huang, G. Mathew, T. C. Chong, "Channel modeling and target design for
  two-dimensional optical storage systems", *IEEE Trans. Magnetics* 41(8), 2414–2424 (2005),
  doi:10.1109/TMAG.2005.852212.
* **Interference cancellation and a response learnt from known symbols** (sections 2.1 and
  2.2) are standard in digital communications: parallel interference cancellation in
  multi-user detection, channel estimation from pilot symbols.
* **Numerical refocusing of a measured complex field** (section 2.4) is how digital holographic
  microscopy extends the depth of focus: T. Colomb, N. Pavillon, J. Kühn, E. Cuche,
  C. Depeursinge, Y. Emery, "Extended depth-of-focus by digital holographic microscopy",
  *Optics Letters* 35(11), 1840–1842 (2010), doi:10.1364/OL.35.001840.

What is new in this report is the size of each effect for a coherent 405 nm, NA 0.90 reader of
APSK-16 dots with placement errors and defocus, in open code. The candidates for a new
contribution (the format compiler, a code aligned to the reader's λ/NA, the three-tier plate)
are not tested here; Phase 2 searched the literature and patents for them and found all three
already published ([Phase 2 report](PHASE2.md)).

## 5. Limits

Scalar optics and thin two-dimensional dots at NA 0.90 (vectorial effects are not small there);
a Gaussian, independent model of writing and placement errors; no camera pixels, aberrations
other than defocus, or non-linear writing; densities are mutual information of hard decisions,
not the output of a real error-correction code. The validation checks prove that the code
implements its model, not that the model matches glass.

## 6. Next steps

1. Phase 2: literature and patent search on the six ingredients of the concept note, now with
   interference cancellation and response learning added to the list.
2. Phase 3 (format compiler): pilots spread over the plate, soft-decision decoding with a real
   code, a writer model with correlated placement errors; prediction of the best lattice, pitch
   and decoder for any reader and writer.
3. Phase 4: the low-cost tier (SAMM-2) with a focus sweep, against a binary code.

**Use of AI tools.** AI assistants helped write the simulator and this report. All results come from the code in
the repository and can be checked by re-running it.
