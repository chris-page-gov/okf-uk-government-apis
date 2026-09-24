from __future__ import annotations

import importlib.util
from collections import Counter
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "sources" / "wayfinder" / "2026-09-24"


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


builder_module = load_script(
    "build_uk_government_api_okf",
    ROOT / "scripts" / "build_uk_government_api_okf.py",
)
wayfinder = load_script(
    "wayfinder_import",
    ROOT / "scripts" / "wayfinder_import.py",
)


def import_services():
    builder = builder_module.CorpusBuilder(
        "https://wayfinder.pbj.cx/",
        wayfinder.load_source(SOURCE / "catalogue.json", SOURCE / "manifest.json")[1][
            "capture"
        ]["sha256"],
        "2026-09-24T20:22:41.964Z",
    )
    records = wayfinder.add_wayfinder_services(
        builder,
        catalogue_path=SOURCE / "catalogue.json",
        manifest_path=SOURCE / "manifest.json",
    )
    return builder, records


class WayfinderImportTest(unittest.TestCase):
    def test_source_snapshot_is_complete_and_hash_bound(self):
        catalogue, manifest = wayfinder.load_source(
            SOURCE / "catalogue.json", SOURCE / "manifest.json"
        )
        counts = {
            key: len(catalogue[key]) for key in wayfinder.EXPECTED_COUNTS
        }

        self.assertEqual(counts, wayfinder.EXPECTED_COUNTS)
        self.assertEqual(sum(counts.values()), 311)
        self.assertEqual(manifest["rights"]["status"], "not specified")
        self.assertEqual(manifest["admission"]["mode"], "synthetic-fixture-opt-in")
        self.assertFalse(manifest["admission"]["defaultLoaded"])

    def test_all_services_are_namespaced_and_preserve_every_source_field(self):
        catalogue = json.loads((SOURCE / "catalogue.json").read_text(encoding="utf-8"))
        source_by_id = {item["id"]: item for item in catalogue["services"]}
        _builder, records = import_services()

        self.assertEqual(len(records), 85)
        self.assertEqual(len({record["name"] for record in records}), 85)
        for record in records:
            source_id = record["source_record_id"]
            self.assertTrue(record["name"].startswith("wayfinder-demo-"))
            self.assertEqual(
                record["extras"]["wayfinder"]["source_record"], source_by_id[source_id]
            )
            self.assertEqual(record["assertion_scope"], "synthetic-fixture")
            self.assertEqual(record["authority_class"], "synthetic")
            self.assertEqual(record["rights_status"], "not specified")
            self.assertFalse(record["default_loaded"])
            self.assertEqual(record["license_id"], "not-specified")
            self.assertEqual(record["license_basis"], "source-rights-not-specified")

    def test_import_is_deterministic_and_does_not_fuzzy_merge(self):
        first_builder, first = import_services()
        second_builder, second = import_services()

        self.assertEqual(first, second)
        self.assertEqual(first_builder.relationships, second_builder.relationships)
        self.assertEqual(len(first), 85)
        self.assertFalse(
            {record["name"] for record in first}
            & {
                "gov-uk-notify",
                "gov-uk-pay",
                "driver-and-vehicle-licensing-agency-dvla-vehicle-enquiry-service",
            }
        )

    def test_relationships_compile_only_to_rejected_synthetic_assertions(self):
        source_builder, records = import_services()
        publisher_counts = Counter(record["publisher"] for record in records)
        publishers = wayfinder.publisher_records(
            catalogue_path=SOURCE / "catalogue.json",
            manifest_path=SOURCE / "manifest.json",
            record_counts=publisher_counts,
        )
        relationships = builder_module.compile_relationship_assertions(
            source_builder.relationships,
            source_builder.records,
            source_builder.resources,
            publishers,
        )

        self.assertEqual(len(publishers), 6)
        self.assertEqual(len(relationships), 707)
        self.assertTrue(
            all(
                relationship["assertion_scope"] == "synthetic-fixture"
                and relationship["authority"]["class"] == "synthetic"
                and relationship["lifecycle"] == "rejected"
                and relationship["rights"]["source"] == "https://wayfinder.pbj.cx"
                for relationship in relationships
            )
        )
        self.assertFalse(
            any(
                relationship["label"]
                in builder_module.MATERIAL_RELATIONSHIP_LABELS
                for relationship in relationships
            )
        )

    def test_public_provenance_contains_no_local_path_or_private_message(self):
        published = "\n".join(
            (SOURCE / name).read_text(encoding="utf-8")
            for name in ("manifest.json", "reconciliation.json")
        )
        for forbidden in (
            "/Users/",
            "/tmp/",
            ".email.md",
            "@gmail.com",
            "@outlook.com",
        ):
            self.assertNotIn(forbidden, published)
        self.assertIn("Paul Buchanan-Jones", published)
        self.assertIn("contact details and message text are retained offline", published)


if __name__ == "__main__":
    unittest.main()
