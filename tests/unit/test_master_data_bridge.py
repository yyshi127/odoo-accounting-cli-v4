from __future__ import annotations

import pytest

from odoo_accounting_cli_v4.bridge.master_data import OdooMasterDataPort


@pytest.mark.parametrize(
    ("capability_id", "expected_action"),
    [
        ("journal.list", "account.journal.read_page"),
        ("tax.list", "account.tax.read_page"),
        ("payment_term.list", "account.payment.term.read_page"),
        ("currency.list", "res.currency.read_page"),
    ],
)
def test_read_page_uses_the_fixed_composite_action(
    capability_id: str, expected_action: str
) -> None:
    calls: list[tuple[str, dict]] = []

    class FakeClient:
        def invoke(self, action, payload):
            calls.append((action, payload))
            return {
                "user_id": 42,
                "company_visible": True,
                "module_installed": True,
                "access_allowed": True,
                "rows": [{"id": 10}],
            }

    port = OdooMasterDataPort(FakeClient(), capability_id)

    assert port.read_page(company_id=7, after={"id": 9}, limit=101) == {
        "user_id": 42,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "rows": [{"id": 10}],
    }
    assert port.user_id == 42
    assert calls == [
        (
            expected_action,
            {"company_id": 7, "after": {"id": 9}, "limit": 101},
        )
    ]


@pytest.mark.parametrize(
    "capability_id",
    ["", "account.account.list", "journal.get", "JOURNAL.LIST", None],
)
def test_unknown_capability_fails_closed_before_invocation(capability_id) -> None:
    class NeverClient:
        def invoke(self, action, payload):
            raise AssertionError("an unknown capability must not reach the bridge")

    with pytest.raises(ValueError, match="Unsupported master-data capability"):
        OdooMasterDataPort(NeverClient(), capability_id)


def test_user_id_is_unavailable_before_a_verified_page() -> None:
    class NeverClient:
        def invoke(self, action, payload):
            raise AssertionError("unexpected invocation")

    port = OdooMasterDataPort(NeverClient(), "journal.list")

    with pytest.raises(ValueError, match="No verified Odoo master-data page"):
        _ = port.user_id


@pytest.mark.parametrize(
    "page",
    [
        {
            "user_id": 42,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "rows": [],
            "extra": True,
        },
        {
            "user_id": True,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "rows": [],
        },
        {
            "user_id": 42,
            "company_visible": 1,
            "module_installed": True,
            "access_allowed": True,
            "rows": [],
        },
        {
            "user_id": 42,
            "company_visible": True,
            "module_installed": "yes",
            "access_allowed": True,
            "rows": [],
        },
        {
            "user_id": 42,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": None,
            "rows": [],
        },
        {
            "user_id": 42,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "rows": {},
        },
        {
            "user_id": 42,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "rows": [1],
        },
    ],
)
def test_invalid_composite_envelope_is_rejected_and_not_cached(page: dict) -> None:
    class FakeClient:
        def invoke(self, action, payload):
            return page

    port = OdooMasterDataPort(FakeClient(), "journal.list")

    with pytest.raises(ValueError, match="invalid master-data page"):
        port.read_page(company_id=7, after=None, limit=2)
    with pytest.raises(ValueError, match="No verified Odoo master-data page"):
        _ = port.user_id


def test_failed_second_read_does_not_reuse_the_first_identity() -> None:
    responses = [
        {
            "user_id": 42,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "rows": [],
        },
        {},
    ]

    class FakeClient:
        def invoke(self, action, payload):
            return responses.pop(0)

    port = OdooMasterDataPort(FakeClient(), "journal.list")
    port.read_page(company_id=7, after=None, limit=2)
    assert port.user_id == 42

    with pytest.raises(ValueError, match="invalid master-data page"):
        port.read_page(company_id=7, after=None, limit=2)
    with pytest.raises(ValueError, match="No verified Odoo master-data page"):
        _ = port.user_id
