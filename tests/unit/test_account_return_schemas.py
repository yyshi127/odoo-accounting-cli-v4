from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "schemas" / "v1"
CAPABILITIES = (
    "account.return.search",
    "account.return.get",
    "account.return.summary",
    "account.return.type.list",
    "account.return.check.list",
    "account.return.check.get",
)


def test_twelve_account_return_schemas_are_valid_and_closed() -> None:
    for capability_id in CAPABILITIES:
        for direction in ("request", "response"):
            path = SCHEMA_DIR / f"{capability_id}.{direction}.schema.json"
            schema = json.loads(path.read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)
            assert schema["additionalProperties"] is False
            assert schema["title"] == f"{capability_id} {direction}"
            if direction == "response":
                assert schema["properties"]["capability"]["const"] == capability_id
