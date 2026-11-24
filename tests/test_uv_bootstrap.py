from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class UvBootstrapTest(unittest.TestCase):
    def setUp(self) -> None:
        self.project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.bootstrap = (ROOT / "scripts/install_pinned_uv.sh").read_text(
            encoding="utf-8"
        )
        self.workflows = {
            name: (ROOT / ".github/workflows" / f"{name}.yml").read_text(
                encoding="utf-8"
            )
            for name in ("ci", "pages")
        }

    def test_uv_bootstrap_is_versioned_and_hash_locked(self) -> None:
        self.assertIn('required-version = "==0.13.4"', self.project)
        self.assertIn(
            "https://github.com/astral-sh/uv/releases/download/0.13.4/",
            self.bootstrap,
        )
        self.assertIn(
            "2b428396f12572d4429cf210ca234dd599a33b3af0958a4d5ed569d63e3f344f",
            self.bootstrap,
        )
        self.assertIn("sha256sum --check --status", self.bootstrap)
        self.assertIn('version="0.13.4"', self.bootstrap)
        self.assertIn(
            '"uv $version (7456b60bc 2026-10-20 x86_64-unknown-linux-gnu)"',
            self.bootstrap,
        )

    def test_ci_and_pages_install_the_exact_python_after_pinned_uv(self) -> None:
        for workflow_name, workflow in self.workflows.items():
            with self.subTest(workflow=workflow_name):
                bootstrap = workflow.index("bash scripts/install_pinned_uv.sh")
                install_python = workflow.index("uv python install 3.12.11")
                sync_python = workflow.index("uv sync --locked --python 3.12.11")
                self.assertLess(bootstrap, install_python)
                self.assertLess(install_python, sync_python)
                self.assertNotIn("actions/setup-python@", workflow)
                self.assertNotIn("setup-uv", workflow)

    def test_publication_contract_declares_all_environment_steps(self) -> None:
        contract = json.loads(
            (ROOT / "okf.publication.json").read_text(encoding="utf-8")
        )
        commands = {
            command["id"]: command["command"]
            for command in contract["tooling"]["commands"]
        }
        self.assertEqual(
            "bash scripts/install_pinned_uv.sh", commands["install-pinned-uv"]
        )
        self.assertEqual(
            "uv python install 3.12.11", commands["install-pinned-python"]
        )
        self.assertEqual(
            "uv sync --locked --python 3.12.11", commands["setup-environment"]
        )


if __name__ == "__main__":
    unittest.main()
