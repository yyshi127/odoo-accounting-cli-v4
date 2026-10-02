"""One bounded daily-accounting workflow, ordinary user and fresh rollback.

S01-S12 are connected acceptance cases, not new commands or per-command gates.
Business writes use in-process public CLI/normal ports/real ORM. Separate real
subprocess CLI/bridge samples are read-only, not durable-write transport proof.
"""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import sysconfig
import uuid
from decimal import Decimal
from pathlib import Path

import test_accounting_maintenance_batch_live as maintenance
import test_accounting_workflows_batch_live as workflows
import test_company_processing_batch_live as company_batch
import test_document_lifecycle_write_batch_live as lifecycle
import test_financial_report_export_batch_live as exports
import test_invoice_preparation_batch_live as preparation
import test_payment_bank_capability_batch_live as core

try:
    import pytest
except ModuleNotFoundError:
    if '--live-worker' not in sys.argv:
        raise
    pytest = None

_ALLOW_ENV = 'ODACV4_ALLOW_DAILY_CORE_ACCEPTANCE_SMOKE'
_SCENARIOS = {f'S{index:02}' for index in range(1, 13)}
_MODELS = tuple(dict.fromkeys((*core._BUSINESS_MODELS, 'account.account',
    'account.journal', 'account.bank.statement', 'mail.alias',
    'account.payment.method.line', 'account.move.reversal', 'account.payment.register',
    'account.tax.group', 'account.tax', 'account.tax.repartition.line',
    'account.payment.term', 'account.payment.term.line', 'account.account.tag',
    'account.report.line', 'account.report.expression')))


def _root():
    return Path(__file__).resolve().parents[2]


class _Client:
    def __init__(self, env, admin):
        self.env, self.admin = env, admin
        self.tracked = {model: set() for model in _MODELS}
        self.capabilities, self.last_runtime_failure = set(), None

    def track(self, record):
        self.tracked[record._name].update(record.ids)
        if record._name == 'account.move':
            self.tracked['account.move.line'].update(record.line_ids.ids)
        elif record._name == 'account.tax':
            self.tracked['account.tax.repartition.line'].update(
                (record.invoice_repartition_line_ids | record.refund_repartition_line_ids).ids)
        elif record._name == 'account.journal':
            self.tracked['mail.alias'].update(record.alias_id.ids)
            self.tracked['account.payment.method.line'].update(
                (record.inbound_payment_method_line_ids | record.outbound_payment_method_line_ids).ids)
        elif record._name == 'account.payment.term':
            self.tracked['account.payment.term.line'].update(record.line_ids.ids)
        return record

    def invoke(self, action, payload):
        from odoo_accounting_cli_v4.bridge.client import BridgeError
        from odoo_accounting_cli_v4.bridge.runtime import RuntimeFailure, _dispatch

        self.env.invalidate_all()
        assert self.env.uid == 5 and not self.env.su and self.env.company.id == 1
        try:
            with self.env.cr.savepoint():
                page = _dispatch(self.env, action, payload, 1, (1,))
        except RuntimeFailure as exc:
            self.last_runtime_failure = exc
            raise BridgeError(exc.code, str(exc), exit_code=exc.exit_code,
                              retryable=exc.retryable, details=exc.details) from exc
        result = page.get('result')
        if isinstance(result, dict):
            for item in result.get('items', [result]):
                if item.get('model') in self.tracked and item.get('id'):
                    # Admin reads only for tracking. Never supplies a business result.
                    self.track(self.admin[item['model']].browse(item['id']))
                self.tracked['account.partial.reconcile'].update(item.get('partial_reconcile_ids', []))
                if item.get('full_reconcile_id'):
                    self.tracked['account.full.reconcile'].add(item['full_reconcile_id'])
        core._collect_related(self.admin, self.tracked)
        return page


