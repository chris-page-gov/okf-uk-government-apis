---
type: "Reference"
title: "okf bundle wiki architecture 2026 07 11"
generated: { by: process:uk-government-api-okf-builder, at: "2026-07-16T00:00:00Z" }
status: draft
sources: [{ id: "repository-source", resource: "https://github.com/chris-page-gov/okf-uk-government-apis/blob/main/docs/okf-bundle-wiki-architecture-2026-07-11.md", title: "okf-bundle-wiki-architecture-2026-07-11.md" }]
---
# Federated OKF Bundle Wiki architecture

Decision date: 11 July 2026. Status: implementation in progress.

Production OKF bundles are independently versioned and independently published
units. The Explorer owns the generic application, profile/context, conformance
tooling, small fixtures and curated registry; registry entries point to bundle
descriptors rather than copying production corpora into the product repository.

Repository-per-bundle is the default when ownership, sources or release cadence
differ. A monorepo remains valid if every bundle builds and publishes through an
independent descriptor, manifest, release and stable URL.

## Semantic and runtime layers

Markdown YAML-LD frontmatter and the deterministic relationship assertion
compiler are the semantic inputs. `okf-bundle.yamlld` and its equivalent
`okf-bundle.jsonld` are bounded graph descriptors. They point to a digest-bound
semantic manifest whose gzip JSON-LD entity shards contain direct triples and
whose assertion shards contain matching evidence-bearing `rdf:Statement` and
`okf:RelationshipAssertion` nodes. Builds compile the same assertion list into
the current Explorer JSON descriptor, complete compatibility chunks, adjacency
indexes and a bounded rich runtime.

Large-corpus descriptors carry stable identity, version, publication status,
publisher, licence, profile and semantic-descriptor links. Relationship indexes
use deterministic UTF-8 FNV-1a hash buckets so selection hydrates one route's
adjacency without loading the corpus-wide edge table. Full relationship chunks
remain available for explicit corpus-wide analysis, subject to the Explorer's
documented memory cap, and are published as Reader-supported gzip JSON rather
than a gigabyte-scale uncompressed plane. The default rich runtime retains a
governed material relationship subset in explicit scope/authority planes and
uses a SHA-256 route locator with exact assertion-count and identity-digest
commitments. Synthetic-fixture planes are opt-in. Semantic graph shards are
independently compressed, hashed and kept below GitHub's single-file boundary;
the root descriptor never requires a Reader to hydrate the complete graph.

The Explorer continues to consume JSON during the migration. Arbitrary remote
context retrieval is not enabled in the browser. Contexts are allowlisted,
pinned locally and expanded during deterministic builds.

## Standard public contract

- `/` human landing page;
- `/okf-bundle.yamlld` canonical YAML-LD descriptor;
- `/okf-bundle.jsonld` JSON-LD equivalent;
- `/okf-explorer.json` Explorer runtime descriptor;
- `/data/manifest.json` counts, indexes and chunks;
- `/data/semantic/manifest.json` semantic entity/direct-triple and reified
  assertion shards, counts and digests;
- `/data/semantic/validation-report.json` exhaustive Draft 2020-12 assertion
  validation receipt;
- `/data/relationship-runtime/manifest.json` bounded material runtime and
  default-plane policy;
- `/data/relationship-runtime/route-locator/manifest.json` SHA-256 route
  locator and bucket commitments;
- `/data/predicate-registry.json` governed direction, label and inverse-label
  definitions;
- `/context/okf-bundle-v1.jsonld` pinned context;
- `/schemas/okf-relationship-assertion.v2.schema.json` pinned assertion shape;
- `/checksums.json` generated artefact integrity metadata.

Large bundles may keep curated Markdown documentation while source records live
in generated chunks and virtual routes. A standard bundle wiki does not require
one committed Markdown file per source record.

## Current migration

1. Land the profile, semantic parser, registry generator and constraints ledger.
2. Extend the Explorer identity and relationship contracts.
3. Extract UK Legislation, UK Government APIs and AI Infrastructure into
   independent repositories and Pages publications.
4. Rename this product repository to `okf-explorer` while preserving current
   URLs for a deprecation cycle.
5. Add full-corpus structural relationships, official legal-effects expansion,
   governed subject/citation/entity enrichment and optional trusted registries.

The detailed implementation decision and the legislation review that motivated
it are retained in the local Legislation OKF workspace review artefacts.
