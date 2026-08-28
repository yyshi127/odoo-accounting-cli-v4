from __future__ import annotations

import copy
from datetime import date

import pytest

from odoo_accounting_cli_v4.bridge.runtime import (
    RuntimeFailure,
    _cursor_factory_for,
    _dispatch,
    _rollback_only_cursor,
)

_OPTIONS_COLUMNS = [
    {"name": "Date", "expression_label": "date", "figure_type": "date"},
    {"name": "Partner", "expression_label": "partner_name", "figure_type": "string"},
    {"name": "Debit", "expression_label": "debit", "figure_type": "monetary"},
    {"name": "Count", "expression_label": "count", "figure_type": "integer"},
]
_RAW_LINES = [
    {
        "id": "line:1",
        "parent_id": False,
        "name": "Entry",
        "level": 1,
        "unfoldable": False,
        "columns": [
            {"expression_label": "date", "no_format": date(2025, 1, 10)},
            {"expression_label": "partner_name", "no_format": "Alpha"},
            {"expression_label": "debit", "no_format": 125.5},
            {"expression_label": "count", "no_format": 2},
        ],
    }
]


class FakeRegistry:
    def get(self, model_name: str):
        return (
            object()
            if model_name
            in {
                "account.asset",
                "account.report",
                "account.move",
                "account.move.line",
                "account.cash.flow.line",
                "account.tax",
                "account.journal",
                "account.bank.statement",
                "account.bank.statement.line",
                "res.currency",
                "res.country",
                "res.partner",
            }
            else None
        )


class FakeSimpleModel:
    def has_access(self, operation: str) -> bool:
        assert operation == "read"
        return True


class FakeCompanyModel(FakeSimpleModel):
    def search_count(self, domain, limit=None):
        assert domain == [("id", "=", 7)]
        assert limit == 1
        return 1

    def search_read(self, domain, *, fields, limit):
        assert domain == [("id", "=", 7)]
        assert fields == ["id", "currency_id"]
        assert limit == 1
        return [{"id": 7, "currency_id": [6, "CNY"]}]


class FakeCurrencyModel(FakeSimpleModel):
    def search_read(self, domain, *, fields, limit):
        assert domain == [("id", "=", 6)]
        assert fields == ["id", "name", "decimal_places"]
        assert limit == 1
        return [{"id": 6, "name": "CNY", "decimal_places": 2}]


class FakeBankJournalModel(FakeSimpleModel):
    def __init__(self, *, available: bool = True) -> None:
        self.available = available
        self.context = None

    def with_context(self, **context):
        self.context = context
        return self

    def search_count(self, domain, *, limit):
        assert self.context == {
            "active_test": False,
            "allowed_company_ids": [7],
        }
        assert domain == [
            ("id", "=", 9),
            ("company_id", "=", 7),
            ("type", "=", "bank"),
        ]
        assert limit == 1
        return int(self.available)


class FakePartnerModel(FakeSimpleModel):
    def __init__(self, *, available: bool = True) -> None:
        self.available = available
        self.context = None

    def with_context(self, **context):
        self.context = context
        return self

    def search_count(self, domain, *, limit):
        assert self.context == {
            "active_test": False,
            "allowed_company_ids": [7],
        }
        assert domain == [
            ("id", "=", 17),
            "|",
            ("company_id", "=", False),
            ("company_id", "=", 7),
        ]
        assert limit == 1
        return int(self.available)


class FakeCountryModel(FakeSimpleModel):
    def __init__(self, code: str = "CN") -> None:
        self.code = code

    def search_read(self, domain, *, fields, limit):
        assert domain == [("id", "=", 86)]
        assert fields == ["id", "code"]
        assert limit == 1
        return [{"id": 86, "code": self.code}]


class FakeLocalizedCompanyModel(FakeCompanyModel):
    def __init__(self, chart_template: str) -> None:
        self.chart_template = chart_template

    def search_read(self, domain, *, fields, limit):
        if fields == ["id", "account_fiscal_country_id", "chart_template"]:
            assert domain == [("id", "=", 7)]
            assert limit == 1
            return [
                {
                    "id": 7,
                    "account_fiscal_country_id": [86, "Fiscal Country"],
                    "chart_template": self.chart_template,
                }
            ]
        return super().search_read(domain, fields=fields, limit=limit)


