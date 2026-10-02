from __future__ import annotations

import io
import json
from contextlib import contextmanager, nullcontext
from copy import deepcopy
from decimal import Decimal
from types import SimpleNamespace

import pytest
from test_fiscal_mapping_writes import request

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4 import invoice_preparation_contracts as contracts
from odoo_accounting_cli_v4.bridge import core_object_reads_runtime as reads
from odoo_accounting_cli_v4.bridge import core_writes_runtime as writes
from odoo_accounting_cli_v4.capabilities import core_object_reads, core_writes
from odoo_accounting_cli_v4.registry import load_registry

PARAMETERS = {
    "invoice.service_dates.update": {"move_id": 31, "changes": {"delivery_date": "2026-10-02", "taxable_supply_date": None}},
    "invoice.tax_totals.adjust": {"move_id": 31, "groups": [{"tax_group_id": 41, "tax_amount": "15.01"}]},
}
READ_PARAMETERS = {
    contracts.DATES_ID: {"move_id": 31}, contracts.ALERTS_ID: {"move_id": 31}, contracts.ORIGINS_ID: {"move_id": 31},
    contracts.CATEGORY_ID: {"category_id": 31}, contracts.TAX_PROFILE_ID: {"product_id": 31},
    contracts.ACCOUNTS_ID: {"product_id": 31, "fiscal_position_id": 91},
}


def result(capability_id, parameters):
    return {"model": "account.move", "id": parameters["move_id"], "name": "INV/2026/0031", "state": "draft",
            "company_id": 7, "move_type": "out_invoice", "source_id": None, "line_ids": [41, 42],
            "partial_reconcile_ids": [], "full_reconcile_id": None, "reconciled": False}


def read_item(capability_id, record_id=31):
    item = {"id": record_id, "company_id": 7}
    if capability_id in {contracts.DATES_ID, contracts.ALERTS_ID, contracts.ORIGINS_ID}:
        item.update(move_type="out_invoice", state="draft")
    if capability_id == contracts.DATES_ID:
        return {**item, "date": "2026-10-02", "invoice_date": "2026-10-02", "delivery_date": None, "taxable_supply_date": "2026-10-02",
                "show_delivery_date": True, "show_taxable_supply_date": False}
    if capability_id == contracts.ALERTS_ID:
        return {**item, "alerts": [{"key": "zero_amount", "level": "warning", "message": "A zero-valued line exists.", "action_label": None}]}
    if capability_id == contracts.ORIGINS_ID:
        reference = {"id": 81, "name": "INV/2026/0081", "move_type": "out_invoice", "state": "posted", "date": "2026-10-02"}
        return {**item, "reversed_entry": reference, "tax_cash_basis_origin_move": None, "reversal_moves": [],
                "tax_cash_basis_created_moves": [], "adjusting_entry_origin_moves": [], "adjusting_entries_moves": []}
    if capability_id == contracts.CATEGORY_ID:
        return {**item, "income_account_id": 11, "expense_account_id": 12, "company_income_account_id": None, "company_expense_account_id": None}
    if capability_id == contracts.TAX_PROFILE_ID:
        return {**item, "template_id": 51, "sale_tax_ids": [41, 42], "purchase_tax_ids": [43], "account_tag_ids": [61]}
    return {**item, "template_id": 51, "fiscal_position_id": 91, "income_account_id": 11, "expense_account_id": 12,
            "stock_valuation_account_id": None, "stock_variation_account_id": None, "stock_journal_id": None}


@pytest.fixture(scope="module")
def registry():
    return load_registry()


@pytest.mark.parametrize("capability_id", PARAMETERS)
def test_closed_write_cli_key_confirmation_schema_and_parent_binding(capability_id, registry, monkeypatch):
    params, expected = PARAMETERS[capability_id], result(capability_id, PARAMETERS[capability_id])
    req = request(params)
    registry.validate_instance(f"schemas/v1/{capability_id}.request.schema.json", req)
    key = contracts.idempotency_key(capability_id, params, 7)
    assert writes._valid_parameters(capability_id, params, 7)
    assert key == writes._deterministic_key(capability_id, params, 7) == core_writes._expected_idempotency_key(capability_id, params, 7)

    class Port:
        user_id = 42

        def execute(self, **payload):
            assert payload["parameters"] == params and payload["company_id"] == 7
            assert payload["confirmation"] == capability_id and payload["idempotency_key"] == key
            return {"user_id": 42, "company_visible": True, "module_installed": True, "access_allowed": True,
                    "idempotent_replay": False, "result": deepcopy(expected)}

    monkeypatch.setattr(cli, "load_registry", lambda: registry)
    stdout, stderr = io.StringIO(), io.StringIO()
    assert cli.main(["write", "run", capability_id, "--request", "-", "--confirm", capability_id, "--idempotency-key", key],
                    stdin=io.StringIO(json.dumps(req)), stdout=stdout, stderr=stderr, port_factory=lambda *args: Port()) == 0, stdout.getvalue()
    assert not stderr.getvalue()
    registry.validate_instance(f"schemas/v1/{capability_id}.response.schema.json", json.loads(stdout.getvalue()))
    for field, value in (("id", 99), ("company_id", 8), ("model", "account.move.line"), ("source_id", 41), ("state", "posted"), ("move_type", "entry")):
        with pytest.raises(core_writes.CoreWriteError):
            core_writes._validate_result(capability_id, params, {**expected, field: value}, company_id=7, idempotent_replay=False)
    core_writes._validate_result(capability_id, params, {**expected, "reconciled": True}, company_id=7, idempotent_replay=True)


