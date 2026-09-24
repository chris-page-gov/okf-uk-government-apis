---
type: "API Product"
title: "Automated Accessibility Checker"
description: "API for automated WCAG 2.1 AA compliance checking. Integrates with CI/CD pipelines."
resource: "https://a11y-check.demo.gov.example/api/v1"
tags: ["accessibility", "api", "automation", "public-administration", "rest-http", "synthetic-demo", "testing", "wayfinder", "wayfinder-demo-dso", "wcag"]
generated: { by: process:uk-government-api-okf-builder, at: "2026-07-16T00:00:00Z" }
status: draft
sources: [{ id: "wayfinder_demo", resource: "https://wayfinder.pbj.cx/services/accessibility-checker", title: "Wayfinder fictional service catalogue", last_modified: "2026-01-30" }]
confidence: "source-captured"
source_adapter: "wayfinder_demo"
---

# Automated Accessibility Checker

API for automated WCAG 2.1 AA compliance checking. Integrates with CI/CD pipelines.

## Metadata

- Type: API Product
- Provider: [Digital Standards Office (Wayfinder demo)](../organisations/wayfinder-demo-dso.md)
- Canonical provider: Wayfinder Demo Dso
- Source adapter: wayfinder_demo
- Source tier: synthetic_demo
- Confidence: source-captured
- Assurance status: synthetic-demo-not-assessed
- Access model: api-key
- Contract status: placeholder-demo-contract
- Licence: Rights not specified (not-specified)
- Licence basis: source-rights-not-specified
- Licence source: https://wayfinder.pbj.cx/services/accessibility-checker
- Licence confidence: 0.0
- Quality band: medium
- DCAT term: `dcat:DataService`
- OpenAPI term: `OpenAPI Object`

- Endpoint: https://a11y-check.demo.gov.example/api/v1
- Documentation: https://docs.demo.gov.example/accessibility-checker

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
- Source URL: https://wayfinder.pbj.cx/services/accessibility-checker
