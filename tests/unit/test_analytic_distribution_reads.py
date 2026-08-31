from __future__ import annotations

from copy import deepcopy

import pytest
import test_core_object_reads as object_fixtures
import test_invoices as invoice_fixtures
import test_journal_entries as entry_fixtures
import test_journal_entry_validation as check_fixtures

from odoo_accounting_cli_v4.capabilities.core_object_reads import CoreObjectReadError
from odoo_accounting_cli_v4.capabilities.invoices import InvoiceError
from odoo_accounting_cli_v4.capabilities.journal_entries import JournalEntryError
from odoo_accounting_cli_v4.contracts import success_document
from odoo_accounting_cli_v4.registry import InstanceValidationError, load_registry

CAPABILITIES = (
    "invoice.get",
    "journal_entry.get",
    "journal_item.search",
    "journal_item.get",
)
NATIVE_MAPPING = {
    "3,1": "60.123456",
    "1,3": "40.123456",
    "1,1": "0",
    "1,2": "-5.25",
    "custom key": "150",
    " ": "2",
}


@pytest.fixture(scope="module")
def registry():
    return load_registry()


def _case(capability_id):
    if capability_id == "invoice.get":
        data = invoice_fixtures._invoice()

        def read():
            return invoice_fixtures.get_invoice(
                invoice_fixtures.FakePort(invoice=data), invoice_fixtures._get_request()
            )

        return data, data["lines"][0], read
    if capability_id == "journal_entry.get":
        data = entry_fixtures._entry()

        def read():
            return entry_fixtures.get_journal_entry(
                entry_fixtures.FakePort(entry=data), entry_fixtures._get_request()
            )

        return data, data["lines"][0], read
    item = object_fixtures._item(capability_id)
    data = (
        {"items": [item], "has_more": False, "next_cursor": None}
        if capability_id == "journal_item.search"
        else item
    )

    def read():
        return object_fixtures.read_core_object(
            capability_id,
            object_fixtures.FakePort([item]),
            object_fixtures._request(
                {}
                if capability_id == "journal_item.search"
                else {"line_id": item["id"]}
            ),
        )

    return data, item, read


def _validate_schema(registry, capability_id, data):
    registry.validate_instance(
        f"schemas/v1/{capability_id}.response.schema.json",
        success_document(
            capability_id,
            data,
            request_id=invoice_fixtures.REQUEST_ID,
            database="odoo_cli_v4_dev",
            company_id=7,
            user_id=42,
            model="account.move.line"
            if capability_id.startswith("journal_item.")
            else "account.move",
            record_ids=[31] if capability_id.startswith("journal_item.") else [30],
        ),
    )


@pytest.mark.parametrize("capability_id", CAPABILITIES)
@pytest.mark.parametrize(
    "distribution",
    [
        pytest.param({}, id="empty"),
        pytest.param({"1": "100"}, id="single"),
        pytest.param(NATIVE_MAPPING, id="native-keys-and-signed-values"),
        pytest.param({str(index): "1" for index in range(1, 21)}, id="over-16-items"),
        pytest.param({"x" * 300: "9" * 300}, id="no-256-character-limit"),
        pytest.param({"1": "-0." + "0" * 300 + "1"}, id="finite-high-precision"),
    ],
)
def test_public_reads_preserve_native_analytic_mapping(
    capability_id, distribution, registry
):
    data, line, read = _case(capability_id)
    line["analytic_distribution"] = deepcopy(distribution)
    original = deepcopy(data)

    assert read() == original
    _validate_schema(registry, capability_id, data)
    assert data == original


@pytest.mark.parametrize("capability_id", CAPABILITIES)
@pytest.mark.parametrize(
    "distribution",
    [
        None,
        False,
        [],
        "100",
        {"": "100"},
        *(
            {"1": value}
            for value in (
                None,
                True,
                1,
                1.5,
                [],
                {},
                "",
                "NaN",
                "Infinity",
                "-Infinity",
                "1e2",
                "1E-2",
                "+1",
                "01",
                "-01",
                ".1",
                "1.",
                "-0",
                "0.0",
                "1.00",
                "-0.10",
                " 1",
                "1 ",
                "1\n",
                "1\r\n",
            )
        ),
    ],
)
def test_public_and_schema_reject_noncanonical_analytic_mapping(
    capability_id, distribution, registry
):
    data, line, read = _case(capability_id)
    line["analytic_distribution"] = distribution
    with pytest.raises(InstanceValidationError):
        _validate_schema(registry, capability_id, data)
    with pytest.raises(
        (InvoiceError, JournalEntryError, CoreObjectReadError)
    ) as caught:
        read()
    assert caught.value.code == "failed_validation" and caught.value.exit_code == 8


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_analytic_mapping_is_a_required_response_field(capability_id, registry):
    data, line, read = _case(capability_id)
    line.pop("analytic_distribution")
    with pytest.raises(InstanceValidationError):
        _validate_schema(registry, capability_id, data)
    with pytest.raises(
        (InvoiceError, JournalEntryError, CoreObjectReadError)
    ) as caught:
        read()
    assert caught.value.code == "failed_validation" and caught.value.exit_code == 8


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_public_analytic_mapping_rejects_non_string_keys(capability_id):
    _, line, read = _case(capability_id)
    line["analytic_distribution"] = {1: "100"}
    with pytest.raises(
        (InvoiceError, JournalEntryError, CoreObjectReadError)
    ) as caught:
        read()
    assert caught.value.code == "failed_validation" and caught.value.exit_code == 8


@pytest.mark.parametrize(
    "move_type", ("out_invoice", "in_invoice", "out_refund", "in_refund")
)
def test_all_invoice_document_types_read_back_analytic_mapping(move_type, registry):
    data, line, read = _case("invoice.get")
    data["move_type"] = move_type
    line["analytic_distribution"] = deepcopy(NATIVE_MAPPING)
    assert read() == data
    _validate_schema(registry, "invoice.get", data)


def test_journal_entry_check_keeps_existing_checks_with_analytic_mapping():
    entry = check_fixtures._entry()
    entry["lines"][0]["analytic_distribution"] = deepcopy(NATIVE_MAPPING)
    result = check_fixtures.check_journal_entry(
        check_fixtures.FakePort(entry=entry), check_fixtures._request()
    )
    assert result == check_fixtures._expected(
        entry, ready=True, draft=True, balanced=True, lines=True
    )


def test_journal_entry_check_rejects_malformed_analytic_mapping():
    entry = check_fixtures._entry()
    entry["lines"][0]["analytic_distribution"] = {"1": "1.0"}
    with pytest.raises(JournalEntryError) as caught:
        check_fixtures.check_journal_entry(
            check_fixtures.FakePort(entry=entry), check_fixtures._request()
        )
    assert caught.value.code == "failed_validation" and caught.value.exit_code == 8