class _Case:
    def __init__(self, admin, client, alias, run_id, marker):
        from odoo import fields

        self.admin, self.client, self.env = admin, client, client.env
        self.alias, self.run_id, self.marker = alias, run_id, marker
        self.today = fields.Date.context_today(self.env.user)
        self.ids, self.verified = lifecycle._fixture_ids(self.env, alias), set()
        self.counter = 0

    def fixture(self, model, values, company=1):
        return self.client.track(self.admin[model].with_company(
            self.admin['res.company'].browse(company)).create(values))

    def _port(self, capability, request):
        from odoo_accounting_cli_v4 import cli

        constructor = cli.OdooBridgeClient
        cli.OdooBridgeClient = lambda *args, **kwargs: self.client
        try:
            # Preserve the production config resolver and actual port selection.
            return cli._configured_port_factory(capability, request)
        finally:
            cli.OdooBridgeClient = constructor

    def _call(self, capability, params, key=None, confirmation=None, code=0):
        from odoo_accounting_cli_v4 import cli

        request = core._request(self.alias, self.run_id, capability, params)
        descriptor = cli.load_registry().describe(capability)
        cli.load_registry().validate_instance(descriptor['schemas']['request'], request)
        argv = ['read', capability, '--request', '-'] if key is None else [
            'write', 'run', capability, '--request', '-', '--idempotency-key', key,
            '--confirm', capability if confirmation is None else confirmation]
        stdout, stderr = io.StringIO(), io.StringIO()
        self.client.last_runtime_failure = None
        actual = cli.main(argv, stdin=io.StringIO(json.dumps(request)), stdout=stdout,
                          stderr=stderr, port_factory=self._port)
        assert actual == code and not stderr.getvalue(), stdout.getvalue()
        assert len(stdout.getvalue().splitlines()) == 1
        response = json.loads(stdout.getvalue())
        cli.load_registry().validate_instance(descriptor['schemas']['response'], response)
        assert response['request_id'] == request['request_id']
        if code:
            assert not response['success']
        else:
            assert response['success'] and response['status'] == 'verified'
            assert response['odoo']['user_id'] == 5 and response['odoo']['company_id'] == 1
            self.client.capabilities.add(capability)
        return response

    def read(self, capability, params):
        return self._call(capability, params)['data']

    def key(self, capability, params, label=None):
        from odoo_accounting_cli_v4.capabilities.core_writes import (
            _expected_idempotency_key,
            validate_core_write_request,
        )

        normalized = validate_core_write_request(capability,
            core._request(self.alias, self.run_id, capability, params))[2]
        expected = _expected_idempotency_key(capability, normalized, 1)
        if expected:
            return expected
        self.counter += 1
        return f'{capability}:{self.run_id.hex}:{label or self.counter}'

    def write(self, capability, params, replay=False, label=None):
        key = self.key(capability, params, label)
        first = self._call(capability, params, key=key)['data']
        assert not first['idempotent_replay'], first
        result = first['result']
        if replay:
            second = self._call(capability, params, key=key)['data']
            assert second['idempotent_replay'] and second['result'] == result, second
        return result

    def denied(self, capability, params, error, code, key=None, confirmation=None):
        response = self._call(capability, params,
            key=key or self.key(capability, params), confirmation=confirmation, code=code)
        assert response['error']['code'] in ({error} if isinstance(error, str) else set(error)), response
        return response


