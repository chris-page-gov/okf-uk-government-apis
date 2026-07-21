#!/usr/bin/env python3
"""Upgrade the checked API corpus to the federated semantic publication contract."""

from __future__ import annotations

import gzip
import html
import json
from pathlib import Path
import shutil

import build_uk_government_api_okf as helpers

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "bundle"


def load(path: Path):
    data = path.read_bytes()
    if path.suffix == ".gz":
        data = gzip.decompress(data)
    return json.loads(data)


def main() -> int:
    descriptor_path = BUNDLE / "okf-explorer.json"
    manifest_path = BUNDLE / "data/manifest.json"
    descriptor = load(descriptor_path)
    manifest = load(manifest_path)
    relationships = [row for relative in manifest["chunks"]["relationships"] for row in load(BUNDLE / relative)]
    adjacency, buckets = helpers.build_relationship_adjacency(relationships)
    adjacency["buckets"] = {key: value.replace(".json", ".json.gz") for key, value in adjacency["buckets"].items()}
    adjacency_root = BUNDLE / "data/adjacency"
    adjacency_root.mkdir(parents=True, exist_ok=True)
    (adjacency_root / "manifest.json").write_text(helpers.render_json(adjacency), encoding="utf-8")
    for path, routes in buckets:
        target = (BUNDLE / path).with_suffix(".json.gz")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(gzip.compress(helpers.render_json(routes).encode(), compresslevel=6, mtime=0))
    for target in adjacency_root.glob("*.json"):
        if target.name != "manifest.json":
            target.unlink()
    descriptor.update({
        "@context": "https://chris-page-gov.github.io/okf-explorer/profile/bundle-wiki/v1/context.jsonld",
        "@id": "https://chris-page-gov.github.io/okf-uk-government-apis/okf-explorer.json",
        "version": "0.4.0",
        "status": "preview",
        "profile": "https://chris-page-gov.github.io/okf-explorer/profile/bundle-wiki/v1/",
        "publisher": "https://github.com/chris-page-gov",
        "license": "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
        "semantic_descriptor": "https://chris-page-gov.github.io/okf-uk-government-apis/okf-bundle.yamlld",
    })
    descriptor["entrypoints"].update({"viewer": "https://chris-page-gov.github.io/okf-explorer/", "relationship_adjacency": "data/adjacency/manifest.json", "notes": "docs/UK-Government-API-OKF.md", "standards_crosswalk": "docs/okf-standards-crosswalk.md"})
    manifest["indexes"]["relationship_adjacency"] = "data/adjacency/manifest.json"
    manifest["performance"]["route_relationship_hydration"] = "hash-sharded adjacency"
    descriptor_path.write_text(helpers.render_json(descriptor), encoding="utf-8")
    manifest_path.write_text(helpers.render_json(manifest), encoding="utf-8")
    semantic = {"@context": descriptor["@context"], "@id": "https://chris-page-gov.github.io/okf-uk-government-apis/", "@type": "okf:Bundle", "title": descriptor["title"], "description": descriptor["description"], "version": descriptor["version"], "status": descriptor["status"], "profile": {"@id": descriptor["profile"]}, "descriptor": {"@id": descriptor["@id"]}, "publisher": {"@id": descriptor["publisher"]}, "license": {"@id": descriptor["license"]}, "generatedAt": descriptor["generated_at"]}
    (BUNDLE / "okf-bundle.yamlld").write_text(json.dumps(semantic, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (BUNDLE / "okf-bundle.jsonld").write_text(helpers.render_json(semantic), encoding="utf-8")
    docs_root = BUNDLE / "docs"
    docs_root.mkdir(parents=True, exist_ok=True)
    for source in (ROOT / "docs").glob("*.md"):
        shutil.copy2(source, docs_root / source.name)
    counts = manifest["counts"]
    explorer_url = (
        "https://chris-page-gov.github.io/okf-explorer/?bundle="
        "https%3A%2F%2Fchris-page-gov.github.io%2Fokf-uk-government-apis%2Fokf-explorer.json"
    )
    index_html = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
        '<title>UK Government APIs OKF</title><style>body{font:18px/1.55 system-ui;max-width:900px;margin:4rem auto;'
        'padding:0 1.5rem}a{color:#1d70b8}</style></head><body><h1>UK Government APIs OKF Bundle Wiki</h1>'
        f'<p>{counts["datasets"]:,} API/data records and {counts["relationships"]:,} provenance-bearing relationships.</p>'
        f'<p><a href="{html.escape(explorer_url, quote=True)}">Open in OKF Explorer</a></p><ul>'
        '<li><a href="okf-bundle.yamlld">YAML-LD</a></li><li><a href="okf-bundle.jsonld">JSON-LD</a></li>'
        '<li><a href="okf-explorer.json">Explorer descriptor</a></li><li><a href="data/manifest.json">Data manifest</a></li>'
        '<li><a href="data/adjacency/manifest.json">Relationship adjacency</a></li><li><a href="checksums.json">Checksums</a></li>'
        '</ul></body></html>\n'
    )
    (BUNDLE / "index.html").write_text(index_html, encoding="utf-8")
    print(f"upgraded {len(relationships):,} relationships across {len(buckets)} adjacency buckets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
