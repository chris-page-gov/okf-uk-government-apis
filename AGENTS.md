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
python3 -m unittest discover -s tests -v
python3 scripts/check_bundle.py
python3 scripts/build_checksums.py --check
python3 scripts/check_publication_contract.py
```

- Pull requests receive the complete validation contract. Feature branches do
  not receive a duplicate push run; `main`, version tags and manual runs retain
  full assurance. Pages deploys the exact successful `main` commit without a
  rebuild, then compares its public checksum manifest and identity routes with
  that checkout.
