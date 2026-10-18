# Research mode: operational protocol

## Gate R0 — Find the current state

- Inspect project instructions, last update, registered experiments, frozen decisions, figure/data manifests, notebooks and computation scripts.
- Distinguish current scientific state from historical record. Newest timestamp alone may not be authoritative: compare lineage and user decisions.
- Preserve project vocabulary: define Moho A/B/C (or other labels) from the **active version** rather than assuming universal meanings.
- Scope creep and reanalysis require an explicit decision; avoid duplicating expensive computations when results already exist.

## Gate R1 — Define testable comparison

- State observable and reference conventions: gravity anomaly class, reduction density, datum and units; wave velocity definitions and anisotropy conventions; depth positive down, coordinate reference and resolution.
- State multiple geologically distinct but observationally competing hypotheses, including a non-identifiable alternative.
- Identify target measure, decision thresholds, minimum recoverable size, error model, and what falsifies each hypothesis.
- Freeze comparison window, parameterization and preprocessing **before** accessing result-dependent selections.

## Gate R2 — Data lineage / observation independence

- Record author/provider, version/DOI, license, native resolution, origin, checksums, shared source ancestry, filtering, sampling and masking.
- Separate observation and model prior from control geometry. An imported tomographic density may invalidate gravity-only independence; imported Moho geometry limits full independence.
- Comparing two gravity models sharing satellite/terrestrial observations is a *consistency comparison*, not automatically independent replication.
- Coordinate and units tests, band match, overlap, interpolation and boundary tests are mandatory prior to scientific comparison.

## Gate R3 — Controlled analysis

Design a reproducible matrix across relevant axes rather than varying everything at once:

- Moho geometry and its uncertainty, regularization, reference density, depth parameterization, horizontal grid/window, spectral filtering and solver tolerance.
- Synthetic truths with different amplitudes, transition widths and centers; blind and wrong-model recoveries; correlated and heteroscedastic noise if applicable.
- Spatial null and nonstationary background tests, edge effects, uncertainty intervals, numerical convergence, repeated seeds and withheld-data validation when feasible.
- Specify how equal-weight vs volume-weight averaging affects reported contrasts; use physical weights appropriate to geometry.
- An interpolation sensitivity test is **not** an increase in native information resolution.

## Gate R4 — Evaluate without overclaiming

Keep distinct fields for:

1. Best score among candidates (model-dependent fit);
2. Decision rule/gate pass (a declared detection criterion);
3. Recoverability when truth is known (synthetic resolution);
4. Independent observation concordance vs shared-source consistency;
5. Geological interpretation and competing mechanisms.

An attractive image, narrow posterior interval conditional on strong priors, or optimizer convergence cannot replace evidence of unique structure. Track adverse members, null rate, uncertainty and data sensitivity.

## Gate R5 — Handoff

Store versioned results and readable summary: what changed, why, frozen vs amended assumptions, executed commands, data lineage, failures, reproducibility limitations and exact next action. Preserve source links or IDs in offline reports; distinguish inaccessible sources from negative search results.
