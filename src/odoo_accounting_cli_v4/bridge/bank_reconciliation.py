"""Fixed bridge ports for bank-reconciliation reads."""

from __future__ import annotations

from typing import Any, Protocol

_GET_ACTION = "account.bank.statement.line.reconciliation.get"
_CANDIDATE_ACTION = "account.bank.statement.line.match_candidate.read_page"
_GATE_FIELDS = {
    "user_id",
    "company_visible",
    "module_installed",
    "access_allowed",
}


class BridgeClient(Protocol):
    def invoke(self, action: str, payload: dict[str, Any]) -> dict[str, Any]: ...


def _positive_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


class OdooBankReconciliationPort:
    def __init__(self, client: BridgeClient) -> None:
        self._client = client
        self._user_id: int | None = None

    @property
    def user_id(self) -> int:
        if self._user_id is None:
            raise ValueError("No verified bank-reconciliation result has been read.")
        return self._user_id

    def _verified_page(self, page: Any, result_field: str) -> dict[str, Any]:
        if (
            not isinstance(page, dict)
            or set(page) != _GATE_FIELDS | {result_field}
            or not _positive_integer(page["user_id"])
            or not isinstance(page["company_visible"], bool)
            or not isinstance(page["module_installed"], bool)
            or not isinstance(page["access_allowed"], bool)
            or (
                result_field == "rows"
                and (
                    not isinstance(page["rows"], list)
                    or any(not isinstance(row, dict) for row in page["rows"])
                )
            )
            or (
                result_field == "result"
                and not (page["result"] is None or isinstance(page["result"], dict))
            )
        ):
            raise ValueError("The Odoo bridge returned an invalid reconciliation page.")
        self._user_id = page["user_id"]
        return page

    def get(self, *, company_id: int, transaction_id: int) -> dict[str, Any]:
        self._user_id = None
        page = self._client.invoke(
            _GET_ACTION,
            {"company_id": company_id, "transaction_id": transaction_id},
        )
        return self._verified_page(page, "result")

    def read_candidates_page(
        self,
        *,
        company_id: int,
        transaction_id: int,
        after: list[Any] | None,
        limit: int,
    ) -> dict[str, Any]:
        self._user_id = None
        page = self._client.invoke(
            _CANDIDATE_ACTION,
            {
                "company_id": company_id,
                "transaction_id": transaction_id,
                "after": after,
                "limit": limit,
            },
        )
        return self._verified_page(page, "rows")
