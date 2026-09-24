#!/usr/bin/env python3
"""Upgrade the checked API corpus to the federated semantic publication contract."""

from __future__ import annotations

import argparse
import gzip
import html
import json
from collections import Counter, defaultdict
from pathlib import Path

import build_uk_government_api_okf as helpers
import wayfinder_import

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "bundle"
WAYFINDER_SOURCE = ROOT / "sources" / "wayfinder" / "2026-09-24"
WAYFINDER_BUNDLE = BUNDLE / "data" / "sources" / "wayfinder"


def load(path: Path):
    data = path.read_bytes()
    if path.suffix == ".gz":
        data = gzip.decompress(data)
    return json.loads(data)


def documentation_concept(source: Path, generated_at: str) -> str:
    relative = source.relative_to(ROOT).as_posix()
    repository_url = f"https://github.com/chris-page-gov/okf-uk-government-apis/blob/main/{relative}"
    title = source.stem.replace("-", " ").replace("_", " ")
    frontmatter = "\n".join(
        [
            "---",
            'type: "Reference"',
            f"title: {helpers.yaml_scalar(title)}",
            f"generated: {{ by: process:uk-government-api-okf-builder, at: {helpers.yaml_scalar(generated_at)} }}",
            "status: draft",
            "sources: [{ "
            f"id: {helpers.yaml_scalar('repository-source')}, "
            f"resource: {helpers.yaml_scalar(repository_url)}, "
            f"title: {helpers.yaml_scalar(source.name)}"
            " }]",
            "---",
            "",
        ]
    )
    return frontmatter + source.read_text(encoding="utf-8").lstrip("\n")


def is_wayfinder_relationship(row: dict) -> bool:
    return bool(
        row.get("source_adapter") == wayfinder_import.SOURCE_ADAPTER
        or str(row.get("source") or "").startswith("dataset/wayfinder-demo-")
        or str(row.get("target") or "").startswith("dataset/wayfinder-demo-")
        or str(row.get("target") or "").startswith("wayfinder-")
        or str(row.get("target") or "").startswith("publisher/wayfinder-demo-")
    )


def rebuild_publishers(
    records: list[dict], resources: list[dict], existing: list[dict]
) -> list[dict]:
    counts = Counter(str(record["publisher"]) for record in records)
    resource_counts: Counter[str] = Counter()
    for record in records:
        resource_counts[str(record["publisher"])] += int(
            record.get("resource_count") or 0
        )
    base = {
        str(publisher["name"]): publisher
        for publisher in existing
        if not str(publisher.get("name") or "").startswith("wayfinder-demo-")
    }
    synthetic = {
        str(publisher["name"]): publisher
        for publisher in wayfinder_import.publisher_records(
            catalogue_path=WAYFINDER_SOURCE / "catalogue.json",
            manifest_path=WAYFINDER_SOURCE / "manifest.json",
            record_counts=dict(counts),
        )
    }
    publishers: list[dict] = []
    for name in sorted(counts):
        if name in synthetic:
            publisher = synthetic[name]
        elif name in base:
            publisher = dict(base[name])
            publisher["dataset_count"] = counts[name]
            publisher["resource_count"] = resource_counts[name]
        else:
            raise ValueError(f"record publisher has no published entity: {name}")
        publishers.append(publisher)
    return publishers


def add_wayfinder_to_frozen_corpus(
    descriptor: dict, manifest: dict
) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    records = [
        row
        for relative in manifest["chunks"]["datasets"]
        for row in load(BUNDLE / relative)
        if row.get("source_adapter") != wayfinder_import.SOURCE_ADAPTER
    ]
    resources = [
        row
        for relative in manifest["chunks"]["resources"]
        for row in load(BUNDLE / relative)
        if row.get("provenance", {}).get("source_adapter")
        != wayfinder_import.SOURCE_ADAPTER
    ]
    existing_publishers = [
        row
        for relative in manifest["chunks"]["publishers"]
        for row in load(BUNDLE / relative)
    ]
    relationships = [
        row
        for relative in manifest["chunks"]["relationships"]
        for row in load(BUNDLE / relative)
        if not is_wayfinder_relationship(row)
    ]

    source_manifest = load(WAYFINDER_SOURCE / "manifest.json")
    builder = helpers.CorpusBuilder(
        "https://wayfinder.pbj.cx/",
        str(source_manifest["capture"]["sha256"]),
        str(source_manifest["capturedAt"]),
    )
    builder.records = records
    builder.resources = resources
    builder.relationships = relationships
    builder.seen_records = {str(record["name"]) for record in records}
    builder.seen_endpoint_urls = {
        (str(record.get("record_type") or ""), str(record.get("url") or ""))
        for record in records
        if record.get("url")
    }
    imported = wayfinder_import.add_wayfinder_services(
        builder,
        catalogue_path=WAYFINDER_SOURCE / "catalogue.json",
        manifest_path=WAYFINDER_SOURCE / "manifest.json",
    )
    if len(imported) != 85:
        raise ValueError("Wayfinder import did not produce exactly 85 services")
    builder.attach_resource_ids()
    publishers = rebuild_publishers(
        builder.records, builder.resources, existing_publishers
    )
    compiled = helpers.compile_relationship_assertions(
        builder.relationships, builder.records, builder.resources, publishers
    )
    helpers.annotate_relationship_density(builder.records, compiled)
    return builder.records, builder.resources, publishers, compiled


