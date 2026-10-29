"""Command-line interface for repro-checklist."""
import argparse
import json
import os

from .core import CHECKLIST, auto_detect, render_report


def main(argv=None, ask=input):
    ap = argparse.ArgumentParser(prog="repro-checklist", description="Reproducibility checklist for a project.")
    ap.add_argument("project", nargs="?", default=".")
    ap.add_argument("--answers", help="JSON with answers (yes/no/partial/na) for manual items")
    ap.add_argument("-i", "--interactive", action="store_true", help="ask about items that cannot be detected")
    ap.add_argument("-o", "--output", help="write the Markdown report here")
    ap.add_argument("--save-answers", help="store all answers as JSON for next time")
    args = ap.parse_args(argv)
    ev = auto_detect(args.project)
    answers = {k: "yes" if ok else "no" for k, (ok, _) in ev.items()}
    if args.answers:
        with open(args.answers, encoding="utf-8") as fh:
            answers.update(json.load(fh))
    if args.interactive:
        for sec, items in CHECKLIST.items():
            for iid, q, _ in items:
                if iid in ev or (args.answers and iid in answers):
                    continue
                a = ""
                while a not in ("yes", "no", "partial", "na"):
                    a = (ask("[%s] %s (yes/no/partial/na): " % (sec, q)) or "no").strip().lower()
                    a = {"y": "yes", "n": "no", "p": "partial"}.get(a, a)
                answers[iid] = a
    report = render_report(answers, ev, os.path.basename(os.path.abspath(args.project)))
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(report)
        print("report written to %s" % args.output)
    else:
        print(report)
    if args.save_answers:
        with open(args.save_answers, "w", encoding="utf-8") as fh:
            json.dump(answers, fh, indent=1, sort_keys=True)
    return 0
