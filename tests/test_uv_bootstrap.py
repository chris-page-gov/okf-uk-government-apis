from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_uv_bootstrap_is_versioned_and_hash_locked() -> None:
    project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    bootstrap = (ROOT / "scripts/install_pinned_uv.sh").read_text(encoding="utf-8")
    workflows = [
        (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"),
        (ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8"),
    ]

    assert 'required-version = "==0.13.4"' in project
    assert "https://github.com/astral-sh/uv/releases/download/0.13.4/" in bootstrap
    assert "2b428396f12572d4429cf210ca234dd599a33b3af0958a4d5ed569d63e3f344f" in bootstrap
    assert "sha256sum --check --status" in bootstrap
    assert 'uv 0.13.4 (7456b60bc 2026-10-20 x86_64-unknown-linux-gnu)' in bootstrap
    for workflow in workflows:
        assert "bash scripts/install_pinned_uv.sh" in workflow
        assert "setup-uv" not in workflow
