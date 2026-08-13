#!/usr/bin/env python3
"""Apply or verify the public, deterministic ODACV4 accounting fixture v1.

This file is executed only inside ``odoo-bin shell`` or an equivalent pinned
Odoo Python process. It has no arbitrary model, method, database, or value
input. The caller chooses apply/verify through ``ODACV4_FIXTURE_MODE``; the
runtime database must be one of the two dedicated synthetic V4 databases.
"""

from __future__ import annotations

import hashlib
import json
import os
from decimal import Decimal

from odoo import Command


SCHEMA = "odacv4-accounting-fixture-v1"
ICP_KEY = "odoo_accounting_cli_v4.fixture.v1"
DATABASES = ("odoo_cli_v4_dev", "odoo_cli_v4_e2e")
COMPANIES = (
    {
        "id": 1,
        "code": "CN",
        "name": "ODACV4 G5 China",
        "currency": "CNY",
        "foreign_currency": "USD",
        "sale_tax": Decimal("13"),
        "purchase_tax": Decimal("13"),
    },
    {
        "id": 2,
        "code": "SG",
        "name": "ODACV4 G5 Singapore",
        "currency": "SGD",
        "foreign_currency": "USD",
        "sale_tax": Decimal("9"),
        "purchase_tax": Decimal("9"),
    },
)
RATE_DATES = ("2025-01-01", "2025-01-15", "2025-02-01")
RATE_VALUES = (Decimal("1.350000"), Decimal("1.360000"), Decimal("1.370000"))
INVOICE_DATE = "2025-01-20"
BILL_DATE = "2025-01-21"
PAYMENT_DATE = "2025-01-25"
INVOICE_UNTAXED = Decimal("100.00")
BILL_TOTAL = Decimal("113.00")
PARTIAL_PAYMENT = Decimal("50.00")


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fixture_definition():
    return {
        "schema": SCHEMA,
        "companies": [
            {
                "id": item["id"],
                "code": item["code"],
                "currency": item["currency"],
                "foreign_currency": item["foreign_currency"],
                "sale_tax": str(item["sale_tax"]),
                "purchase_tax": str(item["purchase_tax"]),
                "invoice_total": str(
                    (INVOICE_UNTAXED * (Decimal("1") + item["sale_tax"] / 100)).quantize(
                        Decimal("0.01")
                    )
                ),
            }
            for item in COMPANIES
        ],
        "rates": [
            {"date": date, "usd_per_company_currency": str(value)}
            for date, value in zip(RATE_DATES, RATE_VALUES)
        ],
        "documents": {
            "invoice_untaxed": str(INVOICE_UNTAXED),
            "bill_total": str(BILL_TOTAL),
            "partial_payment": str(PARTIAL_PAYMENT),
            "invoice_date": INVOICE_DATE,
            "bill_date": BILL_DATE,
            "payment_date": PAYMENT_DATE,
        },
    }


DEFINITION = fixture_definition()
DEFINITION_SHA256 = hashlib.sha256(canonical(DEFINITION).encode()).hexdigest()


def one(records, label):
    if len(records) != 1:
        raise RuntimeError(f"expected one {label}, got {len(records)}")
    return records


def scoped_company_env(company_id):
    company = one(env["res.company"].sudo().search([("id", "=", company_id)]), "company")
    return env(context={"allowed_company_ids": [company.id]}), company


def account(company_env, company, account_type):
    return one(
        company_env["account.account"].sudo().with_company(company).search(
            [("company_ids", "in", [company.id]), ("account_type", "=", account_type)],
            order="code,id",
            limit=1,
        ),
        f"{account_type} account for company {company.id}",
    )


def tax(company_env, company, use, amount):
    candidates = company_env["account.tax"].sudo().with_context(active_test=False).search(
            [
                ("company_id", "=", company.id),
                ("type_tax_use", "=", use),
                ("amount", "=", amount),
                ("active", "=", True),
            ],
            order="id",
        )
    return one(
        candidates.filtered(lambda item: not item.price_include)[:1],
        f"{use} tax {amount} for company {company.id}",
    )


