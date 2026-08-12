"""Fail-closed JSON client for the local Odoo subprocess bridge."""

from __future__ import annotations

import json
import subprocess
from typing import Any, Protocol


_MAX_RESPONSE_CHARS = 4 * 1024 * 1024


class BridgeTarget(Protocol):
    alias: str
    database: str
    company_id: int
    user_login: str
    bridge_argv: tuple[str, ...]
    timeout_seconds: int


class BridgeError(RuntimeError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        exit_code: int = 7,
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code
        self.retryable = retryable
        self.details = details or {}


class OdooBridgeClient:
    def __init__(self, target: BridgeTarget, *, language: str, timezone: str) -> None:
        if not language or not timezone:
            raise ValueError("language and timezone are required")
        self._target = target
        self._language = language
        self._timezone = timezone

    def invoke(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        request = json.dumps(
            {
                "schema_version": "v1",
                "target": {
                    "alias": self._target.alias,
                    "database": self._target.database,
                    "company_id": self._target.company_id,
                    "user_login": self._target.user_login,
                    "language": self._language,
                    "timezone": self._timezone,
                },
                "action": action,
                "payload": payload,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ) + "\n"
        try:
            completed = subprocess.run(
                list(self._target.bridge_argv),
                input=request,
                capture_output=True,
                text=True,
                timeout=self._target.timeout_seconds,
                shell=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise BridgeError(
                "bridge_timeout",
                "The Odoo bridge timed out.",
                retryable=True,
            ) from exc
        except OSError as exc:
            raise BridgeError(
                "bridge_process_error", "The Odoo bridge could not be started."
            ) from exc

        document = self._parse_document(completed.stdout)
        if completed.returncode != 0 and document is None:
            raise BridgeError(
                "bridge_process_error", "The Odoo bridge process failed."
            )
        if document is None:
            raise BridgeError(
                "bridge_protocol_error", "The Odoo bridge response is invalid."
            )
        if (
            set(document) != {"schema_version", "success", "data", "error"}
            or document["schema_version"] != "v1"
            or not isinstance(document["success"], bool)
        ):
            raise BridgeError(
                "bridge_protocol_error", "The Odoo bridge response is invalid."
            )
        if document["success"]:
            if (
                completed.returncode != 0
                or not isinstance(document["data"], dict)
                or document["error"] is not None
            ):
                raise BridgeError(
                    "bridge_protocol_error", "The Odoo bridge response is invalid."
                )
            return document["data"]

        error = document["error"]
        if document["data"] is not None or not isinstance(error, dict):
            raise BridgeError(
                "bridge_protocol_error", "The Odoo bridge response is invalid."
            )
        if set(error) != {
            "code",
            "message",
            "details",
            "retryable",
            "exit_code",
        }:
            raise BridgeError(
                "bridge_protocol_error", "The Odoo bridge response is invalid."
            )
        code = error.get("code")
        message = error.get("message")
        details = error.get("details", {})
        retryable = error.get("retryable", False)
        exit_code = error.get("exit_code", 7)
        if (
            not isinstance(code, str)
            or not code
            or not isinstance(message, str)
            or not message
            or not isinstance(details, dict)
            or not isinstance(retryable, bool)
            or not isinstance(exit_code, int)
            or isinstance(exit_code, bool)
            or exit_code not in range(2, 9)
            or completed.returncode != exit_code
        ):
            raise BridgeError(
                "bridge_protocol_error", "The Odoo bridge response is invalid."
            )
        raise BridgeError(
            code,
            message,
            exit_code=exit_code,
            retryable=retryable,
            details=details,
        )

    @staticmethod
    def _parse_document(stdout: str) -> dict[str, Any] | None:
        if not stdout or len(stdout) > _MAX_RESPONSE_CHARS:
            return None
        def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
            result: dict[str, Any] = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError("duplicate JSON key")
                result[key] = value
            return result
        try:
            value = json.loads(stdout, object_pairs_hook=reject_duplicates)
        except (json.JSONDecodeError, ValueError):
            return None
        return value if isinstance(value, dict) else None