class FakeEffectiveReport:
    id = 12
    name = "General Ledger"

    def __init__(self) -> None:
        self.normal_called = False

    def get_report_information(self, options):
        self.normal_called = True
        assert options["readonly_query"] is False
        return {"lines": copy.deepcopy(_RAW_LINES)}

    def get_report_information_readonly(self, options):
        raise AssertionError("temp-table reports must use the normal report method")


class FakeRootReport:
    def __init__(self, effective: FakeEffectiveReport) -> None:
        self.effective = effective

    def get_options(self, previous):
        return {
            "report_id": self.effective.id,
            "readonly_query": False,
            "all_entries": False,
            "date": {
                "date_from": previous["date"]["date_from"],
                "date_to": previous["date"]["date_to"],
                "mode": "range",
                "filter": "custom",
            },
            "columns": copy.deepcopy(_OPTIONS_COLUMNS),
        }


class FakeReportModel(FakeSimpleModel):
    def __init__(self, effective: FakeEffectiveReport) -> None:
        self.effective = effective

    def browse(self, record_id: int):
        assert record_id == self.effective.id
        return self.effective


class FakeEnv:
    uid = 42

    def __init__(self) -> None:
        self.registry = FakeRegistry()
        self.effective = FakeEffectiveReport()
        self.root = FakeRootReport(self.effective)
        self.models = {
            "res.company": FakeCompanyModel(),
            "res.currency": FakeCurrencyModel(),
            "account.report": FakeReportModel(self.effective),
            "account.asset": FakeSimpleModel(),
            "account.move": FakeSimpleModel(),
            "account.move.line": FakeSimpleModel(),
            "account.cash.flow.line": FakeSimpleModel(),
            "account.tax": FakeSimpleModel(),
            "account.journal": FakeBankJournalModel(),
            "account.bank.statement": FakeSimpleModel(),
            "account.bank.statement.line": FakeSimpleModel(),
            "res.country": FakeCountryModel(),
            "res.partner": FakePartnerModel(),
        }

    def __getitem__(self, model_name: str):
        return self.models[model_name]

    def ref(self, xml_id: str, raise_if_not_found: bool = True):
        assert xml_id == "account_reports.general_ledger_report"
        assert raise_if_not_found is False
        return self.root


def test_typed_report_runtime_serializes_each_fixed_column_type() -> None:
    env = FakeEnv()
    result = _dispatch(
        env,
        "account.report.general_ledger.read_page",
        {
            "company_id": 7,
            "date_from": "2025-01-01",
            "date_to": "2025-01-31",
            "after_line_id": None,
            "limit": 101,
        },
        7,
    )

    assert env.effective.normal_called is True
    assert result["columns"] == [
        {"index": index, **column}
        for index, column in enumerate(
            [
                {"label": "Date", "expression_label": "date", "figure_type": "date"},
                {
                    "label": "Partner",
                    "expression_label": "partner_name",
                    "figure_type": "string",
                },
                {
                    "label": "Debit",
                    "expression_label": "debit",
                    "figure_type": "monetary",
                },
                {
                    "label": "Count",
                    "expression_label": "count",
                    "figure_type": "integer",
                },
            ]
        )
    ]
    assert result["lines"][0]["values"] == ["2025-01-10", "Alpha", "125.5", "2"]


