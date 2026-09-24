# Wayfinder comparison

## Decision

Wayfinder can be documented in this repository, but it must not be presented
as a verified catalogue of live UK government APIs. The public site describes
its departments, services, people, architecture and statistics as fictional
demonstration material. The import therefore uses an opt-in
`synthetic-fixture` scope, `synthetic` authority and record-level
`rights: not specified`.

No explicit reusable licence was found on the public site. That absence does
not prevent this catalogue from recording factual descriptions and source
provenance. It does prevent the publication from implying a source licence or
silently inheriting the repository's licence for the source material.

The concept is attributed to **Paul Buchanan-Jones**. Private correspondence
supplied to the maintainers supports that attribution; its contact details and
message text remain offline and are excluded from the repository.

## Sources and capture

The comparison was observed on 24 September 2026 from:

- [Wayfinder](https://wayfinder.pbj.cx/)
- [About Wayfinder](https://wayfinder.pbj.cx/about)
- [Services](https://wayfinder.pbj.cx/services)
- [Patterns](https://wayfinder.pbj.cx/patterns)
- [Comparison](https://wayfinder.pbj.cx/compare)
- [Documentation](https://wayfinder.pbj.cx/docs)
- [Architecture](https://wayfinder.pbj.cx/architecture)
- [robots.txt](https://wayfinder.pbj.cx/robots.txt)

The public application exposed its records in two content-addressed static
client bundles. The capture preserves all exported arrays and their order:

| Artefact | SHA-256 |
| --- | --- |
| Catalogue bundle `358f0ba2d25ab7b4.js` | `e2cc1df581798b87d65563424011f4f9b2123069b0e0753cb34a9615986a052c` |
| Supporting bundle `6c8c6cf06741410f.js` | `9ef9f05a772f71311063b091be0ff8d88cb3d86151ef256940799e2df149e25f` |
| Normalised catalogue capture | `d15d6c8bfe9490855894aeaa1b1f82a52277737c584a2bc9944a9a906d267969` |

The source manifest records retrieval times, response metadata, content hashes,
the extraction method, the fictional-publication boundary and the rights
finding. Wayfinder's published `robots.txt` disallows crawling, including
named AI agents, so the retained source-centred capture is used for repeatable
offline reconciliation rather than repeated traversal.

## Inventory

The exported inventory contains 311 records.

| Record type | Count |
| --- | ---: |
| Departments | 6 |
| Teams | 23 |
| Services | 85 |
| Patterns | 19 |
| Policies | 5 |
| Declared relationships | 138 |
| Data-sharing agreements | 6 |
| People | 24 |
| Agents | 5 |

The 85 services comprise 57 APIs, 19 platforms, 5 libraries and 4 event
streams. Each imported service retains the complete source object alongside
its department, team, resolved pattern records, missing pattern identifiers,
source page, capture digest and observation time. The untouched 311-record
source capture remains the evidence layer for fields that are not promoted
into the shared API catalogue schema.

## Reconciliation with the UK Government APIs OKF

The offline comparison examined every Wayfinder service against all 41,598
records in the pre-import OKF snapshot. It used stable identifiers, canonical
endpoint URLs and canonical documentation URLs as exact-match keys.

| Result | Count |
| --- | ---: |
| Exact stable-identifier collisions | 0 |
| Exact endpoint URL matches | 0 |
| Exact documentation URL matches | 0 |
| Probable title similarities | 8 |
| Services with no exact match | 85 |
| Admissible real API records | 0 |
| New synthetic service records | 85 |

The eight title similarities cover Government Notify, Government Pay, Vehicle
Enquiry API and five health-related services. They resemble existing GOV.UK,
DVLA or NHS Digital records, but Wayfinder's organisations, URLs and service
claims are fictional. None is merged with a real record. The namespaced
`wayfinder-demo-*` identifiers preserve both records and make that decision
testable.

## Differences and data-quality findings

Wayfinder supplies metadata not consistently present in the current catalogue,
including owning team, semantic version, declared authentication mechanisms,
dependencies, consumers, related patterns, request-volume strings, uptime
strings and service tags. Those values remain source claims rather than
operational assurance:

- all 85 services claim `live`, although the publication is explicitly a demo;
- 17 services have no endpoint and 68 use `demo.gov.example` placeholder
  endpoints;
- all 85 documentation links are placeholders;
- 21 services omit monthly request volume, 66 omit uptime and 9 have no
  authentication value;
- the public agent records name five source repositories, all of which returned
  HTTP 404 when checked on 24 September 2026;
- no supported JSON, RDF, SPARQL or catalogue download endpoint was published.

There are also internal consistency differences:

- the service inventory contains 85 records, while the About page says 75 and
  the comparison page's capability table says 79;
- the pattern inventory contains 19 records, while the About page says 18;
- 137 service-to-pattern references and 14 pattern-to-pattern references point
  to 97 pattern identifiers absent from the export;
- policies contain 9 references to 7 absent services;
- 3 graph relationships refer to absent services (`neptune-graph`,
  `opensearch-index` and `github-actions`);
- 21 `dependsOn` pairs and 22 `consumedBy` pairs are not mirrored by the
  corresponding reciprocal field.

These findings are retained as source-quality observations. The importer does
not repair them or infer missing records.

## OKF mapping and loading policy

The import applies these controls:

- source adapter: `wayfinder_demo`;
- source tier: `synthetic_demo`;
- relationship scope: `synthetic-fixture`;
- authority: `synthetic`;
- rights: `not specified`;
- confidence: `source-captured`;
- default loading: `false` for the synthetic relationship plane;
- exact matches only: probable title similarities are never merged;
- endpoint, documentation, authentication, status, volume and uptime remain
  explicitly source-claimed fields;
- the source snapshot and reconciliation are hash-bound and contain no local
  filesystem paths or private correspondence.

This keeps the 41,598-record real-world catalogue and its default Reader view
separate from the 85-record synthetic comparison layer while making the latter
fully reviewable in the same OKF publication.
