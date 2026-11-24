#!/usr/bin/env python3
"""Check the local OKF publication contract and documentation lockstep."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "okf.publication.json"
SEMANTIC_PROFILE = "https://chris-page-gov.github.io/okf-explorer/profile/bundle-wiki/v2/"
REQUIRED_TOP_LEVEL = {
    "schema",
    "modified",
    "locale",
    "time_zone",
    "repository",
    "semantic_contract",
    "source_families",
    "boundaries",
    "planes",
    "tooling",
    "lockstep",
    "ci",
    "publication",
    "verification",
    "limitations",
}
IDENTIFIER = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
SHELL_CONTROL = re.compile(r"&&|\|\||[;`]|\$\(|[\r\n]")


def load_contract(path: Path = CONTRACT) -> dict[str, Any]:
    """Load strict JSON and reject duplicate keys."""

    def object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise ValueError(f"duplicate JSON key: {key}")
            value[key] = item
        return value

    document = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=object_pairs)
    if not isinstance(document, dict):
        raise ValueError("publication contract root must be an object")
    return document


def _ids(rows: object, label: str, errors: list[str]) -> set[str]:
    if not isinstance(rows, list):
        errors.append(f"{label} must be an array")
        return set()
    values: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"{label}[{index}] must be an object")
            continue
        identifier = row.get("id")
        if not isinstance(identifier, str) or not IDENTIFIER.fullmatch(identifier):
            errors.append(f"{label}[{index}] has an invalid id")
        elif identifier in values:
            errors.append(f"{label} duplicates id {identifier}")
        else:
            values.add(identifier)
    return values


def _command_references(document: dict[str, Any]) -> list[tuple[str, object]]:
    references: list[tuple[str, object]] = []
    for family in document.get("source_families", []):
        if isinstance(family, dict):
            references.append(
                (
                    f"source family {family.get('id')}",
                    (family.get("extraction") or {}).get("command_ids", []),
                )
            )
    boundaries = document.get("boundaries") or {}
    for boundary in boundaries.get("generated", []):
        if isinstance(boundary, dict):
            references.extend(
                (
                    (f"generated boundary {boundary.get('path')} build", boundary.get("build_command_ids", [])),
                    (f"generated boundary {boundary.get('path')} check", boundary.get("check_command_ids", [])),
                )
            )
    for plane in document.get("planes", []):
        if isinstance(plane, dict):
            references.append((f"plane {plane.get('id')}", plane.get("command_ids", [])))
    lockstep = document.get("lockstep") or {}
    references.append(("lockstep", [lockstep.get("check_command_id")]))
    browser = (document.get("ci") or {}).get("browser") or {}
    for policy_name in ("ordinary", "cross_engine"):
        policy = browser.get(policy_name) or {}
        references.append((f"CI browser {policy_name}", policy.get("command_ids", [])))
        installation = policy.get("installation") or {}
        references.append(
            (f"CI browser {policy_name} installation", installation.get("command_ids", []))
        )
    references.append(
        ("verification", (document.get("verification") or {}).get("command_ids", []))
    )
    return references


def validate_contract(document: dict[str, Any]) -> list[str]:
    """Return local structural and cross-reference errors."""

    errors: list[str] = []
    semantic_path = ROOT / "okf.semantic.json"
    semantic_schema_path = ROOT / "profiles/bundle-wiki/v2/repository-contract.schema.json"
    if semantic_path.is_file() and semantic_schema_path.is_file():
        semantic_contract = json.loads(semantic_path.read_text(encoding="utf-8"))
        semantic_schema = json.loads(semantic_schema_path.read_text(encoding="utf-8"))
        for error in Draft202012Validator(semantic_schema).iter_errors(semantic_contract):
            instance_path = "/".join(str(part) for part in error.absolute_path) or "<root>"
            errors.append(f"OKF 0.3 semantic contract schema violation at {instance_path}: {error.message}")
    else:
        errors.append("OKF 0.3 semantic contract or pinned v2 schema is missing")
    errors.extend(profile_lock_errors())
    missing = sorted(REQUIRED_TOP_LEVEL - set(document))
    extra = sorted(set(document) - REQUIRED_TOP_LEVEL)
    if missing:
        errors.append("missing top-level fields: " + ", ".join(missing))
    if extra:
        errors.append("unknown top-level fields: " + ", ".join(extra))
    if document.get("schema") != "okf-repository-publication-contract.v1":
        errors.append("schema must be okf-repository-publication-contract.v1")
    if document.get("locale") != "en-GB":
        errors.append("locale must be en-GB")
    if document.get("time_zone") != "Europe/London":
        errors.append("time_zone must be Europe/London")

    repository = document.get("repository") or {}
    semantic = document.get("semantic_contract") or {}
    for label, value in (
        ("repository.root_index", repository.get("root_index")),
        ("semantic_contract.path", semantic.get("path")),
    ):
        if not isinstance(value, str) or not (ROOT / value).is_file():
            errors.append(f"{label} must name an existing file")
    if semantic.get("profile") != SEMANTIC_PROFILE:
        errors.append("semantic_contract.profile must name Bundle Wiki v2")

    source_ids = _ids(document.get("source_families"), "source_families", errors)
    plane_ids = _ids(document.get("planes"), "planes", errors)
    commands = (document.get("tooling") or {}).get("commands")
    command_ids = _ids(commands, "tooling.commands", errors)
    for command in commands if isinstance(commands, list) else []:
        if not isinstance(command, dict):
            continue
        value = command.get("command")
        if not isinstance(value, str) or not value.strip():
            errors.append(f"command {command.get('id')} has no command string")
        elif SHELL_CONTROL.search(value):
            errors.append(f"command {command.get('id')} contains shell control syntax")
        source = command.get("source")
        if not isinstance(source, str) or not (ROOT / source).is_file():
            errors.append(f"command {command.get('id')} has no existing guidance source")
        if command.get("review_status") != "reviewed-local-guidance":
            errors.append(f"command {command.get('id')} is not reviewed local guidance")

    boundaries = document.get("boundaries") or {}
    for boundary in boundaries.get("authored", []):
        if isinstance(boundary, dict) and boundary.get("source_family_id") not in (
            None,
            *source_ids,
        ):
            errors.append(
                f"authored boundary {boundary.get('path')} references an unknown source family"
            )
    for plane in document.get("planes", []):
        if not isinstance(plane, dict):
            continue
        for dependency in plane.get("depends_on", []):
            if dependency not in plane_ids:
                errors.append(f"plane {plane.get('id')} depends on unknown plane {dependency}")
    for label, values in _command_references(document):
        if not isinstance(values, list):
            errors.append(f"{label} command_ids must be an array")
            continue
        for command_id in values:
            if command_id not in command_ids:
                errors.append(f"{label} references unknown command {command_id}")

    lockstep = document.get("lockstep") or {}
    if lockstep.get("changelog_path") != "CHANGELOG.md":
        errors.append("lockstep changelog_path must be CHANGELOG.md")
    if lockstep.get("dependency_update_policy") != (
        "assess-release-bound-bytes-no-blanket-exemption"
    ):
        errors.append("lockstep dependency update policy is not fail-closed")
    if lockstep.get("unknown_path_policy") != "fail-closed":
        errors.append("lockstep unknown path policy must fail closed")
    documentation_paths = set(lockstep.get("documentation_paths", []))
    for required in ("README.md", "AGENTS.md", "CHANGELOG.md"):
        if required not in documentation_paths:
            errors.append(f"lockstep documentation paths omit {required}")

    ci = document.get("ci") or {}
    ordinary_browser = (ci.get("browser") or {}).get("ordinary") or {}
    if ordinary_browser.get("policy") != "required":
        errors.append("CI must require the canonical Reader browser acceptance")
    if ordinary_browser.get("engines") != ["chromium"]:
        errors.append("CI Reader browser acceptance must name the canonical Chromium engine")
    verification = document.get("verification") or {}
    if verification.get("required") is not True:
        errors.append("publication verification must be required")
    if verification.get("browser") != "required":
        errors.append("publication verification must require browser journeys")
    expected_journeys = {"core-guide-to-reader", "metadata-guide-to-reader"}
    journeys = verification.get("journeys")
    journey_ids = {
        row.get("id") for row in journeys if isinstance(row, dict)
    } if isinstance(journeys, list) else set()
    if not expected_journeys.issubset(journey_ids):
        errors.append("publication verification must include separate core and metadata guide journeys")
    expected_reader_commands = {
        "reader-core-acceptance",
        "reader-metadata-acceptance",
        "walkthrough-browser-acceptance",
    }
    verification_commands = set(verification.get("command_ids", []))
    if not expected_reader_commands.issubset(verification_commands):
        errors.append("publication verification must require both Reader manifests and the guide-to-Reader browser gate")
    browser_commands = set(ordinary_browser.get("command_ids", []))
    if not expected_reader_commands.issubset(browser_commands):
        errors.append("ordinary browser CI must require the descriptor manifests and guide-to-Reader gate")
    for workflow in ci.get("workflow_paths", []):
        if not isinstance(workflow, str) or not (ROOT / workflow).is_file():
            errors.append(f"CI workflow path does not exist: {workflow}")
    publication = document.get("publication") or {}
    if publication.get("candidate_policy") != "promote-exact-assured-bytes-without-rebuild":
        errors.append("publication candidate policy must prohibit rebuilds")
    for target in publication.get("targets", []):
        if not isinstance(target, dict):
            continue
        if target.get("exact_commit_required") is not True:
            errors.append(f"publication target {target.get('id')} does not require an exact commit")
        if target.get("promote_without_rebuild") is not True:
            errors.append(f"publication target {target.get('id')} permits a rebuild")
    return sorted(set(errors))


def profile_lock_errors() -> list[str]:
    """Check frozen v1 and active v2 profile mirrors against their locks."""
    errors: list[str] = []
    for version in ("v1", "v2"):
        profile_root = ROOT / "profiles" / "bundle-wiki" / version
        lock_path = ROOT / "profiles" / "bundle-wiki" / f"{version}.vendor-lock.json"
        try:
            lock = json.loads(lock_path.read_text(encoding="utf-8"))
            entries = lock["files"]
            listed = {row["path"] for row in entries}
            actual = {path.relative_to(profile_root).as_posix() for path in profile_root.rglob("*") if path.is_file() and not path.is_symlink()}
            if actual != listed:
                errors.append(f"{version} profile files differ from the vendor lock")
            canonical = bytearray()
            for row in sorted(entries, key=lambda item: item["path"]):
                path = profile_root / row["path"]
                content = path.read_bytes()
                digest = hashlib.sha256(content).hexdigest()
                if len(content) != row["bytes"] or digest != row["sha256"]:
                    errors.append(f"{version} profile file differs from the vendor lock: {row['path']}")
                canonical.extend(f"{row['path']}\t{row['bytes']}\t{row['sha256']}\n".encode("utf-8"))
            digest = hashlib.sha256(canonical).hexdigest()
            if lock.get("identity", {}).get("sha256") != digest:
                errors.append(f"{version} profile vendor-lock aggregate identity is invalid")
            if lock.get("profile") != f"https://chris-page-gov.github.io/okf-explorer/profile/bundle-wiki/{version}/":
                errors.append(f"{version} profile vendor lock has the wrong canonical URI")
        except (OSError, KeyError, TypeError, ValueError) as exc:
            errors.append(f"{version} profile vendor lock cannot be verified: {exc}")
    return errors


def _matches(path: str, patterns: object) -> bool:
    return isinstance(patterns, list) and any(
        isinstance(pattern, str) and fnmatch.fnmatchcase(path, pattern)
        for pattern in patterns
    )


def lockstep_errors(document: dict[str, Any], changed_paths: list[str]) -> list[str]:
    """Require human guidance and the changelog with controlled changes."""

    lockstep = document["lockstep"]
    if not any(_matches(path, lockstep["controlled_paths"]) for path in changed_paths):
        return []
    changelog = lockstep["changelog_path"]
    documentation_patterns = [
        pattern
        for pattern in lockstep["documentation_paths"]
        if pattern != changelog
    ]
    errors: list[str] = []
    if changelog not in changed_paths:
        errors.append("controlled changes require CHANGELOG.md in the same change set")
    if not any(_matches(path, documentation_patterns) for path in changed_paths):
        errors.append("controlled changes require README.md or AGENTS.md guidance in lockstep")
    return errors


def event_base_sha() -> str | None:
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        return None
    event = json.loads(Path(event_path).read_text(encoding="utf-8"))
    candidate = (event.get("pull_request") or {}).get("base", {}).get("sha")
    if not candidate:
        candidate = event.get("before")
    if isinstance(candidate, str) and FULL_SHA.fullmatch(candidate) and set(candidate) != {"0"}:
        return candidate
    return None


def git_changed_paths(base_sha: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base_sha}...HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return sorted(path for path in result.stdout.splitlines() if path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-ref", help="Git commit used for lockstep comparison")
    parser.add_argument(
        "--changed-path",
        action="append",
        default=[],
        help="Explicit changed path for a local lockstep probe",
    )
    args = parser.parse_args(argv)
    try:
        document = load_contract()
        errors = validate_contract(document)
        base_sha = args.base_ref or event_base_sha()
        changed_paths = args.changed_path or (
            git_changed_paths(base_sha) if base_sha else []
        )
        errors.extend(lockstep_errors(document, changed_paths))
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"publication contract check failed: {exc}")
        return 1
    if errors:
        print("publication contract check failed:")
        for error in sorted(set(errors)):
            print(f"- {error}")
        return 1
    suffix = f"; {len(changed_paths)} changed paths checked" if changed_paths else ""
    print(f"publication contract and documentation lockstep passed{suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