def _fixtures(case):
    from odoo import Command

    def account(label, kind):
        return case.fixture('account.account', {'name': case.marker + label,
            'code': 'D' + label[0].upper() + case.run_id.hex[:8], 'account_type': kind,
            'reconcile': kind in {'asset_cash', 'asset_current'},
            'company_ids': [Command.set([1])]})

    owned = {label: account(label, kind) for label, kind in (
        ('liquidity', 'asset_cash'), ('outstanding', 'asset_current'),
        ('suspense', 'asset_current'), ('tax', 'liability_current'))}
    bank = case.fixture('account.journal', {'name': case.marker + 'bank',
        'code': 'D' + case.run_id.hex[:4], 'type': 'bank', 'company_id': 1,
        'default_account_id': owned['liquidity'].id, 'suspense_account_id': owned['suspense'].id})
    methods = {}
    for direction in ('inbound', 'outbound'):
        method = bank[f'{direction}_payment_method_line_ids'].filtered(
            lambda row: row.payment_method_id.code == 'manual')
        assert len(method) == 1
        method.write({'payment_account_id': owned['outstanding'].id})
        methods[direction] = method.id
    case.ids.update({f'owned_{label}': record.id for label, record in owned.items()})
    case.ids.update(owned_bank_journal=bank.id, owned_bank_inbound=methods['inbound'],
                    owned_bank_outbound=methods['outbound'], company_currency=case.ids['currency'])
    tax_report = case.admin.ref('account.generic_tax_report')
    report_line = case.fixture('account.report.line', {'name': case.marker + 'tax-report',
        'report_id': tax_report.id, 'sequence': 9999})
    expression_label = tax_report.column_ids[:1].expression_label
    case.fixture('account.report.expression', {'report_line_id': report_line.id,
        'label': expression_label, 'engine': 'tax_tags', 'formula': case.marker})
    tag = case.admin['account.account.tag']._get_tax_tags(case.marker, tax_report.country_id.id)
    assert len(tag) == 1
    case.client.track(tag)
    case.ids['tax_report_line'], case.ids['tax_tag'] = report_line.id, tag.id
    for kind in ('sale', 'purchase'):
        group = case.fixture('account.tax.group', {'name': case.marker + kind, 'company_id': 1})
        tax = case.fixture('account.tax', {'name': case.marker + kind, 'company_id': 1,
            'tax_group_id': group.id, 'type_tax_use': kind, 'amount_type': 'percent',
            'amount': 10, 'price_include_override': 'tax_excluded'})
        for repartition in (tax.invoice_repartition_line_ids | tax.refund_repartition_line_ids).filtered(
                lambda row: row.repartition_type == 'tax'):
            repartition.write({'account_id': owned['tax'].id, 'tag_ids': [Command.set(tag.ids)]})
        case.ids[f'{kind}_tax'] = tax.id
    term = case.fixture('account.payment.term', {'name': case.marker + 'term',
        'company_id': 1, 'line_ids': [Command.create({'value': 'percent', 'value_amount': 100,
            'delay_type': 'days_after', 'nb_days': 0})]})
    case.ids['payment_term'] = term.id


def _discovery(case):
    company = case.read('company.accounting_context.list', {'limit': 1000})
    assert 1 in {row['id'] for row in company['items']}
    access = case.read('user.accounting_access.inspect', {})
    assert access['user']['id'] == 5 and access['user']['active']
    assert all(row['read'] for row in access['model_acl'])
    for capability, param, identifier in (
        ('account.account.get', 'account_id', case.ids['income']),
        ('journal.get', 'journal_id', case.ids['sale_journal']),
        ('partner.accounting.get', 'partner_id', case.ids['customer']),
        ('tax.get', 'tax_id', case.ids['sale_tax']),
        ('payment_term.get', 'payment_term_id', case.ids['payment_term'])):
        data = case.read(capability, {param: identifier})
        assert data['id'] == identifier
    case.verified.add('S01')


def _native_report(case, capability, params):
    from odoo_accounting_cli_v4.bridge.financial_reports import _ACTIONS
    from odoo_accounting_cli_v4.bridge.runtime import _FINANCIAL_REPORT_ACTIONS

    spec = _FINANCIAL_REPORT_ACTIONS[_ACTIONS[capability]]
    options = case.env.ref(spec['xml_id']).get_options({'all_entries': False,
        'date': {'date_from': params.get('date_from', False),
                 'date_to': params.get('date_to', params.get('as_of')),
                 'mode': spec['mode'], 'filter': 'custom'}})
    report = case.env['account.report'].browse(options['report_id'])
    information = (report.get_report_information_readonly(options)
                   if options['readonly_query'] else report.get_report_information(options))
    assert set(report.get_report_company_ids(options)) == {1} and not options['all_entries']
    return information['lines']


def _report_value(value, figure_type):
    if value is None or value is False or value == '':
        return None
    return str(value) if figure_type in {'date', 'string'} else Decimal(str(value))