def refreshed_standards_alignment(
    current: dict, records: list[dict]
) -> dict:
    result = dict(current)
    dcat_gaps: Counter[str] = Counter()
    openapi_gaps: Counter[str] = Counter()
    for record in records:
        alignment = record.get("standards_alignment", {})
        dcat_gaps.update(alignment.get("dcat", {}).get("required_missing", []))
        openapi_gaps.update(
            alignment.get("openapi", {}).get("required_missing", [])
        )
    result.update(
        {
            "dcat_type_counts": [
                {"term": value, "count": count}
                for value, count in Counter(
                    record.get("dcat_type", "not-specified") for record in records
                ).most_common()
            ],
            "openapi_type_counts": [
                {"term": value, "count": count}
                for value, count in Counter(
                    record.get("openapi_type", "not-specified")
                    for record in records
                ).most_common()
            ],
            "dcat_export_status_counts": [
                {"status": value, "count": count}
                for value, count in Counter(
                    record.get("dcat_export_status", "not-specified")
                    for record in records
                ).most_common()
            ],
            "openapi_export_status_counts": [
                {"status": value, "count": count}
                for value, count in Counter(
                    record.get("openapi_export_status", "not-specified")
                    for record in records
                ).most_common()
            ],
            "openapi_security_scheme_counts": [
                {"scheme": value, "count": count}
                for value, count in Counter(
                    record.get("openapi_security_scheme", "not-specified")
                    for record in records
                ).most_common()
            ],
            "dcat_common_missing": [
                {"property": value, "count": count}
                for value, count in dcat_gaps.most_common()
            ],
            "openapi_common_missing": [
                {"field": value, "count": count}
                for value, count in openapi_gaps.most_common()
            ],
        }
    )
    return result