@pytest.mark.parametrize("capability_id", READ_PARAMETERS)
def test_closed_read_cli_schema_target_and_fiscal_position_binding(capability_id, registry, monkeypatch):
    params, item = READ_PARAMETERS[capability_id], read_item(capability_id)
    req = request(params)
    registry.validate_instance(f"schemas/v1/{capability_id}.request.schema.json", req)
    assert reads._valid_parameters(capability_id, params)

    class Port:
        user_id = 42

        def read(self, **payload):
            assert payload["parameters"] == params and payload["company_id"] == 7
            return {"user_id": 42, "company_visible": True, "module_installed": True, "access_allowed": True,
                    "cursor_found": True, "items": [item]}

    monkeypatch.setattr(cli, "load_registry", lambda: registry)
    stdout, stderr = io.StringIO(), io.StringIO()
    assert cli.main(["read", capability_id, "--request", "-"], stdin=io.StringIO(json.dumps(req)),
                    stdout=stdout, stderr=stderr, port_factory=lambda *args: Port()) == 0, stdout.getvalue()
    response = json.loads(stdout.getvalue())
    assert not stderr.getvalue()
    registry.validate_instance(f"schemas/v1/{capability_id}.response.schema.json", response)
    invalid = [("id", 99), ("company_id", 8)]
    if capability_id == contracts.ACCOUNTS_ID:
        invalid.append(("fiscal_position_id", None))
    for field, value in invalid:
        original, item[field] = item[field], value
        with pytest.raises(core_object_reads.CoreObjectReadError):
            core_object_reads.read_core_object(capability_id, Port(), req)
        item[field] = original


@pytest.mark.parametrize("capability_id,changes", [
    ("invoice.service_dates.update", {"changes": {}}),
    ("invoice.service_dates.update", {"changes": {"invoice_date": "2026-10-02"}}),
    ("invoice.service_dates.update", {"changes": {"delivery_date": "2026-02-30"}}),
    ("invoice.service_dates.update", {"changes": {"taxable_supply_date": False}}),
    ("invoice.tax_totals.adjust", {"groups": []}),
    ("invoice.tax_totals.adjust", {"groups": [{"tax_group_id": True, "tax_amount": "1"}]}),
    ("invoice.tax_totals.adjust", {"groups": [{"tax_group_id": 41, "tax_amount": 1}]}),
    ("invoice.tax_totals.adjust", {"groups": [{"tax_group_id": 41, "tax_amount": "1.00"}]}),
    ("invoice.tax_totals.adjust", {"groups": [{"tax_group_id": 41, "tax_amount": "NaN"}]}),
    ("invoice.tax_totals.adjust", {"groups": [{"tax_group_id": 41, "tax_amount": "1", "company_id": 8}]}),
    ("invoice.tax_totals.adjust", {"groups": [{"tax_group_id": 42, "tax_amount": "1"}, {"tax_group_id": 41, "tax_amount": "1"}]}),
    ("invoice.tax_totals.adjust", {"groups": [{"tax_group_id": 41, "tax_amount": "1"}, {"tax_group_id": 41, "tax_amount": "2"}]}),
])
def test_invalid_write_parameters_fail_before_native_mutation(capability_id, changes):
    params = {**deepcopy(PARAMETERS[capability_id]), **changes}
    with pytest.raises(ValueError):
        contracts.normalize_parameters(capability_id, params)
    with pytest.raises(core_writes.CoreWriteError):
        core_writes.validate_core_write_request(capability_id, request(params))


