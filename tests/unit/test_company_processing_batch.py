from __future__ import annotations

import io
import json

import pytest
from test_fiscal_mapping_writes import request

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4 import company_processing_contracts as contracts
from odoo_accounting_cli_v4.bridge import core_object_reads_runtime as reads
from odoo_accounting_cli_v4.bridge import core_writes_runtime as writes
from odoo_accounting_cli_v4.capabilities import core_object_reads, core_writes
from odoo_accounting_cli_v4.registry import load_registry

PARAMETERS = {
    'company.fiscal_year_end.update': {'changes': {'fiscalyear_last_day': 29, 'fiscalyear_last_month': '2'}},
    'company.tax_policy.update': {'changes': {'account_sale_tax_id': 31, 'account_purchase_tax_id': None, 'tax_calculation_rounding_method': 'round_per_line'}},
    'company.cash_discount_accounts.assign': {'changes': {'account_journal_early_pay_discount_gain_account_id': 31}},
    'company.exchange_configuration.update': {'changes': {'currency_exchange_journal_id': 31, 'expense_currency_exchange_account_id': None}},
    'company.invoice_display.update': {'changes': {'qr_code': True, 'display_invoice_tax_company_currency': False}},
    'company.credit_policy.update': {'changes': {'account_use_credit_limit': True}},
    'company.bill_processing_policy.update': {'changes': {'quick_edit_mode': None, 'autopost_bills': False}},
}


def result(capability_id, parameters):
    return {'model': 'res.company', 'id': 7, 'name': 'Test company', 'state': 'active', 'company_id': 7,
            'move_type': None, 'source_id': None, 'line_ids': [], 'partial_reconcile_ids': [],
            'full_reconcile_id': None, 'reconciled': False}


@pytest.fixture(scope='module')
def registry():
    return load_registry()


@pytest.mark.parametrize('capability_id', PARAMETERS)
def test_closed_company_write_cli_schema_key_and_binding(capability_id, registry, monkeypatch):
    params, expected = PARAMETERS[capability_id], result(capability_id, PARAMETERS[capability_id])
    req = request(params)
    key = contracts.idempotency_key(capability_id, params, 7)
    registry.validate_instance(f'schemas/v1/{capability_id}.request.schema.json', req)
    assert writes._valid_parameters(capability_id, params, 7)
    assert key == writes._deterministic_key(capability_id, params, 7) == core_writes._expected_idempotency_key(capability_id, params, 7)
    assert writes._GROUPS[capability_id] == 'base.group_erp_manager'

    class Port:
        user_id = 42

        def execute(self, **payload):
            assert payload['parameters'] == params and payload['company_id'] == 7
            assert payload['confirmation'] == capability_id and payload['idempotency_key'] == key
            return {'user_id': 42, 'company_visible': True, 'module_installed': True, 'access_allowed': True,
                    'idempotent_replay': False, 'result': expected}

    monkeypatch.setattr(cli, 'load_registry', lambda: registry)
    stdout, stderr = io.StringIO(), io.StringIO()
    assert cli.main(['write', 'run', capability_id, '--request', '-', '--confirm', capability_id, '--idempotency-key', key],
                    stdin=io.StringIO(json.dumps(req)), stdout=stdout, stderr=stderr, port_factory=lambda *args: Port()) == 0
    registry.validate_instance(f'schemas/v1/{capability_id}.response.schema.json', json.loads(stdout.getvalue()))
    assert not stderr.getvalue()
    for field, value in (('id', 99), ('company_id', 8), ('model', 'account.move'), ('source_id', 99), ('line_ids', [99]), ('state', 'deleted')):
        with pytest.raises(core_writes.CoreWriteError):
            core_writes._validate_result(capability_id, params, {**expected, field: value}, company_id=7, idempotent_replay=False)


def test_context_company_read_has_no_target_override(registry, monkeypatch):
    cap, req = contracts.GET_ID, request({})
    item = {'id': 7, 'company_id': 7}
    for field in contracts.SETTING_FIELDS:
        item[field] = False if field in contracts.BOOL_FIELDS else None if field in contracts.RELATION_MODELS or field == 'quick_edit_mode' else 31 if field == 'fiscalyear_last_day' else '12' if field == 'fiscalyear_last_month' else min(contracts.CHOICES[field])
    assert contracts.valid_read_item(item, 7) and reads._valid_parameters(cap, {})

    class Port:
        user_id = 42

        def read(self, **payload):
            assert payload['parameters'] == {} and payload['company_id'] == 7
            return {'user_id': 42, 'company_visible': True, 'module_installed': True, 'access_allowed': True, 'cursor_found': True, 'items': [item]}

    monkeypatch.setattr(cli, 'load_registry', lambda: registry)
    stdout, stderr = io.StringIO(), io.StringIO()
    assert cli.main(['read', cap, '--request', '-'], stdin=io.StringIO(json.dumps(req)), stdout=stdout, stderr=stderr, port_factory=lambda *args: Port()) == 0
    response = json.loads(stdout.getvalue())
    registry.validate_instance(f'schemas/v1/{cap}.response.schema.json', response)
    assert not stderr.getvalue() and response['odoo']['model'] == 'res.company' and response['odoo']['record_ids'] == [7]
    for field, value in (('id', 8), ('company_id', 8), ('qr_code', 1), ('quick_edit_mode', False), ('account_sale_tax_id', False)):
        with pytest.raises(core_object_reads.CoreObjectReadError):
            original, item[field] = item[field], value
            try: core_object_reads.read_core_object(cap, Port(), req)
            finally: item[field] = original


@pytest.mark.parametrize('capability_id,params', [
    (contracts.GET_ID, {'company_id': 8}),
    ('company.invoice_display.update', {'changes': {}}),
    ('company.invoice_display.update', {'changes': {'qr_code': 1}}),
    ('company.invoice_display.update', {'changes': {'qr_code': None}}),
    ('company.invoice_display.update', {'changes': {'restrictive_audit_trail': True}}),
    ('company.tax_policy.update', {'changes': {'account_price_include': []}}),
    ('company.tax_policy.update', {'changes': {'account_sale_tax_id': True}}),
    ('company.fiscal_year_end.update', {'changes': {'fiscalyear_last_month': 2}}),
    ('company.fiscal_year_end.update', {'changes': {'fiscalyear_last_day': 0}}),
    ('company.fiscal_year_end.update', {'changes': {'fiscalyear_last_day': 32}}),
    ('company.bill_processing_policy.update', {'changes': {'quick_edit_mode': False}}),
    ('company.credit_policy.update', {'changes': {'account_use_credit_limit': True}, 'company_id': 8}),
])
def test_invalid_or_cross_operation_parameters_fail(capability_id, params):
    with pytest.raises(ValueError):
        contracts.normalize_parameters(capability_id, params)


def test_native_price_choice_is_exposed_not_silently_ignored():
    params = {'changes': {'account_price_include': 'tax_included'}}
    assert contracts.normalize_parameters('company.tax_policy.update', params) == params
    assert not any('lock' in field or 'currency_id' == field for field in contracts.SETTING_FIELDS)
