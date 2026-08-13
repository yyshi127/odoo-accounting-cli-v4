"""Deterministic v1 stdout documents."""

from __future__ import annotations

import json
from typing import Any


SCHEMA_VERSION = "v1"


def _odoo_metadata(
    *,
    database: str | None = None,
    company_id: int | None = None,
    user_id: int | None = None,
    model: str | None = None,
    record_ids: list[int] | None = None,
) -> dict[str, Any]:
    return {
        "database": database,
        "company_id": company_id,
        "user_id": user_id,
        "model": model,
        "record_ids": record_ids or [],
    }


def _audit_metadata() -> dict[str, Any]:
    return {
        "operation_id": None,
        "idempotency_key": None,
        "verification": None,
    }


def success_document(
    capability: str,
    data: dict[str, Any],
    *,
    request_id: str | None = None,
    status: str = "verified",
    warnings: list[dict[str, Any]] | None = None,
    database: str | None = None,
    company_id: int | None = None,
    user_id: int | None = None,
    model: str | None = None,
    record_ids: list[int] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "request_id": request_id,
        "success": True,
        "capability": capability,
        "status": status,
        "data": data,
        "warnings": warnings or [],
        "error": None,
        "odoo": _odoo_metadata(
            database=database,
            company_id=company_id,
            user_id=user_id,
            model=model,
            record_ids=record_ids,
        ),
        "audit": _audit_metadata(),
    }


def error_document(
    capability: str,
    code: str,
    message: str,
    *,
    request_id: str | None = None,
    status: str = "failed",
    details: dict[str, Any] | None = None,
    retryable: bool = False,
    database: str | None = None,
    company_id: int | None = None,
    user_id: int | None = None,
    model: str | None = None,
    record_ids: list[int] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "request_id": request_id,
        "success": False,
        "capability": capability,
        "status": status,
        "data": None,
        "warnings": [],
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
            "retryable": retryable,
        },
        "odoo": _odoo_metadata(
            database=database,
            company_id=company_id,
            user_id=user_id,
            model=model,
            record_ids=record_ids,
        ),
        "audit": _audit_metadata(),
    }


def dumps(document: dict[str, Any]) -> str:
    return json.dumps(
        document,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
