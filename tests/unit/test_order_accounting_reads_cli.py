"""Real narrow-port CLI dispatch for the fixed order-accounting read batch."""
from __future__ import annotations

import io
import json
from copy import deepcopy

import pytest
from test_order_documents import (
    _purchase_header,
    _purchase_line,
    _request,
    _sale_header,
    _sale_line,
    _summary,
)

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4.bridge.order_documents import ACTION, OdooOrderDocumentsPort


class Client:
    def __init__(self, row):
        self.row = row
        self.calls = []

    def invoke(self, action, payload):
        self.calls.append((action, deepcopy(payload)))
        return {'user_id': 5, 'company_visible': True, 'module_installed': True,
                'access_allowed': True, 'cursor_found': True, 'items': [deepcopy(self.row)]}


@pytest.mark.parametrize('kind', ['sale', 'purchase'])
@pytest.mark.parametrize('action', ['search', 'get', 'line.search', 'line.get', 'analysis.summary'])
def test_all_fixed_order_reads_use_real_port_and_response_schema(kind, action):
    cap = f'{kind}.order.{action}'
    header = _sale_header if kind == 'sale' else _purchase_header
    line = _sale_line if kind == 'sale' else _purchase_line
    if action == 'analysis.summary':
        row = _summary()
        parameters = {'date_from': row['date_from'], 'date_to': row['date_to'], 'group_by': row['group_by'],
                      'user_id': 5, 'payment_term_id': 42, 'fiscal_position_id': 43, 'invoice_statuses': ['to invoice']}
    elif action.startswith('line.'):
        row = line()
        row.update(is_downpayment=True, **{'invoice_policy' if kind == 'sale' else 'purchase_method': 'order' if kind == 'sale' else 'purchase'})
        if action == 'line.get':
            row['invoices'] = []
            parameters = {'line_id': row['id']}
        else:
            row['to_invoice_quantity'] = '-1'
            parameters = {'is_downpayment': True, 'negative_to_invoice_only': True}
    else:
        row = header(include_details=action == 'get')
        row.update(payment_term_id=42, fiscal_position_id=43)
        parameters = {'order_id': row['id']} if action == 'get' else {'user_id': 5, 'payment_term_id': 42, 'fiscal_position_id': 43}
    client = Client(row)
    stdout, stderr = io.StringIO(), io.StringIO()
    code = cli.main(['read', cap, '--request', '-'], stdin=io.StringIO(json.dumps(_request(parameters))),
                    stdout=stdout, stderr=stderr, port_factory=lambda *_args: OdooOrderDocumentsPort(client))
    response = json.loads(stdout.getvalue())
    assert code == 0 and not stderr.getvalue(), response
    assert response['success'] and response['odoo']['user_id'] == 5
    assert response['odoo']['model'] == (f'{kind}.order.line' if action.startswith('line.') else f'{kind}.order')
    assert response['odoo']['record_ids'] == ([] if action == 'analysis.summary' else [row['id']])
    assert client.calls[0][0] == ACTION and client.calls[0][1]['capability_id'] == cap
    assert all(client.calls[0][1]['parameters'][key] == value for key, value in parameters.items())


@pytest.mark.parametrize('kind', ['sale', 'purchase'])
def test_line_get_has_fixed_handler_validator_factory_and_model(kind, monkeypatch):
    cap = f'{kind}.order.line.get'
    key = f'{kind}_order_line_get'
    request = _request({'line_id': 101})
    assert cli._REQUEST_VALIDATORS[key](request)[2] == {'line_id': 101}
    marker, client = object(), object()
    monkeypatch.setattr(cli, 'load_runtime_config', lambda *_: type('Config', (), {'resolve': lambda *_: marker})())
    monkeypatch.setattr(cli, 'OdooBridgeClient', lambda *_args, **_kwargs: client)
    assert type(cli._configured_port_factory(cap, request)) is OdooOrderDocumentsPort
