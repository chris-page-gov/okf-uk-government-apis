---
type: "API Product"
title: "GIAS read-only API prototype"
description: "DfE prototype for read-only access to GIAS Establishments and Establishment Groups, designed to return selected fields as streamed JSON or CSV. DfE is validating the prototype and exploring authentication, rate limiting and versioning; no published, supported public endpoint is currently documented."
resource: ""
timestamp: "2026-03-05"
tags: "beta, csv, department-for-education, education, education-establishments, gias, json, prototype, read-only, rest-http, schools, urn"
confidence: "declared"
source_adapter: "dfe_gias"
---

# GIAS read-only API prototype

DfE prototype for read-only access to GIAS Establishments and Establishment Groups, designed to return selected fields as streamed JSON or CSV. DfE is validating the prototype and exploring authentication, rate limiting and versioning; no published, supported public endpoint is currently documented.

## Metadata

- Type: API Product
- Provider: [Department for Education](../organisations/department-for-education.md)
- Canonical provider: Department for Education
- Source adapter: dfe_gias
- Source tier: provider_native_api
- Confidence: declared
- Assurance status: declared
- Access model: unknown
- Contract status: design-history-only
- Licence: Open Government Licence v3.0 (open-government-licence-v3)
- Licence basis: provider-declared
- Licence source: https://design-histories.education.gov.uk/get-information-about-schools/designing-the-read-api-for-get-information-about-schools-gias
- Licence confidence: 0.9
- Quality band: medium
- DCAT term: `dcat:DataService`
- OpenAPI term: `OpenAPI Object`

- Documentation: https://design-histories.education.gov.uk/get-information-about-schools/designing-the-read-api-for-get-information-about-schools-gias

## Standards Alignment

This generated record is standards-alignable, not standards-conformant by itself. DCAT-AP conformance needs an RDF export; OpenAPI conformance needs a complete `openapi` document.

- DCAT / DCAT-AP: `dcat:DataService`; export status `data-service-with-gaps`.
- DCAT missing requirements: `dcat:endpointURL`
- OpenAPI: `OpenAPI Object`; export status `service-stub-with-gaps`.
- OpenAPI security scheme: `unknown`.
- OpenAPI missing requirements: `components.securitySchemes`, `servers[].url`
- Crosswalk: [OKF Standards Crosswalk](../../docs/okf-standards-crosswalk.md)

## Credential Requirements

- unknown: secret value stored in OKF = False

## Sample Policy

- Mode: static-placeholder
- Live calls enabled: False

## Provenance

- Source: Department for Education GIAS Read API design history
- Source URL: https://design-histories.education.gov.uk/get-information-about-schools/designing-the-read-api-for-get-information-about-schools-gias