@pytest.mark.parametrize(
    ("action", "xml_id", "report_key", "mode", "country_code", "chart_template"),
    [
        (
            "account.report.deferred_expense.read_page",
            "account_reports.deferred_expense_report",
            "deferred_expense",
            "range",
            None,
            None,
        ),
        (
            "account.report.deferred_revenue.read_page",
            "account_reports.deferred_revenue_report",
            "deferred_revenue",
            "range",
            None,
            None,
        ),
        (
            "account.report.multicurrency_revaluation.read_page",
            "account_reports.multicurrency_revaluation_report",
            "multicurrency_revaluation",
            "single",
            None,
            None,
        ),
        (
            "account.report.china_balance_sheet.read_page",
            "l10n_cn_reports.account_financial_report_cn_balancesheet0",
            "china_balance_sheet",
            "single",
            "CN",
            "cn_oscg",
        ),
        (
            "account.report.china_profit_and_loss.read_page",
            "l10n_cn_reports.account_financial_report_cn_profitloss0",
            "china_profit_and_loss",
            "range",
            "CN",
            "cn_oscg",
        ),
        (
            "account.report.china_cash_flow.read_page",
            "l10n_cn_reports.account_report_cn_cs_flow",
            "china_cash_flow",
            "range",
            "CN",
            "cn_oscg",
        ),
        (
            "account.report.singapore_gst.read_page",
            "l10n_sg.tax_report",
            "singapore_gst",
            "range",
            "SG",
            "sg",
        ),
    ],
)
def test_remaining_reports_use_the_fixed_readonly_odoo_report(
    action: str,
    xml_id: str,
    report_key: str,
    mode: str,
    country_code: str | None,
    chart_template: str | None,
) -> None:
    env = FakeEnv()
    if country_code is not None:
        env.models["res.company"] = FakeLocalizedCompanyModel(chart_template)
        env.models["res.country"] = FakeCountryModel(country_code)
    env.ref = lambda selected, raise_if_not_found=True: (
        env.root if selected == xml_id and raise_if_not_found is False else None
    )
    env.root.get_options = lambda previous: {
        "report_id": env.effective.id,
        "readonly_query": True,
        "all_entries": False,
        "date": {
            "date_from": previous["date"]["date_from"] or "2025-01-01",
            "date_to": previous["date"]["date_to"],
            "mode": mode,
            "filter": "custom",
        },
        "columns": copy.deepcopy(_OPTIONS_COLUMNS),
    }
    env.effective.get_report_information_readonly = lambda _options: {
        "lines": copy.deepcopy(_RAW_LINES)
    }
    env.effective.get_report_information = lambda _options: (_ for _ in ()).throw(
        AssertionError("remaining reports must use the readonly report method")
    )

    result = _dispatch(
        env,
        action,
        {
            "company_id": 7,
            "date_from": None if mode == "single" else "2025-01-01",
            "date_to": "2025-01-31",
            "after_line_id": None,
            "limit": 101,
        },
        7,
    )

    assert result["report"]["key"] == report_key
    assert result["lines"][0]["id"] == "line:1"


def test_bank_reconciliation_requires_and_preserves_a_company_bank_journal() -> None:
    env = FakeEnv()
    env.ref = lambda selected, raise_if_not_found=True: (
        env.root
        if selected == "account_reports.bank_reconciliation_report"
        and raise_if_not_found is False
        else None
    )

    def get_options(previous):
        assert previous["bank_reconciliation_report_journal_id"] == 9
        return {
            "report_id": env.effective.id,
            "readonly_query": True,
            "all_entries": False,
            "bank_reconciliation_report_journal_id": 9,
            "date": {
                "date_from": "2025-01-01",
                "date_to": previous["date"]["date_to"],
                "mode": "single",
                "filter": "custom",
            },
            "columns": copy.deepcopy(_OPTIONS_COLUMNS),
        }

    env.root.get_options = get_options
    env.effective.get_report_information_readonly = lambda _options: {
        "lines": copy.deepcopy(_RAW_LINES)
    }
    env.effective.get_report_information = lambda _options: (_ for _ in ()).throw(
        AssertionError("bank reconciliation must use the readonly report method")
    )

    result = _dispatch(
        env,
        "account.report.bank_reconciliation.read_page",
        {
            "company_id": 7,
            "date_from": None,
            "date_to": "2025-01-31",
            "after_line_id": None,
            "limit": 101,
            "journal_id": 9,
        },
        7,
    )

    assert result["report"]["key"] == "bank_reconciliation"
    assert result["lines"][0]["id"] == "line:1"
    assert (
        _cursor_factory_for("account.report.bank_reconciliation.read_page", {})
        is not _rollback_only_cursor
    )


def test_bank_reconciliation_rejects_a_journal_outside_the_company_scope() -> None:
    env = FakeEnv()
    env.models["account.journal"] = FakeBankJournalModel(available=False)
    env.ref = lambda selected, raise_if_not_found=True: (
        env.root
        if selected == "account_reports.bank_reconciliation_report"
        and raise_if_not_found is False
        else None
    )

    with pytest.raises(RuntimeFailure) as caught:
        _dispatch(
            env,
            "account.report.bank_reconciliation.read_page",
            {
                "company_id": 7,
                "date_from": None,
                "date_to": "2025-01-31",
                "after_line_id": None,
                "limit": 101,
                "journal_id": 9,
            },
            7,
        )

    assert caught.value.code == "company_unavailable"


