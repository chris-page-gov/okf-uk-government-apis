# Working agreement

- Preserve source adapter, tier, confidence, licence and edge provenance.
- Never execute harvested API credentials or publish secrets.
- Keep semantic/runtime descriptors, adjacency, docs and checksums synchronised.
- Treat `bundle/` as generated publication and validate before commits.
- Treat networked acquisition as a separately authorised operation. Routine CI
  and Pages deployment validate and promote the checked-in bounded preview;
  they do not refresh upstream sources.
- Keep `okf.publication.json`, `README.md`, this working agreement and
  `CHANGELOG.md` in lockstep with controlled source, generator, workflow or
  generated-publication changes.
- Before committing, run the complete non-mutating contract:

```sh
uv sync --locked
uv run --locked python -m unittest discover -s tests -v
uv run --locked python scripts/check_bundle.py
uv run --locked python scripts/build_checksums.py --check
uv run --locked python scripts/check_publication_contract.py
uv run --project ../okf-explorer --locked python ../okf-explorer/scripts/reconcile_okf_repositories.py --repo . --strict
```

- Pull requests receive the complete validation contract. Feature branches do
  not receive a duplicate push run; `main`, version tags and manual runs retain
  full assurance. Pages deploys the exact successful `main` commit without a
  rebuild, then compares its public checksum manifest and identity routes with
  that checkout.

<!-- okf-semantic-contract:start -->
## OKF 0.2 and semantic relationship contract

- Read `okf.semantic.json` before changing Markdown, ontology, semantic, relationship, bundle, or Reader-facing files. It records this repository's authored inputs, generated outputs, exact build/check commands, delivery mode, and current migration limitations.
- Keep the intentionally small OKF 0.2 Markdown core separate from the additive Bundle Wiki YAML-LD profile. Unknown OKF fields remain forward-compatible; profile requirements must never be described as universal OKF core.
- Treat the declared YAML-LD/JSON-LD graph or authored Markdown YAML-LD frontmatter as semantic authority. Explorer JSON, shards, adjacency, registries, checksums and sites are generated projections and must not be hand-edited.
- Every new material directed relationship must retain a stable assertion ID, validated local runtime `source` and `target`, absolute `source_iri` and `target_iri`, an absolute predicate IRI, a governed relationship kind, preferred and inverse labels, assertion status and scope, authority, derivation, observation time, evidence and rights. Semantic reification maps the same identities to RDF subject and object. Confidence never upgrades authority.
- Keep the direct semantic triple and its evidence-bearing `okf:RelationshipAssertion` synchronised, or generate both deterministically from one assertion source. Do not infer domain predicates from Markdown links.
- Validate every generated semantic assertion—not merely a sample—against the pinned local shared Draft 2020-12 schema before writing a conformant receipt. Cross-repository sampling is a regression signal, not a substitute for producer validation.
- Canonicalise authority, evidence/resource and rights source links as credential-free HTTP(S) URLs. Percent-encode query values and reject missing hosts, literal whitespace, quotes, malformed escapes, credentials, unsafe delimiters, non-web schemes and ports outside 1–65535 before generating projections.
- For a large sharded rich graph, publish a digest-bound `relationship_runtime` manifest and SHA-256 route locator. Each route must commit per plane to its exact incident assertion count and sorted assertion-ID digest; keep historical/rejected planes out of `default_planes` and obey the Reader's aggregate chunk, row, compressed-byte and retained-text ceilings.
- Resolve only pinned local contexts during builds. The Reader parses bounded YAML-LD safely but does not fetch or reason over arbitrary remote contexts; it consumes explicit route-bearing nodes and assertion rows.
- Preserve official, normalised, inferred, model-derived, synthetic and historical planes. Never collapse presentation grouping, similarity or route adjacency into semantic identity.
- Run any declared `tooling.setup` commands before the build/check commands when the repository environment is absent. Then run `python3 ../okf-explorer/scripts/reconcile_okf_repositories.py --repo .` after semantic changes when the sibling Explorer checkout is available, followed by every local command in `okf.semantic.json` and this repository's existing validation/release guidance.
<!-- okf-semantic-contract:end -->
