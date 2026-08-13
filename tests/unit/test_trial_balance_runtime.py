from __future__ import annotations

import copy

import pytest

from odoo_accounting_cli_v4.bridge.runtime import RuntimeFailure, _dispatch


_OPTIONS_COLUMNS = [
    {"name": "Balance", "expression_label": "balance", "figure_type": "monetary"},
    {"name": "Debit", "expression_label": "debit", "figure_type": "monetary"},
    {"name": "Credit", "expression_label": "credit", "figure_type": "monetary"},
    {"name": "Balance", "expression_label": "balance", "figure_type": "monetary"},
]
_RAW_LINES = [
    {
        "id": "account:bank",
        "parent_id": "trial-balance",
        "name": "1003 Bank",
        "level": 2,
        "unfoldable": False,
        "columns": [
            {"expression_label": "balance", "no_format": 0},
            {"expression_label": "debit", "no_format": 0.0},
            {"expression_label": "credit", "no_format": 123.45},
            {"expression_label": "balance", "no_format": -123.45},
        ],
    },
    {
        "id": "account:expense",
        "parent_id": "trial-balance",
        "name": "530101 R&D expense",
        "level": 2,
        "unfoldable": False,
        "columns": [
            {"expression_label": "balance", "no_format": 0},
            {"expression_label": "debit", "no_format": 123.45},
            {"expression_label": "credit", "no_format": 0.0},
            {"expression_label": "balance", "no_format": 123.45},
        ],
    },
    {
        "id": "total",
        "parent_id": False,
        "name": "Total",
        "level": 1,
        "unfoldable": False,
        "columns": [
            {"expression_label": "balance", "no_format": 0.0},
            {"expression_label": "debit", "no_format": 123.45},
            {"expression_label": "credit", "no_format": 123.45},
            {"expression_label": "balance", "no_format": 0.0},
        ],
    },
]


class FakeRegistry:
    def __init__(self, *, installed: bool = True) -> None:
        self.installed = installed

    def get(self, model_name: str):
        if self.installed and model_name in {
            "account.report",
            "account.move.line",
            "res.currency",
        }:
            return object()
        return None


class FakeSimpleModel:
    def __init__(self, *, access: bool = True) -> None:
        self.access = access

    def has_access(self, operation: str) -> bool:
        assert operation == "read"
        return self.access


class FakeCompanyModel(FakeSimpleModel):
    def __init__(self, *, visible: bool = True, access: bool = True) -> None:
        super().__init__(access=access)
        self.visible = visible

    def search_count(self, domain, limit=None):
        assert domain == [("id", "=", 7)]
        assert limit == 1
        return int(self.visible)

    def search_read(self, domain, *, fields, limit):
        assert domain == [("id", "=", 7)]
        assert fields == ["id", "currency_id"]
        assert limit == 1
        return [{"id": 7, "currency_id": [6, "CNY"]}] if self.visible else []


class FakeCurrencyModel(FakeSimpleModel):
    def search_read(self, domain, *, fields, limit):
        assert domain == [("id", "=", 6)]
        assert fields == ["id", "name", "decimal_places"]
        assert limit == 1
        return [{"id": 6, "name": "CNY", "decimal_places": 2}]


class FakeEffectiveReport:
    id = 12
    name = "Trial Balance"

    def __init__(self, lines) -> None:
        self.lines = lines
        self.options = None

    def get_report_information_readonly(self, options):
        self.options = copy.deepcopy(options)
        return {"lines": copy.deepcopy(self.lines)}


class FakeRootReport:
    def __init__(self, effective: FakeEffectiveReport) -> None:
        self.effective = effective
        self.previous = None

    def get_options(self, previous):
        self.previous = copy.deepcopy(previous)
        date_from = previous["date"]["date_from"] or "2025-01-01"
        return {
            "report_id": self.effective.id,
            "readonly_query": True,
            "all_entries": False,
            "date": {
                "date_from": date_from,
                "date_to": "2025-01-31",
                "mode": "range",
                "filter": "custom",
            },
            "columns": copy.deepcopy(_OPTIONS_COLUMNS),
        }


class FakeReportModel(FakeSimpleModel):
    def __init__(self, effective: FakeEffectiveReport, *, access: bool = True) -> None:
        super().__init__(access=access)
        self.effective = effective

    def browse(self, record_id: int):
        assert record_id == self.effective.id
        return self.effective