@pytest.mark.parametrize(
    ("action", "xml_id", "report_key", "mode", "unreconciled"),
    [
        (
            "account.report.customer_statement.read_page",
            "account_reports.customer_statement_report",
            "customer_statement",
            "range",
            False,
        ),
        (
            "account.report.followup.read_page",
            "account_reports.followup_report",
            "followup",
            "single",
            True,
        ),
    ],
)
def test_partner_reports_force_one_partner_posted_entries_and_unfold_all(
    action: str,
    xml_id: str,
    report_key: str,
    mode: str,
    unreconciled: bool,
) -> None:
    env = FakeEnv()
    env.ref = lambda selected, raise_if_not_found=True: (
        env.root if selected == xml_id and raise_if_not_found is False else None
    )

    def get_options(previous):
        assert previous == {
            "all_entries": False,
            "date": {
                "date_from": "2025-01-01" if mode == "range" else False,
                "date_to": "2025-01-31",
                "mode": mode,
                "filter": "custom",
            },
            "partner_ids": [17],
            "unfold_all": True,
        }
        return {
            "report_id": env.effective.id,
            "readonly_query": True,
            "all_entries": False,
            "date": {
                "date_from": "2025-01-01",
                "date_to": "2025-01-31",
                "mode": mode,
                "filter": "custom",
            },
            "columns": copy.deepcopy(_OPTIONS_COLUMNS),
            "partner_ids": [17],
            "unfold_all": True,
            "unreconciled": unreconciled,
        }

    env.root.get_options = get_options
    env.effective.get_report_information_readonly = lambda _options: {
        "lines": copy.deepcopy(_RAW_LINES)
    }
    env.effective.get_report_information = lambda _options: (_ for _ in ()).throw(
        AssertionError("partner reports must use the readonly report method")
    )

    result = _dispatch(
        env,
        action,
        {
            "company_id": 7,
            "date_from": "2025-01-01" if mode == "range" else None,
            "date_to": "2025-01-31",
            "after_line_id": None,
            "limit": 101,
            "partner_id": 17,
        },
        7,
    )

    assert result["report"]["key"] == report_key
    assert result["basis"] == "posted_entries"
    assert result["lines"][0]["id"] == "line:1"


def test_partner_report_rejects_a_partner_outside_the_company_scope() -> None:
    env = FakeEnv()
    env.models["res.partner"] = FakePartnerModel(available=False)
    env.ref = lambda selected, raise_if_not_found=True: (
        env.root
        if selected == "account_reports.customer_statement_report"
        and raise_if_not_found is False
        else None
    )

    with pytest.raises(RuntimeFailure) as caught:
        _dispatch(
            env,
            "account.report.customer_statement.read_page",
            {
                "company_id": 7,
                "date_from": "2025-01-01",
                "date_to": "2025-01-31",
                "after_line_id": None,
                "limit": 101,
                "partner_id": 17,
            },
            7,
        )

    assert caught.value.code == "company_unavailable"


def test_localized_report_is_unavailable_for_the_wrong_company_configuration() -> None:
    env = FakeEnv()
    env.models["res.company"] = FakeLocalizedCompanyModel("sg")
    env.models["res.country"] = FakeCountryModel("SG")
    env.ref = lambda *_args, **_kwargs: (_ for _ in ()).throw(
        AssertionError("a CN report must not resolve in an SG company")
    )

    result = _dispatch(
        env,
        "account.report.china_balance_sheet.read_page",
        {
            "company_id": 7,
            "date_from": None,
            "date_to": "2025-01-31",
            "after_line_id": None,
            "limit": 101,
        },
        7,
    )

    assert result["company_visible"] is True
    assert result["module_installed"] is False
    assert result["access_allowed"] is False
    assert result["lines"] == []


