from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_publication_contract as checker  # noqa: E402


class PublicationContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = checker.load_contract()

    def test_repository_contract_is_locally_consistent(self) -> None:
        self.assertEqual([], checker.validate_contract(self.contract))

    def test_reader_browser_acceptance_is_required_for_both_descriptors(self) -> None:
        self.assertEqual("required", self.contract["ci"]["browser"]["ordinary"]["policy"])
        journey_ids = {row["id"] for row in self.contract["verification"]["journeys"]}
        self.assertTrue({"core-guide-to-reader", "metadata-guide-to-reader"}.issubset(journey_ids))

    def test_publication_contract_rejects_disabled_browser_acceptance(self) -> None:
        candidate = copy.deepcopy(self.contract)
        candidate["ci"]["browser"]["ordinary"]["policy"] = "not-applicable"
        candidate["verification"]["required"] = False
        errors = checker.validate_contract(candidate)
        self.assertIn("CI must require the canonical Reader browser acceptance", errors)
        self.assertIn("publication verification must be required", errors)

    def test_controlled_change_requires_guidance_and_changelog(self) -> None:
        self.assertEqual(
            [
                "controlled changes require CHANGELOG.md in the same change set",
                "controlled changes require README.md or AGENTS.md guidance in lockstep",
            ],
            checker.lockstep_errors(
                self.contract,
                ["scripts/build_publication.py"],
            ),
        )

    def test_controlled_change_accepts_lockstep_material(self) -> None:
        self.assertEqual(
            [],
            checker.lockstep_errors(
                self.contract,
                [
                    "scripts/build_publication.py",
                    "README.md",
                    "CHANGELOG.md",
                ],
            ),
        )


if __name__ == "__main__":
    unittest.main()