class FakeEnv:
    uid = 42

    def __init__(
        self,
        *,
        visible: bool = True,
        installed: bool = True,
        access: bool = True,
        lines=None,
        report_present: bool = True,
    ) -> None:
        self.registry = FakeRegistry(installed=installed)
        self.effective = FakeEffectiveReport(_RAW_LINES if lines is None else lines)
        self.root_report = FakeRootReport(self.effective) if report_present else None
        self.models = {
            "res.company": FakeCompanyModel(visible=visible, access=access),
            "res.currency": FakeCurrencyModel(access=access),
            "account.report": FakeReportModel(self.effective, access=access),
            "account.move.line": FakeSimpleModel(access=access),
        }

    def __getitem__(self, model_name: str):
        return self.models[model_name]

    def ref(self, xml_id: str, raise_if_not_found: bool = True):
        assert xml_id == "account_reports.trial_balance_report"
        assert raise_if_not_found is False
        return self.root_report


def _payload(**changes) -> dict:
    value = {
        "company_id": 7,
        "date_from": "2025-01-01",
        "date_to": "2025-01-31",
        "after_line_id": None,
        "limit": 101,
    }
    value.update(changes)
    return value


def test_trial_balance_dispatch_uses_one_fixed_readonly_report() -> None:
    env = FakeEnv()

    result = _dispatch(
        env, "account.report.trial_balance.read_page", _payload(), 7
    )

    assert result == {
        "user_id": 42,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "cursor_found": True,
        "report": {"key": "trial_balance", "name": "Trial Balance"},
        "date": {"from": "2025-01-01", "to": "2025-01-31"},
        "currency": {"id": 6, "code": "CNY", "decimal_places": 2},
        "basis": "posted_entries",
        "columns": [
            {"index": index, "label": column["name"], "expression_label": column["expression_label"]}
            for index, column in enumerate(_OPTIONS_COLUMNS)
        ],
        "lines": [
            {
                "id": "account:bank",
                "parent_id": "trial-balance",
                "name": "1003 Bank",
                "level": 2,
                "unfoldable": False,
                "values": ["0", "0", "123.45", "-123.45"],
            },
            {
                "id": "account:expense",
                "parent_id": "trial-balance",
                "name": "530101 R&D expense",
                "level": 2,
                "unfoldable": False,
                "values": ["0", "123.45", "0", "123.45"],
            },
            {
                "id": "total",
                "parent_id": None,
                "name": "Total",
                "level": 1,
                "unfoldable": False,
                "values": ["0", "123.45", "123.45", "0"],
            },
        ],
    }
    assert env.root_report.previous == {
        "all_entries": False,
        "date": {
            "date_from": "2025-01-01",
            "date_to": "2025-01-31",
            "mode": "range",
            "filter": "custom",
        },
    }
    assert env.effective.options["readonly_query"] is True


def test_trial_balance_dispatch_resumes_after_an_exact_opaque_line_id() -> None:
    result = _dispatch(
        FakeEnv(),
        "account.report.trial_balance.read_page",
        _payload(after_line_id="account:bank", limit=2),
        7,
    )
    assert result["cursor_found"] is True
    assert [line["id"] for line in result["lines"]] == ["account:expense", "total"]

    stale = _dispatch(
        FakeEnv(),
        "account.report.trial_balance.read_page",
        _payload(after_line_id="missing", limit=2),
        7,
    )
    assert stale["cursor_found"] is False
    assert stale["lines"] == []


@pytest.mark.parametrize(
    "payload",
    [
        _payload(extra=True),
        _payload(company_id=8),
        _payload(date_to="2025-01-32"),
        _payload(limit=True),
        _payload(after_line_id=""),
    ],
)
def test_trial_balance_dispatch_rejects_invalid_or_out_of_scope_payloads(payload) -> None:
    with pytest.raises(RuntimeFailure):
        _dispatch(FakeEnv(), "account.report.trial_balance.read_page", payload, 7)


@pytest.mark.parametrize(
    ("env", "expected"),
    [
        (FakeEnv(visible=False), (False, True, False)),
        (FakeEnv(installed=False), (True, False, False)),
        (FakeEnv(report_present=False), (True, False, False)),
        (FakeEnv(access=False), (True, True, False)),
    ],
)
def test_trial_balance_dispatch_short_circuits_runtime_gates(env, expected) -> None:
    result = _dispatch(
        env, "account.report.trial_balance.read_page", _payload(), 7
    )
    assert (
        result["company_visible"],
        result["module_installed"],
        result["access_allowed"],
    ) == expected
    assert result["columns"] == []
    assert result["lines"] == []
