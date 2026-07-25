---
type: "Capability Document"
title: "OS Maps API contract"
description: "Machine-readable or service-description contract inferred for OS Maps API from public metadata."
resource: "https://osdatahub.os.uk/docs/wmts/overview"
tags: ["geospatial", "ordnance-survey", "wms"]
generated: { by: process:uk-government-api-okf-builder, at: "2026-07-16T00:00:00Z" }
status: draft
sources: [{ id: "contract_discovery", resource: "https://raw.githubusercontent.com/co-cddo/api-catalogue/main/data/catalogue.csv", title: "Contract discovery from harvested API metadata", last_modified: "2020-08-24" }]
confidence: "observed"
source_adapter: "contract_discovery"
---

# OS Maps API contract

Machine-readable or service-description contract inferred for OS Maps API from public metadata.

## Metadata

- Type: Capability Document
- Provider: [Ordnance Survey](../organisations/ordnance-survey.md)
- Canonical provider: Ordnance Survey
- Source adapter: contract_discovery
- Source tier: contract_discovery
- Confidence: observed
- Assurance status: observed
- Access model: unknown
- Contract status: documentation-only
- Licence: osdatahub.os.uk (osdatahub-os-uk)
- Licence basis: source-declared
- Licence source: https://osdatahub.os.uk/legal/termsConditions
- Licence confidence: 0.9
- Quality band: medium
- DCAT term: `dcterms:Standard`
- OpenAPI term: `OpenAPI Description or external contract`

- Endpoint: https://osdatahub.os.uk/docs/wmts/overview
- Documentation: https://osdatahub.os.uk/docs/wmts/overview

## Standards Alignment

This generated record is standards-alignable, not standards-conformant by itself. DCAT-AP conformance needs an RDF export; OpenAPI conformance needs a complete `openapi` document.

- DCAT / DCAT-AP: `dcterms:Standard`; export status `contract-reference`.
- DCAT missing requirements: none recorded
- OpenAPI: `OpenAPI Description or external contract`; export status `contract-reference`.
- OpenAPI security scheme: `unknown`.
- OpenAPI missing requirements: none recorded
- Crosswalk: [OKF Standards Crosswalk](../docs/okf-standards-crosswalk.md)

## Credential Requirements

- unknown: secret value stored in OKF = False

## Provenance

- Source: Contract discovery from harvested API metadata
- Source URL: https://raw.githubusercontent.com/co-cddo/api-catalogue/main/data/catalogue.csv
