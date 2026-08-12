"""Versioned, data-only capability registry."""

from __future__ import annotations

import copy
import hashlib
import json
import re
import sysconfig
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError
from referencing import Registry as ReferencingRegistry
from referencing import Resource


_CAPABILITY_ID = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+$")
_STATUS_VALUES = {
    "available",
    "uninstalled",
    "unconfigured",
    "unauthorized",
    "disabled",
    "degraded",
    "failed_validation",
}
_DESCRIPTOR_KEYS = {
    "summary",
    "domain",
    "access",
    "source",
    "schemas",
    "requirements",
    "strategies",
    "tests",
    "status",
    "routing",
    "handler_key",
}
_MAX_JSON_BYTES = 4 * 1024 * 1024


class RegistryError(RuntimeError):
    """The shipped registry is absent or internally inconsistent."""


class CapabilityNotFound(KeyError):
    """The caller requested an ID that is not registered."""


class InstanceValidationError(RuntimeError):
    """A request, response, or registry instance violates its public schema."""


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise RegistryError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _read_json(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise RegistryError(f"cannot read registry resource: {path.name}") from exc
    if len(raw) > _MAX_JSON_BYTES:
        raise RegistryError(f"registry resource is too large: {path.name}")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RegistryError(f"invalid JSON resource: {path.name}") from exc
    if not isinstance(value, dict):
        raise RegistryError(f"JSON resource must be an object: {path.name}")
    return value


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _load_schema_resources(root: Path) -> ReferencingRegistry:
    registry = ReferencingRegistry()
    schema_root = root / "schemas" / "v1"
    for path in sorted(schema_root.glob("*.json")):
        schema = _read_json(path)
        try:
            Draft202012Validator.check_schema(schema)
            resource = Resource.from_contents(schema)
        except (SchemaError, ValueError) as exc:
            raise RegistryError(f"invalid JSON Schema: {path.name}") from exc
        schema_id = schema.get("$id")
        if not isinstance(schema_id, str) or not schema_id:
            raise RegistryError(f"JSON Schema has no absolute ID: {path.name}")
        registry = registry.with_resource(schema_id, resource)
    return registry


def _resource_root() -> Path:
    repository_root = Path(__file__).resolve().parents[2]
    if (repository_root / "capabilities" / "v1" / "registry.json").is_file():
        return repository_root
    installed_root = (
        Path(sysconfig.get_path("data")) / "share" / "odoo-accounting-cli-v4"
    )
    if (installed_root / "capabilities" / "v1" / "registry.json").is_file():
        return installed_root
    raise RegistryError("capability registry is not installed")


def _validate_string_list(value: Any, label: str) -> None:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item for item in value
    ) or len(value) != len(set(value)):
        raise RegistryError(f"{label} must be a list of non-empty strings")


def _validate_descriptor(capability_id: str, descriptor: Any) -> None:
    if not isinstance(descriptor, dict) or set(descriptor) != _DESCRIPTOR_KEYS:
        raise RegistryError(f"invalid descriptor fields for {capability_id}")
    if descriptor["access"] not in {"read", "write"}:
        raise RegistryError(f"invalid access class for {capability_id}")
    if not isinstance(descriptor["domain"], str) or not descriptor["domain"]:
        raise RegistryError(f"invalid domain for {capability_id}")
    if not isinstance(descriptor["handler_key"], str) or not re.fullmatch(
        r"[a-z][a-z0-9_]+", descriptor["handler_key"]
    ):
        raise RegistryError(f"invalid handler key for {capability_id}")
    summary = descriptor["summary"]
    if not isinstance(summary, dict) or set(summary) != {"zh_CN", "en_US"}:
        raise RegistryError(f"invalid summary for {capability_id}")
    if any(not isinstance(item, str) or not item for item in summary.values()):
        raise RegistryError(f"invalid summary value for {capability_id}")

    source = descriptor["source"]
    if not isinstance(source, dict) or set(source) != {
        "modules",
        "models",
        "wizards",
        "report_handlers",
        "locations",
    }:
        raise RegistryError(f"invalid source metadata for {capability_id}")
    for key, value in source.items():
        _validate_string_list(value, f"{capability_id}.source.{key}")
    for location in source["locations"]:
        relative = PurePosixPath(location)
        if relative.is_absolute() or ".." in relative.parts:
            raise RegistryError(f"invalid source location for {capability_id}")

    schemas = descriptor["schemas"]
    if not isinstance(schemas, dict) or set(schemas) != {"request", "response"}:
        raise RegistryError(f"invalid schema metadata for {capability_id}")
    for value in schemas.values():
        if not isinstance(value, str) or not value.startswith("schemas/v1/"):
            raise RegistryError(f"invalid schema reference for {capability_id}")

    requirements = descriptor["requirements"]
    if not isinstance(requirements, dict) or set(requirements) != {
        "modules",
        "configuration",
        "company",
        "groups",
        "acl",
    }:
        raise RegistryError(f"invalid requirements for {capability_id}")
    for key in ("modules", "configuration", "groups", "acl"):
        _validate_string_list(requirements[key], f"{capability_id}.requirements.{key}")
    if requirements["company"] not in {"required", "optional", "not_applicable"}:
        raise RegistryError(f"invalid company requirement for {capability_id}")

    strategies = descriptor["strategies"]
    if not isinstance(strategies, dict) or set(strategies) != {
        "preview",
        "execute",
        "verify",
        "idempotency",
        "reverse",
    }:
        raise RegistryError(f"invalid strategies for {capability_id}")
    if any(not isinstance(item, str) or not item for item in strategies.values()):
        raise RegistryError(f"invalid strategy value for {capability_id}")

    tests = descriptor["tests"]
    if not isinstance(tests, dict) or set(tests) != {
        "unit",
        "integration",
        "golden",
        "e2e",
    }:
        raise RegistryError(f"invalid test metadata for {capability_id}")
    for kind, definition in tests.items():
        if not isinstance(definition, dict) or set(definition) != {
            "status",
            "references",
            "reason",
        }:
            raise RegistryError(f"invalid {kind} test definition for {capability_id}")
        _validate_string_list(
            definition["references"], f"{capability_id}.tests.{kind}.references"
        )
        if not isinstance(definition["status"], str) or not isinstance(
            definition["reason"], str
        ):
            raise RegistryError(f"invalid {kind} test status for {capability_id}")
        if definition["status"] not in {
            "implemented",
            "planned",
            "not_applicable",
            "failed",
        }:
            raise RegistryError(f"unknown {kind} test status for {capability_id}")
        if definition["status"] == "implemented" and not definition["references"]:
            raise RegistryError(f"implemented {kind} tests need references")
        if not definition["reason"]:
            raise RegistryError(f"{kind} test reason is required for {capability_id}")

    status = descriptor["status"]
    if not isinstance(status, dict) or set(status) != {
        "value",
        "reason_code",
        "reason",
    }:
        raise RegistryError(f"invalid status for {capability_id}")
    if status["value"] not in _STATUS_VALUES:
        raise RegistryError(f"unknown status for {capability_id}")
    if any(
        not isinstance(status[key], str) or not status[key]
        for key in ("reason_code", "reason")
    ):
        raise RegistryError(f"status reason is required for {capability_id}")

    routing = descriptor["routing"]
    if not isinstance(routing, dict) or set(routing) != {
        "object",
        "actions",
        "aliases",
        "not_for",
        "required_slots",
    }:
        raise RegistryError(f"invalid routing metadata for {capability_id}")
    _validate_string_list(routing["actions"], f"{capability_id}.routing.actions")
    _validate_string_list(
        routing["required_slots"], f"{capability_id}.routing.required_slots"
    )
    for key in ("aliases", "not_for"):
        if not isinstance(routing[key], dict) or set(routing[key]) != {
            "zh_CN",
            "en_US",
        }:
            raise RegistryError(f"invalid {key} routing metadata for {capability_id}")
        for language, values in routing[key].items():
            _validate_string_list(
                values, f"{capability_id}.routing.{key}.{language}"
            )
    if not isinstance(routing["object"], str) or not routing["object"]:
        raise RegistryError(f"invalid routing object for {capability_id}")


