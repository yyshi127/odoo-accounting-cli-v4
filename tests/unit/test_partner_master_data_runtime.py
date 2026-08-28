from __future__ import annotations

import re
from types import SimpleNamespace
from typing import Any

import pytest

from odoo_accounting_cli_v4.bridge import core_object_reads_runtime as reads
from odoo_accounting_cli_v4.bridge import core_writes_runtime as writes


class Failure(RuntimeError):
    def __init__(self, code: str, message: str, *, exit_code: int, **_: Any) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code


def _relation_id(value: Any) -> Any:
    return getattr(value, "id", value) or False


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


class Record:
    def __init__(self, model: Model, record_id: int, **values: Any) -> None:
        self._model = model
        self.id = record_id
        for name, value in values.items():
            setattr(self, name, value)

    def write(self, values: dict[str, Any]) -> None:
        self._model.env.calls.append(("write", self._model.name, self.id, dict(values)))
        self._model.apply_values(self, values)

    def invalidate_recordset(self, _fields: list[str] | None = None) -> None:
        return None

    def with_company(self, _company: Any) -> Record:
        return self

    def action_archive(self) -> None:
        self.active = False

    def action_unarchive(self) -> None:
        self.active = True


class Model:
    def __init__(self, env: Env, name: str) -> None:
        self.env = env
        self.name = name
        self.records: list[Record] = []

    def with_context(self, **_: Any) -> Model:
        return self

    def with_company(self, company_id: int) -> Model:
        assert company_id == self.env.company.id
        return self

    def browse(self, ids: int | list[int]) -> Records:
        wanted = [ids] if isinstance(ids, int) else ids
        return Records(self, [row for row in self.records if row.id in wanted])

    def search(
        self,
        domain: list[Any],
        limit: int | None = None,
        **_: Any,
    ) -> Records:
        selected = [row for row in self.records if _matches(row, domain)]
        return Records(self, selected[:limit] if limit is not None else selected)

    def create(self, values: dict[str, Any]) -> Records:
        self.env.next_id += 1
        resolved = self._resolved(values)
        if self.name == "res.partner":
            for field in (
                "vat",
                "ref",
                "email",
                "phone",
                "mobile",
                "street",
                "street2",
                "city",
                "zip",
                "state_id",
                "country_id",
                "lang",
            ):
                resolved.setdefault(field, False)
            resolved.setdefault("commercial_partner_id", False)
        elif self.name == "res.partner.bank":
            partner = resolved["partner_id"]
            resolved.setdefault("acc_holder_name", partner.name)
            resolved.setdefault("bank_id", False)
            resolved.setdefault("currency_id", False)
            resolved["company_id"] = partner.company_id
        row = Record(self, self.env.next_id, **resolved)
        if self.name == "res.partner" and not row.commercial_partner_id:
            row.commercial_partner_id = row
        self.records.append(row)
        self.env.calls.append(("create", self.name, dict(values)))
        return Records(self, [row])

    def _resolved(self, values: dict[str, Any]) -> dict[str, Any]:
        result = dict(values)
        relations = {
            "company_id": "res.company",
            "partner_id": "res.partner",
            "state_id": "res.country.state",
            "country_id": "res.country",
            "bank_id": "res.bank",
            "currency_id": "res.currency",
            "property_account_receivable_id": "account.account",
            "property_account_payable_id": "account.account",
            "property_account_position_id": "account.fiscal.position",
            "property_payment_term_id": "account.payment.term",
            "property_supplier_payment_term_id": "account.payment.term",
        }
        for field_name, model_name in relations.items():
            if field_name not in result:
                continue
            value = result[field_name]
            if value in (None, False):
                result[field_name] = False
            elif isinstance(value, int):
                result[field_name] = self.env[model_name].browse(value).records[0]
        return result

    def apply_values(self, record: Record, values: dict[str, Any]) -> None:
        for field_name, value in self._resolved(values).items():
            setattr(record, field_name, value)


def _field_value(record: Record, dotted_name: str) -> Any:
    value: Any = record
    for part in dotted_name.split("."):
        value = getattr(value, part, False)
    return value


