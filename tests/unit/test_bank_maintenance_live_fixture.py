from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from uuid import uuid4

import pytest

from odoo_accounting_cli_v4.capabilities import core_writes as public


@pytest.fixture
def live_fixture(monkeypatch):
    path = (
        Path(__file__).resolve().parents[1]
        / "integration"
        / "test_bank_statement_payment_maintenance_live.py"
    )
    spec = importlib.util.spec_from_file_location("bank_maintenance_fixture", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(
        public,
        "validate_core_write_request",
        lambda capability, request: (None, {"company_id": 1}, request["parameters"]),
    )
    return module


@pytest.mark.parametrize("canonical", [None, "canonical-key"])
def test_live_fixture_reuses_the_correct_key_on_replay(
    live_fixture, monkeypatch, canonical
):
    monkeypatch.setattr(public, "_expected_idempotency_key", lambda *args: canonical)
    keys = []

    def invoke(*args, key):
        keys.append(key)
        return {"result": {"id": 1}, "idempotent_replay": len(keys) == 2}

    monkeypatch.setattr(live_fixture, "_invoke", invoke)
    result = live_fixture._write(
        None, "v4-dev", uuid4(), "payment.create", {},
        replayable=True, explicit_key="caller-key" if canonical is None else None,
    )
    assert result == {"id": 1}
    assert keys == [canonical or "caller-key"] * 2


@pytest.mark.parametrize("canonical,explicit", [(None, None), ("canonical", "wrong")])
def test_live_fixture_rejects_missing_or_noncanonical_keys(
    live_fixture, monkeypatch, canonical, explicit
):
    monkeypatch.setattr(public, "_expected_idempotency_key", lambda *args: canonical)
    with pytest.raises(RuntimeError):
        live_fixture._write(
            None, "v4-dev", uuid4(), "payment.create", {},
            replayable=False, explicit_key=explicit,
        )


def test_odoo_worker_can_import_the_cli_environment_dependencies(
    live_fixture, monkeypatch
):
    captured = {}
    monkeypatch.setattr(live_fixture, "_worker_command", lambda *args: (["python"], 1))

    def capture_run(*args, **kwargs):
        captured.update(kwargs["env"])
        raise RuntimeError("captured worker environment")

    monkeypatch.setattr(live_fixture.subprocess, "run", capture_run)
    with pytest.raises(RuntimeError, match="captured worker environment"):
        live_fixture._run_worker("v4-dev", uuid4(), Path("runtime.json"), {})
    assert live_fixture.sysconfig.get_path("purelib") in captured["PYTHONPATH"].split(
        os.pathsep
    )
