from __future__ import annotations

import copy
import gzip
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "uk_government_api_okf"


def load_script(name: str, path: Path):
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


builder = load_script(
    "build_uk_government_api_okf",
    ROOT / "scripts" / "build_uk_government_api_okf.py",
)
checker = load_script("check_bundle", ROOT / "scripts" / "check_bundle.py")


def fixture_corpus():
    csv_bytes = (FIXTURES / "api_catalogue.csv").read_bytes()
    source_hash, rows = builder.rows_from_csv("file://api_catalogue.csv", csv_bytes)
    ckan = json.loads(
        (FIXTURES / "ckan_package_search.json").read_text(encoding="utf-8")
    )
    os_documents = json.loads(
        (FIXTURES / "os_api_tree.json").read_text(encoding="utf-8")
    )
    ons = json.loads((FIXTURES / "ons_payload.json").read_text(encoding="utf-8"))
    return builder.build_corpus(
        rows,
        "file://api_catalogue.csv",
        source_hash,
        ckan_packages=ckan["result"]["results"],
        ckan_source_url="file://ckan_package_search.json",
        os_documents=os_documents,
        ons_root=ons["root"],
        ons_datasets=ons["datasets"],
        ons_topics=ons["topics"],
        ons_code_lists=ons["code_lists"],
        generated_at="2026-07-25T12:00:00Z",
    )


def runtime_rows(files: dict[Path, str | bytes], runtime: dict) -> list[dict]:
    rows: list[dict] = []
    for plane in runtime["planes"]:
        for chunk in plane["chunks"]:
            value = files[Path(chunk["path"])]
            assert isinstance(value, bytes)
            rows.extend(json.loads(gzip.decompress(value)))
    return rows


def write_runtime_files(root: Path, files: dict[Path, str | bytes]) -> None:
    for relative, content in files.items():
        if not (
            relative.as_posix().startswith("data/relationship-runtime/")
            or relative.as_posix().startswith("schemas/")
        ):
            continue
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            target.write_bytes(content)
        else:
            target.write_text(content, encoding="utf-8")


class RelationshipRuntimeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = fixture_corpus()

    def test_material_runtime_is_bounded_without_truncating_full_planes(self):
        corpus = copy.deepcopy(self.corpus)
        files = builder.output_files(corpus)
        runtime = json.loads(files[Path(builder.RELATIONSHIP_RUNTIME_MANIFEST)])
        rows = runtime_rows(files, runtime)
        expected = {
            row["id"]
            for row in corpus["relationships"]
            if row["label"] in builder.MATERIAL_RELATIONSHIP_LABELS
        }

        self.assertEqual({row["assertion_id"] for row in rows}, expected)
        self.assertTrue(
            all(row["label"] in builder.MATERIAL_RELATIONSHIP_LABELS for row in rows)
        )
        self.assertEqual(
            sum(len(chunk_rows) for _, chunk_rows in corpus["relationship_chunks"]),
            len(corpus["relationships"]),
        )
        self.assertGreater(len(corpus["relationships"]), len(rows))
        relationships_by_id = {row["id"]: row for row in corpus["relationships"]}
        for row in rows:
            source = relationships_by_id[row["assertion_id"]]
            for field in (
                "source_adapter",
                "source_tier",
                "source_confidence",
                "license_id",
                "license_title",
                "license_basis",
                "license_confidence",
            ):
                self.assertEqual(row[field], source[field])
            projected = builder.rich_runtime_reader_projection(row)
            for field in (
                "source_adapter",
                "source_tier",
                "source_confidence",
                "license_id",
                "license_title",
                "license_basis",
                "license_confidence",
            ):
                self.assertEqual(projected[field], source[field])
            self.assertEqual(
                projected["evidence"][0]["source_licence"],
                source["evidence"][0]["source_licence"],
            )
            self.assertEqual(
                projected["rights"]["source_licence"],
                source["rights"]["source_licence"],
            )
        receipt = json.loads(
            files[Path("data/semantic/validation-report.json")]
        )["semantic_assertion_validation"]
        self.assertEqual(receipt["runtime_relationships_checked"], len(corpus["relationships"]))
        self.assertEqual(receipt["semantic_assertions_checked"], len(corpus["relationships"]))
        self.assertEqual(receipt["violation_count"], 0)

    def test_runtime_and_route_locator_are_deterministic_and_replay(self):
        relationships = self.corpus["relationships"]
        first, reference = builder.rich_relationship_runtime_outputs(
            relationships,
            generated_at="2026-07-25T12:00:00Z",
            snapshot="2026-07-25T12:00:00Z",
        )
        second, second_reference = builder.rich_relationship_runtime_outputs(
            relationships,
            generated_at="2026-07-25T12:00:00Z",
            snapshot="2026-07-25T12:00:00Z",
        )
        self.assertEqual(first, second)
        self.assertEqual(reference, second_reference)

        descriptor = {
            "snapshot": "2026-07-25T12:00:00Z",
            "entrypoints": {"relationship_runtime": reference},
            "entrypoint_integrity": {"relationship_runtime": reference},
        }
        manifest = {
            "snapshot": "2026-07-25T12:00:00Z",
            "indexes": {
                "relationship_runtime": reference,
                "semantic_graph": "data/semantic/manifest.json",
            },
        }
        expected_material = {
            row["id"]: checker.projection_digest(row)
            for row in relationships
            if row["label"] in builder.MATERIAL_RELATIONSHIP_LABELS
        }
        with tempfile.TemporaryDirectory() as directory:
            bundle = Path(directory)
            write_runtime_files(bundle, first)
            self.assertEqual(
                checker.validate_relationship_runtime(
                    bundle, descriptor, manifest, expected_material
                ),
                [],
            )
            runtime = json.loads(first[Path(builder.RELATIONSHIP_RUNTIME_MANIFEST)])
            locator = json.loads(first[Path(builder.RELATIONSHIP_RUNTIME_LOCATOR)])
            bucket_path = Path(locator["buckets"][0]["path"])
            (bundle / bucket_path).write_bytes((bundle / bucket_path).read_bytes() + b"x")
            errors = checker.validate_relationship_runtime(
                bundle, descriptor, manifest, expected_material
            )
            self.assertTrue(errors)
            self.assertIn("digest commitment", errors[0])
            self.assertEqual(
                runtime["route_locator"]["sha256"],
                builder.sha256_bytes(
                    first[Path(builder.RELATIONSHIP_RUNTIME_LOCATOR)].encode("utf-8")
                ),
            )

    def test_projection_digest_binds_rdf_identity_and_governed_fields(self):
        relationship = copy.deepcopy(
            next(
                row
                for row in self.corpus["relationships"]
                if row["label"] in builder.MATERIAL_RELATIONSHIP_LABELS
            )
        )
        semantic = builder.semantic_assertion_node(relationship)
        expected = checker.projection_digest(relationship)
        self.assertEqual(expected, checker.projection_digest(semantic, semantic=True))

        mutations = {
            "source_iri": "https://example.invalid/source",
            "target_iri": "https://example.invalid/target",
            "kind": "different governed kind",
            "review_status": "changed",
            "stale_after": "2027-01-01T00:00:00Z",
            "support_profile": "different-profile",
            "strength": 0.1,
            "count": 99,
            "official_legal_classification": True,
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                changed = copy.deepcopy(relationship)
                changed[field] = value
                self.assertNotEqual(expected, checker.projection_digest(changed))

        for field in ("source", "target"):
            with self.subTest(semantic_iri=field):
                changed = copy.deepcopy(semantic)
                changed[field]["@id"] = f"https://example.invalid/{field}"
                self.assertNotEqual(
                    expected, checker.projection_digest(changed, semantic=True)
                )

    def test_runtime_replay_rejects_a_rehashed_wrong_source_iri(self):
        relationships = self.corpus["relationships"]
        outputs, reference = builder.rich_relationship_runtime_outputs(
            relationships,
            generated_at="2026-07-25T12:00:00Z",
            snapshot="fixture",
        )
        runtime_path = Path(builder.RELATIONSHIP_RUNTIME_MANIFEST)
        runtime = json.loads(outputs[runtime_path])
        chunk = runtime["planes"][0]["chunks"][0]
        chunk_path = Path(chunk["path"])
        rows = json.loads(gzip.decompress(outputs[chunk_path]))
        rows[0]["source_iri"] = "https://example.invalid/wrong-source"
        compressed = builder.gzip_json(rows)
        outputs[chunk_path] = compressed
        chunk["bytes"] = len(compressed)
        chunk["sha256"] = builder.sha256_bytes(compressed)
        runtime_text = builder.render_json(runtime)
        outputs[runtime_path] = runtime_text
        reference = {
            "path": builder.RELATIONSHIP_RUNTIME_MANIFEST,
            "sha256": builder.sha256_bytes(runtime_text.encode("utf-8")),
            "bytes": len(runtime_text.encode("utf-8")),
        }
        descriptor = {
            "snapshot": "fixture",
            "entrypoints": {"relationship_runtime": reference},
            "entrypoint_integrity": {"relationship_runtime": reference},
        }
        manifest = {
            "snapshot": "fixture",
            "indexes": {
                "relationship_runtime": reference,
                "semantic_graph": "data/semantic/manifest.json",
            },
        }
        expected_material = {
            row["id"]: checker.projection_digest(row)
            for row in relationships
            if row["label"] in builder.MATERIAL_RELATIONSHIP_LABELS
        }
        with tempfile.TemporaryDirectory() as directory:
            bundle = Path(directory)
            write_runtime_files(bundle, outputs)
            errors = checker.validate_relationship_runtime(
                bundle, descriptor, manifest, expected_material
            )
        self.assertTrue(errors)
        self.assertIn("material runtime differs", errors[0])

    def test_decoded_runtime_resources_are_bounded_before_json_parsing(self):
        self.assertEqual(
            builder.MAX_RICH_RUNTIME_DECODED_CHUNK_BYTES,
            64 * 1024 * 1024,
        )
        relationship = next(
            row
            for row in self.corpus["relationships"]
            if row["label"] in builder.MATERIAL_RELATIONSHIP_LABELS
        )
        with patch.object(builder, "MAX_RICH_RUNTIME_DECODED_CHUNK_BYTES", 1):
            with self.assertRaisesRegex(ValueError, "decoded-byte limit"):
                builder.rich_relationship_runtime_outputs(
                    [relationship],
                    generated_at="2026-07-25T12:00:00Z",
                    snapshot="fixture",
                )

        compressed = builder.deterministic_gzip(b'{"padding":"' + (b"x" * 128) + b'"}')
        with patch.object(builder, "MAX_RICH_RUNTIME_DECODED_CHUNK_BYTES", 32):
            with self.assertRaisesRegex(
                checker.RelationshipRuntimeError, "decoded-byte ceiling"
            ):
                checker._bounded_gzip_json(compressed, "locator bucket fixture")

    def test_reader_parity_rejects_duplicate_evidence_excess_support_and_bad_routes(self):
        relationship = copy.deepcopy(
            next(
                row
                for row in self.corpus["relationships"]
                if row["label"] in builder.MATERIAL_RELATIONSHIP_LABELS
            )
        )
        duplicate = copy.deepcopy(relationship["evidence"][0])
        duplicate["rationale"] = "Same identity with different payload"
        relationship["evidence"].append(duplicate)
        with self.assertRaisesRegex(ValueError, "repeats an evidence identity"):
            builder.rich_relationship_runtime_outputs(
                [relationship],
                generated_at="2026-07-25T12:00:00Z",
                snapshot="fixture",
            )
        errors: list[str] = []
        checker.validate_relationship(relationship, errors, "duplicate fixture")
        self.assertTrue(any("repeats an evidence identity" in error for error in errors))

        inferred = copy.deepcopy(
            next(
                row
                for row in self.corpus["relationships"]
                if row["assertion_status"] == "inferred"
                and row["label"] in builder.MATERIAL_RELATIONSHIP_LABELS
            )
        )
        inferred["supporting_assertions"] = [
            f"https://example.invalid/assertion/{index}"
            for index in range(builder.MAX_RICH_RUNTIME_SUPPORTING_ASSERTIONS + 1)
        ]
        with self.assertRaises(ValueError):
            builder.rich_relationship_runtime_outputs(
                [inferred],
                generated_at="2026-07-25T12:00:00Z",
                snapshot="fixture",
            )
        errors = []
        checker.validate_relationship(inferred, errors, "support fixture")
        self.assertTrue(
            any("supporting-assertion ceiling" in error for error in errors)
        )

        self.assertTrue(builder.safe_runtime_route("dataset/example-1"))
        for route in (
            "Dataset/example",
            "dataset",
            "dataset//example",
            "dataset/../example",
            "dataset/example?x=1",
        ):
            with self.subTest(route=route):
                self.assertFalse(builder.safe_runtime_route(route))

    def test_runtime_replay_rejects_duplicate_chunk_identities(self):
        relationships = self.corpus["relationships"]
        outputs, _reference = builder.rich_relationship_runtime_outputs(
            relationships,
            generated_at="2026-07-25T12:00:00Z",
            snapshot="fixture",
        )
        runtime_path = Path(builder.RELATIONSHIP_RUNTIME_MANIFEST)
        runtime = json.loads(outputs[runtime_path])
        chunks = [chunk for plane in runtime["planes"] for chunk in plane["chunks"]]
        self.assertGreaterEqual(len(chunks), 2)
        chunks[1]["id"] = chunks[0]["id"]
        runtime_text = builder.render_json(runtime)
        outputs[runtime_path] = runtime_text
        reference = {
            "path": builder.RELATIONSHIP_RUNTIME_MANIFEST,
            "sha256": builder.sha256_bytes(runtime_text.encode("utf-8")),
            "bytes": len(runtime_text.encode("utf-8")),
        }
        descriptor = {
            "snapshot": "fixture",
            "entrypoints": {"relationship_runtime": reference},
            "entrypoint_integrity": {"relationship_runtime": reference},
        }
        manifest = {
            "snapshot": "fixture",
            "indexes": {
                "relationship_runtime": reference,
                "semantic_graph": "data/semantic/manifest.json",
            },
        }
        expected_material = {
            row["id"]: checker.projection_digest(row)
            for row in relationships
            if row["label"] in builder.MATERIAL_RELATIONSHIP_LABELS
        }
        with tempfile.TemporaryDirectory() as directory:
            bundle = Path(directory)
            write_runtime_files(bundle, outputs)
            errors = checker.validate_relationship_runtime(
                bundle, descriptor, manifest, expected_material
            )
        self.assertTrue(errors)
        self.assertIn("repeats a chunk identity", errors[0])

    def test_route_commitments_bind_exact_incident_counts_and_sorted_ids(self):
        outputs, _reference = builder.rich_relationship_runtime_outputs(
            self.corpus["relationships"],
            generated_at="2026-07-25T12:00:00Z",
            snapshot="fixture",
        )
        runtime = json.loads(outputs[Path(builder.RELATIONSHIP_RUNTIME_MANIFEST)])
        rows = runtime_rows(outputs, runtime)
        incident: dict[tuple[str, str], set[str]] = {}
        for row in rows:
            plane_name = next(
                plane["name"] for plane in runtime["planes"] if plane["id"] == row["plane"]
            )
            for route in {row["source"], row["target"]}:
                incident.setdefault((route, plane_name), set()).add(row["assertion_id"])

        locator = json.loads(outputs[Path(builder.RELATIONSHIP_RUNTIME_LOCATOR)])
        seen: set[tuple[str, str]] = set()
        for metadata in locator["buckets"]:
            compressed = outputs[Path(metadata["path"])]
            assert isinstance(compressed, bytes)
            bucket = json.loads(gzip.decompress(compressed))
            for route in bucket["routes"]:
                self.assertEqual(
                    metadata["bucket"], builder.rich_runtime_route_bucket(route["route"])
                )
                for commitment in route["planes"]:
                    key = (route["route"], commitment["name"])
                    identifiers = incident[key]
                    self.assertEqual(commitment["assertions"], len(identifiers))
                    self.assertEqual(
                        commitment["assertion_ids_sha256"],
                        builder.rich_runtime_assertion_digest(identifiers),
                    )
                    seen.add(key)
        self.assertEqual(seen, set(incident))

    def test_every_active_scope_is_default_and_authority_is_in_plane_identity(self):
        real = copy.deepcopy(
            next(
                row
                for row in self.corpus["relationships"]
                if row["label"] in builder.MATERIAL_RELATIONSHIP_LABELS
            )
        )
        synthetic = copy.deepcopy(real)
        synthetic["id"] = f"{builder.ASSERTION_BASE}{'f' * 24}"
        synthetic["assertion_scope"] = "synthetic-fixture"
        synthetic["authority"] = {
            "class": "synthetic",
            "label": "Repository-authored conformance fixture",
            "source": builder.REPOSITORY_LICENCE_URL,
        }
        outputs, _reference = builder.rich_relationship_runtime_outputs(
            [real, synthetic],
            generated_at="2026-07-25T12:00:00Z",
            snapshot="fixture",
        )
        runtime = json.loads(outputs[Path(builder.RELATIONSHIP_RUNTIME_MANIFEST)])
        planes = {plane["name"]: plane for plane in runtime["planes"]}
        real_name = next(name for name in planes if "real-world" in name)
        synthetic_name = next(name for name in planes if "synthetic-fixture" in name)

        self.assertIn("derived", real_name)
        self.assertIn("synthetic", synthetic_name)
        self.assertTrue(planes[synthetic_name]["active"])
        self.assertIn(real_name, runtime["default_planes"])
        self.assertIn(synthetic_name, runtime["default_planes"])
        self.assertEqual(
            runtime["default_planes"],
            [name for name, plane in planes.items() if plane["active"]],
        )

    def test_compiler_preserves_rejected_synthetic_governance_as_opt_in(self):
        material = [
            row
            for row in self.corpus["relationships"]
            if row["label"] in builder.MATERIAL_RELATIONSHIP_LABELS
        ]
        raw = copy.deepcopy(material[0])
        raw.update(
            {
                "assertion_scope": "synthetic-fixture",
                "scope_detail": "Fictional comparison fixture; not an admitted service",
                "authority": {
                    "class": "synthetic",
                    "label": "Repository-authored synthetic fixture",
                    "source": builder.REPOSITORY_LICENCE_URL,
                },
                "rights": {
                    "source": builder.REPOSITORY_LICENCE_URL,
                    "assertion": "Synthetic fixture retained for opt-in comparison only.",
                    "source_licence": {
                        "id": "MIT",
                        "title": "MIT License",
                        "basis": "repository-declared",
                        "confidence": 1.0,
                        "source": builder.REPOSITORY_LICENCE_URL,
                    },
                },
                "lifecycle": "rejected",
            }
        )
        compiled = builder.compile_relationship_assertions(
            [raw],
            self.corpus["records"],
            self.corpus["resources"],
            self.corpus["publishers"],
        )[0]
        self.assertEqual(compiled["assertion_scope"], raw["assertion_scope"])
        self.assertEqual(compiled["scope_detail"], raw["scope_detail"])
        self.assertEqual(compiled["authority"], raw["authority"])
        self.assertEqual(compiled["rights"], raw["rights"])
        self.assertEqual(compiled["lifecycle"], "rejected")

        active = next(row for row in material[1:] if row["id"] != compiled["id"])
        outputs, _reference = builder.rich_relationship_runtime_outputs(
            [active, compiled],
            generated_at="2026-07-25T12:00:00Z",
            snapshot="fixture",
        )
        runtime = json.loads(outputs[Path(builder.RELATIONSHIP_RUNTIME_MANIFEST)])
        synthetic = next(
            plane
            for plane in runtime["planes"]
            if plane["assertion_scope"] == "synthetic-fixture"
        )
        self.assertFalse(synthetic["active"])
        self.assertEqual(synthetic["lifecycle"], "rejected")
        self.assertNotIn(synthetic["name"], runtime["default_planes"])

    def test_wayfinder_relationship_labels_have_explicit_inverses(self):
        self.assertEqual(
            {
                label: builder.RELATIONSHIP_INVERSE_LABELS[label]
                for label in ("depends on", "implements pattern", "maintained by")
            },
            {
                "depends on": "dependency of",
                "implements pattern": "pattern implemented by",
                "maintained by": "maintains",
            },
        )

    def test_all_default_chunks_count_towards_whole_reader_ceiling(self):
        relationship = next(
            row
            for row in self.corpus["relationships"]
            if row["label"] in builder.MATERIAL_RELATIONSHIP_LABELS
        )
        with patch.object(builder, "MAX_RICH_RUNTIME_WHOLE_ROWS", 0):
            with self.assertRaisesRegex(ValueError, "whole.*row ceiling"):
                builder.rich_relationship_runtime_outputs(
                    [relationship],
                    generated_at="2026-07-25T12:00:00Z",
                    snapshot="fixture",
                )

    def test_validation_receipt_rejects_any_invalid_generated_assertion(self):
        report = builder.semantic_validation_report(
            self.corpus["relationships"],
            generated_at="2026-07-25T12:00:00Z",
        )
        self.assertEqual(report["status"], "conformant")
        invalid = copy.deepcopy(self.corpus["relationships"])
        del invalid[0]["rights"]
        with self.assertRaisesRegex(ValueError, "semantic assertion validation failed"):
            builder.semantic_validation_report(
                invalid, generated_at="2026-07-25T12:00:00Z"
            )


if __name__ == "__main__":
    unittest.main()
