---
type: "Contract"
title: "Veterans by economic activity status contract"
description: "Machine-readable or service-description contract inferred for Veterans by economic activity status from public metadata."
resource: "https://api.beta.ons.gov.uk/v1/datasets/RM144"
tags: ["office-for-national-statistics", "population-and-statistics", "rest-http"]
generated: { by: process:uk-government-api-okf-builder, at: "2026-07-16T00:00:00Z" }
status: draft
sources: [{ id: "contract_discovery", resource: "https://api.beta.ons.gov.uk/v1/datasets", title: "Contract discovery from harvested API metadata", last_modified: "2023-05-26" }]
confidence: "observed"
source_adapter: "contract_discovery"
---

# Veterans by economic activity status contract

Machine-readable or service-description contract inferred for Veterans by economic activity status from public metadata.

## Metadata

- Type: Contract
- Provider: [Office for National Statistics](../organisations/office-for-national-statistics.md)
- Canonical provider: Office For National Statistics
- Source adapter: contract_discovery
- Source tier: contract_discovery
- Confidence: observed
- Assurance status: declared
- Access model: anonymous
- Contract status: dataset-api
- Licence: Open Government Licence v3.0 (open-government-licence-v3)
- Licence basis: source-declared
- Licence source: https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/
- Licence confidence: 0.9
- Quality band: medium
- DCAT term: `dcterms:Standard`
- OpenAPI term: `OpenAPI Description or external contract`

- Endpoint: https://api.beta.ons.gov.uk/v1/datasets/RM144
- Documentation: https://api.beta.ons.gov.uk/v1/datasets/RM144

## Standards Alignment

This generated record is standards-alignable, not standards-conformant by itself. DCAT-AP conformance needs an RDF export; OpenAPI conformance needs a complete `openapi` document.

- DCAT / DCAT-AP: `dcterms:Standard`; export status `contract-reference`.
- DCAT missing requirements: none recorded
- OpenAPI: `OpenAPI Description or external contract`; export status `contract-reference`.
- OpenAPI security scheme: `none`.
- OpenAPI missing requirements: none recorded
- Crosswalk: [OKF Standards Crosswalk](../docs/okf-standards-crosswalk.md)

## Credential Requirements

- none: secret value stored in OKF = False

## Provenance

- Source: Contract discovery from harvested API metadata
- Source URL: https://api.beta.ons.gov.uk/v1/datasets
