from __future__ import annotations

import io
import json
from types import SimpleNamespace

import pytest

from odoo_accounting_cli_v4.bridge.environment_inspection import (
    OdooEnvironmentInspectionPort,
)
from odoo_accounting_cli_v4.bridge.runtime import _dispatch
from odoo_accounting_cli_v4.capabilities.environment_inspection import (
    read_environment_inspection,
    validate_environment_inspection_request,
)
from odoo_accounting_cli_v4.capabilities.master_data_lists import MasterDataListError
from odoo_accounting_cli_v4.cli import main
from odoo_accounting_cli_v4.registry import load_registry


CAPABILITIES = (
    "company.accounting_configuration.inspect",
    "diagnostic.accounting_environment.inspect",
)
MODULES = ("account", "account_reports", "base")
MODELS = (
    "account.account",
    "account.journal",
    "account.move",
    "account.move.line",
    "account.report",
    "account.tax",
    "ir.module.module",
    "res.company",
    "res.users",
)


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


def _company_data() -> dict:
    return {
        "company": {"id": 1, "name": "ODACV4 G5 China"},
        "currency": {"id": 6, "code": "CNY"},
        "country": {"id": 48, "code": "CN", "name": "China"},
        "fiscal_country": {"id": 48, "code": "CN", "name": "China"},
        "chart_template": "cn_oscg",
        "tax_calculation_rounding_method": "round_globally",
        "fiscal_year_end": {"month": 12, "day": 31},
        "anglo_saxon_accounting": False,
        "account_code_prefixes": {
            "bank": "1002",
            "cash": "1001",
            "transfer": "1012",
        },
        "suspense_account": {
            "id": 153,
            "code": "1004",
            "name": "Bank Suspense Account",
        },
        "pos_receivable_account": {
            "id": 58,
            "code": "1124",
            "name": "POS Receivable",
        },
        "opening": {"date": None, "move_id": None},
    }


def _diagnostic_data() -> dict:
    return {
        "company": {"id": 1, "name": "ODACV4 G5 China"},
        "user": {"id": 5, "login": "odacv4_g5_accountant"},
        "modules": [
            {"name": name, "state": "installed", "version": "19.0"}
            for name in MODULES
        ],
        "models": [
            {"model": name, "available": True, "read": True} for name in MODELS
        ],
        "transaction_read_only": True,
    }


class Port:
    user_id = 5

    def __init__(self, data: dict) -> None:
        self.data = data

    def inspect(self, *, company_id: int) -> dict:
        assert company_id == 1
        return {
            "user_id": 5,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "data": self.data,
        }


@pytest.mark.parametrize(
    ("capability_id", "data", "model", "record_ids"),
    [
        (
            "company.accounting_configuration.inspect",
            _company_data(),
            "res.company",
            [1],
        ),
        (
            "diagnostic.accounting_environment.inspect",
            _diagnostic_data(),
            "ir.module.module",
            [],
        ),
    ],
)
def test_inspection_contract_and_cli(
    capability_id: str, data: dict, model: str, record_ids: list[int]
) -> None:
    port = Port(data)
    assert read_environment_inspection(capability_id, port, _request()) == data
    stdout, stderr = io.StringIO(), io.StringIO()
    result = main(
        ["read", capability_id, "--request", "-"],
        stdin=io.StringIO(json.dumps(_request())),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda selected, request: Port(data),
    )
    document = json.loads(stdout.getvalue())
    assert result == 0 and stderr.getvalue() == ""
    assert document["data"] == data
    assert document["odoo"]["model"] == model
    assert document["odoo"]["record_ids"] == record_ids
    load_registry().validate_instance(
        f"schemas/v1/{capability_id}.response.schema.json", document
    )


@pytest.mark.parametrize("capability_id", CAPABILITIES)
@pytest.mark.parametrize(
    "mutate",
    [
        lambda request: request.update(extra=True),
        lambda request: request["parameters"].update(extra=True),
        lambda request: request["context"].update(company_id=True),
    ],
)
def test_inspection_rejects_invalid_requests(capability_id: str, mutate) -> None:
    request = _request()
    mutate(request)
    with pytest.raises(MasterDataListError):
        validate_environment_inspection_request(capability_id, request)


