"""Pure documentation checks; no bridge, Odoo, approvals, or business writes."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _module(relative, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def docs():
    return _module("scripts/build_command_manual.py", "manual_builder")


@pytest.fixture(scope="module")
def keys():
    return _module("docs/reference/cli-v4-manual/request_key.py", "manual_keys")


def request(parameters):
    return {"schema_version": "v1", "request_id": "11111111-1111-4111-8111-111111111111",
            "context": {"database": "v4-dev", "company_id": 1, "user_login": "example.operator",
                        "language": "zh_CN", "timezone": "Asia/Shanghai"}, "parameters": parameters}


def test_response_reference_expansion_retains_nested_fields(docs):
    schemas = docs.Schemas()
    path = "schemas/v1/invoice.get.response.schema.json"
    rows = schemas.rows(schemas.files[path], path, "response")
    assert any(row[0] == "response.data.lines[].taxes[].amount" for row in rows)
    assert any(row[0] == "response.odoo.user_id" for row in rows)
    assert any(row[0] == "response.audit.operation_id" for row in rows)


def test_conditional_rules_are_not_omitted_or_called_unconditional(docs):
    schemas = docs.Schemas()
    path = "schemas/v1/invoice.post.request.schema.json"
    parameters = schemas.files[path]["properties"]["parameters"]
    rows = schemas.rows(parameters, path, "parameters")
    assert '"oneOf"' in rows[0][-1] and '"move_ids"' in rows[0][-1]
    assert any(row[3] == "oneOf[1]" and row[2] == "分支约束" for row in rows)
    assert next(row for row in rows if row[0] == "parameters.move_id")[2].startswith("可选")


def test_table_escapes_pipe_in_regular_expression(docs):
    output = docs.field_table([("p", "string", "必填", "", "", "^(a|b)$")])
    assert "^(a&#124;b)$" in output


def test_offline_key_matches_real_normalized_lifecycle_request(keys):
    assert keys.derive_key("invoice.post", request({"move_id": 9})) == "invoice.post:9"


def test_offline_key_uses_sorted_normalized_batch_not_user_order(keys):
    assert keys.derive_key("invoice.post", request({"move_ids": [3, 9]})) == keys.derive_key(
        "invoice.post", request({"move_ids": [9, 3]}))


def test_offline_helper_never_allows_disabled_or_read_id(keys):
    for cap in ("account.account.list", "period.lock.change"):
        with pytest.raises(ValueError):
            keys.derive_key(cap, request({}))


def test_delivery_request_does_not_invent_operation_key(keys):
    with pytest.raises(ValueError):
        keys.derive_key("invoice.send", request({"move_id": 9}))
    assert keys.derive_key("invoice.send", request({"move_id": 9}), "document-test-001") == "document-test-001"


def test_generated_sample_is_valid_for_exclusive_single_id_branch(docs):
    from odoo_accounting_cli_v4.registry import load_registry
    schemas = docs.Schemas()
    path = "schemas/v1/invoice.post.request.schema.json"
    sample = schemas.sample(schemas.files[path]["properties"]["parameters"], path)
    assert sample == {"move_id": 1}
    load_registry().validate_instance(path, request(sample))


def test_reference_fragment_unescapes_json_pointer(docs):
    schemas = docs.Schemas()
    schemas.files["schemas/v1/unit.json"] = {"$defs": {"a/b~c": {"type": "integer", "minimum": 2}}}
    resolved, path = schemas.resolve({"$ref": "#/$defs/a~1b~0c"}, "schemas/v1/unit.json")
    assert resolved == {"type": "integer", "minimum": 2}
    assert path == "schemas/v1/unit.json"


def test_legacy_envelope_parameter_contract_is_not_lost(docs):
    schemas = docs.Schemas()
    path = "schemas/v1/asset.create.request.schema.json"
    nodes = schemas.property_nodes(schemas.files[path], path, "parameters")
    rows = [row for node, document in nodes for row in schemas.rows(node, document, "parameters")]
    assert any(row[0] == "parameters.original_value" for row in rows)
    assert any(row[0] == "parameters.account_asset_id" for row in rows)


def test_dependent_and_conditional_example_obeys_schema(docs):
    from odoo_accounting_cli_v4.registry import load_registry
    schemas = docs.Schemas()
    path = "schemas/v1/bank.transaction.update.request.schema.json"
    parameters = schemas.sample(schemas.files[path]["properties"]["parameters"], path)
    assert {"foreign_currency_id", "amount_currency"} <= parameters["changes"].keys()
    load_registry().validate_instance(path, request(parameters))


def test_multiline_code_is_not_formatted_as_prose(docs):
    rendered = docs.markdown_html("# Heading\n\n```json\n{\"a\": \"<tag>\"}\n```", "test")
    assert 'id="test-heading-0"' in rendered
    assert '&lt;tag&gt;' in rendered and '<tag>' not in rendered


def test_fixed_prefix_response_arrays_expand_without_banning_prefix_items(docs):
    schemas = docs.Schemas()
    path = "schemas/v1/diagnostic.accounting_environment.inspect.response.schema.json"
    rows = schemas.rows(schemas.files[path], path, "response")
    assert any(row[0] == "response.data.modules[0].state" for row in rows)
    assert any(row[0] == "response.data.models[8].available" for row in rows)
    extra = next(row for row in rows if row[0] == "response.data.modules[]")
    assert extra[2] == "固定前缀以外的剩余元素"


def test_key_file_loader_rejects_duplicate_keys_without_printing_inputs(keys, tmp_path, capsys):
    path = tmp_path / "request.json"
    path.write_text('{"schema_version":"v1","schema_version":"private-do-not-print"}', encoding="utf-8")
    assert keys.main(["invoice.post", str(path)]) == 2
    output = capsys.readouterr()
    assert output.out == "" and "ValueError" in output.err and "private-do-not-print" not in output.err