def test_asset_report_normalizes_its_real_columns_and_empty_cells() -> None:
    asset_columns = [
        {
            "name": "Acquisition Date",
            "expression_label": "acquisition_date",
            "figure_type": "date",
        },
        {"name": "Method", "expression_label": "method", "figure_type": "string"},
        {
            "name": "Duration / Rate",
            "expression_label": "duration_rate",
            "figure_type": "string",
        },
        {
            "name": "01/01/2025",
            "expression_label": "assets_date_from",
            "figure_type": "monetary",
        },
        {"name": "+", "expression_label": "assets_plus", "figure_type": "monetary"},
        {"name": "-", "expression_label": "assets_minus", "figure_type": "monetary"},
        {
            "name": "01/31/2025",
            "expression_label": "assets_date_to",
            "figure_type": "monetary",
        },
        {
            "name": "01/01/2025",
            "expression_label": "depre_date_from",
            "figure_type": "monetary",
        },
        {"name": "+", "expression_label": "depre_plus", "figure_type": "monetary"},
        {"name": "-", "expression_label": "depre_minus", "figure_type": "monetary"},
        {
            "name": "01/31/2025",
            "expression_label": "depre_date_to",
            "figure_type": "monetary",
        },
        {"name": "", "expression_label": "balance", "figure_type": "monetary"},
    ]

    def cells(values):
        return [
            {"expression_label": column["expression_label"], "no_format": value}
            for column, value in zip(asset_columns, values, strict=True)
        ]

    monetary_values = [1000, 200, 0, 1200, 300, 50, 0, 350, 850]

    def asset_options(previous):
        return {
            "report_id": 12,
            "readonly_query": False,
            "all_entries": False,
            "date": {
                "date_from": previous["date"]["date_from"],
                "date_to": previous["date"]["date_to"],
                "mode": "range",
                "filter": "custom",
            },
            "columns": copy.deepcopy(asset_columns),
        }

    def report_information(_options):
        return {
            "lines": [
                {
                    "id": "asset:group",
                    "parent_id": False,
                    "name": "Assets",
                    "level": 1,
                    "unfoldable": True,
                    "columns": cells(["", "", "", *monetary_values]),
                },
                {
                    "id": "asset:1",
                    "parent_id": "asset:group",
                    "name": "Asset",
                    "level": 2,
                    "unfoldable": False,
                    "columns": cells(["01/10/2025", "Linear", "5 y", *monetary_values]),
                },
                {
                    "id": "asset:total",
                    "parent_id": False,
                    "name": "Total",
                    "level": 1,
                    "unfoldable": False,
                    "columns": cells(["", "", "", *monetary_values]),
                },
            ]
        }

    payload = {
        "company_id": 7,
        "date_from": "2025-01-01",
        "date_to": "2025-01-31",
        "after_line_id": None,
        "limit": 101,
    }
    asset_env = FakeEnv()
    asset_env.root.get_options = asset_options
    asset_env.effective.name = "Depreciation Schedule"
    asset_env.effective.get_report_information = report_information
    asset_env.ref = lambda xml_id, raise_if_not_found=True: (
        asset_env.root if xml_id == "account_asset.assets_report" else None
    )

    result = _dispatch(asset_env, "account.report.asset.read_page", payload, 7)

    assert result["columns"] == [
        {
            "index": index,
            "label": "Book Value"
            if column["expression_label"] == "balance"
            else column["name"],
            "expression_label": column["expression_label"],
            "figure_type": (
                "string"
                if column["expression_label"] == "acquisition_date"
                else column["figure_type"]
            ),
        }
        for index, column in enumerate(asset_columns)
    ]
    normalized_monetary_values = [
        "1000",
        "200",
        "0",
        "1200",
        "300",
        "50",
        "0",
        "350",
        "850",
    ]
    assert result["lines"][0]["values"] == [
        None,
        None,
        None,
        *normalized_monetary_values,
    ]
    assert result["lines"][1]["values"] == [
        "01/10/2025",
        "Linear",
        "5 y",
        *normalized_monetary_values,
    ]
    assert result["lines"][2]["values"] == [
        None,
        None,
        None,
        *normalized_monetary_values,
    ]

    other_env = FakeEnv()
    other_env.root.get_options = asset_options
    other_env.effective.get_report_information = report_information
    with pytest.raises(RuntimeFailure):
        _dispatch(other_env, "account.report.general_ledger.read_page", payload, 7)


