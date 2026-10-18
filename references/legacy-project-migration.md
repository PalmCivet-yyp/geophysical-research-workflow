# Migrating a legacy research workflow (general case)

Use this reference when an existing project has historical instructions but no installable Skill, conflicting versions, or obsolete project-specific decision records.

1. Inventory old agent notes/configuration, standalone skill files, executable scripts, datasets, paper drafts, publication evidence and file manifests. Record which pieces actually exist; never infer a runnable skill from a routing name alone.
2. Identify the **current authoritative version**: compare dated research decisions, data windows, model conventions, reviewer changes and reproducibility logs. Do not assume the newest file by name is the scientifically accepted version.
3. Separate timeless workflow rules (provenance, controlled comparisons, evidence/citation audit) from contingent facts (study area, spectral band, solver, inversion coefficients, accepted claims, paper status).
4. Put timeless instructions in the public `SKILL.md` and `references/`; store project-specific state in a **private project directory** unless all data and publication rights are confirmed.
5. First run the helper scripts with synthetic-only data. Integrate with actual scientific solvers only after project-specific input requirements and dependencies are reviewed.
6. Document what was migrated, what was discarded, what needs revalidation and whether unpublished content can be shared.

**Publication-safe rule:** Never copy an internal scientific decision, unpublished figure or numeric result into the public Skill just to demonstrate how it works. A labeled synthetic example is sufficient for feature testing.
