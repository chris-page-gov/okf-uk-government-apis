#!/usr/bin/env python3
"""Prepare the reviewable Wayfinder source snapshot without network access.

The inputs are a separately captured public export, its capture manifest and a
reconciliation report.  This command verifies the immutable capture before it
writes repository-relative, public-safe provenance artefacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


EXPECTED_CAPTURE_SHA256 = (
    "d15d6c8bfe9490855894aeaa1b1f82a52277737c584a2bc9944a9a906d267969"
)
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
PUBLIC_CAPTURE_PATH = "sources/wayfinder/2026-09-24/catalogue.json"


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_capture(capture_bytes: bytes, capture: dict[str, Any]) -> None:
    digest = sha256_bytes(capture_bytes)
    if digest != EXPECTED_CAPTURE_SHA256:
        raise ValueError(
            f"Wayfinder capture SHA-256 is {digest}, expected {EXPECTED_CAPTURE_SHA256}"
        )
    actual_counts = {key: len(capture.get(key, [])) for key in EXPECTED_COUNTS}
    if actual_counts != EXPECTED_COUNTS:
        raise ValueError(
            f"Wayfinder capture counts are {actual_counts!r}, expected {EXPECTED_COUNTS!r}"
        )
    if sum(actual_counts.values()) != 311:
        raise ValueError("Wayfinder capture must contain exactly 311 exported records")


def public_manifest(
    manifest: dict[str, Any], capture_bytes: bytes
) -> dict[str, Any]:
    result = json.loads(json.dumps(manifest))
    capture = result.setdefault("capture", {})
    capture["path"] = "catalogue.json"
    capture["sha256"] = sha256_bytes(capture_bytes)
    capture["bytes"] = len(capture_bytes)

    result["rights"] = {
        "status": "not specified",
        "reusableLicenceFound": False,
        "finding": (
            "No explicit reusable licence or rights statement was located on the "
            "public site. The footer's licence link points to a page fragment."
        ),
        "documentationDecision": (
            "Document the exported records as an explicitly fictional synthetic "
            "comparison source. Keep record-level rights as not specified and do "
            "not imply a reuse licence, government authority or live-service assurance."
        ),
    }
    result["authorAttribution"] = {
        "name": "Paul Buchanan-Jones",
        "source": (
            "Private correspondence supplied to the maintainers; contact details "
            "and message text are retained offline and excluded from publication."
        ),
    }
    result["admission"] = {
        "mode": "synthetic-fixture-opt-in",
        "authority": "synthetic",
        "assertionScope": "synthetic-fixture",
        "defaultLoaded": False,
        "rights": "not specified",
        "realApiAdmissionCount": 0,
        "note": (
            "The records are retained for comparison and modelling. They are not "
            "verified descriptions of live UK government services."
        ),
    }
    return result


def public_reconciliation(report: dict[str, Any]) -> dict[str, Any]:
    result = json.loads(json.dumps(report))
    scope = result.setdefault("scope", {})
    wayfinder_scope = scope.setdefault("wayfinderCapture", {})
    wayfinder_scope["path"] = PUBLIC_CAPTURE_PATH
    okf_scope = scope.setdefault("okfBundle", {})
    okf_scope["manifestPath"] = "bundle/data/manifest.json"
    okf_scope["checksumsPath"] = "bundle/checksums.json"
    quality = result.setdefault("sourceDataQuality", {})
    quality["admissionDecision"] = (
        "Admit as an opt-in synthetic comparison layer with rights not specified. "
        "Do not admit as real or authoritative API records: the publication is an "
        "explicitly fictional demo and its endpoint and documentation URLs are placeholders."
    )
    result["publicationDecision"] = {
        "mode": "synthetic-fixture-opt-in",
        "rights": "not specified",
        "defaultLoaded": False,
        "exactMatches": 0,
        "newSyntheticServices": 85,
        "fuzzyTitleMatchesMerged": 0,
    }
    return result


def write_snapshot(
    *,
    capture_path: Path,
    manifest_path: Path,
    reconciliation_path: Path,
    output: Path,
) -> None:
    capture_bytes = capture_path.read_bytes()
    capture = json.loads(capture_bytes)
    validate_capture(capture_bytes, capture)
    manifest = public_manifest(load_json(manifest_path), capture_bytes)
    reconciliation = public_reconciliation(load_json(reconciliation_path))

    output.mkdir(parents=True, exist_ok=True)
    (output / "catalogue.json").write_bytes(capture_bytes)
    (output / "manifest.json").write_text(
        canonical_json(manifest), encoding="utf-8"
    )
    (output / "reconciliation.json").write_text(
        canonical_json(reconciliation), encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--reconciliation", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("sources/wayfinder/2026-09-24"),
    )
    args = parser.parse_args(argv)
    write_snapshot(
        capture_path=args.capture,
        manifest_path=args.manifest,
        reconciliation_path=args.reconciliation,
        output=args.output,
    )
    print(f"wrote verified Wayfinder snapshot to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
