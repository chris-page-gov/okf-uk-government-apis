#!/usr/bin/env python3
"""Compare the complete typed Markdown core with a pinned Explorer Reader import.

Run this checker in the pinned Explorer checkout's governed Python environment.
It copies only the bundle's Markdown source files into a temporary directory;
no assets are read or executed and no source API is contacted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "bundle"
REQUIRED_READER_COMMIT = "cce6e68d95c2946bb425effbaab48fbf04281a09"


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _copy_markdown_sources(destination: Path) -> dict[str, str]:
    """Copy every regular Markdown file and return its relative path/hash map."""
    hashes: dict[str, str] = {}
    for directory, subdirectories, filenames in os.walk(BUNDLE, followlinks=False):
        directory_path = Path(directory)
        if any((directory_path / name).is_symlink() for name in subdirectories):
            raise ValueError("the source bundle contains a symlinked directory")
        for filename in filenames:
            source = directory_path / filename
            if source.suffix != ".md":
                continue
            if source.is_symlink() or not source.is_file():
                raise ValueError("a Markdown source is not a regular file")
            relative = source.relative_to(BUNDLE)
            raw = source.read_bytes()
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            hashes[relative.as_posix()] = hashlib.sha256(raw).hexdigest()
    return hashes


def _frontmatter_view(producer_node: dict[str, Any], reader_node: dict[str, Any]) -> dict[str, Any]:
    reader_frontmatter = reader_node.get("frontmatter", {})
    return {key: producer_node[key] for key in reader_frontmatter if key in producer_node}


def check(consumer_root: Path) -> dict[str, Any]:
    consumer_root = consumer_root.resolve(strict=True)
    scripts = consumer_root / "scripts"
    if not (scripts / "check_okf_03_source.py").is_file():
        raise ValueError("the pinned Explorer source checker is missing")
    observed_commit = subprocess.run(
        ["git", "-C", str(consumer_root), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True, timeout=10,
    ).stdout.strip()
    dirty = subprocess.run(
        ["git", "-C", str(consumer_root), "status", "--porcelain"],
        capture_output=True, text=True, check=True, timeout=10,
    ).stdout
    if observed_commit != REQUIRED_READER_COMMIT or dirty:
        raise ValueError("the Explorer checkout must be clean at the reviewed pinned commit")

    sys.path.insert(0, str(scripts))
    from check_okf_03_source import inspect_bundle
    from okf_skill import verify_package, verify_runtime

    verify_runtime(consumer_root)
    verify_package()
    with tempfile.TemporaryDirectory(prefix="okf-api-core-reader-") as temporary:
        source_root = Path(temporary) / "bundle"
        source_root.mkdir()
        copied_hashes = _copy_markdown_sources(source_root)
        source_receipt, independent = inspect_bundle(source_root)
    if independent is None or not source_receipt.get("core_conformant"):
        raise ValueError("the independent Reader source check did not pass")
    if not source_receipt.get("declares_okf_0_3"):
        raise ValueError("the independent Reader did not observe core version 0.3")
    if source_receipt.get("explorer_import", {}).get("status") != "passed":
        raise ValueError("the independent Reader import did not pass")

    core_bytes = (BUNDLE / "okf-core-explorer.json").read_bytes()
    core = json.loads(core_bytes)
    producer_nodes = core.get("nodes", {})
    reader_nodes = independent.get("nodes", {})
    differences: list[dict[str, str]] = []
    if set(copied_hashes) != set(source_receipt.get("inspection", {}).get("markdown_sha256", {})):
        differences.append({"path": "<inventory>", "field": "source-file-set"})
    if copied_hashes != source_receipt.get("inspection", {}).get("markdown_sha256", {}):
        differences.append({"path": "<inventory>", "field": "source-file-sha256"})
    if set(producer_nodes) != set(reader_nodes):
        differences.append({"path": "<inventory>", "field": "typed-concept-set"})

    source_hash_differences = []
    for path in sorted(set(producer_nodes) & set(reader_nodes)):
        producer = producer_nodes[path]
        reader = reader_nodes[path]
        for field in ("body", "markdown_links", "markdown_references", "asset_links"):
            if producer.get(field) != reader.get(field):
                differences.append({"path": path, "field": field})
        if _frontmatter_view(producer, reader) != reader.get("frontmatter", {}):
            differences.append({"path": path, "field": "frontmatter"})
        if producer.get("source_path") != path:
            differences.append({"path": path, "field": "source-path"})
        if producer.get("source_sha256") != copied_hashes.get(path):
            source_hash_differences.append(path)
        if producer.get("source_bytes") != len((BUNDLE / path).read_bytes()):
            differences.append({"path": path, "field": "source-bytes"})

    producer_edges = {
        (row.get("source"), row.get("target"), tuple(row.get("source_fields", [])))
        for row in core.get("edges", [])
    }
    reader_edges = {
        (row.get("source"), row.get("target"), tuple(row.get("source_fields", [])))
        for row in independent.get("edges", [])
    }
    report = {
        "schema": "okf-uk-api-core-reader-parity.v1",
        "status": "passed" if not differences and not source_hash_differences and producer_edges == reader_edges else "failed",
        "consumer_commit": observed_commit,
        "consumer_clean": not bool(dirty),
        "source_check": source_receipt,
        "bundle_id": core.get("bundle_id"),
        "producer_core_projection_sha256": hashlib.sha256(core_bytes).hexdigest(),
        "source_markdown_files": len(copied_hashes),
        "typed_concepts": len(producer_nodes),
        "reader_concepts": len(reader_nodes),
        "reserved_navigation_files": len(source_receipt.get("reserved_navigation_paths", [])),
        "frontmatter_body_and_path_differences": len(differences),
        "first_differences": differences[:50],
        "source_sha256_differences": len(source_hash_differences),
        "producer_core_edges": len(producer_edges),
        "reader_core_edges": len(reader_edges),
        "missing_reader_edges": len(producer_edges - reader_edges),
        "unexpected_reader_edges": len(reader_edges - producer_edges),
        "parity_checker_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--consumer-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = check(args.consumer_root)
    payload = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "source_check"}, indent=2, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
