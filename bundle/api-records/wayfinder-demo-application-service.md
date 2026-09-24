---
type: "API Product"
title: "Benefit Application Service"
description: "Handles benefit application submissions, validation, and routing to appropriate teams."
resource: "https://api.citizen-support.demo.gov.example/applications/v1"
tags: ["api", "applications", "benefits", "government-services", "rest-http", "submissions", "synthetic-demo", "wayfinder", "wayfinder-demo-dcs"]
generated: { by: process:uk-government-api-okf-builder, at: "2026-07-16T00:00:00Z" }
status: draft
sources: [{ id: "wayfinder_demo", resource: "https://wayfinder.pbj.cx/services/application-service", title: "Wayfinder fictional service catalogue", last_modified: "2026-02-25" }]
confidence: "source-captured"
source_adapter: "wayfinder_demo"
---

# Benefit Application Service

Handles benefit application submissions, validation, and routing to appropriate teams.

## Metadata

- Type: API Product
- Provider: [Department for Citizen Support (Wayfinder demo)](../organisations/wayfinder-demo-dcs.md)
- Canonical provider: Wayfinder Demo Dcs
- Source adapter: wayfinder_demo
- Source tier: synthetic_demo
- Confidence: source-captured
- Assurance status: synthetic-demo-not-assessed
- Access model: oauth2
- Contract status: placeholder-demo-contract
- Licence: Rights not specified (not-specified)
- Licence basis: source-rights-not-specified
- Licence source: https://wayfinder.pbj.cx/services/application-service
- Licence confidence: 0.0
- Quality band: medium
- DCAT term: `dcat:DataService`
- OpenAPI term: `OpenAPI Object`

- Endpoint: https://api.citizen-support.demo.gov.example/applications/v1
- Documentation: https://docs.demo.gov.example/applications

## Standards Alignment

This generated record is standards-alignable, not standards-conformant by itself. DCAT-AP conformance needs an RDF export; OpenAPI conformance needs a complete `openapi` document.

- DCAT / DCAT-AP: `dcat:DataService`; export status `data-service-with-gaps`.
- DCAT missing requirements: `dcterms:license`
- OpenAPI: `OpenAPI Object`; export status `service-stub-with-gaps`.
- OpenAPI security scheme: `oauth2`.
- OpenAPI missing requirements: `info.license`
- Crosswalk: [OKF Standards Crosswalk](../docs/okf-standards-crosswalk.md)

## Credential Requirements

- oauth2: secret value stored in OKF = False

## Sample Policy

- Mode: static-placeholder
- Live calls enabled: False

## Provenance

- Source: Wayfinder fictional service catalogue
- Source URL: https://wayfinder.pbj.cx/services/application-service
