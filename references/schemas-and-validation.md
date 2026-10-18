# Local project contract and checks

`python scripts/workflow.py init <directory-outside-skill-checkout>` creates `project.json`, `experiment_registry.csv`, `evidence_ledger.csv`, `figure_manifest.csv`, `citation_audit.csv`, `file_manifest.csv` and empty `data`, `results`, `figures`, `code`, `notes` directories. It never overwrites existing files. The scaffold has an incomplete project question and must be edited before `validate` can pass.

## `project.json`

Required: `project_id`, `research_question`, `status`, `updated_utc`, `spatial_context` (object containing `crs`, `horizontal_domain`, `vertical_datum`, `depth_positive`, `units`), `datasets` (array of records with unique `dataset_id`, `role`, `name`, `source`, `version`, `license_notes`).

Roles: `observation`, `geometry`, `prior`, `external_model`, `posthoc_diagnostic`, `context`.

## `experiment_registry.csv`

Columns: `experiment_id,analysis_type,dataset_ids,registered_at_utc,executed_at_utc,status,hypothesis,decision_rule,controls,output_path`.
`analysis_type`: `gravity_only`, `prior_conditioned`, `posthoc_diagnostic`, `other`.
`status`: `planned`, `running`, `validated`, `failed`, `superseded`.
`dataset_ids` is pipe-separated. A `gravity_only` record referencing `prior`, `external_model` or `posthoc_diagnostic` as an input is rejected (these can still be used in **separate** diagnosis experiments). `geometry` is allowed but implies geometry-conditional results.
The date rule guards against *obvious* backdating; it cannot prove genuine preregistration. Keep immutable logs or dated commits for external audit.

## `evidence_ledger.csv`

Columns: `claim_id,claim_text,experiment_id,result_path,locator,uncertainty,limitations,status,allowed_wording`.
`status`: `draft`, `validated`, `rejected`, `superseded`. For `validated`, an existing result path and a validated experiment ID are mandatory. Claim validation is evidence *linkage* only, not a numerical or peer-review endorsement. Rows marked `validated` require a matching SHA-256 entry in `file_manifest.csv`. This checks byte identity, not physical/statistical correctness.

## `figure_manifest.csv`

Columns: `figure_id,figure_path,source_data_path,code_path,units,crs,display_transforms,status`.
For `status=final`, all file paths must exist; transforms, units and coordinate reference must be documented.

## `citation_audit.csv`

Columns: `citation_id,claim_ids,doi_or_url,title,authors,year,metadata_verified,direct_support_verified,notes`.
Verification values: `yes`, `no`, `pending`. `yes` must mean human/tool access to actual sources, not a model guess; the script checks only field consistency.

## `file_manifest.csv`

Columns: `relative_path,sha256,origin,license_notes`. When `sha256` is filled, the file is re-hashed to verify its integrity. Author-marked `validated` experiments and claims require hashed outputs in this manifest. Always record the true origin and permission status of each file.

## CLI boundaries

- `validate`: structural verification, guarded reference checking, basic status and time ordering, checksums. The `validated` label is user-supplied, not independently assessed. Does not run a solver, validate geophysical units quantitatively, certify statistical inference, or browse literature.
- `hash`: calculates SHA-256 of a file (read-only).
- `demo_resolution.py`: 1-D smoothed synthetic profiles with fixed random seed, no geophysical forward operator. Its numbers must never be quoted as real-world geological results.
- `check_release.py`: heuristic release safety check, never a replacement for permissions review and Git history inspection.
