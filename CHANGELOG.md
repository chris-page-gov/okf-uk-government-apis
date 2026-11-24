# Changelog

## 0.5.0 — 2026-11-24 — OKF core 0.3 migration

- Migrated the frozen 16 July 2026 catalogue to the reviewed OKF core 0.3
  contract and Bundle Wiki v2 repository profile while preserving the frozen
  v1 schemas and semantic assertion identities.
- Added a complete Reader projection for all 3,464 typed Markdown concepts,
  separate from the metadata extension graph, with source paths, full bodies,
  frontmatter and SHA-256 digests.
- Labelled typed concepts and metadata-only extensions explicitly, retaining
  the 278,156 existing metadata assertions and the rejected synthetic
  Wayfinder boundary.
- Pinned the active Python bootstrap to uv 0.13.4, which removes the affected
  bundled certificate root, without changing Python or dependency versions.
- Added a source-linked notification catalogue walkthrough. It distinguishes
  similarly named snapshot records, source-reported licence metadata and the
  synthetic Wayfinder negative control; it makes no live availability claim.
- Added a distinct source-linked core walkthrough with its own core descriptor,
  authored Markdown relationship, source digests, diagrams and negative
  controls. It does not use the metadata extension graph or claim live service,
  access or licence status.
- Added separate core and metadata Reader journey manifests and made the pinned
  Chromium journeys a required CI gate. Added a second browser gate that clicks
  both guide links at desktop and mobile sizes, checks accessibility and source
  controls, and fetches every checksum-listed bundle asset over local HTTP.
  Deployment verification binds both descriptors, both manifests and both
  walkthroughs to the exact candidate.
- Added a pinned Explorer Reader source-import parity gate for all typed Markdown
  frontmatter, bodies, links, source hashes and directed core edges.
- Added a frozen baseline check proving the 140 legacy relationship chunks and
  source graph identity files are byte-identical to the 16 July source commit,
  retaining all 278,156 assertion identities before and after migration.

## Unreleased — standards references

- Link the central current and historical OKF standards register and public bundle catalogue.


## Unreleased — 24 September 2026

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

- Canonicalised future and frozen CKAN provenance URLs with deterministic
  percent encoding, and made relationship publication reject unsafe or
  non-canonical authority, evidence, evidence-resource and rights URLs. The
  updated shared Explorer assertion schema is pinned and published byte-for-byte.
- Canonicalised derived protocol targets as safe, collision-checked,
  suffix-free local routes while retaining the harvested protocol label and
  legacy route as aliases in runtime and semantic projections.
- Added explicit `source_iri` and `target_iri` requirements to the repository
  contract and deep route-safety/alias validation to the offline release gate.
- Compiled every directed relationship into a stable evidence-bearing OKF
  assertion with absolute entity/predicate IRIs, validated local routes,
  preferred and inverse labels, authority, derivation, observation time,
  source adapter/tier/confidence, record-level licence context and rights.
- Replaced the descriptor-only semantic surface with a bounded graph manifest,
  pinned local context and schema, predicate registry, gzip JSON-LD direct
  triple/entity shards and matching reified assertion shards. Rich Explorer
  gzip relationship chunks and compressed adjacency now derive from the same
  deterministic assertion list, keeping every individual artefact and the
  complete static publication within bounded hosting limits.
- Added a digest-bound material relationship runtime with explicit
  status/scope/authority planes, SHA-256 route-locator buckets and exact
  per-route assertion-count and sorted-identity commitments. Historical and
  rejected synthetic fixture planes are opt-in; all active planes remain in
  the Reader default as required by the pinned profile.
- Bound runtime validation to the Reader's 64 MiB decoded-resource ceiling,
  route and supporting-assertion limits, duplicate evidence/chunk rejection and
  the complete semantic identity and governed metadata projection.
- Preserved the complete assertion graph in semantic shards and compatibility
  chunks while keeping the default Reader projection within aggregate row,
  compressed-byte and retained-text limits.
- Added exhaustive Draft 2020-12 validation of every runtime and semantic
  relationship assertion, with a generated conformance receipt checked during
  release validation.
- Extended the pinned local JSON-LD context and no-network expansion tests so
  nested authority, evidence, rights and supporting-assertion provenance
  survive expansion.
- Added a locked `uv` validation environment for JSON Schema and JSON-LD
  tooling.
- Kept the semantic plane explicitly metadata-only: it neither executes APIs
  nor upgrades catalogue discovery metadata into service assurance.
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
- Captured and reconciled all 311 publicly exported Wayfinder demonstration
  records with source response metadata and content hashes. Added 85 new
  namespaced synthetic service records without fuzzy-merging eight probable
  title similarities into real APIs.
- Preserved every Wayfinder service field, department, team and available
  pattern metadata; published the full source capture and reconciliation; and
  recorded 707 relationships as synthetic, rejected from real-world catalogue
  admission and absent from the active material runtime.
- Recorded Wayfinder rights as not specified and attributed the concept to
  Paul Buchanan-Jones without publishing the private correspondence, email
  address or message text supplied to the maintainers.

## 0.4.0 — 2026-07-11

- Published as an independent YAML-LD OKF Bundle Wiki.
- Added semantic descriptors, compressed route adjacency, checksums, CI and Pages.