def rebuild_static_views(
    descriptor: dict,
    manifest: dict,
    records: list[dict],
    resources: list[dict],
    publishers: list[dict],
    relationships: list[dict],
) -> dict:
    for record in records:
        record["update_year"] = (
            str(record.get("metadata_modified") or record.get("timestamp") or "")[:4]
            or "not-specified"
        )

    old_facets = load(BUNDLE / manifest["indexes"]["facets"])
    facets = {
        key: helpers.facet_counts(records, key)
        for key in old_facets
        if key not in {"resource_type", "format", "host"}
    }
    facets["resource_type"] = [
        {"value": value, "count": count}
        for value, count in Counter(
            resource["resource_type"] for resource in resources
        ).most_common()
    ]
    facets["format"] = helpers.facet_counts(records, "formats")
    facets["host"] = helpers.facet_counts(records, "endpoint_host")

    canonical = helpers.canonical_counts(records)
    counts = {
        "datasets": len(records),
        "resources": len(resources),
        "publishers": len(publishers),
        "relationships": len(relationships),
        "api_resources": len(resources),
        "providers": len(publishers),
        "synthetic_demo_services": sum(
            1 for record in records if record.get("synthetic_demo")
        ),
        **canonical,
    }
    analysis = load(BUNDLE / manifest["indexes"]["analysis"])
    warnings = dict(analysis.get("warnings", {}))
    warnings.update(
        {
            "missing_contract": sum(
                1
                for record in records
                if record.get("record_type")
                in {"API Product", "Data Access API Endpoint"}
                and record.get("contract_status") == "undocumented-in-catalogue"
            ),
            "unknown_access": sum(
                1 for record in records if record.get("access_model") == "unknown"
            ),
            "api_key_only": sum(
                1 for record in records if record.get("access_model") == "api-key"
            ),
            "missing_licence": sum(
                1 for record in records if record.get("license_id") == "not-specified"
            ),
            "licence_inferred_from_provider_terms": sum(
                1
                for record in records
                if record.get("license_basis") == "provider-terms-inferred"
            ),
            "synthetic_demo_records": counts["synthetic_demo_services"],
        }
    )
    top_publishers = [
        {
            "id": publisher["name"],
            "label": publisher["title"],
            "dataset_count": publisher["dataset_count"],
            "resource_count": publisher["resource_count"],
        }
        for publisher in sorted(
            publishers,
            key=lambda item: (-int(item["dataset_count"]), item["title"]),
        )[:16]
    ]
    standards = refreshed_standards_alignment(
        analysis.get("standards_alignment", {}), records
    )
    standards["crosswalk"] = "docs/okf-standards-crosswalk.md"
    recent = sorted(records, key=lambda item: item.get("timestamp", ""), reverse=True)[
        :16
    ]
    graph_nodes = [
        {
            "id": "corpus/overview",
            "label": "UK Government APIs",
            "type": "corpus",
            "count": len(records),
        }
    ]
    for key in ["record_type", "source_adapter", "protocol", "topic", "confidence"]:
        for row in facets.get(key, [])[:6]:
            graph_nodes.append(
                {
                    "id": f"facet/{key}/{row['value']}",
                    "label": row["value"],
                    "type": key,
                    "count": row["count"],
                }
            )
    graph_edges = [
        {
            "source": "corpus/overview",
            "target": node["id"],
            "label": "summarised by",
            "count": node.get("count"),
        }
        for node in graph_nodes[1:]
    ]
    notice = (
        "Wayfinder contributes 85 explicitly fictional service records as a "
        "rejected-from-real-world-admission synthetic comparison layer. Its "
        "record-level rights remain not specified."
    )
    notices = list(analysis.get("summary", {}).get("notices", []))
    if notice not in notices:
        notices.append(notice)

    overview = load(BUNDLE / manifest["indexes"]["overview"])
    overview.update(
        {
            "counts": counts,
            "warnings": warnings,
            "top_publishers": top_publishers,
            "recent_datasets": helpers.search_docs(recent),
            "format_counts": facets["protocol"],
            "facet_previews": {key: value[:18] for key, value in facets.items()},
            "notices": notices,
            "standards_alignment": standards,
        }
    )

    family_groups: dict[str, Counter[str]] = defaultdict(Counter)
    for record in records:
        family_groups[str(record["organisation_family"])][str(record["publisher"])] += 1
    hierarchy = {
        "id": "hierarchy/provider-family",
        "label": "Organisation family to provider",
        "facet": "publisher",
        "levels": ["organisation family", "provider"],
        "values": [
            {
                "id": f"facet/organisation_family/{family}",
                "label": family,
                "count": sum(provider_counts.values()),
                "route": f"facet/organisation_family/{family}",
                "children": [
                    {
                        "id": f"facet/publisher/{provider}",
                        "label": helpers.provider_title(provider),
                        "count": count,
                        "route": f"facet/publisher/{provider}",
                    }
                    for provider, count in provider_counts.most_common(8)
                ],
            }
            for family, provider_counts in sorted(family_groups.items())
        ],
    }
    relationship_counts = Counter(row["kind"] for row in relationships)
    analysis["summary"].update(
        {
            "record_count": len(records),
            "resource_count": len(resources),
            "relationship_count": len(relationships),
            "notices": notices,
        }
    )
    analysis["canonical_counts"] = counts
    analysis["warnings"] = warnings
    analysis["standards_alignment"] = standards
    analysis["graph_overview"] = {"nodes": graph_nodes, "edges": graph_edges}
    analysis["timeline_overview"] = {
        "buckets": [
            {
                "id": f"year:{year}",
                "label": year,
                "count": count,
                "route": f"facet/update_year/{year}",
                "samples": helpers.search_docs(
                    [record for record in records if record["update_year"] == year]
                )[:2],
            }
            for year, count in Counter(
                record["update_year"]
                for record in records
                if record["update_year"] != "not-specified"
            ).most_common()
        ]
    }
    analysis["relationship_overview"] = {
        "types": [
            {
                "kind": kind,
                "count": count,
                "samples": [
                    {
                        "source": relationship["source"],
                        "target": relationship["target"],
                        "label": kind,
                    }
                    for relationship in relationships
                    if relationship["kind"] == kind
                ][:2],
            }
            for kind, count in relationship_counts.most_common()
        ],
        "top_connected": [
            {
                "id": f"publisher/{publisher['name']}",
                "label": publisher["title"],
                "type": "publisher",
                "count": publisher["dataset_count"],
            }
            for publisher in sorted(
                publishers,
                key=lambda item: (-int(item["dataset_count"]), item["title"]),
            )[:12]
        ],
    }
    analysis["resource_overview"].update(
        {
            "total_resources": len(resources),
            "high_resource_datasets": [
                {
                    "route": record["route"],
                    "label": record["title"],
                    "count": record["resource_count"],
                    "publisher": record["publisher_title"],
                }
                for record in sorted(
                    records,
                    key=lambda item: (-int(item["resource_count"]), item["title"]),
                )[:16]
            ],
            "distributions": {
                "resource_type": facets["resource_type"],
                "record_type": facets["record_type"],
                "source_adapter": facets["source_adapter"],
                "protocol": facets["protocol"],
                "quality_band": facets["quality_band"],
                "assurance_status": facets["assurance_status"],
                "documentation_host": facets["documentation_host"][:16],
                "endpoint_host": facets["endpoint_host"][:16],
            },
        }
    )
    analysis["facet_analysis"] = [
        helpers.facet_analysis(
            records,
            item["key"],
            item["label"],
            item["recommended_control"],
            item["recommendation"],
        )
        for item in analysis.get("facet_analysis", [])
    ]
    analysis["hierarchies"] = [hierarchy]

    search = helpers.build_search(records)
    record_chunks = helpers.chunk_paths("apis", records)
    resource_chunks = helpers.chunk_paths("resources", resources)
    publisher_chunks = helpers.chunk_paths("providers", publishers)
    relationship_chunks = helpers.relationship_chunk_paths(relationships)
    manifest["counts"] = counts
    manifest["chunks"].update(
        {
            "datasets": [str(path) for path, _rows in record_chunks],
            "resources": [str(path) for path, _rows in resource_chunks],
            "publishers": [str(path) for path, _rows in publisher_chunks],
            "relationships": [str(path) for path, _rows in relationship_chunks],
        }
    )
    manifest["search"] = {
        "schema": search["manifest"]["schema"],
        "documents": len(records),
        "tokens": search["manifest"]["counts"]["tokens"],
        "result_limit": search["manifest"]["result_limit"],
    }
    descriptor["counts"] = counts
    return {
        "analysis": analysis,
        "facets": facets,
        "graph_nodes": graph_nodes,
        "graph_edges": graph_edges,
        "overview": overview,
        "record_chunks": record_chunks,
        "resource_chunks": resource_chunks,
        "publisher_chunks": publisher_chunks,
        "relationship_chunks": relationship_chunks,
        "search": search,
        "top_publishers": top_publishers,
        "relationship_counts": relationship_counts,
    }