@dataclass(frozen=True)
class CapabilityRegistry:
    _root: Path
    _document: dict[str, Any]
    _schema_resources: ReferencingRegistry
    digest: str

    def ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._document["capabilities"]))

    def describe(self, capability_id: str) -> dict[str, Any]:
        try:
            descriptor = self._document["capabilities"][capability_id]
        except KeyError as exc:
            raise CapabilityNotFound(capability_id) from exc
        return copy.deepcopy(descriptor)

    def load_schema(self, reference: str) -> dict[str, Any]:
        relative = PurePosixPath(reference)
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or len(relative.parts) != 3
            or relative.parts[:2] != ("schemas", "v1")
        ):
            raise RegistryError("schema reference is outside schemas/v1")
        path = self._root.joinpath(*relative.parts)
        schema = _read_json(path)
        if (
            schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema"
            or not isinstance(schema.get("$id"), str)
            or not schema["$id"].endswith(relative.name)
            or schema.get("type") != "object"
        ):
            raise RegistryError(f"invalid JSON Schema metadata: {relative.name}")
        return schema

    def validate_instance(self, reference: str, instance: Any) -> None:
        schema = self.load_schema(reference)
        validator = Draft202012Validator(
            schema,
            registry=self._schema_resources,
            format_checker=FormatChecker(),
        )
        error = next(iter(validator.iter_errors(instance)), None)
        if error is not None:
            raise InstanceValidationError("instance failed its v1 JSON Schema")


def load_registry() -> CapabilityRegistry:
    root = _resource_root()
    document = _read_json(root / "capabilities" / "v1" / "registry.json")
    schema_resources = _load_schema_resources(root)
    if set(document) != {
        "registry_schema_version",
        "contract_schema_version",
        "capabilities",
    }:
        raise RegistryError("invalid registry document fields")
    if document["registry_schema_version"] != "v1":
        raise RegistryError("unsupported registry schema version")
    if document["contract_schema_version"] != "v1":
        raise RegistryError("unsupported contract schema version")
    capabilities = document["capabilities"]
    if not isinstance(capabilities, dict) or not capabilities:
        raise RegistryError("registry must contain capabilities")
    registry = CapabilityRegistry(
        root,
        document,
        schema_resources,
        hashlib.sha256(_canonical_json(document)).hexdigest(),
    )
    try:
        registry.validate_instance(
            "schemas/v1/capability-registry.schema.json", document
        )
    except InstanceValidationError as exc:
        raise RegistryError("capability registry violates its public schema") from exc
    for capability_id, descriptor in capabilities.items():
        if not _CAPABILITY_ID.fullmatch(capability_id):
            raise RegistryError(f"invalid capability ID: {capability_id}")
        _validate_descriptor(capability_id, descriptor)
    for descriptor in capabilities.values():
        registry.load_schema(descriptor["schemas"]["request"])
        registry.load_schema(descriptor["schemas"]["response"])
    return registry
