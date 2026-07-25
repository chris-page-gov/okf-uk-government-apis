#!/usr/bin/env python3
"""Validate the independently published UK Government APIs OKF bundle."""

from __future__ import annotations

import gzip
import json
import re
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "bundle"
VALID_STATUS = {"draft", "stable", "deprecated"}
ACTOR_PATTERN = re.compile(
    r"^(?:human:[^\s:]+|process:[^\s:]+|[^\s/:]+/[^\s/]+)$"
)
GENERATED_PATTERN = re.compile(
    r"(?m)^generated:\s*\{\s*by:\s*([^,}]+),\s*at:\s*(.+?)\s*\}\s*$"
)


def load(path: Path):
    data = path.read_bytes()
    if path.suffix == ".gz":
        data = gzip.decompress(data)
    return json.loads(data)


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
        "checksums.json",
    ):
        if not (BUNDLE / required).is_file():
            errors.append(f"missing {required}")

    if descriptor.get("okf_version") != "0.2":
        errors.append("Explorer descriptor does not declare okf_version 0.2")
    if manifest.get("okf_version") != "0.2":
        errors.append("data manifest does not declare okf_version 0.2")
    for name, entrypoint in descriptor.get("entrypoints", {}).items():
        if "://" not in entrypoint and not (BUNDLE / entrypoint).is_file():
            errors.append(f"Explorer entrypoint is missing: {name} -> {entrypoint}")
    crosswalk = descriptor.get("extensions", {}).get(
        "okf-standards-crosswalk.v1", {}
    ).get("crosswalk")
    if crosswalk != "docs/okf-standards-crosswalk.md":
        errors.append("standards crosswalk extension is not bundle-root-relative")
    if analysis.get("standards_alignment", {}).get("crosswalk") != crosswalk:
        errors.append("analysis and descriptor standards crosswalks disagree")
    for semantic_name in ("okf-bundle.yamlld", "okf-bundle.jsonld"):
        if load(BUNDLE / semantic_name).get("okf_version") != "0.2":
            errors.append(f"{semantic_name} does not declare okf_version 0.2")

    relationships = sum(
        len(load(BUNDLE / path)) for path in manifest["chunks"]["relationships"]
    )
    if relationships != manifest["counts"]["relationships"]:
        errors.append("relationship count mismatch")
    adjacency = load(BUNDLE / manifest["indexes"]["relationship_adjacency"])
    if (
        adjacency.get("algorithm") != "fnv1a32-prefix-2"
        or adjacency.get("relationships") != relationships
    ):
        errors.append("adjacency mismatch")
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
        f"{concept_count:,} OKF v0.2 concepts"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
