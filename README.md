# repro-checklist

**How reproducible is your project? Get a scored checklist (data, code, environment, analysis)
with items detected automatically from the project folder and a to-do list for the rest.**

Part of the *Research Automation Toolkit*: 100 open tools for daily research work.

## Why

Journals (Nature's reporting summaries), conferences (NeurIPS, ACM artifact badges) and funders
ask for reproducibility checklists, usually right before submission when there is no time to fix
anything. Running the checklist early and often, with automatic evidence where possible, turns it
into a planning tool instead of a last-minute form.

## Features

- 20 items in four sections: Data, Code, Environment, Analysis
- Automatic detection of README, licence, git, CITATION.cff, tests, dependency files and pinning,
  container recipes, pipelines (Makefile, Snakefile, dvc.yaml ...), raw data folder, checksum manifests,
  codebooks, data availability statements and notebooks committed with outputs
- Interactive mode for the remaining items (`yes/no/partial/na`), answers saved as JSON for next time
- Markdown report with per-section scores, evidence notes and a to-do list

## Usage

```bash
pip install .
repro-checklist path/to/project
repro-checklist . -i --save-answers repro_answers.json -o REPRODUCIBILITY.md
repro-checklist . --answers repro_answers.json
```

## Testing

```bash
python -m unittest discover -s tests -t .
```

## License

MIT (c) JANIN A APURBA
