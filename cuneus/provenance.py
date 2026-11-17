"""Provenance of result files.

Every file in ``results/`` has an entry in ``results/MANIFEST.json`` with its SHA-256 hash,
the command and parameters that produced it, the git commit, and the software versions.
``verify()`` recomputes the hashes, so a result edited by hand (or regenerated without
recording it) is detected by the test suite.
"""
import datetime as _dt
import hashlib
import json
import os
import platform
import subprocess

from . import ROOT

MANIFEST_NAME = "MANIFEST.json"
NOT_RESULTS = {MANIFEST_NAME, "claims.json"}     # registries kept in results/, not outputs of a run


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def environment():
    import matplotlib
    import numpy
    import scipy
    return {"python": platform.python_version(), "numpy": numpy.__version__,
            "scipy": scipy.__version__, "matplotlib": matplotlib.__version__,
            "platform": platform.platform(terse=True)}


def git_state():
    try:
        commit = subprocess.run(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"],
                                capture_output=True, text=True, check=True).stdout.strip()
        dirty = bool(subprocess.run(["git", "-C", ROOT, "status", "--porcelain", "--", "cuneus"],
                                    capture_output=True, text=True, check=True).stdout.strip())
        return {"commit": commit, "code_modified": dirty}
    except (OSError, subprocess.CalledProcessError):
        return {"commit": "unknown", "code_modified": None}


def snapshot(folder):
    """{file name: mtime} for the JSON files in a results folder."""
    if not os.path.isdir(folder):
        return {}
    return {f: os.path.getmtime(os.path.join(folder, f))
            for f in os.listdir(folder) if f.endswith(".json") and f not in NOT_RESULTS}


def load(folder):
    path = os.path.join(folder, MANIFEST_NAME)
    if not os.path.exists(path):
        return {"description": "Provenance of every result file: hash, command, parameters, "
                               "commit and software versions. Checked by tests/test_provenance.py.",
                "files": {}}
    with open(path) as f:
        return json.load(f)


def save(folder, manifest):
    manifest["files"] = dict(sorted(manifest["files"].items()))
    with open(os.path.join(folder, MANIFEST_NAME), "w") as f:
        json.dump(manifest, f, indent=1)
        f.write("\n")


def record(folder, before, command, params):
    """Add or update the manifest entry of every JSON file written since ``before``."""
    after = snapshot(folder)
    changed = sorted(f for f, t in after.items() if before.get(f) != t)
    if not changed:
        return []
    manifest = load(folder)
    entry = {"command": command, "parameters": params, **git_state(),
             "environment": environment(),
             "created_utc": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    for f in changed:
        manifest["files"][f] = {"sha256": sha256(os.path.join(folder, f)), **entry}
    save(folder, manifest)
    return changed


def verify(folder):
    """Return a list of problems: missing entries, missing files, hash mismatches."""
    manifest = load(folder)
    problems = []
    present = set(snapshot(folder))
    listed = set(manifest["files"])
    for f in sorted(present - listed):
        problems.append(f"{f}: no provenance entry")
    for f in sorted(listed - present):
        problems.append(f"{f}: listed in the manifest but missing")
    for f in sorted(present & listed):
        if sha256(os.path.join(folder, f)) != manifest["files"][f]["sha256"]:
            problems.append(f"{f}: content differs from the recorded hash")
    return problems
