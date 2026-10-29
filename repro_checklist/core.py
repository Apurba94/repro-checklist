"""Checklist items (inspired by common journal and conference reproducibility checklists) and detectors."""
import fnmatch
import os

# section -> list of (id, question, detector name or None)
CHECKLIST = {
    "Data": [
        ("data-availability", "Is there a data availability statement (repository, DOI, or access conditions)?", "data_statement"),
        ("data-raw-separate", "Are raw data kept separate from processed data and never edited by hand?", "raw_dir"),
        ("data-checksums", "Are checksums (or versioned identifiers) recorded for the input data?", "checksums"),
        ("data-dictionary", "Is there a data dictionary/codebook describing variables and units?", "codebook"),
        ("data-license", "Is the data licence stated?", None),
    ],
    "Code": [
        ("code-public", "Is the analysis code available (public repository or archive with DOI)?", "git"),
        ("code-license", "Does the code have a licence?", "license"),
        ("code-readme", "Does a README explain how to run the analysis from raw data to results?", "readme"),
        ("code-single-entry", "Can all results be regenerated with one command or a documented pipeline?", "pipeline"),
        ("code-tests", "Are there tests or checks for key functions?", "tests"),
        ("code-citation", "Is there a CITATION.cff or equivalent?", "citation"),
    ],
    "Environment": [
        ("env-deps", "Are dependencies listed with versions (requirements, environment.yml, lock file)?", "deps"),
        ("env-pinned", "Are dependency versions pinned?", "pinned"),
        ("env-container", "Is there a container or environment recipe (Dockerfile, environment.yml)?", "container"),
        ("env-hardware", "Are hardware and runtime requirements reported (CPU/GPU, memory, time)?", None),
    ],
    "Analysis": [
        ("ana-seeds", "Are random seeds fixed and reported?", None),
        ("ana-prereg", "Were hypotheses/analysis plans preregistered or clearly marked as exploratory?", None),
        ("ana-stats", "Are statistical tests, effect sizes and uncertainty (CIs) fully reported?", None),
        ("ana-exclusions", "Are all exclusions of data or participants reported with reasons?", None),
        ("ana-notebooks-clean", "Are notebooks committed without stale outputs (or re-run top to bottom)?", "notebooks_clean"),
    ],
}


def _exists(root, *patterns):
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in (".git", "node_modules", ".venv", "__pycache__")]
        rel_dp = os.path.relpath(dp, root)
        for name in fns + dns:
            rel = os.path.normpath(os.path.join(rel_dp, name)).replace(os.sep, "/")
            if any(fnmatch.fnmatch(name.lower(), p) or fnmatch.fnmatch(rel.lower(), p) for p in patterns):
                return rel
    return None


def _read(root, rel):
    try:
        with open(os.path.join(root, rel), encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def auto_detect(root):
    """Return {item_id: (True/False, evidence)} for items that can be checked from files."""
    readme = _exists(root, "readme*")
    readme_text = _read(root, readme).lower() if readme else ""
    deps = _exists(root, "requirements*.txt", "environment.yml", "pyproject.toml", "renv.lock", "poetry.lock",
                   "pipfile.lock", "description")
    det = {
        "readme": (bool(readme), readme or "no README"),
        "license": (bool(_exists(root, "license*", "licence*", "copying*")), "LICENSE file"),
        "git": (os.path.isdir(os.path.join(root, ".git")), ".git directory"),
        "citation": (bool(_exists(root, "citation.cff", "codemeta.json", ".zenodo.json")), "citation metadata"),
        "tests": (bool(_exists(root, "test_*.py", "*_test.py", "tests", "testthat")), "tests"),
        "deps": (bool(deps), deps or "no dependency file"),
        "container": (bool(_exists(root, "dockerfile", "environment.yml", "apptainer*", "*.def", "binder")), "recipe"),
        "pipeline": (bool(_exists(root, "makefile", "snakefile", "pipeline.json", "dvc.yaml", "run_all*", "main.nf")),
                     "pipeline/runner"),
        "raw_dir": (bool(_exists(root, "data/raw", "raw")), "data/raw"),
        "checksums": (bool(_exists(root, "*.sha256", "*.md5", "manifest*", "dvc.lock")), "checksum manifest"),
        "codebook": (bool(_exists(root, "*codebook*", "*data_dictionary*", "*datadictionary*", "data.md")), "codebook"),
        "data_statement": ("data availab" in readme_text or "doi.org" in readme_text or "zenodo" in readme_text,
                           "README mentions data availability/DOI"),
    }
    if deps and deps.endswith(".txt"):
        lines = [l.strip() for l in _read(root, deps).splitlines() if l.strip() and not l.startswith("#")]
        det["pinned"] = (bool(lines) and all("==" in l or l.startswith("-") for l in lines), deps)
    elif deps:
        det["pinned"] = (deps.endswith(".lock"), deps)
    else:
        det["pinned"] = (False, "no dependency file")
    nb = _exists(root, "*.ipynb")
    if nb:
        import json
        dirty = 0
        for dp, _, fns in os.walk(root):
            for fn in fns:
                if fn.endswith(".ipynb") and ".ipynb_checkpoints" not in dp:
                    try:
                        with open(os.path.join(dp, fn), encoding="utf-8") as fh:
                            cells = json.load(fh).get("cells", [])
                        dirty += any(c.get("outputs") for c in cells if c.get("cell_type") == "code")
                    except (ValueError, OSError):
                        pass
        det["notebooks_clean"] = (dirty == 0, "%d notebook(s) with outputs" % dirty)
    out = {}
    for section in CHECKLIST.values():
        for iid, _, d in section:
            if d and d in det:
                out[iid] = det[d]
    return out


def score(answers):
    """answers: {item_id: 'yes' | 'no' | 'na' | 'partial'}. Returns per-section and total percentages."""
    value = {"yes": 1.0, "partial": 0.5, "no": 0.0}
    res, tot_n, tot_v = {}, 0, 0.0
    for sec, items in CHECKLIST.items():
        vals = [value[answers[i]] for i, _, _ in items if answers.get(i) in value]
        res[sec] = round(100 * sum(vals) / len(vals)) if vals else None
        tot_n += len(vals)
        tot_v += sum(vals)
    res["total"] = round(100 * tot_v / tot_n) if tot_n else None
    return res


def render_report(answers, evidence=None, project=""):
    evidence = evidence or {}
    sc = score(answers)
    mark = {"yes": "[x]", "partial": "[~]", "no": "[ ]", "na": "n/a"}
    lines = ["# Reproducibility checklist%s" % (": " + project if project else ""), "",
             "**Overall score: %s%%**" % sc["total"], ""]
    todo = []
    for sec, items in CHECKLIST.items():
        lines += ["## %s (%s%%)" % (sec, sc[sec] if sc[sec] is not None else "-"), ""]
        for iid, q, _ in items:
            a = answers.get(iid, "no")
            ev = evidence.get(iid)
            lines.append("- %s %s%s" % (mark.get(a, "[ ]"), q, " *(auto: %s)*" % ev[1] if ev else ""))
            if a in ("no", "partial"):
                todo.append(q)
        lines.append("")
    if todo:
        lines += ["## To do", ""] + ["%d. %s" % (i, q) for i, q in enumerate(todo, 1)] + [""]
    return "\n".join(lines)
