"""Narrow bridge port for fixed high-frequency accounting object reads."""

from __future__ import annotations

from typing import Any, Protocol

ACTION = "accounting.core_object.read"
CAPABILITY_IDS = frozenset(
    {
        "account.account.get",
        "journal.get",
        "tax.get",
        "payment_term.get",
        "currency.get",
        "partner.accounting.get",
        "partner.search",
        "partner.get",
        "bank.transaction.get",
        "cash_rounding.get",
        "cash_rounding.list",
        "journal_item.search",
        "journal_item.get",
        "journal.group.get",
        "journal.group.list",
        "incoterm.get",
        "incoterm.list",
        "payment.method.get",
        "payment.method.list",
        "reconciliation.model.get",
        "reconciliation.model.list",
        "product.search",
        "product.get",
        "analytic.plan.list",
        "analytic.plan.get",
        "analytic.account.search",
        "analytic.account.get",
        "analytic.line.search",
        "analytic.line.get",
        "analytic.distribution_model.list",
        "analytic.distribution_model.get",
        "analytic.applicability.list",
        "analytic.applicability.get",
        "budget.search",
        "budget.get",
        "budget.line.list",
        "budget.line.get",
        "bank.statement.search",
        "bank.statement.get",
        "fiscal_position.search",
        "fiscal_position.get",
        "fiscal_position.account_mapping.list",
        "fiscal_position.tax_mapping.list",
        "partner.bank_account.search",
        "partner.bank_account.get",
        "account.tag.list",
        "account.tag.get",
        "reconciliation.partial.list",
        "reconciliation.partial.get",
        "reconciliation.full.list",
        "reconciliation.full.get",
        "tax.group.list",
        "tax.group.get",
        "account.group.list",
        "account.group.get",
        "journal.configuration.inspect",
        "tax.repartition_line.list",
        "tax.repartition_line.get",
        "reconciliation.model.line.list",
        "reconciliation.model.line.get",
        "bank.list",
        "bank.get",
        "report.catalog.list",
        "report.catalog.get",
        "invoice.duplicate_candidates.list",
        "invoice.tax_breakdown.inspect",
        "recurring.journal_entry.search",
        "recurring.journal_entry.get",
        "account.transfer_model.search",
        "account.transfer_model.get",
        "partner.credit_exposure.inspect",
        "journal.sequence_irregularity.list",
        "account.lock_exception.search",
        "account.lock_exception.get",
        "report.external_value.search",
        "report.external_value.get",
    }
)


class BridgeClient(Protocol):
    def invoke(self, action: str, payload: dict[str, Any]) -> dict[str, Any]: ...


class OdooCoreObjectReadPort:
    def __init__(self, client: BridgeClient) -> None:
        self._client = client
        self._user_id: int | None = None

    @property
    def user_id(self) -> int:
        if self._user_id is None:
            raise ValueError("No verified Odoo core-object page has been read.")
        return self._user_id

    def read(
        self,
        *,
        capability_id: str,
        company_id: int,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        if capability_id not in CAPABILITY_IDS:
            raise ValueError("Unsupported core-object read capability.")
        self._user_id = None
        page = self._client.invoke(
            ACTION,
            {
                "capability_id": capability_id,
                "company_id": company_id,
                "parameters": parameters,
            },
        )
        if not _valid_page(page, capability_id):
            raise ValueError("The Odoo bridge returned an invalid core-object page.")
        self._user_id = page["user_id"]
        return page


def _valid_page(page: Any, capability_id: str) -> bool:
    if not isinstance(page, dict):
        return False
    base_keys = {
        "user_id",
        "company_visible",
        "module_installed",
        "access_allowed",
        "cursor_found",
        "items",
    }
    successful = all(
        page.get(key) is True
        for key in (
            "company_visible",
            "module_installed",
            "access_allowed",
            "cursor_found",
        )
    )
    expected_keys = (
        base_keys | {"removes_all_taxes"}
        if capability_id == "fiscal_position.tax_mapping.list" and successful
        else base_keys
    )
    return bool(
        set(page) == expected_keys
        and isinstance(page["user_id"], int)
        and not isinstance(page["user_id"], bool)
        and page["user_id"] > 0
        and all(
            isinstance(page[key], bool)
            for key in (
                "company_visible",
                "module_installed",
                "access_allowed",
                "cursor_found",
            )
        )
        and isinstance(page["items"], list)
        and all(isinstance(item, dict) for item in page["items"])
        and (
            capability_id != "fiscal_position.tax_mapping.list"
            or not successful
            or (
                isinstance(page["removes_all_taxes"], bool)
                and (not page["removes_all_taxes"] or not page["items"])
            )
        )
    )
