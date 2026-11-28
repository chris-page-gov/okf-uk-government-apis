# UK Government APIs OKF Bundle Wiki

Independent YAML-LD OKF publication of the multi-source UK Government APIs and
data-access catalogue: 41,683 records, 39,305 evidence resources and 278,156
provenance-bearing relationships.

The bundle separates declared API products, provider-native APIs, data access
endpoints, data products, operations, schemas and contracts. Source tier,
adapter, confidence, credentials policy, licence basis and DCAT/OpenAPI
alignment remain record-level.

The publication is an OKF core 0.3 bundle with the producer-specific
[UK Government APIs profile](profiles/uk-government-apis/v1.md). Its common
repository contract uses the versioned [Bundle Wiki v2 profile](profiles/bundle-wiki/v2/).
`bundle/index.md` declares `okf_version: "0.3"`; each non-reserved Markdown concept has a `type`,
structured `sources`, and `generated.by`/`generated.at`. The publication is
still a preview, so generated concepts are `draft` unless a source explicitly
shows that a record is deprecated. No `verified` claim is emitted without
evidence.

`generated.at` is the frozen bundle build time. Source catalogue dates remain
separate as `sources[].last_modified` and in the producer-specific JSON
extensions.

Machine entry points are under `bundle`: `okf-core-explorer.json` exposes all
3,464 typed Markdown concepts with exact source paths, full body/frontmatter
and source digests. Its core edges come only from authored Markdown links.
The separate `okf-explorer.json`, `okf-bundle.yamlld`,
`okf-bundle.jsonld`, `data/manifest.json`, static search,
and route-scoped relationship adjacency. The YAML-LD and JSON-LD roots are
bounded graph descriptors rather than monolithic corpus files. Their
`data/semantic/manifest.json` identifies digest-bound gzip JSON-LD shards:
route-bearing entity nodes carry the direct triples and matching
`rdf:Statement` / `okf:RelationshipAssertion` nodes carry direction, local
routes, predicate IRIs, inverse labels, authority, derivation, evidence,
freshness and rights. The same assertions generate the complete compatibility
relationship chunks and adjacency, so the semantic and Reader planes cannot
drift silently. `data/relationship-runtime/manifest.json` is the digest-bound
Explorer runtime: it exposes a governed material subset through explicit
planes and a SHA-256 route locator. The complete graph remains available in the
semantic shards and compatibility chunks; the default material planes stay
within the Reader's aggregate row, compressed-byte and retained-text limits.
Historical or rejected synthetic-fixture planes are opt-in. An active plane of
any governed scope would enter the Reader default under the pinned profile.
`data/semantic/validation-report.json` records exhaustive Draft 2020-12
validation of every generated relationship assertion.

The material selection retains documentation, access model, contract signal,
schema, operation, licence, provider portal, supported-alternative and bounded
catalogue-evidence relationships, including their explicit reciprocal edges.
High-volume publisher, adapter, confidence, protocol, endpoint and data-product
facets stay in the complete graph and compatibility chunks rather than the
default whole-runtime load. The selection is deterministic and checked against
the full assertion identities, so omission from the default view is governed
rather than silent.
Derived protocol concepts use collision-checked, suffix-free slug routes such
as `protocol/arcgis-rest`. Their harvested display labels and pre-migration
route spellings remain available as `target_label` and `target_aliases`, and on
the corresponding semantic entity node.

This remains a metadata-only catalogue snapshot. The semantic graph does not
assert that an endpoint is live, accessible or assured, and it never stores or
executes credentials.

The [Notify metadata walkthrough](bundle/notification-catalogue-walkthrough.html)
compares two similarly named GOV.UK API Catalogue entries with the synthetic
Wayfinder negative control. It follows the authored provider link, cites exact
source digests and explains why snapshot licence or endpoint fields must not be
transferred between records. The separate [OKF core walkthrough](bundle/core-walkthrough.html)
uses typed Markdown sources and their authored provider link only; it does not
use the metadata extension graph.

Each guide has its own visible Reader link and replayable journey manifest.
`walkthroughs/notification-reader-journeys.json` exercises the metadata
descriptor; `walkthroughs/core-reader-journeys.json` exercises the separate
typed-source descriptor. CI runs both descriptor manifests against the exact
checked-in bundle and pinned Explorer Reader, including graph traversal and
negative controls. It also opens each authored guide at desktop and mobile
sizes, checks source digests and negative controls, clicks the visible Reader
link and verifies the declared descriptor and source route. The same
guide-to-Reader check runs before a manually triggered Pages deployment.

## Wayfinder comparison layer

