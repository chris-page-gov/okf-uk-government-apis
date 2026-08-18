from __future__ import annotations

import sys
import unittest
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import verify_deployment as verifier  # noqa: E402


class DeploymentVerifierTest(unittest.TestCase):
    def deployment_files(self) -> dict[str, bytes]:
        routes = ("checksums.json", *verifier.IDENTITY_ROUTES)
        return {route: (verifier.BUNDLE / route).read_bytes() for route in routes}

    def test_exact_deployed_routes_pass(self) -> None:
        files = self.deployment_files()

        def fetch(url: str) -> bytes:
            return files[urlsplit(url).path.removeprefix("/bundle/")]

        self.assertEqual([], verifier.verify("https://example.test/bundle/", fetch))

    def test_changed_route_fails_identity(self) -> None:
        files = self.deployment_files()
        files["okf-explorer.json"] += b"\n"

        def fetch(url: str) -> bytes:
            return files[urlsplit(url).path.removeprefix("/bundle/")]

        errors = verifier.verify("https://example.test/bundle/", fetch)
        self.assertTrue(any("okf-explorer.json" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
