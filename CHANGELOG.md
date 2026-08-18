# Changelog

## Unreleased — 2026-08-18

- Added the OKF publication-method v1 repository contract, local structural
  validation and documentation/`CHANGELOG.md` lockstep enforcement.
- Removed duplicate feature-branch push validation while retaining pull
  request, integrated `main`, version-tag and manual assurance; added per-ref
  cancellation, bounded job time and immutable action pins.
- Made Pages wait for the complete `main` validation and deploy the exact
  checked-in preview without rebuilding or reacquiring it. Manual deployment
  runs the complete non-mutating gate first.
- Added bounded post-deploy verification of the exact checksum manifest,
  landing page, Explorer descriptor and record-count manifest.

- Made the Markdown tree the canonical OKF v0.2 layer while retaining the
  large-corpus Explorer, YAML-LD, JSON-LD, search, adjacency and provenance
  extensions.
- Replaced legacy concept `timestamp` fields with structured `generated` and
  `sources`; source modification dates now remain source credibility signals
  rather than being mislabelled as publication time.
- Kept verification absent because this generated preview has not acquired
  independent human or machine confirmation.
- Added structural v0.2 validation for all Markdown concepts and synchronised
  descriptor declarations.
- Added Department for Education Get Information about Schools (GIAS) discovery records for the national register, beta read-only API prototype and supported establishments download alternative.
- Recorded DfE URN identity guidance, Warwickshire LA code 937, OGL v3.0 provenance, API support status and typed links between the service, prototype and download.
- Refreshed the generated multi-source bundle and made the publication upgrade restore copied documentation and the static landing page after regeneration.

## 0.4.0 — 2026-07-11

- Published as an independent YAML-LD OKF Bundle Wiki.
- Added semantic descriptors, compressed route adjacency, checksums, CI and Pages.
