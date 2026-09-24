from __future__ import annotations

import copy
import importlib.util
import gzip
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "uk_government_api_okf"
SCRIPT = ROOT / "scripts" / "build_uk_government_api_okf.py"
CHECK_SCRIPT = ROOT / "scripts" / "check_bundle.py"


spec = importlib.util.spec_from_file_location("build_uk_government_api_okf", SCRIPT)
assert spec and spec.loader
builder_module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = builder_module
spec.loader.exec_module(builder_module)

check_spec = importlib.util.spec_from_file_location("check_bundle", CHECK_SCRIPT)
assert check_spec and check_spec.loader
check_module = importlib.util.module_from_spec(check_spec)
sys.modules[check_spec.name] = check_module
check_spec.loader.exec_module(check_module)


class UkGovernmentApiOkfGeneratorTest(unittest.TestCase):
    def build_fixture_corpus(self):
        csv_bytes = (FIXTURES / "api_catalogue.csv").read_bytes()
        source_hash, rows = builder_module.rows_from_csv("file://api_catalogue.csv", csv_bytes)
        ckan = json.loads((FIXTURES / "ckan_package_search.json").read_text(encoding="utf-8"))
        os_documents = json.loads((FIXTURES / "os_api_tree.json").read_text(encoding="utf-8"))
        ons = json.loads((FIXTURES / "ons_payload.json").read_text(encoding="utf-8"))
        return builder_module.build_corpus(
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

    def test_canonical_counts_keep_api_products_endpoints_and_data_products_separate(self):
        corpus = self.build_fixture_corpus()
        counts = corpus["descriptor"]["counts"]

        # api_catalogue.csv carries two rows: the original payments API and a
        # second row used to exercise javascript: documentation redaction below.
        self.assertEqual(counts["declared_api_products"], 2)
        self.assertGreaterEqual(counts["provider_native_api_products"], 2)
        self.assertEqual(counts["data_access_endpoints"], 2)
        self.assertEqual(counts["data_products"], 4)
        self.assertEqual(counts["contracts"], 6)
        self.assertGreaterEqual(counts["operations"], 2)
        self.assertGreaterEqual(counts["schemas"], 2)
        self.assertEqual(counts["api_products"], counts["declared_api_products"] + counts["provider_native_api_products"])

    def test_ckan_api_like_resources_are_endpoint_records_not_api_products(self):
        corpus = self.build_fixture_corpus()
        records = corpus["records"]
        endpoint_records = [record for record in records if record["record_type"] == "Data Access API Endpoint"]

        self.assertEqual(len(endpoint_records), 2)
        self.assertTrue(all(record["source_adapter"] == "data_gov_uk_ckan" for record in endpoint_records))
        self.assertTrue(all(record["protocol"] == ["ArcGIS REST"] for record in endpoint_records))
        self.assertTrue(all(record["record_type"] != "API Product" for record in endpoint_records))

    def test_gias_records_distinguish_beta_api_from_supported_download(self):
        corpus = self.build_fixture_corpus()
        records = {record["name"]: record for record in corpus["records"]}
        api = records["department-for-education-gias-read-api-prototype"]
        download = records["department-for-education-gias-establishments-download"]
        service = records["department-for-education-get-information-about-schools"]

        self.assertEqual(api["lifecycle_status"], "beta-prototype")
        self.assertEqual(api["extras"]["support_status"], "not-yet-published-or-supported")
        self.assertEqual(api["url"], "")
        self.assertEqual(api["source_adapter"], "dfe_gias")
        self.assertEqual(download["lifecycle_status"], "production-supported-alternative")
        self.assertEqual(download["extras"]["warwickshire_local_authority_code"], "937")
        self.assertEqual(download["license_id"], builder_module.OGL_V3_ID)
        self.assertEqual(service["extras"]["authoritative_identifier"], "DfE URN")
        self.assertTrue(
            any(
                row["source"] == api["route"]
                and row["target"] == download["route"]
                and row["kind"] == "has current supported alternative"
                for row in corpus["relationships"]
            )
        )

    def test_every_record_has_route_provenance_confidence_and_source_adapter(self):
        corpus = self.build_fixture_corpus()

        for record in corpus["records"]:
            self.assertTrue(record["route"].startswith("dataset/"), record["name"])
            self.assertTrue(record["provenance"].get("source_url"), record["name"])
            self.assertIn(record["confidence"], {"observed", "declared", "assured"}, record["name"])
            self.assertTrue(record["source_adapter"], record["name"])

    def test_facets_include_source_record_type_protocol_and_confidence(self):
        corpus = self.build_fixture_corpus()
        facets = corpus["facets"]

        self.assertIn("record_type", facets)
        self.assertIn("source_adapter", facets)
        self.assertIn("protocol", facets)
        self.assertIn("confidence", facets)
        self.assertIn("quality_band", facets)
        self.assertIn("assurance_status", facets)
        self.assertIn("relationship_density", facets)
        self.assertIn("canonical_publisher", facets)
        self.assertIn("dcat_type", facets)
        self.assertIn("openapi_type", facets)
        self.assertIn("openapi_security_scheme", facets)
        self.assertIn("data_gov_uk_ckan", {row["value"] for row in facets["source_adapter"]})
        self.assertIn("Data Access API Endpoint", {row["value"] for row in facets["record_type"]})

    def test_redact_url_strips_password_param_and_reports_count(self):
        cleaned, dropped = builder_module.redact_url("https://example.gov.uk/api?password=hunter2&format=json")

        self.assertEqual(dropped, 1)
        self.assertNotIn("password=", cleaned)
        self.assertIn("format=json", cleaned)

    def test_redact_url_strips_multiple_credential_params(self):
        cleaned, dropped = builder_module.redact_url("https://example.gov.uk/api?token=abc&login=xyz&password=hunter2")

        self.assertEqual(dropped, 3)
        self.assertEqual(cleaned, "https://example.gov.uk/api")

    def test_redact_url_leaves_url_without_query_unchanged(self):
        url = "https://example.gov.uk/api"
        cleaned, dropped = builder_module.redact_url(url)

        self.assertEqual(dropped, 0)
        self.assertEqual(cleaned, url)

    def test_redact_url_preserves_non_credential_params(self):
        url = "https://example.gov.uk/api?format=json&limit=10"
        cleaned, dropped = builder_module.redact_url(url)

        self.assertEqual(dropped, 0)
        self.assertEqual(cleaned, url)

    def test_safe_url_rejects_javascript_scheme(self):
        self.assertEqual(builder_module.safe_url("javascript:alert(1)"), "")

    def test_safe_url_rejects_non_http_schemes(self):
        self.assertEqual(builder_module.safe_url("ftp://example.gov.uk/file.csv"), "")

    def test_safe_url_accepts_https(self):
        url = "https://example.gov.uk/api"
        self.assertEqual(builder_module.safe_url(url), url)

    def test_safe_url_strips_whitespace(self):
        self.assertEqual(builder_module.safe_url("  https://example.gov.uk/api  "), "https://example.gov.uk/api")

    def test_ckan_provenance_url_is_canonical_and_idempotent(self):
        query = builder_module.ckan_api_query()
        raw_url = f"{builder_module.DEFAULT_CKAN_API_URL}?fq={query}"
        expected_url = (
            f"{builder_module.DEFAULT_CKAN_API_URL}?fq="
            "res_format%3A%28%22WMS%22%20OR%20%22WFS%22%20OR%20"
            "%22WMTS%22%20OR%20%22WCS%22%20OR%20%22OGC%20API%20-%20"
            "Features%22%20OR%20%22OGC%20WFS%22%20OR%20%22OGC%20WMS%22%20"
            "OR%20%22ogc%20wfs%22%20OR%20%22ogc%20wms%22%20OR%20%22ArcGIS%20"
            "GeoServices%20REST%20API%22%20OR%20%22arcgis%20geoservices%20rest%20"
            "api%22%20OR%20%22Esri%20REST%22%20OR%20%22ESRI%20REST%20API%22%20"
            "OR%20%22ESRI%20Rest%20API%22%20OR%20%22esri%20rest%20api%22%20OR%20"
            "%22SPARQL%22%20OR%20%22API%22%20OR%20%22api%22%29"
        )

        canonical_url = builder_module.canonical_http_url(raw_url)

        self.assertEqual(canonical_url, expected_url)
        self.assertEqual(builder_module.canonical_http_url(canonical_url), canonical_url)
        self.assertFalse(builder_module.is_canonical_safe_http_url(raw_url))
        self.assertTrue(builder_module.is_canonical_safe_http_url(canonical_url))
        self.assertEqual(
            builder_module.canonical_http_url("https://example.gov.uk/user's/source"),
            "https://example.gov.uk/user%27s/source",
        )

    def test_live_ckan_loader_returns_canonical_provenance(self):
        response = {"result": {"count": 1, "results": [{"name": "example"}]}}
        with patch.object(builder_module, "request_json", return_value=response) as request:
            source_url, packages = builder_module.load_ckan_packages(rows_per_page=1000)

        self.assertEqual(packages, [{"name": "example"}])
        self.assertTrue(builder_module.is_canonical_safe_http_url(source_url))
        self.assertNotRegex(source_url, r'[\s"]')
        self.assertIn("fq=res_format%3A%28%22WMS%22", source_url)
        requested_url = request.call_args.args[0]
        self.assertNotRegex(requested_url, r'[\s"]')

    def test_canonical_http_url_rejects_unsafe_authorities(self):
        for value in (
            "javascript:alert(1)",
            "https:///source",
            "https://user:secret@example.gov.uk/source",
            "https://example.gov.uk/path\\segment",
            "https://example.gov.uk/path?value=%ZZ",
            "https://example.gov.uk:0/source",
            "https://example.gov.uk:65536/source",
        ):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    builder_module.canonical_http_url(value)
                self.assertFalse(builder_module.is_canonical_safe_http_url(value))

    def test_plain_text_strips_entity_encoded_script_tags(self):
        result = builder_module.plain_text("&lt;script&gt;x&lt;/script&gt;")

        self.assertNotIn("<", result)

    def test_plain_text_removes_literal_backslash_n_sequences(self):
        result = builder_module.plain_text("line one\\nline two\\r\\nline three")

        self.assertNotIn("\\n", result)
        self.assertNotIn("\\r\\n", result)

    def test_plain_text_collapses_whitespace(self):
        result = builder_module.plain_text("too   many\n\nspaces\there")

        self.assertEqual(result, "too many spaces here")

    def test_rows_from_csv_tolerates_ragged_rows_with_extra_cells(self):
        csv_text = (
            "dateAdded,dateUpdated,url,name,description,documentation,license,maintainer,areaServed,startDate,endDate,provider\n"
            "2024-01-01,2024-06-01,https://api.example.gov.uk/ragged,Ragged Row API,desc,doc,lic,maint,UK,2024-01-01,,Ragged Dept,extra-cell-1,extra-cell-2\n"
        )

        source_hash, rows = builder_module.rows_from_csv("file://ragged.csv", csv_text.encode("utf-8"))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].raw.get("name"), "Ragged Row API")
        self.assertEqual(rows[0].raw.get("provider"), "Ragged Dept")

    def test_harvested_url_redaction_and_safety_warnings_surface_in_overview(self):
        corpus = self.build_fixture_corpus()

        all_urls = []
        for record in corpus["records"]:
            all_urls.append(str(record.get("url", "")))
            all_urls.append(str(record.get("documentation", "")))
        for resource in corpus["resources"]:
            all_urls.append(str(resource.get("url", "")))
        joined = " ".join(all_urls)

        self.assertNotIn("password=", joined)
        self.assertNotIn("login=", joined)
        self.assertNotIn("token=", joined)

        javascript_row_records = [record for record in corpus["records"] if record["name"] == "example-department-example-records-api"]
        self.assertEqual(len(javascript_row_records), 1)
        self.assertEqual(javascript_row_records[0]["documentation"], "")
        self.assertEqual(javascript_row_records[0]["url"], "https://api.example.gov.uk/records")

        warnings = corpus["overview"]["warnings"]
        self.assertEqual(warnings["credential_parameters_redacted"], 3)
        self.assertEqual(warnings["unsafe_urls_dropped"], 1)
        self.assertEqual(warnings["duplicate_slugs_dropped"], 0)
        self.assertEqual(warnings["duplicate_endpoints_skipped"], 1)
        self.assertEqual(corpus["analysis"]["warnings"], warnings)

    def test_ons_ckan_records_infer_ogl_from_provider_terms_when_source_licence_missing(self):
        corpus = self.build_fixture_corpus()
        records = corpus["records"]
        ons_ckan_records = [
            record
            for record in records
            if record["source_adapter"] == "data_gov_uk_ckan" and record["publisher"] == "office-for-national-statistics"
        ]

        self.assertEqual({record["record_type"] for record in ons_ckan_records}, {"Data Product", "Data Access API Endpoint"})
        for record in ons_ckan_records:
            self.assertEqual(record["license_id"], builder_module.OGL_V3_ID)
            self.assertEqual(record["license_title"], builder_module.OGL_V3_TITLE)
            self.assertEqual(record["license_source_id"], builder_module.ONS_TERMS_URL)
            self.assertEqual(record["license_basis"], "provider-terms-inferred")
            self.assertEqual(record["license_confidence"], 0.75)

        self.assertGreaterEqual(corpus["overview"]["warnings"]["licence_inferred_from_provider_terms"], len(ons_ckan_records))

    def test_ordnance_survey_records_infer_provider_licence_requirement(self):
        corpus = self.build_fixture_corpus()
        os_records = [
            record
            for record in corpus["records"]
            if record["source_adapter"] == "ordnance_survey_api_os_uk"
        ]

        self.assertTrue(os_records)
        for record in os_records:
            self.assertEqual(record["license_id"], builder_module.OS_LICENCE_ID)
            self.assertEqual(record["license_title"], builder_module.OS_LICENCE_TITLE)
            self.assertEqual(record["license_source_id"], builder_module.OS_LICENCE_URL)
            self.assertEqual(record["license_basis"], "provider-terms-inferred")
            self.assertEqual(record["license_confidence"], 0.7)
            self.assertFalse(record["private"])

    def test_search_docs_preserve_licence_metadata_for_first_click_cards(self):
        corpus = self.build_fixture_corpus()
        result_docs = [
            doc
            for _path, chunk in corpus["search"]["result_doc_chunks"]
            for doc in chunk
        ]
        os_doc = next(doc for doc in result_docs if doc["name"] == "ordnance-survey-api-portal")

        self.assertEqual(os_doc["license_id"], builder_module.OS_LICENCE_ID)
        self.assertEqual(os_doc["license_title"], builder_module.OS_LICENCE_TITLE)
        self.assertEqual(os_doc["license_source_id"], builder_module.OS_LICENCE_URL)
        self.assertEqual(os_doc["license_basis"], "provider-terms-inferred")
        self.assertEqual(os_doc["license_confidence"], 0.7)

    def test_ckan_ogl_variants_are_canonicalised_before_provider_inference(self):
        corpus = self.build_fixture_corpus()
        council_product = next(record for record in corpus["records"] if record["name"] == "data-gov-uk-planning-applications")

        self.assertEqual(council_product["license_id"], builder_module.OGL_V3_ID)
        self.assertEqual(council_product["license_title"], builder_module.OGL_V3_TITLE)
        self.assertEqual(council_product["license_basis"], "source-declared")

    def test_license_field_normalisation_preserves_non_ogl_source_ids(self):
        self.assertEqual(
            builder_module.normalize_license_fields("cc-by", "Creative Commons Attribution"),
            ("cc-by", "Creative Commons Attribution", "cc-by"),
        )
        self.assertEqual(
            builder_module.normalize_license_fields("notspecified", "Licence not specified"),
            ("not-specified", "Not specified", ""),
        )

    def test_every_relationship_edge_carries_provenance(self):
        corpus = self.build_fixture_corpus()

        relationships = corpus["relationships"]
        self.assertTrue(relationships)
        observed = {row["observed_at"] for row in relationships}
        for row in relationships:
            self.assertIn(row["evidence_type"], {"harvested_structure", "contract_signal", "inferred_metadata_match"})
            self.assertIn(row["confidence"], {"high", "medium"})
            self.assertTrue(row["observed_at"])
            self.assertTrue(set(builder_module.RICH_RELATIONSHIP_FIELDS) <= set(row))
            self.assertTrue(row["id"].startswith(builder_module.ASSERTION_BASE))
            self.assertTrue(row["source_iri"].startswith(builder_module.IDENTIFIER_BASE))
            self.assertTrue(row["target_iri"].startswith(builder_module.IDENTIFIER_BASE))
            self.assertTrue(builder_module.safe_runtime_route(row["source"]))
            self.assertTrue(builder_module.safe_runtime_route(row["target"]))
            self.assertTrue(row["predicate"].startswith(builder_module.PREDICATE_BASE))
            self.assertEqual(row["label"], row["kind"])
            self.assertEqual(
                row["inverse_label"],
                builder_module.RELATIONSHIP_INVERSE_LABELS[row["kind"]],
            )
            self.assertEqual(row["assertion_scope"], "real-world")
            self.assertEqual(row["scope_detail"], "metadata-only-catalogue-view")
            self.assertEqual(row["authority"]["class"], "derived")
            self.assertTrue(row["evidence"][0]["source_adapter"])
            self.assertIn("source_licence", row["evidence"][0])
            self.assertTrue(row["rights"]["assertion"])
            validation_errors = []
            check_module.validate_relationship(row, validation_errors, row["id"])
            self.assertEqual(validation_errors, [])
        self.assertEqual(len(observed), 1)

        protocol_edges = [row for row in relationships if row["kind"] == "uses protocol"]
        self.assertTrue(protocol_edges)
        for row in protocol_edges:
            self.assertEqual(row["target"], builder_module.protocol_route(row["target_label"]))
            legacy_route = f"protocol/{row['target_label']}"
            if legacy_route != row["target"]:
                self.assertIn(legacy_route, row["target_aliases"])
        semantic_nodes = builder_module.route_entity_nodes(
            corpus["records"],
            corpus["resources"],
            corpus["publishers"],
            relationships,
        )
        arcgis = next(node for node in semantic_nodes if node["route"] == "protocol/arcgis-rest")
        self.assertEqual(arcgis["title"], "ArcGIS REST")
        self.assertIn("protocol/ArcGIS REST", arcgis["aliases"])

        inferred = [row for row in relationships if row["assertion_status"] == "inferred"]
        self.assertTrue(inferred)
        for row in inferred:
            self.assertTrue(row["rule"].startswith(builder_module.PUBLIC_BASE))
            self.assertTrue(row["supporting_assertions"])
            self.assertEqual(row["confidence_score"], 0.65)

    def test_frozen_relationship_compilation_canonicalizes_urls_without_changing_identity(self):
        raw_url = (
            "https://ckan.publishing.service.gov.uk/api/3/action/package_search"
            '?fq=res_format:("WMS" OR "OGC API - Features")'
        )
        canonical_url = builder_module.canonical_http_url(raw_url)
        relationship = {
            "source": "dataset/example",
            "target": "publisher/example-department",
            "kind": "published by",
            "evidence_type": "harvested_structure",
            "confidence": "high",
            "observed_at": "2026-07-16T00:00:00Z",
        }

        def compile_with(source_url):
            record = {
                "route": "dataset/example",
                "source_adapter": "data_gov_uk_ckan",
                "source_tier": "official-catalogue",
                "confidence": "observed",
                "license_id": builder_module.OGL_V3_ID,
                "license_title": builder_module.OGL_V3_TITLE,
                "license_basis": "source-declared",
                "license_confidence": 1.0,
                "license_source_id": builder_module.OGL_V3_URL,
                "provenance": {
                    "source_url": source_url,
                    "source_adapter": "data_gov_uk_ckan",
                    "source_tier": "official-catalogue",
                    "confidence": "observed",
                    "observed_at": "2026-07-16T00:00:00Z",
                },
            }
            return builder_module.compile_relationship_assertions(
                [relationship], [record], [], []
            )[0]

        from_raw = compile_with(raw_url)
        from_canonical = compile_with(canonical_url)

        self.assertEqual(from_raw, from_canonical)
        self.assertEqual(from_raw["authority"]["source"], canonical_url)
        self.assertEqual(from_raw["evidence"][0]["url"], canonical_url)
        self.assertEqual(from_raw["rights"]["source"], builder_module.OGL_V3_URL)
        self.assertTrue(builder_module.is_canonical_safe_http_url(canonical_url))
        expected_digest = from_canonical["evidence"][0]["source_value_sha256"]
        self.assertEqual(from_raw["evidence"][0]["source_value_sha256"], expected_digest)

        with self.assertRaisesRegex(ValueError, "must not contain credentials"):
            compile_with("https://user:secret@example.gov.uk/source")

    def test_relationship_checker_rejects_each_unsafe_renderable_url_field(self):
        corpus = self.build_fixture_corpus()
        valid = corpus["relationships"][0]
        cases = (
            ("authority source", lambda row: row["authority"].update(source="https://example.gov.uk/?q=a b")),
            ("evidence[0] url", lambda row: row["evidence"][0].update(url="https://example.gov.uk/?q=a b")),
            ("evidence[0] resource", lambda row: row["evidence"][0].update(resource="javascript:alert(1)")),
            ("rights source", lambda row: row["rights"].update(source="https://user:secret@example.gov.uk/terms")),
        )

        for expected_error, mutate in cases:
            with self.subTest(field=expected_error):
                invalid = copy.deepcopy(valid)
                mutate(invalid)
                errors = []
                check_module.validate_relationship(invalid, errors, invalid["id"])
                self.assertTrue(
                    any(expected_error in error and "canonical safe HTTP(S) URL" in error for error in errors),
                    errors,
                )

    def test_complete_published_relationship_population_has_safe_canonical_urls(self):
        bundle = ROOT / "bundle"
        manifest = json.loads((bundle / "data/manifest.json").read_text(encoding="utf-8"))
        relationship_count = 0
        checked_url_count = 0
        unsafe_count = 0
        unsafe_samples = []
        for relative in manifest["chunks"]["relationships"]:
            payload = gzip.decompress((bundle / relative).read_bytes())
            for row in json.loads(payload):
                relationship_count += 1
                values = [
                    ("authority.source", (row.get("authority") or {}).get("source")),
                    ("rights.source", (row.get("rights") or {}).get("source")),
                ]
                for evidence_index, evidence in enumerate(row.get("evidence") or []):
                    values.append((f"evidence[{evidence_index}].url", evidence.get("url")))
                    if "resource" in evidence:
                        values.append((f"evidence[{evidence_index}].resource", evidence.get("resource")))
                for field, value in values:
                    checked_url_count += 1
                    if not builder_module.is_canonical_safe_http_url(value):
                        unsafe_count += 1
                        if len(unsafe_samples) < 10:
                            unsafe_samples.append((row.get("id"), field, value))
        self.assertEqual(relationship_count, manifest["counts"]["relationships"])
        self.assertGreaterEqual(checked_url_count, relationship_count * 3)
        self.assertEqual(
            unsafe_count,
            0,
            f"{unsafe_count} unsafe URL occurrences; samples: {unsafe_samples}",
        )

    def test_protocol_route_canonicalization_is_idempotent_and_collision_closed(self):
        legacy = [
            {
                "source": "dataset/example",
                "target": "protocol/ArcGIS REST",
                "kind": "uses protocol",
            }
        ]
        canonical = builder_module.canonicalize_derived_relationship_routes(legacy)
        self.assertEqual(canonical[0]["target"], "protocol/arcgis-rest")
        self.assertEqual(canonical[0]["target_label"], "ArcGIS REST")
        self.assertEqual(canonical[0]["target_aliases"], ["protocol/ArcGIS REST"])
        self.assertEqual(
            builder_module.canonicalize_derived_relationship_routes(canonical), canonical
        )

        with self.assertRaisesRegex(ValueError, "protocol route collision"):
            builder_module.canonicalize_derived_relationship_routes(
                [
                    {"source": "dataset/a", "target": "protocol/A/B", "kind": "uses protocol"},
                    {"source": "dataset/b", "target": "protocol/A B", "kind": "uses protocol"},
                ]
            )

    def test_semantic_shards_reconcile_direct_and_reified_relationships(self):
        corpus = self.build_fixture_corpus()
        files = builder_module.output_files(corpus)
        descriptor = json.loads(files[Path("okf-bundle.jsonld")])
        manifest = json.loads(files[Path("data/semantic/manifest.json")])

        self.assertNotIn("@graph", descriptor)
        self.assertEqual(
            files[Path("schemas/okf-relationship-assertion.v2.schema.json")],
            builder_module.SEMANTIC_ASSERTION_SCHEMA_PATH.read_text(encoding="utf-8"),
        )
        self.assertEqual(
            manifest["counts"]["direct_relationships"], len(corpus["relationships"])
        )
        self.assertEqual(
            manifest["counts"]["reified_assertions"], len(corpus["relationships"])
        )
        expected_direct = {
            (row["source_iri"], row["predicate"], row["target_iri"])
            for row in corpus["relationships"]
        }
        expected_assertions = {
            row["id"]: check_module.projection_digest(row)
            for row in corpus["relationships"]
        }
        seen_direct = set()
        seen_assertions = set()
        for entry in manifest["shards"]:
            compressed = files[Path(entry["path"])]
            self.assertIsInstance(compressed, bytes)
            self.assertLess(len(compressed), check_module.MAX_GITHUB_FILE_BYTES)
            document = json.loads(gzip.decompress(compressed))
            if entry["kind"] == "entity-direct-triples":
                for node in document["@graph"]:
                    for predicate in {row["predicate"] for row in corpus["relationships"]}:
                        for target in node.get(predicate, []):
                            seen_direct.add((node["@id"], predicate, target["@id"]))
            else:
                for node in document["@graph"]:
                    self.assertEqual(
                        check_module.projection_digest(node, semantic=True),
                        expected_assertions[node["@id"]],
                    )
                    seen_assertions.add(node["@id"])
        self.assertEqual(seen_direct, expected_direct)
        self.assertEqual(seen_assertions, set(expected_assertions))

    def test_relationship_adjacency_is_route_scoped_and_portable(self):
        corpus = self.build_fixture_corpus()
        manifest = corpus["relationship_adjacency"]
        files = builder_module.output_files(corpus)

        self.assertEqual(builder_module.relationship_bucket("dataset/dataset-one"), "83")
        self.assertEqual(builder_module.relationship_bucket("é"), "1e")
        self.assertEqual(manifest["algorithm"], "fnv1a32-prefix-2")
        self.assertEqual(manifest["relationships"], len(corpus["relationships"]))
        self.assertIn(Path("data/adjacency/manifest.json"), files)
        relationship_path = Path(corpus["manifest"]["chunks"]["relationships"][0])
        self.assertTrue(relationship_path.name.endswith(".json.gz"))
        self.assertEqual(
            json.loads(gzip.decompress(files[relationship_path]))[0],
            corpus["relationships"][0],
        )
        for relationship in corpus["relationships"]:
            for route in {relationship["source"], relationship["target"]}:
                bucket = builder_module.relationship_bucket(route)
                payload = json.loads(files[Path(f"data/adjacency/{bucket}.json")])
                self.assertIn(relationship, payload[route])

    def test_contract_records_markdown_and_crosslinks_are_emitted(self):
        corpus = self.build_fixture_corpus()
        records = corpus["records"]
        relationships = corpus["relationships"]
        files = builder_module.output_files(corpus)

        self.assertEqual(sum(1 for record in records if record["record_type"] in {"Contract", "Capability Document"}), 6)
        self.assertTrue(any(row["kind"] == "described by" for row in relationships))
        self.assertTrue(any(row["kind"] in {"shares endpoint host", "same provider catalogue evidence"} for row in relationships))
        self.assertIn(Path("index.md"), files)
        self.assertIn(Path("log.md"), files)
        self.assertIn(Path("api-records/example-department-example-payments-api.md"), files)
        self.assertIn(Path("organisations/example-department.md"), files)
        self.assertNotIn(Path("api-records/data-gov-uk-test-api-dataset.md"), files)

    def test_records_include_credentials_samples_and_derived_facets(self):
        corpus = self.build_fixture_corpus()
        operation = next(record for record in corpus["records"] if record["record_type"] == "API Operation")
        product = next(record for record in corpus["records"] if record["name"] == "example-department-example-payments-api")

        self.assertTrue(product["credential_requirements"])
        self.assertIn(product["assurance_status"], {"declared", "assured", "observed"})
        self.assertIn(product["quality_band"], {"high", "medium", "low", "not-assessed"})
        self.assertIn(product["relationship_density"], {"none", "low", "medium", "high"})
        self.assertTrue(operation["sample_policy"])
        self.assertFalse(operation["sample_policy"]["live_calls_enabled"])

    def test_records_include_standards_alignment_metadata(self):
        corpus = self.build_fixture_corpus()
        product = next(record for record in corpus["records"] if record["record_type"] == "API Product")
        operation = next(record for record in corpus["records"] if record["record_type"] == "API Operation")

        self.assertEqual(product["dcat_type"], "dcat:DataService")
        self.assertEqual(product["openapi_type"], "OpenAPI Object")
        self.assertIn(product["dcat_export_status"], {"data-service-ready", "data-service-with-gaps"})
        self.assertIn(product["openapi_export_status"], {"service-stub-ready", "service-stub-with-gaps"})
        self.assertIn(product["openapi_security_scheme"], {"none", "apiKey", "oauth2", "metadata-only", "unknown"})
        self.assertEqual(operation["openapi_type"], "Operation Object")
        self.assertEqual(operation["standards_alignment"]["dcat"]["export_status"], "roll-up-to-parent-service")
        self.assertIn("parameters", operation["standards_alignment"]["openapi"]["required_missing"])

    def test_descriptor_and_markdown_expose_standards_crosswalk(self):
        corpus = self.build_fixture_corpus()
        descriptor = corpus["descriptor"]
        files = builder_module.output_files(corpus)

        self.assertIn("standards_crosswalk", descriptor["entrypoints"])
        self.assertIn("okf-standards-crosswalk.v1", descriptor["extensions"])
        self.assertEqual(
            "docs/okf-standards-crosswalk.md",
            descriptor["extensions"]["okf-standards-crosswalk.v1"]["crosswalk"],
        )
        self.assertEqual(
            "docs/okf-standards-crosswalk.md",
            corpus["analysis"]["standards_alignment"]["crosswalk"],
        )
        self.assertTrue(corpus["analysis"]["standards_alignment"]["standards"])
        record_markdown = files[Path("api-records/example-department-example-payments-api.md")]
        self.assertIn("## Standards Alignment", record_markdown)
        self.assertIn("`dcat:DataService`", record_markdown)
        self.assertIn(
            "[OKF Standards Crosswalk](../docs/okf-standards-crosswalk.md)",
            record_markdown,
        )
        self.assertNotIn(
            "[OKF Standards Crosswalk](../../docs/okf-standards-crosswalk.md)",
            record_markdown,
        )

    def test_v02_markdown_separates_publication_time_from_source_time(self):
        corpus = self.build_fixture_corpus()
        files = builder_module.output_files(corpus)
        record = files[Path("api-records/example-department-example-payments-api.md")]

        self.assertEqual("0.2", corpus["descriptor"]["okf_version"])
        self.assertEqual("0.2", corpus["manifest"]["okf_version"])
        self.assertTrue(files[Path("index.md")].startswith('---\nokf_version: "0.2"\n---'))
        self.assertIn(
            "[Specification notes](docs/UK-Government-API-OKF.md)",
            files[Path("index.md")],
        )
        self.assertIn(
            "[Standards crosswalk](docs/okf-standards-crosswalk.md)",
            files[Path("index.md")],
        )
        self.assertTrue(files[Path("log.md")].startswith("# UK Government APIs OKF generation log\n\n## "))
        self.assertIn(
            'generated: { by: process:uk-government-api-okf-builder, at: "2026-07-25T12:00:00Z" }',
            record,
        )
        self.assertIn('last_modified: "2024-06-01"', record)
        self.assertIn("sources: [{", record)
        self.assertIn("status: draft", record)
        self.assertNotIn("\ntimestamp:", record)
        self.assertNotIn("\nverified:", record)

    def test_v02_validator_enforces_actor_and_calendar_date_conventions(self):
        self.assertTrue(check_module.valid_actor("process:uk-government-api-okf-builder"))
        self.assertTrue(check_module.valid_actor("catalogue-harvester/1.0"))
        self.assertFalse(check_module.valid_actor("team:catalogue"))
        self.assertTrue(check_module.valid_datetime('"2026-07-25T12:00:00Z"'))
        self.assertFalse(check_module.valid_datetime('"2026-07-25"'))
        self.assertTrue(check_module.valid_date('"2026-07-25"'))
        self.assertFalse(check_module.valid_date('"2026-02-30"'))


if __name__ == "__main__":
    unittest.main()
