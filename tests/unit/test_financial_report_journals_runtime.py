from __future__ import annotations

import copy

import pytest
from test_financial_report_exports_runtime import FakeEnv as ExportEnv
from test_trial_balance_runtime import FakeEnv as ReadEnv

from odoo_accounting_cli_v4.bridge.runtime import RuntimeFailure, _dispatch

REPORTS = ("trial_balance", "general_ledger", "balance_sheet", "profit_and_loss")


class JournalModel:
    def __init__(self):
        self.access = True
        self.ids = [9, 10]
        self.calls = []

    def has_access(self, operation):
        assert operation == "read"
        return self.access

    def with_context(self, **context):
        assert context == {"active_test": False, "allowed_company_ids": [7]}
        return self

    def search_read(self, domain, *, fields, limit):
        assert domain == [("id", "in", [9, 10]), ("company_id", "=", 7)]
        assert fields == ["id"] and limit == 2
        self.calls.append(domain)
        return [{"id": value} for value in self.ids]


def case(export=False, report="trial_balance", *, all_selected=False):
    env = ExportEnv() if export else ReadEnv()
    root = env.root if export else env.root_report
    journals = JournalModel()
    env.models["account.journal"] = journals
    original_registry_get = env.registry.get
    env.registry.get = lambda name: (
        object() if name == "account.journal" else original_registry_get(name)
    )
    if export:
        action = "account.report.fixed_export"
        payload = {
            "capability_id": f"report.{report}.export",
            "company_id": 7,
            "date_from": None if report == "balance_sheet" else "2025-01-01",
            "date_to": "2025-01-31",
            "format": "pdf",
        }
    else:
        action = f"account.report.{report}.read_page"
        payload = {
            "company_id": 7,
            "date_from": None if report == "balance_sheet" else "2025-01-01",
            "date_to": "2025-01-31",
            "after_line_id": None,
            "limit": 100,
        }
        env.ref = lambda _xml_id, **_kwargs: root
    payload["journal_ids"] = [10, 9]
    original_options = root.get_options

    def options(previous):
        result = copy.deepcopy(original_options(previous))
        if not export:
            result["date"]["mode"] = (
                "single" if report == "balance_sheet" else "range"
            )
        result["journals"] = [
            {**item, "selected": not all_selected} for item in previous["journals"]
        ]
        return result

    root.get_options = options
    env.effective.filter_journals = True

    def effective_journals(options):
        available = [
            item
            for item in options.get("journals", [])
            if item["model"] == "account.journal"
        ]
        return [item for item in available if item["selected"]] or available

    env.effective._get_options_journals = effective_journals
    return env, journals, action, payload


@pytest.mark.parametrize("export", [False, True])
@pytest.mark.parametrize("report", REPORTS)
def test_journal_filter_reaches_all_eight_fixed_native_report_paths(export, report):
    env, journals, action, payload = case(export, report)
    result = _dispatch(env, action, payload, 7)
    assert result["access_allowed"] is True
    assert len(journals.calls) == 1
    native_options = (
        env.effective.calls[0][1] if export else env.effective.options
    )
    assert native_options["journals"] == [
        {"id": 9, "model": "account.journal", "selected": True},
        {"id": 10, "model": "account.journal", "selected": True},
    ]


@pytest.mark.parametrize("export", [False, True])
def test_native_all_journals_selection_may_collapse_to_unselected(export):
    env, _journals, action, payload = case(export, all_selected=True)
    assert _dispatch(env, action, payload, 7)["access_allowed"] is True


@pytest.mark.parametrize("export", [False, True])
def test_missing_or_cross_company_journal_does_not_fall_back_to_all(export):
    env, journals, action, payload = case(export)
    journals.ids = [9]
    with pytest.raises(RuntimeFailure) as caught:
        _dispatch(env, action, payload, 7)
    assert caught.value.code == "company_unavailable"
    assert not (env.effective.calls if export else env.effective.options)


@pytest.mark.parametrize("export", [False, True])
def test_journal_read_acl_is_required_before_selecting_native_options(export):
    env, journals, action, payload = case(export)
    journals.access = False
    result = _dispatch(env, action, payload, 7)
    assert result["access_allowed"] is False
    assert not journals.calls
    assert not (env.effective.calls if export else env.effective.options)


@pytest.mark.parametrize("export", [False, True])
@pytest.mark.parametrize("failure", ["unsupported_variant", "ignored_ids"])
def test_effective_report_must_retain_the_requested_selection(export, failure):
    env, _journals, action, payload = case(export)
    if failure == "unsupported_variant":
        env.effective.filter_journals = False
    else:
        env.effective._get_options_journals = lambda _options: [{"id": 9}]
    with pytest.raises(RuntimeFailure) as caught:
        _dispatch(env, action, payload, 7)
    assert caught.value.code == "odoo_runtime_error"
    assert not (env.effective.calls if export else env.effective.options)


@pytest.mark.parametrize("export", [False, True])
@pytest.mark.parametrize("value", [None, [], [True], [0], [-1], [9, 9], ["9"], [[9]]])
def test_runtime_rejects_malformed_journal_ids(export, value):
    env, journals, action, payload = case(export)
    payload["journal_ids"] = value
    with pytest.raises(RuntimeFailure) as caught:
        _dispatch(env, action, payload, 7)
    assert caught.value.code == "bridge_protocol_error"
    assert not journals.calls


@pytest.mark.parametrize("export", [False, True])
def test_partner_ledger_does_not_accept_an_unsupported_journal_filter(export):
    env, journals, action, payload = case(export, "partner_ledger")
    with pytest.raises(RuntimeFailure) as caught:
        _dispatch(env, action, payload, 7)
    assert caught.value.code == "bridge_protocol_error"
    assert not journals.calls
