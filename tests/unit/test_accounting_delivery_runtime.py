from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from odoo_accounting_cli_v4.bridge import accounting_delivery_runtime as delivery


class Failure(RuntimeError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        exit_code: int,
        **_: Any,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code


class User:
    def __init__(self) -> None:
        self.groups = {"account.group_account_invoice"}

    def has_group(self, group: str) -> bool:
        return group in self.groups


def _value(record: Any, field_name: str) -> Any:
    value = record
    for part in field_name.split("."):
        value = getattr(value, part, False)
    return getattr(value, "id", value)


def _term_matches(record: Any, term: tuple[str, str, Any]) -> bool:
    field_name, operator, expected = term
    actual = _value(record, field_name)
    if isinstance(expected, Record):
        expected = expected.id
    if operator == "=":
        return actual == expected
    if operator == "in":
        return actual in expected
    if operator == "ilike":
        return str(expected).lower() in str(actual or "").lower()
    raise AssertionError(operator)


def _matches(record: Any, domain: list[Any]) -> bool:
    index = 0
    while index < len(domain):
        term = domain[index]
        if term == "|":
            if not (
                _term_matches(record, domain[index + 1])
                or _term_matches(record, domain[index + 2])
            ):
                return False
            index += 3
            continue
        if not _term_matches(record, term):
            return False
        index += 1
    return True


class Record:
    def __init__(self, record_model: Model, record_id: int, **values: Any) -> None:
        self._model = record_model
        self.id = record_id
        self.context: dict[str, Any] = {}
        for key, value in values.items():
            setattr(self, key, value)

    def __bool__(self) -> bool:
        return True

    def with_context(self, **context: Any) -> Record:
        self.context.update(context)
        self._model.env.calls.append(
            ("record_context", self._model.name, self.id, dict(context))
        )
        return self

    def write(self, values: dict[str, Any]) -> None:
        self._model.env.calls.append(("write", self._model.name, self.id, dict(values)))
        for key, value in values.items():
            setattr(self, key, value)

    def invalidate_recordset(self, fields: list[str]) -> None:
        self._model.env.calls.append(
            ("invalidate_recordset", self._model.name, self.id, list(fields))
        )

    def get_options(self, previous: dict[str, Any]) -> dict[str, Any]:
        assert self._model.name == "account.report"
        self._model.env.report_previous_options.append(deepcopy(previous))
        actual_date = {**previous["date"], "string": "computed"}
        if actual_date["mode"] == "single":
            actual_date["date_from"] = "2026-08-01"
        return {
            "report_id": self.id,
            "partner_ids": list(previous["partner_ids"]),
            "date": actual_date,
        }

    def action_send_and_print(self, **kwargs: Any) -> dict[str, Any]:
        env = self._model.env
        env.calls.append(("action_send_and_print", self._model.name, self.id, kwargs))
        if self._model.name == "account.move.send.wizard":
            env.add_message("account.move", self.move_id.id, self.body)
        elif self._model.name == "account.report.send":
            partner_id = self.report_options["partner_ids"][0]
            env.add_message("res.partner", partner_id, self.mail_body)
        else:
            raise AssertionError(self._model.name)
        return {"type": "ir.actions.act_window_close"}

    def action_send_mail(self) -> dict[str, Any]:
        assert self._model.name == "mail.compose.message"
        self._model.env.calls.append(
            ("action_send_mail", self._model.name, self.id, self.force_send)
        )
        payment_id = int(self.res_ids.strip("[]"))
        self._model.env.add_message("account.payment", payment_id, self.body)
        return {"type": "ir.actions.act_window_close"}


class Model:
    def __init__(self, env: Env, name: str, fields: set[str]) -> None:
        self.env = env
        self.name = name
        self._fields = {field: object() for field in fields}
        self.records: list[Record] = []
        self.context: dict[str, Any] = {}

    def with_context(self, **context: Any) -> Model:
        self.context.update(context)
        self.env.calls.append(("model_context", self.name, dict(context)))
        return self

    def has_access(self, operation: str) -> bool:
        return (self.name, operation) not in self.env.denied

    def search_count(self, domain: list[Any], limit: int | None = None) -> int:
        return len(self.search(domain, limit=limit))

    def search(
        self,
        domain: list[Any],
        *,
        order: str | None = None,
        limit: int | None = None,
    ) -> list[Record]:
        records = [record for record in self.records if _matches(record, domain)]
        if order == "id asc":
            records.sort(key=lambda record: record.id)
        return records if limit is None else records[:limit]

    def create(self, values: dict[str, Any]) -> Record:
        self.env.next_id += 1
        if self.name == "account.move.send.wizard":
            move = self.env.find("account.move", values["move_id"])
            record = Record(
                self,
                self.env.next_id,
                move_id=move,
                alerts={},
                sending_methods=list(values["sending_methods"]),
                extra_edis=list(values["extra_edis"]),
                template_id=self.env.refs["account.email_template_edi_invoice"],
                pdf_report_id=self.env.refs["account.account_invoices"],
                mail_partner_ids=[move.partner_id],
                body="<p>Invoice body</p>",
            )
        elif self.name == "mail.compose.message":
            payment_id = int(values["res_ids"].strip("[]"))
            payment = self.env.find("account.payment", payment_id)
            record = Record(
                self,
                self.env.next_id,
                **values,
                partner_ids=[payment.partner_id],
                attachment_ids=[],
                body="<p>Payment body</p>",
            )
        elif self.name == "account.report.send":
            partner_id = values["report_options"]["partner_ids"][0]
            partner = self.env.find("res.partner", partner_id)
            record = Record(
                self,
                self.env.next_id,
                **values,
                mail_partner_ids=[partner],
                mail_body="<p>Report body</p>",
                warnings={},
            )
        else:
            raise AssertionError(self.name)
        record.context.update(self.context)
        self.records.append(record)
        self.env.calls.append(("create", self.name, deepcopy(values)))
        return record


class Env:
    def __init__(self) -> None:
        self.uid = 5
        self.user = User()
        self.calls: list[tuple[Any, ...]] = []
        self.denied: set[tuple[str, str]] = set()
        self.next_id = 1000
        self.report_previous_options: list[dict[str, Any]] = []
        fields_by_model: dict[str, set[str]] = {}
        for shape in delivery._FIELDS.values():
            for model_name, fields in shape.items():
                fields_by_model.setdefault(model_name, set()).update(fields)
        for models in delivery._MODELS.values():
            for model_name in models:
                fields_by_model.setdefault(model_name, set())
        self.models = {
            name: Model(self, name, fields) for name, fields in fields_by_model.items()
        }
        self.registry = dict(self.models)
        self.refs: dict[str, Record] = {}
        self._seed()

    def __getitem__(self, model_name: str) -> Model:
        return self.models[model_name]

    def ref(self, xmlid: str, *, raise_if_not_found: bool = True) -> Record | bool:
        record = self.refs.get(xmlid)
        if record is None and raise_if_not_found:
            raise ValueError(xmlid)
        return record or False

    def add(self, model_name: str, record_id: int, **values: Any) -> Record:
        record = Record(self.models[model_name], record_id, **values)
        self.models[model_name].records.append(record)
        return record

    def find(self, model_name: str, record_id: int) -> Record:
        return next(
            record
            for record in self.models[model_name].records
            if record.id == record_id
        )

    def add_message(self, model_name: str, res_id: int, body: str) -> Record:
        self.next_id += 1
        return self.add(
            "mail.message",
            self.next_id,
            model=model_name,
            res_id=res_id,
            body=body,
        )

    def _reference(self, model_name: str, record_id: int, xmlid: str) -> Record:
        record = self.add(model_name, record_id, name=xmlid)
        self.refs[xmlid] = record
        return record

    def _seed(self) -> None:
        company = self.add("res.company", 7, name="Company")
        partner = self.add(
            "res.partner",
            21,
            company_id=False,
            email=" billing@example.com ",
        )
        self.add(
            "account.move",
            11,
            company_id=company,
            move_type="out_invoice",
            state="posted",
            partner_id=partner,
            no_followup=False,
        )
        self.add(
            "account.payment",
            31,
            company_id=company,
            state="paid",
            partner_id=partner,
        )
        self._reference("mail.template", 61, "account.email_template_edi_invoice")
        self._reference("ir.actions.report", 62, "account.account_invoices")
        self._reference(
            "mail.template", 63, "account.mail_template_data_payment_receipt"
        )
        self._reference(
            "ir.actions.report", 64, "account.action_report_payment_receipt"
        )
        self._reference(
            "account.report", 65, "account_reports.customer_statement_report"
        )
        self._reference(
            "mail.template", 66, "account_reports.email_template_customer_statement"
        )
        self._reference("account.report", 67, "account_reports.followup_report")
        self._reference(
            "mail.template",
            68,
            "account_reports.email_template_customer_follow_up_report",
        )


def _payload(
    capability_id: str,
    parameters: dict[str, Any],
    key: str | None = None,
) -> dict[str, Any]:
    return {
        "capability_id": capability_id,
        "company_id": 7,
        "parameters": parameters,
        "idempotency_key": key,
    }


def test_cursor_classification_accounts_for_transient_inspection() -> None:
    assert delivery.requires_rollback_only(
        _payload("invoice.send.inspect", {"record_ids": [11]})
    )
    assert not delivery.requires_write(
        _payload("invoice.send.inspect", {"record_ids": [11]})
    )
    assert delivery.requires_write(
        _payload("invoice.send", {"record_ids": [11]}, "invoice-send-key-0001")
    )
    assert not delivery.requires_rollback_only(
        _payload("invoice.send", {"record_ids": [11]}, "invoice-send-key-0001")
    )


def test_invoice_inspect_reports_native_computed_delivery_settings() -> None:
    env = Env()

    page = delivery.dispatch(
        env,
        _payload("invoice.send.inspect", {"record_ids": [11]}),
        7,
        failure_type=Failure,
    )

    assert page["idempotent_replay"] is False
    assert page["result"] == {
        "records": [
            {
                "record_id": 11,
                "partner_id": 21,
                "recipient_emails": ["billing@example.com"],
                "template_id": 61,
                "report_id": 62,
                "sending_methods": ["email"],
                "warnings": [],
                "sendable": True,
            }
        ]
    }
    create = next(
        call for call in env.calls if call[:2] == ("create", "account.move.send.wizard")
    )
    assert create[2]["sending_methods"] == ["email"]
    assert create[2]["extra_edis"] == []


def test_payment_inspect_uses_fixed_template_report_and_trimmed_email() -> None:
    env = Env()

    page = delivery.dispatch(
        env,
        _payload("payment.receipt.send.inspect", {"record_ids": [31]}),
        7,
        failure_type=Failure,
    )

    assert page["result"]["records"] == [
        {
            "record_id": 31,
            "partner_id": 21,
            "recipient_emails": ["billing@example.com"],
            "template_id": 63,
            "report_id": 64,
            "sending_methods": ["email"],
            "warnings": [],
            "sendable": True,
        }
    ]
    create = next(
        call for call in env.calls if call[:2] == ("create", "mail.compose.message")
    )
    assert create[2]["composition_mode"] == "comment"
    assert create[2]["force_send"] is False


@pytest.mark.parametrize(
    "state", ["draft", "in_process", "paid", "canceled", "rejected"]
)
def test_payment_receipt_inspection_preserves_native_payment_state_scope(
    state: str,
) -> None:
    env = Env()
    env.find("account.payment", 31).state = state

    page = delivery.dispatch(
        env,
        _payload("payment.receipt.send.inspect", {"record_ids": [31]}),
        7,
        failure_type=Failure,
    )

    assert page["result"]["records"][0]["sendable"] is True


@pytest.mark.parametrize(
    ("capability_id", "parameters", "expected_date"),
    [
        (
            "report.customer_statement.send",
            {
                "record_ids": [21],
                "date_from": "2026-01-01",
                "date_to": "2026-08-31",
            },
            {
                "date_from": "2026-01-01",
                "date_to": "2026-08-31",
                "mode": "range",
                "filter": "custom",
            },
        ),
        (
            "report.followup.send",
            {"record_ids": [21], "as_of": "2026-08-31"},
            {
                "date_from": False,
                "date_to": "2026-08-31",
                "mode": "single",
                "filter": "custom",
            },
        ),
    ],
)
def test_report_send_uses_fixed_native_report_date_and_queue_only_context(
    capability_id: str,
    parameters: dict[str, Any],
    expected_date: dict[str, Any],
) -> None:
    env = Env()

    page = delivery.dispatch(
        env,
        _payload(capability_id, parameters, "report-send-key-0001"),
        7,
        failure_type=Failure,
    )

    assert page["result"] == {"record_ids": [21], "processed_count": 1}
    assert env.report_previous_options == [{"partner_ids": [21], "date": expected_date}]
    action = next(
        call
        for call in env.calls
        if call[:2] == ("action_send_and_print", "account.report.send")
    )
    assert action[3] == {"force_synchronous": True}
    context = next(
        call
        for call in reversed(env.calls)
        if call[:3] == ("record_context", "account.report.send", action[2])
    )
    assert context[3]["mail_notify_force_send"] is False


@pytest.mark.parametrize(
    "parameters",
    [
        {"record_ids": [21], "date_from": "2026-9-1", "date_to": "2026-09-30"},
        {"record_ids": [21], "date_from": "2026-10-01", "date_to": "2026-09-30"},
        {"record_ids": [21], "as_of": "not-a-date"},
    ],
)
def test_report_dates_fail_closed_at_the_bridge_protocol(
    parameters: dict[str, Any],
) -> None:
    env = Env()
    capability_id = (
        "report.followup.send"
        if "as_of" in parameters
        else "report.customer_statement.send"
    )

    with pytest.raises(Failure) as caught:
        delivery.dispatch(
            env,
            _payload(capability_id, parameters, "report-send-key-0001"),
            7,
            failure_type=Failure,
        )

    assert caught.value.code == "bridge_protocol_error"


def test_invoice_send_persists_hidden_marker_and_replays_without_resending() -> None:
    env = Env()
    payload = _payload("invoice.send", {"record_ids": [11]}, "invoice-send-key-0001")

    first = delivery.dispatch(env, payload, 7, failure_type=Failure)
    replay = delivery.dispatch(env, payload, 7, failure_type=Failure)

    assert first["idempotent_replay"] is False
    assert replay["idempotent_replay"] is True
    assert (
        first["result"]
        == replay["result"]
        == {
            "record_ids": [11],
            "processed_count": 1,
        }
    )
    actions = [
        call
        for call in env.calls
        if call[:2] == ("action_send_and_print", "account.move.send.wizard")
    ]
    assert len(actions) == 1
    messages = env["mail.message"].records
    assert len(messages) == 1
    assert "ODACV4DELIVERYKEY-" in messages[0].body
    assert 'style="display:none"' in messages[0].body
    context = next(
        call
        for call in reversed(env.calls)
        if call[:3] == ("record_context", "account.move.send.wizard", actions[0][2])
    )
    assert context[3]["mail_notify_force_send"] is False


def test_payment_receipt_send_queues_comment_mode_mail_and_replays() -> None:
    env = Env()
    payload = _payload(
        "payment.receipt.send",
        {"record_ids": [31]},
        "payment-receipt-key-0001",
    )

    first = delivery.dispatch(env, payload, 7, failure_type=Failure)
    replay = delivery.dispatch(env, payload, 7, failure_type=Failure)

    assert first["idempotent_replay"] is False
    assert replay["idempotent_replay"] is True
    assert first["result"] == {"record_ids": [31], "processed_count": 1}
    actions = [
        call
        for call in env.calls
        if call[:2] == ("action_send_mail", "mail.compose.message")
    ]
    assert len(actions) == 1
    assert actions[0][3] is False
    message = env["mail.message"].records[0]
    assert (message.model, message.res_id) == ("account.payment", 31)
    assert "ODACV4DELIVERYOP-" in message.body


def test_inspect_exposes_missing_email_but_send_fails_before_native_action() -> None:
    env = Env()
    env.find("res.partner", 21).email = False

    inspected = delivery.dispatch(
        env,
        _payload("invoice.send.inspect", {"record_ids": [11]}),
        7,
        failure_type=Failure,
    )
    descriptor = inspected["result"]["records"][0]
    assert descriptor["recipient_emails"] == []
    assert descriptor["sendable"] is False
    assert descriptor["warnings"] == ["No recipient email address is available."]

    with pytest.raises(Failure) as caught:
        delivery.dispatch(
            env,
            _payload("invoice.send", {"record_ids": [11]}, "invoice-send-key-0001"),
            7,
            failure_type=Failure,
        )
    assert caught.value.code == "business_rule_error"
    assert not any(
        call[:2] == ("action_send_and_print", "account.move.send.wizard")
        for call in env.calls
    )


def test_same_send_key_with_other_parameters_is_rejected() -> None:
    env = Env()
    first = _payload("invoice.send", {"record_ids": [11]}, "invoice-send-key-0001")
    delivery.dispatch(env, first, 7, failure_type=Failure)
    conflicting = _payload(
        "invoice.send", {"record_ids": [11, 12]}, "invoice-send-key-0001"
    )
    company = env.find("res.company", 7)
    partner = env.find("res.partner", 21)
    env.add(
        "account.move",
        12,
        company_id=company,
        move_type="out_invoice",
        state="posted",
        partner_id=partner,
        no_followup=False,
    )

    with pytest.raises(Failure) as caught:
        delivery.dispatch(env, conflicting, 7, failure_type=Failure)

    assert caught.value.code == "idempotency_conflict"


def test_followup_update_writes_explicit_target_and_rereads() -> None:
    env = Env()
    capability_id = "invoice.followup.update"
    record_id = 11
    model_name = "account.move"
    payload = _payload(
        capability_id,
        {"record_id": record_id, "no_followup": True},
        "followup-update-key-0001",
    )

    first = delivery.dispatch(env, payload, 7, failure_type=Failure)
    replay = delivery.dispatch(env, payload, 7, failure_type=Failure)

    assert first["result"] == {"record_id": record_id, "no_followup": True}
    assert first["idempotent_replay"] is False
    assert replay["idempotent_replay"] is True
    writes = [
        call for call in env.calls if call[:3] == ("write", model_name, record_id)
    ]
    assert writes == [("write", model_name, record_id, {"no_followup": True})]
    invalidations = [
        call
        for call in env.calls
        if call[:3] == ("invalidate_recordset", model_name, record_id)
    ]
    assert invalidations == [
        ("invalidate_recordset", model_name, record_id, ["no_followup"]),
        ("invalidate_recordset", model_name, record_id, ["no_followup"]),
        ("invalidate_recordset", model_name, record_id, ["no_followup"]),
        ("invalidate_recordset", model_name, record_id, ["no_followup"]),
    ]


@pytest.mark.parametrize("move_type", ["out_receipt", "in_receipt"])
def test_invoice_followup_update_rejects_receipts(move_type: str) -> None:
    env = Env()
    env.find("account.move", 11).move_type = move_type

    with pytest.raises(Failure) as caught:
        delivery.dispatch(
            env,
            _payload(
                "invoice.followup.update",
                {"record_id": 11, "no_followup": True},
                "followup-update-key-0001",
            ),
            7,
            failure_type=Failure,
        )

    assert caught.value.code == "business_rule_error"
    assert not any(call[:3] == ("write", "account.move", 11) for call in env.calls)


def test_gate_returns_closed_page_without_creating_native_wizard() -> None:
    env = Env()
    env.denied.add(("account.move.send.wizard", "create"))

    page = delivery.dispatch(
        env,
        _payload("invoice.send.inspect", {"record_ids": [11]}),
        7,
        failure_type=Failure,
    )

    assert page == {
        "user_id": 5,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": False,
        "idempotent_replay": False,
        "result": None,
    }
    assert not any(
        call[:2] == ("create", "account.move.send.wizard") for call in env.calls
    )


def test_invoice_inspection_gate_requires_partner_read_access() -> None:
    env = Env()
    env.denied.add(("res.partner", "read"))

    page = delivery.dispatch(
        env,
        _payload("invoice.send.inspect", {"record_ids": [11]}),
        7,
        failure_type=Failure,
    )

    assert page["access_allowed"] is False
    assert page["result"] is None
    assert not any(
        call[:2] == ("create", "account.move.send.wizard") for call in env.calls
    )
