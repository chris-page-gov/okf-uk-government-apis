---
type: "API Product"
title: "Out Of Hours"
description: "Use this message integration to send details of an out of hours (OOH) assessment from an out of hours GP system to the patient's registered GP. It uses MESH to send and receive messages.The message payload is actually not that standard, as explained below."
resource: "https://digital.nhs.uk/developer/api-catalogue/out-of-hours"
tags: ["health-and-care", "mesh", "nhs-digital"]
generated: { by: process:uk-government-api-okf-builder, at: "2026-07-16T00:00:00Z" }
status: draft
sources: [{ id: "api_gov_uk_catalogue", resource: "https://raw.githubusercontent.com/co-cddo/api-catalogue/main/data/catalogue.csv", title: "GOV.UK API Catalogue CSV", last_modified: "2024-04-23" }]
confidence: "declared"
source_adapter: "api_gov_uk_catalogue"
---

# Out Of Hours

Use this message integration to send details of an out of hours (OOH) assessment from an out of hours GP system to the patient's registered GP. It uses MESH to send and receive messages.The message payload is actually not that standard, as explained below.

## Metadata

- Type: API Product
- Provider: [NHS Digital](../organisations/nhs-digital.md)
- Canonical provider: NHS Digital
- Source adapter: api_gov_uk_catalogue
- Source tier: declared_api_catalogue
- Confidence: declared
- Assurance status: declared
- Access model: approval-required
- Contract status: documentation-only
- Licence: Not specified (not-specified)
- Licence basis: not-specified
- Licence source: not-specified
- Licence confidence: 0.2
- Quality band: high
- DCAT term: `dcat:DataService`
- OpenAPI term: `OpenAPI Object`

- Endpoint: https://digital.nhs.uk/developer/api-catalogue/out-of-hours
- Documentation: https://digital.nhs.uk/developer/api-catalogue/out-of-hours

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

- Source: GOV.UK API Catalogue CSV
- Source URL: https://raw.githubusercontent.com/co-cddo/api-catalogue/main/data/catalogue.csv
