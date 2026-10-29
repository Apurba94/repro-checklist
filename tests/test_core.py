import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout

from repro_checklist.cli import main
from repro_checklist.core import CHECKLIST, auto_detect, render_report, score


def touch(root, rel, text="x"):
    p = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(text)


class DetectTests(unittest.TestCase):
    def test_empty_project(self):
        with tempfile.TemporaryDirectory() as d:
            ev = auto_detect(d)
            self.assertFalse(ev["code-readme"][0])
            self.assertFalse(ev["env-deps"][0])

    def test_well_set_up_project(self):
        with tempfile.TemporaryDirectory() as d:
            touch(d, "README.md", "Data availability: https://doi.org/10.5281/zenodo.1")
            touch(d, "LICENSE")
            touch(d, "CITATION.cff")
            touch(d, "requirements.txt", "numpy==2.1.0\npandas==2.2.2\n")
            touch(d, "tests/test_x.py")
            touch(d, "data/raw/MANIFEST.sha256")
            touch(d, "docs/codebook.md")
            touch(d, "pipeline.json")
            touch(d, "nb/a.ipynb", json.dumps({"cells": [{"cell_type": "code", "outputs": []}]}))
            ev = auto_detect(d)
            for iid in ("code-readme", "code-license", "code-citation", "env-deps", "env-pinned", "code-tests",
                        "data-checksums", "data-dictionary", "code-single-entry", "data-availability",
                        "data-raw-separate", "ana-notebooks-clean"):
                self.assertTrue(ev[iid][0], iid)

    def test_unpinned_and_dirty_notebook(self):
        with tempfile.TemporaryDirectory() as d:
            touch(d, "requirements.txt", "numpy\n")
            touch(d, "a.ipynb", json.dumps({"cells": [{"cell_type": "code", "outputs": [{"text": "1"}]}]}))
            ev = auto_detect(d)
            self.assertFalse(ev["env-pinned"][0])
            self.assertFalse(ev["ana-notebooks-clean"][0])


class ReportTests(unittest.TestCase):
    def test_score(self):
        ids = [i for items in CHECKLIST.values() for i, _, _ in items]
        self.assertEqual(score({i: "yes" for i in ids})["total"], 100)
        s = score({"data-availability": "yes", "data-raw-separate": "partial", "data-checksums": "na"})
        self.assertEqual(s["Data"], 75)
        self.assertIsNone(s["Code"])

    def test_report_and_cli(self):
        md = render_report({"code-readme": "yes", "code-license": "no"})
        self.assertIn("- [x] Does a README", md)
        self.assertIn("## To do", md)
        with tempfile.TemporaryDirectory() as d:
            touch(d, "README.md")
            answers = iter(["y", "n", "p"] + ["na"] * 20)
            with redirect_stdout(io.StringIO()) as buf:
                main([d, "-i", "--save-answers", os.path.join(d, "a.json")], ask=lambda prompt: next(answers))
            self.assertIn("Overall score", buf.getvalue())
            with open(os.path.join(d, "a.json"), encoding="utf-8") as fh:
                self.assertEqual(json.load(fh)["data-license"], "yes")


if __name__ == "__main__":
    unittest.main()
