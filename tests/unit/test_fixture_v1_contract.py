from __future__ import annotations

import ast
from pathlib import Path

import tomllib


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "fixtures" / "v1" / "accounting_fixture.py"
DEFINITION_SHA256 = "35f5befc6621975e1d4dc9db425b19e3c1866c5c9093420a19c59c6f9311633d"


def test_fixture_v1_is_fixed_to_the_two_synthetic_databases() -> None:
    text = FIXTURE.read_text(encoding="utf-8")
    tree = ast.parse(text)
    assert 'DATABASES = ("odoo_cli_v4_dev", "odoo_cli_v4_e2e")' in text
    assert "ODACV4_FIXTURE_MODE" in text
    assert 'mode == "apply"' in text
    assert 'mode != "verify"' in text
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"unlink", "sudo_execute"}
        for node in ast.walk(tree)
    )


def test_fixture_v1_freezes_the_required_core_document_values() -> None:
    text = FIXTURE.read_text(encoding="utf-8")
    for expected in (
        'INVOICE_DATE = "2025-01-20"',
        'BILL_DATE = "2025-01-21"',
        'PAYMENT_DATE = "2025-01-25"',
        'INVOICE_UNTAXED = Decimal("100.00")',
        'BILL_TOTAL = Decimal("113.00")',
        'PARTIAL_PAYMENT = Decimal("50.00")',
        '"customer invoice mismatch',
        '"vendor bill mismatch',
        '"partial payment mismatch',
    ):
        assert expected in text


def test_fixture_v1_readme_does_not_overclaim_g2_completion() -> None:
    text = (ROOT / "fixtures" / "v1" / "README.md").read_text(encoding="utf-8")
    assert "remain separate later\nversions" in text
    assert "must not be described as the complete G2 fixture matrix" in text


def test_fixture_v1_definition_hash_is_stable() -> None:
    tree = ast.parse(FIXTURE.read_text(encoding="utf-8"))
    prelude = []
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "odoo":
            continue
        prelude.append(node)
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "DEFINITION_SHA256"
            for target in node.targets
        ):
            break
    namespace: dict[str, object] = {}
    exec(compile(ast.Module(prelude, type_ignores=[]), str(FIXTURE), "exec"), namespace)

    assert namespace["DEFINITION_SHA256"] == DEFINITION_SHA256


def test_fixture_v1_is_declared_as_an_installed_data_file() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text("utf-8"))
    data_files = project["tool"]["setuptools"]["data-files"]

    assert data_files["share/odoo-accounting-cli-v4/fixtures/v1"] == [
        "fixtures/v1/accounting_fixture.py",
        "fixtures/v1/README.md",
    ]
