#!/usr/bin/env python3
"""Confirm the complete migrated relationship source chunks are byte-identical."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASELINE = "de7317cbdada318f1719064ef0afcdb1c6df4905"
RELATIONSHIP_PATH = re.compile(r"^bundle/data/relationships-\d+\.json\.gz$")
IDENTITY_PATHS = {
    "bundle/data/graph.json",
    "bundle/data/predicate-registry.json",
}
EXPECTED_RELATIONSHIP_CHUNKS = 140


def check() -> dict[str, Any]:
    listing = subprocess.run(
        ["git", "-C", str(ROOT), "ls-tree", "-r", "-z", BASELINE, "--", "bundle/data"],
        capture_output=True, check=True, timeout=30,
    ).stdout
    baseline_blobs: dict[str, str] = {}
    for entry in listing.split(b"\0"):
        if not entry:
            continue
        header, raw_path = entry.split(b"\t", 1)
        mode, kind, object_id = header.decode("ascii").split()
        relative = raw_path.decode("utf-8")
        if kind == "blob" and (RELATIONSHIP_PATH.fullmatch(relative) or relative in IDENTITY_PATHS):
            baseline_blobs[relative] = object_id
    relationships = sorted(path for path in baseline_blobs if RELATIONSHIP_PATH.fullmatch(path))
    if len(relationships) != EXPECTED_RELATIONSHIP_CHUNKS:
        raise ValueError(f"baseline relationship chunk inventory changed: {len(relationships)}")
    if not IDENTITY_PATHS.issubset(baseline_blobs):
        raise ValueError("baseline direct graph identity files are incomplete")

    entries = []
    row_count = 0
    total_bytes = 0
    for relative in sorted(baseline_blobs):
        path = ROOT / relative
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"candidate graph identity input is missing or unsafe: {relative}")
        raw = path.read_bytes()
        blob_id = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
        if blob_id != baseline_blobs[relative]:
            raise ValueError(f"frozen graph identity input differs from source baseline: {relative}")
        total_bytes += len(raw)
        entry = {"path": relative, "git_blob": blob_id, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
        if RELATIONSHIP_PATH.fullmatch(relative):
            rows = json.loads(gzip.decompress(raw))
            if not isinstance(rows, list):
                raise ValueError(f"relationship chunk is not a JSON array: {relative}")
            entry["relationships"] = len(rows)
            row_count += len(rows)
        entries.append(entry)
    if row_count != 278_156:
        raise ValueError(f"frozen relationship population differs: {row_count}")
    return {
        "schema": "okf-uk-api-frozen-graph-identity.v1",
        "status": "passed",
        "baseline_commit": BASELINE,
        "candidate_head": subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True, timeout=10,
        ).stdout.strip(),
        "relationship_chunks": len(relationships),
        "relationships": row_count,
        "direct_graph_identity_files": sorted(IDENTITY_PATHS),
        "files_byte_identical_to_baseline": len(entries),
        "verified_file_bytes": total_bytes,
        "identity_files": entries,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = check()
    payload = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "identity_files"}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