def journal(company_env, company, journal_type):
    return one(
        company_env["account.journal"].sudo().search(
            [("company_id", "=", company.id), ("type", "=", journal_type)],
            order="code,id",
            limit=1,
        ),
        f"{journal_type} journal for company {company.id}",
    )


def assert_absent():
    if env["ir.config_parameter"].sudo().get_param(ICP_KEY):
        raise RuntimeError("fixture v1 marker already exists")
    for definition in COMPANIES:
        company_id = definition["id"]
        for model, domain, label in (
            (
                "res.partner",
                [("company_id", "=", company_id), ("ref", "like", "ODACV4-FX1-%")],
                "partner",
            ),
            (
                "account.move",
                [("company_id", "=", company_id), ("ref", "like", "ODACV4-FX1-%")],
                "move",
            ),
            (
                "account.tax",
                [("company_id", "=", company_id), ("name", "like", "ODACV4 FX1")],
                "tax",
            ),
        ):
            if env[model].sudo().with_context(active_test=False).search_count(domain):
                raise RuntimeError(f"fixture {label} already exists for company {company_id}")


def create_partner(company_env, company, definition, role):
    code = definition["code"]
    is_customer = role == "CUSTOMER"
    partner = company_env["res.partner"].sudo().create(
        {
            "name": f"ODACV4 FX1 {code} {role.title()}",
            "ref": f"ODACV4-FX1-{code}-{role}",
            "company_id": company.id,
            "customer_rank": 1 if is_customer else 0,
            "supplier_rank": 0 if is_customer else 1,
        }
    )
    property_name = (
        "property_account_receivable_id" if is_customer else "property_account_payable_id"
    )
    setattr(
        partner.with_company(company),
        property_name,
        account(company_env, company, "asset_receivable" if is_customer else "liability_payable"),
    )
    return partner


def create_rates(company_env, company, definition):
    Currency = company_env["res.currency"].sudo()
    currency = one(Currency.search([("name", "=", definition["foreign_currency"])]), "USD")
    Rate = company_env["res.currency.rate"].sudo()
    for date, inverse in zip(RATE_DATES, RATE_VALUES):
        Rate.create(
            {
                "name": date,
                "currency_id": currency.id,
                "company_id": company.id,
                "inverse_company_rate": inverse,
            }
        )


def create_documents(company_env, company, definition, customer, vendor):
    income = account(company_env, company, "income")
    expense = account(company_env, company, "expense")
    sale_tax = tax(company_env, company, "sale", definition["sale_tax"])
    purchase_tax = tax(company_env, company, "purchase", definition["purchase_tax"])
    included_tax = purchase_tax.copy(
        {
            "name": f"ODACV4 FX1 {definition['code']} Included Purchase Tax",
            "description": "ODACV4-FX1-INCLUDED",
            "price_include_override": "tax_included",
        }
    )
    Move = company_env["account.move"].sudo().with_company(company)
    invoice = Move.create(
        {
            "move_type": "out_invoice",
            "company_id": company.id,
            "journal_id": journal(company_env, company, "sale").id,
            "partner_id": customer.id,
            "invoice_date": INVOICE_DATE,
            "date": INVOICE_DATE,
            "invoice_date_due": "2025-02-20",
            "ref": f"ODACV4-FX1-{definition['code']}-INVOICE-TAX-EXCLUDED",
            "invoice_line_ids": [
                Command.create(
                    {
                        "name": "ODACV4 FX1 tax-exclusive service",
                        "quantity": 1,
                        "price_unit": INVOICE_UNTAXED,
                        "account_id": income.id,
                        "tax_ids": [Command.set(sale_tax.ids)],
                    }
                )
            ],
        }
    )
    invoice.action_post()
    bill = Move.create(
        {
            "move_type": "in_invoice",
            "company_id": company.id,
            "journal_id": journal(company_env, company, "purchase").id,
            "partner_id": vendor.id,
            "invoice_date": BILL_DATE,
            "date": BILL_DATE,
            "invoice_date_due": "2025-02-21",
            "ref": f"ODACV4-FX1-{definition['code']}-BILL-TAX-INCLUDED",
            "invoice_line_ids": [
                Command.create(
                    {
                        "name": "ODACV4 FX1 tax-inclusive supplies",
                        "quantity": 1,
                        "price_unit": BILL_TOTAL,
                        "account_id": expense.id,
                        "tax_ids": [Command.set(included_tax.ids)],
                    }
                )
            ],
        }
    )
    bill.action_post()
    bank = journal(company_env, company, "bank")
    if not bank.suspense_account_id:
        raise RuntimeError(f"bank suspense account is absent for company {company.id}")
    bank.inbound_payment_method_line_ids.write(
        {"payment_account_id": bank.suspense_account_id.id}
    )
    bank.outbound_payment_method_line_ids.write(
        {"payment_account_id": bank.suspense_account_id.id}
    )
    payment_action = company_env["account.payment.register"].sudo().with_context(
        active_model="account.move", active_ids=invoice.ids
    ).create(
        {
            "payment_date": PAYMENT_DATE,
            "amount": PARTIAL_PAYMENT,
            "journal_id": bank.id,
        }
    ).action_create_payments()
    payment = company_env["account.payment"].sudo().browse(payment_action["res_id"])
    return invoice, bill, payment, included_tax