@pytest.mark.parametrize("capability_id", READ_PARAMETERS)
def test_closed_reads_reject_target_overrides(capability_id):
    params = {**READ_PARAMETERS[capability_id], "company_id": 8}
    with pytest.raises(ValueError):
        contracts.normalize_parameters(capability_id, params)


def test_alerts_contain_no_executable_action_and_origins_are_typed():
    alerts = read_item(contracts.ALERTS_ID)
    assert contracts.valid_read_item(contracts.ALERTS_ID, alerts, 7)
    alerts["alerts"][0]["action_call"] = "method_to_execute"
    assert not contracts.valid_read_item(contracts.ALERTS_ID, alerts, 7)
    origins = read_item(contracts.ORIGINS_ID)
    origins["reversal_moves"] = [{"id": 81}]
    assert not contracts.valid_read_item(contracts.ORIGINS_ID, origins, 7)
    accounts = read_item(contracts.ACCOUNTS_ID)
    assert contracts.valid_read_item(contracts.ACCOUNTS_ID, accounts, 7)
    accounts["stock_variation_account_id"] = False
    assert not contracts.valid_read_item(contracts.ACCOUNTS_ID, accounts, 7)


def test_nullable_dates_and_signed_tax_groups_remain_closed_native_inputs():
    assert contracts.normalize_parameters("invoice.service_dates.update", {"move_id": 31, "changes": {"delivery_date": None, "taxable_supply_date": None}})["changes"] == {"delivery_date": None, "taxable_supply_date": None}
    assert contracts.normalize_parameters("invoice.tax_totals.adjust", {"move_id": 31, "groups": [{"tax_group_id": 41, "tax_amount": "-15.01"}]})["groups"][0]["tax_amount"] == "-15.01"


def test_origin_references_allow_native_drafts_without_assigned_names():
    item = read_item(contracts.ORIGINS_ID)
    item["reversed_entry"].update(state="draft", name=None)
    assert contracts.valid_read_item(contracts.ORIGINS_ID, item, 7)
    item["reversed_entry"]["name"] = False
    assert not contracts.valid_read_item(contracts.ORIGINS_ID, item, 7)


@pytest.mark.parametrize("groups", [[{"id": True}], [{"id": 41}, {"id": 41}]])
def test_native_tax_groups_reject_invalid_or_ambiguous_identity(groups):
    with pytest.raises(ValueError):
        writes._invoice_preparation_tax_groups({"subtotals": [{"tax_groups": groups}]})


@pytest.mark.parametrize("state,groups,error", [
    ("draft", [{"tax_group_id": 99, "tax_amount": "15.01"}], "business_rule_error"),
    ("draft", [{"tax_group_id": 41, "tax_amount": "15.011"}], "business_rule_error"),
    ("posted", [{"tax_group_id": 41, "tax_amount": "15.01"}], "state_conflict"),
])
def test_native_target_precision_and_state_denials_happen_before_write(state, groups, error, monkeypatch):
    from test_core_writes_runtime import Failure

    attempted = []
    currency = SimpleNamespace(round=lambda value: float(Decimal(str(value)).quantize(Decimal("0.01"))))
    move = SimpleNamespace(state=state, currency_id=currency,
                           tax_totals={"subtotals": [{"tax_groups": [{"id": 41, "tax_amount_currency": 15.0}]}]},
                           write=lambda values: attempted.append(values))
    monkeypatch.setattr(writes, "_search_one", lambda *args: move)
    env = SimpleNamespace(cr=SimpleNamespace(savepoint=nullcontext))
    with pytest.raises(Failure) as caught:
        writes._write_invoice_preparation(env, "invoice.tax_totals.adjust", {"move_id": 31, "groups": groups}, 7, Failure)
    assert caught.value.code == error and caught.value.exit_code == 6 and attempted == []


