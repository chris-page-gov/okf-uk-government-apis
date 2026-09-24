---
type: "API Product"
title: "Vehicle Enquiry API"
description: "Public API for checking vehicle tax, MOT status, and basic vehicle details."
resource: "https://api.vehicles.demo.gov.example/enquiry/v1"
tags: ["api", "enquiry", "mot", "public", "rest-http", "synthetic-demo", "tax", "tax-and-customs", "transport", "wayfinder", "wayfinder-demo-vla"]
generated: { by: process:uk-government-api-okf-builder, at: "2026-07-16T00:00:00Z" }
status: draft
sources: [{ id: "wayfinder_demo", resource: "https://wayfinder.pbj.cx/services/vehicle-enquiry-api", title: "Wayfinder fictional service catalogue", last_modified: "2026-03-10" }]
confidence: "source-captured"
source_adapter: "wayfinder_demo"
---

# Vehicle Enquiry API

Public API for checking vehicle tax, MOT status, and basic vehicle details.

## Metadata

- Type: API Product
- Provider: [Vehicle & Licensing Authority (Wayfinder demo)](../organisations/wayfinder-demo-vla.md)
- Canonical provider: Wayfinder Demo Vla
- Source adapter: wayfinder_demo
- Source tier: synthetic_demo
- Confidence: source-captured
- Assurance status: synthetic-demo-not-assessed
- Access model: api-key
- Contract status: placeholder-demo-contract
- Licence: Rights not specified (not-specified)
- Licence basis: source-rights-not-specified
- Licence source: https://wayfinder.pbj.cx/services/vehicle-enquiry-api
- Licence confidence: 0.0
- Quality band: medium
- DCAT term: `dcat:DataService`
- OpenAPI term: `OpenAPI Object`

- Endpoint: https://api.vehicles.demo.gov.example/enquiry/v1
- Documentation: https://docs.demo.gov.example/vehicle-enquiry

## Standards Alignment

This generated record is standards-alignable, not standards-conformant by itself. DCAT-AP conformance needs an RDF export; OpenAPI conformance needs a complete `openapi` document.

- DCAT / DCAT-AP: `dcat:DataService`; export status `data-service-with-gaps`.
- DCAT missing requirements: `dcterms:license`
- OpenAPI: `OpenAPI Object`; export status `service-stub-with-gaps`.
- OpenAPI security scheme: `apiKey`.
- OpenAPI missing requirements: `info.license`
- Crosswalk: [OKF Standards Crosswalk](../docs/okf-standards-crosswalk.md)

## Credential Requirements

- api_key: secret value stored in OKF = False

## Sample Policy

- Mode: static-placeholder
- Live calls enabled: False

## Provenance

- Source: Wayfinder fictional service catalogue
- Source URL: https://wayfinder.pbj.cx/services/vehicle-enquiry-api
