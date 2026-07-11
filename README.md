# UK Government APIs OKF Bundle Wiki

Independent YAML-LD OKF publication of the multi-source UK Government APIs and
data-access catalogue: 41,520 records, 39,250 evidence resources and 276,996
provenance-bearing relationships.

The bundle separates declared API products, provider-native APIs, data access
endpoints, data products, operations, schemas and contracts. Source tier,
adapter, confidence, credentials policy, licence basis and DCAT/OpenAPI
alignment remain record-level.

Machine entry points are under `bundle/`: `okf-bundle.yamlld`,
`okf-bundle.jsonld`, `okf-explorer.json`, `data/manifest.json`, static search,
and route-scoped relationship adjacency. Validate with:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/check_bundle.py
python3 scripts/build_checksums.py --check
```