def _reports(case):
    day = case.today.isoformat()
    # Unequal open sale/purchase amounts ensure real aged and tax consumers are nonempty.
    for supplier, price in ((False, '73'), (True, '21')):
        created = case.write('vendor_bill.create' if supplier else 'customer_invoice.create', {
            'partner_id': case.ids['supplier' if supplier else 'customer'],
            'journal_id': case.ids['purchase_journal' if supplier else 'sale_journal'],
            'invoice_date': day, 'date': day, 'currency_id': case.ids['currency'],
            'reference': case.marker + str(supplier), 'lines': [{'name': case.marker + 'report-source',
                'account_id': case.ids['expense' if supplier else 'income'], 'quantity': '1',
                'price_unit': price, 'tax_ids': [case.ids['purchase_tax' if supplier else 'sale_tax']]}]},
            label='report-source-' + str(supplier))
        case.write('invoice.post', {'move_id': created['id']})
    reports = {}
    for key in ('trial_balance', 'general_ledger', 'partner_ledger', 'balance_sheet',
                'profit_and_loss', 'cash_flow', 'tax', 'aged_receivable', 'aged_payable'):
        capability = 'report.' + key
        params = {'as_of': day} if key in {'balance_sheet', 'aged_receivable', 'aged_payable'} else {'date_from': day, 'date_to': day}
        data = case.read(capability, {**params, 'limit': 1000})
        all_lines = list(data['lines'])
        while data['has_more']:
            data = case.read(capability, {**params, 'limit': 1000, 'cursor': data['next_cursor']})
            all_lines += data['lines']
        data = {**data, 'lines': all_lines}
        assert data['currency']['id'] == case.ids['currency'] and data['basis'] == 'posted_entries'
        native = _native_report(case, capability, params)
        types = [column.get('figure_type', 'monetary') for column in data['columns']]
        expected = {row['id']: tuple(_report_value(cell.get('no_format'), figure_type)
            for cell, figure_type in zip(row['columns'], types, strict=True)) for row in native}
        actual = {row['id']: tuple(_report_value(value, figure_type)
            for value, figure_type in zip(row['values'], types, strict=True)) for row in all_lines}
        assert expected == actual, (capability, expected, actual)
        assert any(value for row in actual.values() for value in row if isinstance(value, Decimal)), capability
        reports[key] = data
    # Independent AML oracle, rather than comparing only two report adapter paths.
    amounts = {}
    native_lines = case.env['account.move.line'].search([
            ('company_id', '=', 1), ('parent_state', '=', 'posted'),
            ('date', '>=', day), ('date', '<=', day)])
    precision = Decimal(str(case.env.company.currency_id.rounding))
    for line in native_lines:
        if not line.account_id:
            continue
        values = amounts.setdefault(line.account_id.id, [Decimal(0), Decimal(0)])
        values[0] += Decimal(str(line.debit))
        values[1] += Decimal(str(line.credit))
    actual = {}
    for row in reports['trial_balance']['lines']:
        model, identifier = case.env['account.report']._get_model_info_from_id(row['id'])
        if model == 'account.account' and any(Decimal(value or '0') for value in row['values'][1:3]):
            actual[identifier] = [Decimal(value or '0') for value in row['values'][1:3]]
    assert actual == {identifier: [value.quantize(precision) for value in values]
                      for identifier, values in amounts.items() if any(values)}
    analysis = case.read('invoice.analysis.summary', {'date_from': day, 'date_to': day,
        'group_by': 'move_type', 'states': ['posted']})
    ledger = case.read('journal_item.analysis.summary', {'date_from': day, 'date_to': day, 'group_by': 'journal'})
    invoice_rows = case.env['account.invoice.report'].search([
        ('company_id', '=', 1), ('state', '=', 'posted'),
        ('move_type', 'in', ['out_invoice', 'out_refund', 'in_invoice', 'in_refund']),
        ('invoice_date', '>=', day), ('invoice_date', '<=', day)])
    _assert_summary(analysis, invoice_rows, lambda row: row.move_type,
        {'quantity': 'quantity', 'untaxed_amount': 'price_subtotal',
         'total_amount': 'price_total', 'margin': 'price_margin',
         'inventory_value': 'inventory_value'}, precision)
    _assert_summary(ledger, native_lines, lambda row: row.journal_id.id,
        {'debit': 'debit', 'credit': 'credit', 'balance': 'balance'}, precision)
    case.verified.add('S10')
    for format_name in ('pdf', 'xlsx'):
        exported = case.read('report.trial_balance.export', {'date_from': day, 'date_to': day, 'format': format_name})
        exports._assert_filtered_export(exported, format_name, reports['trial_balance'])
    return reports


