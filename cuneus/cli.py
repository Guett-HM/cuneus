"""Single entry point:  python -m cuneus <command> [options]

  run <experiment>  lattice | placement | focus | all   (writes results/<experiment>.json)
  figures           rebuild figures/ from results/
  validate          physics and numerics checks -> docs/VALIDATION.md
  check             every published number vs results/ and the documents
  manifest          verify the provenance of results/ (hashes, commands, versions)

--quick runs a small version of an experiment into results_quick/ (used by the tests).
Options can also come from a TOML file (--config configs/phase1.toml); options given on
the command line win. Every run records what it wrote in <folder>/MANIFEST.json.
"""
import argparse
import os
import sys
import tomllib

from . import RESULTS, RESULTS_QUICK, ROOT, __version__, provenance

EXPERIMENTS = ("lattice", "placement", "focus")
OVERRIDES = ("frames", "seed", "photons", "writing_variability", "placement_error", "pic_iterations")


def cmd_run(args):
    from . import experiments
    params = {}
    if args.config:
        with open(args.config, "rb") as f:
            params.update(tomllib.load(f))
    for k in OVERRIDES:
        v = getattr(args, k)
        if v is not None:
            params[k] = v
    names = EXPERIMENTS if args.experiment == "all" else (args.experiment,)
    folder = RESULTS_QUICK if args.quick else RESULTS
    os.makedirs(folder, exist_ok=True)
    for name in names:
        before = provenance.snapshot(folder)
        print(f"running {name}{' (quick)' if args.quick else ''} ...", flush=True)
        res = experiments.run(name, quick=args.quick, workers=args.workers, out=folder, **params)
        command = f"python -m cuneus run {name}" + (" --quick" if args.quick else "")
        if args.config:
            command += f" --config {os.path.relpath(args.config, ROOT)}"
        written = provenance.record(folder, before, command, dict(res["parameters"], quick=args.quick))
        print(f"  wrote {', '.join(written)}; provenance in {os.path.relpath(folder, ROOT)}/MANIFEST.json")
    return 0


def cmd_figures(args):
    from . import figures
    for path in figures.make_all():
        print("wrote", os.path.relpath(path, ROOT))
    return 0


def cmd_validate(args):
    from . import validation
    results = validation.run_all()
    for r in results:
        print(("PASS " if r["passed"] else "FAIL ") + r["name"] + ": " + r["measured_text"])
    if args.report:
        validation.write_report(results, args.report)
        print("report written to", os.path.relpath(args.report, ROOT))
    return 0 if all(r["passed"] for r in results) else 1


def cmd_check(args):
    from . import claims
    problems, n = claims.check()
    for msg in problems:
        print("MISMATCH", msg)
    print(f"{n - len(problems)}/{n} published numbers agree with results/ and the documents")
    return 1 if problems else 0


def cmd_manifest(args):
    problems = provenance.verify(RESULTS)
    for msg in problems:
        print("PROBLEM", msg)
    n = len(provenance.load(RESULTS)["files"])
    print(f"{n} result files listed; {len(problems)} problem(s)")
    return 1 if problems else 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m cuneus", description=__doc__.splitlines()[0])
    ap.add_argument("--version", action="version", version=f"cuneus {__version__}")
    sub = ap.add_subparsers(dest="command", required=True)
    r = sub.add_parser("run", help="run an experiment")
    r.add_argument("experiment", choices=(*EXPERIMENTS, "all"))
    r.add_argument("--quick", action="store_true")
    r.add_argument("--workers", type=int)
    r.add_argument("--config")
    r.add_argument("--frames", type=int)
    r.add_argument("--seed", type=int)
    r.add_argument("--photons", type=float)
    r.add_argument("--writing-variability", dest="writing_variability", type=float)
    r.add_argument("--placement-error", dest="placement_error", type=float)
    r.add_argument("--pic-iterations", dest="pic_iterations", type=int)
    r.set_defaults(fn=cmd_run)
    sub.add_parser("figures", help="rebuild figures/").set_defaults(fn=cmd_figures)
    v = sub.add_parser("validate", help="physics and numerics checks")
    v.add_argument("--report", default=os.path.join(ROOT, "docs", "VALIDATION.md"))
    v.set_defaults(fn=cmd_validate)
    sub.add_parser("check", help="published numbers vs results").set_defaults(fn=cmd_check)
    sub.add_parser("manifest", help="verify provenance of results/").set_defaults(fn=cmd_manifest)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