@pytest.fixture
def native_preparation(monkeypatch):
    from test_core_writes_runtime import Failure

    class Move:
        state = "draft"
        delivery_date = taxable_supply_date = False
        currency_id = SimpleNamespace(round=lambda value: float(Decimal(str(value)).quantize(Decimal("0.01"))))
        wrong_inverse = False

        def __init__(self):
            self.ledger = {41: Decimal(15), 42: Decimal(2), "term": Decimal(-117)}
            self.attempted = []
            self.invalidate_recordset()

        def invalidate_recordset(self):
            self.tax_totals = {"sentinel": {"keep": True}, "subtotals": [{"sentinel": "subtotal", "tax_groups": [
                {"id": group_id, "tax_amount_currency": float(self.ledger[group_id]), "non_deductible_tax_amount_currency": 0.0}
                for group_id in (41, 42)
            ]}]}

        def write(self, values):
            self.attempted.append(deepcopy(values))
            if "tax_totals" not in values:
                for field, value in values.items():
                    setattr(self, field, value)
                return
            for group in values["tax_totals"]["subtotals"][0]["tax_groups"]:
                group_id, amount = group["id"], Decimal(str(group["tax_amount_currency"]))
                if self.wrong_inverse and group_id == 41:
                    amount += 1
                self.ledger["term"] -= amount - self.ledger[group_id]
                self.ledger[group_id] = amount

    move = Move()

    @contextmanager
    def savepoint():
        previous = move.delivery_date, move.taxable_supply_date, deepcopy(move.ledger)
        try:
            yield
        except Exception:
            move.delivery_date, move.taxable_supply_date, move.ledger = previous
            move.invalidate_recordset()
            raise

    monkeypatch.setattr(writes, "_search_one", lambda *args: move)
    monkeypatch.setattr(writes, "_move_result", lambda native, company_id: result("", {"move_id": 31}))
    env = SimpleNamespace(cr=SimpleNamespace(savepoint=savepoint))

    def execute(capability_id, parameters):
        return writes._write_invoice_preparation(env, capability_id, parameters, 7, Failure)

    return move, execute, Failure


def test_native_service_dates_persist_clear_and_replay_without_extra_write(native_preparation):
    move, execute, _ = native_preparation
    parameters = {"move_id": 31, "changes": {"delivery_date": "2026-10-02", "taxable_supply_date": "2026-10-01"}}
    assert execute("invoice.service_dates.update", parameters)[1] is False
    assert (move.delivery_date, move.taxable_supply_date) == ("2026-10-02", "2026-10-01")
    assert execute("invoice.service_dates.update", parameters)[1] is True
    parameters["changes"] = dict.fromkeys(parameters["changes"])
    assert execute("invoice.service_dates.update", parameters)[1] is False
    assert (move.delivery_date, move.taxable_supply_date) == (False, False)
    assert execute("invoice.service_dates.update", parameters)[1] is True
    assert len(move.attempted) == 2 and move.attempted[-1] == {"delivery_date": False, "taxable_supply_date": False}


def test_native_tax_inverse_recomputes_ledger_preserves_payload_and_replays(native_preparation):
    move, execute, _ = native_preparation
    original_totals = move.tax_totals
    assert execute("invoice.tax_totals.adjust", PARAMETERS["invoice.tax_totals.adjust"])[1] is False
    assert original_totals["subtotals"][0]["tax_groups"][0]["tax_amount_currency"] == 15.0
    payload = move.attempted[0]["tax_totals"]
    assert payload["sentinel"] == {"keep": True} and payload["subtotals"][0]["sentinel"] == "subtotal"
    assert type(payload["subtotals"][0]["tax_groups"][0]["tax_amount_currency"]) is float
    assert payload["subtotals"][0]["tax_groups"][1] == original_totals["subtotals"][0]["tax_groups"][1]
    assert move.ledger == {41: Decimal("15.01"), 42: Decimal(2), "term": Decimal("-117.01")}
    assert execute("invoice.tax_totals.adjust", PARAMETERS["invoice.tax_totals.adjust"])[1] is True
    assert len(move.attempted) == 1


def test_native_tax_postcompute_mismatch_rolls_back_ledger(native_preparation):
    move, execute, failure_type = native_preparation
    before = deepcopy(move.ledger)
    move.wrong_inverse = True
    with pytest.raises(failure_type) as caught:
        execute("invoice.tax_totals.adjust", PARAMETERS["invoice.tax_totals.adjust"])
    assert caught.value.code == "odoo_write_error" and caught.value.exit_code == 6
    assert len(move.attempted) == 1 and move.ledger == before
    assert move.tax_totals["subtotals"][0]["tax_groups"][0]["tax_amount_currency"] == 15.0


