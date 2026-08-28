from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest

from odoo_accounting_cli_v4.bridge import core_writes_runtime as writes


class Failure(RuntimeError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        exit_code: int,
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code
        self.retryable = retryable
        self.details = details or {}


class AccessError(Exception):
    pass


class ValidationError(Exception):
    pass


class Records:
    def __init__(self, model: Model, records: list[Record] | None = None) -> None:
        self.model = model
        self.records = records or []

    def __iter__(self):
        return iter(self.records)

    def __len__(self) -> int:
        return len(self.records)

    def __bool__(self) -> bool:
        return bool(self.records)

    def __getattr__(self, name: str) -> Any:
        if len(self.records) != 1:
            raise AttributeError(name)
        return getattr(self.records[0], name)

    @property
    def ids(self) -> list[int]:
        return [record.id for record in self.records]

    @property
    def id(self) -> int | bool:
        return self.records[0].id if len(self.records) == 1 else False


class Record:
    def __init__(self, model: Model, record_id: int, **values: Any) -> None:
        self._model = model
        self.id = record_id
        for name, value in values.items():
            setattr(self, name, value)

    def write(self, values: dict[str, Any]) -> None:
        if self._model.env.write_error_model == self._model.name:
            raise self._model.env.write_error or RuntimeError("write failed")
        self._model.env.calls.append(("write", self._model.name, self.id, dict(values)))
        self._model.apply_values(self, values)

    def invalidate_recordset(self, _fields: list[str]) -> None:
        return None

    def action_archive(self) -> None:
        self.active = False

    def action_unarchive(self) -> None:
        self.active = True


def _ids(value: Any) -> list[Any]:
    if isinstance(value, Records):
        return value.ids
    if isinstance(value, list):
        return [getattr(item, "id", item) for item in value]
    return [getattr(value, "id", value)]


def _matches(record: Record, domain: list[Any]) -> bool:
    for field_name, operator, expected in domain:
        actual: Any = record
        for part in field_name.split("."):
            actual = getattr(actual, part, False)
        actual_ids = _ids(actual)
        expected_ids = _ids(expected)
        if operator == "=" and actual_ids[0] != expected_ids[0]:
            return False
        if operator == "in" and not set(actual_ids).intersection(expected_ids):
            return False
    return True


class Model:
    def __init__(self, env: Env, name: str) -> None:
        self.env = env
        self.name = name
        self.records: list[Record] = []

    def with_context(self, **context: Any) -> Model:
        self.env.contexts.append((self.name, context))
        return self

    def with_company(self, company_id: int) -> Model:
        assert company_id == self.env.company.id
        return self

    def has_access(self, operation: str) -> bool:
        self.env.calls.append(("has_access", self.name, operation))
        return self.env.denied_access != (self.name, operation)

    def search_count(self, domain: list[Any], limit: int | None = None) -> int:
        return len(self.search(domain, limit=limit))

    def search(
        self,
        domain: list[Any],
        limit: int | None = None,
        **_: Any,
    ) -> Records:
        selected = [record for record in self.records if _matches(record, domain)]
        return Records(self, selected[:limit] if limit is not None else selected)

    def browse(self, ids: int | list[int]) -> Records:
        requested = [ids] if isinstance(ids, int) else ids
        return Records(
            self, [record for record in self.records if record.id in requested]
        )

    def create(self, values: dict[str, Any]) -> Records:
        if self.env.create_error_model == self.name:
            raise self.env.create_error or RuntimeError("create failed")
        self.env.next_id += 1
        resolved = self._resolved(values)
        resolved.setdefault("active", True)
        if self.name == "account.account":
            resolved.setdefault("currency_id", False)
        elif self.name == "account.journal":
            resolved.setdefault("sequence", 10)
            resolved.setdefault("currency_id", False)
            resolved.setdefault("default_account_id", False)
            if (
                resolved["type"] in {"bank", "cash", "credit"}
                and not resolved["default_account_id"]
            ):
                resolved["default_account_id"] = self.env.default_account
        elif self.name == "account.tax":
            resolved.setdefault("sequence", 1)
            resolved.setdefault("tax_group_id", self.env.tax_group)
            resolved.setdefault("invoice_label", False)
            resolved.setdefault("price_include_override", False)
            resolved.setdefault("country_id", False)
        record = Record(self, self.env.next_id, **resolved)
        self.records.append(record)
        self.env.calls.append(("create", self.name, dict(values)))
        return Records(self, [record])

    def _resolved(self, values: dict[str, Any]) -> dict[str, Any]:
        result = dict(values)
        if "company_ids" in result:
            commands = result["company_ids"]
            company_ids = commands[0][2]
            result["company_ids"] = self.env["res.company"].browse(company_ids)
        relations = {
            "company_id": "res.company",
            "currency_id": "res.currency",
            "default_account_id": "account.account",
            "tax_group_id": "account.tax.group",
        }
        for field_name, model_name in relations.items():
            if field_name not in result:
                continue
            value = result[field_name]
            if value in (None, False):
                result[field_name] = False
            elif isinstance(value, int):
                result[field_name] = self.env[model_name].browse(value)
        return result

    def apply_values(self, record: Record, values: dict[str, Any]) -> None:
        resolved = self._resolved(values)
        if self.name == "account.tax" and resolved.get("tax_group_id") is False:
            resolved["tax_group_id"] = self.env.tax_group
        for field_name, value in resolved.items():
            setattr(record, field_name, value)


class Registry:
    def __init__(self, env: Env) -> None:
        self.env = env

    def get(self, name: str) -> Model | None:
        return self.env.models.get(name)


class User:
    def __init__(self, env: Env) -> None:
        self.env = env

    def has_group(self, group: str) -> bool:
        self.env.calls.append(("has_group", group))
        return self.env.group_allowed


class Env:
    uid = 5

    def __init__(self) -> None:
        self.calls: list[tuple[Any, ...]] = []
        self.contexts: list[tuple[str, dict[str, Any]]] = []
        self.denied_access: tuple[str, str] | None = None
        self.group_allowed = True
        self.create_error_model: str | None = None
        self.create_error: Exception | None = None
        self.write_error_model: str | None = None
        self.write_error: Exception | None = None
        self.next_id = 1000
        self.models = {
            name: Model(self, name)
            for name in (
                "res.company",
                "res.currency",
                "account.account",
                "account.journal",
                "account.tax",
                "account.tax.group",
            )
        }
        self.registry = Registry(self)
        self.user = User(self)
        self.company = self.add("res.company", 7, name="Demo")
        self.other_company = self.add("res.company", 8, name="Other")
        self.currency = self.add("res.currency", 21, name="USD", active=True)
        self.inactive_currency = self.add("res.currency", 22, name="OLD", active=False)
        self.default_account = self.add(
            "account.account",
            31,
            code="1000",
            name="Cash",
            account_type="asset_cash",
            reconcile=False,
            currency_id=False,
            company_ids=Records(self.models["res.company"], [self.company]),
            active=True,
        )
        self.foreign_account = self.add(
            "account.account",
            32,
            code="9000",
            name="Foreign",
            account_type="asset_cash",
            reconcile=False,
            currency_id=False,
            company_ids=Records(self.models["res.company"], [self.other_company]),
            active=True,
        )
        self.tax_group = self.add(
            "account.tax.group",
            41,
            name="Taxes",
            company_id=self.company,
            country_id=False,
        )
        self.foreign_tax_group = self.add(
            "account.tax.group",
            42,
            name="Foreign Taxes",
            company_id=self.other_company,
            country_id=False,
        )

    def __getitem__(self, name: str) -> Model:
        return self.models[name]

    def add(self, model_name: str, record_id: int, **values: Any) -> Record:
        record = Record(self[model_name], record_id, **values)
        self[model_name].records.append(record)
        return record


def _payload(
    capability_id: str,
    parameters: dict[str, Any],
    *,
    company_id: int = 7,
) -> dict[str, Any]:
    key = writes._deterministic_key(capability_id, parameters, company_id)
    return {
        "capability_id": capability_id,
        "company_id": company_id,
        "idempotency_key": key or "create-key-0001",
        "confirmation": capability_id,
        "parameters": parameters,
    }


def _dispatch(
    env: Env, capability_id: str, parameters: dict[str, Any]
) -> dict[str, Any]:
    return writes.dispatch(env, _payload(capability_id, parameters), 7, Failure)


def _account_parameters() -> dict[str, Any]:
    return {
        "code": "2000",
        "name": "Receivable",
        "account_type": "asset_receivable",
        "reconcile": True,
        "currency_id": None,
    }


def _journal_parameters() -> dict[str, Any]:
    return {
        "name": "Miscellaneous",
        "code": "MISC",
        "type": "general",
        "sequence": None,
        "currency_id": None,
        "default_account_id": 31,
    }


def _tax_parameters() -> dict[str, Any]:
    return {
        "name": "VAT 13%",
        "type_tax_use": "sale",
        "amount_type": "percent",
        "amount": "13",
        "sequence": None,
        "tax_group_id": None,
        "invoice_label": None,
        "price_include_override": None,
        "include_base_amount": False,
        "is_base_affected": True,
    }


@pytest.mark.parametrize(
    ("create_id", "update_id", "archive_id", "restore_id", "parameters", "id_name"),
    (
        (
            "account.account.create",
            "account.account.update",
            "account.account.archive",
            "account.account.restore",
            _account_parameters(),
            "account_id",
        ),
        (
            "journal.create",
            "journal.update",
            "journal.archive",
            "journal.restore",
            _journal_parameters(),
            "journal_id",
        ),
        (
            "tax.create",
            "tax.update",
            "tax.archive",
            "tax.restore",
            _tax_parameters(),
            "tax_id",
        ),
    ),
)
def test_create_replay_update_and_lifecycle(
    create_id: str,
    update_id: str,
    archive_id: str,
    restore_id: str,
    parameters: dict[str, Any],
    id_name: str,
) -> None:
    env = Env()
    first = _dispatch(env, create_id, parameters)
    replay = _dispatch(env, create_id, parameters)
    record_id = first["result"]["id"]

    assert first["idempotent_replay"] is False
    assert replay["idempotent_replay"] is True
    assert first["result"]["state"] == "active"

    changes: dict[str, Any]
    if create_id == "account.account.create":
        changes = {"name": "Trade Receivable", "currency_id": 21}
    elif create_id == "journal.create":
        changes = {"name": "General", "sequence": 20, "currency_id": 21}
    else:
        changes = {"amount": "12.5", "invoice_label": "VAT"}
    updated = _dispatch(env, update_id, {id_name: record_id, "changes": changes})
    update_replay = _dispatch(env, update_id, {id_name: record_id, "changes": changes})
    archived = _dispatch(env, archive_id, {id_name: record_id})
    archive_replay = _dispatch(env, archive_id, {id_name: record_id})
    restored = _dispatch(env, restore_id, {id_name: record_id})

    assert updated["idempotent_replay"] is False
    assert update_replay["idempotent_replay"] is True
    assert archived["result"]["state"] == "archived"
    assert archive_replay["idempotent_replay"] is True
    assert restored["result"]["state"] == "active"


def test_company_scope_and_reference_scope_fail_closed() -> None:
    env = Env()
    with pytest.raises(Failure) as caught:
        _dispatch(
            env,
            "account.account.update",
            {"account_id": env.foreign_account.id, "changes": {"name": "No"}},
        )
    assert caught.value.code == "record_not_found"

    journal = _journal_parameters()
    journal["default_account_id"] = env.foreign_account.id
    with pytest.raises(Failure) as caught:
        _dispatch(env, "journal.create", journal)
    assert caught.value.code == "record_not_found"

    tax = _tax_parameters()
    tax["tax_group_id"] = env.foreign_tax_group.id
    with pytest.raises(Failure) as caught:
        _dispatch(env, "tax.create", tax)
    assert caught.value.code == "record_not_found"


@pytest.mark.parametrize(
    ("capability_id", "parameters"),
    (
        (
            "account.account.update",
            {"account_id": 33, "changes": {"name": "Shared Updated"}},
        ),
        ("account.account.archive", {"account_id": 33}),
        ("account.account.restore", {"account_id": 33}),
    ),
)
def test_shared_multicompany_account_writes_fail_closed(
    capability_id: str,
    parameters: dict[str, Any],
) -> None:
    env = Env()
    initial_active = capability_id != "account.account.restore"
    shared = env.add(
        "account.account",
        33,
        code="3000",
        name="Shared",
        account_type="expense",
        reconcile=False,
        currency_id=False,
        company_ids=Records(
            env.models["res.company"], [env.company, env.other_company]
        ),
        active=initial_active,
    )

    with pytest.raises(Failure) as caught:
        _dispatch(env, capability_id, parameters)

    assert caught.value.code == "record_not_found"
    assert shared.name == "Shared"
    assert shared.active is initial_active
    assert not any(
        call[:3] == ("write", "account.account", shared.id) for call in env.calls
    )


@pytest.mark.parametrize(
    ("journal_type", "code"),
    (("bank", "BANK"), ("cash", "CASH"), ("credit", "CRED")),
)
def test_journal_create_accepts_native_automatic_default_account_but_update_clears(
    journal_type: str,
    code: str,
) -> None:
    env = Env()
    parameters = _journal_parameters()
    parameters.update(
        {
            "name": f"{journal_type.title()} Journal",
            "code": code,
            "type": journal_type,
            "default_account_id": None,
        }
    )

    first = _dispatch(env, "journal.create", parameters)
    replay = _dispatch(env, "journal.create", parameters)
    journal = env["account.journal"].browse(first["result"]["id"])

    assert first["idempotent_replay"] is False
    assert replay["idempotent_replay"] is True
    assert journal.default_account_id.id == env.default_account.id

    update_parameters = {
        "journal_id": journal.id,
        "changes": {"default_account_id": None},
    }
    cleared = _dispatch(env, "journal.update", update_parameters)
    cleared_replay = _dispatch(env, "journal.update", update_parameters)

    assert cleared["idempotent_replay"] is False
    assert cleared_replay["idempotent_replay"] is True
    assert journal.default_account_id is False


@pytest.mark.parametrize(
    ("capability_id", "parameters", "model"),
    (
        ("account.account.create", _account_parameters(), "account.account"),
        ("journal.create", _journal_parameters(), "account.journal"),
        ("tax.create", _tax_parameters(), "account.tax"),
    ),
)
def test_natural_key_conflicts(
    capability_id: str,
    parameters: dict[str, Any],
    model: str,
) -> None:
    env = Env()
    first = _dispatch(env, capability_id, parameters)
    record = env[model].browse(first["result"]["id"]).records[0]
    if model == "account.tax":
        record.amount = Decimal(12)
    else:
        record.name = "Changed outside CLI"

    with pytest.raises(Failure) as caught:
        _dispatch(env, capability_id, parameters)
    assert caught.value.code == "idempotency_conflict"


def test_manager_group_and_acl_gate_before_mutation() -> None:
    env = Env()
    env.group_allowed = False
    page = _dispatch(env, "account.account.create", _account_parameters())
    assert page["access_allowed"] is False
    assert ("has_group", "account.group_account_manager") in env.calls
    assert not any(call[:2] == ("create", "account.account") for call in env.calls)

    env = Env()
    env.denied_access = ("account.journal", "create")
    page = _dispatch(env, "journal.create", _journal_parameters())
    assert page["access_allowed"] is False
    assert not any(call[:2] == ("create", "account.journal") for call in env.calls)

    env = Env()
    env.denied_access = ("account.account", "create")
    page = _dispatch(env, "journal.create", _journal_parameters())
    assert page["access_allowed"] is False
    assert not any(call[:2] == ("create", "account.journal") for call in env.calls)


@pytest.mark.parametrize(
    ("error", "expected"),
    (
        (AccessError("denied"), "unauthorized"),
        (ValidationError("invalid"), "business_rule_error"),
        (RuntimeError("broken"), "odoo_write_error"),
    ),
)
def test_odoo_create_exceptions_are_mapped(error: Exception, expected: str) -> None:
    env = Env()
    env.create_error_model = "account.account"
    env.create_error = error
    with pytest.raises(Failure) as caught:
        _dispatch(env, "account.account.create", _account_parameters())
    assert caught.value.code == expected


def test_closed_payload_rejects_noncanonical_and_cross_company_values() -> None:
    env = Env()
    tax = _tax_parameters()
    tax["amount"] = "13.00"
    with pytest.raises(Failure) as caught:
        _dispatch(env, "tax.create", tax)
    assert caught.value.code == "bridge_protocol_error"
    assert env.calls == []

    payload = _payload("journal.create", _journal_parameters(), company_id=8)
    with pytest.raises(Failure) as caught:
        writes.dispatch(env, payload, 7, Failure)
    assert caught.value.code == "company_unavailable"


def test_account_code_preserves_case_and_tax_group_candidates_are_unique() -> None:
    env = Env()
    parameters = _account_parameters()
    parameters["code"] = "Ab10"
    account = _dispatch(env, "account.account.create", parameters)
    assert env["account.account"].browse(account["result"]["id"]).code == "Ab10"

    tax = _tax_parameters()
    _dispatch(env, "tax.create", tax)
    duplicate = dict(tax, amount="12")
    env["account.tax"].create(
        {
            **writes._tax_values(duplicate, creating=True),
            "company_id": 7,
            "active": True,
        }
    )
    with pytest.raises(Failure) as caught:
        _dispatch(env, "tax.create", tax)
    assert caught.value.code == "idempotency_conflict"


def test_tax_update_none_uses_automatic_group_and_replays() -> None:
    env = Env()
    custom_group = env.add(
        "account.tax.group",
        43,
        name="Custom Taxes",
        company_id=env.company,
        country_id=False,
    )
    parameters = _tax_parameters()
    parameters.update({"name": "Custom VAT", "tax_group_id": custom_group.id})
    created = _dispatch(env, "tax.create", parameters)
    tax = env["account.tax"].browse(created["result"]["id"])

    update = {"tax_id": tax.id, "changes": {"tax_group_id": None}}
    first = _dispatch(env, "tax.update", update)
    replay = _dispatch(env, "tax.update", update)

    assert first["idempotent_replay"] is False
    assert replay["idempotent_replay"] is True
    assert tax.tax_group_id.id == env.tax_group.id
    write = next(
        call for call in env.calls if call[:3] == ("write", "account.tax", tax.id)
    )
    assert write[3]["tax_group_id"] == env.tax_group.id


def test_tax_update_none_fails_when_automatic_group_is_missing() -> None:
    env = Env()
    parameters = _tax_parameters()
    parameters.update({"name": "Orphan VAT", "tax_group_id": env.tax_group.id})
    created = _dispatch(env, "tax.create", parameters)
    tax_id = created["result"]["id"]
    env["account.tax.group"].records.clear()

    with pytest.raises(Failure) as caught:
        _dispatch(
            env,
            "tax.update",
            {"tax_id": tax_id, "changes": {"tax_group_id": None}},
        )

    assert caught.value.code == "configuration_missing"
    assert not any(call[:3] == ("write", "account.tax", tax_id) for call in env.calls)


def test_runtime_contracts_are_fixed_to_manager_and_no_unlink() -> None:
    ids = {
        "account.account.create",
        "account.account.update",
        "account.account.archive",
        "account.account.restore",
        "journal.create",
        "journal.update",
        "journal.archive",
        "journal.restore",
        "tax.create",
        "tax.update",
        "tax.archive",
        "tax.restore",
    }
    assert ids <= writes.CAPABILITIES
    assert {writes._GROUPS[item] for item in ids} == {"account.group_account_manager"}
    assert all(("res.company", "read") in writes._ACCESS[item] for item in ids)
    assert ("account.account", "create") in writes._ACCESS["journal.create"]
    assert all(
        operation != "unlink"
        for item in ids
        for _model, operation in writes._ACCESS[item]
    )