def write_plain_chunks(prefix: str, chunks: list[tuple[Path, list[dict]]]) -> None:
    expected = {BUNDLE / path for path, _rows in chunks}
    for target in (BUNDLE / "data").glob(f"{prefix}-*.json"):
        if target not in expected:
            target.unlink()
    for path, rows in chunks:
        target = BUNDLE / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(helpers.render_json(rows), encoding="utf-8")


def write_search(search: dict) -> None:
    root = BUNDLE / "data/search"
    if root.exists():
        for target in sorted(root.rglob("*"), key=lambda item: len(item.parts), reverse=True):
            if target.is_file():
                target.unlink()
            elif target.is_dir():
                try:
                    target.rmdir()
                except OSError:
                    pass
    files: dict[Path, str] = {
        Path("data/search/manifest.json"): helpers.render_json(search["manifest"]),
        Path("data/search/doc-map.json"): helpers.render_json(search["doc_map"]),
    }
    for shard, rows in search["lexicon"].items():
        files[Path(f"data/search/lexicon/{shard}.json")] = helpers.render_json(rows)
    for shard, payload in search["prefixes"].items():
        files[Path(f"data/search/prefixes/{shard}.json")] = helpers.render_json(payload)
    for relative, payload in search["postings"].items():
        files[Path(relative)] = helpers.render_json(payload)
    for path, rows in search["result_doc_chunks"]:
        files[path] = helpers.render_json(rows)
    for relative, content in files.items():
        target = BUNDLE / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


