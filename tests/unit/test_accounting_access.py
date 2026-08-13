from __future__ import annotations

import io
import json
from types import SimpleNamespace

import pytest

from odoo_accounting_cli_v4.bridge.runtime import _dispatch
from odoo_accounting_cli_v4.capabilities.accounting_access import (
    read_accounting_access,
    validate_accounting_access_request,
)
from odoo_accounting_cli_v4.capabilities.master_data_lists import MasterDataListError
from odoo_accounting_cli_v4.cli import main
from odoo_accounting_cli_v4.registry import load_registry


GROUPS = [
    "base.group_user",
    "account.group_account_readonly",
    "account.group_account_invoice",
    "account.group_account_user",
    "account.group_account_manager",
]
MODELS = [
    "account.account",
    "account.journal",
    "account.move",
    "account.move.line",
    "account.report",
    "account.tax",
]


def _request() -> dict:
    return {
        "schema_version": "v1",
        "request_id": "a31769b9-c6ab-4975-9690-e96f1556bd34",
        "context": {
            "database": "v4-dev",
            "company_id": 1,
            "user_login": "odacv4_g5_accountant",
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": {},
    }


def _page() -> dict:
    return {
        "user_id": 5,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "user": {
            "id": 5,
            "login": "odacv4_g5_accountant",
            "name": "ODACV4 G5 Accountant",
            "active": True,
            "company_ids": [1, 2],
        },
        "company_id": 1,
        "groups": [
            {"xml_id": xml_id, "member": xml_id != "account.group_account_manager"}
            for xml_id in GROUPS
        ],
        "model_acl": [
            {
                "model": model,
                "read": True,
                "create": model in {"account.move", "account.move.line"},
                "write": model in {"account.move", "account.move.line"},
                "unlink": model in {"account.move", "account.move.line"},
            }
            for model in MODELS
        ],
    }


class Port:
    user_id = 5

    def inspect(self, *, company_id: int) -> dict:
        assert company_id == 1
        return _page()


def test_accounting_access_contract_and_cli() -> None:
    data = read_accounting_access(Port(), _request())
    assert data["user"]["id"] == 5
    assert data["groups"][-1] == {
        "xml_id": "account.group_account_manager",
        "member": False,
    }
    stdout, stderr = io.StringIO(), io.StringIO()
    result = main(
        ["read", "user.accounting_access.inspect", "--request", "-"],
        stdin=io.StringIO(json.dumps(_request())),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda selected, request: Port(),
    )
    document = json.loads(stdout.getvalue())
    assert result == 0 and stderr.getvalue() == ""
    assert document["odoo"]["model"] == "res.users"
    assert document["odoo"]["record_ids"] == [5]
    load_registry().validate_instance(
        "schemas/v1/user.accounting_access.inspect.response.schema.json", document
    )


class Model:
    def __init__(self, *, visible: bool = True, mutable: bool = False) -> None:
        self.visible = visible
        self.mutable = mutable

    def search_count(self, domain, limit=None):
        return 1 if self.visible else 0

    def has_access(self, operation: str) -> bool:
        return operation == "read" or self.mutable


class User:
    id = 5
    login = "odacv4_g5_accountant"
    name = "ODACV4 G5 Accountant"
    active = True
    company_ids = SimpleNamespace(ids=[2, 1])

    def has_group(self, xml_id: str) -> bool:
        return xml_id != "account.group_account_manager"


class Env:
    uid = 5
    user = User()

    def __init__(self) -> None:
        names = {"res.company", "res.users", "res.groups", "ir.model.access", *MODELS}
        self.models = {
            name: Model(mutable=name in {"account.move", "account.move.line"})
            for name in names
        }
        self.registry = SimpleNamespace(get=lambda name: self.models.get(name))

    def __getitem__(self, name: str) -> Model:
        return self.models[name]


def test_accounting_access_runtime_is_fixed_and_deterministic() -> None:
    result = _dispatch(
        Env(), "res.users.accounting_access.inspect", {"company_id": 1}, 1
    )
    assert result == _page()


@pytest.mark.parametrize(
    "mutate",
    [
        lambda request: request.update(extra=True),
        lambda request: request["parameters"].update(extra=True),
        lambda request: request["context"].update(company_id=True),
    ],
)
def test_accounting_access_rejects_invalid_requests(mutate) -> None:
    request = _request()
    mutate(request)
    with pytest.raises(MasterDataListError):
        validate_accounting_access_request(request)