def _assert_summary(data, rows, group_key, fields, precision):
    assert data['company_id'] == 1 and rows and data['company_currency']['id'] == rows.company_id.currency_id.id
    expected = {}
    for row in rows:
        values = expected.setdefault(group_key(row), {'row_count': 0, **dict.fromkeys(fields, Decimal(0))})
        values['row_count'] += 1
        for key, field in fields.items():
            values[key] += Decimal(str(row[field]))
    actual = {item['group']['value'] if item['group']['id'] is None else item['group']['id']: item
              for item in data['groups']}
    assert set(actual) == set(expected)
    for key, values in expected.items():
        assert actual[key]['row_count'] == values['row_count']
        for field in fields:
            assert Decimal(actual[key][field]).quantize(precision) == values[field].quantize(precision), (key, field)
    assert data['totals']['row_count'] == len(rows)
    for field in fields:
        expected_total = sum((values[field] for values in expected.values()), Decimal(0))
        assert Decimal(data['totals'][field]).quantize(precision) == expected_total.quantize(precision), field


def _external_cli_samples(alias, run_id):
    from odoo_accounting_cli_v4.registry import load_registry

    registry = load_registry()
    for capability in ('user.accounting_access.inspect', 'account.account.list'):
        request = core._request(alias, run_id, capability, {} if capability.startswith('user.') else {'limit': 1})
        completed = subprocess.run([sys.executable, '-m', 'odoo_accounting_cli_v4', 'read', capability, '--request', '-'],
            cwd=_root(), input=json.dumps(request), text=True, capture_output=True, check=False, timeout=240)
        assert completed.returncode == 0 and not completed.stderr and len(completed.stdout.splitlines()) == 1, completed.stdout + completed.stderr
        result = json.loads(completed.stdout)
        registry.validate_instance(registry.describe(capability)['schemas']['response'], result)
        assert result['success'] and result['odoo']['user_id'] == 5 and result['odoo']['company_id'] == 1
        assert result['request_id'] == request['request_id']


