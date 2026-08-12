from __future__ import annotations

from pathlib import Path

import tomllib


def test_pi_skill_uses_registry_driven_routing() -> None:
    root = Path(__file__).resolve().parents[2]
    skill = root / "skills" / "odoo-accounting-cli-v4" / "SKILL.md"
    text = skill.read_text("utf-8")

    assert "name: odoo-accounting-cli-v4" in text
    assert "capabilities list" in text
    assert "capabilities describe" in text
    assert "read <capability-id> --request -" in text
    assert "缺少" in text and "澄清" in text
    assert "不得调用任意 Odoo 模型" in text


def test_pi_skill_is_declared_as_an_installed_data_file() -> None:
    root = Path(__file__).resolve().parents[2]
    project = tomllib.loads((root / "pyproject.toml").read_text("utf-8"))
    data_files = project["tool"]["setuptools"]["data-files"]

    assert data_files[
        "share/odoo-accounting-cli-v4/skills/odoo-accounting-cli-v4"
    ] == ["skills/odoo-accounting-cli-v4/SKILL.md"]
