# UK Government APIs OKF Bundle Wiki

Independent YAML-LD OKF publication of the multi-source UK Government APIs and
data-access catalogue: 41,598 records, 39,305 evidence resources and 277,449
provenance-bearing relationships.

The bundle separates declared API products, provider-native APIs, data access
endpoints, data products, operations, schemas and contracts. Source tier,
adapter, confidence, credentials policy, licence basis and DCAT/OpenAPI
alignment remain record-level.

The publication is an OKF v0.2 bundle. `bundle/index.md` declares
`okf_version: "0.2"`; each non-reserved Markdown concept has a `type`,
structured `sources`, and `generated.by`/`generated.at`. The publication is
still a preview, so generated concepts are `draft` unless a source explicitly
shows that a record is deprecated. No `verified` claim is emitted without
evidence.

`generated.at` is the frozen bundle build time. Source catalogue dates remain
separate as `sources[].last_modified` and in the producer-specific JSON
extensions.

Machine entry points are under `bundle/`: `okf-bundle.yamlld`,
`okf-bundle.jsonld`, `okf-explorer.json`, `data/manifest.json`, static search,
and route-scoped relationship adjacency.

Refresh the v0.2 publication projection and its integrity manifest with:

```sh
python3 scripts/upgrade_publication.py
python3 scripts/build_checksums.py
```

Validate without changing the publication with:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/check_bundle.py
python3 scripts/build_checksums.py --check
python3 scripts/check_publication_contract.py
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

After deployment, `scripts/verify_deployment.py` fetches the public
`checksums.json`, landing page, Explorer descriptor and record-count manifest
and compares them byte for byte with the validated checkout. This is a bounded
HTTP identity gate, not a real-browser interaction or console test.