def _live_worker():
    args = lifecycle._arguments(None)
    sys.path.insert(0, str(args.odoo_source.resolve(strict=True)))
    sys.path.insert(0, str(_root() / 'src'))
    import daily_core_invoice_cases
    import daily_core_ledger_cases
    from odoo import SUPERUSER_ID, api
    from odoo.orm.registry import Registry
    from odoo.tools import config

    from odoo_accounting_cli_v4 import cli

    config.parse_config(['--config', str(args.odoo_config.resolve(strict=True)),
        '--database', args.database, '--no-http', '--logfile=/dev/null'])
    registry, actual_registry = Registry(args.database), cli.load_registry()
    cli.load_registry = lambda: actual_registry
    cursor, marker = registry.cursor(), f'ODACV4-DAILY-{args.alias}-{args.run_id.hex}'
    tracked, baseline, case, failure, wizard_before = {}, None, None, None, {}
    try:
        context = {'allowed_company_ids': [1], 'lang': 'en_US', 'tz': 'Asia/Shanghai',
            'tracking_disable': True, 'mail_create_nosubscribe': True, 'mail_notrack': True}
        admin = api.Environment(cursor, SUPERUSER_ID, context)
        company_fields = sorted(name for name, field in admin['res.company']._fields.items()
            if field.store and field.type not in {'binary', 'one2many', 'many2many'})
        baseline = (maintenance._groups(admin), company_batch._company_snapshot(admin, company_fields),
            preparation._defaults(admin), workflows._currency_snapshot(admin))
        wizard_before = {model: set(admin[model].search([]).ids)
                         for model in ('account.payment.register', 'account.move.reversal')}
        env = api.Environment(cursor, 5, context)
        assert env.user.active and env.user.login == lifecycle._USER_LOGIN and not env.su
        case = _Case(admin, _Client(env, admin), args.alias, args.run_id, marker)
        tracked = case.client.tracked
        _fixtures(case)
        _discovery(case)
        daily_core_invoice_cases.exercise(case)
        daily_core_ledger_cases.exercise(case)
        _reports(case)
        _external_cli_samples(args.alias, args.run_id)
        case.verified.add('S11')
        assert case.verified == _SCENARIOS, sorted(_SCENARIOS - case.verified)
        assert maintenance._groups(admin) == baseline[0], 'No temporary business-user role grants in daily-core acceptance.'
        for model, previous in wizard_before.items():
            tracked[model].update(set(admin[model].search([]).ids) - previous)
        core._collect_marked(admin, tracked, marker)
    except BaseException as exc:  # noqa: BLE001 - audit rollback before propagating.
        failure = exc
    finally:
        if case is not None:
            try:
                core._collect_marked(case.admin, tracked, marker)
                for model, previous in wizard_before.items():
                    tracked[model].update(set(case.admin[model].search([]).ids) - previous)
            except BaseException as audit_failure:  # noqa: BLE001
                if failure is None:
                    failure = audit_failure
        cursor.rollback()
        cursor.close()
    with registry.cursor() as verify_cursor:
        try:
            verify = api.Environment(verify_cursor, SUPERUSER_ID,
                {'allowed_company_ids': [1, 2], 'lang': 'en_US', 'active_test': False})
            for model, identifiers in tracked.items():
                assert not verify[model].search_count([('id', 'in', sorted(identifiers))]), model
            for model in ('account.account', 'account.journal', 'account.tax.group', 'account.tax',
                          'account.payment.term', 'account.account.tag', 'account.report.line'):
                assert not verify[model].search_count([('name', 'ilike', marker)]), model
            assert not verify['account.move.line'].search_count([('name', 'ilike', marker)])
            if baseline is not None:
                assert maintenance._groups(verify) == baseline[0]
                assert company_batch._company_snapshot(verify, company_fields) == baseline[1]
                assert preparation._defaults(verify) == baseline[2]
                assert workflows._currency_snapshot(verify) == baseline[3]
                assert all(set(verify[model].search([]).ids) == previous for model, previous in wizard_before.items())
        finally:
            verify_cursor.rollback()
    if failure is not None:
        print(json.dumps({'alias': args.alias, 'passed_scenarios': sorted(case.verified) if case else [],
            'rollback_verified': True}), file=sys.stderr)
        raise failure
    print(json.dumps({'alias': args.alias, 'database': args.database, 'company_id': 1,
        'user_id': 5, 'business_su': False, 'scenarios': sorted(case.verified),
        'capabilities': sorted(case.client.capabilities), 'rollback_verified': True,
        'execution': 'in_process_cli_real_orm_with_readonly_external_cli_bridge_samples',
        'business_user_groups_unchanged': True}, sort_keys=True))
    return 0


if pytest is not None:
    @pytest.mark.integration
    def test_daily_core_acceptance_rolls_back_both_isolated_aliases():
        config_path, runtime = lifecycle._enabled_runtime(_ALLOW_ENV)
        run_id = uuid.uuid4()
        for alias in lifecycle._ALIASES:
            command, timeout = lifecycle._worker_command(alias, run_id, config_path, runtime)
            command[1] = str(Path(__file__).resolve())
            environment = os.environ.copy()
            environment['PYTHONDONTWRITEBYTECODE'] = '1'
            environment['PYTHONPATH'] = os.pathsep.join(filter(None, (
                str(_root() / 'src'), sysconfig.get_path('purelib'), environment.get('PYTHONPATH'))))
            completed = subprocess.run(command, cwd=_root(), env=environment, text=True,
                capture_output=True, check=False, timeout=max(timeout, 900))
            assert completed.returncode == 0, completed.stdout + completed.stderr
            assert len(completed.stdout.splitlines()) == 1
            summary = json.loads(completed.stdout)
            assert summary['scenarios'] == sorted(_SCENARIOS) and summary['rollback_verified']
            assert summary['user_id'] == 5 and summary['business_su'] is False
            print(completed.stdout.strip(), flush=True)


if __name__ == '__main__':
    raise SystemExit(_live_worker())