def test_diagnostic_rejects_inconsistent_fixed_matrices() -> None:
    data = _diagnostic_data()
    data["modules"].reverse()
    with pytest.raises(MasterDataListError, match="inconsistent"):
        read_environment_inspection(
            "diagnostic.accounting_environment.inspect", Port(data), _request()
        )


class Client:
    def __init__(self, page: dict) -> None:
        self.page = page
        self.calls: list[tuple[str, dict]] = []

    def invoke(self, action: str, payload: dict) -> dict:
        self.calls.append((action, payload))
        return self.page


@pytest.mark.parametrize(
    ("capability_id", "action"),
    [
        (
            "company.accounting_configuration.inspect",
            "res.company.accounting_configuration.inspect",
        ),
        (
            "diagnostic.accounting_environment.inspect",
            "accounting.environment.diagnostic.inspect",
        ),
    ],
)
def test_inspection_port_uses_only_the_fixed_action(
    capability_id: str, action: str
) -> None:
    page = {
        "user_id": 5,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "data": {},
    }
    client = Client(page)
    port = OdooEnvironmentInspectionPort(client, capability_id)
    assert port.inspect(company_id=1) == page
    assert port.user_id == 5
    assert client.calls == [(action, {"company_id": 1})]


class Model:
    def __init__(self, rows: list[dict]) -> None:
        self.rows = rows

    def with_context(self, **context):
        assert context == {"active_test": False}
        return self

    def has_access(self, operation: str) -> bool:
        return operation == "read"

    def search_count(self, domain, limit=None):
        assert limit == 1
        return 1

    def search_read(self, domain, fields, limit=None, order=None):
        rows = self.rows
        if domain and domain[0][0] == "id":
            rows = [row for row in rows if row["id"] == domain[0][2]]
        elif domain and domain[0][0] == "name":
            rows = [row for row in rows if row["name"] in domain[0][2]]
        if order == "name":
            rows = sorted(rows, key=lambda row: row["name"])
        if limit is not None:
            rows = rows[:limit]
        return [{field: row[field] for field in fields} for row in rows]


class Env:
    uid = 5
    user = SimpleNamespace(id=5, login="odacv4_g5_accountant")

    def __init__(self) -> None:
        company = {
            "id": 1,
            "name": "ODACV4 G5 China",
            "currency_id": [6, "CNY"],
            "country_id": [48, "China"],
            "account_fiscal_country_id": [48, "China"],
            "chart_template": "cn_oscg",
            "tax_calculation_rounding_method": "round_globally",
            "fiscalyear_last_month": "12",
            "fiscalyear_last_day": 31,
            "anglo_saxon_accounting": False,
            "bank_account_code_prefix": "1002",
            "cash_account_code_prefix": "1001",
            "transfer_account_code_prefix": "1012",
            "account_journal_suspense_account_id": [153, "1004"],
            "account_default_pos_receivable_account_id": [58, "1124"],
            "account_opening_move_id": False,
            "account_opening_date": False,
        }
        self.models = {name: Model([]) for name in MODELS}
        self.models.update(
            {
                "res.company": Model([company]),
                "res.currency": Model([{"id": 6, "name": "CNY"}]),
                "res.country": Model([{"id": 48, "name": "China", "code": "CN"}]),
                "account.account": Model(
                    [
                        {
                            "id": 153,
                            "code": "1004",
                            "name": "Bank Suspense Account",
                        },
                        {"id": 58, "code": "1124", "name": "POS Receivable"},
                    ]
                ),
                "ir.module.module": Model(
                    [
                        {
                            "name": name,
                            "state": "installed",
                            "latest_version": "19.0",
                        }
                        for name in MODULES
                    ]
                ),
                "res.users": Model([]),
            }
        )
        self.registry = SimpleNamespace(get=lambda name: self.models.get(name))

    def __getitem__(self, name: str) -> Model:
        return self.models[name]


def test_company_configuration_runtime_is_fixed_and_deterministic() -> None:
    result = _dispatch(
        Env(), "res.company.accounting_configuration.inspect", {"company_id": 1}, 1
    )
    assert result == {
        "user_id": 5,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "data": _company_data(),
    }


def test_environment_diagnostic_runtime_is_fixed_and_deterministic() -> None:
    result = _dispatch(
        Env(), "accounting.environment.diagnostic.inspect", {"company_id": 1}, 1
    )
    assert result == {
        "user_id": 5,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "data": _diagnostic_data(),
    }
