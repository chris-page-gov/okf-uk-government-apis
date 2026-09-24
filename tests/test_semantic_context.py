from __future__ import annotations

import json
from pathlib import Path
import unittest

from pyld import jsonld


ROOT = Path(__file__).resolve().parents[1]
LOCAL_CONTEXT_PATH = ROOT / "context" / "okf-bundle-v1.jsonld"
PROFILE_CONTEXT_PATH = ROOT / "profiles" / "bundle-wiki" / "v1" / "semantic-context.jsonld"

DC_TERMS = "http://purl.org/dc/terms/"
OKF = "https://chris-page-gov.github.io/okf-explorer/ns#"
PROV = "http://www.w3.org/ns/prov#"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
SCHEMA = "https://schema.org/"
XSD = "http://www.w3.org/2001/XMLSchema#"


def load_context(path: Path) -> dict[str, object]:
    document = json.loads(path.read_text(encoding="utf-8"))
    context = document.get("@context")
    if not isinstance(context, dict):
        raise AssertionError(f"{path} must contain an @context object")
    return context


class SemanticContextTest(unittest.TestCase):
    def test_direct_assertion_terms_match_the_pinned_profile(self):
        local_context = load_context(LOCAL_CONTEXT_PATH)
        profile_context = load_context(PROFILE_CONTEXT_PATH)
        profile_assertions = profile_context["assertions"]
        self.assertIsInstance(profile_assertions, dict)
        profile_assertion_context = profile_assertions["@context"]
        self.assertIsInstance(profile_assertion_context, dict)

        self.assertEqual(local_context["assertions"], profile_assertions)
        self.assertEqual(local_context["search_variants"], profile_context["search_variants"])
        for term, definition in profile_assertion_context.items():
            with self.subTest(term=term):
                self.assertEqual(local_context.get(term), definition)

        retained_entity_terms = {
            "aliases": {"@container": "@set", "@id": "okf:alias"},
            "description": "dcterms:description",
            "graph_manifest": {"@id": "okf:graphManifest", "@type": "@id"},
            "route": "okf:route",
            "source_adapter": "okf:sourceAdapter",
            "source_iri": {"@id": "okf:sourceIri", "@type": "@id"},
            "source_route": "okf:sourceRoute",
            "source_tier": "okf:sourceTier",
            "target_aliases": {"@container": "@set", "@id": "okf:targetAlias"},
            "target_iri": {"@id": "okf:targetIri", "@type": "@id"},
            "target_label": "okf:targetLabel",
            "target_route": "okf:targetRoute",
            "title": "dcterms:title",
        }
        for term, definition in retained_entity_terms.items():
            with self.subTest(entity_term=term):
                self.assertEqual(local_context.get(term), definition)

    def test_local_expansion_preserves_assertion_provenance(self):
        context = load_context(LOCAL_CONTEXT_PATH)
        base = "https://example.gov.uk/"
        source_digest = "a" * 64
        value_digest = "b" * 64
        assertion = {
            "@context": context,
            "@id": f"{base}assertions/example",
            "@type": ["rdf:Statement", "okf:RelationshipAssertion"],
            "source": f"{base}catalogue/source",
            "predicate": f"{base}relationships/provides",
            "target": f"{base}catalogue/target",
            "authority": {
                "class": "official",
                "label": "Official register",
                "source": f"{base}register",
            },
            "evidence": [
                {
                    "@id": f"{base}evidence/example",
                    "url": f"{base}source-document",
                    "source_field": "items[0].identifier",
                    "retrieved_at": "2026-09-24T12:00:00Z",
                    "source_sha256": source_digest,
                    "source_value_sha256": value_digest,
                    "normalization": f"{base}rules/normalise-identifier",
                    "rule_id": [
                        f"{base}rules/extract-identifier",
                        f"{base}rules/normalise-identifier",
                    ],
                    "locator": "$.items[0].identifier",
                }
            ],
            "rights": {
                "source": f"{base}licences/open-government-licence",
                "assertion": "Use is permitted under the stated licence.",
            },
            "supporting_assertions": [
                f"{base}assertions/support-one",
                f"{base}assertions/support-two",
            ],
        }

        remote_requests: list[str] = []

        def reject_remote_document(url: str, _options: object = None) -> object:
            remote_requests.append(url)
            raise AssertionError(f"JSON-LD expansion attempted a remote fetch: {url}")

        expanded = jsonld.expand(
            assertion,
            options={"documentLoader": reject_remote_document},
        )

        self.assertEqual(remote_requests, [])
        self.assertEqual(len(expanded), 1)
        node = expanded[0]
        self.assertEqual(node[f"{RDF}subject"], [{"@id": f"{base}catalogue/source"}])
        self.assertEqual(
            node[f"{RDF}predicate"],
            [{"@id": f"{base}relationships/provides"}],
        )
        self.assertEqual(node[f"{RDF}object"], [{"@id": f"{base}catalogue/target"}])

        authority = node[f"{OKF}authority"][0]
        self.assertEqual(
            authority[f"{OKF}authorityClass"],
            [{"@id": f"{OKF}OfficialAuthority"}],
        )
        self.assertEqual(authority[f"{RDFS}label"], [{"@value": "Official register"}])
        self.assertEqual(
            authority[f"{DC_TERMS}source"],
            [{"@id": f"{base}register"}],
        )

        evidence = node[f"{PROV}hadPrimarySource"][0]
        self.assertEqual(evidence["@id"], f"{base}evidence/example")
        self.assertEqual(evidence[f"{SCHEMA}url"], [{"@id": f"{base}source-document"}])
        self.assertEqual(
            evidence[f"{OKF}sourceField"],
            [{"@value": "items[0].identifier"}],
        )
        self.assertEqual(
            evidence[f"{PROV}generatedAtTime"],
            [{"@type": f"{XSD}dateTime", "@value": "2026-09-24T12:00:00Z"}],
        )
        self.assertEqual(evidence[f"{OKF}sourceSha256"], [{"@value": source_digest}])
        self.assertEqual(
            evidence[f"{OKF}sourceValueSha256"],
            [{"@value": value_digest}],
        )
        self.assertEqual(
            evidence[f"{OKF}normalizationRule"],
            [{"@id": f"{base}rules/normalise-identifier"}],
        )
        self.assertEqual(
            evidence[f"{OKF}rule"],
            [
                {"@id": f"{base}rules/extract-identifier"},
                {"@id": f"{base}rules/normalise-identifier"},
            ],
        )
        self.assertEqual(
            evidence[f"{OKF}sourceLocator"],
            [{"@value": "$.items[0].identifier"}],
        )

        rights = node[f"{OKF}rights"][0]
        self.assertEqual(
            rights[f"{DC_TERMS}license"],
            [{"@id": f"{base}licences/open-government-licence"}],
        )
        self.assertEqual(
            rights[f"{OKF}assertionRights"],
            [{"@value": "Use is permitted under the stated licence."}],
        )
        self.assertEqual(
            node[f"{PROV}wasDerivedFrom"],
            [
                {"@id": f"{base}assertions/support-one"},
                {"@id": f"{base}assertions/support-two"},
            ],
        )


if __name__ == "__main__":
    unittest.main()
