from __future__ import annotations

import hashlib
import io
import json
from copy import deepcopy

import pytest

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4.bridge.core_writes import OdooCoreWritePort
from odoo_accounting_cli_v4.capabilities.core_writes import (
    CORE_WRITE_CAPABILITY_IDS,
    CoreWriteError,
    _expected_idempotency_key,
    validate_core_write_request,
)
from odoo_accounting_cli_v4.registry import InstanceValidationError, load_registry

CAPABILITIES = {
    "product.create",
    "product.update",
    "product.duplicate",
    "product.archive",
    "product.restore",
    "product.cost.update",
    "product.accounting_profile.update",
    "product.category.accounting_profile.update",
}
PARAMETERS = {
    "product.create": {
        "name": "Consulting service",
        "default_code": "CONSULT-01",
        "product_type": "service",
        "category_id": 11,
        "uom_id": 1,
    },
    "product.update": {
        "product_id": 21,
        "changes": {
            "name": "Consulting service 2027",
            "barcode": None,
            "list_price": "1250.5",
        },
    },
    "product.duplicate": {
        "product_id": 21,
        "name": "Consulting service copy",
        "default_code": "CONSULT-02",
    },
    "product.archive": {"product_id": 21},
    "product.restore": {"product_id": 21},
    "product.cost.update": {"product_id": 21, "standard_price": "700.25"},
    "product.accounting_profile.update": {
        "product_id": 21,
        "changes": {
            "income_account_id": 31,
            "expense_account_id": None,
            "sale_tax_ids": [41, 42],
            "purchase_tax_ids": [],
        },
    },
    "product.category.accounting_profile.update": {
        "category_id": 11,
        "changes": {"income_account_id": 31, "expense_account_id": None},
    },
}
EXPECTED_MODELS = {
    capability_id: (
        "product.category"
        if capability_id == "product.category.accounting_profile.update"
        else "product.product"
    )
    for capability_id in CAPABILITIES
}
UNIT_REFERENCES = [
    "tests/unit/test_product_accounting_write_public.py",
    "tests/unit/test_product_accounting_writes_runtime.py",
]
INTEGRATION_REFERENCE = "tests/integration/test_product_accounting_write_batch_live.py"


def _request(capability_id: str, parameters: dict | None = None) -> dict:
    return {
        "schema_version": "v1",
        "request_id": "32f91531-a230-4dde-a8bf-e56bb03bdaba",
        "context": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": deepcopy(
            PARAMETERS[capability_id] if parameters is None else parameters
        ),
    }


def _digest(value: object) -> str:
    canonical = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(canonical).hexdigest()[:32]


def _key(capability_id: str) -> str:
    parameters = validate_core_write_request(capability_id, _request(capability_id))[2]
    if capability_id in {"product.create", "product.duplicate"}:
        return f"{capability_id}:7:{_digest(parameters)}"
    if capability_id in {"product.archive", "product.restore"}:
        return f"{capability_id}:{parameters['product_id']}"
    target_id = parameters.get("product_id", parameters.get("category_id"))
    target = (
        {"standard_price": parameters["standard_price"]}
        if capability_id == "product.cost.update"
        else parameters["changes"]
    )
    if capability_id == "product.category.accounting_profile.update":
        return f"{capability_id}:7:{target_id}:{_digest(target)}"
    return f"{capability_id}:{target_id}:{_digest(target)}"


class SuccessPort:
    user_id = 42

    def __init__(self, capability_id: str) -> None:
        self.capability_id = capability_id
        self.calls: list[dict] = []

    def execute(self, **kwargs: object) -> dict:
        self.calls.append(deepcopy(kwargs))
        parameters = kwargs["parameters"]
        assert isinstance(parameters, dict)
        category = self.capability_id == ("product.category.accounting_profile.update")
        record_id = (
            parameters["category_id"]
            if category
            else 902
            if self.capability_id in {"product.create", "product.duplicate"}
            else parameters["product_id"]
        )
        return {
            "user_id": self.user_id,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "idempotent_replay": False,
            "result": {
                "model": EXPECTED_MODELS[self.capability_id],
                "id": record_id,
                "name": "Consulting service",
                "state": (
                    "archived" if self.capability_id == "product.archive" else "active"
                ),
                "company_id": 7,
                "move_type": None,
                "source_id": None if category else 901,
                "line_ids": [],
                "partial_reconcile_ids": [],
                "full_reconcile_id": None,
                "reconciled": False,
            },
        }


def test_product_create_defaults_and_all_exact_contracts_are_frozen() -> None:
    for capability_id in CAPABILITIES:
        assert capability_id in CORE_WRITE_CAPABILITY_IDS
        _, context, normalized = validate_core_write_request(
            capability_id, _request(capability_id)
        )
        assert context["company_id"] == 7
        if capability_id == "product.create":
            assert normalized == {
                **PARAMETERS[capability_id],
                "barcode": None,
                "sale_ok": True,
                "purchase_ok": True,
                "list_price": "0",
            }
        else:
            assert normalized == PARAMETERS[capability_id]


@pytest.mark.parametrize(
    ("capability_id", "parameters"),
    [
        ("product.create", {"name": "Missing required fields"}),
        (
            "product.create",
            {**PARAMETERS["product.create"], "product_type": "stockable"},
        ),
        ("product.update", {"product_id": 21, "changes": {}}),
        ("product.update", {"product_id": 21, "changes": {"standard_price": "1"}}),
        ("product.duplicate", {"product_id": 21, "name": "Copy"}),
        ("product.archive", {"product_id": 0}),
        ("product.cost.update", {"product_id": 21, "standard_price": "01.0"}),
        (
            "product.accounting_profile.update",
            {"product_id": 21, "changes": {"sale_tax_ids": [41, 41]}},
        ),
        (
            "product.category.accounting_profile.update",
            {"category_id": 11, "changes": {"sale_tax_ids": [41]}},
        ),
    ],
)
def test_product_contracts_reject_expansion_or_noncanonical_values(
    capability_id: str, parameters: dict
) -> None:
    with pytest.raises(CoreWriteError) as caught:
        validate_core_write_request(capability_id, _request(capability_id, parameters))
    assert caught.value.code == "invalid_request"


