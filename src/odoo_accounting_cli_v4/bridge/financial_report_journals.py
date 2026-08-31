"""Native journal selection shared by fixed report reads and exports."""

from __future__ import annotations

from typing import Any

REPORT_KEYS = frozenset(
    {"trial_balance", "general_ledger", "balance_sheet", "profit_and_loss"}
)


def validate_journal_ids(value: Any, failure_type: Any) -> list[int]:
    if (
        not isinstance(value, list)
        or not 1 <= len(value) <= 1000
        or any(type(item) is not int or item <= 0 for item in value)
        or len(set(value)) != len(value)
    ):
        raise failure_type(
            "bridge_protocol_error", "The bridge action payload is invalid.", exit_code=7
        )
    return sorted(value)


def journal_options(
    env: Any, company_id: int, journal_ids: list[int], failure_type: Any
) -> list[dict[str, Any]]:
    """Resolve all requested journals after the caller's model-read ACL check."""
    records = (
        env["account.journal"]
        .with_context(active_test=False, allowed_company_ids=[company_id])
        .search_read(
            [("id", "in", journal_ids), ("company_id", "=", company_id)],
            fields=["id"],
            limit=len(journal_ids),
        )
    )
    if {record["id"] for record in records} != set(journal_ids):
        raise failure_type(
            "company_unavailable",
            "The requested company-scoped journals are unavailable.",
            exit_code=3,
        )
    return [
        {"id": journal_id, "model": "account.journal", "selected": True}
        for journal_id in journal_ids
    ]


def verify_journal_options(
    report: Any, options: dict[str, Any], journal_ids: list[int], failure_type: Any
) -> None:
    # Native "all journals" may have every selected flag False; use its resolver.
    if not report.filter_journals or {
        item["id"] for item in report._get_options_journals(options)
    } != set(journal_ids):
        raise failure_type(
            "odoo_runtime_error",
            "The native report did not retain the requested journal selection.",
            exit_code=7,
        )
