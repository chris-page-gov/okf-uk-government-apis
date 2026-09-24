---
type: "API Product"
title: "Patient Demographics Service"
description: "Master patient index providing demographics, NHS number lookup, and patient matching."
resource: "https://api.health-data.demo.gov.example/pds/v2"
tags: ["api", "demographics", "government-services", "health-and-care", "nhs-number", "pds", "rest-http", "synthetic-demo", "wayfinder", "wayfinder-demo-nhds"]
generated: { by: process:uk-government-api-okf-builder, at: "2026-07-16T00:00:00Z" }
status: draft
sources: [{ id: "wayfinder_demo", resource: "https://wayfinder.pbj.cx/services/patient-demographics-api", title: "Wayfinder fictional service catalogue", last_modified: "2026-03-05" }]
confidence: "source-captured"
source_adapter: "wayfinder_demo"
---

# Patient Demographics Service

Master patient index providing demographics, NHS number lookup, and patient matching.

## Metadata

- Type: API Product
- Provider: [National Health Data Service (Wayfinder demo)](../organisations/wayfinder-demo-nhds.md)
- Canonical provider: Wayfinder Demo Nhds
- Source adapter: wayfinder_demo
- Source tier: synthetic_demo
- Confidence: source-captured
- Assurance status: synthetic-demo-not-assessed
- Access model: oauth2
- Contract status: placeholder-demo-contract
- Licence: Rights not specified (not-specified)
- Licence basis: source-rights-not-specified
- Licence source: https://wayfinder.pbj.cx/services/patient-demographics-api
- Licence confidence: 0.0
- Quality band: medium
- DCAT term: `dcat:DataService`
- OpenAPI term: `OpenAPI Object`

- Endpoint: https://api.health-data.demo.gov.example/pds/v2
- Documentation: https://docs.demo.gov.example/pds

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
- Source URL: https://wayfinder.pbj.cx/services/patient-demographics-api