def test_product_tax_ids_are_normalized_to_ascending_order() -> None:
    parameters = deepcopy(PARAMETERS["product.accounting_profile.update"])
    parameters["changes"]["sale_tax_ids"] = [42, 41]
    normalized = validate_core_write_request(
        "product.accounting_profile.update",
        _request("product.accounting_profile.update", parameters),
    )[2]
    assert normalized["changes"]["sale_tax_ids"] == [41, 42]


def test_category_accounting_profile_key_is_company_scoped() -> None:
    capability_id = "product.category.accounting_profile.update"
    parameters = validate_core_write_request(capability_id, _request(capability_id))[2]

    assert _expected_idempotency_key(capability_id, parameters, 7) != (
        _expected_idempotency_key(capability_id, parameters, 8)
    )


def test_registry_descriptors_and_schemas_cover_the_fixed_batch() -> None:
    registry = load_registry()
    assert len(registry.ids()) == 390
    assert (
        sum(
            registry.describe(capability_id)["handler_key"] is not None
            for capability_id in registry.ids()
        )
        == 375
    )
    assert (
        sum(
            registry.describe(capability_id)["access"] == "write"
            and registry.describe(capability_id)["handler_key"] is not None
            for capability_id in registry.ids()
        )
        == 160
    )
    assert (
        sum(
            registry.describe(capability_id)["status"]["value"] == "unconfigured"
            for capability_id in registry.ids()
        )
        == 330
    )
    assert (
        sum(
            registry.describe(capability_id)["status"]["value"] == "degraded"
            for capability_id in registry.ids()
        )
        == 45
    )

    for capability_id in CAPABILITIES:
        descriptor = registry.describe(capability_id)
        assert descriptor["access"] == "write"
        assert descriptor["handler_key"] == "core_write"
        expected_groups = ["product.group_product_manager"]
        if capability_id in {"product.archive", "product.restore"}:
            expected_groups.append("stock.group_stock_manager")
            assert "stock.warehouse.orderpoint:write" in descriptor["requirements"][
                "acl"
            ]
        assert descriptor["requirements"]["groups"] == expected_groups
        assert descriptor["requirements"]["company"] == "required"
        assert descriptor["tests"]["unit"]["references"] == UNIT_REFERENCES
        assert descriptor["tests"]["integration"]["references"] == [
            INTEGRATION_REFERENCE
        ]
        assert "stock" in " ".join(descriptor["routing"]["not_for"]["en_US"]).lower()
        registry.validate_instance(
            descriptor["schemas"]["request"], _request(capability_id)
        )


def test_request_schemas_reject_empty_changes_and_numeric_decimals() -> None:
    registry = load_registry()
    invalid = {
        "product.update": {"product_id": 21, "changes": {}},
        "product.cost.update": {"product_id": 21, "standard_price": 1.5},
        "product.accounting_profile.update": {"product_id": 21, "changes": {}},
        "product.category.accounting_profile.update": {
            "category_id": 11,
            "changes": {},
        },
    }
    for capability_id, parameters in invalid.items():
        descriptor = registry.describe(capability_id)
        with pytest.raises(InstanceValidationError):
            registry.validate_instance(
                descriptor["schemas"]["request"],
                _request(capability_id, parameters),
            )


@pytest.mark.parametrize("capability_id", sorted(CAPABILITIES))
def test_cli_routes_every_product_write_through_core_write(
    capability_id: str,
) -> None:
    stdout = io.StringIO()
    stderr = io.StringIO()
    ports: list[SuccessPort] = []

    def port_factory(selected: str, _request_document: dict) -> SuccessPort:
        port = SuccessPort(selected)
        ports.append(port)
        return port

    exit_code = cli.main(
        [
            "write",
            "run",
            capability_id,
            "--request",
            "-",
            "--idempotency-key",
            _key(capability_id),
            "--confirm",
            capability_id,
        ],
        stdin=io.StringIO(json.dumps(_request(capability_id))),
        stdout=stdout,
        stderr=stderr,
        port_factory=port_factory,
    )

    document = json.loads(stdout.getvalue())
    assert exit_code == 0
    assert stderr.getvalue() == ""
    assert document["capability"] == capability_id
    assert document["success"] is True
    assert document["odoo"]["model"] == EXPECTED_MODELS[capability_id]
    assert ports[0].calls[0]["capability_id"] == capability_id
    assert ports[0].calls[0]["confirmation"] == capability_id


@pytest.mark.parametrize("capability_id", sorted(CAPABILITIES))
def test_configured_factory_routes_product_writes_to_core_port(
    capability_id: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = object()
    client = object()

    class RuntimeConfig:
        def resolve(self, database: str, company_id: int, user_login: str) -> object:
            assert (database, company_id, user_login) == (
                "odoo_cli_v4_dev",
                7,
                "v4-agent",
            )
            return target

    monkeypatch.setattr(cli, "load_runtime_config", lambda _path: RuntimeConfig())
    monkeypatch.setattr(cli, "OdooBridgeClient", lambda *_args, **_kwargs: client)
    port = cli._configured_port_factory(capability_id, _request(capability_id))
    assert type(port) is OdooCoreWritePort
    assert port._client is client
