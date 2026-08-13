"""Live accounting-partner search against fixture v1.

Fixture v1 contains exactly one customer and one vendor for each company.  The
two-item search therefore proves one real cursor transition.  It does not
claim traversal beyond the second (terminal) page.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

from odoo_accounting_cli_v4.registry import load_registry


_CONFIG_ENV = "ODOO_ACCOUNTING_CLI_V4_CONFIG"
_CAPABILITY = "partner.accounting.search"
_ALIASES = ("v4-dev", "v4-e2e")
_COMPANY_CODES = {1: "CN", 2: "SG"}


def _invoke(
    alias: str,
    company_id: int,
    parameters: dict,
    *,
    case: str,
) -> dict:
    project_root = Path(__file__).resolve().parents[2]
    request_id = str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"odacv4:{alias}:{company_id}:{_CAPABILITY}:{case}",
        )
    )
    request = {
        "schema_version": "v1",
        "request_id": request_id,
        "context": {
            "database": alias,
            "company_id": company_id,
            "user_login": os.environ.get(
                "ODACV4_LIVE_USER_LOGIN", "odacv4_g5_accountant"
            ),
            "language": os.environ.get("ODACV4_LIVE_LANGUAGE", "en_US"),
            "timezone": os.environ.get(
                "ODACV4_LIVE_TIMEZONE", "Asia/Shanghai"
            ),
        },
        "parameters": parameters,
    }
    registry = load_registry()
    registry.validate_instance(
        f"schemas/v1/{_CAPABILITY}.request.schema.json", request
    )
    environment = os.environ.copy()
    environment[_CONFIG_ENV] = os.environ[_CONFIG_ENV]
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = os.pathsep.join(
        part
        for part in (str(project_root / "src"), environment.get("PYTHONPATH"))
        if part
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "odoo_accounting_cli_v4",
            "read",
            _CAPABILITY,
            "--request",
            "-",
        ],
        cwd=project_root,
        env=environment,
        input=json.dumps(request, sort_keys=True, separators=(",", ":")),
        text=True,
        capture_output=True,
        check=False,
        timeout=240,
    )
    assert completed.returncode == 0, completed.stdout
    assert completed.stderr == ""
    assert len(completed.stdout.splitlines()) == 1
    document = json.loads(completed.stdout)
    registry.validate_instance(
        f"schemas/v1/{_CAPABILITY}.response.schema.json", document
    )
    assert document["schema_version"] == "v1"
    assert document["request_id"] == request_id
    assert document["capability"] == _CAPABILITY
    assert document["success"] is True
    assert document["status"] == "verified"
    assert document["error"] is None
    assert document["odoo"]["database"] == alias
    assert document["odoo"]["company_id"] == company_id
    assert isinstance(document["odoo"]["user_id"], int)
    assert document["odoo"]["user_id"] > 0
    assert document["odoo"]["model"] == "res.partner"
    assert document["odoo"]["record_ids"] == [
        item["id"] for item in document["data"]["items"]
    ]
    return document


def _assert_fixture_partner(item: dict, *, company_id: int, role: str) -> None:
    code = _COMPANY_CODES[company_id]
    title_role = role.title()
    assert item["complete_name"] == f"ODACV4 FX1 {code} {title_role}"
    assert item["ref"] == f"ODACV4-FX1-{code}-{role}"
    assert item["active"] is True
    assert item["is_company"] is False
    assert item["company_id"] == company_id
    assert (item["customer_rank"] > 0) is (role == "CUSTOMER")
    assert (item["supplier_rank"] > 0) is (role == "VENDOR")
    for key in ("receivable_account", "payable_account"):
        account = item[key]
        assert isinstance(account, dict)
        assert set(account) == {"id", "code", "name"}
        assert isinstance(account["id"], int) and account["id"] > 0
        assert isinstance(account["code"], str) and account["code"]
        assert isinstance(account["name"], str) and account["name"]


@pytest.mark.integration
@pytest.mark.parametrize("alias", _ALIASES)
@pytest.mark.parametrize("company_id", tuple(_COMPANY_CODES))
def test_partner_search_scopes_roles_queries_and_one_real_cursor_transition(
    alias: str, company_id: int
) -> None:
    if not os.environ.get(_CONFIG_ENV):
        pytest.skip(f"{_CONFIG_ENV} is not configured")

    first = _invoke(
        alias,
        company_id,
        {"role": "both", "query": None, "limit": 1, "cursor": None},
        case="both-page-1",
    )
    assert len(first["data"]["items"]) == 1
    assert first["data"]["has_more"] is True
    assert isinstance(first["data"]["next_cursor"], str)
    second = _invoke(
        alias,
        company_id,
        {
            "role": "both",
            "query": None,
            "limit": 1,
            "cursor": first["data"]["next_cursor"],
        },
        case="both-page-2",
    )
    assert len(second["data"]["items"]) == 1
    assert second["data"]["has_more"] is False
    assert second["data"]["next_cursor"] is None
    items = first["data"]["items"] + second["data"]["items"]
    assert [(item["complete_name"], item["id"]) for item in items] == sorted(
        (item["complete_name"], item["id"]) for item in items
    )
    assert len({item["id"] for item in items}) == 2
    assert {item["ref"] for item in items} == {
        f"ODACV4-FX1-{_COMPANY_CODES[company_id]}-CUSTOMER",
        f"ODACV4-FX1-{_COMPANY_CODES[company_id]}-VENDOR",
    }
    for item in items:
        _assert_fixture_partner(
            item,
            company_id=company_id,
            role=item["ref"].rsplit("-", 1)[-1],
        )

    customer = _invoke(
        alias,
        company_id,
        {
            "role": "customer",
            "query": f"ODACV4 FX1 {_COMPANY_CODES[company_id]} Customer",
            "limit": 10,
            "cursor": None,
        },
        case="customer-complete-name-query",
    )
    assert customer["data"]["has_more"] is False
    assert len(customer["data"]["items"]) == 1
    _assert_fixture_partner(
        customer["data"]["items"][0],
        company_id=company_id,
        role="CUSTOMER",
    )

    vendor = _invoke(
        alias,
        company_id,
        {
            "role": "vendor",
            "query": f"ODACV4-FX1-{_COMPANY_CODES[company_id]}-VENDOR",
            "limit": 10,
            "cursor": None,
        },
        case="vendor-ref-query",
    )
    assert vendor["data"]["has_more"] is False
    assert len(vendor["data"]["items"]) == 1
    _assert_fixture_partner(
        vendor["data"]["items"][0],
        company_id=company_id,
        role="VENDOR",
    )