The catalogue includes 85 service records from the explicitly fictional
[Wayfinder](https://wayfinder.pbj.cx/) demonstrator. None had an exact stable
identifier, endpoint or documentation match in the 41,598-record pre-import
snapshot, so all use collision-safe `wayfinder-demo-*` identities. Probable
title similarities are retained as non-matches and are never fuzzy-merged.

Wayfinder's complete 311-record public export, source response metadata,
content hashes and offline reconciliation are retained under
`sources/wayfinder/2026-09-24/` and copied into the generated bundle. Every
imported service keeps its complete source object. Its relationships use
`synthetic-fixture` scope, synthetic authority and lifecycle `rejected`, meaning
rejected from real-world catalogue admission rather than disproved. They do not
enter the active material runtime.

No explicit reusable source licence was found. Documentation is therefore
published with record-level `rights: not specified`; it does not imply that the
source material inherits the repository licence. The concept is attributed to
Paul Buchanan-Jones. Private correspondence supporting that attribution stays
offline and is excluded from the repository.

See [the detailed comparison](docs/wayfinder-comparison-2026-09-24.md) for the
field mapping, discrepancies and provenance boundary.

Regenerate the core 0.3 and metadata projections from the checked-in frozen
16 July 2026 publication, then update its integrity manifest:

CI checks the downloaded uv archive digest and exact runtime version, retaining
both values in its log if the pinned bootstrap is rejected.
The version check uses the Linux archive's exact output format, which differs
from the macOS build; the full archive SHA-256 remains the integrity pin.
Reader commands resolve the producer's bundle and journey paths before
`pnpm --dir` selects the separate consumer checkout.

```sh
uv python install 3.12.11
uv sync --locked --python 3.12.11
uv run --locked python scripts/upgrade_publication.py
uv run --locked python scripts/build_checksums.py
```

`upgrade_publication.py` is the supported offline build route: it reads the
checked-in record/resource/publisher chunks and performs no network
acquisition. A source refresh through
`build_uk_government_api_okf.py` contacts upstream catalogues unless all
source-adapter fixtures or skip flags are supplied; do not use it for an
offline semantic-only migration.

Validate without changing the publication with:

```sh
uv run --locked python -m unittest discover -s tests -v
uv run --locked python scripts/check_bundle.py
uv run --locked python scripts/build_checksums.py --check
uv run --locked python scripts/check_publication_contract.py
uv run --locked python scripts/check_frozen_graph_identity.py
uv run --project ../okf-explorer --locked python ../okf-explorer/scripts/reconcile_okf_repositories.py --repo . --strict
uv run --project ../okf-explorer --locked python scripts/check_core_reader_parity.py --consumer-root ../okf-explorer
```

## Publication contract and CI

[`okf.publication.json`](okf.publication.json) records the repository's API
source family, authored and generated boundaries, dependency planes, reviewed
commands, documentation lockstep, CI policy, publication authority and
verification route. The generated
[`bundle/okf-bundle.yamlld`](bundle/okf-bundle.yamlld) remains the semantic
descriptor; lifecycle governance does not alter its bytes.

`scripts/check_publication_contract.py` checks local identifiers and command
references, safe reviewed command declarations and the no-rebuild publication
policy. In pull requests and pushes it also requires controlled changes to
include `CHANGELOG.md` and updated human guidance in either `README.md` or
`AGENTS.md`. Automated dependency changes receive the same assessment; there
is no blanket exemption.

CI runs once for a pull request and again for the integrated `main` commit or a
version tag. Superseded runs are cancelled per pull request or ref. Pages is
triggered only by a successful complete `main` validation, checks out that
exact commit and uploads its existing `bundle/` directory without rebuilding
or reacquiring it. A manual deployment runs the complete non-mutating
validation first. Networked source acquisition remains a separate,
explicitly authorised refresh operation.

Pages uses a unique artifact name for each workflow run and attempt. If the
deployment action fails, it waits ten seconds and retries once against that
same uploaded artifact. A failed retry fails the job. The final deployed-byte
identity check remains required. This bounds recovery from the observed
artifact-service discovery failure and avoids duplicate-name collisions on
workflow reruns.

For a change limited to the landing page and the two walkthroughs, run
`uv run --locked python scripts/upgrade_publication.py --presentation-only`,
then regenerate checksums. This path preserves the frozen source, graph and
descriptor bytes. The pages declare `en-GB` and an explicit icon so a public
browser does not request the GitHub owner's missing favicon.

After deployment, `scripts/verify_deployment.py` fetches the public
`checksums.json`, landing page, both Explorer descriptors, both journey
manifests and record-count manifest and compares them byte for byte with the
validated checkout. The pre-deployment browser gate also fetches every local
checksum-listed asset over HTTP and compares its exact byte count and SHA-256.
It clicks each source-linked guide's visible Reader link, verifies the exact
descriptor identity and route, checks accessibility and guide reflow, and records
desktop and mobile screenshots. CI separately replays both descriptor-specific journey
manifests against the pinned Reader and checks browser errors.

## OKF standards and bundle discovery

The [central standards register](https://github.com/chris-page-gov/okf-explorer/blob/main/docs/okf-standards.md) records current and historical OKF specifications, version-specific pins and the public bundle catalogue. Use the [machine-readable register](https://raw.githubusercontent.com/chris-page-gov/okf-explorer/main/registry/okf-standards.json) to resolve the version implemented by this repository.