def test_asset_report_requires_account_move_read_access() -> None:
    class DeniedModel:
        def has_access(self, operation: str) -> bool:
            assert operation == "read"
            return False

    env = FakeEnv()
    env.models["account.move"] = DeniedModel()
    env.ref = lambda xml_id, raise_if_not_found=True: (
        env.root if xml_id == "account_asset.assets_report" else None
    )

    result = _dispatch(
        env,
        "account.report.asset.read_page",
        {
            "company_id": 7,
            "date_from": "2025-01-01",
            "date_to": "2025-01-31",
            "after_line_id": None,
            "limit": 101,
        },
        7,
    )

    assert result["module_installed"] is True
    assert result["access_allowed"] is False
    assert result["lines"] == []
    assert env.effective.normal_called is False


def test_other_typed_reports_reject_empty_string_cells() -> None:
    env = FakeEnv()
    raw_lines = copy.deepcopy(_RAW_LINES)
    raw_lines[0]["columns"][0]["no_format"] = ""
    env.effective.get_report_information = lambda _options: {"lines": raw_lines}

    with pytest.raises(RuntimeFailure):
        _dispatch(
            env,
            "account.report.general_ledger.read_page",
            {
                "company_id": 7,
                "date_from": "2025-01-01",
                "date_to": "2025-01-31",
                "after_line_id": None,
                "limit": 101,
            },
            7,
        )


def test_asset_report_uses_the_rollback_only_cursor() -> None:
    assert (
        _cursor_factory_for("account.report.asset.read_page", {})
        is _rollback_only_cursor
    )


def test_journal_report_accepts_only_the_real_empty_colspan_structure_line() -> None:
    env = FakeEnv()
    env.ref = lambda _xml_id, raise_if_not_found=True: env.root

    def report_information(_options):
        return {
            "lines": [
                {
                    "id": "journal:placeholder",
                    "parent_id": False,
                    "name": "",
                    "level": 4,
                    "unfoldable": False,
                    "columns": [],
                    "colspan": len(_OPTIONS_COLUMNS) + 1,
                },
                {
                    "id": "journal:section",
                    "parent_id": False,
                    "name": "Journal Entries",
                    "level": 0,
                    "unfoldable": False,
                    "columns": [],
                    "colspan": len(_OPTIONS_COLUMNS) + 1,
                },
            ]
        }

    env.effective.get_report_information = report_information
    payload = {
        "company_id": 7,
        "date_from": "2025-01-01",
        "date_to": "2025-01-31",
        "after_line_id": None,
        "limit": 101,
    }

    result = _dispatch(env, "account.report.journal.read_page", payload, 7)
    assert [line["id"] for line in result["lines"]] == ["journal:section"]
    assert result["lines"][0]["values"] == [None] * len(_OPTIONS_COLUMNS)

    def malformed_information(_options):
        row = report_information(_options)["lines"][0]
        row["colspan"] -= 1
        return {"lines": [row]}

    env.effective.get_report_information = malformed_information
    with pytest.raises(RuntimeFailure):
        _dispatch(env, "account.report.journal.read_page", payload, 7)


def test_rollback_only_cursor_never_commits() -> None:
    events: list[str] = []

    class Cursor:
        def rollback(self):
            events.append("rollback")

        def close(self):
            events.append("close")

        def commit(self):
            raise AssertionError("rollback-only report transaction must not commit")

    cursor = Cursor()

    class Registry:
        def cursor(self):
            events.append("cursor")
            return cursor

    with _rollback_only_cursor(Registry()) as observed:
        assert observed is cursor
        events.append("yield")

    assert events == ["cursor", "yield", "rollback", "close"]


def test_rollback_only_cursor_rolls_back_when_report_dispatch_raises() -> None:
    events: list[str] = []

    class Cursor:
        def rollback(self):
            events.append("rollback")

        def close(self):
            events.append("close")

    cursor = Cursor()

    class Registry:
        def cursor(self):
            return cursor

    with (
        pytest.raises(RuntimeError, match="report failed"),
        _rollback_only_cursor(Registry()),
    ):
        raise RuntimeError("report failed")

    assert events == ["rollback", "close"]
