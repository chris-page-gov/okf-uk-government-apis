#!/usr/bin/env python3
"""Map the Wayfinder demo export into an opt-in synthetic OKF layer."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import build_uk_government_api_okf as okf


SOURCE_ADAPTER = "wayfinder_demo"
SOURCE_TIER = "synthetic_demo"
ASSERTION_SCOPE = "synthetic-fixture"
AUTHORITY_CLASS = "synthetic"
RIGHTS_STATUS = "not specified"
WAYFINDER_BASE = "https://wayfinder.pbj.cx"
EXPECTED_COUNTS = {
    "departments": 6,
    "teams": 23,
    "services": 85,
    "patterns": 19,
    "policies": 5,
    "relationships": 138,
    "dataSharingAgreements": 6,
    "people": 24,
    "agents": 5,
}


def load_source(
    catalogue_path: Path, manifest_path: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    raw = catalogue_path.read_bytes()
    catalogue = json.loads(raw)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    digest = hashlib.sha256(raw).hexdigest()
    declared = str(manifest.get("capture", {}).get("sha256") or "")
    if digest != declared:
        raise ValueError(
            f"Wayfinder catalogue SHA-256 is {digest}, manifest declares {declared}"
        )
    actual_counts = {key: len(catalogue.get(key, [])) for key in EXPECTED_COUNTS}
    if actual_counts != EXPECTED_COUNTS:
        raise ValueError(
            f"Wayfinder catalogue counts are {actual_counts!r}, expected {EXPECTED_COUNTS!r}"
        )
    admission = manifest.get("admission", {})
    if admission.get("mode") != "synthetic-fixture-opt-in":
        raise ValueError("Wayfinder source is not admitted as an opt-in synthetic fixture")
    if admission.get("rights") != RIGHTS_STATUS:
        raise ValueError("Wayfinder record-level rights must remain not specified")
    return catalogue, manifest


def source_route(kind: str, source_id: str) -> str:
    return f"wayfinder-{okf.slugify(kind)}/{okf.slugify(source_id)}"


def service_slug(source_id: str) -> str:
    return f"wayfinder-demo-{okf.slugify(source_id)}"


def source_page(kind: str, source_id: str) -> str:
    page_kind = {
        "service": "services",
        "pattern": "patterns",
        "person": "people",
        "agent": "agents",
    }.get(kind, kind)
    return f"{WAYFINDER_BASE}/{page_kind}/{source_id}"


def access_model(authentication: list[str]) -> str:
    values = {str(value) for value in authentication}
    if any(value.startswith("oauth2-") or value == "jwt-bearer" for value in values):
        return "oauth2"
    if "api-key" in values:
        return "api-key"
    if "mtls" in values:
        return "approval-required"
    return "unknown"


def protocols(service: dict[str, Any]) -> list[str]:
    service_type = str(service.get("type") or "")
    if service_type == "event-stream":
        return ["Streaming"]
    if service_type == "api":
        return ["REST/HTTP"]
    return []


def record_type(service_type: str) -> str:
    return {
        "api": "API Product",
        "event-stream": "Event Stream",
        "library": "Software Library",
        "platform": "Digital Platform",
    }.get(service_type, "Synthetic Service")


def synthetic_relationship_metadata(observed_at: str) -> dict[str, Any]:
    return {
        "evidence_type": "source_declared_synthetic_relationship",
        "confidence": "medium",
        "observed_at": observed_at,
        "assertion_status": "normalized",
        "assertion_scope": ASSERTION_SCOPE,
        "scope_detail": "fictional-wayfinder-demo-comparison",
        "authority": {
            "class": AUTHORITY_CLASS,
            "label": "Fictional source claim retained for comparison",
            "source": f"{WAYFINDER_BASE}/about",
        },
        "rights": {
            "source": WAYFINDER_BASE,
            "assertion": (
                "Rights in the source metadata are not specified; the assertion "
                "is retained only as an attributed synthetic comparison fact."
            ),
        },
        # The pinned Reader contract default-loads every active plane. Rejected
        # here means rejected from real-world catalogue admission, not disproved.
        "lifecycle": "rejected",
    }


def add_wayfinder_services(
    builder: okf.CorpusBuilder,
    *,
    catalogue_path: Path,
    manifest_path: Path,
) -> list[dict[str, Any]]:
    """Append all 85 service records without merging title similarities."""

    catalogue, manifest = load_source(catalogue_path, manifest_path)
    departments = {item["id"]: item for item in catalogue["departments"]}
    teams = {item["id"]: item for item in catalogue["teams"]}
    patterns = {item["id"]: item for item in catalogue["patterns"]}
    observed_at = str(manifest["capturedAt"])
    source_sha256 = str(manifest["capture"]["sha256"])
    imported: list[dict[str, Any]] = []

    for service in catalogue["services"]:
        source_id = str(service["id"])
        slug = service_slug(source_id)
        department = departments[str(service["departmentId"])]
        team = teams[str(service["teamId"])]
        service_url = source_page("service", source_id)
        provenance = okf.source_provenance(
            source="Wayfinder fictional service catalogue",
            source_url=service_url,
            source_tier=SOURCE_TIER,
            adapter=SOURCE_ADAPTER,
            confidence="source-captured",
            observed_at=observed_at,
            source_sha256=source_sha256,
            extra={
                "source_artifact": "sources/wayfinder/2026-09-24/catalogue.json",
                "source_record_type": "service",
                "source_record_id": source_id,
                "synthetic_demo": True,
                "authority": AUTHORITY_CLASS,
                "assertion_scope": ASSERTION_SCOPE,
                "rights": RIGHTS_STATUS,
            },
        )
        authentication = [str(value) for value in service.get("authentication", [])]
        service_protocols = protocols(service)
        first_relationship = len(builder.relationships)
        record = builder.add_record(
            slug=slug,
            title=str(service["name"]),
            record_type=record_type(str(service.get("type") or "")),
            publisher=f"wayfinder-demo-{okf.slugify(str(department['id']))}",
            publisher_title_value=f"{department['name']} (Wayfinder demo)",
            description=str(service.get("description") or ""),
            url=str(service.get("endpoint") or ""),
            documentation=str(service.get("documentation") or ""),
            topics=[],
            protocols=service_protocols or ["Synthetic demo"],
            tags=[
                *[str(value) for value in service.get("tags", [])],
                "wayfinder",
                "synthetic-demo",
                str(service.get("type") or "service"),
            ],
            timestamp=str(service.get("lastUpdated") or ""),
            modified=str(service.get("lastUpdated") or ""),
            license_id="not-specified",
            license_title="Rights not specified",
            license_source_id=service_url,
            license_confidence=0.0,
            license_basis="source-rights-not-specified",
            access_model=access_model(authentication),
            visibility="public-synthetic-demo",
            contract_status="placeholder-demo-contract",
            lifecycle="synthetic-demo-source-claim",
            source_tier=SOURCE_TIER,
            source_adapter=SOURCE_ADAPTER,
            confidence="source-captured",
            provenance=provenance,
            context_note=(
                "Fictional Wayfinder demonstration record. It is retained for "
                "comparison, is not a verified live government API and is not "
                "loaded in the default real-world relationship plane."
            ),
            extras={
                "wayfinder": {
                    "source_record": service,
                    "department": department,
                    "team": team,
                    "resolved_patterns": [
                        patterns[pattern_id]
                        for pattern_id in service.get("relatedPatterns", [])
                        if pattern_id in patterns
                    ],
                    "missing_pattern_ids": sorted(
                        pattern_id
                        for pattern_id in service.get("relatedPatterns", [])
                        if pattern_id not in patterns
                    ),
                    "source_page": service_url,
                },
                "synthetic_demo": True,
                "default_loaded": False,
                "authority": AUTHORITY_CLASS,
                "assertion_scope": ASSERTION_SCOPE,
                "rights": RIGHTS_STATUS,
                "source_claimed_status": service.get("status"),
                "source_claimed_authentication": authentication,
                "source_claimed_endpoint_placeholder": bool(service.get("endpoint")),
                "source_claimed_documentation_placeholder": bool(
                    service.get("documentation")
                ),
            },
            area_served="fictional UK government demo",
        )
        if record is None:
            raise ValueError(f"Wayfinder namespaced service slug collided: {slug}")
        record.update(
            {
                "id": f"urn:okf:synthetic:wayfinder:service:{source_id}",
                "synthetic_demo": True,
                "default_loaded": False,
                "assertion_scope": ASSERTION_SCOPE,
                "authority_class": AUTHORITY_CLASS,
                "rights_status": RIGHTS_STATUS,
                "assurance_status": "synthetic-demo-not-assessed",
                "environment": "synthetic-demo",
                "organisation_family": "synthetic demo",
                "source_record_id": source_id,
                "source_record_type": "service",
            }
        )
        record["extras"]["assurance_status"] = "synthetic-demo-not-assessed"
        record["extras"]["environment"] = "synthetic-demo"
        record["extras"]["organisation_family"] = "synthetic demo"
        for relationship in builder.relationships[first_relationship:]:
            relationship.update(synthetic_relationship_metadata(observed_at))
        imported.append(record)

        for dependency in service.get("dependsOn", []):
            builder.add_relationship(
                okf.record_route(slug),
                okf.record_route(service_slug(str(dependency))),
                "depends on",
                target_label=str(dependency),
                **synthetic_relationship_metadata(observed_at),
            )
        for pattern_id in service.get("relatedPatterns", []):
            builder.add_relationship(
                okf.record_route(slug),
                source_route("pattern", str(pattern_id)),
                "implements pattern",
                target_label=(
                    str(patterns[pattern_id]["name"])
                    if pattern_id in patterns
                    else str(pattern_id)
                ),
                **synthetic_relationship_metadata(observed_at),
            )
        builder.add_relationship(
            okf.record_route(slug),
            source_route("team", str(team["id"])),
            "maintained by",
            target_label=str(team["name"]),
            **synthetic_relationship_metadata(observed_at),
        )

    if len(imported) != 85:
        raise ValueError(f"imported {len(imported)} Wayfinder services, expected 85")
    return imported


def publisher_records(
    *,
    catalogue_path: Path,
    manifest_path: Path,
    record_counts: dict[str, int],
) -> list[dict[str, Any]]:
    """Return the six fictional departments as namespaced provider records."""

    catalogue, manifest = load_source(catalogue_path, manifest_path)
    observed_at = str(manifest["capturedAt"])
    source_sha256 = str(manifest["capture"]["sha256"])
    records: list[dict[str, Any]] = []
    for department in catalogue["departments"]:
        source_id = str(department["id"])
        identifier = f"wayfinder-demo-{okf.slugify(source_id)}"
        records.append(
            {
                "id": identifier,
                "name": identifier,
                "title": f"{department['name']} (Wayfinder demo)",
                "description": str(department.get("description") or ""),
                "dataset_count": int(record_counts.get(identifier, 0)),
                "resource_count": 0,
                "canonical_id": identifier,
                "canonical_title": f"{department['name']} (Wayfinder demo)",
                "concept_id": f"organisations/{identifier}.md",
                "route": f"publisher/{identifier}",
                "provenance": {
                    "source": "Wayfinder fictional department catalogue",
                    "source_url": f"{WAYFINDER_BASE}/",
                    "source_sha256": source_sha256,
                    "source_tier": SOURCE_TIER,
                    "source_adapter": SOURCE_ADAPTER,
                    "confidence": "source-captured",
                    "observed_at": observed_at,
                    "source_artifact": (
                        "sources/wayfinder/2026-09-24/catalogue.json"
                    ),
                    "source_record_type": "department",
                    "source_record_id": source_id,
                    "rights": RIGHTS_STATUS,
                },
                "state": "synthetic-demo-source-claim",
                "approval_status": "not-assessed",
                "type": "synthetic demo organisation",
                "synthetic_demo": True,
                "default_loaded": False,
                "assertion_scope": ASSERTION_SCOPE,
                "authority_class": AUTHORITY_CLASS,
                "rights_status": RIGHTS_STATUS,
                "source_record": department,
            }
        )
    return records