def publish_wayfinder_source(descriptor: dict, manifest: dict) -> None:
    WAYFINDER_BUNDLE.mkdir(parents=True, exist_ok=True)
    references: dict[str, dict[str, object]] = {}
    for name in ("catalogue.json", "manifest.json", "reconciliation.json"):
        content = (WAYFINDER_SOURCE / name).read_bytes()
        target = WAYFINDER_BUNDLE / name
        target.write_bytes(content)
        references[name.removesuffix(".json")] = {
            "path": target.relative_to(BUNDLE).as_posix(),
            "sha256": helpers.sha256_bytes(content),
            "bytes": len(content),
        }
    entrypoint = references["manifest"]
    descriptor["entrypoints"]["wayfinder_source"] = entrypoint
    manifest["indexes"]["wayfinder_source"] = entrypoint
    descriptor["extensions"]["okf-wayfinder-synthetic.v1"] = {
        "mode": "synthetic-fixture-opt-in",
        "source": references["catalogue"],
        "provenance": references["manifest"],
        "reconciliation": references["reconciliation"],
        "records": 311,
        "services": 85,
        "new_synthetic_services": 85,
        "exact_matches": 0,
        "fuzzy_merges": 0,
        "assertion_scope": "synthetic-fixture",
        "authority": "synthetic",
        "relationship_lifecycle": "rejected",
        "default_loaded": False,
        "rights": "not specified",
        "attribution": "Paul Buchanan-Jones",
        "private_correspondence_published": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Regenerate the semantic and runtime projections from the checked-in "
            "frozen catalogue without network access."
        )
    )
    parser.parse_args(argv)
    descriptor_path = BUNDLE / "okf-explorer.json"
    manifest_path = BUNDLE / "data/manifest.json"
    descriptor = load(descriptor_path)
    manifest = load(manifest_path)
    records, resources, publishers, relationships = add_wayfinder_to_frozen_corpus(
        descriptor, manifest
    )
    views = rebuild_static_views(
        descriptor, manifest, records, resources, publishers, relationships
    )
    write_plain_chunks("apis", views["record_chunks"])
    write_plain_chunks("resources", views["resource_chunks"])
    write_plain_chunks("providers", views["publisher_chunks"])
    write_search(views["search"])
    (BUNDLE / manifest["indexes"]["facets"]).write_text(
        helpers.render_json(views["facets"]), encoding="utf-8"
    )
    (BUNDLE / manifest["indexes"]["overview"]).write_text(
        helpers.render_json(views["overview"]), encoding="utf-8"
    )

    relationship_chunks = views["relationship_chunks"]
    expected_relationship_paths = {path for path, _rows in relationship_chunks}
    for target in (BUNDLE / "data").glob("relationships-*.json*"):
        if target.relative_to(BUNDLE) not in expected_relationship_paths:
            target.unlink()
    for path, rows in relationship_chunks:
        rendered = helpers.render_json(rows).encode("utf-8")
        target = BUNDLE / path
        if path.suffix == ".gz":
            target.write_bytes(gzip.compress(rendered, compresslevel=6, mtime=0))
        else:
            target.write_bytes(rendered)
    manifest["chunks"]["relationships"] = [
        path.as_posix() for path, _rows in relationship_chunks
    ]
    manifest["counts"]["relationships"] = len(relationships)
    adjacency, buckets = helpers.build_relationship_adjacency(relationships)
    adjacency["buckets"] = {key: value.replace(".json", ".json.gz") for key, value in adjacency["buckets"].items()}
    adjacency_root = BUNDLE / "data/adjacency"
    adjacency_root.mkdir(parents=True, exist_ok=True)
    (adjacency_root / "manifest.json").write_text(helpers.render_json(adjacency), encoding="utf-8")
    expected_adjacency = set()
    for path, routes in buckets:
        target = (BUNDLE / path).with_suffix(".json.gz")
        expected_adjacency.add(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(gzip.compress(helpers.render_json(routes).encode(), compresslevel=6, mtime=0))
    for target in adjacency_root.glob("*.json"):
        if target.name != "manifest.json":
            target.unlink()
    for target in adjacency_root.glob("*.json.gz"):
        if target not in expected_adjacency:
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
        "okf_version": "0.2",
        "core_conformance": "Markdown concept layer",
    })
    descriptor["entrypoints"].update({
        "viewer": "https://chris-page-gov.github.io/okf-explorer/",
        "relationship_adjacency": "data/adjacency/manifest.json",
        "semantic_graph": "data/semantic/manifest.json",
        "semantic_context": "context/okf-bundle-v1.jsonld",
        "semantic_assertion_schema": "schemas/okf-relationship-assertion.v2.schema.json",
        "predicate_registry": "data/predicate-registry.json",
        "notes": "docs/UK-Government-API-OKF.md",
        "standards_crosswalk": "docs/okf-standards-crosswalk.md",
        "wayfinder_comparison": "docs/wayfinder-comparison-2026-09-24.md",
    })
    source = descriptor.setdefault("source", {})
    source["source_tiers"] = sorted(
        set(source.get("source_tiers", [])) | {wayfinder_import.SOURCE_TIER}
    )
    source["adapters"] = sorted(
        set(source.get("adapters", [])) | {wayfinder_import.SOURCE_ADAPTER}
    )
    source["rights_notice"] = (
        "Record-level rights are authoritative. Wayfinder source records have "
        "rights not specified and do not inherit an asserted source licence."
    )
    descriptor["description"] = (
        "Large-corpus OKF view of UK Government API and data-access metadata, "
        "plus an explicitly fictional Wayfinder comparison layer with separate "
        "synthetic authority, scope and rights."
    )
    publish_wayfinder_source(descriptor, manifest)
    snapshot = str(descriptor.get("snapshot") or descriptor["generated_at"])
    descriptor["snapshot"] = snapshot
    manifest["snapshot"] = snapshot
    runtime_files, runtime_reference = helpers.rich_relationship_runtime_outputs(
        relationships,
        generated_at=str(descriptor["generated_at"]),
        snapshot=snapshot,
    )
    descriptor["entrypoints"]["relationship_runtime"] = runtime_reference
    descriptor.setdefault("entrypoint_integrity", {})[
        "relationship_runtime"
    ] = runtime_reference
    manifest["indexes"]["relationship_runtime"] = runtime_reference
    validation_report = helpers.semantic_validation_report(
        relationships,
        generated_at=str(descriptor["generated_at"]),
    )
    validation_path = "data/semantic/validation-report.json"
    descriptor["entrypoints"]["semantic_validation"] = validation_path
    manifest["indexes"]["semantic_validation"] = validation_path
    descriptor["extensions"]["okf-semantic-relationships.v1"] = {
        "mode": "generated-sharded-assertion-graph",
        "manifest": "data/semantic/manifest.json",
        "runtime_projection": runtime_reference["path"],
        "compatibility_projection": "data/relationships-*.json.gz",
        "runtime_selection": "bounded-material-relationships",
        "direct_triple_policy": "generated-from-one-assertion-source-across-pinned-shards",
        "metadata_scope": "metadata-only-catalogue-view",
    }
    descriptor["extensions"]["okf-standards-crosswalk.v1"]["crosswalk"] = (
        "docs/okf-standards-crosswalk.md"
    )
    manifest["indexes"]["relationship_adjacency"] = "data/adjacency/manifest.json"
    manifest["indexes"]["semantic_graph"] = "data/semantic/manifest.json"
    manifest["indexes"]["predicate_registry"] = "data/predicate-registry.json"
    manifest["performance"]["route_relationship_hydration"] = "hash-sharded adjacency"
    manifest["okf_version"] = "0.2"
    analysis_path = BUNDLE / manifest["indexes"]["analysis"]
    analysis = views["analysis"]
    analysis["standards_alignment"]["crosswalk"] = "docs/okf-standards-crosswalk.md"
    analysis["summary"]["notices"] = list(analysis["summary"].get("notices", []))
    semantic_notice = (
        "Every directed relationship is emitted from one deterministic assertion "
        "source into the complete semantic and compatibility planes. Explorer's "
        "digest-bound rich runtime is a governed material subset that stays within "
        "the Reader's aggregate loading ceilings."
    )
    if semantic_notice not in analysis["summary"]["notices"]:
        analysis["summary"]["notices"].append(semantic_notice)
    semantic_files, semantic_manifest = helpers.semantic_publication_files(
        descriptor=descriptor,
        records=records,
        resources=resources,
        publishers=publishers,
        relationships=relationships,
    )
    semantic_files[Path(validation_path)] = helpers.render_json(validation_report)
    semantic_root = BUNDLE / "data/semantic"
    semantic_root.mkdir(parents=True, exist_ok=True)
    expected_semantic = {
        BUNDLE / path for path in semantic_files if path.parts[:2] == ("data", "semantic")
    }
    for target in semantic_root.glob("*"):
        if target.is_file() and target not in expected_semantic:
            target.unlink()
    for path, content in semantic_files.items():
        target = BUNDLE / path
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            target.write_bytes(content)
        else:
            target.write_text(content, encoding="utf-8")
    runtime_root = BUNDLE / helpers.RELATIONSHIP_RUNTIME_ROOT
    expected_runtime = {
        BUNDLE / path
        for path in runtime_files
        if path.parts[:2] == ("data", "relationship-runtime")
    }
    if runtime_root.exists():
        for target in sorted(
            runtime_root.rglob("*"),
            key=lambda item: len(item.parts),
            reverse=True,
        ):
            if target.is_file() and target not in expected_runtime:
                target.unlink()
            elif target.is_dir():
                try:
                    target.rmdir()
                except OSError:
                    pass
    for path, content in runtime_files.items():
        target = BUNDLE / path
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            target.write_bytes(content)
        else:
            target.write_text(content, encoding="utf-8")
    manifest["semantic_graph"] = semantic_manifest["counts"]
    graph_path = BUNDLE / manifest["indexes"]["graph"]
    graph = load(graph_path)
    graph.update({
        "node_counts": {
            "dataset": len(records),
            "resource": len(resources),
            "publisher": len(publishers),
            "api_product": manifest["counts"]["api_products"],
            "data_access_endpoint": manifest["counts"]["data_access_endpoints"],
            "data_product": manifest["counts"]["data_products"],
            "operation": manifest["counts"]["operations"],
            "schema": manifest["counts"]["schemas"],
            "synthetic_demo_service": manifest["counts"]["synthetic_demo_services"],
        },
        "edge_counts": [
            {"kind": kind, "count": count}
            for kind, count in views["relationship_counts"].most_common()
        ],
        "top_publishers": views["top_publishers"],
        "semantic_manifest": "data/semantic/manifest.json",
        "predicate_registry": "data/predicate-registry.json",
        "relationship_runtime": runtime_reference,
        "semantic_validation": validation_path,
        "semantic_counts": semantic_manifest["counts"],
        "assertion_set_sha256": semantic_manifest["assertion_set_sha256"],
        "relationship_index": "data/relationships-0.json.gz",
    })
    graph_path.write_text(helpers.render_json(graph), encoding="utf-8")
    descriptor_path.write_text(helpers.render_json(descriptor), encoding="utf-8")
    manifest_path.write_text(helpers.render_json(manifest), encoding="utf-8")
    analysis_path.write_text(helpers.render_json(analysis), encoding="utf-8")
    docs_root = BUNDLE / "docs"
    docs_root.mkdir(parents=True, exist_ok=True)
    for source in (ROOT / "docs").glob("*.md"):
        (docs_root / source.name).write_text(
            documentation_concept(source, descriptor["generated_at"]),
            encoding="utf-8",
        )
    markdown_files = helpers.markdown_output_files(
        {"records": records, "publishers": publishers, "descriptor": descriptor}
    )
    for relative, content in markdown_files.items():
        target = BUNDLE / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
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
        '<li><a href="data/semantic/manifest.json">Semantic graph manifest</a></li><li><a href="data/semantic/validation-report.json">Semantic validation receipt</a></li>'
        '<li><a href="data/relationship-runtime/manifest.json">Material relationship runtime</a></li><li><a href="data/predicate-registry.json">Predicate registry</a></li>'
        '<li><a href="data/adjacency/manifest.json">Relationship adjacency</a></li><li><a href="data/sources/wayfinder/manifest.json">Wayfinder source provenance</a></li>'
        '<li><a href="docs/wayfinder-comparison-2026-09-24.md">Wayfinder comparison</a></li><li><a href="checksums.json">Checksums</a></li>'
        '</ul></body></html>\n'
    )
    (BUNDLE / "index.html").write_text(index_html, encoding="utf-8")
    print(
        f"upgraded {len(relationships):,} rich relationships across "
        f"{len(buckets)} adjacency buckets and "
        f"{semantic_manifest['counts']['shards']} semantic graph shards"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
