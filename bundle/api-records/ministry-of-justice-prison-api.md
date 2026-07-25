---
type: "API Product"
title: "Prison API"
description: "The service provides REST access to the Nomis Oracle DB prisoner information."
resource: "https://api.prison.service.justice.gov.uk/swagger-ui.html"
tags: ["government-services", "justice-and-policing", "ministry-of-justice", "rest-http"]
generated: { by: process:uk-government-api-okf-builder, at: "2026-07-16T00:00:00Z" }
status: draft
sources: [{ id: "api_gov_uk_catalogue", resource: "https://raw.githubusercontent.com/co-cddo/api-catalogue/main/data/catalogue.csv", title: "GOV.UK API Catalogue CSV", last_modified: "2023-02-20" }]
confidence: "declared"
source_adapter: "api_gov_uk_catalogue"
---

# Prison API

The service provides REST access to the Nomis Oracle DB prisoner information.

## Metadata

- Type: API Product
- Provider: [Ministry of Justice](../organisations/ministry-of-justice.md)
- Canonical provider: Ministry of Justice
- Source adapter: api_gov_uk_catalogue
- Source tier: declared_api_catalogue
- Confidence: declared
- Assurance status: declared
- Access model: unknown
- Contract status: openapi-indicated
- Licence: Not specified (not-specified)
- Licence basis: not-specified
- Licence source: not-specified
- Licence confidence: 0.2
- Quality band: high
- DCAT term: `dcat:DataService`
- OpenAPI term: `OpenAPI Object`

- Endpoint: https://api.prison.service.justice.gov.uk/swagger-ui.html
- Documentation: https://github.com/ministryofjustice/prison-api

## Standards Alignment

This generated record is standards-alignable, not standards-conformant by itself. DCAT-AP conformance needs an RDF export; OpenAPI conformance needs a complete `openapi` document.

- DCAT / DCAT-AP: `dcat:DataService`; export status `data-service-with-gaps`.
- DCAT missing requirements: `dcterms:license`
- OpenAPI: `OpenAPI Object`; export status `service-stub-with-gaps`.
- OpenAPI security scheme: `unknown`.
- OpenAPI missing requirements: `components.securitySchemes`, `info.license`
- Crosswalk: [OKF Standards Crosswalk](../docs/okf-standards-crosswalk.md)

## Credential Requirements

- unknown: secret value stored in OKF = False

## Sample Policy

- Mode: static-placeholder
- Live calls enabled: False

## Provenance

- Source: GOV.UK API Catalogue CSV
- Source URL: https://raw.githubusercontent.com/co-cddo/api-catalogue/main/data/catalogue.csv
