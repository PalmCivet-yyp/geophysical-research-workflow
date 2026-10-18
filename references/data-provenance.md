# Data audit and evidence-role taxonomy

| Role | Meaning | Permitted influence |
|---|---|---|
| `observation` | Measured or derived observable | In the objective, with explicit provenance and processing |
| `geometry` | Moho, relief, coordinates, survey model or boundary metadata | Affects forward/inverse geometry; discloses assumptions |
| `prior` | Structural/velocity/density target or model constraint | Only in registered prior-conditioned experiments |
| `external_model` | Published inversion or composite model | Post hoc comparison unless explicitly registered as prior |
| `posthoc_diagnostic` | Independent/other-modality interpretation input | Examined *after* primary results frozen |
| `context` | Geological maps, study descriptions | For communication; cannot retroactively set detection windows |

`observation` is not a warranty of statistical independence. Investigate overlapping original acquisition sources and processing chains.

## Minimal dataset entry

- `dataset_id`, `role`, `name`, `source`, `version`, `license_notes`, `checksum_sha256` (if local file), `native_resolution`, `crs`, `units`, `preprocessing`, `uncertainty`.
- A publishable README requires origin and license assessment, even when no files are redistributed.

## Controls specific to geophysics

- Gravity: distinguish complete Bouguer, simple Bouguer, free-air and gravity gradients; record normal field and terrain reductions, reference density, reference ellipsoid, wavelength/resolution and physical units (mGal/Eötvös).
- Seismology: identify Vp/Vs/Vsv/Vsh/Vs0 explicitly, anisotropy convention, smoothing kernels, period band, measurement uncertainties and dependence on inversion priors.
- Interfaces: Moho/RF and crustal models have differing supports, smoothing, datums and uncertainties; document interpolation and boundary artifacts.
- Grids and sections: native cell width, projected vs spherical geometry, partial cells, latitude-dependent cell area and volumetric weights; disallow 'upsampled' being called higher *measured* resolution.
- External density models: distinguish reported density, velocity-to-density conversion, relative anomalies and compositional interpretations.

## Provenance ledger rule

A number can enter an article only when its value, unit, source path, calculation definition, area/depth window, reduction choice, model member, uncertainty or interval, and status can be reconstructed from an artifact. If no verifiable artifact exists, keep it as tentative or explicitly unverified.
