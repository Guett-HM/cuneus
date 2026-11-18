# CUNEUS Phase 2 report: literature and patent search

H. Guettal, 18 November 2026.

*I am not a professional physicist. CUNEUS grew out of my earlier study 4D-VODS, which started
as a geometric intuition (storing data in the shape of engraved symbols); like it, this
search and this report were made with the help of AI tools. Corrections from specialists, and
prior art that this report missed, are very welcome.*

Phase 1 showed that its three results (the hexagonal gain with a two-dimensional equaliser,
interference cancellation with a learnt response, and numerical refocusing) rest on known
techniques ([Phase 1 report](PHASE1.md), section 4). Three candidate contributions were left
for Phase 2: the **three-tier plate**, the **format compiler** and the **low-cost code scaled to
λ/NA** ([concept note](CUNEUS_Concept_Note_v0.2.pdf), sections 3, 4 and 6). The go/no-go
criterion fixed in the concept note was: *at least one contribution not anticipated.*

**Result: no-go.** Each of the three candidates was found in earlier publications, products or
patents. The only thing the search did not find is an open, validated simulator for designing
optical storage formats, which is research software, not an invention. CUNEUS therefore stops
here as an innovation project; the repository stays public as an open, reproducible study.

## 1. Method

Searches of the web, of the scientific literature and of patents (Google Patents, USPTO) on
18 November 2026, for each candidate and for the functions it performs, not only for its
words. A candidate counts as anticipated when an earlier work describes the same function, even
on another medium (film, nickel, paper, a screen) or for another purpose.

This is not a professional patentability or freedom-to-operate search: free databases only,
English only, no analysis of patent claims. A professional search can only find more prior art,
so it could make the conclusion stronger, not weaker.

## 2. The three-tier plate

**Proposed:** one plate read by three readers (naked eye or magnifier, a low-cost microscope
camera, a laboratory microscope), each tier explaining how to read the next.

| Prior art | What it already does |
| --- | --- |
| Rosetta Disk, Long Now Foundation | Text that starts at eye-readable size and spirals down to microscopic size, telling the finder to magnify; more than 13,000 pages on the other side, read with optical magnification only |
| Arch Mission Foundation, Lunar Library (2019; NanoArchival nickel nanofiche) | 25 nickel layers: the first four carry about 60,000 analog pages readable with a 100–200× microscope, including the specifications for reading the digital data stored on the other 21 layers |
| Piql (piqlFilm) | Digital data on film with human-readable instructions, file format descriptions and the source code of the decoder written on the same reel |
| Micr'Olonys (Eupalia; Appuswamy and Joguin, CIDR 2021) | Data as 2D barcodes on microfilm or paper, with a self-contained human-readable bootstrap of about a dozen pages that lets a future user rebuild the decoder |
| US 8,085,304 B2 (The Aerospace Corporation, 2011) | Patent on a photographic medium carrying digital data and a human-readable portion that explains how to read it with basic imaging, without prior knowledge of the format |
| US 2005/0243585 A1 | Patent application on human-readable indicia recorded on an archival digital medium next to the data |

**Verdict: anticipated.** A bootstrap chain from naked eye to magnified text to machine-readable
data, on one object, exists in several products and in patents. Doing it on chrome-on-quartz
with three named readers is an engineering choice, not a new idea.

## 3. The format compiler

**Proposed:** an open program that takes the reader (wavelength, NA, noise, focus range) and the
writer (feature size, levels, placement accuracy, variability) and computes the lattice, the
alphabet, the bit mapping, the decoder, the error-correction rate and the net density.

| Prior art | What it already does |
| --- | --- |
| Microsoft Project Silica, *Nature* 650, 606–612 (2026) | For glass storage: pitch chosen on the Pareto front of density and voxel quality measured on written samples; modulation levels selected from 31 candidates by an optimisation that maximises the estimated mutual information; Gray mappings for alphabets that are not powers of two; LDPC code rate tuned per platter; a neural decoder trained on known data |
| US 11,403,031 B2 (Microsoft, 2022) | Phase-shift and amplitude-phase symbols in silica voxels, with trellis coding, LDPC and interleaving designed for that channel |
| End-to-end constellation shaping (Jones et al., 2018–2019) | Constellations learnt through a differentiable model of the channel, in optical fibre communications |
| IBM holographic storage (Burr et al., SPIE 3468, 1998) | Signal processing and coding developed for, and optimised on, a two-dimensional optical storage channel |

**Verdict: anticipated in function.** Silica already computes levels, mapping and code rate
for its glass, from measurements; fibre communications already learn constellations from a
channel model. What CUNEUS would add is doing it from a physical model of the reader *before*
writing, in open code. The search found no open, validated simulator for designing optical
storage formats in glass (comparable open tools exist for fibre links, e.g. OptiCommPy, and for
DNA storage, e.g. DeSP). That is a useful piece of research software, not an invention.

## 4. The low-cost code scaled to λ/NA

**Proposed:** a hexagonal grey-level code (SAMM-2) whose pitch is set from the reader's λ/NA,
readable without a focus stage thanks to a focus sweep, compared with a binary code.

