"""Documentation example: validate and derive a write key offline; never execute."""

import json
import sys
from functools import cache
from pathlib import Path

from odoo_accounting_cli_v4.capabilities import accounting_delivery, core_writes
from odoo_accounting_cli_v4.registry import load_registry


@cache
def _registry():
    return load_registry()


def derive_key(capability, request, operation_key=None):
    registry = _registry()
    descriptor = registry.describe(capability)
    if descriptor["access"] != "write" or descriptor["status"]["value"] == "disabled":
        raise ValueError("Select an implemented write capability, not a read/disabled ID.")
    registry.validate_instance(descriptor["schemas"]["request"], request)
    if descriptor["handler_key"] == "core_write":
        _, context, normalized = core_writes.validate_core_write_request(capability, request)
        expected = core_writes._expected_idempotency_key(capability, normalized, context["company_id"])
        key = expected if expected is not None else operation_key
        if key is None:
            raise ValueError("This request needs an explicit caller-owned operation key as the third argument.")
        core_writes._validate_idempotency_and_confirmation(capability, normalized, context["company_id"], key, capability)
    elif descriptor["handler_key"] == "accounting_delivery":
        accounting_delivery.validate_accounting_delivery_request(capability, request)
        key = operation_key
        if not isinstance(key, str) or accounting_delivery._IDEMPOTENCY_PATTERN.fullmatch(key) is None:
            raise ValueError("Delivery writes need an explicit 8-128 safe-character operation key as the third argument.")
    else:
        raise ValueError("This capability has no supported write handler.")
    return key


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    try:
        if len(args) not in (2, 3):
            raise ValueError("Usage: request_key.py CAPABILITY request.json [OPERATION_KEY]")
        def unique_pairs(pairs):
            result = dict(pairs)
            if len(result) != len(pairs):
                raise ValueError("Duplicate JSON key")
            return result
        request = json.loads(Path(args[1]).read_text(encoding="utf-8"), object_pairs_hook=unique_pairs)
        print(derive_key(args[0], request, args[2] if len(args) == 3 else None))
        return 0
    except Exception as error:  # noqa: BLE001 - documentation helper, no Odoo/private exception text
        print(f"Key not generated: {type(error).__name__}. Check request/schema/operation key.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
