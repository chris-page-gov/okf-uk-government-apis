#!/usr/bin/env python3
"""Validate the independently published UK Government APIs OKF bundle."""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any

SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

import build_uk_government_api_okf as helpers
import wayfinder_import

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "bundle"
VALID_STATUS = {"draft", "stable", "deprecated"}
ACTOR_PATTERN = re.compile(
    r"^(?:human:[^\s:]+|process:[^\s:]+|[^\s/:]+/[^\s/]+)$"
)
GENERATED_PATTERN = re.compile(
    r"(?m)^generated:\s*\{\s*by:\s*([^,}]+),\s*at:\s*(.+?)\s*\}\s*$"
)
ABSOLUTE_IRI = re.compile(r"^[^\s:]+:.+$")
MAX_GITHUB_FILE_BYTES = 100_000_000


class RelationshipRuntimeError(ValueError):
    """Raised when the bounded relationship runtime breaks its contract."""


def validate_wayfinder_publication(
    descriptor: dict[str, Any], data_manifest: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    extension = descriptor.get("extensions", {}).get(
        "okf-wayfinder-synthetic.v1"
    )
    if not isinstance(extension, dict):
        return ["Wayfinder synthetic extension is missing"]
    expected_policy = {
        "mode": "synthetic-fixture-opt-in",
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
    for key, expected in expected_policy.items():
        if extension.get(key) != expected:
            errors.append(f"Wayfinder extension {key} is not {expected!r}")

    authored_root = ROOT / "sources" / "wayfinder" / "2026-09-24"
    reference_names = {
        "source": "catalogue.json",
        "provenance": "manifest.json",
        "reconciliation": "reconciliation.json",
    }
    for key, name in reference_names.items():
        reference = extension.get(key)
        if not isinstance(reference, dict):
            errors.append(f"Wayfinder {key} reference is missing")
            continue
        relative = str(reference.get("path") or "")
        expected_relative = f"data/sources/wayfinder/{name}"
        if relative != expected_relative:
            errors.append(f"Wayfinder {key} path is not canonical")
            continue
        published = BUNDLE / relative
        authored = authored_root / name
        if not published.is_file() or not authored.is_file():
            errors.append(f"Wayfinder {key} source artefact is missing")
            continue
        content = published.read_bytes()
        if content != authored.read_bytes():
            errors.append(f"Wayfinder {key} differs from its authored source")
        if reference.get("sha256") != hashlib.sha256(content).hexdigest():
            errors.append(f"Wayfinder {key} digest does not reconcile")
        if reference.get("bytes") != len(content):
            errors.append(f"Wayfinder {key} byte count does not reconcile")

    provenance = descriptor.get("entrypoints", {}).get("wayfinder_source")
    manifest_reference = data_manifest.get("indexes", {}).get("wayfinder_source")
    if provenance != extension.get("provenance") or manifest_reference != provenance:
        errors.append("Wayfinder provenance entrypoints do not agree")

    try:
        catalogue, source_manifest = wayfinder_import.load_source(
            authored_root / "catalogue.json", authored_root / "manifest.json"
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        errors.append(f"Wayfinder source validation failed: {error}")
        return errors
    if source_manifest.get("authorAttribution", {}).get("name") != "Paul Buchanan-Jones":
        errors.append("Wayfinder public author attribution is missing")
    public_provenance = (authored_root / "manifest.json").read_text(encoding="utf-8")
    public_provenance += (authored_root / "reconciliation.json").read_text(
        encoding="utf-8"
    )
    for forbidden in ("/Users/", "/tmp/", ".email.md"):
        if forbidden in public_provenance:
            errors.append(f"Wayfinder public provenance leaks private path {forbidden}")

    records = [
        row
        for relative in data_manifest.get("chunks", {}).get("datasets", [])
        for row in load(BUNDLE / relative)
        if row.get("source_adapter") == wayfinder_import.SOURCE_ADAPTER
    ]
    source_services = {str(row["id"]): row for row in catalogue["services"]}
    if len(records) != 85 or len({str(row.get("name")) for row in records}) != 85:
        errors.append("Wayfinder imported service count or identity set is invalid")
    for record in records:
        source_id = str(record.get("source_record_id") or "")
        if record.get("extras", {}).get("wayfinder", {}).get(
            "source_record"
        ) != source_services.get(source_id):
            errors.append(f"Wayfinder source metadata is incomplete: {source_id}")
        required = {
            "synthetic_demo": True,
            "default_loaded": False,
            "assertion_scope": "synthetic-fixture",
            "authority_class": "synthetic",
            "rights_status": "not specified",
            "license_id": "not-specified",
            "license_basis": "source-rights-not-specified",
        }
        for key, expected in required.items():
            if record.get(key) != expected:
                errors.append(
                    f"Wayfinder record {source_id} {key} is not {expected!r}"
                )
    if data_manifest.get("counts", {}).get("synthetic_demo_services") != 85:
        errors.append("Wayfinder synthetic service count is absent from data manifest")
    return errors


def load(path: Path):
    data = path.read_bytes()
    if path.suffix == ".gz":
        data = gzip.decompress(data)
    return json.loads(data)


def _runtime_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RelationshipRuntimeError(f"{label} must be an object")
    return value


def _runtime_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise RelationshipRuntimeError(f"{label} must be an array")
    return value


def _runtime_reference(value: Any, label: str) -> tuple[str, str, int | None]:
    if isinstance(value, str):
        return value, "", None
    reference = _runtime_object(value, label)
    path = reference.get("path")
    digest = reference.get("sha256", "")
    byte_count = reference.get("bytes")
    if not isinstance(path, str) or not path:
        raise RelationshipRuntimeError(f"{label} path is missing")
    if digest and not re.fullmatch(r"[0-9a-f]{64}", str(digest)):
        raise RelationshipRuntimeError(f"{label} SHA-256 is malformed")
    if byte_count is not None and (
        not isinstance(byte_count, int) or isinstance(byte_count, bool) or byte_count < 1
    ):
        raise RelationshipRuntimeError(f"{label} byte count is invalid")
    return path, str(digest), byte_count


def _runtime_path(bundle: Path, relative: Any, label: str) -> tuple[str, Path]:
    if not isinstance(relative, str) or not relative or re.search(r"\s", relative):
        raise RelationshipRuntimeError(f"{label} must be a non-empty relative path")
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise RelationshipRuntimeError(f"{label} is not a safe bundle-relative path")
    bundle_root = bundle.resolve()
    path = (bundle / candidate).resolve()
    if not path.is_relative_to(bundle_root):
        raise RelationshipRuntimeError(f"{label} escapes the bundle")
    return candidate.as_posix(), path


def _bounded_gzip_json(compressed: bytes, label: str) -> Any:
    """Decode one Reader resource without permitting a gzip expansion bomb."""
    with gzip.GzipFile(fileobj=io.BytesIO(compressed), mode="rb") as handle:
        raw = handle.read(helpers.MAX_RICH_RUNTIME_DECODED_CHUNK_BYTES + 1)
    if len(raw) > helpers.MAX_RICH_RUNTIME_DECODED_CHUNK_BYTES:
        raise RelationshipRuntimeError(f"{label} exceeds the decoded-byte ceiling")
    return json.loads(raw)


def validate_relationship_runtime(
    bundle: Path,
    descriptor: dict[str, Any],
    data_manifest: dict[str, Any],
    expected_material: dict[str, str],
) -> list[str]:
    """Replay every runtime, digest, locator and Reader-ceiling commitment."""
    try:
        entrypoints = _runtime_object(
            descriptor.get("entrypoints"), "Explorer descriptor entrypoints"
        )
        indexes = _runtime_object(data_manifest.get("indexes"), "data manifest indexes")
        descriptor_reference = entrypoints.get("relationship_runtime")
        manifest_reference = indexes.get("relationship_runtime")
        descriptor_path, descriptor_hash, descriptor_bytes = _runtime_reference(
            descriptor_reference, "Explorer relationship-runtime entrypoint"
        )
        manifest_path, manifest_hash, manifest_bytes = _runtime_reference(
            manifest_reference, "data-manifest relationship-runtime index"
        )
        integrity = _runtime_object(
            descriptor.get("entrypoint_integrity", {}),
            "Explorer descriptor entrypoint integrity",
        )
        integrity_path, integrity_hash, integrity_bytes = _runtime_reference(
            integrity.get("relationship_runtime"),
            "Explorer relationship-runtime integrity",
        )
        if not descriptor_hash or not manifest_hash or not integrity_hash:
            raise RelationshipRuntimeError(
                "relationship-runtime references must carry SHA-256 digests"
            )
        if len({descriptor_path, manifest_path, integrity_path}) != 1:
            raise RelationshipRuntimeError(
                "relationship-runtime reference paths do not agree"
            )
        if len({descriptor_hash, manifest_hash, integrity_hash}) != 1:
            raise RelationshipRuntimeError(
                "relationship-runtime reference digests do not agree"
            )
        declared_bytes = {
            value
            for value in (descriptor_bytes, manifest_bytes, integrity_bytes)
            if value is not None
        }
        if len(declared_bytes) > 1:
            raise RelationshipRuntimeError(
                "relationship-runtime reference byte counts do not agree"
            )

        runtime_relative, runtime_path = _runtime_path(
            bundle, descriptor_path, "relationship-runtime manifest"
        )
        if not runtime_path.is_file():
            raise RelationshipRuntimeError(
                f"relationship-runtime manifest is missing: {runtime_relative}"
            )
        runtime_raw = runtime_path.read_bytes()
        if hashlib.sha256(runtime_raw).hexdigest() != descriptor_hash:
            raise RelationshipRuntimeError(
                "relationship-runtime manifest digest does not reconcile"
            )
        if declared_bytes and len(runtime_raw) != next(iter(declared_bytes)):
            raise RelationshipRuntimeError(
                "relationship-runtime manifest byte count does not reconcile"
            )
        runtime = _runtime_object(
            json.loads(runtime_raw), "relationship-runtime manifest"
        )
        helpers.validate_runtime_schema(
            runtime, "manifest", "relationship-runtime manifest"
        )
        snapshot = runtime.get("snapshot")
        if descriptor.get("snapshot") != snapshot or data_manifest.get("snapshot") != snapshot:
            raise RelationshipRuntimeError(
                "descriptor, data manifest and relationship runtime snapshots differ"
            )
        if runtime.get("semantic_manifest") != indexes.get("semantic_graph"):
            raise RelationshipRuntimeError(
                "relationship runtime points to the wrong semantic manifest"
            )
        if runtime.get("assertion_contract") != "schemas/okf-relationship-assertion.v2.schema.json":
            raise RelationshipRuntimeError(
                "relationship runtime points to the wrong assertion contract"
            )
        if runtime.get("row_contract") != "schemas/relationship-runtime-row.schema.json":
            raise RelationshipRuntimeError(
                "relationship runtime points to the wrong row contract"
            )

        plane_values = _runtime_list(runtime.get("planes"), "relationship-runtime planes")
        if len(plane_values) > helpers.MAX_RICH_RUNTIME_PLANES:
            raise RelationshipRuntimeError("relationship runtime exceeds the plane ceiling")
        plane_names: set[str] = set()
        plane_ids: set[str] = set()
        plane_by_name: dict[str, dict[str, Any]] = {}
        chunk_ids: set[str] = set()
        chunk_rows: dict[str, int] = {}
        chunk_sizes: dict[str, int] = {}
        chunk_text_units: dict[str, int] = {}
        chunk_plane: dict[str, str] = {}
        route_planes: dict[str, dict[str, set[str]]] = defaultdict(
            lambda: defaultdict(set)
        )
        route_chunks: dict[str, set[str]] = defaultdict(set)
        observed_ids: dict[str, str] = {}
        active_assertions = 0
        historical_assertions = 0
        rejected_assertions = 0
        expected_defaults: list[str] = []
        total_rows = 0

        status_order = {"official", "normalized", "inferred", "model-derived"}
        scope_values = {"real-world", "synthetic-fixture"}
        lifecycle_values = {"active", "historical", "rejected"}
        authority_values = {
            "official", "derived", "model-assisted", "synthetic", "unclassified"
        }
        for plane_index, value in enumerate(plane_values):
            label = f"relationship-runtime plane {plane_index}"
            plane = _runtime_object(value, label)
            name = str(plane.get("name") or "")
            plane_id = str(plane.get("id") or "")
            lifecycle = str(plane.get("lifecycle") or "")
            scope = str(plane.get("assertion_scope") or "")
            active = plane.get("active")
            authorities = _runtime_list(
                plane.get("authority_classes"), f"{label} authority classes"
            )
            if (
                not name
                or not plane_id
                or name in plane_names
                or plane_id in plane_ids
                or lifecycle not in lifecycle_values
                or scope not in scope_values
                or active is not (lifecycle == "active")
                or len(authorities) != 1
                or authorities[0] not in authority_values
            ):
                raise RelationshipRuntimeError(
                    f"{label} identity, lifecycle, scope or authority is invalid"
                )
            plane_names.add(name)
            plane_ids.add(plane_id)
            plane_by_name[name] = plane
            authority_class = str(authorities[0])
            if active:
                expected_defaults.append(name)
            expected_plane_name = (
                f"material-{{status}}-{scope}-{authority_class}"
                + (f"-{lifecycle}" if lifecycle != "active" else "")
            )
            plane_row_count = 0
            for chunk_index, chunk_value in enumerate(
                _runtime_list(plane.get("chunks"), f"{label} chunks")
            ):
                chunk_label = f"{label} chunk {chunk_index}"
                chunk = _runtime_object(chunk_value, chunk_label)
                chunk_id = str(chunk.get("id") or "")
                if chunk_id in chunk_ids:
                    raise RelationshipRuntimeError(
                        f"{chunk_label} repeats a chunk identity"
                    )
                chunk_ids.add(chunk_id)
                relative, path = _runtime_path(
                    bundle, chunk.get("path"), f"{chunk_label} path"
                )
                if relative in chunk_rows or not path.is_file():
                    raise RelationshipRuntimeError(
                        f"{chunk_label} path is duplicated or missing"
                    )
                compressed = path.read_bytes()
                if (
                    len(compressed) != chunk.get("bytes")
                    or hashlib.sha256(compressed).hexdigest() != chunk.get("sha256")
                ):
                    raise RelationshipRuntimeError(
                        f"{chunk_label} byte or SHA-256 commitment differs"
                    )
                if len(compressed) > helpers.MAX_RICH_RUNTIME_CHUNK_BYTES:
                    raise RelationshipRuntimeError(
                        f"{chunk_label} exceeds the compressed-byte ceiling"
                    )
                rows = _bounded_gzip_json(compressed, chunk_label)
                if helpers.gzip_json(rows) != compressed:
                    raise RelationshipRuntimeError(
                        f"{chunk_label} is not deterministic canonical gzip"
                    )
                if (
                    not isinstance(rows, list)
                    or len(rows) != chunk.get("count")
                    or len(rows) != chunk.get("records")
                    or len(rows) > helpers.MAX_RICH_RUNTIME_CHUNK_ROWS
                ):
                    raise RelationshipRuntimeError(
                        f"{chunk_label} row commitments differ or exceed the ceiling"
                    )
                retained_units = 0
                for row_index, row_value in enumerate(rows):
                    row_label = f"{chunk_label} row {row_index}"
                    row = _runtime_object(row_value, row_label)
                    helpers.validate_runtime_schema(row, "row", row_label)
                    evidence = _runtime_list(row.get("evidence"), f"{row_label} evidence")
                    evidence_ids = [
                        str(_runtime_object(item, f"{row_label} evidence item").get("@id") or "")
                        for item in evidence
                    ]
                    if len(set(evidence_ids)) != len(evidence_ids):
                        raise RelationshipRuntimeError(
                            f"{row_label} repeats an evidence identity"
                        )
                    supporting = row.get("supporting_assertions", [])
                    if not isinstance(supporting, list) or len(
                        supporting
                    ) > helpers.MAX_RICH_RUNTIME_SUPPORTING_ASSERTIONS:
                        raise RelationshipRuntimeError(
                            f"{row_label} exceeds the supporting-assertion ceiling"
                        )
                    identifier = str(row.get("assertion_id") or "")
                    status = str(row.get("assertion_status") or "")
                    row_scope = str(row.get("assertion_scope") or "")
                    row_authority = str((row.get("authority") or {}).get("class") or "")
                    if (
                        not identifier
                        or identifier != row.get("id")
                        or identifier in observed_ids
                        or row.get("source") != row.get("source_route")
                        or row.get("target") != row.get("target_route")
                        or not helpers.safe_runtime_route(str(row.get("source") or ""))
                        or not helpers.safe_runtime_route(str(row.get("target") or ""))
                        or row.get("predicate") != row.get("predicate_iri")
                        or row.get("plane") != plane_id
                        or row.get("lifecycle") != lifecycle
                        or row.get("active") is not active
                        or row_scope != scope
                        or row_authority != authority_class
                        or status not in status_order
                        or name != expected_plane_name.format(status=status)
                        or row.get("label") not in helpers.MATERIAL_RELATIONSHIP_LABELS
                    ):
                        raise RelationshipRuntimeError(
                            f"{row_label} identity, plane or material selection is invalid"
                        )
                    observed_ids[identifier] = projection_digest(row)
                    retained = helpers.rich_runtime_text_units(
                        helpers.rich_runtime_reader_projection(row)
                    )
                    if retained > helpers.MAX_RICH_RUNTIME_ROW_TEXT_UNITS:
                        raise RelationshipRuntimeError(
                            f"{row_label} exceeds the retained-text ceiling"
                        )
                    retained_units += retained
                    source = str(row["source"])
                    target = str(row["target"])
                    for route in {source, target}:
                        route_planes[route][name].add(identifier)
                        route_chunks[route].add(relative)
                if retained_units > helpers.MAX_RICH_RUNTIME_RETAINED_TEXT_UNITS:
                    raise RelationshipRuntimeError(
                        f"{chunk_label} exceeds the aggregate retained-text ceiling"
                    )
                chunk_rows[relative] = len(rows)
                chunk_sizes[relative] = len(compressed)
                chunk_text_units[relative] = retained_units
                chunk_plane[relative] = name
                plane_row_count += len(rows)
                total_rows += len(rows)
            if plane_row_count != plane.get("assertions"):
                raise RelationshipRuntimeError(
                    f"{label} assertion total does not reconcile"
                )
            if lifecycle == "active":
                active_assertions += plane_row_count
            elif lifecycle == "historical":
                historical_assertions += plane_row_count
            else:
                rejected_assertions += plane_row_count

        if total_rows > helpers.MAX_RICH_RUNTIME_ROWS:
            raise RelationshipRuntimeError("relationship runtime exceeds the row ceiling")
        if len(chunk_rows) > helpers.MAX_RICH_RUNTIME_CHUNKS:
            raise RelationshipRuntimeError("relationship runtime exceeds the chunk ceiling")
        default_planes = _runtime_list(
            runtime.get("default_planes"), "relationship-runtime default planes"
        )
        if default_planes != expected_defaults:
            raise RelationshipRuntimeError(
                "default_planes must contain exactly the active planes"
            )
        default_chunks = {
            str(chunk["path"])
            for name in default_planes
            for chunk in plane_by_name[name]["chunks"]
        }
        if sum(chunk_rows[path] for path in default_chunks) > helpers.MAX_RICH_RUNTIME_WHOLE_ROWS:
            raise RelationshipRuntimeError(
                "default runtime exceeds the Reader's whole-hydration row ceiling"
            )
        if sum(chunk_sizes[path] for path in default_chunks) > helpers.MAX_RICH_RUNTIME_ROUTE_COMPRESSED_BYTES:
            raise RelationshipRuntimeError(
                "default runtime exceeds the Reader's compressed-byte ceiling"
            )
        if sum(chunk_text_units[path] for path in default_chunks) > helpers.MAX_RICH_RUNTIME_RETAINED_TEXT_UNITS:
            raise RelationshipRuntimeError(
                "default runtime exceeds the Reader's retained-text ceiling"
            )
        if observed_ids != expected_material:
            missing = len(set(expected_material) - set(observed_ids))
            unexpected = len(set(observed_ids) - set(expected_material))
            changed = sum(
                observed_ids[key] != expected_material[key]
                for key in set(observed_ids) & set(expected_material)
            )
            raise RelationshipRuntimeError(
                "material runtime differs from the full compatibility graph: "
                f"{missing} missing, {unexpected} unexpected, {changed} changed"
            )
        totals = _runtime_object(runtime.get("totals"), "relationship-runtime totals")
        expected_totals = {
            "active_assertions": active_assertions,
            "historical_assertions": historical_assertions,
            "rejected_assertions": rejected_assertions,
            "all_assertions": total_rows,
            "chunks": len(chunk_rows),
        }
        if any(totals.get(key) != value for key, value in expected_totals.items()):
            raise RelationshipRuntimeError(
                "relationship-runtime totals do not reconcile"
            )

        locator_reference = _runtime_object(
            runtime.get("route_locator"), "relationship-runtime route locator"
        )
        locator_relative, locator_path = _runtime_path(
            bundle,
            locator_reference.get("path"),
            "relationship route-locator manifest",
        )
        locator_raw = locator_path.read_bytes() if locator_path.is_file() else b""
        if (
            not locator_raw
            or hashlib.sha256(locator_raw).hexdigest()
            != locator_reference.get("sha256")
        ):
            raise RelationshipRuntimeError(
                "relationship route-locator manifest digest does not reconcile"
            )
        locator = _runtime_object(
            json.loads(locator_raw), "relationship route-locator manifest"
        )
        helpers.validate_runtime_schema(
            locator, "locator", "relationship route-locator manifest"
        )
        seen_routes: set[str] = set()
        seen_prefixes: set[str] = set()
        route_total = 0
        bucket_chunk_references = 0
        template = str(locator.get("bucket_path_template") or "")
        for metadata_index, metadata_value in enumerate(
            _runtime_list(locator.get("buckets"), "relationship route-locator buckets")
        ):
            metadata_label = f"relationship route-locator bucket {metadata_index}"
            metadata = _runtime_object(metadata_value, metadata_label)
            prefix = str(metadata.get("bucket") or "")
            relative, path = _runtime_path(
                bundle, metadata.get("path"), f"{metadata_label} path"
            )
            if (
                not re.fullmatch(r"[0-9a-f]{2}", prefix)
                or prefix in seen_prefixes
                or relative != template.replace("{prefix}", prefix)
                or not path.is_file()
            ):
                raise RelationshipRuntimeError(
                    f"{metadata_label} prefix or path is invalid"
                )
            seen_prefixes.add(prefix)
            compressed = path.read_bytes()
            if (
                len(compressed) != metadata.get("bytes")
                or hashlib.sha256(compressed).hexdigest() != metadata.get("sha256")
                or len(compressed) > helpers.MAX_RICH_RUNTIME_CHUNK_BYTES
            ):
                raise RelationshipRuntimeError(
                    f"{metadata_label} byte or digest commitment differs"
                )
            bucket = _runtime_object(
                _bounded_gzip_json(compressed, metadata_label), metadata_label
            )
            if helpers.gzip_json(bucket) != compressed:
                raise RelationshipRuntimeError(
                    f"{metadata_label} is not deterministic canonical gzip"
                )
            helpers.validate_runtime_schema(bucket, "locator_bucket", metadata_label)
            if bucket.get("bucket") != prefix:
                raise RelationshipRuntimeError(f"{metadata_label} prefix differs")
            bucket_references = 0
            routes = _runtime_list(bucket.get("routes"), f"{metadata_label} routes")
            for route_index, route_value in enumerate(routes):
                route_label = f"{metadata_label} route {route_index}"
                route_row = _runtime_object(route_value, route_label)
                route = str(route_row.get("route") or "")
                if (
                    route in seen_routes
                    or helpers.rich_runtime_route_bucket(route) != prefix
                    or route not in route_planes
                ):
                    raise RelationshipRuntimeError(
                        f"{route_label} is duplicated, misplaced or unknown"
                    )
                seen_routes.add(route)
                listed_chunks = _runtime_list(route_row.get("chunks"), f"{route_label} chunks")
                commitments = _runtime_list(route_row.get("planes"), f"{route_label} planes")
                committed_chunks: set[str] = set()
                committed_names: set[str] = set()
                for commitment_value in commitments:
                    commitment = _runtime_object(commitment_value, f"{route_label} commitment")
                    name = str(commitment.get("name") or "")
                    paths = _runtime_list(
                        commitment.get("chunks"), f"{route_label} {name} chunks"
                    )
                    identifiers = route_planes[route].get(name, set())
                    if (
                        name in committed_names
                        or not identifiers
                        or any(chunk_plane.get(path) != name for path in paths)
                        or commitment.get("assertions") != len(identifiers)
                        or commitment.get("assertion_ids_sha256")
                        != helpers.rich_runtime_assertion_digest(identifiers)
                    ):
                        raise RelationshipRuntimeError(
                            f"{route_label} plane commitment does not reconcile"
                        )
                    committed_names.add(name)
                    committed_chunks.update(paths)
                if committed_names != set(route_planes[route]):
                    raise RelationshipRuntimeError(
                        f"{route_label} does not commit every incident plane"
                    )
                if set(listed_chunks) != committed_chunks or set(listed_chunks) != route_chunks[route]:
                    raise RelationshipRuntimeError(
                        f"{route_label} chunk coverage does not reconcile"
                    )
                active_chunks = {
                    path
                    for commitment in commitments
                    if commitment.get("name") in default_planes
                    for path in commitment.get("chunks", [])
                }
                active_rows = sum(
                    len(route_planes[route].get(name, set())) for name in default_planes
                )
                if (
                    len(active_chunks) > helpers.MAX_RICH_RUNTIME_ROUTE_CHUNKS
                    or active_rows > helpers.MAX_RICH_RUNTIME_ROUTE_ROWS
                    or sum(chunk_rows[path] for path in active_chunks)
                    > helpers.MAX_RICH_RUNTIME_ROUTE_ROWS
                    or sum(chunk_sizes[path] for path in active_chunks)
                    > helpers.MAX_RICH_RUNTIME_ROUTE_COMPRESSED_BYTES
                    or sum(chunk_text_units[path] for path in active_chunks)
                    > helpers.MAX_RICH_RUNTIME_RETAINED_TEXT_UNITS
                ):
                    raise RelationshipRuntimeError(
                        f"{route_label} exceeds the bounded Reader ceilings"
                    )
                bucket_references += len(listed_chunks)
            counts = _runtime_object(bucket.get("counts"), f"{metadata_label} counts")
            if (
                len(routes) != metadata.get("routes")
                or bucket_references != metadata.get("chunk_references")
                or counts.get("routes") != len(routes)
                or counts.get("chunk_references") != bucket_references
            ):
                raise RelationshipRuntimeError(
                    f"{metadata_label} counts do not reconcile"
                )
            route_total += len(routes)
            bucket_chunk_references += bucket_references
        locator_counts = _runtime_object(
            locator.get("counts"), "relationship route-locator counts"
        )
        if (
            seen_routes != set(route_planes)
            or locator_reference.get("routes") != route_total
            or locator_reference.get("buckets") != len(seen_prefixes)
            or locator_counts.get("routes") != route_total
            or locator_counts.get("buckets") != len(seen_prefixes)
            or locator_counts.get("chunk_references") != bucket_chunk_references
        ):
            raise RelationshipRuntimeError(
                "relationship route-locator totals do not reconcile"
            )
    except (
        RelationshipRuntimeError,
        ValueError,
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        gzip.BadGzipFile,
        KeyError,
        TypeError,
    ) as error:
        return [f"rich relationship runtime is invalid: {error}"]
    return []


def inline_scalar(value: str) -> str:
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return value
        return decoded if isinstance(decoded, str) else value
    return value


def valid_actor(value: str) -> bool:
    return bool(ACTOR_PATTERN.fullmatch(inline_scalar(value)))


def valid_datetime(value: str) -> bool:
    value = inline_scalar(value)
    if "T" not in value:
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def valid_date(value: str) -> bool:
    try:
        date.fromisoformat(inline_scalar(value))
    except ValueError:
        return False
    return True


def assertion_projection(row: dict, *, semantic: bool = False) -> dict:
    """Return the fields that must survive runtime-to-semantic projection."""
    source = row.get("source_route") if semantic else row.get("source")
    target = row.get("target_route") if semantic else row.get("target")
    source_iri = row.get("source") if semantic else row.get("source_iri")
    target_iri = row.get("target") if semantic else row.get("target_iri")
    predicate = row.get("predicate")
    if semantic:
        source_iri = (
            source_iri.get("@id") if isinstance(source_iri, dict) else source_iri
        )
        target_iri = (
            target_iri.get("@id") if isinstance(target_iri, dict) else target_iri
        )
        predicate = predicate.get("@id") if isinstance(predicate, dict) else predicate
    identifier = row.get("@id") if semantic else row.get("id")
    fields = (
        "kind",
        "label",
        "inverse_label",
        "assertion_status",
        "assertion_scope",
        "scope_detail",
        "authority",
        "derivation",
        "derivation_activity",
        "observed_at",
        "freshness",
        "evidence",
        "rights",
        "evidence_type",
        "confidence",
        "confidence_score",
        "source_adapter",
        "source_tier",
        "source_confidence",
        "license_id",
        "license_title",
        "license_basis",
        "license_confidence",
        "target_label",
        "target_aliases",
        "match_key",
        "rule",
        "supporting_assertions",
        "review_status",
        "stale_after",
        "support_profile",
        "strength",
        "count",
        "official_legal_classification",
    )
    return {
        "id": identifier,
        "source": source,
        "target": target,
        "source_iri": source_iri,
        "target_iri": target_iri,
        "predicate": predicate,
        **{field: row[field] for field in fields if field in row},
    }


def projection_digest(row: dict, *, semantic: bool = False) -> str:
    value = json.dumps(
        assertion_projection(row, semantic=semantic),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def validate_relationship(row: dict, errors: list[str], location: str) -> None:
    missing = [
        field
        for field in helpers.RICH_RELATIONSHIP_FIELDS
        if row.get(field) in (None, "", [])
    ]
    if missing:
        errors.append(f"{location} lacks rich relationship fields: {', '.join(missing)}")
        return
    for field in ("id", "source_iri", "target_iri", "predicate", "derivation"):
        if not ABSOLUTE_IRI.fullmatch(str(row.get(field) or "")):
            errors.append(f"{location} {field} is not an absolute IRI")
    if row.get("source_iri") != helpers.semantic_iri(str(row.get("source") or "")):
        errors.append(f"{location} source route/IRI mapping is invalid")
    if row.get("target_iri") != helpers.semantic_iri(str(row.get("target") or "")):
        errors.append(f"{location} target route/IRI mapping is invalid")
    try:
        expected_predicate = helpers.predicate_iri(str(row.get("label") or ""))
    except ValueError:
        expected_predicate = ""
    if row.get("predicate") != expected_predicate:
        errors.append(f"{location} predicate is not the governed label mapping")
    identity_digest = hashlib.sha256(
        "\0".join(
            (
                str(row.get("source_iri") or ""),
                str(row.get("predicate") or ""),
                str(row.get("target_iri") or ""),
            )
        ).encode("utf-8")
    ).hexdigest()[:24]
    if row.get("id") != f"{helpers.ASSERTION_BASE}{identity_digest}":
        errors.append(f"{location} assertion identity is not deterministic")
    if row.get("label") != row.get("kind"):
        errors.append(f"{location} label and legacy kind disagree")
    for field in ("source", "target"):
        if not helpers.safe_runtime_route(str(row.get(field) or "")):
            errors.append(f"{location} {field} is not a safe local runtime identity")
    target_route = str(row.get("target") or "")
    if target_route.startswith("protocol/"):
        target_label = str(row.get("target_label") or "")
        if not target_label:
            errors.append(f"{location} protocol target label is missing")
        else:
            expected_route = helpers.protocol_route(target_label)
            if target_route != expected_route:
                errors.append(f"{location} protocol target route is not canonical")
            legacy_route = f"protocol/{target_label}"
            aliases = row.get("target_aliases")
            if legacy_route != target_route and (
                not isinstance(aliases, list) or legacy_route not in aliases
            ):
                errors.append(f"{location} protocol legacy route alias is missing")
    if row.get("assertion_status") not in {"official", "normalized", "inferred", "model-derived"}:
        errors.append(f"{location} assertion status is invalid")
    if row.get("assertion_scope") not in {"real-world", "synthetic-fixture"}:
        errors.append(f"{location} assertion scope is invalid")
    authority = row.get("authority")
    if not isinstance(authority, dict) or not all(authority.get(key) for key in ("class", "label", "source")):
        errors.append(f"{location} authority is incomplete")
    elif not helpers.is_canonical_safe_http_url(authority.get("source")):
        errors.append(f"{location} authority source is not a canonical safe HTTP(S) URL")
    evidence = row.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        errors.append(f"{location} evidence is incomplete")
    else:
        required = ("@id", "type", "url", "source_field", "source_value_sha256", "retrieved_at")
        evidence_ids: set[str] = set()
        for evidence_index, item in enumerate(evidence):
            evidence_location = f"{location} evidence[{evidence_index}]"
            if not isinstance(item, dict):
                errors.append(f"{evidence_location} is not an object")
                continue
            if any(not item.get(field) for field in required):
                errors.append(f"{evidence_location} provenance is incomplete")
            evidence_id = str(item.get("@id") or "")
            if evidence_id in evidence_ids:
                errors.append(f"{location} repeats an evidence identity")
            evidence_ids.add(evidence_id)
            for field in ("@id", "normalization"):
                if not ABSOLUTE_IRI.fullmatch(str(item.get(field) or "")):
                    errors.append(f"{evidence_location} {field} is not an absolute IRI")
            if not helpers.is_canonical_safe_http_url(item.get("url")):
                errors.append(f"{evidence_location} url is not a canonical safe HTTP(S) URL")
            if "resource" in item and not helpers.is_canonical_safe_http_url(item.get("resource")):
                errors.append(f"{evidence_location} resource is not a canonical safe HTTP(S) URL")
            if not re.fullmatch(r"[0-9a-f]{64}", str(item.get("source_value_sha256") or "")):
                errors.append(f"{evidence_location} source-value digest is invalid")
    rights = row.get("rights")
    if not isinstance(rights, dict) or not rights.get("source") or not rights.get("assertion"):
        errors.append(f"{location} rights are incomplete")
    elif not helpers.is_canonical_safe_http_url(rights.get("source")):
        errors.append(f"{location} rights source is not a canonical safe HTTP(S) URL")
    if row.get("assertion_status") == "inferred":
        if not all(row.get(field) not in (None, "", []) for field in ("rule", "supporting_assertions", "confidence_score", "derivation_activity")):
            errors.append(f"{location} inferred assertion support is incomplete")
    supporting = row.get("supporting_assertions", [])
    if isinstance(supporting, list) and len(
        supporting
    ) > helpers.MAX_RICH_RUNTIME_SUPPORTING_ASSERTIONS:
        errors.append(f"{location} exceeds the supporting-assertion ceiling")


def check_markdown(errors: list[str], generated_at: str) -> int:
    concepts = 0
    for path in sorted(BUNDLE.rglob("*.md")):
        relative = path.relative_to(BUNDLE)
        text = path.read_text(encoding="utf-8")
        if relative == Path("index.md"):
            expected = '---\nokf_version: "0.2"\n---\n'
            if not text.startswith(expected):
                errors.append("root index.md does not declare only OKF v0.2 frontmatter")
            continue
        if path.name in {"index.md", "log.md"}:
            if text.startswith("---\n"):
                errors.append(f"reserved Markdown has frontmatter: {relative}")
            if path.name == "log.md":
                for heading in re.findall(r"(?m)^## (.+)$", text):
                    if not valid_date(heading):
                        errors.append(f"log date is not ISO 8601: {heading}")
            continue

        concepts += 1
        if not text.startswith("---\n"):
            errors.append(f"concept has no frontmatter: {relative}")
            continue
        try:
            frontmatter, _body = text[4:].split("\n---\n", 1)
        except ValueError:
            errors.append(f"concept frontmatter is unterminated: {relative}")
            continue
        if not re.search(r'(?m)^type:\s*(?!"")\S.+$', frontmatter):
            errors.append(f"concept type is missing: {relative}")
        if re.search(r"(?m)^timestamp:", frontmatter):
            errors.append(f"legacy timestamp remains in concept: {relative}")
        generated = GENERATED_PATTERN.search(frontmatter)
        if not generated:
            errors.append(f"generated.by/at is missing: {relative}")
        else:
            generated_by, generated_on = generated.groups()
            if not valid_actor(generated_by):
                errors.append(f"generated.by is not an OKF actor: {relative}")
            if not valid_datetime(generated_on):
                errors.append(f"generated.at is not an ISO 8601 datetime: {relative}")
            elif inline_scalar(generated_on) != generated_at:
                errors.append(f"generated.at is not the publication time: {relative}")
        status = re.search(r"(?m)^status:\s*(\S+)\s*$", frontmatter)
        if not status or status.group(1).strip('"') not in VALID_STATUS:
            errors.append(f"lifecycle status is missing or invalid: {relative}")
        sources = re.search(r"(?m)^sources:\s*(.+)$", frontmatter)
        if (
            not sources
            or not re.search(r'\bresource:\s*(?:"[^"]+"|[^,}\]]+)', sources.group(1))
        ):
            errors.append(f"standard source provenance is missing: {relative}")
        for last_modified in re.findall(
            r'\blast_modified:\s*("[^"]*"|[^,}\]]+)', frontmatter
        ):
            if not valid_date(last_modified):
                errors.append(f"sources.last_modified is not an ISO 8601 date: {relative}")
        for author in re.findall(r'\bauthor:\s*("[^"]*"|[^,}\]]+)', frontmatter):
            if not valid_actor(author):
                errors.append(f"sources.author is not an OKF actor: {relative}")
        if re.search(r"(?m)^verified:", frontmatter):
            errors.append(f"unsupported verification claim present: {relative}")
    return concepts


def main() -> int:
    descriptor = load(BUNDLE / "okf-explorer.json")
    manifest = load(BUNDLE / "data/manifest.json")
    analysis = load(BUNDLE / manifest["indexes"]["analysis"])
    errors: list[str] = []
    for required in (
        "okf-bundle.yamlld",
        "okf-bundle.jsonld",
        "data/adjacency/manifest.json",
        "data/predicate-registry.json",
        "data/semantic/manifest.json",
        "context/okf-bundle-v1.jsonld",
        "schemas/okf-relationship-assertion.v2.schema.json",
        "schemas/relationship-runtime-manifest.schema.json",
        "schemas/relationship-runtime-row.schema.json",
        "schemas/relationship-route-locator.schema.json",
        "schemas/relationship-route-locator-bucket.schema.json",
        "data/semantic/validation-report.json",
        "checksums.json",
    ):
        if not (BUNDLE / required).is_file():
            errors.append(f"missing {required}")

    if descriptor.get("okf_version") != "0.2":
        errors.append("Explorer descriptor does not declare okf_version 0.2")
    if manifest.get("okf_version") != "0.2":
        errors.append("data manifest does not declare okf_version 0.2")
    for name, entrypoint in descriptor.get("entrypoints", {}).items():
        entrypoint_path = (
            entrypoint.get("path") if isinstance(entrypoint, dict) else entrypoint
        )
        if (
            isinstance(entrypoint_path, str)
            and "://" not in entrypoint_path
            and not (BUNDLE / entrypoint_path).is_file()
        ):
            errors.append(
                f"Explorer entrypoint is missing: {name} -> {entrypoint_path}"
            )
    errors.extend(validate_wayfinder_publication(descriptor, manifest))
    crosswalk = descriptor.get("extensions", {}).get(
        "okf-standards-crosswalk.v1", {}
    ).get("crosswalk")
    if crosswalk != "docs/okf-standards-crosswalk.md":
        errors.append("standards crosswalk extension is not bundle-root-relative")
    if analysis.get("standards_alignment", {}).get("crosswalk") != crosswalk:
        errors.append("analysis and descriptor standards crosswalks disagree")
    semantic_descriptors = [
        load(BUNDLE / semantic_name)
        for semantic_name in ("okf-bundle.yamlld", "okf-bundle.jsonld")
    ]
    for semantic_name, semantic in zip(
        ("okf-bundle.yamlld", "okf-bundle.jsonld"), semantic_descriptors
    ):
        if semantic.get("okf_version") != "0.2":
            errors.append(f"{semantic_name} does not declare okf_version 0.2")
        if "@graph" in semantic:
            errors.append(f"{semantic_name} must remain a bounded graph descriptor, not a monolith")
    if semantic_descriptors[0] != semantic_descriptors[1]:
        errors.append("YAML-LD and JSON-LD semantic descriptors disagree")
    if json.loads((BUNDLE / "context/okf-bundle-v1.jsonld").read_text()) != json.loads(
        helpers.SEMANTIC_CONTEXT_PATH.read_text()
    ):
        errors.append("published semantic context differs from its pinned source")
    if json.loads(
        (BUNDLE / "schemas/okf-relationship-assertion.v2.schema.json").read_text()
    ) != json.loads(helpers.SEMANTIC_ASSERTION_SCHEMA_PATH.read_text()):
        errors.append("published assertion schema differs from its pinned source")
    for schema_path in helpers.RELATIONSHIP_RUNTIME_SCHEMA_PATHS.values():
        published = BUNDLE / "schemas" / schema_path.name
        if published.is_file() and json.loads(published.read_text()) != json.loads(
            schema_path.read_text()
        ):
            errors.append(
                f"published relationship runtime schema differs from its authored source: {schema_path.name}"
            )

    semantic_validation = helpers.semantic_validation_module()
    assertion_validator = semantic_validation.semantic_assertion_validator()
    runtime_assertions_checked = 0
    semantic_assertions_checked = 0
    schema_violation_count = 0

    relationship_count = 0
    runtime_digests: dict[str, str] = {}
    expected_material: dict[str, str] = {}
    runtime_incidence_counts: dict[str, int] = {}
    runtime_routes: set[str] = set()
    protocol_route_labels: dict[str, str] = {}
    expected_direct: set[tuple[str, str, str]] = set()
    assertion_set_digest = hashlib.sha256()
    wayfinder_relationships = 0
    for relative in manifest["chunks"]["relationships"]:
        rows = load(BUNDLE / relative)
        for index, row in enumerate(rows):
            location = f"{relative}[{index}]"
            validate_relationship(row, errors, location)
            if row.get("source_adapter") == wayfinder_import.SOURCE_ADAPTER:
                wayfinder_relationships += 1
                if (
                    row.get("assertion_scope") != "synthetic-fixture"
                    or row.get("authority", {}).get("class") != "synthetic"
                    or row.get("lifecycle") != "rejected"
                    or row.get("license_id") != "not-specified"
                    or row.get("license_basis") != "source-rights-not-specified"
                ):
                    errors.append(
                        f"Wayfinder relationship is not a rejected synthetic assertion: {location}"
                    )
            runtime_assertions_checked += 1
            runtime_schema_errors = list(
                assertion_validator.iter_errors(
                    semantic_validation.runtime_relationship_as_assertion(row)
                )
            )
            schema_violation_count += len(runtime_schema_errors)
            for schema_error in runtime_schema_errors:
                instance_path = "/".join(
                    str(item) for item in schema_error.absolute_path
                ) or "<root>"
                errors.append(
                    f"runtime assertion schema violation at {location}/{instance_path}: "
                    f"{schema_error.message}"
                )
            if str(row.get("target") or "").startswith("protocol/"):
                route = str(row.get("target") or "")
                label = str(row.get("target_label") or "")
                prior = protocol_route_labels.get(route)
                if prior is not None and prior != label:
                    errors.append(
                        f"protocol route collision: {route} represents {prior!r} and {label!r}"
                    )
                protocol_route_labels[route] = label
            identifier = str(row.get("id") or "")
            if identifier in runtime_digests:
                errors.append(f"duplicate relationship assertion id: {identifier}")
                continue
            runtime_digests[identifier] = projection_digest(row)
            if row.get("label") in helpers.MATERIAL_RELATIONSHIP_LABELS:
                expected_material[identifier] = runtime_digests[identifier]
            runtime_incidence_counts[identifier] = (
                1 if row.get("source") == row.get("target") else 2
            )
            runtime_routes.update((str(row.get("source")), str(row.get("target"))))
            expected_direct.add(
                (
                    str(row.get("source_iri")),
                    str(row.get("predicate")),
                    str(row.get("target_iri")),
                )
            )
            assertion_set_digest.update(helpers.relationship_signature(row).encode("utf-8"))
            assertion_set_digest.update(b"\n")
            relationship_count += 1
    relationships = relationship_count
    if wayfinder_relationships != 707:
        errors.append(
            f"Wayfinder relationship count is {wayfinder_relationships}, expected 707"
        )
    if relationships != manifest["counts"]["relationships"]:
        errors.append("relationship count mismatch")
    errors.extend(
        validate_relationship_runtime(
            BUNDLE, descriptor, manifest, expected_material
        )
    )
    adjacency = load(BUNDLE / manifest["indexes"]["relationship_adjacency"])
    if (
        adjacency.get("algorithm") != "fnv1a32-prefix-2"
        or adjacency.get("relationships") != relationships
    ):
        errors.append("adjacency mismatch")

    adjacency_seen: Counter[str] = Counter()
    for bucket, relative in adjacency.get("buckets", {}).items():
        path = BUNDLE / relative
        if not path.is_file():
            errors.append(f"adjacency bucket is missing: {relative}")
            continue
        routes = load(path)
        for route, rows in routes.items():
            if helpers.relationship_bucket(route) != bucket:
                errors.append(f"adjacency route is in the wrong bucket: {route}")
            for row in rows:
                identifier = str(row.get("id") or "")
                if route not in {row.get("source"), row.get("target")}:
                    errors.append(f"adjacency row {identifier} is not incident on {route}")
                expected = runtime_digests.get(identifier)
                if expected is None or projection_digest(row) != expected:
                    errors.append(f"adjacency row differs from runtime assertion: {identifier}")
                adjacency_seen[identifier] += 1
    for identifier in runtime_digests:
        expected_occurrences = runtime_incidence_counts[identifier]
        if adjacency_seen[identifier] != expected_occurrences:
            errors.append(
                f"adjacency assertion {identifier} occurs {adjacency_seen[identifier]} "
                f"times, expected {expected_occurrences}"
            )

    semantic_manifest = load(BUNDLE / manifest["indexes"]["semantic_graph"])
    semantic_counts = semantic_manifest.get("counts", {})
    if semantic_counts.get("direct_relationships") != relationships:
        errors.append("semantic direct relationship count mismatch")
    if semantic_counts.get("reified_assertions") != relationships:
        errors.append("semantic reified assertion count mismatch")
    if semantic_manifest.get("assertion_set_sha256") != assertion_set_digest.hexdigest():
        errors.append("semantic assertion-set digest differs from runtime relationships")
    if semantic_descriptors[0].get("graph_manifest", {}).get("@id") != semantic_manifest.get("@id"):
        errors.append("semantic descriptor and graph manifest identities disagree")

    predicate_registry = load(BUNDLE / manifest["indexes"]["predicate_registry"])
    registered_predicates = {
        str(row.get("id")): row for row in predicate_registry.get("predicates", [])
    }
    runtime_predicate_counts = Counter()
    for relative in manifest["chunks"]["relationships"]:
        runtime_predicate_counts.update(row["predicate"] for row in load(BUNDLE / relative))
    if set(registered_predicates) != set(runtime_predicate_counts):
        errors.append("predicate registry and runtime predicate sets disagree")
    for predicate, count in runtime_predicate_counts.items():
        registered = registered_predicates.get(predicate, {})
        if registered.get("assertions") != count:
            errors.append(f"predicate registry count mismatch: {predicate}")
        label = str(registered.get("label") or "")
        if helpers.RELATIONSHIP_INVERSE_LABELS.get(label) != registered.get("inverse_label"):
            errors.append(f"predicate registry inverse label mismatch: {predicate}")

    entity_routes: dict[str, str] = {}
    semantic_assertions_seen: set[str] = set()
    direct_seen = 0
    shard_reified_count = 0
    shard_entries = semantic_manifest.get("shards", [])
    for entry in shard_entries:
        relative = str(entry.get("path") or "")
        path = BUNDLE / relative
        if not path.is_file():
            errors.append(f"semantic shard is missing: {relative}")
            continue
        size = path.stat().st_size
        if size >= MAX_GITHUB_FILE_BYTES:
            errors.append(f"semantic shard exceeds GitHub's 100 MB file boundary: {relative}")
        compressed = path.read_bytes()
        if hashlib.sha256(compressed).hexdigest() != entry.get("sha256"):
            errors.append(f"semantic shard compressed digest mismatch: {relative}")
        raw = gzip.decompress(compressed)
        if hashlib.sha256(raw).hexdigest() != entry.get("uncompressed_sha256"):
            errors.append(f"semantic shard uncompressed digest mismatch: {relative}")
        if len(raw) != entry.get("uncompressed_bytes") or size != entry.get("compressed_bytes"):
            errors.append(f"semantic shard size metadata mismatch: {relative}")
        document = json.loads(raw)
        graph = document.get("@graph")
        if not isinstance(graph, list) or len(graph) != entry.get("nodes"):
            errors.append(f"semantic shard node count mismatch: {relative}")
            continue
        kind = entry.get("kind")
        if kind == "entity-direct-triples":
            local_direct = 0
            for node in graph:
                source_iri = str(node.get("@id") or "")
                route = str(node.get("route") or "")
                if helpers.semantic_iri(route) != source_iri:
                    errors.append(f"semantic entity route/IRI mismatch: {source_iri}")
                entity_routes[route] = source_iri
                for predicate in runtime_predicate_counts:
                    values = node.get(predicate, [])
                    if isinstance(values, dict):
                        values = [values]
                    if not isinstance(values, list):
                        errors.append(f"semantic direct property is not a list: {source_iri} {predicate}")
                        continue
                    for target in values:
                        triple = (source_iri, predicate, str(target.get("@id") or ""))
                        if triple not in expected_direct:
                            errors.append(f"unexpected semantic direct triple: {triple}")
                        else:
                            expected_direct.remove(triple)
                        local_direct += 1
            if local_direct != entry.get("direct_relationships"):
                errors.append(f"semantic shard direct count mismatch: {relative}")
            direct_seen += local_direct
        elif kind == "reified-assertions":
            for node in graph:
                identifier = str(node.get("@id") or "")
                semantic_assertions_checked += 1
                semantic_schema_errors = list(assertion_validator.iter_errors(node))
                schema_violation_count += len(semantic_schema_errors)
                for schema_error in semantic_schema_errors:
                    instance_path = "/".join(
                        str(item) for item in schema_error.absolute_path
                    ) or "<root>"
                    errors.append(
                        f"semantic assertion schema violation at {relative} "
                        f"{identifier}/{instance_path}: {schema_error.message}"
                    )
                types = node.get("@type", [])
                if not isinstance(types, list) or not {"rdf:Statement", "okf:RelationshipAssertion"}.issubset(types):
                    errors.append(f"semantic assertion has invalid types: {identifier}")
                expected = runtime_digests.get(identifier)
                if expected is None or projection_digest(node, semantic=True) != expected:
                    errors.append(f"semantic assertion differs from runtime row: {identifier}")
                if identifier in semantic_assertions_seen:
                    errors.append(f"duplicate reified semantic assertion: {identifier}")
                semantic_assertions_seen.add(identifier)
            shard_reified_count += len(graph)
        else:
            errors.append(f"unknown semantic shard kind: {kind}")
    if expected_direct:
        errors.append(f"{len(expected_direct)} runtime relationships lack matching direct triples")
    if set(runtime_digests) != semantic_assertions_seen:
        errors.append("runtime and reified semantic assertion identity sets disagree")
    if runtime_routes - set(entity_routes):
        errors.append(f"{len(runtime_routes - set(entity_routes))} relationship routes lack semantic entities")
    if direct_seen != relationships or shard_reified_count != relationships:
        errors.append("semantic shard relationship totals disagree with runtime")
    if len(shard_entries) != semantic_counts.get("shards"):
        errors.append("semantic manifest shard count mismatch")

    validation_reference = manifest.get("indexes", {}).get("semantic_validation")
    descriptor_validation = descriptor.get("entrypoints", {}).get(
        "semantic_validation"
    )
    if validation_reference != descriptor_validation or not isinstance(
        validation_reference, str
    ):
        errors.append(
            "descriptor and data manifest semantic-validation references differ"
        )
    else:
        validation_path = BUNDLE / validation_reference
        if not validation_path.is_file():
            errors.append("semantic assertion validation receipt is missing")
        else:
            validation_report = load(validation_path)
            expected_receipt = {
                "status": "conformant" if not schema_violation_count else "non-conformant",
                "draft": semantic_validation.SEMANTIC_ASSERTION_SCHEMA_DRAFT,
                "schema": semantic_validation.SEMANTIC_ASSERTION_SCHEMA_URL,
                "schema_path": semantic_validation.SEMANTIC_ASSERTION_SCHEMA_RELATIVE_PATH,
                "schema_sha256": semantic_validation.SEMANTIC_ASSERTION_SCHEMA_SHA256,
                "schema_bytes": semantic_validation.SEMANTIC_ASSERTION_SCHEMA_BYTES,
                "semantic_assertions_checked": semantic_assertions_checked,
                "runtime_relationships_checked": runtime_assertions_checked,
                "violation_count": schema_violation_count,
            }
            if (
                validation_report.get("schema")
                != "okf-semantic-assertion-validation-report.v1"
                or validation_report.get("generated_at")
                != descriptor.get("generated_at")
                or validation_report.get("status") != "conformant"
                or validation_report.get("violations") != []
                or validation_report.get("semantic_assertion_validation")
                != expected_receipt
            ):
                errors.append(
                    "semantic assertion validation receipt does not bind the exhaustive check"
                )
    if (
        descriptor.get("@id")
        != "https://chris-page-gov.github.io/okf-uk-government-apis/okf-explorer.json"
    ):
        errors.append("canonical descriptor identity mismatch")

    concept_count = check_markdown(errors, descriptor.get("generated_at", ""))
    if errors:
        print("bundle validation failed:")
        for error in errors[:100]:
            print(f"- {error}")
        return 1
    print(
        "bundle validation passed: "
        f"{manifest['counts']['datasets']:,} records, "
        f"{relationships:,} relationships, "
        f"{adjacency['routes']:,} adjacency routes, "
        f"{semantic_counts['shards']:,} bounded semantic shards, "
        f"{concept_count:,} OKF v0.2 concepts"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
