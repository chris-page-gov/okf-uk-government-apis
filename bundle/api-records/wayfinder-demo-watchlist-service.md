---
type: "API Product"
title: "Watchlist Checking Service"
description: "Real-time checking against security and immigration watchlists."
resource: "https://api.border.demo.gov.example/watchlist/v2"
tags: ["api", "government-services", "matching", "rest-http", "security", "synthetic-demo", "watchlist", "wayfinder", "wayfinder-demo-bia"]
generated: { by: process:uk-government-api-okf-builder, at: "2026-07-16T00:00:00Z" }
status: draft
sources: [{ id: "wayfinder_demo", resource: "https://wayfinder.pbj.cx/services/watchlist-service", title: "Wayfinder fictional service catalogue", last_modified: "2026-02-28" }]
confidence: "source-captured"
source_adapter: "wayfinder_demo"
---

# Watchlist Checking Service

Real-time checking against security and immigration watchlists.

## Metadata

- Type: API Product
- Provider: [Border & Identity Agency (Wayfinder demo)](../organisations/wayfinder-demo-bia.md)
- Canonical provider: Wayfinder Demo Bia
- Source adapter: wayfinder_demo
- Source tier: synthetic_demo
- Confidence: source-captured
- Assurance status: synthetic-demo-not-assessed
- Access model: approval-required
- Contract status: placeholder-demo-contract
- Licence: Rights not specified (not-specified)
- Licence basis: source-rights-not-specified
- Licence source: https://wayfinder.pbj.cx/services/watchlist-service
- Licence confidence: 0.0
- Quality band: medium
- DCAT term: `dcat:DataService`
- OpenAPI term: `OpenAPI Object`

- Endpoint: https://api.border.demo.gov.example/watchlist/v2
- Documentation: https://docs.demo.gov.example/watchlist

## Standards Alignment

This generated record is standards-alignable, not standards-conformant by itself. DCAT-AP conformance needs an RDF export; OpenAPI conformance needs a complete `openapi` document.

- DCAT / DCAT-AP: `dcat:DataService`; export status `data-service-with-gaps`.
- DCAT missing requirements: `dcterms:license`
- OpenAPI: `OpenAPI Object`; export status `service-stub-with-gaps`.
- OpenAPI security scheme: `metadata-only`.
- OpenAPI missing requirements: `info.license`
- Crosswalk: [OKF Standards Crosswalk](../docs/okf-standards-crosswalk.md)

## Credential Requirements

- approval_required: secret value stored in OKF = False

## Sample Policy

- Mode: static-placeholder
- Live calls enabled: False

## Provenance

- Source: Wayfinder fictional service catalogue
- Source URL: https://wayfinder.pbj.cx/services/watchlist-service
