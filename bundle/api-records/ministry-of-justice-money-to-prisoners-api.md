---
type: "API Product"
title: "Money to Prisoners API"
description: "Backend and internal admin site for [Prisoner Money suite of apps](https://github.com/ministryofjustice/money-to-prisoners)."
resource: "https://github.com/ministryofjustice/money-to-prisoners-api"
tags: ["justice-and-policing", "ministry-of-justice", "rest-http"]
generated: { by: process:uk-government-api-okf-builder, at: "2026-07-16T00:00:00Z" }
status: draft
sources: [{ id: "api_gov_uk_catalogue", resource: "https://raw.githubusercontent.com/co-cddo/api-catalogue/main/data/catalogue.csv", title: "GOV.UK API Catalogue CSV", last_modified: "2020-10-28" }]
confidence: "declared"
source_adapter: "api_gov_uk_catalogue"
---

# Money to Prisoners API

Backend and internal admin site for [Prisoner Money suite of apps](https://github.com/ministryofjustice/money-to-prisoners).

## Metadata

- Type: API Product
- Provider: [Ministry of Justice](../organisations/ministry-of-justice.md)
- Canonical provider: Ministry of Justice
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

- Endpoint: https://github.com/ministryofjustice/money-to-prisoners-api
- Documentation: https://github.com/ministryofjustice/money-to-prisoners-api#api-documentation

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
