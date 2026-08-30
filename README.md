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
