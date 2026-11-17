"""Published numbers, traced to the results.

``results/claims.json`` lists every number that the README and the
documents quote. For each claim it gives:

* how to compute the value: either a field of a result file (``file`` + ``path``) or a short
  arithmetic expression (``expr``) over other claims and constants;
* how the value is printed (``format``, a Python format string);
* the text snippets that quote it (``snippets``, with ``{v}`` for the printed value) and the
  files that must contain at least one of those snippets (``cited_in``).

``check()`` recomputes every value from ``results/`` and verifies that each citing file
quotes the current value. If a simulation is rerun and a number moves, the documents that
still quote the old number make the check fail.
"""
import json
import math
import os

from . import RESULTS, ROOT

CLAIMS = os.path.join(RESULTS, "claims.json")


def _resolve(obj, path):
    for step in path:
        if isinstance(step, dict):           # select the list element whose fields match
            matches = [x for x in obj if all(abs(x.get(k, math.nan) - v) < 1e-9 if isinstance(v, float)
                                             else x.get(k) == v for k, v in step.items())]
            if len(matches) != 1:
                raise KeyError(f"{step} matched {len(matches)} elements")
            obj = matches[0]
        else:
            obj = obj[step]
    return obj


def load():
    with open(CLAIMS) as f:
        return json.load(f)


def values(registry=None):
    """{claim id: numeric value}, computed from results/ in registry order."""
    registry = registry or load()
    out, cache = {}, {}
    for c in registry["claims"]:
        if "file" in c:
            if c["file"] not in cache:
                with open(os.path.join(RESULTS, c["file"])) as f:
                    cache[c["file"]] = json.load(f)
            v = _resolve(cache[c["file"]], c.get("path", []))
        else:
            v = eval(c["expr"], {"__builtins__": {}, "sum": sum, "round": round, "math": math},
                     dict(out, **registry.get("constants", {})))
        out[c["id"]] = float(v)
    return out


def printed(claim, value):
    return claim["format"].format(value)


def check():
    """Return (problems, number of claims)."""
    registry = load()
    vals = values(registry)
    texts = {}
    problems = []
    for c in registry["claims"]:
        p = printed(c, vals[c["id"]])
        if "expect" in c and p != c["expect"]:
            problems.append(f"{c['id']}: results give {p}, registry expects {c['expect']}")
        for fn in c["cited_in"]:
            if fn not in texts:
                with open(os.path.join(ROOT, fn), encoding="utf-8") as f:
                    texts[fn] = f.read()
            if not any(s.format(v=p) in texts[fn] for s in c["snippets"]):
                problems.append(f"{c['id']}: {fn} does not quote the current value {p!r}")
    return problems, len(registry["claims"])