def _matches(record: Record, domain: list[Any]) -> bool:
    terms = [term for term in domain if isinstance(term, tuple)]
    for field_name in {term[0] for term in terms}:
        field_terms = [term for term in terms if term[0] == field_name]
        actual = _field_value(record, field_name)
        actual_id = _relation_id(actual)
        if (
            field_name in {"company_id", "partner_id.company_id"}
            and len(field_terms) > 1
        ):
            allowed = {_relation_id(term[2]) for term in field_terms}
            if actual_id not in allowed:
                return False
            continue
        for _, operator, expected in field_terms:
            if operator == "=" and field_name == "acc_number":
                sanitize = lambda value: re.sub(r"\W+", "", value).upper()
                if sanitize(actual) != sanitize(expected):
                    return False
            elif operator == "=" and actual_id != _relation_id(expected):
                return False
            elif operator == "in":
                if isinstance(actual, list):
                    actual_values = {_relation_id(item) for item in actual}
                    if not actual_values.intersection(map(_relation_id, expected)):
                        return False
                elif actual_id not in {_relation_id(item) for item in expected}:
                    return False
            elif operator == "=like":
                if not isinstance(actual, str) or not actual.endswith(
                    expected.removeprefix("%")
                ):
                    return False
    return True


class Env:
    uid = 5

    def __init__(self) -> None:
        self.calls: list[tuple[Any, ...]] = []
        self.next_id = 1000
        model_names = (
            "res.company",
            "res.partner",
            "res.partner.bank",
            "res.country.state",
            "res.country",
            "res.bank",
            "res.currency",
            "account.account",
            "account.fiscal.position",
            "account.payment.term",
        )
        self.models = {name: Model(self, name) for name in model_names}
        self.company = self.add("res.company", 7, name="Current")
        self.other_company = self.add("res.company", 8, name="Other")
        self.country = self.add("res.country", 21, name="China", active=True)
        self.other_country = self.add("res.country", 22, name="Japan", active=True)
        self.state = self.add(
            "res.country.state", 31, name="Shanghai", country_id=self.country
        )
        self.bank = self.add("res.bank", 41, name="Bank", active=True)
        self.currency = self.add("res.currency", 51, name="CNY", active=True)
        self.receivable = self.add(
            "account.account",
            61,
            account_type="asset_receivable",
            company_ids=[self.company],
            active=True,
        )
        self.payable = self.add(
            "account.account",
            62,
            account_type="liability_payable",
            company_ids=[self.company],
            active=True,
        )
        self.position = self.add(
            "account.fiscal.position",
            71,
            company_id=self.company,
            active=True,
        )
        self.term = self.add("account.payment.term", 81, company_id=False, active=True)

    def __getitem__(self, name: str) -> Model:
        return self.models[name]

    def add(self, model_name: str, record_id: int, **values: Any) -> Record:
        row = Record(self[model_name], record_id, **values)
        self[model_name].records.append(row)
        return row


def _partner_parameters() -> dict[str, Any]:
    return {
        "name": "Acme",
        "company_type": "company",
        "vat": None,
        "reference": "ACME-1",
        "email": "finance@example.com",
        "phone": None,
        "mobile": None,
        "street": None,
        "street2": None,
        "city": "Shanghai",
        "zip": None,
        "state_id": 31,
        "country_id": 21,
        "language": "zh_CN",
    }


def test_partner_read_contract_scopes_fields_and_strips_private_marker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert reads._scope_domain(SimpleNamespace(), "partner.search", 7) == [
        "|",
        ("company_id", "=", False),
        ("company_id", "=", 7),
    ]
    assert reads._scope_domain(SimpleNamespace(), "partner.get", 7) == [
        "|",
        ("company_id", "=", False),
        ("company_id", "=", 7),
    ]
    assert reads._REFERENCE_FIELDS["partner"] == (
        "id",
        "name",
        "display_name",
        "company_type",
        "active",
        "vat",
        "ref",
        "email",
        "phone",
        "mobile",
        "street",
        "street2",
        "city",
        "zip",
        "state_id",
        "country_id",
        "lang",
        "company_id",
        "parent_id",
        "customer_rank",
        "supplier_rank",
    )
    without_mobile = {
        name: object()
        for name in reads._REFERENCE_FIELDS["partner"]
        if name != "mobile"
    }
    assert "mobile" not in reads._available_reference_fields(
        SimpleNamespace(_fields=without_mobile), "partner"
    )

    related = {
        "res.country.state": {31: {"id": 31, "name": "Shanghai"}},
        "res.country": {21: {"id": 21, "name": "China"}},
        "res.partner": {9: {"id": 9, "complete_name": "Parent", "company_id": False}},
    }
    monkeypatch.setattr(
        reads,
        "_related_rows",
        lambda _env, model, ids, _fields: {
            record_id: related[model][record_id] for record_id in ids
        },
    )
    marker = "[ODACV4:" + "a" * 64 + "]"
    item = reads._normalize_partners(
        SimpleNamespace(),
        [
            {
                "id": 10,
                "name": "Acme",
                "display_name": "Acme",
                "company_type": "company",
                "active": True,
                "vat": "CN1",
                "ref": f"PUBLIC {marker}",
                "email": "a@example.com",
                "phone": False,
                "mobile": "123",
                "street": "Road",
                "street2": False,
                "city": "Shanghai",
                "zip": "200000",
                "state_id": 31,
                "country_id": 21,
                "lang": "zh_CN",
                "company_id": 7,
                "parent_id": 9,
                "customer_rank": 2,
                "supplier_rank": 0,
            }
        ],
        7,
    )[0]

    assert set(item) == {
        "id",
        "name",
        "display_name",
        "company_type",
        "active",
        "vat",
        "reference",
        "email",
        "phone",
        "mobile",
        "street",
        "street2",
        "city",
        "zip",
        "state",
        "country",
        "language",
        "company_id",
        "parent",
        "customer_rank",
        "supplier_rank",
    }
    assert item["reference"] == "PUBLIC"
    assert item["state"] == {"id": 31, "name": "Shanghai"}
    assert item["parent"] == {"id": 9, "name": "Parent"}


