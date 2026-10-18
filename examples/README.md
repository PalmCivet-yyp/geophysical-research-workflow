# Synthetic example and honest expected outcomes

These examples are deliberately abstract 1-D signals. They have **no actual gravity forward operator**, geographic boundary, observational dataset, geological inference, or recovery-resolution validation.

From a cloned Skill repository:

```bash
# Choose a research folder OUTSIDE the Skill source checkout.
python scripts/workflow.py init ../my-geophysics-study
# Edit ../my-geophysics-study/project.json and add your own authorized data/experiments.
python scripts/workflow.py validate ../my-geophysics-study
# Expected: FAIL until required fields are completed.

python scripts/demo_resolution.py --output ../toy-output
python scripts/build_toy_project.py ../toy-audited-project
python scripts/workflow.py validate ../toy-audited-project
# Expected: STRUCTURE_OK_SCIENCE_UNVERIFIED
```

## What to inspect

- `../toy-output/demo_metrics.json`: fixed random seed, blur settings and `scientific_decision: NOT_ASSESSED`.
- `../toy-audited-project/experiment_registry.csv`: explicit toy registration and execution time labels.
- `../toy-audited-project/evidence_ledger.csv`: traceable synthetic-only claim and limitations.
- `../toy-audited-project/file_manifest.csv`: original file paths and their actual SHA-256 hashes.

A `validated` row is a researcher's own status label in a project registry. This CLI only audits its metadata and file links; it does **not** verify whether the underlying physics or conclusions are correct.
