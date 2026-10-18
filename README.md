# Geophysical Research Workflow

**A lightweight Agent Skill for reproducible geophysical research and evidence-led scientific writing.**

[简体中文](README.zh-CN.md) · [Skill instructions](SKILL.md) · [Synthetic walkthrough](examples/README.md) · [Example output](examples/synthetic-output/demo_metrics.json) · [Publication checklist](docs/publishing.md)

> **Scope:** An agent workflow, reproducibility scaffold and metadata validator — **not** a gravity inversion engine, seismic tomography solver, autonomous literature verifier or certification of scientific validity.

## Why this exists

Geophysical studies often combine observations, geometry assumptions, inversions, prior models, controlled recovery experiments, figures and manuscript claims. Mixing those roles can create conclusions that are difficult to audit. This Skill encourages a **question → registered comparison → traceable output → uncertainty → defensible claim** workflow.

```
Question and input permissions
           |
           v
  RESEARCH: dataset roles -> experiment register -> controlled comparisons
           |                             |
           |                             v
           |                   results + hash manifest
           v                             |
  PUBLICATION: claim/evidence <- results - figures - citation audit
           |
           v
  RELEASE: permission review + static scan + synthetic-only public example
```

## Features

| Mode | What it helps with | What it does *not* do |
| --- | --- | --- |
| Research | Dataset provenance, prior/observation separation, synthetic recovery design, Moho/regularization checks | Perform a physically valid inversion by itself |
| Publication | Claim-to-evidence ledgers, figure provenance, reference and reviewer audit | Verify unread literature or invent results |
| Release | Repository hygiene, private-data boundaries, static publication checks | Certify ownership or guarantee absence of secrets |
| Migration | Separate reusable rules from legacy project assumptions | Automatically transfer obsolete scientific conclusions |

**Bundled Python tools** require Python 3.10+ and the standard library only. The Skill itself is Markdown, designed for Agent Skills-compatible clients. The validator performs **structural checks**: file presence, dataset roles, time ordering, evidence links and SHA-256 hashes. It does not verify the truth of the research.

## Install

Clone this repository, then place the *entire* `geophysical-research-workflow/` folder into a skill directory recognized by your client. For example, for an agent that supports project-local `.agents/skills/`:

```bash
mkdir -p .agents/skills
cp -R /path/to/geophysical-research-workflow .agents/skills/geophysical-research-workflow
```

Replace `/path/to/` with the actual location. Agent clients differ in supported skill locations; check your client's documentation. Copy `SKILL.md` **together with** `references/`, `assets/` and `scripts/`. Installation/discovery in a live agent environment still needs confirmation.

Ask your agent:

> Use `geophysical-research-workflow` to audit the provenance, prior roles and synthetic resolution evidence of my gravity inversion before making any claims.

## Try the offline checks

Execute the following *from the source Skill directory*:

```bash
# Keep real research projects OUTSIDE this public repository.
python scripts/workflow.py init ../my-geophysics-study
# Edit ../my-geophysics-study/project.json and register experiments/datasets.
python scripts/workflow.py validate ../my-geophysics-study
# Expected initially: FAIL (incomplete template). This is intentional.

python scripts/demo_resolution.py --output ../toy-output
python scripts/build_toy_project.py ../toy-audited-project
python scripts/workflow.py validate ../toy-audited-project
# Expected: STRUCTURE_OK_SCIENCE_UNVERIFIED

python scripts/validate_skill.py .
python scripts/check_release.py .
python -m unittest discover -s tests -v
```

**Synthetic example:** the 1D signal uses an abstract coordinate and fixed seed. It is not measured seismic/gravity data and is not a geophysical forward/inverse problem. Its outputs are only an illustration of auditing and reproducibility mechanics.

## Repository layout

```text
geophysical-research-workflow/
├── SKILL.md                  # Agent Skill entrypoint
├── scripts/                  # Initialize, validate, hash, scan, synthetic demo
├── references/               # Research, publication and privacy protocols
├── assets/                   # Blank research ledgers and project template
├── examples/                 # Synthetic walkthrough and sample outputs
├── tests/                    # Standard-library regression tests
├── docs/publishing.md        # How to create a safe GitHub release
├── .github/workflows/ci.yml  # Automated checks (on GitHub after publishing)
├── LICENSE                   # MIT, repository-authored materials only
├── CONTRIBUTING.md
├── SECURITY.md
└── CHANGELOG.md
```

## Scientific and security boundaries

- A record labeled `validated` is a **researcher-entered workflow status**, not a scientific endorsement. It must have a real file and matching SHA-256 manifest entry.
- A preregistration timestamp does not prove the design predates analysis; audit immutable logs or dated commits separately.
- Similar numerical fits do not establish uniqueness; synthetic non-recovery does not prove a geological feature is absent.
- Do not copy any third-party maps, data, code, paper figures, manuscripts or reviewer materials into a public Skill without permission.
- The release scanner is heuristic and cannot inspect past commits or establish legal rights. Run it **and** perform manual permission and secret reviews before making a repository public.

## Contributing and licensing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution checks and [SECURITY.md](SECURITY.md) for private vulnerability reporting. MIT applies to newly authored material in this repository; it **does not** relicense any underlying third-party scientific data or collaborators' code.

This public Skill was generalized from a domain-specific two-track research-and-manuscript workflow. Its private project data, numerical results and publication correspondence are intentionally not included.