def test_partner_read_normalization_rejects_cross_company_rows() -> None:
    with pytest.raises(ValueError, match="outside company"):
        reads._normalize_partners(
            SimpleNamespace(),
            [
                {
                    "id": 10,
                    "name": "Foreign",
                    "display_name": "Foreign",
                    "company_type": "company",
                    "active": True,
                    "company_id": 8,
                    "customer_rank": 0,
                    "supplier_rank": 0,
                }
            ],
            7,
        )


def test_partner_create_update_archive_restore_and_replay() -> None:
    env = Env()
    parameters = _partner_parameters()

    created, replay = writes._create_partner(
        env, parameters, 7, "partner.create:key", Failure
    )
    created_again, replay_again = writes._create_partner(
        env, parameters, 7, "partner.create:key", Failure
    )
    partner = env["res.partner"].browse(created["id"])

    assert replay is False
    assert replay_again is True
    assert created_again == created
    assert partner.ref.startswith("ACME-1 [ODACV4:")
    assert (
        len([call for call in env.calls if call[:2] == ("create", "res.partner")]) == 1
    )

    changed, changed_replay = writes._update_partner(
        env,
        {"partner_id": partner.id, "changes": {"reference": None, "name": "Acme 2"}},
        7,
        Failure,
    )
    _, unchanged_replay = writes._update_partner(
        env,
        {"partner_id": partner.id, "changes": {"reference": None, "name": "Acme 2"}},
        7,
        Failure,
    )
    assert changed["name"] == "Acme 2"
    assert partner.ref.startswith("[ODACV4:")
    assert changed_replay is False
    assert unchanged_replay is True

    archived, archive_replay = writes._transition_partner(
        env, "partner.archive", {"partner_id": partner.id}, 7, Failure
    )
    _, archive_again = writes._transition_partner(
        env, "partner.archive", {"partner_id": partner.id}, 7, Failure
    )
    restored, restore_replay = writes._transition_partner(
        env, "partner.restore", {"partner_id": partner.id}, 7, Failure
    )
    _, restore_again = writes._transition_partner(
        env, "partner.restore", {"partner_id": partner.id}, 7, Failure
    )
    assert (archived["state"], archive_replay, archive_again) == (
        "archived",
        False,
        True,
    )
    assert (restored["state"], restore_replay, restore_again) == (
        "active",
        False,
        True,
    )

    invalid_geo = dict(parameters, country_id=env.other_country.id)
    with pytest.raises(Failure) as caught:
        writes._create_partner(env, invalid_geo, 7, "partner.create:geo", Failure)
    assert caught.value.code == "business_rule_error"


def test_partner_write_treats_uninstalled_mobile_field_as_optional() -> None:
    env = Env()
    model = env["res.partner"]
    model._fields = {
        name: object()
        for name in (
            "name",
            "company_type",
            "vat",
            "ref",
            "email",
            "phone",
            "street",
            "street2",
            "city",
            "zip",
            "state_id",
            "country_id",
            "lang",
            "company_id",
            "active",
        )
    }
    parameters = _partner_parameters()

    result, replay = writes._create_partner(
        env, parameters, 7, "partner.create:no-mobile", Failure
    )

    create_values = next(
        call[2] for call in env.calls if call[:2] == ("create", "res.partner")
    )
    assert result["model"] == "res.partner"
    assert replay is False
    assert "mobile" not in create_values

    with pytest.raises(Failure) as caught:
        writes._update_partner(
            env,
            {"partner_id": result["id"], "changes": {"mobile": "123"}},
            7,
            Failure,
        )
    assert caught.value.code == "configuration_missing"