@pytest.mark.parametrize("current_sale_tax", [False, True])
def test_native_product_reads_keep_parent_company_defaults_without_foreign_leaks(current_sale_tax):
    from test_core_object_reads_runtime import Env, Model, Records, _matches, _record

    calls = []
    parent, branch, foreign = _record(1), _record(7), _record(8)
    parent.parent_id, parent.child_ids = False, Records([branch])
    branch.parent_id, branch.child_ids = parent, Records()
    foreign.parent_id, foreign.child_ids = False, Records()
    empty = _record(False)
    income, expense, foreign_account = [_record(record_id, company_ids=Records([owner])) for record_id, owner in ((11, parent), (12, parent), (13, foreign))]
    branch.income_account_id, branch.expense_account_id = empty, empty
    category = _record(21, property_account_income_categ_id=income, property_account_expense_categ_id=expense)
    parent_sale, parent_purchase, foreign_tax = [_record(record_id, company_id=owner) for record_id, owner in ((41, parent), (42, parent), (49, foreign))]
    child_sale = _record(40, company_id=branch)

    class TaxRecords(Records):
        def filtered_domain(self, domain):
            calls.append(("tax_domain", domain))
            return TaxRecords([record for record in self if _matches(record, domain)])

        def _filter_taxes_by_company(self, company):
            calls.append(("native_tax_filter", company.id))
            while company:
                selected = TaxRecords([record for record in self if record.company_id.id == company.id])
                if selected:
                    return selected
                company = company.parent_id
            return TaxRecords()

    class PositionModel(Model):
        def browse(self, record_id=None):
            return SimpleNamespace(id=False) if record_id is None else super().browse(record_id)

    sale_taxes = [parent_sale, foreign_tax, *([child_sale] if current_sale_tax else [])]
    tag = _record(61)
    position, foreign_position = _record(91, company_id=parent), _record(92, company_id=foreign)
    journal = _record(71, company_id=parent)
    native_accounts = {"income": income, "expense": expense, "stock_journal": journal}

    def get_product_accounts(*, fiscal_pos):
        calls.append(("native_accounts", fiscal_pos.id))
        return native_accounts

    template = _record(51, company_id=parent, taxes_id=TaxRecords(sale_taxes),
                       supplier_taxes_id=TaxRecords([foreign_tax, parent_purchase]), account_tag_ids=Records([tag]),
                       get_product_accounts=get_product_accounts)
    foreign_template = _record(52, company_id=foreign)
    product, foreign_product = _record(31, company_id=parent, product_tmpl_id=template), _record(32, company_id=foreign, product_tmpl_id=foreign_template)
    models = {name: Model(name, rows) for name, rows in {
        "res.company": [parent, branch, foreign], "product.category": [category],
        "product.product": [product, foreign_product], "product.template": [template, foreign_template],
        "account.account": [income, expense, foreign_account], "account.tax": [*sale_taxes, parent_purchase],
        "account.account.tag": [tag], "account.journal": [journal],
    }.items()}
    models["account.fiscal.position"] = PositionModel("account.fiscal.position", [position, foreign_position])
    models["account.tax"]._check_company_domain = lambda company: [("company_id", "parent_of", [company.id])]
    env = Env(models)

    category_item = reads._invoice_preparation_rows(env, contracts.CATEGORY_ID, {"category_id": 21}, 7)[0]
    assert category_item == {"id": 21, "company_id": 7, "income_account_id": 11, "expense_account_id": 12,
                             "company_income_account_id": None, "company_expense_account_id": None}
    tax_item = reads._invoice_preparation_rows(env, contracts.TAX_PROFILE_ID, {"product_id": 31}, 7)[0]
    assert tax_item["sale_tax_ids"] == ([40] if current_sale_tax else [41])
    assert tax_item["purchase_tax_ids"] == [42] and tax_item["account_tag_ids"] == [61]
    assert calls == [("tax_domain", [("company_id", "parent_of", [7])]), ("native_tax_filter", 7),
                     ("tax_domain", [("company_id", "parent_of", [7])]), ("native_tax_filter", 7)]
    account_item = reads._invoice_preparation_rows(env, contracts.ACCOUNTS_ID, {"product_id": 31, "fiscal_position_id": 91}, 7)[0]
    assert account_item["fiscal_position_id"] == 91 and account_item["income_account_id"] == 11
    assert account_item["expense_account_id"] == 12 and account_item["stock_journal_id"] == 71
    assert ("native_accounts", 91) in calls
    for name, field in (("product.product", "company_id"), ("product.template", "company_id"),
                        ("account.account", "company_ids"), ("account.tax", "company_id"),
                        ("account.fiscal.position", "company_id"), ("account.journal", "company_id")):
        searches = [call for call in models[name].calls if call[0] == "search"]
        assert searches and all((field, "parent_of", [7]) in call[1] for call in searches)
    assert reads._invoice_preparation_rows(env, contracts.TAX_PROFILE_ID, {"product_id": 32}, 7) == []
    with pytest.raises(reads._FiscalPositionNotFound):
        reads._invoice_preparation_rows(env, contracts.ACCOUNTS_ID, {"product_id": 31, "fiscal_position_id": 92}, 7)
    native_accounts["income"] = foreign_account
    with pytest.raises(ValueError, match="outside caller scope"):
        reads._invoice_preparation_rows(env, contracts.ACCOUNTS_ID, {"product_id": 31, "fiscal_position_id": 91}, 7)
