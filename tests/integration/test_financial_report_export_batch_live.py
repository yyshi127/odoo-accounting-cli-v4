"""One shared read-only smoke for fixed financial-report exports."""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import os
import subprocess
import sys
import sysconfig
import uuid
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from decimal import Decimal
from pathlib import Path
from typing import Any

try:
    import pytest
except ModuleNotFoundError:
    if "--live-worker" not in sys.argv:
        raise
    pytest = None

_CONFIG_ENV = "ODOO_ACCOUNTING_CLI_V4_CONFIG"
_ALLOW_ENV = "ODACV4_ALLOW_FINANCIAL_REPORT_EXPORT_SMOKE"
_JOURNAL_ALLOW_ENV = "ODACV4_ALLOW_FINANCIAL_REPORT_JOURNAL_FILTER_SMOKE"
_ALIASES = ("v4-dev", "v4-e2e")
_DATABASES = {
    "v4-dev": "odoo_cli_v4_dev",
    "v4-e2e": "odoo_cli_v4_e2e",
}
_COMPANY_IDS = (1, 2)
_USER_LOGIN = "odacv4_g5_accountant"
_CAPABILITIES = {
    "report.trial_balance.export": ("range", 1),
    "report.balance_sheet.export": ("single", 1),
    "report.profit_and_loss.export": ("range", 1),
    "report.cash_flow.export": ("range", 1),
    "report.tax.export": ("range", 1),
    "report.general_ledger.export": ("range", 1),
    "report.partner_ledger.export": ("range", 1),
    "report.aged_receivable.export": ("single", 1),
    "report.aged_payable.export": ("single", 1),
    "report.executive_summary.export": ("range", 1),
    "report.journal.export": ("range", 1),
    "report.asset.export": ("range", 1),
    "report.deferred_expense.export": ("range", 1),
    "report.deferred_revenue.export": ("range", 1),
    "report.multicurrency_revaluation.export": ("single", 1),
    "report.china.balance_sheet.export": ("single", 1),
    "report.china.profit_and_loss.export": ("range", 1),
    "report.china.cash_flow.export": ("range", 1),
    "report.singapore.gst.export": ("range", 2),
}
_JOURNAL_REPORTS = (
    "report.trial_balance",
    "report.general_ledger",
    "report.balance_sheet",
    "report.profit_and_loss",
)
_JOURNAL_CAPABILITIES = tuple(
    capability
    for report in _JOURNAL_REPORTS
    for capability in (report, report + ".export")
)
_PERIOD = {"date_from": "2025-01-01", "date_to": "2025-02-28"}


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _enabled_runtime(
    *,
    journal_filter: bool = False,
) -> tuple[Path, dict[str, Any]]:
    assert pytest is not None
    allow_env = _JOURNAL_ALLOW_ENV if journal_filter else _ALLOW_ENV
    if os.environ.get(allow_env) != "1":
        pytest.skip(f"set {allow_env}=1 to authorize the live read-only smoke")
    raw_path = os.environ.get(_CONFIG_ENV)
    if not raw_path:
        pytest.skip(f"{_CONFIG_ENV} is not configured")
    path = Path(raw_path)
    if not path.is_file():
        pytest.skip(f"{_CONFIG_ENV} does not name an existing file")
    document = json.loads(path.read_text(encoding="utf-8"))
    for alias, database in _DATABASES.items():
        entry = document.get("aliases", {}).get(alias)
        assert isinstance(entry, dict) and entry.get("database") == database
        for company_id in (1,) if journal_filter else _COMPANY_IDS:
            users = entry.get("companies", {}).get(str(company_id))
            assert isinstance(users, list) and _USER_LOGIN in users
    return path, document


