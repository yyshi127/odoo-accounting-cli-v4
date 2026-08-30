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
