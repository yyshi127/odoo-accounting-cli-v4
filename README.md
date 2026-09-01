# Odoo Accounting CLI V4

Independent accounting automation CLI for Odoo 19. This repository is currently in the bootstrap phase and is not a production release.

The active V4 scope is accounting capabilities, structured JSON contracts, and real Odoo ORM/wizard/report integration. It is not a generic ORM browser. Historical sales, purchasing, and inventory extensions remain registered, but are outside current accounting-core development and must not be counted as accounting-core completion.

## Bootstrap development

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r lock/requirements-dev.txt
.venv/bin/python -m pip install -e .
.venv/bin/python -m pytest
.venv/bin/odoo-accounting-cli-v4 version
```

The private Odoo source snapshot, raw generation transcripts, environment evidence, credentials, databases, logs, runtime state, and installed release directories are intentionally excluded from Git and release artifacts.

## Financial reports by journal

`report.trial_balance`, `report.general_ledger`, `report.balance_sheet`, and
`report.profit_and_loss`, plus their `.export` commands, accept optional
`journal_ids` inside `parameters`. For example, a range-report parameter excerpt:

```json
{
  "date_from": "2025-01-01",
  "date_to": "2025-12-31",
  "journal_ids": [9, 10]
}
```

Use IDs returned by `journal.list` for the selected company; the example IDs
are not universal. Balance sheet uses `as_of` instead of a date range. File
exports also require `format` (`pdf` or `xlsx`). The filter uses Odoo's native
journal selection and retains the existing posted-entry report basis.

Supply 1-1000 distinct positive integer IDs. Omit `journal_ids` for the existing
unfiltered behavior; `null` and an empty list are not accepted. Missing,
inaccessible or other-company journals cannot silently become an all-journal
report. If the effective native report does not support the selection, the
command fails rather than returning an unfiltered result.

Pagination cursors bind the selected journal set. Reordering the same IDs is
allowed, but changing the set or switching between filtered and unfiltered
requests requires a new first page. Other reports, including the currently
configured partner ledger, do not accept this optional parameter.

## Invoice taxes and tax-linked journal items

Use existing `tax.list` / `tax.get` results to choose the applicable tax IDs,
then supply each invoice or bill line's `tax_ids` in `customer_invoice.create`,
`vendor_bill.create` or `invoice.lines.replace`. Odoo calculates the amounts;
`invoice.get` and `invoice.tax_breakdown.inspect` read back the invoice-currency
totals and tax-group breakdown.

`journal_item.search` and `journal_item.get` also return:

- `tax_line_id`: the tax ID represented by a tax journal item, otherwise null.
- `tax_ids`: sorted applied tax IDs on the journal item; an empty list is valid.
- `tax_base_amount`: Odoo's signed tax base in **company currency**, not necessarily
  the transaction currency shown by the item's `currency` field.

After posting with `invoice.post`, search by `move_id` to connect the invoice's
base and tax journal items to the tax IDs. Use `report.tax` for the native posted
tax report. Its effective report and columns depend on the company's installed
localization; a generic net/tax report is not proof of statutory-return coverage.
Native generic-tax group rows may have no net amount; those cells are `null`,
not zero. Actual numeric tax amounts retain their native values.
When comparing changes, use the relevant tax row IDs and column expression labels;
do not sum parent totals together with their child rows.

## Financial credit notes and settlement

`customer_credit_note.create` and `vendor_refund.create` create draft financial
credit notes against a posted customer invoice or supplier bill. They do not
return physical stock or transfer cash. Provide replacement `lines` for a partial
credit and a distinct idempotency key for each intended credit note.

Post the credit with `invoice.post`, then read the original document with
`invoice.payment_status.inspect`. Odoo can automatically reconcile a linked
credit during posting; a credit already applied to the original invoice needs no
additional manual reconciliation. If the credit remains outstanding, select the
item whose `move_id` matches that credit and pass its `line_id` to
`reconciliation.apply` as `outstanding_line_id`, together with the original
`invoice_id`. The confirmation is `reconciliation.apply`; its key is
`reconciliation.apply:<invoice_id>:<outstanding_line_id>`.

To undo a specific reconciliation, use `reconciliation.undo` with the invoice,
partial-reconciliation and two line IDs returned by the inspection command.
Undo is a correction operation, not a required step in ordinary credit posting.

Read the source and credit again to verify their residual amounts. A source
settled entirely by credit notes can have `payment_state=reversed`, not `paid`.
Companies using native storno accounting represent credits with negative
debit/credit values; preserve those signs when comparing journal items and
reports. This settlement workflow is distinct from recording an actual cash
refund, which requires the appropriate payment/bank workflow.

For a refund of an already settled original document, create and post the
financial credit note, then use its ID as `move_id` when registering the refund.
`receivable.payment.register` accepts customer invoices and customer credit notes:
Odoo selects an inbound customer receipt for `out_invoice`, or an outbound
customer refund for `out_refund`. `payable.payment.register` accepts supplier bills
and supplier refunds: Odoo selects an outbound supplier payment for `in_invoice`,
or an inbound supplier refund for `in_refund`. The two commands cannot be used
interchangeably across customer and supplier documents.

Amounts remain positive; do not negate the refund amount. Supply an explicit
`amount` to refund only part of the credit, or omit it to settle the remaining
balance using the native wizard defaults. Read `payment.get` for direction and
credit-note linkage, and `invoice.payment_status.inspect` for the remaining
balance. Registration records the accounting payment and its reconciliation;
it does not send a bank transfer or match a bank statement, and a settled
document can remain `in_payment` until the banking workflow is complete.

`receivable.payment.register` and `payable.payment.register` accept optional
`payment_difference_handling` (`open` or `reconcile`). For a document with a
remaining balance of `100`, this parameter excerpt records `99` and writes off
the remaining `1` to the selected account:

```json
{
  "amount": "99",
  "payment_difference_handling": "reconcile",
  "writeoff_account_id": 31,
  "writeoff_label": "Payment difference"
}
```

The existing `move_id`, `journal_id`, and `payment_date` remain required.
`reconcile` requires an explicit positive canonical decimal `amount` and a
positive integer `writeoff_account_id` for an active account accessible in the
selected company; the example ID is not universal. It settles the entire remaining
document difference, including remaining installments. `writeoff_label` is
optional trimmed text of 1-200 characters; omit it to use the native wizard's
default label. Write-off fields are rejected unless the mode is `reconcile`.

Omitting the mode preserves the existing behavior: an explicit `amount` leaves
the unpaid difference open, while omitting `amount` retains the native wizard's
defaults, including early-payment-discount behavior. Explicit `open` may be
used with or without `amount`. Use a distinct operation key for each intended
payment with an explicit amount; reuse that key only for the same request.

Both explicit modes currently require the wizard's payment currency to match
the source document currency. `reconcile` returns `state_conflict` when native
early-payment discounts, special exchange-difference handling, or installment
processing cannot honor the selected write-off account. Read the source balance
and payment journal items to verify settlement; it does not perform bank-statement
matching or guarantee `payment_state=paid`. This explicit write-off extension is
live-verified for untaxed, company-currency customer/vendor documents in both
isolated databases: `100` residual, `99` payment, signed `1` write-off and zero
remaining balance, with immediate replay and rollback checks. This is not a claim
of foreign-currency, early-payment-discount or bank-matching acceptance.

## Analytic distribution readback

`invoice.get` and `journal_entry.get` include `analytic_distribution` on each
returned line. `journal_item.search` and `journal_item.get` expose the same field
on each journal item, so distributions can be checked before and after posting.

An empty distribution is `{}`. Nonempty mappings preserve Odoo's stored keys,
including comma-separated analytic-account combinations, and return percentages
as finite canonical decimal strings such as `"75.25"`. Reading does not resolve
account names, merge keys, round again, or impose the CLI write-input limits on
native stored data. Negative percentages, overlapping combination keys and
native precision are preserved when present.

To clear a distribution through an existing line-write command, supply
`"analytic_distribution": null`; its readback is `{}`. The empty object is a read
representation, not a newly accepted write input. `invoice.lines.replace`
replaces the entire invoice line set, so retain the other lines and fields you
intend to keep.

## Negative unit-price invoice adjustments

`customer_invoice.create` and `vendor_bill.create` accept signed decimal strings
for line `price_unit`, matching the existing `invoice.lines.replace` behavior.
For example, untaxed lines with quantity `"1"` and prices `"100"` and `"-10"`
produce a total of `90`. Quantities must still be positive, discounts remain
between 0 and 100, and amounts must be strings rather than JSON numbers.

Odoo still computes taxes, totals and journal items. A negative-total draft is
not automatically converted into a credit note; native posting rejects a normal
invoice or bill with a negative total under its currency-rounding rules. Use the
appropriate financial credit-note/refund workflow instead. In storno companies,
negative adjustment lines retain native negative debit/credit signs on readback.

## Draft invoice journals and currencies

`invoice.update` accepts optional positive integer `journal_id` and `currency_id`
inside `changes`, for draft customer invoices, supplier bills and financial
credit notes/refunds. For example, this is a `parameters` excerpt:

```json
{
  "move_id": 101,
  "changes": {"journal_id": 9, "currency_id": 1}
}
```

Use accessible IDs for the selected company; the example IDs are not universal.
The journal must belong to that exact company and be a sales journal for customer
documents or a purchase journal for supplier documents. The currency must be
active and accessible. Omit a field to retain the existing update contract;
neither new field accepts `null`. Existing confirmation and replay rules apply.

Odoo's ordinary write recomputes currency amounts, journal items and native
numbering. Changing currency does not exchange the numeric unit prices: a line
priced at 100 remains priced at 100 in the selected currency. A journal's currency
is a default, not an invoice-currency hard lock. Forced account currencies,
previously posted/numbered documents and installed exchange-rate customizations
can impose further native restrictions. Read `invoice.get` and journal items
after the update; the CLI does not bypass those rules or edit posted documents.

## Invoice bank accounts and fiscal positions

`customer_invoice.create` and `vendor_bill.create` accept optional
`partner_bank_id` and `fiscal_position_id` in `parameters`. `invoice.update`
accepts the same fields in `changes`, including on draft financial credit notes
and refunds. Each value is a positive integer ID or `null`; for example:

```json
{
  "move_id": 101,
  "changes": {"partner_bank_id": null, "fiscal_position_id": null}
}
```

This is a parameter excerpt, not a complete request. Explicit `null` writes an
unset relation; omission does not send that field to Odoo or alter an old create
request fingerprint. Other native dependencies, such as a partner or currency
change, can still recompute omitted fields. Read `invoice.get` afterward: it now
returns both fields as IDs or `null`, without bank-account numbers or relation
display names. The existing confirmation, replay and draft-edit rules apply.

An explicitly selected bank must be active, readable by the configured user,
and shared or in the selected company. The CLI does not add bank-owner, currency
or trust-state locks: native payment methods may select a journal's bank rather
than the standard recipient's bank. Selecting this invoice-header reference is
not validation or execution of a bank-payment instruction. Fiscal positions
must be active and accessible in the selected company or its native parent-company
scope. Neither command creates or changes these configuration records.

Setting a fiscal-position header is not a request to remap every invoice line.
Create still submits the caller's explicit account and tax IDs. The CLI does not
call `action_update_fpos_values`, which also recomputes unit prices. Native
computations, country/tax consistency and posting restrictions remain in force.

## Advance payments followed by invoicing

Use `payment.create` and `payment.post` to record an advance before the invoice
exists: inbound/customer for a customer receipt, outbound/supplier for a supplier
payment. Choose an existing permitted journal/payment-method line and a distinct
creation key for each intended payment. An immediate creation replay must occur
while the payment is still draft; do not recreate an already-posted payment.

Create the later document with `customer_invoice.create` or `vendor_bill.create`
and post it with `invoice.post`. Read `payment.get` for the payment's `move_id`,
then `invoice.payment_status.inspect` for the invoice's outstanding items. Match
that move ID and pass its `line_id` to `reconciliation.apply` as
`outstanding_line_id`, together with `invoice_id`. Read the invoice/payment and
journal items again to verify the linked documents and remaining balance.

Zero invoice residual does not necessarily mean `payment_state=paid`; native
payments can remain `in_process` and invoices `in_payment` until bank matching.
This workflow does not create or match a bank statement. The shared two-database
case verifies untaxed company-currency advances of 120/90, subsequent customer/
supplier invoicing, full settlement, immediate replay and transaction rollback.
It does not establish taxed, foreign-currency or nonempty financial-reference
selection coverage.

## Invoice and bill accounting dates

`customer_invoice.create` and `vendor_bill.create` accept an optional `date`
(accounting date), independently of `invoice_date` (document date). For example,
these are header fields within `parameters`, not a complete request:

```json
{
  "invoice_date": "2026-08-27",
  "date": "2026-08-31"
}
```

`invoice.update` also accepts `date` inside `changes` for draft invoices, bills,
and refunds. Use a `YYYY-MM-DD` string, not `null`. Omitting `date` retains the
existing behavior and request fingerprint. `invoice.get` already returns both
dates; read it after updating or posting to see the actual accounting date.

Odoo's native date computation, posting, sequence, and lock-date rules still
apply. A later update to `invoice_date` alone may recompute the accounting date;
include both fields in the same update when both are intentional. Posting can
adjust the date or reject the operation under native rules. This does not bypass
a closed accounting period or allow editing a posted document.

## Manual journal-entry due dates

`journal_entry.create` and `journal_entry.lines.replace` accept optional
`date_maturity` on individual lines. It is independent of the entry's accounting
`date`. For example, add `"date_maturity": "2026-09-30"` to a receivable or payable
line, or use `"date_maturity": null` to clear it. Dates are `YYYY-MM-DD` strings;
the CLI adds no requirement that maturity be on or after the accounting date.

Read `journal_entry.get` or `journal_item.search/get` to check the stored date.
Receivable/payable open-item `due_date_from` and `due_date_to` filters use the
stored maturity date; an unset date does not match those date bounds. Native
aged-receivable/payable reports instead fall back to the accounting date when
maturity is unset. Maturity affects aging, not the entry's debit/credit amounts.

Omitting the new field does not change old request fingerprints or make an
otherwise unchanged line-replacement replay rewrite existing dates. A real
`journal_entry.lines.replace` still replaces the entire submitted line set:
include dates you intend to keep when changing other line values. New lines
without a supplied date use the native default, not the deleted lines' dates.
Actual replacement remains draft-only; this adds no posted-line edit command.

## Deferred invoice and bill lines

The existing `customer_invoice.create`, `vendor_bill.create`,
`invoice.lines.replace`, `customer_credit_note.create`, and `vendor_refund.create`
commands accept these optional fields on each invoice line:

```json
{
  "deferred_start_date": "2026-09-01",
  "deferred_end_date": "2026-10-31"
}
```

This is a line-field excerpt, not a complete command request. Provide both
dates together, with start on or before end, or both as `null` to clear them.
Same-day periods and periods starting before the invoice date are allowed.
Requiring an explicit pair is a CLI contract choice: native Odoo can infer a
start date from an end date, but this CLI does not rely on that inference.
Omitting both fields preserves the original request format and idempotency
input; an otherwise unchanged legacy replay does not clear existing dates.
`invoice.lines.replace` still replaces the entire line set when another line
value changes, so include dates that should remain on replacement lines.

`invoice.get` returns both dates for each line, or `null` when unset or when
the native deferred-date fields are unavailable. Writing non-null dates
requires Odoo's deferred-accounting support and appropriate income/expense
lines. Existing ACLs and company restrictions still apply.

With the company's native `on_validation` setting, `invoice.post` generates
the deferred entries automatically. Future recognition entries remain draft
with native date-based auto-posting; do not post them early merely to complete
a test. Manual month-end generation is a separate existing workflow, not an
extra mandatory step after automatic generation.

On the current server, multi-period automatic generation is blocked by an
existing `exchange_currency_rate` singleton error. Date input/readback has live
evidence, but the complete deferred workflow has not passed; see
[the handoff](docs/execution/HANDOFF.md) for the exact boundary and failed-run log.