def apply_fixture():
    assert_absent()
    for definition in COMPANIES:
        company_env, company = scoped_company_env(definition["id"])
        if company.name != definition["name"] or company.currency_id.name != definition["currency"]:
            raise RuntimeError(f"company fixture baseline mismatch: {definition['id']}")
        customer = create_partner(company_env, company, definition, "CUSTOMER")
        vendor = create_partner(company_env, company, definition, "VENDOR")
        create_rates(company_env, company, definition)
        create_documents(company_env, company, definition, customer, vendor)
    env["ir.config_parameter"].sudo().set_param(ICP_KEY, canonical(DEFINITION))
    env.cr.commit()


def normalized_amount(value):
    return Decimal(str(value)).quantize(Decimal("0.01"))


def verify_company(definition):
    company_env, company = scoped_company_env(definition["id"])
    code = definition["code"]
    Partner = company_env["res.partner"].sudo().with_context(active_test=False)
    customer = one(Partner.search([("ref", "=", f"ODACV4-FX1-{code}-CUSTOMER")]), "customer")
    vendor = one(Partner.search([("ref", "=", f"ODACV4-FX1-{code}-VENDOR")]), "vendor")
    if customer.customer_rank <= 0 or vendor.supplier_rank <= 0:
        raise RuntimeError(f"partner ranks mismatch for {code}")
    Move = company_env["account.move"].sudo()
    invoice = one(
        Move.search([("company_id", "=", company.id), ("ref", "=", f"ODACV4-FX1-{code}-INVOICE-TAX-EXCLUDED")]),
        "invoice",
    )
    bill = one(
        Move.search([("company_id", "=", company.id), ("ref", "=", f"ODACV4-FX1-{code}-BILL-TAX-INCLUDED")]),
        "bill",
    )
    payment = one(
        company_env["account.payment"].sudo().search(
            [("company_id", "=", company.id), ("partner_id", "=", customer.id)]
        ),
        "partial customer payment",
    )
    included_tax = one(
        company_env["account.tax"].sudo().with_context(active_test=False).search(
            [
                ("company_id", "=", company.id),
                ("name", "=", f"ODACV4 FX1 {code} Included Purchase Tax"),
            ]
        ),
        "tax-inclusive purchase tax",
    )
    invoice.invalidate_recordset()
    bill.invalidate_recordset()
    expected_invoice_total = (
        INVOICE_UNTAXED * (Decimal("1") + definition["sale_tax"] / 100)
    ).quantize(Decimal("0.01"))
    if (
        invoice.move_type != "out_invoice"
        or invoice.state != "posted"
        or invoice.payment_state != "partial"
        or normalized_amount(invoice.amount_total) != expected_invoice_total
        or normalized_amount(invoice.amount_residual)
        != expected_invoice_total - PARTIAL_PAYMENT
    ):
        raise RuntimeError(f"customer invoice mismatch for {code}")
    if (
        bill.move_type != "in_invoice"
        or bill.state != "posted"
        or bill.payment_state != "not_paid"
        or normalized_amount(bill.amount_total) != BILL_TOTAL
        or normalized_amount(bill.amount_residual) != BILL_TOTAL
    ):
        raise RuntimeError(f"vendor bill mismatch for {code}")
    if (
        normalized_amount(payment.amount) != PARTIAL_PAYMENT
        or payment.payment_type != "inbound"
        or payment.state not in {"in_process", "paid"}
    ):
        raise RuntimeError(f"partial payment mismatch for {code}")
    invoice_term = one(
        invoice.line_ids.filtered(
            lambda line: line.account_id.account_type == "asset_receivable"
        ),
        f"invoice receivable line for {code}",
    )
    if (
        normalized_amount(invoice_term.amount_residual)
        != expected_invoice_total - PARTIAL_PAYMENT
        or not invoice_term.matched_credit_ids
        or invoice_term.reconciled
    ):
        raise RuntimeError(f"partial reconciliation mismatch for {code}")
    if not included_tax.price_include:
        raise RuntimeError(f"tax-inclusive purchase tax mismatch for {code}")
    bank = journal(company_env, company, "bank")
    if (
        not bank.suspense_account_id
        or any(
            line.payment_account_id != bank.suspense_account_id
            for line in bank.inbound_payment_method_line_ids
            | bank.outbound_payment_method_line_ids
        )
    ):
        raise RuntimeError(f"bank payment-account configuration mismatch for {code}")
    rates = company_env["res.currency.rate"].sudo().search(
        [
            ("company_id", "=", company.id),
            ("currency_id.name", "=", definition["foreign_currency"]),
        ],
        order="name,id",
    )
    if len(rates) != len(RATE_DATES):
        raise RuntimeError(f"currency-rate count mismatch for {code}")
    if [str(item.name) for item in rates] != list(RATE_DATES):
        raise RuntimeError(f"currency-rate dates mismatch for {code}")
    if [Decimal(str(item.inverse_company_rate)).quantize(Decimal("0.000001")) for item in rates] != list(RATE_VALUES):
        raise RuntimeError(f"currency-rate values mismatch for {code}")
    return {
        "company_id": company.id,
        "customer_id": customer.id,
        "vendor_id": vendor.id,
        "invoice_id": invoice.id,
        "bill_id": bill.id,
        "payment_id": payment.id,
        "invoice_total": str(normalized_amount(invoice.amount_total)),
        "invoice_residual": str(normalized_amount(invoice.amount_residual)),
        "bill_total": str(normalized_amount(bill.amount_total)),
        "rate_count": len(rates),
    }


def verify_fixture():
    stored = env["ir.config_parameter"].sudo().get_param(ICP_KEY)
    if stored != canonical(DEFINITION):
        raise RuntimeError("fixture v1 definition marker mismatch")
    companies = [verify_company(item) for item in COMPANIES]
    if env["ir.cron"].sudo().with_context(active_test=False).search_count([("active", "=", True)]):
        raise RuntimeError("active cron jobs reappeared")
    return {
        "result": "pass",
        "schema": SCHEMA,
        "database": env.cr.dbname,
        "definition_sha256": DEFINITION_SHA256,
        "companies": companies,
    }


if env.cr.dbname not in DATABASES:
    raise RuntimeError("fixture v1 can target only the two dedicated synthetic databases")
mode = os.environ.get("ODACV4_FIXTURE_MODE")
if mode == "apply":
    apply_fixture()
elif mode != "verify":
    raise RuntimeError("ODACV4_FIXTURE_MODE must be apply or verify")
print("ODACV4_FIXTURE_RESULT=" + canonical(verify_fixture()))