| Prior art | What it already does |
| --- | --- |
| Microsoft High Capacity Color Barcode (HCCB) | More than one bit per module: triangles in 4 or 8 colours |
| MaxiCode (ISO/IEC 16023) | A 2D code on a hexagonal grid of modules |
| FOCUS (Hermans et al., MobiSys 2016) | Data encoded in the frequency domain of the code image, so that each camera decodes as much as its resolution and distance allow |
| US 11,868,844 | Patent on a visual code whose frequencies and phases are chosen for the effective resolution and dynamic range of the camera |
| Strata (Hu et al., MobiCom 2014) | Layered visual codes readable at different distances and resolutions |
| Wavefront coding (Dowski and Cathey, *Applied Optics* 34, 1859, 1995) | Extended depth of field by optics plus processing, applied to barcode readers |
| QR codes written in silica and gemstones with femtosecond lasers (University of Southampton; *Scientific Reports* 9, 8927, 2019) | Codes written in glass or crystals and read with a smartphone or a microscope |

**Verdict: anticipated.** Multi-level modules, hexagonal grids, codes matched to the reader's
resolution and decoding out of focus are all published. Setting the module from λ/NA is the
usual rule of choosing a module larger than the reader's resolution.

## 5. Go/no-go

| Candidate | Anticipated by | Left for CUNEUS |
| --- | --- | --- |
| Three-tier plate | Rosetta Disk, Arch Lunar Library, Piql, Micr'Olonys, US 8,085,304 | The choice of medium and readers |
| Format compiler | Project Silica (2026), end-to-end constellation shaping | An open simulator that does it from the reader's optics |
| Code scaled to λ/NA | HCCB, MaxiCode, FOCUS, US 11,868,844, wavefront coding | None |

The criterion *"at least one contribution not anticipated"* is **not met.** Decision:
**no-go.** Phases 3 to 6 are not started as an innovation project.

What CUNEUS leaves is real but modest: an open, tested and reproducible simulator of coherent
reading of dense dots in glass, and Phase 1 measurements of how much known techniques give for
one reader (a 405 nm, NA 0.90 coherent microscope), with placement errors and defocus. It can
serve for teaching, or as a reference that others can rerun and correct.

## 6. References

Three-tier plate
- Long Now Foundation, The Rosetta Disk. https://rosettaproject.org/ and https://longnow.org/ideas/very-long-term-backup/
- Arch Mission Foundation, The Lunar Library (2019). https://en.wikipedia.org/wiki/Arch_Mission_Foundation ; Blocks and Files, "Org puts nanofiche disks in lunar library" (2023). https://blocksandfiles.com/2023/08/03/nanofiche-disks-on-moon
- Piql, piqlFilm format description and storage medium description. https://piql.notion.site/Storage-medium-description-20372961908f80d883cde8ff5c9a2355
- R. Appuswamy, V. Joguin, "Universal Layout Emulation for Long-Term Database Archival", CIDR 2021. https://arxiv.org/abs/2009.02678
- V. Joguin, "Passive Digital Preservation now & later: Microfilm, Micr'Olonys and DNA". https://phaidra.univie.ac.at/o:1081750
- US 8,085,304 B2, "Photographic silver emulsion-based digital archival storage", The Aerospace Corporation. https://patents.google.com/patent/US8085304
- US 2005/0243585 A1, "Human-readable indicia for archival digital data storage". https://patents.justia.com/patent/20050243585

Format compiler
- Microsoft Research Project Silica Team, "Laser writing in glass for dense, fast and efficient archival data storage", *Nature* 650, 606–612 (2026), doi:10.1038/s41586-025-10042-w. https://pmc.ncbi.nlm.nih.gov/articles/PMC12916313/
- US 11,403,031 B2, "Systems and methods for encoding and decoding data", Microsoft Technology Licensing (2022). https://patents.google.com/patent/US11403031
- R. T. Jones, T. A. Eriksson, M. P. Yankov, B. J. Puttnam, G. Rademacher, R. S. Luís, D. Zibar, "Geometric Constellation Shaping for Fiber Optic Communication Systems via End-to-end Learning" (2018). https://arxiv.org/abs/1810.00774
- G. W. Burr et al., "Optimizing the holographic digital data storage channel", Proc. SPIE 3468 (1998). https://proceedings.spiedigitallibrary.org/conference-proceedings-of-spie/3468/0000/Optimizing-the-holographic-digital-data-storage-channel/10.1117/12.330403.full
- OptiCommPy, *Journal of Open Source Software* 9(98), 6600 (2024), doi:10.21105/joss.06600; DeSP, https://github.com/WangLabTHU/DeSP

Code scaled to λ/NA
- High Capacity Color Barcode. https://en.wikipedia.org/wiki/High_Capacity_Color_Barcode
- F. Hermans et al., "FOCUS: Robust Visual Codes for Everyone", MobiSys 2016, doi:10.1145/2906388.2906399
- W. Hu et al., "Strata: Layered Coding for Scalable Visual Communication", MobiCom 2014, pp. 79–90
- US 11,868,844, "Visual code and method for encoding and decoding a two-dimensional image". https://patents.google.com/patent/US11868844
- E. R. Dowski, W. T. Cathey, "Extended depth of field through wave-front coding", *Applied Optics* 34(11), 1859–1866 (1995), doi:10.1364/AO.34.001859; US 9,129,173, "Device for optically reading information codes" (wavefront coding in a code reader)
- University of Southampton, nanofoam QR code in silica read with a smartphone. https://eprints.soton.ac.uk/419320/
- A. J. Batista et al., "QR code micro-certified gemstones: femtosecond writing and Raman characterization in Diamond, Ruby and Sapphire", *Scientific Reports* 9, 8927 (2019), doi:10.1038/s41598-019-45405-7

**Use of AI tools.** AI assistants helped run the searches and write this report. Every source is
listed above so that each verdict can be checked.
