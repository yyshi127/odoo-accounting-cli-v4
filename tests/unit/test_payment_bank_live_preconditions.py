from __future__ import annotations

import runpy
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

_LIVE_TEST = (
    Path(__file__).resolve().parents[1]
    / "integration"
    / ("test_payment_bank_capability_batch_live.py")
)


@pytest.mark.parametrize(
    "shared_role", [None, "default_account_id", "suspense_account_id"]
)
def test_split_receipt_fixture_requires_distinct_account_roles(
    monkeypatch, shared_role
):
    fixture = runpy.run_path(str(_LIVE_TEST))["_fixture_ids"]
    monkeypatch.setitem(fixture.__globals__, "_one", lambda records, _label: records)
    outstanding = SimpleNamespace(
        id=153, reconcile=True, company_ids=SimpleNamespace(ids=[1])
    )
    bank = SimpleNamespace(
        id=14,
        default_account_id=SimpleNamespace(id=152),
        suspense_account_id=SimpleNamespace(id=154),
    )
    if shared_role:
        setattr(bank, shared_role, outstanding)

    def journals(domain, **_kwargs):
        journal_type = next(
            value for field, _operator, value in domain if field == "type"
        )
        return bank if journal_type == "bank" else SimpleNamespace(id=20)

    company = SimpleNamespace(currency_id=SimpleNamespace(id=6))
    env = {
        "res.company": SimpleNamespace(
            browse=lambda _id: SimpleNamespace(exists=lambda: company)
        ),
        "res.partner": SimpleNamespace(
            search=lambda _domain: SimpleNamespace(ids=[16, 17])
        ),
        "account.journal": SimpleNamespace(search=journals),
        "account.account": SimpleNamespace(
            search=lambda _domain, **_kwargs: SimpleNamespace(id=40)
        ),
        "account.payment.method.line": SimpleNamespace(
            search=lambda _domain, **_kwargs: SimpleNamespace(
                id=3, payment_account_id=outstanding
            )
        ),
    }
    if shared_role:
        with pytest.raises(RuntimeError, match="distinct from the bank and suspense"):
            fixture(env, "v4-dev")
    else:
        assert fixture(env, "v4-dev")["outstanding"] == outstanding.id


def test_live_cli_preserves_native_failure_chain_only_for_test_diagnostics(monkeypatch):
    from odoo_accounting_cli_v4 import cli

    helpers = runpy.run_path(str(_LIVE_TEST))
    client = helpers["_RuntimeClient"](object())
    native_failure = RuntimeError("native test failure")

    def fail(_argv, *, stdout, **_kwargs):
        client.last_runtime_failure = native_failure
        stdout.write('{"success":false}\n')
        return 6

    monkeypatch.setattr(cli, "main", fail)
    with pytest.raises(AssertionError) as caught:
        helpers["_cli"](
            client, "v4-dev", uuid.uuid4(), "payment.get", {"payment_id": 1}
        )
    assert caught.value.__cause__ is native_failure
