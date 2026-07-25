---
type: "API Product"
title: "Contractmap"
description: "Contractmap is an AI-enabled system that maps contract descriptions to Categories within the Government Commercial Agency (GCA) commercial taxonomy. Given a contract description, it returns the name of a Category if a close match is found, or a null response if no close match is found."
resource: "https://github.com/Crown-Commercial-Service/ccs-contract-map"
tags: ["business-and-economy", "government-commercial-agency", "rest-http"]
generated: { by: process:uk-government-api-okf-builder, at: "2026-07-16T00:00:00Z" }
status: draft
sources: [{ id: "api_gov_uk_catalogue", resource: "https://raw.githubusercontent.com/co-cddo/api-catalogue/main/data/catalogue.csv", title: "GOV.UK API Catalogue CSV", last_modified: "2026-06-24" }]
confidence: "declared"
source_adapter: "api_gov_uk_catalogue"
---

# Contractmap

Contractmap is an AI-enabled system that maps contract descriptions to Categories within the Government Commercial Agency (GCA) commercial taxonomy. Given a contract description, it returns the name of a Category if a close match is found, or a null response if no close match is found.

## Metadata

- Type: API Product
- Provider: [Government Commercial Agency](../organisations/government-commercial-agency.md)
- Canonical provider: Government Commercial Agency
- Source adapter: api_gov_uk_catalogue
- Source tier: declared_api_catalogue
- Confidence: declared
- Assurance status: declared
- Access model: unknown
- Contract status: documentation-only
- Licence: Not specified (not-specified)
- Licence basis: not-specified
- Licence source: not-specified
- Licence confidence: 0.2
- Quality band: medium
- DCAT term: `dcat:DataService`
- OpenAPI term: `OpenAPI Object`

- Endpoint: https://github.com/Crown-Commercial-Service/ccs-contract-map
- Documentation: https://github.com/Crown-Commercial-Service/ccs-contract-map

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