def test_partner_accounting_update_replays_and_rejects_child_partner() -> None:
    env = Env()
    partner = env.add(
        "res.partner",
        91,
        name="Accounting Partner",
        active=True,
        company_id=False,
        commercial_partner_id=False,
        property_account_receivable_id=False,
        property_account_payable_id=False,
        property_account_position_id=False,
        property_payment_term_id=False,
        property_supplier_payment_term_id=False,
    )
    partner.commercial_partner_id = partner
    changes = {
        "property_account_receivable_id": env.receivable.id,
        "property_account_payable_id": env.payable.id,
        "property_account_position_id": env.position.id,
        "property_payment_term_id": env.term.id,
        "property_supplier_payment_term_id": None,
    }

    result, replay = writes._update_partner_accounting(
        env, {"partner_id": partner.id, "changes": changes}, 7, Failure
    )
    _, replay_again = writes._update_partner_accounting(
        env, {"partner_id": partner.id, "changes": changes}, 7, Failure
    )
    assert result["model"] == "res.partner"
    assert replay is False
    assert replay_again is True
    assert partner.property_account_receivable_id.id == env.receivable.id

    child = env.add(
        "res.partner",
        92,
        name="Child",
        active=True,
        company_id=False,
        commercial_partner_id=partner,
    )
    with pytest.raises(Failure) as caught:
        writes._update_partner_accounting(
            env,
            {
                "partner_id": child.id,
                "changes": {"property_account_receivable_id": env.receivable.id},
            },
            7,
            Failure,
        )
    assert caught.value.code == "business_rule_error"


def test_partner_bank_create_update_archive_restore_and_replay() -> None:
    env = Env()
    partner = env.add(
        "res.partner",
        91,
        name="Bank Partner",
        active=True,
        company_id=env.company,
        commercial_partner_id=False,
    )
    partner.commercial_partner_id = partner
    parameters = {
        "partner_id": partner.id,
        "account_number": "CN 123-456",
        "account_holder_name": None,
        "bank_id": env.bank.id,
        "currency_id": env.currency.id,
    }

    created, replay = writes._create_partner_bank(env, parameters, 7, Failure)
    created_again, replay_again = writes._create_partner_bank(
        env, parameters, 7, Failure
    )
    bank = env["res.partner.bank"].browse(created["id"])
    assert replay is False
    assert replay_again is True
    assert created_again == created
    assert bank.acc_holder_name == partner.name
    assert bank.allow_out_payment is False

    changed, changed_replay = writes._update_partner_bank(
        env,
        {
            "partner_bank_id": bank.id,
            "changes": {"account_number": "CN999", "account_holder_name": None},
        },
        7,
        Failure,
    )
    _, unchanged_replay = writes._update_partner_bank(
        env,
        {
            "partner_bank_id": bank.id,
            "changes": {"account_number": "CN999", "account_holder_name": None},
        },
        7,
        Failure,
    )
    assert changed["name"] == "CN999"
    assert changed_replay is False
    assert unchanged_replay is True

    archived, archive_replay = writes._transition_partner_bank(
        env,
        "partner.bank_account.archive",
        {"partner_bank_id": bank.id},
        7,
        Failure,
    )
    _, archive_again = writes._transition_partner_bank(
        env,
        "partner.bank_account.archive",
        {"partner_bank_id": bank.id},
        7,
        Failure,
    )
    restored, restore_replay = writes._transition_partner_bank(
        env,
        "partner.bank_account.restore",
        {"partner_bank_id": bank.id},
        7,
        Failure,
    )
    _, restore_again = writes._transition_partner_bank(
        env,
        "partner.bank_account.restore",
        {"partner_bank_id": bank.id},
        7,
        Failure,
    )
    assert (archived["state"], archive_replay, archive_again) == (
        "archived",
        False,
        True,
    )
    assert (restored["state"], restore_replay, restore_again) == (
        "active",
        False,
        True,
    )


def test_partner_bank_mutations_hide_another_company_owner() -> None:
    env = Env()
    foreign_partner = env.add(
        "res.partner",
        91,
        name="Foreign",
        active=True,
        company_id=env.other_company,
        commercial_partner_id=False,
    )
    foreign_partner.commercial_partner_id = foreign_partner
    foreign_bank = env.add(
        "res.partner.bank",
        92,
        acc_number="FOREIGN",
        acc_holder_name="Foreign",
        partner_id=foreign_partner,
        company_id=False,
        active=True,
        allow_out_payment=False,
        bank_id=False,
        currency_id=False,
    )

    with pytest.raises(Failure) as caught:
        writes._update_partner_bank(
            env,
            {
                "partner_bank_id": foreign_bank.id,
                "changes": {"account_number": "NOPE"},
            },
            7,
            Failure,
        )
    assert caught.value.code == "record_not_found"
    assert foreign_bank.acc_number == "FOREIGN"
