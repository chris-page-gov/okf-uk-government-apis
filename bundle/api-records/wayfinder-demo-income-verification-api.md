---
type: "API Product"
title: "Income Verification API"
description: "Provides verified income data to authorised government departments. Key integration for benefit eligibility."
resource: "https://api.revenue.demo.gov.example/income/v2"
tags: ["api", "cross-government", "government-services", "income", "rest-http", "synthetic-demo", "tax-and-customs", "verification", "wayfinder", "wayfinder-demo-rts"]
generated: { by: process:uk-government-api-okf-builder, at: "2026-07-16T00:00:00Z" }
status: draft
sources: [{ id: "wayfinder_demo", resource: "https://wayfinder.pbj.cx/services/income-verification-api", title: "Wayfinder fictional service catalogue", last_modified: "2026-03-12" }]
confidence: "source-captured"
source_adapter: "wayfinder_demo"
---

# Income Verification API

Provides verified income data to authorised government departments. Key integration for benefit eligibility.

## Metadata

- Type: API Product
- Provider: [Revenue & Taxation Service (Wayfinder demo)](../organisations/wayfinder-demo-rts.md)
- Canonical provider: Wayfinder Demo Rts
- Source adapter: wayfinder_demo
- Source tier: synthetic_demo
- Confidence: source-captured
- Assurance status: synthetic-demo-not-assessed
- Access model: oauth2
- Contract status: placeholder-demo-contract
- Licence: Rights not specified (not-specified)
- Licence basis: source-rights-not-specified
- Licence source: https://wayfinder.pbj.cx/services/income-verification-api
- Licence confidence: 0.0
- Quality band: medium
- DCAT term: `dcat:DataService`
- OpenAPI term: `OpenAPI Object`

- Endpoint: https://api.revenue.demo.gov.example/income/v2
- Documentation: https://docs.demo.gov.example/income-verification

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
- Source URL: https://wayfinder.pbj.cx/services/income-verification-api