def _worker_command(
    alias: str, config_path: Path, runtime: dict[str, Any]
) -> tuple[list[str], int]:
    bridge = runtime.get("bridge")
    assert isinstance(bridge, dict)
    argv = bridge.get("argv")
    timeout = bridge.get("timeout_seconds")
    assert isinstance(argv, list) and len(argv) == 8
    assert argv[2::2] == ["--runtime-config", "--odoo-config", "--odoo-source"]
    assert isinstance(timeout, int) and not isinstance(timeout, bool) and timeout > 0
    executable = Path(argv[0])
    configured_runtime = Path(argv[3])
    odoo_config = Path(argv[5])
    odoo_source = Path(argv[7])
    assert executable.is_absolute() and executable.is_file()
    assert configured_runtime.resolve(strict=True) == config_path.resolve(strict=True)
    assert odoo_config.is_absolute() and odoo_config.is_file()
    assert odoo_source.is_absolute() and odoo_source.is_dir()
    return (
        [
            str(executable),
            str(Path(__file__).resolve()),
            "--live-worker",
            "--odoo-config",
            str(odoo_config),
            "--odoo-source",
            str(odoo_source),
            "--alias",
            alias,
            "--database",
            _DATABASES[alias],
        ],
        max(timeout, 600),
    )


def _run_worker(
    alias: str,
    config_path: Path,
    runtime: dict[str, Any],
    *,
    journal_filter: bool = False,
) -> dict[str, Any]:
    command, timeout = _worker_command(alias, config_path, runtime)
    if journal_filter:
        command.append("--journal-filter-only")
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = os.pathsep.join(
        part
        for part in (
            str(_project_root() / "src"),
            sysconfig.get_paths()["purelib"] if journal_filter else None,
            environment.get("PYTHONPATH"),
        )
        if part
    )
    completed = subprocess.run(
        command,
        cwd=_project_root(),
        env=environment,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert len(completed.stdout.splitlines()) == 1
    result = json.loads(completed.stdout)
    if journal_filter:
        assert result == {
            "alias": alias,
            "capabilities": sorted(_JOURNAL_CAPABILITIES),
            "all_journals_verified": True,
            "cli_calls": 30,
            "combined_journals_verified": True,
            "company_ids": [1],
            "database": _DATABASES[alias],
            "execution": "in_process_cli_real_orm",
            "exports": 16,
            "formats": ["pdf", "xlsx"],
            "journal_filters": 4,
            "pagination_verified": True,
            "read_only_transaction": True,
            "trial_balance_period_totals": result["trial_balance_period_totals"],
            "user_id": 5,
            "xlsx_amounts_verified": 8,
        }
        assert set(result["trial_balance_period_totals"]) == {"sale", "purchase"}
        for totals in result["trial_balance_period_totals"].values():
            assert set(totals) == {"debit", "credit"}
            assert Decimal(totals["debit"]) == Decimal(totals["credit"]) != 0
        return result
    assert result == {
        "alias": alias,
        "capabilities": list(_CAPABILITIES),
        "company_ids": list(_COMPANY_IDS),
        "database": _DATABASES[alias],
        "exports": len(_CAPABILITIES) * 2,
        "formats": ["pdf", "xlsx"],
        "read_only_transaction": True,
        "user_id": result["user_id"],
    }
    assert isinstance(result["user_id"], int) and result["user_id"] > 0
    return result


if pytest is not None:

    @pytest.mark.integration
    def test_financial_report_export_batch_is_live_and_read_only() -> None:
        config_path, runtime = _enabled_runtime()
        results = [_run_worker(alias, config_path, runtime) for alias in _ALIASES]
        assert [item["alias"] for item in results] == list(_ALIASES)

    @pytest.mark.integration
    def test_financial_report_journal_filters_are_live_and_read_only() -> None:
        config_path, runtime = _enabled_runtime(journal_filter=True)
        results = []
        for alias in _ALIASES:
            result = _run_worker(alias, config_path, runtime, journal_filter=True)
            print(json.dumps(result, sort_keys=True, separators=(",", ":")), flush=True)
            results.append(result)
        assert [item["alias"] for item in results] == list(_ALIASES)


def _worker_arguments(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-worker", action="store_true", required=True)
    parser.add_argument("--journal-filter-only", action="store_true")
    parser.add_argument("--odoo-config", type=Path, required=True)
    parser.add_argument("--odoo-source", type=Path, required=True)
    parser.add_argument("--alias", choices=_ALIASES, required=True)
    parser.add_argument("--database", choices=tuple(_DATABASES.values()), required=True)
    args = parser.parse_args(argv)
    if args.database != _DATABASES[args.alias]:
        parser.error("alias and physical database do not match")
    if not args.odoo_config.is_absolute() or not args.odoo_config.is_file():
        parser.error("odoo-config must be an existing absolute file")
    if not args.odoo_source.is_absolute() or not args.odoo_source.is_dir():
        parser.error("odoo-source must be an existing absolute directory")
    return args


class _DirectClient:
    def __init__(self, env: Any, company_id: int) -> None:
        self.env = env
        self.company_id = company_id
        self.calls: list[dict[str, Any]] = []
        self.cli_calls = 0
        self.capabilities: set[str] = set()
        self.last_runtime_failure: Exception | None = None

    def invoke(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        from odoo_accounting_cli_v4.bridge.client import BridgeError
        from odoo_accounting_cli_v4.bridge.runtime import RuntimeFailure, _dispatch

        self.calls.append(payload)
        try:
            return _dispatch(
                self.env, action, payload, self.company_id, (self.company_id,)
            )
        except RuntimeFailure as exc:
            self.last_runtime_failure = exc
            raise BridgeError(
                exc.code,
                str(exc),
                exit_code=exc.exit_code,
                retryable=exc.retryable,
                details=exc.details,
            ) from exc


def _parameters(mode: str, export_format: str) -> dict[str, str]:
    if mode == "single":
        return {"as_of": "2025-12-31", "format": export_format}
    return {
        "date_from": "2025-01-01",
        "date_to": "2025-12-31",
        "format": export_format,
    }


def _request(
    alias: str,
    company_id: int,
    capability_id: str,
    export_format: str,
    mode: str,
) -> dict[str, Any]:
    return {
        "schema_version": "v1",
        "request_id": str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"odacv4:{alias}:{company_id}:{capability_id}:{export_format}",
            )
        ),
        "context": {
            "database": alias,
            "company_id": company_id,
            "user_login": _USER_LOGIN,
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": _parameters(mode, export_format),
    }


def _exercise_batch(env: Any, alias: str, company_id: int) -> None:
    from odoo_accounting_cli_v4.bridge.financial_reports import (
        OdooFinancialReportExportPort,
    )
    from odoo_accounting_cli_v4.capabilities.financial_reports import (
        export_financial_report,
    )

    client = _DirectClient(env, company_id)
    for capability_id, (mode, mapped_company_id) in _CAPABILITIES.items():
        if mapped_company_id != company_id:
            continue
        for export_format in ("pdf", "xlsx"):
            port = OdooFinancialReportExportPort(client)
            data = export_financial_report(
                capability_id,
                port,
                _request(alias, company_id, capability_id, export_format, mode),
            )
            content = base64.b64decode(data["content_base64"], validate=True)
            expected_magic = b"%PDF-" if export_format == "pdf" else b"PK\x03\x04"
            if (
                port.user_id != env.uid
                or data["byte_count"] != len(content)
                or data["sha256"] != hashlib.sha256(content).hexdigest()
                or not content.startswith(expected_magic)
            ):
                raise RuntimeError(f"{capability_id} returned an invalid live export")


def _report_cli(
    client: _DirectClient,
    alias: str,
    capability_id: str,
    parameters: dict[str, Any],
    *,
    expected_error: str | None = None,
) -> dict[str, Any]:
    from odoo_accounting_cli_v4 import cli
    from odoo_accounting_cli_v4.bridge.financial_reports import (
        OdooFinancialReportExportPort,
        OdooFinancialReportPort,
    )

    request = _request(alias, 1, capability_id, "json", "range")
    request["parameters"] = parameters
    request["request_id"] = str(
        uuid.uuid5(uuid.NAMESPACE_URL, json.dumps(request, sort_keys=True))
    )
    port = (
        OdooFinancialReportExportPort(client)
        if capability_id.endswith(".export")
        else OdooFinancialReportPort(client, capability_id)
    )
    stdout, stderr = io.StringIO(), io.StringIO()
    before = len(client.calls)
    client.last_runtime_failure = None
    exit_code = cli.main(
        ["read", capability_id, "--request", "-"],
        stdin=io.StringIO(json.dumps(request)),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda _capability, _request: port,
    )
    client.cli_calls += 1
    assert stderr.getvalue() == "" and len(stdout.getvalue().splitlines()) == 1
    response = json.loads(stdout.getvalue())
    assert response["request_id"] == request["request_id"]
    assert response["schema_version"] == "v1"
    assert response["capability"] == capability_id
    if expected_error is not None:
        assert exit_code == 2 and response["success"] is False
        assert response["error"]["code"] == expected_error
        assert response["data"] is None and len(client.calls) == before
        return {}
    if exit_code != 0:
        raise AssertionError(
            f"{capability_id}: exit={exit_code}, error={response['error']}"
        ) from client.last_runtime_failure
    assert response["success"] is True and response["status"] == "verified"
    assert response["error"] is None and port.user_id == 5
    assert {
        key: response["odoo"][key] for key in ("database", "company_id", "user_id")
    } == {"database": alias, "company_id": 1, "user_id": 5}
    assert len(client.calls) == before + 1
    expected_journals = parameters.get("journal_ids")
    assert client.calls[-1].get("journal_ids") == (
        sorted(expected_journals) if expected_journals is not None else None
    )
    client.capabilities.add(capability_id)
    return response["data"]


def _fixture_journals(env: Any) -> dict[str, int]:
    journals = {}
    for kind, move_type, suffix in (
        ("sale", "out_invoice", "INVOICE-TAX-EXCLUDED"),
        ("purchase", "in_invoice", "BILL-TAX-INCLUDED"),
    ):
        moves = env["account.move"].search(
            [
                ("company_id", "=", 1),
                ("state", "=", "posted"),
                ("move_type", "=", move_type),
                ("ref", "=", f"ODACV4-FX1-CN-{suffix}"),
                ("date", ">=", _PERIOD["date_from"]),
                ("date", "<=", _PERIOD["date_to"]),
            ],
            limit=2,
        )
        assert len(moves) == 1, f"the posted {kind} fixture is unavailable"
        assert moves.journal_id.type == kind
        journals[kind] = moves.journal_id.id
    assert len(set(journals.values())) == 2
    return journals


def _posted_amounts(env: Any, journal_id: int | None) -> dict[int, list[Decimal]]:
    domain = [
        ("company_id", "=", 1),
        ("parent_state", "=", "posted"),
        ("account_id", "!=", False),
        ("date", ">=", _PERIOD["date_from"]),
        ("date", "<=", _PERIOD["date_to"]),
    ]
    if journal_id is not None:
        domain.append(("journal_id", "=", journal_id))
    amounts: dict[int, list[Decimal]] = {}
    for line in env["account.move.line"].search_read(
        domain, ["account_id", "debit", "credit"]
    ):
        values = amounts.setdefault(line["account_id"][0], [Decimal(0), Decimal(0)])
        values[0] += Decimal(str(line["debit"]))
        values[1] += Decimal(str(line["credit"]))
    amounts = {key: values for key, values in amounts.items() if any(values)}
    assert amounts, "journal filtering requires nonzero posted fixture entries"
    return amounts


def _assert_trial_balance(
    env: Any, data: dict[str, Any], expected: dict[int, list[Decimal]]
) -> dict[str, str]:
    assert [column["expression_label"] for column in data["columns"]] == [
        "balance",
        "debit",
        "credit",
        "balance",
    ]
    assert data["date"] == {"from": _PERIOD["date_from"], "to": _PERIOD["date_to"]}
    quantum = Decimal(1).scaleb(-data["currency"]["decimal_places"])
    actual = {}
    totals = []
    for line in data["lines"]:
        values = [Decimal(value or "0").quantize(quantum) for value in line["values"]]
        assert values[3] - values[0] == values[1] - values[2]
        if line["parent_id"] is None:
            totals.append(values)
        model, account_id = env["account.report"]._get_model_info_from_id(line["id"])
        if model == "account.account" and any(values[1:3]):
            assert account_id not in actual
            actual[account_id] = values[1:3]
    assert actual == {
        key: [value.quantize(quantum) for value in values]
        for key, values in expected.items()
    }, "trial-balance account amounts do not match selected posted journal items"
    assert len(totals) == 1
    expected_totals = [
        sum(values[index] for values in expected.values()) for index in (0, 1)
    ]
    assert totals[0][1:3] == [value.quantize(quantum) for value in expected_totals]
    assert totals[0][1] == totals[0][2] != 0
    return {
        key: format(value.normalize(), "f")
        for key, value in zip(("debit", "credit"), totals[0][1:3], strict=True)
    }


def _numeric_values(data: dict[str, Any], line: dict[str, Any]) -> tuple[Decimal, ...]:
    quantum = Decimal(1).scaleb(-data["currency"]["decimal_places"])
    return tuple(
        Decimal(value).quantize(quantum)
        for column, value in zip(data["columns"], line["values"], strict=True)
        if value is not None
        and column.get("figure_type", "monetary")
        in {"monetary", "float", "percentage", "integer"}
    )


def _general_ledger_print_rows(
    env: Any, journal_id: int, data: dict[str, Any]
) -> Counter[tuple[Decimal, ...]]:
    """Independent native print oracle: GL exports unfold individual entries."""
    assert env.uid == 5 and not env.su and env.context["allowed_company_ids"] == [1]
    report = env.ref("account_reports.general_ledger_report")
    options = report.get_options(
        {
            "all_entries": False,
            "date": {**_PERIOD, "mode": "range", "filter": "custom"},
            "journals": [
                {"id": journal_id, "model": "account.journal", "selected": True}
            ],
            "export_mode": "print",
        }
    )
    report = env["account.report"].browse(options["report_id"])
    options = report.get_options({**options, "selected_section_id": report.id})
    assert options["export_mode"] == "print" and options["unfold_all"] is True
    assert options["all_entries"] is False and options["readonly_query"] is True
    assert not options.get("sections")
    assert set(report.get_report_company_ids(options)) == {1}
    assert all(options["date"][key] == value for key, value in _PERIOD.items())
    assert {item["id"] for item in report._get_options_journals(options)} == {
        journal_id
    }
    assert [column["expression_label"] for column in options["columns"]] == [
        column["expression_label"] for column in data["columns"]
    ]
    lines = report._filter_out_folded_children(
        report.with_context(no_format=True)._get_lines(options)
    )
    quantum = Decimal(1).scaleb(-data["currency"]["decimal_places"])
    expected = Counter()
    for line in lines:
        # These are the rendered numeric cell values consumed by the XLSX writer;
        # date/string cells and deliberately blank zero cells stay nonnumeric.
        values = tuple(
            Decimal(str(cell["name"])).quantize(quantum)
            for cell in line["columns"]
            if type(cell.get("name")) in {int, float, Decimal}
        )
        if any(values):
            expected[values] += 1
    assert expected
    return expected


def _assert_filtered_export(
    exported: dict[str, Any],
    export_format: str,
    report: dict[str, Any],
    *,
    expected_numeric_rows: Counter[tuple[Decimal, ...]] | None = None,
) -> None:
    content = base64.b64decode(exported["content_base64"], validate=True)
    assert exported["format"] == export_format
    assert exported["byte_count"] == len(content) > 0
    assert exported["sha256"] == hashlib.sha256(content).hexdigest()
    assert exported["filename"].lower().endswith("." + export_format)
    if export_format == "pdf":
        assert exported["mimetype"] == "application/pdf"
        assert content.startswith(b"%PDF-") and b"%%EOF" in content[-1024:]
        return
    assert exported["mimetype"] == (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert content.startswith(b"PK\x03\x04")
    quantum = Decimal(1).scaleb(-report["currency"]["decimal_places"])
    with zipfile.ZipFile(io.BytesIO(content)) as workbook:
        assert workbook.testzip() is None
        assert {"[Content_Types].xml", "xl/workbook.xml"} <= set(workbook.namelist())
        # Native export writes the report first and an Options sheet afterwards.
        sheet = ET.fromstring(workbook.read("xl/worksheets/sheet1.xml"))
    actual = Counter()
    for row in sheet.findall("{*}sheetData/{*}row"):
        values = tuple(
            Decimal(cell.findtext("{*}v")).quantize(quantum)
            for cell in row.findall("{*}c")
            if cell.get("t", "n") == "n" and cell.findtext("{*}v") is not None
        )
        if any(values):
            actual[values] += 1
    expected = expected_numeric_rows
    if expected is None:
        # Unlike GL, these reports keep the fresh JSON options' folded state.
        folded: set[str] = set()
        expected = Counter()
        for line in report["lines"]:
            if line["unfoldable"]:
                folded.add(line["id"])
            if line["parent_id"] not in folded and any(
                values := _numeric_values(report, line)
            ):
                expected[values] += 1
    assert expected and actual == expected, (
        f"{report['report']['key']} XLSX amount rows differ from filtered report rows: "
        f"expected={expected}, actual={actual}"
    )


def _exercise_journal_filters(env: Any, alias: str) -> dict[str, Any]:
    client = _DirectClient(env, 1)
    journals = _fixture_journals(env)
    amounts = {
        kind: _posted_amounts(env, journal_id) for kind, journal_id in journals.items()
    }
    assert amounts["sale"] != amounts["purchase"], "fixture account vectors must differ"
    totals, trial_pages = {}, {}
    exports = 0
    for capability_id in _JOURNAL_REPORTS:
        vectors = []
        for kind, journal_id in journals.items():
            dates = (
                {"as_of": _PERIOD["date_to"]}
                if capability_id == "report.balance_sheet"
                else _PERIOD
            )
            parameters = {**dates, "journal_ids": [journal_id]}
            data = _report_cli(
                client, alias, capability_id, {**parameters, "limit": 1000}
            )
            assert data["basis"] == "posted_entries"
            assert data["has_more"] is False and data["next_cursor"] is None
            vector = {
                line["id"]: values
                for line in data["lines"]
                if any(values := _numeric_values(data, line))
            }
            assert vector, f"{capability_id} requires a nonzero journal-filter result"
            vectors.append(vector)
            if capability_id == "report.trial_balance":
                totals[kind] = _assert_trial_balance(env, data, amounts[kind])
                trial_pages[kind] = data
            xlsx_expected = (
                _general_ledger_print_rows(env, journal_id, data)
                if capability_id == "report.general_ledger"
                else None
            )
            for export_format in ("pdf", "xlsx"):
                exported = _report_cli(
                    client,
                    alias,
                    capability_id + ".export",
                    {**parameters, "format": export_format},
                )
                _assert_filtered_export(
                    exported, export_format, data, expected_numeric_rows=xlsx_expected
                )
                exports += 1
        assert vectors[0] != vectors[1], f"{capability_id} ignored the journal filter"

    unfiltered = _report_cli(
        client, alias, "report.trial_balance", {**_PERIOD, "limit": 1000}
    )
    assert unfiltered["has_more"] is False and unfiltered["next_cursor"] is None
    _assert_trial_balance(env, unfiltered, _posted_amounts(env, None))
    assert all(unfiltered["lines"] != page["lines"] for page in trial_pages.values())
    combined_expected: dict[int, list[Decimal]] = {}
    for journal_amounts in amounts.values():
        for account_id, values in journal_amounts.items():
            total = combined_expected.setdefault(account_id, [Decimal(0), Decimal(0)])
            total[0] += values[0]
            total[1] += values[1]
    combined = _report_cli(
        client,
        alias,
        "report.trial_balance",
        {
            **_PERIOD,
            "journal_ids": sorted(journals.values(), reverse=True),
            "limit": 1000,
        },
    )
    assert combined["has_more"] is False and combined["next_cursor"] is None
    _assert_trial_balance(
        env,
        combined,
        {key: values for key, values in combined_expected.items() if any(values)},
    )
    # Use the native selectable journals, not every account.journal record.
    native_options = env.ref("account_reports.trial_balance_report").get_options(
        {"all_entries": False, "date": {**_PERIOD, "mode": "range", "filter": "custom"}}
    )
    all_journal_ids = sorted(
        item["id"]
        for item in native_options["journals"]
        if item["model"] == "account.journal"
    )
    assert set(journals.values()) <= set(all_journal_ids)
    all_selected = _report_cli(
        client,
        alias,
        "report.trial_balance",
        {**_PERIOD, "journal_ids": all_journal_ids, "limit": 1000},
    )
    assert all_selected == unfiltered, (
        "native all-journals selection changed the report"
    )
    parameters = {**_PERIOD, "journal_ids": [journals["sale"]], "limit": 1}
    first = _report_cli(client, alias, "report.trial_balance", parameters)
    assert first["has_more"] is True and first["next_cursor"]
    assert first["lines"] == trial_pages["sale"]["lines"][:1]
    second = _report_cli(
        client,
        alias,
        "report.trial_balance",
        {**parameters, "cursor": first["next_cursor"]},
    )
    assert second["lines"] == trial_pages["sale"]["lines"][1:2]
    _report_cli(
        client,
        alias,
        "report.trial_balance",
        {
            **parameters,
            "journal_ids": [journals["purchase"]],
            "cursor": first["next_cursor"],
        },
        expected_error="invalid_cursor",
    )
    assert client.capabilities == set(_JOURNAL_CAPABILITIES)
    assert client.cli_calls == 30 and exports == 16
    env.cr.execute("SHOW transaction_read_only")
    assert env.cr.fetchone()[0] == "on"
    return {
        "capabilities": sorted(client.capabilities),
        "all_journals_verified": True,
        "cli_calls": client.cli_calls,
        "combined_journals_verified": True,
        "execution": "in_process_cli_real_orm",
        "exports": exports,
        "journal_filters": len(journals) + 2,
        "pagination_verified": True,
        "trial_balance_period_totals": totals,
        "xlsx_amounts_verified": exports // 2,
    }


def _live_worker(argv: list[str] | None = None) -> int:
    args = _worker_arguments(argv)
    root = _project_root()
    sys.path.insert(0, str(args.odoo_source.resolve(strict=True)))
    sys.path.insert(0, str((root / "src").resolve(strict=True)))

    from odoo import SUPERUSER_ID, api
    from odoo.orm.registry import Registry
    from odoo.tools import config as odoo_runtime_config

    odoo_runtime_config.parse_config(
        [
            "--config",
            str(args.odoo_config.resolve(strict=True)),
            "--database",
            args.database,
            "--no-http",
        ]
    )
    registry = Registry(args.database)
    cursor = registry.cursor()
    user_id: int | None = None
    company_ids = (1,) if args.journal_filter_only else _COMPANY_IDS
    summary: dict[str, Any] = {
        "capabilities": list(_CAPABILITIES),
        "exports": len(_CAPABILITIES) * 2,
    }
    try:
        cursor.execute("SET TRANSACTION READ ONLY")
        context = {
            "allowed_company_ids": list(company_ids),
            "active_test": True,
            "lang": "en_US",
            "tz": "Asia/Shanghai",
        }
        root_env = api.Environment(cursor, SUPERUSER_ID, context)
        companies = root_env["res.company"].browse(company_ids).exists()
        user = (
            root_env["res.users"]
            .with_context(active_test=False)
            .search([("login", "=", _USER_LOGIN)], limit=1)
        )
        if (
            set(companies.ids) != set(company_ids)
            or not user
            or not user.active
            or any(company not in user.company_ids for company in companies)
        ):
            raise RuntimeError("the configured companies or user are unavailable")
        user_id = user.id
        if args.journal_filter_only:
            assert user_id == 5
        for company_id in company_ids:
            company_context = {**context, "allowed_company_ids": [company_id]}
            env = api.Environment(cursor, user_id, company_context)
            if args.journal_filter_only:
                assert env.su is False and env.company.id == 1
                summary = _exercise_journal_filters(env, args.alias)
            else:
                _exercise_batch(env, args.alias, company_id)
    finally:
        try:
            cursor.rollback()
        finally:
            cursor.close()

    sys.stdout.write(
        json.dumps(
            {
                "alias": args.alias,
                **summary,
                "company_ids": list(company_ids),
                "database": args.database,
                "formats": ["pdf", "xlsx"],
                "read_only_transaction": True,
                "user_id": user_id,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_live_worker())
