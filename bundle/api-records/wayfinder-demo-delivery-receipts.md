---
type: "API Product"
title: "Delivery Receipts API"
description: "Webhook and polling API for tracking notification delivery status and failures."
resource: "https://api.notify.demo.gov.example/receipts/v1"
tags: ["api", "notifications", "public-administration", "rest-http", "status", "synthetic-demo", "wayfinder", "wayfinder-demo-dso", "webhooks"]
generated: { by: process:uk-government-api-okf-builder, at: "2026-07-16T00:00:00Z" }
status: draft
sources: [{ id: "wayfinder_demo", resource: "https://wayfinder.pbj.cx/services/delivery-receipts", title: "Wayfinder fictional service catalogue", last_modified: "2026-01-22" }]
confidence: "source-captured"
source_adapter: "wayfinder_demo"
---

# Delivery Receipts API

Webhook and polling API for tracking notification delivery status and failures.

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
- Licence source: https://wayfinder.pbj.cx/services/delivery-receipts
- Licence confidence: 0.0
- Quality band: medium
- DCAT term: `dcat:DataService`
- OpenAPI term: `OpenAPI Object`

- Endpoint: https://api.notify.demo.gov.example/receipts/v1
- Documentation: https://docs.demo.gov.example/notify/receipts

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
- Source URL: https://wayfinder.pbj.cx/services/delivery-receipts
