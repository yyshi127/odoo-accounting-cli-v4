"""Odoo-side runtime for accounting delivery and follow-up updates.

Delivery is deliberately queue-only: every native mail operation runs with
``mail_notify_force_send=False`` (and payment composers also have
``force_send=False``). A hidden marker in the generated message body supports
serial replay detection for a fixed idempotency key; it is not a concurrent
exactly-once guarantee.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from typing import Any

ACTION = "accounting.delivery.execute"
CAPABILITY_IDS = frozenset(
    {
        "invoice.send.inspect",
        "invoice.send",
        "payment.receipt.send.inspect",
        "payment.receipt.send",
        "report.customer_statement.send",
        "report.followup.send",
        "invoice.followup.update",
    }
)
INSPECT_CAPABILITY_IDS = frozenset(
    {"invoice.send.inspect", "payment.receipt.send.inspect"}
)
SEND_CAPABILITY_IDS = frozenset(
    {
        "invoice.send",
        "payment.receipt.send",
        "report.customer_statement.send",
        "report.followup.send",
    }
)
FOLLOWUP_CAPABILITY_IDS = frozenset({"invoice.followup.update"})

_PAYLOAD_FIELDS = {
    "capability_id",
    "company_id",
    "parameters",
    "idempotency_key",
}
_IDEMPOTENCY_KEY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")
_INVOICE_TYPES = frozenset({"out_invoice", "out_refund", "out_receipt"})
_FOLLOWUP_MOVE_TYPES = frozenset(
    {"out_invoice", "out_refund", "in_invoice", "in_refund"}
)

_MODELS = {
    "invoice.send.inspect": (
        "res.company",
        "account.move",
        "res.partner",
        "account.move.send.wizard",
        "mail.message",
        "mail.template",
        "ir.actions.report",
    ),
    "invoice.send": (
        "res.company",
        "account.move",
        "res.partner",
        "account.move.send.wizard",
        "mail.message",
        "mail.template",
        "ir.actions.report",
    ),
    "payment.receipt.send.inspect": (
        "res.company",
        "account.payment",
        "res.partner",
        "mail.compose.message",
        "mail.message",
        "mail.template",
        "ir.actions.report",
    ),
    "payment.receipt.send": (
        "res.company",
        "account.payment",
        "res.partner",
        "mail.compose.message",
        "mail.message",
        "mail.template",
        "ir.actions.report",
    ),
    "report.customer_statement.send": (
        "res.company",
        "res.partner",
        "account.report",
        "account.report.send",
        "mail.message",
        "mail.template",
    ),
    "report.followup.send": (
        "res.company",
        "res.partner",
        "account.report",
        "account.report.send",
        "mail.message",
        "mail.template",
    ),
    "invoice.followup.update": (
        "res.company",
        "account.move",
        "account.move.line",
    ),
}
_FIELDS = {
    "invoice.send.inspect": {
        "account.move": {"company_id", "move_type", "state", "partner_id"},
        "account.move.send.wizard": {
            "move_id",
            "alerts",
            "sending_methods",
            "extra_edis",
            "template_id",
            "pdf_report_id",
            "mail_partner_ids",
            "body",
        },
        "mail.message": {"model", "res_id", "body"},
    },
    "payment.receipt.send.inspect": {
        "account.payment": {"company_id", "partner_id"},
        "mail.compose.message": {
            "composition_mode",
            "model",
            "res_ids",
            "template_id",
            "partner_ids",
            "attachment_ids",
            "body",
            "force_send",
        },
        "mail.message": {"model", "res_id", "body"},
    },
    "report.customer_statement.send": {
        "res.partner": {"company_id", "email"},
        "account.report.send": {
            "account_report_id",
            "report_options",
            "mail_template_id",
            "mail_partner_ids",
            "mail_body",
            "warnings",
            "checkbox_send_mail",
            "checkbox_download",
        },
        "mail.message": {"model", "res_id", "body"},
    },
    "invoice.followup.update": {
        "account.move": {"company_id", "move_type", "state", "no_followup"},
        "account.move.line": {"no_followup"},
    },
}
_FIELDS["invoice.send"] = _FIELDS["invoice.send.inspect"]
_FIELDS["payment.receipt.send"] = _FIELDS["payment.receipt.send.inspect"]
_FIELDS["report.followup.send"] = _FIELDS["report.customer_statement.send"]

_ACCESS = {
    "invoice.send.inspect": {
        "res.company": ("read",),
        "account.move": ("read",),
        "res.partner": ("read",),
        "account.move.send.wizard": ("read", "create", "write"),
        "mail.message": ("read",),
        "mail.template": ("read",),
        "ir.actions.report": ("read",),
    },
    "invoice.send": {
        "res.company": ("read",),
        "account.move": ("read", "write"),
        "res.partner": ("read",),
        "account.move.send.wizard": ("read", "create", "write"),
        "mail.message": ("read",),
        "mail.template": ("read",),
        "ir.actions.report": ("read",),
    },
    "payment.receipt.send.inspect": {
        "res.company": ("read",),
        "account.payment": ("read",),
        "res.partner": ("read",),
        "mail.compose.message": ("read", "create", "write"),
        "mail.message": ("read",),
        "mail.template": ("read",),
        "ir.actions.report": ("read",),
    },
    "payment.receipt.send": {
        "res.company": ("read",),
        "account.payment": ("read", "write"),
        "res.partner": ("read",),
        "mail.compose.message": ("read", "create", "write"),
        "mail.message": ("read",),
        "mail.template": ("read",),
        "ir.actions.report": ("read",),
    },
    "report.customer_statement.send": {
        "res.company": ("read",),
        "res.partner": ("read", "write"),
        "account.report": ("read",),
        "account.report.send": ("read", "create", "write"),
        "mail.message": ("read",),
        "mail.template": ("read",),
    },
    "invoice.followup.update": {
        "res.company": ("read",),
        "account.move": ("read", "write"),
        "account.move.line": ("read", "write"),
    },
}
_ACCESS["report.followup.send"] = _ACCESS["report.customer_statement.send"]

_REPORT_SPECS = {
    "report.customer_statement.send": (
        "account_reports.customer_statement_report",
        "account_reports.email_template_customer_statement",
    ),
    "report.followup.send": (
        "account_reports.followup_report",
        "account_reports.email_template_customer_follow_up_report",
    ),
}


def requires_write(payload: Any) -> bool:
    """Return whether the request must commit its business operation."""

    return bool(
        isinstance(payload, dict)
        and payload.get("capability_id") in CAPABILITY_IDS - INSPECT_CAPABILITY_IDS
    )


def requires_rollback_only(payload: Any) -> bool:
    """Inspect creates native transient wizards and therefore needs rollback."""

    return bool(
        isinstance(payload, dict)
        and payload.get("capability_id") in INSPECT_CAPABILITY_IDS
    )


def _fail(
    failure_type: type[Exception], code: str, message: str, exit_code: int
) -> Exception:
    return failure_type(code, message, exit_code=exit_code)


def _protocol(failure_type: type[Exception]) -> Exception:
    return _fail(
        failure_type,
        "bridge_protocol_error",
        "The bridge action payload is invalid.",
        7,
    )


def _runtime(failure_type: type[Exception]) -> Exception:
    return _fail(
        failure_type,
        "odoo_runtime_error",
        "The Odoo accounting-delivery runtime failed.",
        7,
    )


def _is_id(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _valid_ids(value: Any) -> bool:
    return bool(
        isinstance(value, list)
        and value
        and len(value) <= 100
        and all(_is_id(item) for item in value)
        and value == sorted(set(value))
    )


def _canonical_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def _valid_parameters(capability_id: str, parameters: Any) -> bool:
    if not isinstance(parameters, dict):
        return False
    if capability_id in FOLLOWUP_CAPABILITY_IDS:
        return bool(
            set(parameters) == {"record_id", "no_followup"}
            and _is_id(parameters["record_id"])
            and isinstance(parameters["no_followup"], bool)
        )
    if capability_id == "report.customer_statement.send":
        return bool(
            set(parameters) == {"record_ids", "date_from", "date_to"}
            and _valid_ids(parameters["record_ids"])
            and _canonical_date(parameters["date_from"])
            and _canonical_date(parameters["date_to"])
            and parameters["date_from"] <= parameters["date_to"]
        )
    if capability_id == "report.followup.send":
        return bool(
            set(parameters) == {"record_ids", "as_of"}
            and _valid_ids(parameters["record_ids"])
            and _canonical_date(parameters["as_of"])
        )
    return set(parameters) == {"record_ids"} and _valid_ids(parameters["record_ids"])


def _validated_payload(
    payload: Any, company_id: int, failure_type: type[Exception]
) -> tuple[str, dict[str, Any], str | None]:
    if not isinstance(payload, dict) or set(payload) != _PAYLOAD_FIELDS:
        raise _protocol(failure_type)
    capability_id = payload["capability_id"]
    if (
        capability_id not in CAPABILITY_IDS
        or not _is_id(payload["company_id"])
        or not _valid_parameters(capability_id, payload["parameters"])
    ):
        raise _protocol(failure_type)
    if payload["company_id"] != company_id:
        raise _fail(
            failure_type,
            "company_unavailable",
            "The company is unavailable.",
            3,
        )
    key = payload["idempotency_key"]
    if capability_id in INSPECT_CAPABILITY_IDS:
        if key is not None:
            raise _protocol(failure_type)
    elif not isinstance(key, str) or not _IDEMPOTENCY_KEY_PATTERN.fullmatch(key):
        raise _protocol(failure_type)
    return capability_id, payload["parameters"], key


def _page(
    env: Any,
    *,
    company_visible: bool,
    module_installed: bool,
    access_allowed: bool,
    idempotent_replay: bool = False,
    result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "user_id": env.uid,
        "company_visible": company_visible,
        "module_installed": module_installed,
        "access_allowed": access_allowed,
        "idempotent_replay": idempotent_replay,
        "result": result,
    }


def _field_shape_available(env: Any, capability_id: str) -> bool:
    return all(
        fields <= set(getattr(env[model_name], "_fields", {}))
        for model_name, fields in _FIELDS[capability_id].items()
    )


def _gate(
    env: Any,
    capability_id: str,
    company_id: int,
    failure_type: type[Exception],
) -> tuple[bool, bool, bool]:
    installed = {
        model_name: env.registry.get(model_name) is not None
        for model_name in _MODELS[capability_id]
    }
    company_model = env["res.company"] if installed["res.company"] else None
    company_read = bool(company_model is not None and company_model.has_access("read"))
    company_visible = bool(
        company_read and company_model.search_count([("id", "=", company_id)], limit=1)
    )
    module_installed = all(installed.values())
    if (
        company_visible
        and module_installed
        and not _field_shape_available(env, capability_id)
    ):
        raise _runtime(failure_type)
    group_allowed = bool(
        module_installed and env.user.has_group("account.group_account_invoice")
    )
    access_allowed = bool(
        company_visible
        and module_installed
        and group_allowed
        and all(
            env[model_name].has_access(operation)
            for model_name, operations in _ACCESS[capability_id].items()
            for operation in operations
        )
    )
    return company_visible, module_installed, access_allowed


def _scoped(env: Any, model_name: str, company_id: int) -> Any:
    return env[model_name].with_context(
        allowed_company_ids=[company_id],
        mail_notify_force_send=False,
    )


def _record_id(record: Any) -> int:
    record_id = getattr(record, "id", None)
    if not _is_id(record_id):
        raise ValueError("invalid record id")
    return record_id


def _related_id(record: Any) -> int | None:
    if not record:
        return None
    return _record_id(record)


def _company_id(record: Any) -> int | None:
    company = getattr(record, "company_id", None)
    return _related_id(company)


def _partner_allowed(partner: Any, company_id: int) -> bool:
    return bool(
        partner
        and _is_id(getattr(partner, "id", None))
        and _company_id(partner) in (None, company_id)
    )


def _targets(
    env: Any,
    model_name: str,
    record_ids: list[int],
    company_id: int,
    failure_type: type[Exception],
    *,
    shared: bool = False,
) -> list[Any]:
    domain: list[Any] = [("id", "in", record_ids)]
    if shared:
        domain.extend(
            ["|", ("company_id", "=", False), ("company_id", "=", company_id)]
        )
    else:
        domain.append(("company_id", "=", company_id))
    records = list(
        _scoped(env, model_name, company_id).search(
            domain, order="id asc", limit=len(record_ids) + 1
        )
    )
    by_id = {_record_id(record): record for record in records}
    if set(by_id) != set(record_ids) or len(records) != len(record_ids):
        raise _fail(
            failure_type,
            "target_unavailable",
            "One or more company-scoped delivery targets are unavailable.",
            4,
        )
    return [by_id[record_id] for record_id in record_ids]


def _warning_texts(value: Any) -> list[str]:
    candidates: list[Any] = []
    if isinstance(value, dict):
        for warning in value.values():
            candidates.append(
                warning.get("message") if isinstance(warning, dict) else warning
            )
    elif isinstance(value, (list, tuple, set)):
        candidates.extend(value)
    elif value:
        candidates.append(value)
    return sorted(
        {text for candidate in candidates if (text := str(candidate).strip())}
    )


def _recipient_emails(partners: Any) -> list[str]:
    return sorted(
        {
            email.strip()
            for partner in partners
            if isinstance((email := getattr(partner, "email", None)), str)
            and email.strip()
        }
    )


def _sending_methods(value: Any) -> list[str]:
    if isinstance(value, dict):
        value = list(value)
    if not isinstance(value, (list, tuple, set, frozenset)):
        return []
    return sorted(
        {
            method.strip()
            for method in value
            if isinstance(method, str) and method.strip()
        }
    )


def _inspect_record(
    *,
    record_id: int,
    partner_id: int,
    recipient_emails: list[str],
    template_id: int | None,
    report_id: int | None,
    sending_methods: list[str],
    warnings: list[str],
    sendable: bool,
) -> dict[str, Any]:
    return {
        "record_id": record_id,
        "partner_id": partner_id,
        "recipient_emails": recipient_emails,
        "template_id": template_id,
        "report_id": report_id,
        "sending_methods": sending_methods,
        "warnings": warnings,
        "sendable": sendable,
    }


def _invoice_wizard(env: Any, move: Any, company_id: int) -> Any:
    return (
        _scoped(env, "account.move.send.wizard", company_id)
        .with_context(
            active_model="account.move",
            active_ids=[_record_id(move)],
            mail_notify_force_send=False,
        )
        .create(
            {
                "move_id": _record_id(move),
                "sending_methods": ["email"],
                "extra_edis": [],
            }
        )
    )


def _invoice_descriptor(move: Any, wizard: Any, company_id: int) -> dict[str, Any]:
    if (
        _company_id(move) != company_id
        or getattr(move, "move_type", None) not in _INVOICE_TYPES
        or getattr(move, "state", None) != "posted"
        or not _partner_allowed(move.partner_id, company_id)
    ):
        raise ValueError("invalid invoice delivery target")
    methods = _sending_methods(wizard.sending_methods)
    emails = _recipient_emails(wizard.mail_partner_ids)
    warnings = _warning_texts(wizard.alerts)
    template_id = _related_id(wizard.template_id)
    report_id = _related_id(wizard.pdf_report_id)
    danger = any(
        isinstance(alert, dict) and alert.get("level") == "danger"
        for alert in (wizard.alerts or {}).values()
    )
    if not emails:
        warnings = sorted({*warnings, "No recipient email address is available."})
    if template_id is None:
        warnings = sorted({*warnings, "No invoice email template is available."})
    if report_id is None:
        warnings = sorted({*warnings, "No invoice PDF report is available."})
    return _inspect_record(
        record_id=_record_id(move),
        partner_id=_record_id(move.partner_id),
        recipient_emails=emails,
        template_id=template_id,
        report_id=report_id,
        sending_methods=methods,
        warnings=warnings,
        sendable=bool(
            "email" in methods
            and emails
            and template_id is not None
            and report_id is not None
            and not danger
        ),
    )


def _payment_template(env: Any) -> Any:
    return env.ref(
        "account.mail_template_data_payment_receipt", raise_if_not_found=False
    )


def _payment_report(env: Any) -> Any:
    return env.ref("account.action_report_payment_receipt", raise_if_not_found=False)


def _payment_composer(env: Any, payment: Any, company_id: int, template: Any) -> Any:
    payment_id = _record_id(payment)
    return (
        _scoped(env, "mail.compose.message", company_id)
        .with_context(
            active_model="account.payment",
            active_ids=[payment_id],
            default_composition_mode="comment",
            default_template_id=_record_id(template),
            default_email_layout_xmlid="mail.mail_notification_light",
            mail_post_autofollow=True,
            mail_notify_force_send=False,
        )
        .create(
            {
                "composition_mode": "comment",
                "model": "account.payment",
                "res_ids": str([payment_id]),
                "template_id": _record_id(template),
                "force_send": False,
                "email_layout_xmlid": "mail.mail_notification_light",
            }
        )
    )


def _payment_descriptor(
    payment: Any,
    composer: Any,
    company_id: int,
    template: Any,
    report: Any,
) -> dict[str, Any]:
    if _company_id(payment) != company_id or not _partner_allowed(
        payment.partner_id, company_id
    ):
        raise ValueError("invalid payment-receipt target")
    emails = _recipient_emails(composer.partner_ids)
    warnings = [] if emails else ["No recipient email address is available."]
    template_id = _related_id(template)
    report_id = _related_id(report)
    if template_id is None:
        warnings.append("The payment-receipt email template is unavailable.")
    if report_id is None:
        warnings.append("The payment-receipt PDF report is unavailable.")
    return _inspect_record(
        record_id=_record_id(payment),
        partner_id=_record_id(payment.partner_id),
        recipient_emails=emails,
        template_id=template_id,
        report_id=report_id,
        sending_methods=["email"],
        warnings=sorted(set(warnings)),
        sendable=bool(emails and template_id is not None and report_id is not None),
    )


def _marker_pair(
    capability_id: str,
    company_id: int,
    key: str,
    parameters: dict[str, Any],
) -> tuple[str, str]:
    key_raw = f"{capability_id}\0{company_id}\0{key}".encode()
    canonical = json.dumps(
        parameters,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    operation_raw = f"{capability_id}\0{company_id}\0{key}\0{canonical}".encode()
    return (
        f"ODACV4DELIVERYKEY-{hashlib.sha256(key_raw).hexdigest()}",
        f"ODACV4DELIVERYOP-{hashlib.sha256(operation_raw).hexdigest()}",
    )


def _marked_body(body: Any, key_marker: str, operation_marker: str) -> str:
    current = body if isinstance(body, str) else ""
    marker = (
        '<span style="display:none" aria-hidden="true">'
        f"{key_marker} {operation_marker}</span>"
    )
    return f"{current}{marker}"


def _expected_message_targets(
    capability_id: str, record_ids: list[int]
) -> set[tuple[str, int]]:
    if capability_id.startswith("invoice."):
        model_name = "account.move"
    elif capability_id.startswith("payment."):
        model_name = "account.payment"
    else:
        model_name = "res.partner"
    return {(model_name, record_id) for record_id in record_ids}


def _marked_messages(env: Any, company_id: int, key_marker: str) -> list[Any]:
    messages = _scoped(env, "mail.message", company_id).search(
        [("body", "ilike", key_marker)], order="id asc", limit=201
    )
    return [
        message
        for message in messages
        if key_marker in str(getattr(message, "body", "") or "")
    ]


def _message_targets(messages: list[Any]) -> set[tuple[str, int]]:
    targets: set[tuple[str, int]] = set()
    for message in messages:
        model_name = getattr(message, "model", None)
        res_id = getattr(message, "res_id", None)
        if not isinstance(model_name, str) or not model_name or not _is_id(res_id):
            raise ValueError("invalid marked mail message")
        targets.add((model_name, res_id))
    return targets


def _send_replay(
    env: Any,
    capability_id: str,
    record_ids: list[int],
    company_id: int,
    key_marker: str,
    operation_marker: str,
    failure_type: type[Exception],
) -> bool:
    messages = _marked_messages(env, company_id, key_marker)
    if not messages:
        return False
    if any(
        operation_marker not in str(getattr(message, "body", "") or "")
        for message in messages
    ):
        raise _fail(
            failure_type,
            "idempotency_conflict",
            "The delivery idempotency key was already used with other parameters.",
            5,
        )
    if _message_targets(messages) != _expected_message_targets(
        capability_id, record_ids
    ):
        raise _fail(
            failure_type,
            "idempotency_conflict",
            "The delivery marker does not identify the requested records.",
            5,
        )
    return True


def _verify_sent_messages(
    env: Any,
    capability_id: str,
    record_ids: list[int],
    company_id: int,
    key_marker: str,
    operation_marker: str,
    failure_type: type[Exception],
) -> None:
    messages = _marked_messages(env, company_id, key_marker)
    expected = _expected_message_targets(capability_id, record_ids)
    matching = [
        message
        for message in messages
        if operation_marker in str(getattr(message, "body", "") or "")
    ]
    if _message_targets(matching) != expected:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not persist every accounting-delivery marker.",
            6,
        )


def _inspect_invoices(
    env: Any,
    record_ids: list[int],
    company_id: int,
    failure_type: type[Exception],
) -> dict[str, Any]:
    moves = _targets(env, "account.move", record_ids, company_id, failure_type)
    records = []
    for move in moves:
        wizard = _invoice_wizard(env, move, company_id)
        records.append(_invoice_descriptor(move, wizard, company_id))
    return {"records": records}


def _inspect_payments(
    env: Any,
    record_ids: list[int],
    company_id: int,
    failure_type: type[Exception],
) -> dict[str, Any]:
    payments = _targets(env, "account.payment", record_ids, company_id, failure_type)
    template = _payment_template(env)
    report = _payment_report(env)
    if not template or not report:
        raise _fail(
            failure_type,
            "configuration_missing",
            "The native payment-receipt template or PDF report is unavailable.",
            4,
        )
    records = []
    for payment in payments:
        composer = _payment_composer(env, payment, company_id, template)
        records.append(
            _payment_descriptor(payment, composer, company_id, template, report)
        )
    return {"records": records}


def _ensure_sendable(
    descriptors: list[dict[str, Any]], failure_type: type[Exception]
) -> None:
    if any(not descriptor["sendable"] for descriptor in descriptors):
        raise _fail(
            failure_type,
            "business_rule_error",
            "One or more accounting documents cannot be sent by email.",
            6,
        )


def _send_invoices(
    env: Any,
    record_ids: list[int],
    company_id: int,
    key_marker: str,
    operation_marker: str,
    failure_type: type[Exception],
) -> None:
    moves = _targets(env, "account.move", record_ids, company_id, failure_type)
    prepared = [
        (move, wizard, _invoice_descriptor(move, wizard, company_id))
        for move in moves
        for wizard in [_invoice_wizard(env, move, company_id)]
    ]
    _ensure_sendable(
        [descriptor for _move, _wizard, descriptor in prepared], failure_type
    )
    for _move, wizard, _descriptor in prepared:
        wizard.write({"body": _marked_body(wizard.body, key_marker, operation_marker)})
        wizard.with_context(mail_notify_force_send=False).action_send_and_print(
            allow_fallback_pdf=False
        )


def _send_payment_receipts(
    env: Any,
    record_ids: list[int],
    company_id: int,
    key_marker: str,
    operation_marker: str,
    failure_type: type[Exception],
) -> None:
    payments = _targets(env, "account.payment", record_ids, company_id, failure_type)
    template = _payment_template(env)
    report = _payment_report(env)
    if not template or not report:
        raise _fail(
            failure_type,
            "configuration_missing",
            "The native payment-receipt template or PDF report is unavailable.",
            4,
        )
    prepared = [
        (
            payment,
            composer,
            _payment_descriptor(payment, composer, company_id, template, report),
        )
        for payment in payments
        for composer in [_payment_composer(env, payment, company_id, template)]
    ]
    _ensure_sendable(
        [descriptor for _payment, _composer, descriptor in prepared], failure_type
    )
    for _payment, composer, _descriptor in prepared:
        composer.write(
            {
                "body": _marked_body(composer.body, key_marker, operation_marker),
                "force_send": False,
            }
        )
        composer.with_context(mail_notify_force_send=False).action_send_mail()


def _report_wizard(
    env: Any,
    capability_id: str,
    partner: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> Any:
    report_xmlid, template_xmlid = _REPORT_SPECS[capability_id]
    report = env.ref(report_xmlid, raise_if_not_found=False)
    template = env.ref(template_xmlid, raise_if_not_found=False)
    if not report or not template:
        raise _fail(
            failure_type,
            "configuration_missing",
            "The native account report or email template is unavailable.",
            4,
        )
    partner_id = _record_id(partner)
    if capability_id == "report.customer_statement.send":
        expected_date = {
            "date_from": parameters["date_from"],
            "date_to": parameters["date_to"],
            "mode": "range",
            "filter": "custom",
        }
    else:
        expected_date = {
            "date_from": False,
            "date_to": parameters["as_of"],
            "mode": "single",
            "filter": "custom",
        }
    options = report.with_context(allowed_company_ids=[company_id]).get_options(
        {"partner_ids": [partner_id], "date": expected_date}
    )
    actual_date = options.get("date") if isinstance(options, dict) else None
    verified_date = (
        expected_date
        if capability_id == "report.customer_statement.send"
        else {key: expected_date[key] for key in ("date_to", "mode", "filter")}
    )
    if (
        not isinstance(options, dict)
        or options.get("partner_ids") != [partner_id]
        or not _is_id(options.get("report_id"))
        or not isinstance(actual_date, dict)
        or any(actual_date.get(key) != value for key, value in verified_date.items())
    ):
        raise _runtime(failure_type)
    return (
        _scoped(env, "account.report.send", company_id)
        .with_context(
            default_mail_template_id=_record_id(template),
            default_report_options=options,
            mail_notify_force_send=False,
        )
        .create(
            {
                "account_report_id": _record_id(report),
                "report_options": options,
                "mail_template_id": _record_id(template),
                "checkbox_send_mail": True,
                "checkbox_download": False,
            }
        )
    )


def _send_reports(
    env: Any,
    capability_id: str,
    record_ids: list[int],
    parameters: dict[str, Any],
    company_id: int,
    key_marker: str,
    operation_marker: str,
    failure_type: type[Exception],
) -> None:
    partners = _targets(
        env,
        "res.partner",
        record_ids,
        company_id,
        failure_type,
        shared=True,
    )
    prepared: list[Any] = []
    for partner in partners:
        if not _partner_allowed(partner, company_id):
            raise ValueError("invalid report recipient")
        wizard = _report_wizard(
            env, capability_id, partner, parameters, company_id, failure_type
        )
        emails = _recipient_emails(wizard.mail_partner_ids)
        warnings = _warning_texts(wizard.warnings)
        if not emails or warnings:
            raise _fail(
                failure_type,
                "business_rule_error",
                "One or more report recipients cannot receive email.",
                6,
            )
        prepared.append(wizard)
    for wizard in prepared:
        wizard.write(
            {"mail_body": _marked_body(wizard.mail_body, key_marker, operation_marker)}
        )
        wizard.with_context(mail_notify_force_send=False).action_send_and_print(
            force_synchronous=True
        )


def _send(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    key: str,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    record_ids = parameters["record_ids"]
    key_marker, operation_marker = _marker_pair(
        capability_id, company_id, key, parameters
    )
    if _send_replay(
        env,
        capability_id,
        record_ids,
        company_id,
        key_marker,
        operation_marker,
        failure_type,
    ):
        return {"record_ids": record_ids, "processed_count": len(record_ids)}, True
    if capability_id == "invoice.send":
        _send_invoices(
            env,
            record_ids,
            company_id,
            key_marker,
            operation_marker,
            failure_type,
        )
    elif capability_id == "payment.receipt.send":
        _send_payment_receipts(
            env,
            record_ids,
            company_id,
            key_marker,
            operation_marker,
            failure_type,
        )
    else:
        _send_reports(
            env,
            capability_id,
            record_ids,
            parameters,
            company_id,
            key_marker,
            operation_marker,
            failure_type,
        )
    _verify_sent_messages(
        env,
        capability_id,
        record_ids,
        company_id,
        key_marker,
        operation_marker,
        failure_type,
    )
    return {"record_ids": record_ids, "processed_count": len(record_ids)}, False


def _followup_update(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    record_id = parameters["record_id"]
    desired = parameters["no_followup"]
    model_name = "account.move"
    records = _targets(env, model_name, [record_id], company_id, failure_type)
    record = records[0]
    if record.move_type not in _FOLLOWUP_MOVE_TYPES or record.state != "posted":
        raise ValueError("invalid invoice follow-up target")
    record.invalidate_recordset(["no_followup"])
    replay = record.no_followup is desired
    if not replay:
        record.write({"no_followup": desired})
    reread = _targets(env, model_name, [record_id], company_id, failure_type)[0]
    reread.invalidate_recordset(["no_followup"])
    if reread.no_followup is not desired:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not persist the follow-up target state.",
            6,
        )
    return {"record_id": record_id, "no_followup": reread.no_followup}, replay


def _dispatch_allowed(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    key: str | None,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    if capability_id == "invoice.send.inspect":
        return (
            _inspect_invoices(env, parameters["record_ids"], company_id, failure_type),
            False,
        )
    if capability_id == "payment.receipt.send.inspect":
        return (
            _inspect_payments(env, parameters["record_ids"], company_id, failure_type),
            False,
        )
    if capability_id in SEND_CAPABILITY_IDS:
        if key is None:
            raise _protocol(failure_type)
        return _send(env, capability_id, parameters, company_id, key, failure_type)
    return _followup_update(env, capability_id, parameters, company_id, failure_type)


def dispatch(
    env: Any,
    payload: dict[str, Any],
    company_id: int,
    *,
    failure_type: type[Exception],
) -> dict[str, Any]:
    """Validate, gate, and execute one fixed accounting-delivery capability."""

    capability_id, parameters, key = _validated_payload(
        payload, company_id, failure_type
    )
    company_visible, module_installed, access_allowed = _gate(
        env, capability_id, company_id, failure_type
    )
    if not access_allowed:
        return _page(
            env,
            company_visible=company_visible,
            module_installed=module_installed,
            access_allowed=False,
        )
    try:
        result, replay = _dispatch_allowed(
            env,
            capability_id,
            parameters,
            company_id,
            key,
            failure_type,
        )
    except failure_type:
        raise
    except Exception as exc:
        class_name = type(exc).__name__
        if class_name == "AccessError":
            code, message, exit_code = (
                "unauthorized",
                "The configured user cannot execute this accounting delivery.",
                3,
            )
        elif class_name in {"UserError", "ValidationError"}:
            code, message, exit_code = (
                "business_rule_error",
                "Odoo rejected the accounting delivery by a business rule.",
                6,
            )
        elif isinstance(exc, ValueError):
            code, message, exit_code = (
                "business_rule_error",
                "The accounting-delivery target is not eligible.",
                6,
            )
        else:
            code, message, exit_code = (
                "odoo_write_error",
                "The Odoo accounting-delivery operation failed.",
                6,
            )
        raise _fail(failure_type, code, message, exit_code) from exc
    return _page(
        env,
        company_visible=True,
        module_installed=True,
        access_allowed=True,
        idempotent_replay=replay,
        result=result,
    )
