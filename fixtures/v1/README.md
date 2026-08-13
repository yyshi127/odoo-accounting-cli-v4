# Accounting fixture v1

This public fixture extends only the two dedicated synthetic V4 databases. It
is fixed to two companies, CNY/SGD company currencies, USD rates on three
dates, one customer and vendor per company, a tax-exclusive customer invoice,
a tax-inclusive vendor bill, and a partial customer payment reconciled against
the invoice.

The fixture is create-once and fail-closed. `apply` requires its marker and all
fixed business references to be absent; `verify` requires the exact canonical
definition marker and all expected accounting outcomes. It has no delete,
replace, arbitrary model, arbitrary method, or arbitrary database operation.

The remaining full Goal fixture domains -- full payment, assets, deferrals,
inventory valuation, and their golden report cases -- remain separate later
versions. This file must not be described as the complete G2 fixture matrix.
